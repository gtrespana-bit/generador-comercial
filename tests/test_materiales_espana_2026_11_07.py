"""El lote nuevo es reproducible y no recalibra recursos pendientes."""
import csv
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import pytest
from tools import generar_matriz_precios_espana as g

ROOT = Path(__file__).resolve().parents[1]


def leer(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter=';'))


def test_ofertas_inventario_y_matriz():
    ofertas = leer(g.FUENTES_MATERIALES_07)
    auditoria = {r['codigo_recurso']: r for r in leer(ROOT / 'docs/auditoria_precios/espana_2026-11-06.csv')}
    matriz = {r['codigo_recurso']: r for r in leer(g.OUT)}
    esperados = {'MT-CABLE-DATOS': ('0.341772', '0.42'),
                 'MT-DESMOLD': ('3.189873', '5.93'), 'MT-ALAMBRE': ('2.1', '4.92')}
    refs = g.referencias_materiales_07()
    for codigo, (antes, nuevo) in esperados.items():
        fuentes = [o for o in ofertas if o['codigo_recurso'] == codigo]
        assert len(fuentes) == len({o['proveedor'] for o in fuentes}) == 2
        normalizados = [Decimal(o['precio_con_iva_eur']) / (1 + Decimal(o['iva_decimal'])) /
                        Decimal(o['cantidad_unidades_catalogo']) for o in fuentes]
        media = (sum(normalizados) / 2).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
        assert media == Decimal(nuevo) == Decimal(str(refs[codigo]['ES'].precio))
        assert matriz[codigo]['precio_referencia'] == nuevo
        assert matriz[codigo]['fuente'] == g.REVISION_MATERIALES_07
        assert matriz[codigo]['fecha_consulta'] == '2026-11-07'
        assert matriz[codigo]['incluye_iva'] == matriz[codigo]['incluye_transporte'] == 'no'
        assert auditoria[codigo]['estado_auditoria'] == 'en_revision'
        assert auditoria[codigo]['precio_matriz'] == antes
        assert auditoria[codigo]['precio_revisado'] == nuevo


def test_lote_incompleto_o_proveedor_repetido_se_rechaza(monkeypatch, tmp_path):
    ofertas = leer(g.FUENTES_MATERIALES_07)
    path = tmp_path / 'ofertas.csv'
    def escribir(filas):
        with path.open('w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=ofertas[0].keys(), delimiter=';')
            w.writeheader(); w.writerows(filas)
    monkeypatch.setattr(g, 'FUENTES_MATERIALES_07', path)
    escribir(ofertas[:-1])
    with pytest.raises(ValueError, match='exactamente dos'):
        g.referencias_materiales_07()
    ofertas[1]['proveedor'] = ofertas[0]['proveedor']
    escribir(ofertas)
    with pytest.raises(ValueError, match='proveedores distintos'):
        g.referencias_materiales_07()
