#!/usr/bin/env python3
"""Lee los CSV de Search Console y responde la pregunta que decide el plan.

Search Console no deja sacar conclusiones de una captura de pantalla. Esta
herramienta trabaja con los CSV que se descargan de **Rendimiento** y contesta
tres cosas concretas:

* **Canibalización**: una misma consulta con impresiones repartidas entre
  varias URLs del propio sitio. Es el patrón del proyecto —``/``, ``/es/``,
  ``/mx/``, ``/es/apu``… compitiendo por «software de presupuestos»— y explica
  una posición media de 44 sin necesidad de ninguna penalización.
* **Dónde está el techo**: páginas que ya reciben impresiones y están en la
  franja 8–25. Ahí subir puestos cambia clics de verdad; en la página 4 no hay
  nada que rascar.
* **Ruido**: consultas de marca (``cotizat``) frente a genéricas. Si las
  impresiones son casi todas de marca, no hay descubrimiento: el sitio no
  compite por las búsquedas que traen clientes nuevos.

Solo usa la biblioteca estándar. No se conecta a ninguna API ni pide
credenciales: los CSV se descargan a mano desde Search Console.

Cómo se exportan (Rendimiento → botón *Exportar* → CSV):

* una exportación con la pestaña **Consultas** → ``Consultas.csv``
* otra con la pestaña **Páginas** → ``Paginas.csv``
* la más útil, con las dos dimensiones (**Consultas** + **Páginas**)
  → ``ConsultasPaginas.csv``

Uso:
  python tools/analizar_gsc.py Consultas.csv Paginas.csv
  python tools/analizar_gsc.py --carpeta ~/gsc
  python tools/analizar_gsc.py Consultas.csv --marca cotizat --min-impresiones 50
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

#: Columnas tal como las nombra la exportación de Search Console, en español
#: e inglés. Se normalizan a: clave, clics, impresiones, posicion.
_ALIAS = {
    "top queries": "clave",
    "top pages": "clave",
    "consultas principales": "clave",
    "páginas principales": "clave",
    "paginas principales": "clave",
    "query": "clave",
    "page": "clave",
    "clics": "clics",
    "clicks": "clics",
    "impresiones": "impresiones",
    "impressions": "impresiones",
    "ctr": "ctr",
    "posición": "posicion",
    "posicion": "posicion",
    "position": "posicion",
}


def _normalizar(cabecera: list[str]) -> list[str]:
    return [_ALIAS.get(c.strip().lower().replace("\ufeff", ""), c) for c in cabecera]


def _numero(valor: str, entero: bool = False) -> float:
    """Convierte «1.234», «12,5 %» y «1,234.5» sin depender del idioma.

    ``entero`` se usa con clics e impresiones: en Search Console son siempre
    enteros, así que cualquier separador que aparezca es de miles. Sin esa
    pista «1.412» es ambiguo (¿mil cuatrocientos doce o uno coma cuatro?) y en
    la posición sí es decimal.
    """
    texto = str(valor or "").strip().replace("%", "").replace(" ", "")
    if not texto:
        return 0.0
    if entero:
        texto = texto.replace(".", "").replace(",", "")
    elif "," in texto and "." in texto:
        # El separador de miles es el de la izquierda del último separador
        # decimal: «1.234,5» es europeo y «1,234.5» anglosajón.
        if texto.rfind(",") > texto.rfind("."):
            texto = texto.replace(".", "").replace(",", ".")
        else:
            texto = texto.replace(",", "")
    elif "," in texto:
        texto = texto.replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return 0.0


def _separador(linea: str) -> str:
    """Search Console exporta con coma en inglés y con punto y coma en español.

    Elegir mal el separador desplaza las columnas y convierte «41,2» en dos
    campos.
    """
    return ";" if linea.count(";") > linea.count(",") else ","


def leer_csv(ruta: Path) -> list[dict]:
    """Filas de una exportación de Search Console, con nombres normalizados.

    La exportación trae dos líneas de preámbulo (título e intervalo de fechas)
    antes de la cabecera real: se busca la cabecera en vez de asumir su
    posición.
    """
    with ruta.open(encoding="utf-8-sig", newline="") as fichero:
        lineas = fichero.read().splitlines()
    inicio = 0
    for i, linea in enumerate(lineas[:10]):
        if "clics" in linea.lower() or "clicks" in linea.lower():
            inicio = i
            break
    filas = list(csv.reader(lineas[inicio:], delimiter=_separador(lineas[inicio])))
    if not filas:
        return []
    cabecera = _normalizar(filas[0])
    datos = []
    for fila in filas[1:]:
        if not fila or not any(celda.strip() for celda in fila):
            continue
        registro = dict(zip(cabecera, fila))
        clave = str(registro.get("clave") or "").strip()
        if not clave:
            continue
        # En una exportación de dos dimensiones la segunda columna es la URL.
        segunda = str(fila[1] or "").strip() if len(fila) > 1 else ""
        url = registro.get("url") or registro.get("pagina") or ""
        if not url and segunda.startswith("http"):
            url = segunda
        registro_dato = {
            "clave": clave,
            "clics": _numero(registro.get("clics", ""), entero=True),
            "impresiones": _numero(registro.get("impresiones", ""), entero=True),
            "posicion": _numero(registro.get("posicion", "")),
        }
        if url:
            registro_dato["url"] = url
        datos.append(registro_dato)
    return datos


def tipo_de_exportacion(filas: list[dict]) -> str:
    """``paginas``, ``cruce`` (consultas + páginas) o ``consultas``."""
    if not filas:
        return "consultas"
    urls_como_clave = sum(1 for f in filas if f["clave"].startswith("http"))
    con_url = sum(1 for f in filas if f.get("url"))
    if urls_como_clave > len(filas) / 2:
        return "paginas"
    if con_url > len(filas) / 2:
        return "cruce"
    return "consultas"


def _clics_a_posicion(impresiones: float, posicion: float) -> float:
    """Clics esperables por CTR según la posición (curva aproximada).

    No es una predicción: es una vara para ordenar oportunidades. La primera
    posición ronda el 25-30 %, la décima el 2 %, la vigésima el 0,5 %.
    """
    if posicion <= 1:
        ctr = 0.28
    elif posicion <= 3:
        ctr = 0.15
    elif posicion <= 5:
        ctr = 0.08
    elif posicion <= 10:
        ctr = 0.025
    elif posicion <= 20:
        ctr = 0.008
    else:
        ctr = 0.002
    return impresiones * ctr


def _fmt(numero: float, decimales: int = 0) -> str:
    return f"{numero:,.{decimales}f}".replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def _tabla(cabeceras: list[str], filas: list[list]) -> str:
    lineas = ["| " + " | ".join(cabeceras) + " |"]
    lineas.append("|" + "|".join("---" for _ in cabeceras) + "|")
    for fila in filas:
        lineas.append("| " + " | ".join(str(c) for c in fila) + " |")
    return "\n".join(lineas)


def _corta(url: str) -> str:
    return (url or "").replace("https://cotizat.online", "") or "/"


def _es_marca(clave: str, marca: str) -> bool:
    return marca.lower() in clave.lower() if marca else False


def informe_consultas(filas: list[dict], marca: str, cantidad: int) -> list[str]:
    total_clics = sum(f["clics"] for f in filas)
    total_impr = sum(f["impresiones"] for f in filas)
    marca_filas = [f for f in filas if _es_marca(f["clave"], marca)]
    marca_impr = sum(f["impresiones"] for f in marca_filas)
    marca_clics = sum(f["clics"] for f in marca_filas)
    cuota = f"{100 * marca_impr / total_impr:.0f} %" if total_impr else "—"

    salida = ["## Resumen", ""]
    salida.append(
        _tabla(
            ["", "Clics", "Impresiones", "Cuota de impresiones"],
            [
                ["Total", _fmt(total_clics), _fmt(total_impr), "100 %"],
                ["Marca", _fmt(marca_clics), _fmt(marca_impr), cuota],
                [
                    "Genéricas (no marca)",
                    _fmt(total_clics - marca_clics),
                    _fmt(total_impr - marca_impr),
                    (
                        f"{100 * (total_impr - marca_impr) / total_impr:.0f} %"
                        if total_impr
                        else "—"
                    ),
                ],
            ],
        )
    )
    salida.append("")
    if total_impr and marca_impr / total_impr > 0.5:
        salida.append(
            "> **Aviso:** más de la mitad de las impresiones son de marca. Casi "
            "nadie te descubre buscando el problema que resuelves: el trabajo "
            "pendiente es de contenido, no de etiquetas."
        )
        salida.append("")
    if total_impr and total_clics == 0:
        salida.append(
            "> **Aviso:** cero clics con impresiones. El sitio se muestra y no "
            "se elige: mira el puesto y el título, en ese orden."
        )
        salida.append("")

    salida.append("## Consultas por impresiones")
    salida.append("")
    top = sorted(filas, key=lambda f: -f["impresiones"])[:cantidad]
    salida.append(
        _tabla(
            ["Consulta", "Impresiones", "Clics", "Posición"],
            [
                [f["clave"], _fmt(f["impresiones"]), _fmt(f["clics"]), _fmt(f["posicion"], 1)]
                for f in top
            ],
        )
    )
    salida.append("")

    sin_clics = [
        f for f in filas if f["clics"] == 0 and f["impresiones"] >= 20
    ]
    sin_clics.sort(key=lambda f: -f["impresiones"])
    salida.append("## Consultas con impresiones y cero clics")
    salida.append("")
    salida.append(
        "Google las muestra y nadie pulsa. Si el puesto es peor que 10 no es un "
        "problema de título: es que no estás en la primera página."
    )
    salida.append("")
    if sin_clics:
        salida.append(
            _tabla(
                ["Consulta", "Impresiones", "Posición"],
                [[f["clave"], _fmt(f["impresiones"]), _fmt(f["posicion"], 1)] for f in sin_clics[:cantidad]],
            )
        )
    else:
        salida.append("Ninguna: todo lo que se muestra recibe algún clic.")
    salida.append("")
    return salida


def informe_paginas(filas: list[dict], cantidad: int) -> list[str]:
    ordenadas = sorted(filas, key=lambda f: -f["impresiones"])
    hundidas = [f for f in ordenadas if f["posicion"] > 10 and f["impresiones"] >= 30]
    techo = [f for f in ordenadas if 5 <= f["posicion"] <= 25 and f["impresiones"] >= 30]
    techo.sort(key=lambda f: -(f["impresiones"] * max(0.0, 25 - f["posicion"])))

    salida = ["## Páginas que gastan impresiones sin clics", ""]
    salida.append("Posición > 10 es página 2 en adelante: no hay clics que perder, hay que ganar puesto.")
    salida.append("")
    salida.append(
        _tabla(
            ["URL", "Impresiones", "Clics", "Posición"],
            [
                [_corta(f["clave"]), _fmt(f["impresiones"]), _fmt(f["clics"]), _fmt(f["posicion"], 1)]
                for f in hundidas[:cantidad]
            ],
        )
    )
    salida.append("")
    salida.append("## El techo real: páginas en la franja 5–25")
    salida.append("")
    salida.append(
        "Son las que, subiendo puestos, producen clics con el contenido que ya "
        "existe. Es donde rinde cada hora de trabajo."
    )
    salida.append("")
    if techo:
        salida.append(
            _tabla(
                ["URL", "Impresiones", "Posición", "Clics si sube a 5"],
                [
                    [
                        _corta(f["clave"]),
                        _fmt(f["impresiones"]),
                        _fmt(f["posicion"], 1),
                        "~" + _fmt(_clics_a_posicion(f["impresiones"], 5)),
                    ]
                    for f in techo[:cantidad]
                ],
            )
        )
    else:
        salida.append("Ninguna página en esa franja: hoy el sitio no está cerca del top 20.")
    salida.append("")
    return salida


def informe_canibalizacion(filas: list[dict], minimo: float, cantidad: int) -> list[str]:
    grupos: dict[str, list[dict]] = {}
    for fila in filas:
        url = fila.get("url")
        if not url:
            continue
        grupos.setdefault(fila["clave"], []).append(fila)
    repetidas = [
        (clave, sorted(items, key=lambda f: -f["impresiones"]))
        for clave, items in grupos.items()
        if len({f["url"] for f in items}) > 1
        and sum(f["impresiones"] for f in items) >= minimo
    ]
    repetidas.sort(key=lambda g: -sum(f["impresiones"] for f in g[1]))

    salida = ["## Canibalización: varias URLs compitiendo por la misma consulta", ""]
    if not repetidas:
        salida.append(
            "No se detecta reparto entre URLs. Para verlo hace falta la "
            "exportación con las dimensiones **Consultas** + **Páginas**."
        )
        salida.append("")
        return salida
    for clave, items in repetidas[:cantidad]:
        total = sum(f["impresiones"] for f in items)
        salida.append(f"### «{clave}» — {_fmt(total)} impresiones repartidas")
        salida.append("")
        salida.append(
            _tabla(
                ["URL", "Impresiones", "Clics", "Posición"],
                [
                    [_corta(f["url"]), _fmt(f["impresiones"]), _fmt(f["clics"]), _fmt(f["posicion"], 1)]
                    for f in items
                ],
            )
        )
        salida.append("")
    salida.append(
        "> Cada consulta debe tener **una** página dueña. Las demás no se "
        "borran: se enlazan hacia la dueña con el texto de esa consulta y, si "
        "son un calco (la misma landing en otro país), se quedan con "
        "`noindex, follow`."
    )
    salida.append("")
    return salida


def informe_cruce(filas: list[dict], cantidad: int) -> list[str]:
    """Con consultas + páginas: dónde aterriza cada consulta y quién gana."""
    por_url: dict[str, dict] = {}
    for fila in filas:
        url = fila.get("url") or fila["clave"]
        acumulado = por_url.setdefault(url, {"impresiones": 0.0, "clics": 0.0, "pos": []})
        acumulado["impresiones"] += fila["impresiones"]
        acumulado["clics"] += fila["clics"]
        if fila["posicion"]:
            acumulado["pos"].append(fila["posicion"])
    orden = sorted(por_url.items(), key=lambda par: -par[1]["impresiones"])
    salida = ["## Reparto de impresiones por URL (todas las consultas)", ""]
    salida.append(
        _tabla(
            ["URL", "Impresiones", "Clics", "Posición media"],
            [
                [
                    _corta(url),
                    _fmt(datos["impresiones"]),
                    _fmt(datos["clics"]),
                    _fmt(sum(datos["pos"]) / len(datos["pos"]), 1) if datos["pos"] else "—",
                ]
                for url, datos in orden[:cantidad]
            ],
        )
    )
    salida.append("")
    return salida


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("ficheros", nargs="*", type=Path, help="CSV de Search Console")
    parser.add_argument("--carpeta", type=Path, help="carpeta con los CSV")
    parser.add_argument("--marca", default="cotizat", help="término de marca (por omisión: cotizat)")
    parser.add_argument("--min-impresiones", type=float, default=20.0)
    parser.add_argument("--cantidad", type=int, default=15)
    args = parser.parse_args(argv)

    rutas = list(args.ficheros)
    if args.carpeta:
        rutas += sorted(args.carpeta.glob("*.csv"))
    rutas = [r for r in rutas if r.exists()]
    if not rutas:
        print("No se encontró ningún CSV. Descárgalos en Search Console → Rendimiento → Exportar.")
        return 2

    bloques = ["# Lectura de Search Console", ""]
    for ruta in rutas:
        filas = leer_csv(ruta)
        if not filas:
            print(f"(sin datos legibles en {ruta})", file=sys.stderr)
            continue
        tipo = tipo_de_exportacion(filas)
        bloques.append(f"## Archivo: `{ruta.name}` — {tipo}, {len(filas)} filas")
        bloques.append("")
        if tipo == "paginas":
            bloques += informe_paginas(filas, args.cantidad)
        elif tipo == "cruce":
            bloques += informe_canibalizacion(filas, args.min_impresiones, 8)
            bloques += informe_cruce(filas, args.cantidad)
        else:
            bloques += informe_consultas(filas, args.marca, args.cantidad)
    print("\n".join(bloques))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
