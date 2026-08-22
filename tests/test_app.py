import asyncio
import json
import os
import re
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.datastructures import FormData

from app.database import Base
from app.main import (
    TEMPLATES,
    _leer_formulario_presupuesto,
    app,
    confirmar_importacion_presupuesto,
    guardar_partida_desde_presupuesto,
)
from app.models import (
    BorradorPresupuesto,
    Capitulo,
    Cliente,
    Medicion,
    Organizacion,
    Partida,
    Presupuesto,
    PresupuestoItem,
    PresupuestoItemProducto,
)


def test_all_templates_syntax():
    """Verifica que todas las plantillas Jinja2 compilen sin errores de sintaxis."""
    env = TEMPLATES.env
    templates_dir = "app/templates"
    for root, _, files in os.walk(templates_dir):
        for f in files:
            if f.endswith(".html"):
                rel_path = os.path.relpath(os.path.join(root, f), templates_dir)
                try:
                    env.get_template(rel_path)
                except Exception as e:
                    pytest.fail(f"Error de sintaxis en plantilla {rel_path}: {e}")


def test_get_routes():
    """Verifica que las rutas principales de la aplicación respondan con 200 OK."""
    with TestClient(app) as client:
        routes = [
            "/",
            "/reportes",
            "/buscar",
            "/presupuestos",
            "/proyectos",
            "/facturas",
            "/partidas",
            "/recursos",
            "/productos",
            "/clientes",
            "/plantillas",
            "/configuracion",
        ]
        for route in routes:
            resp = client.get(route)
            assert resp.status_code == 200, f"Error en la ruta {route}: {resp.status_code} {resp.text[:200]}"


def test_compare_versions_routing():
    """Verifica que la ruta de comparar versiones no sea bloqueada por la ruta con ID entero."""
    with TestClient(app) as client:
        resp = client.get("/presupuestos/1/versiones/comparar?a=1&b=2", follow_redirects=False)
        # Debe redirigir (303) cuando no existen las versiones en la base de datos demo,
        # no devolver 422 (int_parsing error de version_id).
        assert resp.status_code in (200, 303), f"Código inesperado en comparar versiones: {resp.status_code}"


def test_editor_incluye_importador_excel_embebido():
    """El usuario puede iniciar la carga desde el editor, sin ir a Partidas."""
    with TestClient(app) as client:
        resp = client.get("/presupuestos/nuevo")
        assert resp.status_code == 200
        assert 'id="btn-subir-excel"' in resp.text
        assert 'id="modal-importar-excel"' in resp.text
        assert 'id="modal-editor-partida"' in resp.text
        assert "data-partida-catalogo-editor" in resp.text
        assert "/static/js/editor/importador_excel.js" in resp.text
        assert "/static/js/editor/partida_modal.js" in resp.text


def test_catalogo_y_presupuesto_comparten_editor_completo_de_partida():
    with TestClient(app) as client:
        catalogo = client.get("/partidas/nueva")
        presupuesto = client.get("/presupuestos/nuevo")
        assert catalogo.status_code == presupuesto.status_code == 200
        campos = [
            'name="subcategoria"', 'name="codigo_externo"',
            'name="proveedor"', 'name="tiempo_estimado_horas"',
            'name="notas_tecnicas"', 'data-role="tabla-descomposicion-catalogo"',
        ]
        for campo in campos:
            assert campo in catalogo.text
            assert campo in presupuesto.text
        assert "/static/js/partida_catalogo_editor.js" in catalogo.text
        assert "/static/js/partida_catalogo_editor.js" in presupuesto.text


def test_guardar_partida_desde_presupuesto_usa_ficha_y_descomposicion_completas():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        formulario = FormData([
            ("nombre", "Partida completa desde presupuesto"),
            ("categoria", "Revestimientos"),
            ("subcategoria", "Morteros"),
            ("unidad", "m2"),
            ("codigo_externo", "RBE-TEST"),
            ("codigo_interno", "INT-09"),
            ("descripcion", "Descripción técnica completa"),
            ("precio_unitario", "38,50"),
            ("proveedor", "Proveedor de prueba"),
            ("tiempo_estimado_horas", "2,5"),
            ("rendimiento", "12 m2/día"),
            ("desperdicio_recomendado_pct", "4"),
            ("notas_tecnicas", "Aplicar sobre soporte limpio"),
            ("d_categoria", "materiales"),
            ("d_codigo", "mt001"),
            ("d_unidad", "kg"),
            ("d_descripcion", "Mortero"),
            ("d_rendimiento", "2"),
            ("d_precio", "3,25"),
        ])

        class PeticionForm:
            async def form(self):
                return formulario

        respuesta = asyncio.run(guardar_partida_desde_presupuesto(PeticionForm(), db))
        assert respuesta["ok"] is True
        datos = respuesta["partida"]
        assert datos["subcategoria"] == "Morteros"
        assert datos["proveedor"] == "Proveedor de prueba"
        assert datos["tiempo_estimado_horas"] == pytest.approx(2.5)
        assert datos["coste_materiales"] == pytest.approx(6.5)
        assert datos["descomposicion"]["filas"][0]["codigo"] == "mt001"
        guardada = db.get(Partida, datos["id"])
        assert guardada.codigo_externo == "RBE-TEST"
        assert guardada.notas_tecnicas == "Aplicar sobre soporte limpio"
    finally:
        db.close()
        engine.dispose()


