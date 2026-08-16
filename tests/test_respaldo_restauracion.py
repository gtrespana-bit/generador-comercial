"""E3-020 / E3-021 — respaldo y restauración web completos y verificables.

Regla que gobierna todo: una copia solo se restaura si (1) su manifest declara
el formato correcto, (2) cada archivo coincide con su huella SHA-256, (3) el
flujo HTTP exige dos subidas del MISMO archivo y confirmación explícita, y
(4) la restauración nunca borra ni sobrescribe datos existentes (fusión
idempotente). Estas pruebas cubren el paquete, la integridad, la restauración
tras pérdida, la idempotencia, los rechazos, la honestidad de lo omitido y el
flujo HTTP de dos pasos.
"""
from datetime import date, datetime
import hashlib
import io
import json
import zipfile
from pathlib import Path
from urllib.parse import unquote

import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import main as main_module
from app.database import Base, get_db
from app.main import app
from app.models import (
    AnexoPresupuesto,
    ArchivoAlmacenado,
    BorradorPresupuesto,
    CambioAlcance,
    CambioAlcanceItem,
    Capitulo,
    CategoriaPartida,
    Cliente,
    Configuracion,
    DescomposicionFila,
    DescomposicionPartida,
    EnlacePropuesta,
    Factura,
    FacturaCapitulo,
    FacturaItem,
    Licencia,
    Medicion,
    Membresia,
    NotaSeguimiento,
    Organizacion,
    Pago,
    Partida,
    Plantilla,
    Presupuesto,
    PresupuestoItem,
    PresupuestoItemProducto,
    PresupuestoVersion,
    Producto,
    Proyecto,
    RecetaEstancia,
    Recurso,
    Usuario,
)
from app.services.respaldo import (
    FORMATO_RESPALDO,
    VERSION_RESPALDO,
    ErrorRespaldo,
    generar_respaldo,
)
from app.services.restauracion import analizar_respaldo, restaurar_respaldo
from app.storage import read_reference, reset_storage_backend_cache, save_object

ORIGEN = "https://cotizat.test"
AUTH_UUID = "00000000-0000-4000-8000-000000000020"


# ---------------------------------------------------------------------------
# Fábrica del entorno: organización rica con datos, archivos y casos límite
# ---------------------------------------------------------------------------

