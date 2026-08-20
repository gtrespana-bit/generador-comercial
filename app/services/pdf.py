"""Generación del presupuesto en PDF con ReportLab.

Genera un documento comercial estructurado para presupuestos de obra:

  · Cabecera con caja de empresa (fondo azul-grisáceo, faja azul a la
    izquierda) y logotipo a la derecha.
  · Título «PRESUPUESTO» subrayado y bloque proyecto / cliente a dos
    columnas con etiquetas en negrita.
  · Capítulos con banda azul, nombre en mayúsculas y subtotal propio;
    cabeceras de columna (Partida / Cantidad / Precio / Importe).
  · Partidas con título, descripción técnica, fila de totales en negrita,
    mediciones desglosadas por zonas y «Producto presupuestado» opcional
    con imagen enmarcada.
  · Cierre con bloque de totales (BASE IMPONIBLE / I.V.A. / PRESUPUESTO
    TOTAL) sobre fondo azul-grisáceo y faja azul a la derecha.
  · Pie de página con numeración «n/N».
"""
import io
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors

from ..database import BASE_DIR, UPLOADS_DIR
from ..storage import StorageError, materialize_reference, object_key_from_reference
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)

from ..utils import (
    fmt_cantidad,
    fmt_fecha,
    fmt_monto_iso as fmt_monto,
    fmt_num,
    fmt_pct,
    fmt_precio_u_iso as fmt_precio_u,
    saneado,
)
from .traduccion import codigo_desde_pais, traducir
from . import pdf_anexos
from .pdf_interactivo import ContextoInteractivo

# Código de país activo para traducir terminología al vuelo (VE base -> CO/MX/EC/PE)
_CODIGO_PAIS_ACTUAL = ""


