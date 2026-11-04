"""Primer inicio y progreso hasta el primer presupuesto real en PDF."""
from datetime import datetime

from sqlalchemy.orm import Session

from ..models import Cliente, Configuracion, Partida, Presupuesto, asegurar_config
from ..paises import MAX_LONGITUD_ETIQUETA_FISCAL
from ..seeds import sembrar_catalogo, sembrar_demo, sembrar_productos, sembrar_recetas

MODO_DEMO = "demo"
MODO_LIMPIO = "limpio"
MODOS_VALIDOS = {MODO_DEMO, MODO_LIMPIO}


class ErrorOnboarding(ValueError):
    """Datos incompletos o incoherentes al finalizar el primer inicio."""


def _configuracion(db: Session) -> Configuracion:
    asegurar_config(db)
    try:
        return db.query(Configuracion).first()
    except Exception as exc:
        # Fallback si la columna del último merge aún no existe (deploy sin migrate)
        msg = str(exc).lower()
        if "recorrido_inicial_oculto" not in msg and "undefinedcolumn" not in msg:
            raise
        try:
            db.rollback()
        except Exception:
            pass
        from sqlalchemy.orm import defer

        cfg = db.query(Configuracion).options(defer(Configuracion.recorrido_inicial_oculto)).first()
        if cfg is not None and "recorrido_inicial_oculto" not in cfg.__dict__:
            cfg.__dict__["recorrido_inicial_oculto"] = False
        return cfg


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


def completar_onboarding(
    db: Session, datos: dict, modo: str, idioma: str = "es"
) -> Configuracion:
    """Guarda la empresa y aplica, una sola vez, demo o instalación limpia."""
    cfg = _configuracion(db)
    if cfg.onboarding_completado:
        raise ErrorOnboarding("El primer inicio ya fue completado.")

    modo = str(modo or "").strip().lower()
    if modo not in MODOS_VALIDOS:
        raise ErrorOnboarding("Elige el catálogo de CotizaT o empezar con tus propias partidas.")
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
    etiqueta = (
        str(datos.get("etiqueta_id_fiscal") or "RIF").strip()[
            :MAX_LONGITUD_ETIQUETA_FISCAL
        ]
        or "RIF"
    )
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
        if not cfg.semilla_catalogo_aplicada:
            raise ErrorOnboarding(
                "No se ha podido cargar el catálogo de CotizaT. "
                "Reintenta en unos minutos; tu configuración está guardada."
            )
        sembrar_productos(db, idioma)
        sembrar_recetas(db)
        # El país decide el ejemplo: precios, moneda, IVA y jerga del mercado
        # que la persona acaba de elegir. Antes solo viajaba el idioma y el
        # ejemplo salía siempre venezolano.
        sembrar_demo(db, idioma, cfg.empresa_pais)
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
    presupuestos_reales = (
        db.query(Presupuesto).filter(Presupuesto.es_demo.is_(False)).count()
    )
    # El ejemplo del alta, mientras siga siendo ejemplo, no completa el paso.
    # En cuanto el usuario lo duplica, la copia es suya y el paso se cumple.
    ejemplo_sembrado = (
        db.query(Presupuesto)
        .filter(
            Presupuesto.es_demo.is_(True),
            Presupuesto.es_ejemplo.is_(True),
        )
        .first()
    )
    partidas = db.query(Partida).count()

    # Las tarifas mandan en el importe: el generador compone cada precio con
    # lo que cuesta aquí un oficial, un peón o el metro de arena. Una empresa
    # que paga 15 US$/h y otra que paga 25 US$/h DEBEN cotizar distinto, así
    # que confirmar las tarifas es el primer paso real del producto: sin él,
    # el primer presupuesto sale con precios de otro mercado y el margen se
    # pierde sin que nadie lo note.
    tarifas = _estado_tarifas(db, cfg)

    # Orden nuevo (02/11/2026). Antes: empresa → catálogo → cliente →
    # presupuesto → PDF. El 17 % de las cuentas (7 de 41) llegó al presupuesto
    # y solo el 5 % al PDF, con el 98 % habiendo abierto la herramienta: se
    # caían justo al final, después de tres pasos de preparación. Ahora el
    # presupuesto va primero porque quien tiene un ejemplo cargado **ya lo
    # tiene**: abrirlo y cambiarle el nombre al cliente es el camino corto.
    pasos = [
        {
            "clave": "tarifas",
            "titulo": "Confirma tus tarifas",
            "detalle": tarifas["detalle"],
            "completo": tarifas["completo"],
            "url": "/recursos/revisar",
            "accion": "Revisar tarifas" if tarifas["completo"] else "Revisar mis precios",
        },
        {
            "clave": "presupuesto",
            "titulo": "Abre tu presupuesto y hazlo tuyo",
            "detalle": (
                "Ya está montado con partidas, cantidades y precios reales. "
                "Cámbiale el cliente y el título: el resto te sirve."
                if ejemplo_sembrado
                else "Crea tu primer presupuesto: añade capítulos, cantidades y precios."
            ),
            "completo": presupuestos_reales > 0,
            "url": (
                f"/presupuestos/{ejemplo_sembrado.id}"
                if ejemplo_sembrado
                else "/presupuestos/nuevo"
            ),
            "accion": "Abrir mi presupuesto" if ejemplo_sembrado else "Crear presupuesto",
        },
        {
            "clave": "pdf",
            "titulo": "Descarga el PDF",
            "detalle": "Es lo que le vas a enseñar al cliente. Revísalo antes de enviarlo.",
            "completo": bool(cfg.onboarding_pdf_descargado),
            "url": (
                f"/presupuestos/{ejemplo_sembrado.id}#documento"
                if ejemplo_sembrado
                else "/presupuestos"
            ),
            "accion": "Descargar PDF",
        },
        {
            "clave": "empresa",
            "titulo": "Deja tus datos en el PDF",
            "detalle": "Nombre, ubicación, moneda, IVA y datos de contacto que aparecen en el documento.",
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
            "titulo": "Pon el nombre de tu cliente",
            "detalle": "Si duplicaste el ejemplo, ya tienes un cliente real: cámbiale el nombre y los datos.",
            "completo": clientes_reales > 0,
            "url": "/clientes/nuevo",
            "accion": "Crear cliente",
        },
    ]
    completados = sum(1 for paso in pasos if paso["completo"])
    return {
        "pasos": pasos,
        "tarifas": tarifas,
        "completados": completados,
        "total": len(pasos),
        "porcentaje": round(completados * 100 / len(pasos)),
        "completo": completados == len(pasos),
        "modo": cfg.onboarding_modo or "",
        "presupuesto_demo": (
            db.query(Presupuesto).filter(Presupuesto.es_demo.is_(True)).first()
        ),
        "ejemplo_convertible": ejemplo_sembrado,
    }


