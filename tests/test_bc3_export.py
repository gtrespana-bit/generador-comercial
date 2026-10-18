"""Regresiones de exportación: validar los registros, no solo nuestro parser."""
from types import SimpleNamespace as NS

import pytest

from app.services.bc3 import exportar_presupuesto_bc3, parse_bc3, analizar_bc3


def partida(**kwargs):
    datos = dict(nombre="Solado español", unidad="m2", precio_unitario=25.1234,
                 cantidad=1.2345, mediciones=[], descripcion="Descripción con ñ y €",
                 codigo_externo="SOLADO", descomposicion_cype=None)
    datos.update(kwargs)
    return NS(**datos)


def presupuesto(partidas=None, **kwargs):
    datos = dict(numero="P-001", titulo="Reforma", moneda="EUR", impuesto_pct=21,
                 descuento_pct=5, subtotal=100, capitulos=[NS(nombre="Albañilería", subtotal=100,
                 partidas=partidas if partidas is not None else [partida()])])
    datos.update(kwargs)
    return NS(**datos)


def registros(p):
    contenido = exportar_presupuesto_bc3(p, NS(empresa_nombre="Empresa ~ | \\ ñ"))
    assert b"\r\n" in contenido
    return [linea.split("|") for linea in contenido.decode("cp1252").splitlines()]


def arbol(regs):
    resultado = {}
    for r in regs:
        if r[0] != "~D":
            continue
        assert r[1] not in resultado, "Solo un ~D por padre"
        assert len(r) == 4 and r[-1] == ""
        sub = r[2].split("\\")
        assert sub.pop() == ""
        assert len(sub) % 3 == 0
        resultado[r[1]] = [(sub[i], float(sub[i+1]), float(sub[i+2])) for i in range(0, len(sub), 3)]
    return resultado


def test_estructura_capitulos_arbol_y_precision():
    p = presupuesto([partida(), partida(codigo_externo="SEGUNDA", cantidad=0)])
    p.capitulos.append(NS(nombre="Pintura", subtotal=0, partidas=[partida(codigo_externo="TERCERA")]))
    regs = registros(p)
    conceptos = {r[1]: r for r in regs if r[0] == "~C"}
    assert conceptos["P_001##"][2:4] == ["", "Reforma"]
    assert conceptos["01#"][2:4] == ["", "Albañilería"]
    assert conceptos["SOLADO"][4] == "25.1234"
    tree = arbol(regs)
    assert len(tree["P_001##"]) == 2
    assert tree["01#"] == [("SOLADO", 1, 1.2345), ("SEGUNDA", 1, 0)]
    assert all(child in conceptos for hijos in tree.values() for child, _, _ in hijos)
    analisis = analizar_bc3(exportar_presupuesto_bc3(p))
    assert {f["capitulo"] for f in analisis["filas"]} == {"ALBAÑILERÍA", "PINTURA"}
    assert len(analisis["filas"]) == 3


def test_codigos_duplicados_truncados_y_reservados_no_colisionan():
    codigos = ["01", "02", "P-001", "A" * 40, "A" * 40, "A" * 40, "BAD##", "BAD", "MO%", "MO&"]
    regs = registros(presupuesto([partida(codigo_externo=c) for c in codigos], numero="P"*40))
    cods = [r[1] for r in regs if r[0] == "~C"]
    assert len(cods) == len(set(c.rstrip("#") for c in cods))
    assert all(len(c) <= 20 for c in cods)
    assert all(not c.endswith("#") for c in cods[2:])
    arbol(regs)


def test_mediciones_un_campo_seis_subcampos_por_linea_y_ceros():
    p = presupuesto([partida(cantidad_total=1.2345, mediciones=[
        NS(concepto="Salón | ~ \\ norte", cantidad=1.2345), NS(concepto="Anulada", cantidad=0),
    ])])
    regs = registros(p)
    m = next(r for r in regs if r[0] == "~M")
    assert len(m) == 6
    assert m[2:4] == ["1", "1.2345"]
    sub = m[4].split("\\")
    assert sub.pop() == ""
    assert len(sub) == 12
    parsed = parse_bc3(exportar_presupuesto_bc3(p))
    assert len(parsed["mediciones"][0].lineas) == 2
    assert parsed["mediciones"][0].lineas[1]["uds"] == 0


