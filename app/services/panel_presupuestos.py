"""Uso real de presupuestos de un cliente para el panel (SOLO LECTURA).

La Fase 2 del panel dejó el contenido de tenant cerrado por RLS: el operador
veía cifras (nº de presupuestos, totales) pero no lo que hay dentro. Este
módulo abre una ventana de lectura controlada para el **superadmin**:

- lista de presupuestos reales de la organización (sin tocarlos);
- partidas, cantidades y precios de cada presupuesto;
- detección de precios **modificados frente al catálogo** y su desviación;
- partidas **con ajuste recomendado**: sin precio, margen negativo o precio
  sospechoso (los mismos umbrales que ``precios_anomalos`` aplica al catálogo).

Nada de esto escribe en tenant: son consultas. En PostgreSQL la lectura entra
por funciones ``SECURITY DEFINER`` que exigen la marca de operador; en SQLite
(escritorio/pruebas) se consulta directo porque el aislamiento lo aporta la
aplicación. Las rutas que llaman aquí son **GET**, quedan registradas en
``eventos_admin`` y nunca se expone contenido fuera del panel.

Los presupuestos de demostración (``es_demo``) aparecen marcados pero **no**
entran en los agregados ni en el análisis de precios: son datos ficticios.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.orm import joinedload

from ..models import (
    Capitulo,
    ESTADOS_ETIQUETA,
    Partida,
    Presupuesto,
    PresupuestoItem,
)
from .precios_anomalos import (
    UMBRAL_CRITICO_USD,
    UMBRAL_SOSPECHOSO_USD,
)

#: Tolerancia para considerar un precio «igual» al del catálogo (0,5 %).
_EPS_REL = 0.005
_EPS_ABS = 0.01

#: Límites de presentación para que la ficha siga siendo rápida.
MAX_PARTIDAS_MAS_MODIFICADAS = 15
MAX_AJUSTES_MOSTRADOS = 60

#: Etiquetas legibles de los motivos de ajuste.
MOTIVOS_AJUSTE = {
    "sin_precio": "Sin precio (0 o vacío)",
    "margen_negativo": "Precio por debajo del coste",
    "precio_sospechoso": "Precio sospechoso (posible error de moneda)",
    "precio_critico": "Precio crítico",
}

_PESO_MOTIVO = {"sin_precio": 0, "margen_negativo": 1, "precio_critico": 2, "precio_sospechoso": 3}


def _num(valor) -> float:
    if valor is None:
        return 0.0
    if isinstance(valor, Decimal):
        return float(valor)
    try:
        return float(valor)
    except (TypeError, ValueError):
        return 0.0


def _fecha(valor):
    if valor is None:
        return None
    if isinstance(valor, date):
        return valor
    try:
        return valor.date() if hasattr(valor, "date") else valor
    except Exception:
        return None


def _bool(valor) -> bool:
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, str):
        return valor.strip().lower() in {"1", "t", "true", "yes", "on"}
    return bool(valor)


def _a_base(valor: float, moneda: str, moneda_base: str, tipo_cambio) -> float:
    """Precio del presupuesto a moneda base (USD) del catálogo.

    ``tipo_cambio`` es «unidades de moneda contractual por 1 USD», igual que en
    el modelo ``Presupuesto``.
    """
    tasa = _num(tipo_cambio)
    if moneda and moneda_base and moneda != moneda_base and tasa > 0:
        return valor / tasa
    return valor


def _desde_base(valor: float, moneda: str, moneda_base: str, tipo_cambio) -> float:
    """Precio del catálogo (base) a la moneda de la partida del presupuesto."""
    tasa = _num(tipo_cambio)
    if moneda and moneda_base and moneda != moneda_base and tasa > 0:
        return valor * tasa
    return valor


# ---------------------------------------------------------------------------
# Cabeceras: una fila por presupuesto de la organización
# ---------------------------------------------------------------------------


def _cabecera(datos: dict) -> dict:
    moneda = str(datos.get("moneda") or "USD")
    return {
        "id": int(datos.get("id") or 0),
        "numero": str(datos.get("numero") or ""),
        "year": int(datos.get("year") or 0),
        "fecha": _fecha(datos.get("fecha")),
        "titulo": str(datos.get("titulo") or ""),
        "cliente_nombre": str(datos.get("cliente_nombre") or ""),
        "estado": str(datos.get("estado") or "borrador"),
        "estado_label": ESTADOS_ETIQUETA.get(datos.get("estado"), datos.get("estado") or "—"),
        "moneda": moneda,
        "moneda_base": str(datos.get("moneda_base") or "USD"),
        "tipo_cambio": _num(datos.get("tipo_cambio")) or None,
        "total_calculado": _num(datos.get("total_calculado")),
        "es_demo": _bool(datos.get("es_demo")),
        "n_items": int(datos.get("n_items") or 0),
        "created_at": _fecha(datos.get("created_at")),
        "updated_at": _fecha(datos.get("updated_at")),
    }


def _cabeceras_postgres(db, organizacion_id: int) -> list[dict]:
    filas = db.execute(
        text("SELECT * FROM cotizat_security.admin_presupuestos_cliente(:org)"),
        {"org": int(organizacion_id)},
    ).mappings().all()
    return [_cabecera(dict(f)) for f in filas]


def _cabeceras_sqlite(db, organizacion_id: int) -> list[dict]:
    filas = (
        db.query(Presupuesto)
        .options(joinedload(Presupuesto.cliente))
        .filter(Presupuesto.organizacion_id == int(organizacion_id))
        .order_by(Presupuesto.fecha.desc(), Presupuesto.id.desc())
        .all()
    )
    salida = []
    for p in filas:
        salida.append(_cabecera({
            "id": p.id,
            "numero": p.numero,
            "year": getattr(p, "year", 0),
            "fecha": p.fecha,
            "titulo": p.titulo,
            "cliente_nombre": p.cliente.nombre if p.cliente else "",
            "estado": p.estado,
            "moneda": p.moneda,
            "moneda_base": getattr(p, "moneda_base", None) or "USD",
            "tipo_cambio": getattr(p, "tipo_cambio", None),
            "total_calculado": getattr(p, "total_calculado", None),
            "es_demo": bool(getattr(p, "es_demo", False)),
            "n_items": sum(1 for cap in p.capitulos for _ in cap.partidas),
            "created_at": p.created_at,
            "updated_at": p.updated_at,
        }))
    return salida


# ---------------------------------------------------------------------------
# Partidas: todo el detalle (con el precio del catálogo al lado)
# ---------------------------------------------------------------------------


def _item(datos: dict) -> dict:
    """Normaliza una fila de partida y calcula los indicadores de precio."""
    moneda = str(datos.get("moneda") or "USD")
    moneda_base = str(datos.get("moneda_base") or "USD")
    tipo_cambio = _num(datos.get("tipo_cambio")) or None
    precio = _num(datos.get("precio_unitario"))
    catalogo_precio_base = datos.get("catalogo_precio")
    catalogo_precio = (
        _desde_base(_num(catalogo_precio_base), moneda, moneda_base, tipo_cambio)
        if catalogo_precio_base is not None
        else None
    )
    tiene_catalogo = bool(datos.get("partida_catalogo_id"))
    modificado = False
    desviacion_pct = None
    if tiene_catalogo and catalogo_precio is not None and catalogo_precio > 0:
        dif = abs(precio - catalogo_precio)
        if dif > max(_EPS_ABS, catalogo_precio * _EPS_REL):
            modificado = True
            desviacion_pct = (precio - catalogo_precio) / catalogo_precio * 100.0
    elif tiene_catalogo and catalogo_precio is not None and precio != catalogo_precio:
        modificado = abs(precio - catalogo_precio) > _EPS_ABS

    coste = (
        _num(datos.get("coste_materiales"))
        + _num(datos.get("coste_mano_obra"))
        + _num(datos.get("coste_complementarios"))
        + _num(datos.get("coste_otros"))
        + (_num(datos.get("producto_coste")) if datos.get("producto_coste") is not None else 0.0)
    )
    motivos: list[str] = []
    if precio <= 0:
        motivos.append("sin_precio")
    elif coste > 0 and coste > precio + _EPS_ABS:
        motivos.append("margen_negativo")
    precio_base = _a_base(precio, moneda, moneda_base, tipo_cambio)
    if precio_base >= UMBRAL_CRITICO_USD:
        motivos.append("precio_critico")
    elif precio_base > UMBRAL_SOSPECHOSO_USD:
        motivos.append("precio_sospechoso")

    return {
        "item_id": int(datos.get("item_id") or 0),
        "presupuesto_id": int(datos.get("presupuesto_id") or 0),
        "presupuesto_numero": str(datos.get("presupuesto_numero") or ""),
        "presupuesto_fecha": _fecha(datos.get("presupuesto_fecha")),
        "presupuesto_estado": str(datos.get("presupuesto_estado") or ""),
        "presupuesto_actualizado": _fecha(datos.get("presupuesto_actualizado")),
        "presupuesto_es_demo": _bool(datos.get("presupuesto_es_demo")),
        "capitulo": str(datos.get("capitulo") or ""),
        "capitulo_orden": int(datos.get("capitulo_orden") or 0),
        "item_orden": int(datos.get("item_orden") or 0),
        "nombre": str(datos.get("nombre") or ""),
        "unidad": str(datos.get("unidad") or "ud"),
        "cantidad": _num(datos.get("cantidad")),
        "precio_unitario": precio,
        "importe": _num(datos.get("importe")),
        "moneda": moneda,
        "moneda_base": moneda_base,
        "tipo_cambio": tipo_cambio,
        "producto_nombre": str(datos.get("producto_nombre") or ""),
        "producto_precio": _num(datos.get("producto_precio")),
        "coste": round(coste, 2),
        "margen": round(precio - coste, 2),
        "margen_pct": _num(datos.get("margen_pct")),
        "partida_catalogo_id": int(datos.get("partida_catalogo_id") or 0) or None,
        "catalogo_nombre": str(datos.get("catalogo_nombre") or ""),
        "catalogo_precio": round(catalogo_precio, 2) if catalogo_precio is not None else None,
        "catalogo_precio_base": round(_num(catalogo_precio_base), 2) if catalogo_precio_base is not None else None,
        "codigo_externo": str(datos.get("codigo_externo") or ""),
        "tipo_partida": str(datos.get("tipo_partida") or "included"),
        "seleccionada": _bool(datos.get("seleccionada")),
        "es_catalogo": bool(tiene_catalogo),
        "personalizada": not tiene_catalogo,
        "modificado": modificado,
        "desviacion_pct": round(desviacion_pct, 2) if desviacion_pct is not None else None,
        "motivos_ajuste": motivos,
        "motivos_ajuste_label": [MOTIVOS_AJUSTE.get(m, m) for m in motivos],
        "peor_motivo": min(motivos, key=lambda m: _PESO_MOTIVO.get(m, 9)) if motivos else "",
    }


def _items_postgres(db, organizacion_id: int, presupuesto_id: int = 0) -> list[dict]:
    filas = db.execute(
        text("SELECT * FROM cotizat_security.admin_presupuesto_items_cliente(:org, :pres)"),
        {"org": int(organizacion_id), "pres": int(presupuesto_id or 0)},
    ).mappings().all()
    return [_item(dict(f)) for f in filas]


def _items_sqlite(db, organizacion_id: int, presupuesto_id: int = 0) -> list[dict]:
    consulta = (
        db.query(PresupuestoItem, Capitulo, Presupuesto, Partida)
        .join(Capitulo, PresupuestoItem.capitulo_id == Capitulo.id)
        .join(Presupuesto, Capitulo.presupuesto_id == Presupuesto.id)
        .outerjoin(Partida, PresupuestoItem.partida_catalogo_id == Partida.id)
        .filter(Presupuesto.organizacion_id == int(organizacion_id))
        .order_by(Presupuesto.id, Capitulo.orden, PresupuestoItem.orden, PresupuestoItem.id)
    )
    if presupuesto_id:
        consulta = consulta.filter(Presupuesto.id == int(presupuesto_id))
    salida = []
    for item, cap, presupuesto, partida in consulta.all():
        mediciones = sum(_num(m.cantidad) for m in item.mediciones)
        cantidad_total = mediciones if item.mediciones else _num(item.cantidad)
        importe = round(cantidad_total * _num(item.precio_unitario), 2)
        salida.append(_item({
            "item_id": item.id,
            "presupuesto_id": presupuesto.id,
            "presupuesto_numero": presupuesto.numero,
            "presupuesto_fecha": presupuesto.fecha,
            "presupuesto_estado": presupuesto.estado,
            "presupuesto_actualizado": presupuesto.updated_at or presupuesto.created_at,
            "presupuesto_es_demo": bool(getattr(presupuesto, "es_demo", False)),
            "capitulo": cap.nombre,
            "capitulo_orden": cap.orden,
            "item_orden": item.orden,
            "nombre": item.nombre,
            "unidad": item.unidad,
            "cantidad": cantidad_total,
            "precio_unitario": item.precio_unitario,
            "importe": importe,
            "moneda": item.moneda or presupuesto.moneda or "USD",
            "moneda_base": getattr(presupuesto, "moneda_base", None) or "USD",
            "tipo_cambio": getattr(presupuesto, "tipo_cambio", None),
            "producto_nombre": item.producto_nombre or "",
            "producto_precio": item.producto_precio,
            "coste_materiales": item.coste_materiales,
            "coste_mano_obra": item.coste_mano_obra,
            "coste_complementarios": item.coste_complementarios,
            "coste_otros": item.coste_otros,
            "producto_coste": item.producto_coste,
            "margen_pct": item.margen_pct,
            "partida_catalogo_id": item.partida_catalogo_id,
            "catalogo_nombre": partida.nombre if partida else "",
            "catalogo_precio": partida.precio_unitario if partida else None,
            "codigo_externo": item.codigo_externo,
            "tipo_partida": item.tipo_partida,
            "seleccionada": bool(item.seleccionada),
        }))
    return salida


# ---------------------------------------------------------------------------
# Análisis agregado
# ---------------------------------------------------------------------------


def _analizar(cabeceras: list[dict], items: list[dict]) -> dict:
    reales = [c for c in cabeceras if not c["es_demo"]]
    demo = [c for c in cabeceras if c["es_demo"]]
    items_reales = [i for i in items if not i["presupuesto_es_demo"]]

    por_presupuesto: dict[int, dict] = defaultdict(lambda: {
        "n_items": 0, "modificadas": 0, "personalizadas": 0, "ajustes": 0,
        "importe_total": 0.0,
    })
    totales = {
        "presupuestos": len(reales),
        "demo": len(demo),
        "partidas": 0,
        "modificadas": 0,
        "personalizadas": 0,
        "ajustes": 0,
        "presupuestado": defaultdict(float),
        "ultima_actualizacion": None,
    }
    por_estado: dict[str, int] = defaultdict(int)
    for c in reales:
        por_estado[c["estado"]] += 1
        if c["total_calculado"]:
            totales["presupuestado"][c["moneda"]] += c["total_calculado"]
        if c["updated_at"] and (
            totales["ultima_actualizacion"] is None
            or c["updated_at"] > totales["ultima_actualizacion"]
        ):
            totales["ultima_actualizacion"] = c["updated_at"]

    # Agregados de precios modificados por partida del catálogo.
    grupos_mod: dict[tuple, dict] = {}
    ajustes: list[dict] = []
    nombres_unicos: set[str] = set()

    for i in items_reales:
        clave_p = i["presupuesto_id"]
        grupo = por_presupuesto[clave_p]
        grupo["n_items"] += 1
        if i["es_catalogo"] and i["modificado"]:
            grupo["modificadas"] += 1
        if i["personalizada"]:
            grupo["personalizadas"] += 1
        if i["motivos_ajuste"]:
            grupo["ajustes"] += 1
        grupo["importe_total"] += i["importe"]

        totales["partidas"] += 1
        totales["modificadas"] += 1 if (i["es_catalogo"] and i["modificado"]) else 0
        totales["personalizadas"] += 1 if i["personalizada"] else 0
        totales["ajustes"] += 1 if i["motivos_ajuste"] else 0
        nombres_unicos.add(i["nombre"].strip().lower())

        if i["motivos_ajuste"]:
            ajustes.append(i)

        if i["es_catalogo"] and i["modificado"]:
            clave = (i["partida_catalogo_id"], (i["catalogo_nombre"] or i["nombre"]).strip().lower())
            g = grupos_mod.setdefault(clave, {
                "partida_catalogo_id": i["partida_catalogo_id"],
                "nombre": i["catalogo_nombre"] or i["nombre"],
                "unidad": i["unidad"],
                "catalogo_precio_base": i["catalogo_precio_base"],
                "veces": 0,
                "desviaciones": [],
                "ultimo_numero": i["presupuesto_numero"],
                "ultimo_uso": i["presupuesto_actualizado"] or i["presupuesto_fecha"],
            })
            g["veces"] += 1
            if i["desviacion_pct"] is not None:
                g["desviaciones"].append(i["desviacion_pct"])
            if (g["ultimo_uso"] is None) or (
                i["presupuesto_actualizado"] and i["presupuesto_actualizado"] > g["ultimo_uso"]
            ):
                g["ultimo_uso"] = i["presupuesto_actualizado"] or i["presupuesto_fecha"]
                g["ultimo_numero"] = i["presupuesto_numero"]

    top_modificadas = []
    for g in sorted(
        grupos_mod.values(),
        key=lambda g: (len(g["desviaciones"]) and max(abs(d) for d in g["desviaciones"]), g["veces"]),
        reverse=True,
    )[:MAX_PARTIDAS_MAS_MODIFICADAS]:
        desvs = g["desviaciones"]
        top_modificadas.append({
            **g,
            "veces_label": f"{g['veces']}x",
            "desviacion_media": round(sum(desvs) / len(desvs), 2) if desvs else None,
            "desviacion_max": round(max(desvs, key=abs), 2) if desvs else None,
        })

    ajustes.sort(key=lambda i: (_PESO_MOTIVO.get(i["peor_motivo"], 9), str(i["presupuesto_actualizado"] or ""), i["nombre"].lower()))
    return {
        "por_presupuesto": dict(por_presupuesto),
        "totales": {
            **totales,
            "presupuestado": dict(totales["presupuestado"]),
            "partidas_unicas": len(nombres_unicos),
        },
        "por_estado": dict(por_estado),
        "top_modificadas": top_modificadas,
        "ajustes": ajustes[:MAX_AJUSTES_MOSTRADOS],
    }


def resumen_uso_presupuestos(db, organizacion_id: int) -> dict | None:
    """Datos de uso real para la pestaña «Presupuestos y precios» de la ficha."""
    cabeceras = (
        _cabeceras_postgres(db, organizacion_id)
        if db.get_bind().dialect.name == "postgresql"
        else _cabeceras_sqlite(db, organizacion_id)
    )
    items = (
        _items_postgres(db, organizacion_id)
        if db.get_bind().dialect.name == "postgresql"
        else _items_sqlite(db, organizacion_id)
    )
    analisis = _analizar(cabeceras, items)

    por_presupuesto = analisis["por_presupuesto"]
    presupuestos = []
    for c in cabeceras:
        stats = por_presupuesto.get(c["id"], {"n_items": 0, "modificadas": 0, "personalizadas": 0, "ajustes": 0, "importe_total": 0.0})
        presupuestos.append({
            **c,
            "n_items": stats["n_items"],
            "modificadas": stats["modificadas"],
            "personalizadas": stats["personalizadas"],
            "ajustes": stats["ajustes"],
            "monto_partidas": round(stats["importe_total"], 2),
            "monto": round(c["total_calculado"] or stats["importe_total"], 2),
        })

    return {
        "presupuestos": presupuestos,
        "totales": analisis["totales"],
        "por_estado": analisis["por_estado"],
        "top_modificadas": analisis["top_modificadas"],
        "ajustes": analisis["ajustes"],
        "hoy": date.today(),
    }


def detalle_presupuesto_cliente(db, organizacion_id: int, presupuesto_id: int) -> dict | None:
    """Detalle de un presupuesto del cliente para la vista de solo lectura."""
    cabeceras = (
        _cabeceras_postgres(db, organizacion_id)
        if db.get_bind().dialect.name == "postgresql"
        else _cabeceras_sqlite(db, organizacion_id)
    )
    cabecera = next((c for c in cabeceras if c["id"] == int(presupuesto_id)), None)
    if cabecera is None:
        return None
    items = (
        _items_postgres(db, organizacion_id, presupuesto_id=int(presupuesto_id))
        if db.get_bind().dialect.name == "postgresql"
        else _items_sqlite(db, organizacion_id, presupuesto_id=int(presupuesto_id))
    )
    capitulos: dict[int, dict] = {}
    for i in items:
        clave = (i["capitulo_orden"], i["capitulo"])
        cap = capitulos.setdefault(clave, {"capitulo": i["capitulo"], "orden": i["capitulo_orden"], "partidas": []})
        cap["partidas"].append(i)
    lista_capitulos = [capitulos[k] for k in sorted(capitulos)]

    total_items = len(items)
    modificadas = sum(1 for i in items if i["modificado"])
    personalizadas = sum(1 for i in items if i["personalizada"])
    ajustes = sum(1 for i in items if i["motivos_ajuste"])
    importe_total = round(sum(i["importe"] for i in items), 2)
    return {
        "presupuesto": {**cabecera, "monto": round(cabecera["total_calculado"] or importe_total, 2), "monto_partidas": importe_total},
        "capitulos": lista_capitulos,
        "resumen": {
            "items": total_items,
            "modificadas": modificadas,
            "personalizadas": personalizadas,
            "ajustes": ajustes,
            "importe_total": importe_total,
        },
        "hoy": date.today(),
    }