def test_actualizar_precio_partida_desde_presupuesto_no_modifica_linea_guardada():
    """Al actualizar el catálogo, el presupuesto conserva su precio copiado."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        cliente = Cliente(nombre="Cliente prueba")
        maestra = Partida(nombre="Pintura económica", precio_unitario=10, unidad="m2", categoria="Pintura")
        db.add_all([cliente, maestra])
        db.commit()
        presupuesto = Presupuesto(
            numero="PRE-PRICE-001", year=date.today().year, fecha=date.today(),
            titulo="Prueba precio", client_id=cliente.id, moneda="USD", impuesto_pct=16,
        )
        capitulo = Capitulo(nombre="CAPÍTULO", orden=1)
        linea = PresupuestoItem(
            nombre=maestra.nombre, unidad=maestra.unidad, cantidad=2,
            precio_unitario=10, orden=1, partida_catalogo_id=maestra.id,
        )
        capitulo.partidas.append(linea)
        presupuesto.capitulos.append(capitulo)
        db.add(presupuesto)
        db.commit()

        class PeticionJSON:
            async def json(self):
                return {"precio": "12,50"}

        from app.main import actualizar_precio_partida_desde_presupuesto

        respuesta = asyncio.run(actualizar_precio_partida_desde_presupuesto(maestra.id, PeticionJSON(), db))
        assert respuesta["ok"] is True
        assert respuesta["partida"]["precio"] == pytest.approx(12.5)
        db.expire_all()
        assert db.get(Partida, maestra.id).precio_unitario == pytest.approx(12.5)
        assert db.get(PresupuestoItem, linea.id).precio_unitario == pytest.approx(10)
    finally:
        db.close()
        engine.dispose()


def test_eliminar_partida_del_catalogo_desvincula_lineas_de_presupuesto():
    """Borrar una partida del catálogo no debe borrar presupuestos.

    ``presupuesto_items.partida_catalogo_id`` es solo el origen de la copia;
    el precio ya vive en la línea. Al eliminar la partida maestra, las líneas
    que la referenciaban deben sobrevivir con el vínculo a NULL (en vez de
    fallar con ForeignKeyViolation como ocurría en producción).
    """
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)

    @event.listens_for(engine, "connect")
    def _fk_on(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        organizacion = Organizacion(nombre="Empresa de pruebas", slug="empresa-de-pruebas")
        db.add(organizacion)
        db.flush()  # id=1; los TenantMixin usan organizacion_id=1 por defecto
        cliente = Cliente(nombre="Cliente prueba")
        maestra = Partida(nombre="Solado porcelanato", precio_unitario=30, unidad="m2", categoria="Pavimentos")
        db.add_all([cliente, maestra])
        db.commit()
        presupuesto = Presupuesto(
            numero="PRE-DEL-001", year=date.today().year, fecha=date.today(),
            titulo="Prueba borrado", client_id=cliente.id, moneda="USD", impuesto_pct=16,
        )
        capitulo = Capitulo(nombre="CAPÍTULO", orden=1)
        linea = PresupuestoItem(
            nombre=maestra.nombre, unidad=maestra.unidad, cantidad=1,
            precio_unitario=30, orden=1, partida_catalogo_id=maestra.id,
        )
        capitulo.partidas.append(linea)
        presupuesto.capitulos.append(capitulo)
        db.add(presupuesto)
        db.commit()

        from app.main import eliminar_partida

        respuesta = eliminar_partida(maestra.id, db)
        assert respuesta.status_code == 303
        db.expire_all()
        assert db.get(Partida, maestra.id) is None
        item = db.get(PresupuestoItem, linea.id)
        assert item is not None
        assert item.partida_catalogo_id is None
    finally:
        db.close()
        engine.dispose()


def test_eliminar_partida_oficial_la_oculta_y_permite_restaurarla():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        db.add(Organizacion(nombre="Empresa", slug="empresa-visibilidad"))
        db.flush()
        cliente = Cliente(nombre="Cliente")
        oficial = Partida(
            nombre="Partida oficial",
            precio_unitario=30,
            catalogo_uid="OFICIAL-001",
            es_oficial=True,
            version_catalogo=2,
        )
        db.add_all([cliente, oficial])
        db.commit()
        presupuesto = Presupuesto(
            numero="PRE-HIDE-001", year=date.today().year, fecha=date.today(),
            client_id=cliente.id,
        )
        capitulo = Capitulo(nombre="CAPÍTULO", orden=1)
        linea = PresupuestoItem(
            nombre=oficial.nombre, unidad="ud", cantidad=1,
            precio_unitario=30, orden=1, partida_catalogo_id=oficial.id,
        )
        capitulo.partidas.append(linea)
        presupuesto.capitulos.append(capitulo)
        db.add(presupuesto)
        db.commit()

        from app.main import eliminar_partida, restaurar_partida

        respuesta = eliminar_partida(oficial.id, db)
        assert respuesta.status_code == 303
        db.expire_all()
        guardada = db.get(Partida, oficial.id)
        assert guardada is not None
        assert guardada.oculta is True
        assert db.get(PresupuestoItem, linea.id).partida_catalogo_id == oficial.id

        restaurada = restaurar_partida(oficial.id, db)
        assert restaurada.status_code == 303
        db.expire_all()
        assert db.get(Partida, oficial.id).oculta is False
    finally:
        db.close()
        engine.dispose()


def test_importacion_inline_persiste_presupuesto_y_catalogo_sin_redireccion():
    """Confirmar inline devuelve filas para el DOM y guarda ambas copias."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        cliente = Cliente(nombre="Cliente importación inline")
        db.add(cliente)
        db.flush()
        presupuesto = Presupuesto(
            numero="PRE-TEST-001",
            year=2026,
            fecha=date(2026, 8, 8),
            titulo="Prueba inline",
            client_id=cliente.id,
        )
        db.add(presupuesto)
        db.commit()

        class PeticionJSON:
            async def json(self):
                return {
                    "modo": "editor_inline",
                    "formato": "tabular",
                    "presupuesto_destino_id": presupuesto.id,
                    "primera_fila": 2,
                    "mapeo": {
                        "capitulo": 0,
                        "partida": 1,
                        "descripcion": 2,
                        "unidad": 3,
                        "cantidad": 4,
                        "precio": 5,
                        "categoria": 6,
                        "tipo_partida": None,
                    },
                    "filas": [[
                        "PINTURA",
                        "Pintura plástica interior inline",
                        "Dos manos sobre paramentos",
                        "m2",
                        "12,5",
                        "8,40",
                        "Pintura",
                    ]],
                }

        respuesta = asyncio.run(confirmar_importacion_presupuesto(PeticionJSON(), db))
        assert respuesta["ok"] is True
        assert respuesta["permanecer_en_editor"] is True
        assert respuesta["presupuesto_guardado"] is True
        assert "url" not in respuesta
        assert respuesta["capitulos"][0]["nombre"] == "PINTURA"
        assert respuesta["capitulos"][0]["partidas"][0]["partida_id"]

        db.expire_all()
        guardado = db.get(Presupuesto, presupuesto.id)
        assert len(guardado.capitulos) == 1
        assert guardado.capitulos[0].partidas[0].nombre == "Pintura plástica interior inline"
        catalogo = db.query(Partida).filter(Partida.nombre == "Pintura plástica interior inline").one()
        assert catalogo.precio_unitario == pytest.approx(8.4)
        assert catalogo.usos == 1
    finally:
        db.close()
        engine.dispose()


