import csv
from decimal import Decimal, ROUND_HALF_UP
import pytest
from tools import generar_matriz_precios_espana as g


def leer(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter=';'))


def test_precios_con_componentes_sin_redondeo_intermedio():
    fuentes = leer(g.FUENTES_LOTE_POSTERIOR)
    grupos = {}
    for f in fuentes:
        grupos.setdefault(f['codigo_recurso'], []).append(Decimal(f['importe_eur']) / Decimal(f['cantidad']) / (1 + Decimal(f['iva_decimal'])))
    q = lambda x: x.quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
    esperado = {
        'MT-PYL-PASTA': q(sum(grupos['PASTA']) / 2 + Decimal('1.30') / Decimal('0.34') * sum(grupos['CINTA']) / 2),
        'MT-CABLE-ALARMA': q(sum(grupos['MT-CABLE-ALARMA']) / 2),
        'MT-TORN-TECHO': q(sum(grupos['MT-TORN-TECHO']) / 2),
    }
    assert esperado == {'MT-PYL-PASTA': Decimal('1.01'), 'MT-CABLE-ALARMA': Decimal('0.62'), 'MT-TORN-TECHO': Decimal('0.21')}
    matriz = {r['codigo_recurso']: r for r in leer(g.OUT)}
    auditoria = {r['codigo_recurso']: r for r in leer(g.ROOT / 'docs/auditoria_precios/espana_2026-11-06.csv')}
    refs = g.referencias_lote_posterior()
    for codigo, valor in esperado.items():
        r = matriz[codigo]
        assert Decimal(r['precio_referencia']) == Decimal(str(refs[codigo]['ES'].precio)) == valor
        assert r['fecha_consulta'] == '2026-11-07' and r['fuente'] == g.REVISION_LOTE_POSTERIOR
        assert r['incluye_iva'] == 'no' and r['incluye_transporte'] == 'no_confirmado'
        assert Decimal(r['precio_min']) <= valor <= Decimal(r['precio_max'])
        assert auditoria[codigo]['estado_auditoria'] == 'confirmado_referencia'
        assert Decimal(auditoria[codigo]['precio_revisado']) == valor


def test_no_acepta_fuentes_incompletas(monkeypatch, tmp_path):
    rows = leer(g.FUENTES_LOTE_POSTERIOR)[:-1]
    archivo = tmp_path / 'fuentes.csv'
    with archivo.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=rows[0], delimiter=';')
        w.writeheader(); w.writerows(rows)
    monkeypatch.setattr(g, 'FUENTES_LOTE_POSTERIOR', archivo)
    with pytest.raises(ValueError, match='exactamente dos'):
        g.referencias_lote_posterior()