def _money(valor: float) -> float:
    """Redondeo monetario único del PDF (ROUND_HALF_UP a 2 decimales),
    idéntico al motor de cálculos de la aplicación."""
    from decimal import Decimal, ROUND_HALF_UP
    try:
        return float(Decimal(str(valor or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    except Exception:
        return 0.0

# ---------------------------------------------------------------------------
# Fuentes Lato (idénticas a las del presupuesto de referencia)
# ---------------------------------------------------------------------------
_FONTS_DIR = BASE_DIR / "app" / "static" / "fonts"
_FUENTES_CARGADAS = False


def _registrar_fuentes():
    global _FUENTES_CARGADAS
    if _FUENTES_CARGADAS:
        return
    for nombre, archivo in [
        ("Lato", "Lato-Regular.ttf"),
        ("Lato-Bold", "Lato-Bold.ttf"),
        ("Lato-Italic", "Lato-Italic.ttf"),
        ("Lato-BoldItalic", "Lato-BoldItalic.ttf"),
        ("Lato-Black", "Lato-Black.ttf"),
    ]:
        ruta = _FONTS_DIR / archivo
        if ruta.exists():
            pdfmetrics.registerFont(TTFont(nombre, str(ruta)))
    pdfmetrics.registerFontFamily(
        "Lato", normal="Lato", bold="Lato-Bold", italic="Lato-Italic", boldItalic="Lato-BoldItalic"
    )
    _FUENTES_CARGADAS = True


# ---------------------------------------------------------------------------
# Paleta exacta del documento de referencia
# ---------------------------------------------------------------------------
AZUL = colors.HexColor("#04265D")       # bandas, líneas y acentos
TEXTO = colors.HexColor("#333333")      # títulos y cifras principales
GRIS = colors.HexColor("#666666")       # texto secundario / descripciones
GRIS_CLARO = colors.HexColor("#999999") # razón social
FONDO = colors.HexColor("#DADFE7")      # caja de empresa y bloque de totales
LINEA_TOT = colors.HexColor("#B9C1D1")  # separadores del bloque de totales
LINEA_HEAD = colors.HexColor("#CCCCCC") # línea bajo cabeceras de columna
ROSA = colors.HexColor("#CC0066")       # enlaces / referencia

_ANCHO = A4[0] - 68                     # ancho útil: 34 pt de margen por lado
COLS = [_ANCHO - 221, 73, 74, 74]       # columnas de la tabla de partidas


def _estilos():
    base = {"fontName": "Lato"}
    return {
        # Tamaños compactos: la caja de empresa ahora es más estrecha
        "empresa": ParagraphStyle("empresa", fontName="Lato-Bold", fontSize=11.5, leading=13.5, textColor=GRIS),
        "empresa_linea": ParagraphStyle("empresa_linea", **base, fontSize=8.2, leading=9.8, textColor=GRIS),
        "legal": ParagraphStyle("legal", fontName="Lato", fontSize=8.2, leading=9.8, textColor=GRIS_CLARO),
        "titulo_doc": ParagraphStyle("titulo_doc", fontName="Lato-Bold", fontSize=15, leading=18, textColor=TEXTO, alignment=TA_CENTER),
        "t13": ParagraphStyle("t13", fontName="Lato-Bold", fontSize=13.5, leading=16.2, textColor=TEXTO),
        "campo": ParagraphStyle("campo", **base, fontSize=9, leading=10.8, textColor=GRIS),
        "ref": ParagraphStyle("ref", fontName="Lato-Italic", fontSize=9, leading=10.8, textColor=GRIS),
        "cap": ParagraphStyle("cap", fontName="Lato-Bold", fontSize=13.5, leading=16.2, textColor=TEXTO),
        "cap_d": ParagraphStyle("cap_d", fontName="Lato-Bold", fontSize=13.5, leading=16.2, textColor=TEXTO, alignment=TA_RIGHT),
        "head": ParagraphStyle("head", fontName="Lato", fontSize=9, leading=10.8, textColor=GRIS),
        "head_c": ParagraphStyle("head_c", fontName="Lato", fontSize=9, leading=10.8, textColor=GRIS, alignment=TA_CENTER),
        "p_nombre": ParagraphStyle("p_nombre", fontName="Lato-Bold", fontSize=10.5, leading=12.6, textColor=TEXTO),
        "p_desc": ParagraphStyle("p_desc", fontName="Lato", fontSize=9.75, leading=11.7, textColor=GRIS, spaceBefore=3),
        "tot_c": ParagraphStyle("tot_c", fontName="Lato-Bold", fontSize=9, leading=10.8, textColor=TEXTO, alignment=TA_CENTER),
        "med_d": ParagraphStyle("med_d", fontName="Lato", fontSize=8.25, leading=9.9, textColor=GRIS, alignment=TA_RIGHT),
        "med_c": ParagraphStyle("med_c", fontName="Lato", fontSize=8.25, leading=9.9, textColor=GRIS, alignment=TA_CENTER),
        "prod_lab": ParagraphStyle("prod_lab", fontName="Lato-Bold", fontSize=9.75, leading=11.7, textColor=TEXTO),
        "prod": ParagraphStyle("prod", fontName="Lato", fontSize=9.75, leading=11.7, textColor=GRIS),
        "prod_nota": ParagraphStyle("prod_nota", fontName="Lato-Italic", fontSize=7.6, leading=9.2, textColor=GRIS_CLARO),
        "mini": ParagraphStyle("mini", fontName="Lato", fontSize=7.4, leading=8.8, textColor=GRIS, alignment=TA_CENTER),
        "tot_lab": ParagraphStyle("tot_lab", fontName="Lato-Bold", fontSize=12, leading=14.4, textColor=GRIS, alignment=TA_RIGHT),
        "tot_lab_s": ParagraphStyle("tot_lab_s", fontName="Lato-Bold", fontSize=10.5, leading=12.6, textColor=GRIS, alignment=TA_RIGHT),
        "tot_lab_g": ParagraphStyle("tot_lab_g", fontName="Lato-Bold", fontSize=13.5, leading=16.2, textColor=TEXTO, alignment=TA_RIGHT),
        "nota": ParagraphStyle("nota", fontName="Lato", fontSize=9, leading=12.6, textColor=GRIS),
    }


def _esc(texto: str) -> str:
    return escape(saneado(texto or ""))


def _hr(color, grosor=1, ancho="100%", **kw):
    return HRFlowable(width=ancho, thickness=grosor, color=color, lineCap="butt", **kw)


def _fit_image(ruta: Path, max_w: float, max_h: float, halign="RIGHT"):
    """Image flowable ajustado a la caja max_w × max_h conservando la proporción."""
    from PIL import Image as PILImage

    try:
        with PILImage.open(ruta) as im:
            w, h = im.size
    except Exception:
        return None
    if not w or not h:
        return None
    escala = min(max_w / w, max_h / h)
    return Image(str(ruta), width=w * escala, height=h * escala, hAlign=halign)


def _static_path(rel: str) -> Path:
    """Resuelve recursos locales o materializa objetos privados en ``/tmp``."""
    if not rel:
        return Path("/__cotizat_archivo_inexistente__")
    try:
        es_objeto_privado = object_key_from_reference(str(rel)) is not None
    except StorageError:
        return Path("/__cotizat_archivo_inexistente__")
    if es_objeto_privado:
        try:
            return materialize_reference(str(rel))
        except StorageError:
            return Path("/__cotizat_archivo_inexistente__")
    clean = str(rel).strip().lstrip("/")
    if clean.startswith("static/"):
        clean = clean[7:]
    if clean.startswith("uploads/"):
        return UPLOADS_DIR / clean[8:]
    p1 = BASE_DIR / "app" / "static" / clean
    if p1.exists():
        return p1
    p2 = UPLOADS_DIR / clean
    if p2.exists():
        return p2
    return p1


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Cabecera (primera página)
# ---------------------------------------------------------------------------

def _cabecera(presupuesto, config, st, azul_color, titulo_doc="PRESUPUESTO",
              etiqueta_num="Presupuesto Nº", titulo_por_defecto="Presupuesto de remodelación"):
    """Caja de empresa + logo, título y bloque proyecto / cliente.

    También se usa para el documento de cobro (título no fiscal).
    """
    # -- Caja de empresa ---------------------------------------------------
    # Etiquetas cortas: la caja de empresa ahora es estrecha
    filas_empresa = [Paragraph(_esc(config.empresa_nombre), st["empresa"])]
    if config.empresa_rif:
        _etiq = getattr(config, "etiqueta_id_fiscal", "") or "RIF"
        filas_empresa.append(Paragraph(f"<b>{_esc(_etiq)}:</b> {_esc(config.empresa_rif)}", st["empresa_linea"]))
    if config.empresa_email:
        filas_empresa.append(Paragraph(f"<b>Email:</b> {_esc(config.empresa_email)}", st["empresa_linea"]))
    if config.empresa_telefono:
        filas_empresa.append(Paragraph(f"<b>Teléfono:</b> {_esc(config.empresa_telefono)}", st["empresa_linea"]))
    if config.empresa_web:
        web = _esc(config.empresa_web)
        filas_empresa.append(Paragraph(f"<b>Web:</b> <font color='#CC0066'>{web}</font>", st["empresa_linea"]))
    if config.empresa_direccion:
        filas_empresa.append(Paragraph(f"<b>Dirección:</b> {_esc(config.empresa_direccion)}", st["empresa_linea"]))
    if config.empresa_legal:
        filas_empresa.append(Spacer(1, 2))
        filas_empresa.append(Paragraph(_esc(config.empresa_legal), st["legal"]))

    # -- Logo --------------------------------------------------------------
    # El ancho del logo se configura en «Configuración → Logotipo». Se
    # reserva sitio para la caja de empresa (mín. 150 pt) y se limita a un
    # máximo razonable.
    ancho_logo = int(getattr(config, "logo_ancho_pdf", None) or 360)
    ancho_logo = max(140, min(ancho_logo, _ANCHO - 150))
    logo_flow = None
    if config.logo:
        ruta = _static_path(config.logo)
        if ruta.exists():
            logo_flow = _fit_image(ruta, ancho_logo - 7, 160, halign="LEFT")

    cab = Table([[logo_flow or "", filas_empresa]], colWidths=[ancho_logo, _ANCHO - ancho_logo])
    cab.setStyle(TableStyle([
        ("BACKGROUND", (1, 0), (1, 0), FONDO),
        ("LINEBEFORE", (1, 0), (1, 0), 3, azul_color),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (1, 0), (1, 0), 9),
        ("RIGHTPADDING", (1, 0), (1, 0), 6),
        ("TOPPADDING", (1, 0), (1, 0), 5),
        ("BOTTOMPADDING", (1, 0), (1, 0), 5),
        ("LEFTPADDING", (0, 0), (0, 0), 2),
        ("RIGHTPADDING", (0, 0), (0, 0), 8),
    ]))

    # -- Título del documento ----------------------------------------------
    titulo = Paragraph(titulo_doc, st["titulo_doc"])
    ancho_titulo = pdfmetrics.stringWidth(titulo_doc, "Lato-Bold", 15)
    sub = _hr(colors.HexColor("#333333"), 1, ancho_titulo, hAlign="CENTER", spaceBefore=2.5)

    # -- Proyecto / cliente -------------------------------------------------
    def encabezado(texto):
        p = Paragraph(_esc(texto), st["t13"])
        w = min(pdfmetrics.stringWidth(saneado(texto), "Lato-Bold", 13.5) + 1, (_ANCHO / 2) - 4)
        return [p, _hr(colors.HexColor("#333333"), 1, w, hAlign="LEFT", spaceBefore=1.5)]

    izq = encabezado(presupuesto.titulo or titulo_por_defecto)
    if presupuesto.direccion_obra:
        izq.append(Paragraph(f"<b>Dirección de la obra:</b> {_esc(presupuesto.direccion_obra)}", st["campo"]))
    if presupuesto.codigo_postal:
        izq.append(Paragraph(f"<b>Código postal:</b> {_esc(presupuesto.codigo_postal)}", st["campo"]))
    izq.append(Paragraph(f"<b>Fecha:</b> {fmt_fecha(presupuesto.fecha)}", st["campo"]))

    c = presupuesto.cliente
    der = encabezado("Cliente")
    nombre_linea = f"<b>Nombre:</b> {_esc(c.nombre)}"
    if c.rif:
        _etiq_cli = getattr(config, "etiqueta_id_fiscal", "") or "RIF"
        nombre_linea += f"&nbsp;&nbsp;&nbsp;<b>{_esc(_etiq_cli)}:</b> {_esc(c.rif)}"
    der.append(Paragraph(nombre_linea, st["campo"]))
    if c.pais:
        der.append(Paragraph(f"<b>País:</b> {_esc(c.pais)}", st["campo"]))
    if presupuesto.validez_dias:
        der.append(Paragraph(f"<b>Validez de la oferta:</b> {presupuesto.validez_dias} días", st["campo"]))
    # Moneda del documento, siempre visible y con su código ISO: los símbolos
    # «$» de la región no distinguen pesos mexicanos, colombianos ni dólares.
    from ..services.monedas import codigo_iso as _iso_doc, simbolo as _simbolo_doc

    _iso_presupuesto = _iso_doc(presupuesto.moneda)
    der.append(Paragraph(
        f"<b>Moneda:</b> {_esc(_iso_presupuesto)} ({_esc(_simbolo_doc(_iso_presupuesto))})",
        st["campo"],
    ))
    if presupuesto.tipo_cambio and presupuesto.moneda != "USD":
        _fuente = getattr(presupuesto, "fuente_tipo_cambio", "") or "referencia"
        der.append(Paragraph(f"<b>Tasa ({_esc(_fuente)}):</b> 1 USD = {fmt_num(presupuesto.tipo_cambio)} {_esc(presupuesto.moneda)}", st["campo"]))
    der.append(Paragraph(f"{etiqueta_num} <font color='#CC0066'>{_esc(presupuesto.numero)}</font>", st["ref"]))

    bloque = Table([[izq, der]], colWidths=[_ANCHO / 2, _ANCHO / 2])
    bloque.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 1),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))

    return [
        cab,
        Spacer(1, 7),
        titulo,
        sub,
        Spacer(1, 9),
        bloque,
        _hr(azul_color, 1, spaceBefore=4, spaceAfter=13),
    ]


# ---------------------------------------------------------------------------
# Capítulos y partidas
# ---------------------------------------------------------------------------

def _banda(azul_color):
    t = Table([[""]], colWidths=[_ANCHO], rowHeights=[8])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), azul_color),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return t


