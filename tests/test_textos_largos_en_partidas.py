"""Regresión del 3/11/2026: un texto largo en el nombre de una partida no
puede tumbar el guardado del presupuesto.

El incidente real
-----------------
Un usuario pegó sus condiciones de pago (~400 caracteres: porcentajes, datos
bancarios, cédula) en el campo «nombre» de una partida y pulsó guardar.
``presupuesto_items.nombre`` es ``VARCHAR(250)`` y la partida que se guarda
sola en el catálogo va a ``partidas.nombre``, ``VARCHAR(200)``. PostgreSQL no
recorta: abortó el INSERT con ``StringDataRightTruncation`` y el ``flush``
completo falló, así que el presupuesto **no se guardó** y el usuario recibió un
500.

SQLite —escritorio y toda la suite— ignora el ancho declarado, por eso ninguna
prueba lo detectaba: el fallo solo existía en producción. Estas pruebas no
dependen de que el motor se queje; comprueban que lo que se escribe cabe en la
columna, que es la condición que PostgreSQL exige.

La regla que se verifica aquí:

1. El guardado del presupuesto termina bien (303) con nombres larguísimos.
2. Lo guardado respeta la anchura de cada columna (250 en la línea, 200 en el
   catálogo).
3. No se cuela un error distinto por el camino: dos nombres que solo difieren
   a partir del carácter 201 quedan idénticos al recortarse y no deben chocar
   contra ``uq_partida_organizacion_nombre``.
"""
from __future__ import annotations

import json
from datetime import date

from app.models import Cliente, Partida, Presupuesto, PresupuestoItem, Producto
from app.services.limites_columnas import (
    limites_de,
    recortar_a_columnas,
    recortar_campo,
)

#: El texto del incidente, con lo esencial: condiciones de pago pegadas en un
#: campo que solo admite un nombre corto.
CONDICIONES = (
    "Del cliente estar de acuerdo con lo que aquí se plantea deberá desembolsar "
    "el 70% de dicho trabajo y el restante al culminar todo satisfactoriamente, "
    "el pago se hará en un lapso no mayor a 15 días continuos después de "
    "terminados los trabajos de clima favorables, datos bancarios, número de "
    "cuenta: 31070190024, nombre: Miguel Angel mata salomón, cédula de "
    "identidad: 134-000-5447-7, banco: BHD"
)


# ---------------------------------------------------------------------------
# La red, en aislamiento
# ---------------------------------------------------------------------------

def test_el_texto_del_incidente_no_cabe_en_ninguna_de_las_dos_columnas():
    assert len(CONDICIONES) > 250
    assert recortar_campo(Partida, "nombre", CONDICIONES) == CONDICIONES[:200]
    assert recortar_campo(PresupuestoItem, "nombre", CONDICIONES) == CONDICIONES[:250]


def test_los_limites_salen_del_modelo_y_no_de_una_lista_a_mano():
    """El tope es el ancho declarado: modelo, Alembic y base dicen lo mismo."""
    assert limites_de(Partida)["nombre"] == 200
    assert limites_de(Partida)["unidad"] == 30
    assert limites_de(Partida)["categoria"] == 80
    assert limites_de(PresupuestoItem)["nombre"] == 250
    assert limites_de(PresupuestoItem)["unidad"] == 20
    assert limites_de(Producto)["nombre"] == 250
    # Los ``Text`` no tienen tope: no deben aparecer ni recortarse nunca.
    assert "descripcion" not in limites_de(Partida)
    assert "notas_tecnicas" not in limites_de(Partida)


def test_recortar_un_objeto_respeta_cada_columna():
    partida = Partida(
        nombre=CONDICIONES,
        unidad="m2 de porcelanato rectificado 60x120",
        categoria="Revestimientos y alicatados de gran formato, piezas especiales y mosaicos de sala",
        codigo_interno="X" * 120,
        descripcion=CONDICIONES,  # Text: no se toca
    )
    recortes = recortar_a_columnas(partida)

    assert recortes["nombre"] == len(CONDICIONES)
    assert len(partida.nombre) == 200
    assert len(partida.unidad) == 30
    assert len(partida.categoria) == 80
    assert len(partida.codigo_interno) == 80
    assert partida.descripcion == CONDICIONES


def test_el_escucha_de_sesion_recorta_antes_de_escribir(entorno):
    """La red vive en la sesión: cualquier alta queda dentro de su columna.

    Se comprueba leyendo de la base con una sesión nueva, que es lo único que
    ve el valor realmente persistido.
    """
    Session, _ids, _rol = entorno
    with Session() as db:
        db.add(Partida(nombre=CONDICIONES, unidad="ud"))
        db.commit()

    with Session() as db:
        guardada = (
            db.query(Partida).filter(Partida.nombre == CONDICIONES[:200]).first()
        )
        assert guardada is not None
        assert len(guardada.nombre) == 200


# ---------------------------------------------------------------------------
# El recorrido real: el formulario que falló
# ---------------------------------------------------------------------------

def _cliente_id(Session) -> int:
    with Session() as db:
        return db.query(Cliente).first().id