def test_estructura_json_conserva_metadatos_de_excel_en_formulario():
    """La estructura dinámica no se desalineará al guardar tras importar."""
    estructura = [{
        "nombre": "PARTIDAS IMPORTADAS",
        "partidas": [{
            "partida_id": "",
            "codigo_externo": "DPT020",
            "nombre": "Demolición de tabique",
            "unidad": "m2",
            "cantidad": 1,
            "precio": 17.25,
            "descripcion": "Partida importada",
            "tipo_partida": "included",
            "seleccionada": True,
            "mediciones": [],
            "descomposicion_meta": {
                "origen": "cype",
                "archivo_origen": "importaciones/prueba.xlsx",
                "nombre_archivo_origen": "DPT020.xlsx",
            },
            "descomposicion": {"origen": "cype", "filas": [{
                "tipo": "recurso",
                "codigo": "mo020",
                "unidad": "h",
                "descripcion": "Oficial",
                "rendimiento": 1,
                "precio": 17.25,
                "celdas": ["mo020", "h"],
                "formulas": {},
            }]},
        }],
    }]
    capitulos, partidas = _leer_formulario_presupuesto(FormData([
        ("estructura_json", json.dumps(estructura)),
    ]))
    assert capitulos[0]["nombre"] == "PARTIDAS IMPORTADAS"
    assert partidas[0]["codigo_externo"] == "DPT020"
    assert partidas[0]["descomposicion_meta"]["origen"] == "cype"
    assert partidas[0]["descomposicion"][0]["codigo"] == "mo020"


def test_autosave_borrador_presupuesto_roundtrip():
    """El autoguardado del servidor persiste y devuelve el borrador, y el
    guardado completo del formulario lo elimina."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        cliente = Cliente(nombre="Cliente autosave")
        db.add(cliente)
        db.flush()
        presupuesto = Presupuesto(
            numero="PRE-AUTO-001", year=date.today().year, fecha=date.today(),
            titulo="Autosave", client_id=cliente.id,
        )
        db.add(presupuesto)
        db.commit()

        from app.main import guardar_borrador_presupuesto, leer_borrador_presupuesto

        capitulos = [{"nombre": "CAP 1", "partidas": [{"nombre": "Partida A", "precio": 5}]}]

        class PeticionJSON:
            async def json(self):
                return {"capitulos": capitulos, "ts": 1000}

        respuesta = asyncio.run(guardar_borrador_presupuesto(presupuesto.id, PeticionJSON(), db))
        assert respuesta["ok"] is True

        leido = leer_borrador_presupuesto(presupuesto.id, db)
        assert leido["ok"] is True
        assert leido["capitulos"] == capitulos
        assert leido["ts"] == 1000

        # El borrador no debe tocar el presupuesto real
        db.expire_all()
        guardado = db.get(Presupuesto, presupuesto.id)
        assert guardado.titulo == "Autosave"
        assert len(guardado.capitulos) == 0

        # Guardado completo: se borra el borrador
        from app.main import actualizar_presupuesto

        class PeticionForm:
            async def form(self):
                return FormData([
                    ("client_id", str(cliente.id)),
                    ("titulo", "Autosave"),
                    ("fecha", date.today().isoformat()),
                    ("validez_dias", "30"),
                    ("moneda", "USD"),
                    ("impuesto_pct", "16"),
                    ("descuento_pct", "0"),
                    ("estado", "borrador"),
                    ("estructura_json", json.dumps([{
                        "nombre": "CAP 1",
                        "partidas": [{"nombre": "Partida A", "precio": 5, "cantidad": 1, "mediciones": []}],
                    }])),
                ])

        asyncio.run(actualizar_presupuesto(presupuesto.id, PeticionForm(), db))
        db.expire_all()
        from app.models import BorradorPresupuesto
        assert db.query(BorradorPresupuesto).filter_by(presupuesto_id=presupuesto.id).first() is None
    finally:
        db.close()
        engine.dispose()


def test_catalogo_guardado_desde_presupuesto_usa_precio_base_sin_producto():
    """Al crear un presupuesto, la partida nueva del catálogo guarda SOLO el
    precio base (sin el producto asociado), para que no se duplique el precio
    al reutilizarla."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        cliente = Cliente(nombre="Cliente catálogo base")
        db.add(cliente)
        db.commit()

        from app.main import crear_presupuesto

        estructura = [{
            "nombre": "CAPÍTULO 1",
            "partidas": [{
                "nombre": "Rodapié lacado",
                "unidad": "ml",
                "precio": 12.5,          # base 10 + producto 2.5
                "cantidad": 1,
                "prod_nombre": "Rodapié MDF 8cm",
                "prod_precio": "2.5",
                "prod_coste": "1.2",
                "prod_unidad": "ml",
                "mediciones": [],
            }],
        }]

        class PeticionForm:
            async def form(self):
                return FormData([
                    ("client_id", str(cliente.id)),
                    ("titulo", "Catálogo base"),
                    ("fecha", date.today().isoformat()),
                    ("validez_dias", "30"),
                    ("moneda", "USD"),
                    ("impuesto_pct", "16"),
                    ("descuento_pct", "0"),
                    ("estado", "borrador"),
                    ("estructura_json", json.dumps(estructura)),
                ])

        respuesta = asyncio.run(crear_presupuesto(PeticionForm(), db))
        assert respuesta.status_code == 303

        db.expire_all()
        partida_catalogo = db.query(Partida).filter(Partida.nombre == "Rodapié lacado").first()
        assert partida_catalogo is not None
        assert partida_catalogo.precio_unitario == pytest.approx(10.0)

        # La línea del presupuesto conserva su total (base + producto)
        linea = db.query(PresupuestoItem).filter(PresupuestoItem.nombre == "Rodapié lacado").first()
        assert linea.precio_unitario == pytest.approx(12.5)
        assert linea.producto_precio == pytest.approx(2.5)
    finally:
        db.close()
        engine.dispose()


