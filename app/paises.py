"""Datos de países para la landing adaptativa (LatAm + España).

Un solo lugar con la verdad sobre cada mercado hispano: bandera, moneda,
IVA de referencia, etiqueta del ID fiscal y vocabulario local de obra.

No es fiscalidad normativa: el IVA que se muestra es la alícuota general
de referencia (no un asesoramiento tributario) y solo sirve para que la
landing hable el idioma del visitante. La configuración real del IVA sigue
siendo libre en /configuracion.

NOTA: El catálogo mantiene sus precios en USD como referencia regional;
la moneda_local aquí es solo informativa para el selector. España es la
excepción con mercado propio en EUR: sus recursos tienen referencias
nacionales en esa moneda (ver ``tools/generar_matriz_precios_espana.py``).

Separadores de miles y decimales
--------------------------------
Se eligen por **mercado**, nunca por idioma, y siguen el uso documental
real de cada país (lo que ve el cliente en un presupuesto o una factura),
no la norma literaria. donde la autoridad fiscal fija un formato para la
facturación electrónica, ese formato manda.

======  =============  ====================================================
País    Formato        Criterio
======  =============  ====================================================
ES, CO, ``1.234,56``   RAE y uso bancario: coma decimal.
CL, AR,
UY, PY,
BO, CR,
VE, PE
MX, EC, ``1,234.56``   México y Centroamérica usan punto (RAE); Ecuador
PA, DO,                 además lo fija el SRI (ficha técnica de
GT, HN,                 comprobantes electrónicos, §8.17) y está dolarizado.
NI, SV
US, GB, ``1,234.56``   Formato anglosajón.
AU, CA,
IE
======  =============  ====================================================

Dos casos que parecen errores y no lo son:

* **Venezuela usa coma** («Bs. 5.355,5058» en el BCV) aunque la RAE la
  liste con punto: manda la práctica institucional del banco central, que
  es la que aparece en cada factura al tipo de cambio oficial.
* **Perú usa coma** («3,4160» en el BCRP) aunque el PDT de SUNAT configure
  el punto internamente: el punto es el formato del XML, no el del
  documento que ve el cliente. La Ley 23560 y el manual peruano del SI
  declaran expresamente erróneo el punto decimal.
"""

from __future__ import annotations
from functools import lru_cache

