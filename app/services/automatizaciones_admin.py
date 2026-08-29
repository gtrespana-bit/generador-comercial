"""Automatizaciones visibles del panel (Fase 2, B5).

El despliegue serverless no tiene procesos en segundo plano; las tareas
programadas viven en ``vercel.json`` con ``CRON_SECRET``. Este módulo las hace
**visibles y accionables**: muestra cada regla y, cuando tiene sentido, deja
dispararla a mano desde el panel (misma lógica que el cron, sin cambiar el
contrato de las rutas programadas).
"""
from __future__ import annotations

from datetime import date, timedelta

from ..models import CompraPlan, Licencia, Organizacion
from .licencias import resumen_organizaciones


class GestionAutomatizacionError(RuntimeError):
    """La regla no se puede ejecutar en este despliegue."""


#: Catálogo cerrado de reglas conocidas. ``ejecutable`` indica si el panel
#: oferta un botón de ejecución manual (las que solo corren por cron no).
REGLAS = [
    {
        "id": "recordatorios",
        "nombre": "Recordatorios de vencimiento (5 y 1 día)",
        "descripcion": (
            "El cron diario envía el aviso a 5 días y la última llamada a 1 "
            "día antes de vencer. Una vez por hito y licencia."
        ),
        "frecuencia": "Diaria · vercel.json · CRON_SECRET",
        "ejecutable": True,
    },
    {
        "id": "avisos_vencimiento",
        "nombre": "Avisos de vencimiento (ventana 15 días)",
        "descripcion": (
            "Barrido operativo que avisa a las organizaciones cuyo acceso "
            "vence en los próximos 15 días. No repite en el mismo día."
        ),
        "frecuencia": "Bajo demanda desde el panel",
        "ejecutable": True,
    },
    {
        "id": "mantenimiento",
        "nombre": "Respaldo + verificación diaria",
        "descripcion": (
            "Respaldo automático del SQLite local y verificación de salud con "
            "alerta al operador si algo queda rojo."
        ),
        "frecuencia": "Diaria · vercel.json · CRON_SECRET",
        "ejecutable": True,
    },
    {
        "id": "clientes_sin_plan",
        "nombre": "Alertas de clientes sin plan",
        "descripcion": (
            "Se calcula en cada apertura del panel: cuántas organizaciones no "
            "tienen acceso activo, para no dejar clientes colgados."
        ),
        "frecuencia": "Calculada en vivo",
        "ejecutable": False,
    },
]


def estado_automatizaciones(db, *, hoy: date | None = None) -> dict:
    """Info de lo que cada regla dispararía hoy (solo lee tablas del titular)."""
    hoy = hoy or date.today()
    filas = resumen_organizaciones(db, hoy=hoy, dias_aviso=15)
    por_renovar = [f for f in filas if f["por_vencer"]]
    recordatorios_hoy = [
        f for f in por_renovar if f["dias_restantes"] in (5, 1)
    ]
    sin_plan = [f for f in filas if not f["vigente"]]
    compras_pendientes = (
        db.query(CompraPlan).filter(CompraPlan.estado == "pendiente").count()
    )
    return {
        "por_renovar": len(por_renovar),
        "recordatorios_hoy": len(recordatorios_hoy),
        "sin_plan": len(sin_plan),
        "compras_pendientes": compras_pendientes,
        "control": {
            "dispara_hoy": len(recordatorios_hoy) + len(sin_plan) + compras_pendientes,
        },
    }


def ejecutar_regla(
    db,
    regla: str,
    *,
    remitente=None,
) -> dict:
    """Ejecuta a mano una regla. Reutiliza exactamente la lógica de los crons."""
    regla = (regla or "").strip().lower()
    if regla == "recordatorios":
        if remitente is None:
            raise GestionAutomatizacionError(
                "El correo no está configurado; no se puede enviar."
            )
        from .licencias import enviar_recordatorios_vencimiento

        return enviar_recordatorios_vencimiento(db, remitente=remitente)

    if regla == "avisos_vencimiento":
        if remitente is None:
            raise GestionAutomatizacionError(
                "El correo no está configurado; no se puede enviar."
            )
        from .licencias import enviar_avisos_vencimiento

        return enviar_avisos_vencimiento(db, remitente=remitente)

    if regla == "mantenimiento":
        from .mantenimiento import (
            ejecutar_respaldo_automatico,
            ejecutar_verificacion_diaria,
        )

        respaldo = ejecutar_respaldo_automatico(db)
        verificacion = ejecutar_verificacion_diaria()
        return {"respaldo": respaldo, "verificacion": verificacion}

    raise GestionAutomatizacionError("La regla indicada no existe o no es accionable.")
