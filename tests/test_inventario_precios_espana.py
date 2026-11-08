from collections import Counter
import pytest
from tools import inventario_precios_espana as i


def test_inventario_integral_reproducible_y_estados_actuales():
    filas = i.inventario(i.leer(i.AUDITORIA), i.leer(i.CANDIDATOS), i.leer(i.MATRIZ))
    assert filas == i.leer(i.SALIDA)
    assert len(filas) == len({f['codigo_recurso'] for f in filas}) == 388
    assert Counter(f['estado_auditoria_actual'] for f in filas) == {
        'confirmado_referencia': 37, 'en_revision': 351}
    assert sum(bool(f['primer_codigo_bcca']) for f in filas) == 359
    assert sum(bool(f['precio_revisado']) for f in filas) == 388
    assert all(int(f['numero_candidatos_bcca']) == 0 for f in filas if not f['primer_codigo_bcca'])
    assert any(f['estado_auditoria_actual'] != f0['estado_auditoria']
               for f in filas for f0 in i.leer(i.CANDIDATOS)
               if f['codigo_recurso'] == f0['codigo_recurso'])


def test_falla_con_recursos_faltantes_o_duplicados():
    a, c, m = i.leer(i.AUDITORIA), i.leer(i.CANDIDATOS), i.leer(i.MATRIZ)
    with pytest.raises(ValueError):
        i.inventario(a[:-1], c, m)
    with pytest.raises(ValueError):
        i.inventario(a + [a[0]], c, m)
    with pytest.raises(ValueError):
        i.inventario(a, c, m + [m[0]])
