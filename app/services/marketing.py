"""Secuencia de correos de marketing de CotizaT (E1 — embudo).

Donde los recordatorios de vencimiento avisan de que el acceso se acaba,
estos correos **enseñan a usar el producto** para que la prueba no se pierda
sin crear ni un presupuesto real. El embudo del 02/11/2026 lo explica:

- 41 cuentas, 4 pagadoras (9,8 %). 40/41 abrieron la app, pero solo 7/41
  crearon un presupuesto real y 2 lo enviaron. La rotura no está en el
  registro, está en «hacer el primer presupuesto útil».

La secuencia va por días de prueba y se personaliza con el progreso del
recorrido (``estado_recorrido_inicial``): quien ya configuró tarifas no
recibe el consejo de tarifas, quien ya descargó el PDF no recibe el de PDF.

Idempotencia y respeto
----------------------
- Cada plantilla se envía **una sola vez por organización**. La unicidad
  ``(organizacion_id, plantilla)`` de ``envios_marketing`` lo garantiza aunque
  el cron se ejecute dos veces el mismo día.
- Un envío fallido también deja marca (``estado='fallido'``) para no
  reintentar en bucle un buzón que rebota.
- Quien pide la baja (enlace firmado en cada correo) deja de recibir
  **marketing** —bienvenida, consejos, win-back, campañas—, nunca
  transaccionales (invitaciones, recibos, avisos de vencimiento).

Baja
----
El enlace de baja lleva un token ``base64url(email).firma`` donde la firma
es HMAC-SHA256 del email con un secreto del despliegue. No hay sesión, no hay
base previa: quien recibe el correo puede darse de baja sin entrar.
"""

from __future__ import annotations

import base64
import datetime
import hashlib
import hmac
import logging
import os
import re
from datetime import date, datetime as dt

from sqlalchemy.orm import Session

from ..models import BajaMarketing, EnvioMarketing

logger = logging.getLogger("cotizat.marketing")

# ---------------------------------------------------------------------------
# Firma de baja (un clic, sin sesión)
# ---------------------------------------------------------------------------

def _secreto_baja() -> str:
    """Secreto estable para firmar la baja.

    Se resuelve en orden: variable dedicada, secreto del cron, JWT de Supabase,
    ``SECRET_KEY`` genérica y, en último recurso, una cadena fija que hace que
    el token siga siendo verificable en entornos de test sin configuración.
    """
    for nombre in (
        "COTIZAT_MARKETING_SECRET",
        "CRON_SECRET",
        "SUPABASE_JWT_SECRET",
        "SUPABASE_SECRET_KEY",
        "SECRET_KEY",
    ):
        valor = str(os.environ.get(nombre, "") or "").strip()
        if valor:
            return valor
    return "cotizat-marketing-inseguro-solo-tests"


def _b64url_encode(texto: str) -> str:
    return base64.urlsafe_b64encode(texto.encode("utf-8")).decode("ascii").rstrip("=")


def _b64url_decode(token: str) -> str:
    # Restaura padding
    pad = "=" * (-len(token) % 4)
    return base64.urlsafe_b64decode(token + pad).decode("utf-8")


