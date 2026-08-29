"""Administración de la web pública y del producto (Fase 3).

Da al operador control sobre contenido (publicar/descartar), avisos/banners,
changelog y feature flags, sin editar producción directamente. Todos los
escritores usan ``get_operator_db`` y solo escriben cuando la sesión es
operador (RLS de PostgreSQL + ruta admin).

El módulo **nunca** abre datos de tenant ni desactiva el aislamiento.
"""
from __future__ import annotations

import hashlib
import json
import logging
import secrets
from datetime import date, datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import (
    ApiKeyOperador,
    AvisoWeb,
    ContenidoWeb,
    CrmCliente,
    FeatureFlag,
    Organizacion,
    ReleaseWeb,
    VistaGuardada,
)

log = logging.getLogger("cotizat")

TIPOS_AVISO = ("info", "mantenimiento", "legal", "version", "estado")
NIVELES_AVISO = ("info", "warning", "danger")

ESTADOS_AVISO_ETIQUETA = {
    "info": "Información",
    "mantenimiento": "Mantenimiento",
    "legal": "Legal",
    "version": "Versión",
    "estado": "Estado",
}


class GestionWebError(RuntimeError):
    """La operación sobre contenido/avisos/releases/flags no es válida."""


# ---------------------------------------------------------------------------
# Contenido web (C1/C2): borrador → publicar/descartar
# ---------------------------------------------------------------------------

def _contenido_o_raise(db: Session, clave: str) -> ContenidoWeb:
    fila = db.query(ContenidoWeb).filter(ContenidoWeb.clave == clave).one_or_none()
    if fila is None:
        raise GestionWebError(f"La clave de contenido «{clave}» no existe.")
    return fila


def claves_contenido_disponibles() -> list[dict]:
    """Catálogo de claves editables; se crean al primer guardado."""
    return [
        {
            "clave": "landing.hero",
            "nombre": "Hero de la landing",
            "descripcion": "Título, subtítulo y CTA principal que se ven en /.",
        },
        {
            "clave": "landing.outcomes",
            "nombre": "Beneficios de la landing",
            "descripcion": "Los 4 beneficios destacados bajo el hero.",
        },
        {
            "clave": "seo.software-presupuestos",
            "nombre": "SEO · software de presupuestos",
            "descripcion": "title y description de /software-presupuestos.",
        },
        {
            "clave": "seo.apu",
            "nombre": "SEO · APU",
            "descripcion": "title y description de /apu.",
        },
        {
            "clave": "seo.remodelacion",
            "nombre": "SEO · remodelación",
            "descripcion": "title y description de /remodelacion.",
        },
    ]


def listar_contenido(db: Session) -> list[dict]:
    """Lista las claves del catálogo con su borrador y publicado."""
    filas = {c.clave: c for c in db.query(ContenidoWeb).all()}
    salida = []
    for ficha in claves_contenido_disponibles():
        fila = filas.get(ficha["clave"])
        salida.append({
            **ficha,
            "id": fila.id if fila else None,
            "borrador": _leer_json(fila.borrador) if fila else {},
            "publicado": _leer_json(fila.publicado) if fila and fila.publicado else {},
            "publicado_at": fila.publicado_at if fila else None,
            "publicado_por": fila.publicado_por if fila else "",
        })
    return salida


def guardar_contenido(
    db: Session,
    *,
    clave: str,
    campos: dict,
    operador_email: str,
) -> ContenidoWeb:
    """Guarda el borrador (aún no visible al público)."""
    clave = (clave or "").strip()
    if clave not in {c["clave"] for c in claves_contenido_disponibles()}:
        raise GestionWebError("La clave de contenido indicada no es editable.")
    if not isinstance(campos, dict):
        raise GestionWebError("El contenido debe ser un objeto.")
    limpio = {}
    for k, v in list(campos.items())[:30]:
        if not isinstance(v, (str, int, float, bool, list, dict)):
            continue
        limpio[str(k)[:60]] = v
    texto = json.dumps(limpio, ensure_ascii=False, separators=(",", ":"))[:20000]

    fila = db.query(ContenidoWeb).filter(ContenidoWeb.clave == clave).one_or_none()
    if fila is None:
        fila = ContenidoWeb(clave=clave, borrador=texto)
        db.add(fila)
    else:
        fila.borrador = texto
        fila.updated_at = datetime.utcnow()
    fila.updated_by = str(operador_email or "").lower()[:254]
    db.flush()
    return fila


