#!/usr/bin/env python3
"""Comprueba que las plantillas traducidas no rompen el render.

Para cada plantilla ``X_en.html`` se compara con su original ``X.html``:

1. Ambas deben parsear (sintaxis Jinja válida).
2. Deben incluir/extender los mismos parciales, traduciendo el sufijo ``_en``
   cuando exista (``base.html`` -> ``base_en.html``).
3. Deben usar las mismas variables de primer nivel. Una variable que exista en
   español y falte en inglés (o al revés) casi siempre es un ``extends``
   olvidado, un bucle mal cerrado o un cambio de nombre al traducir.
4. Deben declarar los mismos bloques.

Los filtros y globales que registra la aplicación se sustituyen por dobles:
lo que se quiere detectar aquí son diferencias estructurales entre los dos
idiomas, no errores de datos.

Uso:
    python tools/chequear_plantillas_en.py
"""
from __future__ import annotations

import glob
import os
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, meta

TEMPLATES = Path(__file__).resolve().parent.parent / "app" / "templates"

# Variables que inyecta la aplicación en todas las plantillas.
GLOBALES = {
    "request",
    "product_name",
    "database_is_sqlite",
    "hay_prueba_gratuita",
    "dias_de_prueba",
    "catalogo",
    "url_for",
    "get_flashed_messages",
    "t",
    "normalizar_idioma",
}


class _FiltrosComodin(dict):
    """Cualquier filtro desconocido devuelve su entrada sin tocarla.

    ``dict.get`` no pasa por ``__missing__`` y el generador de código de Jinja
    lo usa para validar el nombre del filtro, así que hay que reescribirlo.
    """

    def _comodin(self):  # noqa: ANN202
        return lambda valor, *args, **kwargs: valor

    def __missing__(self, clave):  # noqa: ANN001, ANN204
        return self._comodin()

    def get(self, clave, defecto=None):  # noqa: ANN001, ANN201
        if dict.__contains__(self, clave):
            return dict.__getitem__(self, clave)
        return defecto if defecto is not None else self._comodin()

    def __contains__(self, clave):  # noqa: ANN001, ANN204
        return True


def _entorno() -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES)),
        extensions=[],
    )
    env.filters = _FiltrosComodin(env.filters)
    env.globals.setdefault("product_name", "CotizaT")
    env.globals.setdefault("database_is_sqlite", True)
    env.globals.setdefault("t", lambda clave, *a, **k: clave)
    env.globals.setdefault("normalizar_idioma", lambda valor: "es")
    return env


def _equivalente(referencia: str | None) -> str | None:
    """Traduce una referencia a plantilla a su equivalente en inglés."""
    if not referencia:
        return None
    if referencia.endswith(".html") and not referencia.endswith("_en.html"):
        candidato = referencia[: -len(".html")] + "_en.html"
        if (TEMPLATES / candidato).is_file():
            return candidato
    return referencia


def _referencias(env: Environment, nombre: str) -> set[str]:
    ast = env.parse((TEMPLATES / nombre).read_text(encoding="utf-8"))
    return {_equivalente(r) for r in meta.find_referenced_templates(ast) if r}


def _variables(env: Environment, nombre: str) -> set[str]:
    ast = env.parse((TEMPLATES / nombre).read_text(encoding="utf-8"))
    return {v for v in meta.find_undeclared_variables(ast) if v not in GLOBALES}


# Diferencias asumidas: la landing en inglés es una pieza propia (no usa el
# copy por país del ``seo``) y los hubs/seo en inglés no enlazan guías que
# todavía están en español.
DIFERENCIAS_ACEPTADAS: dict[str, set[str]] = {
    "landing.html": {"jsonld_bloques", "seo"},
    "seo_guia.html": {"guias"},
    "seo_hub.html": {"guias"},
}


def main() -> int:
    env = _entorno()
    pares = []
    for ruta in sorted(glob.glob(str(TEMPLATES / "**" / "*_en.html"), recursive=True)):
        rel = os.path.relpath(ruta, TEMPLATES)
        original = rel[: -len("_en.html")] + ".html"
        if (TEMPLATES / original).is_file():
            pares.append((original, rel))

    problemas = 0
    for original, traducida in pares:
        try:
            env.parse((TEMPLATES / traducida).read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            print(f"✗ {traducida}: sintaxis inválida -> {exc}")
            problemas += 1
            continue

        ref_es = _referencias(env, original)
        ref_en = _referencias(env, traducida)
        if ref_es != ref_en:
            print(
                f"✗ {traducida}: parciales distintos\n"
                f"    faltan={sorted(ref_es - ref_en)}\n"
                f"    sobran={sorted(ref_en - ref_es)}"
            )
            problemas += 1

        vars_es = _variables(env, original)
        vars_en = _variables(env, traducida)
        aceptadas = DIFERENCIAS_ACEPTADAS.get(original, set())
        faltan, sobran = (vars_es - vars_en) - aceptadas, vars_en - vars_es
        if faltan or sobran:
            print(
                f"✗ {traducida}: variables distintas\n"
                f"    faltan={sorted(faltan)}\n"
                f"    sobran={sorted(sobran)}"
            )
            problemas += 1

        try:
            bloques_es = set(env.get_template(original).blocks)
            bloques_en = set(env.get_template(traducida).blocks)
            if bloques_es != bloques_en:
                print(
                    f"✗ {traducida}: bloques distintos\n"
                    f"    faltan={sorted(bloques_es - bloques_en)}\n"
                    f"    sobran={sorted(bloques_en - bloques_es)}"
                )
                problemas += 1
        except Exception:  # noqa: BLE001, S110
            # los parciales sin padre resolvible no declaran bloques
            pass

    print(f"\n{len(pares)} pares revisados · {problemas} problemas")
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main())
