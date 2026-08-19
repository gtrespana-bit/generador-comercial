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

# Tasas sugeridas para pre-rellenar el formulario de configuración.
#
# IMPORTANTE: solo se listan monedas cuya tasa fue verificada el día de la
# actualización (TASAS_ACTUALIZADAS). Las demás devuelven None y la interfaz
# ofrece el botón «Tasa de hoy» (open.er-api.com) o la entrada manual: nunca
# se pre-rellena un número no verificado.
#
# No son vinculantes: el usuario ve la tasa y la confirma antes de guardar.
# Cada presupuesto congela su tasa al crearse.
TASAS_ACTUALIZADAS = "2026-08-19"
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
}
# El resto de monedas del selector (CLP, ARS, UYU, PYG, BOB, DOP, CRC, GTQ,
# HNL, NIO, BRL, EUR…) no se pre-rellenan: sin tasa verificada a la fecha de
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
    """Convierte precio USD -> local con tasa. Si tasa es None/0/1, devuelve USD."""
    try:
        p = float(precio_usd or 0)
        t = float(tasa) if tasa else 1.0
        if t <= 0:
            t = 1.0
        return round(p * t, 2)
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
