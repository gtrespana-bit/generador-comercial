"""Resumen consolidado del panel de operador premium (``/admin``).

Une en una sola vista lo que el titular necesita para administrar el
producto: cada cliente (organización) con su plan, fecha de compra, fecha de
caducidad y estado, más las compras pendientes de activar. Las cifras y la
tabla se calculan aquí, en el servidor; el navegador solo ordena y filtra la
tabla ya renderizada.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date

from ..models import CompraPlan, Licencia, Membresia, Organizacion, Usuario

#: Los planes publicados se reconocen por su importe (ver app/datos_pago.py).
PLAN_POR_IMPORTE = {89.0: "Anual", 9.99: "Mensual"}
ETIQUETA_ORIGEN = {
    "pago": "Pago",
    "prueba": "Prueba",
    "cortesia": "Cortesía",
    "compensacion": "Compensación",
}
ETIQUETA_ESTADO = {
    "activa": "Activo",
    "por_vencer": "Por vencer",
    "vencida": "Vencido",
    "sin_licencia": "Sin plan",
}


def _plan_label(licencia: Licencia | None) -> str:
    if licencia is None:
        return "—"
    if licencia.origen == "pago":
        return PLAN_POR_IMPORTE.get(round(licencia.importe, 2), "Pago")
    return ETIQUETA_ORIGEN.get(licencia.origen, licencia.origen)


def _estado_licencia(licencia: Licencia | None, hay_historial: bool, hoy: date, dias_aviso: int) -> str:
    if licencia is None:
        return "vencida" if hay_historial else "sin_licencia"
    if licencia.dias_restantes(hoy) <= dias_aviso:
        return "por_vencer"
    return "activa"


def resumen_admin(
    db,
    *,
    hoy: date | None = None,
    dias_aviso: int = 15,
) -> dict:
    """Una fila por cliente con su plan y compras, más los totales y pendientes."""
    hoy = hoy or date.today()

    organizaciones = (
        db.query(Organizacion).order_by(Organizacion.nombre, Organizacion.id).all()
    )
    licencias = db.query(Licencia).all()
    compras = db.query(CompraPlan).order_by(CompraPlan.created_at.asc()).all()
    membresias = (
        db.query(Membresia).filter(Membresia.activa.is_(True)).all()
    )
    usuarios = {u.id: u for u in db.query(Usuario).all()}

    # Normaliza el estado (misma regla que el panel de licencias).
    for licencia in licencias:
        if licencia.estado == "activa" and licencia.vence < hoy:
            licencia.estado = "vencida"

    lic_por_org: dict[int, list[Licencia]] = defaultdict(list)
    for licencia in licencias:
        lic_por_org[licencia.organizacion_id].append(licencia)

    compras_por_org: dict[int, list[CompraPlan]] = defaultdict(list)
    for compra in compras:
        compras_por_org[compra.organizacion_id].append(compra)

    emails_por_org: dict[int, list[str]] = defaultdict(list)
    for membresia in membresias:
        usuario = usuarios.get(membresia.usuario_id)
        if usuario and usuario.email:
            emails_por_org[membresia.organizacion_id].append(usuario.email)

    filas = []
    pendientes = []
    for organizacion in organizaciones:
        licencias_org = sorted(
            lic_por_org.get(organizacion.id, []),
            key=lambda l: (l.inicio, l.id),
            reverse=True,
        )
        vigente = next((l for l in licencias_org if l.vigente(hoy)), None)
        compras_org = sorted(
            compras_por_org.get(organizacion.id, []),
            key=lambda c: (c.created_at or c.id, c.id),
        )
        pendientes_org = [c for c in compras_org if c.estado == "pendiente"]
        for compra in pendientes_org:
            pendientes.append(
                {
                    "compra": compra,
                    "organizacion_nombre": organizacion.nombre,
                    "plan_label": _plan_label_compra(compra),
                }
            )

        filas.append(
            {
                "organizacion": organizacion,
                "emails": sorted(set(emails_por_org.get(organizacion.id, []))),
                "licencias": licencias_org,
                "vigente": vigente,
                "plan_label": _plan_label(vigente),
                "inicio": vigente.inicio if vigente else None,
                "vence": vigente.vence if vigente else None,
                "dias_restantes": vigente.dias_restantes(hoy) if vigente else 0,
                "estado": _estado_licencia(
                    vigente, bool(licencias_org), hoy, dias_aviso
                ),
                "estado_label": ETIQUETA_ESTADO[
                    _estado_licencia(vigente, bool(licencias_org), hoy, dias_aviso)
                ],
                "ingresos": sum(
                    licencia.importe
                    for licencia in licencias_org
                    if licencia.es_ingreso
                ),
                "compras_pendientes": pendientes_org,
                "metodo_cobro": vigente.metodo_cobro if vigente else "",
            }
        )

    totales = {
        "clientes": len(filas),
        "con_plan": sum(1 for f in filas if f["vigente"]),
        "sin_plan": sum(1 for f in filas if not f["vigente"]),
        "por_vencer": sum(1 for f in filas if f["estado"] == "por_vencer"),
        "pendientes": len(pendientes),
        "ingresos": sum(f["ingresos"] for f in filas),
    }
    return {
        "filas": filas,
        "pendientes": pendientes,
        "totales": totales,
        "hoy": hoy,
    }


def _plan_label_compra(compra: CompraPlan) -> str:
    """Etiqueta de plan para una compra (la compra guarda el plan, no el importe)."""
    return {"anual": "Anual", "mensual": "Mensual"}.get(compra.plan, compra.plan)
