"""Contraste provincial: candidatos en revisión, sin aplicar como precios."""
import csv
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def leer(path):
    with path.open(encoding='utf-8-sig', newline='') as archivo:
        return {r['codigo_recurso']: r for r in csv.DictReader(archivo, delimiter=';')}


def test_contraste_maquinaria_palencia_no_aplica_precios():
    auditoria = leer(ROOT / 'docs/auditoria_precios/espana_2026-11-06.csv')
    matriz = leer(ROOT / 'basedatos_partidas/salida/precios_recursos_espana.csv')
    observaciones = {
        'MQ-TALADRO': ('U02SW650', '3.11'),
        'MQ-SIERRA': ('U02SW600', '4.78'),
        'MQ-VIBRADOR': ('U02SW550', '4.42'),
        'MQ-MART-ELEC': ('U02SW615', '4.53'),
        'MQ-MART-NEUM': ('U02SW610', '6.19'),
        'MQ-GRUA': ('U02J040', '51.02'),
        'MQ-VOLQ': ('U02J030', '51.02'),
        'MQ-PLANCHA-COMP': ('U02F205', '7.73'),
        'MQ-COMPACT-SALTO': ('U02F200', '5.42'),
        'MQ-BOMBA-CONC': ('U02L010', '125.16'),
        'MQ-BOMBA-ACHI': ('U02SM005', '10.83'),
    }
    for codigo, (fuente, precio) in observaciones.items():
        r = auditoria[codigo]
        assert r['estado_auditoria'] == 'en_revision'
        assert r['codigo_fuente'] == fuente
        assert Decimal(r['precio_fuente_normalizado']) == Decimal(precio)
        assert r['unidad_fuente_normalizada'] == 'h'
        assert 'diputaciondepalencia.es/' in r['fuente_observada']
        assert not r['precio_revisado']
        assert Decimal(matriz[codigo]['precio_referencia']) == Decimal(r['precio_matriz'])
