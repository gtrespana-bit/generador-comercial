"""Cálculos, límites y publicación local del lote de tiendas."""
import csv
from decimal import Decimal, ROUND_HALF_UP
from tools import generar_matriz_precios_espana as g


def leer(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter=';'))


def test_lote_y_conversiones():
    fuentes = leer(g.FUENTES_LOTE_TIENDAS)
    matriz = {r['codigo_recurso']: r for r in leer(g.OUT)}
    auditoria = {r['codigo_recurso']: r for r in leer(g.ROOT / 'docs/auditoria_precios/espana_2026-11-06.csv')}
    referencias = g.referencias_lote_tiendas()
    esperados = {'MT-PINT-ANTICORR': '7.75', 'MT-POLIESTIRENO-EXT': '4.74', 'MT-BANDA-REF': '3.01', 'MT-CURADOR': '2.25', 'MT-YESO-REP': '0.16', 'MT-PIN-ESMALTE': '9.84', 'MT-PLO-ABASTO': '2.21', 'MT-POLIUR-LIQ': '7.85'}
    for codigo, valor in esperados.items():
        filas = [f for f in fuentes if f['codigo_recurso'] == codigo]
        assert len(filas) == len({f['fuente'] for f in filas}) == 2
        precios = [Decimal(f['importe_eur']) / Decimal(f['cantidad']) / (1 + Decimal(f['iva_decimal'])) for f in filas]
        assert (sum(precios) / 2).quantize(Decimal('.01'), rounding=ROUND_HALF_UP) == Decimal(valor)
        assert Decimal(str(referencias[codigo]['ES'].precio)) == Decimal(valor)
        assert Decimal(matriz[codigo]['precio_referencia']) == Decimal(valor)
        assert matriz[codigo]['fuente'] == g.REVISION_LOTE_TIENDAS
        assert matriz[codigo]['fecha_consulta'] == '2026-11-07'
        assert auditoria[codigo]['estado_auditoria'] == 'en_revision'
        assert Decimal(auditoria[codigo]['precio_revisado']) == Decimal(valor)
    for codigo in ('MT-PINT-ANTICORR', 'MT-PLO-ABASTO', 'MT-POLIUR-LIQ'):
        assert matriz[codigo]['incluye_transporte'] == 'no_confirmado'
    for codigo in set(esperados) - {'MT-PINT-ANTICORR', 'MT-PLO-ABASTO', 'MT-POLIUR-LIQ'}:
        assert matriz[codigo]['incluye_iva'] == matriz[codigo]['incluye_transporte'] == 'no'
    for f in (f for f in fuentes if f['codigo_recurso'] == 'MT-CURADOR'):
        assert abs(Decimal(f['cantidad']) * Decimal('0.975') - Decimal('25')) < Decimal('1e-18')