def _fila_capitulo(cap, st, moneda, azul_color, ctx=None):
    # Con productos a elegir el subtotal del capítulo depende de la opción
    # marcada, así que se emite como campo calculado del formulario.
    if ctx is not None and any(ctx.es_interactiva(p) for p in cap.partidas):
        celda_subtotal = ctx.campo(
            "cap_" + ctx.id_capitulo(cap),
            ctx.txt_capitulo(cap),
            ctx.js_capitulo(cap),
            COLS[3],
            alto=16,
            alineacion="right",
            tam=13.5,
        )
    else:
        celda_subtotal = Paragraph(fmt_monto(cap.subtotal, moneda), st["cap_d"])
    cap_nombre_trad = traducir(cap.nombre, _CODIGO_PAIS_ACTUAL) if _CODIGO_PAIS_ACTUAL else cap.nombre
    t = Table(
        [[Paragraph(_esc(cap_nombre_trad.upper()), st["cap"]), "", "", celda_subtotal]],
        colWidths=COLS,
    )
    t.setStyle(TableStyle([
        ("SPAN", (1, 0), (2, 0)),
        ("LINEBELOW", (0, 0), (-1, 0), 2, azul_color),
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (-1, 0), (-1, 0), 1),
        ("TOPPADDING", (0, 0), (-1, -1), 1.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))
    return t


def _fila_columnas(st):
    t = Table(
        [[Paragraph("Partida", st["head"]),
          Paragraph("Cantidad", st["head_c"]),
          Paragraph("Precio", st["head_c"]),
          Paragraph("Importe", st["head_c"])]],
        colWidths=COLS,
    )
    t.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, 0), 0.9, LINEA_HEAD),
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
        ("LEFTPADDING", (0, 0), (0, 0), 4),
        ("LEFTPADDING", (1, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 4.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ]))
    return t


def _marco_imagen(ruta_rel, azul_color, ancho=140, max_w=132, max_h=148):
    """Imagen de producto enmarcada en azul, o None si no se puede cargar."""
    if not ruta_rel:
        return None
    ruta = _static_path(ruta_rel)
    if not ruta.exists():
        return None
    img = _fit_image(ruta, max_w, max_h, halign="LEFT")
    if not img:
        return None
    marco = Table([[img]], colWidths=[ancho])
    marco.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1.6, azul_color),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return marco


def _datos_opcion(op, partida):
    """Normaliza una opción de producto (o el propio primario de la partida).

    Ojo: cuando `op` **es** la partida, sus atributos `nombre`/`unidad` son
    los de la PARTIDA («Solado de porcelanato», «m2»), no los del producto.
    Los del producto viven en `producto_nombre` / `producto_unidad`, así que
    esos tienen prioridad cuando existen.
    """
    es_primario = op is partida or hasattr(op, "producto_nombre")
    if es_primario:
        nombre = str(getattr(op, "producto_nombre", "") or "")
        unidad = str(getattr(op, "producto_unidad", "") or "")
        precio = getattr(op, "producto_precio", None)
        imagen = str(getattr(op, "producto_imagen", "") or "")
        marca = str(getattr(op, "producto_marca", "") or "")
        modelo = str(getattr(op, "producto_modelo", "") or "")
        color = str(getattr(op, "producto_color", "") or "")
        acabado = str(getattr(op, "producto_acabado", "") or "")
        sku = str(getattr(op, "producto_sku", "") or "")
        descripcion = ""
    else:
        nombre = str(getattr(op, "nombre", "") or "")
        unidad = str(getattr(op, "unidad", "") or "")
        precio = getattr(op, "precio", None)
        imagen = str(getattr(op, "imagen", "") or "")
        marca = str(getattr(op, "marca", "") or "")
        modelo = str(getattr(op, "modelo", "") or "")
        color = str(getattr(op, "color", "") or "")
        acabado = str(getattr(op, "acabado", "") or "")
        sku = str(getattr(op, "sku", "") or "")
        descripcion = str(getattr(op, "descripcion", "") or "")

    unidad = unidad or str(getattr(partida, "unidad", "") or "ud")
    detalle_items = [v for v in (marca, modelo, color, acabado) if v]
    detalle = " · ".join(detalle_items) if detalle_items else ""

    return {
        "nombre": nombre,
        "unidad": unidad,
        "precio": precio,
        "imagen": imagen,
        "marca": marca,
        "modelo": modelo,
        "color": color,
        "acabado": acabado,
        "sku": sku,
        "detalle": detalle,
        "descripcion": descripcion,
    }


def _bloque_productos(partida, filas, estilos, st, moneda, mon_simb, azul_color,
                      ctx, interactiva, pid):
    """Filas del bloque «producto(s)» de una partida.

    Con una sola opción se conserva el formato clásico («Producto
    presupuestado: 68,00 $/m2  Porcelanato»). Con varias se presentan en
    elegantes tarjetas de opción con su foto, specs y precio. Si el PDF es
    interactivo, lleva un radio button AcroForm sin superponer imágenes.
    """
    opciones = list(getattr(partida, "productos_multiples", None) or [partida])
    elegido = int(getattr(partida, "indice_producto_elegido", 0) or 0)
    if elegido >= len(opciones):
        elegido = 0

    def fila_ancho_completo(contenido, arriba=1, abajo=2):
        indice = len(filas)
        filas.append([contenido, "", "", ""])
        estilos.extend([
            ("SPAN", (0, indice), (-1, indice)),
            ("TOPPADDING", (0, indice), (-1, indice), arriba),
            ("BOTTOMPADDING", (0, indice), (-1, indice), abajo),
        ])
        return indice

    def _ruta_imagen_robusta(rel):
        if not rel:
            return None
        s = str(rel).strip().lstrip("/")
        if s.startswith("static/"):
            s = s[7:]
        r1 = _static_path(rel)
        if r1 and r1.exists():
            return r1
        r2 = BASE_DIR / "app" / "static" / s
        if r2.exists():
            return r2
        r3 = UPLOADS_DIR / s
        if r3.exists():
            return r3
        return None

    # ---- Un solo producto: formato clásico ------------------------------
    if len(opciones) == 1:
        datos = _datos_opcion(opciones[0], partida)
        fila_ancho_completo(Paragraph("Producto presupuestado:", st["prod_lab"]), arriba=6, abajo=1)
        linea = ""
        if datos["precio"] is not None:
            linea = f"<b>{fmt_num(datos['precio'])} {mon_simb} / {_esc(datos['unidad'])}</b>&nbsp;&nbsp;&nbsp;&nbsp;"
        linea += f"<i>{_esc(datos['nombre'])}</i>"
        if datos["detalle"]:
            linea += f"<br/><font size='8' color='#64748B'>{_esc(datos['detalle'])}</font>"
        fila_ancho_completo(Paragraph(linea, st["prod"]))
        ruta = _ruta_imagen_robusta(datos["imagen"])
        if ruta:
            rel_path = str(ruta.relative_to(BASE_DIR / "app" / "static") if (BASE_DIR / "app" / "static") in ruta.parents else datos["imagen"])
            marco = _marco_imagen(rel_path, azul_color)
            if marco is not None:
                indice = fila_ancho_completo(marco, arriba=4, abajo=2)
                estilos.append(("LEFTPADDING", (0, indice), (-1, indice), 0))
        return filas, estilos

    # ---- Varios productos a elegir --------------------------------------
    if interactiva:
        titulo = "OPCIONES DE PRODUCTO A ELEGIR (selecciona una opción para recalcular el presupuesto):"
    else:
        titulo = "OPCIONES DE PRODUCTO DISPONIBLES:"
    fila_ancho_completo(Paragraph(titulo, st["prod_lab"]), arriba=8, abajo=4)

    ancho_foto = 100
    ancho_texto = _ANCHO - ancho_foto - 24

    for i, op in enumerate(opciones):
        datos = _datos_opcion(op, partida)
        marcado = (i == elegido)

        # Cabecera de la tarjeta con badge de Opción
        num_op = i + 1
        if marcado:
            badge_txt = f"<font color='#0F4C81'><b>✓ OPCIÓN {num_op} — SELECCIONADA</b></font>"
        else:
            badge_txt = f"<font color='#64748B'><b>OPCIÓN {num_op}</b></font>"

        precio_txt = ""
        if datos["precio"] is not None:
            precio_txt = f"<font color='#0F4C81'><b>{fmt_num(datos['precio'])} {mon_simb} / {_esc(datos['unidad'])}</b></font>"

        nombre_txt = _esc(datos["nombre"]) or "—"

        # Fila 1 del texto: Radio AcroForm (si es interactivo) + Nombre del producto
        tooltip = "Elegir «%s»" % saneado(datos["nombre"] or "producto")
        if interactiva:
            radio = ctx.radio(partida, i, marcado, tooltip=tooltip)
            head_table = Table(
                [[radio, Paragraph(f"<b>{nombre_txt}</b>", st["prod"])]],
                colWidths=[16, ancho_texto - 20],
            )
            head_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            linea_nombre = head_table
        else:
            prefijo = "&#10003;&nbsp;" if marcado else "&#8226;&nbsp;"
            linea_nombre = Paragraph(f"<b>{prefijo}{nombre_txt}</b>", st["prod"])

        # Fila de detalles / especificaciones
        cuerpo_items = [Paragraph(badge_txt, st["prod"]), linea_nombre]
        if precio_txt:
            cuerpo_items.append(Paragraph(precio_txt, st["prod"]))
        if datos["detalle"]:
            cuerpo_items.append(Paragraph(f"<font size='8' color='#64748B'><i>{_esc(datos['detalle'])}</i></font>", st["prod"]))
        if datos["descripcion"]:
            cuerpo_items.append(Paragraph(f"<font size='7.8' color='#475569'>{_esc(datos['descripcion'][:220])}</font>", st["prod"]))

        cuerpo_cell = Table([[item] for item in cuerpo_items], colWidths=[ancho_texto - 10])
        cuerpo_cell.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING", (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))

        # Foto del producto
        ruta = _ruta_imagen_robusta(datos["imagen"])
        if ruta:
            foto_img = _fit_image(ruta, ancho_foto - 12, ancho_foto - 12, halign="CENTER")
            if foto_img:
                foto_box = Table([[foto_img]], colWidths=[ancho_foto])
                foto_box.setStyle(TableStyle([
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#CBD5E1")),
                    ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ]))
            else:
                foto_box = Paragraph("<font size='8' color='#94A3B8'>Sin imagen</font>", st["mini"])
        else:
            foto_box = Paragraph("<font size='8' color='#94A3B8'>Sin imagen</font>", st["mini"])

        # Ensamblar la tarjeta completa
        tarjeta = Table(
            [[foto_box, cuerpo_cell]],
            colWidths=[ancho_foto + 6, ancho_texto],
        )
        border_color = azul_color if marcado else colors.HexColor("#CBD5E1")
        bg_color = colors.HexColor("#F0F7FF") if marcado else colors.white
        border_width = 1.2 if marcado else 0.6

        tarjeta.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (0, 0), 6),
            ("RIGHTPADDING", (0, 0), (0, 0), 6),
            ("LEFTPADDING", (1, 0), (1, 0), 8),
            ("RIGHTPADDING", (1, 0), (1, 0), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("BOX", (0, 0), (-1, -1), border_width, border_color),
            ("BACKGROUND", (0, 0), (-1, -1), bg_color),
        ]))

        if interactiva:
            tarjeta = ctx.tarjeta_clicable(tarjeta, partida, i, tooltip=tooltip)

        fila_ancho_completo(tarjeta, arriba=4, abajo=4)

    if interactiva:
        nota = ("Este presupuesto es interactivo: pulsa en cualquier parte de la tarjeta "
                "(foto, nombre o texto) para elegir esa opción. Se recalculan el precio "
                "unitario, el importe de la partida y los totales del documento. "
                "Requiere un visor de PDF con soporte para formularios (p. ej. Adobe Acrobat Reader o Foxit).")
        fila_ancho_completo(Paragraph(nota, st["prod_nota"]), arriba=3, abajo=2)

    return filas, estilos