# Cada entrada es lo que la landing necesita para personalizarse.
# `vocab` es la línea corta que aparece en el banner del catálogo:
# 5 términos que cambian por país (concreto/hormigón, friso/revoque, etc.).
PAISES: dict[str, dict] = {
    "VE": {
        "codigo": "VE",
        "nombre": "Venezuela",
        "nombre_en": "Venezuela",
        "gentilicio": "venezolano",
        "bandera": "🇻🇪",
        "moneda": "USD",
        "moneda_local": "VES",
        "simbolo_local": "Bs",
        "iva": 16,
        "id_fiscal": "RIF",
        "vocab": "concreto, friso, cielo raso, rodapié, plomero",
        "vocab_en": "concrete, trowel plaster, suspended ceiling, baseboard, plumber",
        "id_fiscal_placeholder": "J-12345678-9",
        "telefono_ejemplo": "+58 412 000 0000",
        "razon_social_ejemplo": "C.A.",
        "ciudad_ejemplo": "Caracas",
        "mercado": "venezolano",
        "locale": "es-VE",
        "idioma": "es",
        "etiqueta_impuesto": "I.V.A.",
        "etiqueta_impuesto_en": "VAT",
        "separador_miles": ".",
        "separador_decimal": ",",
        "formato_fecha": "DD/MM/YYYY",
        "sistema_unidades": "metrico",
    },
    "CO": {
        "codigo": "CO",
        "nombre": "Colombia",
        "nombre_en": "Colombia",
        "gentilicio": "colombiano",
        "bandera": "🇨🇴",
        "moneda": "COP",
        "moneda_local": "COP",
        "simbolo_local": "$",
        "iva": 19,
        "id_fiscal": "NIT",
        "vocab": "concreto, pañete, cielo raso, guardaescoba, plomero",
        "vocab_en": "concrete, skim coat, suspended ceiling, baseboard, plumber",
        "id_fiscal_placeholder": "900.123.456-7",
        "telefono_ejemplo": "+57 300 000 0000",
        "razon_social_ejemplo": "S.A.S.",
        "ciudad_ejemplo": "Bogotá",
        "mercado": "colombiano",
        "locale": "es-CO",
        "idioma": "es",
        "etiqueta_impuesto": "I.V.A.",
        "etiqueta_impuesto_en": "VAT",
        "separador_miles": ".",
        "separador_decimal": ",",
        "formato_fecha": "DD/MM/YYYY",
        "sistema_unidades": "metrico",
    },
    "MX": {
        "codigo": "MX",
        "nombre": "México",
        "nombre_en": "Mexico",
        "gentilicio": "mexicano",
        "bandera": "🇲🇽",
        "moneda": "MXN",
        "moneda_local": "MXN",
        "simbolo_local": "$",
        "iva": 16,
        "id_fiscal": "RFC",
        "vocab": "concreto, aplanado, plafón, zoclo, plomero",
        "vocab_en": "concrete, skim coat, suspended ceiling, baseboard, plumber",
        "id_fiscal_placeholder": "AAA010101AAA",
        "telefono_ejemplo": "+52 55 0000 0000",
        "razon_social_ejemplo": "S.A. de C.V.",
        "ciudad_ejemplo": "Ciudad de México",
        "mercado": "mexicano",
        "locale": "es-MX",
        "idioma": "es",
        "etiqueta_impuesto": "I.V.A.",
        "etiqueta_impuesto_en": "VAT",
        "separador_miles": ",",
        "separador_decimal": ".",
        "formato_fecha": "DD/MM/YYYY",
        "sistema_unidades": "metrico",
    },
    "PE": {
        "codigo": "PE",
        "nombre": "Perú",
        "nombre_en": "Peru",
        "gentilicio": "peruano",
        "bandera": "🇵🇪",
        "moneda": "PEN",
        "moneda_local": "PEN",
        "simbolo_local": "S/",
        "iva": 18,
        "id_fiscal": "RUC",
        "vocab": "concreto, tarrajeo, cielo raso, zócalo, gasfitero",
        "vocab_en": "concrete, plastering, suspended ceiling, baseboard, gas fitter",
        "id_fiscal_placeholder": "20123456789",
        "telefono_ejemplo": "+51 900 000 000",
        "razon_social_ejemplo": "S.A.C.",
        "ciudad_ejemplo": "Lima",
        "mercado": "peruano",
        "locale": "es-PE",
        "idioma": "es",
        "etiqueta_impuesto": "IGV",
        "etiqueta_impuesto_en": "IGV",
        "separador_miles": ".",
        "separador_decimal": ",",
        "formato_fecha": "DD/MM/YYYY",
        "sistema_unidades": "metrico",
    },
    "CL": {
        "codigo": "CL",
        "nombre": "Chile",
        "nombre_en": "Chile",
        "gentilicio": "chileno",
        "bandera": "🇨🇱",
        "moneda": "CLP",
        "moneda_local": "CLP",
        "simbolo_local": "$",
        "iva": 19,
        "id_fiscal": "RUT",
        "vocab": "hormigón, estuco, cielo falso, guardapolvo, gasfíter",
        "vocab_en": "concrete, plaster, suspended ceiling, baseboard, gas fitter",
        "id_fiscal_placeholder": "76.123.456-K",
        "telefono_ejemplo": "+56 9 0000 0000",
        "razon_social_ejemplo": "SpA",
        "ciudad_ejemplo": "Santiago",
        "mercado": "chileno",
        "locale": "es-CL",
        "idioma": "es",
        "etiqueta_impuesto": "I.V.A.",
        "etiqueta_impuesto_en": "VAT",
        "separador_miles": ".",
        "separador_decimal": ",",
        "formato_fecha": "DD/MM/YYYY",
        "sistema_unidades": "metrico",
    },
    "AR": {
        "codigo": "AR",
        "nombre": "Argentina",
        "nombre_en": "Argentina",
        "gentilicio": "argentino",
        "bandera": "🇦🇷",
        "moneda": "ARS",
        "moneda_local": "ARS",
        "simbolo_local": "$",
        "iva": 21,
        "id_fiscal": "CUIT",
        "vocab": "hormigón, revoque, cielorraso, zócalo, plomero",
        "vocab_en": "concrete, rendering, suspended ceiling, baseboard, plumber",
        "id_fiscal_placeholder": "20-12345678-9",
        "telefono_ejemplo": "+54 11 0000 0000",
        "razon_social_ejemplo": "S.R.L.",
        "ciudad_ejemplo": "Buenos Aires",
        "mercado": "argentino",
        "locale": "es-AR",
        "idioma": "es",
        "etiqueta_impuesto": "I.V.A.",
        "etiqueta_impuesto_en": "VAT",
        "separador_miles": ".",
        "separador_decimal": ",",
        "formato_fecha": "DD/MM/YYYY",
        "sistema_unidades": "metrico",
    },
    "EC": {
        "codigo": "EC",
        "nombre": "Ecuador",
        "nombre_en": "Ecuador",
        "gentilicio": "ecuatoriano",
        "bandera": "🇪🇨",
        "moneda": "USD",
        "moneda_local": "USD",
        "simbolo_local": "$",
        "iva": 15,
        "id_fiscal": "RUC",
        "vocab": "hormigón, enlucido, tumbado, barredera, gasfitero",
        "vocab_en": "concrete, render, suspended ceiling, baseboard, gas fitter",
        "id_fiscal_placeholder": "0991234567001",
        "telefono_ejemplo": "+593 99 000 0000",
        "razon_social_ejemplo": "S.A.",
        "ciudad_ejemplo": "Quito",
        "mercado": "ecuatoriano",
        "locale": "es-EC",
        "idioma": "es",
        "etiqueta_impuesto": "I.V.A.",
        "etiqueta_impuesto_en": "VAT",
        "separador_miles": ",",
        "separador_decimal": ".",
        "formato_fecha": "DD/MM/YYYY",
        "sistema_unidades": "metrico",
    },
    "DO": {
        "codigo": "DO",
        "nombre": "República Dominicana",
        "nombre_en": "the Dominican Republic",
        "gentilicio": "dominicano",
        "bandera": "🇩🇴",
        "moneda": "DOP",
        "moneda_local": "DOP",
        "simbolo_local": "RD$",
        "iva": 18,
        "id_fiscal": "RNC",
        "vocab": "hormigón, pañete, plafón, zócalo, plomero",
        "vocab_en": "concrete, skim coat, suspended ceiling, baseboard, plumber",
        "id_fiscal_placeholder": "130-12345-6",
        "telefono_ejemplo": "+1 809 000 0000",
        "razon_social_ejemplo": "S.R.L.",
        "ciudad_ejemplo": "Santo Domingo",
        "mercado": "dominicano",
        "locale": "es-DO",
        "idioma": "es",
        "etiqueta_impuesto": "ITBIS",
        "etiqueta_impuesto_en": "ITBIS",
        "separador_miles": ",",
        "separador_decimal": ".",
        "formato_fecha": "DD/MM/YYYY",
        "sistema_unidades": "metrico",
    },
    "UY": {
        "codigo": "UY",
        "nombre": "Uruguay",
        "nombre_en": "Uruguay",
        "gentilicio": "uruguayo",
        "bandera": "🇺🇾",
        "moneda": "UYU",
        "moneda_local": "UYU",
        "simbolo_local": "$U",
        "iva": 22,
        "id_fiscal": "RUT",
        "vocab": "hormigón, revoque, cielorraso, zócalo, sanitario",
        "vocab_en": "concrete, rendering, suspended ceiling, baseboard, sanitary fitter",
        "id_fiscal_placeholder": "211234567812",
        "telefono_ejemplo": "+598 99 000 000",
        "razon_social_ejemplo": "S.A.",
        "ciudad_ejemplo": "Montevideo",
        "mercado": "uruguayo",
        "locale": "es-UY",
        "idioma": "es",
        "etiqueta_impuesto": "I.V.A.",
        "etiqueta_impuesto_en": "VAT",
        "separador_miles": ".",
        "separador_decimal": ",",
        "formato_fecha": "DD/MM/YYYY",
        "sistema_unidades": "metrico",
    },
    "PY": {
        "codigo": "PY",
        "nombre": "Paraguay",
        "nombre_en": "Paraguay",
        "gentilicio": "paraguayo",
        "bandera": "🇵🇾",
        "moneda": "PYG",
        "moneda_local": "PYG",
        "simbolo_local": "₲",
        "iva": 10,
        "id_fiscal": "RUC",
        "vocab": "hormigón, revoque, cielorraso, zócalo, plomero",
        "vocab_en": "concrete, rendering, suspended ceiling, baseboard, plumber",
        "id_fiscal_placeholder": "80012345-6",
        "telefono_ejemplo": "+595 21 000 000",
        "razon_social_ejemplo": "S.A.",
        "ciudad_ejemplo": "Asunción",
        "mercado": "paraguayo",
        "locale": "es-PY",
        "idioma": "es",
        "etiqueta_impuesto": "I.V.A.",
        "etiqueta_impuesto_en": "VAT",
        "separador_miles": ".",
        "separador_decimal": ",",
        "formato_fecha": "DD/MM/YYYY",
        "sistema_unidades": "metrico",
    },
    "BO": {
        "codigo": "BO",
        "nombre": "Bolivia",
        "nombre_en": "Bolivia",
        "gentilicio": "boliviano",
        "bandera": "🇧🇴",
        "moneda": "BOB",
        "moneda_local": "BOB",
        "simbolo_local": "Bs",
        "iva": 13,
        "id_fiscal": "NIT",
        "vocab": "hormigón, revoque, cielo falso, zócalo, plomero",
        "vocab_en": "concrete, rendering, suspended ceiling, baseboard, plumber",
        "id_fiscal_placeholder": "1020304050",
        "telefono_ejemplo": "+591 2 000 0000",
        "razon_social_ejemplo": "S.R.L.",
        "ciudad_ejemplo": "La Paz",
        "mercado": "boliviano",
        "locale": "es-BO",
        "idioma": "es",
        "etiqueta_impuesto": "I.V.A.",
        "etiqueta_impuesto_en": "VAT",
        "separador_miles": ".",
        "separador_decimal": ",",
        "formato_fecha": "DD/MM/YYYY",
        "sistema_unidades": "metrico",
    },
    "PA": {
        "codigo": "PA",
        "nombre": "Panamá",
        "nombre_en": "Panama",
        "gentilicio": "panameño",
        "bandera": "🇵🇦",
        "moneda": "USD",
        "moneda_local": "PAB",
        "simbolo_local": "B/.",
        "iva": 7,
        "id_fiscal": "RUC",
        "vocab": "concreto, repello, cielo raso, zócalo, plomero",
        "vocab_en": "concrete, render, suspended ceiling, baseboard, plumber",
        "id_fiscal_placeholder": "1234567-1-123456",
        "telefono_ejemplo": "+507 6000 0000",
        "razon_social_ejemplo": "S.A.",
        "ciudad_ejemplo": "Ciudad de Panamá",
        "mercado": "panameño",
        "locale": "es-PA",
        "idioma": "es",
        "etiqueta_impuesto": "ITBMS",
        "etiqueta_impuesto_en": "ITBMS",
        "separador_miles": ",",
        "separador_decimal": ".",
        "formato_fecha": "DD/MM/YYYY",
        "sistema_unidades": "metrico",
    },
    "CR": {
        "codigo": "CR",
        "nombre": "Costa Rica",
        "nombre_en": "Costa Rica",
        "gentilicio": "costarricense",
        "bandera": "🇨🇷",
        "moneda": "CRC",
        "moneda_local": "CRC",
        "simbolo_local": "₡",
        "iva": 13,
        "id_fiscal": "NITE",
        "vocab": "concreto, repello, cielo raso, rodapié, fontanero",
        "vocab_en": "concrete, render, suspended ceiling, baseboard, plumber",
        "id_fiscal_placeholder": "3-101-123456",
        "telefono_ejemplo": "+506 8888 0000",
        "razon_social_ejemplo": "S.A.",
        "ciudad_ejemplo": "San José",
        "mercado": "costarricense",
        "locale": "es-CR",
        "idioma": "es",
        "etiqueta_impuesto": "I.V.A.",
        "etiqueta_impuesto_en": "VAT",
        "separador_miles": ".",
        "separador_decimal": ",",
        "formato_fecha": "DD/MM/YYYY",
        "sistema_unidades": "metrico",
    },
    "GT": {
        "codigo": "GT",
        "nombre": "Guatemala",
        "nombre_en": "Guatemala",
        "gentilicio": "guatemalteco",
        "bandera": "🇬🇹",
        "moneda": "GTQ",
        "moneda_local": "GTQ",
        "simbolo_local": "Q",
        "iva": 12,
        "id_fiscal": "NIT",
        "vocab": "concreto, repello, cielo falso, zócalo, fontanero",
        "vocab_en": "concrete, render, suspended ceiling, baseboard, plumber",
        "id_fiscal_placeholder": "1234567-8",
        "telefono_ejemplo": "+502 5555 0000",
        "razon_social_ejemplo": "S.A.",
        "ciudad_ejemplo": "Ciudad de Guatemala",
        "mercado": "guatemalteco",
        "locale": "es-GT",
        "idioma": "es",
        "etiqueta_impuesto": "I.V.A.",
        "etiqueta_impuesto_en": "VAT",
        "separador_miles": ",",
        "separador_decimal": ".",
        "formato_fecha": "DD/MM/YYYY",
        "sistema_unidades": "metrico",
    },
    "HN": {
        "codigo": "HN",
        "nombre": "Honduras",
        "nombre_en": "Honduras",
        "gentilicio": "hondureño",
        "bandera": "🇭🇳",
        "moneda": "HNL",
        "moneda_local": "HNL",
        "simbolo_local": "L",
        "iva": 15,
        "id_fiscal": "RTN",
        "vocab": "concreto, repello, cielo falso, zócalo, fontanero",
        "vocab_en": "concrete, render, suspended ceiling, baseboard, plumber",
        "id_fiscal_placeholder": "08011999123456",
        "telefono_ejemplo": "+504 9999 0000",
        "razon_social_ejemplo": "S.A.",
        "ciudad_ejemplo": "Tegucigalpa",
        "mercado": "hondureño",
        "locale": "es-HN",
        "idioma": "es",
        "etiqueta_impuesto": "ISV",
        "etiqueta_impuesto_en": "ISV",
        "separador_miles": ",",
        "separador_decimal": ".",
        "formato_fecha": "DD/MM/YYYY",
        "sistema_unidades": "metrico",
    },
    "SV": {
        "codigo": "SV",
        "nombre": "El Salvador",
        "nombre_en": "El Salvador",
        "gentilicio": "salvadoreño",
        "bandera": "🇸🇻",
        "moneda": "USD",
        "moneda_local": "USD",
        "simbolo_local": "$",
        "iva": 13,
        "id_fiscal": "NIT",
        "vocab": "concreto, repello, cielo falso, zócalo, fontanero",
        "vocab_en": "concrete, render, suspended ceiling, baseboard, plumber",
        "id_fiscal_placeholder": "0614-123456-789-0",
        "telefono_ejemplo": "+503 7000 0000",
        "razon_social_ejemplo": "S.A. de C.V.",
        "ciudad_ejemplo": "San Salvador",
        "mercado": "salvadoreño",
        "locale": "es-SV",
        "idioma": "es",
        "etiqueta_impuesto": "I.V.A.",
        "etiqueta_impuesto_en": "VAT",
        "separador_miles": ",",
        "separador_decimal": ".",
        "formato_fecha": "DD/MM/YYYY",
        "sistema_unidades": "metrico",
    },
    "NI": {
        "codigo": "NI",
        "nombre": "Nicaragua",
        "nombre_en": "Nicaragua",
        "gentilicio": "nicaragüense",
        "bandera": "🇳🇮",
        "moneda": "NIO",
        "moneda_local": "NIO",
        "simbolo_local": "C$",
        "iva": 15,
        "id_fiscal": "RUC",
        "vocab": "concreto, repello, cielo raso, zócalo, fontanero",
        "vocab_en": "concrete, render, suspended ceiling, baseboard, plumber",
        "id_fiscal_placeholder": "J0310000001234",
        "telefono_ejemplo": "+505 8888 0000",
        "razon_social_ejemplo": "S.A.",
        "ciudad_ejemplo": "Managua",
        "mercado": "nicaragüense",
        "locale": "es-NI",
        "idioma": "es",
        "etiqueta_impuesto": "I.V.A.",
        "etiqueta_impuesto_en": "VAT",
        "separador_miles": ",",
        "separador_decimal": ".",
        "formato_fecha": "DD/MM/YYYY",
        "sistema_unidades": "metrico",
    },
    # Primer mercado fuera de LatAm: moneda EUR, IVA 21 % y NIF. El catálogo
    # base sigue en USD como referencia; los recursos tienen referencias
    # nacionales en EUR (matriz precios_recursos_espana.csv) y la
    # terminología se adapta al mostrar con el glosario VE→ES.
    "ES": {
        "codigo": "ES",
        "nombre": "España",
        "nombre_en": "Spain",
        "gentilicio": "español",
        "bandera": "🇪🇸",
        "moneda": "EUR",
        "moneda_local": "EUR",
        "simbolo_local": "€",
        "iva": 21,
        "id_fiscal": "NIF",
        "vocab": "hormigón, pladur, falso techo, alicatado, fontanero",
        "vocab_en": "concrete, plasterboard, suspended ceiling, wall tiling, plumber",
        "id_fiscal_placeholder": "B12345678",
        "telefono_ejemplo": "+34 600 000 000",
        "razon_social_ejemplo": "S.L.",
        "ciudad_ejemplo": "Madrid",
        "mercado": "español",
        "locale": "es-ES",
        "idioma": "es",
        "etiqueta_impuesto": "I.V.A.",
        "etiqueta_impuesto_en": "VAT",
        "separador_miles": ".",
        "separador_decimal": ",",
        "formato_fecha": "DD/MM/YYYY",
        "sistema_unidades": "metrico",
    },
    "US": {
        "codigo": "US",
        "nombre": "Estados Unidos",
        "nombre_en": "the United States",
        "gentilicio": "estadounidense",
        "bandera": "🇺🇸",
        "moneda": "USD",
        "moneda_local": "USD",
        "simbolo_local": "$",
        "iva": 7.0,
        "id_fiscal": "EIN",
        "vocab": "drywall, concrete, ceiling, baseboard, plumber",
        "vocab_en": "drywall, concrete, ceiling, baseboard, plumber",
        "id_fiscal_placeholder": "12-3456789",
        "telefono_ejemplo": "+1 202 555 0000",
        "razon_social_ejemplo": "LLC",
        "ciudad_ejemplo": "Miami",
        "mercado": "estadounidense",
        "locale": "en-US",
        "idioma": "en",
        "etiqueta_impuesto": "Sales tax",
        "etiqueta_impuesto_en": "Sales tax",
        "separador_miles": ",",
        "separador_decimal": ".",
        "formato_fecha": "MM/DD/YYYY",
        "sistema_unidades": "imperial",
    },
    "GB": {
        "codigo": "GB",
        "nombre": "Reino Unido",
        "nombre_en": "the United Kingdom",
        "gentilicio": "británico",
        "bandera": "🇬🇧",
        "moneda": "GBP",
        "moneda_local": "GBP",
        "simbolo_local": "£",
        "iva": 20,
        "id_fiscal": "VAT registration number",
        "vocab": "plasterboard, concrete, ceiling, skirting, plumber",
        "vocab_en": "plasterboard, concrete, ceiling, skirting, plumber",
        "id_fiscal_placeholder": "GB123456789",
        "telefono_ejemplo": "+44 20 7946 0000",
        "razon_social_ejemplo": "Ltd",
        "ciudad_ejemplo": "London",
        "mercado": "británico",
        "locale": "en-GB",
        "idioma": "en",
        "etiqueta_impuesto": "VAT",
        "etiqueta_impuesto_en": "VAT",
        "separador_miles": ",",
        "separador_decimal": ".",
        "formato_fecha": "DD/MM/YYYY",
        "sistema_unidades": "metrico",
    },
    "AU": {
        "codigo": "AU",
        "nombre": "Australia",
        "nombre_en": "Australia",
        "gentilicio": "australiano",
        "bandera": "🇦🇺",
        "moneda": "AUD",
        "moneda_local": "AUD",
        "simbolo_local": "A$",
        "iva": 10,
        "id_fiscal": "ABN",
        "vocab": "plasterboard, concrete, ceiling, skirting, plumber",
        "vocab_en": "plasterboard, concrete, ceiling, skirting, plumber",
        "id_fiscal_placeholder": "12 345 678 901",
        "telefono_ejemplo": "+61 2 5550 0000",
        "razon_social_ejemplo": "Pty Ltd",
        "ciudad_ejemplo": "Sydney",
        "mercado": "australiano",
        "locale": "en-AU",
        "idioma": "en",
        "etiqueta_impuesto": "GST",
        "etiqueta_impuesto_en": "GST",
        "separador_miles": ",",
        "separador_decimal": ".",
        "formato_fecha": "DD/MM/YYYY",
        "sistema_unidades": "metrico",
    },
    "CA": {
        "codigo": "CA",
        "nombre": "Canadá",
        "nombre_en": "Canada",
        "gentilicio": "canadiense",
        "bandera": "🇨🇦",
        "moneda": "CAD",
        "moneda_local": "CAD",
        "simbolo_local": "C$",
        "iva": 5,
        "id_fiscal": "BN",
        "vocab": "drywall, concrete, ceiling, baseboard, plumber",
        "vocab_en": "drywall, concrete, ceiling, baseboard, plumber",
        "id_fiscal_placeholder": "123456789 RT 0001",
        "telefono_ejemplo": "+1 416 555 0000",
        "razon_social_ejemplo": "Inc.",
        "ciudad_ejemplo": "Toronto",
        "mercado": "canadiense",
        "locale": "en-CA",
        "idioma": "en",
        "etiqueta_impuesto": "GST/HST",
        "etiqueta_impuesto_en": "GST/HST",
        "separador_miles": ",",
        "separador_decimal": ".",
        "formato_fecha": "DD/MM/YYYY",
        "sistema_unidades": "metrico",
    },
    "IE": {
        "codigo": "IE",
        "nombre": "Irlanda",
        "nombre_en": "Ireland",
        "gentilicio": "irlandés",
        "bandera": "🇮🇪",
        "moneda": "EUR",
        "moneda_local": "EUR",
        "simbolo_local": "€",
        "iva": 13.5,
        "id_fiscal": "VAT number",
        "vocab": "plasterboard, concrete, ceiling, skirting, plumber",
        "vocab_en": "plasterboard, concrete, ceiling, skirting, plumber",
        "id_fiscal_placeholder": "IE1234567FA",
        "telefono_ejemplo": "+353 1 555 0000",
        "razon_social_ejemplo": "Ltd",
        "ciudad_ejemplo": "Dublin",
        "mercado": "irlandés",
        "locale": "en-IE",
        "idioma": "en",
        "etiqueta_impuesto": "VAT",
        "etiqueta_impuesto_en": "VAT",
        "separador_miles": ",",
        "separador_decimal": ".",
        "formato_fecha": "DD/MM/YYYY",
        "sistema_unidades": "metrico",
    },
}

