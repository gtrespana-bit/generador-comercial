import apoyo_cierre_espana as cierre
import csv
from decimal import Decimal
import pytest
from tools import generar_matriz_precios_espana as g


def leer(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter=';'))


def test_precios_materiales_en_matriz_y_auditoria():
    filas = leer(g.FUENTES_LOTE_MATERIALES)
    assert len(filas) == 7
    refs = g.referencias_lote_materiales()
    matriz = {r['codigo_recurso']: r for r in leer(g.OUT)}
    auditoria = {r['codigo_recurso']: r for r in leer(g.ROOT / 'docs/auditoria_precios/espana_2026-11-06.csv')}
    for f in filas:
        code, price = f['codigo_recurso'], Decimal(f['precio_eur'])
        m, a = matriz[code], auditoria[code]
        assert Decimal(str(refs[code]['ES'].precio)) == price == Decimal(m['precio_referencia'])
        assert Decimal(m['precio_min']) == price == Decimal(m['precio_max'])
        assert m['unidad_fuente'] == f['unidad'] and m['fecha_consulta'] == '2026-11-07'
        assert m['fuente'] == cierre.fuente(code, g.REVISION_LOTE_MATERIALES)
        assert m['confianza'] == 'derivado'
        assert m['incluye_iva'] == m['incluye_transporte'] == 'no_confirmado'
        assert a['estado_auditoria'] == cierre.estado(code, 'en_revision')
        assert Decimal(a['precio_revisado']) == price


def test_fuentes_incompletas_o_unidad_invalida(monkeypatch, tmp_path):
    filas = leer(g.FUENTES_LOTE_MATERIALES)
    archivo = tmp_path / 'fuentes.csv'
    monkeypatch.setattr(g, 'FUENTES_LOTE_MATERIALES', archivo)
    def escribir(rows):
        with archivo.open('w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=filas[0], delimiter=';')
            w.writeheader(); w.writerows(rows)
    escribir(filas[:-1])
    with pytest.raises(ValueError, match='incompleto'):
        g.referencias_lote_materiales()
    filas[0]['unidad'] = 'ud'
    escribir(filas)
    with pytest.raises(ValueError, match='inválida'):
        g.referencias_lote_materiales()
