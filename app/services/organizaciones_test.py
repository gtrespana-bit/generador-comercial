"""Helper para excluir organizaciones de prueba de todas las métricas del panel.

Toda cuenta que el titular marca como `es_test` en la ficha de cliente queda
visible en el directorio (con badge gris) pero no debe mover ningún KPI:
MRR, totales, embudo, cohortes, ventas, cobros, renovaciones, analítica ni
marketing. Este módulo centraliza el filtro para no repetir la lógica en los
15 servicios del panel.

Compatibilidad: la columna nace en la migración a8f1c3d9e7b2. Antes de aplicarla
(`Organizacion` sin atributo `es_test`) todas las orgs se consideran reales,
así que ningún dashboard se rompe por una migración pendiente.
"""

from __future__ import annotations


def es_organizacion_test(org) -> bool:
    """¿La organización está marcada como test? Tolera columna ausente."""
    if org is None:
        return False
    try:
        return bool(getattr(org, "es_test", False))
    except Exception:
        return False


def ids_organizaciones_test(db) -> set[int]:
    """Set de IDs de orgs test (consulta directa, tolera esquema viejo)."""
    try:
        from ..models import Organizacion

        # Si la columna no existe la consulta fallará en PostgreSQL/SQLite con
        # OperationalError (no such column). En ese caso devolvemos vacío.
        resultado = db.query(Organizacion).filter(Organizacion.es_test.is_(True)).all()
        return {int(o.id) for o in resultado}
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
        return set()


def filtrar_organizaciones_reales(organizaciones: list, db=None) -> list:
    """Filtra una lista ya cargada de Organizacion, excluyendo test."""
    if not organizaciones:
        return []
    # Si nos pasan el set precalculado evitamos getattr por cada una, pero
    # el helper simple es suficiente para listas de 200-500 orgs.
    return [o for o in organizaciones if not es_organizacion_test(o)]


def es_licencia_test(licencia, ids_test: set[int] | None = None, db=None) -> bool:
    """¿La licencia pertenece a una org test?"""
    if licencia is None:
        return False
    org_id = getattr(licencia, "organizacion_id", None)
    if org_id is None:
        return False
    if ids_test is not None:
        return int(org_id) in ids_test
    if db is not None:
        return int(org_id) in ids_organizaciones_test(db)
    return False


def es_compra_test(compra, ids_test: set[int] | None = None, db=None) -> bool:
    if compra is None:
        return False
    org_id = getattr(compra, "organizacion_id", None)
    if org_id is None:
        return False
    if ids_test is not None:
        return int(org_id) in ids_test
    if db is not None:
        return int(org_id) in ids_organizaciones_test(db)
    return False
