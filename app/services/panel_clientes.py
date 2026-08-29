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
