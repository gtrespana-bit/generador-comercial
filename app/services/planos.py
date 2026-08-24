"""Detección geométrica, calibración, dibujo y medición sobre planos.

El módulo cubre cuatro responsabilidades:

1. **Detección automática de estancias** sobre una imagen PNG/JPG/WEBP.
   Reconoce muros, descarta cotas y rellena los recintos cerrados como
   áreas. Conoce el grosor del tabique declarado en el plano y ajusta la
   barrera para que las dos caras de un muro cuenten una sola vez.
2. **Calibración y medición real** a partir de una distancia conocida
   sobre la imagen (escala px/m) y una altura libre (m² de paredes).
3. **Dibujo desde cero** en el editor: crea planos vectoriales
   (``origen='dibujado'``) o mezcla imagen + geometría
   (``origen='mixto'``), con muros, puertas y ventanas.
4. **Mediciones editables** de cualquier tipo (línea, área, perímetro,
   conteo) sobre píxeles de imagen, persistidas como ``PlanoMedicion``.

No se envía ningún plano a un servicio externo: el procesamiento es
100% local (Pillow + heurísticas) y no tiene coste por uso.
"""

from __future__ import annotations

import io
import json
import math
from collections import deque
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from ..models import PlanoElemento, PlanoMedicion, PlanoObra

EXT_PLANOS_IMG = {".png", ".jpg", ".jpeg", ".webp"}
EXT_PLANOS_PDF = {".pdf"}
MAX_PLANO_BYTES = 12 * 1024 * 1024
MAX_PLANOS_POR_PRESUPUESTO = 20
MAX_MEDICIONES_POR_PLANO = 500
MAX_ELEMENTOS_POR_PLANO = 4000

# Grosor por defecto de un tabique cuando el plano es nuevo o no se ha
# declarado todavía. Coincide con el default de ``PlanoObra`` y con la
# opción del editor: 10 cm (tabiquería interior estándar). Los planos
# importados de AutoCAD/CAD o de constructoras latinoamericanas suelen
# trabajar entre 10 y 15 cm, por lo que este es un buen punto de partida.
GROSOR_TABIQUE_DEFECTO_CM = 10.0
# Rango válido para evitar valores absurdos al teclear (1 mm a 100 cm).
GROSOR_TABIQUE_MIN_CM = 0.1
GROSOR_TABIQUE_MAX_CM = 100.0

# Escala interna de los planos dibujados desde cero (``origen='dibujado'``).
# 1 px = 1 cm real: el usuario dibuja a escala real y las medidas en metros
# salen directas, sin necesidad de calibrar una distancia conocida.
ESCALA_LIENZO_DIBUJO_PX_M = 100.0


class ErrorPlano(ValueError):
    pass


def _validar_archivo(nombre: str, contenido: bytes) -> tuple[str, str]:
    """Valida extensión y contenido, devuelve (ext, content_type)"""
    if not contenido or len(contenido) > MAX_PLANO_BYTES:
        raise ErrorPlano("El plano supera 12 MB o está vacío.")
    ext = Path(nombre or "").suffix.lower()
    if ext not in EXT_PLANOS_IMG and ext not in EXT_PLANOS_PDF:
        raise ErrorPlano("Formato no soportado. Usa PNG, JPG, WEBP o PDF.")
    if ext in EXT_PLANOS_PDF:
        if not contenido.startswith(b"%PDF-"):
            raise ErrorPlano("El PDF no es válido.")
        return ext, "application/pdf"
    # Imagen
    try:
        from PIL import Image
        with Image.open(io.BytesIO(contenido)) as im:
            w, h = im.size
            if w <= 0 or h <= 0 or w * h > 40_000_000:
                raise ErrorPlano("Imagen demasiado grande o corrupta.")
            im.verify()
            fmt = (im.format or "").upper()
    except ErrorPlano:
        raise
    except Exception:
        raise ErrorPlano("No se pudo leer la imagen. Usa PNG/JPG válido.")
    mime = {"PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp"}.get(fmt, "image/png")
    return ext, mime


def _pdf_a_imagen(contenido_pdf: bytes) -> tuple[bytes, int, int]:
    """
    Convierte primera página de PDF a PNG usando PyMuPDF si está disponible,
    si no, devuelve el PDF tal cual y dimensiones None (el frontend usará pdf.js).
    Para MVP, si no hay librería, guardamos PDF y el frontend lo renderiza.
    """
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=contenido_pdf, filetype="pdf")
        if len(doc) == 0:
            raise ErrorPlano("PDF vacío.")
        page = doc[0]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x para calidad
        img_bytes = pix.tobytes("png")
        w, h = pix.width, pix.height
        doc.close()
        return img_bytes, w, h
    except ImportError:
        # Sin PyMuPDF, devolver PDF y dejar que frontend use pdf.js
        return contenido_pdf, 0, 0
    except ErrorPlano:
        raise
    except Exception as e:
        # Fallback: guardar PDF
        return contenido_pdf, 0, 0


def _distancia_px(puntos: list[list[float]]) -> float:
    """Suma distancia euclídea entre puntos consecutivos"""
    if len(puntos) < 2:
        return 0.0
    total = 0.0
    for i in range(1, len(puntos)):
        x0, y0 = puntos[i-1]
        x1, y1 = puntos[i]
        total += math.hypot(x1 - x0, y1 - y0)
    return total


def _area_px(puntos: list[list[float]]) -> float:
    """Área polígono por Shoelace, en px²"""
    if len(puntos) < 3:
        return 0.0
    s = 0.0
    n = len(puntos)
    for i in range(n):
        x0, y0 = puntos[i]
        x1, y1 = puntos[(i+1) % n]
        s += x0 * y1 - x1 * y0
    return abs(s) / 2.0


ALTURA_LIBRE_DEFECTO_M = 2.5


def _clamp_grosor_cm(valor: Any) -> float:
    """Devuelve un grosor de tabique utilizable (en cm) o el default.

    Se aplica tanto al crear planos como al recalibrar: un valor
    claramente inválido (negativo, no numérico, o fuera del rango
    físicamente plausible) cae al default de 10 cm en lugar de
    propagarse al resto de mediciones.
    """
    try:
        grosor = float(valor)
    except (TypeError, ValueError):
        return GROSOR_TABIQUE_DEFECTO_CM
    if grosor < GROSOR_TABIQUE_MIN_CM or grosor > GROSOR_TABIQUE_MAX_CM:
        return GROSOR_TABIQUE_DEFECTO_CM
    return round(grosor, 2)


def grosor_px_plano(plano: PlanoObra) -> float:
    """Grosor del tabique en píxeles del lienzo del plano.

    Si el plano todavía no está calibrado devuelve el grosor por defecto
    convertido a píxeles sobre un lienzo ``px=1 m`` arbitrario: el
    resultado sirve para que las heurísticas de detección (que sí
    necesitan un número) puedan funcionar, sin pretender ser la medida
    definitiva. En cuanto el usuario calibre, ``grosor_px_plano``
    empezará a usar la escala real.
    """
    if not plano or not getattr(plano, "escala_px_por_metro", None):
        # Equivale a 10 cm sobre una hipotética imagen de 100 px/m.
        return 10.0
    return max(1.0, plano.grosor_tabique_m * float(plano.escala_px_por_metro))


def _perimetro_cerrado_px(puntos: list[list[float]]) -> float:
    """Perímetro de un polígono, incluyendo el cierre si falta."""
    if len(puntos) < 2:
        return 0.0
    px = _distancia_px(puntos)
    if len(puntos) >= 3:
        x0, y0 = puntos[0]
        x1, y1 = puntos[-1]
        cierre = math.hypot(x1 - x0, y1 - y0)
        if cierre > 1e-6:
            px += cierre
    return px


def metricas_estancia(
    puntos: list[list[float]],
    escala_px_por_m: float | None,
    altura_m: float | None = None,
    grosor_tabique_m: float | None = None,
) -> dict[str, Any]:
    """Suelo, perímetro y desarrollo de paredes a partir del polígono.

    Sin calibrar se informan píxeles. Con escala, el suelo va en m², el
    perímetro en m y las paredes en m² (perímetro × altura).

    El grosor del tabique es informativo: el motor real descuenta en la
    barrera detectada y al ajustar los límites compartidos entre
    estancias; aquí se expone para que la UI pueda mostrarlo al
    usuario y entienda de dónde sale cada medida.
    """
    altura = float(altura_m) if altura_m and altura_m > 0 else ALTURA_LIBRE_DEFECTO_M
    area_px2 = _area_px(puntos)
    perimetro_px = _perimetro_cerrado_px(puntos)
    extras: dict[str, Any] = {"altura_m": altura}
    if grosor_tabique_m and grosor_tabique_m > 0:
        extras["grosor_tabique_m"] = round(float(grosor_tabique_m), 3)
    if not escala_px_por_m or escala_px_por_m <= 0:
        return {
            "suelo": round(area_px2, 2),
            "suelo_unidad": "px2",
            "perimetro": round(perimetro_px, 2),
            "perimetro_unidad": "px",
            "paredes": None,
            "paredes_unidad": "m2",
            "calibrado": False,
            **extras,
        }
    factor = 1.0 / escala_px_por_m
    suelo = area_px2 * (factor ** 2)
    perimetro = perimetro_px * factor
    return {
        "suelo": round(suelo, 2),
        "suelo_unidad": "m2",
        "perimetro": round(perimetro, 2),
        "perimetro_unidad": "m",
        "paredes": round(perimetro * altura, 2),
        "paredes_unidad": "m2",
        "calibrado": True,
        **extras,
    }


def calcular_valor_real(tipo: str, puntos: list[list[float]], escala_px_por_m: float | None) -> tuple[float, str]:
    """
    Calcula valor real a partir de puntos y escala.
    Devuelve (valor, unidad)
    """
    if not escala_px_por_m or escala_px_por_m <= 0:
        # Sin calibrar, devolver valor en px
        if tipo == "lineal":
            return _distancia_px(puntos), "px"
        elif tipo in ("area",):
            return _area_px(puntos), "px2"
        elif tipo == "perimetro":
            return _distancia_px(puntos), "px"
        elif tipo == "conteo":
            return float(len(puntos)), "ud"
        else:
            return 0.0, "px"

    # Con escala: 1 m = escala_px_por_m px
    factor = 1.0 / escala_px_por_m  # m por px
    if tipo == "lineal":
        px = _distancia_px(puntos)
        return px * factor, "m"
    elif tipo == "area":
        px2 = _area_px(puntos)
        return px2 * (factor ** 2), "m2"
    elif tipo == "perimetro":
        px = _distancia_px(puntos)
        # Si polígono cerrado, añadir cierre
        if len(puntos) >= 3:
            x0, y0 = puntos[0]
            x1, y1 = puntos[-1]
            if math.hypot(x1-x0, y1-y0) > 1e-6:
                px += math.hypot(x1-x0, y1-y0)
        return px * factor, "m"
    elif tipo == "conteo":
        return float(len(puntos)), "ud"
    elif tipo == "volumen":
        # Volumen no directo, por ahora área * altura? devolver área
        px2 = _area_px(puntos)
        return px2 * (factor ** 2), "m2"
    return 0.0, "m"


