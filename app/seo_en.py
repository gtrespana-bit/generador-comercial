"""Copy SEO en inglés para las landings, los hubs de intención y las páginas
estáticas de CotizaT.

Se mantienen aquí los textos en inglés para no mezclarlos con ``seo.py`` y
poder revisarlos de una pieza. El vocabulario sigue la terminología real de
obra en inglés (EE. UU. por defecto):

- presupuesto            -> estimate
- partida                -> line item (en catálogo: work item)
- APU                    -> unit price analysis
- recurso                -> resource (materials / labor / equipment)
- rendimiento            -> productivity rate
- cuadrilla              -> crew
- oficial / ayudante     -> journeyman / helper
- metrado                -> quantity takeoff
- capítulo               -> section
- coste / beneficio      -> cost / profit
- margen                 -> margin
- IVA                    -> VAT
- NIF / RUC / RFC / NIT  -> <acrónimo> + tax ID

Las monedas, los porcentajes de IVA y los identificadores fiscales salen de
``app.paises`` para no duplicar la fuente de datos.
"""
from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Datos por país necesarios para redactar copy en inglés.
# ---------------------------------------------------------------------------
# vocabulario: términos locales (entre paréntesis su equivalente en inglés)
# autoridad: organismo fiscal que emite la factura electrónica local
# precios: frase con las referencias nacionales (cuando el país las tiene)
_PAISES_EN: dict[str, dict[str, Any]] = {
    "": {
        "nombre": "Spain and Latin America",
        "en": "Spain and Latin America",
        "moneda_txt": "your local currency",
        "fiscal_txt": "your local tax ID",
        "iva_txt": "the local VAT rate",
        "vocabulario": (
            "concrete, plaster skim coat, suspended ceiling, baseboard and plumbing"
        ),
        "autoridad": "your national tax authority",
        "ciudad": "",
        "precios": "",
        "nota": "",
    },
    "ES": {
        "nombre": "Spain",
        "en": "Spain",
        "moneda_txt": "euros (EUR)",
        "fiscal_txt": "NIF tax ID",
        "iva_txt": "21% VAT",
        "vocabulario": (
            "concrete (*hormigón*), plasterboard (*pladur*), suspended ceiling "
            "(*falso techo*), wall tiling (*alicatado*) and plumbing (*fontanería*)"
        ),
        "autoridad": "the Spanish Tax Agency (AEAT)",
        "ciudad": "Madrid",
        "precios": "",
        "nota": "",
    },
    "VE": {
        "nombre": "Venezuela",
        "en": "Venezuela",
        "moneda_txt": "US dollars or bolívares",
        "fiscal_txt": "RIF tax ID",
        "iva_txt": "16% VAT",
        "vocabulario": (
            "concrete (*concreto*), trowel plaster (*friso*), suspended ceiling "
            "(*cielo raso*), baseboard (*rodapié*) and plumber (*plomero*)"
        ),
        "autoridad": "SENIAT",
        "ciudad": "Caracas",
        "precios": "",
        "nota": (
            "Every estimate locks its currency and reference exchange rate, so an "
            "old PDF does not move when the rate does."
        ),
    },
    "CO": {
        "nombre": "Colombia",
        "en": "Colombia",
        "moneda_txt": "Colombian pesos (COP)",
        "fiscal_txt": "NIT tax ID",
        "iva_txt": "19% VAT",
        "vocabulario": (
            "concrete (*concreto*), skim-coat plaster (*pañete*), suspended ceiling "
            "(*cielo raso*), baseboard (*guardaescoba*) and plumber (*plomero*)"
        ),
        "autoridad": "DIAN",
        "ciudad": "Bogotá",
        "precios": "",
        "nota": "",
    },
    "MX": {
        "nombre": "Mexico",
        "en": "Mexico",
        "moneda_txt": "Mexican pesos (MXN)",
        "fiscal_txt": "RFC tax ID",
        "iva_txt": "16% VAT",
        "vocabulario": (
            "concrete (*concreto*), skim-coat plaster (*aplanado*), ceiling "
            "(*plafón*), baseboard (*zoclo*) and plumber (*plomero*)"
        ),
        "autoridad": "the SAT (CFDI)",
        "ciudad": "Mexico City",
        "precios": "",
        "nota": "",
    },
    "PE": {
        "nombre": "Peru",
        "en": "Peru",
        "moneda_txt": "Peruvian soles (PEN)",
        "fiscal_txt": "RUC tax ID",
        "iva_txt": "18% IGV",
        "vocabulario": (
            "concrete (*concreto*), wall plastering (*tarrajeo*), suspended ceiling "
            "(*cielo raso*), baseboard (*zócalo*) and plumber (*gasfitero*)"
        ),
        "autoridad": "SUNAT",
        "ciudad": "Lima",
        "precios": "",
        "nota": "",
    },
    "EC": {
        "nombre": "Ecuador",
        "en": "Ecuador",
        "moneda_txt": "US dollars (USD)",
        "fiscal_txt": "RUC tax ID",
        "iva_txt": "15% VAT",
        "vocabulario": (
            "concrete (*hormigón*), skim-coat plaster (*enlucido*), ceiling "
            "(*tumbado*), curb (*barredera*) and plumber (*gasfitero*)"
        ),
        "autoridad": "the SRI",
        "ciudad": "Quito",
        "precios": "",
        "nota": "",
    },
    "CL": {
        "nombre": "Chile",
        "en": "Chile",
        "moneda_txt": "Chilean pesos (CLP)",
        "fiscal_txt": "RUT tax ID",
        "iva_txt": "19% VAT",
        "vocabulario": (
            "concrete (*hormigón*), skim plaster (*estuco*), suspended ceiling "
            "(*cielo falso*), baseboard (*guardapolvo*) and plumber (*gasfíter*)"
        ),
        "autoridad": "the SII",
        "ciudad": "Santiago",
        "precios": "",
        "nota": "",
    },
    "AR": {
        "nombre": "Argentina",
        "en": "Argentina",
        "moneda_txt": "Argentine pesos (ARS)",
        "fiscal_txt": "CUIT tax ID",
        "iva_txt": "21% VAT",
        "vocabulario": (
            "concrete (*hormigón*), render (*revoque*), ceiling (*cielorraso*), "
            "baseboard (*zócalo*) and plumber (*plomero*)"
        ),
        "autoridad": "AFIP / ARCA",
        "ciudad": "Buenos Aires",
        "precios": "",
        "nota": "",
    },
    "DO": {
        "nombre": "the Dominican Republic",
        "en": "the Dominican Republic",
        "moneda_txt": "DOP",
        "fiscal_txt": "RNC tax ID",
        "iva_txt": "18% ITBIS",
        "vocabulario": (
            "concrete (*hormigón*), plaster (*pañete*), ceiling (*plafón*), "
            "baseboard (*zócalo*) and plumber (*plomero*)"
        ),
        "autoridad": "DGII",
        "ciudad": "Santo Domingo",
        "precios": "",
        "nota": "",
    },
    "UY": {
        "nombre": "Uruguay",
        "en": "Uruguay",
        "moneda_txt": "Uruguayan pesos (UYU)",
        "fiscal_txt": "RUT tax ID",
        "iva_txt": "22% VAT",
        "vocabulario": (
            "concrete (*hormigón*), render (*revoque*), ceiling (*cielorraso*), "
            "baseboard (*zócalo*) and plumbing (*sanitario*)"
        ),
        "autoridad": "the DGI",
        "ciudad": "Montevideo",
        "precios": "",
        "nota": "",
    },
    "PY": {
        "nombre": "Paraguay",
        "en": "Paraguay",
        "moneda_txt": "guaraníes (PYG)",
        "fiscal_txt": "RUC tax ID",
        "iva_txt": "10% VAT",
        "vocabulario": (
            "concrete (*hormigón*), render (*revoque*), ceiling (*cielorraso*), "
            "baseboard (*zócalo*) and plumber (*plomero*)"
        ),
        "autoridad": "the SET",
        "ciudad": "Asunción",
        "precios": "",
        "nota": "",
    },
    "BO": {
        "nombre": "Bolivia",
        "en": "Bolivia",
        "moneda_txt": "bolivianos (BOB)",
        "fiscal_txt": "NIT tax ID",
        "iva_txt": "13% VAT",
        "vocabulario": (
            "concrete (*hormigón*), render (*revoque*), suspended ceiling "
            "(*cielo falso*), baseboard (*zócalo*) and plumber (*plomero*)"
        ),
        "autoridad": "the SIN",
        "ciudad": "Santa Cruz de la Sierra",
        "precios": "",
        "nota": "",
    },
    "PA": {
        "nombre": "Panama",
        "en": "Panama",
        "moneda_txt": "US dollars (USD)",
        "fiscal_txt": "RUC tax ID",
        "iva_txt": "7% ITBMS",
        "vocabulario": (
            "concrete (*concreto*), plaster (*repello*), suspended ceiling "
            "(*cielo raso*), baseboard (*zócalo*) and plumber (*plomero*)"
        ),
        "autoridad": "the DGI",
        "ciudad": "Panama City",
        "precios": "",
        "nota": "",
    },
    "CR": {
        "nombre": "Costa Rica",
        "en": "Costa Rica",
        "moneda_txt": "colones (CRC)",
        "fiscal_txt": "NITE tax ID",
        "iva_txt": "13% VAT",
        "vocabulario": (
            "concrete (*concreto*), plaster (*repello*), suspended ceiling "
            "(*cielo raso*), baseboard (*rodapié*) and plumber (*fontanero*)"
        ),
        "autoridad": "the Treasury (*Hacienda*)",
        "ciudad": "San José",
        "precios": "",
        "nota": "",
    },
    "GT": {
        "nombre": "Guatemala",
        "en": "Guatemala",
        "moneda_txt": "quetzales (GTQ)",
        "fiscal_txt": "NIT tax ID",
        "iva_txt": "12% VAT",
        "vocabulario": (
            "concrete (*concreto*), plaster (*repello*), suspended ceiling "
            "(*cielo falso*), baseboard (*zócalo*) and plumber (*fontanero*)"
        ),
        "autoridad": "the SAT (FEL)",
        "ciudad": "Guatemala City",
        "precios": "",
        "nota": "",
    },
    "HN": {
        "nombre": "Honduras",
        "en": "Honduras",
        "moneda_txt": "lempiras (HNL)",
        "fiscal_txt": "RTN tax ID",
        "iva_txt": "15% ISV",
        "vocabulario": (
            "concrete (*concreto*), plaster (*repello*), suspended ceiling "
            "(*cielo falso*), baseboard (*zócalo*) and plumber (*fontanero*)"
        ),
        "autoridad": "the SAR",
        "ciudad": "Tegucigalpa",
        "precios": "",
        "nota": "",
    },
    "SV": {
        "nombre": "El Salvador",
        "en": "El Salvador",
        "moneda_txt": "US dollars (USD)",
        "fiscal_txt": "NIT tax ID",
        "iva_txt": "13% VAT",
        "vocabulario": (
            "concrete (*concreto*), plaster (*repello*), suspended ceiling "
            "(*cielo falso*), baseboard (*zócalo*) and plumber (*fontanero*)"
        ),
        "autoridad": "the Ministry of Finance (*Hacienda*)",
        "ciudad": "San Salvador",
        "precios": "",
        "nota": "",
    },
    "NI": {
        "nombre": "Nicaragua",
        "en": "Nicaragua",
        "moneda_txt": "córdobas (NIO)",
        "fiscal_txt": "RUC tax ID",
        "iva_txt": "15% VAT",
        "vocabulario": (
            "concrete (*concreto*), plaster (*repello*), suspended ceiling "
            "(*cielo raso*), baseboard (*zócalo*) and plumber (*fontanero*)"
        ),
        "autoridad": "the DGI",
        "ciudad": "Managua",
        "precios": "",
        "nota": "",
    },
}


