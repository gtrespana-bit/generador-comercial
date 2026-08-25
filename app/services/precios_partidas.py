"""Recalcula partidas del catálogo con los precios de mercado del país.

El catálogo se guardó históricamente con los precios base (Venezuela, USD).
Cuando una organización cotiza para España, Colombia, México, Perú… los
recursos tienen referencias nacionales en ``precios_recursos_mercado`` y esas
referencias son las que deben alimentar el APU y el precio de venta de la
partida, no el valor base convertido con una tasa.

Este módulo:

* Resuelve el precio de mercado de cada recurso de la descomposición (una
  sola consulta por lote).
* Sustituye el precio unitario de cada fila por el de mercado.
* Recalcula la cascada de costes (materiales, mano de obra, complementarios,
  otros) con la misma lógica CYPE del editor.
* Conserva el margen que tuvo la partida base (beneficio unitario) y aplica
  ese margen sobre el coste directo de mercado.

Si la organización no tiene precios de mercado para un recurso, la fila
vuelve a su precio base convertido a la moneda de la vista y se señala el
fallback, para no inventar cifras.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from sqlalchemy.orm import Session

from ..models import Partida, Recurso
from .recursos import normalizar
from .tasa import tasa_convertir_precio


@dataclass(frozen=True)
class ResultadoPartidaMercado:
    precio_unitario: float
    coste_materiales: float
    coste_mano_obra: float
    coste_complementarios: float
    coste_otros: float
    filas: list[dict]
    con_precio_mercado: bool


def _fila_precio_base(fila: dict, factor: float) -> float:
    try:
        valor = float(fila.get("precio") if fila.get("precio") is not None else fila.get("precio_unitario") or 0)
    except (TypeError, ValueError):
        valor = 0.0
    return tasa_convertir_precio(valor, factor)


def _filas_partida(partida: Partida) -> list[dict]:
    try:
        valor = json.loads(partida.descomposicion_json or "[]")
    except (TypeError, ValueError):
        valor = []
    filas = valor.get("filas", []) if isinstance(valor, dict) else valor
    return [dict(fila) if isinstance(fila, dict) else fila for fila in filas]


def _recurso_de_fila(recurso: Recurso, fila: dict) -> bool:
    cod_recurso = normalizar(recurso.codigo)
    cod_fila = normalizar(fila.get("codigo"))
    if cod_recurso and cod_fila:
        return cod_recurso == cod_fila
    return (
        normalizar(recurso.descripcion) == normalizar(fila.get("descripcion"))
        and normalizar(recurso.unidad) == normalizar(fila.get("unidad"))
        and normalizar(recurso.categoria) == normalizar(fila.get("categoria"))
    )


def _buscar_recursos(db: Session, filas: list[dict]) -> list[Recurso]:
    """Busca los recursos de la BD que corresponden a las filas del APU."""
    codigos = {normalizar(f.get("codigo")) for f in filas if f.get("codigo")}
    filas_sin_codigo = [f for f in filas if not (f.get("codigo") or "").strip()]
    if codigos and not filas_sin_codigo:
        return [
            r for r in db.query(Recurso).filter(Recurso.codigo != "").all()
            if normalizar(r.codigo) in codigos
        ]
    # Con filas sin código el volumen es pequeño: se barre la tabla local.
    recursos = db.query(Recurso).all()
    salida: list[Recurso] = []
    visto: set[int] = set()
    for fila in filas:
        for recurso in recursos:
            if recurso.id in visto:
                continue
            if _recurso_de_fila(recurso, fila):
                salida.append(recurso)
                visto.add(recurso.id)
                break
    return salida


def _resolver_precios_filas(
    db: Session, filas: list[dict], pais: str, org_id: int | None,
    moneda: str, factor: float,
) -> dict[str, float]:
    """Devuelve {clave_fila: precio de mercado en moneda de la vista}.

    La clave es el código normalizado cuando existe y, si no, una cadena
    derivada de descripción/unidad/categoría.
    """
    from .precios_mercado import resolver_precios_para_presupuesto_lote

    recursos = _buscar_recursos(db, filas)
    if not recursos:
        return {}
    efectivos = resolver_precios_para_presupuesto_lote(
        db, recursos, pais, org_id, moneda, tasa_usd_presupuesto=factor,
    )
    if not efectivos:
        return {}
    por_id = {r.id: r for r in recursos}
    salida: dict[str, float] = {}
    for r in por_id.values():
        ef = efectivos.get(r.id)
        # Solo se consideran precios reales de este país: referencia nacional
        # o precio fijado por la organización. El precio base de la partida
        # original (Venezuela convertida) no es un precio de mercado y no debe
        # alimentar el APU mostrado.
        if (
            ef is not None
            and ef.get("precio") is not None
            and not ef.get("requiere_tasa")
            and (ef.get("origen") or "base") in ("nacional", "organizacion")
        ):
            salida[normalizar(r.codigo)] = float(ef["precio"])
    # Filas sin código: match por descripción. Solo se guardan cuando hay
    # referencia nacional real; si no, la fila usará su precio base.
    for fila in filas:
        cod = normalizar(fila.get("codigo"))
        if cod and cod in salida:
            continue
        clave = f"desc:{normalizar(fila.get('descripcion'))}|{normalizar(fila.get('unidad'))}|{normalizar(fila.get('categoria'))}"
        for r in por_id.values():
            if _recurso_de_fila(r, fila):
                ef = efectivos.get(r.id)
                if (
                    ef is not None
                    and ef.get("precio") is not None
                    and not ef.get("requiere_tasa")
                    and (ef.get("origen") or "base") in ("nacional", "organizacion")
                ):
                    salida.setdefault(clave, float(ef["precio"]))
                break
    return salida


def recalcular_partida_mercado(
    db: Session,
    partida: Partida,
    pais: str,
    org_id: int | None,
    moneda: str,
    factor: float,
) -> ResultadoPartidaMercado | None:
    """Recalcula una partida con los precios de mercado de su país.

    Devuelve ``None`` cuando la partida no tiene descomposición utilizable: en
    ese caso la vista debe mantener el precio base convertido (no hay nada que
    recalcular).
    """
    filas = _filas_partida(partida)
    filas = [f for f in filas if isinstance(f, dict) and f.get("tipo") == "recurso"]
    if not filas:
        return None

    precios = _resolver_precios_filas(db, filas, pais, org_id, moneda, factor)
    if not precios:
        return None

    desde_mercado = False
    nuevas_filas: list[dict] = []
    for fila in filas:
        nueva = dict(fila)
        cod = fila.get("codigo")
        clave = normalizar(cod) if cod else ""
        if not clave or clave not in precios:
            clave = f"desc:{normalizar(fila.get('descripcion'))}|{normalizar(fila.get('unidad'))}|{normalizar(fila.get('categoria'))}"
        precio = precios.get(clave)
        if precio is None:
            precio = _fila_precio_base(fila, factor)
        nueva["precio"] = precio
        nueva["precio_unitario"] = precio
        # El importe lo recalcula la cascada CYPE; aquí solo mantenemos el
        # precio por si la fila es un % de complementarios.
        nuevas_filas.append(nueva)
        if clave in precios:
            desde_mercado = True

    from .importer import recalcular_descompuesto_cype

    if not desde_mercado:
        return None
    resultado = recalcular_descompuesto_cype(nuevas_filas)
    costes = resultado.get("costes", {})
    coste_directo = float(resultado.get("coste_directo", 0) or 0)

    # Margen conservado de la partida base (USD). Si la partida no tenía
    # coste o precio usamos el margen por defecto del catálogo (35 % desde
    # 2026-08-25).
    coste_base = (
        float(partida.coste_materiales or 0)
        + float(partida.coste_mano_obra or 0)
        + float(partida.coste_complementarios or 0)
        + float(partida.coste_otros or 0)
    )
    precio_base = float(partida.precio_unitario or 0)
    margen = (precio_base - coste_base) / coste_base if coste_base > 0 else 0.35
    precio_venta = round(coste_directo * (1.0 + margen), 2)

    # Aplica los precios de la cascada (para las filas de % se usa el precio
    # base recalculado).
    for idx, precio_comp in resultado.get("precios_complementarios", {}).items():
        if 0 <= idx < len(nuevas_filas):
            nuevas_filas[idx]["precio"] = precio_comp
            nuevas_filas[idx]["precio_unitario"] = precio_comp
    for idx, importe in resultado.get("importes", {}).items():
        if 0 <= idx < len(nuevas_filas):
            nuevas_filas[idx]["importe"] = importe

    return ResultadoPartidaMercado(
        precio_unitario=precio_venta,
        coste_materiales=float(costes.get("materiales", 0) or 0),
        coste_mano_obra=float(costes.get("mano_obra", 0) or 0),
        coste_complementarios=float(costes.get("complementarios", 0) or 0),
        coste_otros=float(costes.get("otros", 0) or 0),
        filas=nuevas_filas,
        con_precio_mercado=desde_mercado,
    )


def recalcular_partidas_mercado(
    db: Session,
    partidas: list[Partida],
    pais: str,
    org_id: int | None,
    moneda: str,
    factor: float,
) -> dict[int, ResultadoPartidaMercado]:
    """Versión por lote para las listas del catálogo (una consulta por fila no)."""
    salida: dict[int, ResultadoPartidaMercado] = {}
    for partida in partidas:
        try:
            resultado = recalcular_partida_mercado(
                db, partida, pais, org_id, moneda, factor,
            )
            if resultado is not None:
                salida[partida.id] = resultado
        except Exception:
            continue
    return salida
