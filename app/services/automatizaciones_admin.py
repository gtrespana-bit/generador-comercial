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
        "id": "marketing",
        "nombre": "Secuencia de marketing (consejos + win-back)",
        "descripcion": (
            "Correos que enseñan a usar el producto durante la prueba y "
            "recuperan a quien se fue: bienvenida, tarifas, presupuesto, PDF, "
            "cierre y win-back a 7 y 30 días. Respeta bajas y pasos completados."
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
    filas = [f for f in resumen_organizaciones(db, hoy=hoy, dias_aviso=15) if not f["organizacion"].es_test]
    por_renovar = [f for f in filas if f["por_vencer"]]
    recordatorios_hoy = [
        f for f in por_renovar if f["dias_restantes"] in (5, 1)
    ]
    sin_plan = [f for f in filas if not f["vigente"]]
    compras_pendientes = (
        db.query(CompraPlan).filter(CompraPlan.estado == "pendiente", CompraPlan.organizacion_id.in_([f["organizacion"].id for f in filas])).count()
    )
    # Marketing: cuántas orgs están en el día exacto de su plantilla.
    try:
        from ..models import BajaMarketing, EnvioMarketing, PruebaConcedida
        from .marketing import PLANTILLAS_SECUENCIA, historial_enviado

        marketing_hoy = 0
        # Usa la misma lógica que la secuencia: días desde alta de prueba.
        altas = {}
        for pc in db.query(PruebaConcedida).all():
            oid = int(getattr(pc, "organizacion_id", 0) or 0)
            if oid in {f["organizacion"].id for f in filas} and getattr(pc, "created_at", None):
                try:
                    altas[oid] = pc.created_at.date() if hasattr(pc.created_at, "date") else pc.created_at
                except Exception:
                    pass
        # También licencias de prueba vigentes (orgs que aún no aparecen en pruebas_concedidas en SQLite de tests).
        for f in filas:
            oid = int(f["organizacion"].id)
            lic = f.get("vigente")
            if oid not in altas and lic and getattr(lic, "origen", "") == "prueba" and getattr(lic, "inicio", None):
                altas[oid] = lic.inicio
        for entrada in PLANTILLAS_SECUENCIA:
            dia = int(entrada["dia"])
            plantilla = str(entrada["plantilla"])
            for oid, alta in altas.items():
                try:
                    if (hoy - alta).days == dia and not historial_enviado(db, oid, plantilla):
                        marketing_hoy += 1
                        break
                except Exception:
                    continue
    except Exception:
        marketing_hoy = 0
    return {
        "por_renovar": len(por_renovar),
        "recordatorios_hoy": len(recordatorios_hoy),
        "sin_plan": len(sin_plan),
        "compras_pendientes": compras_pendientes,
        "marketing_hoy": marketing_hoy,
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

    if regla == "marketing":
        from .marketing import enviar_secuencia_marketing

        return enviar_secuencia_marketing(db, remitente=remitente)

    raise GestionAutomatizacionError("La regla indicada no existe o no es accionable.")
