"""Importador validado de la matriz nacional de precios.

Por defecto solo procesa referencias investigadas. Las filas pendientes nunca
se convierten en cero y los respaldos por tipo de cambio requieren una opción
explícita. Antes de escribir se valida **toda** la matriz para evitar cargas
parciales con unidad, rango, país o moneda incoherentes.
"""
from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from sqlalchemy.orm import Session

from ..models import Recurso
from .precios_mercado import guardar_precio

MONEDA_PAIS = {"CO": "COP", "PE": "PEN", "MX": "MXN", "EC": "USD", "PA": "USD", "SV": "USD", "CL": "CLP", "AR": "ARS", "DO": "DOP", "UY": "UYU", "PY": "PYG", "VE": "USD", "ES": "EUR"}
CONFIANZAS = {"confirmado", "referencia", "derivado", "provisional"}
IVA_VALIDO = {"si", "no", "no_aplica", "no_confirmado", "por_verificar"}
TRANSPORTE_VALIDO = {"si", "no", "no_aplica", "no_confirmado", "por_verificar"}


def _texto(row: dict, clave: str) -> str:
    return str(row.get(clave) or "").strip()


def _numero(row: dict, clave: str, *, obligatorio: bool = False) -> float | None:
    bruto = _texto(row, clave).replace(",", ".")
    if not bruto:
        if obligatorio:
            raise ValueError(f"falta {clave}")
        return None
    valor = float(bruto)
    if valor <= 0:
        raise ValueError(f"{clave} debe ser mayor que cero")
    return valor


def _fecha(row: dict, clave: str, *, obligatoria: bool = False) -> date | None:
    bruto = _texto(row, clave)
    if not bruto:
        if obligatoria:
            raise ValueError(f"falta {clave}")
        return None
    try:
        return date.fromisoformat(bruto)
    except ValueError as exc:
        raise ValueError(f"{clave} no es ISO AAAA-MM-DD") from exc


def _unidad(valor: str) -> str:
    return {
        "h": "hora", "hr": "hora", "m²": "m2", "m³": "m3",
        "u": "ud", "und": "ud",
    }.get(str(valor or "").strip(), str(valor or "").strip())