def publicar_contenido(
    db: Session, *, clave: str, operador_email: str
) -> ContenidoWeb:
    """Publica el borrador: a partir de aquí sí lo sirve la web pública."""
    fila = _contenido_o_raise(db, clave)
    datos = _leer_json(fila.borrador)
    if not datos:
        raise GestionWebError("No hay borrador para publicar.")
    fila.publicado = json.dumps(datos, ensure_ascii=False, separators=(",", ":"))[:20000]
    fila.publicado_at = datetime.utcnow()
    fila.publicado_por = str(operador_email or "").lower()[:254]
    fila.updated_at = datetime.utcnow()
    fila.updated_by = str(operador_email or "").lower()[:254]
    db.flush()
    return fila


def descartar_contenido(db: Session, *, clave: str) -> ContenidoWeb:
    """Descartar el borrador y volver al contenido publicado (o vacío)."""
    fila = _contenido_o_raise(db, clave)
    fila.borrador = json.dumps(_leer_json(fila.publicado), ensure_ascii=False, separators=(",", ":"))
    fila.updated_at = datetime.utcnow()
    db.flush()
    return fila


# ---------------------------------------------------------------------------
# Avisos web (C4)
# ---------------------------------------------------------------------------

def listar_avisos(db: Session) -> list[AvisoWeb]:
    return db.query(AvisoWeb).order_by(AvisoWeb.created_at.desc(), AvisoWeb.id.desc()).all()


def crear_aviso(
    db: Session,
    *,
    tipo: str,
    nivel: str,
    titulo: str,
    mensaje: str,
    activo: bool = False,
    inicio: date | None = None,
    fin: date | None = None,
    operador_email: str = "",
) -> AvisoWeb:
    tipo = (tipo or "").strip().lower()
    nivel = (nivel or "").strip().lower()
    titulo = (titulo or "").strip()
    if tipo not in TIPOS_AVISO:
        raise GestionWebError("El tipo de aviso no es válido.")
    if nivel not in NIVELES_AVISO:
        raise GestionWebError("El nivel de aviso no es válido.")
    if not titulo:
        raise GestionWebError("El aviso necesita un título.")
    if inicio and fin and fin < inicio:
        raise GestionWebError("La fecha de fin no puede ser anterior al inicio.")
    aviso = AvisoWeb(
        tipo=tipo, nivel=nivel, titulo=titulo[:180],
        mensaje=str(mensaje or "")[:4000], activo=bool(activo),
        inicio=inicio, fin=fin, creado_por=str(operador_email or "").lower()[:254],
    )
    db.add(aviso)
    db.flush()
    return aviso


def actualizar_aviso(
    db: Session, aviso_id: int, *, campos: dict, operador_email: str = ""
) -> AvisoWeb:
    aviso = db.get(AvisoWeb, aviso_id)
    if aviso is None:
        raise GestionWebError("El aviso indicado no existe.")
    if "tipo" in campos:
        valor = str(campos.get("tipo") or "").strip().lower()
        if valor not in TIPOS_AVISO:
            raise GestionWebError("El tipo de aviso no es válido.")
        aviso.tipo = valor
    if "nivel" in campos:
        valor = str(campos.get("nivel") or "").strip().lower()
        if valor not in NIVELES_AVISO:
            raise GestionWebError("El nivel de aviso no es válido.")
        aviso.nivel = valor
    if "titulo" in campos:
        valor = str(campos.get("titulo") or "").strip()
        if not valor:
            raise GestionWebError("El aviso necesita un título.")
        aviso.titulo = valor[:180]
    if "mensaje" in campos:
        aviso.mensaje = str(campos.get("mensaje") or "")[:4000]
    if "activo" in campos:
        aviso.activo = bool(campos.get("activo"))
    if "inicio" in campos:
        aviso.inicio = campos.get("inicio") or None
    if "fin" in campos:
        aviso.fin = campos.get("fin") or None
    if aviso.inicio and aviso.fin and aviso.fin < aviso.inicio:
        raise GestionWebError("La fecha de fin no puede ser anterior al inicio.")
    aviso.updated_at = datetime.utcnow()
    aviso.creado_por = str(operador_email or "").lower()[:254]
    db.flush()
    return aviso


