"""El editor y el catálogo hablan siempre la misma moneda.

El catálogo (partidas, productos, recursos y packs) se guarda en la moneda base
—USD— y el presupuesto tiene su propia moneda contractual. Cada vez que un dato
cruza esa frontera hay que convertirlo, y en la dirección correcta:

- al **leer** hacia el editor: base → moneda del presupuesto;
- al **escribir** hacia el catálogo: moneda del presupuesto → base.

Estas pruebas cubren el fallo que motivó el módulo: el total de la partida se
veía en pesos mexicanos mientras los precios unitarios que lo calculaban
seguían en dólares, y «actualizar el catálogo» desde ese presupuesto guardaba
los pesos como si fueran dólares.
"""
import json

import pytest

from app.models import Configuracion, Partida, Producto, RecetaEstancia

TASA_MXN = 17.5


def _mexico(Session, *, precio=12.0, costes=(8.0, 2.0), precio_recurso=5.0):
    """Organización mexicana con una partida de 12 USD y su descomposición."""
    with Session() as db:
        cfg = db.query(Configuracion).first()
        cfg.empresa_pais = "México"
        cfg.moneda_default = "MXN"
        cfg.tasa_cambio = TASA_MXN
        partida = db.query(Partida).first()
        partida.precio_unitario = precio
        partida.coste_materiales, partida.coste_mano_obra = costes
        partida.descomposicion_json = json.dumps([{
            "tipo": "recurso", "codigo": "MT01", "descripcion": "Cemento",
            "unidad": "saco", "rendimiento": 2, "cantidad": 2,
            "precio": precio_recurso, "importe": precio_recurso * 2,
            "categoria": "materiales",
        }])
        producto = db.query(Producto).first()
        producto.precio_unitario = 45.0
        producto.precio_compra = 30.0
        db.commit()
        return partida.id


def test_la_ficha_del_catalogo_llega_en_la_moneda_del_presupuesto(entorno, cliente_web):
    """Regresión directa: total en MXN y precios unitarios en USD.

    Al pulsar «editar» sobre una partida, el modal pedía la ficha sin contexto
    monetario y recibía el precio, los costes y **la descomposición** en la
    moneda base, aunque el total de la línea ya estuviera convertido.
    """
    Session, _ids, _rol = entorno
    partida_id = _mexico(Session)

    datos = cliente_web.get(f"/partidas/{partida_id}/ficha").json()

    assert datos["ok"] is True
    assert datos["moneda"] == "MXN"
    ficha = datos["partida"]
    assert ficha["moneda"] == "MXN"
    assert ficha["precio"] == pytest.approx(12.0 * TASA_MXN)
    assert ficha["coste_materiales"] == pytest.approx(8.0 * TASA_MXN)
    assert ficha["coste_mano_obra"] == pytest.approx(2.0 * TASA_MXN)
    fila = ficha["descomposicion"]["filas"][0]
    assert fila["precio"] == pytest.approx(5.0 * TASA_MXN)
    assert fila["importe"] == pytest.approx(10.0 * TASA_MXN)


def test_la_ficha_respeta_la_moneda_pedida_por_el_presupuesto(entorno, cliente_web):
    """Un presupuesto en USD dentro de una organización mexicana no convierte."""
    Session, _ids, _rol = entorno
    partida_id = _mexico(Session)

    datos = cliente_web.get(
        f"/partidas/{partida_id}/ficha", params={"moneda": "USD"}
    ).json()

    assert datos["moneda"] == "USD"
    assert datos["partida"]["precio"] == pytest.approx(12.0)
    assert datos["partida"]["descomposicion"]["filas"][0]["precio"] == pytest.approx(5.0)


def test_sin_tasa_no_se_inventa_una_conversion(entorno, cliente_web):
    """Pedir una moneda ajena sin tasa devuelve la base, no un número falso."""
    Session, _ids, _rol = entorno
    partida_id = _mexico(Session)

    datos = cliente_web.get(
        f"/partidas/{partida_id}/ficha", params={"moneda": "COP"}
    ).json()

    assert datos["partida"]["precio"] == pytest.approx(12.0)


