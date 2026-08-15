"""E1W-012 — importación controlada de una instalación SQLite hacia la web.

La regla que gobierna todo: nunca se migran datos privados sin acción y
confirmación del propietario. Estas pruebas cubren el servicio (análisis,
importación, idempotencia, honestidad de avisos, permisos) y el flujo HTTP de
dos pasos con verificación SHA-256.
"""
import hashlib
import io
import json
import sqlite3
import zipfile
from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import (
    Capitulo,
    Cliente,
    Factura,
    Medicion,
    Membresia,
    Organizacion,
    Partida,
    PermisoOrganizacionError,
    Presupuesto,
    PresupuestoItem,
    Producto,
    Proyecto,
    Recurso,
    Usuario,
    usar_organizacion,
)
from app.services.instalacion_sqlite import (
    ErrorInstalacion,
    analizar_instalacion,
    importar_instalacion,
)


# ---------------------------------------------------------------------------
# Fábrica de instalaciones locales de origen
# ---------------------------------------------------------------------------

def _instalacion_local(tmp_path, con_demo=False, organizacion_id=1, numero="P-2026-001"):
    """Crea un presupuestos.db realista usando los modelos actuales."""
    ruta = tmp_path / "presupuestos.db"
    engine = create_engine(f"sqlite:///{ruta}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as db:
        db.add(Organizacion(id=organizacion_id, nombre="Local", slug=f"local-{organizacion_id}"))
        db.flush()
        db.info["organizacion_id"] = organizacion_id

        cliente = Cliente(nombre="Cliente Local", telefono="+58 400 000", email="c@example.com")
        db.add(cliente)
        partida_cat = Partida(
            nombre="Tabique local",
            precio_unitario=30.0,
            unidad="m2",
            categoria="Albañilería",
            imagen="uploads/partidas/foto.png",  # referencia local que no debe viajar
        )
        db.add(partida_cat)
        db.add(Producto(
            nombre="Porcelanato local", precio_unitario=45.0,
            imagen="uploads/products/p.png", ficha_tecnica="uploads/products/p.pdf",
            imagenes=json.dumps(["uploads/products/g1.png", "uploads/products/g2.png"]),
        ))
        db.add(Recurso(codigo="MO001", descripcion="Oficial de primera", unidad="hora", categoria="mano_obra", precio=6.5))
        db.flush()

        presupuesto = Presupuesto(
            numero=numero, year=2026, fecha=date(2026, 5, 10),
            titulo="Obra local", cliente=cliente, foto_proyecto="uploads/projects/x.jpg",
        )
        db.add(presupuesto)
        db.flush()
        capitulo = Capitulo(presupuesto_id=presupuesto.id, nombre="CAPÍTULO LOCAL", orden=0)
        db.add(capitulo)
        db.flush()
        item = PresupuestoItem(
            capitulo_id=capitulo.id, nombre="Tabique local", unidad="m2",
            cantidad=0.0, precio_unitario=30.0, partida_catalogo_id=partida_cat.id,
        )
        db.add(item)
        db.flush()
        db.add(Medicion(partida_id=item.id, concepto="Tramo A", cantidad=7.5, orden=0))
        db.add(Medicion(partida_id=item.id, concepto="Tramo B", cantidad=2.5, orden=1))

        proyecto = Proyecto(presupuesto_id=presupuesto.id, nombre="Obra local", estado="en_ejecucion")
        db.add(proyecto)

        if con_demo:
            demo_cliente = Cliente(nombre="Cliente Demo", es_demo=True)
            db.add(demo_cliente)
            db.flush()
            db.add(Presupuesto(
                numero="P-2026-099", year=2026, titulo="Presupuesto demo",
                cliente=demo_cliente, es_demo=True,
            ))
        db.commit()
    engine.dispose()
    return ruta.read_bytes()


def _zip_de_backup(db_bytes, extras=()):
    """Empaqueta un backup en un zip **determinista**.

    ``writestr(nombre, datos)`` graba la fecha/hora actual en cada entrada, así
    que dos llamadas en segundos distintos producen bytes distintos y el
    SHA-256 que el test recalcula deja de coincidir con el que el servidor
    calculó sobre el archivo subido. Se fija la marca de tiempo para que el
    zip sea reproducible y el flujo de análisis→confirmación (que verifica el
    hash) sea estable en CI.
    """
    buf = io.BytesIO()
    fecha_fija = (2026, 1, 1, 0, 0, 0)
    entradas = [("presupuestos.db", db_bytes), ("LEEME_BACKUP.txt", "Copia de seguridad")]
    entradas.extend(extras)
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for nombre, contenido in entradas:
            info = zipfile.ZipInfo(nombre, date_time=fecha_fija)
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, contenido)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Sesión de destino (web) con organización activa
# ---------------------------------------------------------------------------

