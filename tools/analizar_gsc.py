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


#: Primera columna de las exportaciones que no son Consultas/Páginas. Se
#: reconoce el archivo por ella, no por el nombre: Search Console bautiza con
#: «Gráfico.csv», «Países.csv»… y el usuario puede renombrarlos.
_TIPOS = {
    "país": "paises",
    "pais": "paises",
    "country": "paises",
    "dispositivo": "dispositivos",
    "device": "dispositivos",
    "aparición en búsquedas": "apariencias",
    "aparicion en busquedas": "apariencias",
    "search appearance": "apariencias",
    "fecha": "grafico",
    "date": "grafico",
    "motivo": "problemas",
    "reason": "problemas",
    "propiedad": "contexto",
    "property": "contexto",
    "filtrar": "contexto",
    "filter": "contexto",
}


def _normalizar(cabecera: list[str]) -> list[str]:
    return [_ALIAS.get(c.strip().lower().replace("\ufeff", ""), c) for c in cabecera]


def tipo_de_archivo(ruta: Path) -> str:
    """Qué exportación es, mirando su primera columna.

    ``grafico`` es el del tiempo (Fecha + Clics/Impresiones) y ``cobertura`` el
    de Indexación → Páginas, que trae «Sin indexar»/«Indexadas».
    """
    try:
        with ruta.open(encoding="utf-8-sig") as fichero:
            primera = fichero.readline().strip()
    except OSError:
        return "desconocido"
    columnas = [c.strip().lower().replace("\ufeff", "") for c in primera.split(_separador(primera))]
    if "sin indexar" in columnas or "indexadas" in columnas or "not indexed" in columnas:
        return "cobertura"
    if columnas and columnas[0] == "fecha" and any(
        c in columnas for c in ("clics", "clicks", "impresiones", "impressions")
    ):
        return "grafico"
    if columnas and columnas[0] == "fecha":
        return "cobertura"
    return _TIPOS.get(columnas[0] if columnas else "", "desconocido")


def leer_tabla(ruta: Path) -> tuple[list[str], list[dict]]:
    """Cabecera y filas tal cual, sin interpretar. Para países, dispositivos…"""
    with ruta.open(encoding="utf-8-sig", newline="") as fichero:
        lineas = fichero.read().splitlines()
    if not lineas:
        return [], []
    filas = list(csv.reader(lineas, delimiter=_separador(lineas[0])))
    if not filas:
        return [], []
    cabecera = [c.strip() for c in filas[0]]
    datos = [dict(zip(cabecera, fila)) for fila in filas[1:] if fila and any(c.strip() for c in fila)]
    return cabecera, datos


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


#: Mercados con prefijo propio y su idioma real. Brasil es el caso que más
#: engaña: paga impresiones en portugués y la web no tiene ni una página en
#: portugués, así que su CTR cercano a cero no es un fallo de la ficha.
_MERCADOS_IDIOMA = {
    "en-us": "inglés", "en-gb": "inglés", "en-au": "inglés", "en-ie": "inglés",
    "en-ca": "inglés", "en": "inglés",
    "es": "español", "mx": "español", "co": "español", "ar": "español",
    "cl": "español", "pe": "español", "ec": "español", "do": "español",
    "uy": "español", "py": "español", "bo": "español", "pa": "español",
    "cr": "español", "gt": "español", "hn": "español", "sv": "español",
    "ni": "español", "ve": "español",
    "br": "portugués",
}


def mercado_de(url: str) -> str:
    """Prefijo de mercado de una URL del sitio (``/en-ie/…`` → ``en-ie``)."""
    import re

    camino = re.sub(r"^https?://[^/]+", "", url or "")
    partes = [p for p in camino.split("/") if p]
    return partes[0].lower() if partes else "(home)"


def idioma_de_mercado(mercado: str) -> str:
    return _MERCADOS_IDIOMA.get(mercado, "sin idioma propio")


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


