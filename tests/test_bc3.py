from app.services.bc3 import analizar_bc3, es_formato_bc3


def test_es_formato_bc3():
    assert es_formato_bc3(b"~V|BCCA|FIEBDC-3/2020|")
    assert es_formato_bc3(b"~C|01#|m2|DEMOLICIONES|0|")
    assert not es_formato_bc3(b"Capitulo,Partida,Precio\n")


def test_analizar_bc3_basico():
    sample = """~V|BCCA 2023|FIEBDC-3/2020|Presto|Titulo obra|ANSI|Comentario|2||
~C|01#|m2|DEMOLICIONES|0|01012024|0|
~C|01.01|m2|Demolicion solado|12.5|01012024|0|
~T|01.01|Descripcion larga demolicion|
~C|02#|m2|REVESTIMIENTOS|0|01012024|0|
~C|02.01|m2|Solado porcelanico|38.5|01012024|0|
~D|01#|01.01\\1\\1\\|
~D|02#|02.01\\1\\1\\|
~M|01#\\01.01||12.5|0\\Salon\\1\\4\\3\\|
"""
    res = analizar_bc3(sample.encode("utf-8"))
    assert res["formato"] == "bc3"
    assert res["capitulos_detectados"] == 2
    assert len(res["filas"]) == 2
    # Ver capítulos respetados
    capitulos = {c["nombre"] for c in res["capitulos"]}
    assert "DEMOLICIONES" in capitulos
    assert "REVESTIMIENTOS" in capitulos
    # Mediciones
    demo = next(f for f in res["filas"] if f["codigo"] == "01.01")
    assert demo["cantidad"] == 12.5
    assert demo["mediciones"][0]["concepto"] == "Salon"


def test_analizar_bc3_con_costes():
    sample = """~C|02.01|m2|Solado|38.5|01012024|0|
~C|MO001|h|Oficial|24.41|01012024|1|
~C|MT001|kg|Cemento|0.23|01012024|3|
~D|02.01|MO001\\0.2\\1\\|MT001\\8.5\\1\\|
"""
    res = analizar_bc3(sample.encode("utf-8"))
    assert len(res["filas"]) >= 1
    solado = next((f for f in res["filas"] if f["codigo"] == "02.01"), None)
    assert solado is not None
    # coste materiales y mano obra separados
    assert solado["costes"]["mano_obra"] > 0
    assert solado["costes"]["materiales"] > 0