@pytest.fixture
def entorno(monkeypatch, tmp_path):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _fk(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as db:
        org = Organizacion(nombre="Constructora Restaurada", slug="restauracion")
        duena = Usuario(
            auth_user_id=AUTH_UUID,
            email="duena@example.com",
            nombre="Dueña",
            email_verificado_at=datetime(2026, 8, 16),
        )
        miembro = Usuario(
            auth_user_id="00000000-0000-4000-8000-000000000021",
            email="miembro@example.com",
            nombre="Miembro",
        )
        db.add_all([org, duena, miembro])
        db.flush()
        db.info["organizacion_id"] = org.id
        db.info["rol_membresia"] = "propietario"

        configuracion = Configuracion(
            empresa_nombre="Constructora Restaurada",
            iva_default=18.0,
            moneda_default="Bs",
            validez_default=45,
        )
        cliente = Cliente(nombre="Cliente Restaurado", rif="J-12345678-9", email="c@example.com")
        cliente_demo = Cliente(nombre="Cliente Demo", es_demo=True)
        db.add_all([configuracion, cliente, cliente_demo])

        # Catálogo con archivo en storage
        logo_bytes = b"PNG-logotipo-empresa"
        guardado_logo = save_object(db, logo_bytes, "logos", "logo.png", "image/png")
        # Mismo contenido con otra clave: la copia debe deduplicarlo por SHA-256
        guardado_foto = save_object(db, logo_bytes, "fotos-proyecto", "foto.jpg", "image/jpeg")
        partida = Partida(
            nombre="Cerámica esmaltada", precio_unitario=12.0, unidad="m2",
            categoria="Albañilería", imagen=guardado_logo.reference,
        )
        producto = Producto(
            nombre="Porcelanato gris", precio_unitario=45.0, unidad="m2",
            imagen=guardado_logo.reference,  # misma huella: deduplicación por SHA-256
        )
        recurso = Recurso(codigo="MO001", descripcion="Oficial", unidad="hora",
                          categoria="mano_obra", precio=6.5)
        categoria = CategoriaPartida(categoria="Albañilería", subcategoria="Muros")
        plantilla = Plantilla(nombre="Baño básico", datos="[]")
        receta = RecetaEstancia(nombre="Baño principal", datos="[]")
        db.add_all([partida, producto, recurso, categoria, plantilla, receta])
        db.flush()

        presupuesto = Presupuesto(
            numero="P-2026-020", year=2026, fecha=date(2026, 8, 16),
            titulo="Reforma de baño", estado="aprobado", client_id=cliente.id,
            foto_proyecto=guardado_foto.reference,
        )
        demo = Presupuesto(
            numero="P-DEMO-001", year=2026, fecha=date(2026, 8, 16),
            titulo="Presupuesto de ejemplo", estado="borrador",
            client_id=cliente.id, es_demo=True,
        )
        capitulo = Capitulo(nombre="BAÑO", orden=1)
        item = PresupuestoItem(
            nombre="Revestimiento", unidad="m2", cantidad=10,
            precio_unitario=20, orden=1,
        )
        item.mediciones.append(Medicion(concepto="Paredes", cantidad=8, orden=1))
        item.productos_opciones.append(PresupuestoItemProducto(
            nombre="Porcelanato gris", precio=45.0, seleccionado=True, orden=1,
        ))
        item.descomposicion_cype = DescomposicionPartida(
            codigo="D-01", unidad="m2", coste_directo_unitario=15.0,
            archivo_origen=guardado_logo.reference, nombre_archivo_origen="cype.xlsx",
        )
        capitulo.partidas.append(item)
        presupuesto.capitulos.append(capitulo)
        db.add_all([presupuesto, demo])
        db.flush()

        version = PresupuestoVersion(
            presupuesto_id=presupuesto.id, numero_version=1,
            estado="aprobada", total=200.0, datos_snapshot="{}",
            pdf_snapshot=guardado_logo.reference,
        )
        db.add_all([
            version,
            AnexoPresupuesto(presupuesto_id=presupuesto.id, nombre="Plano.pdf",
                             archivo=guardado_logo.reference),
            NotaSeguimiento(
                presupuesto_id=presupuesto.id,
                texto="Llamé al cliente y confirmó el alcance.",
                created_at=datetime(2026, 8, 16, 12, 0),
            ),
        ])
        db.flush()

        descomposicion = (
            db.query(DescomposicionPartida).filter(
                DescomposicionPartida.partida_id == item.id).first()
        )
        db.add(DescomposicionFila(
            descomposicion_id=descomposicion.id, orden=1, tipo="material",
            descripcion="Cerámica", rendimiento=1.0, precio_unitario=12.0,
            importe=12.0,
        ))

        # Enlace con respuesta histórica + enlace pendiente (no deben viajar)
        db.add_all([
            EnlacePropuesta(
                presupuesto_id=presupuesto.id,
                presupuesto_version_id=version.id,
                presupuesto_version_numero=1,
                token_hash="a" * 64, token_prefix="prefijoresp",
                pdf_snapshot=guardado_logo.reference,
                empresa_nombre="Constructora Restaurada",
                cliente_nombre="Cliente Restaurado",
                presupuesto_numero="P-2026-020",
                presupuesto_titulo="Reforma de baño",
                total=200.0, moneda="Bs",
                fecha_presupuesto=date(2026, 8, 16),
                valido_hasta=date(2026, 9, 15),
                expires_at=datetime(2026, 9, 15, 23, 59),
                respuesta="aceptada",
                respondido_por_nombre="Cliente Restaurado",
                respondido_por_email="c@example.com",
                respuesta_comentario="Aprobado, empezamos el lunes.",
                responded_at=datetime(2026, 8, 16, 13, 30),
            ),
            EnlacePropuesta(
                presupuesto_id=presupuesto.id,
                presupuesto_version_id=version.id,
                presupuesto_version_numero=1,
                token_hash="b" * 64, token_prefix="prefijopend",
                pdf_snapshot=guardado_logo.reference,
                empresa_nombre="Constructora Restaurada",
                cliente_nombre="Cliente Restaurado",
                presupuesto_numero="P-2026-020",
                presupuesto_titulo="Reforma de baño",
                total=200.0, moneda="Bs",
                fecha_presupuesto=date(2026, 8, 16),
                valido_hasta=date(2026, 9, 15),
                expires_at=datetime(2026, 9, 15, 23, 59),
            ),
        ])

        factura = Factura(
            numero="F-2026-001", year=2026, fecha=date(2026, 8, 16),
            titulo="Anticipo baño", estado="emitida", client_id=cliente.id,
        )
        factura_capitulo = FacturaCapitulo(nombre="ANTICIPO", orden=1)
        factura_capitulo.partidas.append(FacturaItem(
            nombre="Anticipo 50%", unidad="global", cantidad=1,
            precio_unitario=100, orden=1,
        ))
        factura.capitulos.append(factura_capitulo)
        db.add(factura)
        db.flush()

        proyecto = Proyecto(
            presupuesto_id=presupuesto.id, presupuesto_version_id=version.id,
            nombre="Baño Cliente Restaurado", estado="en_ejecucion",
        )
        proyecto.cambios.append(CambioAlcance(
            numero=1, descripcion="Cambio de grifería", estado="aprobado",
            diferencia_total=30.0,
            items=[CambioAlcanceItem(
                tipo="agregado", nombre="Grifería", cantidad=1, precio_unitario=30,
            )],
        ))
        proyecto.pagos.append(Pago(
            fecha=date(2026, 8, 16), importe=100.0, moneda="Bs",
            metodo="transferencia", referencia="REF-1", estado="confirmado",
        ))
        db.add(proyecto)
        db.flush()
        # Pago vinculado solo a la factura (sin proyecto): clave natural parcial
        db.add(Pago(
            factura_id=factura.id, fecha=date(2026, 8, 16), importe=100.0,
            moneda="Bs", metodo="transferencia", referencia="REF-2",
            estado="confirmado",
        ))

        # Lo que NUNCA debe viajar: licencias y datos de otra índole operativa
        db.add(Licencia(
            organizacion_id=org.id,
            estado="activa", origen="cortesia",
            inicio=date(2026, 8, 1), vence=date(2026, 9, 1),
            creada_por_email="operador@example.com",
        ))

        db.add(Membresia(usuario_id=duena.id, organizacion_id=org.id, rol="propietario"))
        db.add(Membresia(usuario_id=miembro.id, organizacion_id=org.id, rol="miembro"))
        db.commit()
        ids = (org.id, duena.id, presupuesto.id)

    monkeypatch.setenv("COTIZAT_STORAGE_BACKEND", "local")
    monkeypatch.setenv("COTIZAT_STORAGE_DIR", str(tmp_path / "storage"))
    reset_storage_backend_cache()
    rol = {"valor": "propietario"}

    def _db(request: Request):
        db = Session()
        db.info["organizacion_id"] = ids[0]
        db.info["usuario_id"] = ids[1]
        db.info["rol_membresia"] = rol["valor"]
        request.state.organizacion = db.get(Organizacion, ids[0])
        request.state.membresia = None
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _db
    try:
        yield Session, ids, rol
    finally:
        app.dependency_overrides.pop(get_db, None)
        reset_storage_backend_cache()
        engine.dispose()


def _cliente():
    return TestClient(app, base_url=ORIGEN)


def _paquete_bytes(Session, org_id) -> bytes:
    with Session() as db:
        db.info["organizacion_id"] = org_id
        db.info["rol_membresia"] = "propietario"
        return generar_respaldo(db)


def _borrar_negocio(Session, org_id) -> None:
    """Simula la pérdida total de datos de negocio (no de la organización).

    El borrado sigue el orden inverso de las dependencias para que las
    claves foráneas (activadas como en la aplicación real) no se quejen.
    """
    orden = (
        EnlacePropuesta,
        Pago, CambioAlcanceItem, CambioAlcance, Proyecto,
        NotaSeguimiento, AnexoPresupuesto, BorradorPresupuesto, PresupuestoVersion,
        DescomposicionFila, DescomposicionPartida,
        Medicion, PresupuestoItemProducto, PresupuestoItem, Capitulo,
        Presupuesto,
        FacturaItem, FacturaCapitulo, Factura,
        Cliente,
        Partida, Producto, Recurso, Plantilla, RecetaEstancia, CategoriaPartida,
        ArchivoAlmacenado,
    )
    with Session() as db:
        db.info["organizacion_id"] = org_id
        db.info["rol_membresia"] = "propietario"
        for modelo in orden:
            db.query(modelo).delete(synchronize_session=False)
        configuracion = db.query(Configuracion).first()
        configuracion.iva_default = 16.0
        configuracion.moneda_default = "USD"
        db.commit()


def _restaurar(Session, org_id, ruta: Path):
    with Session() as db:
        db.info["organizacion_id"] = org_id
        db.info["rol_membresia"] = "propietario"
        resultado = restaurar_respaldo(db, ruta)
        db.commit()
        return resultado


# ---------------------------------------------------------------------------
# E3-020: el paquete es completo, verificable y honesto
# ---------------------------------------------------------------------------

def test_paquete_manifest_sha256_y_omisiones_declaradas(entorno, tmp_path):
    Session, ids, _rol = entorno
    contenido = _paquete_bytes(Session, ids[0])
    with zipfile.ZipFile(io.BytesIO(contenido)) as paquete:
        manifest = json.loads(paquete.read("manifest.json"))
        assert manifest["formato"] == FORMATO_RESPALDO
        assert manifest["version"] == VERSION_RESPALDO
        assert manifest["organizacion"]["nombre"] == "Constructora Restaurada"
        # Los datos de demostración no viajan
        assert manifest["conteos"]["clientes.json"] == 1
        assert manifest["conteos"]["presupuestos.json"] == 1
        # Cada archivo declarado existe y coincide con su huella
        for entrada in manifest["archivos"]:
            crudo = paquete.read(f"archivos/{entrada['sha256']}")
            assert len(crudo) == entrada["tamano"]
            assert hashlib.sha256(crudo).hexdigest() == entrada["sha256"]
        # La misma huella agrupa las referencias repetidas (sin duplicar bytes)
        assert len(manifest["archivos"]) == 1
        assert len(manifest["archivos"][0]["referencias"]) >= 2
        # Lo omitido está declarado con su motivo
        assert "licencias" in manifest["omitido"]
        assert "enlaces_propuesta" in manifest["omitido"]
        # El historial de respuestas viaja como trazabilidad
        historial = json.loads(paquete.read("datos/enlaces_historial.json"))
        assert len(historial) == 1
        assert historial[0]["respuesta"] == "aceptada"
        # Las membresías viajan como pares (correo, rol)
        membresias = json.loads(paquete.read("datos/membresias.json"))
        assert sorted((m["email"], m["rol"]) for m in membresias) == [
            ("duena@example.com", "propietario"),
            ("miembro@example.com", "miembro"),
        ]
        # El LEEME explica la restauración
        assert "SHA-256" in paquete.read("LEEME_RESTAURACION.txt").decode("utf-8")


def test_archivo_no_recuperable_se_declara_y_la_referencia_se_conserva(entorno, tmp_path):
    Session, ids, _rol = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        presupuesto = db.query(Presupuesto).first()
        presupuesto.foto_proyecto = "uploads/inexistente.png"
        db.commit()
    contenido = _paquete_bytes(Session, ids[0])
    with zipfile.ZipFile(io.BytesIO(contenido)) as paquete:
        manifest = json.loads(paquete.read("manifest.json"))
        assert any("no se pudo leer" in aviso for aviso in manifest["avisos"])

    ruta = tmp_path / "copia.zip"
    ruta.write_bytes(contenido)
    _borrar_negocio(Session, ids[0])
    _restaurar(Session, ids[0], ruta)
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        restaurado = db.query(Presupuesto).first()
        # La referencia original se conserva tal cual (no se falsea ni se pierde)
        assert restaurado.foto_proyecto == "uploads/inexistente.png"


# ---------------------------------------------------------------------------
# E3-021: restauración completa tras pérdida, con archivos y sin duplicados
# ---------------------------------------------------------------------------

def test_restauracion_recupera_datos_archivos_y_ajustes_sin_pisar_identidad(entorno, tmp_path):
    Session, ids, _rol = entorno
    contenido = _paquete_bytes(Session, ids[0])
    ruta = tmp_path / "copia.zip"
    ruta.write_bytes(contenido)

    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        configuracion = db.query(Configuracion).first()
        configuracion.empresa_nombre = "Identidad del destino"
        db.commit()
    _borrar_negocio(Session, ids[0])
    resultado = _restaurar(Session, ids[0], ruta)

    assert resultado.restaurados["presupuestos.json"] == 1
    assert resultado.restaurados["clientes.json"] == 1
    assert resultado.archivos_restaurados == 1
    assert resultado.avisos == []

    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        presupuesto = db.query(Presupuesto).first()
        assert presupuesto.numero == "P-2026-020"
        assert len(presupuesto.capitulos) == 1
        assert presupuesto.capitulos[0].partidas[0].nombre == "Revestimiento"
        # Los archivos volvieron verificados y legibles
        referencia = presupuesto.foto_proyecto
        assert referencia.startswith("storage://")
        assert read_reference(referencia) == b"PNG-logotipo-empresa"
        anexo = db.query(AnexoPresupuesto).first()
        assert read_reference(anexo.archivo) == b"PNG-logotipo-empresa"
        # Ajustes comerciales restaurados; identidad del destino intacta
        configuracion = db.query(Configuracion).first()
        assert configuracion.iva_default == 18.0
        assert configuracion.moneda_default == "Bs"
        assert configuracion.empresa_nombre == "Identidad del destino"
        # La respuesta histórica de la propuesta se conservó como nota
        notas = db.query(NotaSeguimiento).all()
        textos = " | ".join(nota.texto for nota in notas)
        assert "Historial de propuesta (restaurado): aceptada" in textos
        # Los enlaces (secretos no reconstruibles) no se restauran
        assert db.query(EnlacePropuesta).count() == 0
        # Trazabilidad completa: proyectos, cambios, pagos y facturas
        assert db.query(Proyecto).count() == 1
        assert db.query(CambioAlcance).count() == 1
        assert db.query(Pago).count() == 2
        assert db.query(Factura).count() == 1


def test_restauracion_es_idempotente_y_no_duplica(entorno, tmp_path):
    Session, ids, _rol = entorno
    ruta = tmp_path / "copia.zip"
    ruta.write_bytes(_paquete_bytes(Session, ids[0]))
    _borrar_negocio(Session, ids[0])
    primera = _restaurar(Session, ids[0], ruta)
    assert primera.restaurados["presupuestos.json"] == 1

    segunda = _restaurar(Session, ids[0], ruta)
    assert segunda.restaurados == {}
    assert segunda.reutilizados["presupuestos.json"] == 1
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        assert db.query(Presupuesto).count() == 1
        assert db.query(Cliente).count() == 1
        assert db.query(Capitulo).count() == 1


def test_restauracion_tras_perdida_parcial_solo_repone_lo_faltante(entorno, tmp_path):
    Session, ids, _rol = entorno
    ruta = tmp_path / "copia.zip"
    ruta.write_bytes(_paquete_bytes(Session, ids[0]))
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        capitulo = db.query(Capitulo).first()
        db.delete(capitulo)
        db.commit()

    resultado = _restaurar(Session, ids[0], ruta)
    # El presupuesto existente se reutiliza; el capítulo perdido se repone
    assert resultado.reutilizados["presupuestos.json"] == 1
    assert resultado.restaurados["capitulos.json"] == 1
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        reales = db.query(Presupuesto).filter(Presupuesto.es_demo.is_(False)).all()
        assert len(reales) == 1
        assert db.query(Capitulo).count() == 1


# ---------------------------------------------------------------------------
# Rechazos: una copia alterada o extraña nunca se restaura
# ---------------------------------------------------------------------------

def _reescribir_zip(origen: bytes, mutacion) -> bytes:
    destino = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(origen)) as lectura:
        with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as escritura:
            for info in lectura.infolist():
                datos = lectura.read(info.filename)
                datos = mutacion(info.filename, datos)
                escritura.writestr(info.filename, datos)
    return destino.getvalue()


