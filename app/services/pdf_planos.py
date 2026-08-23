"""Anexo PDF «Planos y mediciones» para el presupuesto.

Cuando el presupuesto tiene planos con mediciones y la opción «incluir
anexos» está activada, se genera un anexo en memoria con una página por
plano: la imagen con las mediciones dibujadas encima (igual que en el
área de medición) y una tabla con etiqueta, tipo y valor de cada una.

El anexo entra por el mismo circuito que el resto de anexos
(:mod:`app.services.pdf_anexos`), de modo que hereda sus reglas: índice
con página de inicio, tope de tamaño y degradación elegante si algo
falla (nunca rompe la descarga del presupuesto).
"""
from __future__ import annotations

import io
import logging

from pypdf import PdfReader
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as pdfcanvas

from ..storage import read_reference
from . import pdf_anexos

log = logging.getLogger("cotizat")

AZUL = "#04265D"
GRIS = "#64748b"
BORDE = "#cbd5e1"
MARGEN = 34
MAX_FILAS_TABLA = 13  # filas de mediciones por página (la tabla continúa en la siguiente)


def generar_anexo(presupuesto) -> pdf_anexos.Anexo | None:
    """Anexo listo para fusionar, o None si no hay planos con mediciones."""
    planos = [
        plano for plano in (getattr(presupuesto, "planos", None) or [])
        if plano.mediciones
    ]
    if not planos:
        return None
    try:
        datos = _generar_pdf(planos)
        paginas = len(PdfReader(io.BytesIO(datos)).pages)
    except Exception:
        log.exception("No se pudo generar el anexo de planos y mediciones")
        return None
    n_med = sum(len(plano.mediciones) for plano in planos)
    return pdf_anexos.Anexo(
        nombre=f"Planos y mediciones ({n_med} medición{'es' if n_med != 1 else ''})",
        datos=datos,
        paginas=paginas,
    )


def _generar_pdf(planos: list) -> bytes:
    buf = io.BytesIO()
    c = pdfcanvas.Canvas(buf, pagesize=A4)
    ancho, alto_pag = A4
    for plano in planos:
        mediciones = plano.mediciones
        restantes = list(mediciones)
        primera = True
        while restantes or primera:
            bloque = restantes[:MAX_FILAS_TABLA]
            restantes = restantes[MAX_FILAS_TABLA:]
            _pagina_plano(c, plano, bloque, len(mediciones), primera, ancho, alto_pag)
            c.showPage()
            primera = False
    c.save()
    return buf.getvalue()


def _pagina_plano(c, plano, mediciones, total, es_primera, ancho, alto_pag):
    y = alto_pag - 42

    # Encabezado
    c.setFillColor(HexColor(AZUL))
    c.setFont("Helvetica-Bold", 13)
    titulo = f"Plano: {plano.nombre}" if es_primera else f"Plano: {plano.nombre} (cont.)"
    c.drawString(MARGEN, y, titulo[:70])
    c.setFont("Helvetica", 8.5)
    c.setFillColor(HexColor(GRIS))
    escala = (
        f"{plano.escala_px_por_metro:.2f} px/m" if plano.calibrado else "sin calibrar"
    )
    c.drawString(
        MARGEN, y - 13,
        f"Escala: {escala} · {total} medición{'es' if total != 1 else ''} · "
        "valores dibujados sobre el plano como en el área de medición",
    )
    y -= 26

    # Zona de imagen (solo en la primera página del plano)
    if es_primera:
        y = _dibujar_imagen_con_mediciones(c, plano, mediciones, MARGEN, y, ancho)

    # Tabla de mediciones
    y -= 14
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(HexColor(AZUL))
    c.drawString(MARGEN, y, "Mediciones")
    y -= 6
    y = _tabla(c, mediciones, y, ancho)


def _dibujar_imagen_con_mediciones(c, plano, mediciones, x0, y0, ancho_pag):
    """Dibuja la imagen del plano (si es legible) y las mediciones encima."""
    alto_disp = 300
    img = None
    if (plano.content_type or "").startswith("image/"):
        try:
            datos = read_reference(plano.archivo)
            img = ImageReader(io.BytesIO(datos))
            iw, ih = img.getSize()
        except Exception:
            img = None

    caja_w = ancho_pag - 2 * x0
    caja_h = alto_disp
    x, y, w, h = x0, y0 - caja_h, caja_w, caja_h

    if img is not None:
        escala = min(caja_w / iw, caja_h / ih)
        w, h = iw * escala, ih * escala
        x = x0 + (caja_w - w) / 2
        y = y0 - h
        c.drawImage(img, x, y, width=w, height=h, preserveAspectRatio=True, mask="auto")
        _dibujar_mediciones(c, mediciones, plano, x, y, w, h)
    else:
        c.setFillColor(HexColor("#f1f5f9"))
        c.setStrokeColor(HexColor(BORDE))
        c.rect(x, y, caja_w, caja_h, stroke=1, fill=1)
        c.setFillColor(HexColor(GRIS))
        c.setFont("Helvetica-Oblique", 9)
        c.drawCentredString(
            x + caja_w / 2, y + caja_h / 2,
            "Imagen del plano no disponible (PDF o archivo no embebible)",
        )
    c.setStrokeColor(HexColor(BORDE))
    c.rect(x, y, w, h, stroke=1, fill=0)
    return y


