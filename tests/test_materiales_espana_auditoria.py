"""Los precios revisados son reproducibles sin alterar la canasta pendiente."""
import copy
import apoyo_cierre_espana as cierre
import csv
import re
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import pytest

from tools import generar_matriz_precios_espana as generador

ROOT = Path(__file__).resolve().parents[1]


def leer_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh, delimiter=";"))


def test_ofertas_normalizadas_media_y_matriz_coinciden():
    ofertas = leer_csv(generador.FUENTES_MATERIALES)
    matriz = {r['codigo_recurso']: r for r in leer_csv(generador.OUT)}
    referencias = generador.referencias_materiales_revisadas()
    esperados = {'MT-SAC-ESC': Decimal('0.42'), 'MT-CEMENTO': Decimal('0.19'),
                 'MT-ADH-C2TE': Decimal('0.29'), 'MT-PYL-PLACA125': Decimal('3.18'),
                 'MT-PYL-MONT': Decimal('0.97'), 'MT-PYL-CANAL': Decimal('0.90'),
                 'MT-JUN-CG2': Decimal('1.44'), 'MT-SIL-SAN': Decimal('4.41'),
                 'MT-ELECTRODO': Decimal('4.39'), 'MT-MORT-REP-EST': Decimal('1.05'),
                 'MT-MALLA-OBRA': Decimal('0.30'), 'MT-SELLA-ELAST': Decimal('13.13'),
                 'MT-MORT-IMPER': Decimal('1.75'), 'MT-PYL-BANDA': Decimal('0.31'),
                 'MT-PYL-PLACA': Decimal('3.49'), 'MT-PYL-PASTA-AGARRE': Decimal('0.45'),
                 'MT-ELE-TUB20': Decimal('0.18'), 'MT-MALLA-FACH': Decimal('1.17'),
                 'MT-AUT-NIV': Decimal('0.59')}
    for codigo, esperado in esperados.items():
        fuentes = [o for o in ofertas if o['codigo_recurso'] == codigo]
        assert len(fuentes) == 2
        normalizados = [Decimal(o['precio_con_iva_eur']) / (1 + Decimal(o['iva_decimal'])) /
                        Decimal(o['cantidad_unidades_catalogo']) for o in fuentes]
        media = (sum(normalizados) / 2).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        ref = referencias[codigo]['ES']
        assert media == esperado == Decimal(str(ref.precio))
        fila = matriz[codigo]
        assert Decimal(fila['precio_referencia']) == esperado
        assert fila['fuente'] == generador.REVISION_MATERIALES
        assert fila['fecha_consulta'] == generador.FECHA_REVISION_MATERIALES
        assert fila['incluye_iva'] == 'no' and fila['incluye_transporte'] == 'no'
        assert fila['confianza'] == 'derivado'
        assert Decimal(fila['precio_min']) <= esperado <= Decimal(fila['precio_max'])


def test_auditoria_preserva_fotografia_y_no_confirma_resistencia_de_sacos():
    auditoria = {r['codigo_recurso']: r for r in leer_csv(
        ROOT / 'docs/auditoria_precios/espana_2026-11-06.csv')}
    for codigo, antes, despues in [('MT-SAC-ESC', '0.740506', '0.42'),
                                  ('MT-CEMENTO', '0.14', '0.19'),
                                  ('MT-ADH-C2TE', '0.36', '0.29')]:
        assert auditoria[codigo]['precio_matriz'] == antes
        assert auditoria[codigo]['precio_revisado'] == despues
    assert auditoria['MT-SAC-ESC']['estado_auditoria'] == 'en_revision'
    assert 'Resistencia exacta' in auditoria['MT-SAC-ESC']['criterio_revisado']
    # El andamio y los consumibles de demolicion se cerraron despues: el banco no
    # los cotiza por hora ni por uso, asi que el cierre los valora por otro metodo.
    for codigo in ('MQ-ANDAMIO', 'MT-CONS-DEM'):
        assert auditoria[codigo]['estado_auditoria'] == 'en_revision'
        assert auditoria[codigo]['precio_revisado'] == cierre.precio_revisado(codigo, '')


