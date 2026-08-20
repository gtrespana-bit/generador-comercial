"""Comparación simple de una versión enviada frente al presupuesto actual.

No intenta ser un análisis técnico completo. Sirve para el flujo real: cliente
pide cambios por teléfono/WhatsApp, el contratista modifica y CotizaT prepara
un resumen claro para reenviar el PDF actualizado.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from .versions import leer_snapshot, serializar_presupuesto

MAX_CAMBIOS_MENSAJE = 8
_EPS = 0.009


def _num(v) -> float:
    try:
        return float(v or 0)
    except Exception:
        return 0.0


def _norm(txt: str) -> str:
    s = unicodedata.normalize("NFD", str(txt or "").strip().lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def _money(valor: float, moneda: str) -> str:
    signo = "-" if valor < 0 else ""
    n = abs(float(valor or 0))
    s = f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{signo}{s} {moneda or 'USD'}"


def _flatten(snapshot: dict) -> list[dict]:
    filas = []
    for cap in snapshot.get("capitulos") or []:
        cap_nombre = str(cap.get("nombre") or "").strip()
        for idx, item in enumerate(cap.get("partidas") or [], start=1):
            nombre = str(item.get("nombre") or "").strip()
            unidad = str(item.get("unidad") or "").strip()
            codigo = str(item.get("codigo_externo") or "").strip()
            key = f"cod:{_norm(codigo)}" if codigo else f"txt:{_norm(cap_nombre)}|{_norm(nombre)}|{_norm(unidad)}|{idx}"
            filas.append({
                "key": key,
                "capitulo": cap_nombre,
                "nombre": nombre,
                "unidad": unidad,
                "cantidad": _num(item.get("cantidad_total", item.get("cantidad"))),
                "precio": _num(item.get("precio_unitario")),
                "importe": _num(item.get("importe")),
            })
    return filas


def _capitulos(snapshot: dict) -> set[str]:
    return {_norm(c.get("nombre")) for c in snapshot.get("capitulos") or [] if str(c.get("nombre") or "").strip()}


def comparar_snapshot_con_actual(snapshot_anterior: dict, snapshot_actual: dict, *, version_numero: int | None = None) -> dict:
    moneda = str(snapshot_actual.get("moneda") or snapshot_anterior.get("moneda") or "USD")
    total_anterior = _num((snapshot_anterior.get("totales") or {}).get("total"))
    total_actual = _num((snapshot_actual.get("totales") or {}).get("total"))
    diferencia = round(total_actual - total_anterior, 2)

    anteriores = _flatten(snapshot_anterior)
    actuales = _flatten(snapshot_actual)
    ant_map = {x["key"]: x for x in anteriores}
    act_map = {x["key"]: x for x in actuales}

    añadidas = [act_map[k] for k in act_map.keys() - ant_map.keys()]
    eliminadas = [ant_map[k] for k in ant_map.keys() - act_map.keys()]
    modificadas = []
    for key in sorted(act_map.keys() & ant_map.keys()):
        a = ant_map[key]
        b = act_map[key]
        cambios = []
        if abs(a["cantidad"] - b["cantidad"]) > _EPS:
            cambios.append({"campo": "cantidad", "antes": a["cantidad"], "despues": b["cantidad"]})
        if abs(a["precio"] - b["precio"]) > _EPS:
            cambios.append({"campo": "precio", "antes": a["precio"], "despues": b["precio"]})
        if cambios:
            modificadas.append({"nombre": b["nombre"], "capitulo": b["capitulo"], "unidad": b["unidad"], "cambios": cambios, "importe_antes": a["importe"], "importe_despues": b["importe"]})

    caps_ant = _capitulos(snapshot_anterior)
    caps_act = _capitulos(snapshot_actual)
    caps_anadidos = sorted(c for c in caps_act - caps_ant)
    caps_eliminados = sorted(c for c in caps_ant - caps_act)

    hay_cambios = bool(abs(diferencia) > _EPS or añadidas or eliminadas or modificadas or caps_anadidos or caps_eliminados)

    cambios_principales = []
    for item in añadidas[:MAX_CAMBIOS_MENSAJE]:
        cambios_principales.append(f"Se añadió {item['nombre']} ({_money(item['importe'], moneda)}).")
    for item in eliminadas[: max(0, MAX_CAMBIOS_MENSAJE - len(cambios_principales))]:
        cambios_principales.append(f"Se eliminó {item['nombre']} ({_money(-item['importe'], moneda)}).")
    for item in modificadas[: max(0, MAX_CAMBIOS_MENSAJE - len(cambios_principales))]:
        partes = []
        for c in item["cambios"]:
            if c["campo"] == "cantidad":
                partes.append(f"cantidad {c['antes']:g} → {c['despues']:g}")
            elif c["campo"] == "precio":
                partes.append(f"precio {_money(c['antes'], moneda)} → {_money(c['despues'], moneda)}")
        delta = item["importe_despues"] - item["importe_antes"]
        cambios_principales.append(f"Se modificó {item['nombre']}: {', '.join(partes)} ({_money(delta, moneda)}).")

    cliente = ((snapshot_actual.get("cliente") or {}).get("nombre") or "").strip()
    numero = snapshot_actual.get("numero") or ""
    texto = ""
    if hay_cambios:
        saludo = f"Hola{', ' + cliente if cliente else ''}."
        texto = "\n".join([
            saludo,
            f"Te envío el presupuesto actualizado {numero}.",
            "",
            f"Total anterior: {_money(total_anterior, moneda)}",
            f"Nuevo total: {_money(total_actual, moneda)}",
            f"Diferencia: {_money(diferencia, moneda)}",
            "",
            "Cambios principales:",
            *[f"- {c}" for c in (cambios_principales or ["Se actualizó el presupuesto."])],
            "",
            "Adjunto el PDF actualizado.",
        ])

    return {
        "hay_cambios": hay_cambios,
        "version_numero": version_numero,
        "moneda": moneda,
        "total_anterior": total_anterior,
        "total_actual": total_actual,
        "diferencia": diferencia,
        "añadidas": añadidas,
        "eliminadas": eliminadas,
        "modificadas": modificadas,
        "capitulos_añadidos": caps_anadidos,
        "capitulos_eliminados": caps_eliminados,
        "cambios_principales": cambios_principales,
        "texto": texto,
    }


def comparar_version_con_presupuesto(version, presupuesto) -> dict:
    anterior = leer_snapshot(version)
    actual = serializar_presupuesto(presupuesto)
    return comparar_snapshot_con_actual(anterior, actual, version_numero=getattr(version, "numero_version", None))