def _datos(codigo: str) -> dict[str, Any]:
    return _PAISES_EN.get(str(codigo or "").strip().upper()) or _PAISES_EN[""]


# ---------------------------------------------------------------------------
# Landing (home genérica y por país)
# ---------------------------------------------------------------------------

def _faq_landing(codigo: str) -> list[dict[str, str]]:
    d = _datos(codigo)
    nombre = d["nombre"]
    faq: list[dict[str, str]] = []

    if codigo == "":
        faq.append(
            {
                "q": "Does CotizaT work for construction estimates in Spain and Latin America?",
                "a": (
                    "Yes. It is built for small builders, remodelers and contractors in "
                    "Spain, Venezuela, Colombia, Mexico, Ecuador, Peru, Chile, Argentina "
                    "and the rest of the region. Each country ships its own price "
                    "catalog, currency, VAT rate and tax ID (NIF, RIF, NIT, RFC, RUC, "
                    "RUT, CUIT, RTN, NITE) and you pick it when you sign up."
                ),
            }
        )
    elif d["nota"]:
        faq.append(
            {
                "q": f"Can I estimate in hard currency and show the local-currency equivalent?",
                "a": (
                    f"Yes. You work in {d['moneda_txt']} and every estimate locks the "
                    f"reference exchange rate it was priced with, so a PDF you sent last "
                    f"month does not change when the rate moves."
                ),
            }
        )
    else:
        faq.append(
            {
                "q": f"Is CotizaT built for contractors in {nombre}?",
                "a": (
                    f"Yes. Your workspace is created in {d['moneda_txt']}, with the "
                    f"{d['fiscal_txt']} and {d['iva_txt']} applied by default, and the "
                    f"catalog uses the trade terms used on site in {nombre}."
                ),
            }
        )

    faq.append(
        {
            "q": "Does it include unit price analysis?",
            "a": (
                "Yes. Every line item in the catalog comes broken down into materials, "
                "labor and equipment, with productivity rates and unit prices. Change "
                "one resource and every line item that uses it is recalculated."
            ),
        }
    )
    faq.append(
        {
            "q": "Does my client have to create an account?",
            "a": (
                "No. You send the PDF by WhatsApp or email exactly the way you already "
                "work. The private link with online signature is optional."
            ),
        }
    )
    faq.append(
        {
            "q": f"Does it issue {d['autoridad']} tax invoices?",
            "a": (
                "No. CotizaT produces commercial documents: estimates and payment "
                "requests. They are not a substitute for the tax invoice you must issue "
                "through your authorized provider. The PDF and the terms say so."
            ),
        }
    )
    return faq


