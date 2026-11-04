"""Qué hace cada empresa dentro del producto, contado para el operador.

El panel sabía cuánto paga cada cliente y hasta cuándo, pero no **qué está
haciendo con la app**: si entra, si crea presupuestos, si los reenvía, y sobre
todo qué toca cuando algo no le cuadra (precios, textos, cantidades). Ese dato
es el que dice dónde falla el producto.

Tres piezas, con responsabilidades separadas:

``instantanea`` / ``resumen_cambios``
    Funciones puras (sin base de datos) que comparan el presupuesto *antes* de
    guardar con lo que trae el formulario y devuelven un recuento legible:
    partidas nuevas, eliminadas, precios cambiados, nombres reescritos,
    cantidades corregidas. Se calculan en el guardado y se anotan como evento
    de auditoría, que es la tabla que el panel ya puede leer con la marca de
    operador (política ``cotizat_evento_select_operator``).

``anotar_creacion`` / ``anotar_edicion``
    Best-effort, después del commit del cambio real. Igual que el resto de
    avisos internos: si el registro falla, el usuario no se entera y no se
    pierde su trabajo.

``actividad_organizacion``
    Lo que pinta la ficha del cliente: cifras de uso de la ventana, «qué
    modifica más» y una cronología en castellano (no códigos internos).
"""
from __future__ import annotations

import json
import logging
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta

from ..models import EventoAuditoria, EventoProducto
from .auditoria import registrar_evento

log = logging.getLogger("cotizat.actividad")

#: Acción → (etiqueta para el operador, tono visual). El tono se usa como clase
#: de badge; ``info`` es lo neutro y ``warn`` lo que conviene mirar.
ACCIONES: dict[str, tuple[str, str]] = {
    # Ciclo de vida del presupuesto: lo que el titular quiere ver de un vistazo.
    "presupuesto.creado": ("Creó un presupuesto", "info"),
    "presupuesto.editado": ("Modificó un presupuesto", "info"),
    "presupuesto.estado": ("Cambió el estado de un presupuesto", "ok"),
    "presupuesto.enviado": ("Envió el presupuesto al cliente", "ok"),
    "presupuesto.pdf_descargado": ("Descargó el PDF", "info"),
    "presupuesto.duplicado": ("Duplicó un presupuesto", "info"),
    "presupuesto.eliminado": ("Eliminó un presupuesto", "warn"),
    # Catálogo: aquí se ve dónde el producto no acierta con el precio.
    "catalogo.precio_partida": ("Corrigió el precio de una partida", "warn"),
    "catalogo.precios_ajustados": ("Ajustó precios del catálogo en bloque", "warn"),
    "catalogo.precios_reparados": ("Reparó precios imposibles", "warn"),
    "partida.creada": ("Creó una partida en el catálogo", "info"),
    "partida.actualizada": ("Editó una partida del catálogo", "info"),
    "partida.eliminada": ("Eliminó una partida del catálogo", "warn"),
    "producto.creado": ("Creó un producto", "info"),
    "producto.actualizado": ("Editó un producto", "info"),
    "recurso.creado": ("Creó un recurso", "info"),
    "recurso.actualizado": ("Editó un recurso", "info"),
    "recurso.eliminado": ("Eliminó un recurso", "warn"),
    # Resto de la operación diaria.
    "cliente.creado": ("Creó un cliente", "info"),
    "cliente.actualizado": ("Editó un cliente", "info"),
    "cliente.eliminado": ("Eliminó un cliente", "warn"),
    "configuracion.actualizada": ("Cambió la configuración de su empresa", "info"),
    "factura.estado": ("Cambió el estado de un documento de cobro", "info"),
    "equipo.invitacion_enviada": ("Invitó a alguien al equipo", "ok"),
    "importacion.confirmada": ("Importó un presupuesto (CYPE/BC3)", "info"),
    "asistente.consulta": ("Preguntó al asistente", "info"),
    "datos.respaldo_descargado": ("Descargó un respaldo", "info"),
    "cuenta.clave_cambiada": ("Cambió su contraseña", "info"),
    "sesion.login": ("Inició sesión", "info"),
    "sesion.logout": ("Cerró sesión", "info"),
}

#: Acciones que cuentan como «trabajo real» en la ficha. El latido y la
#: presencia se registran solos y no dicen nada del uso: se excluyen.
RUIDO = frozenset({"actividad.diaria", "sesion.activa", "sesion.login", "sesion.logout"})

#: Campos que se cuentan al comparar una edición de presupuesto.
CAMPOS_TEXTO = ("nombre", "descripcion")
CAMPOS_NUMERO = ("precio", "cantidad")


