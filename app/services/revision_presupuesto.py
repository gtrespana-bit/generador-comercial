"""Asistente de revisión comercial antes de enviar un presupuesto.

La idea no es bloquear el flujo ni añadir complejidad: devuelve una lista corta
 de señales accionables para que el usuario sepa si puede enviar la propuesta
con confianza.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Iterable

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

    def as_dict(self) -> dict:
        return {
            "clave": self.clave,
            "estado": self.estado,
            "titulo": self.titulo,
            "detalle": self.detalle,
            "accion": self.accion,
            "url": self.url,
        }


def _activos(presupuesto) -> list:
    return [p for p in presupuesto.todas_partidas if partida_activa(p)]


def _primeros_nombres(items: Iterable, attr: str = "nombre", max_items: int = MAX_ITEMS_MOSTRAR) -> str:
    nombres = [str(getattr(x, attr, "") or "Sin nombre").strip() for x in items]
    if not nombres:
        return ""
    visibles = nombres[:max_items]
    extra = len(nombres) - len(visibles)
    texto = ", ".join(visibles)
    if extra > 0:
        texto += f" y {extra} más"
    return texto


def revisar_presupuesto_antes_de_enviar(presupuesto, cfg=None, tiempos: dict | None = None) -> dict:
    """Devuelve el estado de preparación de un presupuesto para enviarlo.

    La salida está pensada para UI: pocos mensajes, estado global y enlaces de
    corrección. No expone datos sensibles al cliente; es uso interno.
    """
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
        items.append(RevisionItem("cliente", "ok", "Cliente asignado", getattr(cliente, "nombre", "") or ""))
        tiene_contacto = bool((getattr(cliente, "email", "") or "").strip() or (getattr(cliente, "telefono", "") or "").strip())
        if tiene_contacto:
            items.append(RevisionItem("contacto", "ok", "Contacto listo", "Hay email o teléfono para enviar la propuesta."))
        else:
            items.append(RevisionItem("contacto", "warn", "Falta email o teléfono del cliente", "Puedes descargar PDF, pero no tendrás envío rápido ni seguimiento cómodo.", "Completar cliente", f"/clientes/{cliente.id}/editar"))
    else:
        items.append(RevisionItem("cliente", "danger", "Falta cliente", "Asigna un cliente antes de enviar.", "Editar presupuesto", editar_url))

    # Estructura y precios
    if partidas_activas:
        items.append(RevisionItem("partidas", "ok", "Presupuesto con partidas", f"{len(partidas_activas)} partida(s) activa(s)."))
    else:
        items.append(RevisionItem("partidas", "danger", "No hay partidas activas", "Añade al menos una partida incluida en el presupuesto.", "Editar partidas", editar_url))

    sin_precio = [p for p in partidas_activas if float(getattr(p, "precio_unitario", 0) or 0) <= 0]
    sin_cantidad = [p for p in partidas_activas if float(getattr(p, "cantidad_total", 0) or 0) <= 0]
    if sin_precio:
        items.append(RevisionItem("precios", "danger", f"{len(sin_precio)} partida(s) sin precio", _primeros_nombres(sin_precio), "Corregir precios", editar_url))
    else:
        items.append(RevisionItem("precios", "ok", "Precios completos", "Todas las partidas activas tienen precio."))
    if sin_cantidad:
        items.append(RevisionItem("cantidades", "danger", f"{len(sin_cantidad)} partida(s) sin cantidad", _primeros_nombres(sin_cantidad), "Corregir cantidades", editar_url))
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
        items.append(RevisionItem("costes", estado, f"Costes internos al {cobertura}%", f"{len(con_costes)} de {len(partidas_activas)} partidas permiten calcular margen.", "Revisar costes" if estado != "ok" else "", editar_url if estado != "ok" else ""))
        if sin_costes:
            items.append(RevisionItem("sin_costes", "warn", f"{len(sin_costes)} partida(s) sin coste interno", _primeros_nombres(sin_costes), "Completar costes", editar_url))

    margen_pct = float(getattr(presupuesto, "margen_pct", 0) or 0)
    if con_costes:
        if margen_pct >= MARGEN_MINIMO_RECOMENDADO:
            items.append(RevisionItem("margen", "ok", f"Margen total {margen_pct:.1f}%", "Por encima del mínimo recomendado."))
        elif margen_pct > 0:
            items.append(RevisionItem("margen", "warn", f"Margen total bajo: {margen_pct:.1f}%", f"Referencia mínima: {MARGEN_MINIMO_RECOMENDADO:.0f}%.", "Revisar margen", "/presupuestos/optimizar-precios"))
        else:
            items.append(RevisionItem("margen", "danger", "Margen sin beneficio", "El presupuesto puede no dejar ganancia según los costes cargados.", "Revisar margen", "/presupuestos/optimizar-precios"))

        bajo_margen = [p for p in con_costes if float(getattr(p, "margen_beneficio_pct", 0) or 0) < MARGEN_MINIMO_RECOMENDADO]
        if bajo_margen:
            items.append(RevisionItem("margen_partidas", "warn", f"{len(bajo_margen)} partida(s) con margen bajo", _primeros_nombres(bajo_margen), "Revisar precios", "/presupuestos/optimizar-precios"))

    # Tiempos
    if tiempos and tiempos.get("n_partidas_activas"):
        sin_tiempo = int(tiempos.get("n_partidas_activas", 0) - tiempos.get("n_con_datos", 0))
        if sin_tiempo <= 0:
            items.append(RevisionItem("tiempos", "ok", "Planificación de obra completa", f"{tiempos.get('total_dias_duracion', 0):.1f} días críticos estimados."))
        else:
            pct_t = round(tiempos.get("n_con_datos", 0) * 100 / max(1, tiempos.get("n_partidas_activas", 1)))
            items.append(RevisionItem("tiempos", "warn", f"Tiempos al {pct_t}%", f"{sin_tiempo} partida(s) sin tiempo estimado.", "Planificar tiempos", tiempos_url))
    elif partidas_activas:
        items.append(RevisionItem("tiempos", "warn", "Sin planificación de tiempos", "Asigna tiempos para saber duración y cuadrilla antes de prometer fechas.", "Planificar tiempos", tiempos_url))

    # PDF/empresa
    if cfg is not None and (getattr(cfg, "logo", "") or "").strip():
        items.append(RevisionItem("logo", "ok", "PDF con logo", "La propuesta saldrá identificada con tu marca."))
    else:
        items.append(RevisionItem("logo", "warn", "PDF sin logo", "Añade tu logo para que la propuesta se vea más profesional.", "Configurar logo", cfg_url))

    if validez > 0 and fecha_vencimiento >= hoy:
        items.append(RevisionItem("validez", "ok", "Validez vigente", f"Vence el {fecha_vencimiento.strftime('%d/%m/%Y')}."))
    elif validez > 0:
        items.append(RevisionItem("validez", "danger", "Presupuesto vencido", f"Venció el {fecha_vencimiento.strftime('%d/%m/%Y')}. Actualiza fecha o validez antes de enviarlo.", "Editar presupuesto", editar_url))
    else:
        items.append(RevisionItem("validez", "warn", "Validez no definida", "Configura cuántos días es válida la oferta.", "Editar presupuesto", editar_url))

    if getattr(presupuesto, "moneda", ""):
        items.append(RevisionItem("moneda", "ok", f"Moneda {presupuesto.moneda}", ""))
    else:
        items.append(RevisionItem("moneda", "warn", "Moneda no definida", "Revisa moneda y tasa antes de enviar.", "Editar presupuesto", editar_url))

    versiones = list(getattr(presupuesto, "versiones", []) or [])
    if versiones:
        items.append(RevisionItem("version", "ok", "Historial de propuesta disponible", f"Última versión: V{versiones[0].numero_version}."))
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
    elif avisos:
        estado = "revisar"
        titulo = "Casi listo"
        resumen = f"Hay {len(avisos)} aviso(s) recomendable(s) antes de enviar."
    else:
        estado = "listo"
        titulo = "Listo para enviar"
        resumen = "No hay avisos críticos. Puedes enviar la propuesta con confianza."

    criticos = [i.as_dict() for i in peligros]
    recomendaciones = [i.as_dict() for i in avisos]
    correctos = [i.as_dict() for i in oks]
    return {
        "estado": estado,
        "titulo": titulo,
        "resumen": resumen,
        "score": score,
        "criticos": criticos,
        "recomendaciones": recomendaciones,
        "correctos": correctos,
        "items": [i.as_dict() for i in items],
        "puede_enviar": not peligros,
        "texto_boton": "Enviar propuesta" if not peligros else "Revisar puntos críticos",
        "url_principal": f"{base_url}/enlace-publico" if not peligros else (criticos[0].get("url") if criticos else editar_url),
    }
