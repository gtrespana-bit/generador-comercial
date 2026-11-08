import apoyo_cierre_espana as cierre
import csv
from decimal import Decimal

import pytest
from tools import generar_matriz_precios_espana as g


def leer(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter=';'))


def test_referencias_trazadas_y_normalizadas():
    fuentes = leer(g.FUENTES_LOTE_ALTA_FRECUENCIA)
    refs = g.referencias_lote_alta_frecuencia()
    assert len(fuentes) == 7 and len(refs) == 5
    esperado = {'MT-PLO-SOP': '0.95', 'MT-TUB-FRIGO': '5.53',
                'MT-FLOTANTE': '8.16', 'MT-MACHIH-MAD': '17.16', 'MT-MELAMINA': '18.68'}
    matriz = {r['codigo_recurso']: r for r in leer(g.OUT)}
    audit = {r['codigo_recurso']: r for r in leer(g.ROOT / 'docs/auditoria_precios/espana_2026-11-06.csv')}
    for codigo, valor in esperado.items():
        ref = refs[codigo]['ES']
        assert Decimal(str(ref.precio)) == Decimal(valor)
        assert Decimal(matriz[codigo]['precio_referencia']) == Decimal(valor)
        assert Decimal(audit[codigo]['precio_revisado']) == Decimal(valor)
        assert audit[codigo]['estado_auditoria'] == 'confirmado_referencia'
        assert matriz[codigo]['fuente'] == g.REVISION_LOTE_ALTA_FRECUENCIA
        assert matriz[codigo]['fecha_consulta'] == '2026-11-07'
        assert matriz[codigo]['incluye_iva'] == 'no'
        assert matriz[codigo]['incluye_transporte'] == 'no_confirmado'
        assert all(row['url'] in audit[codigo]['fuente_observada'] for row in fuentes if row['codigo_recurso'] == codigo)
    for codigo in ('MT-SENAL-OBRA', 'MT-PIN-LIJA', 'MQ-LIJAD', 'MQ-DETECTOR'):
        # El lote no puso precio: si hoy hay uno, viene del modelo de maquinaria o
        # del cierre total del 7 de noviembre, que se aplican después y por otra vía.
        if audit[codigo]['precio_revisado']:
            assert ('MODELO-MQ' in audit[codigo]['codigo_fuente']
                    or audit[codigo]['precio_revisado'] == cierre.precio_revisado(codigo, ''))


def test_fuentes_incompletas_o_invalidas_se_rechazan(monkeypatch, tmp_path):
    fuentes = leer(g.FUENTES_LOTE_ALTA_FRECUENCIA)
    path = tmp_path / 'fuentes.csv'
    monkeypatch.setattr(g, 'FUENTES_LOTE_ALTA_FRECUENCIA', path)
    def escribir(rows):
        with path.open('w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=fuentes[0], delimiter=';', lineterminator='\n')
            w.writeheader(); w.writerows(rows)
    for rows in (fuentes[:-1], fuentes + fuentes[:1]):
        escribir(rows)
        with pytest.raises(ValueError):
            g.referencias_lote_alta_frecuencia()
    for campo, valor in [('unidad', 'h'), ('importe_base', '-1'), ('cantidad_por_envase', '0'),
                         ('cantidad_por_recurso', 'NaN'), ('url_precio', ''), ('precio_resultante', '999'),
                         ('precio_bruto', '999'), ('criterio_iva', 'sin dato')]:
        malas = [r.copy() for r in fuentes]; malas[0][campo] = valor; escribir(malas)
        with pytest.raises(ValueError):
            g.referencias_lote_alta_frecuencia()
    malas = [r.copy() for r in fuentes]; malas[2]['producto'] = malas[1]['producto']; escribir(malas)
    with pytest.raises(ValueError, match='Componente duplicado'):
        g.referencias_lote_alta_frecuencia()