def etiqueta_accion(accion: str) -> tuple[str, str]:
    """Nombre legible y tono de una acción; si es nueva, se humaniza el código.

    El catálogo cerrado evita que un evento sin etiqueta aparezca como
    ``presupuesto.editado`` (el operador no debería leer nombres de tabla).
    """
    accion = str(accion or "").strip()
    if accion in ACCIONES:
        return ACCIONES[accion]
    if not accion:
        return ("Actividad", "info")
    dominio, _, verbo = accion.partition(".")
    texto = (verbo or dominio).replace("_", " ").strip().capitalize()
    return (f"{texto} ({dominio})" if verbo else texto, "info")


# ---------------------------------------------------------------------------
# Comparación de una edición (puro: sin base de datos, se puede probar aislado)
# ---------------------------------------------------------------------------


def instantanea(presupuesto) -> dict:
    """Estado mínimo del presupuesto justo antes de aplicar el formulario."""
    partidas = {}
    for capitulo in presupuesto.capitulos:
        for item in capitulo.partidas:
            partidas[item.id] = {
                "nombre": item.nombre or "",
                "descripcion": item.descripcion or "",
                "precio": float(item.precio_unitario or 0),
                "cantidad": float(item.cantidad or 0),
                "unidad": item.unidad or "",
            }
    return {
        "partidas": partidas,
        "capitulos": len(presupuesto.capitulos),
        "total": float(getattr(presupuesto, "total_calculado", 0) or 0),
        "estado": str(presupuesto.estado or ""),
        "titulo": str(presupuesto.titulo or ""),
        "moneda": str(presupuesto.moneda or ""),
    }


def _texto(valor) -> str:
    return str(valor if valor is not None else "").strip()


def _numero(valor) -> float:
    try:
        return float(valor or 0)
    except (TypeError, ValueError):
        return 0.0


def resumen_cambios(antes: dict, partidas: list[dict], capitulos: list[dict]) -> dict:
    """Qué cambió entre la instantánea y lo que trae el formulario.

    Trabaja sobre los datos del formulario (no sobre el ORM), porque en ese
    momento las partidas nuevas todavía no tienen id. Cuenta, no guarda texto:
    el detalle de auditoría nunca lleva el contenido del cliente.
    """
    previas: dict[int, dict] = dict((antes or {}).get("partidas") or {})
    # Solo las líneas con nombre llegan a guardarse (el editor deja filas vacías).
    vigentes = [p for p in partidas if _texto(p.get("nombre"))]
    ids_vigentes = {p.get("id") for p in vigentes if p.get("id")}

    conteo = Counter()
    partidas_nuevas = 0
    for partida in vigentes:
        anterior = previas.get(partida.get("id"))
        if anterior is None:
            partidas_nuevas += 1
            continue
        if any(_texto(partida.get(campo)) != _texto(anterior.get(campo)) for campo in CAMPOS_TEXTO):
            conteo["textos"] += 1
        for campo in CAMPOS_NUMERO:
            if abs(_numero(partida.get(campo)) - _numero(anterior.get(campo))) > 1e-9:
                if campo == "precio":
                    conteo["precios"] += 1
                else:
                    conteo["cantidades"] += 1
        if _texto(partida.get("unidad")) != _texto(anterior.get("unidad")):
            conteo["unidades"] += 1

    eliminadas = len([pid for pid in previas if pid not in ids_vigentes])
    cap_ahora = len([c for c in (capitulos or []) if _texto(c.get("nombre"))])
    # ``instantanea`` guarda el recuento; se acepta también la colección por si
    # otro llamador pasa los capítulos enteros (contar mal sería peor que no
    # contar: el panel diría «eliminaste un capítulo» sin que nadie lo tocara).
    cap_previos = (antes or {}).get("capitulos")
    if isinstance(cap_previos, (list, tuple, set, dict)):
        cap_antes = len(cap_previos)
    else:
        cap_antes = int(_numero(cap_previos))

    return {
        "partidas_nuevas": partidas_nuevas,
        "partidas_eliminadas": eliminadas,
        "precios": conteo["precios"],
        "cantidades": conteo["cantidades"],
        "textos": conteo["textos"],
        "unidades": conteo["unidades"],
        "capitulos_nuevos": max(cap_ahora - cap_antes, 0),
        "capitulos_eliminados": max(cap_antes - cap_ahora, 0),
        "partidas_total": len(vigentes),
        "total_antes": float((antes or {}).get("total") or 0),
        "estado_antes": str((antes or {}).get("estado") or ""),
        "titulo_antes": str((antes or {}).get("titulo") or ""),
        "moneda_antes": str((antes or {}).get("moneda") or ""),
    }