def alternar_aviso(db: Session, aviso_id: int, activo: bool) -> AvisoWeb:
    return actualizar_aviso(db, aviso_id, campos={"activo": activo})


# ---------------------------------------------------------------------------
# Releases / changelog (C5)
# ---------------------------------------------------------------------------

def listar_releases(db: Session) -> list[ReleaseWeb]:
    return db.query(ReleaseWeb).order_by(ReleaseWeb.fecha.desc(), ReleaseWeb.id.desc()).all()


def crear_release(
    db: Session,
    *,
    version: str,
    titulo: str,
    notas: str,
    destacado: bool = False,
    publicado: bool = False,
    fecha: date | None = None,
    operador_email: str = "",
) -> ReleaseWeb:
    version = (version or "").strip()
    titulo = (titulo or "").strip()
    if not version:
        raise GestionWebError("La versión es obligatoria.")
    if not titulo:
        raise GestionWebError("El título es obligatorio.")
    release = ReleaseWeb(
        version=version[:30], titulo=titulo[:200], notas=str(notas or "")[:8000],
        destacado=bool(destacado), publicado=bool(publicado),
        fecha=fecha or date.today(), creado_por=str(operador_email or "").lower()[:254],
    )
    db.add(release)
    db.flush()
    return release


def alternar_release(db: Session, release_id: int, publicado: bool) -> ReleaseWeb:
    release = db.get(ReleaseWeb, release_id)
    if release is None:
        raise GestionWebError("La versión indicada no existe.")
    release.publicado = bool(publicado)
    release.updated_at = datetime.utcnow()
    db.flush()
    return release


# ---------------------------------------------------------------------------
# Feature flags (D3)
# ---------------------------------------------------------------------------

_FEATURE_FLAGS_CONOCIDOS = {
    "onboarding": "Onboarding guiado",
    "planos": "Editor de planos",
    "ia": "Asistente IA",
    "cohortes": "Cohortes y retención",
    "cms": "CMS de landing desde el panel",
}


def listar_flags(db: Session) -> list[dict]:
    filas = {f.clave: f for f in db.query(FeatureFlag).all()}
    salida = []
    for clave in _FEATURE_FLAGS_CONOCIDOS:
        fila = filas.get(clave)
        salida.append({
            "clave": clave,
            "nombre": _FEATURE_FLAGS_CONOCIDOS[clave],
            "activo": bool(fila.activo) if fila else False,
            "descripcion": fila.descripcion if fila else "",
        })
    return salida


def actualizar_flag(
    db: Session, *, clave: str, activo: bool, operador_email: str
) -> FeatureFlag:
    clave = (clave or "").strip()
    if clave not in _FEATURE_FLAGS_CONOCIDOS:
        raise GestionWebError("El feature flag indicado no existe.")
    fila = db.query(FeatureFlag).filter(FeatureFlag.clave == clave).one_or_none()
    if fila is None:
        fila = FeatureFlag(clave=clave, activo=bool(activo))
        db.add(fila)
    else:
        fila.activo = bool(activo)
        fila.updated_at = datetime.utcnow()
    fila.updated_by = str(operador_email or "").lower()[:254]
    db.flush()
    return fila


def flag_activo(db: Session, clave: str) -> bool:
    fila = db.query(FeatureFlag).filter(FeatureFlag.clave == clave).one_or_none()
    return bool(fila.activo) if fila else False


# ---------------------------------------------------------------------------
# API keys de operador (A6): solo se guarda el hash
# ---------------------------------------------------------------------------

def _hash_clave(clave: str) -> str:
    return hashlib.sha256(clave.encode("utf-8")).hexdigest()


