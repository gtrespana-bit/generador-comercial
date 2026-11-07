import csv
from decimal import Decimal

import pytest
from tools import generar_matriz_precios_espana as g


def leer(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter=';'))


def test_fuentes_matriz_y_auditoria_coinciden():
    fuentes = leer(g.FUENTES_LOTE_BLOQUE_AMPLIO)
    refs = g.referencias_lote_bloque_amplio()
    assert len(fuentes) == 14 and len(refs) == 12
    for codigo, precio in {'MT-CANAL-PVC': '10.11', 'MT-ESCALERILLA': '2.41', 'MT-TOMA-DATOS': '39.16', 'MT-LADRILLO-VISTO': '0.44', 'MT-TORNILLO-EST': '7.80', 'MT-STEELDECK': '28.94', 'MT-CANON-TIERRA': '2.14', 'MT-ENDURECEDOR': '0.63', 'MT-BARRERA-ANTICAP': '0.87', 'MT-ANCLA-PIEDRA': '6.00', 'MT-EXTINTOR': '63.00', 'MT-ARNES': '44.93'}.items():
        assert Decimal(str(refs[codigo]['ES'].precio)) == Decimal(precio)
    matriz = {r['codigo_recurso']: r for r in leer(g.OUT)}
    audit = {r['codigo_recurso']: r for r in leer(g.ROOT / 'docs/auditoria_precios/espana_2026-11-06.csv')}
    for codigo, ref in refs.items():
        filas = [r for r in fuentes if r['codigo_recurso'] == codigo]
        dato = ref['ES']
        assert Decimal(str(dato.precio)) == Decimal(audit[codigo]['precio_revisado']) == Decimal(matriz[codigo]['precio_referencia'])
        assert audit[codigo]['estado_auditoria'] == 'en_revision'
        assert matriz[codigo]['fuente'] == g.REVISION_LOTE_BLOQUE_AMPLIO
        assert matriz[codigo]['fecha_consulta'] == '2026-11-07'
        assert matriz[codigo]['incluye_iva'] == ('por_verificar' if any(r['criterio_iva'] == 'IVA no confirmado' for r in filas) else 'no')
        assert matriz[codigo]['incluye_transporte'] == 'no_confirmado'
        assert all(r['url'] in audit[codigo]['fuente_observada'] for r in filas)
    assert not audit['MQ-DETECTOR']['precio_revisado']


def test_datos_invalidos_y_conjuntos_incompletos_se_rechazan(monkeypatch, tmp_path):
    fuentes = leer(g.FUENTES_LOTE_BLOQUE_AMPLIO)
    path = tmp_path / 'fuentes.csv'
    monkeypatch.setattr(g, 'FUENTES_LOTE_BLOQUE_AMPLIO', path)
    def escribir(rows):
        with path.open('w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=fuentes[0], delimiter=';', lineterminator='\n')
            w.writeheader(); w.writerows(rows)
    for rows in (fuentes[:-1], fuentes + fuentes[:1]):
        escribir(rows)
        with pytest.raises(ValueError):
            g.referencias_lote_bloque_amplio()
    for campo, valor in [('unidad', 'h'), ('importe_base', '-1'), ('cantidad_por_envase', '0'),
                         ('cantidad_por_recurso', 'NaN'), ('url_precio', ''), ('precio_resultante', '999'),
                         ('precio_bruto', '999'), ('criterio_iva', 'sin dato')]:
        malas = [r.copy() for r in fuentes]; malas[0][campo] = valor; escribir(malas)
        with pytest.raises(ValueError):
            g.referencias_lote_bloque_amplio()
