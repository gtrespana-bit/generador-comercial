"""La hora del panel se pinta en la zona del operador (Caracas, UTC−4).

Todo lo guardado es UTC. Antes, una venta de las 20:30 en Caracas salía en el
panel como «00:30» **del día siguiente**: un dato falso en la pantalla que se
usa para decidir. Estas pruebas fijan la conversión, el respaldo cuando la zona
está mal escrita y que ninguna plantilla del panel vuelva a pintar una hora en
UTC sin avisar.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from app import tiempo
from app.routers.common import TEMPLATES

RAIZ = Path(__file__).resolve().parents[1]
ADMIN = RAIZ / "app" / "templates" / "admin"


@pytest.fixture(autouse=True)
def zona_por_defecto(monkeypatch):
    """Cada prueba arranca con la zona de la empresa, no con la del entorno."""
    monkeypatch.delenv("COTIZAT_ZONA_HORARIA", raising=False)


def test_una_venta_de_la_noche_no_se_va_al_dia_siguiente():
    instante = datetime(2026, 11, 7, 0, 30)  # UTC: 00:30 del día 7
    assert tiempo.hora_local(instante, "%d/%m/%Y %H:%M") == "06/11/2026 20:30"


def test_el_instante_guardado_se_interpreta_como_utc():
    naive = datetime(2026, 3, 1, 12, 0)
    aware = datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc)
    assert tiempo.a_local(naive) == tiempo.a_local(aware)
    assert tiempo.a_local(naive).utcoffset().total_seconds() == -4 * 3600


def test_un_vencimiento_es_un_dia_del_calendario_y_no_se_desplaza():
    vence = date(2026, 11, 7)
    assert tiempo.a_local(vence) == vence
    assert tiempo.hora_local(vence, "%d/%m/%Y") == "07/11/2026"


def test_lo_que_no_es_fecha_no_revienta_la_plantilla():
    assert tiempo.hora_local(None) == "—"
    assert tiempo.hora_local("sin fecha") == "sin fecha"
    assert tiempo.hora_local(0) == "0"


def test_si_la_zona_esta_mal_escrita_se_cae_a_utc(monkeypatch):
    monkeypatch.setenv("COTIZAT_ZONA_HORARIA", "Marte/Olympus")
    assert tiempo.zona().key == "UTC"
    instante = datetime(2026, 11, 7, 0, 30)
    assert tiempo.hora_local(instante, "%H:%M") == "00:30"


def test_la_zona_se_puede_cambiar_sin_desplegar(monkeypatch):
    monkeypatch.setenv("COTIZAT_ZONA_HORARIA", "America/Bogota")
    assert tiempo.nombre_zona() == "America/Bogota"
    assert tiempo.hora_local(datetime(2026, 11, 7, 0, 30), "%d/%m %H:%M") == "06/11 19:30"
    assert "Bogotá" in tiempo.etiqueta_zona()


def test_la_etiqueta_dice_el_desfase_para_que_nadie_tenga_que_adivinarlo():
    etiqueta = tiempo.etiqueta_zona()
    assert "Caracas" in etiqueta
    assert "UTC−04:00" in etiqueta


def test_el_dia_del_operador_no_es_el_dia_utc(monkeypatch):
    """A las 02:00 UTC en Caracas todavía es ayer: el panel debe decir ayer."""
    monkeypatch.setenv("COTIZAT_ZONA_HORARIA", "Pacific/Midway")  # UTC−11
    assert tiempo.hoy_local() <= datetime.now(timezone.utc).date()
    assert tiempo.hoy_local() == tiempo.a_local(datetime.now(timezone.utc)).date()


def test_el_filtro_utc_deja_el_instante_exacto_para_el_title():
    assert tiempo.utc_iso(datetime(2026, 11, 7, 0, 30)) == "2026-11-07T00:30:00Z"


def test_los_filtros_estan_registrados_en_el_entorno_de_plantillas():
    filtros = TEMPLATES.env.filters
    assert {"local", "local_fecha", "utc"} <= set(filtros)
    assert "zona_horaria" in TEMPLATES.env.globals


def test_la_plantilla_pinta_la_hora_del_operador():
    plantilla = TEMPLATES.env.from_string(
        "{{ cuando|local('%d/%m/%Y %H:%M') }} · {{ cuando|utc }} · {{ zona_horaria() }}"
    )
    salida = plantilla.render(cuando=datetime(2026, 11, 7, 0, 30))
    assert "06/11/2026 20:30" in salida
    assert "2026-11-07T00:30:00Z" in salida
    assert "Caracas" in salida


def test_ninguna_plantilla_del_panel_pinta_una_hora_sin_zona():
    """Cerrojo: si alguien vuelve a escribir `x.strftime('%H:%M')`, falla aquí."""
    culpables = []
    for ruta in sorted(ADMIN.rglob("*.html")):
        for numero, linea in enumerate(ruta.read_text(encoding="utf-8").splitlines(), 1):
            if "strftime" not in linea or "%H" not in linea:
                continue
            if "|local" in linea or "|utc" in linea:
                continue
            culpables.append(f"{ruta.relative_to(RAIZ)}:{numero}")
    assert not culpables, "fechas con hora sin convertir a la zona del operador: " + ", ".join(culpables)
