import apoyo_cierre_espana as cierre
"""Observaciones parciales de Extremadura, sin aplicación automática."""
import csv
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def leer(nombre):
    with (ROOT / nombre).open(encoding='utf-8-sig', newline='') as archivo:
        return list(csv.DictReader(archivo, delimiter=';'))


def test_observaciones_extremadura_son_candidatos_no_precios_aplicados():
    observaciones = leer('docs/auditoria_precios/espana_maquinaria_extremadura_2026.csv')
    auditoria = {r['codigo_recurso']: r for r in leer('docs/auditoria_precios/espana_2026-11-06.csv')}
    matriz = {r['codigo_recurso']: r for r in leer('basedatos_partidas/salida/precios_recursos_espana.csv')}
    assert len(observaciones) == 23
    assert len({r['codigo_recurso'] for r in observaciones}) == 23
    for obs in observaciones:
        r = auditoria[obs['codigo_recurso']]
        assert r['estado_auditoria'] == 'en_revision'
        assert (not r['precio_revisado']
                or r['precio_revisado'] == cierre.precio_revisado(obs['codigo_recurso'], ''))
        assert (Decimal(matriz[obs['codigo_recurso']]['precio_referencia'])
                == cierre.precio(obs['codigo_recurso'], r['precio_matriz']))
        assert obs['unidad_fuente'] == 'h' and obs['fecha_fuente_bruta'] == '240426'
        assert obs['codigo_fuente'].startswith('M') and Decimal(obs['precio_fuente']) > 0
        assert 'juntaex.es/documents/' in obs['url_fuente']
        assert obs['fragmento_lectura_web'] and obs['limitaciones']
    por_codigo = {r['codigo_recurso']: r for r in observaciones}
    assert (por_codigo['MQ-TALADRO']['codigo_fuente'], por_codigo['MQ-TALADRO']['precio_fuente']) == ('M11T010', '0.84')
    assert (por_codigo['MQ-BOMBA-CONC']['codigo_fuente'], por_codigo['MQ-BOMBA-CONC']['precio_fuente']) == ('M01HA010', '212.50')
    # Las observaciones de Palencia no se sustituyen por las de Extremadura.
    assert auditoria['MQ-TALADRO']['codigo_fuente'] == 'U02SW650'
    assert auditoria['MQ-MEZCL']['codigo_fuente'] == 'U02L020'
