import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'docs/auditoria_precios'
DESCOMPUESTOS = ROOT / 'basedatos_partidas/datos/descompuestos'
INFORME = 'ESPANA_SEXTO_BARRIDO_PARCIAL_2026-11-07.md'


def leer(nombre):
    with (DOC / nombre).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter=';'))


def partidas():
    return {p.stem: json.loads(p.read_text(encoding='utf-8'))
            for p in DESCOMPUESTOS.glob('*.json')}


def refs(partida):
    return {x['ref'] for x in partida['recursos']}


def test_decisiones_trazables_sin_precios():
    decisions = leer('espana_decisiones_sexto_barrido_parcial_2026-11-07.csv')
    codes = {r['codigo_recurso'] for r in decisions}
    assert len(decisions) == len(codes) == 14
    for name in ('ESPANA_LOTE_30_2026-11-07.md', 'ESPANA_LOTE_OTROS_30_2026-11-07.md',
                 'ESPANA_TERCER_BARRIDO_PARCIAL_2026-11-07.md',
                 'ESPANA_CUARTO_BARRIDO_PARCIAL_2026-11-07.md',
                 'ESPANA_QUINTO_BARRIDO_PARCIAL_2026-11-07.md'):
        previos = set(re.findall(r'\b(?:MO|MQ|MT)-[A-Z0-9-]+\b',
                                 (DOC / name).read_text(encoding='utf-8')))
        assert not codes & previos
    audit = {r['codigo_recurso']: r for r in leer('espana_2026-11-06.csv')}
    adjudicacion = {r['codigo_recurso']: r for r in leer('espana_adjudicacion_2026-11-07.csv')}
    informe = (DOC / INFORME).read_text(encoding='utf-8')
    p = partidas()
    for r in decisions:
        a = audit[r['codigo_recurso']]
        assert r['decision'] == 'sin_precio_revisado'
        if a['precio_revisado']:
            # Cerrado después del barrido con una decisión posterior.
            assert adjudicacion[r['codigo_recurso']]['decision'] != r['decision']
            assert a['estado_auditoria'] == 'confirmado_referencia'
            continue
        assert not a['precio_revisado']
        assert a['estado_auditoria'] in ('pendiente', 'en_revision')
        assert r['unidad'] == a['unidad']
        assert int(r['usos']) == int(a['partidas_que_lo_usan']) == 3
        assert sum(r['codigo_recurso'] in refs(x) for x in p.values()) == 3
        assert r['fuente'].startswith('https://') and r['fuente'] in informe
        assert r['motivo'] in informe and r['motivo'] in a['evidencia_y_pendientes']


def test_alertas_reales_y_alcances_no_concluyentes():
    p = partidas()
    informe = (DOC / INFORME).read_text(encoding='utf-8')
    assert p['04.08.02.040']['unidad'] == 'm2'
    assert 'metro lineal' in p['04.08.02.040']['descripcion']
    assert 'MQ-PERF-PILOTE' in refs(p['04.08.02.040'])
    for code in ('14.09.01.060', '18.08.01.030'):
        assert 'MT-CINTA-LED' in refs(p[code])
        assert 'tira' in p[code]['producto_cliente']['tipo'].lower()
        assert code in informe
    for code in ('01.05.01.050', '11.07.01.060', '17.04.01.010'):
        assert {'MT-LINEA-VIDA', 'MT-PERNO-ANCLA'} <= refs(p[code])
        assert code in informe
    for code in ('14.01.01.020', '14.01.01.070', '14.02.01.050'):
        assert {'MT-ADOQUIN', 'MT-ARENA'} <= refs(p[code])
        assert code in informe
    assert {'MQ-LIJAD-PISO', 'MQ-ASPIR'} <= refs(p['12.05.05.040'])
    assert 'no duplicidad demostrada' in informe
    assert 'ESPANA_QUINTO_BARRIDO_PARCIAL_2026-11-07.md' in informe
