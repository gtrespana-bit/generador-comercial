"""Recibo en PDF de una licencia de pago (E1-060, segunda parte).

Con el cobro manual del piloto (E1-059), el cliente paga por transferencia,
Zelle, Binance o Pago Móvil y el titular registra la licencia en el panel.
Este módulo produce el comprobante que acompaña ese pago: qué organización
pagó, por qué período de acceso, cuánto y con qué referencia.

Honestidad obligatoria
----------------------
- **No es una factura fiscal.** Mientras el titular no registre su razón
  social no puede existir factura válida; el propio documento lo declara en
  el pie para que nadie lo imprima como si lo fuera.
- Solo existe recibo para licencias ``origen='pago'`` con importe: una
  prueba o una cortesía no generan comprobante de cobro.
"""
from __future__ import annotations

import io
from datetime import date

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from ..branding import LEGAL_ENTITY, PRODUCT_DESCRIPTOR, PRODUCT_NAME, SUPPORT_EMAIL
from ..utils import fmt_fecha, fmt_monto
from .licencias import GestionLicenciaError

_MARCA = colors.HexColor("#0b5b38")


def numero_recibo(licencia) -> str:
    """Número estable del recibo, derivado del registro: CT-000013."""
    return f"CT-{int(licencia.id):06d}"


def _p(texto, estilo):
    return Paragraph(texto or "", estilo)


def generar_recibo_licencia_pdf(
    licencia, organizacion, *, emision: date | None = None
) -> io.BytesIO:
    """Genera el recibo de una licencia de pago.

    Lanza ``GestionLicenciaError`` si la licencia no es de pago: un período
    regalado no tiene comprobante de cobro.
    """
    if licencia.origen != "pago":
        raise GestionLicenciaError(
            "Solo las licencias de pago tienen recibo; este período no se cobró."
        )
    if licencia.importe <= 0:
        raise GestionLicenciaError("Una licencia de pago sin importe no tiene recibo.")

    emision = emision or date.today()
    numero = numero_recibo(licencia)
    dias = (licencia.vence - licencia.inicio).days + 1

    titulo = ParagraphStyle("titulo", fontName="Helvetica-Bold", fontSize=16, alignment=TA_CENTER, spaceAfter=4)
    subtitulo = ParagraphStyle("subtitulo", fontName="Helvetica", fontSize=9.5, alignment=TA_CENTER, textColor=colors.HexColor("#555555"), spaceAfter=14)
    h2 = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=11, spaceBefore=14, spaceAfter=6, textColor=_MARCA)
    normal = ParagraphStyle("normal", fontName="Helvetica", fontSize=9.7, leading=14, alignment=TA_LEFT)
    justificado = ParagraphStyle("justificado", parent=normal, alignment=TA_JUSTIFY)
    etiqueta = ParagraphStyle("etiqueta", fontName="Helvetica-Bold", fontSize=9.5, leading=13)
    pie = ParagraphStyle("pie", fontName="Helvetica", fontSize=8.3, leading=11.5, textColor=colors.HexColor("#66776f"), alignment=TA_JUSTIFY)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=2.2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2.2 * cm,
        rightMargin=2.2 * cm,
        title=f"Recibo {numero} — {PRODUCT_NAME}",
    )

    story = []
    story.append(_p("RECIBO DE SERVICIO", titulo))
    story.append(
        _p(
            f"{PRODUCT_NAME} · {PRODUCT_DESCRIPTOR}<br/>"
            f"N.º {numero} · Emitido el {fmt_fecha(emision)}",
            subtitulo,
        )
    )
    story.append(HRFlowable(width="100%", color=_MARCA, thickness=1.2))
    story.append(Spacer(1, 10))

    # ---- Partes ----------------------------------------------------------
    partes = Table(
        [
            [_p("EMISOR", etiqueta), _p("ORGANIZACIÓN CLIENTE", etiqueta)],
            [
                _p(
                    f"<b>{PRODUCT_NAME}</b><br/>{LEGAL_ENTITY}<br/>"
                    f"Soporte: {SUPPORT_EMAIL}",
                    normal,
                ),
                _p(f"<b>{organizacion.nombre}</b>", normal),
            ],
        ],
        colWidths=[8.2 * cm, 8.2 * cm],
    )
    partes.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
                ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.HexColor("#CCCCCC")),
            ]
        )
    )
    story.append(partes)

    # ---- Concepto ----------------------------------------------------------
    story.append(_p("CONCEPTO", h2))
    filas = [
        ["Concepto", "Período de acceso", "Importe"],
        [
            _p(
                f"Suscripción a {PRODUCT_NAME} — uso del servicio de "
                f"presupuestos y control comercial durante {dias} días.",
                normal,
            ),
            _p(
                f"{fmt_fecha(licencia.inicio)} → {fmt_fecha(licencia.vence)}<br/>"
                f"(ambos inclusive)",
                normal,
            ),
            _p(fmt_monto(licencia.importe, licencia.moneda), normal),
        ],
    ]
    tabla = Table(filas, colWidths=[7.6 * cm, 5.2 * cm, 3.6 * cm])
    tabla.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9.3),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (2, 0), (2, -1), "RIGHT"),
                ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.HexColor("#999999")),
                ("LINEBELOW", (0, -1), (-1, -1), 0.8, _MARCA),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(tabla)

    total = Table(
        [[_p("TOTAL RECIBIDO", etiqueta), _p(fmt_monto(licencia.importe, licencia.moneda), etiqueta)]],
        colWidths=[12.8 * cm, 3.6 * cm],
    )
    total.setStyle(
        TableStyle(
            [
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("FONTSIZE", (0, 0), (-1, -1), 10.5),
                ("TEXTCOLOR", (0, 0), (-1, -1), _MARCA),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(total)

    # ---- Cobro -------------------------------------------------------------
    if licencia.metodo_cobro or licencia.referencia:
        story.append(_p("DATOS DEL COBRO", h2))
        if licencia.metodo_cobro:
            story.append(_p(f"Método: {licencia.metodo_cobro}", normal))
        if licencia.referencia:
            story.append(_p(f"Referencia: {licencia.referencia}", normal))

    # ---- Declaración -------------------------------------------------------
    story.append(Spacer(1, 26))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#CCCCCC"), thickness=0.7))
    story.append(Spacer(1, 8))
    story.append(
        _p(
            "Este documento es un <b>recibo comercial sin validez fiscal ni "
            "tributaria</b>: acredita el pago del servicio entre las partes y "
            "no sustituye una factura. El servicio se rige por los términos "
            "publicados en la aplicación. "
            f"Registrado en el panel de licencias por {licencia.creada_por_email or 'el titular'}. "
            f"Cualquier consulta: {SUPPORT_EMAIL}.",
            pie,
        )
    )

    doc.build(story)
    buf.seek(0)
    return buf