def test_redondeo_consistente_importes_capitulos_y_totales():
    """El importe de partida, el subtotal de capítulo y los totales deben
    usar la misma regla (ROUND_HALF_UP) y coincidir al céntimo, incluso con
    precios de 3 decimales que antes divergían ±0.02."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        cliente = Cliente(nombre="Cliente redondeo")
        db.add(cliente)
        db.flush()
        presupuesto = Presupuesto(
            numero="PRE-RED-001", year=date.today().year, fecha=date.today(),
            titulo="Redondeo", client_id=cliente.id, moneda="USD",
            impuesto_pct=16, descuento_pct=0,
        )
        cap = Capitulo(nombre="CAP", orden=1)
        presupuesto.capitulos.append(cap)
        # Casos que antes divergían: 3 × 0.335 y 3 × 5.005
        cap.partidas.append(PresupuestoItem(nombre="A", unidad="ud", cantidad=3, precio_unitario=0.335, orden=1))
        cap.partidas.append(PresupuestoItem(nombre="B", unidad="ud", cantidad=3, precio_unitario=5.005, orden=2))
        db.add(presupuesto)
        db.commit()

        db.expire_all()
        p = db.get(Presupuesto, presupuesto.id)
        importes = [part.importe for part in p.todas_partidas]
        # money(3 × 0.335) = 1.01 (ROUND_HALF_UP) · money(3 × 5.005) = 15.02
        assert importes[0] == pytest.approx(1.01, abs=0.001)
        assert importes[1] == pytest.approx(15.02, abs=0.001)
        # El subtotal del capítulo = suma de los importes redondeados
        assert p.capitulos[0].subtotal == pytest.approx(16.03, abs=0.001)
        assert p.subtotal == pytest.approx(16.03, abs=0.001)
        assert p.total == pytest.approx(round(16.03 * 1.16, 2), abs=0.001)
    finally:
        db.close()
        engine.dispose()


def test_factura_solo_incluye_partidas_del_total():
    """La factura generada desde un presupuesto aprobado debe facturar
    exactamente el total del presupuesto: opcionales/alternativas NO
    seleccionadas y excluidas no se facturan."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        cliente = Cliente(nombre="Cliente factura")
        db.add(cliente)
        db.flush()
        presupuesto = Presupuesto(
            numero="PRE-FAC-001", year=date.today().year, fecha=date.today(),
            titulo="Factura", client_id=cliente.id, moneda="USD",
            impuesto_pct=16, descuento_pct=0, estado="aprobado",
            usar_funciones_avanzadas=True,
        )
        cap = Capitulo(nombre="CAP", orden=1)
        presupuesto.capitulos.append(cap)
        cap.partidas.append(PresupuestoItem(nombre="Incluida", unidad="ud", cantidad=2, precio_unitario=100, orden=1,
                                            tipo_partida="included", seleccionada=True))
        cap.partidas.append(PresupuestoItem(nombre="Opcional", unidad="ud", cantidad=1, precio_unitario=50, orden=2,
                                            tipo_partida="optional", seleccionada=False))
        cap.partidas.append(PresupuestoItem(nombre="Alternativa", unidad="ud", cantidad=1, precio_unitario=30, orden=3,
                                            tipo_partida="alternative", seleccionada=False))
        cap.partidas.append(PresupuestoItem(nombre="Excluida", unidad="ud", cantidad=1, precio_unitario=999, orden=4,
                                            tipo_partida="excluded", seleccionada=False))
        db.add(presupuesto)
        db.commit()

        from app.main import crear_factura
        r = crear_factura(presupuesto.id, db)
        assert r.status_code == 303
        db.expire_all()
        from app.models import Factura
        factura = db.query(Factura).order_by(Factura.id.desc()).first()
        assert factura.numero.startswith("DC-")
        assert [i.nombre for i in factura.todas_partidas] == ["Incluida"]
        assert factura.total == pytest.approx(presupuesto.total, abs=0.011)
    finally:
        db.close()
        engine.dispose()


