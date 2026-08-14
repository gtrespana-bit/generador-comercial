"""Verifica que todas las plantillas Jinja del proyecto se parsean sin errores.

Usa el entorno Jinja real de la aplicación (mismos delimitadores, extensiones y
opciones que ``app.main``), de modo que un error de sintaxis en una plantilla se
detecte en integración continua y no al abrir la pantalla en producción.

El parseo no renderiza: no necesita base de datos, sesión ni contexto. Detecta
bloques sin cerrar, ``{% endfor %}`` sobrantes, expresiones mal formadas y
etiquetas desconocidas.

Uso:
    python tools/verificar_plantillas.py
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

# La aplicación se importa solo para reutilizar su entorno Jinja. Se aísla la
# base de datos para no tocar nunca la del desarrollador ni la de producción.
os.environ.pop("DATABASE_URL", None)
os.environ["COTIZAT_DB"] = str(Path(tempfile.mkdtemp(prefix="cotizat-plantillas-")) / "verificacion.db")

PLANTILLAS = REPO / "app" / "templates"


def _entorno():
    """Devuelve el entorno Jinja real de la aplicación."""
    from app.main import TEMPLATES

    return TEMPLATES.env


def main() -> int:
    if not PLANTILLAS.is_dir():
        print(f"No existe el directorio de plantillas: {PLANTILLAS}")
        return 1

    entorno = _entorno()
    archivos = sorted(PLANTILLAS.rglob("*.html"))
    if not archivos:
        print("No se encontró ninguna plantilla que verificar.")
        return 1

    errores: list[str] = []
    for archivo in archivos:
        relativo = archivo.relative_to(REPO)
        try:
            entorno.parse(
                archivo.read_text(encoding="utf-8"),
                name=str(archivo.relative_to(PLANTILLAS)),
                filename=str(archivo),
            )
        except Exception as exc:  # noqa: BLE001 - se reporta cualquier fallo de parseo
            errores.append(f"{relativo}: {exc}")

    for error in errores:
        print(f"ERROR {error}")

    if errores:
        print(f"\n{len(errores)} plantilla(s) con errores de {len(archivos)} revisadas.")
        return 1

    print(f"{len(archivos)} plantillas Jinja parseadas correctamente ✅")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