def _destino(rol="propietario", organizacion_id=7):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    org = Organizacion(id=organizacion_id, nombre="Web", slug="web")
    usuario = Usuario(email="dueno@example.com", nombre="Dueño")
    db.add_all([org, usuario])
    db.flush()
    db.add(Membresia(usuario_id=usuario.id, organizacion_id=org.id, rol=rol))
    db.commit()
    usar_organizacion(db, org.id)
    db.info["rol_membresia"] = rol
    return db


# ---------------------------------------------------------------------------
# Servicio: análisis
# ---------------------------------------------------------------------------

def test_analizar_describe_contenido_y_avisos_sin_escribir(tmp_path):
    contenido = _instalacion_local(tmp_path, con_demo=True)
    db = _destino()
    resumen = analizar_instalacion(db, contenido)

    assert resumen["conteos"]["clientes"] == 1          # el demo no cuenta
    assert resumen["conteos"]["presupuestos"] == 1      # el demo no cuenta
    assert resumen["conteos"]["partidas_catalogo"] == 1
    assert resumen["conteos"]["productos"] == 1
    assert resumen["conteos"]["recursos"] == 1
    assert resumen["conteos"]["proyectos"] == 1
    assert resumen["sha256"] == hashlib.sha256(contenido).hexdigest()
    # Honestidad: avisa de referencias a archivos y de la exclusión de demos.
    texto = " ".join(resumen["advertencias"])
    assert "archivos locales" in texto
    assert "demostración" in texto
    assert "configuración de empresa" in texto.lower()
    # Analizar no escribe nada.
    assert db.query(Cliente).count() == 0
    assert db.query(Presupuesto).count() == 0
    db.close()


def test_analizar_acepta_el_zip_de_backup_y_avisa_de_archivos(tmp_path):
    db_bytes = _instalacion_local(tmp_path)
    contenido = _zip_de_backup(db_bytes, extras=[("uploads/products/foto.png", b"png")])
    db = _destino()
    resumen = analizar_instalacion(db, contenido)
    assert resumen["conteos"]["presupuestos"] == 1
    assert any("no se importan" in a for a in resumen["advertencias"])
    db.close()


def test_analizar_rechaza_archivos_invalidos(tmp_path):
    db = _destino()
    with pytest.raises(ErrorInstalacion):
        analizar_instalacion(db, b"")
    with pytest.raises(ErrorInstalacion):
        analizar_instalacion(db, b"no es sqlite ni zip")
    # Un zip sin presupuestos.db
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("otro.txt", "x")
    with pytest.raises(ErrorInstalacion):
        analizar_instalacion(db, buf.getvalue())
    # Una base SQLite que no es de CotizaT
    otra = tmp_path / "otra.db"
    con = sqlite3.connect(str(otra))
    con.execute("CREATE TABLE cosas (id INTEGER)")
    con.commit()
    con.close()
    with pytest.raises(ErrorInstalacion):
        analizar_instalacion(db, otra.read_bytes())
    db.close()


# ---------------------------------------------------------------------------
# Servicio: importación
# ---------------------------------------------------------------------------

def test_importar_trae_el_grafo_completo_al_espacio_web(tmp_path):
    contenido = _instalacion_local(tmp_path, con_demo=True)
    db = _destino(organizacion_id=7)
    resultado = importar_instalacion(db, contenido)
    db.commit()

    assert resultado["importados"]["clientes"] == 1
    assert resultado["importados"]["presupuestos"] == 1
    assert resultado["importados"]["partidas_catalogo"] == 1
    assert resultado["importados"]["productos"] == 1
    assert resultado["importados"]["recursos"] == 1
    assert resultado["importados"]["proyectos"] == 1

    # Todo pertenece a la organización web y conserva su estructura.
    presupuesto = db.query(Presupuesto).one()
    assert presupuesto.organizacion_id == 7
    assert presupuesto.numero == "P-2026-001"
    assert presupuesto.cliente.nombre == "Cliente Local"
    assert len(presupuesto.capitulos) == 1
    item = presupuesto.capitulos[0].partidas[0]
    assert item.cantidad_total == 10.0          # 7.5 + 2.5 de las mediciones
    assert item.organizacion_id == 7
    # La partida de presupuesto quedó vinculada a la partida de catálogo importada.
    partida_catalogo = db.query(Partida).one()
    assert item.partida_catalogo_id == partida_catalogo.id

    # Los demo no viajaron.
    assert db.query(Cliente).filter(Cliente.nombre == "Cliente Demo").count() == 0
    assert db.query(Presupuesto).filter(Presupuesto.numero == "P-2026-099").count() == 0

    # Las referencias a archivos locales quedaron limpias.
    assert presupuesto.foto_proyecto == ""
    assert partida_catalogo.imagen == ""
    producto = db.query(Producto).one()
    assert producto.imagen == "" and producto.ficha_tecnica == "" and producto.imagenes_lista == []
    assert any("archivos locales" in a for a in resultado["advertencias"])
    db.close()