def test_medicion_en_cero_no_cae_a_cantidad_directa():
    """Una medición con cantidad 0 hace que la cantidad total sea 0 (suma de
    mediciones), nunca la cantidad directa."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        cliente = Cliente(nombre="Cliente medición cero")
        db.add(cliente)
        db.flush()
        presupuesto = Presupuesto(
            numero="PRE-MED-001", year=date.today().year, fecha=date.today(),
            titulo="Medición cero", client_id=cliente.id, moneda="USD",
        )
        cap = Capitulo(nombre="CAP", orden=1)
        presupuesto.capitulos.append(cap)
        partida = PresupuestoItem(nombre="Medición cero", unidad="ud", cantidad=5, precio_unitario=100, orden=1)
        from app.models import Medicion
        partida.mediciones.append(Medicion(concepto="Zona", cantidad=0, orden=1))
        cap.partidas.append(partida)
        db.add(presupuesto)
        db.commit()
        db.expire_all()
        p = db.get(Presupuesto, presupuesto.id)
        assert p.todas_partidas[0].cantidad_total == 0.0
        assert p.todas_partidas[0].importe == 0.0
        assert p.total == 0.0
    finally:
        db.close()
        engine.dispose()


def test_parseo_numero_local_robusto():
    """_f acepta formatos con separador de miles y coma decimal."""
    from app.main import _f
    assert _f("12,50") == pytest.approx(12.5)
    assert _f("1.234,56") == pytest.approx(1234.56)
    assert _f("1,234.56") == pytest.approx(1234.56)
    assert _f("1234.56") == pytest.approx(1234.56)
    assert _f("1.234") == pytest.approx(1.234)
    assert _f("", 7.0) == 7.0
    assert _f("abc", 7.0) == 7.0


def test_partida_coste_property():
    """Verifica que el modelo Partida calcule el coste como suma de sus costes directos."""
    p = Partida(
        nombre="Partida test coste",
        coste_materiales=10.5,
        coste_mano_obra=20.0,
        coste_complementarios=2.5,
        coste_otros=1.0,
    )
    assert p.coste == pytest.approx(34.0)


def test_editar_presupuesto_form_render():
    """Verifica que /presupuestos/{id}/editar renderice correctamente sin Internal Server Error."""
    with TestClient(app) as client:
        # GET /presupuestos/1/editar
        resp = client.get("/presupuestos/1/editar")
        assert resp.status_code == 200
        assert "datos-catalogo" in resp.text
        assert "datos-productos" in resp.text
        assert "Guardar cambios" in resp.text or "guardar" in resp.text.lower()


def test_editor_envia_indice_ligero_y_carga_ficha_bajo_demanda():
    with TestClient(app) as client:
        resp = client.get("/presupuestos/nuevo")
        assert resp.status_code == 200
        # El HTML ya no embebe las ~3.000 partidas: eso era el 504 de Vercel.
        match = re.search(
            r'id="datos-catalogo"[^>]*>\s*(.*?)\s*</script>',
            resp.text,
            re.DOTALL,
        )
        assert match
        assert json.loads(match.group(1)) == []
        assert "CATALOGO_DATOS_URL" in resp.text
        assert "/presupuestos/editor/datos" in resp.text
        assert len(resp.content) < 500_000

        datos = client.get("/presupuestos/editor/datos")
        assert datos.status_code == 200
        catalogo = datos.json()["partidas"]
        assert catalogo
        assert "buscable" in catalogo[0]
        assert "descripcion" not in catalogo[0]
        assert "descomposicion" not in catalogo[0]

        ficha = client.get(f"/partidas/{catalogo[0]['id']}/ficha")
        assert ficha.status_code == 200
        payload = ficha.json()
        assert payload["ok"]
        assert "descripcion" in payload["partida"]
        assert "descomposicion" in payload["partida"]


def test_busqueda_remota_cubre_descripcion_y_catalogo_se_pagina():
    with TestClient(app) as client:
        busqueda = client.get(
            "/partidas/api/buscar",
            params={"q": "distanciómetro", "limite": 10},
        )
        assert busqueda.status_code == 200
        data = busqueda.json()
        assert data["ok"]
        assert any("Levantamiento" in p["nombre"] for p in data["resultados"])
        sinonimo = client.get(
            "/partidas/api/buscar", params={"q": "hormigón", "limite": 20}
        ).json()
        assert sinonimo["resultados"]
        assert any("concreto" in p["nombre"].lower() for p in sinonimo["resultados"])
        metrica = client.post(
            "/partidas/api/busqueda-sin-resultados",
            json={"q": "partida técnica inexistente"},
        )
        assert metrica.status_code == 200
        assert metrica.json()["ok"]

        # La navegación monta el árbol completo contraído y carga las filas de
        # cada subcapítulo bajo demanda: la primera respuesta no trae filas,
        # sino el árbol (18 capítulos, 172 subcapítulos) con sus totales.
        listado = client.get("/partidas")
        assert listado.status_code == 200
        assert listado.text.count('class="partida-tr"') == 0
        assert listado.text.count('data-lazy="1"') == 172
        assert "18 Rehabilitación energética" in listado.text


def test_partida_oculta_desaparece_del_editor_y_aparece_en_su_vista():
    with TestClient(app) as client:
        encontrada = client.get(
            "/partidas/api/buscar", params={"q": "Levantamiento de medidas"}
        ).json()["resultados"][0]
        partida_id = encontrada["id"]
        nombre = encontrada["nombre"]
        try:
            respuesta = client.post(
                f"/partidas/{partida_id}/eliminar", follow_redirects=False
            )
            assert respuesta.status_code == 303
            resultados = client.get(
                "/partidas/api/buscar", params={"q": "Levantamiento de medidas"}
            ).json()["resultados"]
            assert all(p["id"] != partida_id for p in resultados)
            # La partida oculta reaparece en su subcapítulo al pedir las filas
            # con vista=ocultas (la navegación las carga bajo demanda).
            ocultas = client.get(
                "/partidas/api/filas",
                params={
                    "categoria": encontrada["categoria"],
                    "subcategoria": encontrada["subcategoria"],
                    "vista": "ocultas",
                },
            )
            assert ocultas.status_code == 200
            assert nombre in ocultas.text
            indice = client.get("/presupuestos/editor/datos").json()["partidas"]
            assert all(p["id"] != partida_id for p in indice)
        finally:
            client.post(f"/partidas/{partida_id}/restaurar")


def test_flujo_completo_crear_y_modificar_presupuesto():
    """Prueba creación, edición, exportación a PDF y cambio de estado de un presupuesto."""
    with TestClient(app) as client:
        estructura = [{
            "nombre": "CAPÍTULO TEST",
            "partidas": [{
                "partida_id": "",
                "nombre": "Partida de prueba test",
                "descripcion": "Descripción partida test",
                "unidad": "m2",
                "cantidad": 10,
                "precio": 50.0,
                "tipo_partida": "included",
                "seleccionada": True,
                "coste_materiales": 15.0,
                "coste_mano_obra": 15.0,
                "coste_complementarios": 2.0,
                "coste_otros": 0.0,
                "mediciones": [
                    {"concepto": "Tramo 1", "cantidad": 6},
                    {"concepto": "Tramo 2", "cantidad": 4},
                ],
            }],
        }]
        # Crear presupuesto
        resp_nuevo = client.post(
            "/presupuestos/nuevo",
            data={
                "client_id": "1",
                "titulo": "Presupuesto Test Automatizado",
                "fecha": date.today().isoformat(),
                "validez_dias": "30",
                "moneda": "USD",
                "impuesto_pct": "16",
                "descuento_pct": "0",
                "estado": "borrador",
                "estructura_json": json.dumps(estructura),
            },
            follow_redirects=False,
        )
        assert resp_nuevo.status_code == 303
        loc = resp_nuevo.headers["location"]
        pid = loc.split("?")[0].split("/")[-1]

        # Editar formulario GET
        resp_get_edit = client.get(f"/presupuestos/{pid}/editar")
        assert resp_get_edit.status_code == 200
        assert "Presupuesto Test Automatizado" in resp_get_edit.text

        # Modificar presupuesto POST
        resp_post_edit = client.post(
            f"/presupuestos/{pid}/editar",
            data={
                "client_id": "1",
                "titulo": "Presupuesto Test Modificado",
                "fecha": date.today().isoformat(),
                "validez_dias": "45",
                "moneda": "USD",
                "impuesto_pct": "16",
                "descuento_pct": "5",
                "estado": "borrador",
                "estructura_json": json.dumps(estructura),
            },
            follow_redirects=False,
        )
        assert resp_post_edit.status_code == 303

        # Ver detalle
        resp_detail = client.get(f"/presupuestos/{pid}")
        assert resp_detail.status_code == 200
        assert "Presupuesto Test Modificado" in resp_detail.text

        # PDF
        resp_pdf = client.get(f"/presupuestos/{pid}/pdf")
        assert resp_pdf.status_code == 200
        assert resp_pdf.headers["content-type"] == "application/pdf"


def test_crear_presupuesto_con_varias_opciones_de_producto():
    """Una partida puede tener varios productos a elegir. El servidor debe
    persistirlos en la tabla presupuesto_item_productos y mantener la
    coherencia (un solo marcado como seleccionado)."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        cliente = Cliente(nombre="Cliente MultiProducto")
        db.add(cliente)
        db.flush()
        presupuesto = Presupuesto(
            numero="P-MULTI-001", year=date.today().year, fecha=date.today(),
            titulo="Multi producto", client_id=cliente.id,
        )
        db.add(presupuesto)
        db.commit()
        db.refresh(presupuesto)

        # Estructura con dos opciones: la segunda marcada como seleccionada
        estructura = [{
            "nombre": "PISOS",
            "partidas": [
                {
                    "nombre": "Pavimento porcelanato",
                    "precio": 100.0,
                    "cantidad": 10.0,
                    "unidad": "m2",
                    "descripcion": "Pavimento de interior",
                    "productos_opciones": [
                        {"nombre": "Porcelanato A", "precio": 95.0, "unidad": "m2", "seleccionado": False, "orden": 0},
                        {"nombre": "Porcelanato B", "precio": 150.0, "unidad": "m2", "seleccionado": True, "orden": 1},
                        # Una opción con nombre vacío: NO debe persistirse
                        {"nombre": "", "precio": 999.0, "seleccionado": False, "orden": 2},
                    ],
                    "mediciones": [],
                    "descomposicion": [],
                }
            ],
        }]

        class PeticionForm:
            def __init__(self, datos):
                self._datos = datos
            async def form(self):
                return FormData([
                    ("client_id", str(cliente.id)),
                    ("titulo", "Multi producto"),
                    ("fecha", date.today().isoformat()),
                    ("validez_dias", "30"),
                    ("moneda", "USD"),
                    ("impuesto_pct", "16"),
                    ("descuento_pct", "0"),
                    ("estado", "borrador"),
                    ("estructura_json", json.dumps(self._datos)),
                ])

        from app.main import actualizar_presupuesto
        asyncio.run(actualizar_presupuesto(presupuesto.id, PeticionForm(estructura), db))
        db.expire_all()
        db.refresh(presupuesto)
        assert len(presupuesto.capitulos) == 1
        assert len(presupuesto.capitulos[0].partidas) == 1
        partida = presupuesto.capitulos[0].partidas[0]
        # Solo se guardan las opciones con nombre no vacío
        assert len(partida.productos_opciones) == 2, partida.productos_opciones
        nombres = [op.nombre for op in partida.productos_opciones]
        assert "Porcelanato A" in nombres
        assert "Porcelanato B" in nombres
        # Solo una está marcada como seleccionada
        marcados = [op for op in partida.productos_opciones if op.seleccionado]
        assert len(marcados) == 1
        assert marcados[0].nombre == "Porcelanato B"
        # La partida expone las propiedades auxiliares
        assert partida.tiene_producto
        assert partida.producto_seleccionado is not None
        assert partida.producto_seleccionado.nombre == "Porcelanato B"
        # productos_multiples: el PDF debe listar TODAS las alternativas para
        # que el cliente pueda compararlas y (en el PDF interactivo) pulsar
        # sobre cualquiera de ellas para recalcular el precio.
        assert len(partida.productos_multiples) == 2
        assert [op.nombre for op in partida.productos_multiples] == [
            "Porcelanato A", "Porcelanato B",
        ]
        # …y la marcada se identifica por su índice dentro de esa lista.
        assert partida.indice_producto_elegido == 1
    finally:
        db.close()
        engine.dispose()


