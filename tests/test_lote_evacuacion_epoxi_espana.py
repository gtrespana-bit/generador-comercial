import csv
from decimal import Decimal

import pytest
from tools import generar_matriz_precios_espana as g


def leer(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter=';'))


def test_fuentes_auditoria_y_matriz():
    fuentes = leer(g.FUENTES_LOTE_EVACUACION_EPOXI)
    refs = g.referencias_lote_evacuacion_epoxi()
    assert len(fuentes) == 5 and len(refs) == 3
    esperados = {'MT-PLO-PVC4': ('10.36', 'por_verificar'),
                 'MT-TRAGANTE': ('37.82', 'no'),
                 'MT-EPOXI-ANCLA': ('24.23', 'por_verificar')}
    matriz = {r['codigo_recurso']: r for r in leer(g.OUT)}
    audit = {r['codigo_recurso']: r for r in leer(g.ROOT / 'docs/auditoria_precios/espana_2026-11-06.csv')}
    for codigo, (precio, iva) in esperados.items():
        assert Decimal(str(refs[codigo]['ES'].precio)) == Decimal(precio)
        assert Decimal(matriz[codigo]['precio_referencia']) == Decimal(precio) == Decimal(audit[codigo]['precio_revisado'])
        assert audit[codigo]['estado_auditoria'] == 'en_revision'
        assert matriz[codigo]['fuente'] == g.REVISION_LOTE_EVACUACION_EPOXI
        assert matriz[codigo]['fecha_consulta'] == '2026-11-07'
        assert matriz[codigo]['incluye_iva'] == iva
        assert matriz[codigo]['incluye_transporte'] == 'no_confirmado'
        for fila in (f for f in fuentes if f['codigo_recurso'] == codigo):
            assert fila['url'] in audit[codigo]['fuente_observada']
            if fila['url_tecnica']:
                assert fila['url_tecnica'] in audit[codigo]['fuente_observada']
    tubo = [r for r in fuentes if r['codigo_recurso'] == 'MT-PLO-PVC4']
    assert sum(Decimal(r['importe_base']) / Decimal(r['cantidad_por_envase']) * Decimal(r['cantidad_por_recurso']) for r in tubo).quantize(Decimal('.01')) == Decimal('10.36')
    epoxi = next(r for r in fuentes if r['codigo_recurso'] == 'MT-EPOXI-ANCLA')
    assert epoxi['url_tecnica'] and 'aprox. 1 kg por litro' in epoxi['reserva']
    assert not audit['MT-TUBO-ACERO']['precio_revisado']


def test_rechaza_componentes_invalidos_o_faltantes(monkeypatch, tmp_path):
    fuentes = leer(g.FUENTES_LOTE_EVACUACION_EPOXI)
    path = tmp_path / 'fuentes.csv'
    monkeypatch.setattr(g, 'FUENTES_LOTE_EVACUACION_EPOXI', path)
    def escribir(rows):
        with path.open('w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=fuentes[0], delimiter=';', lineterminator='\n')
            w.writeheader(); w.writerows(rows)
    for rows in (fuentes[:-1], fuentes + fuentes[:1]):
        escribir(rows)
        with pytest.raises(ValueError):
            g.referencias_lote_evacuacion_epoxi()
    for campo, valor in [('unidad', 'h'), ('importe_base', '-1'), ('cantidad_por_envase', '0'),
                         ('cantidad_por_recurso', 'NaN'), ('url_precio', ''), ('precio_resultante', '999'),
                         ('precio_bruto', '999'), ('criterio_iva', 'sin dato')]:
        malas = [r.copy() for r in fuentes]; malas[0][campo] = valor; escribir(malas)
        with pytest.raises(ValueError):
            g.referencias_lote_evacuacion_epoxi()
