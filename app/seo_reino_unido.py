# -*- coding: utf-8 -*-
"""SEO propio de Reino Unido: texto de mercado, no plantilla traducida.

La landing inglesa es una sola plantilla que sustituye el nombre del país:
sirve para no romper nada, pero deja las cinco landings anglófonas con el
mismo texto y el mismo esquema. Para el mercado que se abre primero —Reino
Unido— eso es justo lo que Google penaliza y lo que un contratista británico
detecta en dos líneas: un presupuesto no es una *quotation*, el IVA no es
siempre el 20 %, y el CIS no existe en ningún otro mercado del producto.

Este módulo concentra lo que es **exclusivo** de Reino Unido:

- el cuerpo largo de la landing ``/en-gb/``;
- los bloques extra de los tres hubs (``/en-gb/software-presupuestos``,
  ``/en-gb/apu``, ``/en-gb/remodelacion``);
- cuatro artículos de cola larga con su propia URL canónica
  (``/en-gb/guia/<slug>``), pensados para búsquedas que una landing no cubre:
  plantilla de presupuesto, retenciones CIS, inversión del sujeto pasivo y
  análisis de precios unitarios.

Los datos de precio y fiscalidad no se inventan aquí: salen de
``docs/INVESTIGACION_PRECIOS_REINO_UNIDO.md``,
``docs/METODOLOGIA_PRECIOS_REFERENCIA_REINO_UNIDO.md`` y
``app/services/fiscalidad_reino_unido.py``. Si cambia una cifra allí, cambia
aquí.
"""

from __future__ import annotations

PAIS = "GB"

# ── Landing /en-gb/ ─────────────────────────────────────────────────────
# Título y descripción se sustituyen a los de ``seo_en.landing_en("GB")``,
# que son genéricos y anuncian «20% VAT» como si la obra británica tuviera
# una sola alícuota. La descripción cabe en un snippet de escritorio sin
# que la recorte ``_recortar_meta``.
LANDING_TITLE = "CotizaT: construction estimating software for UK builders"
LANDING_DESCRIPTION = (
    "Estimating software for UK builders: 388 priced resources in GBP, CIS "
    "deductions, VAT treatment and PDF quotes."
)

