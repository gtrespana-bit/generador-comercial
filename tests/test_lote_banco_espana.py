import csv
from decimal import Decimal

import pytest

from tools import generar_matriz_precios_espana as g


def leer(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter=';'))


def test_lote_banco_en_matriz_y_auditoria():
    filas = leer(g.FUENTES_LOTE_BANCO)
    assert len(filas) == 10
    refs = g.referencias_lote_banco()
    matriz = {r['codigo_recurso']: r for r in leer(g.OUT)}
    auditoria = {r['codigo_recurso']: r for r in leer(g.ROOT / 'docs/auditoria_precios/espana_2026-11-06.csv')}
    for f in filas:
        code = f['codigo_recurso']
        precio = Decimal(f['precio_eur'])
        m, a = matriz[code], auditoria[code]
        assert Decimal(str(refs[code]['ES'].precio)) == precio == Decimal(m['precio_referencia'])
        assert Decimal(m['precio_min']) == precio == Decimal(m['precio_max'])
        assert m['unidad_fuente'] == f['unidad'] and m['fecha_consulta'] == '2026-11-07'
        assert m['fuente'] == g.REVISION_LOTE_BANCO and m['confianza'] == 'derivado'
        assert m['incluye_iva'] == m['incluye_transporte'] == 'no_confirmado'
        assert a['estado_auditoria'] == 'en_revision' and Decimal(a['precio_revisado']) == precio
    assert Decimal('1.5') * Decimal('.18') + Decimal('1.2') * Decimal('.75') + Decimal('.15') == Decimal('1.32')
    assert Decimal('4.62') + Decimal('2.63') + Decimal('3.00') == Decimal('10.25')


def test_lote_no_admite_unidad_erronea_ni_fuentes_incompletas(monkeypatch, tmp_path):
    filas = leer(g.FUENTES_LOTE_BANCO)
    archivo = tmp_path / 'fuentes.csv'
    monkeypatch.setattr(g, 'FUENTES_LOTE_BANCO', archivo)
    def escribir(rows):
        with archivo.open('w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=filas[0], delimiter=';')
            w.writeheader(); w.writerows(rows)
    escribir(filas[:-1])
    with pytest.raises(ValueError, match='incompleto'):
        g.referencias_lote_banco()
    filas[0]['unidad'] = 'ud'
    escribir(filas)
    with pytest.raises(ValueError, match='inválida'):
        g.referencias_lote_banco()
