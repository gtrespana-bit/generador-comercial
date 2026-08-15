"""Regenera el «PDF de ejemplo» de la landing (E1-052).

Genera el presupuesto de muestra comercial (datos ficticios, ver
`app/services/presupuesto_muestra.py`) y escribe el PDF en
`app/static/pdf/presupuesto-ejemplo.pdf`, que enlaza `/conocer`.

Uso:

    python tools/generar_presupuesto_muestra.py

El archivo resultante se versiona; la suite (`tests/test_presupuesto_muestra.py`)
verifica que el contenido generado siga siendo un PDF válido sin datos reales.
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "app" / "static" / "pdf" / "presupuesto-ejemplo.pdf"


def main() -> int:
    if str(RAIZ) not in sys.path:
        sys.path.insert(0, str(RAIZ))
    from app.services.presupuesto_muestra import construir

    datos = construir()
    if not datos.startswith(b"%PDF"):
        print("Error: el contenido generado no es un PDF válido.", file=sys.stderr)
        return 1

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_bytes(datos)
    print(f"Presupuesto de muestra escrito en {DESTINO.relative_to(RAIZ)} ({len(datos)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
