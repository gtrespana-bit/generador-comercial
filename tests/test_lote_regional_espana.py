"""Comprobaciones de procedencia, normalización y límites del lote."""
import csv
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import pytest
from tools import generar_matriz_precios_espana as g

ROOT = Path(__file__).resolve().parents[1]


def leer(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter=';'))


def test_referencias_y_artefactos():
    fuentes = leer(g.FUENTES_LOTE_REGIONAL)
    matriz = {r['codigo_recurso']: r for r in leer(g.OUT)}
    audit = {r['codigo_recurso']: r for r in leer(ROOT / 'docs/auditoria_precios/espana_2026-11-06.csv')}
    esperado = {'MT-AGUA-OBRA': ('0.84', 'no_confirmado'),
                'MT-MALLA-ELEC': ('2.51', 'no_confirmado'),
                'MT-CLAVOS': ('3.21', 'no')}
    refs = g.referencias_lote_regional()
    for codigo, (precio, iva) in esperado.items():
        filas = [f for f in fuentes if f['codigo_recurso'] == codigo]
        assert len(filas) == len({f['fuente'] for f in filas}) == 2
        valores = [Decimal(f['importe_eur']) / Decimal(f['cantidad']) /
                   (1 + Decimal(f['iva_decimal']) if f['iva_decimal'] else 1) for f in filas]
        calculado = (sum(valores) / 2).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
        assert calculado == Decimal(precio) == Decimal(str(refs[codigo]['ES'].precio))
        assert matriz[codigo]['precio_referencia'] == precio
        assert matriz[codigo]['incluye_iva'] == iva
        assert matriz[codigo]['fuente'] == g.REVISION_LOTE_REGIONAL
        assert matriz[codigo]['fecha_consulta'] == '2026-11-07'
        assert audit[codigo]['estado_auditoria'] == 'en_revision'
        assert audit[codigo]['precio_revisado'] == precio


def test_exige_dos_fuentes_y_unidades_validas(tmp_path, monkeypatch):
    filas = leer(g.FUENTES_LOTE_REGIONAL)
    path = tmp_path / 'fuentes.csv'
    monkeypatch.setattr(g, 'FUENTES_LOTE_REGIONAL', path)
    def guardar():
        with path.open('w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=filas[0].keys(), delimiter=';')
            w.writeheader(); w.writerows(filas)
    filas[1]['fuente'] = filas[0]['fuente']
    guardar()
    with pytest.raises(ValueError, match='dos fuentes'):
        g.referencias_lote_regional()
    filas[1]['fuente'] = 'otra'
    filas[0]['unidad'] = 'l'
    guardar()
    with pytest.raises(ValueError, match='unidad'):
        g.referencias_lote_regional()
