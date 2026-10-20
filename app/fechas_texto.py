"""Fechas como texto para las superficies públicas (Fase 2).

Las notas de las tablas de precios de las guías derivan su fecha de los
datos (``fecha_consulta`` de las matrices) para que no vuelva a quedar un
«agosto de 2026» escrito a mano envejeciendo en silencio: si la matriz se
reconsulta, la guía lo dice sola; si no, sigue diciendo la verdad antigua.
"""
from __future__ import annotations

import re
from collections.abc import Iterable

_MESES_ES = (
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
)

_INICIO_ISO = re.compile(r"^\s*(\d{4})-(\d{2})")


def _mes_anio(valor: object) -> tuple[int, int] | None:
    """``(año, mes)`` desde «2026-08», «2026-08-25» o «2026-08 · nota»."""
    encontrado = _INICIO_ISO.match(str(valor or ""))
    if not encontrado:
        return None
    anio, mes = int(encontrado.group(1)), int(encontrado.group(2))
    return (anio, mes) if 1 <= mes <= 12 else None


def mes_anio_es(valor: object) -> str:
    """«agosto de 2026» desde una fecha ISO; cadena vacía si no se entiende."""
    par = _mes_anio(valor)
    if par is None:
        return ""
    anio, mes = par
    return f"{_MESES_ES[mes - 1]} de {anio}"


def consulta_es(fechas: Iterable[object]) -> str:
    """Rango de consulta con preposición, listo para colgar de una frase.

    «en agosto de 2026» si todas caen en el mismo mes, «entre junio y
    agosto de 2026» dentro del año, «entre noviembre de 2025 y febrero de
    2026» cruzándolo. Cadena vacía si ninguna fecha se entiende: la guía
    no inventa una fecha que los datos no traen.
    """
    pares = sorted({par for par in (_mes_anio(f) for f in fechas) if par})
    if not pares:
        return ""
    (anio1, mes1), (anio2, mes2) = pares[0], pares[-1]
    if (anio1, mes1) == (anio2, mes2):
        return f"en {_MESES_ES[mes1 - 1]} de {anio1}"
    if anio1 == anio2:
        return f"entre {_MESES_ES[mes1 - 1]} y {_MESES_ES[mes2 - 1]} de {anio1}"
    return (
        f"entre {_MESES_ES[mes1 - 1]} de {anio1}"
        f" y {_MESES_ES[mes2 - 1]} de {anio2}"
    )
