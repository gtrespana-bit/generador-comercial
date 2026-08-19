"""Datos de países para la landing adaptativa (Semana 1 — LatAm).

Un solo lugar con la verdad sobre cada mercado hispano: bandera, moneda,
IVA de referencia, etiqueta del ID fiscal y vocabulario local de obra.

No es fiscalidad normativa: el IVA que se muestra es la alícuota general
de referencia (no un asesoramiento tributario) y solo sirve para que la
landing hable el idioma del visitante. La configuración real del IVA sigue
siendo libre en /configuracion.

NOTA: El catálogo mantiene sus precios en USD como referencia regional;
la moneda_local aquí es solo informativa para el selector.
"""

from __future__ import annotations

# Cada entrada es lo que la landing necesita para personalizarse.
# `vocab` es la línea corta que aparece en el banner del catálogo:
# 5 términos que cambian por país (concreto/hormigón, friso/revoque, etc.).
PAISES: dict[str, dict] = {
    "VE": {
        "codigo": "VE",
        "nombre": "Venezuela",
        "gentilicio": "venezolano",
        "bandera": "🇻🇪",
        "moneda": "USD",
        "moneda_local": "VES",
        "simbolo_local": "Bs",
        "iva": 16,
        "id_fiscal": "RIF",
        "vocab": "concreto, friso, cielo raso, rodapié, plomero",
        "id_fiscal_placeholder": "J-12345678-9",
        "telefono_ejemplo": "+58 412 000 0000",
        "razon_social_ejemplo": "C.A.",
        "ciudad_ejemplo": "Caracas",
        "mercado": "venezolano",
    },
    "CO": {
        "codigo": "CO",
        "nombre": "Colombia",
        "gentilicio": "colombiano",
        "bandera": "🇨🇴",
        "moneda": "COP",
        "moneda_local": "COP",
        "simbolo_local": "$",
        "iva": 19,
        "id_fiscal": "NIT",
        "vocab": "concreto, pañete, cielo raso, guardaescoba, plomero",
        "id_fiscal_placeholder": "900.123.456-7",
        "telefono_ejemplo": "+57 300 000 0000",
        "razon_social_ejemplo": "S.A.S.",
        "ciudad_ejemplo": "Bogotá",
        "mercado": "colombiano",
    },
    "MX": {
        "codigo": "MX",
        "nombre": "México",
        "gentilicio": "mexicano",
        "bandera": "🇲🇽",
        "moneda": "MXN",
        "moneda_local": "MXN",
        "simbolo_local": "$",
        "iva": 16,
        "id_fiscal": "RFC",
        "vocab": "concreto, aplanado, plafón, zoclo, plomero",
        "id_fiscal_placeholder": "AAA010101AAA",
        "telefono_ejemplo": "+52 55 0000 0000",
        "razon_social_ejemplo": "S.A. de C.V.",
        "ciudad_ejemplo": "Ciudad de México",
        "mercado": "mexicano",
    },
    "PE": {
        "codigo": "PE",
        "nombre": "Perú",
        "gentilicio": "peruano",
        "bandera": "🇵🇪",
        "moneda": "PEN",
        "moneda_local": "PEN",
        "simbolo_local": "S/",
        "iva": 18,
        "id_fiscal": "RUC",
        "vocab": "concreto, tarrajeo, cielo raso, zócalo, gasfitero",
        "id_fiscal_placeholder": "20123456789",
        "telefono_ejemplo": "+51 900 000 000",
        "razon_social_ejemplo": "S.A.C.",
        "ciudad_ejemplo": "Lima",
        "mercado": "peruano",
    },
    "CL": {
        "codigo": "CL",
        "nombre": "Chile",
        "gentilicio": "chileno",
        "bandera": "🇨🇱",
        "moneda": "CLP",
        "moneda_local": "CLP",
        "simbolo_local": "$",
        "iva": 19,
        "id_fiscal": "RUT",
        "vocab": "hormigón, estuco, cielo falso, guardapolvo, gasfíter",
        "id_fiscal_placeholder": "76.123.456-K",
        "telefono_ejemplo": "+56 9 0000 0000",
        "razon_social_ejemplo": "SpA",
        "ciudad_ejemplo": "Santiago",
        "mercado": "chileno",
    },
    "AR": {
        "codigo": "AR",
        "nombre": "Argentina",
        "gentilicio": "argentino",
        "bandera": "🇦🇷",
        "moneda": "ARS",
        "moneda_local": "ARS",
        "simbolo_local": "$",
        "iva": 21,
        "id_fiscal": "CUIT",
        "vocab": "hormigón, revoque, cielorraso, zócalo, plomero",
        "id_fiscal_placeholder": "20-12345678-9",
        "telefono_ejemplo": "+54 11 0000 0000",
        "razon_social_ejemplo": "S.R.L.",
        "ciudad_ejemplo": "Buenos Aires",
        "mercado": "argentino",
    },
    "EC": {
        "codigo": "EC",
        "nombre": "Ecuador",
        "gentilicio": "ecuatoriano",
        "bandera": "🇪🇨",
        "moneda": "USD",
        "moneda_local": "USD",
        "simbolo_local": "$",
        "iva": 15,
        "id_fiscal": "RUC",
        "vocab": "hormigón, enlucido, tumbado, barredera, gasfitero",
        "id_fiscal_placeholder": "0991234567001",
        "telefono_ejemplo": "+593 99 000 0000",
        "razon_social_ejemplo": "S.A.",
        "ciudad_ejemplo": "Quito",
        "mercado": "ecuatoriano",
    },
    "DO": {
        "codigo": "DO",
        "nombre": "República Dominicana",
        "gentilicio": "dominicano",
        "bandera": "🇩🇴",
        "moneda": "DOP",
        "moneda_local": "DOP",
        "simbolo_local": "RD$",
        "iva": 18,
        "id_fiscal": "RNC",
        "vocab": "hormigón, pañete, plafón, zócalo, plomero",
        "id_fiscal_placeholder": "130-12345-6",
        "telefono_ejemplo": "+1 809 000 0000",
        "razon_social_ejemplo": "S.R.L.",
        "ciudad_ejemplo": "Santo Domingo",
        "mercado": "dominicano",
    },
    "UY": {
        "codigo": "UY",
        "nombre": "Uruguay",
        "gentilicio": "uruguayo",
        "bandera": "🇺🇾",
        "moneda": "UYU",
        "moneda_local": "UYU",
        "simbolo_local": "$U",
        "iva": 22,
        "id_fiscal": "RUT",
        "vocab": "hormigón, revoque, cielorraso, zócalo, sanitario",
        "id_fiscal_placeholder": "211234567812",
        "telefono_ejemplo": "+598 99 000 000",
        "razon_social_ejemplo": "S.A.",
        "ciudad_ejemplo": "Montevideo",
        "mercado": "uruguayo",
    },
    "PY": {
        "codigo": "PY",
        "nombre": "Paraguay",
        "gentilicio": "paraguayo",
        "bandera": "🇵🇾",
        "moneda": "PYG",
        "moneda_local": "PYG",
        "simbolo_local": "₲",
        "iva": 10,
        "id_fiscal": "RUC",
        "vocab": "hormigón, revoque, cielorraso, zócalo, plomero",
        "id_fiscal_placeholder": "80012345-6",
        "telefono_ejemplo": "+595 21 000 000",
        "razon_social_ejemplo": "S.A.",
        "ciudad_ejemplo": "Asunción",
        "mercado": "paraguayo",
    },
    "BO": {
        "codigo": "BO",
        "nombre": "Bolivia",
        "gentilicio": "boliviano",
        "bandera": "🇧🇴",
        "moneda": "BOB",
        "moneda_local": "BOB",
        "simbolo_local": "Bs",
        "iva": 13,
        "id_fiscal": "NIT",
        "vocab": "hormigón, revoque, cielo falso, zócalo, plomero",
        "id_fiscal_placeholder": "1020304050",
        "telefono_ejemplo": "+591 2 000 0000",
        "razon_social_ejemplo": "S.R.L.",
        "ciudad_ejemplo": "La Paz",
        "mercado": "boliviano",
    },
    "PA": {
        "codigo": "PA",
        "nombre": "Panamá",
        "gentilicio": "panameño",
        "bandera": "🇵🇦",
        "moneda": "USD",
        "moneda_local": "PAB",
        "simbolo_local": "B/.",
        "iva": 7,
        "id_fiscal": "RUC",
        "vocab": "concreto, repello, cielo raso, zócalo, plomero",
        "id_fiscal_placeholder": "1234567-1-123456",
        "telefono_ejemplo": "+507 6000 0000",
        "razon_social_ejemplo": "S.A.",
        "ciudad_ejemplo": "Ciudad de Panamá",
        "mercado": "panameño",
    },
    "CR": {
        "codigo": "CR",
        "nombre": "Costa Rica",
        "gentilicio": "costarricense",
        "bandera": "🇨🇷",
        "moneda": "CRC",
        "moneda_local": "CRC",
        "simbolo_local": "₡",
        "iva": 13,
        "id_fiscal": "NITE",
        "vocab": "concreto, repello, cielo raso, rodapié, fontanero",
        "id_fiscal_placeholder": "3-101-123456",
        "telefono_ejemplo": "+506 8888 0000",
        "razon_social_ejemplo": "S.A.",
        "ciudad_ejemplo": "San José",
        "mercado": "costarricense",
    },
    "GT": {
        "codigo": "GT",
        "nombre": "Guatemala",
        "gentilicio": "guatemalteco",
        "bandera": "🇬🇹",
        "moneda": "GTQ",
        "moneda_local": "GTQ",
        "simbolo_local": "Q",
        "iva": 12,
        "id_fiscal": "NIT",
        "vocab": "concreto, repello, cielo falso, zócalo, fontanero",
        "id_fiscal_placeholder": "1234567-8",
        "telefono_ejemplo": "+502 5555 0000",
        "razon_social_ejemplo": "S.A.",
        "ciudad_ejemplo": "Ciudad de Guatemala",
        "mercado": "guatemalteco",
    },
    "HN": {
        "codigo": "HN",
        "nombre": "Honduras",
        "gentilicio": "hondureño",
        "bandera": "🇭🇳",
        "moneda": "HNL",
        "moneda_local": "HNL",
        "simbolo_local": "L",
        "iva": 15,
        "id_fiscal": "RTN",
        "vocab": "concreto, repello, cielo falso, zócalo, fontanero",
        "id_fiscal_placeholder": "08011999123456",
        "telefono_ejemplo": "+504 9999 0000",
        "razon_social_ejemplo": "S.A.",
        "ciudad_ejemplo": "Tegucigalpa",
        "mercado": "hondureño",
    },
    "SV": {
        "codigo": "SV",
        "nombre": "El Salvador",
        "gentilicio": "salvadoreño",
        "bandera": "🇸🇻",
        "moneda": "USD",
        "moneda_local": "USD",
        "simbolo_local": "$",
        "iva": 13,
        "id_fiscal": "NIT",
        "vocab": "concreto, repello, cielo falso, zócalo, fontanero",
        "id_fiscal_placeholder": "0614-123456-789-0",
        "telefono_ejemplo": "+503 7000 0000",
        "razon_social_ejemplo": "S.A. de C.V.",
        "ciudad_ejemplo": "San Salvador",
        "mercado": "salvadoreño",
    },
    "NI": {
        "codigo": "NI",
        "nombre": "Nicaragua",
        "gentilicio": "nicaragüense",
        "bandera": "🇳🇮",
        "moneda": "NIO",
        "moneda_local": "NIO",
        "simbolo_local": "C$",
        "iva": 15,
        "id_fiscal": "RUC",
        "vocab": "concreto, repello, cielo raso, zócalo, fontanero",
        "id_fiscal_placeholder": "J0310000001234",
        "telefono_ejemplo": "+505 8888 0000",
        "razon_social_ejemplo": "S.A.",
        "ciudad_ejemplo": "Managua",
        "mercado": "nicaragüense",
    },
}

# Orden en que aparecen en el selector (Semana 2 — foco 5 países)
# VE histórico + 4 nuevos (CO + MX + EC + PE). Los otros 12 quedan en PAISES
# pero ocultos hasta la ola 2 para no dispersar validación.
ORDEN_SELECTOR = [
    "VE", "CO", "MX", "EC", "PE",
]

# Genérico para cuando no hay país seleccionado (SEO, primera visita)
PAIS_GENERICO: dict = {
    "codigo": "",
    "nombre": "Latinoamérica",
    "gentilicio": "latinoamericano",
    "bandera": "🌎",
    "moneda": "USD",
    "moneda_local": "USD",
    "simbolo_local": "$",
    "iva": 16,
    "id_fiscal": "ID fiscal",
    "vocab": "concreto, friso, cielo raso, rodapié, plomero",
    "mercado": "latinoamericano",
    "id_fiscal_placeholder": "RIF, NIT, RUC, RFC…",
    "telefono_ejemplo": "+00 000 000 0000",
    "razon_social_ejemplo": "",
    "ciudad_ejemplo": "",
}


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