def _estado_tarifas(db: Session, cfg: Configuracion) -> dict:
    """Cuántas tarifas del catálogo siguen siendo referencia y no precio propio.

    Se lee del servicio de revisión, que ya distingue «tiene precio» de «la
    empresa confirmó que es el suyo». Aun así el paso también se cierra con la
    marca de la configuración: quien confirma en bloque sin tocar ningún precio
    no debe seguir viendo el paso pendiente.
    """
    vacio = {
        "completo": bool(getattr(cfg, "onboarding_precios_revisados", False)),
        "pendientes": 0,
        "mano_obra": 0,
        "total": 0,
        "detalle": "Comprueba que la mano de obra y los materiales básicos están a tus precios.",
    }
    try:
        from ..services.traduccion import codigo_desde_pais
        from .revision_precios import resumen_revision

        organizacion_id = int(db.info.get("organizacion_id") or 0)
        pais = codigo_desde_pais(getattr(cfg, "empresa_pais", "") or "") or "VE"
        resumen = resumen_revision(db, organizacion_id=organizacion_id, pais=pais)
    except Exception:
        return vacio
    if not resumen.get("total"):
        # Instalación limpia: no hay catálogo, así que no hay tarifas que
        # confirmar. El paso se da por bueno (no se puede pedir revisar una
        # lista vacía) y su detalle dice cuándo aparecerá.
        return {
            **vacio,
            "completo": True,
            "detalle": (
                "Aún no tienes tarifas: aparecerán aquí en cuanto crees tu "
                "primera partida o cargues tu catálogo."
            ),
        }
    pendientes = int(resumen.get("pendientes") or 0)
    mano_obra = int(resumen.get("mano_obra_pendientes") or 0)
    completo = bool(vacio["completo"]) or pendientes == 0
    if pendientes == 0:
        detalle = (
            f"Tus {resumen['total']} tarifas están confirmadas: el generador ya "
            "cotiza con tus precios, no con una media de mercado."
        )
    else:
        detalle = f"{pendientes} de {resumen['total']} tarifas siguen siendo referencia"
        if mano_obra:
            detalle += f" ({mano_obra} de mano de obra)"
        detalle += (
            ". Es lo que separa un presupuesto rentable de uno que trabaja "
            "por debajo de coste."
        )
    return {
        "completo": completo,
        "pendientes": pendientes,
        "mano_obra": mano_obra,
        "total": int(resumen.get("total") or 0),
        "detalle": detalle,
    }
