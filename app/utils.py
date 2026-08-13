"""Utilidades de formato compartidas entre la web y el PDF.

Formato numérico estilo Venezuela/España: miles con punto y decimales
con coma (1.234.567,89). Cantidades con punto decimal (12.50 m2),
igual que en los presupuestos de referencia.
"""

SIMBOLOS = {"USD": "$", "Bs": "Bs"}

# Sustituciones para glifos que no siempre están en las fuentes del PDF
_SANEADO = {
    "²": "2",
    "³": "3",
    "×": "x",
    "Ø": "Ø",
    " ": " ",
}


def saneado(texto: str) -> str:
    """Limpia caracteres problemáticos antes de meterlos en el PDF."""
    if not texto:
        return ""
    for k, v in _SANEADO.items():
        texto = texto.replace(k, v)
    return texto


def fmt_num(valor, decimales=2) -> str:
    """1234567.891 -> '1.234.567,89'"""
    s = f"{valor:,.{decimales}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_monto(valor, moneda="USD") -> str:
    """Importe con símbolo de moneda como sufijo: 35.755,89 $ / 35.755,89 Bs"""
    return f"{fmt_num(valor)} {SIMBOLOS.get(moneda, moneda)}"


def fmt_precio_u(valor, moneda="USD", unidad="") -> str:
    """Precio unitario: 32,50 $/m2"""
    base = f"{fmt_num(valor)} {SIMBOLOS.get(moneda, moneda)}"
    if unidad:
        base += f"/{unidad}"
    return base


def fmt_cantidad(valor, unidad="") -> str:
    """Cantidad con punto decimal (como el PDF de referencia): 12.50 m2"""
    s = f"{valor:.2f}"
    return f"{s} {unidad}".strip()


def fmt_fecha(fecha) -> str:
    """dd/mm/aaaa"""
    return fecha.strftime("%d/%m/%Y")


def fmt_pct(valor) -> str:
    """16.0 -> '16.0' (para la etiqueta I.V.A. (16.0 %))"""
    return f"{float(valor):.1f}"


def fmt_decimal(valor) -> str:
    """1.5 -> '1,5' (para inputs y cantidades libres)"""
    return f"{valor:g}".replace(".", ",")
