import json
from tools.cruzar_precios_cerp import leer_cerp
from tools.cruzar_precios_bc3 import candidatos


def test_filtra_fuentes_tipos_unidades_y_precios_ambiguos(tmp_path):
    p = {'currency':'EUR', 'date':'2022-12', 'edition':'2024-01', 'source':'bcca',
         'scope':{'country':'ES', 'region':'AND'}, 'sourceCode':'TA00100', 'value':22.36}
    def item(**kw):
        base = {'kind':'labor','unit':'h','summary':'AYUDANTE','text':'Horas trabajadas', 'bom':[], 'prices':[p]}
        return dict(base, **kw)
    items = [item(), item(kind='auxiliary'), item(unit='t'), item(bom=[{'id':'x'}]),
             item(prices=[p, p]), item(prices=[dict(p, value=0)]),
             item(prices=[dict(p, scope={'country':'ES','region':'MAD'})]),
             item(prices=[dict(p, currency='USD')])]
    path = tmp_path / 'basicos.json'; path.write_text(json.dumps({'version':'test', 'items':items}), encoding='utf-8')
    precios, sha, version = leer_cerp(path)
    assert len(precios) == 1 and version == 'test' and len(sha) == 64
    assert precios[0].fecha_fuente == '2024-01|2022-12'
    r = [{'codigo_recurso':'X','unidad':'h','categoria':'mano_obra','descripcion':'Ayudante'}]
    assert list(candidatos(r, precios))[0][1][0][2].codigo == 'TA00100'


def test_fuente_sin_datos_validos_no_produce_resultado(tmp_path):
    import pytest
    path = tmp_path / 'data.json'; path.write_text('{"items": []}', encoding='utf-8')
    with pytest.raises(ValueError, match='No hay precios'):
        leer_cerp(path)