def test_reimportar_no_duplica_y_avisa_de_conflictos(tmp_path):
    contenido = _instalacion_local(tmp_path)
    db = _destino()
    importar_instalacion(db, contenido)
    db.commit()

    resultado = importar_instalacion(db, contenido)
    db.commit()
    assert resultado["importados"].get("presupuestos") is None
    assert resultado["omitidos"]["presupuestos_conflicto"] == 1
    assert resultado["omitidos"]["partidas_catalogo"] == 1
    assert resultado["omitidos"]["productos"] == 1
    assert any("ya existe" in a for a in resultado["advertencias"])
    assert db.query(Presupuesto).count() == 1
    assert db.query(Partida).count() == 1
    assert db.query(Cliente).count() == 1
    db.close()


def test_importar_verifica_sha256_del_analisis(tmp_path):
    contenido = _instalacion_local(tmp_path)
    db = _destino()
    with pytest.raises(ErrorInstalacion):
        importar_instalacion(db, contenido, sha256_esperado="0" * 64)
    assert db.query(Presupuesto).count() == 0
    db.close()


def test_importar_exige_rol_con_permiso(tmp_path):
    contenido = _instalacion_local(tmp_path)
    for rol in ("lectura", "miembro"):
        db = _destino(rol=rol)
        with pytest.raises(PermisoOrganizacionError):
            importar_instalacion(db, contenido)
        db.rollback()
        assert db.query(Presupuesto).count() == 0
        db.close()