def _firma(email_normalizado: str) -> str:
    mac = hmac.new(
        _secreto_baja().encode("utf-8"),
        email_normalizado.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return base64.urlsafe_b64encode(mac).decode("ascii").rstrip("=")


def token_baja(email: str) -> str:
    """Token público para el enlace de baja de ``email``."""
    normalizado = str(email or "").strip().lower()
    if not normalizado:
        return ""
    return f"{_b64url_encode(normalizado)}.{_firma(normalizado)}"


def verificar_token_baja(token: str) -> str | None:
    """Devuelve el email si ``token`` es válido, ``None`` si no."""
    token = str(token or "").strip()
    if "." not in token:
        return None
    prefix, sig = token.rsplit(".", 1)
    if not prefix or not sig:
        return None
    try:
        email = _b64url_decode(prefix).strip().lower()
    except Exception:
        return None
    if not email or "@" not in email:
        return None
    esperado = _firma(email)
    if not hmac.compare_digest(sig, esperado):
        return None
    return email


def url_baja(email: str) -> str:
    """URL absoluta de baja para ``email`` (pie de cada correo)."""
    from ..auth import public_app_url

    try:
        base = public_app_url("/baja-marketing")
    except Exception:
        base = "https://cotizat.online/baja-marketing"
    tok = token_baja(email)
    return f"{base}?token={tok}" if tok else base


# ---------------------------------------------------------------------------
# Consultas de baja y de historial
# ---------------------------------------------------------------------------

def es_baja(db: Session, email: str) -> bool:
    normalizado = str(email or "").strip().lower()
    if not normalizado:
        return False
    return (
        db.query(BajaMarketing).filter(BajaMarketing.email == normalizado).first()
        is not None
    )


def registrar_baja(db: Session, email: str, *, origen: str = "enlace") -> bool:
    """Guarda la baja de ``email``. True si era nueva, False si ya existía."""
    normalizado = str(email or "").strip().lower()
    if not normalizado or "@" not in normalizado:
        return False
    if es_baja(db, normalizado):
        return False
    db.add(BajaMarketing(email=normalizado, origen=str(origen or "enlace")[:20]))
    db.flush()
    return True


def quitar_baja(db: Session, email: str) -> bool:
    """Retira la baja de ``email`` (panel de operador). True si existía."""
    normalizado = str(email or "").strip().lower()
    fila = db.query(BajaMarketing).filter(BajaMarketing.email == normalizado).first()
    if not fila:
        return False
    db.delete(fila)
    db.flush()
    return True


def historial_enviado(db: Session, organizacion_id: int, plantilla: str) -> bool:
    return (
        db.query(EnvioMarketing)
        .filter(
            EnvioMarketing.organizacion_id == int(organizacion_id),
            EnvioMarketing.plantilla == str(plantilla or "").strip(),
        )
        .first()
        is not None
    )


def _registrar_envio(
    db: Session,
    *,
    organizacion_id: int,
    email: str,
    plantilla: str,
    estado: str = "enviado",
    proveedor_id: str = "",
) -> None:
    # Upsert idempotente: si ya existe (org, plantilla) no duplica, solo
    # actualiza estado/proveedor. La unicidad lo protege en carrera.
    plantilla = str(plantilla or "").strip()
    if not plantilla:
        return
    existente = (
        db.query(EnvioMarketing)
        .filter(
            EnvioMarketing.organizacion_id == int(organizacion_id),
            EnvioMarketing.plantilla == plantilla,
        )
        .first()
    )
    if existente:
        existente.estado = str(estado or "enviado")[:20]
        if proveedor_id:
            existente.proveedor_id = str(proveedor_id)[:120]
        existente.enviado_en = dt.utcnow()
        return
    db.add(
        EnvioMarketing(
            organizacion_id=int(organizacion_id),
            email=str(email or "")[:254],
            plantilla=plantilla,
            estado=str(estado or "enviado")[:20],
            proveedor_id=str(proveedor_id or "")[:120],
        )
    )


# ---------------------------------------------------------------------------
# Catálogo de la secuencia (qué se manda y cuándo)
# ---------------------------------------------------------------------------

# Cada entrada: cuándo (días desde inicio de prueba) y qué plantilla de
# ``app/services/email.py`` dispara. El nombre de plantilla coincide con el
# nombre del archivo de plantilla ``app/templates/emails/marketing_*.html``.

PLANTILLAS_SECUENCIA = (
    # Durante la prueba (0–6): enseñar a llegar al primer PDF.
    {
        "plantilla": "bienvenida",
        "dia": 0,
        "titulo": "Bienvenida — tu prueba de 7 días",
        "descripcion": "Qué es CotizaT y cuál es tu primer paso (abrir el presupuesto de ejemplo).",
        "grupo": "secuencia",
    },
    {
        "plantilla": "consejo_tarifas",
        "dia": 1,
        "titulo": "Ajusta tus tarifas en 2 minutos",
        "descripcion": "Por qué tus precios de mano de obra deciden tu margen — y cómo revisarlos.",
        "grupo": "secuencia",
    },
    {
        "plantilla": "consejo_presupuesto",
        "dia": 2,
        "titulo": "Tu primer presupuesto en 5 minutos",
        "descripcion": "Del presupuesto de ejemplo al tuyo: duplica, cambia cliente y cantidades.",
        "grupo": "secuencia",
    },
    {
        "plantilla": "consejo_pdf",
        "dia": 4,
        "titulo": "El PDF que tu cliente va a firmar",
        "descripcion": "Descarga, revisa y envía tu propuesta: es donde se cierra el trabajo.",
        "grupo": "secuencia",
    },
    {
        "plantilla": "cierre_prueba",
        "dia": 6,
        "titulo": "Mañana vence tu prueba — qué pasa después",
        "descripcion": "Recordatorio amable con CTA a planes y testimonios. Solo si aún no pagaste.",
        "grupo": "secuencia",
    },
    # Win-back: después de la prueba, para quien no compró.
    {
        "plantilla": "winback_7",
        "dia": 14,  # 7 días después de vencer (prueba 7d → día 14 desde alta)
        "titulo": "¿Te echamos una mano?",
        "descripcion": "Vuelve con un clic: qué te faltó y cómo lo resolvemos.",
        "grupo": "winback",
    },
    {
        "plantilla": "winback_30",
        "dia": 37,  # ~30 días después de vencer
        "titulo": "Novedades de CotizaT + oferta",
        "descripcion": "Qué ha mejorado desde que nos dejaste y por qué volver ahora.",
        "grupo": "winback",
    },
)

PLANTILLA_A_DIA = {e["plantilla"]: e["dia"] for e in PLANTILLAS_SECUENCIA}

# Plantillas que exigen personalización por progreso de onboarding.
# Si el paso ya está completo, se salta el correo: no se quiere ser pesado.
PLANTILLA_A_PASO = {
    "consejo_tarifas": "tarifas",
    "consejo_presupuesto": "presupuesto",
    "consejo_pdf": "pdf",
}

# Campañas manuales del operador (fuera de secuencia). No tienen día: se
# disparan a mano desde el panel a un segmento. Cada una tiene su marca de
# idempotencia por organización igual que la secuencia.
PLANTILLAS_CAMPANA = (
    {
        "plantilla": "novedades",
        "titulo": "Novedades del producto",
        "descripcion": "Qué hay de nuevo en CotizaT que tus clientes no tienen.",
        "grupo": "campana",
    },
    {
        "plantilla": "oferta",
        "titulo": "Oferta / promoción",
        "descripcion": "Descuento o plan especial por tiempo limitado.",
        "grupo": "campana",
    },
    {
        "plantilla": "consejo_obra",
        "titulo": "Consejo de obra / productividad",
        "descripcion": "Consejos prácticos de presupuestos que posicionan la marca.",
        "grupo": "campana",
    },
)

# Todo lo que conoce el sistema (secuencia + campañas).
TODAS_PLANTILLAS = {e["plantilla"]: e for e in (*PLANTILLAS_SECUENCIA, *PLANTILLAS_CAMPANA)}

# Alias públicos para plantillas anteriores que el panel aún reconoce.
ALIAS_PLANTILLAS = {
    "dia1_tarifas": "consejo_tarifas",
    "dia2_presupuesto": "consejo_presupuesto",
    "dia4_pdf": "consejo_pdf",
    "dia6_cierre": "cierre_prueba",
}


def _normalizar_plantilla(nombre: str) -> str:
    clave = str(nombre or "").strip().lower()
    if not clave:
        return ""
    if clave in ALIAS_PLANTILLAS:
        clave = ALIAS_PLANTILLAS[clave]
    return clave


# ---------------------------------------------------------------------------
# Contexto común de los correos de marketing (CTA, baja, marca)
# ---------------------------------------------------------------------------

def _origen_app_url(path: str) -> str:
    from ..auth import public_app_url

    try:
        return public_app_url(path)
    except Exception:
        return f"https://cotizat.online{path}"


def _contexto_base(email: str, organizacion_nombre: str) -> dict:
    return {
        "organizacion_nombre": str(organizacion_nombre or "").strip() or "tu empresa",
        "cta_url": _origen_app_url("/inicio"),
        "cta_label": "Abrir CotizaT",
        "baja_url": url_baja(email),
        "soporte_email": str(os.environ.get("SUPPORT_EMAIL", "") or "soporte@cotizat.online").strip()
        or "soporte@cotizat.online",
    }


# ---------------------------------------------------------------------------
# Envío inmediato: bienvenida (alta de organización)
# ---------------------------------------------------------------------------

def enviar_bienvenida(
    db: Session,
    *,
    organizacion_id: int,
    organizacion_nombre: str,
    email: str,
    remitente=None,
    idioma: str = "es",
) -> dict:
    """Envía la bienvenida a ``email``. Best-effort, nunca lanza si falla Resend.

    Se llama desde ``crear_organizacion_web`` tras el commit. Si el correo ya
    se envió a esta organización, o si ``email`` está de baja, no hace nada.
    Devuelve ``{enviadas, omitidas, fallidas}`` para auditoría.
    """
    return _enviar_plantillas_a_destinos(
        db,
        organizacion_id=organizacion_id,
        organizacion_nombre=organizacion_nombre,
        plantillas=["bienvenida"],
        destinatarios=[str(email or "").strip()],
        remitente=remitente,
        idioma=idioma,
    )


# ---------------------------------------------------------------------------
# Núcleo de envío (inyectable para tests)
# ---------------------------------------------------------------------------

def _enviador_para(plantilla: str):
    from . import email as email_mod

    mapa = {
        "bienvenida": email_mod.enviar_bienvenida_por_email,
        "consejo_tarifas": email_mod.enviar_marketing_consejo_tarifas,
        "consejo_presupuesto": email_mod.enviar_marketing_consejo_presupuesto,
        "consejo_pdf": email_mod.enviar_marketing_consejo_pdf,
        "cierre_prueba": email_mod.enviar_marketing_cierre_prueba,
        "winback_7": email_mod.enviar_marketing_winback_7,
        "winback_30": email_mod.enviar_marketing_winback_30,
        "novedades": email_mod.enviar_marketing_novedades,
        "oferta": email_mod.enviar_marketing_oferta,
        "consejo_obra": email_mod.enviar_marketing_consejo_obra,
    }
    fn = mapa.get(str(plantilla or "").strip())
    if not fn:
        raise ValueError(f"Plantilla de marketing desconocida: {plantilla}")
    return fn


def _contexto_para(
    plantilla: str,
    *,
    email: str,
    organizacion_nombre: str,
    organizacion_id: int | None = None,
    db: Session | None = None,
    dias_restantes: int | None = None,
    vence: date | None = None,
    es_prueba: bool = True,
    personalizado: dict | None = None,
) -> dict:
    """Contexto Jinja por plantilla (CTA y copy específico)."""
    base = _contexto_base(email, organizacion_nombre)
    # Personalización por progreso: si el recorrido ya está avanzado, el copy
    # cambia de «haz esto» a «ya vas bien, te queda esto».
    prog = personalizado or {}
    if plantilla == "bienvenida":
        base.update(
            {
                "cta_url": _origen_app_url("/bienvenida"),
                "cta_label": "Empezar ahora",
                "dias_prueba": 7,
                "vence": vence,
            }
        )
    elif plantilla == "consejo_tarifas":
        base.update(
            {
                "cta_url": _origen_app_url("/recursos/revisar"),
                "cta_label": "Revisar mis tarifas",
                "mano_obra_pendiente": prog.get("mano_obra_pendiente", 0),
                "total_tarifas": prog.get("total_tarifas", 0),
            }
        )
    elif plantilla == "consejo_presupuesto":
        # Si hay presupuesto de ejemplo convertible, el CTA lleva directo.
        if prog.get("presupuesto_demo_id"):
            base.update(
                {
                    "cta_url": _origen_app_url(f"/presupuestos/{prog['presupuesto_demo_id']}"),
                    "cta_label": "Abrir mi presupuesto",
                    "tiene_demo": True,
                }
            )
        else:
            base.update(
                {
                    "cta_url": _origen_app_url("/presupuestos/nuevo"),
                    "cta_label": "Crear mi primer presupuesto",
                    "tiene_demo": False,
                }
            )
    elif plantilla == "consejo_pdf":
        base.update(
            {
                "cta_url": _origen_app_url("/presupuestos"),
                "cta_label": "Ver mis presupuestos",
                "pdf_descargado": bool(prog.get("pdf_descargado")),
            }
        )
    elif plantilla == "cierre_prueba":
        base.update(
            {
                "cta_url": _origen_app_url("/pago"),
                "cta_label": "Ver planes",
                "dias_restantes": dias_restantes if dias_restantes is not None else 1,
                "vence": vence,
                "es_prueba": es_prueba,
            }
        )
    elif plantilla in ("winback_7", "winback_30"):
        base.update(
            {
                "cta_url": _origen_app_url("/inicio"),
                "cta_label": "Volver a CotizaT",
                "dias_desde_vencimiento": prog.get("dias_desde_vencimiento", 7),
            }
        )
    elif plantilla in ("novedades", "oferta", "consejo_obra"):
        # Campaña manual: el operador decide el CTA al dispararla; aquí cae al genérico.
        base.update(
            {
                "cta_url": prog.get("cta_url") or _origen_app_url("/novedades"),
                "cta_label": prog.get("cta_label") or "Ver novedades",
                "titulo_campana": prog.get("titulo_campana") or "",
                "cuerpo_campana": prog.get("cuerpo_campana") or "",
            }
        )
    return base


def _enviar_plantillas_a_destinos(
    db: Session,
    *,
    organizacion_id: int,
    organizacion_nombre: str,
    plantillas: list[str],
    destinatarios: list[str],
    remitente=None,
    idioma: str = "es",
    contexto_extra: dict | None = None,
) -> dict:
    """Envía ``plantillas`` a cada uno de ``destinatarios``.

    Respeta baja, idempotencia por (org, plantilla) y baja por email. Si
    ``remitente`` es None usa el enviador real de ``app/services/email.py``;
    en tests se inyecta un doble que no toca red.

    Devuelve ``{enviadas, omitidas_baja, omitidas_ya_enviada, fallidas}``.
    """
    plantillas = [_normalizar_plantilla(p) for p in (plantillas or []) if _normalizar_plantilla(p)]
    destinatarios = [str(e or "").strip().lower() for e in (destinatarios or []) if str(e or "").strip()]
    # Deduplica manteniendo orden
    vistos: set[str] = set()
    destinatarios = [e for e in destinatarios if not (e in vistos or vistos.add(e))]

    resultado: dict = {
        "enviadas": [],  # (organizacion, plantilla, email)
        "omitidas_baja": [],
        "omitidas_ya_enviada": [],
        "omitidas_sin_progreso": [],  # paso ya completo
        "fallidas": [],  # (organizacion, plantilla, email, error)
    }
    if not plantillas or not destinatarios or not organizacion_id:
        return resultado

    from .email import EmailNotConfigured

    for plantilla in plantillas:
        # Idempotencia por organización: cada plantilla una vez por empresa.
        if historial_enviado(db, int(organizacion_id), plantilla):
            for em in destinatarios:
                resultado["omitidas_ya_enviada"].append((organizacion_nombre, plantilla, em))
            continue

        # Personalización: si el paso ya está completo, se salta la plantilla
        # para no ser pesado (ej. «revisa tarifas» a quien ya las confirmó).
        paso_clave = PLANTILLA_A_PASO.get(plantilla)
        if paso_clave and contexto_extra and contexto_extra.get(f"paso_{paso_clave}_completo"):
            for em in destinatarios:
                resultado["omitidas_sin_progreso"].append((organizacion_nombre, plantilla, em))
            # Igualmente marca como enviada para no re-evaluar cada día.
            _registrar_envio(
                db,
                organizacion_id=int(organizacion_id),
                email=destinatarios[0] if destinatarios else "",
                plantilla=plantilla,
                estado="omitida_completada",
            )
            continue

        enviador = None
        if remitente is not None:
            # En tests el remitente es un callable genérico: lo envolvemos para
            # que reciba (email, plantilla, contexto).
            enviador = remitente
        else:
            try:
                enviador = _enviador_para(plantilla)
            except ValueError as exc:
                for em in destinatarios:
                    resultado["fallidas"].append((organizacion_nombre, plantilla, em, str(exc)))
                continue

        for email_dest in destinatarios:
            if es_baja(db, email_dest):
                resultado["omitidas_baja"].append((organizacion_nombre, plantilla, email_dest))
                continue

            ctx = _contexto_para(
                plantilla,
                email=email_dest,
                organizacion_nombre=organizacion_nombre,
                organizacion_id=int(organizacion_id),
                db=db,
                dias_restantes=(contexto_extra or {}).get("dias_restantes"),
                vence=(contexto_extra or {}).get("vence"),
                es_prueba=(contexto_extra or {}).get("es_prueba", True),
                personalizado=contexto_extra,
            )
            ctx["idioma"] = str(idioma or "es").strip().lower() or "es"

            try:
                if remitente is not None:
                    # Doble de tests: (email, plantilla, contexto) -> id
                    prov_id = enviador(email=email_dest, plantilla=plantilla, contexto=ctx) or ""
                else:
                    prov_id = enviador(email=email_dest, contexto=ctx, idioma=ctx["idioma"]) or ""
            except EmailNotConfigured:
                raise
            except Exception as exc:
                logger.warning("Marketing %s a %s falló: %s", plantilla, email_dest, exc)
                # Marca fallo para no reintentar en bucle el mismo día; el
                # cron siguiente no lo reintentará por la marca de idempotencia.
                _registrar_envio(
                    db,
                    organizacion_id=int(organizacion_id),
                    email=email_dest,
                    plantilla=plantilla,
                    estado="fallido",
                )
                resultado["fallidas"].append((organizacion_nombre, plantilla, email_dest, str(exc)))
                continue
            else:
                _registrar_envio(
                    db,
                    organizacion_id=int(organizacion_id),
                    email=email_dest,
                    plantilla=plantilla,
                    estado="enviado",
                    proveedor_id=str(prov_id or ""),
                )
                resultado["enviadas"].append((organizacion_nombre, plantilla, email_dest))

    db.flush()
    return resultado


# ---------------------------------------------------------------------------
# Cron diario: secuencia + win-back
# ---------------------------------------------------------------------------

def _progreso_para_personalizar(db: Session, organizacion_id: int) -> dict:
    """Lee el recorrido inicial para personalizar los consejos.

    Se hace best-effort: si la configuración no existe o el servicio falla, se
    devuelve vacío y los correos caen al copy genérico.
    """
    try:
        from ..models import Configuracion
        from .onboarding import estado_recorrido_inicial

        cfg = (
            db.query(Configuracion)
            .filter(Configuracion.organizacion_id == int(organizacion_id))
            .first()
        )
        if not cfg:
            return {}
        estado = estado_recorrido_inicial(db, cfg)
        pasos = {p["clave"]: p for p in estado.get("pasos", [])}
        tarifas = estado.get("tarifas") or {}
        demo = estado.get("ejemplo_convertible") or estado.get("presupuesto_demo")
        return {
            "paso_tarifas_completo": bool(pasos.get("tarifas", {}).get("completo")),
            "paso_presupuesto_completo": bool(pasos.get("presupuesto", {}).get("completo")),
            "paso_pdf_completo": bool(pasos.get("pdf", {}).get("completo")),
            "mano_obra_pendiente": int(tarifas.get("mano_obra") or 0),
            "total_tarifas": int(tarifas.get("total") or 0),
            "pdf_descargado": bool(getattr(cfg, "onboarding_pdf_descargado", False)),
            "presupuesto_demo_id": int(getattr(demo, "id", 0) or 0) if demo else 0,
            "tiene_demo": bool(demo),
        }
    except Exception:
        return {}


def enviar_secuencia_marketing(
    db: Session,
    *,
    remitente=None,
    hoy: date | None = None,
    limite: int = 200,
) -> dict:
    """Cron diario que dispara la secuencia según los días de cada organización.

    - Para cada org con prueba (``pruebas_concedidas`` o ``licencias.origen=prueba``),
      mira cuántos días lleva desde el alta y envía la plantilla del día si toca.
    - Para cada org con licencia vencida hace 7/30 días y sin licencia nueva,
      envía el win-back correspondiente (solo a ex-pruebas, no a ex-pagadores
      que cancelaron a propósito sin más señal).
    - Respeta bajas, idempotencia y pasos ya completados.

    ``remitente`` se inyecta en tests. ``limite`` evita que un despliegue con
    miles de orgs mande miles de correos en un solo cron.

    Devuelve el mismo resumen que los cron de vencimiento para que el endpoint
    pueda devolver qué pasó sin esconder fallos.
    """
    from datetime import timedelta as _td

    from .licencias import correos_administradores

    hoy = hoy or date.today()
    enviadas: list = []
    omitidas_baja: list = []
    omitidas_ya: list = []
    omitidas_completadas: list = []
    sin_correo: list = []
    fallidas: list = []

    # 1) Construir el universo de organizaciones candidatas (prueba o vencida
    #    reciente). Se consulta ``resumen_organizaciones`` que ya resuelve
    #    licencias vigentes/vencidas, y ``pruebas_concedidas`` para el alta real
    #    cuando la licencia de prueba ya expiró hace días.
    from ..models import Licencia, Organizacion, PruebaConcedida

    # Mapa org_id -> (alta_prueba: date, licencia_vigente, licencia_vence)
    altas: dict[int, dict] = {}

    # Altas por licencia vigente (prueba o paga)
    for fila in _resumen_todas(db, hoy=hoy):
        org = fila["organizacion"]
        lic: Licencia | None = fila.get("vigente")
        altas[int(org.id)] = {
            "org": org,
            "vigente": lic,
            "vencimiento": fila.get("vence"),
            "dias_restantes": fila.get("dias_restantes"),
            "por_vencer": bool(fila.get("por_vencer")),
            "nombre": str(getattr(org, "nombre", "") or "").strip() or f"Org {org.id}",
        }

    # Altas por prueba concedida (necesaria para win-back: la licencia ya no
    # es vigente, pero la fecha de alta sigue en pruebas_concedidas).
    for pc in db.query(PruebaConcedida).all():
        oid = int(getattr(pc, "organizacion_id", 0) or 0)
        if not oid or oid in altas and altas[oid].get("vigente"):
            continue
        org = db.get(Organizacion, oid)
        if not org:
            continue
        # Si no estaba en el resumen (sin licencia vigente), añádela con su alta.
        if oid not in altas:
            altas[oid] = {
                "org": org,
                "vigente": None,
                "vencimiento": None,
                "dias_restantes": None,
                "por_vencer": False,
                "nombre": str(getattr(org, "nombre", "") or "").strip() or f"Org {oid}",
            }
        # La fecha de alta real es created_at de la prueba (o inicio de licencia si no hay prueba).
        try:
            alta_fecha = getattr(pc, "created_at", None)
            if alta_fecha:
                altas[oid]["alta_prueba"] = alta_fecha.date() if hasattr(alta_fecha, "date") else alta_fecha
        except Exception:
            pass

    # Si la alta no vino de pruebas_concedidas, usa el inicio de la licencia vigente.
    for oid, info in altas.items():
        if "alta_prueba" not in info:
            lic = info.get("vigente")
            if lic and getattr(lic, "inicio", None):
                info["alta_prueba"] = lic.inicio
            else:
                # Fallback: created_at de la organización (siempre existe).
                try:
                    info["alta_prueba"] = info["org"].created_at.date() if hasattr(info["org"].created_at, "date") else info["org"].created_at
                except Exception:
                    info["alta_prueba"] = hoy

    # 2) Para cada org, determina qué plantilla toca hoy y dispara.
    for oid, info in sorted(altas.items()):
        if len(enviadas) + len(fallidas) >= int(limite or 200):
            break

        alta: date = info.get("alta_prueba") or hoy
        try:
            dias_desde_alta = (hoy - alta).days
        except Exception:
            continue
        if dias_desde_alta < 0:
            continue

        # Qué plantilla toca hoy (una al día, como máximo).
        plantilla_hoy: str | None = None
        for entrada in PLANTILLAS_SECUENCIA:
            if int(entrada["dia"]) == int(dias_desde_alta):
                plantilla_hoy = str(entrada["plantilla"])
                break
        if not plantilla_hoy:
            continue
        # Idempotencia ya vista arriba, pero filtra antes de tocar destinatarios.
        if historial_enviado(db, oid, plantilla_hoy):
            continue

        vigentes = info.get("vigente")
        # Cierre de prueba: solo si aún es prueba por vencer (no a pagadores).
        if plantilla_hoy == "cierre_prueba":
            if not vigentes or getattr(vigentes, "origen", "") != "prueba":
                continue
        # Win-back: solo si ya venció y no hay acceso vigente.
        if plantilla_hoy.startswith("winback"):
            if vigentes is not None:
                continue
            # Y solo si alguna vez tuvo prueba (no a orgs creadas con plan pago directo).
            pc_exists = db.query(PruebaConcedida).filter(PruebaConcedida.organizacion_id == oid).first()
            if not pc_exists:
                continue
            # Y solo si no tiene ninguna licencia de pago posterior (compró y volvió).
            tiene_pago = (
                db.query(Licencia)
                .filter(Licencia.organizacion_id == oid, Licencia.origen == "pago")
                .first()
            )
            if tiene_pago:
                continue

        destinatarios = correos_administradores(db, oid)
        if not destinatarios:
            sin_correo.append(info["nombre"])
            continue

        # Personalización por progreso del recorrido.
        progreso = _progreso_para_personalizar(db, oid)
        vence = info.get("vencimiento")
        # Win-back: días desde vencimiento para el copy.
        if plantilla_hoy.startswith("winback") and vence:
            try:
                progreso["dias_desde_vencimiento"] = max(0, (hoy - vence).days)
            except Exception:
                pass

        contexto_extra = {
            **progreso,
            "dias_restantes": info.get("dias_restantes"),
            "vence": vence,
            "es_prueba": bool(vigentes and getattr(vigentes, "origen", "") == "prueba"),
        }

        res = _enviar_plantillas_a_destinos(
            db,
            organizacion_id=oid,
            organizacion_nombre=info["nombre"],
            plantillas=[plantilla_hoy],
            destinatarios=destinatarios,
            remitente=remitente,
            contexto_extra=contexto_extra,
        )
        enviadas.extend(res["enviadas"])
        omitidas_baja.extend(res["omitidas_baja"])
        omitidas_ya.extend(res["omitidas_ya_enviada"])
        omitidas_completadas.extend(res["omitidas_sin_progreso"])
        fallidas.extend(res["fallidas"])

    return {
        "enviadas": enviadas,
        "omitidas_baja": omitidas_baja,
        "omitidas_ya_enviada": omitidas_ya,
        "omitidas_completada": omitidas_completadas,
        "sin_correo": sin_correo,
        "fallidas": fallidas,
    }


def _resumen_todas(db: Session, hoy: date | None = None):
    """Envuelve ``resumen_organizaciones`` tolerando despliegues sin migración.

    En SQLite de tests la vista puede no existir; en ese caso cae a una consulta
    directa sobre ``organizaciones`` + ``licencias``.
    """
    hoy = hoy or date.today()
    try:
        from .licencias import resumen_organizaciones

        return resumen_organizaciones(db, hoy=hoy, dias_aviso=60)
    except Exception:
        # Fallback mínimo: todas las orgs con su licencia vigente si la hay.
        from ..models import Licencia, Organizacion

        from .licencias import licencia_vigente as _lic_vigente

        filas = []
        for org in db.query(Organizacion).all():
            lic = None
            try:
                lic = _lic_vigente(db, int(org.id), hoy=hoy)
            except Exception:
                lic = (
                    db.query(Licencia)
                    .filter(Licencia.organizacion_id == int(org.id), Licencia.estado == "activa")
                    .order_by(Licencia.vence.desc())
                    .first()
                )
                if lic and (lic.vence < hoy or lic.inicio > hoy):
                    lic = None
            filas.append(
                {
                    "organizacion": org,
                    "vigente": lic,
                    "vence": getattr(lic, "vence", None) if lic else None,
                    "dias_restantes": (lic.vence - hoy).days if lic and lic.vence else None,
                    "por_vencer": False,
                }
            )
        return filas


# ---------------------------------------------------------------------------
# Campaña manual del operador (segmento + plantilla)
# ---------------------------------------------------------------------------

SEGMENTOS_CAMPANA = {
    "prueba": "En prueba (con acceso vigente de prueba)",
    "vencidas": "Prueba vencida sin compra",
    "pagadoras": "Con plan de pago activo",
    "todas": "Todas las organizaciones con email",
}


def _orgs_por_segmento(db: Session, segmento: str, hoy: date | None = None) -> list:
    hoy = hoy or date.today()
    segmento = str(segmento or "").strip().lower()
    filas = _resumen_todas(db, hoy=hoy)
    from ..models import Licencia, PruebaConcedida

    if segmento == "prueba":
        return [f for f in filas if f.get("vigente") and getattr(f["vigente"], "origen", "") == "prueba"]
    if segmento == "pagadoras":
        return [f for f in filas if f.get("vigente") and getattr(f["vigente"], "origen", "") == "pago"]
    if segmento == "vencidas":
        # Vencidas = tuvo prueba y hoy no tiene acceso vigente ni plan pago.
        vigentes_ids = {int(f["organizacion"].id) for f in filas if f.get("vigente")}
        candidatas = []
        for pc in db.query(PruebaConcedida).all():
            oid = int(getattr(pc, "organizacion_id", 0) or 0)
            if not oid or oid in vigentes_ids:
                continue
            org = db.get(filas[0]["organizacion"].__class__, oid) if filas else None
            if not org:
                from ..models import Organizacion as _Org

                org = db.get(_Org, oid)
            if not org:
                continue
            # Si tiene plan pago, no es vencida sin compra.
            tiene_pago = (
                db.query(Licencia)
                .filter(Licencia.organizacion_id == oid, Licencia.origen == "pago")
                .first()
            )
            if tiene_pago:
                continue
            candidatas.append({"organizacion": org, "vigente": None})
        return candidatas
    if segmento == "todas":
        return filas
    raise ValueError(f"Segmento desconocido: {segmento}")


def enviar_campana(
    db: Session,
    *,
    plantilla: str,
    segmento: str,
    remitente=None,
    hoy: date | None = None,
    titulo_campana: str = "",
    cuerpo_campana: str = "",
    cta_url: str = "",
    cta_label: str = "",
    limite: int = 500,
) -> dict:
    """Dispara ``plantilla`` de campaña a ``segmento``. Solo operador.

    Cada organización recibe la campaña una vez (idempotencia por plantilla).
    Respeta bajas. Devuelve el mismo resumen que la secuencia.

    El operador elige el copy en el panel: ``titulo_campana``/``cuerpo_campana``/
    ``cta_url``/``cta_label`` viajan en el contexto del email.
    """
    hoy = hoy or date.today()
    plantilla = _normalizar_plantilla(plantilla)
    if plantilla not in {e["plantilla"] for e in PLANTILLAS_CAMPANA}:
        raise ValueError(f"Plantilla de campaña desconocida: {plantilla}")
    from .licencias import correos_administradores

    candidatas = _orgs_por_segmento(db, segmento, hoy=hoy)
    enviadas: list = []
    omitidas_baja: list = []
    omitidas_ya: list = []
    sin_correo: list = []
    fallidas: list = []

    for fila in candidatas:
        if len(enviadas) + len(fallidas) >= int(limite or 500):
            break
        org = fila["organizacion"]
        oid = int(getattr(org, "id", 0) or 0)
        nombre = str(getattr(org, "nombre", "") or "").strip() or f"Org {oid}"
        if historial_enviado(db, oid, plantilla):
            # Campaña: si ya se envió esta plantilla a la org, no repite.
            # El operador puede crear una campaña nueva con otro slug si quiere
            # repetir el mismo tipo de correo con copy distinto.
            omitidas_ya.append(nombre)
            continue
        destinatarios = correos_administradores(db, oid)
        if not destinatarios:
            sin_correo.append(nombre)
            continue
        contexto_extra = {
            "titulo_campana": str(titulo_campana or "").strip(),
            "cuerpo_campana": str(cuerpo_campana or "").strip(),
            "cta_url": str(cta_url or "").strip(),
            "cta_label": str(cta_label or "").strip(),
        }
        res = _enviar_plantillas_a_destinos(
            db,
            organizacion_id=oid,
            organizacion_nombre=nombre,
            plantillas=[plantilla],
            destinatarios=destinatarios,
            remitente=remitente,
            contexto_extra=contexto_extra,
        )
        enviadas.extend(res["enviadas"])
        omitidas_baja.extend(res["omitidas_baja"])
        omitidas_ya.extend(res["omitidas_ya_enviada"])
        fallidas.extend(res["fallidas"])

    return {
        "enviadas": enviadas,
        "omitidas_baja": omitidas_baja,
        "omitidas_ya_enviada": omitidas_ya,
        "sin_correo": sin_correo,
        "fallidas": fallidas,
    }


# ---------------------------------------------------------------------------
# Panel / auditoría
# ---------------------------------------------------------------------------

def resumen_marketing(db: Session) -> dict:
    """Estadísticas para el panel de operador."""
    total_envios = db.query(EnvioMarketing).count()
    total_bajas = db.query(BajaMarketing).count()
    por_plantilla: dict[str, int] = {}
    for fila in db.query(EnvioMarketing.plantilla).all():
        p = str(fila[0] or "")
        por_plantilla[p] = por_plantilla.get(p, 0) + 1
    por_estado: dict[str, int] = {}
    for fila in db.query(EnvioMarketing.estado).all():
        e = str(fila[0] or "")
        por_estado[e] = por_estado.get(e, 0) + 1
    return {
        "total_envios": total_envios,
        "total_bajas": total_bajas,
        "por_plantilla": por_plantilla,
        "por_estado": por_estado,
        "plantillas": [dict(e) for e in PLANTILLAS_SECUENCIA],
        "campanas": [dict(e) for e in PLANTILLAS_CAMPANA],
        "segmentos": dict(SEGMENTOS_CAMPANA),
    }