def recurso(**kwargs):
    datos = dict(tipo="recurso", codigo="MO01", unidad="h", descripcion="Oficial",
                 precio_unitario=10, rendimiento=0.5, moneda="EUR", categoria="mano_obra")
    datos.update(kwargs)
    return NS(**datos)


def test_recursos_compartidos_y_precios_distintos_y_precio_venta():
    partes = [partida(codigo_externo=f"P{i}", precio_unitario=20,
                     descomposicion_cype=NS(filas=[recurso(precio_unitario=precio)]))
              for i, precio in enumerate([10, 10, 15])]
    regs = registros(presupuesto(partes))
    tree = arbol(regs)
    assert tree["P0"][0][0] == tree["P1"][0][0]
    assert tree["P0"][0][0] != tree["P2"][0][0]
    precios = {r[1]: float(r[4]) for r in regs if r[0] == "~C"}
    for cod in ["P0", "P1", "P2"]:
        assert sum(precios[c] * f * rend for c, f, rend in tree[cod]) == pytest.approx(20)


def test_no_conversion_inventada_y_rendimiento_cero():
    partes = [partida(codigo_externo="USD", precio_unitario=20,
                      descomposicion_cype=NS(filas=[recurso(moneda="USD", rendimiento=0)])),
              partida(codigo_externo="GBP", descomposicion_cype=NS(filas=[recurso(moneda="GBP")]))]
    regs = registros(presupuesto(partes, tipo_cambio=0.85))
    tree = arbol(regs)
    assert tree["USD"][0][2] == 0
    assert "GBP" not in tree  # precio cerrado, no costes en moneda incorrecta


def test_opcionales_y_excluidas_no_alteran_presupuesto_contratado():
    regs = registros(presupuesto([
        partida(codigo_externo="INC"), partida(codigo_externo="EXC", tipo_partida="excluded"),
        partida(codigo_externo="OPT", tipo_partida="optional", seleccionada=False),
        partida(codigo_externo="SEL", tipo_partida="optional", seleccionada=True),
    ], usar_funciones_avanzadas=True))
    assert [c for c, _, _ in arbol(regs)["01#"]] == ["INC", "SEL"]


def test_descarga_bc3_con_numero_unicode(entorno, cliente_web):
    from app.models import Presupuesto
    Session, ids, _rol = entorno
    with Session() as db:
        db.info["organizacion_id"] = ids[0]
        p = db.query(Presupuesto).filter(Presupuesto.es_demo.is_(False)).first()
        p.numero = 'P-ñ-漢"01'
        identificador = p.id
        db.commit()
    resp = cliente_web.get(f"/presupuestos/{identificador}/exportar?formato=bc3", follow_redirects=False)
    assert resp.status_code == 200, resp.text[:300]
    assert "windows-1252" in resp.headers["content-type"]
    assert "filename*=UTF-8''presupuesto_" in resp.headers["content-disposition"]
    assert "%22" in resp.headers["content-disposition"]
    parsed = parse_bc3(resp.content)
    assert parsed["conceptos"]


def test_recargos_descuento_iva_y_divisa():
    regs = registros(presupuesto(moneda="GBP", transporte_monto=12,
                                 gastos_indirectos_pct=10, imprevistos_pct=2,
                                 otros_cargos_monto=3))
    tree = arbol(regs)
    conceptos = {r[1]: r for r in regs if r[0] == "~C"}
    assert float(conceptos["P_001##"][4]) == 127
    assert sum(float(conceptos[c][4]) for c, _, _ in tree["CARGOS#"]) == 27
    k = next(r for r in regs if r[0] == "~K")
    assert k[1].split("\\")[-2] == "GBP"
    assert k[2].split("\\")[-2:] == ["5", "21"]
