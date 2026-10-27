# -*- coding: utf-8 -*-
"""Artículos long-tail de Estados Unidos, Irlanda, Australia y Canadá.

Reino Unido abrió el camino con su módulo (``seo_reino_unido.py``): textos
de mercado con URL propia (``/en-gb/guia/...``) que responden a lo que un
contratista busca de verdad —qué debe llevar el documento, cómo se grava,
qué cuesta la mano de obra— en vez de repetir la landing con otro nombre.

Los otros cuatro mercados anglófonos no tenían ningún artículo: su huella
en Google eran la landing y los tres hubs. Este módulo les da el mismo
tratamiento que tiene Reino Unido, con la ventaja de que ahora sí hay
datos propios que publicar: las cuatro matrices de precios investigadas en
octubre de 2026 (salarios BLS OEWS, SEO irlandés, awards australianos,
medianas del Job Bank canadiense, convertidos a coste empresa por hora
facturable por las herramientas ``tools/coste_empresa_*.py``) y el motor
fiscal por estado de Estados Unidos (``app.services.fiscalidad_eeuu``),
cuya tabla de 51 jurisdicciones se **genera** en este módulo para que el
artículo nunca diga otra cosa que el producto.

Contrato de contenido: cifras = salarios oficiales y coste empresa de la
matriz (verificado por test contra las herramientas); nada de «precios de
mercado típicos» inventados. El salario no es el coste y el coste no es el
precio de venta: los artículos lo explican, que es exactamente la
diferencia que el catálogo con APU hace visible.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Tabla de fiscalidad de Estados Unidos, derivada del motor (fuente única).
# ---------------------------------------------------------------------------

_BASE_TEXTO_EN = {
    "none": "No tax charged to the customer — the contractor pays tax on materials at the store",
    "full": "Tax charged on the full contract price (labor and materials)",
    "gross_receipts": "Tax on the contractor's gross receipts from the job",
    "materials": "Tax charged on materials sold with the job",
    "labor": "Tax charged on labor (services)",
}


def _tabla_estados_eeuu() -> dict[str, Any]:
    """Tabla pública de las 51 jurisdicciones, generada desde el motor.

    Se construye al importar el módulo para que el artículo nunca se
    desincronice de ``fiscalidad_eeuu.ESTADOS_EEUU``: si un estudio futuro
    cambia el criterio de un estado, la guía cambia con el producto.
    """
    from .services.fiscalidad_eeuu import ESTADOS_EEUU

    filas: list[list[str]] = []
    for estado in ESTADOS_EEUU:
        nota = str(estado.nota or "").strip()
        if nota:
            # Solo la primera frase: la tabla es un mapa, no un tratado.
            nota = nota.split(". ")[0].rstrip(".") + "."
            if len(nota) > 180:
                nota = nota[:177].rsplit(" ", 1)[0] + "…"
        filas.append(
            [
                f"{estado.nombre} ({estado.codigo})",
                _BASE_TEXTO_EN.get(estado.base_defecto, estado.base_defecto),
                f"{estado.nombre_impuesto} · {estado.tipo_medio}%",
                nota or "—",
            ]
        )
    return {
        "cabecera": [
            "State",
            "Default treatment of a residential remodel",
            "Tax and average combined rate",
            "Watch out for",
        ],
        "filas": filas,
        "nota": (
            "Rates are each state's average combined state + local rate "
            "(Tax Foundation, mid-2026), published as a starting point to "
            "adjust to the job address — not as the exact rate of any "
            "county or city. Researched October 2026; general information, "
            "not tax advice."
        ),
    }


def _tabla_mano_obra(
    cabecera_salario: str,
    filas: list[tuple[str, str, str]],
    nota: str,
) -> dict[str, Any]:
    """Tabla oficio/salario/coste empresa con la forma que pinta la guía."""
    return {
        "cabecera": ["Trade", cabecera_salario, "Employer cost per billable hour"],
        "filas": [list(f) for f in filas],
        "nota": nota,
    }


# ---------------------------------------------------------------------------
# Artículos
# ---------------------------------------------------------------------------

ARTICULOS: dict[str, dict[str, Any]] = {
    # ── Estados Unidos ───────────────────────────────────────────────────
    "construction-estimate-template": {
        "slug": "construction-estimate-template",
        "pais": "US",
        "pais_nombre": "the United States",
        "pais_path": "/en-us/",
        "kicker": "United States · Estimates",
        "title": "What a US construction estimate must include (template & checklist)",
        "h1": "What a construction estimate must include in the United States",
        "description": (
            "A complete US construction estimate template: license details, sectioned scope, "
            "allowances, sales tax by state, payment schedule, retainage and change-order terms. "
            "Includes a checklist for contractors, remodelers and general contractors in all 51 jurisdictions."
        ),
        "lead": (
            "A homeowner compares three estimates and signs one. The document that "
            "wins is rarely the cheapest: it is the one that makes the scope, the "
            "numbers and the rules of the job unambiguous. This is what an estimate "
            "has to carry in the United States, section by section."
        ),
        "secciones": [
            (
                "1. Your business details — and your license number",
                [
                    "Company name, address, phone and email, your EIN, and your state "
                    "contractor license number. Most states require the license number "
                    "on contracts and advertising, and a general contractor asking you "
                    "to bid wants it on the paper from the first page. If your state "
                    "does not license your trade, your registration or local license "
                    "goes in the same place.",
                    "Insurance belongs in this block too: general liability and "
                    "workers' compensation, with certificates available on request. A "
                    "property manager will not read further than a missing workers' "
                    "comp line.",
                ],
            ),
            (
                "2. Scope of work, written as sections",
                [
                    "The scope is the part that protects you. Written as sections —"
                    "demolition, framing, rough plumbing, rough electrical, finishes— "
                    "it lets the client see what they are buying and lets you see "
                    "where the money is. One paragraph saying 'remodel bathroom' "
                    "guarantees an argument about what was included.",
                    "Contractors pricing for general contractors usually map those "
                    "sections to CSI MasterFormat divisions (concrete, masonry, "
                    "thermal and moisture protection, finishes, mechanical, "
                    "electrical). For a homeowner the division numbers do not matter; "
                    "the order does: it reads the way the job will actually run.",
                ],
            ),
            (
                "3. The basis of the price: fixed, unit price or time and materials",
                [
                    "Say it explicitly. A fixed (lump sum) price for a defined scope, "
                    "unit prices per square foot, linear foot or cubic yard for "
                    "measured work, or time and materials with a not-to-exceed cap if "
                    "the job cannot be measured yet. Mixing the three without "
                    "labelling them is how an estimate becomes a dispute.",
                    "Where a finish has not been chosen, price it as an allowance —a "
                    "stated budget for tile, fixtures or cabinets— and say what "
                    "happens when the client picks above it. Allowances are a normal "
                    "part of US residential estimating; hiding one inside a fixed "
                    "total is not.",
                ],
            ),
            (
                "4. The tax treatment — which depends on the state of the job",
                [
                    "There is no national rule. In most states a contractor improving "
                    "real property is the final consumer of the materials: tax is "
                    "paid at the supply house, labor is not taxed, and the estimate "
                    "correctly carries no tax line. Washington charges sales tax on "
                    "the full contract price; Hawaii, New Mexico and South Dakota tax "
                    "the contractor's gross receipts; others split by kind of job. A "
                    "separate guide on this site lists the default treatment of all "
                    "51 jurisdictions.",
                    "Whatever your state does, the estimate should show its working: "
                    "which treatment was applied, on what base, at what rate. A tax "
                    "line that just says 'sales tax 8 %' on a job that should not be "
                    "taxed at all is the most common estimating error in the country.",
                ],
            ),
            (
                "5. Payment schedule, deposit and retainage",
                [
                    "Deposits are regulated in several states for home improvement: "
                    "California, for example, caps the down payment at the lesser of "
                    "$1,000 or 10 % of the contract price. State the deposit, the "
                    "progress payments tied to completed stages (not calendar dates), "
                    "and the final payment on completion.",
                    "On commercial work expect retainage —commonly 5 to 10 % held "
                    "until substantial completion— and lien waivers exchanged at each "
                    "payment. The estimate is where you say whether your price "
                    "assumes them.",
                ],
            ),
            (
                "6. Exclusions, assumptions, validity and change orders",
                [
                    "List what is not in the price: permits, dumpsters, temporary "
                    "facilities, work by others, concealed conditions. State how "
                    "long the price stays open —30 days is typical— and that work "
                    "beyond the scope is done only on a written change order priced "
                    "before it starts.",
                    "This block looks defensive but it is what a professional client "
                    "reads first: it tells them you have been through a job before.",
                ],
            ),
        ],
        "faq": [
            {
                "q": "What is the difference between an estimate, a quote and a bid?",
                "a": (
                    "An estimate is your calculated cost of the work; a quote (or "
                    "proposal) is the priced offer you send the client; a bid is a "
                    "fixed offer against someone else's specification, usually in "
                    "competition. The document should say which one it is, because "
                    "only accepted offers become contracts."
                ),
            },
            {
                "q": "Does my license number have to be on the estimate?",
                "a": (
                    "In most licensed states, yes on contracts and usually on any "
                    "document offered to a consumer. Rules are state-level: check "
                    "your licensing board. Putting it there costs nothing and "
                    "removes the first doubt a client has."
                ),
            },
            {
                "q": "Should a US estimate show sales tax?",
                "a": (
                    "Only where the job's state charges it to the customer — in most "
                    "states a real-property remodel carries no tax line at all. Our "
                    "guide to sales tax on construction by state lists the default "
                    "for all 51 jurisdictions and the cases that change it."
                ),
            },
            {
                "q": "How long should an estimate stay valid?",
                "a": (
                    "30 days is the residential norm; material-heavy work is "
                    "sometimes priced for 15. What matters is that the date is "
                    "printed and that the document says prices are rechecked after it."
                ),
            },
        ],
        "related": [
            ("Sales tax on construction by state", "/en-us/guia/sales-tax-on-construction-by-state"),
            ("Construction labor cost per hour (2026)", "/en-us/guia/construction-labor-cost-per-hour"),
        ],
    },
    "sales-tax-on-construction-by-state": {
        "slug": "sales-tax-on-construction-by-state",
        "pais": "US",
        "pais_nombre": "the United States",
        "pais_path": "/en-us/",
        "kicker": "United States · Sales tax",
        "title": "Sales tax on US construction: the default treatment for all 51 states and DC",
        "h1": "Do contractors charge sales tax? Construction tax in all 51 jurisdictions",
        "description": (
            "Most US states never charge sales tax on a remodel invoice. The default treatment, "
            "average rate and exceptions for all 50 states plus DC: no tax, full tax, materials only, "
            "gross receipts (Hawaii GET, New Mexico GRT) and Washington's full-contract tax."
        ),
        "lead": (
            "The short answer most software gets wrong: in the majority of states "
            "a contractor does not charge the customer any sales tax on a remodel "
            "of real property. The contractor is the consumer of the materials, "
            "pays tax at the store, and labor on real property is not a taxable "
            "service. The exceptions are specific, and they are listed here state "
            "by state."
        ),
        "secciones": [
            (
                "The five ways a state can tax your job",
                [
                    "Every state lands in one of five buckets for a typical "
                    "residential remodel. (1) No tax charged to the customer: tax is "
                    "paid on materials at purchase and disappears into your price. "
                    "(2) Tax on the materials you resell or invoice separately. (3) "
                    "Tax on labor —services are taxable in that state. (4) Tax on "
                    "the full contract price. (5) A gross-receipts-style tax on the "
                    "contractor (Hawaii's GET, New Mexico's GRT, South Dakota's "
                    "contractor's excise tax), sometimes on only a fraction of the "
                    "price (Arizona prime contracting taxes 65 %).",
                    "Two of the buckets surprise people. Services are taxable by "
                    "default in only four states (Hawaii, New Mexico, South Dakota, "
                    "West Virginia), and Washington is the one state that treats "
                    "retailing construction as a retail sale of the whole contract.",
                ],
            ),
            (
                "The default for a residential remodel, state by state",
                [
                    "These are the defaults CotizaT proposes when you pick the job "
                    "state, classified for the job our users send most: a remodel or "
                    "improvement of residential real property for the owner. Where a "
                    "state changes the answer with the kind of work, the 'watch out "
                    "for' column says so — a capital improvement in New York is not "
                    "a repair, a Texas home is not a Texas storefront, Arizona draws "
                    "the line between MRRA maintenance work and prime contracting.",
                    {"tabla": _tabla_estados_eeuu()},
                    "Your usual state lives on the company; every estimate can "
                    "override it, and the PDF shows the treatment, the base and the "
                    "rate that were applied. CotizaT proposes and shows its working "
                    "— it does not file your sales tax return.",
                ],
            ),
            (
                "Where the default flips: repairs, commercial work and separated contracts",
                [
                    "Three fact patterns move a job out of its state's default. "
                    "Repair and maintenance of real property is a taxable service in "
                    "a second set of states (for example New Jersey and North "
                    "Carolina tax repair, maintenance and installation services), "
                    "even where an improvement is not. Commercial work flips "
                    "others: Kansas taxes labor on commercial remodels but exempts "
                    "residential work and original construction. And in states like "
                    "Colorado, Indiana or Texas, a separated or time-and-materials "
                    "contract turns you into a retailer of the materials — taxable "
                    "on that part, where a lump-sum contract would not be.",
                    "The practical rule: re-ask the question whenever the client is "
                    "a business, the job is a repair rather than an improvement, or "
                    "the contract separates materials from labor. Those three facts "
                    "decide more cases than the rate does.",
                ],
            ),
            (
                "Keep the receipts: how the contractor-as-consumer states police it",
                [
                    "In no-tax-line states the audit trail runs through your "
                    "purchases: you owe use tax on anything you bought tax-free and "
                    "installed. That is why the estimate's internal cost side "
                    "matters — materials priced with the tax you actually paid keep "
                    "your margin honest and your file defensible. It is also why a "
                    "state average rate printed on a customer invoice in one of "
                    "these states is doubly wrong: it charges the client a tax "
                    "nobody owes, at a rate tied to no address.",
                ],
            ),
        ],
        "faq": [
            {
                "q": "Do contractors charge sales tax to customers?",
                "a": (
                    "In most states, no — on real-property construction the "
                    "contractor is the consumer of the materials and labor is not "
                    "taxed. Washington charges the full contract price; Hawaii, New "
                    "Mexico and South Dakota tax the contractor's gross receipts; a "
                    "handful of states change the answer for repairs, commercial "
                    "work or separated contracts."
                ),
            },
            {
                "q": "Is construction labor taxable?",
                "a": (
                    "Only in a minority of states. Services are taxable by default "
                    "in Hawaii, New Mexico, South Dakota and West Virginia; others "
                    "tax specific services (repair and maintenance in New Jersey or "
                    "North Carolina, commercial remodel labor in Kansas)."
                ),
            },
            {
                "q": "Why does the table show an average rate instead of the exact one?",
                "a": (
                    "US sales tax is set by state, county, city and special "
                    "districts — the exact rate belongs to the job address. The "
                    "combined average is the honest starting point to adjust before "
                    "sending, which is what the app asks you to do."
                ),
            },
            {
                "q": "What rate do I use in Alaska?",
                "a": (
                    "Alaska has no state sales tax, but many municipalities levy "
                    "their own. The table stores 0 % as the default: set your local "
                    "rate on the estimate if your borough or city taxes the work."
                ),
            },
        ],
        "related": [
            ("What a US construction estimate must include", "/en-us/guia/construction-estimate-template"),
            ("Construction labor cost per hour (2026)", "/en-us/guia/construction-labor-cost-per-hour"),
        ],
    },
    "construction-labor-cost-per-hour": {
        "slug": "construction-labor-cost-per-hour",
        "pais": "US",
        "pais_nombre": "the United States",
        "pais_path": "/en-us/",
        "kicker": "United States · Labor costs",
        "title": "US construction labor cost per hour (2026): BLS wages vs. employer cost",
        "h1": "Construction labor cost per hour in 2026: wage vs. what an hour really costs you",
        "description": (
            "BLS median wages by trade (carpenter $39.07, electrician $39.76, plumber $40.21, laborer $30.68) "
            "loaded with FICA, FUTA, SUTA, workers' comp and overhead into true employer cost per billable hour. "
            "Includes the formula to convert a wage into a billable rate for estimates."
        ),
        "lead": (
            "Ask what an hour of labor costs and you get three different numbers: "
            "the wage, what that hour costs your company, and what you charge for "
            "it. Estimates fail when the first is used where the second belongs. "
            "These are the 2026 wage benchmarks behind our US price library, next "
            "to the employer cost each one produces."
        ),
        "secciones": [
            (
                "Wages by trade, and the employer cost they turn into",
                [
                    "The wage column is the national median from the Bureau of "
                    "Labor Statistics (OEWS program). The employer cost is what the "
                    "library carries: that wage loaded with the employer side of "
                    "FICA (7.65 %), federal and state unemployment insurance, "
                    "workers' compensation, paid time away from the tools and the "
                    "non-billable hours every crew has — then spread over the hours "
                    "you can actually charge for.",
                    {
                        "tabla": _tabla_mano_obra(
                            "BLS median wage",
                            [
                                ("Plumber", "$30.67/h", "$40.21/h"),
                                ("Electrician", "$30.38/h", "$39.76/h"),
                                ("Brick/block mason", "$29.87/h", "$39.78/h"),
                                ("HVAC mechanic/installer", "$29.33/h", "$38.50/h"),
                                ("Journeyman carpenter", "$29.12/h", "$39.07/h"),
                                ("Drywall installer and taper", "$28.74/h", "$38.00/h"),
                                ("Tile and stone setter", "$26.77/h", "$35.31/h"),
                                ("Painter", "$23.75/h", "$31.44/h"),
                                ("Construction laborer", "$22.66/h", "$30.68/h"),
                            ],
                            "Employer costs researched October 2026 from BLS OEWS "
                            "medians; each library entry also keeps a low–high "
                            "range (roughly −15 %/+35 % around the cost shown). "
                            "Cost only: your charge-out rate adds overhead and "
                            "margin on top.",
                        )
                    },
                    "Read it as a floor, not a price: an hour billed at the "
                    "employer cost returns nothing for vehicles, insurance, "
                    "supervision or profit. The catalog applies your own margin per "
                    "line item so you can see the gap before you send.",
                ],
            ),
            (
                "The burden, line by line",
                [
                    "On a median wage the unavoidable add-ons are: 7.65 % FICA; "
                    "federal unemployment (0.6 % net on the first $7,000); state "
                    "unemployment (varies, on a low wage base); workers' "
                    "compensation —the swing item, cheap for a painter, expensive "
                    "for a roofer or ironworker—; paid holidays, vacation and sick "
                    "days; and the gap between paid hours and hours that land on a "
                    "job. Add small tools, consumables and supervision spread over "
                    "the crew and a wage grows by roughly a quarter to a third "
                    "before it is a cost you can estimate with.",
                    "That multiplier is also why two contractors in the same town "
                    "price the same bathroom $4,000 apart: one of them is "
                    "estimating with wages and finding the difference at the end of "
                    "the job.",
                ],
            ),
            (
                "Regional and union reality",
                [
                    "A national median is a reference, not a local fact: BLS "
                    "publishes the same occupations by state and metro area, and "
                    "coastal metros sit well above these figures while much of the "
                    "Southeast and Midwest sits below. Union scale and prevailing-"
                    "wage work (Davis-Bacon on federal jobs and its state versions) "
                    "run on their own published packages —wage plus fringe— which "
                    "you should enter as your own rates for that work. The library "
                    "treats every figure as a starting point: your rates replace "
                    "them per resource and stay yours.",
                ],
            ),
        ],
        "faq": [
            {
                "q": "What is labor burden?",
                "a": (
                    "Everything an hour of work costs beyond the wage: payroll "
                    "taxes, unemployment insurance, workers' compensation, paid "
                    "time off and non-billable hours. In this library it turns a "
                    "median wage into the employer cost per billable hour, which "
                    "is the number an estimate should start from."
                ),
            },
            {
                "q": "What should I charge per hour if a journeyman costs me $39?",
                "a": (
                    "Cost is not price. Add your overhead recovery (vehicles, "
                    "insurance, office, supervision) and your margin — the catalog "
                    "applies the margin you set on top of the employer cost, line "
                    "by line, so the number you send is built rather than guessed."
                ),
            },
            {
                "q": "Do these rates apply in my state?",
                "a": (
                    "They are national medians: use them as the reference and "
                    "adjust to your market or your crew's actual wages. The library "
                    "keeps a low–high range around each rate precisely because a "
                    "Texas framer and a Boston framer do not cost the same."
                ),
            },
        ],
        "related": [
            ("What a US construction estimate must include", "/en-us/guia/construction-estimate-template"),
            ("Sales tax on construction by state", "/en-us/guia/sales-tax-on-construction-by-state"),
        ],
    },
    # ── Irlanda ──────────────────────────────────────────────────────────
    "builders-quote-template-ireland": {
        "slug": "builders-quote-template-ireland",
        "pais": "IE",
        "pais_nombre": "Ireland",
        "pais_path": "/en-ie/",
        "kicker": "Ireland · Quotations",
        "title": "What an Irish builder's quote must include (VAT 13.5 %, RCT, terms)",
        "h1": "What a builder's quote must include in Ireland (VAT 13.5 %, RCT and terms)",
        "description": (
            "An Irish builder's quote must carry scope sections, price basis, VAT treatment (13.5 % standard, 23 % two-thirds rule), "
            "RCT retention, exclusions, exclusions, and validity. Includes a checklist for contractors, remodelers and general contractors."
        ),
        "lead": (
            "An Irish homeowner compares three quotes and signs one. The document "
            "that wins is rarely the cheapest: it is the one whose scope and terms "
            "cannot be misunderstood — and, in Ireland, whose VAT is right. This "
            "is what the quote has to carry."
        ),
        "secciones": [
            (
                "1. Your details, and the numbers Revenue expects",
                [
                    "Trading name, address, phone and email, plus your VAT number "
                    "if you are registered. If you also work as a subcontractor, a "
                    "principal contractor will want your tax reference and your RCT "
                    "rate (0 %, 20 % or 35 %), because that decides what they "
                    "deduct before paying you. Your insurance —public liability "
                    "and employer's liability— belongs in this block too.",
                ],
            ),
            (
                "2. Scope of works, in sections, with preliminaries named",
                [
                    "Write the scope as sections —strip-out, structural, first fix, "
                    "second fix, finishes— rather than one paragraph. That is what "
                    "lets the client see what they are buying and what lets you "
                    "price a variation later without reopening the whole job. "
                    "Preliminaries (site setup, skips, scaffold, protection, "
                    "waste) go in as their own lines: on Irish domestic work they "
                    "are often what decides whether the job makes money.",
                ],
            ),
            (
                "3. The basis of the price: fixed, measured or daywork",
                [
                    "Say which it is. Fixed for a defined scope; a rate per square "
                    "metre for measured work; daywork for opening-up work nobody "
                    "can measure yet. Where something is genuinely unknown —what "
                    "is under a floor, behind a wall— carry a provisional sum and "
                    "say what it covers and how it will be adjusted. Provisional "
                    "sums are normal in Irish estimating; hiding one inside a "
                    "fixed total is not.",
                ],
            ),
            (
                "4. The VAT statement — 13.5 %, unless the two-thirds rule bites",
                [
                    "Construction services in Ireland are charged at the reduced "
                    "13.5 % rate, but if the materials in the job come to more "
                    "than two thirds of the VAT-exclusive price, the whole amount "
                    "is standard-rated at 23 %. The quote has to say which rate "
                    "was applied and show the VAT clearly — a separate guide on "
                    "this site works the rule with numbers. For a homeowner, "
                    "quote the VAT-inclusive total with the rate stated; for a "
                    "business client, show net and VAT lines.",
                ],
            ),
            (
                "5. The labour/materials split, because RCT needs it",
                [
                    "RCT is deducted from the labour element of a payment, not "
                    "from materials. A quote that shows only one total forces a "
                    "principal contractor to come back and ask for the split — or "
                    "to deduct on more than they should. Pricing your document "
                    "from a cost breakdown (each line item knows its labour, "
                    "materials and plant) means the split is already there when "
                    "they ask, and the VAT two-thirds test can be checked from "
                    "the same numbers.",
                ],
            ),
            (
                "6. Exclusions, validity and how you get paid",
                [
                    "List what is excluded (planning and certification fees, "
                    "utility connections, client-supplied items), how long the "
                    "price stays open —30 days is typical— and the payment "
                    "schedule by stage. On business-to-business work the "
                    "Construction Contracts Act 2013 gives you a statutory "
                    "payment-claim rhythm; on domestic work the schedule you "
                    "print is the one you will argue from, so print it.",
                ],
            ),
        ],
        "faq": [
            {
                "q": "Should an Irish quote show prices with or without VAT?",
                "a": (
                    "For a homeowner, lead with the VAT-inclusive total and state "
                    "the rate applied (usually 13.5 % for construction services). "
                    "For a VAT-registered business, show the net amount and the "
                    "VAT line separately."
                ),
            },
            {
                "q": "When is building work charged at 23 % VAT in Ireland?",
                "a": (
                    "When the materials supplied in the job exceed two thirds of "
                    "the VAT-exclusive price — then the whole job is standard-"
                    "rated at 23 %. Goods-only supplies are also 23 %. Our "
                    "guide to VAT on construction in Ireland works an example."
                ),
            },
            {
                "q": "Is a builder's quote legally binding in Ireland?",
                "a": (
                    "A quote becomes binding when accepted and forming a "
                    "contract; an estimate is not a fixed offer. Say which one "
                    "the document is and how long it stays open. General "
                    "information, not legal advice."
                ),
            },
            {
                "q": "What is RCT and why does my quote need a labour split?",
                "a": (
                    "Relevant Contracts Tax is deducted by principal contractors "
                    "from payments to subcontractors at 0 %, 20 % or 35 %, on the "
                    "labour element only — so the split has to be visible in your "
                    "pricing for the deduction to be right."
                ),
            },
        ],
        "related": [
            ("VAT on construction in Ireland and the two-thirds rule", "/en-ie/guia/vat-on-construction-ireland"),
            ("Builder and trades rates in Ireland (2026)", "/en-ie/guia/builder-rates-ireland"),
        ],
    },
    "vat-on-construction-ireland": {
        "slug": "vat-on-construction-ireland",
        "pais": "IE",
        "pais_nombre": "Ireland",
        "pais_path": "/en-ie/",
        "kicker": "Ireland · VAT and RCT",
        "title": "VAT on Irish construction: 13.5 %, the two-thirds rule and RCT (2026)",
        "h1": "VAT on construction in Ireland: the 13.5 % rate, the two-thirds rule and RCT",
        "description": (
            "Irish construction VAT is 13.5 % — unless materials exceed two-thirds of the price, making the whole job 23 %. "
            "Includes the RCT retention, the two-thirds rule explained with examples, and how to configure VAT in estimates."
        ),
        "lead": (
            "Ireland taxes construction services at a reduced 13.5 % VAT — with a "
            "trap. If the value of the materials in the job exceeds two thirds of "
            "the VAT-exclusive price, Revenue treats the supply as one of goods "
            "and the entire amount is taxed at 23 %. It is the single most "
            "expensive VAT mistake an Irish builder can make on a quote."
        ),
        "secciones": [
            (
                "The rule, with numbers",
                [
                    "Take a bathroom refit quoted at €12,000 (VAT-exclusive): "
                    "labour and plant €4,600, materials and sanitary ware €7,400. "
                    "Materials are 61.7 % of the total — under two thirds — so "
                    "the job is a construction service at 13.5 %: €1,620 of VAT, "
                    "€13,620 to the client. Now the client upgrades the suite and "
                    "tiling so materials reach €8,300 of a €12,300 job: 67.5 %. "
                    "The whole contract flips to 23 %, and the VAT becomes "
                    "€2,829. If your quote promised a VAT-inclusive total at "
                    "13.5 %, the €1,200 difference comes out of your margin.",
                    "You cannot test the rule on a one-line quote. It needs the "
                    "materials share of the job, which means the estimate has to "
                    "be built from a cost breakdown where every line item knows "
                    "its labour, its materials and its plant. That is how CotizaT "
                    "checks the two-thirds test for Irish estimates: from the "
                    "budget's own numbers, before the VAT line is printed.",
                ],
            ),
            (
                "What counts as materials, and what stays at 13.5 %",
                [
                    "The test compares the value of goods supplied under the "
                    "contract against the total VAT-exclusive consideration. "
                    "Supply-only sales —a boiler sold over the counter, goods "
                    "with no installation— are standard-rated at 23 % regardless. "
                    "Construction services proper (building, alteration, repair, "
                    "installation work by a contractor) start at 13.5 % and stay "
                    "there while materials remain at or under two thirds. Where a "
                    "job is likely to hover near the line, price the variants: "
                    "what the upgrade does to the rate is part of the price of "
                    "the upgrade, and it belongs in front of the client before "
                    "they choose.",
                ],
            ),
            (
                "RCT: the deduction taken before you are paid",
                [
                    "Under Relevant Contracts Tax a principal contractor notifies "
                    "each payment to a subcontractor and deducts at the "
                    "subcontractor's rate —0 %, 20 % or 35 % depending on their "
                    "compliance record— from the labour element of the payment. "
                    "The deduction is a payment on account, credited against the "
                    "subcontractor's own tax. Two things follow for estimating: "
                    "your paperwork has to separate labour from materials from "
                    "the first quote (the same split the VAT test needs), and if "
                    "you work as a principal, the RCT you deduct never touches "
                    "your price — it is the subcontractor's money passing "
                    "through.",
                ],
            ),
            (
                "The reverse charge between contractors",
                [
                    "Where a subcontractor supplies construction services to a "
                    "principal contractor who is themselves in the chain, the VAT "
                    "reverse charge applies: the subcontractor does not charge "
                    "VAT and the principal self-accounts. A quote or invoice in "
                    "that chain should say so on its face, because a VAT line "
                    "charged where the reverse charge applies is an error both "
                    "sides have to unwind. To the final customer —the homeowner "
                    "or the business that will own the work— the normal 13.5 % / "
                    "23 % logic above is what appears on the document.",
                ],
            ),
        ],
        "faq": [
            {
                "q": "What is the VAT rate on building work in Ireland?",
                "a": (
                    "13.5 % for construction services. If materials exceed two "
                    "thirds of the VAT-exclusive price, the whole job becomes "
                    "23 %. Supply-only goods are 23 %."
                ),
            },
            {
                "q": "How does the two-thirds rule work exactly?",
                "a": (
                    "Compare the value of goods in the contract with the total "
                    "price excluding VAT. Over two thirds in goods → treated as "
                    "a supply of goods, 23 % on everything. At or under → a "
                    "construction service at 13.5 %."
                ),
            },
            {
                "q": "What are the RCT deduction rates?",
                "a": (
                    "0 %, 20 % or 35 %, set by Revenue from the subcontractor's "
                    "compliance history, and deducted from the labour element of "
                    "each payment notified by the principal contractor."
                ),
            },
            {
                "q": "Do I charge VAT when subcontracting to another builder?",
                "a": (
                    "Between contractors in the chain the VAT reverse charge "
                    "usually applies: you invoice without VAT and the principal "
                    "self-accounts. Check the status of both parties before "
                    "invoicing — general information, not tax advice."
                ),
            },
        ],
        "related": [
            ("What a builder's quote must include in Ireland", "/en-ie/guia/builders-quote-template-ireland"),
            ("Builder and trades rates in Ireland (2026)", "/en-ie/guia/builder-rates-ireland"),
        ],
    },
    "builder-rates-ireland": {
        "slug": "builder-rates-ireland",
        "pais": "IE",
        "pais_nombre": "Ireland",
        "pais_path": "/en-ie/",
        "kicker": "Ireland · Labour costs",
        "title": "Irish builder and trades rates (2026): SEO wages vs. true employer cost",
        "h1": "Builder and trades rates in Ireland 2026: the SEO wage vs. the true hourly cost",
        "description": (
            "Statutory SEO craft wage (€23.74/h) and Connect/AECI mechanical/electrical rates, loaded with PRSI, pension, "
            "leave and non-billable time into true employer cost per billable hour. A craft rate costs €32.67 — before overhead and margin."
        ),
        "lead": (
            "Ireland is the one market where construction wages are set in law: "
            "the Sectoral Employment Order fixes the craft and operative grades, "
            "and the mechanical and electrical trades run on their own "
            "Connect/AECI scales. Those wages are the floor — this page shows "
            "what they become once employer PRSI, pension and non-billable hours "
            "are counted."
        ),
        "secciones": [
            (
                "Statutory wages by trade, and the cost of an hour on site",
                [
                    "The wage column is the statutory or scale rate. The employer "
                    "cost is the figure our Irish price library carries: the wage "
                    "loaded with employer PRSI (11.25 %), the CWPS pension and "
                    "sick-pay contributions, holiday and public-holiday pay, and "
                    "the hours in the year that are paid but not worked on a "
                    "client's job — divided over the billable hours that remain.",
                    {
                        "tabla": _tabla_mano_obra(
                            "SEO / scale wage",
                            [
                                ("Craftsperson — general builder, bricklayer, carpenter & joiner, tiler, painter (SEO craft grade)", "€23.74/h", "€32.67/h"),
                                ("Plumber / pipefitter (Connect mechanical, 3rd year)", "€29.12/h", "€39.62/h"),
                                ("HVAC and refrigeration engineer (Connect mechanical)", "€29.12/h", "€39.62/h"),
                                ("Electrician (AECI, 3rd year)", "€27.60/h", "€37.66/h"),
                                ("Skilled general operative, steel fixer (SEO category A)", "€23.03/h", "€31.75/h"),
                                ("General operative / labourer (SEO category B)", "€21.37/h", "€29.60/h"),
                            ],
                            "Rates as researched October 2026. Cost only: what you "
                            "charge a client adds your margin on top — and market "
                            "day rates, especially around Dublin, are a selling "
                            "price, not a cost.",
                        )
                    },
                ],
            ),
            (
                "Why the €350 day rate you hear is not a contradiction",
                [
                    "Divide the numbers above into a day and you get roughly "
                    "€260–€315 of employer cost for a craftsperson — below the "
                    "day rates commonly quoted to homeowners. There is no "
                    "inconsistency: the day rate is a price. It has to recover "
                    "the employer cost plus vans, tools, insurance, supervision, "
                    "the gap days between jobs and profit — and then VAT at "
                    "13.5 % goes on the customer's document. Estimating from the "
                    "wage alone (€23.74 × 8 ≈ €190 a day) is how a job that "
                    "'looked fine on day rates' loses money.",
                    "Our library keeps the employer cost as the base and applies "
                    "the margin you set per line item, so the comparison is "
                    "visible inside every estimate rather than discovered at "
                    "the end of the job.",
                ],
            ),
            (
                "Apprentices, new entrants and keeping your own rates",
                [
                    "The SEO also sets apprentice percentages of the craft rate "
                    "by year, and new-entrant operative rates below category B "
                    "for the first two years. A crew estimate that prices every "
                    "pair of hands at the craft rate overstates cost; one that "
                    "prices apprentices as craftsmen to the client has a "
                    "different problem. The library's grades map one-to-one "
                    "onto the statutory ones so a crew can be built the way you "
                    "actually staff it — and every rate stays editable, because "
                    "what you must pay and what you do pay to keep good people "
                    "are rarely the same number.",
                ],
            ),
        ],
        "faq": [
            {
                "q": "What is a builder's hourly rate in Ireland?",
                "a": (
                    "The statutory SEO craft wage is €23.74/h, which becomes "
                    "about €32.67/h of employer cost per billable hour once "
                    "PRSI, pension and paid non-working time are counted. What a "
                    "client is charged adds overheads and margin on top."
                ),
            },
            {
                "q": "What is the SEO in Irish construction?",
                "a": (
                    "The Sectoral Employment Order: a legally binding floor for "
                    "pay and conditions in construction, set by grade "
                    "(craftsperson, category A and B operatives, apprentices, "
                    "new entrants) and updated periodically."
                ),
            },
            {
                "q": "Why are plumbers and electricians on different scales?",
                "a": (
                    "The mechanical trades negotiate through Connect, the "
                    "electrical trade through AECI, with their own graded "
                    "scales by years qualified — both above the general craft "
                    "rate, which is why an electrician's hour costs more than "
                    "a blocklayer's in the library."
                ),
            },
        ],
        "related": [
            ("VAT on construction in Ireland and the two-thirds rule", "/en-ie/guia/vat-on-construction-ireland"),
            ("What a builder's quote must include in Ireland", "/en-ie/guia/builders-quote-template-ireland"),
        ],
    },
    # ── Australia ────────────────────────────────────────────────────────
    "building-quote-template-australia": {
        "slug": "building-quote-template-australia",
        "pais": "AU",
        "pais_nombre": "Australia",
        "pais_path": "/en-au/",
        "kicker": "Australia · Quotes",
        "title": "What an Australian building quote must include (ABN, licence, GST)",
        "h1": "What a building quote must include in Australia (ABN, licence, GST)",
        "description": (
            "An Australian building quote must include ABN, state licence number, GST-inclusive price for consumers, "
            "scope sections (demolition, framing, finishes), exclusions, validity period and payment terms. Checklist included."
        ),
        "lead": (
            "An Aussie homeowner gets three quotes and picks one — and the state "
            "gets a say in what those quotes must look like. Licence numbers, "
            "GST-inclusive pricing to consumers and written-contract thresholds "
            "are law, not style. This is what belongs on the document."
        ),
        "secciones": [
            (
                "1. Business details: ABN and licence number first",
                [
                    "Business name, ABN, contact details — and your builder or "
                    "trade licence number. In most states the licence number "
                    "must appear on advertising and quotes, and for work above "
                    "your state's threshold you cannot legally contract without "
                    "it. A quote without an ABN also flags a bigger problem "
                    "discussed below: the person paying you may have to withhold "
                    "47 % (see our GST guide).",
                ],
            ),
            (
                "2. The price: GST-inclusive for consumers, always one clear total",
                [
                    "Australian Consumer Law requires a single, all-in price to "
                    "consumers: the total a homeowner sees must already include "
                    "GST. You can show the ex-GST amount and the GST component "
                    "as information, but the headline figure is the one they "
                    "pay. To another business you may quote ex-GST — say so on "
                    "the page. A quote that is silent on GST is read as "
                    "GST-inclusive, and the 10 % then comes out of your side of "
                    "the deal.",
                ],
            ),
            (
                "3. Inclusions and exclusions, in plain English",
                [
                    "Scope written as sections with materials named (brand, "
                    "grade, finish), then an explicit exclusions list: council "
                    "and certifier fees, asbestos, rock excavation, temporary "
                    "services, client-supplied items. Provisional sums and prime "
                    "cost items are normal in Australian contracts — label them, "
                    "state the allowance, and say how the difference is handled "
                    "when the client chooses above it.",
                ],
            ),
            (
                "4. Contract thresholds and deposits: where the states step in",
                [
                    "Every state sets a value above which residential building "
                    "work needs a written contract with statutory content — in "
                    "NSW a written contract is required over $5,000 and home "
                    "building compensation cover over $20,000; Victoria requires "
                    "a domestic building contract over $10,000. Deposits are "
                    "capped too (commonly 5–10 % depending on state and value). "
                    "The quote does not replace that contract, and saying 'a "
                    "written contract will follow on acceptance for work over "
                    "$X' protects both sides.",
                ],
            ),
            (
                "5. Expiry, variations and how progress payments run",
                [
                    "State how long the quote stays open (30 days is typical), "
                    "that variations are priced and agreed in writing before "
                    "the work is done, and the progress payment stages tied to "
                    "completed work. State security-of-payment legislation "
                    "gives those progress claims statutory force in "
                    "commercial work; on domestic work the schedule you print "
                    "is the rhythm you will be paid to.",
                ],
            ),
        ],
        "faq": [
            {
                "q": "Does a building quote in Australia have to include GST?",
                "a": (
                    "For consumers, the price shown must be the full "
                    "GST-inclusive amount. To businesses you can quote ex-GST "
                    "if you say so clearly. Silence is read as GST-inclusive."
                ),
            },
            {
                "q": "Do I need my licence number on a quote?",
                "a": (
                    "In most states yes, if you are quoting work that needs a "
                    "licence — it is generally required on advertising and "
                    "quotes. Thresholds and which trades are licensed vary by "
                    "state."
                ),
            },
            {
                "q": "When does a quote need to become a written contract?",
                "a": (
                    "Above your state's threshold for residential building work "
                    "(for example over $5,000 in NSW, over $10,000 in Victoria). "
                    "The statutory contract then governs deposits, progress "
                    "payments and warranties."
                ),
            },
            {
                "q": "How long should a quote be valid for?",
                "a": (
                    "30 days is the common default; shorter on material-heavy "
                    "work. Print the expiry date — an open-ended quote is an "
                    "open-ended material price."
                ),
            },
        ],
        "related": [
            ("GST on building work in Australia", "/en-au/guia/gst-on-building-work-australia"),
            ("Tradie hourly rates in Australia (2026)", "/en-au/guia/tradie-hourly-rates-australia"),
        ],
    },
    "gst-on-building-work-australia": {
        "slug": "gst-on-building-work-australia",
        "pais": "AU",
        "pais_nombre": "Australia",
        "pais_path": "/en-au/",
        "kicker": "Australia · GST",
        "title": "GST on Australian building work: registration, quoting & 47 % withholding (2026)",
        "h1": "GST on building work in Australia: registration, quoting and the 47 % no-ABN withholding",
        "description": (
            "10 % GST on building services, $75,000 registration threshold, GST-inclusive consumer quotes (Australian Consumer Law), "
            "ex-GST business quotes, and the 47 % no-ABN withholding. Includes a calculator for estimates."
        ),
        "lead": (
            "GST on building work is simpler than most countries' systems — one "
            "rate, 10 %, on the whole supply of building services. What catches "
            "tradies out is everything around the rate: when you must register, "
            "how the price has to be presented to a homeowner, and what happens "
            "when an ABN is missing from the paperwork."
        ),
        "secciones": [
            (
                "Registering: the $75,000 line",
                [
                    "You must register for GST when your business turnover "
                    "reaches $75,000 a year (and you may register voluntarily "
                    "below it, which matters in construction: most of your "
                    "inputs carry GST you can only claim back if registered). "
                    "Once registered you charge 10 % on your building services, "
                    "claim credits on materials and subbies, and report through "
                    "your BAS. If you are not registered you cannot charge GST "
                    "— your quote simply shows one price with no GST line, and "
                    "it must not be presented as a tax invoice.",
                ],
            ),
            (
                "Quoting with GST: who sees which number",
                [
                    "To a homeowner, Australian Consumer Law's single-price "
                    "rule means the total shown includes GST — you may break "
                    "out the GST component underneath, but the headline is what "
                    "they pay. To another business, ex-GST quoting with "
                    "'+ GST' stated is standard. The expensive failure mode is "
                    "silence: a price that says nothing about GST is treated as "
                    "GST-inclusive, and on a $110,000 renovation that reading "
                    "hands the ATO $10,000 of your margin. In CotizaT the "
                    "estimate is built ex-GST and the document prints the "
                    "treatment you set — the point is that it prints it.",
                ],
            ),
            (
                "The no-ABN withholding: 47 % before you see a cent",
                [
                    "If a business pays you for work and you have not quoted an "
                    "ABN (and no exemption applies), the payer must withhold "
                    "47 % and send it to the ATO. It is credited against your "
                    "tax later, but as cash flow it is brutal — and it is "
                    " triggered by paperwork, not by wrongdoing. ABN on the "
                    "quote, ABN on the invoice, every time.",
                ],
            ),
            (
                "Progress claims, retentions and what GST follows",
                [
                    "GST generally follows the invoice or payment (depending "
                    "on whether you account on a cash or accruals basis), "
                    "including on progress claims — each claim is a supply "
                    "with its own GST. Retentions held back by a head "
                    "contractor raise their own timing question, which your "
                    "accounting basis answers; what the estimate side must do "
                    "is keep each claim's ex-GST value, GST and any retention "
                    "visible so the claim, the tax invoice and the contract "
                    "sum reconcile. (Selling a new home you built is a "
                    "different GST animal — including the margin scheme — and "
                    "sits outside quoting work for a client.)",
                ],
            ),
        ],
        "faq": [
            {
                "q": "What GST rate applies to building work in Australia?",
                "a": (
                    "10 % on the supply of building services — labour and the "
                    "materials supplied with them — charged by businesses "
                    "registered for GST (mandatory from $75,000 turnover)."
                ),
            },
            {
                "q": "Should my quote include GST?",
                "a": (
                    "Quotes to consumers must show the total GST-inclusive "
                    "price. Business quotes can be ex-GST if clearly stated. "
                    "If the document is silent, the price is treated as "
                    "including GST."
                ),
            },
            {
                "q": "What happens if I don't put an ABN on an invoice?",
                "a": (
                    "A business payer must generally withhold 47 % and remit "
                    "it to the ATO (no-ABN withholding). You get credit for it "
                    "in your return, but not until then."
                ),
            },
            {
                "q": "I'm under $75,000 — should I register for GST anyway?",
                "a": (
                    "Many builders do, because materials and subcontractors "
                    "charge you GST you can only claim back when registered. "
                    "It is a cash-flow and pricing decision — general "
                    "information here, not tax advice."
                ),
            },
        ],
        "related": [
            ("What a building quote must include in Australia", "/en-au/guia/building-quote-template-australia"),
            ("Tradie hourly rates in Australia (2026)", "/en-au/guia/tradie-hourly-rates-australia"),
        ],
    },
    "tradie-hourly-rates-australia": {
        "slug": "tradie-hourly-rates-australia",
        "pais": "AU",
        "pais_nombre": "Australia",
        "pais_path": "/en-au/",
        "kicker": "Australia · Labour costs",
        "title": "Tradie hourly rates in Australia (2026): award rates vs. true employer cost",
        "h1": "Tradie hourly rates in Australia 2026: award pay vs. what an hour really costs",
        "description": (
            "Australian award hourly rates (CW3 $31.22/h, plumber $31.63, electrician $31.13) loaded with 12 % super, "
            "portable long service leave, workers' comp and non-billable time into true employer cost per billable hour. "
            "Includes the formula to convert an award rate into a billable rate."
        ),
        "lead": (
            "Australia sets construction pay by award: the Building and "
            "Construction General On-site Award (MA000020), the Electrical "
            "Award (MA000025) and the Plumbing Award (MA000036). Those ordinary "
            "hourly rates are the legal minimum a tradesperson costs you before "
            "super, portable long service leave, workers comp and the hours "
            "nobody can bill. Both numbers follow."
        ),
        "secciones": [
            (
                "Award ordinary rates by trade, and the cost of a billable hour",
                [
                    "The rate column is the award ordinary hourly rate "
                    "(including the industry/tool allowances where they apply "
                    "to that classification). The employer cost is the number "
                    "our Australian price library carries: that rate loaded "
                    "with the 12 % superannuation guarantee, portable long "
                    "service leave, workers compensation, annual and personal "
                    "leave, public holidays and RDOs — divided over the hours "
                    "actually worked on clients' jobs.",
                    {
                        "tabla": _tabla_mano_obra(
                            "Award ordinary rate",
                            [
                                ("Fit-out carpenter / carpenter and joiner (CW3 + tool allowance)", "A$32.30/h", "A$49.59/h"),
                                ("Bricklayer (CW3 + tool allowance)", "A$31.99/h", "A$49.15/h"),
                                ("Plumber (tradesperson level 1)", "A$31.63/h", "A$48.65/h"),
                                ("Painter (CW3 + tool allowance)", "A$31.48/h", "A$48.43/h"),
                                ("General tradesperson (CW3)", "A$31.22/h", "A$48.06/h"),
                                ("Electrician (grade 5)", "A$31.13/h", "A$47.94/h"),
                                ("Steel fixer / skilled worker (CW2)", "A$30.39/h", "A$46.89/h"),
                                ("Construction labourer (CW1(d))", "A$29.82/h", "A$46.10/h"),
                            ],
                            "Award rates as researched October 2026 (Fair Work "
                            "Ombudsman instruments). Employer cost is cost only "
                            "— your charge-out rate adds overheads, margin and "
                            "then GST for the client document.",
                        )
                    },
                    "Note what the table quietly shows: because an hour costed "
                    "is an hour on the tools, and a year holds roughly 1,600 "
                    "of those against ~1,980 paid hours, even a modest award "
                    "rate becomes a A$46–50 cost before a single overhead is "
                    "recovered.",
                ],
            ),
            (
                "The award is a floor — and the market knows it",
                [
                    "Nobody has to tell a builder in Sydney or Brisbane that "
                    "good trades charge well above award. Enterprise "
                    "agreements on commercial sites lift the wage floor "
                    "substantially, and subcontractor charge-out rates bundle "
                    "the whole burden plus profit into one number. The "
                    "library's job is not to guess your market rate: it is to "
                    "make sure that when you type your real rate over the "
                    "award-based one, the estimate is still built from cost "
                    "upwards — and that while you use the defaults, you are "
                    "never unknowingly pricing below the legal cost of the "
                    "crew.",
                ],
            ),
            (
                "From cost to charge-out without guessing",
                [
                    "The arithmetic every estimate should show: employer cost "
                    "per billable hour → plus overhead recovery (vehicles, "
                    "insurance, supervision, the quoting hours that never "
                    "convert) → plus margin → equals charge-out; GST then "
                    "applies on the client document. Run that forward from "
                    "A$48–50 and the quote rates you see in the market stop "
                    "looking mysterious — and run it from the raw award "
                    "A$31–32 and you can see exactly where a too-cheap "
                    "competitor's job is heading. CotizaT applies your margin "
                    "per line item on top of this cost base so the gap is "
                    "visible while you can still fix it.",
                ],
            ),
        ],
        "faq": [
            {
                "q": "What is a tradie's hourly rate in Australia?",
                "a": (
                    "The award ordinary rate for a qualified tradesperson "
                    "sits around A$31–32/h depending on trade and "
                    "allowances, which becomes roughly A$48–50/h of employer "
                    "cost per billable hour with 12 % super and leave counted. "
                    "Charge-out rates add overheads and margin on top."
                ),
            },
            {
                "q": "Which award covers builders and tradies?",
                "a": (
                    "Construction generally: the Building and Construction "
                    "General On-site Award 2020 (MA000020). Electricians: "
                    "MA000025. Plumbers: MA000036. Classifications (CW1–CW8 "
                    "and trade levels) set the minimum ordinary rate."
                ),
            },
            {
                "q": "Why does the cost jump so much from the award rate?",
                "a": (
                    "Super at 12 %, portable long service leave, workers "
                    "compensation, four weeks' annual leave, personal leave, "
                    "public holidays and RDOs are all paid time that produces "
                    "no billable hour. Spread over the hours on the tools, "
                    "the rate grows by roughly half."
                ),
            },
        ],
        "related": [
            ("GST on building work in Australia", "/en-au/guia/gst-on-building-work-australia"),
            ("What a building quote must include in Australia", "/en-au/guia/building-quote-template-australia"),
        ],
    },
    # ── Canadá ───────────────────────────────────────────────────────────
    "contractor-estimate-template-canada": {
        "slug": "contractor-estimate-template-canada",
        "pais": "CA",
        "pais_nombre": "Canada",
        "pais_path": "/en-ca/",
        "kicker": "Canada · Estimates",
        "title": "What a Canadian contractor estimate must include (GST/HST, holdback, permits)",
        "h1": "What a contractor estimate must include in Canada (GST/HST number, holdback, permits)",
        "description": (
            "A Canadian contractor estimate needs GST/HST number, provincial tax treatment (5 % GST, 13 % HST Ontario, 15 % HST Atlantic), "
            "scope sections, exclusions, deposit, holdback (10 % common), permits, and validity period. Includes a checklist."
        ),
        "lead": (
            "A Canadian homeowner signs the estimate that reads like it was "
            "written by someone who has finished jobs in their province — "
            "because in Canada the details that differ are provincial: the "
            "tax, the holdback, the consumer-protection rules. This is what "
            "belongs on the document."
        ),
        "secciones": [
            (
                "1. Business details, Business Number and GST/HST number",
                [
                    "Legal business name, address and contact details, your "
                    "Business Number (BN) and your GST/HST registration number "
                    "— the same number that must appear on your receipts and "
                    "invoices so a business client can claim input tax "
                    "credits. Add your provincial trade licence or municipal "
                    "licence where your trade requires one, and note your "
                    "WSIB (or provincial equivalent) clearance status: on "
                    "commercial work you will be asked for the certificate, "
                    "and the estimate is where saying you have it costs "
                    "nothing.",
                ],
            ),
            (
                "2. Scope in sections — and who handles the permits",
                [
                    "Write the scope as staged sections (demolition, framing, "
                    "rough-ins, finishes) with quantities and unit prices "
                    "where the work is measurable. Then a line Canadian "
                    "homeowners always ask about: permits. Say which permits "
                    "the job needs, whether your price includes applying for "
                    "and paying for them, and whose name they go under. "
                    "'Permits extra' discovered after signing is a dispute "
                    "scheduled in advance.",
                ],
            ),
            (
                "3. The tax line: GST, HST or GST + provincial tax — by province",
                [
                    "Canada has no single construction tax: HST at 13 % in "
                    "Ontario and 15 % (14 % in Nova Scotia since April 2025) "
                    "in Atlantic Canada, GST 5 % alone in Alberta and the "
                    "territories, GST plus a provincial tax in BC, "
                    "Saskatchewan, Manitoba and Quebec. A separate guide on "
                    "this site tabulates all ten provinces. On the estimate, "
                    "name the tax(es) and rate(s) applied; for a consumer, "
                    "show the total they will actually pay.",
                ],
            ),
            (
                "4. Deposit, progress draws and the statutory holdback",
                [
                    "State the deposit (modest on domestic work — provincial "
                    "consumer law and plain trust both favour small deposits "
                    "and payment for work done), the progress draws tied to "
                    "stages, and the holdback. On work caught by provincial "
                    "lien legislation the payer must retain a basic holdback —"
                    "10 % in Ontario and several other provinces— until the "
                    "lien period runs; if you are pricing as a subcontractor, "
                    "that 10 % is a cash-flow fact your margin has to survive, "
                    "and the estimate is where you acknowledge it.",
                ],
            ),
            (
                "5. Exclusions, allowances, validity and change orders",
                [
                    "Unchosen finishes go in as stated allowances; "
                    "concealed conditions (knob-and-tube, asbestos, rot) as "
                    "explicit exclusions with a unit-price mechanism if you "
                    "can offer one. Print the validity (30 days is typical) "
                    "and that changes are priced in a written change order "
                    "before the work is done. In provinces whose consumer "
                    "protection law caps how far a final price may exceed an "
                    "estimate, that paperwork discipline is also what keeps "
                    "you legal.",
                ],
            ),
        ],
        "faq": [
            {
                "q": "Does a Canadian estimate have to show GST/HST?",
                "a": (
                    "Your GST/HST registration number must appear on "
                    "receipts and invoices, and the tax treatment should be "
                    "plain on the estimate itself — which taxes, at which "
                    "provincial rate, and the total payable for a consumer "
                    "client."
                ),
            },
            {
                "q": "What is the holdback in Canadian construction?",
                "a": (
                    "Under provincial lien statutes the payer retains a "
                    "percentage of each payment — 10 % in Ontario and several "
                    "other provinces — until the lien rights of everyone "
                    "down the chain expire. It protects suppliers and "
                    "subcontractors; price your cash flow around it."
                ),
            },
            {
                "q": "Can the final price exceed the estimate in Canada?",
                "a": (
                    "Some provinces cap overruns on consumer agreements "
                    "unless the consumer agrees to the change (Ontario's "
                    "Consumer Protection Act is the well-known example). "
                    "Written change orders are how you stay inside the rules "
                    "— general information, not legal advice."
                ),
            },
            {
                "q": "When must I register for GST/HST?",
                "a": (
                    "At $30,000 of taxable revenue over four consecutive "
                    "calendar quarters (the small-supplier threshold). Below "
                    "it you may still register voluntarily to recover input "
                    "tax credits."
                ),
            },
        ],
        "related": [
            ("GST/HST on construction, province by province", "/en-ca/guia/gst-hst-on-construction-canada"),
            ("Construction labour rates in Canada (2026)", "/en-ca/guia/construction-labour-rates-canada"),
        ],
    },
    "gst-hst-on-construction-canada": {
        "slug": "gst-hst-on-construction-canada",
        "pais": "CA",
        "pais_nombre": "Canada",
        "pais_path": "/en-ca/",
        "kicker": "Canada · GST/HST",
        "title": "GST/HST on Canadian construction by province (2026): what contractors charge",
        "h1": "GST/HST on construction in Canada: the provincial table (2026)",
        "description": (
            "Federal GST (5 %) plus provincial HST or PST for all provinces: Ontario 13 % HST, Nova Scotia 15 % HST, Alberta 5 % GST, "
            "British Columbia 5 % GST + 7 % PST, Quebec 5 % GST + 9.975 % QST. Includes the place-of-supply rule for real property."
        ),
        "lead": (
            "Ask what tax to put on a Canadian construction estimate and the "
            "honest answer is a table, not a number: the federal GST is 5 %, "
            "but five provinces harmonized it into a single HST, four run a "
            "second provincial tax, and the rate that applies to real property "
            "is the one where the property sits — not where your office is."
        ),
        "secciones": [
            (
                "The table: what you charge on construction services, by province",
                [
                    "Construction and renovation services supplied to a client "
                    "are taxable supplies. A GST/HST registrant (registration "
                    "is required past $30,000 of taxable revenue over four "
                    "quarters) charges at the combined rate of the province of "
                    "the property:",
                    {
                        "tabla": {
                            "cabecera": ["Province", "Tax on construction services", "Combined rate"],
                            "filas": [
                                ["Ontario", "HST", "13 %"],
                                ["New Brunswick, Newfoundland and Labrador, Prince Edward Island", "HST", "15 %"],
                                ["Nova Scotia", "HST (reduced 1 April 2025)", "14 %"],
                                ["British Columbia", "GST 5 % on services; PST 7 % generally borne on materials as a cost", "5 % charged *"],
                                ["Saskatchewan", "GST + PST, both charged on real-property services", "11 %"],
                                ["Manitoba", "GST + RST (retail sales tax) on construction contracts under provincial rules", "12 %"],
                                ["Quebec", "GST + QST (9.975 %)", "14.975 %"],
                                ["Alberta, Yukon, Northwest Territories, Nunavut", "GST only", "5 %"],
                            ],
                            "nota": (
                                "* British Columbia is the classic trap: the "
                                "contractor pays 7 % PST on materials as an "
                                "end-use cost (it cannot be recovered like "
                                "GST) and charges only GST on the contract — "
                                "the PST belongs inside your material prices. "
                                "Saskatchewan and Manitoba each have their "
                                "own base rules for real-property contracts; "
                                "rates as researched October 2026."
                            ),
                        }
                    },
                    "In CotizaT an estimate carries one applied rate and the "
                    "tax label you configure (GST, HST 13 %, GST + QST…), "
                    "printed on the document — because for a fixed property "
                    "there is exactly one right answer and it should be "
                    "visible rather than assumed.",
                ],
            ),
            (
                "Place of supply: the property's province wins",
                [
                    "For services in respect of real property, the place of "
                    "supply is where the property is located. An Ontario "
                    "contractor renovating a cottage in Quebec charges "
                    "GST + QST (with QST registration considerations), and the "
                    "same contractor working in Alberta charges 5 %. If your "
                    "work crosses a border, the estimate has to be built in "
                    "the destination province's terms from the first line.",
                ],
            ),
            (
                "Renovation vs. new housing — the line that changes everything",
                [
                    "Charging GST/HST on your renovation services is the "
                    "simple case. Two neighbouring rules catch builders out. "
                    "First, the sale of a new or substantially renovated home "
                    "by a builder is itself taxable on the full selling "
                    "price (with the New Housing Rebate softening some of "
                    "it) — so a 'renovation' extensive enough to count as "
                    "substantial can move the tax from your invoices onto the "
                    "property's value. Second, self-supply rules can deem a "
                    "builder to have sold a new residential property to "
                    "themselves at fair market value when they first occupy "
                    "or rent it. Neither is an estimating question; both are "
                    "reasons the tax treatment belongs in writing between "
                    "you and your accountant before a major job is priced.",
                ],
            ),
        ],
        "faq": [
            {
                "q": "Do contractors charge GST/HST on labour in Canada?",
                "a": (
                    "Yes — construction services are taxable supplies, so a "
                    "registrant charges GST/HST on the full contract "
                    "(labour and materials together) at the rate of the "
                    "province where the property sits."
                ),
            },
            {
                "q": "What is the HST rate for construction in Ontario?",
                "a": "13 %. Atlantic Canada is 15 % (14 % in Nova Scotia since 1 April 2025).",
            },
            {
                "q": "Which province's rate applies if I work across a border?",
                "a": (
                    "The province where the real property is located — the "
                    "place of supply for real-property services follows the "
                    "property, not your business address."
                ),
            },
            {
                "q": "When must a contractor register for GST/HST?",
                "a": (
                    "After passing $30,000 of taxable revenue in any four "
                    "consecutive calendar quarters. Voluntary registration "
                    "below that lets you claim input tax credits on "
                    "materials."
                ),
            },
        ],
        "related": [
            ("What a Canadian contractor estimate must include", "/en-ca/guia/contractor-estimate-template-canada"),
            ("Construction labour rates in Canada (2026)", "/en-ca/guia/construction-labour-rates-canada"),
        ],
    },
    "construction-labour-rates-canada": {
        "slug": "construction-labour-rates-canada",
        "pais": "CA",
        "pais_nombre": "Canada",
        "pais_path": "/en-ca/",
        "kicker": "Canada · Labour costs",
        "title": "Canadian construction labour rates (2026): Job Bank wages vs. employer cost",
        "h1": "Construction labour rates in Canada 2026: Job Bank wages vs. true employer cost",
        "description": (
            "Government of Canada Job Bank median wages by trade (bricklayer $38.00/h, electrician $34.00, plumber $32.50) loaded with CPP, EI, WSIB, "
            "vacation pay and overhead into true employer cost per billable hour. Includes the formula to convert a wage into a billable rate."
        ),
        "lead": (
            "Canada publishes its construction wages: the federal Job Bank "
            "maintains low, median and high hourly wages by occupation and "
            "region from official surveys. Those medians are what a worker "
            "earns — this page puts beside them what an hour costs the "
            "company that employs them, which is the number an estimate "
            "should be built on."
        ),
        "secciones": [
            (
                "Median wages by trade, and the cost of an hour of work",
                [
                    "The wage column is the Job Bank median (Ontario — the "
                    "largest provincial market, and the reference our "
                    "Canadian library is built on). The employer cost loads "
                    "that wage with the employer side of CPP and EI, "
                    "provincial workplace-insurance premiums (WSIB in "
                    "Ontario, whose construction classes are among the most "
                    "expensive), statutory holidays, vacation pay and the "
                    "paid hours that never reach a client's job.",
                    {
                        "tabla": _tabla_mano_obra(
                            "Job Bank median wage (Ontario)",
                            [
                                ("Bricklayer", "C$38.00/h", "C$49.96/h"),
                                ("HVAC / refrigeration mechanic", "C$37.00/h", "C$47.90/h"),
                                ("Drywall installer and finisher", "C$35.48/h", "C$46.32/h"),
                                ("Construction electrician", "C$34.00/h", "C$44.30/h"),
                                ("Journeyperson plumber", "C$32.50/h", "C$42.47/h"),
                                ("Journeyman carpenter", "C$32.00/h", "C$42.09/h"),
                                ("Construction labourer", "C$27.00/h", "C$35.84/h"),
                                ("Painter and decorator", "C$25.00/h", "C$33.33/h"),
                            ],
                            "Wages: Government of Canada Job Bank medians "
                            "(Ontario), as researched October 2026; the "
                            "library keeps a low–high range around each "
                            "figure. Employer cost only — your contract "
                            "price adds overhead recovery and margin, and "
                            "GST/HST on top for the client.",
                        )
                    },
                ],
            ),
            (
                "Union packages and regional reality",
                [
                    "Two honest caveats. First, ICI (industrial-commercial-"
                    "institutional) union agreements publish 'total packages' "
                    "—wage plus pension, benefits and funds— that run well "
                    "above these medians in markets like the GTA; if your "
                    "crew works under one, your own package replaces the "
                    "median in the library and the estimate follows. Second, "
                    "the Job Bank itself publishes every region separately: "
                    "Alberta energy-corridor trades and Lower Mainland "
                    "carpenters do not live on the Ontario median. The "
                    "medians exist so your starting point is a government "
                    "survey rather than a guess, and every rate stays "
                    "editable by crew and by region.",
                ],
            ),
            (
                "From wage to estimate without losing the burden",
                [
                    "The estimating failure this table exists to prevent is "
                    "pricing labour at the wage. Between the median and the "
                    "billable hour sit CPP and EI employer contributions, "
                    "WSIB premiums that vary by class and claim history, 4 % "
                    "(or 6 %) vacation pay, nine-plus statutory holidays "
                    "depending on province, and supervision — roughly a "
                    "quarter to a third again before margin. CotizaT's "
                    "Canadian library carries labour at that employer cost "
                    "and applies your margin per line item, so the figure "
                    "you defend to a client is built, not improvised.",
                ],
            ),
        ],
        "faq": [
            {
                "q": "What do construction trades earn per hour in Canada?",
                "a": (
                    "Job Bank medians for Ontario run from about C$25/h "
                    "(painter) to C$38/h (bricklayer), with electricians "
                    "around C$34 and plumbers C$32.50. Employer cost per "
                    "billable hour lands roughly a quarter to a third above "
                    "the wage."
                ),
            },
            {
                "q": "What is the Job Bank wage data?",
                "a": (
                    "The Government of Canada's official wage reference: low, "
                    "median and high hourly wages by occupation and economic "
                    "region, built from Statistics Canada survey data and "
                    "updated annually."
                ),
            },
            {
                "q": "Why is WSIB such a big part of the burden?",
                "a": (
                    "Workplace-insurance premiums are priced by industry "
                    "class and risk, and several construction classes carry "
                    "among the highest rates in Ontario. It is usually the "
                    "largest single employer add-on after CPP/EI."
                ),
            },
        ],
        "related": [
            ("GST/HST on construction, province by province", "/en-ca/guia/gst-hst-on-construction-canada"),
            ("What a Canadian contractor estimate must include", "/en-ca/guia/contractor-estimate-template-canada"),
        ],
    },
}

ORDEN_ARTICULOS: tuple[str, ...] = (
    "construction-estimate-template",
    "sales-tax-on-construction-by-state",
    "construction-labor-cost-per-hour",
    "builders-quote-template-ireland",
    "vat-on-construction-ireland",
    "builder-rates-ireland",
    "building-quote-template-australia",
    "gst-on-building-work-australia",
    "tradie-hourly-rates-australia",
    "contractor-estimate-template-canada",
    "gst-hst-on-construction-canada",
    "construction-labour-rates-canada",
)

MERCADOS_CON_GUIAS = ("US", "IE", "AU", "CA")


def articulo(slug: str) -> dict[str, Any] | None:
    return ARTICULOS.get(str(slug or "").strip())


def guias_de(codigo: str) -> list[dict[str, Any]]:
    """Artículos de un mercado, en el orden editorial declarado."""
    codigo = str(codigo or "").strip().upper()
    return [
        ARTICULOS[s]
        for s in ORDEN_ARTICULOS
        if ARTICULOS[s].get("pais") == codigo
    ]


def ruta_articulo(codigo: str, slug: str) -> str:
    return f"/en-{str(codigo or '').strip().lower()}/guia/{slug}"


# ---------------------------------------------------------------------------
# Cuerpo extra y FAQ de los hubs de intención (mismo papel que HUB_EXTRA y
# HUB_FAQ de seo_reino_unido para GB): sin ellos los hubs de los cuatro
# mercados eran el texto genérico con el nombre del país cambiado (~570
# palabras frente a ~900 en GB).
# ---------------------------------------------------------------------------

HUB_EXTRA: dict[tuple[str, str], list[tuple[str, str]]] = {
    ("US", "software-presupuestos"): [
        (
            "Priced from a US library, not a conversion",
            "The catalog ships with a US price library researched in October 2026 "
            "in the units the market sells —cubic yards of ready-mix, 94-lb "
            "cement bags, 4×8 sheets, gallons of paint— with labor at employer "
            "cost per billable hour built from BLS median wages (a plumber whose "
            "wage is $30.67 costs your company $40.21). Every entry keeps its "
            "source and a low–high range, and you work in feet, square feet and "
            "gallons from takeoff to the client PDF.",
        ),
        (
            "Sales tax decided by the job state, not a generic percentage",
            "Pick the state of the job and CotizaT proposes how that state taxes "
            "a remodel —no tax line at all in most states, materials or labour "
            "only in a few, the full price in Washington, gross receipts in "
            "Hawaii, New Mexico and South Dakota— with the state's average "
            "combined rate as the starting point you adjust to the address. The "
            "PDF shows the treatment it applied.",
        ),
    ],
    ("US", "remodelacion"): [
        (
            "Built for how US remodels actually get paid",
            "Room packages (bathroom, kitchen) scale from your dimensions in "
            "square feet, allowances stay labelled as allowances, and the "
            "document carries the deposit and progress-payment schedule your "
            "state allows —with retainage and change-order wording where the "
            "job needs it. The estimate you send is the internal cost build-up "
            "plus your margin, never a number copied out of a flat price list.",
        ),
    ],
    ("US", "apu"): [
        (
            "Unit prices a general contractor can audit",
            "Each line item breaks into materials, labor at employer cost "
            "(burden included) and equipment, at a productivity rate you can "
            "change. That is the breakdown behind a defensible per-square-foot "
            "drywall rate or a per-linear-foot pipe rate — and it is also how "
            "the app splits materials from labour when a state's tax treatment "
            "needs the split.",
        ),
    ],
    ("IE", "software-presupuestos"): [
        (
            "Irish prices, from the statutory scales up",
            "The catalog ships with an Irish price library researched in October "
            "2026: labour from the SEO craft and operative grades and the "
            "Connect/AECI scales, loaded to employer cost per billable hour "
            "(the €23.74 craft wage becomes €32.67), materials quoted ex-VAT "
            "from Irish trade merchants with a source and a range on every line.",
        ),
        (
            "The 13.5 % / 23 % test, checked before you send",
            "Construction services are 13.5 % VAT unless the materials in the "
            "job pass two thirds of the ex-VAT price — then the whole amount "
            "is 23 %. The estimate knows its own materials share, so the app "
            "checks the two-thirds rule from your numbers and prints the "
            "treatment applied. The same breakdown gives you the "
            "labour/materials split RCT deductions need.",
        ),
    ],
    ("IE", "remodelacion"): [
        (
            "Stage payments and provisional sums, written down",
            "Renovation quotes carry sectioned scope with preliminaries as "
            "their own lines, provisional sums for opening-up work labelled "
            "instead of buried, and a stage-payment schedule — the document "
            "that stands up when a homeowner compares you with two others.",
        ),
    ],
    ("IE", "apu"): [
        (
            "Cost breakdowns that answer Revenue's questions",
            "Every line item knows its labour, materials and plant. That one "
            "discipline feeds three Irish obligations at once: your margin per "
            "item, the VAT two-thirds test on the job total, and the labour "
            "element a principal contractor needs for RCT.",
        ),
    ],
    ("AU", "software-presupuestos"): [
        (
            "Award-based costing, GST handled on the page",
            "The Australian library is built from the Building (MA000020), "
            "Electrical (MA000025) and Plumbing (MA000036) award ordinary "
            "rates, loaded with 12 % super, portable long service leave and "
            "workers comp to an employer cost per billable hour — a A$32.30 "
            "carpenter costs A$49.59 before your margin. Estimates are built "
            "ex-GST; the document prints the GST-inclusive total a homeowner "
            "needs and the GST component under it.",
        ),
        (
            "Quotes that carry what the states require",
            "ABN and licence number on the document, inclusions and exclusions "
            "in plain English, a printed expiry and progress stages — the "
            "quote a written contract can follow for work above your state's "
            "threshold, in the same numbers.",
        ),
    ],
    ("AU", "remodelacion"): [
        (
            "Renovation quotes from room packages",
            "Bathroom and kitchen packages scale to the measured metres, "
            "provisional sums and prime cost items stay labelled, and "
            "variations get priced as written revisions — so the version the "
            "client approved is the version you build from.",
        ),
    ],
    ("AU", "apu"): [
        (
            "See the margin before the quote goes out",
            "Each item is materials, award-based labour at employer cost and "
            "plant, at a productivity rate you control. It is the difference "
            "between knowing a bathroom leaves you 18 % and finding out at "
            "handover that it left you 4 %.",
        ),
    ],
    ("CA", "software-presupuestos"): [
        (
            "Job Bank wages, turned into estimating costs",
            "The Canadian library builds labour from Government of Canada Job "
            "Bank median wages (a C$34 construction electrician becomes "
            "C$44.30 of employer cost per billable hour with CPP, EI and "
            "workplace-insurance premiums counted), with materials priced "
            "from Canadian trade sources — each entry dated, sourced and "
            "kept with its range.",
        ),
        (
            "The right tax for the property's province",
            "13 % HST in Ontario, 15 % in most of Atlantic Canada (14 % in "
            "Nova Scotia), GST alone in Alberta, GST + QST in Quebec: the "
            "estimate carries the tax label and rate of the province where "
            "the property sits, and prints it on the document.",
        ),
    ],
    ("CA", "remodelacion"): [
        (
            "Renovations priced for Canadian payments",
            "Room packages scaled to the real square metres, allowances "
            "labelled as allowances, deposit and draw schedule printed with "
            "the statutory holdback in view — an estimate written for how "
            "Canadian jobs are actually paid.",
        ),
    ],
    ("CA", "apu"): [
        (
            "Unit prices with the burden already in",
            "Every line item breaks into materials, labour at employer cost "
            "and equipment with its productivity rate. The wage is never "
            "mistaken for the cost, which is the most expensive quiet error "
            "in renovation estimating.",
        ),
    ],
}

HUB_FAQ: dict[tuple[str, str], list[dict[str, str]]] = {
    ("US", "software-presupuestos"): [
        {
            "q": "Does it work in feet and square feet?",
            "a": "Yes. US estimates measure, price and print in imperial units (ft, sq ft, cu yd, gal, lb); the conversion happens underneath, so the rate on the page is a true rate per square foot.",
        },
        {
            "q": "How is sales tax handled?",
            "a": "By job state: the app proposes each state's default treatment for a remodel — usually no tax charged to the customer — with the average combined rate as a starting point. You confirm or change it per estimate.",
        },
    ],
    ("IE", "software-presupuestos"): [
        {
            "q": "Does it check the two-thirds VAT rule?",
            "a": "Yes. The estimate knows its materials share, so if materials pass two thirds of the ex-VAT price, the document applies 23 % to the whole job instead of 13.5 % — and shows the treatment used.",
        },
        {
            "q": "Where do the Irish labour rates come from?",
            "a": "The statutory SEO grades and the Connect/AECI scales, loaded with employer PRSI and CWPS to a cost per billable hour. Every entry keeps its source and range, and you can override any rate.",
        },
    ],
    ("AU", "software-presupuestos"): [
        {
            "q": "Are prices shown with GST?",
            "a": "You build the estimate ex-GST; the client document prints the GST-inclusive total with the GST component shown, as consumer quotes require.",
        },
        {
            "q": "Where do the labour rates come from?",
            "a": "Award ordinary rates (MA000020/25/36) loaded with 12 % super, portable long service leave and workers comp. The award is the floor; set your own charge-out by keeping your margin per item.",
        },
    ],
    ("CA", "software-presupuestos"): [
        {
            "q": "Can it apply HST or GST + QST?",
            "a": "Yes — the estimate carries the tax name and combined rate of the property's province (HST 13 %, GST 5 % + QST, GST alone) and prints the treatment on the document.",
        },
        {
            "q": "Where do the Canadian labour rates come from?",
            "a": "Government of Canada Job Bank median wages, loaded with CPP/EI and workplace-insurance premiums to an employer cost per billable hour — each with its source and range.",
        },
    ],
}


def extra_hub(codigo: str, tema: str) -> list[tuple[str, str]]:
    clave = (str(codigo or "").strip().upper(), str(tema or "").strip().lower())
    return list(HUB_EXTRA.get(clave, ()))


def faq_hub(codigo: str, tema: str) -> list[dict[str, str]]:
    clave = (str(codigo or "").strip().upper(), str(tema or "").strip().lower())
    return list(HUB_FAQ.get(clave, ()))


def relacionados_hub(codigo: str) -> list[tuple[str, str]]:
    """Enlaces del hub a los artículos de su mercado (etiqueta corta, ruta)."""
    etiquetas = {
        "construction-estimate-template": "What a US estimate must include",
        "sales-tax-on-construction-by-state": "Sales tax on construction by state",
        "construction-labor-cost-per-hour": "True labor cost per hour (2026)",
        "builders-quote-template-ireland": "What an Irish quote must include",
        "vat-on-construction-ireland": "VAT 13.5 %/23 % and the two-thirds rule",
        "builder-rates-ireland": "Builder and trades rates (2026)",
        "building-quote-template-australia": "What a building quote must include",
        "gst-on-building-work-australia": "GST on building work",
        "tradie-hourly-rates-australia": "Tradie hourly rates (2026)",
        "contractor-estimate-template-canada": "What a Canadian estimate must include",
        "gst-hst-on-construction-canada": "GST/HST by province",
        "construction-labour-rates-canada": "Construction labour rates (2026)",
    }
    out = []
    for guia in guias_de(codigo):
        slug = guia["slug"]
        out.append((etiquetas.get(slug, guia["h1"]), ruta_articulo(codigo, slug)))
    return out