def listar_api_keys(db: Session) -> list[dict]:
    return [
        {
            "id": k.id,
            "nombre": k.nombre,
            "activo": k.activo and k.revoked_at is None,
            "scopes": k.scopes_lista(),
            "creada_por": k.creada_por,
            "last_used_at": k.last_used_at,
            "revoked_at": k.revoked_at,
        }
        for k in db.query(ApiKeyOperador).order_by(
            ApiKeyOperador.created_at.desc(), ApiKeyOperador.id.desc()
        ).all()
    ]


def crear_api_key(
    db: Session, *, nombre: str, scopes: list[str], operador_email: str
) -> tuple[ApiKeyOperador, str]:
    """Crea una clave y devuelve la token en claro UNA sola vez."""
    nombre = (nombre or "").strip()
    if not nombre:
        raise GestionWebError("Indica un nombre para la clave.")
    scopes = [str(s).strip().lower() for s in (scopes or []) if str(s).strip()]
    token = "cotizat_" + secrets.token_urlsafe(32)
    clave = ApiKeyOperador(
        nombre=nombre[:100],
        clave_hash=_hash_clave(token),
        scopes=json.dumps(scopes, ensure_ascii=False, separators=(",", ":")),
        creada_por=str(operador_email or "").lower()[:254],
    )
    db.add(clave)
    db.flush()
    return clave, token


def revocar_api_key(db: Session, api_key_id: int) -> ApiKeyOperador:
    clave = db.get(ApiKeyOperador, api_key_id)
    if clave is None:
        raise GestionWebError("La API key indicada no existe.")
    clave.activo = False
    clave.revoked_at = datetime.utcnow()
    db.flush()
    return clave


def verificar_api_key(db: Session, token: str) -> ApiKeyOperador | None:
    """Valida una token contra su hash y actualiza ``last_used_at``."""
    if not token or not token.startswith("cotizat_"):
        return None
    clave = db.query(ApiKeyOperador).filter(
        ApiKeyOperador.clave_hash == _hash_clave(token),
        ApiKeyOperador.activo.is_(True),
        ApiKeyOperador.revoked_at.is_(None),
    ).one_or_none()
    if clave is None:
        return None
    clave.last_used_at = datetime.utcnow()
    db.flush()
    return clave


def _leer_json(texto) -> dict:
    try:
        datos = json.loads(texto or "{}")
    except (TypeError, ValueError):
        return {}
    return datos if isinstance(datos, dict) else {}


# ---------------------------------------------------------------------------
# CRM ligero (B4)
# ---------------------------------------------------------------------------

ESTADOS_CRM = ("lead", "prueba", "activo", "riesgo", "inactivo")
ESTADOS_CRM_ETIQUETA = {
    "lead": "Lead",
    "prueba": "En prueba",
    "activo": "Activo",
    "riesgo": "En riesgo",
    "inactivo": "Inactivo",
}


def listar_crm(db: Session) -> list[dict]:
    """Lista el CRM junto a la organización (sin exponer datos de negocio)."""
    filas_crm = {c.organizacion_id: c for c in db.query(CrmCliente).all()}
    organizaciones = db.query(Organizacion).order_by(Organizacion.nombre, Organizacion.id).all()
    salida = []
    for org in organizaciones:
        crm = filas_crm.get(org.id)
        salida.append({
            "organizacion": org,
            "crm": crm,
            "estado": crm.estado if crm else "",
            "estado_etiqueta": ESTADOS_CRM_ETIQUETA.get(crm.estado, "Sin asignar") if crm else "Sin asignar",
            "proximo_contacto": crm.proximo_contacto if crm else None,
            "notas": crm.notas if crm else "",
        })
    return salida


def guardar_crm(
    db: Session,
    *,
    organizacion_id: int,
    estado: str,
    proximo_contacto: date | None,
    notas: str,
    operador_email: str,
) -> CrmCliente:
    org = db.get(Organizacion, organizacion_id)
    if org is None:
        raise GestionWebError("La organización indicada no existe.")
    estado = (estado or "").strip().lower()
    if estado not in ESTADOS_CRM:
        raise GestionWebError("El estado comercial no es válido.")
    fila = db.query(CrmCliente).filter(
        CrmCliente.organizacion_id == organizacion_id
    ).one_or_none()
    if fila is None:
        fila = CrmCliente(
            organizacion_id=organizacion_id,
            estado=estado,
            proximo_contacto=proximo_contacto,
            notas=str(notas or "")[:4000],
        )
        db.add(fila)
    else:
        fila.estado = estado
        fila.proximo_contacto = proximo_contacto
        fila.notas = str(notas or "")[:4000]
        fila.updated_at = datetime.utcnow()
    fila.updated_by = str(operador_email or "").lower()[:254]
    db.flush()
    return fila