def test_solo_una_opcion_puede_estar_seleccionada():
    """Si por error llegan varias opciones marcadas, el servidor deja solo la
    primera marcada y desmarca el resto (consistencia visual en el PDF)."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        cliente = Cliente(nombre="Cliente Sanity")
        db.add(cliente)
        db.flush()
        presupuesto = Presupuesto(
            numero="P-SANITY-001", year=date.today().year, fecha=date.today(),
            titulo="Sanity", client_id=cliente.id,
        )
        db.add(presupuesto)
        db.commit()
        db.refresh(presupuesto)

        estructura = [{
            "nombre": "BAÑO",
            "partidas": [
                {
                    "nombre": "Revestimiento",
                    "precio": 50.0, "cantidad": 5.0, "unidad": "m2",
                    "productos_opciones": [
                        {"nombre": "Opcion A", "precio": 40, "seleccionado": True, "orden": 0},
                        {"nombre": "Opcion B", "precio": 60, "seleccionado": True, "orden": 1},
                        {"nombre": "Opcion C", "precio": 80, "seleccionado": True, "orden": 2},
                    ],
                    "mediciones": [], "descomposicion": [],
                }
            ],
        }]

        class PeticionForm:
            def __init__(self, datos): self._datos = datos
            async def form(self):
                return FormData([
                    ("client_id", str(cliente.id)),
                    ("titulo", "Sanity"),
                    ("fecha", date.today().isoformat()),
                    ("validez_dias", "30"),
                    ("moneda", "USD"),
                    ("impuesto_pct", "16"),
                    ("descuento_pct", "0"),
                    ("estado", "borrador"),
                    ("estructura_json", json.dumps(self._datos)),
                ])

        from app.main import actualizar_presupuesto
        asyncio.run(actualizar_presupuesto(presupuesto.id, PeticionForm(estructura), db))
        db.expire_all()
        db.refresh(presupuesto)
        partida = presupuesto.capitulos[0].partidas[0]
        marcados = [op for op in partida.productos_opciones if op.seleccionado]
        assert len(marcados) == 1
        # El orden debe ser el de la primera marcada
        assert marcados[0].nombre == "Opcion A"
    finally:
        db.close()
        engine.dispose()


def test_autosave_borrador_acepta_capitulos_vacios():
    """Si por algún motivo llegan capítulos vacíos al autoguardado, el
    servidor debe aceptarlos sin error (la edición puede estar a medias)."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        cliente = Cliente(nombre="Cliente Vacio")
        db.add(cliente)
        db.flush()
        presupuesto = Presupuesto(
            numero="P-VACIO-001", year=date.today().year, fecha=date.today(),
            titulo="Vacio", client_id=cliente.id,
        )
        db.add(presupuesto)
        db.commit()

        from app.main import guardar_borrador_presupuesto, leer_borrador_presupuesto

        class PeticionVacia:
            async def json(self):
                return {"capitulos": [], "ts": 9999}

        respuesta = asyncio.run(guardar_borrador_presupuesto(presupuesto.id, PeticionVacia(), db))
        assert respuesta["ok"] is True

        leido = leer_borrador_presupuesto(presupuesto.id, db)
        assert leido["ok"] is True
        assert leido["capitulos"] == []
        assert leido["ts"] == 9999
    finally:
        db.close()
        engine.dispose()