def informe_cobertura(cabecera: list[str], filas: list[dict]) -> list[str]:
    """Indexación: qué crece a la derecha de la raya (indexadas) y qué no."""
    def _col(*nombres: str) -> str:
        for nombre in nombres:
            for c in cabecera:
                if c.strip().lower() == nombre:
                    return c
        return ""

    c_fecha = _col("fecha", "date")
    c_sin = _col("sin indexar", "not indexed")
    c_si = _col("indexadas", "indexed")
    datos = []
    for fila in filas:
        datos.append(
            {
                "fecha": (fila.get(c_fecha) or "").strip(),
                "sin": _numero(fila.get(c_sin, ""), entero=True),
                "si": _numero(fila.get(c_si, ""), entero=True),
            }
        )
    datos = [d for d in datos if d["fecha"]]
    if not datos:
        return []

    salida = ["## Cobertura del índice", ""]
    primero, ultimo = datos[0], datos[-1]
    salida.append(
        _tabla(
            ["Fecha", "Indexadas", "Sin indexar", "Total"],
            [
                [d["fecha"], _fmt(d["si"]), _fmt(d["sin"]), _fmt(d["si"] + d["sin"])]
                for d in (primero, datos[len(datos) // 2], ultimo)
            ],
        )
    )
    salida.append("")
    delta_si = ultimo["si"] - primero["si"]
    delta_sin = ultimo["sin"] - primero["sin"]
    if delta_sin > delta_si and delta_sin > 0:
        salida.append(
            f"> **Aviso:** desde {primero['fecha']} las no indexadas suben "
            f"{_fmt(delta_sin)} y las indexadas solo {_fmt(delta_si)}. Se "
            "está anunciando a Google bastante más de lo que se indexa."
        )
    elif delta_si > 0 and delta_sin <= 0:
        salida.append(
            f"> **Bien:** las indexadas suben {_fmt(delta_si)} y las no "
            f"indexadas bajan {_fmt(abs(delta_sin))}. La limpieza funciona."
        )
    else:
        salida.append(
            f"> Indexadas {_fmt(primero['si'])} → {_fmt(ultimo['si'])} "
            f"({_fmt(delta_si)}); sin indexar {_fmt(primero['sin'])} → "
            f"{_fmt(ultimo['sin'])} ({_fmt(delta_sin)})."
        )
    salida.append("")
    return salida


def informe_grafico(cabecera: list[str], filas: list[dict]) -> list[str]:
    """La serie diaria: forma de la curva, pico y días muertos."""
    def _col(*nombres: str) -> str:
        for nombre in nombres:
            for c in cabecera:
                if c.strip().lower() == nombre:
                    return c
        return ""

    c_fecha = _col("fecha", "date")
    c_clics = _col("clics", "clicks")
    c_impr = _col("impresiones", "impressions")
    c_pos = _col("posición", "posicion", "position")
    datos = []
    for fila in filas:
        fecha = (fila.get(c_fecha) or "").strip()
        if not fecha:
            continue
        datos.append(
            {
                "fecha": fecha,
                "clics": _numero(fila.get(c_clics, ""), entero=True),
                "impr": _numero(fila.get(c_impr, ""), entero=True),
                "pos": _numero(fila.get(c_pos, "")) if c_pos else 0.0,
            }
        )
    if not datos:
        return []

    salida = ["## Serie diaria", ""]
    pico = max(datos, key=lambda d: d["impr"])
    salida.append(
        f"- Periodo: **{datos[0]['fecha']} → {datos[-1]['fecha']}** "
        f"({len(datos)} días)"
    )
    salida.append(
        f"- Impresiones: **{_fmt(sum(d['impr'] for d in datos))}** · "
        f"Clics: **{_fmt(sum(d['clics'] for d in datos))}**"
    )
    salida.append(
        f"- Pico de impresiones: **{pico['fecha']}** con {_fmt(pico['impr'])}"
    )
    # Antes y después del pico: un escalón es un cambio técnico o de contenido;
    # una pendiente suave es posición o competencia.
    antes = [d["impr"] for d in datos if d["fecha"] < pico["fecha"]]
    despues = [d["impr"] for d in datos if d["fecha"] > pico["fecha"]]
    if antes and despues:
        media_antes = sum(antes) / len(antes)
        media_despues = sum(despues) / len(despues)
        salida.append(
            f"- Media antes del pico: {_fmt(media_antes)} · después: {_fmt(media_despues)}"
        )
        if media_antes and media_despues / media_antes > 1.5:
            salida.append(
                "> **Escalón hacia arriba tras el pico.** Si coincide con un "
                "cambio de contenido o de política de indexación, es la señal "
                "de que ese cambio funcionó; si coincide con un despliegue "
                "técnico, revisa qué se publicó ese día."
            )
    salida.append("")
    return salida


def informe_dimension(cabecera: list[str], filas: list[dict], titulo: str, etiqueta: str) -> list[str]:
    """Países y dispositivos: dónde se muestra y con qué CTR."""
    c_nombre = cabecera[0] if cabecera else ""
    c_clics = next((c for c in cabecera if c.strip().lower() in ("clics", "clicks")), "")
    c_impr = next((c for c in cabecera if c.strip().lower() in ("impresiones", "impressions")), "")
    c_pos = next((c for c in cabecera if c.strip().lower() in ("posición", "posicion", "position")), "")
    datos = []
    for fila in filas:
        datos.append(
            {
                "nombre": (fila.get(c_nombre) or "").strip(),
                "clics": _numero(fila.get(c_clics, ""), entero=True),
                "impr": _numero(fila.get(c_impr, ""), entero=True),
                "pos": _numero(fila.get(c_pos, "")) if c_pos else 0.0,
            }
        )
    datos = [d for d in datos if d["nombre"]]
    total = sum(d["impr"] for d in datos) or 1
    datos.sort(key=lambda d: -d["impr"])
    salida = [f"## {titulo}", ""]
    salida.append(
        _tabla(
            [etiqueta, "Clics", "Impresiones", "Cuota", "CTR", "Posición"],
            [
                [
                    d["nombre"][:26],
                    _fmt(d["clics"]),
                    _fmt(d["impr"]),
                    f"{100 * d['impr'] / total:.0f} %",
                    (_fmt(100 * d["clics"] / d["impr"], 2) + " %") if d["impr"] else "—",
                    _fmt(d["pos"], 1),
                ]
                for d in datos[:15]
            ],
        )
    )
    salida.append("")
    return salida


def informe_problemas(cabecera: list[str], filas: list[dict]) -> list[str]:
    """Indexación → Páginas: los motivos, ordenados por páginas afectadas."""
    c_motivo = cabecera[0] if cabecera else ""
    c_pag = next((c for c in cabecera if c.strip().lower() == "páginas"), "")
    c_pag = c_pag or next((c for c in cabecera if c.strip().lower() == "pages"), "")
    datos = [
        {
            "motivo": (fila.get(c_motivo) or "").strip(),
            "paginas": _numero(fila.get(c_pag, ""), entero=True),
        }
        for fila in filas
    ]
    datos = [d for d in datos if d["motivo"] and d["paginas"]]
    if not datos:
        return ["## Problemas de indexación", "", "Sin filas con páginas afectadas.", ""]
    datos.sort(key=lambda d: -d["paginas"])
    salida = ["## Problemas de indexación (por páginas afectadas)", ""]
    salida.append(
        _tabla(
            ["Motivo", "Páginas"],
            [[d["motivo"][:64], _fmt(d["paginas"])] for d in datos],
        )
    )
    salida.append("")
    return salida


def informe_apariencias(cabecera: list[str], filas: list[dict]) -> list[str]:
    """Qué resultado enriquecido recibe impresiones y con qué CTR."""
    c_nombre = cabecera[0] if cabecera else ""
    c_clics = next((c for c in cabecera if c.strip().lower() in ("clics", "clicks")), "")
    c_impr = next((c for c in cabecera if c.strip().lower() in ("impresiones", "impressions")), "")
    salida = ["## Aparición en búsquedas (resultados enriquecidos)", ""]
    filas_txt = []
    for fila in filas:
        clics = _numero(fila.get(c_clics, ""), entero=True)
        impr = _numero(fila.get(c_impr, ""), entero=True)
        filas_txt.append(
            [
                (fila.get(c_nombre) or "").strip(),
                _fmt(clics),
                _fmt(impr),
                (_fmt(100 * clics / impr, 2) + " %") if impr else "—",
            ]
        )
    salida.append(_tabla(["Tipo", "Clics", "Impresiones", "CTR"], filas_txt))
    salida.append("")
    if any("product" in (f[0] or "").lower() or "producto" in (f[0] or "").lower() for f in filas_txt):
        salida.append(
            "> Hay impresiones de **Fragmentos de productos**: la página que "
            "emite `Product` (hoy solo `/pago`) participa en ese resultado. Si "
            "el CTR es bajo, el problema es el título y el precio mostrado, no "
            "el marcado."
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
        tipo_archivo = tipo_de_archivo(ruta)
        if tipo_archivo != "desconocido":
            cabecera, filas_tabla = leer_tabla(ruta)
            if tipo_archivo == "cobertura":
                bloque = informe_cobertura(cabecera, filas_tabla)
            elif tipo_archivo == "grafico":
                bloque = informe_grafico(cabecera, filas_tabla)
            elif tipo_archivo == "paises":
                bloque = informe_dimension(cabecera, filas_tabla, "Por país", "País")
            elif tipo_archivo == "dispositivos":
                bloque = informe_dimension(cabecera, filas_tabla, "Por dispositivo", "Dispositivo")
            elif tipo_archivo == "problemas":
                bloque = informe_problemas(cabecera, filas_tabla)
            elif tipo_archivo == "contexto":
                # Metadatos y Filtros: con qué datos se generó el resto.
                bloque = [
                    f"- **{fila.get(cabecera[0], '')}:** {fila.get(cabecera[1], '')}"
                    for fila in filas_tabla
                ] + [""]
            else:
                bloque = informe_apariencias(cabecera, filas_tabla)
            if bloque:
                bloques.append(f"## Archivo: `{ruta.name}` — {tipo_archivo}")
                bloques.append("")
                bloques += bloque
            continue

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