# --------------------------------------------------------------------------- #
# Detección automática local de estancias
# --------------------------------------------------------------------------- #

def _umbral_otsu(histograma: list[int], total: int) -> int:
    """Umbral de tinta adaptativo sin depender de OpenCV ni de servicios externos."""
    suma_total = sum(i * n for i, n in enumerate(histograma))
    peso_fondo = 0
    suma_fondo = 0.0
    mejor_varianza = -1.0
    mejor = 128
    for nivel, cantidad in enumerate(histograma):
        peso_fondo += cantidad
        if peso_fondo == 0:
            continue
        peso_frente = total - peso_fondo
        if peso_frente <= 0:
            break
        suma_fondo += nivel * cantidad
        media_fondo = suma_fondo / peso_fondo
        media_frente = (suma_total - suma_fondo) / peso_frente
        varianza = peso_fondo * peso_frente * (media_fondo - media_frente) ** 2
        if varianza > mejor_varianza:
            mejor_varianza = varianza
            mejor = nivel
    # Los planos suelen tener fondo blanco y tinta negra/gris. El margen recoge
    # el antialias de las líneas sin convertir sombras claras en paredes.
    return max(45, min(215, mejor + 18))


def _runs_tinta(valores: list[int], max_hueco: int, largo_minimo: int) -> list[tuple[int, int]]:
    """Une tramos de tinta alineados, cerrando huecos típicos de puertas.

    Exige tramos con entidad a ambos lados del hueco. Así un «3.50» escrito
    junto a un muro no se convierte en un tabique extra.
    """
    runs: list[tuple[int, int, int]] = []
    inicio = None
    for i, valor in enumerate(valores):
        if valor:
            if inicio is None:
                inicio = i
        elif inicio is not None:
            runs.append((inicio, i - 1, i - inicio))
            inicio = None
    if inicio is not None:
        runs.append((inicio, len(valores) - 1, len(valores) - inicio))
    if not runs:
        return []

    # Un dígito o un tick de cota suele medir pocos píxeles. Solo se
    # puentea cuando ambos lados parecen un muro de verdad.
    tinta_minima_lado = max(10, largo_minimo // 4)
    unidos: list[tuple[int, int, int]] = [runs[0]]
    for inicio, fin, tinta in runs[1:]:
        anterior_i, anterior_f, anterior_tinta = unidos[-1]
        hueco = inicio - anterior_f - 1
        lados_utiles = anterior_tinta >= tinta_minima_lado and tinta >= tinta_minima_lado
        if hueco <= max_hueco and lados_utiles:
            unidos[-1] = (anterior_i, fin, anterior_tinta + tinta)
        else:
            unidos.append((inicio, fin, tinta))

    salida = []
    for inicio, fin, tinta in unidos:
        largo = fin - inicio + 1
        densidad = tinta / max(1, largo)
        if largo >= largo_minimo and densidad >= 0.32:
            salida.append((inicio, fin))
    return salida


def _componentes_tinta(tinta: list[int] | bytearray, ancho: int, alto: int) -> list[dict[str, Any]]:
    """Componentes 4-conectados de tinta para distinguir cotas de muros."""
    visitado = bytearray(ancho * alto)
    componentes: list[dict[str, Any]] = []
    for origen in range(ancho * alto):
        if visitado[origen] or not tinta[origen]:
            continue
        cola = deque([origen])
        visitado[origen] = 1
        pixeles: list[int] = []
        min_x = ancho
        max_x = 0
        min_y = alto
        max_y = 0
        while cola:
            indice = cola.popleft()
            pixeles.append(indice)
            y, x = divmod(indice, ancho)
            min_x = min(min_x, x)
            max_x = max(max_x, x)
            min_y = min(min_y, y)
            max_y = max(max_y, y)
            if x > 0:
                vecino = indice - 1
                if not visitado[vecino] and tinta[vecino]:
                    visitado[vecino] = 1
                    cola.append(vecino)
            if x + 1 < ancho:
                vecino = indice + 1
                if not visitado[vecino] and tinta[vecino]:
                    visitado[vecino] = 1
                    cola.append(vecino)
            if y > 0:
                vecino = indice - ancho
                if not visitado[vecino] and tinta[vecino]:
                    visitado[vecino] = 1
                    cola.append(vecino)
            if y + 1 < alto:
                vecino = indice + ancho
                if not visitado[vecino] and tinta[vecino]:
                    visitado[vecino] = 1
                    cola.append(vecino)
        componentes.append({
            "pixeles": pixeles,
            "area": len(pixeles),
            "min_x": min_x,
            "max_x": max_x,
            "min_y": min_y,
            "max_y": max_y,
        })
    return componentes


def _es_anotacion_cota(comp: dict[str, Any], dim_menor: int) -> bool:
    """Números, ticks y líneas de cota: no son tabiques."""
    w = comp["max_x"] - comp["min_x"] + 1
    h = comp["max_y"] - comp["min_y"] + 1
    largo = max(w, h)
    corto = min(w, h)
    area = comp["area"]
    bbox = max(1, w * h)
    densidad = area / bbox
    aspect = largo / max(1, corto)
    alto_texto = max(16, round(dim_menor * 0.048))
    area_texto = max(70, round(dim_menor * dim_menor * 0.0011))

    if area <= 22:
        return True
    # Dígitos, cotas «3.50», flechas y símbolos compactos.
    if largo <= alto_texto and area <= area_texto and aspect <= 5.2:
        return True
    # Tick o trazo de acotación: corto y muy delgado.
    if corto <= 3 and largo <= alto_texto * 1.6:
        return True
    # Línea de cota fina y larga, sin el cuerpo de un muro.
    if corto <= 2 and aspect >= 7 and densidad <= 0.55:
        return True
    return False


def _borrar_anotaciones_cotas(tinta: bytearray, ancho: int, alto: int) -> bytearray:
    """Borra cotas numéricas y sus ticks para que no se lean como muros."""
    dim_menor = min(ancho, alto)
    componentes = _componentes_tinta(tinta, ancho, alto)
    anotaciones = [c for c in componentes if _es_anotacion_cota(c, dim_menor)]
    if not anotaciones:
        return tinta

    limpio = bytearray(tinta)
    for comp in anotaciones:
        for indice in comp["pixeles"]:
            limpio[indice] = 0

    # Las líneas de cota suelen acompañar al número. Se borran trazos finos
    # que quedan pegados a una anotación recién eliminada.
    margen = max(6, round(dim_menor * 0.018))
    restantes = [c for c in componentes if not _es_anotacion_cota(c, dim_menor)]
    for texto in anotaciones:
        caja = (
            texto["min_x"] - margen,
            texto["min_y"] - margen,
            texto["max_x"] + margen,
            texto["max_y"] + margen,
        )
        for comp in restantes:
            w = comp["max_x"] - comp["min_x"] + 1
            h = comp["max_y"] - comp["min_y"] + 1
            corto = min(w, h)
            if corto > 4:
                continue
            solapa = not (
                comp["max_x"] < caja[0]
                or comp["min_x"] > caja[2]
                or comp["max_y"] < caja[1]
                or comp["min_y"] > caja[3]
            )
            if solapa:
                for indice in comp["pixeles"]:
                    limpio[indice] = 0
    return limpio


def _pintar_run_direccion(
    barrera: bytearray,
    ancho: int,
    alto: int,
    origen_x: int,
    origen_y: int,
    dx: int,
    dy: int,
    tinta: list[int] | bytearray,
    max_hueco: int,
    largo_minimo: int,
    grosor: int,
) -> None:
    """Prolonga un muro en una dirección (incluye diagonales)."""
    valores: list[int] = []
    coords: list[tuple[int, int]] = []
    x, y = origen_x, origen_y
    while 0 <= x < ancho and 0 <= y < alto:
        valores.append(1 if tinta[y * ancho + x] else 0)
        coords.append((x, y))
        x += dx
        y += dy
    for i0, i1 in _runs_tinta(valores, max_hueco, largo_minimo):
        for i in range(i0, i1 + 1):
            cx, cy = coords[i]
            for yy in range(max(0, cy - grosor), min(alto, cy + grosor + 1)):
                for xx in range(max(0, cx - grosor), min(ancho, cx + grosor + 1)):
                    barrera[yy * ancho + xx] = 1


def _runs_tinta_todas(tinta: list[int] | bytearray, ancho: int, alto: int) -> tuple[list[list[tuple[int, int]]], list[list[tuple[int, int]]]]:
    """Todas las tiradas de tinta por fila y por columna (sin filtrar largo).

    Devuelve ``(filas, columnas)`` donde ``filas[y]`` es la lista de
    intervalos ``(x0, x1)`` con tinta en la fila ``y`` y ``columnas[x]``
    la lista de ``(y0, y1)`` con tinta en la columna ``x``. Se usa para
    rellenar el hueco de los muros de doble línea.
    """
    filas: list[list[tuple[int, int]]] = []
    for y in range(alto):
        base = y * ancho
        runs: list[tuple[int, int]] = []
        x = 0
        while x < ancho:
            if tinta[base + x]:
                x0 = x
                while x < ancho and tinta[base + x]:
                    x += 1
                runs.append((x0, x - 1))
            else:
                x += 1
        filas.append(runs)
    columnas: list[list[tuple[int, int]]] = []
    for x in range(ancho):
        runs: list[tuple[int, int]] = []
        y = 0
        while y < alto:
            if tinta[y * ancho + x]:
                y0 = y
                while y < alto and tinta[y * ancho + x]:
                    y += 1
                runs.append((y0, y - 1))
            else:
                y += 1
        columnas.append(runs)
    return filas, columnas


def _extremo_vertical_muro(
    tinta: list[int] | bytearray,
    ancho: int,
    alto: int,
    y: int,
    x0: int,
    x1: int,
    tope: int,
) -> tuple[int, int]:
    """Filas ``(top, bot)`` del cuerpo de un muro horizontal en la fila ``y``.

    Sonda varias columnas del tramo y se queda con la mediana de los extremos:
    así una puerta (que vacía la columna central) o una esquina (que une con
    un muro perpendicular) no deforman la medida del espesor real.
    """
    tops: list[int] = []
    bots: list[int] = []
    for frac in (0.15, 0.3, 0.5, 0.7, 0.85):
        cx = min(ancho - 1, max(0, x0 + int((x1 - x0) * frac)))
        t = y
        while t > 0 and y - t < tope and tinta[(t - 1) * ancho + cx]:
            t -= 1
        b = y
        while b + 1 < alto and b - y < tope and tinta[(b + 1) * ancho + cx]:
            b += 1
        tops.append(t)
        bots.append(b)
    tops.sort()
    bots.sort()
    return tops[len(tops) // 2], bots[len(bots) // 2]


def _extremo_horizontal_muro(
    tinta: list[int] | bytearray,
    ancho: int,
    alto: int,
    x: int,
    y0: int,
    y1: int,
    tope: int,
) -> tuple[int, int]:
    """Columnas ``(left, right)`` del cuerpo de un muro vertical en la columna ``x``."""
    lefts: list[int] = []
    rights: list[int] = []
    for frac in (0.15, 0.3, 0.5, 0.7, 0.85):
        cy = min(alto - 1, max(0, y0 + int((y1 - y0) * frac)))
        l = x
        while l > 0 and x - l < tope and tinta[cy * ancho + (l - 1)]:
            l -= 1
        r = x
        while r + 1 < ancho and r - x < tope and tinta[cy * ancho + (r + 1)]:
            r += 1
        lefts.append(l)
        rights.append(r)
    lefts.sort()
    rights.sort()
    return lefts[len(lefts) // 2], rights[len(rights) // 2]


def _medir_espesor_muros(
    tinta: list[int] | bytearray,
    ancho: int,
    alto: int,
    runs_horiz: list[tuple[int, int, int]],
    runs_vert: list[tuple[int, int, int]],
) -> int | None:
    """Mediana del espesor real (px) de los muros de la imagen.

    Mide el cuerpo de los tramos largos horizontales y verticales (los que
    parecen muros de verdad) y devuelve la mediana, acotada a un rango
    plausible. ``None`` si no hay muros medibles.
    """
    tope = max(4, min(80, round(min(ancho, alto) * 0.08)))
    espesores: list[int] = []
    for y, x0, x1 in runs_horiz:
        top, bot = _extremo_vertical_muro(tinta, ancho, alto, y, x0, x1, tope)
        if bot - top + 1 >= 2:
            espesores.append(bot - top + 1)
    for x, y0, y1 in runs_vert:
        left, right = _extremo_horizontal_muro(tinta, ancho, alto, x, y0, y1, tope)
        if right - left + 1 >= 2:
            espesores.append(right - left + 1)
    if not espesores:
        return None
    espesores.sort()
    mediana = espesores[len(espesores) // 2]
    tope_final = max(4, min(60, round(min(ancho, alto) * 0.06)))
    return int(max(2, min(mediana, tope_final)))


def _rdp(puntos: list[list[float]], epsilon: float) -> list[list[float]]:
    """Simplificación Ramer-Douglas-Peucker de un trazado abierto."""
    if len(puntos) <= 2:
        return puntos
    x1, y1 = puntos[0]
    x2, y2 = puntos[-1]
    dx, dy = x2 - x1, y2 - y1
    largo = math.hypot(dx, dy)
    maxima = -1.0
    indice = 0
    for i, (x, y) in enumerate(puntos[1:-1], 1):
        if largo <= 1e-9:
            distancia = math.hypot(x - x1, y - y1)
        else:
            distancia = abs(dy * x - dx * y + x2 * y1 - y2 * x1) / largo
        if distancia > maxima:
            maxima = distancia
            indice = i
    if maxima > epsilon:
        izquierda = _rdp(puntos[: indice + 1], epsilon)
        derecha = _rdp(puntos[indice:], epsilon)
        return izquierda[:-1] + derecha
    return [puntos[0], puntos[-1]]


def _ortogonalizar_poligono(puntos: list[list[float]], tolerancia_deg: float = 14.0) -> list[list[float]]:
    """Alinea tramos casi horizontales/verticales y conserva diagonales reales."""
    if len(puntos) < 3:
        return puntos
    pts = [p[:] for p in puntos]
    n = len(pts)
    for i in range(n):
        a = pts[i]
        b = pts[(i + 1) % n]
        dx, dy = b[0] - a[0], b[1] - a[1]
        if abs(dx) < 1e-6 and abs(dy) < 1e-6:
            continue
        ang = abs(math.degrees(math.atan2(dy, dx))) % 180.0
        if ang <= tolerancia_deg or ang >= 180.0 - tolerancia_deg:
            y = (a[1] + b[1]) / 2.0
            a[1] = b[1] = y
        elif abs(ang - 90.0) <= tolerancia_deg:
            x = (a[0] + b[0]) / 2.0
            a[0] = b[0] = x
    limpios: list[list[float]] = []
    for punto in pts:
        red = [round(punto[0], 2), round(punto[1], 2)]
        if not limpios or distancia_entre_puntos(limpios[-1], red) > 0.8:
            limpios.append(red)
    if len(limpios) >= 3 and distancia_entre_puntos(limpios[0], limpios[-1]) < 0.8:
        limpios.pop()
    return limpios


def _poligono_desde_filas(
    filas: dict[int, tuple[int, int]],
    factor_x: float,
    factor_y: float,
    ancho_original: int,
    alto_original: int,
) -> list[list[float]]:
    """Convierte la envolvente por filas de una estancia en un polígono editable."""
    ys = sorted(filas)
    if len(ys) < 2:
        return []
    izquierda = [[float(filas[y][0]), float(y)] for y in ys]
    derecha = [[float(filas[y][1] + 1), float(y)] for y in reversed(ys)]
    trazado = izquierda + derecha
    alto_estancia = max(1, ys[-1] - ys[0])
    anchos = [filas[y][1] - filas[y][0] + 1 for y in ys]
    ancho_estancia = max(anchos) if anchos else 1
    # Epsilon más generoso: colapsa la escalera de una diagonal real y no
    # deja cada diente de antialias como un «tabique».
    epsilon = max(3.0, min(ancho_estancia, alto_estancia) * 0.045, 8.0)
    simplificado = _rdp(trazado, epsilon)
    while len(simplificado) > 48:
        epsilon *= 1.3
        simplificado = _rdp(trazado, epsilon)

    resultado: list[list[float]] = []
    for x, y in simplificado:
        punto = [
            round(min(ancho_original, max(0.0, x * factor_x)), 2),
            round(min(alto_original, max(0.0, y * factor_y)), 2),
        ]
        if not resultado or distancia_entre_puntos(resultado[-1], punto) > 0.5:
            resultado.append(punto)
    return _ortogonalizar_poligono(resultado)


def distancia_entre_puntos(a: list[float], b: list[float]) -> float:
    return math.hypot(float(a[0]) - float(b[0]), float(a[1]) - float(b[1]))


def _ajustar_limites_compartidos(
    candidatos: list[dict[str, Any]],
    banda_px: float,
) -> None:
    """Alisa las caras de dos estancias separadas por un tabique.

    El relleno por inundación termina en la cara interior de la barrera
    rasterizada, que ahora se pega al muro. Cada recinto conserva su propia
    cara: la estancia de la izquierda se pega a la cara derecha del tabique y
    la de la derecha a la cara izquierda. El ajuste solo alisa el ruido del
    raster agrupando las caras de una misma línea de tabique (sin colapsarlas
    a un eje central, que dejaría medio muro dentro de cada estancia).
    """
    if len(candidatos) < 2:
        return

    def extremos(candidato: dict[str, Any]) -> tuple[float, float, float, float]:
        puntos = candidato.get("puntos") or []
        if not puntos:
            return 0.0, 0.0, 0.0, 0.0
        xs = [float(p[0]) for p in puntos]
        ys = [float(p[1]) for p in puntos]
        return min(xs), min(ys), max(xs), max(ys)

    def solapa(a0: float, a1: float, b0: float, b1: float) -> float:
        return max(0.0, min(a1, b1) - max(a0, b0))

    parejas: list[dict[str, Any]] = []
    for i, primero in enumerate(candidatos):
        ax0, ay0, ax1, ay1 = extremos(primero)
        for segundo in candidatos[i + 1 :]:
            bx0, by0, bx1, by1 = extremos(segundo)

            # Borde vertical enfrentado: estancia | tabique | estancia.
            solapa_y = solapa(ay0, ay1, by0, by1)
            if ax1 <= bx0 and bx0 - ax1 <= banda_px and solapa_y >= min(ay1 - ay0, by1 - by0) * 0.30:
                parejas.append({
                    "eje": 0, "primero": primero, "segundo": segundo,
                    "borde_primero": ax1, "borde_segundo": bx0,
                    "tramo0": max(ay0, by0), "tramo1": min(ay1, by1),
                })

            # Borde horizontal enfrentado.
            solapa_x = solapa(ax0, ax1, bx0, bx1)
            if ay1 <= by0 and by0 - ay1 <= banda_px and solapa_x >= min(ax1 - ax0, bx1 - bx0) * 0.30:
                parejas.append({
                    "eje": 1, "primero": primero, "segundo": segundo,
                    "borde_primero": ay1, "borde_segundo": by0,
                    "tramo0": max(ax0, bx0), "tramo1": min(ax1, bx1),
                })

    def poner_borde(puntos: list[list[float]], eje: int, extremo: float, nuevo: float) -> bool:
        tolerancia = max(2.0, banda_px * 0.6)
        indices = [i for i, punto in enumerate(puntos) if abs(float(punto[eje]) - extremo) <= tolerancia]
        # Dos puntos o más evitan tocar un vértice suelto de una diagonal.
        if len(indices) < 2:
            return False
        for i in indices:
            puntos[i][eje] = round(nuevo, 2)
        return True

    # Agrupa segmentos de una misma línea por lado (cara "primero" y cara
    # "segundo" por separado) y ajusta cada lado a su mediana. Así la cara de
    # cada estancia queda pegada a su lado del tabique y el espesor del muro
    # permanece entre ambas.
    tolerancia_linea = max(4.0, banda_px * 0.6)
    for eje in (0, 1):
        for lado in ("borde_primero", "borde_segundo"):
            grupos: list[list[dict[str, Any]]] = []
            for pareja in [p for p in parejas if p["eje"] == eje]:
                valor = pareja[lado]
                colocado = False
                for grupo in grupos:
                    media = sum(g[lado] for g in grupo) / len(grupo)
                    tramo0 = min(g["tramo0"] for g in grupo)
                    tramo1 = max(g["tramo1"] for g in grupo)
                    if abs(valor - media) <= tolerancia_linea and pareja["tramo0"] <= tramo1 + banda_px and pareja["tramo1"] >= tramo0 - banda_px:
                        grupo.append(pareja)
                        colocado = True
                        break
                if not colocado:
                    grupos.append([pareja])
            for grupo in grupos:
                media = round(sum(g[lado] for g in grupo) / len(grupo), 2)
                for pareja in grupo:
                    if poner_borde(pareja["primero" if lado == "borde_primero" else "segundo"]["puntos"], eje, pareja[lado], media):
                        if lado == "borde_primero":
                            if eje == 0:
                                pareja["primero"]["bbox"][2] = media
                            else:
                                pareja["primero"]["bbox"][3] = media
                        else:
                            if eje == 0:
                                pareja["segundo"]["bbox"][0] = media
                            else:
                                pareja["segundo"]["bbox"][1] = media

    for candidato in candidatos:
        candidato["area_px2"] = round(_area_px(candidato.get("puntos") or []), 2)


def detectar_espacios_plano(
    contenido: bytes,
    content_type: str = "",
    max_espacios: int = 30,
    grosor_tabique_px: float | None = None,
) -> list[dict[str, Any]]:
    """Detecta recintos cerrados de una planta y devuelve polígonos candidatos.

    Visión geométrica local: quita cotas y números, reconoce muros también en
    diagonal, cierra huecos de puerta y segmenta los recintos que no tocan el
    borde. No envía el archivo a una IA.

    ``grosor_tabique_px`` es el grosor del muro **en píxeles de la imagen
    original** (no de la copia de trabajo). Si el usuario lo ha declarado, se
    usa para engrosar la barrera: dos recintos separados por un tabique de N
    píxeles ven una franja barrera coherente y la heurística de ajuste de
    bordes compartidos funciona con el mismo criterio. Si no se informa, se
    infiere del ancho medio de los trazos verticales/horizontales: el
    sistema mide unos cuantos muros y elige el grueso más frecuente (modo
    robusto por defecto).
    """
    if content_type and not content_type.lower().startswith("image/"):
        raise ErrorPlano("La detección automática requiere un plano PNG, JPG o WEBP.")
    max_espacios = max(1, min(int(max_espacios), 30))
    try:
        from PIL import Image

        with Image.open(io.BytesIO(contenido)) as original:
            original.load()
            gris = original.convert("L")
            ancho_original, alto_original = gris.size
    except Exception as exc:
        raise ErrorPlano("No se pudo analizar la imagen del plano.") from exc

    if ancho_original < 80 or alto_original < 80:
        raise ErrorPlano("El plano es demasiado pequeño para detectar estancias.")

    max_dimension = 1100
    escala_reduccion = min(1.0, max_dimension / max(ancho_original, alto_original))
    ancho = max(1, round(ancho_original * escala_reduccion))
    alto = max(1, round(alto_original * escala_reduccion))
    if (ancho, alto) != (ancho_original, alto_original):
        gris = gris.resize((ancho, alto), Image.Resampling.LANCZOS)

    histograma = gris.histogram()
    umbral = _umbral_otsu(histograma, ancho * alto)
    tinta_img = gris.point(lambda p: 255 if p <= umbral else 0, mode="L")
    tinta_cruda = bytearray(1 if valor else 0 for valor in tinta_img.tobytes())
    tinta = _borrar_anotaciones_cotas(tinta_cruda, ancho, alto)

    dimension_menor = min(ancho, alto)
    max_hueco = max(6, min(48, round(dimension_menor * 0.055)))
    largo_minimo = max(28, round(dimension_menor * 0.09))
    grosor_base = max(1, min(2, round(dimension_menor / 480)))

    # Tiradas de tinta por fila/columna. Las largas (puertas puenteadas) son
    # las que parecen muro; las brutas sirven para rellenar dobles líneas.
    filas_tinta, columnas_tinta = _runs_tinta_todas(tinta, ancho, alto)
    runs_horiz: list[tuple[int, int, int]] = []
    for y, runs in enumerate(filas_tinta):
        fila = [tinta[y * ancho + x] for x in range(ancho)]
        for x0, x1 in _runs_tinta(fila, max_hueco, largo_minimo):
            runs_horiz.append((y, x0, x1))
    runs_vert: list[tuple[int, int, int]] = []
    for x in range(ancho):
        columna = [tinta[y * ancho + x] for y in range(alto)]
        for y0, y1 in _runs_tinta(columna, max_hueco, largo_minimo):
            runs_vert.append((x, y0, y1))

    # Espesor real del muro medido sobre la imagen. Tiene prioridad sobre el
    # grosor declarado (que depende de una escala que puede no estar
    # calibrada) y sobre el grosor base. El antiguo motor aplicaba el grosor
    # declarado como relleno extra alrededor de cada trazo, engordando los
    # tabiques varios centímetros hacia el interior de la estancia; medir el
    # trazo real hace que la barrera se pegue a la cara del tabique.
    espesor_medido = _medir_espesor_muros(
        tinta, ancho, alto, runs_horiz, runs_vert
    )
    if espesor_medido:
        grosor_px_trabajo = float(espesor_medido)
    elif grosor_tabique_px and grosor_tabique_px > 0:
        grosor_px_trabajo = max(1.0, float(grosor_tabique_px) * escala_reduccion)
    else:
        grosor_px_trabajo = float(grosor_base)

    grosor_barrera = max(1, int(round(grosor_px_trabajo)))
    tope_cuerpo = max(6, grosor_barrera * 6)

    # Barrera que se pega a la cara del muro:
    # 1) tinta + 1 px de dilatación (cierra el antialias);
    # 2) cuerpo del muro relleno hasta su cara real (no se engorda);
    # 3) muros de doble línea: se rellena el hueco entre caras paralelas.
    barrera = bytearray(tinta)
    for y in range(alto):
        base = y * ancho
        for x in range(ancho):
            if not tinta[base + x]:
                continue
            for yy in range(max(0, y - 1), min(alto, y + 2)):
                bb = yy * ancho
                for xx in range(max(0, x - 1), min(ancho, x + 2)):
                    barrera[bb + xx] = 1

    # Muros horizontales: rellena el cuerpo entre sus caras reales (la
    # tirada ya puentea los huecos de puerta, así el hueco queda cerrado).
    for y, x0, x1 in runs_horiz:
        top, bot = _extremo_vertical_muro(tinta, ancho, alto, y, x0, x1, tope_cuerpo)
        for yy in range(top, bot + 1):
            inicio = yy * ancho + x0
            barrera[inicio : yy * ancho + x1 + 1] = b"\x01" * (x1 - x0 + 1)

    # Muros verticales.
    for x, y0, y1 in runs_vert:
        left, right = _extremo_horizontal_muro(tinta, ancho, alto, x, y0, y1, tope_cuerpo)
        for xx in range(left, right + 1):
            for y in range(y0, y1 + 1):
                barrera[y * ancho + xx] = 1

    # Muros de doble línea (caras paralelas separadas por el hueco del muro):
    # rellena entre las dos caras para que el interior no se cuele como
    # recinto. Solo une caras próximas (espesor medido) y muy solapadas.
    tolerancia_hueco = max(2, grosor_barrera)
    for y, x0, x1 in runs_horiz:
        for yy in range(y + 1, min(alto, y + tolerancia_hueco + 1)):
            for a0, a1 in filas_tinta[yy]:
                if a1 - a0 + 1 < largo_minimo:
                    continue
                solapa = min(x1, a1) - max(x0, a0) + 1
                if solapa < max(12, min(x1 - x0, a1 - a0) * 0.6):
                    continue
                for rr in range(y, yy + 1):
                    inicio = rr * ancho + x0
                    barrera[inicio : rr * ancho + x1 + 1] = b"\x01" * (x1 - x0 + 1)
                break
    for x, y0, y1 in runs_vert:
        for xx in range(x + 1, min(ancho, x + tolerancia_hueco + 1)):
            for b0, b1 in columnas_tinta[xx]:
                if b1 - b0 + 1 < largo_minimo:
                    continue
                solapa = min(y1, b1) - max(y0, b0) + 1
                if solapa < max(12, min(y1 - y0, b1 - b0) * 0.6):
                    continue
                for cc in range(x, xx + 1):
                    for y in range(y0, y1 + 1):
                        barrera[y * ancho + cc] = 1
                break

    # Muros a 45° y 135°: sin esto un tabique diagonal se lee como escalera
    # de píxeles y parte mal las estancias. Se pinta con el espesor medido.
    grosor_diag = max(1, int(round(grosor_px_trabajo / 2.0)))
    for x in range(ancho):
        _pintar_run_direccion(barrera, ancho, alto, x, 0, 1, 1, tinta, max_hueco, largo_minimo, grosor_diag)
        _pintar_run_direccion(barrera, ancho, alto, x, alto - 1, 1, -1, tinta, max_hueco, largo_minimo, grosor_diag)
    for y in range(1, alto):
        _pintar_run_direccion(barrera, ancho, alto, 0, y, 1, 1, tinta, max_hueco, largo_minimo, grosor_diag)
        _pintar_run_direccion(barrera, ancho, alto, 0, y, 1, -1, tinta, max_hueco, largo_minimo, grosor_diag)

    visitado = bytearray(ancho * alto)
    area_minima = max(380, round(ancho * alto * 0.003))
    area_maxima = round(ancho * alto * 0.78)
    candidatos: list[dict[str, Any]] = []

    for origen in range(ancho * alto):
        if visitado[origen] or barrera[origen]:
            continue
        cola = deque([origen])
        visitado[origen] = 1
        area = 0
        toca_borde = False
        min_x = ancho
        max_x = 0
        min_y = alto
        max_y = 0
        filas: dict[int, tuple[int, int]] = {}

        while cola:
            indice = cola.popleft()
            y, x = divmod(indice, ancho)
            area += 1
            min_x = min(min_x, x)
            max_x = max(max_x, x)
            min_y = min(min_y, y)
            max_y = max(max_y, y)
            previo = filas.get(y)
            filas[y] = (x, x) if previo is None else (min(previo[0], x), max(previo[1], x))
            if x == 0 or y == 0 or x == ancho - 1 or y == alto - 1:
                toca_borde = True

            if x > 0:
                vecino = indice - 1
                if not visitado[vecino] and not barrera[vecino]:
                    visitado[vecino] = 1
                    cola.append(vecino)
            if x + 1 < ancho:
                vecino = indice + 1
                if not visitado[vecino] and not barrera[vecino]:
                    visitado[vecino] = 1
                    cola.append(vecino)
            if y > 0:
                vecino = indice - ancho
                if not visitado[vecino] and not barrera[vecino]:
                    visitado[vecino] = 1
                    cola.append(vecino)
            if y + 1 < alto:
                vecino = indice + ancho
                if not visitado[vecino] and not barrera[vecino]:
                    visitado[vecino] = 1
                    cola.append(vecino)

        bbox_area = max(1, (max_x - min_x + 1) * (max_y - min_y + 1))
        ocupacion = area / bbox_area
        anchura = max_x - min_x + 1
        altura = max_y - min_y + 1
        proporcion = max(anchura / max(1, altura), altura / max(1, anchura))
        if (
            toca_borde
            or area < area_minima
            or area > area_maxima
            or anchura < dimension_menor * 0.04
            or altura < dimension_menor * 0.04
            or proporcion > 10
            or ocupacion < 0.22
        ):
            continue

        puntos = _poligono_desde_filas(
            filas,
            ancho_original / ancho,
            alto_original / alto,
            ancho_original,
            alto_original,
        )
        if len(puntos) < 3:
            continue
        confianza = min(0.97, 0.56 + min(0.25, ocupacion * 0.25) + min(0.12, area / (ancho * alto)))
        candidatos.append({
            "tipo": "area",
            "puntos": puntos,
            "confianza": round(confianza, 2),
            "area_px2": round(_area_px(puntos), 2),
            "bbox": [
                round(min_x * ancho_original / ancho, 2),
                round(min_y * alto_original / alto, 2),
                round((max_x + 1) * ancho_original / ancho, 2),
                round((max_y + 1) * alto_original / alto, 2),
            ],
        })

    # El relleno por inundación ya termina en la cara interior del tabique
    # (la barrera se pega al muro). Reconciliamos las parejas adyacentes
    # alisando cada cara por separado —sin colapsarlas a un eje central— para
    # que cada estancia conserve su cara y el espesor del tabique quede entre
    # ambas. La banda de búsqueda es proporcional al espesor del muro.
    banda_busqueda_px = max(grosor_px_trabajo * 1.8, 6.0) / max(escala_reduccion, 1e-3)
    _ajustar_limites_compartidos(
        candidatos,
        banda_px=banda_busqueda_px,
    )

    candidatos.sort(key=lambda c: c["area_px2"], reverse=True)
    for numero, candidato in enumerate(candidatos[:max_espacios], 1):
        candidato["etiqueta"] = f"Estancia {numero}"
    return candidatos[:max_espacios]


def _bbox_puntos(puntos: list[list[float]]) -> tuple[float, float, float, float]:
    xs = [float(p[0]) for p in puntos]
    ys = [float(p[1]) for p in puntos]
    return min(xs), min(ys), max(xs), max(ys)


def _solapamiento_bbox(a: list[list[float]], b: list[list[float]]) -> float:
    if not a or not b:
        return 0.0
    ax0, ay0, ax1, ay1 = _bbox_puntos(a)
    bx0, by0, bx1, by1 = _bbox_puntos(b)
    inter = max(0.0, min(ax1, bx1) - max(ax0, bx0)) * max(0.0, min(ay1, by1) - max(ay0, by0))
    area_a = max(1.0, (ax1 - ax0) * (ay1 - ay0))
    area_b = max(1.0, (bx1 - bx0) * (by1 - by0))
    return inter / max(1.0, area_a + area_b - inter)


def guardar_detecciones_automaticas(
    db: Session,
    plano: PlanoObra,
    candidatos: list[dict[str, Any]],
) -> tuple[list[PlanoMedicion], int]:
    """Persiste candidatos nuevos y evita duplicarlos al volver a analizar."""
    existentes = list(plano.mediciones)
    creadas: list[PlanoMedicion] = []
    omitidas = 0
    colores = ("#2563eb", "#16a34a", "#9333ea", "#ea580c", "#0891b2", "#db2777")
    for candidato in candidatos:
        puntos = candidato.get("puntos") or []
        duplicada = any(
            med.tipo in ("area", "perimetro")
            and _solapamiento_bbox(med.puntos(), puntos) >= 0.78
            for med in existentes
        )
        if duplicada:
            omitidas += 1
            continue
        med = crear_medicion(
            db,
            plano,
            "area",
            str(candidato.get("etiqueta") or f"Estancia detectada {len(creadas) + 1}"),
            puntos,
            colores[len(creadas) % len(colores)],
            confirmar=False,
        )
        creadas.append(med)
        existentes.append(med)
    if creadas:
        db.commit()
        for med in creadas:
            db.refresh(med)
    return creadas, omitidas


def crear_plano(
    db: Session,
    presupuesto_id: int,
    nombre: str,
    archivo_nombre: str,
    contenido: bytes,
) -> PlanoObra:
    from ..storage import save_object

    # Contar planos existentes
    existentes = db.query(PlanoObra).filter(PlanoObra.presupuesto_id == presupuesto_id).count()
    if existentes >= MAX_PLANOS_POR_PRESUPUESTO:
        raise ErrorPlano(f"Máximo {MAX_PLANOS_POR_PRESUPUESTO} planos por presupuesto.")

    ext, mime = _validar_archivo(archivo_nombre, contenido)

    # Si PDF, intentar convertir a imagen
    ancho = alto = None
    contenido_guardar = contenido
    content_type_guardar = mime
    if ext == ".pdf":
        img_bytes, w, h = _pdf_a_imagen(contenido)
        if w and h:
            contenido_guardar = img_bytes
            content_type_guardar = "image/png"
            ancho, alto = w, h
            ext = ".png"
        else:
            # Guardar PDF tal cual, frontend lo renderizará
            ancho = alto = None

    if ext in EXT_PLANOS_IMG and (ancho is None or alto is None):
        try:
            from PIL import Image
            with Image.open(io.BytesIO(contenido_guardar)) as im:
                ancho, alto = im.size
        except Exception:
            ancho = alto = None

    plano = PlanoObra(
        presupuesto_id=presupuesto_id,
        nombre=(nombre or Path(archivo_nombre).stem)[:250] or "Plano",
        archivo="",  # se rellena tras save_object
        content_type=content_type_guardar,
        ancho_px=ancho,
        alto_px=alto,
    )
    db.add(plano)
    db.flush()  # para tener id

    # Guardar archivo
    try:
        guardado = save_object(
            db,
            contenido_guardar,
            "planos",
            f"{plano.id}{ext}",
            content_type_guardar,
            prefix=f"presupuesto-{presupuesto_id}/plano-{plano.id}",
        )
        plano.archivo = guardado.reference
    except Exception as exc:
        db.rollback()
        raise ErrorPlano(f"No se pudo guardar el plano: {exc}") from exc

    db.commit()
    return plano


def calibrar_plano(
    db: Session,
    plano: PlanoObra,
    distancia_px: float,
    distancia_real: float,
    unidad: str = "m",
    altura_libre_m: float | None = None,
) -> PlanoObra:
    if distancia_px <= 0 or distancia_real <= 0:
        raise ErrorPlano("Distancias de calibración deben ser positivas.")
    if distancia_px > 10000 or distancia_real > 10000:
        raise ErrorPlano("Calibración fuera de rango.")

    unidad = (unidad or "m").strip().lower()
    # Convertir a metros
    factor_unidad = {"m": 1.0, "cm": 0.01, "mm": 0.001, "km": 1000.0}.get(unidad, 1.0)
    distancia_real_m = distancia_real * factor_unidad

    escala = distancia_px / distancia_real_m  # px por metro

    plano.escala_px_por_metro = escala
    plano.calibracion_px = distancia_px
    plano.calibracion_real = distancia_real_m
    plano.unidad_calibracion = unidad
    if altura_libre_m is not None:
        if altura_libre_m <= 0 or altura_libre_m > 20:
            raise ErrorPlano("La altura libre debe estar entre 0 y 20 m.")
        plano.altura_libre_m = float(altura_libre_m)

    # Recalcular mediciones existentes
    for med in plano.mediciones:
        pts = med.puntos()
        valor, uni = calcular_valor_real(med.tipo, pts, escala)
        med.valor = valor
        med.unidad = uni

    db.commit()
    return plano


TIPOS_MEDICION = ("lineal", "area", "perimetro", "conteo", "volumen")
MIN_PUNTOS_MEDICION = {
    "lineal": 2,
    "area": 3,
    "perimetro": 3,
    "conteo": 1,
    "volumen": 3,
}


def _limpiar_puntos_medicion(tipo: str, puntos: list[list[float]]) -> list[list[float]]:
    if not isinstance(puntos, list):
        raise ErrorPlano("Los puntos de la medición no son válidos.")
    if len(puntos) > 100:
        raise ErrorPlano("Demasiados puntos (máx. 100).")
    puntos_limpios = []
    for punto in puntos:
        if not isinstance(punto, (list, tuple)) or len(punto) < 2:
            continue
        try:
            x, y = float(punto[0]), float(punto[1])
        except (TypeError, ValueError):
            continue
        if math.isfinite(x) and math.isfinite(y):
            puntos_limpios.append([x, y])
    minimo = MIN_PUNTOS_MEDICION[tipo]
    if len(puntos_limpios) < minimo:
        nombres = {"lineal": "línea", "area": "área", "perimetro": "perímetro", "conteo": "conteo", "volumen": "volumen"}
        raise ErrorPlano(
            f"La medición de {nombres.get(tipo, tipo)} necesita al menos {minimo} punto(s)."
        )
    return puntos_limpios


def _color_medicion(color: str) -> str:
    color = (color or "#ff0000").strip()
    if len(color) == 7 and color.startswith("#"):
        try:
            int(color[1:], 16)
            return color.lower()
        except ValueError:
            pass
    return "#ff0000"


def crear_medicion(
    db: Session,
    plano: PlanoObra,
    tipo: str,
    etiqueta: str,
    puntos: list[list[float]],
    color: str = "#ff0000",
    partida_destino_id: int | None = None,
    confirmar: bool = True,
) -> PlanoMedicion:
    tipo = (tipo or "lineal").strip().lower()
    if tipo not in TIPOS_MEDICION:
        raise ErrorPlano("Tipo de medición no válido.")

    existentes = db.query(PlanoMedicion).filter(PlanoMedicion.plano_id == plano.id).count()
    if existentes >= MAX_MEDICIONES_POR_PLANO:
        raise ErrorPlano(f"Máximo {MAX_MEDICIONES_POR_PLANO} mediciones por plano.")

    puntos_limpios = _limpiar_puntos_medicion(tipo, puntos)
    valor, unidad = calcular_valor_real(tipo, puntos_limpios, plano.escala_px_por_metro)

    med = PlanoMedicion(
        plano_id=plano.id,
        presupuesto_id=plano.presupuesto_id,
        tipo=tipo,
        etiqueta=(etiqueta or "").strip()[:250],
        valor=valor,
        unidad=unidad,
        puntos_json=json.dumps(puntos_limpios, ensure_ascii=False),
        partida_destino_id=partida_destino_id,
        color=_color_medicion(color),
    )
    db.add(med)
    if confirmar:
        db.commit()
        db.refresh(med)
    else:
        db.flush()
    return med


def actualizar_medicion(
    db: Session,
    plano: PlanoObra,
    medicion: PlanoMedicion,
    tipo: str,
    etiqueta: str,
    puntos: list[list[float]],
    color: str = "#ff0000",
) -> PlanoMedicion:
    """Actualiza y confirma en servidor un trazo autoguardado."""
    if medicion.plano_id != plano.id:
        raise ErrorPlano("La medición no pertenece a este plano.")
    tipo = (tipo or medicion.tipo or "lineal").strip().lower()
    if tipo not in TIPOS_MEDICION:
        raise ErrorPlano("Tipo de medición no válido.")
    puntos_limpios = _limpiar_puntos_medicion(tipo, puntos)
    valor, unidad = calcular_valor_real(tipo, puntos_limpios, plano.escala_px_por_metro)
    medicion.tipo = tipo
    medicion.etiqueta = (etiqueta or "").strip()[:250]
    medicion.puntos_json = json.dumps(puntos_limpios, ensure_ascii=False)
    medicion.color = _color_medicion(color)
    medicion.valor = valor
    medicion.unidad = unidad
    db.commit()
    db.refresh(medicion)
    return medicion


def actualizar_altura_plano(db: Session, plano: PlanoObra, altura_libre_m: float) -> PlanoObra:
    """Cambia la altura libre y no toca la geometría: las paredes se recalculan al leer."""
    if altura_libre_m <= 0 or altura_libre_m > 20:
        raise ErrorPlano("La altura libre debe estar entre 0 y 20 m.")
    plano.altura_libre_m = float(altura_libre_m)
    db.commit()
    return plano


def eliminar_plano(db: Session, plano: PlanoObra):
    from ..storage import delete_object
    ref = plano.archivo
    db.delete(plano)
    db.flush()
    if ref:
        try:
            delete_object(db, ref)
        except Exception:
            pass
    db.commit()


def eliminar_medicion(db: Session, medicion: PlanoMedicion):
    db.delete(medicion)
    db.commit()


def aplicar_medicion_a_partida(
    db: Session,
    medicion: PlanoMedicion,
    partida_id: int,
) -> dict:
    """Crea una Medicion (del presupuesto) a partir de una PlanoMedicion."""
    from ..models import Medicion, PresupuestoItem

    partida = db.query(PresupuestoItem).filter(PresupuestoItem.id == partida_id).first()
    if not partida:
        raise ErrorPlano("Partida destino no encontrada.")

    # Verificar que partida pertenece al mismo presupuesto que el plano
    if partida.capitulo and partida.capitulo.presupuesto_id != medicion.presupuesto_id:
        raise ErrorPlano("La partida no pertenece al mismo presupuesto que el plano.")

    # Crear medición de presupuesto
    # Si es conteo, valor es uds; si lineal, m; si área, m2
    concepto = medicion.etiqueta or f"Plano {medicion.plano.nombre} - {medicion.tipo}"
    # Si ya hay mediciones, añadir, si no, cantidad directa se reemplaza por suma
    from sqlalchemy import func
    max_orden = db.query(func.max(Medicion.orden)).filter(Medicion.partida_id == partida.id).scalar() or 0
    nueva = Medicion(
        partida_id=partida.id,
        concepto=concepto[:250],
        cantidad=float(medicion.valor or 0),
        orden=max_orden + 1,
    )
    db.add(nueva)
    # Vincular
    medicion.partida_destino_id = partida.id
    db.commit()
    return {"ok": True, "medicion_id": nueva.id, "cantidad": nueva.cantidad}


def renombrar_medicion(db: Session, medicion: PlanoMedicion, etiqueta: str) -> PlanoMedicion:
    """Cambia la etiqueta de una medición guardada."""
    etiqueta = (etiqueta or "").strip()
    if not etiqueta:
        raise ErrorPlano("La etiqueta no puede estar vacía.")
    medicion.etiqueta = etiqueta[:250]
    db.commit()
    return medicion


# --------------------------------------------------------------------------- #
# Grosor de tabiques y planos creados desde cero
# --------------------------------------------------------------------------- #

def actualizar_grosor_tabique(
    db: Session,
    plano: PlanoObra,
    grosor_cm: float,
) -> PlanoObra:
    """Cambia el grosor típico de los tabiques del plano (en cm).

    No recalcula mediciones ya guardadas: cada medición conserva los
    píxeles que el usuario trazó. La nueva cifra se aplica en
    detecciones futuras, en el render de muros dibujados y en la
    conversión a metros del grosor declarado.
    """
    plano.grosor_tabique_cm = _clamp_grosor_cm(grosor_cm)
    db.commit()
    return plano


def crear_plano_en_blanco(
    db: Session,
    presupuesto_id: int,
    nombre: str,
    ancho_lienzo_m: float = 30.0,
    alto_lienzo_m: float = 20.0,
    grosor_tabique_cm: float = GROSOR_TABIQUE_DEFECTO_CM,
) -> PlanoObra:
    """Crea un plano vectorial vacío, sin imagen subida.

    El usuario lo dibujará entero desde el editor. El lienzo se describe en
    metros solo como tamaño inicial de trabajo; no se le pide al usuario (el
    editor crece solo si dibuja cerca del borde). El plano nace con la escala
    interna ``ESCALA_LIENZO_DIBUJO_PX_M`` (1 px = 1 cm), de modo que las
    medidas en metros salen directas al dibujar, sin calibrar.
    """
    existentes = db.query(PlanoObra).filter(PlanoObra.presupuesto_id == presupuesto_id).count()
    if existentes >= MAX_PLANOS_POR_PRESUPUESTO:
        raise ErrorPlano(f"Máximo {MAX_PLANOS_POR_PRESUPUESTO} planos por presupuesto.")

    try:
        ancho_m = float(ancho_lienzo_m)
        alto_m = float(alto_lienzo_m)
    except (TypeError, ValueError):
        ancho_m, alto_m = 30.0, 20.0
    if ancho_m <= 0 or alto_m <= 0 or ancho_m > 200 or alto_m > 200:
        raise ErrorPlano("El lienzo debe medir entre 0,1 m y 200 m por lado.")

    plano = PlanoObra(
        presupuesto_id=presupuesto_id,
        nombre=(nombre or "").strip()[:250] or "Plano sin título",
        archivo="",
        content_type="image/svg+xml",  # marca para que el visor pinte un canvas vacío
        ancho_px=None,
        alto_px=None,
        escala_px_por_metro=ESCALA_LIENZO_DIBUJO_PX_M,
        altura_libre_m=ALTURA_LIBRE_DEFECTO_M,
        origen="dibujado",
        grosor_tabique_cm=_clamp_grosor_cm(grosor_tabique_cm),
        ancho_lienzo_m=ancho_m,
        alto_lienzo_m=alto_m,
    )
    db.add(plano)
    db.commit()
    db.refresh(plano)
    return plano


def actualizar_lienzo(
    db: Session,
    plano: PlanoObra,
    ancho_lienzo_m: float | None = None,
    alto_lienzo_m: float | None = None,
) -> PlanoObra:
    """Amplía el lienzo de trabajo del editor vectorial (en metros).

    El editor crece solo cuando el usuario dibuja cerca del borde; aquí se
    persiste el nuevo tamaño para que el siguiente render conserve el espacio
    de trabajo. Nunca se encoge: solo se acepta crecer.
    """
    try:
        nuevo_ancho = float(ancho_lienzo_m) if ancho_lienzo_m is not None else None
        nuevo_alto = float(alto_lienzo_m) if alto_lienzo_m is not None else None
    except (TypeError, ValueError):
        nuevo_ancho = nuevo_alto = None

    ancho_actual = float(plano.ancho_lienzo_m or 0.0)
    alto_actual = float(plano.alto_lienzo_m or 0.0)
    if nuevo_ancho is not None and nuevo_ancho > ancho_actual:
        if nuevo_ancho > 200:
            raise ErrorPlano("El lienzo no puede superar 200 m de ancho.")
        plano.ancho_lienzo_m = nuevo_ancho
    if nuevo_alto is not None and nuevo_alto > alto_actual:
        if nuevo_alto > 200:
            raise ErrorPlano("El lienzo no puede superar 200 m de alto.")
        plano.alto_lienzo_m = nuevo_alto
    db.commit()
    return plano


TIPOS_ELEMENTO = ("muro", "hueco", "linea_auxiliar")
SUBTIPOS_HUECO = ("puerta", "ventana")


def _validar_puntos_elemento(tipo: str, puntos: list) -> list:
    """Normaliza la lista de puntos de un elemento dibujable."""
    if not isinstance(puntos, list):
        raise ErrorPlano("Los puntos del elemento no son una lista.")
    out: list = []
    for p in puntos:
        if not isinstance(p, (list, tuple)):
            continue
        if len(p) < 2:
            continue
        try:
            x = float(p[0])
            y = float(p[1])
        except (TypeError, ValueError):
            continue
        if not (math.isfinite(x) and math.isfinite(y)):
            continue
        if len(p) >= 3:
            try:
                z = float(p[2])
            except (TypeError, ValueError):
                z = None
            if z is not None and math.isfinite(z):
                out.append([x, y, z])
                continue
        out.append([x, y])
    if tipo == "muro" and len(out) < 2:
        raise ErrorPlano("Un muro necesita al menos 2 puntos (inicio y fin).")
    if tipo == "hueco" and len(out) < 1:
        raise ErrorPlano("Un hueco necesita posición y tamaño.")
    if tipo == "linea_auxiliar" and len(out) < 2:
        raise ErrorPlano("Una línea auxiliar necesita al menos 2 puntos.")
    return out


def guardar_elemento(
    db: Session,
    plano: PlanoObra,
    tipo: str,
    puntos: list,
    grosor_cm: float | None = None,
    color: str = "#1f2937",
    muro_id: int | None = None,
) -> PlanoElemento:
    """Crea o reemplaza un elemento vectorial del plano."""
    tipo = (tipo or "").strip().lower()
    if tipo not in TIPOS_ELEMENTO:
        raise ErrorPlano(f"Tipo de elemento no válido ({tipo}).")
    pts = _validar_puntos_elemento(tipo, puntos)
    if not pts:
        raise ErrorPlano("Elemento sin puntos válidos.")
    existentes = db.query(PlanoElemento).filter(PlanoElemento.plano_id == plano.id).count()
    if existentes >= MAX_ELEMENTOS_POR_PLANO:
        raise ErrorPlano(f"Máximo {MAX_ELEMENTOS_POR_PLANO} elementos por plano.")

    if tipo == "muro":
        grosor = _clamp_grosor_cm(grosor_cm if grosor_cm is not None else plano.grosor_tabique_cm)
    else:
        grosor = _clamp_grosor_cm(grosor_cm or plano.grosor_tabique_cm)

    color_limpio = (color or "#1f2937").strip()
    if not (len(color_limpio) == 7 and color_limpio.startswith("#")):
        color_limpio = "#1f2937"

    if tipo == "hueco" and muro_id is not None:
        muro = db.get(PlanoElemento, muro_id)
        if not muro or muro.plano_id != plano.id or muro.tipo != "muro":
            raise ErrorPlano("El muro de referencia no pertenece a este plano.")

    elem = PlanoElemento(
        plano_id=plano.id,
        tipo=tipo,
        puntos_json=json.dumps(pts, ensure_ascii=False),
        grosor_cm=grosor,
        color=color_limpio,
        muro_id=muro_id,
    )
    db.add(elem)
    db.commit()
    db.refresh(elem)
    return elem


def actualizar_elemento(
    db: Session,
    plano: PlanoObra,
    elemento: PlanoElemento,
    puntos: list,
    grosor_cm: float | None = None,
    color: str | None = None,
) -> PlanoElemento:
    """Actualiza un elemento existente con nuevos puntos / grosor / color."""
    if elemento.plano_id != plano.id:
        raise ErrorPlano("El elemento no pertenece a este plano.")
    pts = _validar_puntos_elemento(elemento.tipo, puntos)
    elemento.puntos_json = json.dumps(pts, ensure_ascii=False)
    if grosor_cm is not None:
        elemento.grosor_cm = _clamp_grosor_cm(grosor_cm)
    if color:
        c = color.strip()
        if len(c) == 7 and c.startswith("#"):
            try:
                int(c[1:], 16)
                elemento.color = c.lower()
            except ValueError:
                pass
    db.commit()
    db.refresh(elemento)
    return elemento


def eliminar_elemento(db: Session, plano: PlanoObra, elemento: PlanoElemento) -> None:
    if elemento.plano_id != plano.id:
        raise ErrorPlano("El elemento no pertenece a este plano.")
    db.delete(elemento)
    db.commit()


def _interseccion_segmentos(
    p1: tuple[float, float],
    p2: tuple[float, float],
    p3: tuple[float, float],
    p4: tuple[float, float],
) -> tuple[float, float] | None:
    """Punto de corte de los segmentos p1-p2 y p3-p4, o ``None`` si no se cruzan."""
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4
    denom = (x2 - x1) * (y4 - y3) - (y2 - y1) * (x4 - x3)
    if abs(denom) < 1e-9:
        return None
    t = ((x3 - x1) * (y4 - y3) - (y3 - y1) * (x4 - x3)) / denom
    u = ((x3 - x1) * (y2 - y1) - (y3 - y1) * (x2 - x1)) / denom
    if -1e-6 <= t <= 1 + 1e-6 and -1e-6 <= u <= 1 + 1e-6:
        return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))
    return None


def _interseccion_rectas(
    p1: tuple[float, float],
    d1: tuple[float, float],
    p2: tuple[float, float],
    d2: tuple[float, float],
) -> tuple[float, float] | None:
    """Corte de las rectas p1+t·d1 y p2+s·d2 (d1 y d2 no paralelas)."""
    denom = d1[0] * d2[1] - d1[1] * d2[0]
    if abs(denom) < 1e-9:
        return None
    t = ((p2[0] - p1[0]) * d2[1] - (p2[1] - p1[1]) * d2[0]) / denom
    return (p1[0] + t * d1[0], p1[1] + t * d1[1])


def _area_orientada(puntos: list[tuple[float, float]]) -> float:
    """Área con signo (positiva en sentido antihorario)."""
    n = len(puntos)
    if n < 3:
        return 0.0
    suma = 0.0
    for i in range(n):
        x0, y0 = puntos[i]
        x1, y1 = puntos[(i + 1) % n]
        suma += x0 * y1 - x1 * y0
    return suma / 2.0


def detectar_estancias_sobre_dibujo(plano: PlanoObra) -> list[dict]:
    """Detecta estancias de un plano 100% vectorial (muros dibujados).

    Construye el grafo planar de los ejes de los muros (dividiendo los
    segmentos en sus intersecciones), enumera las caras cerradas del grafo y
    desplaza cada cara hacia su interior media vez el grosor de cada muro.
    Así el polígono de la estancia se pega a la cara interior del tabique,
    igual que hace el detector raster, y el espesor del muro queda entre
    estancias adyacentes. Si la geometría no cierra ningún recinto devuelve
    ``[]``.
    """
    muros = [e for e in plano.elementos if e.tipo == "muro"]
    if len(muros) < 3:
        return []

    escala = plano.escala_px_por_metro or ESCALA_LIENZO_DIBUJO_PX_M

    # 1) Segmentos de eje con su grosor en px (cada tramo de una polilínea).
    segmentos: list[tuple[float, float, float, float, float]] = []
    for muro in muros:
        pts = muro.puntos()
        if len(pts) < 2:
            continue
        try:
            grosor_px = max(1.0, float(muro.grosor_cm or plano.grosor_tabique_cm) / 100.0 * escala)
        except (TypeError, ValueError):
            grosor_px = max(1.0, GROSOR_TABIQUE_DEFECTO_CM / 100.0 * escala)
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            if math.hypot(float(b[0]) - float(a[0]), float(b[1]) - float(a[1])) < 1e-6:
                continue
            segmentos.append(
                (float(a[0]), float(a[1]), float(b[0]), float(b[1]), grosor_px)
            )

    if len(segmentos) < 3:
        return []

    # 2) Puntos únicos: extremos + todos los cruces entre segmentos.
    indice_punto: dict[tuple[int, int], int] = {}
    puntos: list[tuple[float, float]] = []

    def _idx(x: float, y: float) -> int:
        clave = (round(x * 2), round(y * 2))
        if clave in indice_punto:
            return indice_punto[clave]
        idx = len(puntos)
        indice_punto[clave] = idx
        puntos.append((round(x * 2) / 2.0, round(y * 2) / 2.0))
        return idx

    for seg in segmentos:
        _idx(seg[0], seg[1])
        _idx(seg[2], seg[3])
    for i in range(len(segmentos)):
        a = segmentos[i]
        for j in range(i + 1, len(segmentos)):
            b = segmentos[j]
            corte = _interseccion_segmentos(
                (a[0], a[1]), (a[2], a[3]), (b[0], b[1]), (b[2], b[3])
            )
            if corte is not None:
                _idx(corte[0], corte[1])

    # 3) Divide cada segmento en las aristas que pasan por sus puntos.
    aristas: list[tuple[int, int, float]] = []
    for seg in segmentos:
        x0, y0, x1, y1, grosor = seg
        dx, dy = x1 - x0, y1 - y0
        largo2 = dx * dx + dy * dy
        if largo2 < 1e-9:
            continue
        sobre: list[tuple[float, int]] = []
        for idx, (px, py) in enumerate(puntos):
            t = ((px - x0) * dx + (py - y0) * dy) / largo2
            if -1e-6 <= t <= 1 + 1e-6:
                # distancia perpendicular a la recta del segmento
                proj_x = x0 + t * dx
                proj_y = y0 + t * dy
                if math.hypot(px - proj_x, py - proj_y) <= 0.9:
                    sobre.append((t, idx))
        sobre.sort()
        for k in range(len(sobre) - 1):
            aristas.append((sobre[k][1], sobre[k + 1][1], grosor))

    if len(aristas) < 3:
        return []

    # 3b) Poda iterativa de tramos con extremo libre: un muro que no cierra
    # con otro en su extremo no delimita ningún recinto (es un muro a medias),
    # y de no quitarlo aparecería como una «espina» que rompe el contorno.
    grado: dict[int, int] = {}
    incidencia: dict[int, list[int]] = {}
    for idx, (a, b, _g) in enumerate(aristas):
        grado[a] = grado.get(a, 0) + 1
        grado[b] = grado.get(b, 0) + 1
        incidencia.setdefault(a, []).append(idx)
        incidencia.setdefault(b, []).append(idx)
    activa = [True] * len(aristas)
    cola = [n for n, g in grado.items() if g <= 1]
    while cola:
        n = cola.pop()
        for idx in incidencia.get(n, []):
            if not activa[idx]:
                continue
            activa[idx] = False
            a, b, _g = aristas[idx]
            otro = b if a == n else a
            grado[otro] -= 1
            if grado[otro] <= 1:
                cola.append(otro)
    aristas = [aristas[i] for i in range(len(aristas)) if activa[i]]
    if len(aristas) < 3:
        return []

    # 4) Grafo planar y enumeración de caras (recorrido de medias aristas).
    adyacencia: dict[int, list[tuple[float, int]]] = {i: [] for i in range(len(puntos))}
    for a, b, _g in aristas:
        if a == b:
            continue
        ang_ab = math.atan2(puntos[b][1] - puntos[a][1], puntos[b][0] - puntos[a][0])
        ang_ba = math.atan2(puntos[a][1] - puntos[b][1], puntos[a][0] - puntos[b][0])
        adyacencia[a].append((ang_ab, b))
        adyacencia[b].append((ang_ba, a))
    for k in adyacencia:
        adyacencia[k].sort()

    def _siguiente(a: int, b: int) -> int:
        vecinos = adyacencia.get(b)
        if not vecinos:
            return a
        n = len(vecinos)
        for k in range(n):
            if vecinos[k][1] == a:
                return vecinos[(k - 1) % n][1]
        return vecinos[0][1]

    visitadas: set[tuple[int, int]] = set()
    caras: list[list[int]] = []
    total_mitades = sum(len(v) for v in adyacencia.values())
    for u in list(adyacencia.keys()):
        for _ang, v in adyacencia[u]:
            if (u, v) in visitadas:
                continue
            camino = [u]
            a, b = u, v
            guarda = 0
            while True:
                visitadas.add((a, b))
                camino.append(b)
                w = _siguiente(a, b)
                a, b = b, w
                guarda += 1
                if (a, b) == (u, v) or guarda > total_mitades + 2:
                    break
            caras.append(camino)

    # 5) Caras interiores: se desplazan media vez el grosor hacia dentro.
    # Con la regla de recorrido elegida, las caras cerradas (estancias) salen
    # con área positiva y las exteriores con área negativa, sea cual sea el
    # número de componentes sueltos del dibujo.
    grosor_por_arista: dict[tuple[int, int], float] = {}
    for a, b, g in aristas:
        grosor_por_arista[(a, b)] = g

    poligonos: list[list[list[float]]] = []
    for camino in caras:
        n = len(camino)
        if n < 4:
            continue
        # quitar el nodo final repetido
        if camino[0] == camino[-1]:
            ciclo = camino[:-1]
        else:
            ciclo = camino
        if len(ciclo) < 3:
            continue
        area = _area_orientada([puntos[i] for i in ciclo])
        if area <= 0.0:
            continue

        # Desplaza cada arista del ciclo hacia el interior media vez su grosor.
        lineas: list[tuple[tuple[float, float], tuple[float, float]]] = []
        for i in range(len(ciclo)):
            a = ciclo[i]
            b = ciclo[(i + 1) % len(ciclo)]
            pa = puntos[a]
            pb = puntos[b]
            dx, dy = pb[0] - pa[0], pb[1] - pa[1]
            largo = math.hypot(dx, dy)
            if largo < 1e-6:
                continue
            nx, ny = -dy / largo, dx / largo  # normal izquierda (área > 0 → interior)
            g = grosor_por_arista.get((a, b), grosor_por_arista.get((b, a), 10.0))
            d = g / 2.0
            lineas.append(((pa[0] + nx * d, pa[1] + ny * d), (dx, dy)))

        m = len(lineas)
        if m < 3:
            continue
        poligono: list[list[float]] = []
        for k in range(m):
            corte = _interseccion_rectas(
                lineas[k][0], lineas[k][1],
                lineas[(k + 1) % m][0], lineas[(k + 1) % m][1],
            )
            if corte is None:
                # Tramo colineal: usar el punto medio entre los extremos
                # desplazados evita saltos feos.
                q1 = lineas[k][0]
                q2 = lineas[(k + 1) % m][0]
                corte = ((q1[0] + q2[0]) / 2.0, (q1[1] + q2[1]) / 2.0)
            poligono.append([round(corte[0], 2), round(corte[1], 2)])
        if len(poligono) >= 3 and _area_px(poligono) >= 1.0:
            poligonos.append(poligono)

    if not poligonos:
        return []

    # 6) Filtra por superficie mínima y emite el resultado.
    pixeles_por_metro = escala
    min_area_px = max(250.0, (0.5 * pixeles_por_metro) ** 2)
    salida: list[dict[str, Any]] = []
    for idx, poligono in enumerate(poligonos, 1):
        area_px2 = _area_px(poligono)
        if area_px2 < min_area_px:
            continue
        perimetro_px = _perimetro_cerrado_px(poligono)
        confianza = min(0.97, 0.55 + min(0.42, area_px2 / (pixeles_por_metro ** 2) / 40.0))
        bbox = _bbox_puntos(poligono)
        salida.append({
            "tipo": "area",
            "puntos": poligono,
            "confianza": round(confianza, 2),
            "area_px2": round(area_px2, 2),
            "perimetro_px": round(perimetro_px, 2),
            "bbox": [round(bbox[0], 2), round(bbox[1], 2), round(bbox[2], 2), round(bbox[3], 2)],
            "etiqueta": f"Estancia {idx}",
        })
    salida.sort(key=lambda c: c["area_px2"], reverse=True)
    return salida


def guardar_detecciones_sobre_dibujo(
    db: Session,
    plano: PlanoObra,
    candidatos: list[dict[str, Any]],
) -> tuple[list[PlanoMedicion], int]:
    """Crea :class:`PlanoMedicion` para las estancias detectadas en un plano dibujado.

    Aplica la misma política de deduplicación por solapamiento que
    :func:`guardar_detecciones_automaticas`, así un segundo análisis
    no acumula estancias duplicadas.
    """
    existentes = list(plano.mediciones)
    creadas: list[PlanoMedicion] = []
    omitidas = 0
    colores = ("#2563eb", "#16a34a", "#9333ea", "#ea580c", "#0891b2", "#db2777")
    for candidato in candidatos:
        puntos = candidato.get("puntos") or []
        duplicada = any(
            med.tipo in ("area", "perimetro")
            and _solapamiento_bbox(med.puntos(), puntos) >= 0.78
            for med in existentes
        )
        if duplicada:
            omitidas += 1
            continue
        med = crear_medicion(
            db,
            plano,
            "area",
            str(candidato.get("etiqueta") or f"Estancia dibujada {len(creadas) + 1}"),
            puntos,
            colores[len(creadas) % len(colores)],
            confirmar=False,
        )
        creadas.append(med)
        existentes.append(med)
    if creadas:
        db.commit()
        for med in creadas:
            db.refresh(med)
    return creadas, omitidas


# --------------------------------------------------------------------------- #
# Exportaciones
# --------------------------------------------------------------------------- #

ETIQUETAS_TIPO_MEDICION = {
    "lineal": "Lineal",
    "area": "Área",
    "perimetro": "Perímetro",
    "conteo": "Conteo",
    "volumen": "Volumen",
}


def _fmt_num(valor: float) -> str:
    """Número con coma decimal, como el resto de CSV de la app (Excel ES)."""
    return f"{float(valor or 0):.2f}".replace(".", ",")


def filas_csv_mediciones(
    presupuesto,
    planos: list[PlanoObra] | None = None,
) -> list[list[str]]:
    """Filas CSV con todas las mediciones de todos los planos del presupuesto.

    Incluye una fila por cada elemento vectorial de los planos
    ``dibujado`` o ``mixto`` para que el exporte refleje también las
    paredes y huecos que el usuario ha creado desde el editor.

    ``planos`` permite al router suministrar una carga compatible durante la
    ventana entre desplegar el código y aplicar la migración vectorial. Sin él
    se conserva el comportamiento histórico basado en la relación ORM.
    """
    planos = sorted(
        planos if planos is not None else (getattr(presupuesto, "planos", None) or []),
        key=lambda pl: pl.id,
    )
    filas = [[
        "Plano", "Origen", "Etiqueta", "Tipo", "Valor", "Unidad", "Puntos",
        "Escala (px/m)", "Grosor (cm)", "Partida destino",
    ]]
    for plano in planos:
        escala_txt = f"{plano.escala_px_por_metro:.2f}".replace(".", ",") if plano.calibrado else ""
        grosor_txt = f"{plano.grosor_tabique_cm:.2f}".replace(".", ",")
        for med in plano.mediciones:
            destino = ""
            if med.partida_destino:
                destino = med.partida_destino.nombre
            filas.append([
                plano.nombre,
                plano.origen or "subido",
                med.etiqueta or "",
                ETIQUETAS_TIPO_MEDICION.get(med.tipo, med.tipo),
                _fmt_num(med.valor),
                med.unidad or "",
                str(len(med.puntos())),
                escala_txt,
                grosor_txt,
                destino,
            ])
        for elem in plano.elementos:
            pts = elem.puntos()
            filas.append([
                plano.nombre,
                plano.origen or "subido",
                f"[{elem.tipo}] {elem.id}",
                elem.tipo,
                "",
                "",
                str(len(pts)),
                escala_txt,
                f"{elem.grosor_cm:.2f}".replace(".", ",") if elem.tipo == "muro" else "",
                "",
            ])
    return filas


def _color_dxf(hex_color: str) -> int:
    """Color hex → índice ACI (aproximado) de la paleta DXF."""
    try:
        h = (hex_color or "#ff0000").lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    except (ValueError, IndexError):
        return 1
    if r > 200 and g < 100 and b < 100:
        return 1   # rojo
    if g > 150 and r < 150:
        return 3   # verde
    if b > 150 and r < 150:
        return 5   # azul
    if r > 200 and g > 150 and b < 100:
        return 2   # amarillo
    if r > 150 and b > 150 and g < 120:
        return 6   # magenta
    if r > 150 and g > 100 and b < 100:
        return 30  # naranja
    return 7      # blanco


def exportar_plano_dxf(plano: PlanoObra) -> str:
    """DXF ASCII (R12, solo ENTITIES) con las mediciones del plano.

    Coordenadas en metros cuando el plano está calibrado (origen abajo-
    izquierda, como en CAD: la Y se invierte respecto de la imagen) y en
    píxeles cuando no. Cada tipo de medición va a su capa MED_<TIPO>_*
    para poder congelarlas/aislarlas en el editor CAD.
    """
    if not plano.mediciones:
        raise ErrorPlano("Este plano no tiene mediciones que exportar.")

    factor = plano.factor_m if plano.calibrado else 1.0
    sufijo = "M" if plano.calibrado else "PX"
    alto = plano.alto_px
    if not alto:
        alto = max(
            (p[1] for m in plano.mediciones for p in m.puntos()),
            default=1000,
        )

    lineas: list[str] = []

    def par(codigo: int, valor):
        lineas.append(str(codigo))
        lineas.append(str(valor))

    def vertice(x_px: float, y_px: float) -> tuple[float, float]:
        return (x_px * factor, (alto - y_px) * factor)

    for med in plano.mediciones:
        pts = [vertice(x, y) for x, y in med.puntos()]
        capa = f"MED_{(med.tipo or 'LINEAL').upper()}_{sufijo}"
        color = _color_dxf(med.color)

        def segmentos(puntos, cerrar):
            for i in range(1, len(puntos)):
                par(0, "LINE"); par(8, capa); par(62, color)
                par(10, f"{puntos[i-1][0]:.4f}"); par(20, f"{puntos[i-1][1]:.4f}")
                par(11, f"{puntos[i][0]:.4f}"); par(21, f"{puntos[i][1]:.4f}")
            if cerrar and len(puntos) >= 3:
                par(0, "LINE"); par(8, capa); par(62, color)
                par(10, f"{puntos[-1][0]:.4f}"); par(20, f"{puntos[-1][1]:.4f}")
                par(11, f"{puntos[0][0]:.4f}"); par(21, f"{puntos[0][1]:.4f}")

        if med.tipo in ("lineal", "perimetro", "volumen"):
            segmentos(pts, cerrar=(med.tipo != "lineal"))
        elif med.tipo == "area":
            segmentos(pts, cerrar=True)
        elif med.tipo == "conteo":
            radio = (8 * factor) if factor < 1 else 8
            for x, y in pts:
                par(0, "CIRCLE"); par(8, capa); par(62, color)
                par(10, f"{x:.4f}"); par(20, f"{y:.4f}"); par(40, f"{radio:.4f}")

        etiqueta = (med.etiqueta or "").strip()
        if etiqueta and pts:
            alto_txt = (0.25 if plano.calibrado else 12)
            par(0, "TEXT"); par(8, "MED_ETIQUETAS"); par(62, 7)
            par(10, f"{pts[0][0]:.4f}"); par(20, f"{pts[0][1]:.4f}")
            par(40, f"{alto_txt:.2f}")
            par(1, etiqueta[:80])

    cuerpo = "\n".join(lineas)
    unidad = "metros" if plano.calibrado else "píxeles"
    return (
        f"999\nMediciones CotizaT - {plano.nombre} - coordenadas en {unidad}\n"
        "0\nSECTION\n2\nENTITIES\n"
        f"{cuerpo}\n"
        "0\nENDSEC\n0\nEOF\n"
    )