def _tabla_partida(partida, st, moneda, ultima: bool, azul_color, num=None, ctx=None):
    """Una partida: fila principal + mediciones + producto presupuestado.

    Si `num` (p. ej. "1.2") no es None, se antepone al nombre de la partida
    para numerar los trabajos (1.1, 1.2, …).

    Si `ctx` es un :class:`ContextoInteractivo` y la partida ofrece varios
    productos a elegir, el precio unitario y los importes se emiten como
    campos de formulario recalculables y cada producto lleva su casilla.
    """
    mon_simb = moneda or "USD"
    filas = []
    interactiva = ctx is not None and ctx.es_interactiva(partida)
    pid = ctx.id_partida(partida) if interactiva else ""

    tipo = (getattr(partida, "tipo_partida", "included") or "included").lower()
    etiquetas = {
        "optional": "OPCIONAL",
        "alternative": "ALTERNATIVA",
        "excluded": "NO INCLUIDA",
        "provisional": "PROVISIONAL",
        "measurement": "SUJETA A MEDICIÓN",
    }
    etiqueta = etiquetas.get(tipo, "")
    # Traducción VE->país para nombre/descripción (catálogo guarda VE)
    nombre_trad = traducir(partida.nombre, _CODIGO_PAIS_ACTUAL) if _CODIGO_PAIS_ACTUAL else partida.nombre
    desc_trad = traducir(partida.descripcion, _CODIGO_PAIS_ACTUAL) if (_CODIGO_PAIS_ACTUAL and partida.descripcion) else partida.descripcion
    nombre_pdf = f"{_esc(num)}&nbsp;&nbsp;{_esc(nombre_trad)}" if num else _esc(nombre_trad)
    if etiqueta:
        nombre_pdf += f"&nbsp;&nbsp;<font color='#CC0066'><b>[{etiqueta}]</b></font>"
    celda_texto = [Paragraph(nombre_pdf, st["p_nombre"])]
    if desc_trad:
        desc = _esc(desc_trad).replace("\n", "<br/>")
        celda_texto.append(Paragraph(desc, st["p_desc"]))

    if interactiva:
        # El precio unitario y el importe cambian con el producto elegido.
        # El texto inicial se calcula con las MISMAS fórmulas que usará el
        # JavaScript del PDF, así el documento recién abierto y el
        # documento recalculado coinciden siempre al céntimo.
        celda_precio = ctx.campo(
            "pu_" + pid,
            ctx.txt_precio_unitario(partida),
            ctx.js_precio_unitario(partida),
            COLS[2],
        )
        celda_importe = ctx.campo(
            "imp_" + pid,
            ctx.txt_importe(partida),
            ctx.js_importe(partida),
            COLS[3],
        )
    else:
        celda_precio = Paragraph(fmt_precio_u(partida.precio_unitario, moneda, _esc(partida.unidad or "ud")), st["tot_c"])
        celda_importe = Paragraph(fmt_monto(partida.importe, moneda), st["tot_c"])

    filas.append([
        celda_texto,
        Paragraph(fmt_cantidad(partida.cantidad_total, _esc(partida.unidad or "ud")), st["tot_c"]),
        celda_precio,
        celda_importe,
    ])

    for i_med, m in enumerate(partida.mediciones):
        # Cada línea de medición se redondea con la misma regla que el resto
        # del documento (ROUND_HALF_UP a 2 decimales) para que el desglose
        # sea coherente con los importes de fila y totales.
        importe_medicion = _money(m.cantidad * partida.precio_unitario)
        if interactiva:
            celda_med_precio = ctx.campo(
                "mpu_%s_%d" % (pid, i_med),
                ctx.txt_precio_unitario(partida),
                ctx.js_precio_unitario(partida),
                COLS[2], alto=10, tam=8.25, fuente="Helvetica",
            )
            celda_med_importe = ctx.campo(
                "mimp_%s_%d" % (pid, i_med),
                ctx.txt_importe_medicion(partida, i_med),
                ctx.js_importe_medicion(partida, i_med),
                COLS[3], alto=10, tam=8.25, fuente="Helvetica",
            )
        else:
            celda_med_precio = Paragraph(fmt_precio_u(partida.precio_unitario, moneda, _esc(partida.unidad or "ud")), st["med_c"])
            celda_med_importe = Paragraph(fmt_monto(importe_medicion, moneda), st["med_c"])
        filas.append([
            Paragraph(_esc(m.concepto.strip()) or "-", st["med_d"]),
            Paragraph(fmt_cantidad(m.cantidad, _esc(partida.unidad or "ud")), st["med_c"]),
            celda_med_precio,
            celda_med_importe,
        ])

    estilos = [
        ("VALIGN", (0, 0), (0, 0), "TOP"),
        ("VALIGN", (1, 0), (-1, 0), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (0, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING", (1, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, -1), (0, -1), 6),
        ("TOPPADDING", (0, 0), (-1, 0), 7),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 1),
        ("TOPPADDING", (0, 1), (-1, -1), 5.5),
        ("BOTTOMPADDING", (0, 1), (-1, -2), 0.5),
    ]

    # -- Productos presupuestados -----------------------------------------
    if partida.tiene_producto:
        filas, estilos = _bloque_productos(
            partida, filas, estilos, st, moneda, mon_simb, azul_color, ctx, interactiva, pid
        )

    idx_ultima = len(filas) - 1
    estilos.append(("BOTTOMPADDING", (0, idx_ultima), (-1, idx_ultima), 8))
    if not ultima:
        estilos.append(("LINEBELOW", (0, idx_ultima), (-1, idx_ultima), 0.8, azul_color))

    t = Table(filas, colWidths=COLS)
    t.setStyle(TableStyle(estilos))
    return t


def _capitulo_flujo(cap, st, moneda, azul_color, cap_index=0, ctx=None):
    banda = _banda(azul_color)
    titulo = _fila_capitulo(cap, st, moneda, azul_color, ctx=ctx)
    columnas = _fila_columnas(st)
    partidas = [
        _tabla_partida(p, st, moneda, i == len(cap.partidas) - 1, azul_color,
                       num=f"{cap_index + 1}.{i + 1}", ctx=ctx)
        for i, p in enumerate(cap.partidas)
    ]
    flujo = []
    if partidas:
        flujo.append(KeepTogether([banda, titulo, columnas, partidas[0]]))
        flujo.extend(KeepTogether(p) for p in partidas[1:])
    else:
        flujo.append(KeepTogether([banda, titulo, columnas]))
    return flujo


# ---------------------------------------------------------------------------
# Bloque de totales y secciones finales
# ---------------------------------------------------------------------------

def _totales(presupuesto, st, moneda, azul_color, etiqueta_total="PRESUPUESTO TOTAL", ctx=None):
    filas = []
    ancho_valor = 135

    def valor(clave, importe, estilo, prefijo=""):
        """Celda de importe: campo recalculable si el PDF es interactivo."""
        if ctx is None:
            return Paragraph(prefijo + fmt_monto(importe, moneda), st[estilo])
        alturas = {"tot_lab_s": 14, "tot_lab": 16, "tot_lab_g": 18}
        tamanos = {"tot_lab_s": 10.5, "tot_lab": 12, "tot_lab_g": 13.5}
        return ctx.campo(
            "tot_" + clave, ctx.txt_total(clave), ctx.js_total(clave), ancho_valor,
            alto=alturas.get(estilo, 14), alineacion="right", tam=tamanos.get(estilo, 10.5),
        )

    if getattr(presupuesto, "usar_funciones_avanzadas", False):
        filas.append([Paragraph("SUBTOTAL INCLUIDO", st["tot_lab_s"]), valor("subtotal", presupuesto.subtotal, "tot_lab_s"), ""])
        if getattr(presupuesto, "subtotal_opcional", 0):
            filas.append([Paragraph("OPCIONALES DISPONIBLES", st["tot_lab_s"]), valor("opcional", presupuesto.subtotal_opcional, "tot_lab_s"), ""])
        if getattr(presupuesto, "subtotal_alternativas", 0):
            filas.append([Paragraph("ALTERNATIVAS DISPONIBLES", st["tot_lab_s"]), valor("alternativas", presupuesto.subtotal_alternativas, "tot_lab_s"), ""])
        if getattr(presupuesto, "costes_adicionales", 0):
            filas.append([Paragraph("COSTES ADICIONALES", st["tot_lab_s"]), valor("adicionales", presupuesto.costes_adicionales, "tot_lab_s"), ""])
    filas.append([Paragraph("BASE IMPONIBLE", st["tot_lab"]), valor("base", presupuesto.base, "tot_lab"), ""])
    if presupuesto.descuento_pct:
        filas.append([
            Paragraph(f"DESCUENTO ({fmt_pct(presupuesto.descuento_pct)} %)", st["tot_lab_s"]),
            valor("descuento", presupuesto.descuento_monto, "tot_lab_s", prefijo="- "), "",
        ])
    filas.append([
        Paragraph(f"I.V.A. ({fmt_pct(presupuesto.impuesto_pct)} %)", st["tot_lab_s"]),
        valor("impuesto", presupuesto.impuesto_monto, "tot_lab_s"), "",
    ])
    filas.append([
        Paragraph(etiqueta_total, st["tot_lab_g"]),
        valor("total", presupuesto.total, "tot_lab_g"), "",
    ])

    n = len(filas)
    t = Table(filas, colWidths=[_ANCHO - 141, 135, 6])
    estilos = [
        ("BACKGROUND", (0, 0), (1, -1), FONDO),
        ("BACKGROUND", (2, 0), (2, -1), azul_color),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (1, -1), 8),
        ("LEFTPADDING", (2, 0), (2, -1), 0),
        ("RIGHTPADDING", (2, 0), (2, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, 0), 14),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 14),
    ]
    for i in range(n - 1):
        estilos.append(("LINEBELOW", (0, i), (1, i), 0.75, LINEA_TOT))
    t.setStyle(TableStyle(estilos))
    return t