def test_duplicar_presupuesto_copia_opciones_de_producto():
    """Al duplicar un presupuesto, las opciones de producto de cada
    partida también se copian (con imágenes independientes)."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        cliente = Cliente(nombre="Cliente Dup")
        db.add(cliente)
        db.flush()
        # Crear el original con opciones
        original = Presupuesto(
            numero="P-DUP-001", year=date.today().year, fecha=date.today(),
            titulo="Original", client_id=cliente.id,
        )
        db.add(original)
        db.flush()
        cap = Capitulo(nombre="CAP", orden=1)
        original.capitulos.append(cap)
        partida = PresupuestoItem(
            nombre="Pavimento", precio_unitario=100, cantidad=10, unidad="m2",
            orden=1, producto_nombre="Porcelanato X", producto_precio=100,
        )
        partida.productos_opciones.append(PresupuestoItemProducto(
            nombre="Porcelanato A", precio=95, unidad="m2", seleccionado=False, orden=0,
        ))
        partida.productos_opciones.append(PresupuestoItemProducto(
            nombre="Porcelanato B", precio=150, unidad="m2", seleccionado=True, orden=1,
        ))
        cap.partidas.append(partida)
        db.commit()
        db.refresh(original)

        # Duplicar usando la lógica interna (igual que duplicar_presupuesto)
        from app.main import _montar_presupuesto
        copia = Presupuesto(
            numero="P-DUP-002", year=date.today().year, fecha=date.today(),
            titulo="Copia", client_id=cliente.id,
        )
        capitulos = [{"nombre": "CAP", "partidas": [
            {
                "nombre": "Pavimento",
                "precio": 100.0, "cantidad": 10.0, "unidad": "m2",
                "prod_nombre": "Porcelanato X", "prod_precio": 100,
                "productos_opciones": [
                    {"nombre": "Porcelanato A", "precio": 95, "unidad": "m2", "seleccionado": False, "orden": 0},
                    {"nombre": "Porcelanato B", "precio": 150, "unidad": "m2", "seleccionado": True, "orden": 1},
                ],
                "mediciones": [],
                "descomposicion": [],
            }
        ]}]
        partidas = [{
            "cap": 0, "id": None, "catalogo_id": None,
            "nombre": "Pavimento", "precio": 100, "cantidad": 10,
            "unidad": "m2", "descripcion": "", "categoria": "",
            "prod_nombre": "Porcelanato X", "prod_precio": 100,
            "prod_coste": None, "prod_unidad": "m2", "prod_categoria": "",
            "prod_imagen_actual": "", "prod_imagen_file": None,
            "tipo_partida": "included", "seleccionada": False,
            "coste_materiales": 0, "coste_mano_obra": 0,
            "coste_complementarios": 0, "coste_otros": 0,
            "desperdicio_pct": 0, "margen_pct": 0,
            "grupo_alternativa": "",
            "mediciones": [], "descomposicion": [],
            "productos_opciones": [
                {"id": None, "nombre": "Porcelanato A", "precio": 95, "coste": None, "unidad": "m2",
                 "categoria": "", "marca": "", "modelo": "", "sku": "", "color": "", "acabado": "",
                 "descripcion": "", "imagen_actual": "", "seleccionado": False, "orden": 0},
                {"id": None, "nombre": "Porcelanato B", "precio": 150, "coste": None, "unidad": "m2",
                 "categoria": "", "marca": "", "modelo": "", "sku": "", "color": "", "acabado": "",
                 "descripcion": "", "imagen_actual": "", "seleccionado": True, "orden": 1},
            ],
        }]
        _montar_presupuesto(copia, capitulos, partidas, {}, None)
        db.add(copia)
        db.commit()
        db.refresh(copia)

        assert len(copia.capitulos) == 1
        assert len(copia.capitulos[0].partidas) == 1
        partida_copia = copia.capitulos[0].partidas[0]
        assert len(partida_copia.productos_opciones) == 2
        nombres = [op.nombre for op in partida_copia.productos_opciones]
        assert "Porcelanato A" in nombres
        assert "Porcelanato B" in nombres
        marcados = [op for op in partida_copia.productos_opciones if op.seleccionado]
        assert len(marcados) == 1
        assert marcados[0].nombre == "Porcelanato B"
    finally:
        db.close()
        engine.dispose()


def test_tiene_producto_detecta_opciones_multiples():
    """Una partida sin producto primario pero con opciones alternativas
    debe seguir siendo detectada como 'tiene producto' (el PDF la muestra)."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        cliente = Cliente(nombre="Cliente Tiene")
        db.add(cliente)
        db.flush()
        presupuesto = Presupuesto(
            numero="P-TIENE-001", year=date.today().year, fecha=date.today(),
            titulo="Tiene", client_id=cliente.id,
        )
        db.add(presupuesto)
        db.flush()
        cap = Capitulo(nombre="CAP", orden=1)
        presupuesto.capitulos.append(cap)
        # Partida SIN producto primario pero CON opciones
        partida = PresupuestoItem(
            nombre="Solo Opciones", precio_unitario=50, cantidad=5,
            orden=1, producto_nombre="", producto_precio=None,
        )
        partida.productos_opciones.append(PresupuestoItemProducto(
            nombre="Opcion 1", precio=80, unidad="m2", seleccionado=True, orden=0,
        ))
        cap.partidas.append(partida)
        db.commit()
        db.refresh(presupuesto)
        part = presupuesto.capitulos[0].partidas[0]
        assert part.tiene_producto is True
        assert part.producto_seleccionado is not None
        assert part.producto_seleccionado.nombre == "Opcion 1"
    finally:
        db.close()
        engine.dispose()



# ---------------------------------------------------------------------------
# PDF interactivo: varios productos por partida
# ---------------------------------------------------------------------------

def _partida_con_opciones():
    """Partida de obra (30 €/m2) con 3 productos candidatos, el 1º elegido."""
    partida = PresupuestoItem(
        nombre="Solado de porcelanato", unidad="m2", cantidad=10,
        precio_unitario=30 + 68, orden=1,
        producto_nombre="Porcelanato Calacatta", producto_precio=68,
        producto_unidad="m2",
    )
    for i, (nom, pre) in enumerate(
        [("Porcelanato Calacatta", 68), ("Marquina 60x120", 92), ("Gres Nórdico", 41.5)]
    ):
        partida.productos_opciones.append(PresupuestoItemProducto(
            nombre=nom, precio=pre, unidad="m2", seleccionado=(i == 0), orden=i,
        ))
    return partida


def test_productos_multiples_lista_todas_las_alternativas():
    """El PDF debe recibir TODOS los candidatos, no solo el marcado."""
    partida = _partida_con_opciones()
    assert len(partida.productos_multiples) == 3
    assert partida.indice_producto_elegido == 0
    # El primario ya está representado (mismo nombre) → no se duplica
    assert [op.nombre for op in partida.productos_multiples] == [
        "Porcelanato Calacatta", "Marquina 60x120", "Gres Nórdico",
    ]


def test_primario_se_antepone_como_una_opcion_mas():
    """Si el producto primario no está entre las opciones, se añade a la lista."""
    partida = _partida_con_opciones()
    partida.producto_nombre = "Producto exclusivo de la partida"
    lista = partida.productos_multiples
    assert len(lista) == 4
    assert lista[0] is partida          # el primario va el primero
    assert partida.indice_producto_elegido == 1  # la opción marcada se desplaza


def test_precio_base_sin_producto_descuenta_el_producto():
    """El precio de la partida es obra + producto; la base es solo la obra."""
    partida = _partida_con_opciones()
    assert partida.precio_base_sin_producto == pytest.approx(30.0)
    # Sin producto asociado la base es el precio unitario íntegro
    simple = PresupuestoItem(nombre="Demolición", precio_unitario=15, cantidad=2)
    assert simple.precio_base_sin_producto == pytest.approx(15.0)


