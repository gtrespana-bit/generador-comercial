import apoyo_cierre_espana as cierre
import csv
from decimal import Decimal

import pytest
from tools import generar_matriz_precios_espana as g


def leer(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter=';'))


def test_fuentes_matriz_y_auditoria_coinciden():
    fuentes = leer(g.FUENTES_LOTE_VERIFICACION)
    refs = g.referencias_lote_verificacion()
    assert len(fuentes) == 8 and len(refs) == 7
    for codigo, precio in {'MT-MOLDURA-YESO': '1.39', 'MT-CORNISA': '7.15', 'MT-JUNTA-DILAT': '4.09', 'MT-HERRAJE-MAD': '5.45', 'MT-TABIQUE-MOVIL': '467.09', 'MT-MASTIC-CORTAFUEGO': '46.24', 'MT-TUBO-DREN': '6.50'}.items():
        assert Decimal(str(refs[codigo]['ES'].precio)) == Decimal(precio)
    matriz = {r['codigo_recurso']: r for r in leer(g.OUT)}
    audit = {r['codigo_recurso']: r for r in leer(g.ROOT / 'docs/auditoria_precios/espana_2026-11-06.csv')}
    for codigo, ref in refs.items():
        filas = [r for r in fuentes if r['codigo_recurso'] == codigo]
        dato = ref['ES']
        assert Decimal(str(dato.precio)) == Decimal(audit[codigo]['precio_revisado']) == Decimal(matriz[codigo]['precio_referencia'])
        assert audit[codigo]['estado_auditoria'] == 'en_revision'
        assert matriz[codigo]['fuente'] == g.REVISION_LOTE_VERIFICACION
        assert matriz[codigo]['fecha_consulta'] == '2026-11-07'
        assert matriz[codigo]['incluye_iva'] == ('por_verificar' if any(r['criterio_iva'] == 'IVA no confirmado' for r in filas) else 'no')
        assert matriz[codigo]['incluye_transporte'] == 'no_confirmado'
        assert all(r['url'] in audit[codigo]['fuente_observada'] for r in filas)
    assert (not audit['MQ-ASPIR']['precio_revisado']
            or 'MODELO-MQ' in audit['MQ-ASPIR']['codigo_fuente'])
    # El lote no puso precio: si hoy lo tiene, es el cierre del 7 de noviembre.
    assert audit['MT-HERRAJE-CORRED']['precio_revisado'] == cierre.precio_revisado(
        'MT-HERRAJE-CORRED', '')
    masilla = next(r for r in fuentes if r['codigo_recurso'] == 'MT-MASTIC-CORTAFUEGO')
    assert masilla['cantidad_por_envase'] == '0.465' and masilla['criterio_iva'] == 'neto en ficha'
    assert Decimal('0.310') * Decimal('1.5') == Decimal(masilla['cantidad_por_envase'])


def test_datos_invalidos_y_conjuntos_incompletos_se_rechazan(monkeypatch, tmp_path):
    fuentes = leer(g.FUENTES_LOTE_VERIFICACION)
    path = tmp_path / 'fuentes.csv'
    monkeypatch.setattr(g, 'FUENTES_LOTE_VERIFICACION', path)
    def escribir(rows):
        with path.open('w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=fuentes[0], delimiter=';', lineterminator='\n')
            w.writeheader(); w.writerows(rows)
    for rows in (fuentes[:-1], fuentes + fuentes[:1]):
        escribir(rows)
        with pytest.raises(ValueError):
            g.referencias_lote_verificacion()
    for campo, valor in [('unidad', 'h'), ('importe_base', '-1'), ('cantidad_por_envase', '0'),
                         ('cantidad_por_recurso', 'NaN'), ('url_precio', ''), ('precio_resultante', '999'),
                         ('precio_bruto', '999'), ('criterio_iva', 'sin dato')]:
        malas = [r.copy() for r in fuentes]; malas[0][campo] = valor; escribir(malas)
        with pytest.raises(ValueError):
            g.referencias_lote_verificacion()
