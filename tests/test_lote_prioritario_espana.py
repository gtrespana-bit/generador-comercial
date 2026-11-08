"""Trazabilidad y cálculo del lote provisional de materiales prioritarios."""
import csv
from decimal import Decimal, ROUND_HALF_UP
from tools import generar_matriz_precios_espana as g


def leer(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter=';'))


def test_precios_del_lote_y_auditoria():
    fuentes = leer(g.FUENTES_LOTE_PRIORITARIO)
    matriz = {r['codigo_recurso']: r for r in leer(g.OUT)}
    auditoria = {r['codigo_recurso']: r for r in leer(g.ROOT / 'docs/auditoria_precios/espana_2026-11-06.csv')}
    referencias = g.referencias_lote_prioritario()
    esperados = {'MT-PYL-LANA': '2.30', 'MT-PLO-PPR20': '0.91', 'MT-TUB-PPR25': '1.41', 'MT-PIN-CAUCHO': '3.35'}
    for codigo, valor in esperados.items():
        filas = [x for x in fuentes if x['codigo_recurso'] == codigo]
        assert len(filas) == len({x['fuente'] for x in filas}) == 2
        precios = [Decimal(x['importe_eur']) / Decimal(x['cantidad']) / (1 + Decimal(x['iva_decimal'])) for x in filas]
        assert (sum(precios) / 2).quantize(Decimal('.01'), rounding=ROUND_HALF_UP) == Decimal(valor)
        assert Decimal(str(referencias[codigo]['ES'].precio)) == Decimal(valor)
        assert Decimal(matriz[codigo]['precio_referencia']) == Decimal(valor)
        assert matriz[codigo]['fuente'] == g.REVISION_LOTE_PRIORITARIO
        assert matriz[codigo]['fecha_consulta'] == '2026-11-07'
        assert matriz[codigo]['incluye_iva'] == matriz[codigo]['incluye_transporte'] == 'no'
        assert auditoria[codigo]['estado_auditoria'] == 'confirmado_referencia'
        assert Decimal(auditoria[codigo]['precio_revisado']) == Decimal(valor)