def _seccion(titulo, contenido, st, azul_color):
    return KeepTogether([
        Paragraph(_esc(titulo), st["t13"]),
        _hr(azul_color, 1, spaceBefore=4, spaceAfter=7),
        Paragraph(_esc(contenido).replace("\n", "<br/>"), st["nota"]),
    ])


# ---------------------------------------------------------------------------
# Pie de página «n / N»
# ---------------------------------------------------------------------------

class _CanvasNumerado(canvas.Canvas):
    """Pie de página «n/N» + marca de agua según el estado del documento.

    Cuando se le pasa un `ctx` interactivo, además cierra el formulario del
    PDF (orden de cálculo y script del documento) justo antes de guardar.
    """

    _MARCAS = {
        "borrador": "BORRADOR",
        "rechazado": "RECHAZADO",
        "vencido": "VENCIDO",
    }

    def __init__(self, *args, estado="", ctx=None, paginas_extra=0, **kwargs):
        super().__init__(*args, **kwargs)
        self._paginas = []
        self._estado = estado
        self._ctx = ctx
        # Páginas que se añadirán después (anexos fusionados): el total del
        # pie «n/N» debe contarlas para que coincida con el archivo que
        # recibe el cliente.
        self._paginas_extra = int(paginas_extra or 0)

    def showPage(self):
        self._paginas.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._paginas) + self._paginas_extra
        for state in self._paginas:
            self.__dict__.update(state)
            # Marca de agua diagonal (sobre el contenido, con transparencia)
            marca = self._MARCAS.get(self._estado)
            if marca:
                self.saveState()
                self.setFont("Lato-Bold", 62)
                self.setFillColor(colors.HexColor("#445566"))
                self.setFillAlpha(0.09)
                self.translate(A4[0] / 2, A4[1] / 2)
                self.rotate(45)
                self.drawCentredString(0, 0, marca)
                self.restoreState()
            self.setFont("Lato", 7.5)
            self.setFillColor(GRIS)
            self.drawRightString(A4[0] - 34, 16, f"{self._pageNumber}/{total}")
            canvas.Canvas.showPage(self)
        # El formulario debe cerrarse con TODOS los campos ya emitidos: por
        # eso se hace aquí y no en `generar_pdf`.
        if self._ctx is not None:
            self._ctx.aplicar_al_canvas(self)
        canvas.Canvas.save(self)


# ---------------------------------------------------------------------------
# Opciones Premium: Portada, Resumen Ejecutivo y Firmas
# ---------------------------------------------------------------------------

