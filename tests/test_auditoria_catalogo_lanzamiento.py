"""Regresiones de la auditoría exhaustiva del catálogo y sus mercados."""
import csv
from pathlib import Path

from basedatos_partidas.auditar_lanzamiento import auditar_matriz, auditar_partidas


def test_las_3006_partidas_y_6062_lineas_de_mano_de_obra_son_validas():
    resultado = auditar_partidas()
    assert resultado.errores == []
    assert resultado.resumen["partidas"] == 3006
    assert resultado.resumen["partidas_con_mano_obra"] == 3006
    assert resultado.resumen["lineas_mano_obra"] == 6062
    assert resultado.resumen["recursos_fisicos"] == 388


def test_matriz_cubre_cada_recurso_fisico_en_cada_pais():
    resultado = auditar_matriz(388)
    assert resultado.errores == []
    for pais in ("CO", "PE", "MX", "EC", "PA", "SV", "CL", "AR"):
        assert resultado.resumen[pais]["total"] == 388
        assert resultado.resumen[pais].get("pendiente", 0) == 0
        assert resultado.resumen[pais]["con_referencia"] == 388


def test_matriz_distingue_observacion_directa_de_referencia_derivada():
    ruta = "basedatos_partidas/salida/precios_recursos_latam.csv"
    with open(ruta, encoding="utf-8-sig", newline="") as fh:
        filas = list(csv.DictReader(fh, delimiter=";"))

    def fila(codigo, pais):
        return next(
            f for f in filas
            if f["codigo_recurso"] == codigo and f["pais_codigo"] == pais
        )

    # 59.125 COP/saco / 25 kg = 2.365 COP/kg. El generador anterior dividía
    # dos veces y publicaba 138 COP/kg (25 veces por debajo del rango alto).
    adhesivo = fila("MT-ADH-C2TE", "CO")
    assert float(adhesivo["precio_referencia"]) == 2365
    assert float(adhesivo["precio_min"]) <= 2365 <= float(adhesivo["precio_max"])

    # La ronda 3 no aporta observación individual mexicana para estas
    # familias: deben tener referencia nacional, pero etiquetada como derivada.
    pvc_mx = fila("MT-PLO-PVC4", "MX")
    cable_mx = fila("MT-ELE-CABLE", "MX")
    assert pvc_mx["confianza"] == "derivado"
    assert cable_mx["confianza"] == "derivado"
    assert float(pvc_mx["precio_referencia"]) > 0
    assert pvc_mx["fuente"] == "docs/METODOLOGIA_PRECIOS_REFERENCIA_LATAM.md"

    # Los compuestos no existen como recursos físicos en la aplicación.
    codigos = {f["codigo_recurso"] for f in filas}
    assert "MT-MOR-PEGA" not in codigos
    assert "MT-MOR-FRISO" not in codigos


def test_sql_de_carga_supabase_es_completo_idempotente_y_acotado():
    from tools.generar_sql_precios_latam import SALIDA, generar

    filas, codigos = generar()
    sql = Path(SALIDA).read_text(encoding="utf-8")
    # 388 recursos × 8 países (CO, PE, MX, EC, PA, SV, CL, AR) = 3104 referencias
    assert (filas, codigos) == (3104, 388)
    assert "public.alembic_version = a4c8e2f7b1d6" in sql
    assert f"v_filas <> {filas} OR v_codigos <> 388" in sql or f"v_filas <> {filas}" in sql
    assert "p.organizacion_id IS NULL" in sql
    assert "p.pais_codigo = s.pais_codigo" in sql
    # Debe incluir los 8 países
    for pais in ("CO", "PE", "MX", "EC", "PA", "SV", "CL", "AR"):
        assert pais in sql
    assert "DELETE FROM public.precios_recursos_mercado" in sql
    assert "INSERT INTO public.precios_recursos_mercado" in sql
    assert "COMMIT;" in sql