def hay_cambios(resumen: dict) -> bool:
    """¿Merece la pena anotar la edición? Guardar sin tocar nada no es evento."""
    claves = (
        "partidas_nuevas", "partidas_eliminadas", "precios", "cantidades",
        "textos", "unidades", "capitulos_nuevos", "capitulos_eliminados",
    )
    if any(int(resumen.get(clave) or 0) for clave in claves):
        return True
    return abs(_numero(resumen.get("total_antes")) - _numero(resumen.get("total_despues"))) > 0.005


def texto_resumen(resumen: dict) -> str:
    """Frase corta con lo que se tocó, para la cronología y las tarjetas."""
    piezas = []
    for clave, singular, plural in (
        ("partidas_nuevas", "partida nueva", "partidas nuevas"),
        ("partidas_eliminadas", "partida eliminada", "partidas eliminadas"),
        ("precios", "precio corregido", "precios corregidos"),
        ("cantidades", "cantidad corregida", "cantidades corregidas"),
        ("textos", "texto reescrito", "textos reescritos"),
        ("unidades", "unidad cambiada", "unidades cambiadas"),
    ):
        valor = int(resumen.get(clave) or 0)
        if valor:
            piezas.append(f"{valor} {singular if valor == 1 else plural}")
    return ", ".join(piezas)


# ---------------------------------------------------------------------------
# Registro (best-effort, siempre después del commit del cambio real)
# ---------------------------------------------------------------------------


def _detalle_json(detalle: dict) -> str:
    try:
        return json.dumps(detalle, ensure_ascii=False, default=str)[:2000]
    except (TypeError, ValueError):  # pragma: no cover - datos no serializables
        return "{}"


def anotar_creacion(db, presupuesto, *, origen: str = "") -> bool:
    """Deja constancia del alta: sin esto, «creó un presupuesto» no existía.

    ``origen`` distingue el alta de la copia (``duplicado``, o de la plantilla
    del ejemplo): las dos crean trabajo, pero solo una parte de cero.
    """
    try:
        try:
            capitulos = list(presupuesto.capitulos or [])
            partidas = sum(len(list(cap.partidas or [])) for cap in capitulos)
        except Exception:  # relación no cargada: el evento vale sin el recuento
            capitulos, partidas = [], 0
        detalle = {
            "numero": str(presupuesto.numero or ""),
            "capitulos": len(capitulos),
            "partidas": partidas,
            "total": round(float(getattr(presupuesto, "total_calculado", 0) or 0), 2),
            "moneda": str(presupuesto.moneda or ""),
        }
        if origen:
            detalle["origen"] = origen
        return registrar_evento(
            db,
            "presupuesto.creado",
            entidad="presupuesto",
            entidad_id=presupuesto.id,
            detalle=detalle,
        )
    except Exception:  # pragma: no cover - la auditoría nunca rompe el guardado
        log.warning("No se pudo anotar la creación del presupuesto.", exc_info=True)
        return False


def anotar_edicion(db, presupuesto, antes: dict, resumen: dict) -> bool:
    """Anota la edición con su resumen de cambios, si hubo alguno."""
    try:
        resumen = dict(resumen or {})
        resumen["total_despues"] = round(
            float(getattr(presupuesto, "total_calculado", 0) or 0), 2
        )
        if not hay_cambios(resumen):
            return False
        resumen["resumen"] = texto_resumen(resumen)
        resumen["numero"] = str(presupuesto.numero or "")
        resumen["moneda"] = str(presupuesto.moneda or "")
        return registrar_evento(
            db,
            "presupuesto.editado",
            entidad="presupuesto",
            entidad_id=presupuesto.id,
            detalle=resumen,
        )
    except Exception:  # pragma: no cover - idem
        log.warning("No se pudo anotar la edición del presupuesto.", exc_info=True)
        return False


# ---------------------------------------------------------------------------
# Lectura para el panel: uso, «qué modifica» y cronología legible
# ---------------------------------------------------------------------------


def _desde(dias: int) -> datetime:
    return datetime.utcnow() - timedelta(days=max(int(dias or 30), 1))


def _detalle(evento) -> dict:
    try:
        datos = json.loads(evento.detalle or "{}")
    except (TypeError, ValueError):
        return {}
    return datos if isinstance(datos, dict) else {}