def importar_matriz_csv(
    db: Session,
    ruta: str | Path,
    *,
    aplicar: bool = False,
    incluir_respaldo: bool = False,
) -> dict:
    ruta = Path(ruta)
    resultado = {
        "filas": 0,
        "aplicables": 0,
        "creadas_o_actualizadas": 0,
        "pendientes": 0,
        "no_encontrados": 0,
        "errores": [],
    }
    recursos = {r.codigo.strip(): r for r in db.query(Recurso).all() if r.codigo}
    vistos: set[tuple[str, str]] = set()
    planes: list[tuple[Recurso, dict]] = []

    with ruta.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh, delimiter=";")
        requeridas = {
            "codigo_recurso", "descripcion", "categoria", "unidad_fuente",
            "pais_codigo", "moneda", "precio_referencia", "precio_min",
            "precio_max", "fuente", "fecha_consulta", "confianza",
            "incluye_iva", "incluye_transporte", "origen", "observaciones",
        }
        faltantes = sorted(requeridas - set(reader.fieldnames or []))
        if faltantes:
            resultado["errores"].append(
                "Faltan columnas obligatorias: " + ", ".join(faltantes)
            )
            return resultado

        for numero_fila, row in enumerate(reader, start=2):
            resultado["filas"] += 1
            codigo = _texto(row, "codigo_recurso")
            pais = _texto(row, "pais_codigo").upper()
            clave = (codigo, pais)
            prefijo = f"fila {numero_fila} ({codigo or 'sin código'}/{pais or 'sin país'})"
            if clave in vistos:
                resultado["errores"].append(f"{prefijo}: fila duplicada")
                continue
            vistos.add(clave)

            origen = _texto(row, "origen")
            precio_raw = _texto(row, "precio_referencia")
            if not precio_raw:
                resultado["pendientes"] += 1
                if origen != "pendiente" or _texto(row, "confianza") != "pendiente":
                    resultado["errores"].append(
                        f"{prefijo}: una fila sin precio debe ser pendiente/pendiente"
                    )
                continue
            if origen == "base" and not incluir_respaldo:
                resultado["pendientes"] += 1
                continue
            if origen not in {"nacional", "base"}:
                resultado["errores"].append(f"{prefijo}: origen no permitido «{origen}»")
                continue

            recurso = recursos.get(codigo)
            if recurso is None:
                resultado["no_encontrados"] += 1
                resultado["errores"].append(f"{prefijo}: recurso no encontrado")
                continue
            try:
                if pais not in MONEDA_PAIS:
                    raise ValueError("país no soportado")
                moneda = _texto(row, "moneda").upper()
                if moneda != MONEDA_PAIS[pais]:
                    raise ValueError(
                        f"moneda {moneda or 'vacía'}; se esperaba {MONEDA_PAIS[pais]}"
                    )
                if _unidad(_texto(row, "unidad_fuente")) != _unidad(recurso.unidad):
                    raise ValueError(
                        f"unidad {_texto(row, 'unidad_fuente') or 'vacía'}; "
                        f"el recurso usa {recurso.unidad}"
                    )
                precio = _numero(row, "precio_referencia", obligatorio=True)
                minimo = _numero(row, "precio_min")
                maximo = _numero(row, "precio_max")
                if origen == "nacional" and (minimo is None or maximo is None):
                    raise ValueError("la referencia nacional debe conservar precio_min y precio_max")
                if minimo is not None and maximo is not None and maximo < minimo:
                    raise ValueError("precio_max es menor que precio_min")
                if minimo is not None and precio < minimo or maximo is not None and precio > maximo:
                    raise ValueError("precio_referencia queda fuera del rango")
                confianza = _texto(row, "confianza")
                if confianza not in CONFIANZAS:
                    raise ValueError(f"confianza no válida «{confianza}»")
                fuente = _texto(row, "fuente")
                if not fuente:
                    raise ValueError("falta fuente")
                consulta = _fecha(row, "fecha_consulta", obligatoria=True)
                iva = _texto(row, "incluye_iva")
                transporte = _texto(row, "incluye_transporte")
                if iva not in IVA_VALIDO:
                    raise ValueError(f"incluye_iva no válido «{iva}»")
                if transporte not in TRANSPORTE_VALIDO:
                    raise ValueError(f"incluye_transporte no válido «{transporte}»")
            except (TypeError, ValueError) as exc:
                resultado["errores"].append(f"{prefijo}: {exc}")
                continue

            planes.append((recurso, {
                "pais": pais,
                "precio": precio,
                "moneda": moneda,
                "precio_min": minimo,
                "precio_max": maximo,
                "unidad_referencia": _texto(row, "unidad_fuente"),
                "fuente": fuente,
                "confianza": confianza,
                "fecha_consulta": consulta,
                "incluye_iva": iva,
                "incluye_transporte": transporte,
                "observaciones": _texto(row, "observaciones"),
            }))

    resultado["aplicables"] = len(planes)
    # La carga es todo-o-nada: un rango corrupto no puede convivir con las
    # filas que sí alcanzaron a guardarse antes del error.
    if aplicar and not resultado["errores"]:
        try:
            for recurso, dato in planes:
                guardar_precio(
                    db,
                    recurso.id,
                    dato["pais"],
                    dato["precio"],
                    dato["moneda"],
                    fuente=dato["fuente"],
                    confianza=dato["confianza"],
                    fecha_consulta=dato["fecha_consulta"],
                    precio_min=dato["precio_min"],
                    precio_max=dato["precio_max"],
                    unidad_referencia=dato["unidad_referencia"],
                    incluye_iva=dato["incluye_iva"],
                    incluye_transporte=dato["incluye_transporte"],
                    observaciones=dato["observaciones"],
                )
            db.commit()
            resultado["creadas_o_actualizadas"] = len(planes)
        except Exception:
            db.rollback()
            raise
    return resultado
