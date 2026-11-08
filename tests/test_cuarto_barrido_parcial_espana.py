import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'docs/auditoria_precios'
DESCOMPUESTOS = ROOT / 'basedatos_partidas/datos/descompuestos'
MATRIZ = ROOT / 'basedatos_partidas/salida/precios_recursos_espana.csv'


def leer(nombre):
    with (DOC / nombre).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter=';'))


def partidas():
    for path in DESCOMPUESTOS.glob('*.json'):
        data = json.loads(path.read_text(encoding='utf-8'))
        yield path.stem, {r['ref'] for r in data.get('recursos', [])}


def test_decisiones_distintas_trazables_y_sin_precio():
    decisiones = leer('espana_decisiones_cuarto_barrido_parcial_2026-11-07.csv')
    codigos = {r['codigo_recurso'] for r in decisiones}
    assert len(decisiones) == len(codigos) == 30
    informes_anteriores = [
        'ESPANA_LOTE_30_2026-11-07.md',
        'ESPANA_LOTE_OTROS_30_2026-11-07.md',
        'ESPANA_TERCER_BARRIDO_PARCIAL_2026-11-07.md',
    ]
    for nombre in informes_anteriores:
        previos = set(re.findall(r'\b(?:MO|MQ|MT)-[A-Z0-9-]+\b',
                                 (DOC / nombre).read_text(encoding='utf-8')))
        assert not codigos & previos
    audit = {r['codigo_recurso']: r for r in leer('espana_2026-11-06.csv')}
    informe = (DOC / 'ESPANA_CUARTO_BARRIDO_PARCIAL_2026-11-07.md').read_text(encoding='utf-8')
    with MATRIZ.open(encoding='utf-8-sig', newline='') as f:
        matriz = {r['codigo_recurso']: r for r in csv.DictReader(f, delimiter=';') if r['pais_codigo'] == 'ES'}
    usos = {code: 0 for code in codigos}
    for _, refs in partidas():
        for code in refs & codigos:
            usos[code] += 1
    for r in decisiones:
        code = r['codigo_recurso']
        a = audit[code]
        # Tras la revision cruzada masiva, estos recursos se confirmaron con
        # BCCA 2023 o Extremadura 2026 dentro del +/-15 %.
        assert a['estado_auditoria'] == 'confirmado_referencia'
        assert a['precio_revisado'] and float(a['precio_revisado']) > 0
        assert r['fuente'].startswith('https://') and r['fuente'] in informe
        assert r['motivo'] in informe and r['motivo'] in a['evidencia_y_pendientes']
        assert r['unidad'] == a['unidad']
        assert int(r['usos']) == int(a['partidas_que_lo_usan']) == usos[code]


def test_alertas_epi_fachada_y_apeo_no_desaparecen():
    informe = (DOC / 'ESPANA_CUARTO_BARRIDO_PARCIAL_2026-11-07.md').read_text(encoding='utf-8')
    indices = dict(partidas())
    assert 'MT-EPP' in indices['17.02.01.040']
    assert 'MT-EPP' in indices['17.02.01.050']
    assert '17.02.01.040' in informe and '17.02.01.050' in informe
    fachada = {code for code, refs in indices.items()
               if {'MT-PLACA-FACHADA', 'MT-SUBESTRUCTURA'} <= refs}
    assert fachada == {'06.07.01.010', '06.07.01.040', '18.02.01.050'}
    assert all(code in informe for code in fachada)
    assert {code for code in fachada if 'MT-TORN-TECHO' in indices[code]} == {
        '06.07.01.010', '06.07.01.040'}
    apeos = [code for code, refs in indices.items() if {'MT-APEO', 'MT-VIGA-APEO'} <= refs]
    assert len(apeos) == 23
    assert 'posible doble cómputo' in informe


def test_alertas_camilla_piscina_pasivante_y_guias():
    informe = (DOC / 'ESPANA_CUARTO_BARRIDO_PARCIAL_2026-11-07.md').read_text(encoding='utf-8')
    indices = dict(partidas())
    assert indices['17.07.01.080'] == {'MT-BOTIQUIN', 'MO-AYU'}
    assert 'MT-QUIMICO-LIMP-AC' in indices['14.10.01.110']
    assert 'MT-PASIVANTE' in indices['06.09.01.230']
    guiadas = {code for code, refs in indices.items()
               if {'MT-HERRAJE-CORRED', 'MT-RIEL-CORRED'} <= refs}
    assert guiadas == {'07.01.01.130', '07.01.01.140', '07.01.01.200',
                       '07.01.01.230', '07.09.01.070'}
    assert all(code in informe for code in guiadas | {
        '17.07.01.080', '14.10.01.110', '06.09.01.230'})
    assert 'no duplicidad demostrada' in informe
    assert 'no utilizarlo como sustituto' in informe
