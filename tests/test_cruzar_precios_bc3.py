from tools.cruzar_precios_bc3 import leer_bc3, candidatos, unidad


def test_solo_precios_simples_unidad_y_un_precio(tmp_path):
    bc3 = tmp_path / 'base.bc3'
    bc3.write_bytes(('~V|RIB|FIEBDC-3/2020|\n'
                     '~C|P001|kg|Mortero reparación R4|1.23|240426|0|\n'
                     '~T|P001|Mortero estructural R4 para reparación.|\n'
                     '~C|P002|kg|Mortero instalación|8|240426|0|\n'
                     '~D|P002|O001\\1\\1\\|\n'
                     '~C|P003|kg|Precio por zona|1\\2|240426|0|\n'
                     '~C|E001|kg|Partida no básica|5|240426|0|\n'
                     '~C|M001|h|Taladro|2|240426|0|\n').encode('cp1252'))
    precios, sha = leer_bc3(bc3)
    assert len(sha) == 64
    assert {p.codigo for p in precios} == {'P001', 'M001'}
    assert next(p for p in precios if p.codigo == 'P001').texto.startswith('Mortero estructural')
    r = [{'codigo_recurso': 'A', 'categoria': 'materiales', 'unidad': 'kg', 'descripcion': 'Mortero reparación R4'}]
    _, hits = next(candidatos(r, precios))
    assert len(hits) == 1 and hits[0][2].codigo == 'P001'
    assert unidad('m²') == 'm2' and unidad('t') is None


def test_sin_coincidencia_ni_conversion_y_alerta_dimensiones(tmp_path):
    path = tmp_path / 'test.bc3'
    path.write_text('~C|P01|m|Tubo PVC diámetro 25 mm|1.5|240426|0|\n~C|P02|kg|Tubo PVC 20 mm|1|240426|0|', encoding='utf8')
    precios, _ = leer_bc3(path)
    recursos = [{'codigo_recurso':'A','categoria':'materiales','unidad':'m','descripcion':'Tubo PVC diámetro 20 mm'}, {'codigo_recurso':'B','categoria':'maquinaria','unidad':'ud','descripcion':'Tubo'}]
    result = list(candidatos(recursos, precios))
    assert result[0][1][0][2].codigo == 'P01'
    assert result[0][1][0][3] == 'numeros_diferentes_o_ausentes'
    assert result[1][1] == []