def resumen_crm(db: Session) -> dict:
    try:
        filas = listar_crm(db)
    except Exception:
        return {"total": 0, "por_estado": {}, "proximos": []}
    por_estado = {}
    for fila in filas:
        estado = fila["estado"] or "sin_asignar"
        por_estado[estado] = por_estado.get(estado, 0) + 1
    hoy = date.today()
    proximos = [
        f for f in filas
        if f["proximo_contacto"] and f["proximo_contacto"] <= hoy
    ]
    return {
        "total": len(filas),
        "por_estado": por_estado,
        "proximos": proximos,
    }


# ---------------------------------------------------------------------------
# Vistas guardadas persistentes (A5 completo)
# ---------------------------------------------------------------------------

_MODULOS_VISTA = ("clientes", "cobros", "renovaciones", "compras", "automatizaciones")


def listar_vistas(db: Session, modulo: str = "") -> list[VistaGuardada]:
    consulta = db.query(VistaGuardada)
    if modulo:
        consulta = consulta.filter(VistaGuardada.modulo == modulo)
    return consulta.order_by(VistaGuardada.modulo, VistaGuardada.nombre).all()


def guardar_vista(
    db: Session,
    *,
    modulo: str,
    nombre: str,
    filtros: dict,
    columnas: list,
    operador_email: str,
) -> VistaGuardada:
    modulo = (modulo or "").strip().lower()
    nombre = (nombre or "").strip()
    if modulo not in _MODULOS_VISTA:
        raise GestionWebError("El módulo de vista no es válido.")
    if not nombre:
        raise GestionWebError("Indica un nombre para la vista.")
    if not isinstance(filtros, dict):
        raise GestionWebError("Los filtros deben ser un objeto.")
    if not isinstance(columnas, list):
        raise GestionWebError("Las columnas deben ser una lista.")
    vista = VistaGuardada(
        nombre=nombre[:120],
        modulo=modulo,
        filtros=json.dumps(filtros, ensure_ascii=False, separators=(",", ":"))[:20000],
        columnas=json.dumps([str(c)[:40] for c in columnas[:40]], ensure_ascii=False, separators=(",", ":")),
        creada_por=str(operador_email or "").lower()[:254],
    )
    db.add(vista)
    db.flush()
    return vista


def eliminar_vista(db: Session, vista_id: int) -> None:
    vista = db.get(VistaGuardada, vista_id)
    if vista is None:
        raise GestionWebError("La vista indicada no existe.")
    db.delete(vista)
    db.flush()


# ---------------------------------------------------------------------------
# Lectura pública (RLS deja ver solo publicado/activo)
# ---------------------------------------------------------------------------

def contenido_publico(db: Session, clave: str) -> dict:
    fila = db.query(ContenidoWeb).filter(ContenidoWeb.clave == clave).one_or_none()
    if fila is None or not fila.publicado:
        return {}
    return _leer_json(fila.publicado)


def avisos_publicos(db: Session, hoy: date | None = None) -> list[AvisoWeb]:
    hoy = hoy or date.today()
    return db.query(AvisoWeb).filter(
        AvisoWeb.activo.is_(True),
        (AvisoWeb.inicio.is_(None) | (AvisoWeb.inicio <= hoy)),
        (AvisoWeb.fin.is_(None) | (AvisoWeb.fin >= hoy)),
    ).order_by(AvisoWeb.created_at.desc(), AvisoWeb.id.desc()).all()


def releases_publicas(db: Session) -> list[ReleaseWeb]:
    return db.query(ReleaseWeb).filter(
        ReleaseWeb.publicado.is_(True)
    ).order_by(ReleaseWeb.fecha.desc(), ReleaseWeb.id.desc()).all()
