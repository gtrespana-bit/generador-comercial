"""Compatibilidad de lectura mientras la migración vectorial está pendiente.

El despliegue web y la migración de PostgreSQL no son una operación atómica.
Durante esa ventana el modelo :class:`PlanoObra` puede conocer columnas que la
base todavía no tiene. Una consulta ORM normal seleccionaría todas las columnas
y dejaría inutilizable incluso el visor histórico con ``UndefinedColumn``.

Este módulo inspecciona el esquema físico con el mismo login de la petición,
difiere únicamente las cuatro columnas añadidas por la migración vectorial y
rellena valores seguros sin disparar cargas diferidas. No intenta sustituir la
migración: crear planos nuevos y escribir geometría vectorial continúa
requiriendo el esquema completo, sus permisos y sus políticas RLS.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from sqlalchemy import inspect
from sqlalchemy.orm import Session, attributes, defer

from ..models import PlanoObra


COLUMNAS_PLANOS_VECTORIALES = frozenset(
    {
        "origen",
        "grosor_tabique_cm",
        "ancho_lienzo_m",
        "alto_lienzo_m",
    }
)

_VALORES_LEGACY = {
    "origen": "subido",
    "grosor_tabique_cm": 10.0,
    "ancho_lienzo_m": None,
    "alto_lienzo_m": None,
}

_CACHE_SESSION_KEY = "_esquema_planos_vectoriales"


@dataclass(frozen=True)
class EsquemaPlanos:
    """Capacidades físicas relevantes para el editor de planos."""

    columnas: frozenset[str]
    tiene_tabla_elementos: bool

    @property
    def columnas_vectoriales_completas(self) -> bool:
        return COLUMNAS_PLANOS_VECTORIALES.issubset(self.columnas)

    @property
    def editor_vectorial_disponible(self) -> bool:
        return self.columnas_vectoriales_completas and self.tiene_tabla_elementos

    def tiene_columna(self, nombre: str) -> bool:
        return nombre in self.columnas


# Valor útil para pruebas y para responder de forma controlada cuando ya se
# sabe que la migración administrativa todavía no se ha aplicado.
ESQUEMA_PLANOS_LEGACY = EsquemaPlanos(frozenset(), False)


def detectar_esquema_planos(db: Session) -> EsquemaPlanos:
    """Inspecciona una vez por sesión las columnas/tablas disponibles.

    Se usa ``Inspector`` en lugar de intentar un ``ALTER TABLE``. El login de
    runtime de producción es deliberadamente no propietario y PostgreSQL no le
    permite reparar el esquema; una introspección de catálogo sí es segura.
    """
    cacheado = db.info.get(_CACHE_SESSION_KEY)
    if isinstance(cacheado, EsquemaPlanos):
        return cacheado

    inspector = inspect(db.connection())
    columnas = frozenset(
        columna["name"] for columna in inspector.get_columns("planos_obra")
    )
    esquema = EsquemaPlanos(
        columnas=columnas,
        tiene_tabla_elementos=inspector.has_table("planos_elementos"),
    )
    db.info[_CACHE_SESSION_KEY] = esquema
    return esquema


def opciones_columnas_compatibles(esquema: EsquemaPlanos) -> tuple:
    """Opciones ORM que evitan referenciar las columnas físicas ausentes."""
    return tuple(
        defer(getattr(PlanoObra, nombre))
        for nombre in sorted(COLUMNAS_PLANOS_VECTORIALES - esquema.columnas)
    )


def completar_plano_legacy(plano: PlanoObra, esquema: EsquemaPlanos) -> PlanoObra:
    """Rellena atributos omitidos sin marcarlos sucios ni hacer otra SELECT."""
    for nombre in COLUMNAS_PLANOS_VECTORIALES - esquema.columnas:
        attributes.set_committed_value(plano, nombre, _VALORES_LEGACY[nombre])
    if not esquema.tiene_tabla_elementos:
        # La plantilla y los exportadores recorren ``plano.elementos``. Marcar
        # la relación como cargada y vacía impide una SELECT contra una tabla
        # que la misma migración todavía no ha creado.
        attributes.set_committed_value(plano, "elementos", [])
    return plano


def completar_planos_legacy(
    planos: Iterable[PlanoObra],
    esquema: EsquemaPlanos,
) -> list[PlanoObra]:
    return [completar_plano_legacy(plano, esquema) for plano in planos]