# Orden en que aparecen en el selector: todos los países disponibles.
# España va primero porque es un mercado prioritario (EUR, NIF, IVA 21 %
# y referencias nacionales propias) y le sigue Latinoamérica. Cada país
# tiene catálogo de precios, moneda, IVA, ID fiscal y vocabulario propios;
# por eso el selector es explícito y debe elegirse correctamente antes de
# cotizar.
ORDEN_SELECTOR = [
    "ES",
    "VE", "CO", "MX", "EC", "PE", "CL", "AR",
    "DO", "UY", "PY", "BO", "PA", "CR", "GT",
    "HN", "SV", "NI",
    # Mercados de habla inglesa: idioma, moneda, impuesto, formato de número
    # y fecha, sistema de unidades y terminología propios de cada uno.
    "US", "GB", "AU", "CA", "IE",
]

# Genérico para cuando no hay país seleccionado (SEO, primera visita).
# Antes decía "Latinoamérica" (incl. mercado "latinoamericano"), pero desde
# que España es un mercado real con EUR/NIF/Vocabulario propio, decir
# "Latinoamérica" invisibilizaba a España. Ahora se enuncia el mercado
# completo: "España y Latinoamérica", gentilicio "iberoamericano".
PAIS_GENERICO: dict = {
    "codigo": "",
    "nombre": "España y Latinoamérica",
    "nombre_en": "Spain and Latin America",
    "gentilicio": "iberoamericano",
    "bandera": "🌎",
    "moneda": "USD",
    "moneda_local": "USD",
    "simbolo_local": "$",
    "iva": 16,
    "id_fiscal": "ID fiscal",
    "vocab": "concreto, friso, cielo raso, rodapié, plomero",
    # El bloque genérico es venezolano en español, así que en inglés se
    # traduce ese mismo vocabulario, no el de otro mercado.
    "vocab_en": "concrete, trowel plaster, suspended ceiling, baseboard, plumber",
    "mercado": "iberoamericano",
    "id_fiscal_placeholder": "RIF, NIT, RUC, RFC…",
    "telefono_ejemplo": "+00 000 000 0000",
    "razon_social_ejemplo": "",
    "ciudad_ejemplo": "",
    "locale": "",
    "idioma": "es",
    "etiqueta_impuesto": "I.V.A.",
    "etiqueta_impuesto_en": "VAT",
    "separador_miles": ".",
    "separador_decimal": ",",
    "formato_fecha": "DD/MM/YYYY",
    "sistema_unidades": "metrico",

}