def test_pdf_interactivo_emite_campos_de_formulario():
    """El PDF generado lleva AcroForm con radios por producto y JS de cálculo."""
    from app.models import Configuracion
    from app.services import pdf as pdf_service

    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    try:
        cfg = Configuracion(empresa_nombre="Test SL")
        cliente = Cliente(nombre="Cliente")
        db.add_all([cfg, cliente])
        db.flush()
        presu = Presupuesto(
            numero="P-1", year=2026, fecha=date.today(), client_id=cliente.id,
            impuesto_pct=16, moneda="EUR",
        )
        cap = Capitulo(nombre="BAÑO", orden=1)
        cap.partidas.append(_partida_con_opciones())
        presu.capitulos.append(cap)
        db.add(presu)
        db.commit()
        db.refresh(presu)

        data = pdf_service.generar_pdf(presu, cfg).getvalue()
        assert data.startswith(b"%PDF")
        # Formulario interactivo con JavaScript de recálculo
        for marca in (b"/JavaScript", b"NeedAppearances", b"/CO", b"PRESU"):
            assert marca in data, marca
        # Un grupo de radios por partida y los campos calculados
        for campo in (b"sel_p1", b"pu_p1", b"imp_p1", b"cap_c1", b"tot_total"):
            assert campo in data, campo
    finally:
        db.close()
        engine.dispose()


def test_pdf_sin_opciones_no_es_interactivo():
    """Sin varios productos que elegir no se añade formulario ni JavaScript."""
    from app.models import Configuracion
    from app.services import pdf as pdf_service

    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    try:
        cfg = Configuracion(empresa_nombre="Test SL")
        cliente = Cliente(nombre="Cliente")
        db.add_all([cfg, cliente])
        db.flush()
        presu = Presupuesto(
            numero="P-2", year=2026, fecha=date.today(), client_id=cliente.id,
            impuesto_pct=16, moneda="EUR",
        )
        cap = Capitulo(nombre="BAÑO", orden=1)
        cap.partidas.append(PresupuestoItem(
            nombre="Demolición", unidad="m2", cantidad=12, precio_unitario=15, orden=1,
        ))
        presu.capitulos.append(cap)
        db.add(presu)
        db.commit()
        db.refresh(presu)

        data = pdf_service.generar_pdf(presu, cfg).getvalue()
        assert data.startswith(b"%PDF")
        assert b"/JavaScript" not in data
        assert b"sel_p1" not in data
    finally:
        db.close()
        engine.dispose()


def test_pdf_interactivo_con_fotos_de_producto_no_rompe():
    """Regresión: el PDF interactivo con fotos de producto no debe lanzar
    ValueError por `setFillColor(None)` al dibujar el marco de la foto."""
    from PIL import Image

    from app.database import UPLOADS_DIR
    from app.models import Configuracion
    from app.services import pdf as pdf_service

    dir_fotos = UPLOADS_DIR / "products"
    dir_fotos.mkdir(parents=True, exist_ok=True)
    foto = dir_fotos / "test_foto_producto.png"
    Image.new("RGB", (60, 40), (180, 60, 60)).save(foto)
    try:
        engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool,
        )
        Base.metadata.create_all(engine)
        db = sessionmaker(bind=engine)()
        try:
            cfg = Configuracion(empresa_nombre="Test SL")
            cliente = Cliente(nombre="Cliente")
            db.add_all([cfg, cliente])
            db.flush()
            presu = Presupuesto(
                numero="P-3", year=2026, fecha=date.today(), client_id=cliente.id,
                impuesto_pct=16, moneda="EUR",
            )
            cap = Capitulo(nombre="BAÑO", orden=1)
            partida = _partida_con_opciones()
            partida.producto_imagen = "uploads/products/test_foto_producto.png"
            for op in partida.productos_opciones:
                op.imagen = "uploads/products/test_foto_producto.png"
            cap.partidas.append(partida)
            presu.capitulos.append(cap)
            db.add(presu)
            db.commit()
            db.refresh(presu)

            data = pdf_service.generar_pdf(presu, cfg).getvalue()
            assert data.startswith(b"%PDF")
            assert b"sel_p1" in data
        finally:
            db.close()
            engine.dispose()
    finally:
        if foto.exists():
            foto.unlink()


def test_configuracion_muestra_y_guarda_nombre_de_organizacion():
    """/configuracion permite editar el nombre de la organización (menú lateral)."""
    from app.models import Organizacion, Configuracion
    from app.database import SessionLocal

    with TestClient(app) as client:
        r = client.get("/configuracion")
        assert r.status_code == 200
        assert "Nombre de la organización" in r.text
        assert 'name="organizacion_nombre"' in r.text

        r2 = client.post(
            "/configuracion",
            data={
                "organizacion_nombre": "Reformas Nueva C.A.",
                "empresa_nombre": "Reformas Nueva C.A.",
                "empresa_legal": "",
                "empresa_rif": "",
                "empresa_pais": "Venezuela",
                "empresa_ciudad": "",
                "empresa_direccion": "",
                "empresa_telefono": "",
                "empresa_email": "",
                "empresa_web": "",
                "iva_default": "16",
                "moneda_default": "USD",
                "validez_default": "30",
                "notas_default": "",
                "condiciones_default": "",
                "pdf_color": "#04265D",
                "logo_ancho_pdf": "360",
                "horas_jornada": "8",
                "tarifa_hora_media": "8",
            },
            follow_redirects=False,
        )
        assert r2.status_code == 303

    with SessionLocal() as db:
        org = db.query(Organizacion).first()
        assert org is not None
        assert org.nombre == "Reformas Nueva C.A."
        assert org.slug  # el slug se regenera con el nuevo nombre
        cfg = db.query(Configuracion).first()
        assert cfg.empresa_nombre == "Reformas Nueva C.A."


def test_pdf_incluye_resumen_comercial_y_titulos_claros():
    import io
    from pypdf import PdfReader
    from app.models import Configuracion
    from app.services import pdf as pdf_service

    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    try:
        cfg = Configuracion(empresa_nombre="Constructora Clara")
        cliente = Cliente(nombre="Cliente PDF")
        db.add_all([cfg, cliente])
        db.flush()
        presu = Presupuesto(
            numero="P-PDF-1", year=2026, fecha=date.today(), client_id=cliente.id,
            impuesto_pct=16, moneda="USD", validez_dias=30,
            notas="Incluye suministro e instalación descritos en las partidas.",
            condiciones="Forma de pago: 50% anticipo y 50% contra entrega.",
        )
        cap = Capitulo(nombre="BAÑO", orden=1)
        cap.partidas.append(PresupuestoItem(
            nombre="Demolición", unidad="m2", cantidad=10, precio_unitario=20, orden=1,
        ))
        presu.capitulos.append(cap)
        db.add(presu)
        db.commit()
        db.refresh(presu)

        data = pdf_service.generar_pdf(presu, cfg).getvalue()
        texto = "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(data)).pages)
        assert "RESUMEN DE LA PROPUESTA" in texto
        assert "TOTAL" in texto
        assert "VALIDEZ" in texto
        assert "Alcance e información adicional" in texto
        assert "Condiciones comerciales" in texto
    finally:
        db.close()
        engine.dispose()
