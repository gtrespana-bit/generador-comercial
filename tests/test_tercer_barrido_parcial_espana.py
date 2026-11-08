import apoyo_cierre_espana as cierre
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'docs/auditoria_precios'


def leer(nombre):
    with (DOC / nombre).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter=';'))


def test_tercer_barrido_completo_sin_aplicaciones_y_sin_repeticiones():
    decisiones = leer('espana_decisiones_tercer_barrido_parcial_2026-11-07.csv')
    anterior = leer('espana_decisiones_otros_30_2026-11-07.csv')
    informe_primero = (DOC / 'ESPANA_LOTE_30_2026-11-07.md').read_text(encoding='utf-8')
    informe = (DOC / 'ESPANA_TERCER_BARRIDO_PARCIAL_2026-11-07.md').read_text(encoding='utf-8')
    auditoria = {r['codigo_recurso']: r for r in leer('espana_2026-11-06.csv')}
    codigos = {r['codigo_recurso'] for r in decisiones}
    assert len(decisiones) == len(codigos) == 30
    assert '30 recursos examinados, 0 precios aplicados' in informe
    assert not codigos.intersection(r['codigo_recurso'] for r in anterior)
    usos_reales = {codigo: 0 for codigo in codigos}
    for path in (ROOT / 'basedatos_partidas/datos/descompuestos').glob('*.json'):
        data = json.loads(path.read_text(encoding='utf-8'))
        for codigo in {r['ref'] for r in data.get('recursos', [])} & codigos:
            usos_reales[codigo] += 1
    for r in decisiones:
        codigo = r['codigo_recurso']
        assert int(r['usos']) == usos_reales[codigo]
        a = auditoria[codigo]
        assert codigo not in informe_primero and codigo in informe
        assert r['decision'] == 'sin_precio_revisado'
        # Si el recurso se confirmó después con BCCA 2023 o Extremadura 2026,
        # tiene precio_revisado y estado confirmado_referencia.
        if a['precio_revisado']:
            assert float(a['precio_revisado']) > 0
            assert a['estado_auditoria'] in ('en_revision', 'confirmado_referencia')
        else:
            assert a['precio_revisado'] == cierre.precio_revisado(r['codigo_recurso'], '')
        assert r['motivo'] in a['evidencia_y_pendientes']
        assert r['fuente'].startswith('https://')
        assert r['usos'] == a['partidas_que_lo_usan'] and r['unidad'] == a['unidad']


def test_alerta_madera_con_partidas_en_informe():
    informe = (DOC / 'ESPANA_TERCER_BARRIDO_PARCIAL_2026-11-07.md').read_text(encoding='utf-8')
    partidas = []
    for path in (ROOT / 'basedatos_partidas/datos/descompuestos').glob('*.json'):
        data = json.loads(path.read_text(encoding='utf-8'))
        refs = {r['ref'] for r in data.get('recursos', [])}
        if {'MT-APEO', 'MT-VIGA-APEO'} <= refs:
            partidas.append(path.stem)
    assert len(partidas) == 23
    assert all(c in informe for c in partidas)
    audit = {r['codigo_recurso']: r for r in leer('espana_2026-11-06.csv')}
    assert 'puede duplicar madera' in audit['MT-APEO']['evidencia_y_pendientes']
    assert audit['MT-APEO']['precio_revisado'] == '1.04'
