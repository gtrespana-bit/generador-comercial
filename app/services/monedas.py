"""Catálogo y contexto monetario unificado de Cotizat.

La moneda comercial de Cotizat (licencias y planes) es USD, mientras que los
presupuestos tienen una moneda contractual propia. Este módulo solo define
identidad, validación y formato; no realiza conversiones ni decide precios de
mercado.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from ..utils import SIMBOLOS, normalizar_moneda

@dataclass(frozen=True)
class DefinicionMoneda:
    codigo: str
    nombre: str
    decimales: int
    simbolo_auxiliar: str

# La lista visible debe crecer de forma explícita; no se acepta cualquier
# texto como moneda válida.
MONEDAS: dict[str, DefinicionMoneda] = {
    "USD": DefinicionMoneda("USD", "Dólar estadounidense", 2, "$"),
    "COP": DefinicionMoneda("COP", "Peso colombiano", 2, "$"),
    "MXN": DefinicionMoneda("MXN", "Peso mexicano", 2, "$"),
    "PEN": DefinicionMoneda("PEN", "Sol peruano", 2, "S/"),
    "CLP": DefinicionMoneda("CLP", "Peso chileno", 0, "$"),
    "ARS": DefinicionMoneda("ARS", "Peso argentino", 2, "$"),
    "UYU": DefinicionMoneda("UYU", "Peso uruguayo", 2, "$U"),
    "PYG": DefinicionMoneda("PYG", "Guaraní paraguayo", 0, "₲"),
    "BOB": DefinicionMoneda("BOB", "Boliviano", 2, "Bs"),
    "DOP": DefinicionMoneda("DOP", "Peso dominicano", 2, "RD$"),
    "PAB": DefinicionMoneda("PAB", "Balboa panameño", 2, "B/."),
    "CRC": DefinicionMoneda("CRC", "Colón costarricense", 2, "₡"),
    "GTQ": DefinicionMoneda("GTQ", "Quetzal guatemalteco", 2, "Q"),
    "HNL": DefinicionMoneda("HNL", "Lempira hondureño", 2, "L"),
    "NIO": DefinicionMoneda("NIO", "Córdoba nicaragüense", 2, "C$"),
    "BRL": DefinicionMoneda("BRL", "Real brasileño", 2, "R$"),
    "EUR": DefinicionMoneda("EUR", "Euro", 2, "€"),
    # Compatibilidad de datos antiguos; no se ofrece como moneda visible en
    # Venezuela y no se usa para nuevos valores persistidos.
    "VES": DefinicionMoneda("VES", "Bolívar venezolano (histórico)", 2, "Bs"),
}

MONEDA_COMERCIAL_COTIZAT = "USD"
MONEDA_BASE_CATALOGO = "USD"
MONEDAS_VISIBLE = tuple(k for k in MONEDAS if k != "VES")


def definicion(moneda: str | None, defecto: str = "USD") -> DefinicionMoneda:
    codigo = normalizar_moneda(moneda, defecto)
    return MONEDAS.get(codigo, MONEDAS[defecto])


def moneda_valida(moneda: str | None, *, visible: bool = True) -> bool:
    codigo = normalizar_moneda(moneda, "")
    return codigo in (MONEDAS_VISIBLE if visible else MONEDAS)


def decimales(moneda: str | None) -> int:
    return definicion(moneda).decimales


def codigo_iso(moneda: str | None, defecto: str = "USD") -> str:
    return definicion(moneda, defecto).codigo


def etiqueta(moneda: str | None, defecto: str = "USD") -> str:
    """Código ISO para interfaces y documentos; nunca solo el símbolo."""
    return definicion(moneda, defecto).codigo


def cuantizar(valor, moneda: str | None = "USD") -> Decimal:
    places = decimales(moneda)
    quantum = Decimal(1).scaleb(-places)
    return Decimal(str(valor or 0)).quantize(quantum, rounding=ROUND_HALF_UP)


def formato_iso(valor, moneda: str | None = "USD") -> str:
    """Formato textual estable: valor + código ISO, sin símbolos ambiguos."""
    d = cuantizar(valor, moneda)
    return f"{d:,.{decimales(moneda)}f}".replace(",", "X").replace(".", ",").replace("X", ".") + f" {codigo_iso(moneda)}"


def contexto(moneda: str | None, *, base: str = MONEDA_BASE_CATALOGO,
             tasa=None, fecha=None, fuente: str | None = None) -> dict:
    """Contexto serializable para backend, plantillas y editor."""
    return {
        "moneda_base": codigo_iso(base),
        "moneda_contractual": codigo_iso(moneda),
        "decimales": decimales(moneda),
        "simbolo_auxiliar": definicion(moneda).simbolo_auxiliar,
        "tipo_cambio": tasa,
        "fecha_tipo_cambio": fecha.isoformat() if hasattr(fecha, "isoformat") else fecha,
        "fuente_tipo_cambio": fuente or "",
    }