# ---------------------------------------------------------------------------
# Resolución de mercados
# ---------------------------------------------------------------------------
# Un mercado se puede pedir de cuatro formas: por locale («en-GB»), por
# código de país («GB», «mx»), por nombre («Reino Unido») o solo por idioma
# («en»). Esta es la única función que sabe traducir eso a un mercado
# completo; nadie debe hacer `startswith("en")` por su cuenta, porque eso
# asume que el inglés es un bloque único y no lo es.

# Mercado al que cae un idioma cuando no se dice el país.
MERCADO_POR_DEFECTO_IDIOMA = {"en": "US", "es": "ES"}


def normalizar_clave(texto: str) -> str:
    """Minúsculas sin marcas diacríticas: «España» y «Espana» → «espana».

    Se normaliza en NFD y se descartan los diacríticos combinantes, así que
    resuelve cualquier acento y también la eñe, que es la que se escribe mal
    más a menudo. Antes se quitaban cinco vocales acentuadas a mano y la eñe
    quedaba, obligando a listar las dos formas de cada país.
    """
    import unicodedata

    descompuesto = unicodedata.normalize("NFD", str(texto or "").strip().lower())
    return "".join(c for c in descompuesto if not unicodedata.combining(c))


# Mercados donde la alícuota no la fija un único organismo central: en
# Estados Unidos la fijan el estado, el condado y la ciudad; en Canadá, la
# provincia (GST federal más el tramo provincial, que da lugar al HST).
# Mostrar una cifra única en estos casos sería inventar un dato que el
# visitante tomará por oficial.
IMPUESTO_REGIONAL = frozenset({"US", "CA"})


