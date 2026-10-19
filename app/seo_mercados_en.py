# -*- coding: utf-8 -*-
"""Contenido de mercado para los otros cuatro mercados de habla inglesa.

Reino Unido tiene su módulo propio (``seo_reino_unido.py``) porque es el
mercado que se abre primero y el único con matriz de precios cargada. Este
módulo cubre Estados Unidos, Australia, Canadá e Irlanda: sin él, sus cinco
landings eran la misma página con el nombre del país cambiado, y Google trata
ese patrón como contenido duplicado.

Lo que cambia de un mercado a otro no es el idioma: es la fiscalidad (sales
tax por estado, GST, HST, VAT irlandés), el contrato (retainage, holdback,
progress claims, RCT) y la forma de medir la obra (imperial solo en Estados
Unidos). El texto lo dice con nombres propios, no con adjetivos.

Ninguno de estos mercados tiene todavía estudio de precios propio, así que
aquí no se publican cifras de precios: se explica cómo se presupuesta y qué
lleva el documento. Cuando haya matriz, las cifras entran en su sitio.
"""

from __future__ import annotations

CUERPO: dict[str, list[tuple[str, list[str]]]] = {
    # ── Estados Unidos ───────────────────────────────────────────────────
    "US": [
        (
            "An estimate is not a bid, and a proposal is neither",
            [
                "In the United States the three words describe three different "
                "documents. An estimate is your internal number: what the work "
                "costs with your labour, material and equipment. A proposal is what "
                "you send the client: scope, inclusions, exclusions, assumptions, "
                "validity. A bid is a fixed offer against someone else's "
                "specification, usually with alternates and unit prices for work "
                "that cannot be measured yet.",
                "CotizaT builds the estimate with its unit price analysis and turns "
                "it into a proposal with sections, line items, quantities and a "
                "total you can defend. If the job is a bid, the same catalog gives "
                "you the unit prices (per square foot of drywall, per linear foot of "
                "pipe) that a general contractor expects to see broken out.",
            ],
        ),
        (
            "Sales tax is local, and labour is not taxed the same everywhere",
            [
                "There is no national sales tax. Each state sets its own rate, and "
                "counties and cities add theirs on top. Many states tax construction "
                "materials but not the labour to install them, some tax the finished "
                "improvement, and a few treat a contractor as the final consumer of "
                "the materials it buys. That is why the app asks you for the rate "
                "instead of inventing a national one.",
                "The tax treatment is set per estimate, so a job in Austin and a job "
                "in Miami do not come out looking the same. CotizaT does not decide "
                "your sales tax and does not issue a tax invoice: it produces the "
                "commercial proposal that leads to the contract.",
            ],
        ),
        (
            "Feet, inches and gallons — and CSI divisions",
            [
                "The United States is the only imperial market in the product. The "
                "US price library is researched in the units the market actually "
                "sells — cubic yards of ready-mix, 94-lb cement bags, 4x8 sheets, "
                "gallons of paint — and kept with its low-high range, so the number "
                "behind a line item is an American price, not a foreign one "
                "converted. Entering quantities in feet and inches is in "
                "development; until it lands, estimates are measured in the "
                "catalog's metric units, and we'd rather tell you that here than "
                "in the small print.",
                "The catalog is organised in sections that map onto the CSI "
                "MasterFormat divisions a general contractor already uses: concrete, "
                "masonry, metals, thermal and moisture protection, finishes, "
                "mechanical and electrical. You do not have to learn a private "
                "numbering to find a line item.",
            ],
        ),
        (
            "Retainage, lien waivers and change orders",
            [
                "Money in US construction moves on documents. Retainage —commonly 5 "
                "to 10 % held until substantial completion—, progress payments "
                "against a schedule of values, lien waivers signed at each payment, "
                "and change orders that must be written before the work is done. A "
                "verbal change is how a profitable job becomes an argument.",
                "CotizaT keeps the estimate, the client and the payment requests in "
                "the same workspace, and every revision is a version with a previous "
                "total, a new total and what moved. The contract and the lien waivers "
                "remain your documents; the numbers behind them do not have to be "
                "rebuilt in a spreadsheet.",
            ],
        ),
        (
            "What an hour of labour really costs",
            [
                "A carpenter's wage is not the labour cost. Payroll taxes, workers' "
                "compensation, general liability and the cost of keeping a crew "
                "employed between jobs sit on top of the hourly rate. That burdened "
                "rate —not the wage— is what has to be in the unit price analysis.",
                "Each line item arrives broken down into materials with waste, labour "
                "with its productivity rate and equipment where there is equipment. "
                "Change the price of lumber or the crew's hourly cost once and every "
                "line item that uses it recalculates, while estimates already sent "
                "stay frozen in their version.",
            ],
        ),
    ],
    # ── Australia ────────────────────────────────────────────────────────
    "AU": [
        (
            "A quote, an estimate and a variation are three different things",
            [
                "An Australian quote is an offer: a fixed price for a defined scope, "
                "with a validity period. An estimate is a guide, not a promise. And a "
                "variation is the written instruction that changes the scope after "
                "the contract is signed —the one document that decides whether the "
                "job still makes money.",
                "CotizaT builds the quote by sections with its scope, exclusions and "
                "validity, and every revision becomes a version with the previous "
                "total, the new total and what changed, so a variation is documented "
                "instead of remembered.",
            ],
        ),
        (
            "GST is 10 %, and a tax invoice is not a quote",
            [
                "Goods and services tax is 10 % nationally, and the document that "
                "matters for a business client is the tax invoice, which has its own "
                "requirements once the supply reaches A$1,000: the seller's ABN, the "
                "words 'tax invoice', the GST amount and the buyer's identity if they "
                "ask for it.",
                "CotizaT produces the quote and the payment request, and states the "
                "GST treatment you configure. It does not issue the tax invoice —that "
                "comes from your accounting system— but the numbers stop being "
                "rebuilt by hand when the job moves to invoicing.",
            ],
        ),
        (
            "Prime cost, provisional sum and progress claims",
            [
                "Australian residential work leans on two figures an American or "
                "British estimate rarely uses: the prime cost (PC) sum for items "
                "whose price is not fixed when the contract is signed —tiles, "
                "tapware, an appliance chosen by the owner— and the provisional sum "
                "for work that cannot be measured yet.",
                "Progress claims split the job into stages —slab, frame, lock-up, fit-"
                "out— and each claim is measured against what was actually built. "
                "Both fit into the same structure: sections, line items, quantities, "
                "and a total per stage you can send without rebuilding the document.",
            ],
        ),
        (
            "Licensing and certification are state by state",
            [
                "There is no single national builder licence. Queensland has the "
                "QBCC, New South Wales has Fair Trading and home building "
                "compensation, Victoria has the VBA, and each state has its own "
                "thresholds, insurance and certifier rules. A quote that travels "
                "between states without saying which licence covers the work is a "
                "quote that will be questioned.",
                "CotizaT does not manage licensing, but the document carries your "
                "business details, your ABN and the terms you configure, and the "
                "catalog speaks the trade vocabulary used on site: plasterboard, "
                "cornice, skirting, Colorbond, brick veneer, slab on ground.",
            ],
        ),
        (
            "Metric, and priced from the trade up",
            [
                "Australia is metric, so there is no conversion to worry about: "
                "square metres, linear metres and cubic metres are what the "
                "catalog already uses. The difference with the northern hemisphere "
                "is the construction itself —brick veneer, suspended slab, "
                "Colorbond roofing— and the resources that go with it.",
                "Each line item arrives with its unit price analysis: materials with "
                "waste, labour at the employer cost of the trade with its "
                "productivity rate, and plant where plant is needed. That breakdown "
                "is what turns a rate per square metre into a price you can defend.",
            ],
        ),
    ],
    # ── Canadá ───────────────────────────────────────────────────────────
    "CA": [
        (
            "GST, HST and QST: the tax depends on the province",
            [
                "Canada has a federal goods and services tax of 5 %, but what a "
                "contractor charges depends on where the work is. Ontario uses the "
                "13 % harmonised sales tax; Nova Scotia, New Brunswick, Newfoundland "
                "and Labrador and Prince Edward Island use 15 %; Alberta, British "
                "Columbia, Saskatchewan and Manitoba charge 5 % GST, with a "
                "provincial tax separate in BC, Saskatchewan and Manitoba. Quebec has "
                "its own QST alongside the GST.",
                "That is why the app asks you to configure the rate instead of "
                "showing a national figure. The estimate states the treatment it was "
                "priced with, and the PDF does not pretend that a job in Toronto and "
                "a job in Calgary carry the same tax.",
            ],
        ),
        (
            "Holdback and progress draws",
            [
                "Construction lien legislation is provincial, and almost all of it "
                "works the same way: the owner or the general contractor holds back a "
                "percentage of each payment —commonly 10 %— for a period after "
                "substantial performance, so subcontractors can be paid if a lien is "
                "registered. The holdback is released later, not on the final invoice.",
                "Progress draws work with it: the job is measured in stages, each "
                "draw is certified against what was built, and the holdback is "
                "tracked separately. CotizaT keeps sections, quantities and totals per "
                "stage, so a draw is a copy of a structure that already exists.",
            ],
        ),
        (
            "Change orders and CCDC contracts",
            [
                "Canadian construction runs on standard contracts —the CCDC family "
                "in the institutional and commercial world— and on change orders and "
                "change directives that must be in writing before the work proceeds. "
                "The same job can have ten change orders, and the tenth is the one "
                "someone forgets to price.",
                "Every revision in CotizaT is a version: previous total, new total "
                "and what moved. That is the record the change order refers to when "
                "the client asks why the final number is not the one in the original "
                "estimate.",
            ],
        ),
        (
            "Metric, and two official languages",
            [
                "Canada measures in metric like Australia and the United Kingdom, so "
                "there is no imperial conversion outside the United States. The "
                "vocabulary is the North American one —drywall, baseboard, joist, "
                "concrete— with British spelling, which is exactly how Canadian "
                "construction documents read.",
                "The product's interface and documents are in English and Spanish "
                "today; French for Quebec is a separate job and is not claimed here. "
                "What the catalog does have is the trade terminology a Canadian crew "
                "uses, with its own price base and its own tax rules.",
            ],
        ),
        (
            "What the estimate has to show a Canadian client",
            [
                "Scope by section, quantities, unit prices, the tax treatment by "
                "province, the validity of the price and what is excluded. Add the "
                "holdback if the contract has one and the schedule of values if the "
                "job is billed in draws.",
                "Behind each line item is the unit price analysis: materials with "
                "waste, labour at the employer cost of the trade with its "
                "productivity rate, and equipment where it applies. That breakdown "
                "never appears on the client's PDF; it exists so the number in the "
                "PDF can be defended.",
            ],
        ),
    ],
    # ── Irlanda ──────────────────────────────────────────────────────────
    "IE": [
        (
            "VAT at 13.5 % on construction services, 23 % on materials",
            [
                "Ireland charges the reduced 13.5 % rate on construction services "
                "and the standard 23 % on most goods, which is why an Irish "
                "contractor has to be careful with a job that mixes both. When the "
                "value of the goods in a supply reaches two thirds or more of the "
                "total, the whole supply can be standard-rated —a rule that changes "
                "the tax of the entire invoice, not just the materials line.",
                "The treatment is configured per estimate. CotizaT prints the "
                "treatment it was priced with and does not decide your VAT; the "
                "document is commercial and the VAT invoice comes from your "
                "accounting system.",
            ],
        ),
        (
            "RCT: the Irish deduction a UK-trained builder often misses",
            [
                "Relevant Contracts Tax works like the British CIS but is not the "
                "same. A principal contractor deducts from payments to a "
                "subcontractor at a rate Revenue sets from the subcontractor's own "
                "tax record —0 % for three years clean, 20 % as the registered "
                "standard, 35 % where the record is poor or there is no "
                "registration— and confirms in the deduction authorisation it "
                "issues for every single payment in ROS.",
                "And here is the part the UK-trained builder misses: the base is "
                "the whole VAT-exclusive payment, materials included. CIS strips "
                "the materials out and deducts on labour only; RCT does not. "
                "CotizaT applies the rate you were authorised to the full payment "
                "and shows the deduction and the net on the document; the ROS "
                "notifications and the return stay where they belong, with the "
                "principal.",
            ],
        ),
        (
            "Tender, bill of quantities and snag list",
            [
                "Irish work splits between private refurbishment and tendered work. "
                "The tendered side speaks in bills of quantities, measured items and "
                "a priced tender return; the private side speaks in a quotation, a "
                "deposit and a snag list at handover.",
                "Both fit the same structure: sections, line items with quantity and "
                "unit, prices and a total. The bill of quantities is a longer version "
                "of the same document, and the snag list is a section at the end of "
                "the job, not a separate spreadsheet.",
            ],
        ),
        (
            "Metric, euro and British trade vocabulary",
            [
                "Ireland measures and prices in metric and works in euro, and shares "
                "most of the British trade vocabulary: skirting, plasterboard, "
                "worktop, socket outlet, consumer unit, kerb. The catalog uses it, "
                "because a Dublin contractor reading 'baseboard' hears an American "
                "software.",
                "What does not carry over from the United Kingdom is the tax: VAT "
                "rates, RCT instead of CIS and a different registration number "
                "(VAT number and, for RCT, the tax reference). Each one is configured "
                "per market, not inherited.",
            ],
        ),
        (
            "What the estimate has to show an Irish client",
            [
                "Scope by section, quantities, unit prices, the VAT treatment, the "
                "validity of the price and what is excluded. For a business client, "
                "the notice that RCT applies to the payment; for a private "
                "householder, a clear gross total with the VAT element stated.",
                "Behind each line item is its unit price analysis —materials with "
                "waste, labour at the employer cost of the trade with productivity, "
                "plant where it exists— and that breakdown stays in the workspace. "
                "The client receives a document, not a login.",
            ],
        ),
    ],
}

