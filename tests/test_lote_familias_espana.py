import apoyo_cierre_espana as cierre
import csv
from decimal import Decimal

import pytest
from tools import generar_matriz_precios_espana as g


def leer(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter=';'))


def test_fuentes_matriz_y_auditoria_coinciden():
    fuentes = leer(g.FUENTES_LOTE_FAMILIAS)
    refs = g.referencias_lote_familias()
    assert len(fuentes) == 29 and len(refs) == 28
    assert Decimal(str(refs['MT-VALV-CHECK']['ES'].precio)) == Decimal('17.22')
    assert Decimal(str(refs['MT-MEMBRANA-PVC']['ES'].precio)) == Decimal('30.40')
    assert Decimal(str(refs['MT-SELLA-FISURA']['ES'].precio)) == Decimal('9.48')
    matriz = {r['codigo_recurso']: r for r in leer(g.OUT)}
    audit = {r['codigo_recurso']: r for r in leer(g.ROOT / 'docs/auditoria_precios/espana_2026-11-06.csv')}
    for codigo, ref in refs.items():
        filas = [r for r in fuentes if r['codigo_recurso'] == codigo]
        dato = ref['ES']
        assert Decimal(str(dato.precio)) == Decimal(audit[codigo]['precio_revisado']) == Decimal(matriz[codigo]['precio_referencia'])
        assert audit[codigo]['estado_auditoria'] == cierre.estado(codigo, 'en_revision')
        assert matriz[codigo]['fuente'] == cierre.fuente(codigo, g.REVISION_LOTE_FAMILIAS)
        assert matriz[codigo]['fecha_consulta'] == '2026-11-07'
        assert matriz[codigo]['incluye_iva'] == ('por_verificar' if any(r['criterio_iva'] == 'IVA no confirmado' for r in filas) else 'no')
        assert matriz[codigo]['incluye_transporte'] == 'no_confirmado'
        assert all(r['url'] in audit[codigo]['fuente_observada'] for r in filas)
    # El lote no puso precio: si hoy lo tiene, es el cierre del 7 de noviembre.
    assert audit['MT-BARRA-APOYO']['precio_revisado'] == cierre.precio_revisado('MT-BARRA-APOYO', '')


def test_datos_invalidos_y_conjuntos_incompletos_se_rechazan(monkeypatch, tmp_path):
    fuentes = leer(g.FUENTES_LOTE_FAMILIAS)
    path = tmp_path / 'fuentes.csv'
    monkeypatch.setattr(g, 'FUENTES_LOTE_FAMILIAS', path)
    def escribir(rows):
        with path.open('w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=fuentes[0], delimiter=';', lineterminator='\n')
            w.writeheader(); w.writerows(rows)
    for rows in (fuentes[:-1], fuentes + fuentes[:1]):
        escribir(rows)
        with pytest.raises(ValueError):
            g.referencias_lote_familias()
    for campo, valor in [('unidad', 'h'), ('importe_base', '-1'), ('cantidad_por_envase', '0'),
                         ('cantidad_por_recurso', 'NaN'), ('url_precio', ''), ('precio_resultante', '999'),
                         ('precio_bruto', '999'), ('criterio_iva', 'sin dato')]:
        malas = [r.copy() for r in fuentes]; malas[0][campo] = valor; escribir(malas)
        with pytest.raises(ValueError):
            g.referencias_lote_familias()
