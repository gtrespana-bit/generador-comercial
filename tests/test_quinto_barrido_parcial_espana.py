import apoyo_cierre_espana as cierre
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'docs/auditoria_precios'
DESCOMPUESTOS = ROOT / 'basedatos_partidas/datos/descompuestos'
INFORME = 'ESPANA_QUINTO_BARRIDO_PARCIAL_2026-11-07.md'


def leer(nombre):
    with (DOC / nombre).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter=';'))


def partidas():
    return {p.stem: json.loads(p.read_text(encoding='utf-8'))
            for p in DESCOMPUESTOS.glob('*.json')}


def referencias(partida):
    return {x['ref'] for x in partida['recursos']}


def test_decisiones_sin_precio_independientes_y_trazables():
    decisiones = leer('espana_decisiones_quinto_barrido_parcial_2026-11-07.csv')
    codigos = {r['codigo_recurso'] for r in decisiones}
    assert len(decisiones) == len(codigos) == 16
    for anterior in ('ESPANA_LOTE_30_2026-11-07.md', 'ESPANA_LOTE_OTROS_30_2026-11-07.md',
                     'ESPANA_TERCER_BARRIDO_PARCIAL_2026-11-07.md',
                     'ESPANA_CUARTO_BARRIDO_PARCIAL_2026-11-07.md'):
        previos = set(re.findall(r'\b(?:MO|MQ|MT)-[A-Z0-9-]+\b',
                                 (DOC / anterior).read_text(encoding='utf-8')))
        assert not codigos & previos
    audit = {r['codigo_recurso']: r for r in leer('espana_2026-11-06.csv')}
    informe = (DOC / INFORME).read_text(encoding='utf-8')
    partes = partidas()
    for r in decisiones:
        code = r['codigo_recurso']
        a = audit[code]
        assert r['decision'] == 'sin_precio_revisado'
        assert not a['precio_revisado'] and a['estado_auditoria'] == cierre.estado(r['codigo_recurso'], 'pendiente')
        assert r['fuente'].startswith('https://') and r['fuente'] in informe
        assert r['motivo'] in informe and r['motivo'] in a['evidencia_y_pendientes']
        assert r['unidad'] == a['unidad']
        assert int(r['usos']) == int(a['partidas_que_lo_usan'])
        assert int(r['usos']) == sum(code in referencias(p) for p in partes.values())


def test_alertas_de_seguridad_y_posibles_solapes():
    p = partidas()
    informe = (DOC / INFORME).read_text(encoding='utf-8')
    assert 'MT-LAMP-OBRA' in referencias(p['17.03.01.080'])
    red = p['17.01.01.070']
    assert red['unidad'] == 'm' and 'soportes' in red['descripcion']
    assert referencias(red) == {'MT-RED-SEG', 'MQ-TALADRO', 'MO-OF1-ALB', 'MO-AYU'}
    pares = {
        ('MT-PERSIANA-ALU', 'MT-CAJON-PERS'): {
            '07.08.01.010', '07.08.01.020', '18.05.01.080', '18.06.01.020'},
        ('MT-MICROCEM', 'MT-MALLA-JUNTA'): {
            '12.04.01.050', '12.04.01.260', '12.05.07.030', '12.13.01.080'},
        ('MT-CIELO-PVC', 'MT-PERFIL-REMATE'): {
            '12.09.02.010', '12.09.02.020', '12.09.02.030', '12.09.02.040'},
    }
    for par, esperado in pares.items():
        assert {code for code, partida in p.items() if set(par) <= referencias(partida)} == esperado
    assert 'portón' in p['07.08.01.020']['producto_cliente']['tipo']
    assert 'sellador' in p['12.05.07.030']['descripcion']
    assert all(x in informe for x in ['17.03.01.080', '17.01.01.070', '07.08.01.020', '12.05.07.030'])
    assert 'no duplicidad demostrada' in informe
    assert 'ESPANA_CUARTO_BARRIDO_PARCIAL_2026-11-07.md' in informe