def _dibujar_mediciones(c, mediciones, plano, x, y, w, h):
    """Superpone los trazos de cada medición sobre la imagen ya dibujada."""
    if not plano.ancho_px or not plano.alto_px:
        return
    sx = w / plano.ancho_px
    sy = h / plano.alto_px

    def punto(px, py):
        return (x + px * sx, y + h - py * sy)  # la imagen crece hacia abajo

    c.setLineWidth(1.1)
    for m in mediciones:
        pts = [punto(px, py) for px, py in m.puntos()]
        if not pts:
            continue
        try:
            color = HexColor((m.color or "#ff0000"))
        except ValueError:
            color = HexColor("#ff0000")
        if m.tipo == "area":
            c.setFillColor(color)
            try:
                c.setFillAlpha(0.16)
            except Exception:
                pass
            p = c.beginPath()
            p.moveTo(*pts[0])
            for pt in pts[1:]:
                p.lineTo(*pt)
            p.close()
            c.drawPath(p, stroke=1, fill=1)
            try:
                c.setFillAlpha(1)
            except Exception:
                pass
        else:
            c.setStrokeColor(color)
            p = c.beginPath()
            p.moveTo(*pts[0])
            for pt in pts[1:]:
                p.lineTo(*pt)
            if m.tipo == "perimetro" and len(pts) >= 3:
                p.close()
            c.drawPath(p, stroke=1, fill=0)
        for pt in pts:
            c.setFillColor(color)
            c.circle(pt[0], pt[1], 1.3, stroke=0, fill=1)
        etiqueta = (m.etiqueta or "").strip()
        if etiqueta:
            c.setFillColor(HexColor("#111827"))
            c.setFont("Helvetica", 6)
            c.drawString(pts[0][0] + 3, pts[0][1] + 3, etiqueta[:48])


def _tabla(c, mediciones, y, ancho_pag):
    """Tabla compacta: etiqueta · tipo · valor · unidad. Devuelve la Y final."""
    x0 = MARGEN
    ancho_total = ancho_pag - 2 * MARGEN
    col_tipo = 90
    col_valor = 70
    col_unidad = 46
    col_etiqueta = ancho_total - col_tipo - col_valor - col_unidad

    # Cabecera
    y -= 14
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(HexColor(AZUL))
    c.rect(x0, y, ancho_total, 14, stroke=0, fill=1)
    c.setFillColor(HexColor("#ffffff"))
    c.drawString(x0 + 4, y + 4, "Etiqueta")
    c.drawString(x0 + col_etiqueta + 4, y + 4, "Tipo")
    c.drawRightString(x0 + col_etiqueta + col_tipo + col_valor, y + 4, "Valor")
    c.drawString(x0 + col_etiqueta + col_tipo + col_valor + 6, y + 4, "Unidad")

    c.setFont("Helvetica", 8.5)
    for i, m in enumerate(mediciones):
        y -= 13
        if i % 2 == 0:
            c.setFillColor(HexColor("#f8fafc"))
            c.rect(x0, y, ancho_total, 13, stroke=0, fill=1)
        c.setFillColor(HexColor("#0f172a"))
        etiqueta = (m.etiqueta or "—").strip()
        c.drawString(x0 + 4, y + 3.5, etiqueta[: int(col_etiqueta // 4)])
        tipo = {
            "lineal": "Lineal", "area": "Área", "perimetro": "Perímetro",
            "conteo": "Conteo", "volumen": "Volumen",
        }.get(m.tipo, m.tipo)
        c.drawString(x0 + col_etiqueta + 4, y + 3.5, tipo)
        c.drawRightString(x0 + col_etiqueta + col_tipo + col_valor, y + 3.5, f"{(m.valor or 0):.2f}")
        c.drawString(x0 + col_etiqueta + col_tipo + col_valor + 6, y + 3.5, m.unidad or "")
    y -= 4
    c.setStrokeColor(HexColor(BORDE))
    c.line(x0, y, x0 + ancho_total, y)
    return y
