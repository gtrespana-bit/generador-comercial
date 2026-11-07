import csv
from decimal import Decimal

import pytest
import apoyo_cierre_espana as cierre
from tools import generar_matriz_precios_espana as g


def leer(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter=';'))


def test_prioridad_trazable_en_auditoria_y_matriz():
    fuentes = leer(g.FUENTES_LOTE_PRIORIDAD)
    referencias = g.referencias_lote_prioridad()
    assert len(fuentes) == 20 and len(referencias) == 18
    matriz = {x['codigo_recurso']: x for x in leer(g.OUT)}
    audit = {x['codigo_recurso']: x for x in leer(g.ROOT / 'docs/auditoria_precios/espana_2026-11-06.csv')}
    for codigo, r in referencias.items():
        m, a, ref = matriz[codigo], audit[codigo], r['ES']
        p = Decimal(str(ref.precio))
        assert Decimal(m['precio_referencia']) == Decimal(m['precio_min']) == Decimal(m['precio_max']) == p
        assert Decimal(a['precio_revisado']) == p
        assert a['estado_auditoria'] == cierre.estado(codigo, 'en_revision')
        assert m['fuente'] == g.REVISION_LOTE_PRIORIDAD and m['fecha_consulta'] == '2026-11-07'
        assert m['incluye_iva'] == ('por_verificar' if any(f['criterio_iva'] == 'IVA no confirmado' for f in fuentes if f['codigo_recurso'] == codigo) else 'no')
        assert m['incluye_transporte'] == 'no_confirmado'
        assert all(f['url'] in a['fuente_observada'] for f in fuentes if f['codigo_recurso'] == codigo)
    esperados = {'MT-PERNO-ANCLA': '1.55', 'MT-PUENTE-ADH': '23.91', 'MT-CINTA-ENM': '1.83',
                 'MT-CIELO-DESM': '4.86', 'MT-HIDROFUGO': '1.91', 'MT-PIN-MAGNETICA': '21.97'}
    assert all(Decimal(str(referencias[k]['ES'].precio)) == Decimal(v) for k, v in esperados.items())
    for codigo in ('MT-MALLA-JUNTA', 'MT-PER-BANDA'):
        # Posteriormente investigados en el lote de componentes.
        assert audit[codigo]['estado_auditoria'] == cierre.estado(codigo, 'en_revision')
        assert codigo in g.referencias_lote_componentes()


def test_faltantes_duplicados_y_datos_invalidos(monkeypatch, tmp_path):
    fuentes = leer(g.FUENTES_LOTE_PRIORIDAD)
    path = tmp_path / 'fuentes.csv'
    monkeypatch.setattr(g, 'FUENTES_LOTE_PRIORIDAD', path)
    def escribir(filas):
        with path.open('w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fuentes[0], delimiter=';')
            writer.writeheader(); writer.writerows(filas)
    for filas in (fuentes[:-1], fuentes + fuentes[:1]):
        escribir(filas)
        with pytest.raises(ValueError, match='incompleto o duplicado'):
            g.referencias_lote_prioridad()
    for campo, valor in [('unidad', 'litros'), ('importe_base', '-1'), ('cantidad_por_envase', '0'),
                         ('precio_resultante', '999'), ('criterio_iva', 'sin dato'), ('url_precio', '')]:
        malas = [f.copy() for f in fuentes]; malas[0][campo] = valor
        escribir(malas)
        with pytest.raises(ValueError):
            g.referencias_lote_prioridad()
    malas = [f.copy() for f in fuentes]
    malas[2]['producto'] = malas[1]['producto']  # pertenecen a códigos distintos
    # Duplicar dos componentes del mismo recurso sin alterar el número de filas.
    malas[1]['producto'] = malas[0]['producto']
    escribir(malas)
    with pytest.raises(ValueError, match='Componente duplicado'):
        g.referencias_lote_prioridad()
    malas = [f.copy() for f in fuentes]
    i = next(i for i, x in enumerate(malas) if x['codigo_recurso'] == 'MT-PUENTE-ADH')
    malas[i]['url_tecnica'] = ''
    escribir(malas)
    with pytest.raises(ValueError, match='Fuente de prioridad inválida'):
        g.referencias_lote_prioridad()
    malas = [f.copy() for f in fuentes]
    i = next(i for i, x in enumerate(malas) if x['criterio_iva'] == 'IVA 21% supuesto')
    malas[i]['precio_bruto'] = '999'
    escribir(malas)
    with pytest.raises(ValueError, match='IVA incoherente'):
        g.referencias_lote_prioridad()