def _resumen_en_texto(accion: str, detalle: dict) -> str:
    """Detalle corto y legible; nunca vuelca el JSON crudo en la tabla."""
    if not detalle:
        return ""
    if accion == "presupuesto.editado":
        return str(detalle.get("resumen") or "")
    if accion == "presupuesto.creado":
        piezas = []
        if detalle.get("origen") == "duplicado":
            piezas.append("copia")
        if detalle.get("partidas") is not None:
            piezas.append(f"{detalle['partidas']} partidas")
        if detalle.get("total"):
            piezas.append(f"{_numero(detalle['total']):,.2f} {detalle.get('moneda') or ''}".strip())
        return " · ".join(piezas)
    if accion == "presupuesto.estado":
        return f"{detalle.get('de', '?')} → {detalle.get('a', '?')}"
    if accion in ("catalogo.precio_partida",):
        return f"{_numero(detalle.get('de')):,.2f} → {_numero(detalle.get('a')):,.2f}"
    if accion in ("presupuesto.enviado",):
        return str(detalle.get("destinatario") or "")
    if detalle.get("a") is not None and detalle.get("de") is not None:
        return f"{detalle['de']} → {detalle['a']}"
    return ", ".join(f"{clave}: {valor}" for clave, valor in list(detalle.items())[:3])[:160]


def _url_de(accion: str, entidad: str, entidad_id, organizacion_id: int) -> str:
    """A dónde lleva el evento: siempre a la pestaña de la ficha donde se amplía."""
    if entidad == "presupuesto" or accion.startswith("presupuesto."):
        return f"/admin/clientes/{organizacion_id}?tab=presupuestos"
    if entidad == "factura":
        return f"/admin/clientes/{organizacion_id}?tab=cobros"
    if entidad in ("partida", "producto", "recurso") or accion.startswith("catalogo."):
        return f"/admin/clientes/{organizacion_id}?tab=presupuestos"
    return ""


