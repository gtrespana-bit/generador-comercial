"""Herramientas deterministas del asistente CotizaT.

Estas funciones consultan exclusivamente la base de datos de la organización
activa. No consumen tokens ni dependen de Groq: el modelo generativo se reserva
para conversación y redacción, mientras búsquedas, revisiones y packs devuelven
datos verificables y enlaces accionables.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any
from urllib.parse import quote_plus, urlencode

from sqlalchemy.orm import Session

from .busqueda_catalogo import normalizar

log = logging.getLogger("cotizat")

_BUSCAR_RE = re.compile(
    r"\b(?:busca|buscar|buscame|encuentra|encontrar|localiza|muestra|dame|cual|cuales|que)\w*\b"
    # Inglés.
    r"|\b(?:find|search|look\s+up|locate|show|list|which|what)\w*\b",
    re.IGNORECASE,
)

_TIPOS_ENTIDAD = {
    "cliente": ("cliente", "clientes", "client", "clients", "customer", "customers"),
    "presupuesto": ("presupuesto", "presupuestos", "cotizacion", "cotizaciones",
                    "estimate", "estimates", "quote", "quotes", "proposal", "proposals"),
    "producto": ("producto", "productos", "material", "materiales",
                 "product", "products"),
    "recurso": ("recurso", "recursos", "insumo", "insumos",
                "resource", "resources"),
}

# Cómo se nombra cada tipo en pantalla, por idioma.
_ETIQUETAS_ENTIDAD = {
    "es": {"cliente": "clientes", "presupuesto": "presupuestos",
           "producto": "productos", "recurso": "recursos"},
    "en": {"cliente": "clients", "presupuesto": "estimates",
           "producto": "products", "recurso": "resources"},
}


def _es_ingles(idioma) -> bool:
    """Las variantes regionales (/en-mx/) comparten vocabulario."""
    return str(idioma or "es").strip().lower().startswith("en")

_STOP_BUSQUEDA = frozenset({
    "a", "al", "algo", "cual", "cuales", "como", "con", "de", "del", "dame",
    "el", "en", "encuentra", "encontrar", "es", "ese", "esta", "este", "hay",
    "la", "las", "localiza", "los", "me", "mi", "muestra", "que", "quiero",
    "se", "tengo", "tiene", "tu", "un", "una", "unos", "unas", "y", "por",
    "busca", "buscar", "buscame",
    "cliente", "clientes", "presupuesto", "presupuestos", "cotizacion",
    "cotizaciones", "producto", "productos", "material", "materiales",
    "recurso", "recursos", "insumo", "insumos",
    # Inglés: las mismas palabras vacías al pedir una búsqueda.
    "a", "an", "the", "which", "what", "for", "of", "to", "need", "want",
    "find", "search", "look", "up", "locate", "show", "give", "please",
    "could", "would", "there", "any", "my", "is", "are", "and", "or", "with",
    "it", "this", "that", "do", "does", "can", "tell", "list",
    "client", "clients", "customer", "customers", "estimate", "estimates",
    "quote", "quotes", "proposal", "proposals", "product", "products",
    "resource", "resources",
})


def _seguro(valor: Any) -> str:
    """Texto de datos privados que no puede convertirse en Markdown activo."""
    return re.sub(r"[\[\]*`]", "", str(valor or "")).strip()


def _contexto_presupuesto_id(contexto: dict[str, Any] | None) -> int | None:
    try:
        valor = int((contexto or {}).get("presupuesto_id") or 0)
    except (TypeError, ValueError):
        return None
    return valor if valor > 0 else None


def _editor_abierto(contexto: dict[str, Any] | None) -> bool:
    pagina = str((contexto or {}).get("pagina") or "")
    return bool(
        _contexto_presupuesto_id(contexto)
        and re.fullmatch(r"/presupuestos/\d+/editar", pagina)
    )


def contexto_pagina_verificado(
    db: Session,
    contexto: dict[str, Any] | None,
) -> str:
    """Contexto corto para el prompt, validado contra el tenant.

    El navegador solo aporta la ruta y un posible id. Los nombres, estado y
    número se vuelven a leer en servidor para no confiar en texto manipulable.
    """
    if not contexto:
        return ""
    pagina = str(contexto.get("pagina") or "").strip()[:240]
    if not re.fullmatch(r"/[A-Za-z0-9_./-]*", pagina):
        pagina = ""
    lineas = []
    if pagina:
        lineas.append(f"- Ruta abierta: {pagina}")
    presupuesto_id = _contexto_presupuesto_id(contexto)
    if presupuesto_id:
        from ..models import Presupuesto

        presupuesto = db.get(Presupuesto, presupuesto_id)
        if presupuesto is not None:
            lineas.extend((
                f"- Presupuesto abierto verificado: {presupuesto.numero}",
                f"- Proyecto: {presupuesto.titulo or 'Sin título'}",
                f"- Estado: {presupuesto.estado}",
            ))
    if not lineas:
        return ""
    return "CONTEXTO DE LA PANTALLA ACTUAL:\n" + "\n".join(lineas)


def _detectar_tipo_entidad(consulta: str) -> str | None:
    texto = normalizar(consulta)
    if not _BUSCAR_RE.search(texto):
        return None
    for tipo, nombres in _TIPOS_ENTIDAD.items():
        if any(re.search(rf"\b{re.escape(nombre)}\b", texto) for nombre in nombres):
            return tipo
    return None


def _termino_entidad(consulta: str) -> str:
    originales = re.findall(r"[\w@.+-]+", str(consulta or "").lower(), flags=re.UNICODE)
    salida = []
    vistos = set()
    for original in originales:
        limpio = normalizar(original)
        if not limpio or limpio in _STOP_BUSQUEDA or limpio in vistos:
            continue
        vistos.add(limpio)
        salida.append(original)
        if len(salida) >= 6:
            break
    return " ".join(salida)


def _puntuar_texto(termino: str, campos: list[Any]) -> tuple[int, int]:
    consulta = normalizar(termino)
    tokens = consulta.split()
    texto = normalizar(" ".join(str(c or "") for c in campos))
    if not tokens or not texto:
        return 0, 0
    encontrados = sum(1 for token in tokens if token in texto)
    score = encontrados * 100
    if consulta and consulta in texto:
        score += 250
    primer_campo = normalizar(campos[0] if campos else "")
    if consulta and primer_campo.startswith(consulta):
        score += 150
    elif consulta and consulta in primer_campo:
        score += 80
    return encontrados, score


def _seleccionar_coincidencias(filas: list, termino: str, campos_fn, limite: int = 5) -> list:
    puntuadas = []
    total_tokens = max(1, len(normalizar(termino).split()))
    for fila in filas:
        encontrados, score = _puntuar_texto(termino, campos_fn(fila))
        if encontrados:
            puntuadas.append((encontrados, score, fila))
    exactas = [p for p in puntuadas if p[0] == total_tokens]
    seleccion = exactas
    if not seleccion and puntuadas:
        mejor = max(p[0] for p in puntuadas)
        seleccion = [p for p in puntuadas if p[0] == mejor]
    seleccion.sort(key=lambda p: (-p[1], str(campos_fn(p[2])[0] or "").lower()))
    return [p[2] for p in seleccion[:limite]]


def _buscar_entidad(db: Session, tipo: str, termino: str) -> list[dict[str, Any]]:
    from ..models import Cliente, Presupuesto, Producto, Recurso

    if tipo == "cliente":
        filas = db.query(Cliente).all()
        seleccion = _seleccionar_coincidencias(
            filas, termino,
            lambda c: [c.nombre, c.rif, c.email, c.telefono, c.direccion],
        )
        return [{
            "titulo": c.nombre,
            "detalle": " · ".join(v for v in (c.rif, c.telefono, c.email) if v) or "Sin datos de contacto",
            "url": f"/clientes/{c.id}/editar",
        } for c in seleccion]

    if tipo == "presupuesto":
        filas = db.query(Presupuesto).all()
        seleccion = _seleccionar_coincidencias(
            filas, termino,
            lambda p: [
                p.numero, p.titulo, p.direccion_obra,
                getattr(getattr(p, "cliente", None), "nombre", ""), p.estado,
            ],
        )
        return [{
            "titulo": f"{p.numero} · {p.titulo or 'Sin título'}",
            "detalle": (
                f"{getattr(getattr(p, 'cliente', None), 'nombre', 'Sin cliente')} · "
                f"{p.estado.capitalize()} · {float(p.total or 0):,.2f} {p.moneda or 'USD'}"
            ),
            "url": f"/presupuestos/{p.id}",
            "editar_url": f"/presupuestos/{p.id}/editar",
        } for p in seleccion]

    if tipo == "producto":
        filas = db.query(Producto).all()
        seleccion = _seleccionar_coincidencias(
            filas, termino,
            lambda p: [
                p.nombre, p.descripcion, p.sku, p.marca, p.modelo,
                p.categoria, p.proveedor, p.formato, p.acabado,
            ],
        )
        return [{
            "titulo": p.nombre,
            "detalle": (
                " · ".join(v for v in (p.sku, p.marca, p.modelo, p.formato) if v)
                + (" · " if any((p.sku, p.marca, p.modelo, p.formato)) else "")
                + f"{float(p.precio_unitario or 0):,.2f} {p.moneda or 'USD'}/{p.unidad or 'ud'}"
            ),
            "url": f"/productos/{p.id}/editar",
        } for p in seleccion]

    filas = db.query(Recurso).all()
    seleccion = _seleccionar_coincidencias(
        filas, termino,
        lambda r: [r.descripcion, r.codigo, r.categoria, r.grupo, r.proveedor, r.subtipo],
    )
    return [{
        "titulo": f"{r.codigo + ' · ' if r.codigo else ''}{r.descripcion}",
        "detalle": f"{r.categoria.replace('_', ' ').title()} · {float(r.precio or 0):,.2f} {r.moneda or 'USD'}/{r.unidad or 'ud'}",
        "url": f"/recursos?q={quote_plus(r.codigo or r.descripcion)}",
    } for r in seleccion]


def responder_busqueda_entidad(
    db: Session, consulta: str, tipo: str, idioma: str = "es",
) -> str:
    en = _es_ingles(idioma)
    termino = _termino_entidad(consulta)
    etiqueta = _ETIQUETAS_ENTIDAD["en" if en else "es"][tipo]
    if not termino:
        if en:
            return (
                f"Tell me which {etiqueta} to look for, by name, code or "
                "reference."
            )
        return f"Indícame qué {etiqueta} debo buscar, por nombre, código o referencia."
    resultados = _buscar_entidad(db, tipo, termino)
    if not resultados:
        log.warning(
            "asistente_busqueda_sin_resultados",
            extra={
                "evento": "asistente_busqueda_sin_resultados",
                "organizacion_id": db.info.get("organizacion_id"),
                "tipo": tipo,
                "consulta": termino[:120],
            },
        )
        if en:
            return (
                f"### 🔎 {etiqueta.capitalize()} search\n\n"
                f"I looked for **{_seguro(termino)}** across your company data "
                "and found no matches. I am not going to invent results.\n\n"
                f"[Open the global search](/buscar?q={quote_plus(termino)})"
            )
        return (
            f"### 🔎 Búsqueda de {etiqueta}\n\n"
            f"He buscado **{_seguro(termino)}** en los datos de tu empresa y no encontré coincidencias. "
            "No voy a inventar resultados.\n\n"
            f"[Abrir la búsqueda global](/buscar?q={quote_plus(termino)})"
        )

    if en:
        lineas = [
            f"### 🔎 {etiqueta.capitalize()} found",
            "",
            f"Real results for **{_seguro(termino)}**:",
            "",
        ]
    else:
        lineas = [
            f"### 🔎 {etiqueta.capitalize()} encontrados",
            "",
            f"Resultados reales para **{_seguro(termino)}**:",
            "",
        ]
    for indice, resultado in enumerate(resultados, start=1):
        lineas.extend((
            f"{indice}. **{_seguro(resultado['titulo'])}**",
            f"   - {_seguro(resultado['detalle'])}",
            f"   - [{'Open' if en else 'Abrir'}]({resultado['url']})",
        ))
        if resultado.get("editar_url"):
            lineas.append(
                f"   - [{'Edit' if en else 'Editar'}]({resultado['editar_url']})"
            )
    pie = "See all results in the global search" if en else "Ver búsqueda global"
    lineas.extend(("", f"[{pie}](/buscar?q={quote_plus(termino)})"))
    return "\n".join(lineas)


_REVISION_RE = re.compile(
    r"\b(?:revisa|revisar|audita|auditar|analiza|analizar)\w*\b.*\b(?:presupuesto|cotizacion|propuesta)\b"
    r"|\b(?:presupuesto|cotizacion|propuesta)\b.*\b(?:listo|lista|enviar|errores|problemas|revisar)\b"
    # Inglés: «review this estimate», «is the quote ready to send?»…
    r"|\b(?:review|audit|check|analyse|analyze)\w*\b.*\b(?:estimate|quote|proposal)\b"
    r"|\b(?:estimate|quote|proposal)\b.*\b(?:ready|send|errors?|issues?|problems?|review)\b",
    re.IGNORECASE,
)


def _resolver_presupuesto(db: Session, consulta: str, contexto: dict[str, Any] | None):
    from ..models import Presupuesto

    presupuesto_id = _contexto_presupuesto_id(contexto)
    if presupuesto_id:
        presupuesto = db.get(Presupuesto, presupuesto_id)
        if presupuesto is not None:
            return presupuesto
    numero = re.search(r"\bP-\d{4}-\d{3,}\b", str(consulta or ""), re.IGNORECASE)
    if numero:
        return db.query(Presupuesto).filter(Presupuesto.numero.ilike(numero.group(0))).first()
    return None


def responder_revision_borrador_vivo(
    capitulos: list[dict[str, Any]], idioma: str = "es",
) -> str:
    from .copiloto_presupuesto import revisar_borrador_vivo

    en = _es_ingles(idioma)
    revision = revisar_borrador_vivo(capitulos, idioma)
    icono = {"listo": "✅", "revisar": "🟠", "riesgo": "🔴"}.get(revision["estado"], "📋")
    if en:
        lineas = [
            f"### {icono} Review of the draft on screen",
            "",
            f"**Structural score: {revision['score']}/100.** I reviewed "
            f"{revision['total_capitulos']} section(s) and "
            f"{revision['total_partidas']} line item(s) exactly as the editor "
            "is showing them now.",
        ]
    else:
        lineas = [
            f"### {icono} Revisión del borrador visible",
            "",
            f"**Puntuación estructural: {revision['score']}/100.** Revisé "
            f"{revision['total_capitulos']} capítulo(s) y {revision['total_partidas']} partida(s) "
            "tal como aparecen ahora en el editor.",
        ]
    ir_al_campo = "Go to the field" if en else "Ir al campo"

    def agregar_items(titulo: str, items: list[dict[str, Any]], max_items: int = 8):
        if not items:
            return
        lineas.extend(("", titulo))
        for item in items[:max_items]:
            texto = f"- **{_seguro(item['titulo'])}**"
            if item.get("detalle"):
                texto += f": {_seguro(item['detalle'])}"
            if "capitulo_indice" in item:
                params = {"capitulo": item["capitulo_indice"]}
                if "partida_indice" in item:
                    params["partida"] = item["partida_indice"]
                texto += f" · [{ir_al_campo}](/api/ia/accion/enfocar-borrador?{urlencode(params)})"
            lineas.append(texto)

    agregar_items("**Critical points:**" if en else "**Puntos críticos:**", revision["criticos"])
    agregar_items("**Warnings:**" if en else "**Avisos:**", revision["avisos"])
    if not revision["criticos"] and not revision["avisos"]:
        lineas.extend((
            "",
            "No structural problems found in the current draft." if en else
            "No se detectaron problemas estructurales en el borrador actual.",
        ))
    lineas.extend((
        "",
        "This review has saved and changed nothing. Definitive totals keep being worked out on the server when you save."
        if en else
        "Esta revisión no ha guardado ni modificado nada. Los totales definitivos continúan calculándose en el servidor al guardar.",
    ))
    return "\n".join(lineas)


def responder_revision_presupuesto(
    db: Session,
    consulta: str,
    contexto: dict[str, Any] | None,
    idioma: str = "es",
) -> str:
    from ..models import Configuracion
    from .revision_presupuesto import revisar_presupuesto_antes_de_enviar
    from .tiempos import calcular_tiempos_presupuesto

    en = _es_ingles(idioma)
    borrador = (contexto or {}).get("borrador")
    if isinstance(borrador, list):
        return responder_revision_borrador_vivo(borrador, idioma)

    presupuesto = _resolver_presupuesto(db, consulta, contexto)
    if presupuesto is None:
        if en:
            return (
                "### ✅ Estimate review\n\n"
                "Open the estimate you want to review, or give me its number, "
                "for example `P-2026-001`.\n\n[See estimates](/presupuestos)"
            )
        return (
            "### ✅ Revisión de presupuesto\n\n"
            "Abre el presupuesto que quieres revisar o indícame su número, por ejemplo "
            "`P-2026-001`.\n\n[Ver presupuestos](/presupuestos)"
        )
    cfg = db.query(Configuracion).first()
    tiempos = None
    try:
        tiempos = calcular_tiempos_presupuesto(
            presupuesto,
            db=db,
            horas_jornada=float(getattr(cfg, "horas_jornada", 8) or 8),
            tarifa_hora_media=float(getattr(cfg, "tarifa_hora_media", 0) or 0),
            usar_estimacion_coste=bool(getattr(cfg, "estimar_tiempo_por_coste", False)),
        )
    except Exception:
        log.debug("No se pudieron calcular tiempos en la revisión IA", exc_info=True)
    revision = revisar_presupuesto_antes_de_enviar(
        presupuesto, cfg=cfg, tiempos=tiempos, idioma=idioma,
    )

    estado_icono = {"listo": "✅", "revisar": "🟠", "riesgo": "🔴"}.get(revision["estado"], "📋")
    lineas = [
        f"### {estado_icono} {presupuesto.numero}: {revision['titulo']}",
        "",
        f"**{'Score' if en else 'Puntuación'}: {revision['score']}/100.** {revision['resumen']}",
    ]
    if str((contexto or {}).get("pagina") or "").endswith("/editar"):
        lineas.extend((
            "",
            "The review uses the last saved version. Save first if you have just changed quantities, prices or line items."
            if en else
            "La revisión usa la última versión guardada. Guarda primero si acabas de cambiar cantidades, precios o partidas.",
        ))
    if revision["criticos"]:
        lineas.extend(("", "**Critical points:**" if en else "**Puntos críticos:**"))
        for item in revision["criticos"][:6]:
            texto = f"- **{_seguro(item['titulo'])}**"
            if item.get("detalle"):
                texto += f": {_seguro(item['detalle'])}"
            if item.get("url"):
                texto += f" · [{'Fix' if en else 'Corregir'}]({item['url']})"
            lineas.append(texto)
    if revision["recomendaciones"]:
        lineas.extend(("", "**Recommendations:**" if en else "**Recomendaciones:**"))
        for item in revision["recomendaciones"][:6]:
            texto = f"- **{_seguro(item['titulo'])}**"
            if item.get("detalle"):
                texto += f": {_seguro(item['detalle'])}"
            if item.get("url"):
                texto += f" · [{'Review' if en else 'Revisar'}]({item['url']})"
            lineas.append(texto)
    if en:
        lineas.extend((
            "",
            f"[Open estimate](/presupuestos/{presupuesto.id}) · "
            f"[Edit](/presupuestos/{presupuesto.id}/editar)",
        ))
    else:
        lineas.extend((
            "",
            f"[Abrir presupuesto](/presupuestos/{presupuesto.id}) · "
            f"[Editar](/presupuestos/{presupuesto.id}/editar)",
        ))
    return "\n".join(lineas)


_PLAN_RE = re.compile(
    r"\bcapitulos?\s+y\s+partidas?\b"
    r"|\b(?:planifica|planificar|estructura|estructurar)\w*\b.*\b(?:obra|reforma|remodelacion|presupuesto)\b"
    r"|\bpresupuesto\s+para\s+(?:reformar|remodelar)\b"
    # Inglés: «sections and line items», «plan a bathroom refurbishment»…
    r"|\b(?:line\s+)?items?\s+and\s+sections?\b"
    r"|\bsections?\s+and\s+(?:line\s+)?items?\b"
    r"|\b(?:plan|structure|organise|organize)\w*\b.*\b(?:works?|refurbishment|renovation|estimate)\b"
    r"|\bestimate\s+for\s+(?:refurbish|renovat)\w*\b",
    re.IGNORECASE,
)

_STOP_PLAN = _STOP_BUSQUEDA.union({
    "capitulo", "capitulos", "partida", "partidas", "debo", "incluir", "incluye",
    "obra", "reforma", "reformar", "remodelacion", "remodelar", "presupuestar",
    "planifica", "planificar", "estructura", "estructurar",
    # Inglés.
    "section", "sections", "item", "items", "line", "works", "refurbishment",
    "refurbish", "renovation", "renovate", "plan", "structure", "should",
    "include", "includes", "need", "want", "bathroom", "kitchen",
})


def _terminos_plan(consulta: str) -> list[str]:
    salida = []
    for token in normalizar(consulta).split():
        if len(token) >= 3 and token not in _STOP_PLAN and token not in salida:
            salida.append(token)
    return salida[:6]


def responder_plan_catalogo(
    db: Session,
    consulta: str,
    contexto: dict[str, Any] | None,
    idioma: str = "es",
) -> str | None:
    from ..models import RecetaEstancia

    en = _es_ingles(idioma)

    terminos = _terminos_plan(consulta)
    if not terminos:
        return None
    recetas = db.query(RecetaEstancia).all()
    puntuadas = []
    for receta in recetas:
        texto = normalizar(" ".join((receta.nombre or "", receta.descripcion or "", receta.categoria or "")))
        score = sum(1 for termino in terminos if termino in texto)
        if score:
            puntuadas.append((score, receta))
    if not puntuadas:
        return None
    puntuadas.sort(key=lambda fila: (-fila[0], (fila[1].nombre or "").lower()))
    editor_abierto = _editor_abierto(contexto)
    if en:
        lineas = [
            "### 🧩 Structures available in your packs",
            "",
            "Rather than invent a generic list, I found these structures already saved in your company:",
            "",
        ]
    else:
        lineas = [
            "### 🧩 Estructuras disponibles en tus Packs",
            "",
            "En lugar de inventar una lista genérica, encontré estas estructuras guardadas en tu empresa:",
            "",
        ]
    for indice, (_, receta) in enumerate(puntuadas[:4], start=1):
        try:
            items = json.loads(receta.datos or "[]")
        except (TypeError, ValueError):
            items = []
        if not isinstance(items, list):
            items = []
        nombres = [
            _seguro(item.get("nombre")) for item in items
            if isinstance(item, dict) and item.get("nombre")
        ]
        muestra = ", ".join(nombres[:4])
        if len(nombres) > 4:
            muestra += f" and {len(nombres) - 4} more" if en else f" y {len(nombres) - 4} más"
        if en:
            lineas.extend((
                f"{indice}. **{_seguro(receta.nombre)}** · {len(items)} line item(s)",
                f"   - Base: {float(receta.cantidad_base_default or 0):g} {_seguro(receta.unidad_base)}"
                + (f" · {muestra}" if muestra else ""),
                f"   - [View or edit pack](/recetas/{receta.id}/editar)",
            ))
        else:
            lineas.extend((
                f"{indice}. **{_seguro(receta.nombre)}** · {len(items)} partida(s)",
                f"   - Base: {float(receta.cantidad_base_default or 0):g} {_seguro(receta.unidad_base)}"
                + (f" · {muestra}" if muestra else ""),
                f"   - [Ver o editar Pack](/recetas/{receta.id}/editar)",
            ))
        if editor_abierto:
            lineas.append(
                f"   - [{'Open this pack in the estimate' if en else 'Abrir este Pack en el presupuesto'}]"
                f"(/api/ia/accion/abrir-pack?receta_id={receta.id})"
            )
    if en:
        lineas.extend((
            "",
            "The pack works out quantities from the measurement you give it and shows a preview before inserting anything.",
            "[See all packs](/recetas)",
        ))
    else:
        lineas.extend((
            "",
            "El Pack calcula cantidades según la medida que indiques y te muestra una vista previa antes de insertarlo.",
            "[Ver todos los Packs](/recetas)",
        ))
    return "\n".join(lineas)


_MEDICION_RE = re.compile(
    r"\d+(?:[.,]\d+)?\s*(?:m)?\s*[x×]\s*\d+(?:[.,]\d+)?"
    r".*\b(?:mide|medida|medicion|mediciones|altura|piso|pared|bano|baño|habitacion)\b"
    r"|\b(?:mide|medida|medicion|mediciones|calcula)\w*\b"
    r".*\d+(?:[.,]\d+)?\s*(?:m)?\s*[x×]\s*\d+(?:[.,]\d+)?"
    # Inglés: «3 × 2 m bathroom», «measure a 4 x 5 room»…
    r"|\d+(?:[.,]\d+)?\s*(?:m)?\s*[x×]\s*\d+(?:[.,]\d+)?"
    r".*\b(?:measure|measurement|measurements|height|floor|wall|bathroom|room|ceiling)\b"
    r"|\b(?:measure|measurement|measurements|calculate)\w*\b"
    r".*\d+(?:[.,]\d+)?\s*(?:m)?\s*[x×]\s*\d+(?:[.,]\d+)?",
    re.IGNORECASE,
)

_LOTE_RE = re.compile(
    r"\b(?:anade|añade|agrega|prepara|propone|sugiere)\w*\b.*\b(?:partidas|alcance)\b"
    r"|\bpartidas\s+necesarias\b"
    # Inglés: «add the line items», «prepare a batch for this scope»…
    r"|\b(?:add|prepare|propose|suggest)\w*\b.*\b(?:(?:line\s+)?items|scope)\b"
    r"|\b(?:line\s+)?items\s+needed\b",
    re.IGNORECASE,
)

_FALTANTES_RE = re.compile(
    r"\b(?:que\s+)?(?:falta|faltan|faltante|faltantes)\b"
    r"|\b(?:revisa|analiza)\w*\b.*\balcance\b"
    r"|\b(?:alcance|presupuesto)\b.*\b(?:incompleto|olvidado|faltante)\b"
    # Inglés: «what is missing?», «anything missing from the scope?»…
    r"|\b(?:what\s+is\s+|what\s+)?(?:missing|missed|forgotten)\b"
    r"|\b(?:review|check|analyse|analyze)\w*\b.*\bscope\b"
    r"|\b(?:scope|estimate)\b.*\b(?:incomplete|missing|forgotten)\b",
    re.IGNORECASE,
)


def responder_mediciones(
    consulta: str,
    contexto: dict[str, Any] | None,
    idioma: str = "es",
) -> str:
    from .copiloto_presupuesto import calcular_mediciones_texto

    en = _es_ingles(idioma)
    calculo = calcular_mediciones_texto(consulta, idioma)
    if not calculo.get("ok"):
        titulo = "Measurements assistant" if en else "Asistente de mediciones"
        return f"### 📐 {titulo}\n\n{_seguro(calculo.get('error'))}"
    if en:
        lineas = [
            "### 📐 Measurements worked out on the server",
            "",
            f"Main dimensions: **{calculo['largo']:g} × {calculo['ancho']:g} m**"
            + (f" · height **{calculo['altura']:g} m**" if calculo.get("altura") else ""),
            "",
        ]
    else:
        lineas = [
            "### 📐 Mediciones calculadas en el servidor",
            "",
            f"Dimensiones principales: **{calculo['largo']:g} × {calculo['ancho']:g} m**"
            + (f" · altura **{calculo['altura']:g} m**" if calculo.get("altura") else ""),
            "",
        ]
    for fila in calculo["filas"]:
        lineas.append(
            f"- **{_seguro(fila['concepto'])}: {fila['cantidad']:g} {fila['unidad']}** · `{_seguro(fila['formula'])}`"
        )
        if _editor_abierto(contexto):
            params = urlencode({
                "tipo": fila["tipo"],
                "cantidad": fila["cantidad"],
                "concepto": fila["concepto"],
                "unidad": fila["unidad"],
            })
            lineas.append(
                f"  [{'Apply as a measurement' if en else 'Aplicar como medición'}]"
                f"(/api/ia/accion/aplicar-medicion?{params})"
            )
    if calculo.get("aberturas"):
        lineas.extend((
            "",
            f"I deducted **{calculo['descuento_aberturas']:g} m2** for doors, "
            "windows or openings identified." if en else
            f"Desconté **{calculo['descuento_aberturas']:g} m2** por puertas, ventanas o huecos identificados.",
        ))
    lineas.extend((
        "",
        "The estimate has not been modified. Check the figures and press an "
        "action to choose the destination line item." if en else
        "No se ha modificado el presupuesto. Revisa los datos y pulsa una acción para elegir la partida de destino.",
    ))
    return "\n".join(lineas)


def responder_preparacion_lote(
    db: Session,
    consulta: str,
    contexto: dict[str, Any] | None,
    idioma: str = "es",
) -> str:
    from .copiloto_presupuesto import preparar_lote_catalogo

    en = _es_ingles(idioma)
    borrador = (contexto or {}).get("borrador")
    lote = preparar_lote_catalogo(db, consulta, borrador, idioma)
    candidatos = lote["candidatos"]
    if not candidatos:
        if en:
            return (
                "### 🧰 Preparing line items\n\n"
                "I found no new line items reliable enough in the active "
                "catalogue. They may already be in the draft, or the catalogue "
                "may need another term.\n\n"
                f"[Search manually](/partidas?q={quote_plus(consulta[:120])})"
            )
        return (
            "### 🧰 Preparación de partidas\n\n"
            "No encontré partidas nuevas suficientemente fiables en el catálogo activo. "
            "Puede que ya estén en el borrador o que el catálogo necesite otro término.\n\n"
            f"[Buscar manualmente](/partidas?q={quote_plus(consulta[:120])})"
        )
    if en:
        lineas = [
            "### 🧰 Batch prepared from your catalogue",
            "",
            "These are real line items; none has been added yet:",
            "",
        ]
    else:
        lineas = [
            "### 🧰 Lote preparado desde tu catálogo",
            "",
            "Estas son partidas reales; todavía no se ha añadido ninguna:",
            "",
        ]
    ids = []
    for indice, partida in enumerate(candidatos, start=1):
        ids.append(str(partida["id"]))
        if en:
            lineas.extend((
                f"{indice}. **{_seguro(partida['codigo'])} · {_seguro(partida['nombre'])}**",
                f"   - Suggested section: {_seguro(partida['capitulo_sugerido'])} · "
                f"{float(partida['precio'] or 0):,.2f} {partida['moneda']}/{_seguro(partida['unidad'])}",
                f"   - [Open record](/partidas/{partida['id']}/editar)",
            ))
        else:
            lineas.extend((
                f"{indice}. **{_seguro(partida['codigo'])} · {_seguro(partida['nombre'])}**",
                f"   - Capítulo sugerido: {_seguro(partida['capitulo_sugerido'])} · "
                f"{float(partida['precio'] or 0):,.2f} {partida['moneda']}/{_seguro(partida['unidad'])}",
                f"   - [Ver ficha](/partidas/{partida['id']}/editar)",
            ))
    if _editor_abierto(contexto):
        lineas.extend((
            "",
            f"[{'Review the selection and add to the estimate' if en else 'Revisar selección y añadir al presupuesto'}]"
            f"(/api/ia/accion/agregar-lote?ids={','.join(ids)})",
        ))
    else:
        lineas.extend((
            "",
            "Open an estimate editor to select and insert the batch." if en else
            "Abre el editor de un presupuesto para seleccionar e insertar el lote.",
        ))
    lineas.append(
        "The selection lets you untick line items and choose the section before confirming."
        if en else
        "La selección permite desmarcar partidas y elegir el capítulo antes de confirmar."
    )
    return "\n".join(lineas)


def responder_faltantes_alcance(
    db: Session,
    consulta: str,
    contexto: dict[str, Any] | None,
    idioma: str = "es",
) -> str:
    from .copiloto_presupuesto import detectar_faltantes_alcance

    en = _es_ingles(idioma)
    borrador = (contexto or {}).get("borrador")
    if not isinstance(borrador, list):
        if en:
            return (
                "### 🧭 Scope review\n\n"
                "Open the estimate editor so I can compare the visible line "
                "items against the technical rules."
            )
        return (
            "### 🧭 Revisión de alcance\n\n"
            "Abre el editor del presupuesto para que pueda comparar las partidas visibles con las reglas técnicas."
        )
    resultado = detectar_faltantes_alcance(db, borrador, consulta, idioma)
    if not resultado["sugerencias"]:
        if en:
            return (
                "### ✅ Scope reviewed\n\n"
                f"I reviewed **{resultado['analizadas']} line item(s)** and found "
                "no obvious additions with the rules available. This does not "
                "replace a technical review specific to the works."
            )
        return (
            "### ✅ Alcance revisado\n\n"
            f"Analicé **{resultado['analizadas']} partida(s)** y no detecté complementos evidentes con las reglas disponibles. "
            "Esto no sustituye la revisión técnica específica de la obra."
        )
    if en:
        lineas = [
            "### 🧭 Possible gaps in scope",
            "",
            "These are technical warnings, not compulsory line items. Check whether they are already included inside another description:",
            "",
        ]
    else:
        lineas = [
            "### 🧭 Posibles faltantes de alcance",
            "",
            "Son advertencias técnicas, no partidas obligatorias. Revisa si ya están incluidas dentro de otra descripción:",
            "",
        ]
    for indice, sugerencia in enumerate(resultado["sugerencias"], start=1):
        lineas.append(f"{indice}. **{_seguro(sugerencia['titulo'])}**: {_seguro(sugerencia['motivo'])}")
        for partida in sugerencia["partidas"][:2]:
            lineas.append(
                f"   - [{_seguro(partida['codigo'])} · {_seguro(partida['nombre'])}](/partidas/{partida['id']}/editar)"
            )
    if resultado["ids_recomendados"] and _editor_abierto(contexto):
        ids = ",".join(str(i) for i in resultado["ids_recomendados"])
        lineas.extend((
            "",
            f"[{'Review the suggestions and add the selected ones' if en else 'Revisar sugerencias y añadir seleccionadas'}]"
            f"(/api/ia/accion/agregar-lote?ids={ids})",
        ))
    lineas.extend((
        "",
        "Nothing is added automatically. Confirm the contractual scope and "
        "whether each item is included, excluded or should be budgeted "
        "separately." if en else
        "Nada se añade automáticamente. Confirma el alcance contractual y si cada concepto está incluido, excluido o debe presupuestarse aparte.",
    ))
    return "\n".join(lineas)


def resolver_herramienta_ia(
    db: Session,
    consulta: str,
    contexto: dict[str, Any] | None = None,
    idioma: str = "es",
) -> str | None:
    """Resuelve búsquedas, revisiones y planes sin llamar a un LLM."""
    texto = normalizar(consulta)
    if _MEDICION_RE.search(consulta):
        return responder_mediciones(consulta, contexto, idioma)
    if _FALTANTES_RE.search(texto):
        return responder_faltantes_alcance(db, consulta, contexto, idioma)
    if _LOTE_RE.search(texto):
        return responder_preparacion_lote(db, consulta, contexto, idioma)
    if _REVISION_RE.search(texto):
        return responder_revision_presupuesto(db, consulta, contexto, idioma)
    if _PLAN_RE.search(texto):
        return responder_plan_catalogo(db, consulta, contexto, idioma)
    tipo = _detectar_tipo_entidad(consulta)
    if tipo:
        return responder_busqueda_entidad(db, consulta, tipo, idioma)
    return None
