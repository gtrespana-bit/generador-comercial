"""Herramientas deterministas del copiloto para el editor de presupuestos.

El módulo trabaja con la serialización viva del editor. No persiste cambios ni
confía en cálculos enviados por el navegador: revisa estructura, calcula
mediciones en servidor y prepara propuestas que la interfaz debe confirmar.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import re
from typing import Any

from sqlalchemy.orm import Session

from .busqueda_catalogo import normalizar
from ..paises import es_ingles

MAX_CAPITULOS_BORRADOR = 100
MAX_PARTIDAS_BORRADOR = 600
_UNIDADES_CONOCIDAS = {
    "ud", "u", "und", "unidad", "unidades", "m", "ml", "m2", "m²", "m3", "m³",
    "kg", "g", "t", "ton", "l", "lt", "hora", "h", "dia", "día", "jornada",
    "juego", "glb", "global", "pa", "%", "saco", "rollo", "punto",
}


def _es_ingles(idioma) -> bool:
    """Las variantes regionales (/en-mx/) comparten vocabulario."""
    """Delegado en el registro de mercados, que es la única fuente.
    Así «en-GB» y «en-US» se resuelven como inglés sin duplicar la
    regla en ocho módulos.
    """
    return es_ingles(idioma)


def _t(texto: str, en: bool = False) -> str:
    """Traduce una etiqueta fija; en castellano la devuelve intacta."""
    return _ETIQUETAS_EN.get(texto, texto) if en else texto


# Mensajes de la revisión del borrador, por código. Los marcadores se
# rellenan con los mismos datos que ya usa la versión en castellano.
_MENSAJES_REVISION_EN: dict[str, tuple[str, str]] = {
    "sin_capitulos": (
        "The draft has no sections",
        "Add a section and at least one line item.",
    ),
    "capitulo_sin_nombre": (
        "Section {n} has no name",
        "Sections must be identified before saving.",
    ),
    "capitulo_vacio": (
        "{nombre} is empty",
        "Delete it or add line items, so it does not leave an empty section.",
    ),
    "partida_sin_nombre": (
        "Line item {pos} has no name",
        "Complete the name or delete the row.",
    ),
    "sin_precio": (
        "{nombre}: no price",
        "The active line item has a price of zero.",
    ),
    "sin_cantidad": (
        "{nombre}: no quantity",
        "The effective quantity must be greater than zero.",
    ),
    "cantidad_mediciones_difiere": (
        "{nombre}: direct quantity differs",
        "The direct quantity is {directa}, but the measurements add up to "
        "{mediciones}; CotizaT will use the sum of the measurements.",
    ),
    "sin_unidad": (
        "{nombre}: no unit",
        "Set m2, m, each or another unit of measure.",
    ),
    "unidad_inusual": (
        "{nombre}: unusual unit «{unidad}»",
        "Check it is not a typo or an abbreviation written by mistake.",
    ),
    "margen_negativo": (
        "{nombre}: cost above price",
        "Cost of {coste} against a price of {precio} per unit.",
    ),
    "producto_sin_precio": (
        "{nombre}: product without a sale price",
        "«{producto}» is linked but has no sale price.",
    ),
    "producto_sin_coste": (
        "{nombre}: product without a purchase cost",
        "The product margin cannot be checked until its cost is loaded.",
    ),
    "partida_duplicada": (
        "Possibly duplicated line item: {nombre}",
        "It appears at {posiciones}. Check that the same work is not being "
        "charged twice.",
    ),
    "estructura": (
        "{caps} section(s) and {total} line item(s) reviewed",
        "The review ran on what the editor is showing right now.",
    ),
    "precios": (
        "Active line items have a price",
        "No empty prices found.",
    ),
    "cantidades": (
        "Quantities filled in",
        "No empty effective quantities found.",
    ),
}


def _traducir_items(items: list[dict[str, Any]], en: bool) -> list[dict[str, Any]]:
    """Sustituye título y detalle por su versión inglesa, si la hay.

    Los mensajes en castellano se siguen construyendo igual (y son los que
    consume el editor en español); en inglés se reformatean con los mismos
    datos, así que ninguna cifra ni nombre se pierde por el camino.
    """
    if not en:
        return items
    salida = []
    for item in items:
        plantilla = _MENSAJES_REVISION_EN.get(item.get("codigo"))
        if not plantilla:
            salida.append(item)
            continue
        try:
            titulo = plantilla[0].format(**item.get("params", {}))
            detalle = plantilla[1].format(**item.get("params", {}))
        except (KeyError, IndexError, ValueError):
            salida.append(item)
            continue
        salida.append({**item, "titulo": titulo, "detalle": detalle})
    return salida


# Etiquetas fijas del copiloto: capítulos sugeridos y avisos de alcance.
_ETIQUETAS_EN: dict[str, str] = {
    # Capítulos sugeridos al preparar un lote.
    "Protecciones": "Protection",
    "Demoliciones": "Demolition and strip-out",
    "Residuos": "Waste and debris",
    "Preparación": "Preparation",
    "Pintura": "Painting",
    "Instalaciones": "Plumbing and services",
    "Impermeabilización": "Waterproofing",
    "Revestimientos": "Finishes",
    "Aparatos": "Sanitaryware",
    "Partidas sugeridas": "Suggested line items",
    "puertas": "doors",
    "de huecos": "of openings",
    # Conceptos de las mediciones.
    "Superficie de piso": "Floor area",
    "Perímetro útil / rodapié": "Net perimeter / skirting",
    "Superficie neta de paredes": "Net wall area",
    # Títulos y motivos de los posibles faltantes de alcance.
    "Protección de elementos existentes": "Protection of existing elements",
    "Antes de demoler conviene definir qué superficies y equipos deben protegerse.": (
        "Before any demolition it is worth agreeing which surfaces and "
        "equipment must be protected."
    ),
    "Gestión o transporte de escombros": "Debris handling and cartage",
    "La demolición genera residuos y su alcance debe quedar incluido o expresamente excluido.": (
        "Demolition produces waste; its scope must be either included or "
        "expressly excluded."
    ),
    "Preparación o regularización del soporte": "Screed or substrate preparation",
    "El acabado depende de una base plana, limpia y estable.": (
        "The finish depends on a flat, clean and stable base."
    ),
    "Preparación de superficies": "Surface preparation",
    "La pintura no debería ocultar reparaciones, lijado o saneado necesarios.": (
        "Painting should not hide repairs, sanding or making good that are "
        "needed."
    ),
    "Imprimación o fondo": "Primer or sealer coat",
    "Puede ser necesaria para uniformar absorción y adherencia.": (
        "It may be needed to even out suction and adhesion."
    ),
    "Impermeabilización de la zona húmeda": "Waterproofing to the wet area",
    "Hay revestimientos en un área húmeda, pero no se identifica una impermeabilización explícita.": (
        "There is tiling in a wet area, but no explicit waterproofing was "
        "identified."
    ),
}


def _decimal(valor: Any, defecto: str = "0") -> Decimal:
    try:
        texto = str(valor if valor not in (None, "") else defecto).strip().replace(" ", "")
        if "," in texto and "." in texto:
            texto = texto.replace(".", "").replace(",", ".")
        else:
            texto = texto.replace(",", ".")
        return Decimal(texto)
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(defecto)


def _redondear(valor: Decimal) -> float:
    return float(valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _capitulos_validos(capitulos: Any) -> list[dict[str, Any]]:
    if not isinstance(capitulos, list):
        return []
    salida = []
    total_partidas = 0
    for capitulo in capitulos[:MAX_CAPITULOS_BORRADOR]:
        if not isinstance(capitulo, dict):
            continue
        partidas = capitulo.get("partidas")
        if not isinstance(partidas, list):
            partidas = []
        disponibles = max(0, MAX_PARTIDAS_BORRADOR - total_partidas)
        partidas = [p for p in partidas[:disponibles] if isinstance(p, dict)]
        total_partidas += len(partidas)
        salida.append({
            "nombre": str(capitulo.get("nombre") or "")[:200],
            "partidas": partidas,
        })
        if total_partidas >= MAX_PARTIDAS_BORRADOR:
            break
    return salida


def _cantidad_partida(partida: dict[str, Any]) -> tuple[Decimal, Decimal | None]:
    mediciones = partida.get("mediciones")
    if isinstance(mediciones, list) and mediciones:
        total = sum(
            (_decimal(m.get("cantidad")) for m in mediciones if isinstance(m, dict)),
            Decimal("0"),
        )
        return total, _decimal(partida.get("cantidad"))
    return _decimal(partida.get("cantidad")), None


def _ubicacion(capitulo_indice: int, partida_indice: int | None = None) -> dict[str, int]:
    dato = {"capitulo_indice": capitulo_indice}
    if partida_indice is not None:
        dato["partida_indice"] = partida_indice
    return dato


def revisar_borrador_vivo(capitulos: Any, idioma: str = "es") -> dict[str, Any]:
    """Audita el estado exacto serializado por el editor, sin persistirlo."""
    en = _es_ingles(idioma)
    caps = _capitulos_validos(capitulos)
    criticos: list[dict[str, Any]] = []
    avisos: list[dict[str, Any]] = []
    correctos: list[dict[str, Any]] = []
    nombres: dict[str, list[tuple[int, int, str]]] = {}
    total_partidas = 0

    if not caps:
        criticos.append({
            "codigo": "sin_capitulos",
            "titulo": "El borrador no contiene capítulos",
            "detalle": "Añade un capítulo y al menos una partida.",
            "params": {},
        })

    for ci, capitulo in enumerate(caps):
        nombre_cap = str(capitulo.get("nombre") or "").strip()
        partidas = capitulo["partidas"]
        if not nombre_cap:
            criticos.append({
                "codigo": "capitulo_sin_nombre",
                "titulo": f"Capítulo {ci + 1} sin nombre",
                "detalle": "Los capítulos deben identificarse antes de guardar.",
                **_ubicacion(ci),
                "params": {"n": ci + 1},
            })
        if not partidas:
            avisos.append({
                "codigo": "capitulo_vacio",
                "titulo": f"{nombre_cap or f'Capítulo {ci + 1}'} está vacío",
                "detalle": "Elimínalo o añade partidas para que no genere una sección vacía.",
                **_ubicacion(ci),
                "params": {
                    "n": ci + 1,
                    "nombre": nombre_cap or (
                        f"Section {ci + 1}" if en else f"Capítulo {ci + 1}"
                    ),
                },
            })

        for pi, partida in enumerate(partidas):
            total_partidas += 1
            nombre = str(partida.get("nombre") or "").strip()
            ubicacion = _ubicacion(ci, pi)
            if not nombre:
                criticos.append({
                    "codigo": "partida_sin_nombre",
                    "titulo": f"Partida {ci + 1}.{pi + 1} sin nombre",
                    "detalle": "Completa el nombre o elimina la fila.",
                    **ubicacion,
                    "params": {"pos": f"{ci + 1}.{pi + 1}"},
                })
                continue
            clave = normalizar(nombre)
            nombres.setdefault(clave, []).append((ci, pi, nombre))

            tipo = str(partida.get("tipo_partida") or "included").lower()
            activa = tipo == "included" or bool(partida.get("seleccionada"))
            precio = _decimal(partida.get("precio"))
            cantidad, cantidad_directa = _cantidad_partida(partida)
            if activa and precio <= 0:
                criticos.append({
                    "codigo": "sin_precio",
                    "titulo": f"{nombre}: sin precio",
                    "detalle": "La partida activa tiene precio cero.",
                    **ubicacion,
                    "params": {"nombre": nombre},
                })
            if activa and cantidad <= 0:
                criticos.append({
                    "codigo": "sin_cantidad",
                    "titulo": f"{nombre}: sin cantidad",
                    "detalle": "La cantidad efectiva debe ser mayor que cero.",
                    **ubicacion,
                    "params": {"nombre": nombre},
                })

            mediciones = partida.get("mediciones")
            if (
                isinstance(mediciones, list) and mediciones
                and cantidad_directa is not None and cantidad_directa > 0
                and abs(cantidad_directa - cantidad) > Decimal("0.005")
            ):
                avisos.append({
                    "codigo": "cantidad_mediciones_difiere",
                    "titulo": f"{nombre}: cantidad directa distinta",
                    "detalle": (
                        f"La cantidad directa es {_redondear(cantidad_directa):g}, pero las mediciones suman "
                        f"{_redondear(cantidad):g}; CotizaT utilizará la suma de mediciones."
                    ),
                    **ubicacion,
                    "params": {
                        "nombre": nombre,
                        "directa": f"{_redondear(cantidad_directa):g}",
                        "mediciones": f"{_redondear(cantidad):g}",
                    },
                })

            unidad = str(partida.get("unidad") or "").strip()
            if not unidad:
                avisos.append({
                    "codigo": "sin_unidad",
                    "titulo": f"{nombre}: unidad vacía",
                    "detalle": "Define m2, m, ud u otra unidad de medición.",
                    **ubicacion,
                    "params": {"nombre": nombre},
                })
            elif normalizar(unidad).replace(" ", "") not in {
                normalizar(u).replace(" ", "") for u in _UNIDADES_CONOCIDAS
            }:
                avisos.append({
                    "codigo": "unidad_inusual",
                    "titulo": f"{nombre}: unidad poco habitual «{unidad[:30]}»",
                    "detalle": "Comprueba que no sea una abreviatura escrita por error.",
                    **ubicacion,
                    "params": {"nombre": nombre, "unidad": unidad[:30]},
                })

            coste = sum((_decimal(partida.get(campo)) for campo in (
                "coste_materiales", "coste_mano_obra", "coste_complementarios", "coste_otros",
            )), Decimal("0"))
            if activa and precio > 0 and coste > precio:
                criticos.append({
                    "codigo": "margen_negativo",
                    "titulo": f"{nombre}: coste superior al precio",
                    "detalle": f"Coste {_redondear(coste):,.2f} frente a precio {_redondear(precio):,.2f} por unidad.",
                    **ubicacion,
                    "params": {
                        "nombre": nombre,
                        "coste": f"{_redondear(coste):,.2f}",
                        "precio": f"{_redondear(precio):,.2f}",
                    },
                })

            producto = str(partida.get("prod_nombre") or "").strip()
            producto_precio = _decimal(partida.get("prod_precio"))
            producto_coste_raw = partida.get("prod_coste")
            if producto and producto_precio <= 0:
                avisos.append({
                    "codigo": "producto_sin_precio",
                    "titulo": f"{nombre}: producto sin precio",
                    "detalle": f"«{producto[:100]}» está asociado pero no tiene precio de venta.",
                    **ubicacion,
                    "params": {"nombre": nombre, "producto": producto[:100]},
                })
            if producto and producto_precio > 0 and product_coste_vacio(producto_coste_raw):
                avisos.append({
                    "codigo": "producto_sin_coste",
                    "titulo": f"{nombre}: producto sin coste de compra",
                    "detalle": "El margen del producto no puede comprobarse hasta cargar su coste.",
                    **ubicacion,
                    "params": {"nombre": nombre},
                })

    for repetidos in nombres.values():
        if len(repetidos) <= 1:
            continue
        ubicaciones = ", ".join(f"{ci + 1}.{pi + 1}" for ci, pi, _ in repetidos)
        ci, pi, nombre = repetidos[0]
        avisos.append({
            "codigo": "partida_duplicada",
            "titulo": f"Partida posiblemente duplicada: {nombre}",
            "detalle": f"Aparece en las posiciones {ubicaciones}. Confirma que no se esté cobrando dos veces.",
            **_ubicacion(ci, pi),
            "params": {"nombre": nombre, "posiciones": ubicaciones},
        })

    if total_partidas:
        correctos.append({
            "codigo": "estructura",
            "titulo": f"{len(caps)} capítulo(s) y {total_partidas} partida(s) analizados",
            "detalle": "La revisión se hizo sobre el contenido visible actual del editor.",
            "params": {"caps": len(caps), "total": total_partidas},
        })
    if not any(i["codigo"] == "sin_precio" for i in criticos) and total_partidas:
        correctos.append({"codigo": "precios", "titulo": "Partidas activas con precio", "detalle": "No se detectaron precios vacíos.", "params": {}})
    if not any(i["codigo"] == "sin_cantidad" for i in criticos) and total_partidas:
        correctos.append({"codigo": "cantidades", "titulo": "Cantidades informadas", "detalle": "No se detectaron cantidades efectivas vacías.", "params": {}})

    score = max(0, min(100, 100 - len(criticos) * 14 - len(avisos) * 4))
    estado = "riesgo" if criticos else ("revisar" if avisos else "listo")
    return {
        "estado": estado,
        "score": score,
        "criticos": _traducir_items(criticos, en),
        "avisos": _traducir_items(avisos, en),
        "correctos": _traducir_items(correctos, en),
        "total_capitulos": len(caps),
        "total_partidas": total_partidas,
    }


def product_coste_vacio(valor: Any) -> bool:
    return valor is None or (isinstance(valor, str) and not valor.strip())


_NUM = r"(\d+(?:[.,]\d+)?)"
_PAR = re.compile(rf"{_NUM}\s*(?:m)?\s*[x×]\s*{_NUM}\s*(?:m)?", re.IGNORECASE)
_ABERTURA = re.compile(
    rf"(?:(\d+)\s+)?(puertas?|ventanas?|huecos?)\s+(?:de\s+)?{_NUM}\s*(?:m)?\s*[x×]\s*{_NUM}\s*(?:m)?",
    re.IGNORECASE,
)


def calcular_mediciones_texto(texto: str, idioma: str = "es") -> dict[str, Any]:
    """Calcula superficies y perímetros a partir de dimensiones explícitas."""
    en = _es_ingles(idioma)
    texto = str(texto or "")[:1200]
    aberturas = []
    spans_aberturas = []
    descuento = Decimal("0")
    ancho_puertas = Decimal("0")
    for match in _ABERTURA.finditer(texto):
        cantidad = int(match.group(1) or 1)
        tipo = match.group(2).lower()
        ancho = _decimal(match.group(3))
        alto = _decimal(match.group(4))
        area = Decimal(cantidad) * ancho * alto
        descuento += area
        if tipo.startswith("puerta"):
            ancho_puertas += Decimal(cantidad) * ancho
        aberturas.append({
            "tipo": tipo,
            "cantidad": cantidad,
            "ancho": _redondear(ancho),
            "alto": _redondear(alto),
            "area": _redondear(area),
        })
        spans_aberturas.append(match.span())

    pares = []
    for match in _PAR.finditer(texto):
        if any(match.start() >= inicio and match.end() <= fin for inicio, fin in spans_aberturas):
            continue
        lado_a, lado_b = _decimal(match.group(1)), _decimal(match.group(2))
        if lado_a > 0 and lado_b > 0:
            pares.append((lado_a * lado_b, lado_a, lado_b))
    if not pares:
        return {
            "ok": False,
            "error": (
                "I could not make out length × width. Write, for example: "
                "bathroom 3 × 2 m with a ceiling height of 2.40 m."
                if en else
                "No pude identificar largo × ancho. Escribe, por ejemplo: baño de 3 × 2 m y 2,40 m de altura."
            ),
        }
    _, largo, ancho = max(pares, key=lambda par: par[0])

    altura = None
    # «2,40 m de altura» y «2.40 m high» son la misma medición.
    patrones_altura = (
        re.search(rf"altura\s+(?:de\s+)?{_NUM}\s*(?:m)?", texto, re.IGNORECASE),
        re.search(rf"{_NUM}\s*m\s+de\s+altura", texto, re.IGNORECASE),
        re.search(rf"(?:height|high|ceiling)\s+(?:of\s+)?{_NUM}\s*(?:m)?", texto, re.IGNORECASE),
        re.search(rf"{_NUM}\s*m\s+(?:high|in\s+height|ceiling)", texto, re.IGNORECASE),
    )
    for match in patrones_altura:
        if match:
            altura = _decimal(match.group(1))
            break

    desperdicio = Decimal("0")
    match_desperdicio = re.search(
        rf"{_NUM}\s*%\s*(?:de\s+)?(?:desperdicio|merma|waste|wastage)",
        texto, re.IGNORECASE,
    )
    if match_desperdicio:
        desperdicio = max(Decimal("0"), min(Decimal("50"), _decimal(match_desperdicio.group(1))))

    piso = largo * ancho
    perimetro = Decimal("2") * (largo + ancho)
    rodapie = max(Decimal("0"), perimetro - ancho_puertas)
    filas = [
        {"tipo": "piso", "concepto": _t("Superficie de piso", en), "cantidad": _redondear(piso), "unidad": "m2", "formula": f"{_redondear(largo):g} × {_redondear(ancho):g}"},
        {"tipo": "rodapie", "concepto": _t("Perímetro útil / rodapié", en), "cantidad": _redondear(rodapie), "unidad": "m", "formula": f"2 × ({_redondear(largo):g} + {_redondear(ancho):g}) - {_t('puertas', en)}"},
    ]
    if altura and altura > 0:
        paredes_brutas = perimetro * altura
        paredes_netas = max(Decimal("0"), paredes_brutas - descuento)
        filas.append({
            "tipo": "pared",
            "concepto": _t("Superficie neta de paredes", en),
            "cantidad": _redondear(paredes_netas),
            "unidad": "m2",
            "formula": (
                f"perimeter × {_redondear(altura):g} - {_redondear(descuento):g} m2 {_t('de huecos', en)}"
                if en else
                f"perímetro × {_redondear(altura):g} - {_redondear(descuento):g} m2 de huecos"
            ),
        })
    if desperdicio > 0:
        factor = Decimal("1") + desperdicio / Decimal("100")
        filas.append({
            "tipo": "piso_desperdicio",
            "concepto": (
                f"Floor with {desperdicio:g}% waste" if en else
                f"Piso con {desperdicio:g}% de desperdicio"
            ),
            "cantidad": _redondear(piso * factor),
            "unidad": "m2",
            "formula": f"{_redondear(piso):g} × {factor:g}",
        })
        if altura and altura > 0:
            paredes_netas = max(Decimal("0"), perimetro * altura - descuento)
            filas.append({
                "tipo": "pared_desperdicio",
                "concepto": (
                    f"Walls with {desperdicio:g}% waste" if en else
                    f"Paredes con {desperdicio:g}% de desperdicio"
                ),
                "cantidad": _redondear(paredes_netas * factor),
                "unidad": "m2",
                "formula": f"{_redondear(paredes_netas):g} × {factor:g}",
            })
    return {
        "ok": True,
        "largo": _redondear(largo),
        "ancho": _redondear(ancho),
        "altura": _redondear(altura) if altura else None,
        "aberturas": aberturas,
        "descuento_aberturas": _redondear(descuento),
        "desperdicio_pct": _redondear(desperdicio),
        "filas": filas,
    }


_FLUJOS = (
    {
        "requiere": (("demolicion", "demoler", "quitar", "retirar",
                      "demolition", "demolish", "remove", "strip"),
                     ("porcelanato", "ceramica", "baldosa",
                      "porcelain", "tile", "tiling")),
        "consultas": (
            ("Protecciones", "proteccion de elementos existentes"),
            ("Demoliciones", "demolicion piso porcelanato"),
            ("Demoliciones", "picado pared porcelanato"),
            ("Residuos", "acopio escombros"),
            ("Residuos", "transporte escombros"),
        ),
    },
    {
        "requiere": (("pintura", "pintar", "paint", "painting"),),
        "consultas": (
            ("Preparación", "preparacion superficie pintura"),
            ("Pintura", "imprimacion pared"),
            ("Pintura", "pintura paredes"),
            ("Protecciones", "proteccion elementos pintura"),
        ),
    },
    {
        "requiere": (("bano", "baño", "bathroom", "washroom"),
                     ("remodelacion", "remodelar", "reforma",
                      "refurbish", "refurbishment", "remodel", "renovate")),
        "consultas": (
            ("Demoliciones", "demolicion revestimiento bano"),
            ("Instalaciones", "adecuacion puntos agua bano"),
            ("Impermeabilización", "impermeabilizacion ducha"),
            ("Revestimientos", "colocacion porcelanato piso"),
            ("Revestimientos", "enchapado porcelanato pared"),
            ("Aparatos", "instalacion aparatos sanitarios"),
        ),
    },
)


def _flujo_para(consulta: str) -> tuple[tuple[str, str], ...]:
    texto = normalizar(consulta)
    for flujo in _FLUJOS:
        if all(any(normalizar(opcion) in texto for opcion in grupo) for grupo in flujo["requiere"]):
            return flujo["consultas"]
    return ()


def _existentes_borrador(capitulos: Any) -> tuple[set[int], set[str]]:
    ids: set[int] = set()
    nombres: set[str] = set()
    for capitulo in _capitulos_validos(capitulos):
        for partida in capitulo["partidas"]:
            try:
                catalogo_id = int(partida.get("catalogo_id") or 0)
            except (TypeError, ValueError):
                catalogo_id = 0
            if catalogo_id:
                ids.add(catalogo_id)
            nombre = normalizar(partida.get("nombre") or "")
            if nombre:
                nombres.add(nombre)
    return ids, nombres


def preparar_lote_catalogo(
    db: Session, consulta: str, capitulos: Any = None, idioma: str = "es",
) -> dict[str, Any]:
    """Prepara un lote real del catálogo y excluye lo ya presente."""
    from .asistente_ia import buscar_partidas_catalogo

    en = _es_ingles(idioma)
    existentes_ids, existentes_nombres = _existentes_borrador(capitulos)
    flujo = _flujo_para(consulta)
    candidatos: list[dict[str, Any]] = []
    vistos: set[int] = set()
    consultas = flujo or (("Partidas sugeridas", consulta),)
    for capitulo, termino in consultas:
        busqueda = buscar_partidas_catalogo(db, termino, limite=5 if not flujo else 2)
        for partida in busqueda.get("resultados", []):
            pid = int(partida["id"])
            if pid in vistos or pid in existentes_ids or normalizar(partida["nombre"]) in existentes_nombres:
                continue
            vistos.add(pid)
            candidatos.append({
                **partida,
                "capitulo_sugerido": _t(capitulo, en),
                "consulta_origen": termino,
            })
            if flujo:
                break
    return {
        "consulta": consulta[:300],
        "flujo_reconocido": bool(flujo),
        "candidatos": candidatos[:12],
        "omitidas_existentes": len(existentes_ids),
    }


_REGLAS_ALCANCE = (
    {
        "disparador": (("demolicion", "demoler", "picado", "desmontaje"),),
        "requisitos": (
            {"clave": "proteccion", "presencia": ("proteccion", "cubrir"), "consulta": "proteccion elementos existentes", "titulo": "Protección de elementos existentes", "motivo": "Antes de demoler conviene definir qué superficies y equipos deben protegerse."},
            {"clave": "residuos", "presencia": ("escombro", "residuo", "bote", "transporte"), "consulta": "transporte escombros", "titulo": "Gestión o transporte de escombros", "motivo": "La demolición genera residuos y su alcance debe quedar incluido o expresamente excluido."},
        ),
    },
    {
        "disparador": (("porcelanato", "ceramica", "enchapado", "solado"),),
        "requisitos": (
            {"clave": "soporte", "presencia": ("regularizacion", "preparacion del soporte", "nivelacion"), "consulta": "regularizacion soporte piso", "titulo": "Preparación o regularización del soporte", "motivo": "El acabado depende de una base plana, limpia y estable."},
        ),
    },
    {
        "disparador": (("pintura", "pintar"),),
        "requisitos": (
            {"clave": "preparacion_pintura", "presencia": ("lijado", "preparacion", "saneado"), "consulta": "preparacion superficie pintura", "titulo": "Preparación de superficies", "motivo": "La pintura no debería ocultar reparaciones, lijado o saneado necesarios."},
            {"clave": "imprimacion", "presencia": ("imprimacion", "fondo", "sellador"), "consulta": "imprimacion pared", "titulo": "Imprimación o fondo", "motivo": "Puede ser necesaria para uniformar absorción y adherencia."},
        ),
    },
)


def detectar_faltantes_alcance(
    db: Session,
    capitulos: Any,
    contexto_texto: str = "",
    idioma: str = "es",
) -> dict[str, Any]:
    """Detecta complementos no cubiertos y los vincula al catálogo real."""
    from .asistente_ia import buscar_partidas_catalogo

    en = _es_ingles(idioma)
    caps = _capitulos_validos(capitulos)
    nombres = []
    descripciones = []
    for capitulo in caps:
        nombres.append(capitulo["nombre"])
        for partida in capitulo["partidas"]:
            nombres.append(str(partida.get("nombre") or ""))
            descripciones.append(str(partida.get("descripcion") or ""))
    texto_nombres = normalizar(" ".join(nombres) + " " + contexto_texto)
    texto_completo = normalizar(" ".join(nombres + descripciones) + " " + contexto_texto)
    sugerencias = []
    claves = set()

    for regla in _REGLAS_ALCANCE:
        activa = all(any(normalizar(opcion) in texto_nombres for opcion in grupo) for grupo in regla["disparador"])
        if not activa:
            continue
        for requisito in regla["requisitos"]:
            if requisito["clave"] in claves:
                continue
            if any(normalizar(frase) in texto_completo for frase in requisito["presencia"]):
                continue
            claves.add(requisito["clave"])
            busqueda = buscar_partidas_catalogo(db, requisito["consulta"], limite=3)
            sugerencias.append({
                **requisito,
                "titulo": _t(requisito["titulo"], en),
                "motivo": _t(requisito["motivo"], en),
                "partidas": busqueda.get("resultados", [])[:3],
            })

    # En áreas húmedas, impermeabilización es una revisión específica.
    # (Los textos ya vienen normalizados: sin tildes y en minúsculas.)
    area_humeda = any(t in texto_nombres for t in (
        "bano", "ducha", "lavadero", "terraza",
        "bathroom", "shower", "wet room", "utility", "terrace",
    ))
    hay_revestimiento = any(t in texto_nombres for t in (
        "porcelanato", "ceramica", "enchapado", "piso",
        "porcelain", "tile", "tiling", "floor",
    ))
    if area_humeda and hay_revestimiento and not any(
        t in texto_completo for t in ("impermeabil", "membrana", "manto")
    ):
        busqueda = buscar_partidas_catalogo(db, "impermeabilizacion zona humeda", limite=3)
        sugerencias.append({
            "clave": "impermeabilizacion",
            "titulo": _t("Impermeabilización de la zona húmeda", en),
            "motivo": _t(
                "Hay revestimientos en un área húmeda, pero no se identifica "
                "una impermeabilización explícita.", en,
            ),
            "consulta": "impermeabilizacion zona humeda",
            "presencia": ("impermeabilizacion",),
            "partidas": busqueda.get("resultados", [])[:3],
        })

    ids = []
    for sugerencia in sugerencias:
        if sugerencia["partidas"]:
            pid = int(sugerencia["partidas"][0]["id"])
            if pid not in ids:
                ids.append(pid)
    return {
        "sugerencias": sugerencias,
        "ids_recomendados": ids,
        "total": len(sugerencias),
        "analizadas": sum(len(c["partidas"]) for c in caps),
    }
