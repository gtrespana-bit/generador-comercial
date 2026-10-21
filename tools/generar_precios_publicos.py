"""Genera ``basedatos_partidas/datos/precios_publicos/{PAIS}.json`` (Fase 5).

Las páginas públicas de precios leen sus índices (partidas publicables
por país con su descompuesto ya calculado y traducido) en cada proceso.
Calcularlos en vivo cuesta segundos por país —la capa de variante del
inglés pasa por miles de cadenas— y en una instancia fría de Vercel la
primera petición pagaba los cinco países sin llegar a calentar (las
páginas salieron con 404 por timeout el primer día). Se precalculan
aquí y viajan con el código: en producción solo se lee un JSON.

Un fichero por país (~4 MB): el artefacto único de los cinco primeros
mercados ya pesaba 17,7 MB y con los 22 mercados habría rondado los
90 MB. Por país, el proceso solo parsea los países que sirve, git
solo versiona el país que cambia y un país que se apague pierde su
fichero en la siguiente generación (sin zombis).

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

DESTINO_DIR = REPO / "basedatos_partidas" / "datos" / "precios_publicos"


def main() -> int:
    from app.services.precios_publicos import generar_artefacto

    artefacto = generar_artefacto()
    DESTINO_DIR.mkdir(parents=True, exist_ok=True)
    escritos = set()
    for cc, indice in sorted(artefacto["paises"].items()):
        destino = DESTINO_DIR / f"{cc}.json"
        # Sin indentar: es un artefacto generado de varios MB, no se
        # edita a mano y compacto se parsea más rápido en frío.
        destino.write_text(
            json.dumps(indice, ensure_ascii=False, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        escritos.add(destino.name)
        print(
            f"{cc}: {indice['total_partidas']} partidas, "
            f"{indice['total_apartados']} apartados "
            f"({destino.stat().st_size / 1e6:.1f} MB)"
        )
    for viejo in sorted(DESTINO_DIR.glob("*.json")):
        if viejo.name not in escritos:
            viejo.unlink()
            print(f"Retirado {viejo.name} (país ya no encendido)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
