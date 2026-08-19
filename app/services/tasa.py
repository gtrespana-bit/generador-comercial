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

# Tasa sugerida inicial si la API falla y no hay tasa guardada (aprox 2026-08)
# No es vinculante: el usuario la ve y la confirma antes de guardar.
TASAS_SUGERIDAS: dict[str, float] = {
    "VES": 36.50,  # BCV aprox
    "COP": 4200.0,
    "MXN": 17.20,
    "PEN": 3.75,
    "CLP": 950.0,
    "ARS": 950.0,  # volátil, solo referencia
    "UYU": 40.0,
    "PYG": 7500.0,
    "BOB": 6.90,
    "DOP": 59.0,
    "PAB": 1.0,  # USD
    "CRC": 510.0,
    "GTQ": 7.80,
    "HNL": 24.80,
    "NIO": 36.70,
    "BRL": 5.60,
    "EUR": 0.92,
    "USD": 1.0,
}


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


def tasa_sugerida(moneda: str) -> float:
    moneda = str(moneda or "USD").strip().upper()
    if moneda == "BS":
        moneda = "VES"
    return TASAS_SUGERIDAS.get(moneda, 1.0)