def test_importar_solo_el_espacio_local_dominante(tmp_path):
    """Una base local con restos de otro espacio importa solo el principal."""
    ruta = tmp_path / "presupuestos.db"
    engine = create_engine(f"sqlite:///{ruta}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as db:
        db.add_all([
            Organizacion(id=1, nombre="Principal", slug="principal"),
            Organizacion(id=2, nombre="Resto", slug="resto"),
        ])
        db.flush()
        db.info["organizacion_id"] = 1
        principal = Cliente(nombre="Cliente principal")
        db.add(principal)
        db.add(Partida(nombre="Partida principal", precio_unitario=10.0))
        db.flush()
        db.add(Presupuesto(numero="P-2026-001", year=2026, cliente=principal))
        db.commit()
    with Session() as db:
        db.info["organizacion_id"] = 2
        db.add(Cliente(nombre="Cliente de otro espacio"))
        db.commit()
    engine.dispose()

    db = _destino()
    resumen = analizar_instalacion(db, ruta.read_bytes())
    assert resumen["conteos"]["clientes"] == 1
    assert any("otros espacios" in a for a in resumen["advertencias"])
    resultado = importar_instalacion(db, ruta.read_bytes())
    db.commit()
    assert resultado["importados"]["clientes"] == 1
    assert db.query(Cliente).filter(Cliente.nombre == "Cliente de otro espacio").count() == 0
    db.close()


def test_importar_base_sin_columnas_nuevas(tmp_path):
    """Una instalación de una versión anterior (columnas ausentes) importa igual."""
    contenido = _instalacion_local(tmp_path)
    ruta = tmp_path / "vieja.db"
    ruta.write_bytes(contenido)
    con = sqlite3.connect(str(ruta))
    con.execute("ALTER TABLE presupuestos DROP COLUMN mostrar_garantias")
    con.execute("ALTER TABLE configuracion DROP COLUMN mostrar_garantias_default")
    con.commit()
    con.close()

    db = _destino()
    resultado = importar_instalacion(db, ruta.read_bytes())
    db.commit()
    assert resultado["importados"]["presupuestos"] == 1
    presupuesto = db.query(Presupuesto).one()
    assert presupuesto.mostrar_garantias is False  # valor por defecto del modelo
    db.close()


def test_los_documentos_de_cobro_conservan_totales(tmp_path):
    """El grafo de facturas viaja completo y los totales se mantienen."""
    ruta = tmp_path / "presupuestos.db"
    engine = create_engine(f"sqlite:///{ruta}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as db:
        db.add(Organizacion(id=1, nombre="Local", slug="local"))
        db.flush()
        db.info["organizacion_id"] = 1
        cliente = Cliente(nombre="Cliente Facturado")
        db.add(cliente)
        db.flush()
        from app.models import FacturaCapitulo, FacturaItem
        factura = Factura(
            numero="DC-2026-001", year=2026, impuesto_pct=16.0,
            descuento_pct=0.0, client_id=cliente.id,
        )
        db.add(factura)
        db.flush()
        cap = FacturaCapitulo(factura_id=factura.id, nombre="OBRA", orden=0)
        db.add(cap)
        db.flush()
        db.add(FacturaItem(capitulo_id=cap.id, nombre="Trabajo", cantidad=4, precio_unitario=25.0))
        db.commit()
        total_origen = db.query(Factura).one().total
    engine.dispose()

    db = _destino()
    resultado = importar_instalacion(db, ruta.read_bytes())
    db.commit()
    assert resultado["importados"]["documentos_cobro"] == 1
    factura = db.query(Factura).one()
    assert factura.total == total_origen == 116.0
    db.close()


# ---------------------------------------------------------------------------
# Flujo HTTP de dos pasos (contra la instalación SQLite local de la suite)
# ---------------------------------------------------------------------------

def _cliente_http():
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)


def test_http_flujo_completo_analizar_y_confirmar(tmp_path):
    # Número propio: la instalación demo de la suite ya usa P-2026-001.
    contenido = _instalacion_local(tmp_path, organizacion_id=1, numero="P-1999-777")
    with _cliente_http() as client:
        pantalla = client.get("/configuracion/importar-instalacion")
        assert pantalla.status_code == 200
        assert "Paso 1 de 2" in pantalla.text

        analisis = client.post(
            "/configuracion/importar-instalacion/analizar",
            files={"archivo": ("copia.zip", _zip_de_backup(contenido), "application/zip")},
        )
        assert analisis.status_code == 200
        assert "Paso 2 de 2" in analisis.text
        sha256 = hashlib.sha256(_zip_de_backup(contenido)).hexdigest()
        assert sha256 in analisis.text

        confirmacion = client.post(
            "/configuracion/importar-instalacion/confirmar",
            data={"sha256": sha256, "confirmar": "si"},
            files={"archivo": ("copia.zip", _zip_de_backup(contenido), "application/zip")},
        )
        assert confirmacion.status_code == 200
        assert "Importación completada" in confirmacion.text

        # Los datos quedaron en la instalación de la suite; se limpian al final
        # para no afectar a otras regresiones históricas.
        from app.database import SessionLocal
        with SessionLocal() as db:
            db.info["organizacion_id"] = 1
            presupuesto = (
                db.query(Presupuesto).filter(Presupuesto.numero == "P-1999-777").one()
            )
            assert presupuesto.titulo == "Obra local"
            proyecto = db.query(Proyecto).filter(
                Proyecto.presupuesto_id == presupuesto.id
            ).one()
            db.delete(proyecto)
            db.delete(presupuesto)  # cascadea capítulos, partidas y mediciones
            db.flush()  # los items deben borrarse antes que la partida de catálogo
            cliente_importado = db.query(Cliente).filter(Cliente.nombre == "Cliente Local").one()
            db.delete(cliente_importado)
            db.query(Partida).filter(Partida.nombre == "Tabique local").delete()
            db.query(Producto).filter(Producto.nombre == "Porcelanato local").delete()
            db.query(Recurso).filter(Recurso.codigo == "MO001").delete()
            db.commit()


def test_http_confirmar_sin_casilla_o_con_sha_distinto_no_importa(tmp_path):
    contenido = _instalacion_local(tmp_path, numero="P-1999-778")
    sha256 = hashlib.sha256(contenido).hexdigest()
    with _cliente_http() as client:
        sin_casilla = client.post(
            "/configuracion/importar-instalacion/confirmar",
            data={"sha256": sha256},
            files={"archivo": ("copia.db", contenido, "application/octet-stream")},
            follow_redirects=False,
        )
        assert sin_casilla.status_code == 303
        assert "error=" in sin_casilla.headers["location"]

        otro_sha = client.post(
            "/configuracion/importar-instalacion/confirmar",
            data={"sha256": "f" * 64, "confirmar": "si"},
            files={"archivo": ("copia.db", contenido, "application/octet-stream")},
            follow_redirects=False,
        )
        assert otro_sha.status_code == 303
        assert "error=" in otro_sha.headers["location"]

        sin_analisis = client.post(
            "/configuracion/importar-instalacion/confirmar",
            data={"confirmar": "si"},
            files={"archivo": ("copia.db", contenido, "application/octet-stream")},
            follow_redirects=False,
        )
        assert sin_analisis.status_code == 303
        assert "error=" in sin_analisis.headers["location"]

        from app.database import SessionLocal
        with SessionLocal() as db:
            db.info["organizacion_id"] = 1
            assert (
                db.query(Presupuesto).filter(Presupuesto.numero == "P-1999-778").count()
                == 0
            )
