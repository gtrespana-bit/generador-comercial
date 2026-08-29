"""Panel de renovaciones (Fase 2, B3): qué vence este mes y qué hacer.

Reutiliza ``resumen_organizaciones`` (solo tablas del titular: organizaciones,
licencias) y añade la vista mensual por vencimiento, el importe y el estado de
aviso. Nada de esto abre datos de tenant.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

from ..models import CompraPlan, Licencia, Organizacion
from .licencias import aviso_enviado_hoy


def _normalizar_importe(valor):
    try:
        return round(float(valor or 0), 2)
    except (TypeError, ValueError):
        return 0.0


def renovaciones_del_mes(
    db,
    *,
    mes: date | None = None,
    hoy: date | None = None,
) -> dict:
    """Renovaciones del mes pedido, más recientes por vencimiento primero."""
    hoy = hoy or date.today()
    mes = mes or hoy.replace(day=1)
    inicio = mes.replace(day=1)
    if inicio.month == 12:
        fin = inicio.replace(year=inicio.year + 1, month=1, day=1)
    else:
        fin = inicio.replace(month=inicio.month + 1, day=1)

    organizaciones = {o.id: o for o in db.query(Organizacion).all()}
    licencias = db.query(Licencia).filter(
        Licencia.estado != "cancelada"
    ).all()
    por_org: dict[int, list[Licencia]] = defaultdict(list)
    for lic in licencias:
        por_org[lic.organizacion_id].append(lic)

    filas = []
    for org_id, grupo in por_org.items():
        for lic in grupo:
            vence = lic.vence
            if not vence or not (inicio <= vence < fin):
                continue
            dias = max((vence - hoy).days, 0)
            importe = _normalizar_importe(lic.importe)
            estado = "vencida" if lic.estado == "vencida" or vence < hoy else (
                "por_renovar" if dias <= 15 else "activa"
            )
            filas.append({
                "organizacion": organizaciones.get(org_id),
                "organizacion_id": org_id,
                "licencia": lic,
                "vence": vence,
                "dias_restantes": dias,
                "importe": importe,
                "estado": estado,
                "avisado_hoy": bool(aviso_enviado_hoy(lic, hoy)),
                "origen": lic.origen or "",
            })
    filas = [f for f in filas if f["organizacion"] is not None]
    filas.sort(key=lambda f: (f["vence"], f["organizacion"].nombre))
    importe_mes = sum(f["importe"] for f in filas)
    por_renovar = sum(1 for f in filas if f["estado"] == "por_renovar")
    return {
        "mes": mes,
        "inicio": inicio,
        "fin": fin.replace(day=1) - timedelta(days=1),
        "filas": filas,
        "importe_mes": _normalizar_importe(importe_mes),
        "por_renovar": por_renovar,
        "total": len(filas),
    }


def proximas_renovaciones(db, *, hoy: date | None = None, limite: int = 20) -> list[dict]:
    """Las renovaciones más próximas (para el dashboard y notificaciones)."""
    hoy = hoy or date.today()
    organizaciones = {o.id: o for o in db.query(Organizacion).all()}
    licencias = db.query(Licencia).filter(Licencia.estado != "cancelada").all()
    filas = []
    for lic in licencias:
        if not lic.vence:
            continue
        dias = max((lic.vence - hoy).days, 0)
        if dias > 15:
            continue
        filas.append({
            "organizacion": organizaciones.get(lic.organizacion_id),
            "organizacion_id": lic.organizacion_id,
            "vence": lic.vence,
            "dias_restantes": dias,
            "importe": _normalizar_importe(lic.importe),
        })
    filas = [f for f in filas if f["organizacion"] is not None]
    filas.sort(key=lambda f: (f["vence"], f["organizacion"].nombre))
    return filas[:limite]