def _portada_presentacion(presupuesto, config, st, azul_color):
    """Genera una portada de nivel editorial claramente diferenciada.

    Estructura: banda superior de marca (azul, con logo o nombre), título
    grande del proyecto, foto destacada (o un recuadro decorativo si no la
    hay), ficha del cliente y banda inferior de cierre, en página completa.
    """
    res = []
    ancho = _ANCHO

    # ------------------------------------------------------------------
    # Banda superior de marca (fondo azul)
    # ------------------------------------------------------------------
    logo_flow = None
    if config.logo:
        ruta = _static_path(config.logo)
        if ruta.exists():
            ancho_logo = int(getattr(config, "logo_ancho_pdf", None) or 360)
            ancho_logo = max(140, min(ancho_logo, 500))
            logo_flow = _fit_image(ruta, ancho_logo + 20, 105, halign="CENTER")

    marca_cell = logo_flow
    if marca_cell is None:
        st_marca = ParagraphStyle(
            "marca_banda", fontName="Lato-Bold", fontSize=23, leading=28,
            alignment=TA_CENTER, textColor=colors.white,
        )
        marca_cell = Paragraph(_esc(config.empresa_nombre or "MI EMPRESA"), st_marca)

    banda = Table([[marca_cell]], colWidths=[ancho], rowHeights=[120])
    banda.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), azul_color),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 20),
        ("RIGHTPADDING", (0, 0), (-1, -1), 20),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    res.append(banda)
    res.append(Spacer(1, 34))

    # ------------------------------------------------------------------
    # Título del documento y del proyecto
    # ------------------------------------------------------------------
    st_lab = ParagraphStyle(
        "port_lab", fontName="Lato-Bold", fontSize=10.5, leading=13,
        alignment=TA_CENTER, textColor=GRIS, textTransform="uppercase",
    )
    res.append(Paragraph("Propuesta comercial de proyecto y presupuesto", st_lab))
    res.append(Spacer(1, 10))

    st_tit = ParagraphStyle(
        "port_tit", fontName="Lato-Bold", fontSize=25, leading=30,
        alignment=TA_CENTER, textColor=azul_color,
    )
    res.append(Paragraph(_esc(presupuesto.titulo or "Remodelación de vivienda de lujo"), st_tit))
    res.append(_hr(azul_color, 2, 170, hAlign="CENTER", spaceBefore=16, spaceAfter=26))

    # ------------------------------------------------------------------
    # Foto del proyecto (o recuadro decorativo)
    # ------------------------------------------------------------------
    img_proyecto = None
    if presupuesto.foto_proyecto:
        ruta_p = _static_path(presupuesto.foto_proyecto)
        if ruta_p.exists():
            img_proyecto = _fit_image(ruta_p, 430, 250, halign="CENTER")

    if img_proyecto:
        marco = Table([[img_proyecto]], colWidths=[450])
        marco.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 1.6, azul_color),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        res.append(marco)
        res.append(Spacer(1, 28))
    else:
        st_ph = ParagraphStyle(
            "ph", fontName="Lato-Bold", fontSize=12, leading=16,
            alignment=TA_CENTER, textColor=GRIS,
        )
        ph_cell = Paragraph(_esc(config.empresa_nombre or "MI EMPRESA"), st_ph)
        ph = Table([[ph_cell]], colWidths=[450], rowHeights=[170])
        ph.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EEF2F7")),
            ("BOX", (0, 0), (-1, -1), 1.6, colors.HexColor("#C6CFDD")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ]))
        res.append(ph)
        res.append(Spacer(1, 12))
        st_hint = ParagraphStyle(
            "ph_hint", fontName="Lato-Italic", fontSize=10, leading=13,
            alignment=TA_CENTER, textColor=GRIS,
        )
        res.append(Paragraph(
            "Sube una foto destacada del proyecto (render o estado actual) en "
            "«Opciones premium» para mostrarla en esta portada.",
            st_hint,
        ))
        res.append(Spacer(1, 26))

    # ------------------------------------------------------------------
    # Ficha del cliente / presupuesto
    # ------------------------------------------------------------------
    st_meta_lbl = ParagraphStyle("port_ml", fontName="Lato-Bold", fontSize=9, leading=12, textColor=GRIS)
    st_meta_val = ParagraphStyle("port_mv", fontName="Lato", fontSize=10, leading=12.5, textColor=TEXTO)

    meta_filas = [
        [Paragraph("CLIENTE", st_meta_lbl), Paragraph(_esc(presupuesto.cliente.nombre), st_meta_val)],
        [Paragraph("PRESUPUESTO Nº", st_meta_lbl), Paragraph(_esc(presupuesto.numero), st_meta_val)],
        [Paragraph("FECHA DE EMISIÓN", st_meta_lbl), Paragraph(fmt_fecha(presupuesto.fecha), st_meta_val)],
    ]
    if presupuesto.direccion_obra:
        meta_filas.append([Paragraph("OBRA / DIRECCIÓN", st_meta_lbl), Paragraph(_esc(presupuesto.direccion_obra), st_meta_val)])
    if presupuesto.validez_dias:
        meta_filas.append([Paragraph("VALIDEZ DE LA OFERTA", st_meta_lbl), Paragraph(f"{presupuesto.validez_dias} días", st_meta_val)])

    t_meta = Table(meta_filas, colWidths=[150, _ANCHO - 150 - 120])
    t_meta.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, colors.HexColor("#DDE3EC")),
    ]))
    t_meta_wrap = Table([[t_meta]], colWidths=[_ANCHO])
    t_meta_wrap.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 60),
        ("RIGHTPADDING", (0, 0), (-1, -1), 60),
    ]))
    res.append(t_meta_wrap)
    res.append(Spacer(1, 40))

    # ------------------------------------------------------------------
    # Banda inferior de cierre
    # ------------------------------------------------------------------
    banda2 = Table([[""]], colWidths=[ancho], rowHeights=[30])
    banda2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), azul_color),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    res.append(banda2)

    res.append(PageBreak())
    return res


def _tabla_garantias(presupuesto, st, azul_color):
    """Bloque de garantías al tono del resto del PDF (no una parrilla Excel)."""
    from .garantias import NOTA_LEGAL, familias_para_pdf

    familias = familias_para_pdf(presupuesto)
    st_grupo = ParagraphStyle(
        "gar_grupo", fontName="Lato-Bold", fontSize=9.4, leading=12, textColor=TEXTO,
    )
    st_plazo = ParagraphStyle(
        "gar_plazo", fontName="Lato-Bold", fontSize=10, leading=12,
        textColor=azul_color, alignment=TA_RIGHT,
    )
    st_alcance = ParagraphStyle(
        "gar_alcance", fontName="Lato", fontSize=8.3, leading=11.2, textColor=GRIS,
    )
    st_intro = ParagraphStyle(
        "gar_intro", fontName="Lato", fontSize=8.6, leading=11.6, textColor=GRIS,
    )
    st_nota = ParagraphStyle(
        "gar_nota", fontName="Lato", fontSize=8, leading=11, textColor=GRIS,
    )

    flujo = [
        _banda(azul_color),
        Spacer(1, 8),
        Paragraph("GARANTÍAS DE LA OBRA", st["cap"]),
        _hr(azul_color, 2, spaceBefore=2, spaceAfter=8),
        Paragraph(
            "Plazos sobre la <b>ejecución e instalación</b> de los trabajos "
            "incluidos en este presupuesto, agrupados por tipo de obra. "
            "Los materiales, luminarias, grifería y equipos conservan la "
            "garantía de su fabricante.",
            st_intro,
        ),
        Spacer(1, 12),
    ]

    for i, fam in enumerate(familias):
        cab = Table(
            [[
                Paragraph(_esc(fam["grupo"]).upper(), st_grupo),
                Paragraph(_esc(fam["plazo"]), st_plazo),
            ]],
            colWidths=[_ANCHO - 88, 88],
        )
        cab.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), FONDO),
            ("LINEBEFORE", (0, 0), (0, 0), 3, azul_color),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (0, 0), 10),
            ("RIGHTPADDING", (0, 0), (0, 0), 6),
            ("LEFTPADDING", (1, 0), (1, 0), 4),
            ("RIGHTPADDING", (1, 0), (1, 0), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        cuerpo = Table(
            [[Paragraph(_esc(fam["alcance"]), st_alcance)]],
            colWidths=[_ANCHO],
        )
        cuerpo.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.white),
            ("BOX", (0, 0), (-1, -1), 0.4, LINEA_TOT),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        bloque = [cab, cuerpo]
        if i < len(familias) - 1:
            bloque.append(Spacer(1, 7))
        flujo.append(KeepTogether(bloque))

    nota = Table(
        [[Paragraph(_esc(NOTA_LEGAL), st_nota)]],
        colWidths=[_ANCHO],
    )
    nota.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F4F6F9")),
        ("LINEBEFORE", (0, 0), (0, 0), 3, azul_color),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    flujo += [Spacer(1, 12), nota, Spacer(1, 8)]
    return flujo


def _resumen_comercial(presupuesto, st, moneda, azul_color, ctx=None):
    """Resumen comercial corto y visible para el cliente.

    No muestra costes internos, beneficio ni tiempos. Solo lo que el cliente
    necesita identificar rápido al abrir el PDF: total, validez, fecha y moneda.
    """
    title_style = ParagraphStyle(
        "resumen_comercial_titulo",
        fontName="Lato-Bold",
        fontSize=11.2,
        leading=13.5,
        textColor=TEXTO,
    )
    label_style = ParagraphStyle(
        "resumen_comercial_label",
        fontName="Lato-Bold",
        fontSize=7.5,
        leading=9,
        textColor=GRIS,
        alignment=TA_CENTER,
    )
    value_style = ParagraphStyle(
        "resumen_comercial_valor",
        fontName="Lato-Bold",
        fontSize=11,
        leading=13,
        textColor=TEXTO,
        alignment=TA_CENTER,
    )
    total_style = ParagraphStyle(
        "resumen_comercial_total",
        fontName="Lato-Bold",
        fontSize=13.5,
        leading=16,
        textColor=azul_color,
        alignment=TA_CENTER,
    )

    def total_cell():
        if ctx is None:
            return Paragraph(fmt_monto(presupuesto.total, moneda), total_style)
        return ctx.campo(
            "resumen_total", ctx.txt_total("total"), ctx.js_total("total"),
            126, alto=18, alineacion="center", tam=12.5,
        )

    validez = f"{presupuesto.validez_dias} días" if presupuesto.validez_dias else "—"
    filas = [
        [Paragraph("TOTAL", label_style), Paragraph("VALIDEZ", label_style), Paragraph("FECHA", label_style), Paragraph("MONEDA", label_style)],
        [total_cell(), Paragraph(validez, value_style), Paragraph(fmt_fecha(presupuesto.fecha), value_style), Paragraph(_esc(moneda), value_style)],
    ]
    tabla = Table(filas, colWidths=[_ANCHO * 0.34, _ANCHO * 0.22, _ANCHO * 0.22, _ANCHO * 0.22])
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#DDE3EC")),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#DDE3EC")),
        ("LINEBEFORE", (1, 0), (-1, -1), 0.5, colors.HexColor("#E5EAF1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    return KeepTogether([
        Paragraph("RESUMEN DE LA PROPUESTA", title_style),
        _hr(azul_color, 1.2, spaceBefore=4, spaceAfter=8),
        tabla,
        Spacer(1, 16),
    ])


