import apoyo_cierre_espana as cierre
import csv
from decimal import Decimal

import pytest
from tools import generar_matriz_precios_espana as g


def leer(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter=';'))


def test_observaciones_trazables_y_referencias_en_matriz_y_auditoria():
    fuentes = leer(g.FUENTES_LOTE_CADENAS)
    assert len(fuentes) == 21
    referencias = g.referencias_lote_cadenas()
    assert len(referencias) == 20
    matriz = {r['codigo_recurso']: r for r in leer(g.OUT)}
    auditoria = {r['codigo_recurso']: r for r in leer(g.ROOT / 'docs/auditoria_precios/espana_2026-11-06.csv')}
    for codigo, ref in referencias.items():
        dato = ref['ES']
        m, a = matriz[codigo], auditoria[codigo]
        precio = Decimal(str(dato.precio))
        assert Decimal(m['precio_referencia']) == Decimal(m['precio_min']) == Decimal(m['precio_max']) == precio
        assert m['fuente'] == cierre.fuente(codigo, g.REVISION_LOTE_CADENAS)
        assert m['fecha_consulta'] == '2026-11-07'
        assert m['confianza'] == 'derivado' and m['incluye_iva'] == 'no'
        assert m['incluye_transporte'] == 'no_confirmado'
        assert a['estado_auditoria'] == cierre.estado(codigo, 'en_revision')
        assert Decimal(a['precio_revisado']) == precio
        assert all(x['url'] in a['fuente_observada'] for x in fuentes if x['codigo_recurso'] == codigo)
    assert Decimal(str(referencias['MT-PIN-MASILLA']['ES'].precio)) == Decimal('1.23')
    assert Decimal(str(referencias['MT-PYL-PLACA-HD']['ES'].precio)) == Decimal('4.40')
    assert Decimal(str(referencias['MT-ESPEJO']['ES'].precio)) == Decimal('29.52')


def test_fuentes_incompletas_repetidas_y_calculos_erroneos(monkeypatch, tmp_path):
    fuentes = leer(g.FUENTES_LOTE_CADENAS)
    archivo = tmp_path / 'fuentes.csv'
    monkeypatch.setattr(g, 'FUENTES_LOTE_CADENAS', archivo)

    def escribir(filas):
        with archivo.open('w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=fuentes[0], delimiter=';')
            w.writeheader()
            w.writerows(filas)

    escribir(fuentes[:-1])
    with pytest.raises(ValueError, match='incompleto'):
        g.referencias_lote_cadenas()
    escribir(fuentes + [fuentes[0]])
    with pytest.raises(ValueError, match='duplicado'):
        g.referencias_lote_cadenas()
    for campo, valor in [('unidad', 'ud'), ('cantidad_recurso', '0'), ('precio_normalizado', '999'), ('precio_envase_iva', '0'), ('criterio_iva', 'sin información')]:
        malas = [f.copy() for f in fuentes]
        malas[0][campo] = valor
        escribir(malas)
        with pytest.raises(ValueError):
            g.referencias_lote_cadenas()
    malas = [f.copy() for f in fuentes]
    malas[2]['precio_envase_iva'] = '20.00'
    escribir(malas)
    with pytest.raises(ValueError, match='IVA supuesto incoherente'):
        g.referencias_lote_cadenas()
    malas = [f.copy() for f in fuentes]
    malas[2]['url'] = malas[1]['url']
    escribir(malas)
    with pytest.raises(ValueError, match='duplicada'):
        g.referencias_lote_cadenas()