def test_la_descomposicion_usa_el_contexto_del_presupuesto(entorno, cliente_web):
    Session, _ids, _rol = entorno
    partida_id = _mexico(Session)

    datos = cliente_web.get(
        f"/partidas/{partida_id}/descomposicion",
        params={"moneda": "MXN", "tasa": TASA_MXN},
    ).json()

    assert datos["moneda"] == "MXN"
    assert datos["filas"][0]["precio"] == pytest.approx(5.0 * TASA_MXN)


def test_actualizar_el_precio_del_catalogo_no_multiplica_por_la_tasa(entorno, cliente_web):
    """Regresión de corrupción de datos.

    El editor envía el precio en la moneda del presupuesto. Sin la conversión
    inversa, «cambiar también en el catálogo» guardaba 3.675 MXN como 3.675 USD
    y el precio se multiplicaba por la tasa en cada edición.
    """
    Session, _ids, _rol = entorno
    partida_id = _mexico(Session)
    nuevo_en_pesos = 15.0 * TASA_MXN

    respuesta = cliente_web.post(
        f"/partidas/{partida_id}/actualizar-precio",
        json={"precio": nuevo_en_pesos, "moneda": "MXN", "tasa": TASA_MXN},
    ).json()

    assert respuesta["ok"] is True
    # La respuesta vuelve en la moneda del editor…
    assert respuesta["partida"]["precio"] == pytest.approx(nuevo_en_pesos)
    # …y la base de datos guarda la moneda base.
    with Session() as db:
        assert db.get(Partida, partida_id).precio_unitario == pytest.approx(15.0)


def test_guardar_la_ficha_desde_el_presupuesto_persiste_en_moneda_base(entorno, cliente_web):
    """Precio, costes y filas del descompuesto vuelven a la moneda base."""
    Session, _ids, _rol = entorno
    partida_id = _mexico(Session)

    respuesta = cliente_web.post(
        "/partidas/guardar-desde-presupuesto",
        data={
            "partida_catalogo_id": str(partida_id),
            "nombre": "Muro de bloque",
            "unidad": "m2",
            "categoria": "Albañilería",
            "precio_unitario": str(20.0 * TASA_MXN),
            "moneda": "MXN",
            "tasa": str(TASA_MXN),
            "d_tipo": "recurso",
            "d_codigo": "MT01",
            "d_descripcion": "Cemento",
            "d_unidad": "saco",
            "d_rendimiento": "2",
            "d_precio": str(5.0 * TASA_MXN),
            "d_categoria": "materiales",
        },
    ).json()

    assert respuesta["ok"] is True, respuesta
    assert respuesta["moneda"] == "MXN"
    assert respuesta["partida"]["precio"] == pytest.approx(20.0 * TASA_MXN, rel=1e-3)
    with Session() as db:
        guardada = db.get(Partida, partida_id)
        assert guardada.precio_unitario == pytest.approx(20.0, rel=1e-3)
        filas = json.loads(guardada.descomposicion_json)["filas"]
        assert filas[0]["precio"] == pytest.approx(5.0, rel=1e-3)
        # El coste calculado desde las filas también queda en la moneda base
        # (antes se guardaba en pesos junto a un precio en dólares).
        assert guardada.coste_materiales == pytest.approx(10.0, rel=1e-3)


