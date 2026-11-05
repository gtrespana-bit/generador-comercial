"""Ficha de cliente del panel (Fase 2, B1): gestión, no solo lectura.

El operador ya ve licencias y compras (datos del titular). Este servicio añade
la única pieza que faltaba para convertir el panel en un centro de gestión:

- Notas internas por cliente (``notas_operador``).
- Agregados de uso del cliente (clientes, presupuestos, facturas, pagos) y
  sus movimientos de cobro, **sin abrir el aislamiento multi-tenant**: en
  PostgreSQL se obtienen por funciones ``SECURITY DEFINER`` guardadas con la
  marca de operador; en SQLite (escritorio/pruebas) se consultan directo.

Nunca se devuelve contenido de presupuestos; solo cifras y metadatos.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import func, or_, text

from ..models import (
    Cliente,
    CompraPlan,
    EventoAuditoria,
    Factura,
    Licencia,
    Membresia,
    NotaOperador,
    Organizacion,
    Pago,
    Presupuesto,
    Usuario,
)
from .audit_admin import resumen_auditoria_admin
from .licencias import correos_administradores, licencias_de_organizacion, vence_cadena


def _normalizar_numero(valor):
    if valor is None:
        return 0.0
    if isinstance(valor, Decimal):
        return float(valor)
    try:
        return float(valor)
    except (TypeError, ValueError):
        return 0.0


def _agregados_tenant(db, organizacion_id: int) -> dict:
    """Conteos y totales de uso del cliente (nunca contenido)."""
    if db.get_bind().dialect.name == "postgresql":
        fila = db.execute(
            text("SELECT * FROM cotizat_security.admin_resumen_cliente(:org)"),
            {"org": int(organizacion_id)},
        ).mappings().first()
        if not fila:
            return {
                "clientes": 0, "presupuestos": 0, "facturas": 0, "pagos": 0,
                "total_presupuestado": 0.0, "total_cobrado": 0.0,
                "ultimo_acceso": None,
            }
        return {
            "clientes": int(fila.get("clientes") or 0),
            "presupuestos": int(fila.get("presupuestos") or 0),
            "facturas": int(fila.get("facturas") or 0),
            "pagos": int(fila.get("pagos") or 0),
            "total_presupuestado": _normalizar_numero(fila.get("total_presupuestado")),
            "total_cobrado": _normalizar_numero(fila.get("total_cobrado")),
            "ultimo_acceso": fila.get("ultimo_acceso"),
        }

    clientes = db.query(func.count(Cliente.id)).filter(
        Cliente.organizacion_id == organizacion_id
    ).scalar() or 0
    presupuestos = db.query(func.count(Presupuesto.id)).filter(
        Presupuesto.organizacion_id == organizacion_id
    ).scalar() or 0
    facturas = db.query(func.count(Factura.id)).filter(
        Factura.organizacion_id == organizacion_id
    ).scalar() or 0
    pagos = db.query(func.count(Pago.id)).filter(
        Pago.organizacion_id == organizacion_id
    ).scalar() or 0
    total_presupuestado = db.query(func.coalesce(func.sum(Presupuesto.total_calculado), 0.0)).filter(
        Presupuesto.organizacion_id == organizacion_id,
        Presupuesto.total_calculado > 0,
    ).scalar() or 0.0
    total_cobrado = db.query(func.coalesce(func.sum(Pago.importe), 0.0)).filter(
        Pago.organizacion_id == organizacion_id,
        Pago.estado == "confirmado",
    ).scalar() or 0.0
    ultimo_acceso = db.query(func.max(Usuario.ultimo_acceso_at)).join(
        Membresia, Membresia.usuario_id == Usuario.id
    ).filter(
        Membresia.organizacion_id == organizacion_id,
        Membresia.activa.is_(True),
    ).scalar()
    return {
        "clientes": int(clientes),
        "presupuestos": int(presupuestos),
        "facturas": int(facturas),
        "pagos": int(pagos),
        "total_presupuestado": _normalizar_numero(total_presupuestado),
        "total_cobrado": _normalizar_numero(total_cobrado),
        "ultimo_acceso": ultimo_acceso,
    }


def _cobros_tenant(db, organizacion_id: int) -> list[dict]:
    """Facturas y pagos del cliente para la ficha (centro de cobros B2)."""
    if db.get_bind().dialect.name == "postgresql":
        filas = db.execute(
            text("SELECT * FROM cotizat_security.admin_cobros_cliente(:org)"),
            {"org": int(organizacion_id)},
        ).mappings().all()
        return [
            {
                "id": int(fila.get("id") or 0),
                "tipo": str(fila.get("tipo") or "factura"),
                "numero": str(fila.get("numero") or ""),
                "fecha": fila.get("fecha"),
                "importe": _normalizar_numero(fila.get("importe")),
                "moneda": str(fila.get("moneda") or "USD"),
                "estado": str(fila.get("estado") or ""),
                "descripcion": str(fila.get("descripcion") or ""),
            }
            for fila in filas
        ]

    movimientos: list[dict] = []
    for f in db.query(Factura).filter(
        Factura.organizacion_id == organizacion_id
    ).order_by(Factura.fecha.desc(), Factura.id.desc()).all():
        movimientos.append({
            "id": f.id,
            "tipo": "factura",
            "numero": f.numero,
            "fecha": f.fecha,
            "importe": _normalizar_numero(f.total),
            "moneda": f.moneda or "USD",
            "estado": f.estado or "emitida",
            "descripcion": f.titulo or "",
        })
    for p in db.query(Pago).filter(
        Pago.organizacion_id == organizacion_id
    ).order_by(Pago.fecha.desc(), Pago.id.desc()).all():
        movimientos.append({
            "id": p.id,
            "tipo": "pago",
            "numero": p.referencia or f"pago-{p.id}",
            "fecha": p.fecha,
            "importe": _normalizar_numero(p.importe),
            "moneda": p.moneda or "USD",
            "estado": p.estado or "confirmado",
            "descripcion": p.notas or p.metodo or "",
        })
    return movimientos


def resumen_cliente(
    db,
    organizacion_id: int,
    *,
    hoy: date | None = None,
    limite_eventos: int = 60,
) -> dict | None:
    """Ficha completa de una organización para el operador (B1)."""
    hoy = hoy or date.today()
    org = db.get(Organizacion, organizacion_id)
    if org is None:
        return None

    licencias = licencias_de_organizacion(db, organizacion_id, hoy=hoy)
    vigente = next((l for l in licencias if l.vigente(hoy)), None)
    vence_total = vence_cadena(licencias, hoy) if licencias else None
    dias_restantes = max((vence_total - hoy).days, 0) if vence_total else 0

    compras = (
        db.query(CompraPlan)
        .filter(CompraPlan.organizacion_id == organizacion_id)
        .order_by(CompraPlan.created_at.desc(), CompraPlan.id.desc())
        .all()
    )
    correos = correos_administradores(db, organizacion_id)

    eventos_tenant = (
        db.query(EventoAuditoria)
        .filter(EventoAuditoria.organizacion_id == organizacion_id)
        .order_by(EventoAuditoria.created_at.desc(), EventoAuditoria.id.desc())
        .limit(limite_eventos)
        .all()
    )
    eventos_admin = resumen_auditoria_admin(
        db, organizacion_id=organizacion_id, limite=limite_eventos
    )

    ingresos = sum(l.importe for l in licencias if l.es_ingreso)
    return {
        "organizacion": org,
        "licencias": licencias,
        "vigente": vigente,
        "vence_total": vence_total,
        "dias_restantes": dias_restantes,
        "compras": compras,
        "emails": sorted(set(correos)),
        "agregados": _agregados_tenant(db, organizacion_id),
        "cobros": _cobros_tenant(db, organizacion_id),
        "notas": listar_notas_operador(db, organizacion_id),
        "eventos_cliente": eventos_tenant,
        "eventos_admin": eventos_admin,
        "ingresos": _normalizar_numero(ingresos),
        "hoy": hoy,
    }


def listar_notas_operador(db, organizacion_id: int) -> list[NotaOperador]:
    return (
        db.query(NotaOperador)
        .filter(NotaOperador.organizacion_id == int(organizacion_id))
        .order_by(NotaOperador.created_at.desc(), NotaOperador.id.desc())
        .all()
    )


def crear_nota_operador(
    db,
    organizacion_id: int,
    *,
    contenido: str,
    autor_email: str,
) -> NotaOperador:
    """Crea una nota interna de gestión (B1). Lanza ValueError si vacía."""
    contenido = (contenido or "").strip()
    if not contenido:
        raise ValueError("La nota no puede quedar vacía.")
    if db.get(Organizacion, organizacion_id) is None:
        raise ValueError("El cliente indicado no existe.")
    nota = NotaOperador(
        organizacion_id=int(organizacion_id),
        contenido=contenido[:4000],
        autor_email=str(autor_email or "").lower()[:254],
    )
    db.add(nota)
    db.flush()
    return nota


# ---------------------------------------------------------------------------
# Timeline unificado de cliente
# ---------------------------------------------------------------------------

_TIPO_ICONO = {
    "licencia.concedida": "M5 12h14M12 5l7 7-7 7-7-7 7-7",
    "licencia.renovada": "M13 10V3L4 14h7v7l9-11h-7z",
    "licencia.cancelada": "M6 6l12 12M18 6L6 12",
    "licencia.suspendida": "M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2M9 5a2 2 0 0 0 2 2h2a2 2 0 0 0 2-2M9 5a2 2 0 0 1-2-2h2a2 2 0 0 1 2 2",
    "compra.activada": "M9 19l-6 6 12-12m0 0l-6 6m6-6a6 6 0 0 1-7.744 5.744zm6 12a6 6 0 0 1-7.744-5.744zm0 0L9 16l12 12",
    "compra.rechazada": "M12 9v4m0 4v.01m-6.938-4.938 0 0M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z",
    "nota.creada": "M17 7v4a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1m3-4a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V8a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1m3-4a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-4a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1",
    "crm.cambiado": "M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 0 0 1 1h3m10-11l2 2m-2-2v10a1 1 0 0 1-1 1h-3m-6 0a1 1 0 0 0 1-1v-4a1 1 0 0 1 1-1h3a1 1 0 0 1 1 1v4a1 1 0 0 1-1 1",
    "evento.producto": "M12 6V4m0 2a2 2 0 1 0 0 4m0-4V4m0 2V4m0 2V4m0 2V4m0 2V4m0 2V4m0 2V4m0 2V4m0 2V4m0 2V4",
    "soporte.mensaje": "M3 8l7.89 5.26a2 2 0 0 0 2.22 0L21 8M5 19h14a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2",
    "admin.licencia": "M5 12h14M12 5l7 7-7 7-7-7 7-7",
    "admin.compra": "M9 19l-6 6 12-12m0 0l-6 6m6-6a6 6 0 0 1-7.744 5.744zm6 12a6 6 0 0 1-7.744-5.744zm0 0L9 16l12 12",
    "admin.suspender": "M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2M9 5a2 2 0 0 0 2 2h2a2 2 0 0 0 2-2M9 5a2 2 0 0 1-2-2h2a2 2 0 0 1 2 2",
}


def _evento(
    *,
    cuando,
    tipo: str,
    titulo: str,
    detalle: str = "",
    url: str = "",
    severidad: str = "info",
) -> dict:
    """Un evento del timeline normalizado."""
    return {
        "cuando": cuando,
        "tipo": tipo,
        "titulo": titulo,
        "detalle": detalle,
        "url": url,
        "severidad": severidad,
        "icono": _TIPO_ICONO.get(tipo, _TIPO_ICONO["evento.producto"]),
    }


def timeline_cliente(
    db,
    organizacion_id: int,
    *,
    hoy: date | None = None,
    limite: int = 40,
) -> list[dict]:
    """Línea cronológica unificada de todo lo que ha pasado con un cliente.

    Mezcla en una sola lista ordenada por fecha descendente:

    - **Licencias**: concedidas, renovadas, canceladas, suspendidas.
    - **Compras**: activadas, rechazadas.
    - **Notas internas**: creadas por el equipo.
    - **Cambios de CRM**: cambios de estado comercial.
    - **Eventos de producto**: actividad dentro de la app del cliente.
    - **Acciones de admin**: operaciones tomadas desde el panel.

    Best-effort: si alguna fuente falla, se salta y la línea continúa con lo
    que se pudo leer. Nunca devuelve error fatal.
    """
    hoy = hoy or date.today()
    eventos: list[dict] = []

    # --- Licencias -----------------------------------------------------------
    try:
        licencias = licencias_de_organizacion(db, organizacion_id, hoy=hoy)
        for lic in licencias:
            cuando = lic.created_at or lic.inicio
            if not cuando:
                continue
            if lic.origen == "pago":
                if lic.estado == "activa":
                    eventos.append(_evento(
                        cuando=cuando,
                        tipo="licencia.concedida",
                        titulo="Licencia de pago concedida",
                        detalle=f"{lic.importe:.2f} {lic.moneda or 'USD'} · {lic.duracion or '—'}",
                        url=f"/admin/licencias/{lic.id}",
                        severidad="success",
                    ))
                elif lic.estado == "cancelada":
                    eventos.append(_evento(
                        cuando=cuando,
                        tipo="licencia.cancelada",
                        titulo="Licencia cancelada",
                        detalle="El acceso se cortó para esta licencia.",
                        url=f"/admin/licencias/{lic.id}",
                        severidad="warn",
                    ))
            elif lic.origen in ("prueba", "cortesia", "compensacion"):
                eventos.append(_evento(
                    cuando=cuando,
                    tipo="licencia.concedida",
                    titulo=f"Acceso {lic.origen.capitalize()}",
                    detalle=f"Desde {lic.inicio:%d/%m/%Y} hasta {lic.vence:%d/%m/%Y}",
                    url=f"/admin/licencias/{lic.id}",
                    severidad="info",
                ))
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass

    # --- Compras ------------------------------------------------------------
    try:
        compras = (
            db.query(CompraPlan)
            .filter(CompraPlan.organizacion_id == organizacion_id)
            .order_by(CompraPlan.created_at.desc(), CompraPlan.id.desc())
            .all()
        )
        for c in compras:
            cuando = c.created_at
            if not cuando:
                continue
            if c.estado == "activa":
                eventos.append(_evento(
                    cuando=cuando,
                    tipo="compra.activada",
                    titulo="Compra activada",
                    detalle=f"{c.plan} · {c.importe:.2f} {c.moneda or 'USD'}",
                    url=f"/admin/ingresos?tab=compras&compra={c.id}",
                    severidad="success",
                ))
            elif c.estado == "rechazada":
                eventos.append(_evento(
                    cuando=cuando,
                    tipo="compra.rechazada",
                    titulo="Compra rechazada",
                    detalle=f"{c.plan} · {c.importe:.2f} {c.moneda or 'USD'}",
                    url=f"/admin/ingresos?tab=compras&compra={c.id}",
                    severidad="danger",
                ))
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass

    # --- Notas internas -----------------------------------------------------
    try:
        notas = listar_notas_operador(db, organizacion_id)
        for n in notas:
            if not n.created_at:
                continue
            eventos.append(_evento(
                cuando=n.created_at,
                tipo="nota.creada",
                titulo="Nota interna",
                detalle=n.contenido[:200],
                url=f"/admin/clientes/{organizacion_id}?tab=gestion",
                severidad="info",
            ))
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass

    # --- Eventos de auditoría del cliente (actividad dentro de la app) -------
    try:
        from .audit_admin import resumen_auditoria_admin
        eventos_admin = resumen_auditoria_admin(
            db, organizacion_id=organizacion_id, limite=limite
        )
        for e in eventos_admin:
            cuando = e.get("created_at")
            if not cuando:
                continue
            accion = e.get("accion", "")
            if accion.startswith("cliente."):
                continue  # ya aparecen como acciones de admin abajo
            eventos.append(_evento(
                cuando=cuando,
                tipo="evento.producto",
                titulo=e.get("titulo") or accion.replace("_", " ").title(),
                detalle=e.get("detalle", "")[:200],
                severidad="info",
            ))
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass

    # --- Acciones de admin (auditoría del panel sobre esta org) -------------
    try:
        from .audit_admin import resumen_auditoria_admin
        eventos_admin = resumen_auditoria_admin(
            db, organizacion_id=organizacion_id, limite=limite
        )
        for e in eventos_admin:
            cuando = e.get("created_at")
            if not cuando:
                continue
            accion = e.get("accion", "")
            operador = e.get("operador_email") or "—"
            if accion.startswith("cliente."):
                tipo_map = {
                    "cliente.licencia_concedida": "admin.licencia",
                    "cliente.licencia_renovada": "admin.licencia",
                    "cliente.licencia_cancelada": "admin.licencia",
                    "cliente.licencia_suspendida": "admin.suspender",
                    "cliente.compra_activada": "admin.compra",
                    "cliente.compra_rechazada": "admin.compra",
                }
                tipo = tipo_map.get(accion, "admin.licencia")
                severidad = "success" if "concedida" in accion or "activada" in accion else "warn"
                eventos.append(_evento(
                    cuando=cuando,
                    tipo=tipo,
                    titulo=f"{operador}: {accion.replace('cliente.', '').replace('_', ' ').title()}",
                    detalle=e.get("detalle", "")[:200] or "Acción del panel",
                    url=f"/admin/sistema?tab=auditoria&organizacion_id={organizacion_id}",
                    severidad=severidad,
                ))
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass

    # Ordena por fecha descendente (más reciente primero)
    eventos.sort(key=lambda ev: ev["cuando"] or hoy, reverse=True)
    return eventos[: max(1, int(limite))]
