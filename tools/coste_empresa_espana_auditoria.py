#!/usr/bin/env python3
"""Modelo de auditoría, NO actualiza precios ni determina bases o tarifas.

Escenario: Régimen General, contrato indefinido ordinario en 2026, sin
bonificaciones. Los parámetros se introducen para un año completo y deben
proceder de nómina, convenio y actividad. Las bases se suministran por
separado: el salario no es automáticamente la base de cotización.

El coste calculado solo incluye lo introducido. No estima costes desconocidos,
ni decide si un gasto está en otro concepto del presupuesto. No valida topes,
convenio, bonificaciones, ni la aplicabilidad del tipo de accidentes.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


@dataclass(frozen=True)
class Resultado:
    cuotas_comunes_mei: Decimal
    cuotas_profesionales: Decimal
    total_anual: Decimal
    coste_hora: Decimal


def calcular_coste_empresa(
    *, salario_anual: Decimal, base_comun_anual: Decimal,
    base_profesional_anual: Decimal, pension_empresa: Decimal,
    otros_costes: Decimal, horas_productivas: Decimal,
    porcentaje_at_ep: Decimal,
) -> Resultado:
    """Devuelve las cuotas y el coste con los importes explícitos, en euros.

    Las bases ya deben incluir las retribuciones en especie que correspondan.
    El salario no debe incluir la contribución al plan que se suma aparte.
    Otros costes no deben estar incluidos ya en salario ni repercutidos en otra
    línea presupuestaria. Las horas productivas no se presuponen iguales a la
    jornada del convenio. AT/EP se indica como porcentaje: 6.7, no 0.067.
    """
    valores = (salario_anual, base_comun_anual, base_profesional_anual,
               pension_empresa, otros_costes, horas_productivas, porcentaje_at_ep)
    if any(not isinstance(v, Decimal) or not v.is_finite() for v in valores):
        raise ValueError('Todos los importes deben ser decimales finitos.')
    if any(v < 0 for v in valores) or horas_productivas <= 0:
        raise ValueError('Los importes no pueden ser negativos y las horas deben ser positivas.')
    if salario_anual <= 0 or base_comun_anual <= 0 or base_profesional_anual <= 0:
        raise ValueError('Salario y bases de cotización deben ser positivos.')
    if porcentaje_at_ep > 100:
        raise ValueError('El porcentaje AT/EP no puede superar 100.')
    # Régimen General 2026, indefinido ordinario: 23,60 % CC + 0,75 % MEI.
    comunes_mei = base_comun_anual * Decimal('0.2435')
    # Sobre base profesional: 5,50 desempleo + 0,20 FOGASA + 0,60 FP + AT/EP.
    profesionales = base_profesional_anual * (Decimal('0.063') + porcentaje_at_ep / 100)
    total = salario_anual + comunes_mei + profesionales + pension_empresa + otros_costes
    return Resultado(comunes_mei, profesionales, total, total / horas_productivas)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    for nombre, ayuda in (
        ('salario-anual', 'Retribución bruta anual sin contribución empresarial al plan'),
        ('base-comun-anual', 'Base anual de contingencias comunes, incluidos conceptos aplicables'),
        ('base-profesional-anual', 'Base anual de contingencias profesionales'),
        ('pension-empresa', 'Contribución anual empresarial al plan, en euros'),
        ('otros-costes', 'Costes anuales atribuibles no contabilizados en otros conceptos'),
        ('horas-productivas', 'Horas productivas anuales estimadas o medidas'),
        ('porcentaje-at-ep', 'Tipo aplicable de AT/EP en porcentaje, por ejemplo 6.7'),
    ):
        p.add_argument('--' + nombre, required=True, help=ayuda)
    args = p.parse_args()
    try:
        valores = {k: Decimal(v.replace(',', '.')) for k, v in vars(args).items()}
        r = calcular_coste_empresa(**valores)
    except (InvalidOperation, ValueError) as exc:
        p.error(str(exc))
    print('Modelo orientativo, solo con los conceptos introducidos; no es una nómina.')
    print(f'Cuota empresarial CC + MEI: {r.cuotas_comunes_mei:.2f} EUR/año')
    print(f'Cuota empresarial desempleo + FOGASA + FP + AT/EP: {r.cuotas_profesionales:.2f} EUR/año')
    print(f'Coste anual calculado: {r.total_anual:.2f} EUR')
    print(f'Coste por hora productiva: {r.coste_hora:.2f} EUR/h')


if __name__ == '__main__':
    main()
