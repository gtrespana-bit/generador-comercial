import apoyo_cierre_espana as cierre
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'docs/auditoria_precios'
PARTIDAS = ROOT / 'basedatos_partidas/datos/descompuestos'
INFORME = 'ESPANA_SEPTIMO_BARRIDO_PARCIAL_2026-11-07.md'


def leer_csv(nombre):
    with (DOC / nombre).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter=';'))


def leer_partida(codigo):
    return json.loads((PARTIDAS / (codigo + '.json')).read_text(encoding='utf-8'))


def refs(partida):
    return {r['ref']: r['rendimiento'] for r in partida['recursos']}


def test_quince_decisiones_independientes_y_trazables():
    decisiones = leer_csv('espana_decisiones_septimo_barrido_parcial_2026-11-07.csv')
    codigos = {r['codigo_recurso'] for r in decisiones}
    assert len(decisiones) == len(codigos) == 15
    previos = ('ESPANA_LOTE_30_2026-11-07.md', 'ESPANA_LOTE_OTROS_30_2026-11-07.md',
               'ESPANA_TERCER_BARRIDO_PARCIAL_2026-11-07.md',
               'ESPANA_CUARTO_BARRIDO_PARCIAL_2026-11-07.md',
               'ESPANA_QUINTO_BARRIDO_PARCIAL_2026-11-07.md',
               'ESPANA_SEXTO_BARRIDO_PARCIAL_2026-11-07.md')
    for nombre in previos:
        anteriores = set(re.findall(r'\b(?:MO|MQ|MT)-[A-Z0-9-]+\b',
                                    (DOC / nombre).read_text(encoding='utf-8')))
        assert not codigos & anteriores
    audit = {r['codigo_recurso']: r for r in leer_csv('espana_2026-11-06.csv')}
    p = [json.loads(f.read_text(encoding='utf-8')) for f in PARTIDAS.glob('*.json')]
    informe = (DOC / INFORME).read_text(encoding='utf-8')
    for r in decisiones:
        a = audit[r['codigo_recurso']]
        assert r['decision'] == 'sin_precio_revisado'
        # El barrido no cerró precio; si hoy lo hay, es el del cierre total del 7 de noviembre.
        assert a['precio_revisado'] == cierre.precio_revisado(r['codigo_recurso'], '')
        assert a['estado_auditoria'] == cierre.estado(r['codigo_recurso'], 'pendiente')
        assert r['unidad'] == a['unidad'] and int(r['usos']) == 2
        assert int(a['partidas_que_lo_usan']) == 2
        assert sum(r['codigo_recurso'] in refs(x) for x in p) == 2
        assert r['fuente'].startswith('https://') and r['fuente'] in informe
        assert r['motivo'] in informe and r['motivo'] in a['evidencia_y_pendientes']


def test_alertas_reflejan_catalogo_sin_inferir_incumplimiento():
    informe = (DOC / INFORME).read_text(encoding='utf-8')
    p = leer_partida('13.06.01.100')
    assert 'MT-TIMBRE' in refs(p) and 'asistencia' in p['titulo'].lower()
    for codigo in ('12.13.01.030', '12.13.01.160'):
        assert {'MT-POLIURETANO-PISO', 'MT-PUENTE-ADH'} <= refs(leer_partida(codigo)).keys()
    for codigo in ('11.03.01.020', '11.03.01.060'):
        assert {'MT-TEJA-ASF', 'MT-CLAVOS'} <= refs(leer_partida(codigo)).keys()
    assert {'MT-BLQ-VIDRIO', 'MT-ACERO-CAB'} <= refs(leer_partida('06.05.01.010')).keys()
    assert refs(leer_partida('06.05.01.010'))['MT-BLQ-VIDRIO'] == 26
    assert refs(leer_partida('06.05.01.080'))['MT-BLQ-VIDRIO'] == 24
    assert {'MT-MAT-PRESTAMO', 'MQ-VOLQ'} <= refs(leer_partida('03.06.01.040')).keys()
    assert {'MT-TABLERO-PROV', 'MT-BREAKER'} <= refs(leer_partida('01.08.01.060')).keys()
    for codigo in ('18.06.01.060', '12.14.01.090'):
        assert not leer_partida(codigo).get('producto_cliente')
        assert codigo in informe
    assert refs(leer_partida('01.04.01.040'))['MT-ZIPPER'] == 1
    assert refs(leer_partida('01.03.01.030'))['MT-ZIPPER'] == 0.35
    assert refs(leer_partida('09.07.01.010'))['MT-GAS-REFRIG'] == 0.35
    assert 'no duplicidad probada' in informe
    assert 'No se ha determinado un incumplimiento' in informe
    assert 'ESPANA_SEXTO_BARRIDO_PARCIAL_2026-11-07.md' in informe
