"""Todo módulo de ``app/`` debe importarse sin errores (E5-013).

Motivo (incidente del 05/11/2026): el PR 188 añadió en
``app/panel_arquitectura.py`` la línea ``ROLES_TODOS = ROLES_OPERADOR`` sin
importar ``ROLES_OPERADOR``. Como la asignación está en el ámbito del módulo,
el ``NameError`` saltaba al importar. Ese módulo lo importa ``app.routers.admin``,
que a su vez importa ``app.main``: la aplicación entera no podía arrancar y
**todas** las rutas —incluidas ``/healthz`` y la portada pública— devolvían
``500 FUNCTION_INVOCATION_FAILED`` en Vercel. ``compileall`` no lo detecta
(es un error de ejecución, no de sintaxis) y la suite completa lo detectaba,
pero su fallo se pasó por alto antes de fusionar.

Esta prueba es la red mínima: recorre todos los módulos del paquete ``app`` y
los importa uno a uno, de modo que cualquier error de ámbito de módulo
(nombre no definido, import roto, ``raise`` en el cuerpo) falla aquí con el
nombre del módulo culpable en lugar de tumbar el despliegue.
"""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest

APP_DIR = Path(__file__).resolve().parents[1] / "app"


def _modulos() -> list[str]:
    modulos: list[str] = []
    for ruta in sorted(APP_DIR.rglob("*.py")):
        relativa = ruta.relative_to(APP_DIR.parent)
        partes = list(relativa.with_suffix("").parts)
        if partes[-1] == "__init__":
            partes.pop()
        modulos.append(".".join(partes))
    return modulos


@pytest.mark.parametrize("modulo", _modulos(), ids=_modulos())
def test_modulo_importable(modulo: str) -> None:
    """Importar el módulo no debe lanzar ninguna excepción."""
    importlib.import_module(modulo)


def test_se_importa_todo_el_paquete() -> None:
    """Control de cordura: el recorrido encuentra módulos de verdad."""
    modulos = _modulos()
    assert "app.main" in modulos
    assert "app.panel_arquitectura" in modulos
    assert len(modulos) > 100
