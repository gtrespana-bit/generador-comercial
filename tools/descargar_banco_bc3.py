#!/usr/bin/env python3
"""Descarga una base de precios BC3 oficial y deja el archivo listo para cruzar.

La descarga necesita red abierta (el sandbox de auditoría solo permite GitHub y
PyPI), así que este comando está pensado para ejecutarse en local o en CI. El
archivo se guarda en ``bases_precios/``, que está en .gitignore: son decenas de
MB y la licencia es de la fuente.

Origen oficial (Junta de Extremadura, edición 2026):

    https://www.juntaex.es/w/base-precios-construccion-2026
    -> "Base de precios de la construcción de Extremadura 2026 en formato bc3"

Uso:
    python3 tools/descargar_banco_bc3.py                       # Extremadura 2026
    python3 tools/descargar_banco_bc3.py --cruzar              # y cruza con el catálogo
    python3 tools/descargar_banco_bc3.py --url <otra base> --destino bases_precios/x.bc3
"""
from __future__ import annotations

import argparse
import hashlib
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESTINO = ROOT / "bases_precios/BCEXTGREM_26_v1.bc3"
EXTREMADURA_2026 = ("https://www.juntaex.es/documents/77055/621768/BCEXTGREM_26_v1.bc3/"
                    "8066c810-a694-eeed-c456-a64abca3cc2e?t=1782217730923")
CABECERAS = (b"~V|", b"\xef\xbb\xbf~V|")


def comprobar_bc3(ruta: Path) -> str:
    """Valida que el archivo es un FIEBDC-3 y devuelve su sha256."""
    datos = ruta.read_bytes()
    if not datos.startswith(CABECERAS):
        raise ValueError(f"{ruta.name} no empieza por una cabecera ~V| de FIEBDC-3")
    if b"~C|" not in datos:
        raise ValueError(f"{ruta.name} no contiene registros de concepto (~C|)")
    return hashlib.sha256(datos).hexdigest()


def descargar(url: str, destino: Path, tiempo: int = 120) -> Path:
    destino.parent.mkdir(parents=True, exist_ok=True)
    peticion = urllib.request.Request(url, headers={"User-Agent": "auditoria-precios/1.0"})
    with urllib.request.urlopen(peticion, timeout=tiempo) as respuesta, \
            destino.open("wb") as archivo:
        while trozo := respuesta.read(1 << 20):
            archivo.write(trozo)
    return destino


def relativa(ruta: Path) -> str:
    """Ruta legible aunque el archivo esté fuera del repositorio (pruebas, /tmp)."""
    try:
        return str(ruta.relative_to(ROOT))
    except ValueError:
        return str(ruta)


def main() -> int:
    analizador = argparse.ArgumentParser(description=__doc__,
                                        formatter_class=argparse.RawDescriptionHelpFormatter)
    analizador.add_argument("--url", default=EXTREMADURA_2026)
    analizador.add_argument("--destino", type=Path, default=DESTINO)
    analizador.add_argument("--cruzar", action="store_true",
                            help="lanza tools/cruzar_precios_bc3.py al terminar")
    argumentos = analizador.parse_args()

    if argumentos.destino.exists():
        print(f"Ya existe {relativa(argumentos.destino)}; no se vuelve a descargar")
    else:
        try:
            descargar(argumentos.url, argumentos.destino)
        except Exception as error:  # red cerrada o URL caída
            print(f"No se pudo descargar: {error}", file=sys.stderr)
            print("Descarga el BC3 a mano desde la web oficial y guárdalo en "
                  f"{relativa(argumentos.destino)}", file=sys.stderr)
            return 1
    sha = comprobar_bc3(argumentos.destino)
    tamano = argumentos.destino.stat().st_size / 1e6
    print(f"{relativa(argumentos.destino)}: {tamano:.1f} MB, sha256={sha}")
    if argumentos.cruzar:
        sys.path.insert(0, str(ROOT / "tools"))
        from cruzar_precios_bc3 import main as cruzar  # noqa: PLC0415
        sys.argv = ["cruzar_precios_bc3.py", "--fuente",
                    f"Extremadura 2026|Extremadura|https://www.juntaex.es/w/"
                    f"base-precios-construccion-2026|{argumentos.destino}",
                    "--salida", str(ROOT / "bases_precios/candidatos_extremadura.csv")]
        return cruzar()
    print("Siguiente paso: python3 tools/cruzar_precios_bc3.py --fuente "
          f"'Extremadura 2026|Extremadura|<url>|{argumentos.destino}' "
          "--salida bases_precios/candidatos_extremadura.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
