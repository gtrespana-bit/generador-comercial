"""Los selectores ES/EN conservan la moneda al abrir y enviar formularios."""
import re
from pathlib import Path
from types import SimpleNamespace

import pytest
from jinja2 import Environment


@pytest.mark.parametrize("plantilla", [
    "settings.html", "settings_en.html", "budgets/form.html", "budgets/form_en.html",
])
@pytest.mark.parametrize("moneda", ["GBP", "AUD", "CAD"])
def test_selector_ofrece_y_selecciona_moneda(plantilla, moneda):
    texto = (Path(__file__).resolve().parents[1] / "app/templates" / plantilla).read_text()
    nombre = "moneda_default" if plantilla.startswith("settings") else "moneda"
    select = re.search(r'<select\b[^>]*name="' + nombre + r'"[^>]*>.*?</select>', texto, re.S)
    assert select
    for presupuesto in (None, SimpleNamespace(moneda=moneda)):
        html = Environment().from_string(select.group()).render(
            cfg=SimpleNamespace(moneda_default=moneda), presupuesto=presupuesto,
        )
        opciones = re.findall(r'<option\s+value="([^"]+)"([^>]*)>', html)
        assert [codigo for codigo, attrs in opciones if "selected" in attrs] == [moneda]
        for codigo in ("GBP", "AUD", "CAD"):
            assert [c for c, _ in opciones].count(codigo) == 1
