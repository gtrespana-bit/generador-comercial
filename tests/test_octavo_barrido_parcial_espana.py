import apoyo_cierre_espana as cierre
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'docs/auditoria_precios'
PARTIDAS = ROOT / 'basedatos_partidas/datos/descompuestos'
INFORME = 'ESPANA_OCTAVO_BARRIDO_PARCIAL_2026-11-07.md'


def csv_leer(nombre):
    with (DOC / nombre).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter=';'))


def partida(codigo):
    return json.loads((PARTIDAS / (codigo + '.json')).read_text(encoding='utf-8'))


def refs(p):
    return {r['ref']: r['rendimiento'] for r in p['recursos']}


def test_decisiones_y_trazabilidad():
    decisiones = csv_leer('espana_decisiones_octavo_barrido_parcial_2026-11-07.csv')
    codes = {r['codigo_recurso'] for r in decisiones}
    assert len(decisiones) == len(codes) == 8
    anteriores = ('ESPANA_LOTE_30_2026-11-07.md', 'ESPANA_LOTE_OTROS_30_2026-11-07.md',
                  'ESPANA_TERCER_BARRIDO_PARCIAL_2026-11-07.md',
                  'ESPANA_CUARTO_BARRIDO_PARCIAL_2026-11-07.md',
                  'ESPANA_QUINTO_BARRIDO_PARCIAL_2026-11-07.md',
                  'ESPANA_SEXTO_BARRIDO_PARCIAL_2026-11-07.md',
                  'ESPANA_SEPTIMO_BARRIDO_PARCIAL_2026-11-07.md')
    for nombre in anteriores:
        assert not codes & set(re.findall(r'\b(?:MO|MQ|MT)-[A-Z0-9-]+\b',
                                          (DOC / nombre).read_text(encoding='utf-8')))
    auditoria = {r['codigo_recurso']: r for r in csv_leer('espana_2026-11-06.csv')}
    ps = [json.loads(p.read_text(encoding='utf-8')) for p in PARTIDAS.glob('*.json')]
    informe = (DOC / INFORME).read_text(encoding='utf-8')
    for r in decisiones:
        a = auditoria[r['codigo_recurso']]
        assert r['decision'] == 'sin_precio_revisado'
        assert not a['precio_revisado'] and a['estado_auditoria'] == cierre.estado(r['codigo_recurso'], 'pendiente')
        assert r['unidad'] == a['unidad'] and int(r['usos']) == int(a['partidas_que_lo_usan']) == 1
        assert sum(r['codigo_recurso'] in refs(p) for p in ps) == 1
        assert r['fuente'].startswith('https://') and r['fuente'] in informe
        assert r['motivo'] in informe and r['motivo'] in a['evidencia_y_pendientes']


def test_alertas_y_alcances():
    p = partida('10.02.02.060')
    assert p['unidad'] == 'm2' and 'por unidad instalada' in p['descripcion']
    assert refs(p)['MT-SOPORTE-ANTIVIB'] == refs(p)['MT-PERNO-ANCLA'] == 4
    p = partida('09.10.01.030')
    assert {'MT-GABINETE-MANG', 'MT-SENAL-OBRA', 'MT-TUB-PPR25'} <= refs(p).keys()
    p = partida('06.07.01.030')
    assert {'MT-PIEDRA-FACHADA', 'MT-SUBESTRUCTURA', 'MT-PERNO-ANCLA'} <= refs(p).keys()
    p = partida('09.02.01.020')
    assert {'MT-TRAMPA-GRASA', 'MT-PLO-PVC4', 'MT-PLO-ACC4'} <= refs(p).keys()
    p = partida('12.04.01.190')
    assert 'fijación mecánica' in p['descripcion'] and 'MT-VIDRIO-DECOR' in refs(p)
    audit = {r['codigo_recurso']: r for r in csv_leer('espana_2026-11-06.csv')}
    assert 'tornillería' in audit['MT-SOPORTE-ANTIVIB']['descripcion']
    assert 'con anclajes' in audit['MT-SUBESTRUCTURA']['descripcion']
    assert '4 pulgadas' in audit['MT-PLO-PVC4']['descripcion']
    informe = (DOC / INFORME).read_text(encoding='utf-8')
    assert 'sin demostración de duplicidad' in informe
    assert 'No se ha probado incumplimiento' in informe
    assert 'ESPANA_SEPTIMO_BARRIDO_PARCIAL_2026-11-07.md' in informe