def test_rechaza_archivo_con_huella_alterada(entorno, tmp_path):
    Session, ids, _rol = entorno
    contenido = _paquete_bytes(Session, ids[0])

    def alterar(nombre, datos):
        if nombre.startswith("archivos/"):
            return b"X" + datos[1:]
        return datos

    alterado = _reescribir_zip(contenido, alterar)
    ruta = tmp_path / "alterado.zip"
    ruta.write_bytes(alterado)
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        with pytest.raises(ErrorRespaldo, match="huella"):
            analizar_respaldo(db, ruta)


def test_rechaza_conteos_que_no_coinciden_con_el_manifest(entorno, tmp_path):
    Session, ids, _rol = entorno
    contenido = _paquete_bytes(Session, ids[0])

    def inflar(nombre, datos):
        if nombre == "datos/clientes.json":
            filas = json.loads(datos)
            filas.append(filas[0])
            return json.dumps(filas).encode("utf-8")
        return datos

    alterado = _reescribir_zip(contenido, inflar)
    ruta = tmp_path / "inflado.zip"
    ruta.write_bytes(alterado)
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        with pytest.raises(ErrorRespaldo, match="conteos"):
            analizar_respaldo(db, ruta)


def test_rechaza_formato_y_version_desconocidos(entorno, tmp_path):
    Session, ids, _rol = entorno
    contenido = _paquete_bytes(Session, ids[0])

    def cambiar_manifest(nombre, datos, **cambios):
        if nombre == "manifest.json":
            manifest = json.loads(datos)
            manifest.update(cambios)
            return json.dumps(manifest).encode("utf-8")
        return datos

    for cambios, mensaje in (
        ({"formato": "otro-formato"}, "copia de seguridad web"),
        ({"version": 99}, "versión no soportada"),
    ):
        alterado = _reescribir_zip(
            contenido, lambda n, d, c=cambios: cambiar_manifest(n, d, **c)
        )
        ruta = tmp_path / "formato.zip"
        ruta.write_bytes(alterado)
        with Session() as db:
            db.info["organizacion_id"] = ids[0]
            with pytest.raises(ErrorRespaldo, match=mensaje):
                analizar_respaldo(db, ruta)


