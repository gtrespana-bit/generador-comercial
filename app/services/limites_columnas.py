"""Recorte de texto a la anchura real de las columnas (la última red anti-500).

El 3/11/2026, a las 23:55 UTC, un usuario pegó el texto completo de sus
condiciones de pago —unas 400 letras: porcentajes, datos bancarios, cédula—
en el campo «nombre» de una partida. Ese texto viaja a dos columnas con
anchos distintos:

- ``presupuesto_items.nombre`` → ``VARCHAR(250)``
- ``partidas.nombre`` (el catálogo que se rellena solo al guardar) →
  ``VARCHAR(200)``

PostgreSQL no recorta: aborta el INSERT con
``psycopg.errors.StringDataRightTruncation: value too long for type character
varying(200)``. El ``flush`` de SQLAlchemy falla entero, el usuario recibe un
500 y **pierde el presupuesto completo** por un texto de más. SQLite
(escritorio y pruebas) ignora el ancho declarado, así que el fallo solo
aparecía en producción y nunca en la suite.

Qué hace este módulo
--------------------
Traduce la anchura declarada en el modelo —que es la misma que tiene la
columna en la base— a un recorte del valor antes de enviarlo. La regla es la
que ya sigue el resto de la casa (ver ``paises.etiqueta_fiscal_segura``):
**el recorte es la última red**. Si alguien escribe más de lo que cabe, se
guarda lo que cabe y el presupuesto se guarda; nunca un 500 por un texto largo.

Dónde se aplica
---------------
1. Un escucha ``before_flush`` sobre la clase ``Session`` (ver
   ``app/database.py``) recorta cualquier objeto nuevo o modificado. Es la red
   de seguridad: cubre las rutas que hoy existen y las que se escriban mañana,
   sin obligar a cada formulario a acordarse de su columna.
2. ``_guardar_en_catalogos`` recorta además el nombre **antes** de calcular su
   clave de deduplicación. Sin eso, dos nombres que solo se diferencian a
   partir del carácter 201 quedarían idénticos al guardarse y chocarían contra
   ``uq_partida_organizacion_nombre``: el 500 cambiaría de forma, no de sitio.

Lo recortado se anota en el log con su campo y su longitud original (nunca el
texto), que es lo que permite ver desde el panel que un cliente está usando un
campo para algo que no era.
"""
from __future__ import annotations

import logging
from functools import lru_cache

from sqlalchemy import String, inspect

log = logging.getLogger("cotizat.limites_columnas")


@lru_cache(maxsize=None)
def limites_de(modelo) -> dict[str, int]:
    """Anchuras ``VARCHAR(n)`` declaradas por un modelo: ``{campo: n}``.

    Se leen del propio modelo y no de una lista escrita a mano: el modelo es la
    definición que comparten SQLAlchemy, Alembic y la base. Los tipos ``Text``
    no aparecen aquí (no tienen tope) y por eso nunca se recortan.
    """
    tabla = getattr(modelo, "__table__", None)
    if tabla is None:  # pragma: no cover - solo por si llega algo sin tabla
        return {}
    return {
        columna.key: columna.type.length
        for columna in tabla.columns
        if isinstance(columna.type, String) and getattr(columna.type, "length", None)
    }


def recortar_campo(modelo, campo: str, valor):
    """Devuelve ``valor`` recortado a la anchura de ``modelo.campo``.

    Un valor que no es texto, o una columna sin tope, se devuelven intactos:
    esto es una red, no una validación.
    """
    limite = limites_de(modelo).get(campo)
    if not limite or not isinstance(valor, str) or len(valor) <= limite:
        return valor
    return valor[:limite]


def _anotar(etiqueta: str, campo: str, original: int, nuevo: int) -> None:
    log.warning(
        "Texto recortado a la anchura de la columna (%s.%s): %s → %s caracteres",
        etiqueta,
        campo,
        original,
        nuevo,
    )


def recortar_a_columnas(instancia) -> dict[str, int]:
    """Recorta los textos de un objeto nuevo. Devuelve ``{campo: longitud previa}``.

    Solo toca los campos cuyo valor actual se pasa del ancho declarado, así que
    en el caso normal —todo cabe— no hace absolutamente nada.
    """
    modelo = type(instancia)
    recortes: dict[str, int] = {}
    for campo, limite in limites_de(modelo).items():
        try:
            valor = getattr(instancia, campo, None)
        except Exception:  # pragma: no cover - atributo no cargado
            continue
        if isinstance(valor, str) and len(valor) > limite:
            recortes[campo] = len(valor)
            setattr(instancia, campo, valor[:limite])
    for campo, original in recortes.items():
        _anotar(modelo.__table__.name, campo, original, limites_de(modelo)[campo])
    return recortes


def recortar_cambios(instancia) -> dict[str, int]:
    """Igual que :func:`recortar_a_columnas`, pero solo para lo modificado.

    En un objeto ya persistente se mira el historial de cada atributo para no
    recorrer ni reasignar columnas que nadie tocó (evita marcar como ``dirty``
    un objeto limpio y disparar un UPDATE que no hacía falta).
    """
    modelo = type(instancia)
    limites = limites_de(modelo)
    if not limites:
        return {}
    try:
        atributos = inspect(instancia).attrs
    except Exception:  # pragma: no cover - objeto no mapeado
        return {}
    recortes: dict[str, int] = {}
    for campo, limite in limites.items():
        try:
            estado = atributos[campo]
        except (KeyError, TypeError):  # pragma: no cover - columna sin atributo
            estado = None
        historial = getattr(estado, "history", None)
        if historial is None or not historial.has_changes():
            continue
        valor = getattr(instancia, campo, None)
        if isinstance(valor, str) and len(valor) > limite:
            recortes[campo] = len(valor)
            setattr(instancia, campo, valor[:limite])
    for campo, original in recortes.items():
        _anotar(modelo.__table__.name, campo, original, limites[campo])
    return recortes


def ajustar_sesion(sesion) -> int:
    """Recorta todo lo que la sesión va a escribir. Devuelve nº de campos tocados.

    Se llama desde el escucha ``before_flush``: en ese momento los objetos están
    completos y todavía no se ha enviado una sola sentencia, así que cambiar un
    valor aquí sí llega al INSERT/UPDATE.
    """
    tocados = 0
    for instancia in list(sesion.new):
        tocados += len(recortar_a_columnas(instancia))
    for instancia in list(sesion.dirty):
        if sesion.is_modified(instancia):
            tocados += len(recortar_cambios(instancia))
    return tocados