FAQ: dict[str, list[dict[str, str]]] = {
    "US": [
        {
            "q": "Which sales tax rate should I apply?",
            "a": (
                "You configure it: there is no national rate, and states, counties "
                "and cities set their own. Some states tax materials but not the "
                "labour to install them, and some treat the contractor as the final "
                "consumer. CotizaT applies the rate you set per estimate."
            ),
        },
        {
            "q": "Does it handle imperial measurements?",
            "a": (
                "Prices yes, quantities not yet. The US price library is built from "
                "American sources in their own units (cubic yards, square feet, "
                "gallons, pounds) with the price range kept. Feet-and-inches "
                "quantity entry is in development; today quantities are worked in "
                "the catalog's metric units."
            ),
        },
    ],
    "AU": [
        {
            "q": "Does it handle prime cost and provisional sums?",
            "a": (
                "Yes. Both are ordinary line items with their own description, so "
                "the quote shows what is fixed and what will be settled later "
                "instead of hiding an allowance inside a lump sum."
            ),
        },
        {
            "q": "Does it issue a tax invoice with my ABN?",
            "a": (
                "It produces the quote and the payment request with your business "
                "details and ABN. The tax invoice, with its own requirements, comes "
                "from your accounting system."
            ),
        },
    ],
    "CA": [
        {
            "q": "Does it apply GST or HST automatically?",
            "a": (
                "You choose the rate for the province the work is in —5 % GST, 13 % "
                "HST in Ontario, 15 % in the Atlantic provinces— and the estimate "
                "states which treatment it was priced with."
            ),
        },
        {
            "q": "Does it handle holdback on progress draws?",
            "a": (
                "The estimate and the payment requests are organised by section and "
                "stage, which is the structure a draw is certified against. The "
                "holdback percentage is set by provincial lien legislation; the app "
                "does not decide it for you."
            ),
        },
    ],
    "IE": [
        {
            "q": "Does it apply RCT deductions?",
            "a": (
                "Yes. The three rates Revenue sets —0 %, 20 % and 35 %— are "
                "applied to the full VAT-exclusive payment, materials included: "
                "unlike the British CIS, RCT is not a labour-only deduction. The "
                "contract and payment notifications in ROS, and the return, "
                "remain yours to file."
            ),
        },
        {
            "q": "Is it the English version with Irish tax on top?",
            "a": (
                "No. Ireland has its own market in the product: euro, Irish VAT "
                "treatment, RCT instead of CIS and the trade vocabulary shared with "
                "the United Kingdom but not the tax."
            ),
        },
    ],
}


def cuerpo_landing(codigo: str) -> list[tuple[str, list[str]]]:
    """Bloques de la landing del mercado; vacío si no hay contenido propio."""
    return CUERPO.get(str(codigo or "").strip().upper(), [])


def faq_landing(codigo: str) -> list[dict[str, str]]:
    return FAQ.get(str(codigo or "").strip().upper(), [])
