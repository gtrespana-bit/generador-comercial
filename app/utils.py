"""Utilidades de formato compartidas entre la web y el PDF.

Formato numérico estilo Venezuela/España: miles con punto y decimales
con coma (1.234.567,89). Cantidades con punto decimal (12.50 m2),
igual que en los presupuestos de referencia.
"""

# Semana 2 — Bloque B: catálogo de símbolos por ISO 4217 (20 monedas LatAm + extras)
# Bs se mantiene como alias histórico de VES para no romper presupuestos antiguos.
SIMBOLOS = {
    "USD": "$",
    "VES": "Bs",
    "Bs": "Bs",
    "COP": "$",
    "MXN": "$",
    "PEN": "S/",
    "CLP": "$",
    "ARS": "$",
    "UYU": "$U",
    "PYG": "₲",
    "BOB": "Bs",
    "DOP": "RD$",
    "PAB": "B/.",
    "CRC": "₡",
    "GTQ": "Q",
    "HNL": "L",
    "NIO": "C$",
    "BRL": "R$",
    "EUR": "€",
}

# Símbolo inequívoco por moneda. Doce países de la región usan «$» para
# monedas distintas: un importe con «$» a secas no dice si son pesos mexicanos,
# colombianos o dólares. Se antepone el prefijo nacional, como hacen los bancos
# locales. `SIMBOLOS` se conserva como catálogo ISO 4217 puro.
SIMBOLOS_DISTINTIVOS = {
    "USD": "US$",
    "MXN": "MX$",
    "COP": "COL$",
    "CLP": "CLP$",
    "ARS": "AR$",
}


def simbolo_moneda(moneda: str | None, defecto: str = "USD") -> str:
    """Símbolo que no se puede confundir con el de otro país."""
    clave = str(moneda or defecto).strip()
    if clave == "Bs":
        clave = "VES"
    clave = clave.upper()
    return SIMBOLOS_DISTINTIVOS.get(clave) or SIMBOLOS.get(clave, clave or "$")


# Lista blanca de monedas aceptadas en formularios (ISO + alias histórico)
MONEDAS_SOPORTADAS: tuple[str, ...] = tuple(sorted(set(SIMBOLOS.keys()) | {"USD", "VES", "Bs"}))
# Normalización: VES/Bs son la misma moneda a efectos de validación
_ALIAS_MONEDA = {"VES": "VES", "Bs": "VES"}

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


def fmt_num(valor, decimales=2, idioma="es") -> str:
    """1234567.891 -> '1.234.567,89' (es) o '1,234,567.89' (en).

    El separador de miles y decimales es de idioma, no de moneda: una landing
    en inglés no puede mostrar «2.914,52 US$». En español (y en cualquier
    otro caso) se conserva exactamente el formato de siempre.
    """
    s = f"{valor:,.{decimales}f}"
    if str(idioma or "es").strip().lower().startswith("en"):
        return s
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def normalizar_moneda(moneda: str | None, defecto: str = "USD") -> str:
    """Normaliza un código de moneda: mayúsculas, alias Bs→VES, fallback."""
    if not moneda:
        return defecto
    m = str(moneda).strip().upper()
    # Alias histórico: Bs es VES
    if m == "BS":
        return "VES"
    if m in SIMBOLOS or m in MONEDAS_SOPORTADAS:
        # Si es alias, devuelve canónico VES
        return _ALIAS_MONEDA.get(m, m)
    return defecto


def es_moneda_soportada(moneda: str | None) -> bool:
    if not moneda:
        return False
    return str(moneda).strip().upper() in MONEDAS_SOPORTADAS or str(moneda).strip().upper() == "BS"


def decimales_moneda(moneda: str | None) -> int:
    """Decimales visibles de una moneda (COP/CLP/PYG: 0; el resto: 2)."""
    try:
        from .services.monedas import decimales

        return decimales(moneda)
    except Exception:  # pragma: no cover - degradación defensiva
        return 2


def fmt_monto(valor, moneda="USD") -> str:
    """Importe con símbolo inequívoco: 35.755,89 MX$ / 4.200.000 COL$"""
    # Normaliza Bs→VES para que el símbolo sea consistente
    clave = str(moneda or "USD").strip()
    # Respeta Bs si viene literal (presupuestos antiguos)
    if clave == "Bs":
        clave = "VES"
    else:
        clave = clave.upper() if clave else "USD"
    return f"{fmt_num(valor, decimales_moneda(clave))} {simbolo_moneda(clave)}"


def fmt_monto_iso(valor, moneda="USD", idioma="es") -> str:
    """Importe profesional con código ISO, no símbolo ambiguo."""
    try:
        from .services.monedas import formato_iso
        return formato_iso(valor, moneda, idioma)
    except Exception:
        return f"{fmt_num(valor, idioma=idioma)} {str(moneda or 'USD').upper()}"


def fmt_monto_raw(valor, moneda="USD") -> str:
    """Alias histórico para compatibilidad con documentos antiguos."""
    return fmt_monto(valor, moneda)


def fmt_precio_u_iso(valor, moneda="USD", unidad="", idioma="es") -> str:
    """Precio unitario profesional: 32,50 COP/m2."""
    base = fmt_monto_iso(valor, moneda, idioma)
    return f"{base}/{unidad}" if unidad else base


def fmt_precio_u(valor, moneda="USD", unidad="") -> str:
    """Precio unitario histórico con símbolo: 32,50 $/m2"""
    base = f"{fmt_num(valor, decimales_moneda(moneda))} {simbolo_moneda(moneda)}"
    if unidad:
        base += f"/{unidad}"
    return base


def fmt_cantidad(valor, unidad="") -> str:
    """Cantidad con punto decimal (como el PDF de referencia): 12.50 m2"""
    s = f"{valor:.2f}"
    return f"{s} {unidad}".strip()


def fmt_fecha(fecha, idioma="es") -> str:
    """Fecha corta con el orden propio del idioma.

    Español: dd/mm/aaaa (15/08/2026). Inglés: el orden de Estados Unidos,
    mm/dd/aaaa (08/15/2026), que es el que se usa por defecto en el producto.
    """
    formato = "%m/%d/%Y" if str(idioma or "es").strip().lower().startswith("en") else "%d/%m/%Y"
    return fecha.strftime(formato)


def fmt_pct(valor) -> str:
    """16.0 -> '16.0' (para la etiqueta I.V.A. (16.0 %))"""
    return f"{float(valor):.1f}"


def fmt_decimal(valor) -> str:
    """1.5 -> '1,5' (para inputs y cantidades libres)"""
    return f"{valor:g}".replace(".", ",")