def _resumen_ejecutivo(presupuesto, st, moneda, azul_color, ctx=None):
    """Genera una elegante tabla con el resumen de subtotales por capítulo.

    Si `ctx` está presente (PDF interactivo) el subtotal y el peso de cada
    capítulo se emiten como campos de formulario, para que sigan cuadrando
    con el resto del documento al cambiar de producto.
    """
    elementos = []
    
    title_style = ParagraphStyle("res_title", fontName="Lato-Bold", fontSize=11, leading=13, textColor=TEXTO)
    elementos.append(Paragraph("RESUMEN EJECUTIVO DE LA PROPUESTA (DESGLOSE POR CAPÍTULOS)", title_style))
    elementos.append(_hr(azul_color, 1.2, spaceBefore=4, spaceAfter=8))
    
    filas = [
        [
            Paragraph("<b>Capítulo del Proyecto</b>", st["head"]),
            Paragraph("<b>Subtotal</b>", st["head_c"]),
            Paragraph("<b>Peso (%)</b>", st["head_c"])
        ]
    ]
    
    subtotal_general = presupuesto.subtotal or 1.0
    
    for cap in presupuesto.capitulos:
        porcentaje = (cap.subtotal / subtotal_general) * 100.0
        if ctx is None:
            celda_subtotal = Paragraph(fmt_monto(cap.subtotal, moneda), st["tot_c"])
            celda_peso = Paragraph(f"{porcentaje:.1f} %", st["tot_c"])
        else:
            cid = ctx.id_capitulo(cap)
            celda_subtotal = ctx.campo(
                "res_" + cid, ctx.txt_capitulo(cap), ctx.js_capitulo(cap),
                100, alto=12, alineacion="center", tam=9, fuente="Helvetica",
            )
            celda_peso = ctx.campo(
                "pes_" + cid, ctx.txt_peso_capitulo(cap), ctx.js_peso_capitulo(cap),
                80, alto=12, alineacion="center", tam=9, fuente="Helvetica",
            )
        filas.append([
            Paragraph(_esc(cap.nombre.upper()), st["campo"]),
            celda_subtotal,
            celda_peso,
        ])
        
    t_resumen = Table(filas, colWidths=[_ANCHO - 180, 100, 80])
    
    estilos = [
        ("LINEBELOW", (0, 0), (-1, 0), 1.5, azul_color),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F8FAFC")),
    ]
    
    for i in range(1, len(filas)):
        estilos.append(("LINEBELOW", (0, i), (-1, i), 0.5, colors.HexColor("#E2E8F0")))
        
    t_resumen.setStyle(TableStyle(estilos))
    elementos.append(t_resumen)
    elementos.append(Spacer(1, 20))
    
    return KeepTogether(elementos)


def _bloque_firmas(presupuesto, config, st, azul_color):
    """Genera un área de firma bilateral estructurada al final.

    Si el presupuesto tiene una firma digital del cliente (dibujada en la
    web), se inserta sobre la línea de firma.
    """
    col_w = _ANCHO / 2 - 10
    
    empresa_p = [
        Paragraph("<b>POR LA EMPRESA CONSTRUCTORA</b>", st["tot_c"]),
        Spacer(1, 45),
        _hr(colors.HexColor("#A0AEC0"), 0.8, 180, hAlign="CENTER"),
        Spacer(1, 4),
        Paragraph(_esc(config.empresa_nombre), st["tot_c"]),
        Paragraph(f"RIF: {_esc(config.empresa_rif)}" if config.empresa_rif else "", st["head_c"]),
    ]

    # Firma digital del cliente (opcional)
    firma_flow = None
    ruta_firma = getattr(presupuesto, "firma_cliente", "") or ""
    if ruta_firma:
        p_f = _static_path(ruta_firma)
        if p_f.exists():
            firma_flow = _fit_image(p_f, 175, 62, halign="CENTER")

    cliente_p = [
        Paragraph("<b>ACEPTADO POR EL CLIENTE</b>", st["tot_c"]),
        Spacer(1, 10),
    ]
    if firma_flow:
        cliente_p.append(firma_flow)
        cliente_p.append(Spacer(1, 6))
    cliente_p += [
        _hr(colors.HexColor("#A0AEC0"), 0.8, 180, hAlign="CENTER"),
        Spacer(1, 4),
        Paragraph(_esc(presupuesto.cliente.nombre), st["tot_c"]),
        Paragraph("Firma de Conformidad / Fecha", st["head_c"]),
    ]
    
    t_firmas = Table([[empresa_p, "", cliente_p]], colWidths=[col_w, 20, col_w])
    t_firmas.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    
    return KeepTogether([
        Spacer(1, 15),
        _hr(azul_color, 1.2, spaceBefore=4, spaceAfter=12),
        t_firmas
    ])


# ---------------------------------------------------------------------------
# Documento completo
# ---------------------------------------------------------------------------

def generar_pdf(presupuesto, config):
    """Devuelve un BytesIO con el PDF del presupuesto.

    Si alguna partida ofrece varios productos a elegir, el documento se
    genera como PDF interactivo: el cliente marca la alternativa que
    prefiere y el precio unitario, los importes, los subtotales de capítulo
    y los totales se recalculan dentro del propio PDF (ver
    :mod:`app.services.pdf_interactivo`).

    Cuando el presupuesto tiene anexos y la opción está activada, los anexos
    se incorporan como páginas finales del mismo archivo y el índice indica
    en qué página empieza cada uno (ver :mod:`app.services.pdf_anexos`).
    """
    anexos = pdf_anexos.cargar(presupuesto)
    if not anexos:
        return _documento_presupuesto(presupuesto, config)

    # El índice cita la página en la que empieza cada anexo, pero esa página
    # depende de cuántas ocupe el presupuesto, que solo se sabe tras generar.
    # Se genera con un índice provisional del mismo número de líneas, se mide
    # y se vuelve a generar con las páginas reales; si el texto definitivo
    # cambiase la paginación, se repite una vez más.
    buf = _documento_presupuesto(
        presupuesto, config, pdf_anexos.texto(pdf_anexos.plan_provisional(anexos))
    )
    for _ in range(2):
        tam, paginas = pdf_anexos.medir(buf)
        pdf_anexos.planificar(anexos, tam, paginas)
        buf = _documento_presupuesto(
            presupuesto, config, pdf_anexos.texto(anexos),
            paginas_extra=pdf_anexos.paginas_incorporadas(anexos),
        )
        if pdf_anexos.medir(buf)[1] == paginas:
            break

    fusionado = pdf_anexos.fusionar(buf, anexos)
    if len(fusionado.getvalue()) <= pdf_anexos.LIMITE_DURO_BYTES:
        return fusionado
    # Red de seguridad: si aun así el archivo se pasa del tope, se entrega el
    # presupuesto sin fusionar antes que una descarga que el servidor rechace.
    return _documento_presupuesto(
        presupuesto, config, pdf_anexos.texto(pdf_anexos.descartar_todos(anexos))
    )


