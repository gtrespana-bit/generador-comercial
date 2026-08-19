"""Primer inicio y progreso hasta el primer presupuesto real en PDF."""
from datetime import datetime

from sqlalchemy.orm import Session

from ..models import Cliente, Configuracion, Partida, Presupuesto, asegurar_config
from ..seeds import sembrar_catalogo, sembrar_demo, sembrar_productos, sembrar_recetas

MODO_DEMO = "demo"
MODO_LIMPIO = "limpio"
MODOS_VALIDOS = {MODO_DEMO, MODO_LIMPIO}


class ErrorOnboarding(ValueError):
    """Datos incompletos o incoherentes al finalizar el primer inicio."""


def _configuracion(db: Session) -> Configuracion:
    asegurar_config(db)
    return db.query(Configuracion).first()


def marcar_instalacion_anterior(db: Session) -> Configuracion:
    """Evita mostrar el asistente al actualizar una base de versiones previas.

    Solo debe llamarse cuando el esquema anterior no tenía la columna de
    onboarding. No altera datos empresariales, catálogos ni documentos.
    """
    cfg = _configuracion(db)
    if not cfg.onboarding_completado:
        cfg.onboarding_completado = True
        cfg.onboarding_modo = "existente"
        cfg.onboarding_completado_at = datetime.utcnow()
        # No mostramos una lista de primer uso a quien ya trabajaba con la
        # aplicación; esta migración solo protege la continuidad.
        cfg.onboarding_catalogo_revisado = True
        cfg.onboarding_pdf_descargado = db.query(Presupuesto).count() > 0
        db.commit()
    return cfg


def completar_onboarding(db: Session, datos: dict, modo: str) -> Configuracion:
    """Guarda la empresa y aplica, una sola vez, demo o instalación limpia."""
    cfg = _configuracion(db)
    if cfg.onboarding_completado:
        raise ErrorOnboarding("El primer inicio ya fue completado.")

    modo = str(modo or "").strip().lower()
    if modo not in MODOS_VALIDOS:
        raise ErrorOnboarding("Elige si quieres empezar con un ejemplo o en limpio.")
    modo_en_curso = str(cfg.onboarding_modo or "").strip().lower()
    if modo_en_curso in MODOS_VALIDOS and modo_en_curso != modo:
        raise ErrorOnboarding(
            "La preparación ya comenzó en el modo elegido. Reintenta con la misma opción."
        )

    empresa_nombre = str(datos.get("empresa_nombre") or "").strip()
    if not empresa_nombre or empresa_nombre.lower() == "mi empresa":
        raise ErrorOnboarding("Escribe el nombre comercial de tu empresa.")

    # Moneda: 20 ISOs (validación contra lista blanca, alias Bs->VES)
    from ..utils import MONEDAS_SOPORTADAS, normalizar_moneda
    moneda_raw = str(datos.get("moneda_default") or "USD").strip()
    moneda = normalizar_moneda(moneda_raw, "USD")
    if moneda not in MONEDAS_SOPORTADAS and moneda != "VES":
        moneda = "USD"
    try:
        iva = float(datos.get("iva_default", 16.0))
    except (TypeError, ValueError):
        iva = 16.0
    if not 0 <= iva <= 100:
        raise ErrorOnboarding("El IVA debe estar entre 0 y 100 %.")
    # Etiqueta ID fiscal y tasa (LatAm)
    etiqueta = str(datos.get("etiqueta_id_fiscal") or "RIF").strip()[:20] or "RIF"
    tasa_raw = datos.get("tasa_cambio")
    try:
        tasa = float(str(tasa_raw).replace(",", ".")) if str(tasa_raw or "").strip() else None
        if tasa is not None and tasa <= 0:
            tasa = None
    except Exception:
        tasa = None
    fecha_tasa = datos.get("fecha_tasa")
    try:
        from datetime import date as _date
        if isinstance(fecha_tasa, str) and fecha_tasa.strip():
            fecha_tasa = _date.fromisoformat(fecha_tasa.strip())
        elif not isinstance(fecha_tasa, _date):
            fecha_tasa = None
    except Exception:
        fecha_tasa = None

    cfg.empresa_nombre = empresa_nombre[:200]
    cfg.empresa_legal = str(datos.get("empresa_legal") or "").strip()[:250]
    cfg.empresa_rif = str(datos.get("empresa_rif") or "").strip()[:50]
    cfg.empresa_pais = str(datos.get("empresa_pais") or "Venezuela").strip()[:80] or "Venezuela"
    cfg.empresa_ciudad = str(datos.get("empresa_ciudad") or "").strip()[:120]
    cfg.empresa_direccion = str(datos.get("empresa_direccion") or "").strip()
    cfg.empresa_telefono = str(datos.get("empresa_telefono") or "").strip()[:50]
    cfg.empresa_email = str(datos.get("empresa_email") or "").strip()[:200]
    cfg.moneda_default = moneda
    cfg.iva_default = iva
    cfg.etiqueta_id_fiscal = etiqueta
    cfg.tasa_cambio = tasa
    cfg.fecha_tasa = fecha_tasa
    cfg.onboarding_modo = modo
    db.commit()

    if modo == MODO_DEMO:
        # Las funciones son idempotentes: si el proceso se interrumpe puede
        # repetirse sin duplicar catálogos ni el documento de ejemplo.
        sembrar_catalogo(db)
        sembrar_productos(db)
        sembrar_recetas(db)
        sembrar_demo(db)
    else:
        # La opción limpia no debe inyectar contenido en arranques posteriores.
        cfg.semilla_catalogo_aplicada = True
        cfg.semilla_productos_aplicada = True
        cfg.semilla_recetas_aplicada = True
        db.commit()

    cfg.onboarding_completado = True
    cfg.onboarding_completado_at = datetime.utcnow()
    db.commit()
    return cfg