def landing_en(codigo: str = "") -> dict[str, Any]:
    """Ficha de la landing en inglés (home genérica o de un país)."""
    codigo = str(codigo or "").strip().upper()
    d = _datos(codigo)
    nombre = d["nombre"]

    if codigo:
        title = f"CotizaT: construction estimating software for {nombre}"
        description = (
            f"Construction estimating software for {nombre}: price catalog in "
            f"{d['moneda_txt']}, {d['fiscal_txt']}, {d['iva_txt']}. Unit price "
            f"analysis and PDF."
        )
        h1 = f"Construction estimating software for {nombre}"
        h1_resalte = f"{d['moneda_txt']}, with your margin under control"
        sub = (
            f"Price building work and remodeling in {d['moneda_txt']}, with the "
            f"{d['fiscal_txt']} and {d['iva_txt']} already set. The catalog ships with "
            f"editable unit price analysis and the trade terms used in {nombre}: "
            f"{d['vocabulario']}. You see cost, profit and crew hours before you send a "
            f"PDF with your logo on it."
        )
        kicker = f"Commercial system for {nombre} · Construction and remodeling"
    else:
        title = "CotizaT: construction estimating software"
        description = (
            "Construction estimating and remodeling software for Spain and Latin "
            "America: price catalog per country, VAT and tax ID, unit price "
            "analysis and PDF."
        )
        h1 = "Construction estimating software for Spain and Latin America"
        h1_resalte = "margin, crew time and close"
        sub = (
            "CotizaT turns your catalog and your prices into clear construction "
            "estimates, with internal cost, profit and crew hours. Spain in euros with "
            "NIF and 21% VAT; Latin America with its own currency and tax rules. A PDF "
            "carrying your logo, ready for WhatsApp."
        )
        kicker = "Commercial system for Spain and Latin America · Construction and remodeling"

    return {
        "title": title,
        "description": description,
        "h1": h1,
        "h1_resalte": h1_resalte,
        "sub": sub,
        "kicker": kicker,
        "faq": _faq_landing(codigo),
    }


