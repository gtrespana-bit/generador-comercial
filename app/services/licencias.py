"""Registro interno de licencias del producto (E1-060).

Reglas de negocio del panel de operador: conceder acceso, renovarlo, regalar un
período de prueba o compensar una incidencia. Todo lo que cobra o regala el
titular pasa por aquí, así que el módulo prioriza dos cosas: que el historial
sea reconstruible y que nada quede en un estado ambiguo.

Decisiones que conviene no revertir sin pensarlo
------------------------------------------------
- **Las licencias no se borran, se cancelan.** El historial es la única fuente
  para saber qué se cobró; un DELETE lo destruiría. La migración ni siquiera
  concede el privilegio.
- **Solo `origen='pago'` cuenta como ingreso.** Una prueba o una cortesía valen
  0: mezclarlas inflaría la facturación al mirar el panel.
- **El estado se deriva de la fecha al leer**, no por un proceso programado.
  Sin trabajos en segundo plano (Vercel serverless), una licencia «activa» con
  fecha pasada sería una mentira silenciosa.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from ..models import (
    ESTADOS_LICENCIA,
    ORIGENES_LICENCIA,
    Licencia,
    Organizacion,
)


class GestionLicenciaError(RuntimeError):
    """La operación sobre licencias no respeta las reglas del registro."""


#: Duraciones ofrecidas por el panel. Cubren los planes publicados y los gestos
#: comerciales habituales (una semana de prueba, un mes de cortesía).
DURACIONES = {
    "7d": ("7 días de prueba", timedelta(days=7)),
    "1m": ("1 mes", timedelta(days=30)),
    "3m": ("3 meses", timedelta(days=90)),
    "6m": ("6 meses", timedelta(days=180)),
    "1a": ("1 año", timedelta(days=365)),
}

#: Tope de seguridad: evita que un error de tecleo conceda acceso indefinido.
MAXIMO_DIAS = 366 * 3


def _exigir_organizacion(db: Session, organizacion_id: int) -> Organizacion:
    organizacion = db.get(Organizacion, organizacion_id)
    if organizacion is None:
        raise GestionLicenciaError("La organización indicada no existe.")
    return organizacion


def _normalizar_estado(licencia: Licencia, hoy: date) -> None:
    """Marca como vencida la licencia activa cuya fecha ya pasó.

    Se hace al leer porque no hay proceso programado que lo haga por la noche.
    """
    if licencia.estado == "activa" and licencia.vence < hoy:
        licencia.estado = "vencida"


def crear_licencia(
    db: Session,
    *,
    organizacion_id: int,
    origen: str,
    duracion: str = "",
    dias: int = 0,
    importe: float = 0.0,
    moneda: str = "USD",
    metodo_cobro: str = "",
    referencia: str = "",
    notas: str = "",
    operador_email: str,
    inicio: date | None = None,
    hoy: date | None = None,
) -> Licencia:
    """Concede una licencia nueva a una organización.

    Si la organización ya tiene una licencia vigente, la nueva **encadena** a
    continuación en vez de solaparse: renovar a alguien que aún tiene días no
    debe regalarle ni quitarle tiempo.
    """
    hoy = hoy or date.today()
    _exigir_organizacion(db, organizacion_id)

    origen = str(origen or "").strip().lower()
    if origen not in ORIGENES_LICENCIA:
        raise GestionLicenciaError("El origen de la licencia no es válido.")

    if duracion:
        if duracion not in DURACIONES:
            raise GestionLicenciaError("La duración indicada no es válida.")
        delta = DURACIONES[duracion][1]
    else:
        try:
            dias = int(dias)
        except (TypeError, ValueError):
            raise GestionLicenciaError("Indica un número de días válido.") from None
        if dias < 1:
            raise GestionLicenciaError("La licencia debe durar al menos un día.")
        delta = timedelta(days=dias)

    if delta.days > MAXIMO_DIAS:
        raise GestionLicenciaError(
            f"Una licencia no puede superar {MAXIMO_DIAS} días."
        )

    try:
        importe = float(importe or 0)
    except (TypeError, ValueError):
        raise GestionLicenciaError("El importe no es válido.") from None
    if importe < 0:
        raise GestionLicenciaError("El importe no puede ser negativo.")
    if origen != "pago" and importe:
        raise GestionLicenciaError(
            "Solo las licencias de pago llevan importe; una cortesía vale 0."
        )
    if origen == "pago" and importe <= 0:
        raise GestionLicenciaError("Una licencia de pago necesita un importe.")

    if inicio is None:
        # Encadena tras la licencia vigente más lejana, si la hay.
        vigente_hasta = max(
            (
                lic.vence
                for lic in licencias_de_organizacion(db, organizacion_id, hoy=hoy)
                if lic.estado == "activa" and lic.vence >= hoy
            ),
            default=None,
        )
        inicio = vigente_hasta + timedelta(days=1) if vigente_hasta else hoy

    licencia = Licencia(
        organizacion_id=organizacion_id,
        estado="activa",
        origen=origen,
        inicio=inicio,
        vence=inicio + delta - timedelta(days=1),
        importe=importe,
        moneda=str(moneda or "USD").strip()[:10] or "USD",
        metodo_cobro=str(metodo_cobro or "").strip()[:80],
        referencia=str(referencia or "").strip()[:150],
        notas=str(notas or "").strip(),
        creada_por_email=str(operador_email or "").strip().lower()[:254],
    )
    db.add(licencia)
    db.flush()
    return licencia


def cancelar_licencia(
    db: Session,
    *,
    licencia_id: int,
    motivo: str = "",
    operador_email: str = "",
    hoy: datetime | None = None,
) -> Licencia:
    """Cancela una licencia dejando constancia de quién y por qué.

    No borra la fila: el registro debe seguir explicando qué se cobró.
    """
    licencia = db.get(Licencia, licencia_id)
    if licencia is None:
        raise GestionLicenciaError("La licencia indicada no existe.")
    if licencia.estado == "cancelada":
        raise GestionLicenciaError("Esa licencia ya estaba cancelada.")
    marca = (hoy or datetime.utcnow()).strftime("%Y-%m-%d")
    licencia.estado = "cancelada"
    nota = f"[{marca}] Cancelada por {operador_email or 'operador'}"
    if motivo.strip():
        nota += f": {motivo.strip()}"
    licencia.notas = f"{licencia.notas}\n{nota}".strip()
    db.flush()
    return licencia


def licencias_de_organizacion(
    db: Session, organizacion_id: int, *, hoy: date | None = None
) -> list[Licencia]:
    """Historial de una organización, de la más reciente a la más antigua."""
    hoy = hoy or date.today()
    licencias = (
        db.query(Licencia)
        .filter(Licencia.organizacion_id == organizacion_id)
        .order_by(Licencia.inicio.desc(), Licencia.id.desc())
        .all()
    )
    for licencia in licencias:
        _normalizar_estado(licencia, hoy)
    return licencias


def licencia_vigente(
    db: Session, organizacion_id: int, *, hoy: date | None = None
) -> Licencia | None:
    """Licencia que da acceso hoy, si existe."""
    hoy = hoy or date.today()
    for licencia in licencias_de_organizacion(db, organizacion_id, hoy=hoy):
        if licencia.vigente(hoy):
            return licencia
    return None


def resumen_organizaciones(
    db: Session, *, hoy: date | None = None, dias_aviso: int = 15
) -> list[dict]:
    """Una fila por organización con su estado de licencia.

    Incluye a las organizaciones **sin licencia**: son precisamente las que hay
    que mirar (alguien se registró y nunca se le concedió acceso).
    """
    hoy = hoy or date.today()
    organizaciones = (
        db.query(Organizacion).order_by(Organizacion.nombre, Organizacion.id).all()
    )
    todas = db.query(Licencia).all()
    for licencia in todas:
        _normalizar_estado(licencia, hoy)

    por_organizacion: dict[int, list[Licencia]] = {}
    for licencia in todas:
        por_organizacion.setdefault(licencia.organizacion_id, []).append(licencia)

    filas = []
    for organizacion in organizaciones:
        licencias = sorted(
            por_organizacion.get(organizacion.id, []),
            key=lambda l: (l.inicio, l.id),
            reverse=True,
        )
        vigente = next((l for l in licencias if l.vigente(hoy)), None)
        filas.append(
            {
                "organizacion": organizacion,
                "licencias": licencias,
                "vigente": vigente,
                "dias_restantes": vigente.dias_restantes(hoy) if vigente else 0,
                "por_vencer": bool(
                    vigente and vigente.dias_restantes(hoy) <= dias_aviso
                ),
                "ingresos": sum(l.importe for l in licencias if l.es_ingreso),
            }
        )
    return filas


def totales(filas: list[dict]) -> dict:
    """Cifras de cabecera del panel."""
    return {
        "organizaciones": len(filas),
        "con_licencia": sum(1 for f in filas if f["vigente"]),
        "sin_licencia": sum(1 for f in filas if not f["vigente"]),
        "por_vencer": sum(1 for f in filas if f["por_vencer"]),
        "ingresos": sum(f["ingresos"] for f in filas),
    }
