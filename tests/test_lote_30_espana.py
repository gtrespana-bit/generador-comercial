import apoyo_cierre_espana as cierre
import csv
from decimal import Decimal
import pytest
from tools import generar_matriz_precios_espana as g


def leer(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter=';'))


def test_lote_30_trazable_y_precio_provisional():
    esperados = {'MT-TUB-RIEGO': '1.19', 'MT-CUARZO-COLOR': '2.47',
                 'MT-POLIUREA': '5.80', 'MT-DOM-ACTUADOR': '61.42',
                 'MT-DOM-DIMMER': '58.40', 'MT-DOM-SENSOR-INUND': '38.99',
                 'MT-DOM-SENSOR-MOV': '43.87', 'MT-DOM-SENSOR-LUZ': '43.87',
                 'MT-DOM-SENSOR-PUERTA': '38.99'}
    bloqueados = {'MQ-TALADRO', 'MT-CONS-DEM', 'MQ-SIERRA', 'MQ-ANDAMIO',
                  'MT-ELE-CAJA', 'MQ-ATORN', 'MT-TORN', 'MQ-RODILLO', 'MQ-VIBRADOR',
                  'MQ-MEZCL', 'MQ-SOLDADORA', 'MQ-RETRO', 'MT-TUBO-ACERO',
                  'MT-CABLE-COBRE-DESN', 'MT-POLIET', 'MT-MALLA-ESQ',
                  'MQ-PROYECT-MORT', 'MT-ESTUCO-VEN', 'MT-GRAMA', 'MT-BLQ-12', 'MT-DOM-CENTRAL'}
    assert len(esperados) + len(bloqueados) == 30
    fuentes = leer(g.FUENTES_LOTE_30)
    refs = g.referencias_lote_treinta()
    matriz = {x['codigo_recurso']: x for x in leer(g.OUT)}
    audit = {x['codigo_recurso']: x for x in leer(g.ROOT / 'docs/auditoria_precios/espana_2026-11-06.csv')}
    informe = (g.ROOT / g.REVISION_LOTE_30).read_text(encoding='utf-8')
    assert len(fuentes) == len(refs) == 9
    for c, p in esperados.items():
        assert Decimal(str(refs[c]['ES'].precio)) == Decimal(p)
        assert Decimal(matriz[c]['precio_referencia']) == Decimal(p) == Decimal(audit[c]['precio_revisado'])
        assert audit[c]['estado_auditoria'] == 'en_revision'
        assert matriz[c]['fuente'] == g.REVISION_LOTE_30
        assert matriz[c]['incluye_iva'] == 'por_verificar'
        assert matriz[c]['incluye_transporte'] == 'no_confirmado'
        assert next(x['url'] for x in fuentes if x['codigo_recurso'] == c) in audit[c]['fuente_observada']
        assert c in informe
    for c in bloqueados:
        assert (not audit[c]['precio_revisado']
                or audit[c]['precio_revisado'] == cierre.precio_revisado(c, '')) and c in informe
    assert 'una sola vez' in audit['MT-DOM-SENSOR-MOV']['evidencia_y_pendientes']
    assert '10%' in audit['MT-TUB-RIEGO']['evidencia_y_pendientes']


def test_lote_30_rechaza_componentes_invalidos(monkeypatch, tmp_path):
    fuentes = leer(g.FUENTES_LOTE_30)
    path = tmp_path / 'fuentes.csv'
    monkeypatch.setattr(g, 'FUENTES_LOTE_30', path)
    def escribir(rows):
        with path.open('w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=fuentes[0], delimiter=';', lineterminator='\n')
            w.writeheader(); w.writerows(rows)
    for rows in (fuentes[:-1], fuentes + fuentes[:1]):
        escribir(rows)
        with pytest.raises(ValueError):
            g.referencias_lote_treinta()
    for campo, valor in [('unidad', 'h'), ('importe_base', '-1'), ('cantidad_por_envase', '0'),
                         ('cantidad_por_recurso', 'NaN'), ('url_precio', ''), ('precio_resultante', '999'),
                         ('precio_bruto', '999'), ('criterio_iva', 'sin dato')]:
        malas = [r.copy() for r in fuentes]; malas[0][campo] = valor; escribir(malas)
        with pytest.raises(ValueError):
            g.referencias_lote_treinta()