def impuesto_es_regional(codigo: str | None) -> bool:
    """¿La alícuota de este mercado depende de la región y no es nacional?"""
    return str(codigo or "").strip().upper() in IMPUESTO_REGIONAL


def texto_impuesto(codigo: str | None, idioma: str = "es") -> str:
    """Cómo se presenta el impuesto de un mercado en un listado.

    «21% IVA», «20% VAT», «10% GST», «GST/HST», «Sales tax»: el nombre que
    tiene en cada sitio y, cuando la alícuota es nacional, su valor. Donde
    depende de la región no se muestra ninguna cifra.
    """
    pais = PAISES.get(str(codigo or "").strip().upper()) or PAIS_GENERICO
    # El idioma es el de la página que lo muestra, no el del mercado: una
    # landing en inglés que lista México dice «16% VAT», no «16% I.V.A.».
    en = str(idioma or "es").strip().lower().startswith("en")
    etiqueta = pais["etiqueta_impuesto_en"] if en else pais["etiqueta_impuesto"]
    if impuesto_es_regional(codigo):
        return etiqueta
    iva = pais.get("iva")
    if iva is None:
        return etiqueta
    iva = f"{iva:g}" if isinstance(iva, float) else str(iva)
    return f"{iva} % {etiqueta}"


@lru_cache(maxsize=128)
def resolver_mercado(clave: str | None) -> dict:
    """Devuelve el mercado que corresponde a una clave; nunca falla.

    Siempre devuelve un mercado completo (con las ocho dimensiones), así que
    quien lo llama puede usar `mercado["separador_decimal"]` o
    `mercado["idioma"]` sin comprobar nada. Si la clave no identifica un
    mercado concreto, cae al mercado por defecto del idioma y, si no hay
    idioma reconocible, al genérico.
    """
    c = str(clave or "").strip().replace("_", "-")
    if not c:
        return PAIS_GENERICO

    # 1 · Locale completo: «en-GB», «es-MX».
    for pais in PAISES.values():
        if pais["locale"].lower() == c.lower():
            return pais

    # 2 · Código de país: «GB», «mx».
    if c.upper() in PAISES:
        return PAISES[c.upper()]

    # 3 · Nombre oficial o gentilicio: «Reino Unido», «canadiense».
    k = normalizar_clave(c)
    for pais in PAISES.values():
        if k in (normalizar_clave(pais["nombre"]), normalizar_clave(pais["mercado"])):
            return pais

    # 4 · Solo el idioma: «en» -> Estados Unidos, «es» -> España.
    defecto = MERCADO_POR_DEFECTO_IDIOMA.get(c.split("-")[0].lower())
    if defecto:
        return PAISES[defecto]
    return PAIS_GENERICO