def test_el_editor_recibe_productos_y_recursos_en_la_moneda_del_presupuesto(entorno, cliente_web):
    """El catálogo embebido del editor no puede traer dólares sueltos."""
    import re

    Session, _ids, _rol = entorno
    _mexico(Session)

    html = cliente_web.get("/presupuestos/nuevo").text

    productos = json.loads(
        re.search(r'id="datos-productos" type="application/json">(.*?)</script>', html, re.S).group(1)
    )
    assert productos[0]["precio"] == pytest.approx(45.0 * TASA_MXN)
    assert productos[0]["coste"] == pytest.approx(30.0 * TASA_MXN)
    assert productos[0]["moneda"] == "MXN"

    recursos = json.loads(
        re.search(r'id="datos-recursos" type="application/json">(.*?)</script>', html, re.S).group(1)
    )
    assert recursos[0]["moneda"] == "MXN"
    # Procedencia del precio: el editor la necesita para avisar de que un
    # recurso no tiene precio local confirmado.
    assert recursos[0]["origen_precio"] in {"base", "nacional", "organizacion"}
    assert "aviso_precio" in recursos[0]

    # El contexto monetario viaja al navegador para que las llamadas al
    # catálogo conviertan en la dirección correcta.
    assert 'window.COTIZAT_MONEDA_ACTIVA = "MXN"' in html
    assert "window.COTIZAT_TASA_ACTIVA = 17.5" in html


def test_los_packs_se_guardan_en_moneda_base_y_se_leen_convertidos(entorno, cliente_web):
    """Un pack creado en un presupuesto mexicano no puede multiplicar por 17
    al insertarlo en uno en dólares."""
    Session, _ids, _rol = entorno
    _mexico(Session)

    creado = cliente_web.post(
        "/recetas/api/guardar-desde-capitulo",
        json={
            "nombre": "Baño completo",
            "unidad_base": "m²",
            "cantidad_base_default": 10,
            "moneda": "MXN",
            "tasa": TASA_MXN,
            "items": [{"nombre": "Alicatado", "unidad": "m2", "cantidad": 10, "precio": 25.0 * TASA_MXN}],
        },
    ).json()
    assert creado["ok"] is True

    with Session() as db:
        receta = db.get(RecetaEstancia, creado["id"])
        assert json.loads(receta.datos)[0]["precio"] == pytest.approx(25.0, rel=1e-3)

    en_pesos = cliente_web.get("/recetas/api/list", params={"moneda": "MXN", "tasa": TASA_MXN}).json()
    pack = next(r for r in en_pesos["recetas"] if r["id"] == creado["id"])
    assert pack["items"][0]["precio"] == pytest.approx(25.0 * TASA_MXN, rel=1e-3)

    en_dolares = cliente_web.get("/recetas/api/list", params={"moneda": "USD"}).json()
    pack_usd = next(r for r in en_dolares["recetas"] if r["id"] == creado["id"])
    assert pack_usd["items"][0]["precio"] == pytest.approx(25.0, rel=1e-3)


def test_el_producto_se_edita_y_se_guarda_en_la_misma_moneda(entorno, cliente_web):
    Session, _ids, _rol = entorno
    _mexico(Session)
    with Session() as db:
        producto_id = db.query(Producto).first().id

    formulario = cliente_web.get(f"/productos/{producto_id}/editar").text
    assert "Precio de venta unitario (MXN)" in formulario
    assert f"{45.0 * TASA_MXN:.1f}" in formulario.replace(",", ".")

    cliente_web.post(
        f"/productos/{producto_id}/editar",
        data={"nombre": "Porcelanato gris", "unidad": "m2", "precio_unitario": str(50.0 * TASA_MXN)},
        follow_redirects=False,
    )
    with Session() as db:
        assert db.get(Producto, producto_id).precio_unitario == pytest.approx(50.0, rel=1e-3)


def test_los_importes_se_muestran_con_codigo_iso_y_simbolo_del_pais(entorno, cliente_web):
    """Nada de «$» a secas: ni en las listas ni en los símbolos auxiliares."""
    from app.services.monedas import simbolo
    from app.utils import fmt_monto

    assert simbolo("MXN") == "MX$"
    assert simbolo("COP") == "COL$"
    assert simbolo("USD") == "US$"
    assert simbolo("PEN") == "S/"
    assert fmt_monto(1234.5, "MXN").endswith("MX$")
    # El peso colombiano no muestra decimales (política acordada).
    assert fmt_monto(4200000, "COP") == "4.200.000 COL$"

    Session, _ids, _rol = entorno
    _mexico(Session)
    listado = cliente_web.get("/partidas").text
    assert "MXN" in listado
    assert "210,00 $" not in listado
