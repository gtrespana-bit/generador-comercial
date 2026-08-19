"""Integración de recursos, rendimientos y costes directos de partidas."""
from __future__ import annotations
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass

@dataclass(frozen=True)
class ResultadoAPU:
    coste_directo: Decimal
    materiales: Decimal
    mano_obra: Decimal
    complementarios: Decimal
    otros: Decimal
    filas_calculadas: int


def _d(v): return Decimal(str(v or 0))
def _m(v): return _d(v).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def calcular_apu(filas) -> ResultadoAPU:
    acumulados = {'materiales': Decimal('0'), 'mano_obra': Decimal('0'), 'complementarios': Decimal('0'), 'otros': Decimal('0')}
    n = 0
    for fila in filas or []:
        if getattr(fila, 'tipo', '') not in ('recurso', 'material', 'mano_obra', 'equipo', 'complementario', 'otro'):
            continue
        rendimiento = _d(getattr(fila, 'rendimiento', 0))
        precio = _d(getattr(fila, 'precio_unitario', 0))
        importe = _m(rendimiento * precio)
        fila.importe = float(importe)
        categoria = str(getattr(fila, 'categoria', '') or 'otros').lower()
        if categoria not in acumulados: categoria = 'otros'
        acumulados[categoria] += importe
        n += 1
    for k in acumulados: acumulados[k] = _m(acumulados[k])
    return ResultadoAPU(_m(sum(acumulados.values())), acumulados['materiales'], acumulados['mano_obra'], acumulados['complementarios'], acumulados['otros'], n)
