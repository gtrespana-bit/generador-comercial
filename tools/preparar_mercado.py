#!/usr/bin/env python3
"""Prepara la localización de un mercado, apartado a apartado.

El catálogo comparte el descompuesto entre los 22 mercados hispanos: la ficha
de México es la española con precios en MXN. Medido, el 98 % del vocabulario es
idéntico (`app/services/localizacion.py`), y eso es lo que se anunció el
22/10/2026 y hundió el sitio dos días después.

La salida es gradual y ficha a ficha: se escribe el texto de los apartados que
tienen demanda en el país, y **solo esas fichas** se anuncian a Google
(`MERCADOS_FICHAS_INDEXABLES` sigue mandando para los mercados completos).

Este comando hace el trabajo mecánico:

* crea ``basedatos_partidas/datos/localizado/<CC>.json`` con una entrada por
  partida del apartado elegido, con el texto español como referencia en
  ``_origen`` (no cuenta: el registro solo valida título y descripción propios);
* conserva lo ya escrito al volver a ejecutarlo (nunca pisa texto);
* informa de cuánto falta.

Uso:
  python tools/preparar_mercado.py --mercado MX --apartados            # lista
  python tools/preparar_mercado.py --mercado MX --apartados 03-04-05,07-01-02
  python tools/preparar_mercado.py --mercado MX --apartados todos
  python tools/preparar_mercado.py --mercado MX --estado

Después de escribir el texto:
  python tools/radar_activacion_mercados.py --mercado MX
  python tools/generar_precios_publicos.py       # si el mercado está encendido

El registro se valida solo: una entrada sin título, con descripción corta o con
la descripción española copiada no enciende nada. Es la guardia, no una promesa.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from app.paises import PAISES  # noqa: E402
from app.services import precios_publicos as pp  # noqa: E402

DESTINO = RAIZ / "basedatos_partidas" / "datos" / "localizado"


def _ruta(cc: str) -> Path:
    return DESTINO / f"{cc}.json"


def _leer(cc: str) -> dict:
    ruta = _ruta(cc)
    if not ruta.exists():
        return {}
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except ValueError:
        raise SystemExit(f"{ruta} no es JSON válido: corrígelo antes de seguir")
    return datos if isinstance(datos, dict) else {}


def _escribir(cc: str, datos: dict) -> None:
    DESTINO.mkdir(parents=True, exist_ok=True)
    datos["_comentario"] = (
        "Texto propio del mercado. Solo se anuncia a buscadores la partida con "
        "titulo y descripcion validos (>=120 caracteres) y distintos del "
        "español. Lo que no cumpla eso es un borrador: no enciende nada."
    )
    datos["_mercado"] = cc
    datos.setdefault("_revision", "")
    partidas = datos.get("partidas") or {}
    datos["partidas"] = {
        codigo: partidas[codigo] for codigo in sorted(partidas)
    }
    _ruta(cc).write_text(
        json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _apartados(cc: str) -> list[dict]:
    indice = pp._indice(cc) or {}
    salida = []
    for slug, ficha in sorted((indice.get("apartados") or {}).items()):
        salida.append(
            {
                "slug": slug,
                "clave": ficha.get("clave") or "",
                "nombre": ficha.get("nombre") or "",
                "partidas": len(ficha.get("partidas") or []),
            }
        )
    return salida


def _listar(cc: str) -> str:
    indice = pp._indice(cc) or {}
    lineas = [f"Apartados de {cc} ({indice.get('total_apartados', 0)}):", ""]
    for apartado in _apartados(cc):
        lineas.append(
            f"  {apartado['clave']:<12} {apartado['partidas']:>3} partidas  "
            f"{apartado['nombre']}"
        )
    lineas += [
        "",
        "Elige los de más demanda en el país y pásalos por --apartados.",
    ]
    return "\n".join(lineas)


def _scaffold(cc: str, claves: list[str], limite: int) -> str:
    """Crea (sin pisar) las entradas de las partidas de esos apartados."""
    indice = pp._indice(cc) or {}
    datos = _leer(cc)
    partidas = datos.get("partidas") or {}
    creadas = 0
    for clave in claves:
        slug_ap = (indice.get("apartados_por_clave") or {}).get(clave)
        if slug_ap is None:
            # La clave puede venir como slug del apartado.
            slug_ap = clave if clave in (indice.get("apartados") or {}) else None
        if slug_ap is None:
            raise SystemExit(f"Apartado desconocido en {cc}: {clave}")
        apartado = indice["apartados"][slug_ap]
        for resumen in (apartado.get("partidas") or [])[: limite or None]:
            ficha = indice["partidas"].get((slug_ap, resumen["slug"])) or {}
            codigo = ficha.get("codigo") or ""
            if not codigo or codigo in partidas:
                continue
            partidas[codigo] = {
                "titulo": "",
                "descripcion": "",
                "recursos": {},
                "revisado": "",
                "_origen": {
                    "titulo": ficha.get("titulo") or "",
                    "descripcion": ficha.get("descripcion") or "",
                    "apartado": apartado.get("nombre") or "",
                },
            }
            creadas += 1
    datos["partidas"] = partidas
    _escribir(cc, datos)
    return f"{creadas} entradas nuevas en {_ruta(cc)} ({len(partidas)} en total)"


def _estado(cc: str) -> str:
    indice = pp._indice(cc) or {}
    datos = _leer(cc)
    partidas = datos.get("partidas") or {}
    validas = set(pp._localizado(cc).keys())
    publicadas = set((indice.get("por_codigo") or {}).keys())
    total = indice.get("total_partidas", 0)
    lineas = [
        f"Mercado {cc}: {total} fichas publicadas",
        f"  con texto propio válido: {len(validas & publicadas)}",
        f"  borradores en el registro: {len(set(partidas) - validas)}",
        f"  sin tocar: {max(0, total - len(partidas))}",
        f"  encendido completo (MERCADOS_FICHAS_INDEXABLES): "
        f"{'sí' if pp.ficha_indexable(cc) else 'no'}",
    ]
    por_apartado = []
    for apartado in _apartados(cc):
        slug_ap = apartado["slug"]
        codigos = [
            (indice["partidas"].get((slug_ap, r["slug"])) or {}).get("codigo")
            for r in indice["apartados"][slug_ap]["partidas"]
        ]
        propias = sum(1 for c in codigos if c in validas)
        if propias:
            por_apartado.append((propias, apartado["nombre"], apartado["partidas"]))
    if por_apartado:
        lineas.append("  apartados con texto propio (necesitan 3 para anunciarse):")
        for propias, nombre, total_ap in sorted(por_apartado, reverse=True):
            marca = "✓" if propias >= 3 else "·"
            lineas.append(f"    {marca} {propias}/{total_ap}  {nombre}")
    return "\n".join(lineas)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Prepara y vigila la localización del catálogo de un mercado.",
    )
    parser.add_argument("--mercado", required=True, help="código ISO: MX, CO, PE…")
    parser.add_argument(
        "--apartados",
        nargs="?",
        const="",
        default=None,
        help="claves separadas por comas, o 'todos'; sin valor, lista los disponibles",
    )
    parser.add_argument(
        "--limite",
        type=int,
        default=0,
        help="máximo de partidas por apartado (0 = todas)",
    )
    parser.add_argument(
        "--estado", action="store_true", help="informe de progreso del registro"
    )
    args = parser.parse_args(argv)

    cc = str(args.mercado or "").strip().upper()
    if cc not in PAISES:
        raise SystemExit(f"Mercado desconocido: {cc}")
    if pp._indice(cc) is None:
        raise SystemExit(f"{cc} no tiene catálogo público (ni matriz de precios)")

    if args.estado:
        print(_estado(cc))
        return 0
    if args.apartados is None:
        print(_listar(cc))
        return 0

    if args.apartados.strip().lower() == "todos":
        claves = [a["clave"] for a in _apartados(cc)]
    else:
        claves = [c.strip() for c in args.apartados.split(",") if c.strip()]
        if not claves:
            raise SystemExit("--apartados necesita al menos una clave")
    print(_scaffold(cc, claves, args.limite))
    print()
    print(_estado(cc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
