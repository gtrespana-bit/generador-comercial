"""Detección geométrica, calibración y mediciones editables sobre planos.

El flujo principal analiza localmente PNG/JPG/WEBP, crea áreas candidatas y las
persiste como geometrías ordinarias. El usuario puede calibrarlas, editarlas o
añadir líneas, perímetros y conteos manuales. No se envían planos a servicios de
visión externos y no hay coste por uso.
"""

from __future__ import annotations

import io
import json
import math
from collections import deque
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from ..models import PlanoMedicion, PlanoObra

EXT_PLANOS_IMG = {".png", ".jpg", ".jpeg", ".webp"}
EXT_PLANOS_PDF = {".pdf"}
MAX_PLANO_BYTES = 12 * 1024 * 1024
MAX_PLANOS_POR_PRESUPUESTO = 20
MAX_MEDICIONES_POR_PLANO = 500

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
    """Une tramos de tinta alineados, cerrando huecos típicos de puertas."""
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

    unidos: list[tuple[int, int, int]] = [runs[0]]
    for inicio, fin, tinta in runs[1:]:
        anterior_i, anterior_f, anterior_tinta = unidos[-1]
        hueco = inicio - anterior_f - 1
        # Solo se puentea cuando los trazos a ambos lados tienen entidad. Así
        # no se convierte cada palabra del plano en una pared artificial.
        lados_utiles = anterior_tinta >= 3 and tinta >= 3
        if hueco <= max_hueco and lados_utiles:
            unidos[-1] = (anterior_i, fin, anterior_tinta + tinta)
        else:
            unidos.append((inicio, fin, tinta))

    salida = []
    for inicio, fin, tinta in unidos:
        largo = fin - inicio + 1
        densidad = tinta / max(1, largo)
        if largo >= largo_minimo and densidad >= 0.18:
            salida.append((inicio, fin))
    return salida


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
    epsilon = max(1.5, min(len(ys) / 80.0, 6.0))
    simplificado = _rdp(trazado, epsilon)
    while len(simplificado) > 80:
        epsilon *= 1.35
        simplificado = _rdp(trazado, epsilon)

    resultado: list[list[float]] = []
    for x, y in simplificado:
        punto = [
            round(min(ancho_original, max(0.0, x * factor_x)), 2),
            round(min(alto_original, max(0.0, y * factor_y)), 2),
        ]
        if not resultado or distancia_entre_puntos(resultado[-1], punto) > 0.5:
            resultado.append(punto)
    return resultado


def distancia_entre_puntos(a: list[float], b: list[float]) -> float:
    return math.hypot(float(a[0]) - float(b[0]), float(a[1]) - float(b[1]))


def detectar_espacios_plano(
    contenido: bytes,
    content_type: str = "",
    max_espacios: int = 30,
) -> list[dict[str, Any]]:
    """Detecta recintos cerrados de una planta y devuelve polígonos candidatos.

    Es visión geométrica local y determinista: binariza el plano, prolonga
    paredes horizontales/verticales a través de huecos de puerta y busca las
    regiones claras que no alcanzan el borde exterior. No envía el archivo a
    una IA ni promete interpretar la semántica de cada habitación.
    """
    if content_type and not content_type.lower().startswith("image/"):
        raise ErrorPlano("La detección automática requiere un plano PNG, JPG o WEBP.")
    max_espacios = max(1, min(int(max_espacios), 30))
    try:
        from PIL import Image, ImageFilter

        with Image.open(io.BytesIO(contenido)) as original:
            original.load()
            gris = original.convert("L")
            ancho_original, alto_original = gris.size
    except Exception as exc:
        raise ErrorPlano("No se pudo analizar la imagen del plano.") from exc

    if ancho_original < 80 or alto_original < 80:
        raise ErrorPlano("El plano es demasiado pequeño para detectar estancias.")

    max_dimension = 950
    escala_reduccion = min(1.0, max_dimension / max(ancho_original, alto_original))
    ancho = max(1, round(ancho_original * escala_reduccion))
    alto = max(1, round(alto_original * escala_reduccion))
    if (ancho, alto) != (ancho_original, alto_original):
        gris = gris.resize((ancho, alto), Image.Resampling.LANCZOS)

    histograma = gris.histogram()
    umbral = _umbral_otsu(histograma, ancho * alto)
    # 255 representa tinta/barrera; 0 representa espacio transitable.
    tinta_img = gris.point(lambda p: 255 if p <= umbral else 0, mode="L")
    tinta = [1 if valor else 0 for valor in tinta_img.tobytes()]

    # Engrosado mínimo para cerrar el antialias y las intersecciones de muros.
    barrera_img = tinta_img.filter(ImageFilter.MaxFilter(3))
    barrera = bytearray(1 if valor else 0 for valor in barrera_img.tobytes())

    dimension_menor = min(ancho, alto)
    max_hueco = max(6, min(55, round(dimension_menor * 0.06)))
    largo_minimo = max(18, round(dimension_menor * 0.075))
    grosor = max(1, min(3, round(dimension_menor / 420)))

    # Paredes horizontales. Se prolongan los dos bordes alineados de una puerta
    # para que la estancia quede cerrada durante la segmentación.
    for y in range(alto):
        fila = tinta[y * ancho : (y + 1) * ancho]
        for x0, x1 in _runs_tinta(fila, max_hueco, largo_minimo):
            for yy in range(max(0, y - grosor), min(alto, y + grosor + 1)):
                inicio = yy * ancho + x0
                barrera[inicio : yy * ancho + x1 + 1] = b"\x01" * (x1 - x0 + 1)

    # Paredes verticales.
    for x in range(ancho):
        columna = [tinta[y * ancho + x] for y in range(alto)]
        for y0, y1 in _runs_tinta(columna, max_hueco, largo_minimo):
            for xx in range(max(0, x - grosor), min(ancho, x + grosor + 1)):
                for y in range(y0, y1 + 1):
                    barrera[y * ancho + xx] = 1

    visitado = bytearray(ancho * alto)
    area_minima = max(300, round(ancho * alto * 0.0025))
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
            or anchura < dimension_menor * 0.035
            or altura < dimension_menor * 0.035
            or proporcion > 12
            or ocupacion < 0.24
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

    # Primero los recintos grandes; se evita devolver ruido y se da un nombre
    # estable que el usuario puede cambiar desde la lista.
    candidatos.sort(key=lambda c: c["area_px2"], reverse=True)
    for numero, candidato in enumerate(candidatos[:max_espacios], 1):
        candidato["etiqueta"] = f"Estancia detectada {numero}"
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


def filas_csv_mediciones(presupuesto) -> list[list[str]]:
    """Filas CSV con todas las mediciones de todos los planos del presupuesto."""
    planos = sorted(
        getattr(presupuesto, "planos", None) or [],
        key=lambda pl: pl.id,
    )
    filas = [[
        "Plano", "Etiqueta", "Tipo", "Valor", "Unidad", "Puntos",
        "Escala (px/m)", "Partida destino",
    ]]
    for plano in planos:
        escala_txt = f"{plano.escala_px_por_metro:.2f}".replace(".", ",") if plano.calibrado else ""
        for med in plano.mediciones:
            destino = ""
            if med.partida_destino:
                destino = med.partida_destino.nombre
            filas.append([
                plano.nombre,
                med.etiqueta or "",
                ETIQUETAS_TIPO_MEDICION.get(med.tipo, med.tipo),
                _fmt_num(med.valor),
                med.unidad or "",
                str(len(med.puntos())),
                escala_txt,
                destino,
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
