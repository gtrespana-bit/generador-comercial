"""El guardado automático del catálogo no puede inflar los precios.

Regresión del fallo reportado en producción: en una organización colombiana,
una partida del catálogo aparecía en el presupuesto a «46.897.962 COP/m²» por
demoler un piso cerámico. La cifra era el precio real (4,79 USD) multiplicado
DOS veces por la tasa (3.128,65):

1. El editor muestra el catálogo convertido a la moneda del presupuesto.
2. Al guardar, ``_guardar_en_catalogos`` escribía ese importe en el catálogo
   —que vive en moneda base— como si fueran dólares.
3. Además, la partida llegaba con el nombre TRADUCIDO al país («capa de
   pegante» en vez de «capa de pega»), así que no coincidía con ninguna
   maestra y se creaba un duplicado con el precio ya inflado.
4. La siguiente vez que se usaba esa partida, el editor volvía a multiplicar.

Estas pruebas cubren los cuatro puntos y la herramienta de reparación del
catálogo ya dañado.
"""
import json
from datetime import date

import pytest

from app.models import Configuracion, Partida, Presupuesto, Producto
from app.services.precios_anomalos import (
    detectar_precios_anomalos,
    reparar_precios_anomalos,
)

TASA_COP = 3128.65


def _colombia(Session, *, nombre="Demolición de piso cerámico y su capa de pega.",
              precio=4.89):
    """Organización colombiana con una partida oficial de 4,89 USD."""
    with Session() as db:
        cfg = db.query(Configuracion).first()
        cfg.empresa_pais = "Colombia"
        cfg.moneda_default = "COP"
        cfg.tasa_cambio = TASA_COP
        partida = db.query(Partida).first()
        partida.nombre = nombre
        partida.precio_unitario = precio
        partida.es_oficial = True
        partida.coste_mano_obra = 1.98
        db.commit()
        return partida.id


def _crear_presupuesto(cliente_web, estructura, *, moneda="COP", tasa=TASA_COP):
    respuesta = cliente_web.post(
        "/presupuestos/nuevo",
        data={
            "client_id": "1",
            "titulo": "Obra en Bogotá",
            "fecha": date.today().isoformat(),
            "validez_dias": "30",
            "moneda": moneda,
            "tipo_cambio": str(tasa),
            "impuesto_pct": "19",
            "estado": "borrador",
            "estructura_json": json.dumps(estructura),
        },
        follow_redirects=False,
    )
    assert respuesta.status_code == 303, respuesta.text[:400]
    return int(respuesta.headers["location"].split("?")[0].split("/")[-1])


def test_una_partida_traducida_no_se_duplica_en_el_catalogo(entorno, cliente_web):
    """El nombre traducido al país es la MISMA partida, no una nueva."""
    Session, _ids, _rol = entorno
    partida_id = _colombia(Session)

    with Session() as db:
        partidas_antes = db.query(Partida).count()

    _crear_presupuesto(cliente_web, [{
        "nombre": "DEMOLICIONES",
        "partidas": [{
            # Nombre tal y como lo ve un usuario colombiano en el editor.
            "nombre": "Demolición de piso cerámico y su capa de pegante.",
            "unidad": "m2", "cantidad": 1, "precio": 4.89 * TASA_COP,
        }],
    }])

    with Session() as db:
        assert db.query(Partida).count() == partidas_antes, (
            "el guardado automático duplicó la partida por su nombre traducido"
        )
        # Y la línea queda vinculada a la maestra correcta.
        item = db.query(Presupuesto).order_by(Presupuesto.id.desc()).first().capitulos[0].partidas[0]
        assert item.partida_catalogo_id == partida_id