def idioma_de(clave: str | None) -> str:
    """«en-GB» -> «en». El idioma se pregunta al mercado, no a la cadena."""
    return str(resolver_mercado(clave)["idioma"] or "es")


def es_ingles(clave: str | None) -> bool:
    """¿Este mercado redacta en inglés?

    Sustituye a los `startswith("en")` repartidos por el código: la pregunta
    no es si la cadena empieza por «en», sino de qué mercado se trata.
    """
    return idioma_de(clave) == "en"


def obtener_pais(codigo: str | None) -> dict | None:
    if not codigo:
        return None
    c = str(codigo).strip().upper()
    return PAISES.get(c)


def lista_paises() -> list[dict]:
    return [PAISES[c] for c in ORDEN_SELECTOR if c in PAISES]


def es_codigo_valido(codigo: str | None) -> bool:
    if not codigo:
        return False
    return str(codigo).strip().upper() in PAISES


# ---- Helpers para Semana 2 — Bloque B/C (auto-config) -----------------------

def defaults_para_pais(codigo: str | None) -> dict:
    """Devuelve los defaults de un país (moneda, IVA, ID fiscal, ejemplos).

    Incluye los ejemplos de formulario por país (placeholder del ID fiscal,
    teléfono, forma legal y ciudad) para que onboarding y /configuracion
    hablen el idioma local sin lógica duplicada.

    Si el código es inválido o vacío, devuelve el genérico LatAm.
    Es la única fuente de defaults de país para onboarding y /configuracion.
    """
    pais = obtener_pais(codigo) if codigo else None
    base = pais or PAIS_GENERICO
    return {
        "codigo": base["codigo"],
        "nombre": base["nombre"],
        "moneda": base["moneda"],
        "iva": base["iva"],
        "id_fiscal": base["id_fiscal"],
        "vocab": base["vocab"],
        "bandera": base["bandera"],
        "mercado": base["mercado"],
        "id_fiscal_placeholder": base.get("id_fiscal_placeholder", ""),
        "telefono_ejemplo": base.get("telefono_ejemplo", ""),
        "razon_social_ejemplo": base.get("razon_social_ejemplo", ""),
        "ciudad_ejemplo": base.get("ciudad_ejemplo", ""),
        "etiqueta_impuesto_en": base.get("etiqueta_impuesto_en", "VAT"),
        "locale": base.get("locale", ""),
        "idioma": base.get("idioma", "es"),
        "etiqueta_impuesto": base.get("etiqueta_impuesto", "IVA"),
        "separador_miles": base.get("separador_miles", "."),
        "separador_decimal": base.get("separador_decimal", ","),
        "formato_fecha": base.get("formato_fecha", "DD/MM/YYYY"),
        "sistema_unidades": base.get("sistema_unidades", "metrico"),
    }


# Re-exporta la lista blanca de monedas para validar formularios sin importar utils
try:
    from .utils import MONEDAS_SOPORTADAS as _MONEDAS_UTILS  # type: ignore
    MONEDAS_SOPORTADAS = _MONEDAS_UTILS
except Exception:
    # Fallback si utils aún no se importó (evita ciclo en tests)
    MONEDAS_SOPORTADAS: tuple[str, ...] = tuple(
        sorted({p["moneda"] for p in PAISES.values()} | {"USD", "VES", "BRL", "EUR", "Bs"})
    )