def actividad_organizacion(db, organizacion_id: int, *, dias: int = 30) -> dict:
    """Uso de una empresa en la ventana: cifras, «qué modifica» y cronología.

    Lee ``eventos_auditoria`` (quién hizo qué, con detalle) y
    ``eventos_producto`` (uso y presencia). Ambas tablas permiten SELECT al
    operador por RLS, así que no hace falta abrir ninguna tabla de tenant.
    """
    desde = _desde(dias)
    eventos = (
        db.query(EventoAuditoria)
        .filter(
            EventoAuditoria.organizacion_id == organizacion_id,
            EventoAuditoria.created_at >= desde,
        )
        .order_by(EventoAuditoria.created_at.desc(), EventoAuditoria.id.desc())
        .limit(400)
        .all()
    )
    producto = (
        db.query(EventoProducto)
        .filter(
            EventoProducto.organizacion_id == organizacion_id,
            EventoProducto.created_at >= desde,
        )
        .order_by(EventoProducto.created_at.desc(), EventoProducto.id.desc())
        .limit(400)
        .all()
    )

    por_accion: dict[str, dict] = {}
    cambios = Counter()
    ediciones = 0
    partidas_por_edicion: list[int] = []
    cronologia: list[dict] = []
    actores = Counter()
    dias_uso = set()

    for evento in eventos:
        etiqueta, tono = etiqueta_accion(evento.accion)
        detalle = _detalle(evento)
        por_accion.setdefault(evento.accion, {
            "accion": evento.accion,
            "etiqueta": etiqueta,
            "tono": tono,
            "veces": 0,
            "ultima": evento.created_at,
        })
        por_accion[evento.accion]["veces"] += 1
        if evento.actor_email:
            actores[evento.actor_email] += 1
        if evento.created_at:
            dias_uso.add(evento.created_at.date())
        if evento.accion == "presupuesto.editado":
            ediciones += 1
            partidas_por_edicion.append(int(detalle.get("partidas_total") or 0))
            for clave in ("partidas_nuevas", "partidas_eliminadas", "precios",
                          "cantidades", "textos", "unidades", "capitulos_nuevos",
                          "capitulos_eliminados"):
                cambios[clave] += int(detalle.get(clave) or 0)
        cronologia.append({
            "cuando": evento.created_at,
            "accion": evento.accion,
            "etiqueta": etiqueta,
            "tono": tono,
            "actor": evento.actor_email or "",
            "detalle": _resumen_en_texto(evento.accion, detalle),
            "url": _url_de(evento.accion, evento.entidad or "", evento.entidad_id, organizacion_id),
            "origen": "app",
        })

    for evento in producto:
        if evento.accion in RUIDO:
            if evento.accion == "actividad.diaria" and evento.created_at:
                dias_uso.add(evento.created_at.date())
            continue
        etiqueta, tono = etiqueta_accion(evento.accion)
        detalle = _detalle(evento)
        por_accion.setdefault(evento.accion, {
            "accion": evento.accion,
            "etiqueta": etiqueta,
            "tono": tono,
            "veces": 0,
            "ultima": evento.created_at,
        })
        por_accion[evento.accion]["veces"] += 1
        if evento.actor_email:
            actores[evento.actor_email] += 1
        if evento.created_at:
            dias_uso.add(evento.created_at.date())
        cronologia.append({
            "cuando": evento.created_at,
            "accion": evento.accion,
            "etiqueta": etiqueta,
            "tono": tono,
            "actor": evento.actor_email or "",
            "detalle": _resumen_en_texto(evento.accion, detalle),
            "url": _url_de(evento.accion, "", None, organizacion_id),
            "origen": "producto",
        })

    cronologia.sort(key=lambda fila: (fila["cuando"] or datetime.min), reverse=True)

    creados = por_accion.get("presupuesto.creado", {}).get("veces", 0)
    enviados = por_accion.get("presupuesto.enviado", {}).get("veces", 0)
    pdfs = por_accion.get("presupuesto.pdf_descargado", {}).get("veces", 0)
    kpis = {
        "dias": max(int(dias or 30), 1),
        "eventos": len(eventos) + len([e for e in producto if e.accion not in RUIDO]),
        "presupuestos_creados": creados,
        "presupuestos_editados": ediciones,
        "presupuestos_enviados": enviados,
        "pdfs": pdfs,
        "dias_uso": len(dias_uso),
        "usuarios_activos": len(actores),
        "ultima_actividad": cronologia[0]["cuando"] if cronologia else None,
        "tasa_edicion": (ediciones / creados) if creados else 0.0,
    }
    total_cambios = sum(cambios.get(clave, 0) for clave in (
        "partidas_nuevas", "partidas_eliminadas", "precios", "cantidades",
        "textos", "unidades",
    ))
    return {
        "dias": kpis["dias"],
        "kpis": kpis,
        "cambios": {
            **{clave: int(cambios.get(clave, 0)) for clave in (
                "partidas_nuevas", "partidas_eliminadas", "precios", "cantidades",
                "textos", "unidades", "capitulos_nuevos", "capitulos_eliminados",
            )},
            "ediciones": ediciones,
            "total": total_cambios,
            "media_partidas": (
                sum(partidas_por_edicion) / len(partidas_por_edicion)
                if partidas_por_edicion else 0.0
            ),
        },
        "por_accion": sorted(
            por_accion.values(), key=lambda fila: (-fila["veces"], fila["etiqueta"])
        ),
        "actores": [{"email": email, "veces": veces} for email, veces in actores.most_common(6)],
        "cronologia": cronologia[:60],
        "hoy": date.today(),
    }


def totales_cambios(db, *, dias: int = 30) -> dict:
    """«Qué se modifica más» en **todas** las empresas, para la analítica.

    Agrega el detalle de los eventos ``presupuesto.editado``: si en 100
    ediciones 70 tocan precios y 12 solo textos, el problema del producto está
    en el precio de partida, no en el editor de texto.
    """
    desde = _desde(dias)
    eventos = (
        db.query(EventoAuditoria)
        .filter(
            EventoAuditoria.accion.in_(("presupuesto.editado", "presupuesto.creado")),
            EventoAuditoria.created_at >= desde,
        )
        .all()
    )
    cambios = Counter()
    ediciones = 0
    por_organizacion: dict[int, int] = defaultdict(int)
    for evento in eventos:
        detalle = _detalle(evento)
        if evento.accion == "presupuesto.editado":
            ediciones += 1
            if evento.organizacion_id:
                por_organizacion[int(evento.organizacion_id)] += 1
            for clave in ("partidas_nuevas", "partidas_eliminadas", "precios",
                          "cantidades", "textos", "unidades"):
                cambios[clave] += int(detalle.get(clave) or 0)
    filas = [
        {"clave": clave, "total": total}
        for clave, total in cambios.most_common()
        if total
    ]
    maximo = max((fila["total"] for fila in filas), default=0)
    for fila in filas:
        fila["pct"] = (fila["total"] / maximo * 100) if maximo else 0
    return {
        "dias": max(int(dias or 30), 1),
        "ediciones": ediciones,
        "filas": filas,
        "organizaciones": dict(por_organizacion),
    }
