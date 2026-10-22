"""Paginación y orden comunes de las listas del panel (Fase 1).

De las nueve listas del panel, solo una —Clientes › Directorio— se podía
interrogar, y ninguna paginaba. Cada pantalla resolvía el mismo problema a su
manera: unas buscaban, otras filtraban, otras ordenaban en Python y el CSV salía
de un sitio distinto al de la tabla.

Aquí vive el cálculo único:

- **Tamaño de página** (25/50/100) y **ventana de páginas** con elipsis.
- **Orden por URL** (``?orden=&dir=``) con el mismo criterio para la tabla y
  para el CSV: lo que se ve es lo que se exporta.
- **Paginador** ya montado (URLs, anterior/siguiente, números, tamaños) para que
  la plantilla no reconstruya query strings.

Convención: la página 1 y el tamaño por omisión no viajan en la URL. Así un
filtro enlazado desde ⌘K, una notificación o una vista guardada no arrastra
``?pagina=1&por=25``.
"""
from __future__ import annotations

import math

from .panel_contextos import url_panel

#: Filas por página por omisión. Es el tamaño que cabe en una pantalla sin
#: convertir la lista en un scroll infinito y sin obligar a paginar de cinco en
#: cinco.
POR_PAGINA = 25

#: Tamaños ofrecidos. El tope acota el coste de contar y pintar: una lista del
#: panel no es un volcado de base de datos.
OPCIONES_POR_PAGINA = (25, 50, 100)


def normalizar_pagina(valor) -> int:
    """Página pedida como entero ≥ 1 (1 si viene vacía o rota)."""
    try:
        numero = int(str(valor).strip())
    except (TypeError, ValueError):
        return 1
    return max(1, numero)


def normalizar_por_pagina(valor) -> int:
    """Tamaño de página pedido, limitado a las opciones ofrecidas."""
    try:
        numero = int(str(valor).strip())
    except (TypeError, ValueError):
        return POR_PAGINA
    return numero if numero in OPCIONES_POR_PAGINA else POR_PAGINA


def meta_pagina(total: int, pagina: int, por_pagina: int) -> dict:
    """Cifras de la página: rango visible, total de páginas y vecinos.

    Si la página pedida se pasa del final (un filtro cambió mientras la lista
    estaba abierta), se ajusta a la última: nunca se devuelve una lista vacía
    por una URL vieja.
    """
    total = max(0, int(total or 0))
    por_pagina = normalizar_por_pagina(por_pagina)
    paginas = max(1, math.ceil(total / por_pagina)) if total else 1
    numero = min(max(1, int(pagina or 1)), paginas)
    desde = 0 if not total else (numero - 1) * por_pagina + 1
    hasta = min(total, numero * por_pagina)
    return {
        "total": total,
        "numero": numero,
        "paginas": paginas,
        "por_pagina": por_pagina,
        "desde": desde,
        "hasta": hasta,
        "hay_anterior": numero > 1,
        "hay_siguiente": numero < paginas,
    }


def paginar_consulta(consulta, *, pagina: int = 1, por_pagina: int = POR_PAGINA):
    """``(filas, meta)`` de una consulta SQL ya ordenada.

    El recuento se hace sobre la consulta sin ``ORDER BY``: contar con orden no
    cambia el número y en PostgreSQL obliga a ordenar la tabla entera.
    """
    total = consulta.order_by(None).count()
    meta = meta_pagina(total, pagina, por_pagina)
    filas = (
        consulta.offset((meta["numero"] - 1) * meta["por_pagina"])
        .limit(meta["por_pagina"])
        .all()
    )
    return filas, meta


def paginar_lista(filas, *, pagina: int = 1, por_pagina: int = POR_PAGINA):
    """``(recorte, meta)`` para listas ya materializadas en memoria.

    Se usa donde la lista sale de un servicio que recorre varias tablas (por
    ejemplo los contratos, que se construyen desde el resumen de clientes).
    La meta es la misma que la de SQL para que el paginador no cambie.
    """
    filas = list(filas or [])
    meta = meta_pagina(len(filas), pagina, por_pagina)
    inicio = (meta["numero"] - 1) * meta["por_pagina"]
    return filas[inicio : inicio + meta["por_pagina"]], meta


def paginador(ruta: str, actuales: dict, meta: dict) -> dict:
    """Paginador listo para la plantilla: URLs y números, sin lógica en Jinja."""
    base = {clave: valor for clave, valor in actuales.items() if clave != "pagina"}

    def url(pagina: int) -> str:
        if pagina <= 1:
            return url_panel(ruta, **base)
        return url_panel(ruta, **{**base, "pagina": pagina})

    numeros = []
    for numero in _ventana(meta["numero"], meta["paginas"]):
        if numero is None:
            numeros.append({"numero": None, "url": "", "activa": False})
        else:
            numeros.append({
                "numero": numero,
                "url": url(numero),
                "activa": numero == meta["numero"],
            })

    tamanos = [
        {
            "valor": valor,
            "url": url_panel(
                ruta,
                **({**base, "por": valor} if valor != POR_PAGINA else base),
            ),
            "activa": valor == meta["por_pagina"],
        }
        for valor in OPCIONES_POR_PAGINA
    ]

    return {
        "meta": meta,
        "anterior": url(meta["numero"] - 1) if meta["hay_anterior"] else "",
        "siguiente": url(meta["numero"] + 1) if meta["hay_siguiente"] else "",
        "numeros": numeros,
        "tamanos": tamanos,
        "info": (
            f"{meta['desde']}–{meta['hasta']} de {meta['total']}"
            if meta["total"]
            else "Sin resultados"
        ),
    }


def _ventana(numero: int, paginas: int) -> list[int | None]:
    """Números de página a mostrar: primera, última y el entorno de la actual."""
    if paginas <= 7:
        return list(range(1, paginas + 1))
    visibles = {1, paginas, numero - 1, numero, numero + 1}
    visibles = {n for n in visibles if 1 <= n <= paginas}
    ordenados = sorted(visibles)
    salida: list[int | None] = []
    anterior = 0
    for actual in ordenados:
        if anterior and actual - anterior > 1:
            salida.append(None)
        salida.append(actual)
        anterior = actual
    return salida


def orden_chips(ruta: str, actuales: dict, opciones) -> list[dict]:
    """Chips de «Ordenar por», con la flecha de la dirección activa.

    ``opciones`` son ``(clave, etiqueta, dirección_inicial)``. Pulsar la columna
    activa invierte la dirección; pulsar otra empieza por la suya (fecha e
    importe, de mayor a menor; nombres, de la A a la Z).
    """
    activa = actuales.get("orden", "")
    direccion_actual = actuales.get("dir", "asc")
    salida = []
    for opcion in opciones:
        clave, etiqueta, inicial = opcion[0], opcion[1], opcion[2]
        es_activa = clave == activa
        direccion = (
            ("asc" if direccion_actual == "desc" else "desc")
            if es_activa
            else inicial
        )
        salida.append({
            "clave": clave,
            "etiqueta": etiqueta,
            "url": url_panel(ruta, **{**actuales, "orden": clave, "dir": direccion}),
            "activo": es_activa,
            "flecha": ("↑" if direccion_actual == "asc" else "↓") if es_activa else "",
        })
    return salida