def _documento_presupuesto(presupuesto, config, texto_anexos="", paginas_extra=0):
    """Construye el PDF del presupuesto (sin fusionar los anexos).

    ``paginas_extra`` son las páginas de anexos que se añadirán después: el
    pie «n/N» las cuenta para que el total sea el del archivo entregado.
    """
    _registrar_fuentes()
    st = _estilos()
    moneda = presupuesto.moneda
    palette = {"tecnica": "#334155", "minimalista": "#475569", "corporativa": "#0F4C81", "compacta": "#374151", "editorial": "#7C2D12"}
    azul_color = colors.HexColor(palette.get(getattr(presupuesto, "estilo_pdf", "elegante"), config.pdf_color or "#04265D"))
    global _CODIGO_PAIS_ACTUAL
    try:
        _CODIGO_PAIS_ACTUAL = codigo_desde_pais(getattr(config, "empresa_pais", "") or "")
    except Exception:
        _CODIGO_PAIS_ACTUAL = ""

    # Capa interactiva. `preparar()` decide si hay algo que hacer: sin
    # partidas de varios productos devuelve False y el PDF sale exactamente
    # igual que antes, sin formulario ni JavaScript.
    ctx = ContextoInteractivo(presupuesto, moneda, TEXTO, azul_color)
    if not ctx.preparar():
        ctx = None

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=34,
        rightMargin=34,
        topMargin=30,
        bottomMargin=34,
        title=f"Presupuesto {presupuesto.numero} — {presupuesto.titulo or config.empresa_nombre}",
        author=config.empresa_nombre,
        subject="Presupuesto de remodelación",
    )

    story = []
    
    # Portada de presentación (Opcional)
    if presupuesto.con_portada:
        story += _portada_presentacion(presupuesto, config, st, azul_color)
        
    story += _cabecera(presupuesto, config, st, azul_color)
    story.append(_resumen_comercial(presupuesto, st, moneda, azul_color, ctx=ctx))
    
    # Resumen Ejecutivo de Capítulos (Opcional)
    if presupuesto.mostrar_resumen_capitulos:
        story.append(_resumen_ejecutivo(presupuesto, st, moneda, azul_color, ctx=ctx))

    for i, cap in enumerate(presupuesto.capitulos):
        if i > 0:
            story.append(Spacer(1, 26))
        story += _capitulo_flujo(cap, st, moneda, azul_color, cap_index=i, ctx=ctx)

    # Totales (en página nueva si no caben las ~160 pt)
    story.append(Spacer(1, 22))
    story.append(KeepTogether(_totales(presupuesto, st, moneda, azul_color, ctx=ctx)))

    if presupuesto.notas:
        story.append(Spacer(1, 19))
        story.append(_seccion("Alcance e información adicional", presupuesto.notas, st, azul_color))
    if presupuesto.condiciones:
        story.append(Spacer(1, 19))
        story.append(_seccion("Condiciones comerciales", presupuesto.condiciones, st, azul_color))
    # Datos venezolanos, siempre guardados en el documento para preservar su histórico.
    regional = []
    if getattr(config, "mostrar_numero_control", False) and getattr(presupuesto, "numero_control", ""): regional.append(f"Número de control: {presupuesto.numero_control}")
    if getattr(config, "mostrar_tasa_cambio", False) and presupuesto.tipo_cambio:
        # Tasa genérica LatAm: 1 USD = X en la otra moneda (no solo Bs)
        _mon_tasa = getattr(config, "moneda_default", "") or "USD"
        if _mon_tasa == "BS":
            _mon_tasa = "VES"
        _mon_destino_tasa = presupuesto.moneda if presupuesto.moneda not in ("USD", "", "PAB") else _mon_tasa
        if _mon_destino_tasa in ("USD", "", "PAB"):
            _mon_destino_tasa = "VES"
        regional.append(f"Tasa de referencia: 1 USD = {fmt_num(presupuesto.tipo_cambio)} {_mon_destino_tasa}" + (f" ({fmt_fecha(presupuesto.fecha_tipo_cambio)})" if getattr(presupuesto, "fecha_tipo_cambio", None) else ""))
    if getattr(config, "mostrar_total_bs", False) and presupuesto.tipo_cambio:
        # Equivalente genérico: si presupuesto es USD -> muestra en moneda local, si es local -> muestra en USD
        try:
            _mon_cfg = getattr(config, "moneda_default", "") or "USD"
            if _mon_cfg == "BS":
                _mon_cfg = "VES"
            if presupuesto.moneda == "USD" and _mon_cfg not in ("USD", "", "PAB"):
                regional.append(f"Equivalente referencial: {fmt_monto(presupuesto.total * presupuesto.tipo_cambio, _mon_cfg)}")
            elif presupuesto.moneda not in ("USD", "", "PAB") and presupuesto.moneda != _mon_cfg:
                # Presupuesto en local, muestra equivalente en USD
                if presupuesto.tipo_cambio and presupuesto.tipo_cambio != 0:
                    regional.append(f"Equivalente referencial: {fmt_monto(presupuesto.total / presupuesto.tipo_cambio, 'USD')}")
            elif presupuesto.moneda == "USD":
                # Fallback genérico si no hay moneda local configurada
                regional.append(f"Equivalente referencial: {fmt_monto(presupuesto.total * presupuesto.tipo_cambio, 'VES')}")
        except Exception:
            pass
    if getattr(config, "mostrar_retenciones", False) and (getattr(presupuesto, "retencion_pct", 0) or getattr(presupuesto, "operacion_exenta", False)): regional.append("Operación exenta" if presupuesto.operacion_exenta else f"Retención aplicable: {fmt_num(presupuesto.retencion_pct)} %")
    if getattr(config, "datos_bancarios", ""): regional.append("Datos de pago:\n" + config.datos_bancarios)
    if regional: story.append(Spacer(1, 16)); story.append(_seccion("Datos fiscales y pago", "\n".join(regional), st, azul_color))
    if getattr(config, "mostrar_clausula_cambiaria", False) and getattr(presupuesto, "clausula_cambiaria", ""): story.append(Spacer(1, 12)); story.append(_seccion("Cláusula de ajuste cambiario", presupuesto.clausula_cambiaria, st, azul_color))

    # Ahorro comercial visible solo cuando se solicita explícitamente.
    if getattr(presupuesto, "mostrar_ahorro", False) and presupuesto.descuento_pct:
        original = presupuesto.base / max(0.0001, 1 - presupuesto.descuento_pct / 100)
        ahorro = original - presupuesto.base
        texto_ahorro = f"Precio original: {fmt_monto(original, moneda)}\nDescuento comercial: {fmt_monto(ahorro, moneda)}\nPrecio final antes de IVA: {fmt_monto(presupuesto.base, moneda)}"
        story.append(Spacer(1, 16)); story.append(_seccion("Ahorro obtenido", texto_ahorro, st, azul_color))
    if texto_anexos:
        story.append(Spacer(1, 16))
        story.append(_seccion("Anexos incluidos", texto_anexos, st, azul_color))

    # Bloque formal de firmas de aceptación (Opcional)
    if getattr(presupuesto, "mostrar_garantias", False):
        story.append(Spacer(1, 18))
        story += _tabla_garantias(presupuesto, st, azul_color)

    if presupuesto.mostrar_firmas:
        story.append(_bloque_firmas(presupuesto, config, st, azul_color))

    doc.build(story, canvasmaker=lambda *a, **k: _CanvasNumerado(
        *a, estado=presupuesto.estado, ctx=ctx, paginas_extra=paginas_extra, **k))
    buf.seek(0)
    return buf


def generar_factura_pdf(factura, config):
    """Devuelve un PDF comercial de cobro, expresamente no fiscal."""
    _registrar_fuentes()
    st = _estilos()
    moneda = factura.moneda
    azul_color = colors.HexColor(config.pdf_color or "#04265D")

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=34,
        rightMargin=34,
        topMargin=30,
        bottomMargin=34,
        title=f"Documento de cobro {factura.numero} — {factura.titulo or config.empresa_nombre}",
        author=config.empresa_nombre,
        subject="Documento comercial de cobro no fiscal",
    )

    story = []
    story += _cabecera(
        factura, config, st, azul_color,
        titulo_doc="DOCUMENTO DE COBRO", etiqueta_num="Documento Nº", titulo_por_defecto="Documento de cobro",
    )
    story.append(_seccion(
        "Alcance del documento",
        "Documento comercial no fiscal. No sustituye una factura fiscal emitida conforme a la normativa aplicable.",
        st,
        azul_color,
    ))
    story.append(Spacer(1, 14))
    for i, cap in enumerate(factura.capitulos):
        if i > 0:
            story.append(Spacer(1, 26))
        story += _capitulo_flujo(cap, st, moneda, azul_color, cap_index=i)

    story.append(Spacer(1, 22))
    story.append(KeepTogether(_totales(factura, st, moneda, azul_color, etiqueta_total="TOTAL A PAGAR")))

    if factura.notas:
        story.append(Spacer(1, 19))
        story.append(_seccion("Información adicional", factura.notas, st, azul_color))
    if factura.condiciones:
        story.append(Spacer(1, 19))
        story.append(_seccion("Condiciones de pago", factura.condiciones, st, azul_color))

    doc.build(story, canvasmaker=lambda *a, **k: _CanvasNumerado(*a, estado="", **k))
    buf.seek(0)
    return buf