def estado_recorrido_inicial(db: Session, cfg: Configuracion | None = None) -> dict:
    """Devuelve pasos verificables del recorrido hasta el primer PDF real."""
    cfg = cfg or _configuracion(db)
    empresa_lista = bool(
        (cfg.empresa_nombre or "").strip()
        and (cfg.empresa_nombre or "").strip().lower() != "mi empresa"
    )
    clientes_reales = db.query(Cliente).filter(Cliente.es_demo.is_(False)).count()
    presupuestos_reales = db.query(Presupuesto).filter(Presupuesto.es_demo.is_(False)).count()
    partidas = db.query(Partida).count()

    pasos = [
        {
            "clave": "empresa",
            "titulo": "Configura tu empresa",
            "detalle": "Nombre, ubicación, moneda, IVA y datos que aparecerán en el PDF.",
            "completo": empresa_lista,
            "url": "/configuracion",
            "accion": "Revisar datos",
        },
        {
            "clave": "catalogo",
            "titulo": "Revisa o carga tu catálogo",
            "detalle": (
                f"Hay {partidas} partidas disponibles. Comprueba precios y alcance antes de cotizar."
                if partidas
                else "Crea tu primera partida o importa tu catálogo desde Excel."
            ),
            "completo": bool(cfg.onboarding_catalogo_revisado),
            "url": "/recorrido/catalogo-revisado",
            "metodo": "post",
            "accion": "Abrir catálogo",
        },
        {
            "clave": "cliente",
            "titulo": "Crea un cliente real",
            "detalle": "Los clientes de demostración no cuentan para completar este paso.",
            "completo": clientes_reales > 0,
            "url": "/clientes/nuevo",
            "accion": "Crear cliente",
        },
        {
            "clave": "presupuesto",
            "titulo": "Crea tu primer presupuesto",
            "detalle": "Añade capítulos, cantidades y precios; todo seguirá siendo editable.",
            "completo": presupuestos_reales > 0,
            "url": "/presupuestos/nuevo",
            "accion": "Crear presupuesto",
        },
        {
            "clave": "pdf",
            "titulo": "Descarga el primer PDF",
            "detalle": "Revísalo antes de compartirlo con el cliente.",
            "completo": bool(cfg.onboarding_pdf_descargado),
            "url": "/presupuestos",
            "accion": "Ver presupuestos",
        },
    ]
    completados = sum(1 for paso in pasos if paso["completo"])
    return {
        "pasos": pasos,
        "completados": completados,
        "total": len(pasos),
        "porcentaje": round(completados * 100 / len(pasos)),
        "completo": completados == len(pasos),
        "modo": cfg.onboarding_modo or "",
        "presupuesto_demo": db.query(Presupuesto).filter(Presupuesto.es_demo.is_(True)).first(),
    }
