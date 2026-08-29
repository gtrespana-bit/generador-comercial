"""Buscador global (A3): una sola barra para encontrar clientes y registros."""

from __future__ import annotations

from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from ..models import CompraPlan, EventoAdmin, Licencia, OperadorProducto, Organizacion

#: Límite por categoría para que la paleta sea instantánea.
LIMITE_CATEGORIA = 8
LIMITE_TOTAL = 48


def _filtro_like(expresion, q: str):
    return expresion.ilike(f"%{q}%")


def buscar_global(db, q: str, *, limite: int = LIMITE_TOTAL) -> list[dict]:
    """Devuelve coincidencias seguras para el panel del operador.

    Nunca consulta tablas de tenant (presupuestos, clientes, pagos): esas
    siguen bajo RLS de organización. El operador busca clientes, licencias,
    compras de plan, equipo y eventos del panel.
    """
    q = (q or "").strip()
    if not q:
        return []
    resultados: list[dict] = []

    for org in db.query(Organizacion).filter(
        _filtro_like(Organizacion.nombre, q)
        | _filtro_like(Organizacion.slug, q)
    ).order_by(Organizacion.nombre).limit(LIMITE_CATEGORIA).all():
        resultados.append({
            "tipo": "cliente",
            "titulo": org.nombre,
            "subtitulo": org.slug,
            "url": f"/admin/clientes/{org.id}",
        })

    for lic in db.query(Licencia).join(
        Organizacion, Licencia.organizacion_id == Organizacion.id
    ).filter(
        _filtro_like(Organizacion.nombre, q)
        | _filtro_like(Organizacion.slug, q)
        | Licencia.creada_por_email.ilike(f"%{q}%")
        | Licencia.referencia.ilike(f"%{q}%")
    ).order_by(Licencia.created_at.desc()).limit(LIMITE_CATEGORIA).all():
        nombre = lic.organizacion.nombre if lic.organizacion else "?"
        resultados.append({
            "tipo": "licencia",
            "titulo": f"Licencia · {nombre}",
            "subtitulo": f"{lic.estado} · vence {lic.vence}",
            "url": f"/admin/licencias?licencia={lic.id}",
        })

    for compra in db.query(CompraPlan).join(
        Organizacion, CompraPlan.organizacion_id == Organizacion.id
    ).filter(
        _filtro_like(Organizacion.nombre, q)
        | CompraPlan.creada_por_email.ilike(f"%{q}%")
        | CompraPlan.comprobante_nombre.ilike(f"%{q}%")
        | CompraPlan.datos_verificacion.ilike(f"%{q}%")
    ).order_by(CompraPlan.created_at.desc()).limit(LIMITE_CATEGORIA).all():
        nombre = compra.organizacion.nombre if compra.organizacion else "?"
        resultados.append({
            "tipo": "compra",
            "titulo": f"Compra #{compra.id} · {nombre}",
            "subtitulo": f"{compra.plan} · {compra.estado}",
            "url": f"/admin/compras?compra={compra.id}",
        })

    for op in db.query(OperadorProducto).filter(
        _filtro_like(OperadorProducto.email, q)
        | _filtro_like(OperadorProducto.notas, q)
    ).order_by(OperadorProducto.email).limit(LIMITE_CATEGORIA).all():
        resultados.append({
            "tipo": "operador",
            "titulo": op.email,
            "subtitulo": f"{op.etiqueta_rol} · {'activo' if op.activo else 'suspendido'}",
            "url": f"/admin/equipo?operador={op.id}",
        })

    for evento in db.query(EventoAdmin).filter(
        _filtro_like(EventoAdmin.operador_email, q)
        | _filtro_like(EventoAdmin.accion, q)
        | _filtro_like(EventoAdmin.detalle, q)
    ).order_by(EventoAdmin.created_at.desc()).limit(LIMITE_CATEGORIA).all():
        resultados.append({
            "tipo": "auditoria",
            "titulo": evento.accion,
            "subtitulo": f"{evento.operador_email} · {evento.created_at:%d/%m/%Y %H:%M}",
            "url": f"/admin/auditoria?accion={evento.accion}",
        })

    resultados.sort(key=lambda r: (_orden_tipo(r["tipo"]), r["titulo"].lower()))
    return resultados[:limite]


def _orden_tipo(tipo: str) -> int:
    return {
        "cliente": 0,
        "licencia": 1,
        "compra": 2,
        "operador": 3,
        "auditoria": 4,
    }.get(tipo, 9)