# ---------------------------------------------------------------------------
# Hubs de intención: software-presupuestos, apu, remodelacion
# ---------------------------------------------------------------------------

def _ruta_en(codigo: str, tema: str = "") -> str:
    """Ruta canónica en inglés: /en/, /en-mx/, /en/apu, /en-mx/apu."""
    codigo = str(codigo or "").strip().upper()
    tema = str(tema or "").strip().strip("/")
    prefijo = f"/en-{codigo.lower()}" if codigo else "/en"
    return f"{prefijo}/{tema}" if tema else f"{prefijo}/"


def tema_en(codigo: str, tema: str) -> dict[str, Any] | None:
    """Bloques de un hub de intención en inglés."""
    codigo = str(codigo or "").strip().upper()
    tema = str(tema or "").strip().lower()
    d = _datos(codigo)
    nombre = d["nombre"]
    ciudad = d["ciudad"] or nombre
    moneda = d["moneda_txt"]
    fiscal = d["fiscal_txt"]
    iva = d["iva_txt"]
    vocab = d["vocabulario"]

    if tema == "software-presupuestos":
        title = f"CotizaT: construction estimating software{' for ' + nombre if codigo else ''}"
        h1 = f"Construction estimating software for {nombre}"
        lead = (
            f"CotizaT is the estimating and remodeling software for small building "
            f"companies in {nombre}. Price catalog with unit price analysis, "
            f"{fiscal}, {iva} and {moneda}. Professional PDF ready for WhatsApp."
        )
        body = [
            (
                "What it fixes",
                f"Most small builders in {nombre} still estimate in Excel or Word. "
                "Prices live in one person's head, the client asks for two changes and "
                "the document has to be rebuilt, and nobody remembers which version was "
                "approved. CotizaT keeps your catalog, builds the estimate by section "
                "and produces a PDF that carries your logo.",
            ),
            (
                "Who it is for",
                f"Remodelers, contractors and building companies of 2 to 15 people in "
                f"{nombre} who send several estimates a month. It is not an ERP for "
                "public works and it is not a BIM viewer. It is the commercial flow: "
                "estimate, check the margin, send, and resend the revision.",
            ),
            (
                "What you get on day one",
                "More than 3,000 broken-down line items and hundreds of priced "
                f"resources. Trade terms of {nombre}: {vocab}. Room packages (bathroom, "
                "kitchen) scaled to the actual square meters. Import from Excel "
                "(.xlsx) and BC3.",
            ),
            (
                "Price",
                "US$89 for the first year at launch price (US$109 afterwards) or "
                "US$9.99 a month for the first year. 7-day full trial, no card, no "
                "commitment.",
            ),
        ]
        description = (
            f"Construction estimating software for {nombre}: unit price analysis, "
            f"{fiscal}, {iva} and professional PDF."
        )
        related = [
            ("Unit price analysis", _ruta_en(codigo, "apu")),
            ("Remodeling estimates", _ruta_en(codigo, "remodelacion")),
        ]
    elif tema == "apu":
        title = f"CotizaT: unit price analysis software{' for ' + nombre if codigo else ''}"
        h1 = f"Unit price analysis for {nombre}"
        lead = (
            f"CotizaT is not a flat price list. Every line item arrives with its unit "
            f"price analysis: materials, labor and equipment, productivity rate and "
            f"unit price, ready to edit in {moneda}."
        )
        body = [
            (
                "What a unit price analysis is here",
                "A unit price analysis breaks the price of a line item down into "
                "resources: kilos of cement, hours of a journeyman, hours of equipment. "
                "Each row is productivity rate times unit price. Complementary direct "
                "costs are computed on top of that base.",
            ),
            (
                f"Why it matters in {nombre}",
                f"Without a unit price analysis you are estimating blind: you do not "
                f"know whether the bathroom in {ciudad} leaves you 30% or 8%. With it "
                "you see internal cost, profit and crew hours before you send. Those "
                "numbers stay out of the PDF your client receives.",
            ),
            (
                "Prices that cascade",
                "Raise the cement price or the journeyman's hourly rate once, in "
                "Resources. Every line item that uses it is recalculated. Estimates "
                "already sent are not touched: each version stays frozen.",
            ),
            (
                "Excel and BC3",
                "If you already work with breakdown matrices in Excel (.xlsx), you "
                "import the file and materials, labor and complementary costs are "
                "classified for you, without losing rows or formulas. You can also "
                "paste TSV from Excel or import .bc3 (FIEBDC-3).",
            ),
        ]
        description = (
            f"Unit price analysis software for {nombre}: editable breakdown, "
            f"productivity rates and cascading prices."
        )
        related = [
            ("Estimating software", _ruta_en(codigo, "software-presupuestos")),
            ("Remodeling estimates", _ruta_en(codigo, "remodelacion")),
        ]
    elif tema == "remodelacion":
        title = f"CotizaT: remodeling estimate software{' for ' + nombre if codigo else ''}"
        h1 = f"Remodeling estimates for {nombre}"
        lead = (
            f"Build the estimate for a bathroom, a kitchen or a whole house in "
            f"{nombre} with room packages, products with photos and a PDF you can "
            f"resend when the client asks for changes."
        )
        body = [
            (
                "The real flow of a remodel",
                "You prepare the estimate, send it by WhatsApp, the client calls and "
                "asks to drop the porcelain tile and use ceramic instead. In CotizaT "
                "you edit, a new version is created and you copy a summary: previous "
                "total, new total and what changed.",
            ),
            (
                "Room packages",
                "A bathroom or a kitchen should not cost you 40 minutes of hunting for "
                "line items. The package inserts the whole section, scaled to the real "
                "square meters. Fixed pieces (toilet, vanity) are not multiplied.",
            ),
            (
                "Options for the client",
                "Products marked as included, optional or alternative, with a photo. "
                "The estimate records what was approved. You do not rewrite the "
                "document from scratch.",
            ),
            (
                f"Taxes in {nombre}",
                f"{fiscal}, {iva}, {moneda}. The documents are commercial: they are not "
                "a tax invoice. We say so in the PDF and in the terms.",
            ),
        ]
        description = (
            f"Remodeling estimating software for {nombre}: room packages, "
            f"professional PDF and clear revisions."
        )
        related = [
            ("Estimating software", _ruta_en(codigo, "software-presupuestos")),
            ("Unit price analysis", _ruta_en(codigo, "apu")),
        ]
    else:
        return None

    faq = [
        {
            "q": f"Does CotizaT work for {nombre}?",
            "a": (
                f"Yes. You pick {nombre} when you sign up and the workspace is created "
                f"with the {fiscal}, {iva} and {moneda}."
            ),
        },
        {
            "q": "Can I try it before paying?",
            "a": "7 days of full access, no card. One trial per email address.",
        },
        {
            "q": "How much is it afterwards?",
            "a": (
                "US$89 for the first year at launch price or US$9.99 a month for the "
                "first year. No commitment."
            ),
        },
    ]
    return {
        "title": title,
        "description": description,
        "h1": h1,
        "lead": lead,
        "body": body,
        "faq": faq,
        "related": related,
    }


