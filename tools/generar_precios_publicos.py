"""Genera ``basedatos_partidas/datos/precios_publicos.json`` (Fase 5).

Las páginas públicas de precios leen sus índices (partidas publicables
por país con su descompuesto ya calculado y traducido) en cada proceso.
Calcularlos en vivo cuesta segundos por país —la capa de variante del
inglés pasa por miles de cadenas— y en una instancia fría de Vercel la
primera petición pagaba los cinco países sin llegar a calentar (las
páginas salieron con 404 por timeout el primer día). Se precalculan
aquí y viajan con el código: en producción solo se lee un JSON.

Hay que volver a ejecutarlo cuando cambien el catálogo
(``basedatos_partidas/datos``), los CSV de precios
(``basedatos_partidas/salida/precios_recursos_*.csv``), las tablas de
traducción o los países encendidos en
``services.precios_publicos.PAISES_PRECIOS_PUBLICOS``. El test
``test_el_artefacto_precalculado_coincide_con_el_calculo_en_vivo``
(tests/test_precios_publicos.py) caza el olvido en CI.

Uso:
    python tools/generar_precios_publicos.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

# Importar módulos de la app puede crear el engine de BD: se aísla para
# no tocar nunca la del desarrollador ni la de producción (mismo patrón
# que tools/generar_cifras_catalogo.py).
os.environ.pop("DATABASE_URL", None)
os.environ["COTIZAT_DB"] = str(
    Path(tempfile.mkdtemp(prefix="cotizat-precios-")) / "generacion.db"
)

DESTINO = REPO / "basedatos_partidas" / "datos" / "precios_publicos.json"


def main() -> int:
    from app.services.precios_publicos import generar_artefacto

    artefacto = generar_artefacto()
    artefacto["_generado"] = datetime.now(timezone.utc).isoformat()
    # Sin indentar: es un artefacto generado de varios MB, no se edita a
    # mano y compacto se parsea más rápido en frío.
    DESTINO.write_text(
        json.dumps(artefacto, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    for cc, indice in sorted(artefacto["paises"].items()):
        print(f"{cc}: {indice['total_partidas']} partidas, {indice['total_apartados']} apartados")
    print(f"Escrito {DESTINO} ({DESTINO.stat().st_size / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