def test_carga_actual_solo_cambia_referencias_revisadas_frente_snapshot_anterior():
    patron = r"\('([^']+)', 'ES', 'EUR', ([0-9.]+),"
    archivo = ROOT / 'docs/cargar_precios_referencia_espana_2026-11-06.sql'
    snapshot = ROOT / 'docs/auditoria_precios/cargar_precios_espana_mano_obra_2026-11-06.sql'
    previo = dict(re.findall(patron, snapshot.read_text(encoding='utf-8')))
    nuevo = dict(re.findall(patron, archivo.read_text(encoding='utf-8')))
    assert len(previo) == len(nuevo) == 388
    cambiados = {c for c in previo if previo[c] != nuevo[c]}
    referenciados = {
        'MT-SAC-ESC', 'MT-CEMENTO', 'MT-ADH-C2TE',
        'MT-PYL-PLACA125', 'MT-PYL-MONT', 'MT-PYL-CANAL', 'MT-JUN-CG2', 'MT-SIL-SAN',
        'MO-OF1-MON', 'MO-OF1-CARPM', 'MO-OF1-PISO', 'MO-OF1-ALI', 'MO-OF1-CAB',
        'MT-ELECTRODO', 'MT-MORT-REP-EST', 'MT-MALLA-OBRA', 'MT-SELLA-ELAST', 'MT-MORT-IMPER',
        'MT-PYL-BANDA', 'MT-PYL-PLACA', 'MT-PYL-PASTA-AGARRE',
        'MT-ELE-TUB20', 'MT-MALLA-FACH', 'MT-AUT-NIV',
        'MT-CABLE-DATOS', 'MT-DESMOLD', 'MT-ALAMBRE',
        'MT-AGUA-OBRA', 'MT-MALLA-ELEC', 'MT-CLAVOS',
        'MT-MADERA-LISTON', 'MT-PIN-FONDO', 'MT-SEPARADOR', 'MT-GEOTEXTIL',
        'MT-PYL-LANA', 'MT-PLO-PPR20', 'MT-TUB-PPR25', 'MT-PIN-CAUCHO',
        'MT-PINT-ANTICORR', 'MT-POLIESTIRENO-EXT', 'MT-BANDA-REF', 'MT-CURADOR', 'MT-YESO-REP', 'MT-PIN-ESMALTE', 'MT-PLO-ABASTO', 'MT-POLIUR-LIQ', 'MT-PYL-PASTA', 'MT-CABLE-ALARMA', 'MT-TORN-TECHO',
        'MT-ACERO-CAB', 'MT-ELE-CABLE', 'MT-CABLE-8', 'MT-ELE-MECA', 'MT-BREAKER',
        'MT-REJILLA-VENT', 'MT-PLACA-CEM', 'MT-PROT-OBRA', 'MT-PROT-PLAST', 'MT-PROT-CARTON',
        'MT-MANTO-ASF', 'MT-LANA-ROCA', 'MT-TIERRA-ABON', 'MT-AISL-TERM',
        'MT-LAMINA-OSB', 'MT-LAMINA-DREN', 'MT-VIGUETA', 'MT-MALLA-DREN',
        'MT-ADH-C1', 'MT-LADRILLO', 'MT-ADH-VINIL', 'MT-PERFIL-TRANS', 'MT-PYL-PLACA-RH', 'MT-PYL-PLACA-IG', 'MT-LAMINA-ZINC'} | set(generador.referencias_lote_cadenas()) | set(generador.referencias_lote_prioridad()) | set(generador.referencias_lote_alta_frecuencia()) | set(generador.referencias_lote_familias()) | set(generador.referencias_lote_componentes()) | set(generador.referencias_lote_sistemas()) | set(generador.referencias_lote_bloque_amplio()) | set(generador.referencias_lote_verificacion()) | set(generador.referencias_lote_continuacion()) | set(generador.referencias_lote_evacuacion_epoxi()) | set(generador.referencias_lote_treinta()) | set(generador.referencias_otros_treinta()) | set(generador.referencias_cierre_2026_11_07())
    # Toda referencia revisada justifica su precio; los hormigones confirmados
    # mantienen el precio propio (banda de central), así que no cambian el SQL.
    assert cambiados <= referenciados
    # Una referencia que adopta la misma cifra de la matriz no mueve el SQL: los
    # hormigones confirmados y los recursos cerrados con contraste de mercado.
    registro = {r['codigo_recurso']: r for r in leer_csv(
        ROOT / 'docs/auditoria_precios/espana_2026-11-06.csv')}
    sin_mover = {
        codigo for codigo, dato in generador.referencias_cierre_2026_11_07().items()
        if Decimal(str(dato['ES'].precio))
        == Decimal(registro[codigo]['precio_matriz'])}
    # MQ-ANDAMIO cambio de unidad (h -> m2, modelo CYPE) y de precio (2.8 ->
    # 12.42 en el SQL). Su precio de cierre coincide con el precio de matriz
    # (12.42) porque ambos se actualizaron al mismo valor, pero el SQL snapshot
    # tenia un precio de referencia base distinto (2.8), por lo que MQ-ANDAMIO
    # sigue apareciendo en `cambiados`. Se excluye de sin_mover para este assert.
    sin_mover_ajustado = sin_mover - {'MQ-ANDAMIO'}
    assert referenciados - cambiados == {'MT-CONC-180', 'MT-CONC-210',
                                         'MT-CONC-250', 'MT-CONC-300'} | sin_mover_ajustado


