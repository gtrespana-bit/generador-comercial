"""Asistente de revisión comercial antes de enviar un presupuesto.

La idea no es bloquear el flujo ni añadir complejidad: devuelve una lista corta
 de señales accionables para que el usuario sepa si puede enviar la propuesta
con confianza.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from .calculations import partida_activa

MARGEN_MINIMO_RECOMENDADO = 20.0
MAX_ITEMS_MOSTRAR = 5


@dataclass(frozen=True)
class RevisionItem:
    clave: str
    estado: str  # ok | warn | danger
    titulo: str
    detalle: str = ""
    accion: str = ""
    url: str = ""
    # Desempate cuando la misma clave emite dos mensajes distintos con el
    # mismo estado (por ejemplo «tiempos» avisa de cobertura parcial y de
    # ausencia total de planificación).
    sub: str = ""
    # Datos ya calculados que la versión inglesa necesita para redactar el
    # mismo mensaje con las mismas cifras.
    params: dict = None

    def as_dict(self, idioma: str = "es") -> dict:
        titulo, detalle, accion = self.titulo, self.detalle, self.accion
        if _es_ingles(idioma):
            plantilla = _REVISION_EN.get((self.clave, self.estado, self.sub))
            if plantilla:
                params = self.params or {}
                try:
                    titulo = plantilla.get("titulo", titulo).format(**params)
                    detalle = plantilla.get("detalle", detalle).format(**params)
                    accion = plantilla.get("accion", accion).format(**params)
                except (KeyError, IndexError, ValueError):
                    # Si falta un dato, mejor el texto en castellano que uno roto.
                    titulo, detalle, accion = self.titulo, self.detalle, self.accion
        return {
            "clave": self.clave,
            "estado": self.estado,
            "titulo": titulo,
            "detalle": detalle,
            "accion": accion,
            "url": self.url,
        }


def _es_ingles(idioma) -> bool:
    """Las variantes regionales (/en-mx/) comparten vocabulario."""
    return str(idioma or "es").strip().lower().startswith("en")


# Mensajes en inglés por (clave, estado, sub). Los marcadores se rellenan con
# los mismos datos que ya usa la versión en castellano, así que ninguna cifra
# se recalcula ni se pierde.
_REVISION_EN: dict[tuple[str, str, str], dict[str, str]] = {
    ("cliente", "ok", ""): {
        "titulo": "Client assigned", "detalle": "{nombre}", "accion": "",
    },
    ("contacto", "ok", ""): {
        "titulo": "Contact details ready",
        "detalle": "There is an email address or a phone number to send the proposal to.",
        "accion": "",
    },
    ("contacto", "warn", ""): {
        "titulo": "Client email or phone missing",
        "detalle": "You can still download the PDF, but you lose quick sending and easy follow-up.",
        "accion": "Complete client",
    },
    ("cliente", "danger", ""): {
        "titulo": "No client assigned",
        "detalle": "Assign a client before sending.", "accion": "Edit estimate",
    },
    ("partidas", "ok", ""): {
        "titulo": "Estimate has line items",
        "detalle": "{n} active line item(s).", "accion": "",
    },
    ("partidas", "danger", ""): {
        "titulo": "No active line items",
        "detalle": "Add at least one line item that is included in the estimate.",
        "accion": "Edit line items",
    },
    ("precios", "danger", ""): {
        "titulo": "{n} line item(s) without a price",
        "detalle": "{nombres}", "accion": "Fix prices",
    },
    ("precios", "ok", ""): {
        "titulo": "Prices complete",
        "detalle": "Every active line item has a price.", "accion": "",
    },
    ("cantidades", "danger", ""): {
        "titulo": "{n} line item(s) without a quantity",
        "detalle": "{nombres}", "accion": "Fix quantities",
    },
    ("cantidades", "ok", ""): {
        "titulo": "Quantities complete",
        "detalle": "Every active line item has a quantity.", "accion": "",
    },
    ("costes", "danger", ""): {
        "titulo": "No margin to calculate",
        "detalle": "No active line item has an internal cost loaded.",
        "accion": "Complete costs",
    },
    ("costes", "ok", ""): {
        "titulo": "Internal costs at {pct}%",
        "detalle": "{n} of {m} line items allow the margin to be calculated.",
        "accion": "",
    },
    ("costes", "warn", ""): {
        "titulo": "Internal costs at {pct}%",
        "detalle": "{n} of {m} line items allow the margin to be calculated.",
        "accion": "Review costs",
    },
    ("sin_costes", "warn", ""): {
        "titulo": "{n} line item(s) with no internal cost",
        "detalle": "{nombres}", "accion": "Complete costs",
    },
    ("margen", "ok", ""): {
        "titulo": "Total margin {pct}",
        "detalle": "Above the recommended minimum.", "accion": "",
    },
    ("margen", "warn", ""): {
        "titulo": "Low total margin: {pct}",
        "detalle": "Reference minimum: {minimo}.", "accion": "Review margin",
    },
    ("margen", "danger", ""): {
        "titulo": "Margin without profit",
        "detalle": "According to the costs loaded, the estimate may leave no profit.",
        "accion": "Review margin",
    },
    ("margen_partidas", "warn", ""): {
        "titulo": "{n} line item(s) with a low margin",
        "detalle": "{nombres}", "accion": "Review prices",
    },
    ("tiempos", "ok", ""): {
        "titulo": "Works programme complete",
        "detalle": "{dias} critical days estimated.", "accion": "",
    },
    ("tiempos", "warn", ""): {
        "titulo": "Time data at {pct}%",
        "detalle": "{n} line item(s) with no estimated time.",
        "accion": "Plan times",
    },
    ("tiempos", "warn", "sin_plan"): {
        "titulo": "No time programme",
        "detalle": "Set times so you know the duration and the crew before promising dates.",
        "accion": "Plan times",
    },
    ("logo", "ok", ""): {
        "titulo": "PDF with logo",
        "detalle": "The proposal will go out identified with your brand.",
        "accion": "",
    },
    ("logo", "warn", ""): {
        "titulo": "PDF without a logo",
        "detalle": "Add your logo so the proposal looks more professional.",
        "accion": "Set up logo",
    },
    ("validez", "ok", ""): {
        "titulo": "Still within validity",
        "detalle": "Expires on {fecha}.", "accion": "",
    },
    ("validez", "danger", ""): {
        "titulo": "Estimate expired",
        "detalle": "It expired on {fecha}. Update the date or the validity before sending.",
        "accion": "Edit estimate",
    },
    ("validez", "warn", ""): {
        "titulo": "Validity not set",
        "detalle": "Set how many days the offer stays valid for.",
        "accion": "Edit estimate",
    },
    ("moneda", "ok", ""): {
        "titulo": "Currency {moneda}", "detalle": "", "accion": "",
    },
    ("moneda", "warn", ""): {
        "titulo": "No currency set",
        "detalle": "Check the currency and the exchange rate before sending.",
        "accion": "Edit estimate",
    },
    ("version", "ok", ""): {
        "titulo": "Proposal history available",
        "detalle": "Latest version: V{n}.", "accion": "",
    },
    ("version", "warn", ""): {
        "titulo": "No frozen version yet",
        "detalle": "One is created when you send or publish, but you can freeze one manually if you want a record.",
        "accion": "Freeze version",
    },
}

_RESUMEN_EN = {
    "riesgo": ("Review before sending",
               "There are {n} critical point(s) that may affect the proposal."),
    "revisar": ("Almost ready",
                "There are {n} recommended check(s) before sending."),
    "listo": ("Ready to send",
              "No critical warnings. You can send the proposal with confidence."),
}


def _primeros_nombres(items, attr="nombre", max_items=MAX_ITEMS_MOSTRAR, en=False):
    """Igual que `_primeros_nombres`, pero en inglés cuando toca."""
    nombres = [
        str(getattr(x, attr, "") or ("No name" if en else "Sin nombre")).strip()
        for x in items
    ]
    if not nombres:
        return ""
    visibles = nombres[:max_items]
    extra = len(nombres) - len(visibles)
    texto = ", ".join(visibles)
    if extra > 0:
        texto += f" and {extra} more" if en else f" y {extra} más"
    return texto



def _activos(presupuesto) -> list:
    return [p for p in presupuesto.todas_partidas if partida_activa(p)]


def revisar_presupuesto_antes_de_enviar(
    presupuesto, cfg=None, tiempos: dict | None = None, idioma: str = "es",
) -> dict:
    """Devuelve el estado de preparación de un presupuesto para enviarlo.

    La salida está pensada para UI: pocos mensajes, estado global y enlaces de
    corrección. No expone datos sensibles al cliente; es uso interno.
    """
    en = _es_ingles(idioma)
    pid = getattr(presupuesto, "id", None)
    base_url = f"/presupuestos/{pid}" if pid else "/presupuestos"
    editar_url = f"{base_url}/editar" if pid else "/presupuestos"
    tiempos_url = f"{base_url}/tiempos" if pid else "/presupuestos"
    cfg_url = "/configuracion"
    cliente = getattr(presupuesto, "cliente", None)
    partidas = list(getattr(presupuesto, "todas_partidas", []) or [])
    partidas_activas = _activos(presupuesto)
    hoy = date.today()
    fecha = getattr(presupuesto, "fecha", hoy) or hoy
    validez = int(getattr(presupuesto, "validez_dias", None) or 30)
    fecha_vencimiento = fecha + timedelta(days=validez)

    items: list[RevisionItem] = []

    # Cliente
    if cliente is not None:
        items.append(RevisionItem(
            "cliente", "ok", "Cliente asignado", getattr(cliente, "nombre", "") or "",
            params={"nombre": getattr(cliente, "nombre", "") or ""},
        ))
        tiene_contacto = bool((getattr(cliente, "email", "") or "").strip() or (getattr(cliente, "telefono", "") or "").strip())
        if tiene_contacto:
            items.append(RevisionItem("contacto", "ok", "Contacto listo", "Hay email o teléfono para enviar la propuesta."))
        else:
            items.append(RevisionItem("contacto", "warn", "Falta email o teléfono del cliente", "Puedes descargar PDF, pero no tendrás envío rápido ni seguimiento cómodo.", "Completar cliente", f"/clientes/{cliente.id}/editar"))
    else:
        items.append(RevisionItem("cliente", "danger", "Falta cliente", "Asigna un cliente antes de enviar.", "Editar presupuesto", editar_url))

    # Estructura y precios
    if partidas_activas:
        items.append(RevisionItem(
            "partidas", "ok", "Presupuesto con partidas",
            f"{len(partidas_activas)} partida(s) activa(s).",
            params={"n": len(partidas_activas)},
        ))
    else:
        items.append(RevisionItem("partidas", "danger", "No hay partidas activas", "Añade al menos una partida incluida en el presupuesto.", "Editar partidas", editar_url))

    sin_precio = [p for p in partidas_activas if float(getattr(p, "precio_unitario", 0) or 0) <= 0]
    sin_cantidad = [p for p in partidas_activas if float(getattr(p, "cantidad_total", 0) or 0) <= 0]
    if sin_precio:
        items.append(RevisionItem(
            "precios", "danger", f"{len(sin_precio)} partida(s) sin precio",
            _primeros_nombres(sin_precio), "Corregir precios", editar_url,
            params={"n": len(sin_precio), "nombres": _primeros_nombres(sin_precio, en=en)},
        ))
    else:
        items.append(RevisionItem("precios", "ok", "Precios completos", "Todas las partidas activas tienen precio."))
    if sin_cantidad:
        items.append(RevisionItem(
            "cantidades", "danger", f"{len(sin_cantidad)} partida(s) sin cantidad",
            _primeros_nombres(sin_cantidad), "Corregir cantidades", editar_url,
            params={"n": len(sin_cantidad), "nombres": _primeros_nombres(sin_cantidad, en=en)},
        ))
    else:
        items.append(RevisionItem("cantidades", "ok", "Cantidades completas", "Todas las partidas activas tienen cantidad."))

    # Margen/costes
    con_costes = [p for p in partidas_activas if getattr(p, "tiene_costes", False)]
    sin_costes = [p for p in partidas_activas if not getattr(p, "tiene_costes", False)]
    if not partidas_activas:
        pass
    elif not con_costes:
        items.append(RevisionItem("costes", "danger", "Sin margen calculable", "Ninguna partida activa tiene coste interno cargado.", "Completar costes", editar_url))
    else:
        cobertura = round(len(con_costes) * 100 / len(partidas_activas))
        estado = "ok" if cobertura >= 90 else "warn"
        items.append(RevisionItem(
            "costes", estado, f"Costes internos al {cobertura}%",
            f"{len(con_costes)} de {len(partidas_activas)} partidas permiten calcular margen.",
            "Revisar costes" if estado != "ok" else "", editar_url if estado != "ok" else "",
            params={"pct": cobertura, "n": len(con_costes), "m": len(partidas_activas)},
        ))
        if sin_costes:
            items.append(RevisionItem(
                "sin_costes", "warn", f"{len(sin_costes)} partida(s) sin coste interno",
                _primeros_nombres(sin_costes), "Completar costes", editar_url,
                params={"n": len(sin_costes), "nombres": _primeros_nombres(sin_costes, en=en)},
            ))

    margen_pct = float(getattr(presupuesto, "margen_pct", 0) or 0)
    if con_costes:
        if margen_pct >= MARGEN_MINIMO_RECOMENDADO:
            items.append(RevisionItem(
                "margen", "ok", f"Margen total {margen_pct:.1f}%",
                "Por encima del mínimo recomendado.",
                params={"pct": f"{margen_pct:.1f}%"},
            ))
        elif margen_pct > 0:
            items.append(RevisionItem(
                "margen", "warn", f"Margen total bajo: {margen_pct:.1f}%",
                f"Referencia mínima: {MARGEN_MINIMO_RECOMENDADO:.0f}%.",
                "Revisar margen", "/presupuestos/optimizar-precios",
                params={"pct": f"{margen_pct:.1f}%", "minimo": f"{MARGEN_MINIMO_RECOMENDADO:.0f}%"},
            ))
        else:
            items.append(RevisionItem("margen", "danger", "Margen sin beneficio", "El presupuesto puede no dejar ganancia según los costes cargados.", "Revisar margen", "/presupuestos/optimizar-precios"))

        bajo_margen = [p for p in con_costes if float(getattr(p, "margen_beneficio_pct", 0) or 0) < MARGEN_MINIMO_RECOMENDADO]
        if bajo_margen:
            items.append(RevisionItem(
                "margen_partidas", "warn", f"{len(bajo_margen)} partida(s) con margen bajo",
                _primeros_nombres(bajo_margen), "Revisar precios",
                "/presupuestos/optimizar-precios",
                params={"n": len(bajo_margen), "nombres": _primeros_nombres(bajo_margen, en=en)},
            ))

    # Tiempos
    if tiempos and tiempos.get("n_partidas_activas"):
        sin_tiempo = int(tiempos.get("n_partidas_activas", 0) - tiempos.get("n_con_datos", 0))
        if sin_tiempo <= 0:
            items.append(RevisionItem(
                "tiempos", "ok", "Planificación de obra completa",
                f"{tiempos.get('total_dias_duracion', 0):.1f} días críticos estimados.",
                params={"dias": f"{tiempos.get('total_dias_duracion', 0):.1f}"},
            ))
        else:
            pct_t = round(tiempos.get("n_con_datos", 0) * 100 / max(1, tiempos.get("n_partidas_activas", 1)))
            items.append(RevisionItem(
                "tiempos", "warn", f"Tiempos al {pct_t}%",
                f"{sin_tiempo} partida(s) sin tiempo estimado.",
                "Planificar tiempos", tiempos_url,
                params={"pct": pct_t, "n": sin_tiempo},
            ))
    elif partidas_activas:
        items.append(RevisionItem(
            "tiempos", "warn", "Sin planificación de tiempos",
            "Asigna tiempos para saber duración y cuadrilla antes de prometer fechas.",
            "Planificar tiempos", tiempos_url, sub="sin_plan",
        ))

    # PDF/empresa
    if cfg is not None and (getattr(cfg, "logo", "") or "").strip():
        items.append(RevisionItem("logo", "ok", "PDF con logo", "La propuesta saldrá identificada con tu marca."))
    else:
        items.append(RevisionItem("logo", "warn", "PDF sin logo", "Añade tu logo para que la propuesta se vea más profesional.", "Configurar logo", cfg_url))

    if validez > 0 and fecha_vencimiento >= hoy:
        items.append(RevisionItem(
            "validez", "ok", "Validez vigente",
            f"Vence el {fecha_vencimiento.strftime('%d/%m/%Y')}.",
            params={"fecha": fecha_vencimiento.strftime("%d/%m/%Y")},
        ))
    elif validez > 0:
        items.append(RevisionItem(
            "validez", "danger", "Presupuesto vencido",
            f"Venció el {fecha_vencimiento.strftime('%d/%m/%Y')}. Actualiza fecha o validez antes de enviarlo.",
            "Editar presupuesto", editar_url,
            params={"fecha": fecha_vencimiento.strftime("%d/%m/%Y")},
        ))
    else:
        items.append(RevisionItem("validez", "warn", "Validez no definida", "Configura cuántos días es válida la oferta.", "Editar presupuesto", editar_url))

    if getattr(presupuesto, "moneda", ""):
        items.append(RevisionItem(
            "moneda", "ok", f"Moneda {presupuesto.moneda}", "",
            params={"moneda": presupuesto.moneda},
        ))
    else:
        items.append(RevisionItem("moneda", "warn", "Moneda no definida", "Revisa moneda y tasa antes de enviar.", "Editar presupuesto", editar_url))

    versiones = list(getattr(presupuesto, "versiones", []) or [])
    if versiones:
        items.append(RevisionItem(
            "version", "ok", "Historial de propuesta disponible",
            f"Última versión: V{versiones[0].numero_version}.",
            params={"n": versiones[0].numero_version},
        ))
    else:
        items.append(RevisionItem("version", "warn", "Aún no hay versión congelada", "Se creará al enviar/publicar, pero puedes congelarla manualmente si quieres dejar constancia.", "Congelar versión", f"{base_url}#versiones"))

    # Resumen
    peligros = [i for i in items if i.estado == "danger"]
    avisos = [i for i in items if i.estado == "warn"]
    oks = [i for i in items if i.estado == "ok"]
    total = len(items) or 1
    puntos = len(oks) + len(avisos) * 0.55
    score = max(0, min(100, round(puntos / total * 100)))
    if peligros:
        estado = "riesgo"
        titulo = "Revisar antes de enviar"
        resumen = f"Hay {len(peligros)} punto(s) crítico(s) que pueden afectar la propuesta."
        if en:
            titulo, resumen = _RESUMEN_EN["riesgo"]
            resumen = resumen.format(n=len(peligros))
    elif avisos:
        estado = "revisar"
        titulo = "Casi listo"
        resumen = f"Hay {len(avisos)} aviso(s) recomendable(s) antes de enviar."
        if en:
            titulo, resumen = _RESUMEN_EN["revisar"]
            resumen = resumen.format(n=len(avisos))
    else:
        estado = "listo"
        titulo = "Listo para enviar"
        resumen = "No hay avisos críticos. Puedes enviar la propuesta con confianza."
        if en:
            titulo, resumen = _RESUMEN_EN["listo"]
            resumen = resumen.format(n=0)

    criticos = [i.as_dict(idioma) for i in peligros]
    recomendaciones = [i.as_dict(idioma) for i in avisos]
    correctos = [i.as_dict(idioma) for i in oks]
    return {
        "estado": estado,
        "titulo": titulo,
        "resumen": resumen,
        "score": score,
        "criticos": criticos,
        "recomendaciones": recomendaciones,
        "correctos": correctos,
        "items": [i.as_dict(idioma) for i in items],
        "puede_enviar": not peligros,
        "texto_boton": (
            ("Send proposal" if not peligros else "Review critical points")
            if en else
            ("Enviar propuesta" if not peligros else "Revisar puntos críticos")
        ),
        "url_principal": f"{base_url}/enlace-publico" if not peligros else (criticos[0].get("url") if criticos else editar_url),
    }
