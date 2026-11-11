"""Buscador global (A3): una sola barra para encontrar clientes y registros."""

from __future__ import annotations

from sqlalchemy import or_
from urllib.parse import quote
from sqlalchemy.orm import joinedload

from ..models import (
    CompraPlan,
    EventoAdmin,
    Licencia,
    Membresia,
    OperadorProducto,
    Organizacion,
    Usuario,
)

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

    # El email era el gran agujero del buscador: el operador tiene el correo del
    # cliente en la mano (un ticket, una transferencia) y escribirlo no devolvía
    # nada porque `usuarios` no estaba en ninguna categoría. Se busca por el
    # correo del usuario y se devuelve la EMPRESA, que es lo que se administra.
    orgs_por_email: dict[int, list[str]] = {}
    for usuario_id, email, organizacion_id in db.query(
        Usuario.id, Usuario.email, Membresia.organizacion_id
    ).join(
        Membresia, Membresia.usuario_id == Usuario.id
    ).filter(
        _filtro_like(Usuario.email, q),
        Membresia.organizacion_id.in_(db.query(Organizacion.id).filter(Organizacion.es_test.is_(False)))
    ).order_by(Usuario.email).limit(LIMITE_CATEGORIA * 4).all():
        orgs_por_email.setdefault(organizacion_id, []).append(email)

    for org in db.query(Organizacion).filter(
        Organizacion.es_test.is_(False),
        _filtro_like(Organizacion.nombre, q)
        | _filtro_like(Organizacion.slug, q)
    ).order_by(Organizacion.nombre).limit(LIMITE_CATEGORIA).all():
        resultados.append({
            "tipo": "cliente",
            "titulo": org.nombre,
            "subtitulo": org.slug,
            "url": f"/admin/clientes/{org.id}",
        })

    encontradas = {r["url"] for r in resultados}
    for organizacion_id, emails in orgs_por_email.items():
        org = db.get(Organizacion, organizacion_id)
        if org is None or f"/admin/clientes/{org.id}" in encontradas:
            continue
        resultados.insert(0, {
            "tipo": "cliente",
            "titulo": org.nombre,
            "subtitulo": f"por email · {emails[0]}",
            # Lleva al directorio ya filtrado por ese correo: si la persona
            # administra dos empresas, se ven las dos juntas.
            "url": f"/admin/clientes?tab=directorio&q={quote(emails[0], safe='')}",
        })

    for lic in db.query(Licencia).join(
        Organizacion, Licencia.organizacion_id == Organizacion.id
    ).filter(
        Organizacion.es_test.is_(False),
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
            # La ficha del cliente es donde la licencia se ve entera (cadena,
            # recibo, renovación). Antes llevaba a la lista filtrada por nombre y
            # el operador tenía que volver a buscar la fila.
            "url": f"/admin/clientes/{lic.organizacion_id}?tab=acceso",
        })

    for compra in db.query(CompraPlan).join(
        Organizacion, CompraPlan.organizacion_id == Organizacion.id
    ).filter(
        Organizacion.es_test.is_(False),
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
            # `?compra=` abre exactamente esa compra, no la cola entera: el
            # buscador ya sabía cuál era y la obligaba a buscar a ojo.
            "url": f"/admin/ingresos?tab=compras&estado=todas&compra={compra.id}",
        })

    for op in db.query(OperadorProducto).filter(
        _filtro_like(OperadorProducto.email, q)
        | _filtro_like(OperadorProducto.notas, q)
    ).order_by(OperadorProducto.email).limit(LIMITE_CATEGORIA).all():
        resultados.append({
            "tipo": "operador",
            "titulo": op.email,
            "subtitulo": f"{op.etiqueta_rol} · {'activo' if op.activo else 'suspendido'}",
            "url": "/admin/sistema?tab=equipo",
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
            "url": f"/admin/sistema?tab=auditoria&accion={quote(evento.accion, safe='')}",
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