def test_rechaza_zip_con_rutas_invalidas(tmp_path, entorno):
    Session, ids, _rol = entorno
    ruta = tmp_path / "malicioso.zip"
    with zipfile.ZipFile(ruta, "w") as paquete:
        paquete.writestr("manifest.json", json.dumps({
            "formato": FORMATO_RESPALDO,
            "version": VERSION_RESPALDO,
            "archivos": [],
            "conteos": {},
        }))
        paquete.writestr("../fuera-del-paquete.txt", "no debe pasar")
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        with pytest.raises(ErrorRespaldo, match="rutas no válidas"):
            analizar_respaldo(db, ruta)


# ---------------------------------------------------------------------------
# Flujo HTTP de dos pasos con verificación SHA-256 y roles
# ---------------------------------------------------------------------------

def _post_archivo(cliente, ruta_archivo: Path, **extra):
    datos = {"confirmar": "si", **extra}
    return cliente.post(
        "/configuracion/respaldo/restaurar/confirmar",
        files={"archivo": (ruta_archivo.name, ruta_archivo.read_bytes(), "application/zip")},
        data=datos,
        headers={"Origin": ORIGEN},
        follow_redirects=False,
    )


def test_flujo_http_dos_pasos_exige_el_mismo_archivo(entorno, tmp_path):
    Session, ids, _rol = entorno
    ruta = tmp_path / "copia.zip"
    ruta.write_bytes(_paquete_bytes(Session, ids[0]))
    _borrar_negocio(Session, ids[0])
    cliente = _cliente()

    paso1 = cliente.post(
        "/configuracion/respaldo/restaurar",
        files={"archivo": (ruta.name, ruta.read_bytes(), "application/zip")},
        headers={"Origin": ORIGEN},
        follow_redirects=False,
    )
    assert paso1.status_code == 200
    assert "Paso 2 de 2 — Revisa y confirma" in paso1.text
    sha256 = hashlib.sha256(ruta.read_bytes()).hexdigest()
    assert sha256 in paso1.text

    # Confirmar con otro archivo: rechazo sin escribir nada
    otro = tmp_path / "otro.zip"
    with zipfile.ZipFile(otro, "w") as paquete:
        paquete.writestr("nada.txt", "otra cosa")
    paso2_distinto = _post_archivo(cliente, otro, sha256=sha256)
    assert paso2_distinto.status_code == 303
    assert "no es el mismo" in unquote(paso2_distinto.headers["location"])

    # Confirmar con el archivo correcto y la casilla marcada
    paso2 = _post_archivo(cliente, ruta, sha256=sha256)
    assert paso2.status_code == 200
    assert "Restauración completada" in paso2.text

    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        assert db.query(Presupuesto).count() == 1