def _post_presupuesto(cliente_web, cliente_id: int, partidas: list[dict], **extra):
    datos = {
        "client_id": str(cliente_id),
        "titulo": "Obra",
        "fecha": date.today().isoformat(),
        "validez_dias": "30",
        "moneda": "USD",
        "impuesto_pct": "16",
        "descuento_pct": "0",
        "estado": "borrador",
        "estructura_json": json.dumps([
            {"nombre": "TRABAJOS PREVIOS", "partidas": partidas},
        ]),
    }
    datos.update(extra)
    respuesta = cliente_web.post(
        "/presupuestos/nuevo", data=datos, follow_redirects=False
    )
    return respuesta


def _partida(nombre: str, precio: float = 58.99) -> dict:
    return {
        "nombre": nombre,
        "unidad": "ud",
        "cantidad": 1.0,
        "precio": precio,
        "descripcion": "",
    }


def test_guardar_un_presupuesto_con_el_nombre_del_incidente(entorno, cliente_web):
    """Réplica del 500: ahora guarda, y guarda lo que cabe en cada columna."""
    Session, _ids, _rol = entorno
    respuesta = _post_presupuesto(
        cliente_web, _cliente_id(Session), [_partida(CONDICIONES)]
    )
    assert respuesta.status_code == 303, respuesta.text[:400]
    presupuesto_id = int(respuesta.headers["location"].split("?")[0].split("/")[-1])

    with Session() as db:
        presupuesto = db.get(Presupuesto, presupuesto_id)
        lineas = [p for cap in presupuesto.capitulos for p in cap.partidas]
        assert len(lineas) == 1
        assert len(lineas[0].nombre) == 250
        assert lineas[0].nombre == CONDICIONES[:250]

        maestra = (
            db.query(Partida).filter(Partida.nombre == CONDICIONES[:200]).first()
        )
        assert maestra is not None, "la partida del catálogo no se guardó"
        # El vínculo y el contador de usos se resuelven por la forma recortada.
        assert lineas[0].partida_catalogo_id == maestra.id
        assert maestra.usos >= 1


def test_dos_nombres_que_solo_difieren_al_final_no_chocan_entre_si(entorno, cliente_web):
    """Al recortar, dos nombres largos quedan idénticos: sin duplicado.

    Es el segundo 500 que este fallo podía provocar. El catálogo tiene
    ``uq_partida_organizacion_nombre``, así que la deduplicación tiene que usar
    la misma forma recortada que se va a escribir.
    """
    Session, _ids, _rol = entorno
    comun = "Retirar juntas de piso en terraza de coralina " + "X" * 180
    uno = comun + " primera parte"
    otro = comun + " segunda parte"
    assert uno[:200] == otro[:200]

    respuesta = _post_presupuesto(
        cliente_web,
        _cliente_id(Session),
        [_partida(uno, 10.0), _partida(otro, 20.0)],
    )
    assert respuesta.status_code == 303, respuesta.text[:400]
    presupuesto_id = int(respuesta.headers["location"].split("?")[0].split("/")[-1])

    with Session() as db:
        assert db.query(Partida).filter(Partida.nombre == uno[:200]).count() == 1
        presupuesto = db.get(Presupuesto, presupuesto_id)
        lineas = [p for cap in presupuesto.capitulos for p in cap.partidas]
        # En el presupuesto las dos líneas siguen existiendo y con su precio.
        assert len(lineas) == 2
        assert sorted(round(l.precio_unitario, 2) for l in lineas) == [10.0, 20.0]


def test_editar_un_presupuesto_admite_igual_el_nombre_largo(entorno, cliente_web):
    """El otro camino de guardado del editor: mismo recorte, sin 500."""
    Session, _ids, _rol = entorno
    cliente_id = _cliente_id(Session)
    creado = _post_presupuesto(cliente_web, cliente_id, [_partida("Nombre corto")])
    assert creado.status_code == 303
    presupuesto_id = int(creado.headers["location"].split("?")[0].split("/")[-1])

    editado = cliente_web.post(
        f"/presupuestos/{presupuesto_id}/editar",
        data={
            "client_id": str(cliente_id),
            "titulo": "Obra editada",
            "fecha": date.today().isoformat(),
            "validez_dias": "30",
            "moneda": "USD",
            "impuesto_pct": "16",
            "descuento_pct": "0",
            "estado": "borrador",
            "estructura_json": json.dumps([
                {"nombre": "TRABAJOS PREVIOS", "partidas": [_partida(CONDICIONES)]},
            ]),
        },
        follow_redirects=False,
    )
    assert editado.status_code == 303, editado.text[:400]

    with Session() as db:
        presupuesto = db.get(Presupuesto, presupuesto_id)
        lineas = [p for cap in presupuesto.capitulos for p in cap.partidas]
        assert len(lineas) == 1
        assert lineas[0].nombre == CONDICIONES[:250]


def test_la_ficha_del_catalogo_acepta_un_nombre_largo_sin_romperse(entorno, cliente_web):
    """/partidas/nueva y su edición pasan por la misma red."""
    Session, _ids, _rol = entorno
    respuesta = cliente_web.post(
        "/partidas/nueva",
        data={
            "nombre": CONDICIONES,
            "categoria": "General",
            "unidad": "m2 de porcelanato rectificado de gran formato",
            "precio_unitario": "10",
            "codigo_externo": "Y" * 140,
        },
        follow_redirects=False,
    )
    assert respuesta.status_code == 303, respuesta.text[:400]

    with Session() as db:
        partida = db.query(Partida).filter(Partida.nombre == CONDICIONES[:200]).first()
        assert partida is not None
        assert len(partida.unidad) == 30
        assert len(partida.codigo_externo) <= 100