LANDING_CUERPO: list[tuple[str, list[str]]] = [
    (
        "A UK quote is not a Spanish budget with the words changed",
        [
            "In Spain the document is a *presupuesto*; in the United Kingdom it "
            "is a quotation, and it is read differently. A builder's quote here "
            "is expected to open with the scope of works, carry a section per "
            "trade, state whether the price is fixed or daywork, say how long it "
            "stays open and what it excludes. Clients compare three of them side "
            "by side, so a document that mixes a lump sum with a rate per square "
            "metre and no exclusions reads as amateur before anyone checks the "
            "arithmetic.",
            "CotizaT is built around that document: sections, line items with "
            "quantity and unit, a price per line and a total you can defend. "
            "Preliminaries, provisional sums and daywork lines are ordinary line "
            "items, not notes at the bottom. The PDF carries your logo and your "
            "VAT registration number, and the client receives a file, not a login.",
        ],
    ),
    (
        "Prices in pounds from the British market, never converted dollars",
        [
            "The catalog holds 388 resource references for the United Kingdom, "
            "priced in pounds sterling from British sources. 167 were researched "
            "one by one —trade rates, merchants, plant hire— and 221 were derived "
            "from the factor of their own family. Nothing was obtained by "
            "converting the dollar catalog at the exchange rate: that route gives "
            "a tiled floor at roughly half the real cost of the British market.",
            "Labour is stored as employer cost per billable hour, with the "
            "employer's on-costs already inside: 19.8 % over 1,751.9 billable "
            "hours a year. An experienced general builder, a plumber, an "
            "electrician, a tiler and a groundworker do not cost the same hour, "
            "and the catalog does not pretend they do. Every reference carries "
            "the date it was checked, and the app marks it as current, due for "
            "review, stale or expired instead of showing an old figure as if it "
            "were today's.",
        ],
    ),
    (
        "CIS: 20 %, 30 % or gross, deducted from labour only",
        [
            "If you are a contractor paying subcontractors under the "
            "Construction Industry Scheme, the deduction is not a percentage of "
            "the invoice. It applies to the labour element, after materials and "
            "plant have been taken out. A registered subcontractor suffers 20 %, "
            "an unregistered one 30 %, and a subcontractor with gross payment "
            "status suffers nothing. Getting that base wrong is one of the most "
            "common ways a UK builder loses margin quietly.",
            "CotizaT models the three rates on the labour part of the line item, "
            "keeps materials out of the base and reflects the result in the "
            "document. The monthly return and the statement to the subcontractor "
            "remain your obligation with HMRC —the CIS300 is due by the 19th of "
            "the following month, or the 22nd if you file online— but the "
            "arithmetic behind it is already done when you quote.",
        ],
    ),
    (
        "VAT is not one number: 20 %, 5 %, 0 % and the domestic reverse charge",
        [
            "Standard-rated work is 20 %. Qualifying work on residential property "
            "can be 5 % —a home that has stood empty for at least two years, or a "
            "non-residential building turned into a dwelling— and a new-build "
            "home is zero-rated. Since March 2021 the domestic reverse charge also "
            "applies to most construction services supplied business to business "
            "and reported under CIS: the supplier does not charge VAT and the "
            "customer accounts for it, with the invoice carrying the note that "
            "VAT Act 1994 section 55A applies.",
            "The tax treatment is set per quote, not baked into the country. You "
            "choose standard, reduced, zero or reverse charge, and the PDF says "
            "which one it is. CotizaT does not decide your VAT for you and does "
            "not issue a VAT invoice: it produces the commercial document that "
            "precedes it, and it says so in the terms.",
        ],
    ),
    (
        "The trades are named the way they are named on site",
        [
            "A British client does not read *countertop*, *drywall* or *faucet*. "
            "They read worktop, plasterboard and tap. The catalog is written in "
            "the vocabulary of the British site: skirting, splashback, cooker "
            "hood, socket outlet, consumer unit, call point, ironmongery, kerb, "
            "lintel, screed, making good, skip. A quote that says *pull station* "
            "or *built-in hob* announces that it was written for somewhere else.",
            "That vocabulary is applied on top of the English base, not instead "
            "of it: the same line item reads *baseboard* on a US quote and "
            "*skirting* on a UK one, and the descriptions follow. Australia, "
            "Canada, Ireland and the United States have their own tables, because "
            "no two of those markets share a price base.",
        ],
    ),
    (
        "A rate per square metre is not a price",
        [
            "Every line item in the catalog arrives broken down: materials with "
            "waste, labour with its productivity rate in hours per unit, and "
            "plant where there is plant. That breakdown is the only way to know "
            "whether a job at £45 per square metre leaves you 30 % or 4 %. The "
            "unit price analysis is editable, and changing one resource "
            "recalculates every line item that uses it while quotes already sent "
            "stay frozen in their version.",
            "From the breakdown the app also gives you crew hours by trade, which "
            "is the number that decides whether you can finish before the scaffold "
            "comes down. None of that internal cost appears on the client's PDF: "
            "they see the line item, the quantity, the price and the total.",
        ],
    ),
    (
        "From the site visit to the signed quote",
        [
            "You measure, build the quote by sections, check the margin and send a "
            "PDF by WhatsApp or email —the way work is actually won in the UK. If "
            "the client asks to drop the porcelain and use ceramic, you do not "
            "rewrite the file: a new version is created and you copy a summary "
            "with the previous total, the new total and what moved.",
            "The client never creates an account. The private link with an online "
            "acceptance is optional, and the document stays a commercial quote: it "
            "is not a VAT invoice, not a JCT contract and not tax advice. When the "
            "job is won, the same workspace holds the project, the client and the "
            "payment requests.",
        ],
    ),
]

LANDING_FAQ: list[dict[str, str]] = [
    {
        "q": "Does CotizaT apply CIS deductions on a quote?",
        "a": (
            "Yes. You mark the subcontractor as registered (20 %), unregistered "
            "(30 %) or gross payment status (0 %), and the deduction is applied "
            "to the labour part of the line item, after materials and plant. The "
            "monthly CIS return to HMRC is still yours to file."
        ),
    },
    {
        "q": "Can I quote a VAT domestic reverse charge job?",
        "a": (
            "Yes. VAT treatment is chosen per quote: standard 20 %, reduced 5 %, "
            "zero-rated or domestic reverse charge under VAT Act 1994 section "
            "55A. The PDF states the treatment, and the reverse-charge note is "
            "printed when it applies."
        ),
    },
    {
        "q": "Are the prices real UK prices or dollars converted?",
        "a": (
            "Real UK prices. 388 resources priced in pounds from British sources: "
            "167 researched one by one and 221 derived from the factor of their "
            "family. Each reference carries the date it was checked, and the app "
            "flags it when it needs review instead of showing an old figure as "
            "current."
        ),
    },
    {
        "q": "Is it for big contractors or for a small firm?",
        "a": (
            "It is built for firms of two to fifteen people: general builders, "
            "refurbishment specialists, bathroom and kitchen fitters, and "
            "subcontractors who quote several jobs a month. It is not an ERP for "
            "public works and it is not a BIM viewer."
        ),
    },
    {
        "q": "Does it issue VAT invoices?",
        "a": (
            "No. CotizaT produces commercial documents: quotations and payment "
            "requests. A VAT invoice has legal requirements and is issued through "
            "your accounting software; the quote is what gets you to that point."
        ),
    },
    {
        "q": "Can I bring my own price list?",
        "a": (
            "Yes. You can import breakdown matrices from Excel (.xlsx) or BC3 "
            "(FIEBDC-3), paste TSV from a spreadsheet, or start from the included "
            "catalog of more than 3,000 line items with its unit price analyses."
        ),
    },
]

