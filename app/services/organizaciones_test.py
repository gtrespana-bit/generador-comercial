"""Helper para excluir organizaciones de prueba de todas las métricas del panel.

Toda cuenta que el titular marca como `es_test` en la ficha de cliente queda
aislada del directorio real y no debe mover ningún KPI:
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


def usuarios_solo_test(db):
    """IDs asociados a test y a ninguna organización real; conserva usuarios sin empresa.

    Un usuario que pertenece a ambos tipos sigue contando como usuario real.
    Se consideran también membresías inactivas para no recuperar como registros
    reales cuentas de prueba cuya membresía se desactivó.
    """
    from ..models import Membresia, Organizacion

    test = db.query(Membresia.usuario_id).join(
        Organizacion, Organizacion.id == Membresia.organizacion_id
    ).filter(Organizacion.es_test.is_(True))
    reales = db.query(Membresia.usuario_id).join(
        Organizacion, Organizacion.id == Membresia.organizacion_id
    ).filter(Organizacion.es_test.is_(False))
    return test.filter(~Membresia.usuario_id.in_(reales))


def registro_real(db, organizacion_id, email):
    """Incluye registros globales salvo los atribuibles a usuarios solo TEST."""
    from sqlalchemy import or_, and_, func
    from ..models import Organizacion, Usuario

    orgs_test = db.query(Organizacion.id).filter(Organizacion.es_test.is_(True))
    emails_test = db.query(func.lower(Usuario.email)).filter(
        Usuario.id.in_(usuarios_solo_test(db)), Usuario.email.isnot(None)
    )
    return or_(
        and_(organizacion_id.isnot(None), ~organizacion_id.in_(orgs_test)),
        and_(organizacion_id.is_(None), or_(email.is_(None), ~func.lower(email).in_(emails_test))),
    )
