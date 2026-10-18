"""Regenera el «PDF de ejemplo» de la landing (E1-052).

Genera el presupuesto de muestra comercial (datos ficticios, ver
`app/services/presupuesto_muestra.py`) en los dos idiomas de la landing y
escribe los PDF en `app/static/pdf/`:

  · `presupuesto-ejemplo.pdf`    — enlazado desde `/conocer`
  · `presupuesto-ejemplo-en.pdf` — enlazado desde `/en/`

Los dos documentos muestran el mismo presupuesto: mismas mediciones, mismos
importes y mismo total. Cambia únicamente la redacción.

Uso:

    python tools/generar_presupuesto_muestra.py

El archivo resultante se versiona; la suite (`tests/test_presupuesto_muestra.py`)
verifica que el contenido generado siga siendo un PDF válido sin datos reales.
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DIR_PDF = RAIZ / "app" / "static" / "pdf"
SALIDAS = (
    ("es", "presupuesto-ejemplo.pdf"),
    ("en", "presupuesto-ejemplo-en.pdf"),
)


def main() -> int:
    if str(RAIZ) not in sys.path:
        sys.path.insert(0, str(RAIZ))
    from app.services.presupuesto_muestra import construir

    DIR_PDF.mkdir(parents=True, exist_ok=True)
    for idioma, nombre in SALIDAS:
        datos = construir(idioma)
        if not datos.startswith(b"%PDF"):
            print(f"Error: el PDF en {idioma!r} no es válido.", file=sys.stderr)
            return 1
        destino = DIR_PDF / nombre
        destino.write_bytes(datos)
        print(f"{destino.relative_to(RAIZ)} ({len(datos)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
