"""Precios comerciales reproducibles, con rechazos y preservación de alcance."""
import csv
from decimal import Decimal, ROUND_HALF_UP
import pytest
from tools import generar_matriz_precios_espana as g


def leer(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter=';'))


def test_medias_y_artefactos():
    fuentes = leer(g.FUENTES_LOTE_COMERCIAL)
    matriz = {x['codigo_recurso']: x for x in leer(g.OUT)}
    audit = {x['codigo_recurso']: x for x in leer(g.ROOT / 'docs/auditoria_precios/espana_2026-11-06.csv')}
    esperados = {'MT-MADERA-LISTON': '0.82', 'MT-PIN-FONDO': '4.09', 'MT-SEPARADOR': '0.06', 'MT-GEOTEXTIL': '0.68'}
    referencias = g.referencias_lote_comercial()
    for codigo, esperado in esperados.items():
        filas = [x for x in fuentes if x['codigo_recurso'] == codigo]
        assert len(filas) == len({x['fuente'] for x in filas}) == 2
        precios = [Decimal(x['importe_eur']) / Decimal(x['cantidad']) / (1 + Decimal(x['iva_decimal'])) for x in filas]
        assert (sum(precios) / 2).quantize(Decimal('.01'), rounding=ROUND_HALF_UP) == Decimal(esperado)
        assert Decimal(str(referencias[codigo]['ES'].precio)) == Decimal(esperado)
        assert matriz[codigo]['precio_referencia'] == esperado
        assert matriz[codigo]['fuente'] == g.REVISION_LOTE_COMERCIAL
        assert matriz[codigo]['incluye_iva'] == matriz[codigo]['incluye_transporte'] == 'no'
        assert audit[codigo]['estado_auditoria'] == 'en_revision'
        assert audit[codigo]['precio_revisado'] == esperado


def test_rechaza_fuentes_invalidas(tmp_path, monkeypatch):
    filas = leer(g.FUENTES_LOTE_COMERCIAL)
    path = tmp_path / 'fuentes.csv'
    monkeypatch.setattr(g, 'FUENTES_LOTE_COMERCIAL', path)
    def guardar():
        with path.open('w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=filas[0].keys(), delimiter=';')
            w.writeheader(); w.writerows(filas)
    filas[1]['fuente'] = filas[0]['fuente']; guardar()
    with pytest.raises(ValueError, match='dos fuentes'):
        g.referencias_lote_comercial()
    filas[1]['fuente'] = 'otra'; filas[0]['cantidad'] = '0'; guardar()
    with pytest.raises(ValueError, match='inválida'):
        g.referencias_lote_comercial()
    filas[0]['cantidad'] = '3'; filas[0]['unidad'] = 'kg'; guardar()
    with pytest.raises(ValueError, match='unidad'):
        g.referencias_lote_comercial()