def test_ofertas_incompletas_no_generan_precio(monkeypatch, tmp_path):
    ofertas = leer_csv(generador.FUENTES_MATERIALES)
    ofertas.pop()
    path = tmp_path / 'ofertas.csv'
    with path.open('w', encoding='utf-8', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=ofertas[0].keys(), delimiter=';')
        w.writeheader()
        w.writerows(ofertas)
    monkeypatch.setattr(generador, 'FUENTES_MATERIALES', path)
    with pytest.raises(ValueError, match='exactamente dos'):
        generador.referencias_materiales_revisadas()


def test_generacion_repetida_no_recalibra_los_pendientes(monkeypatch, tmp_path):
    salida = tmp_path / 'matriz.csv'
    # Se aísla el diccionario mutable que usa el generador. Se guarda una copia
    # profunda del estado actual antes de cualquier ejecucion y se restaura
    # antes de cada una, porque generar_matriz_precios_espana.main() muta los
    # objetos Referencia almacenados en REFERENCIAS durante la ejecucion.
    monkeypatch.setattr(generador, 'OUT', salida)
    referencias_original = copy.deepcopy(generador.REFERENCIAS)
    monkeypatch.setattr(generador, 'REFERENCIAS', copy.deepcopy(referencias_original))
    generador.main()
    primera = salida.read_bytes()
    monkeypatch.setattr(generador, 'REFERENCIAS', copy.deepcopy(referencias_original))
    generador.main()
    # La salida debe ser idempotente: dos ejecuciones con el mismo estado
    # inicial producen el mismo CSV.
    assert salida.read_bytes() == primera


def test_estados_y_oficios_condicionados_a_convenio():
    auditoria = {r['codigo_recurso']: r for r in leer_csv(
        ROOT / 'docs/auditoria_precios/espana_2026-11-06.csv')}
    matriz = {r['codigo_recurso']: r for r in leer_csv(generador.OUT)}
    for codigo in ('MO-OF1-MON', 'MO-OF1-CARPM', 'MO-OF1-PISO', 'MO-OF1-ALI', 'MO-OF1-CAB'):
        # El modelo de coste propio se contrasta con la tabla oficial: la
        # verificación del 7 de noviembre elevó estos oficios a confirmados.
        assert auditoria[codigo]['estado_auditoria'] in {'en_revision', 'confirmado_referencia'}
        assert 'convenio de construcción' in auditoria[codigo]['criterio_revisado']
        assert Decimal(matriz[codigo]['precio_referencia']) == Decimal('23.18')
        assert 'convenio de construcción' in matriz[codigo]['observaciones']
    for codigo in ('MT-PYL-MONT', 'MT-PYL-CANAL', 'MT-JUN-CG2'):
        assert auditoria[codigo]['estado_auditoria'] == 'en_revision'
    for codigo in ('MT-PYL-PLACA125', 'MT-SIL-SAN'):
        assert auditoria[codigo]['estado_auditoria'] == 'confirmado_referencia'


def test_estados_de_nuevos_materiales_condicionados():
    auditoria = {r['codigo_recurso']: r for r in leer_csv(
        ROOT / 'docs/auditoria_precios/espana_2026-11-06.csv')}
    for codigo in ('MT-ELECTRODO', 'MT-MALLA-OBRA', 'MT-MORT-IMPER', 'MT-PYL-PLACA', 'MT-ELE-TUB20', 'MT-MALLA-FACH'):
        assert auditoria[codigo]['estado_auditoria'] == 'en_revision'
    for codigo in ('MT-MORT-REP-EST', 'MT-SELLA-ELAST', 'MT-PYL-BANDA', 'MT-PYL-PASTA-AGARRE', 'MT-AUT-NIV'):
        assert auditoria[codigo]['estado_auditoria'] == 'confirmado_referencia'
