"""La hora que ve el operador.

Todo lo que se guarda en la base de datos es UTC (columnas `DateTime` con
`datetime.utcnow`). El panel imprimía esos valores tal cual, así que a un
operador en Caracas (UTC−4) una venta de las 20:30 le aparecía como las 00:30
del día siguiente: un dato falso en la pantalla que se usa para decidir.

Aquí se resuelve una sola vez: la zona se configura con
`COTIZAT_ZONA_HORARIA` (por omisión `America/Caracas`, que es donde opera la
empresa) y las plantillas convierten con el filtro `local`.

Reglas:

- `local` recibe un `datetime` (naive = UTC, como todo lo guardado) o un
  `date` y devuelve el texto ya en la zona del operador.
- Las fechas sin hora (`vence`, `inicio`) **no** se desplazan: un vencimiento
  es un día del calendario, no un instante.
- Si el valor no es una fecha, se devuelve tal cual: una plantilla con un
  `None` no debe reventar por un filtro de formato.
"""
from __future__ import annotations

import os
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

#: Zona por omisión: donde opera la empresa. Se puede cambiar sin desplegar
#: código con `COTIZAT_ZONA_HORARIA=America/Bogota`.
ZONA_POR_DEFECTO = "America/Caracas"

#: Nombre legible de la zona para los pies de página del panel.
_NOMBRES = {
    "America/Caracas": "hora de Caracas",
    "America/Bogota": "hora de Bogotá",
    "America/Lima": "hora de Lima",
    "America/Santiago": "hora de Santiago",
    "America/Mexico_City": "hora de Ciudad de México",
    "America/Argentina/Buenos_Aires": "hora de Buenos Aires",
    "America/Panama": "hora de Panamá",
    "America/Santo_Domingo": "hora de Santo Domingo",
    "UTC": "UTC",
    "Europe/Madrid": "hora de Madrid",
}


def nombre_zona() -> str:
    """Zona configurada, tal como se escribe en `COTIZAT_ZONA_HORARIA`."""
    return (os.environ.get("COTIZAT_ZONA_HORARIA") or "").strip() or ZONA_POR_DEFECTO


def zona() -> ZoneInfo:
    """La zona del operador; UTC si el nombre configurado no existe.

    Se resuelve en cada llamada y no al importar: así una variable de entorno
    mal escrita degrada a UTC con un aviso, en vez de tumbar el panel al
    arrancar (el `ZoneInfoNotFoundError` sería un 500 de módulo).
    """
    try:
        return ZoneInfo(nombre_zona())
    except (ZoneInfoNotFoundError, ValueError):
        return ZoneInfo("UTC")


def a_local(valor: datetime | date | None) -> datetime | date | None:
    """Pasa un instante UTC a la zona del operador.

    Un `datetime` naive se interpreta como UTC (es lo que guarda la base de
    datos). Las `date` se devuelven intactas: un vencimiento no tiene hora.
    """
    if valor is None:
        return None
    if isinstance(valor, datetime):
        if valor.tzinfo is None:
            valor = valor.replace(tzinfo=timezone.utc)
        return valor.astimezone(zona())
    return valor


def hora_local(valor, formato: str = "%d/%m/%Y %H:%M") -> str:
    """Formatea un instante en la zona del operador. Filtro `|local`."""
    if valor is None:
        return "—"
    if not isinstance(valor, (datetime, date)):
        return str(valor)
    return a_local(valor).strftime(formato)


def fecha_local(valor, formato: str = "%d/%m/%Y") -> str:
    """Igual que `hora_local`, con formato de fecha por omisión."""
    return hora_local(valor, formato)


def hoy_local() -> date:
    """El día del calendario del operador (en UTC puede ser «mañana»)."""
    return datetime.now(zona()).date()


def etiqueta_zona() -> str:
    """«hora de Caracas (UTC−4)»: quita la ambigüedad sin pedir cuentas."""
    ahora = datetime.now(zona())
    desfase = ahora.utcoffset()
    if desfase is None:
        return nombre_zona()
    minutos = int(desfase.total_seconds() // 60)
    signo = "+" if minutos >= 0 else "−"
    minutos = abs(minutos)
    texto = f"UTC{signo}{minutos // 60:02d}:{minutos % 60:02d}"
    nombre = _NOMBRES.get(nombre_zona(), nombre_zona())
    return f"{nombre} ({texto})"


def utc_iso(valor) -> str:
    """El instante en UTC, para el `title` de un `<time>` (detalle exacto)."""
    if not isinstance(valor, (datetime, date)):
        return ""
    if isinstance(valor, datetime):
        if valor.tzinfo is None:
            valor = valor.replace(tzinfo=timezone.utc)
        return valor.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return valor.isoformat()
