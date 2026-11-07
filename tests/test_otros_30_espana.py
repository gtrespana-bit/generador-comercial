import apoyo_cierre_espana as cierre
import csv
from decimal import Decimal

import pytest
from tools import generar_matriz_precios_espana as g


def leer(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter=';'))


def test_otros_30_trazabilidad_y_bloqueos():
    d = g.ROOT / 'docs/auditoria_precios'
    decisiones = leer(d / 'espana_decisiones_otros_30_2026-11-07.csv')
    previo = (d / 'ESPANA_LOTE_30_2026-11-07.md').read_text(encoding='utf-8')
    informe = (g.ROOT / g.REVISION_OTROS_30).read_text(encoding='utf-8')
    audit = {x['codigo_recurso']: x for x in leer(d / 'espana_2026-11-06.csv')}
    matriz = {x['codigo_recurso']: x for x in leer(g.OUT)}
    codigos = {x['codigo_recurso'] for x in decisiones}
    assert len(decisiones) == len(codigos) == 30
    assert all(c not in previo and c in informe for c in codigos)
    assert sum(x['decision'] == 'estimacion_provisional' for x in decisiones) == 1
    assert sum(x['decision'] == 'sin_precio_revisado' for x in decisiones) == 29
    for x in decisiones:
        a = audit[x['codigo_recurso']]
        assert a['estado_auditoria'] == cierre.estado(x['codigo_recurso'], x['estado_auditoria'])
        assert x['fuente'] and x['motivo']
        if x['decision'] == 'sin_precio_revisado':
            assert (not a['precio_revisado']
                    or a['precio_revisado'] == cierre.precio_revisado(x['codigo_recurso'], ''))
            assert x['motivo'] in a['evidencia_y_pendientes']
    a, m = audit['MT-APEO'], matriz['MT-APEO']
    assert a['estado_auditoria'] == 'en_revision'
    assert Decimal(a['precio_revisado']) == Decimal(m['precio_referencia']) == Decimal('1.04')
    assert Decimal(str(g.referencias_otros_treinta()['MT-APEO']['ES'].precio)) == Decimal('1.04')
    assert m['fuente'] == g.REVISION_OTROS_30 and m['incluye_iva'] == 'por_verificar'
    assert m['incluye_transporte'] == 'no_confirmado'
    assert '150' in a['evidencia_y_pendientes'] and '10' in a['evidencia_y_pendientes']
    assert 'no kg' not in audit['MT-TORN']['evidencia_y_pendientes']  # texto anterior corregido
    assert 'compactación requerido' not in audit['MQ-RODILLO']['evidencia_y_pendientes']


def test_otros_30_fuentes_validadas(monkeypatch, tmp_path):
    fuentes = leer(g.FUENTES_OTROS_30)
    assert [(x['importe_base'], x['cantidad_por_envase']) for x in fuentes] == [('1.76', '2'), ('0.06', '2'), ('0.25', '2')]
    path = tmp_path / 'fuentes.csv'
    monkeypatch.setattr(g, 'FUENTES_OTROS_30', path)
    def escribir(rows):
        with path.open('w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=fuentes[0], delimiter=';', lineterminator='\n')
            w.writeheader(); w.writerows(rows)
    for rows in (fuentes[:-1], fuentes + fuentes[:1]):
        escribir(rows)
        with pytest.raises(ValueError):
            g.referencias_otros_treinta()
    for campo, valor in [('unidad', 'm'), ('importe_base', '-1'), ('cantidad_por_envase', '0'),
                         ('cantidad_por_recurso', 'NaN'), ('url_precio', ''), ('precio_resultante', '999'),
                         ('precio_bruto', '999'), ('criterio_iva', 'sin dato')]:
        malas = [r.copy() for r in fuentes]; malas[0][campo] = valor; escribir(malas)
        with pytest.raises(ValueError):
            g.referencias_otros_treinta()
