"""Generación de un contrato de servicios en PDF a partir de un presupuesto.

Reemplaza a los antiguos botones "Generar Contrato (IA)" / "Generar Contrato
Smart", que sólo mostraban un alert() con texto fijo (uno incluso mencionaba
"Blockchain" sin ningún sentido) y no producían ningún documento.

Este generador sí crea un PDF real con las partes, el alcance de obra, el
monto, la forma de pago y la validez de la oferta — todo tomado de los datos
reales del presupuesto y de la configuración de la empresa. No usa ningún
servicio de IA: es una plantilla de contrato de servicios de construcción /
remodelación estándar, rellenada con tus datos.
"""
import io
from datetime import date, timedelta

from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
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
from reportlab.lib import colors

from ..utils import fmt_fecha, fmt_monto


def _p(texto, estilo):
    return Paragraph(texto or "", estilo)


def generar_contrato_pdf(presupuesto, config) -> io.BytesIO:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=2.2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2.2 * cm,
        rightMargin=2.2 * cm,
        title=f"Contrato — Presupuesto {presupuesto.numero}",
    )

    titulo = ParagraphStyle("titulo", fontName="Helvetica-Bold", fontSize=15, alignment=TA_CENTER, spaceAfter=4)
    subtitulo = ParagraphStyle("subtitulo", fontName="Helvetica", fontSize=9.5, alignment=TA_CENTER, textColor=colors.HexColor("#555555"), spaceAfter=14)
    h2 = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=11, spaceBefore=12, spaceAfter=6, textColor=colors.HexColor("#04265D"))
    normal = ParagraphStyle("normal", fontName="Helvetica", fontSize=9.7, leading=14, alignment=TA_JUSTIFY)
    etiqueta = ParagraphStyle("etiqueta", fontName="Helvetica-Bold", fontSize=9.5, leading=13)

    hoy = date.today()
    vencimiento = presupuesto.fecha + timedelta(days=presupuesto.validez_dias or 30)

    story = []
    story.append(_p("CONTRATO DE SERVICIOS DE CONSTRUCCIÓN / REMODELACIÓN", titulo))
    story.append(_p(f"Basado en el presupuesto N.º {presupuesto.numero} · Generado el {fmt_fecha(hoy)}", subtitulo))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#04265D"), thickness=1.2))
    story.append(Spacer(1, 10))

    # ---- Partes -------------------------------------------------------
    empresa_nombre = getattr(config, "empresa_nombre", "") or "Mi Empresa"
    empresa_legal = getattr(config, "empresa_legal", "") or empresa_nombre
    empresa_rif = getattr(config, "empresa_rif", "") or "—"
    empresa_dir = getattr(config, "empresa_direccion", "") or "—"

    cliente = presupuesto.cliente
    filas_partes = [
        [_p("EL CONTRATISTA", etiqueta), _p("EL CLIENTE", etiqueta)],
        [
            _p(f"<b>{empresa_legal}</b><br/>RIF/C.I.: {empresa_rif}<br/>Dirección: {empresa_dir}", normal),
            _p(f"<b>{cliente.nombre}</b><br/>RIF/C.I.: {cliente.rif or '—'}<br/>Dirección: {cliente.direccion or '—'}", normal),
        ],
    ]
    tabla_partes = Table(filas_partes, colWidths=[8.2 * cm, 8.2 * cm])
    tabla_partes.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
                ("TOPPADDING", (0, 1), (-1, 1), 2),
                ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.HexColor("#CCCCCC")),
            ]
        )
    )
    story.append(tabla_partes)

    # ---- Objeto y alcance ----------------------------------------------
    story.append(_p("1. OBJETO DEL CONTRATO", h2))
    alcance = presupuesto.notas or "Ejecución de los trabajos descritos en el presupuesto de referencia."
    obra = presupuesto.titulo or "el proyecto"
    direccion_obra = presupuesto.direccion_obra or "la dirección indicada por EL CLIENTE"
    story.append(
        _p(
            f"EL CONTRATISTA se compromete a ejecutar para EL CLIENTE los trabajos de <b>{obra}</b>, "
            f"en {direccion_obra}, conforme al alcance descrito en el presupuesto N.º {presupuesto.numero} "
            f"y detallado a continuación: {alcance}",
            normal,
        )
    )

    # ---- Resumen de capítulos ------------------------------------------
    if presupuesto.capitulos:
        story.append(_p("2. RESUMEN DE PARTIDAS CONTRATADAS", h2))
        filas = [["Capítulo", "Importe"]]
        for cap in presupuesto.capitulos:
            filas.append([cap.nombre or "—", fmt_monto(cap.subtotal, presupuesto.moneda)])
        tabla_cap = Table(filas, colWidths=[12.4 * cm, 4 * cm])
        tabla_cap.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9.3),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.HexColor("#999999")),
                    ("LINEBELOW", (0, -1), (-1, -1), 0.8, colors.HexColor("#04265D")),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        story.append(tabla_cap)

    # ---- Monto y forma de pago -------------------------------------------
    numero_seccion = 3 if presupuesto.capitulos else 2
    story.append(_p(f"{numero_seccion}. MONTO Y FORMA DE PAGO", h2))
    story.append(
        _p(
            f"El monto total de este contrato es de <b>{fmt_monto(presupuesto.total, presupuesto.moneda)}</b> "
            f"({presupuesto.moneda}), IVA {'incluido' if presupuesto.impuesto_pct else 'no aplicable'}.",
            normal,
        )
    )
    condiciones = presupuesto.condiciones or "A convenir entre las partes antes del inicio de los trabajos."
    story.append(_p(f"Forma de pago: {condiciones}", normal))

    # ---- Vigencia ---------------------------------------------------------
    numero_seccion += 1
    story.append(_p(f"{numero_seccion}. VIGENCIA DE LA OFERTA", h2))
    story.append(
        _p(
            f"Esta propuesta económica es válida hasta el <b>{fmt_fecha(vencimiento)}</b> "
            f"({presupuesto.validez_dias or 30} días desde la fecha del presupuesto). "
            "Pasada esta fecha, los precios deberán ser revisados nuevamente.",
            normal,
        )
    )

    # ---- Firmas -------------------------------------------------------
    story.append(Spacer(1, 36))
    firmas = Table(
        [
            ["_______________________________", "_______________________________"],
            [_p("EL CONTRATISTA", etiqueta), _p("EL CLIENTE", etiqueta)],
            [_p(empresa_legal, normal), _p(cliente.nombre, normal)],
        ],
        colWidths=[8.2 * cm, 8.2 * cm],
    )
    firmas.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("TOPPADDING", (0, 1), (-1, 1), 6)]))
    story.append(firmas)

    doc.build(story)
    buf.seek(0)
    return buf