# ---------------------------------------------------------------------------
# Páginas públicas que no son landing: copy y schema propios.
# ---------------------------------------------------------------------------

_PAGINAS_ESTATICAS_EN: dict[str, dict[str, Any]] = {
    "como-funciona": {
        "path": "/en/como-funciona",
        "title": "CotizaT: how the construction estimating software works",
        "description": (
            "A walkthrough of CotizaT: catalog with unit price analysis, estimates, "
            "margin, crew time, PDF, WhatsApp, versions, projects and collections."
        ),
        "h1": "How CotizaT works, feature by feature",
        "software": True,
    },
    "contacto": {
        "path": "/en/soporte",
        "title": "CotizaT support: write to us and we answer",
        "description": (
            "CotizaT support form: questions, problems, complaints or suggestions "
            "about the estimating software. Answered by email within one business day."
        ),
        "h1": "Support",
        "software": False,
    },
    "pago": {
        "path": "/en/pago",
        "title": "CotizaT: plans for the construction estimating software",
        "description": (
            "Annual and monthly plans for CotizaT, construction estimating software. "
            "US$89 a year at launch price. 7 days free, no card."
        ),
        "h1": "Plans for the construction estimating software",
        "software": True,
    },
    "mapa-del-sitio": {
        "path": "/en/mapa-del-sitio",
        "title": "CotizaT: site map — construction estimating software",
        "description": (
            "Index of CotizaT public pages: countries, estimating software, unit "
            "price analysis, remodeling and guides."
        ),
        "h1": "Site map",
        "software": False,
    },
    "novedades": {
        "path": "/en/novedades",
        "title": "CotizaT: releases and changelog of the estimating software",
        "description": (
            "CotizaT releases and versions: improvements to the construction "
            "estimating software, performance and new features."
        ),
        "h1": "Releases and versions",
        "software": False,
    },
    "terminos": {
        "path": "/en/legal/terminos",
        "title": "CotizaT: terms of service of the estimating software",
        "description": (
            "CotizaT terms of service. License, data, commercial documents (not a "
            "tax invoice) and cancel any time."
        ),
        "h1": "Terms of service and license",
        "software": False,
    },
    "privacidad": {
        "path": "/en/legal/privacidad",
        "title": "CotizaT: privacy policy of the estimating software",
        "description": (
            "CotizaT privacy policy: which data the estimating software stores, who "
            "processes it and how to export or delete it."
        ),
        "h1": "Privacy policy",
        "software": False,
    },
    "soporte": {
        "path": "/en/legal/soporte",
        "title": "CotizaT: support terms of the estimating software",
        "description": (
            "What CotizaT support includes, what it does not (tax advice, custom "
            "development) and how to report a bug."
        ),
        "h1": "Support terms",
        "software": False,
    },
    "licencias": {
        "path": "/en/legal/licencias",
        "title": "CotizaT: third-party licenses",
        "description": (
            "Third-party software and typefaces used by CotizaT, with their licenses "
            "(SIL OFL, FastAPI and others)."
        ),
        "h1": "Third-party licenses",
        "software": False,
    },
    "preguntas": {
        "path": "/en/legal/preguntas",
        "title": "CotizaT: frequently asked questions about the estimating software",
        "description": (
            "Questions about CotizaT: free trial, catalog and unit price analysis, "
            "PDF, WhatsApp, price, tax invoice and support."
        ),
        "h1": "Frequently asked questions",
        "software": False,
    },
}


def pagina_estatica_en(clave: str) -> dict[str, Any] | None:
    """Ficha en inglés de una página pública que no es landing."""
    datos = _PAGINAS_ESTATICAS_EN.get(str(clave or "").strip())
    if not datos:
        return None
    return {
        "path": datos["path"],
        "title": datos["title"],
        "description": datos["description"],
        "lang": "en",
        "h1": datos["h1"],
        "canonical_path": datos["path"],
        "faq": [],
        "software": datos.get("software", False),
        "nombre_pais": "Latin America",
    }
