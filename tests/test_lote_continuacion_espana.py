import csv
from decimal import Decimal

import pytest
from tools import generar_matriz_precios_espana as g


def leer(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter=';'))


def test_fuentes_matriz_y_auditoria_coinciden():
    fuentes = leer(g.FUENTES_LOTE_CONTINUACION)
    refs = g.referencias_lote_continuacion()
    assert len(fuentes) == 7 and len(refs) == 6
    for codigo, precio in {'MT-GRAVILLA': '38.97', 'MT-CRU-NIV': '0.19', 'MT-MAMPARA-OFI': '131.21', 'MT-PANEL-PVC-BANO': '34.75', 'MT-MOSAICO': '12.40', 'MT-ADH-PIEDRA': '3.08'}.items():
        assert Decimal(str(refs[codigo]['ES'].precio)) == Decimal(precio)
    matriz = {r['codigo_recurso']: r for r in leer(g.OUT)}
    audit = {r['codigo_recurso']: r for r in leer(g.ROOT / 'docs/auditoria_precios/espana_2026-11-06.csv')}
    for codigo, ref in refs.items():
        filas = [r for r in fuentes if r['codigo_recurso'] == codigo]
        dato = ref['ES']
        assert Decimal(str(dato.precio)) == Decimal(audit[codigo]['precio_revisado']) == Decimal(matriz[codigo]['precio_referencia'])
        assert audit[codigo]['estado_auditoria'] == 'en_revision'
        assert matriz[codigo]['fuente'] == g.REVISION_LOTE_CONTINUACION
        assert matriz[codigo]['fecha_consulta'] == '2026-11-07'
        assert matriz[codigo]['incluye_iva'] == ('por_verificar' if any(r['criterio_iva'] == 'IVA no confirmado' for r in filas) else 'no')
        assert matriz[codigo]['incluye_transporte'] == 'no_confirmado'
        assert all(r['url'] in audit[codigo]['fuente_observada'] for r in filas)
    # La convención de medida (7 de noviembre) sí le puso precio después.
    assert (not audit['MT-ELE-CAJA']['precio_revisado']
            or 'Convención de medida' in audit['MT-ELE-CAJA']['criterio_revisado'])
    gravilla = next(r for r in fuentes if r['codigo_recurso'] == 'MT-GRAVILLA')
    assert Decimal(gravilla['cantidad_por_recurso']) == Decimal('0.180') / Decimal('0.10')
    cunas = [r for r in fuentes if r['codigo_recurso'] == 'MT-CRU-NIV']
    assert len(cunas) == 2 and all(r['criterio_iva'] == 'IVA 21% supuesto' for r in cunas)
    assert 'reutilizable' in cunas[1]['reserva']



def test_datos_invalidos_y_conjuntos_incompletos_se_rechazan(monkeypatch, tmp_path):
    fuentes = leer(g.FUENTES_LOTE_CONTINUACION)
    path = tmp_path / 'fuentes.csv'
    monkeypatch.setattr(g, 'FUENTES_LOTE_CONTINUACION', path)
    def escribir(rows):
        with path.open('w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=fuentes[0], delimiter=';', lineterminator='\n')
            w.writeheader(); w.writerows(rows)
    for rows in (fuentes[:-1], fuentes + fuentes[:1]):
        escribir(rows)
        with pytest.raises(ValueError):
            g.referencias_lote_continuacion()
    for campo, valor in [('unidad', 'h'), ('importe_base', '-1'), ('cantidad_por_envase', '0'),
                         ('cantidad_por_recurso', 'NaN'), ('url_precio', ''), ('precio_resultante', '999'),
                         ('precio_bruto', '999'), ('criterio_iva', 'sin dato')]:
        malas = [r.copy() for r in fuentes]; malas[0][campo] = valor; escribir(malas)
        with pytest.raises(ValueError):
            g.referencias_lote_continuacion()
