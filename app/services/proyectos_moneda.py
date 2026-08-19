"""Reglas monetarias para proyectos, cambios, pagos y facturas."""
from __future__ import annotations

def moneda_proyecto(proyecto) -> str:
    return str(getattr(proyecto, "moneda_contractual", None) or getattr(getattr(proyecto, "presupuesto", None), "moneda", None) or "USD").upper()

def validar_pago(proyecto, moneda: str | None) -> str:
    esperada = moneda_proyecto(proyecto)
    recibida = str(moneda or esperada).upper()
    if recibida != esperada:
        raise ValueError(f"El pago debe registrarse en {esperada}, moneda contractual del proyecto")
    return esperada

def resumen_proyecto(proyecto) -> dict:
    moneda = moneda_proyecto(proyecto)
    return {"moneda": moneda, "contratado": proyecto.total_contratado, "cambios": proyecto.total_cambios_aprobados, "actual": proyecto.total_actual, "pagado": proyecto.total_pagado, "saldo": proyecto.saldo_pendiente}
