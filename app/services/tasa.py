"""Servicio de tasa de referencia USD -> moneda local (LatAm).

Usa https://open.er-api.com/v6/latest/USD (gratis, sin clave, 1.500 req/mes
suficiente para tasa diaria por org). Fallback a manual si no hay red.

No se usa como fuente contable: es referencia para convertir el catálogo USD
a COP/MXN/PEN al mostrar/insertar. Cada presupuesto congela su tasa.
"""

from __future__ import annotations

import json
import urllib.request
import urllib.error
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

# Tasas sugeridas para pre-rellenar el formulario de configuración.
#
# IMPORTANTE: solo se listan monedas cuya tasa fue verificada el día de la
# actualización (TASAS_ACTUALIZADAS). Las demás devuelven None y la interfaz
# ofrece el botón «Tasa de hoy» (open.er-api.com) o la entrada manual: nunca
# se pre-rellena un número no verificado.
#
# No son vinculantes: el usuario ve la tasa y la confirma antes de guardar.
# Cada presupuesto congela su tasa al crearse.
TASAS_ACTUALIZADAS = "2026-08-25"
TASAS_SUGERIDAS: dict[str, float | None] = {
    "USD": 1.0,
    "PAB": 1.0,  # balboa, paridad con USD
    # BCV oficial 18/08/2026 (773,31 Bs/USD)
    "VES": 773.31,
    # TRM oficial Superintendencia Financiera de Colombia, 19/08/2026
    "COP": 3128.65,
    # Mercado (cierre 18/08/2026, ~17,06)
    "MXN": 17.06,
    # SUNAT (12/08/2026: 3,364 compra / 3,372 venta; ~3,37)
    "PEN": 3.37,
    # EUR/USD 1,1677 (xe.com mid-market 22/08/2026; BCE 21/08: 1,1681)
    # -> 1 USD = 0,8564 EUR
    "EUR": 0.8564,
    # CLP/USD 18/08/2026 (currency.me.uk 925.903, mid-market 913.16) → 925.90 adoptado
    "CLP": 925.90,
    # ARS/USD 08-11/08/2026 (pluang 1497.38, alanchand 1498.36) → 1497.38 adoptado
    "ARS": 1497.38,
    # DOP/USD 02-24/08/2026 (currency.me.uk 57.8169, Forbes 58.753, Xe 58.3369) → 58.33 adoptado
    "DOP": 58.33,
    # UYU/USD 05-18/08/2026 (Xe 40.2124, valutafx 40.248-40.28) → 40.21 adoptado
    "UYU": 40.21,
    # PYG/USD 08-24/08/2026 (pluang 5946.10, Xe 6009.42, RioTimes 5932) → 5946.10 adoptado
    "PYG": 5946.10,
}
# El resto de monedas del selector (BOB, CRC, GTQ,
# HNL, NIO, BRL…) no se pre-rellenan: sin tasa verificada a la fecha de
# TASAS_ACTUALIZADAS. El usuario consulta «Tasa de hoy» o escribe la oficial.


def obtener_tasa_api(moneda_local: str, timeout: int = 6) -> tuple[float | None, str | None]:
    """Intenta traer 1 USD -> moneda_local desde open.er-api.com.

    Devuelve (tasa, error). tasa es float o None si falla.
    """
    moneda = str(moneda_local or "").strip().upper()
    if not moneda or moneda in ("USD", "PAB"):
        return 1.0, None
    # Normaliza Bs -> VES
    if moneda == "BS":
        moneda = "VES"
    url = "https://open.er-api.com/v6/latest/USD"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "CotizaT/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status != 200:
                return None, f"HTTP {resp.status}"
            data = json.loads(resp.read().decode("utf-8"))
            rates = data.get("rates") or {}
            tasa = rates.get(moneda)
            if tasa is None:
                # VES suele no estar; prueba VEF obsoleto
                tasa = rates.get("VES") or rates.get("VEF")
            if tasa is None:
                return None, f"Moneda {moneda} no disponible en la API"
            try:
                tasa_f = float(tasa)
                if tasa_f <= 0 or not (0.01 < tasa_f < 1_000_000):
                    return None, "Tasa fuera de rango"
                return tasa_f, None
            except (TypeError, ValueError):
                return None, "Tasa no numérica"
    except urllib.error.URLError as e:
        return None, f"Sin conexión: {e.reason if hasattr(e, 'reason') else str(e)}"
    except Exception as e:
        return None, str(e)


def tasa_convertir_precio(precio_usd: float, tasa: float | None) -> float:
    """Convierte USD -> local con precisión decimal y redondeo comercial.

    Se conserva la firma histórica para no romper importadores ni el editor;
    la identidad de moneda y la exigencia de tasa viven en ``monedas.py``.
    """
    try:
        p = Decimal(str(precio_usd or 0))
        t = Decimal(str(tasa)) if tasa else Decimal("1")
        if t <= 0:
            t = Decimal("1")
        return float((p * t).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    except Exception:
        return float(precio_usd or 0)


def tasa_sugerida(moneda: str) -> float | None:
    """Tasa verificada para pre-rellenar, o None si no hay una verificada.

    None significa «sin sugerencia»: la interfaz invita a consultar la tasa
    del día (botón «Tasa de hoy») o a escribir la oficial. Nunca se devuelve
    un valor inventado.
    """
    moneda = str(moneda or "USD").strip().upper()
    if moneda == "BS":
        moneda = "VES"
    return TASAS_SUGERIDAS.get(moneda)


def factor_conversion_local(moneda: str | None, tasa: float | None) -> float:
    """Factor para convertir precios/costes USD a la moneda local.

    Devuelve 1.0 (sin conversión) cuando la moneda es USD/PAB, está vacía o
    no hay tasa válida. Con moneda local (COP/MXN/PEN/…) y tasa > 0 devuelve
    la propia tasa: precio_local = precio_usd × factor.

    Es la única forma de mantener coherencia entre precio, costes y beneficio:
    todos los importes de una vista se convierten con el MISMO factor o
    ninguno.
    """
    m = str(moneda or "USD").strip().upper()
    if m == "BS":
        m = "VES"
    if m in ("", "USD", "PAB") or not tasa:
        return 1.0
    try:
        t = float(tasa)
    except (TypeError, ValueError):
        return 1.0
    return t if t > 0 else 1.0