# ── Hubs de intención /en-gb/<tema> ─────────────────────────────────────
# Se añaden al cuerpo genérico del hub. Cada bloque es británico de verdad:
# no repite «in the United Kingdom» lo que ya dice el H1.
HUB_EXTRA: dict[str, list[tuple[str, str]]] = {
    "software-presupuestos": [
        (
            "Quotes with sections, preliminaries and exclusions",
            "A British quotation is read as a scope document. CotizaT builds it by "
            "sections —strip-out, first fix, second fix, finishes— with "
            "preliminaries, provisional sums and daywork as ordinary lines, and "
            "with exclusions written where the client will see them. The total is "
            "the sum of what you actually priced, not a rate multiplied by a "
            "number someone measured on the back of a business card.",
        ),
        (
            "Excel is fine until the third revision",
            "Most UK builders start in a spreadsheet and it works: one tab for "
            "rates, another for the job, a formula for the total. It stops working "
            "when cement goes up, the client changes the tiles and nobody "
            "remembers which file was approved. CotizaT keeps the price base once, "
            "recalculates every line item that uses a resource, and freezes each "
            "quote in the version that was sent.",
        ),
        (
            "CIS and VAT handled where they belong",
            "CIS is a deduction on labour, not on the invoice, and VAT treatment "
            "changes with the job: 20 % standard, 5 % on qualifying residential "
            "work, 0 % on new-build, and domestic reverse charge between "
            "VAT-registered businesses reporting under CIS. Both are set per "
            "quote, so a refurbishment for a private homeowner and a subcontract "
            "for a main contractor do not come out looking the same.",
        ),
    ],
    "apu": [
        (
            "The breakdown behind a UK rate",
            "A unit price analysis for a British job is materials with waste, "
            "labour at the employer cost of the trade with its productivity rate, "
            "and plant where plant is needed. The catalog stores it for 388 "
            "resources in pounds, so the rate per square metre of plasterboard or "
            "the price of a socket outlet has a breakdown underneath instead of a "
            "number someone remembers.",
        ),
        (
            "Plant, waste and making good belong in the price",
            "UK estimating rarely fails on the big numbers; it fails on the small "
            "ones that were never priced: a skip, a scissor lift for a week, "
            "chasing and making good around new sockets, the plaster that follows "
            "the electrician. Those are resources with a price and a productivity "
            "rate, and they belong in the line item before the quote is sent.",
        ),
        (
            "Labour cost is not the wage",
            "An hourly rate on site is not what the hour costs the company. "
            "Employer National Insurance, pension, CITB levy, holiday and sick pay "
            "sit on top: in this catalog they add 19.8 % over 1,751.9 billable "
            "hours a year. Pricing labour at the operative's wage is the fastest "
            "way to win work and lose money.",
        ),
    ],
    "remodelacion": [
        (
            "Refurbishment quotes: strip-out, making good and snagging",
            "A bathroom refurbishment in Manchester or a kitchen in Bristol is "
            "not a list of finishes. It is strip-out, waste removal, first fix, "
            "plastering and making good, tiling, second fix and a snagging list "
            "that eats a day at the end. CotizaT prices those stages as sections, "
            "so the quote shows the scope and you can see which stage is thin.",
        ),
        (
            "Variations in writing, not on WhatsApp",
            "The client asks for a different worktop. You change one product, the "
            "new version is created and you send a summary with the previous "
            "total, the new total and what moved. That is what stops the argument "
            "about what was agreed three weeks later, and it costs you no more "
            "than a click.",
        ),
        (
            "Room packages scaled to the real square metres",
            "A bathroom or kitchen package inserts the whole section with its line "
            "items and quantities scaled to the measured area. Fixed pieces —WC, "
            "basin, vanity unit— are not multiplied. Products can be marked as "
            "included, optional or alternative, with a photo, so the client picks "
            "without you rebuilding the quote.",
        ),
    ],
}

