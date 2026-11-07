"""Apoyo de pruebas para el cierre de la auditoría de precios de España.

El cierre del 7 de noviembre de 2026 sustituye, en los recursos que documenta,
el precio y la fuente que dejó cada lote anterior. Estas funciones permiten que
las pruebas de los lotes sigan comprobando la trazabilidad de su propio lote y,
a la vez, exijan que la matriz coincida con la decisión de cierre vigente.
"""
from __future__ import annotations

import csv
from decimal import Decimal
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRO = ROOT / "docs/auditoria_precios/espana_2026-11-06.csv"
LIBRO = ROOT / "docs/auditoria_precios/espana_cierre_decisiones_2026-11-07.csv"
REVISION_CIERRE = "docs/auditoria_precios/ESPANA_CIERRE_2026-11-07.md"
APLICA = {"aplicar_mano_obra_dos_fuentes", "aplicar_media_dos_bancos",
          "aplicar_fuente_unica_coherente"}


@lru_cache(maxsize=1)
def decisiones() -> dict[str, dict]:
    if not LIBRO.exists():
        return {}
    with LIBRO.open(encoding="utf-8-sig", newline="") as manejador:
        return {f["codigo_recurso"]: f for f in csv.DictReader(manejador, delimiter=";")}


def precio(codigo: str, previsto) -> Decimal:
    """Precio que debe figurar en la matriz: el del cierre si lo sustituyó."""
    fila = decisiones().get(codigo)
    if fila and fila["decision"] in APLICA:
        return Decimal(fila["precio_final"])
    return Decimal(str(previsto))


def fuente(codigo: str, prevista: str) -> str:
    fila = decisiones().get(codigo)
    if fila and fila["decision"] in APLICA:
        return REVISION_CIERRE
    return prevista


def condiciones(codigo: str, iva: str, transporte: str) -> tuple[str, str]:
    """IVA y transporte declarados en la matriz según la fuente vigente."""
    fila = decisiones().get(codigo)
    if fila and fila["decision"] in APLICA:
        return "no_confirmado", "no_confirmado"
    return iva, transporte


@lru_cache(maxsize=1)
def registro() -> dict[str, dict]:
    """Estado actual del registro maestro (puede haber confirmado después)."""
    with REGISTRO.open(encoding="utf-8-sig", newline="") as manejador:
        return {f["codigo_recurso"]: f for f in csv.DictReader(manejador, delimiter=";")}


def estado(codigo: str, previsto: str) -> str:
    # Una verificación posterior solo puede elevar el estado a confirmado; el
    # precio no cambia al confirmar, por eso las pruebas de lote siguen valiendo.
    actual = registro().get(codigo)
    if actual and actual["estado_auditoria"] == "confirmado_referencia":
        return "confirmado_referencia"
    fila = decisiones().get(codigo)
    if not fila:
        return previsto
    if fila["decision"] in APLICA:
        return "en_revision"
    if fila["decision"] == "confirmar_referencia":
        return "confirmado_referencia"
    return "en_revision" if previsto == "pendiente" else previsto


def precio_revisado(codigo: str, previsto: str) -> str:
    """Precio revisado vigente; el cierre puede añadirlo o confirmarlo."""
    fila = decisiones().get(codigo)
    if fila and fila["decision"] in APLICA:
        return fila["precio_final"]
    return previsto


def confirmado(codigo: str) -> bool:
    fila = decisiones().get(codigo)
    return bool(fila) and fila["decision"] == "confirmar_referencia"
