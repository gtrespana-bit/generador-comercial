"""Centro de notificaciones del panel (A4): pendientes y alertas del negocio.

La campana consulta solamente datos que el operador ya puede leer por RLS
(organizaciones, licencias, compras, operadores). Nunca abre datos de tenant.
"""
from __future__ import annotations

from datetime import date, timedelta

from collections import defaultdict

from sqlalchemy import func

from ..models import CompraPlan, Licencia, OperadorProducto, Organizacion
from ..operadores import ROLES_OPERADOR_ETIQUETA, operadores_configurados
from .licencias import vence_cadena


def notificaciones_admin(
    db,
    *,
    hoy: date | None = None,
) -> list[dict]:
    """Lista ordenada de avisos activos para la campana del panel."""
    hoy = hoy or date.today()
    avisos: list[dict] = []

    # --- Licencias por vencer (≤15 días) ------------------------------
    licencias = db.query(Licencia).all()
    por_org: dict[int, list[Licencia]] = defaultdict(list)
    for lic in licencias:
        por_org[lic.organizacion_id].append(lic)

    organizaciones = {o.id: o for o in db.query(Organizacion).all()}
    nombres = {o.id: o.nombre for o in organizaciones.values()}

    por_vencer = 0
    for org_id, cadena in por_org.items():
        vigente = next((l for l in cadena if l.vigente(hoy)), None)
        if vigente is None:
            continue
        vence_total = vence_cadena(cadena, hoy) or vigente.vence
        dias = max((vence_total - hoy).days, 0)
        if dias <= 15:
            por_vencer += 1
            avisos.append(_aviso(
                "renovacion",
                "critical" if dias <= 3 else "warning",
                f"{nombres.get(org_id, 'Cliente')} vence en {dias} día(s)",
                f"El acceso caduca el {vence_total:%d/%m/%Y}.",
                # Directo a la ficha del cliente que vence: es donde se renueva o
                # se concede, no a una lista genérica.
                f"/admin/clientes/{org_id}?tab=acceso",
            ))
        if len(avisos) >= 8:
            break

    # --- Compras pendientes de activar --------------------------------
    pendientes = db.query(CompraPlan).filter(
        CompraPlan.estado == "pendiente"
    ).order_by(CompraPlan.created_at.asc()).limit(3).all()
    for compra in pendientes:
        nombre = nombres.get(compra.organizacion_id, "Cliente")
        avisos.append(_aviso(
            "compra",
            "warning",
            f"Compra #{compra.id} de {nombre} por activar",
            f"Plan {compra.plan} · {compra.moneda} {compra.importe:,.2f}",
            "/admin/ingresos?tab=compras&estado=pendiente",
        ))

    # --- Seguridad del equipo -----------------------------------------
    equipo_db = db.query(OperadorProducto).all()
    env = operadores_configurados()
    if not equipo_db and not env:
        avisos.append(_aviso(
            "equipo",
            "critical",
            "Equipo vacío: nadie puede administrar el panel",
            "Configura COTIZAT_OPERADORES o da de alta un superadmin.",
            "/admin/sistema?tab=equipo",
        ))
    superadmins_activos = sum(
        1 for op in equipo_db if op.rol == "superadmin" and op.activo
    )
    if env and superadmins_activos == 0:
        avisos.append(_aviso(
            "equipo",
            "warning",
            "Sin superadmin activo en la base",
            "El acceso por COTIZAT_OPERADORES sigue funcionando como semilla.",
            "/admin/sistema?tab=equipo",
        ))

    # --- Estado del negocio -------------------------------------------
    sin_plan = len(organizaciones) - sum(
        1 for cadena in por_org.values() if any(vigente for vigente in cadena if vigente.vigente(hoy))
    )
    if sin_plan > 0:
        avisos.append(_aviso(
            "negocio",
            "info",
            f"{sin_plan} cliente(s) sin plan activo",
            "Revisar la conversión y las oportunidades de renovación.",
            "/admin/clientes?tab=directorio&plan=sin",
        ))

    return _ordenar(avisos)[:12]


def _aviso(tipo: str, severidad: str, titulo: str, detalle: str, url: str) -> dict:
    return {
        "id": f"{tipo}-{len(titulo)}-{hash(titulo)}",
        "tipo": tipo,
        "severidad": severidad,
        "titulo": titulo,
        "detalle": detalle,
        "url": url,
    }


def _ordenar(avisos: list[dict]) -> list[dict]:
    peso = {"critical": 0, "warning": 1, "info": 2}
    return sorted(avisos, key=lambda a: peso.get(a["severidad"], 3))