HUB_FAQ: dict[str, list[dict[str, str]]] = {
    "software-presupuestos": [
        {
            "q": "Does it handle a job priced at a rate per square metre?",
            "a": (
                "Yes. You can price by line item with quantities, by rate per "
                "square metre, or as daywork, and the quote states which basis it "
                "uses. The unit price analysis behind each line item is what tells "
                "you whether that rate leaves a margin."
            ),
        },
        {
            "q": "Does it cover the whole UK or only England?",
            "a": (
                "The price base is national and is not split by region. Scottish "
                "and Welsh work uses the same catalog with your own rates where "
                "you know them; VAT and CIS rules are UK-wide."
            ),
        },
    ],
    "apu": [
        {
            "q": "Where do the UK resource prices come from?",
            "a": (
                "From British sources checked one by one for 167 of the 388 "
                "references —trade rates, builders' merchants, plant hire— and "
                "derived from the factor of their family for the rest. Each one "
                "carries the date of the check and the app flags when it needs "
                "review."
            ),
        },
        {
            "q": "Can I edit the productivity rate?",
            "a": (
                "Yes. Productivity is a property of the resource row in the line "
                "item, so you can adjust it per job without touching the catalog, "
                "and the price recalculates."
            ),
        },
    ],
    "remodelacion": [
        {
            "q": "Does it work for a single bathroom, not a whole house?",
            "a": (
                "Yes. The bathroom package is the fastest path: it inserts the "
                "section scaled to the measured area, and you remove or add line "
                "items from there. Nothing forces you into a full-house structure."
            ),
        },
        {
            "q": "Can the client see the breakdown of costs?",
            "a": (
                "No. The PDF shows line items, quantities, prices, totals and the "
                "sections you choose to print. Internal cost, productivity and "
                "crew hours stay in the workspace."
            ),
        },
    ],
}