def test_flujo_http_exige_confirmacion_explicita(entorno, tmp_path):
    Session, ids, _rol = entorno
    ruta = tmp_path / "copia.zip"
    ruta.write_bytes(_paquete_bytes(Session, ids[0]))
    cliente = _cliente()
    sha256 = hashlib.sha256(ruta.read_bytes()).hexdigest()
    paso = cliente.post(
        "/configuracion/respaldo/restaurar/confirmar",
        files={"archivo": (ruta.name, ruta.read_bytes(), "application/zip")},
        data={"sha256": sha256},
        headers={"Origin": ORIGEN},
        follow_redirects=False,
    )
    assert paso.status_code == 303
    assert "casilla de confirmación" in unquote(paso.headers["location"])


def test_rutas_exigen_rol_propietario_o_administrador(entorno, tmp_path):
    Session, ids, rol = entorno
    cliente = _cliente()

    rol["valor"] = "miembro"
    for ruta, metodo in (
        ("/configuracion/respaldo", "get"),
        ("/configuracion/respaldo/descargar", "get"),
    ):
        respuesta = getattr(cliente, metodo)(ruta, follow_redirects=False)
        assert respuesta.status_code == 303
        assert respuesta.headers["location"].startswith("/configuracion")

    rol["valor"] = "propietario"
    pagina = cliente.get("/configuracion/respaldo")
    assert pagina.status_code == 200
    assert "Descargar copia completa" in pagina.text

    descarga = cliente.get("/configuracion/respaldo/descargar")
    assert descarga.status_code == 200
    assert descarga.content.startswith(b"PK")  # zip
    assert descarga.headers["cache-control"] == "no-store"


def test_descarga_y_restauracion_disponibles_en_ambos_backends(entorno, tmp_path):
    Session, ids, _rol = entorno
    contenido = _paquete_bytes(Session, ids[0])
    # La descarga funciona igual en SQLite que en PostgreSQL: es un paquete
    # de organización, no un volcado de archivos de base de datos.
    with zipfile.ZipFile(io.BytesIO(contenido)) as paquete:
        assert "manifest.json" in paquete.namelist()
        assert "presupuestos.db" not in paquete.namelist()


def test_membresia_de_cuenta_inexistente_se_omite_con_aviso(entorno, tmp_path):
    Session, ids, _rol = entorno
    ruta = tmp_path / "copia.zip"
    ruta.write_bytes(_paquete_bytes(Session, ids[0]))
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        miembro = db.query(Usuario).filter(Usuario.email == "miembro@example.com").first()
        db.delete(miembro)  # elimina en cascada su membresía
        db.commit()

    resultado = _restaurar(Session, ids[0], ruta)
    assert any(
        "no existe una cuenta" in aviso for aviso in resultado.avisos
    )
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        emails = {m.usuario.email for m in db.query(Membresia).all()}
        assert "miembro@example.com" not in emails
