"""Fechas como texto para las guías (Fase 2).

Las notas de las tablas de precios derivan su fecha de ``fecha_consulta``:
estas pruebas fijan cómo se resume un conjunto de fechas en una frase
(«en agosto de 2026», «entre junio y septiembre de 2026»…) y que nunca se
inventa una fecha cuando los datos no la traen.
"""
from __future__ import annotations

from app.fechas_texto import consulta_es, mes_anio_es


def test_mes_anio_desde_iso_y_desde_declaracion_con_texto():
    assert mes_anio_es("2026-08-25") == "agosto de 2026"
    assert mes_anio_es("2026-08") == "agosto de 2026"
    # Así viene la clave _revision de recursos.json (cuadro base VE).
    assert mes_anio_es("2026-08 · segunda ronda de contraste") == "agosto de 2026"


def test_mes_anio_vacio_si_no_se_entiende():
    assert mes_anio_es("") == ""
    assert mes_anio_es(None) == ""
    assert mes_anio_es("sin fecha") == ""
    assert mes_anio_es("2026-13-01") == ""


def test_consulta_un_solo_mes():
    assert consulta_es(["2026-09-08", "2026-09-08"]) == "en septiembre de 2026"


def test_consulta_rango_dentro_del_anio_sin_orden_ni_duplicados():
    assert consulta_es(["2026-09-30", "2026-06-01", "2026-09-02"]) == (
        "entre junio y septiembre de 2026"
    )


def test_consulta_rango_que_cruza_el_anio():
    assert consulta_es(["2025-11-15", "2026-02-03"]) == (
        "entre noviembre de 2025 y febrero de 2026"
    )


def test_consulta_vacia_sin_fechas_entendibles():
    assert consulta_es([]) == ""
    assert consulta_es(["", None, "n/a"]) == ""
