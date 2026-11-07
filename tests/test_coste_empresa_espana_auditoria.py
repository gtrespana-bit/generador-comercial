from decimal import Decimal as D

import pytest

from tools.coste_empresa_espana_auditoria import calcular_coste_empresa


def entradas(**cambios):
    valores = dict(salario_anual=D('23051.90'), base_comun_anual=D('23051.90'),
                   base_profesional_anual=D('23051.90'), pension_empresa=D('0'),
                   otros_costes=D('0'), horas_productivas=D('1736'), porcentaje_at_ep=D('6.7'))
    valores.update(cambios)
    return valores


def test_escenario_pone_cargas_empresa_no_cuotas_trabajador():
    r = calcular_coste_empresa(**entradas())
    assert r.cuotas_comunes_mei == D('23051.90') * D('0.2435')
    assert r.cuotas_profesionales == D('23051.90') * D('0.13')
    assert r.total_anual == D('23051.90') * D('1.3735')
    assert round(r.coste_hora, 2) == D('18.24')


def test_bases_distintas_y_costes_adicionales_se_incluyen_una_vez():
    valores = entradas(base_comun_anual=D('25000'), base_profesional_anual=D('27000'),
                       pension_empresa=D('500'), otros_costes=D('1000'), horas_productivas=D('1500'))
    r = calcular_coste_empresa(**valores)
    esperado = D('23051.90') + D('25000') * D('0.2435') + D('27000') * D('0.13') + D('500') + D('1000')
    assert r.total_anual == esperado
    assert r.coste_hora == esperado / D('1500')


@pytest.mark.parametrize('cambios', [
    {'horas_productivas': D('0')}, {'salario_anual': D('-1')},
    {'base_comun_anual': D('0')}, {'porcentaje_at_ep': D('101')},
    {'otros_costes': D('NaN')}, {'pension_empresa': D('Infinity')},
])
def test_entradas_invalidas_no_producen_coste(cambios):
    with pytest.raises(ValueError):
        calcular_coste_empresa(**entradas(**cambios))


def test_referencias_operativas_se_calculan_de_las_tablas_y_coinciden_con_la_matriz():
    import csv
    from pathlib import Path
    from tools.generar_matriz_precios_espana import referencias_mano_obra_revisadas

    root = Path(__file__).resolve().parents[1]
    with (root / 'basedatos_partidas/salida/precios_recursos_espana.csv').open(encoding='utf-8-sig', newline='') as fh:
        matriz = {r['codigo_recurso']: r for r in csv.DictReader(fh, delimiter=';')}
    refs = referencias_mano_obra_revisadas()
    esperados = {'MO-AYU': 20.39, 'MO-AYU-ESP': 20.59,
                 'MO-OF1': 23.18, 'MO-OF1-ALB': 23.18}
    for codigo, importe in esperados.items():
        dato = refs[codigo]['ES']
        assert dato.precio == importe
        assert float(matriz[codigo]['precio_referencia']) == importe
        assert float(matriz[codigo]['precio_min']) == dato.minimo
        assert float(matriz[codigo]['precio_max']) == dato.maximo
        assert matriz[codigo]['confianza'] == 'derivado'
        assert matriz[codigo]['fecha_consulta'] == '2026-11-06'


def test_ambito_de_revision_no_confunde_estimacion_con_coste_garantizado():
    from tools.generar_matriz_precios_espana import referencias_mano_obra_revisadas
    for por_pais in referencias_mano_obra_revisadas().values():
        assert 'estimad' in por_pais['ES'].observaciones.lower()
        assert 'No incluye todos los costes' in por_pais['ES'].observaciones