# ── Artículos de cola larga ─────────────────────────────────────────────
# Cuatro URLs propias bajo /en-gb/guia/. Cada una responde a una búsqueda
# concreta que la landing no puede cubrir sin volverse un documento.
ARTICULOS: dict[str, dict] = {
    "construction-quote-template-uk": {
        "slug": "construction-quote-template-uk",
        "pais": "GB",
        "pais_nombre": "the United Kingdom",
        "pais_path": "/en-gb/",
        "kicker": "United Kingdom · Quotations",
        "title": "CotizaT: what a UK construction quote must include",
        "h1": "What a UK construction quote must include (VAT, CIS and terms)",
        "description": (
            "A UK construction quote must state scope, basis of price, VAT "
            "treatment, exclusions, validity and payment terms. What each part "
            "is for."
        ),
        "lead": (
            "A British client compares three quotes and signs one. The document "
            "that wins is not the cheapest: it is the one that makes the scope "
            "and the terms unambiguous. This is what a construction quote in the "
            "UK has to carry, section by section."
        ),
        "secciones": [
            (
                "1. Your details, and the ones the taxman expects",
                [
                    "Trading name, address, phone and email, plus your VAT "
                    "registration number if you are registered. Under CIS a "
                    "contractor also wants your UTR and your verification status, "
                    "because that decides whether they deduct 20 %, 30 % or "
                    "nothing. Missing VAT number on a quote is the first thing an "
                    "accountant flags when the job goes to invoice.",
                ],
            ),
            (
                "2. Scope of works, written as sections",
                [
                    "The scope is the part that protects you. Written as sections "
                    "—strip-out, first fix, second fix, finishes— it lets the "
                    "client see what they are buying and lets you see where the "
                    "money is. A single paragraph saying 'refurbish bathroom' "
                    "guarantees a conversation about what was included.",
                    "Preliminaries belong here too: site setup, waste removal, "
                    "scaffold, protection of existing finishes. In the UK these are "
                    "often the lines that decide whether the job makes money, and "
                    "they are the first ones a client asks to remove.",
                ],
            ),
            (
                "3. The basis of the price: fixed, rate or daywork",
                [
                    "Say it explicitly. A fixed price for a defined scope, a rate "
                    "per square metre or per linear metre for measured work, or "
                    "daywork at an hourly rate plus materials. Mixing the three "
                    "without labelling them is how a quote becomes a dispute.",
                    "If part of the job depends on opening up —a wall, a floor, a "
                    "roof— price it as a provisional sum and explain what it "
                    "covers. Provisional sums are a normal part of UK estimating; "
                    "what is not normal is hiding one inside a fixed total.",
                ],
            ),
            (
                "4. Labour and materials split, because CIS needs it",
                [
                    "A contractor deducting under CIS must exclude materials and "
                    "plant from the deduction base, so a quote that only shows one "
                    "total forces them to ask you for the split. Showing labour and "
                    "materials separately —or pricing materials as their own "
                    "sections— makes the deduction obvious and speeds up payment.",
                    "This is also where the 5 % and 0 % VAT cases are decided: "
                    "qualifying residential renovation and new-build are priced "
                    "differently from standard-rated work, and the quote should say "
                    "which treatment applies rather than leaving it to the invoice.",
                ],
            ),
            (
                "5. Exclusions, validity and payment terms",
                [
                    "List what is not included: making good after other trades, "
                    "asbestos removal, building control fees, decorations, "
                    "scaffold licence. Then say how long the price holds —30 days "
                    "is common— and how payment works: deposit, stage payments, "
                    "final balance on practical completion, retention if any.",
                    "A quote without an expiry date is a promise to work at last "
                    "year's prices. A quote without payment terms is an interest-free "
                    "loan to your client.",
                ],
            ),
            (
                "6. Revisions, in writing",
                [
                    "The quote will change. The only question is whether the change "
                    "is documented. Version the document, keep the previous total, "
                    "the new total and the difference, and send it by email so the "
                    "date is recorded.",
                    "CotizaT does exactly that: sections and line items, CIS on the "
                    "labour element, VAT treatment per quote and an immutable "
                    "version each time you send. The client opens a PDF, not an "
                    "account.",
                ],
            ),
        ],
        "faq": [
            {
                "q": "Do I have to show prices with and without VAT?",
                "a": (
                    "For a business client, yes: a VAT-registered customer needs to "
                    "know the net figure and the VAT. For a consumer, showing the "
                    "gross total is clearer, with the VAT element stated. CotizaT "
                    "prints the treatment and the tax line you configure."
                ),
            },
            {
                "q": "Is a quote legally binding in the UK?",
                "a": (
                    "A quotation becomes binding when it is accepted and forms a "
                    "contract; an estimate is not a fixed offer. That is why the "
                    "document has to say which one it is and how long it stays "
                    "open. This is general information, not legal advice."
                ),
            },
            {
                "q": "Can I send a quote without a site visit?",
                "a": (
                    "You can, but then the scope has to be tighter and the "
                    "exclusions longer. Most builders price from a measured survey "
                    "and list assumptions explicitly."
                ),
            },
        ],
        "related": [
            ("CIS deductions explained", "/en-gb/guia/cis-deduction-subcontractors"),
            ("VAT domestic reverse charge", "/en-gb/guia/vat-domestic-reverse-charge-construction"),
            ("Estimating software for the UK", "/en-gb/software-presupuestos"),
        ],
    },
    "cis-deduction-subcontractors": {
        "slug": "cis-deduction-subcontractors",
        "pais": "GB",
        "pais_nombre": "the United Kingdom",
        "pais_path": "/en-gb/",
        "kicker": "United Kingdom · CIS",
        "title": "CotizaT: CIS deductions explained (20%, 30% or gross)",
        "h1": "CIS deductions explained: 20 %, 30 % or gross payment status",
        "description": (
            "How CIS deductions work in the UK: the three rates, why materials "
            "are excluded, what the contractor files and by when, and where the "
            "money goes."
        ),
        "lead": (
            "The Construction Industry Scheme takes a percentage of the labour in "
            "a subcontractor's invoice, not of the whole invoice. Getting that "
            "base wrong quietly eats a builder's margin on every job. This is how "
            "the three rates work and where they land in a quote."
        ),
        "secciones": [
            (
                "The three rates, and who decides which one applies",
                [
                    "A subcontractor registered with HMRC for CIS suffers a 20 % "
                    "deduction. One who is not registered —or who cannot be "
                    "verified— suffers 30 %. One with gross payment status suffers "
                    "nothing. The contractor verifies the subcontractor with HMRC "
                    "before the first payment and applies the rate HMRC returns.",
                    "The status follows the subcontractor, not the job. The same "
                    "tiler can be at 20 % for one contractor and gross for another "
                    "only if their registration actually differs.",
                ],
            ),
            (
                "Why materials come out of the deduction base",
                [
                    "CIS is a tax on labour. Materials, plant hire and consumables "
                    "that you supply are not subject to the deduction, provided "
                    "they are identifiable in the invoice. A £4,000 invoice made of "
                    "£1,200 of tiles and £2,800 of labour is not deducted on "
                    "£4,000.",
                    "This is exactly why a quote that shows one lump sum causes "
                    "friction: the contractor has to reconstruct the split, and "
                    "many simply apply the percentage to the total. The "
                    "subcontractor loses cash flow; the contractor risks an "
                    "incorrect return.",
                ],
            ),
            (
                "What the contractor files, and when",
                [
                    "Monthly. The CIS300 return covers payments made in the tax "
                    "month and is due by the 19th of the following month, or the "
                    "22nd if filed online. The contractor also has to give each "
                    "subcontractor a written statement of the deductions made, "
                    "within 14 days of the end of the tax month.",
                    "At the end of the tax year the contractor files a final "
                    "return, and the subcontractor can claim the deductions back "
                    "against their tax bill. None of that administration "
                    "disappears because the quote was well built; it just stops "
                    "the numbers being wrong.",
                ],
            ),
            (
                "Where CIS sits in a line item",
                [
                    "In a unit price analysis, labour is hours at the employer "
                    "cost of the trade. CIS is not part of that cost: it is a "
                    "deduction applied to the labour value when paying the "
                    "subcontractor. Mixing both in the same cell hides the rate "
                    "you are actually paying for the hour.",
                    "For a contractor hiring subcontractors, the practical "
                    "question is what the labour line costs the company once the "
                    "deduction has been withheld and later accounted for. For the "
                    "subcontractor, it is what arrives in the bank this month and "
                    "what comes back at the end of the year.",
                ],
            ),
            (
                "Gross payment status is not permanent",
                [
                    "HMRC reviews gross status periodically and can withdraw it if "
                    "turnover, tax compliance or the business structure no longer "
                    "meet the conditions. A quote built on the assumption of 0 % "
                    "deduction should survive the year it changes.",
                    "In CotizaT the three rates are a setting per subcontractor, "
                    "so the same catalog produces a quote at 20 %, 30 % or gross "
                    "without duplicating the price base. The monthly return is "
                    "still filed with HMRC, not with us.",
                ],
            ),
        ],
        "faq": [
            {
                "q": "Is CIS deducted on the total invoice?",
                "a": (
                    "No. The deduction applies to the labour element, excluding "
                    "materials and plant that you supply and that are identifiable "
                    "in the invoice."
                ),
            },
            {
                "q": "What happens if a subcontractor is not registered?",
                "a": (
                    "The contractor applies 30 % until HMRC verifies a different "
                    "status. The subcontractor can register and recover the "
                    "difference through their tax return."
                ),
            },
            {
                "q": "Does CIS apply to a homeowner?",
                "a": (
                    "No. CIS applies to payments between contractors and "
                    "subcontractors in the construction industry. A private "
                    "householder is not a contractor for CIS purposes."
                ),
            },
        ],
        "related": [
            ("VAT domestic reverse charge", "/en-gb/guia/vat-domestic-reverse-charge-construction"),
            ("What a UK quote must include", "/en-gb/guia/construction-quote-template-uk"),
            ("Unit price analysis for a UK job", "/en-gb/guia/unit-price-analysis-uk"),
        ],
    },
    "vat-domestic-reverse-charge-construction": {
        "slug": "vat-domestic-reverse-charge-construction",
        "pais": "GB",
        "pais_nombre": "the United Kingdom",
        "pais_path": "/en-gb/",
        "kicker": "United Kingdom · VAT",
        "title": "CotizaT: VAT domestic reverse charge in construction",
        "h1": "VAT domestic reverse charge in construction: when it applies",
        "description": (
            "The domestic reverse charge since March 2021: which construction "
            "services it covers, what the invoice must say, and when 5% or 0% "
            "still applies."
        ),
        "lead": (
            "Since 1 March 2021 most construction services supplied business to "
            "business and reported under CIS carry the domestic reverse charge. "
            "The supplier does not charge VAT and the customer accounts for it. "
            "Applying it to the wrong job, or forgetting the note on the "
            "invoice, creates a problem that surfaces months later."
        ),
        "secciones": [
            (
                "What the reverse charge does",
                [
                    "Normally the supplier charges VAT and pays it to HMRC. Under "
                    "the domestic reverse charge the supplier issues an invoice "
                    "with no VAT, and the customer accounts for both the output and "
                    "the input tax on their return. For a business that can recover "
                    "VAT the cash effect is usually neutral; for the supplier it "
                    "removes a VAT bill they would otherwise hold temporarily.",
                    "It applies to construction services supplied between "
                    "VAT-registered businesses where the supply is reported under "
                    "CIS, and to goods supplied with those services. It does not "
                    "apply to zero-rated supplies or to services outside the scope "
                    "of CIS.",
                ],
            ),
            (
                "Who is excluded: end users and intermediary suppliers",
                [
                    "If your customer is the end user of the building —a "
                    "householder, or a business that will occupy the property and "
                    "is not itself a contractor— the reverse charge does not apply: "
                    "you charge VAT normally. The same happens with an intermediary "
                    "supplier in a chain, who must tell you in writing that they "
                    "are acting as one.",
                    "This is why the same refurbishment can be standard-rated for "
                    "one client and reverse-charged for another. The treatment "
                    "follows the customer and the chain, not the type of work.",
                ],
            ),
            (
                "What the invoice has to say",
                [
                    "The invoice must show the net amount, no VAT, and a statement "
                    "that the domestic reverse charge applies and that the customer "
                    "must account for the VAT. The usual wording references VAT Act "
                    "1994 section 55A. The customer's VAT number is normally shown "
                    "as well.",
                    "CotizaT prints the treatment you select on the quote and on "
                    "the payment request, including the reverse-charge note, so the "
                    "document and the eventual invoice do not tell two different "
                    "stories.",
                ],
            ),
            (
                "The rest of the VAT map: 20 %, 5 % and 0 %",
                [
                    "Standard-rated work is 20 %. The reduced 5 % rate covers "
                    "qualifying work on residential property, such as renovating a "
                    "home that has been empty for at least two years or converting "
                    "a non-residential building into a dwelling, and certain "
                    "energy-saving materials. New-build residential work is "
                    "zero-rated.",
                    "A quote states the treatment it was priced with. When the job "
                    "mixes standard and reduced work, splitting the sections is the "
                    "only honest way to show it —and the only way the customer can "
                    "check it.",
                ],
            ),
            (
                "What this means for the person writing the quote",
                [
                    "Three questions decide the treatment: is the customer "
                    "VAT-registered, is the supply reported under CIS, and is the "
                    "customer the end user. Get those three answers before you "
                    "price, because they change the document, not just the invoice.",
                    "CotizaT does not decide your VAT and does not file returns. It "
                    "keeps the treatment per quote, prints it, and stops the same "
                    "catalog from producing a standard-rated quote for a job that "
                    "was reverse charge.",
                ],
            ),
        ],
        "faq": [
            {
                "q": "Does the reverse charge apply to a homeowner?",
                "a": (
                    "No. A private householder is the end user, so you charge VAT "
                    "as normal. The reverse charge needs a VAT-registered business "
                    "customer and a supply reported under CIS."
                ),
            },
            {
                "q": "Do I still charge 5 % on an empty property renovation?",
                "a": (
                    "Qualifying work on a home that has been empty for at least two "
                    "years can be reduced-rated at 5 %, but the reverse charge does "
                    "not apply to zero-rated or reduced-rated supplies in the way it "
                    "does to standard-rated ones. Check the conditions of the "
                    "specific job."
                ),
            },
            {
                "q": "What if I get the treatment wrong?",
                "a": (
                    "It is a VAT error that has to be corrected, usually by "
                    "adjusting the invoice and the return. It is far cheaper to "
                    "decide the treatment when quoting, which is why the quote "
                    "records it."
                ),
            },
        ],
        "related": [
            ("CIS deductions explained", "/en-gb/guia/cis-deduction-subcontractors"),
            ("What a UK quote must include", "/en-gb/guia/construction-quote-template-uk"),
            ("Unit price analysis for a UK job", "/en-gb/guia/unit-price-analysis-uk"),
        ],
    },
    "unit-price-analysis-uk": {
        "slug": "unit-price-analysis-uk",
        "pais": "GB",
        "pais_nombre": "the United Kingdom",
        "pais_path": "/en-gb/",
        "kicker": "United Kingdom · Unit price analysis",
        "title": "CotizaT: unit price analysis for a UK construction job",
        "h1": "How to build a unit price analysis for a UK job",
        "description": (
            "Materials with waste, labour at employer cost with productivity, and "
            "plant: how to build a unit price analysis in pounds that survives a "
            "price change mid-job."
        ),
        "lead": (
            "A rate per square metre is a decision, not a price. Behind it there "
            "has to be a breakdown of materials, labour and plant, with "
            "productivity rates in pounds. This is how that breakdown is built for "
            "a British job, and what it changes when a price moves."
        ),
        "secciones": [
            (
                "The three blocks, in the order they are priced",
                [
                    "Materials first, with waste. A tiling line is not the price of "
                    "the tile: it is the tile plus adhesive, grout, trim, spacers "
                    "and the percentage that ends up in the skip. Waste is not "
                    "padding; it is what the job actually consumes.",
                    "Labour second, in hours per unit of work, at the employer cost "
                    "of the trade. Plant third, only where plant exists: a mixer, a "
                    "scissor lift, a breaker, a skip. Each block is a row with a "
                    "price and a quantity, and the sum is the direct cost.",
                ],
            ),
            (
                "Productivity is the number that decides the price",
                [
                    "Two builders can pay the same hourly rate and produce wildly "
                    "different prices because one tiler lays 8 m² a day and the "
                    "other lays 14. The unit price analysis stores hours per unit, "
                    "so the difference is visible instead of being buried in a "
                    "guessed rate per square metre.",
                    "It also gives you crew hours: the number that tells you "
                    "whether the job fits in the week you promised. That number "
                    "never appears on the client's PDF.",
                ],
            ),
            (
                "Employer cost, not the wage",
                [
                    "The hour costs more than the operative is paid. Employer "
                    "National Insurance, pension contributions, the CITB levy, "
                    "holiday and sick pay all sit on the employment cost. In this "
                    "catalog they add 19.8 % over 1,751.9 billable hours a year.",
                    "That is why the reference rates per trade differ: a "
                    "groundworker, a bricklayer, a tiler, a plumber and an "
                    "electrician are not interchangeable hours. Pricing everything "
                    "at one blended rate is how a profitable job turns into a "
                    "break-even one.",
                ],
            ),
            (
                "Prices that cascade, quotes that do not",
                [
                    "When a merchant puts cement or plasterboard up, you change the "
                    "resource once. Every line item that uses it recalculates with "
                    "the new price, and so does the quote still in edit. Quotes "
                    "already sent keep the version and the total they were sent "
                    "with.",
                    "That separation —live price base, frozen documents— is the "
                    "difference between a spreadsheet and a price system. In a "
                    "spreadsheet, either everything moves or nothing does.",
                ],
            ),
            (
                "From the breakdown to the client's page",
                [
                    "The client does not see materials, productivity or crew hours. "
                    "They see the section, the line item, the quantity, the unit "
                    "price and the total, with the VAT treatment stated. The "
                    "breakdown exists so the numbers you send can be defended, not "
                    "so they can be audited by the customer.",
                    "CotizaT ships 388 UK resource references in pounds and more "
                    "than 3,000 broken-down line items. You can also import your "
                    "own from Excel or BC3 and keep working with the rates you "
                    "already trust.",
                ],
            ),
        ],
        "faq": [
            {
                "q": "Do I need productivity rates for every trade?",
                "a": (
                    "The catalog ships with rates for its line items, and you can "
                    "change them per job. For work you price yourself, an hours-per-"
                    "unit figure is what turns a guessed rate into a defensible "
                    "price."
                ),
            },
            {
                "q": "Is the unit price analysis visible to the client?",
                "a": (
                    "No. The PDF shows line items and totals. Internal cost, "
                    "productivity and crew hours stay in your workspace."
                ),
            },
            {
                "q": "Can I use my own material prices?",
                "a": (
                    "Yes. You can edit the resource price, import your own list from "
                    "Excel or BC3, or keep the national reference and override the "
                    "ones you buy better."
                ),
            },
        ],
        "related": [
            ("What a UK quote must include", "/en-gb/guia/construction-quote-template-uk"),
            ("CIS deductions explained", "/en-gb/guia/cis-deduction-subcontractors"),
            ("Unit price analysis hub", "/en-gb/apu"),
        ],
    },
}

ORDEN_ARTICULOS: tuple[str, ...] = (
    "construction-quote-template-uk",
    "cis-deduction-subcontractors",
    "vat-domestic-reverse-charge-construction",
    "unit-price-analysis-uk",
)


def es_de_reino_unido(mercado: str) -> bool:
    """¿Este mercado es Reino Unido? La pregunta se hace una sola vez."""
    return str(mercado or "").strip().upper() == PAIS


def cuerpo_landing() -> list[tuple[str, list[str]]]:
    return LANDING_CUERPO


def guias() -> list[dict]:
    """Artículos UK en el orden en que se enlazan."""
    return [ARTICULOS[slug] for slug in ORDEN_ARTICULOS]


def ruta_articulo(slug: str) -> str:
    return f"/en-gb/guia/{slug}"


def articulo(slug: str) -> dict | None:
    return ARTICULOS.get(str(slug or "").strip())


def extra_hub(tema: str) -> list[tuple[str, str]]:
    return HUB_EXTRA.get(str(tema or "").strip().lower(), [])


def faq_hub(tema: str) -> list[dict[str, str]]:
    return HUB_FAQ.get(str(tema or "").strip().lower(), [])
