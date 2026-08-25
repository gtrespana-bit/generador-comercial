"""Configuración centralizada por entorno (E4-003).

Hasta ahora la configuración se leía ad hoc con ``os.environ`` en cada módulo
(``auth``, ``storage``, ``email``, ``database``…). Cada pieza tenía su propio
resolver y su propia idea de qué falta y qué no. Este módulo no sustituye a
esos resolvers — siguen siendo la capa de validación fina (formato de claves,
URLs, roles) —, sino que concentra tres cosas que antes no existían en ningún
sitio:

1. **El concepto de entorno.** ``development``, ``test`` y ``production``, con
   una detección única y explícita (``COTIZAT_ENV``, luego ``VERCEL_ENV``,
   luego la presencia de pytest, y por omisión desarrollo).

2. **El catálogo único de variables**, incluida la marca de cuáles son
   secretas y cuáles se exigen o recomiendan en cada entorno. Es la fuente de
   verdad de la superficie de configuración; ``.env.example`` la documenta y
   ``variables_secretas()`` puede alimentar la auditoría de datos sensibles.

3. **Validación por entorno.** ``validar()`` devuelve problemas estructurados
   (errores = faltan variables exigidas; avisos = faltan recomendadas) **sin
   valores**: un resumen seguro para el panel del operador o para un chequeo
   de despliegue, sin riesgo de filtrar secretos.

Los resolvers existentes (``SupabaseAuthSettings``, ``StorageSettings``,
``EmailSettings``, ``DatabaseSettings``) conservan su comportamiento; este
módulo es aditivo y no cambia los valores por omisión actuales, que siguen
siendo seguros por omisión.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import os
import sys


class Entorno(Enum):
    DESARROLLO = "development"
    PRUEBAS = "test"
    PRODUCCION = "production"

    @property
    def etiqueta(self) -> str:
        return {
            Entorno.DESARROLLO: "desarrollo",
            Entorno.PRUEBAS: "pruebas",
            Entorno.PRODUCCION: "producción",
        }[self]

    @property
    def es_produccion(self) -> bool:
        return self is Entorno.PRODUCCION


_ALIAS = {
    # production
    "production": Entorno.PRODUCCION,
    "prod": Entorno.PRODUCCION,
    "produccion": Entorno.PRODUCCION,
    "producción": Entorno.PRODUCCION,
    # test
    "test": Entorno.PRUEBAS,
    "testing": Entorno.PRUEBAS,
    "pruebas": Entorno.PRUEBAS,
    "prueba": Entorno.PRUEBAS,
    # development
    "development": Entorno.DESARROLLO,
    "dev": Entorno.DESARROLLO,
    "desarrollo": Entorno.DESARROLLO,
    "local": Entorno.DESARROLLO,
}


def entorno_actual() -> Entorno:
    """Detecta el entorno con una única regla explícita y repetible.

    Prioridad:

    1. ``COTIZAT_ENV`` (valor explícito del despliegue).
    2. ``VERCEL_ENV``: solo ``production`` cuenta como producción; ``preview``
       y ``development`` se tratan como no-producción a propósito, para que un
       preview de Vercel nunca active las exigencias duras de producción.
    3. Si la suite de pruebas está cargada (``pytest``), entorno de pruebas.
    4. Por omisión, desarrollo (escritorio local o arranque sin más señales).
    """
    crudo = os.environ.get("COTIZAT_ENV", "").strip().lower()
    if crudo in _ALIAS:
        return _ALIAS[crudo]
    vercel = os.environ.get("VERCEL_ENV", "").strip().lower()
    if vercel == "production":
        return Entorno.PRODUCCION
    if "pytest" in sys.modules:
        return Entorno.PRUEBAS
    return Entorno.DESARROLLO


@dataclass(frozen=True)
class Variable:
    """Una variable de entorno documentada en el catálogo central.

    ``secreta`` marca credenciales que nunca deben llegar al navegador ni a los
    logs. ``requerida_en`` / ``recomendada_en`` declaran en qué entornos falta
    y es un error (o solo un aviso) que no esté definida.
    """

    nombre: str
    secreta: bool
    descripcion: str
    requerida_en: frozenset[str] = frozenset()
    recomendada_en: frozenset[str] = frozenset()


_PRODUCCION = frozenset({"production"})

# ---------------------------------------------------------------------------
# Catálogo único de variables (E4-003). Las exigidas en producción coinciden
# con los chequeos de /readyz; las recomendadas degradan con gracia (email →
# enlace en pantalla, contador → memoria por proceso).
# ---------------------------------------------------------------------------
DEFINICIONES: tuple[Variable, ...] = (
    # --- Persistencia -----------------------------------------------------
    Variable(
        "DATABASE_URL",
        True,
        "cadena de conexión PostgreSQL (contiene credenciales)",
        requerida_en=_PRODUCCION,
    ),
    Variable(
        "MIGRATION_DATABASE_URL",
        True,
        "conexión administrativa solo para Alembic; nunca en runtime",
    ),
    # --- Supabase Auth y Storage ------------------------------------------
    Variable(
        "SUPABASE_URL",
        False,
        "origen del proyecto Supabase (Auth y Storage)",
        requerida_en=_PRODUCCION,
    ),
    Variable(
        "SUPABASE_PUBLISHABLE_KEY",
        False,
        "clave publicable de Supabase Auth (pública por diseño)",
        requerida_en=_PRODUCCION,
    ),
    Variable(
        "SUPABASE_SECRET_KEY",
        True,
        "clave service_role del backend de Storage (solo servidor)",
        requerida_en=_PRODUCCION,
    ),
    Variable(
        "SUPABASE_STORAGE_BUCKET",
        False,
        "bucket privado de Storage",
        recomendada_en=_PRODUCCION,
    ),
    # --- Origen público y cookies ----------------------------------------
    Variable(
        "COTIZAT_PUBLIC_URL",
        False,
        "origen HTTPS público autorizado en Supabase",
        requerida_en=_PRODUCCION,
    ),
    Variable(
        "COTIZAT_COOKIE_SECURE",
        False,
        "marcar las cookies de sesión como Secure",
    ),
    Variable(
        "COTIZAT_TRUST_PROXY",
        False,
        "confiar en X-Forwarded-For solo detrás de un proxy que lo sanee",
    ),
    # --- Email transaccional (Resend) -------------------------------------
    Variable(
        "RESEND_API_KEY",
        True,
        "clave de envío de correos transaccionales",
        recomendada_en=_PRODUCCION,
    ),
    Variable(
        "COTIZAT_EMAIL_FROM",
        False,
        "dirección remitente verificada en Resend",
        recomendada_en=_PRODUCCION,
    ),
    # --- Trabajo programado (Vercel Cron) --------------------------------
    Variable(
        "CRON_SECRET",
        True,
        "secreto con el que Vercel autentica las invocaciones del cron",
        recomendada_en=_PRODUCCION,
    ),
    Variable(
        "STRIPE_SECRET_KEY",
        True,
        "clave secreta de Stripe (sk_test_ / sk_live_, solo servidor)",
        recomendada_en=_PRODUCCION,
    ),
    Variable(
        "STRIPE_WEBHOOK_SECRET",
        True,
        "secreto de firma de webhooks de Stripe (whsec_)",
        recomendada_en=_PRODUCCION,
    ),
    Variable(
        "COTIZAT_RESPALDO_AUTOMATICO",
        False,
        "interruptor del respaldo automático diario (E4-021); false lo apaga",
    ),
    Variable(
        "COTIZAT_RESPALDO_RETENCION",
        False,
        "copias diarias que se conservan por organización (E4-021, 14 por omisión)",
    ),
    Variable(
        "COTIZAT_RESPALDO_MAX_MB",
        False,
        "tope por organización del paquete automático en MB (E4-021, 12 por omisión)",
    ),
    # --- Contador de intentos compartido (Upstash) ------------------------
    Variable(
        "UPSTASH_REDIS_REST_URL",
        False,
        "URL REST de la base Upstash",
        recomendada_en=_PRODUCCION,
    ),
    Variable(
        "UPSTASH_REDIS_REST_TOKEN",
        True,
        "token REST de Upstash (solo servidor)",
        recomendada_en=_PRODUCCION,
    ),
    Variable(
        "COTIZAT_REQUIRE_DISTRIBUTED_RATELIMIT",
        False,
        "fallar /readyz si no hay contador compartido en web",
    ),
    # --- Políticas de seguridad y negocio ---------------------------------
    Variable(
        "COTIZAT_REQUIRE_RLS_ROLE",
        False,
        "fallar el arranque si el rol runtime omite RLS",
    ),
    Variable(
        "COTIZAT_EXIGIR_LICENCIA",
        False,
        "cortar el acceso a organizaciones sin licencia vigente",
    ),
    Variable(
        "COTIZAT_STORAGE_BACKEND",
        False,
        "backend de Storage (local o supabase)",
    ),
    Variable(
        "COTIZAT_OPERADORES",
        False,
        "correos autorizados a administrar licencias (separados por comas)",
    ),
    Variable(
        "COTIZAT_FRAME_ANCESTORS",
        False,
        "origen extra permitido en la política de frames (CSP)",
    ),
    Variable(
        "COTIZAT_LOG_JSON",
        False,
        "emitir los logs como objetos JSON",
    ),
    # --- Identidad y datos locales ----------------------------------------
    Variable(
        "COTIZAT_LEGAL_ENTITY",
        False,
        "razón social publicada en legales y recibos",
    ),
    Variable(
        "COTIZAT_SUPPORT_EMAIL",
        False,
        "dirección de soporte publicada",
    ),
    Variable(
        "COTIZAT_GA_ID",
        False,
        "ID de medición GA4 (G-XXXX…) para la etiqueta de audiencia",
    ),
    Variable(
        "COTIZAT_DATA_DIR",
        False,
        "directorio de datos en modo desarrollo",
    ),
    Variable(
        "COTIZAT_DB",
        False,
        "ruta del archivo SQLite local",
    ),
    Variable(
        "PRESUPUESTOS_DB",
        False,
        "alias heredado de la ruta SQLite",
    ),
    Variable(
        "COTIZAT_ORGANIZATION_ID",
        False,
        "organización activa en SQLite local (compatibilidad)",
    ),
    Variable(
        "COTIZAT_ENV",
        False,
        "entorno explícito: development, test o production",
    ),
    # --- Inteligencia Artificial y Asistente ------------------------------
    Variable(
        "GROQ_API_KEY",
        True,
        "clave de API gratuita de Groq para el asistente de IA (solo servidor)",
    ),
    Variable(
        "COTIZAT_IA_MODEL",
        False,
        "modelo del asistente de IA (por omisión openai/gpt-oss-120b)",
    ),
)


def variables_secretas() -> frozenset[str]:
    """Nombres de las variables que contienen credenciales.

    Útil para auditar: cualquier sitio que las imprima o las envíe al navegador
    es una filtración, sin importar el entorno.
    """
    return frozenset(v.nombre for v in DEFINICIONES if v.secreta)


def secretos_configurados() -> dict[str, bool]:
    """Mapa nombre → si está definido, para cada variable secreta.

    Devuelve solo booleanos (nunca los valores), de modo que es seguro
    exponerlo en un panel o en un log.
    """
    return {
        v.nombre: bool(os.environ.get(v.nombre, "").strip())
        for v in DEFINICIONES
        if v.secreta
    }


@dataclass(frozen=True)
class Problema:
    gravedad: str  # "error" | "aviso"
    mensaje: str

    def to_dict(self) -> dict[str, str]:
        return {"gravedad": self.gravedad, "mensaje": self.mensaje}


@dataclass(frozen=True)
class ResultadoValidacion:
    entorno: Entorno
    problemas: tuple[Problema, ...]

    @property
    def errores(self) -> tuple[Problema, ...]:
        return tuple(p for p in self.problemas if p.gravedad == "error")

    @property
    def avisos(self) -> tuple[Problema, ...]:
        return tuple(p for p in self.problemas if p.gravedad == "aviso")

    @property
    def ok(self) -> bool:
        return not self.errores


def validar(entorno: Entorno | None = None) -> ResultadoValidacion:
    """Comprueba la configuración mínima del entorno, sin revelar valores.

    Una variable exigida y ausente es un **error** (en producción haría que el
    despliegue no deba recibir tráfico); una recomendada y ausente es un
    **aviso** (la función degrada con gracia). En desarrollo y pruebas no hay
    exigencias ni recomendaciones: el objetivo es no obstaculizar el trabajo
    local.
    """
    entorno = entorno or entorno_actual()
    problemas: list[Problema] = []
    for variable in DEFINICIONES:
        if os.environ.get(variable.nombre, "").strip():
            continue
        if entorno.value in variable.requerida_en:
            problemas.append(
                Problema(
                    "error",
                    f"Falta {variable.nombre}: {variable.descripcion}.",
                )
            )
        elif entorno.value in variable.recomendada_en:
            problemas.append(
                Problema(
                    "aviso",
                    f"Sin {variable.nombre}: {variable.descripcion}.",
                )
            )
    return ResultadoValidacion(entorno, tuple(problemas))


def resumen_configuracion(entorno: Entorno | None = None) -> dict:
    """Resumen seguro de la configuración para el panel del operador.

    Incluye el entorno, qué secretos están definidos (booleano) y los problemas
    de validación. Nunca contiene valores de credenciales.
    """
    entorno = entorno or entorno_actual()
    validacion = validar(entorno)
    return {
        "entorno": entorno.value,
        "entorno_etiqueta": entorno.etiqueta,
        "secretos": secretos_configurados(),
        "problemas": [p.to_dict() for p in validacion.problemas],
    }
