"""Cálculo de mano de obra, cuadrillas y rendimientos por mercado."""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

@dataclass(frozen=True)
class Cuadrilla:
    oficial_hora: Decimal = Decimal("0")
    ayudante_hora: Decimal = Decimal("0")
    especialistas_hora: Decimal = Decimal("0")
    numero_oficiales: Decimal = Decimal("1")
    numero_ayudantes: Decimal = Decimal("1")
    numero_especialistas: Decimal = Decimal("0")
    horas_jornada: Decimal = Decimal("8")

@dataclass(frozen=True)
class RendimientoResultado:
    coste_jornada: Decimal
    produccion_jornada: Decimal
    coste_por_unidad: Decimal
    unidad: str
    aviso: str = ""


def D(value) -> Decimal:
    return Decimal(str(value or 0))


def calcular_rendimiento(cuadrilla: Cuadrilla, produccion_jornada, unidad: str = "ud", cargas_pct=0) -> RendimientoResultado:
    horas = D(cuadrilla.horas_jornada)
    coste = (
        D(cuadrilla.oficial_hora) * D(cuadrilla.numero_oficiales)
        + D(cuadrilla.ayudante_hora) * D(cuadrilla.numero_ayudantes)
        + D(cuadrilla.especialistas_hora) * D(cuadrilla.numero_especialistas)
    ) * horas
    coste = coste * (Decimal("1") + D(cargas_pct) / Decimal("100"))
    produccion = D(produccion_jornada)
    if produccion <= 0:
        return RendimientoResultado(coste.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), produccion, Decimal("0"), unidad, "Falta rendimiento válido")
    por_unidad = (coste / produccion).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return RendimientoResultado(coste.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), produccion, por_unidad, unidad)


def coste_equipo(precio, modalidad: str, *, horas=0, jornadas=0, viajes=0, km=0) -> Decimal:
    modo = str(modalidad or "hora").lower()
    unidades = {"hora": horas, "jornada": jornadas, "viaje": viajes, "km": km}.get(modo, horas)
    return (D(precio) * D(unidades)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