def test_una_partida_nueva_se_guarda_en_el_catalogo_en_moneda_base(entorno, cliente_web):
    """Lo que el usuario escribe en pesos se guarda en dólares en el catálogo."""
    Session, _ids, _rol = entorno
    _colombia(Session)

    _crear_presupuesto(cliente_web, [{
        "nombre": "VARIOS",
        "partidas": [{
            "nombre": "Partida escrita a mano por el usuario",
            "unidad": "m2", "cantidad": 2,
            "precio": 30.0 * TASA_COP,
            "coste_materiales": 10.0 * TASA_COP,
            "coste_mano_obra": 5.0 * TASA_COP,
        }],
    }])

    with Session() as db:
        nueva = db.query(Partida).filter(
            Partida.nombre == "Partida escrita a mano por el usuario"
        ).one()
        assert nueva.precio_unitario == pytest.approx(30.0, rel=1e-3)
        assert nueva.coste_materiales == pytest.approx(10.0, rel=1e-3)
        assert nueva.coste_mano_obra == pytest.approx(5.0, rel=1e-3)
        # La línea del presupuesto conserva su importe en pesos.
        item = db.query(Presupuesto).order_by(Presupuesto.id.desc()).first().capitulos[0].partidas[0]
        assert item.precio_unitario == pytest.approx(30.0 * TASA_COP, rel=1e-3)


def test_el_producto_nuevo_tambien_se_guarda_en_moneda_base(entorno, cliente_web):
    Session, _ids, _rol = entorno
    _colombia(Session)

    _crear_presupuesto(cliente_web, [{
        "nombre": "ACABADOS",
        "partidas": [{
            "nombre": "Suministro y colocación de porcelanato propio",
            "unidad": "m2", "cantidad": 1, "precio": 40.0 * TASA_COP,
            "prod_nombre": "Porcelanato importado 60x60",
            "prod_precio": 25.0 * TASA_COP,
            "prod_coste": 18.0 * TASA_COP,
            "prod_unidad": "m2",
        }],
    }])

    with Session() as db:
        producto = db.query(Producto).filter(
            Producto.nombre == "Porcelanato importado 60x60"
        ).one()
        assert producto.precio_unitario == pytest.approx(25.0, rel=1e-3)
        assert producto.precio_compra == pytest.approx(18.0, rel=1e-3)
        # La partida guarda solo su base (precio de línea menos el producto).
        partida = db.query(Partida).filter(
            Partida.nombre == "Suministro y colocación de porcelanato propio"
        ).one()
        assert partida.precio_unitario == pytest.approx(15.0, rel=1e-3)


def test_un_presupuesto_en_dolares_no_convierte_nada(entorno, cliente_web):
    """Sin conversión en la vista no puede haber conversión al guardar."""
    Session, _ids, _rol = entorno
    _colombia(Session)

    _crear_presupuesto(cliente_web, [{
        "nombre": "VARIOS",
        "partidas": [{
            "nombre": "Partida cotizada directamente en dólares",
            "unidad": "ud", "cantidad": 1, "precio": 120.0,
        }],
    }], moneda="USD", tasa="")

    with Session() as db:
        nueva = db.query(Partida).filter(
            Partida.nombre == "Partida cotizada directamente en dólares"
        ).one()
        assert nueva.precio_unitario == pytest.approx(120.0, rel=1e-6)


def test_reutilizar_la_partida_no_multiplica_el_precio(entorno, cliente_web):
    """El ciclo completo: usar → guardar → volver a buscar mantiene el precio."""
    Session, _ids, _rol = entorno
    _colombia(Session)

    _crear_presupuesto(cliente_web, [{
        "nombre": "DEMOLICIONES",
        "partidas": [{
            "nombre": "Demolición de piso cerámico y su capa de pegante.",
            "unidad": "m2", "cantidad": 1, "precio": 4.89 * TASA_COP,
        }],
    }])

    resultados = cliente_web.get(
        "/partidas/api/buscar",
        params={"q": "demolición de piso cerámico", "moneda": "COP", "tasa": TASA_COP},
    ).json()["resultados"]

    assert resultados, "la búsqueda debe seguir encontrando la partida"
    for resultado in resultados:
        assert resultado["precio"] < 1_000_000, (
            f"precio imposible tras reutilizar la partida: {resultado}"
        )
    assert resultados[0]["precio"] == pytest.approx(4.89 * TASA_COP, rel=1e-3)


# ---------------------------------------------------------------------------
# Reparación del catálogo ya dañado por el fallo anterior
# ---------------------------------------------------------------------------

