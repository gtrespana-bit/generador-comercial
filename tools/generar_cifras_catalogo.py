"""Genera ``basedatos_partidas/datos/cifras_catalogo.json`` (cifras precalculadas).

La landing lee las cifras del catálogo (partidas, recursos, líneas de
precio…) en cada proceso. Calcularlas en vivo recorre miles de ficheros de
descompuestos en el primer render de cada instancia, así que se precalculan
aquí y viajan con el código: en producción solo se lee un JSON pequeño.

Hay que volver a ejecutarlo cuando cambie el catálogo
(``basedatos_partidas/datos``) o las recetas demo (``app/seeds.py`` →
``RECETAS_DEMO``, de donde salen los packs). El test
``test_cifras_catalogo_sin_deriva`` (tests/test_landing_ejemplo.py) caza
el olvido en CI comparando el JSON con el cálculo en vivo.

Uso:
    python tools/generar_cifras_catalogo.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

# Solo se importa la función de cálculo, pero importar módulos de la app crea
# el engine de BD: se aísla para no tocar nunca la del desarrollador ni la
# de producción (mismo patrón que tools/verificar_plantillas.py).
os.environ.pop("DATABASE_URL", None)
os.environ["COTIZAT_DB"] = str(
    Path(tempfile.mkdtemp(prefix="cotizat-cifras-")) / "generacion.db"
)

DESTINO = REPO / "basedatos_partidas" / "datos" / "cifras_catalogo.json"


def main() -> int:
    from app.routers.common import _calcular_cifras_catalogo

    cifras = _calcular_cifras_catalogo()
    DESTINO.write_text(
        json.dumps(cifras, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Escrito {DESTINO.relative_to(REPO)}")
    print(
        f"  {cifras['partidas_txt']} partidas · {cifras['recursos_txt']} recursos · "
        f"{cifras['lineas_precio_txt']} líneas de precio · "
        f"{cifras['lineas_descomp_txt']} líneas de descompuesto · "
        f"{cifras['packs']} packs ({cifras['packs_partidas']} partidas)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