def test_detecta_y_repara_el_duplicado_inflado(entorno, cliente_web):
    Session, _ids, _rol = entorno
    _colombia(Session)
    with Session() as db:
        # Estado exacto que dejaba el fallo: duplicado con el nombre traducido
        # y el precio en pesos guardado como si fuera moneda base.
        db.add(Partida(
            nombre="Demolición de piso cerámico y su capa de pegante.",
            unidad="m2", precio_unitario=4.89 * TASA_COP,
        ))
        db.commit()

        anomalias = detectar_precios_anomalos(db)
        assert len(anomalias) == 1
        assert anomalias[0]["reparable"] is True
        assert anomalias[0]["precio_sugerido"] == pytest.approx(4.89, rel=1e-2)

        resumen = reparar_precios_anomalos(db)
        assert resumen["total_corregidas"] == 1

        reparada = db.query(Partida).filter(
            Partida.nombre == "Demolición de piso cerámico y su capa de pegante."
        ).one()
        assert reparada.precio_unitario == pytest.approx(4.89, rel=1e-2)
        assert detectar_precios_anomalos(db) == []


def test_no_toca_una_partida_cara_pero_creible(entorno, cliente_web):
    """La reparación nunca «arregla» un precio alto que puede ser real."""
    Session, _ids, _rol = entorno
    _colombia(Session)
    with Session() as db:
        db.add(Partida(
            nombre="Instalación llave en mano de ascensor de 8 paradas",
            unidad="ud", precio_unitario=45_000.0, categoria="Transporte",
        ))
        db.commit()

        anomalias = detectar_precios_anomalos(db)
        assert [a["reparable"] for a in anomalias] == [False]

        reparar_precios_anomalos(db)
        cara = db.query(Partida).filter(
            Partida.nombre == "Instalación llave en mano de ascensor de 8 paradas"
        ).one()
        assert cara.precio_unitario == pytest.approx(45_000.0)


def test_el_boton_de_reparacion_esta_disponible_en_el_catalogo(entorno, cliente_web):
    Session, _ids, _rol = entorno
    _colombia(Session)
    with Session() as db:
        db.add(Partida(
            nombre="Demolición de piso cerámico y su capa de pegante.",
            unidad="m2", precio_unitario=4.89 * TASA_COP,
        ))
        db.commit()

    listado = cliente_web.get("/partidas")
    assert "Precios imposibles" in listado.text

    diagnostico = cliente_web.get("/partidas/precios/anomalos").json()
    assert diagnostico["total"] == 1
    assert diagnostico["reparables"] == 1

    reparacion = cliente_web.post("/partidas/precios/reparar", follow_redirects=False)
    assert reparacion.status_code == 303

    with Session() as db:
        reparada = db.query(Partida).filter(
            Partida.nombre == "Demolición de piso cerámico y su capa de pegante."
        ).one()
        assert reparada.precio_unitario == pytest.approx(4.89, rel=1e-2)


def test_importar_una_lista_de_precios_local_no_infla_el_catalogo(entorno, cliente_web):
    """El Excel se lee en la moneda del usuario; el catálogo guarda la base.

    Segunda vía por la que aparecían precios imposibles: importar al catálogo
    una lista de precios en pesos escribía esos pesos como si fueran dólares.
    """
    Session, _ids, _rol = entorno
    _colombia(Session)

    respuesta = cliente_web.post(
        "/presupuestos/importar/confirmar",
        json={
            "modo": "catalogo",
            "moneda": "COP",
            "tasa": TASA_COP,
            "primera_fila": 2,
            "mapeo": {"partida": 0, "unidad": 1, "precio": 2},
            "filas": [["Suministro de arena lavada", "m3", str(30.0 * TASA_COP)]],
        },
    ).json()

    assert respuesta["ok"] is True, respuesta
    with Session() as db:
        importada = db.query(Partida).filter(
            Partida.nombre == "Suministro de arena lavada"
        ).one()
        assert importada.precio_unitario == pytest.approx(30.0, rel=1e-2)
