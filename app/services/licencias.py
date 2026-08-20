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

import os
from datetime import date, datetime, timedelta

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..models import (
    ESTADOS_LICENCIA,
    ORIGENES_LICENCIA,
    Licencia,
    Membresia,
    Organizacion,
    Usuario,
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


def vence_cadena(licencias, hoy: date) -> date | None:
    """Último día del acceso continuo que cubre ``hoy``.

    Al renovar con días por delante, la licencia nueva se encadena a
    continuación (empieza al día siguiente del vencimiento anterior), de modo
    que el acceso real llega hasta el final de la cadena, no hasta el
    vencimiento de la primera licencia: si quedan 4 días y se añade 1 mes,
    quedan ~34 días, no 4.

    Fusiona intervalos contiguos o solapados (misma regla que usa
    ``crear_licencia``: un día de hueco rompe la cadena) y devuelve el final
    del intervalo que contiene a ``hoy``. Devuelve ``None`` si hoy no está
    cubierto. Las licencias canceladas rompen la cadena porque no se cuentan.
    """
    activas = sorted(
        (
            lic
            for lic in licencias
            if lic.estado == "activa" and lic.vence >= hoy
        ),
        key=lambda lic: (lic.inicio, lic.vence),
    )
    if not activas:
        return None
    intervalos: list[list[date]] = []
    for licencia in activas:
        if not intervalos or licencia.inicio > intervalos[-1][1] + timedelta(days=1):
            intervalos.append([licencia.inicio, licencia.vence])
        elif licencia.vence > intervalos[-1][1]:
            intervalos[-1][1] = licencia.vence
    for inicio, vence in intervalos:
        if inicio <= hoy <= vence:
            return vence
    return None


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


def crear_licencia_hasta(
    db: Session,
    *,
    organizacion_id: int,
    vence: date,
    importe: float = 0.0,
    moneda: str = "USD",
    metodo_cobro: str = "",
    referencia: str = "",
    notas: str = "",
    operador_email: str = "",
    hoy: date | None = None,
) -> Licencia:
    """Concede una licencia nueva con fecha de vencimiento explícita.

    Igual que :func:`crear_licencia`, pero para fechas que no salen de una
    duración fija (p. ej. el ``current_period_end`` de una suscripción de
    Stripe). Se encadena tras la licencia activa más lejana, como las demás.
    """
    hoy = hoy or date.today()
    _exigir_organizacion(db, organizacion_id)

    vence = vence or date.today()
    if vence < hoy:
        raise GestionLicenciaError("La fecha de vencimiento ya pasó.")
    if (vence - hoy).days > MAXIMO_DIAS:
        raise GestionLicenciaError(
            f"Una licencia no puede superar {MAXIMO_DIAS} días."
        )

    try:
        importe = float(importe or 0)
    except (TypeError, ValueError):
        raise GestionLicenciaError("El importe no es válido.") from None
    if importe < 0:
        raise GestionLicenciaError("El importe no puede ser negativo.")
    if importe <= 0:
        raise GestionLicenciaError("Una licencia de pago necesita un importe.")

    # Encadena tras la licencia activa más lejana, si la hay.
    vigente_hasta = max(
        (
            lic.vence
            for lic in licencias_de_organizacion(db, organizacion_id, hoy=hoy)
            if lic.estado == "activa" and lic.vence >= hoy
        ),
        default=None,
    )
    inicio = vigente_hasta + timedelta(days=1) if vigente_hasta else hoy
    if vence < inicio:
        raise GestionLicenciaError(
            "La fecha de vencimiento no llega a cubrir un día nuevo de acceso."
        )

    licencia = Licencia(
        organizacion_id=organizacion_id,
        estado="activa",
        origen="pago",
        inicio=inicio,
        vence=vence,
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


def extender_licencia_hasta(
    licencia: Licencia, vence: date, hoy: date | None = None
) -> bool:
    """Extiende una licencia existente hasta ``vence``, si es más lejana.

    Devuelve ``True`` si cambió algo y ``False`` si ya cubría esa fecha (lo que
    hace idempotente la renovación). Si estaba vencida y la nueva fecha la
    vuelve a cubrir, la reactiva.
    """
    hoy = hoy or date.today()
    if licencia.estado == "cancelada":
        raise GestionLicenciaError("La licencia está cancelada y no se renueva.")
    vence = vence or date.today()
    if licencia.vence >= vence:
        return False
    licencia.vence = vence
    if licencia.estado == "vencida" and vence >= hoy:
        licencia.estado = "activa"
    return True


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


def suspender_organizacion(
    db: Session,
    *,
    organizacion_id: int,
    motivo: str = "",
    operador_email: str = "",
    hoy: date | None = None,
) -> list[Licencia]:
    """Corta el acceso de una organización **ya**, en una sola operación.

    Cancelar licencia por licencia no basta para cortar el acceso: al
    encadenarse las renovaciones, una organización puede tener varias activas
    y quedarse dentro por la siguiente de la cadena. Esta función cancela
    todas las que cubren hoy o empiezan más adelante, que es lo que el
    operador quiere decir cuando pulsa «suspender».

    Devuelve las licencias canceladas (vacío si no había ninguna que cortar).
    """
    hoy = hoy or date.today()
    _exigir_organizacion(db, organizacion_id)

    afectadas = [
        licencia
        for licencia in licencias_de_organizacion(db, organizacion_id, hoy=hoy)
        if licencia.estado == "activa" and licencia.vence >= hoy
    ]
    if not afectadas:
        raise GestionLicenciaError(
            "Esa organización no tiene ningún acceso vigente que suspender."
        )

    for licencia in afectadas:
        cancelar_licencia(
            db,
            licencia_id=licencia.id,
            motivo=motivo,
            operador_email=operador_email,
        )
    return afectadas


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
        # El vencimiento mostrado es el final de la cadena completa, no el de
        # la primera licencia: renovar con días por delante suma el tiempo.
        vence_total = vence_cadena(licencias, hoy) if vigente else None
        dias_restantes = (
            max((vence_total - hoy).days, 0) if vence_total else 0
        )
        filas.append(
            {
                "organizacion": organizacion,
                "licencias": licencias,
                "vigente": vigente,
                "vence": vence_total,
                "dias_restantes": dias_restantes,
                "por_vencer": bool(vence_total and dias_restantes <= dias_aviso),
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


# ---------------------------------------------------------------------------
# Corte automático de acceso (E1-060, segunda parte)
# ---------------------------------------------------------------------------
#
# La exigencia es un interruptor del despliegue, no del código: hasta que el
# titular lo activa, el producto funciona como siempre. Al activarlo, las
# organizaciones sin licencia vigente pierden el acceso a sus pantallas de
# trabajo (los datos no se tocan: al renovar, todo sigue donde estaba).


def exigencia_licencia_activada() -> bool:
    """``COTIZAT_EXIGIR_LICENCIA`` activa el corte automático de acceso.

    Valor por omisión: **desactivado**. Es una decisión de negocio del
    despliegue (Vercel), como `COTIZAT_OPERADORES`: no hay pantalla para
    encenderla y solo surte efecto en el backend web (PostgreSQL); la
    instalación de escritorio jamás exige licencia.
    """
    valor = os.environ.get("COTIZAT_EXIGIR_LICENCIA", "").strip().lower()
    return valor in {"1", "true", "on", "si", "sí"}


def organizacion_tiene_acceso(
    db: Session, organizacion_id: int, *, hoy: date | None = None
) -> bool:
    """Indica si la organización puede usar la aplicación hoy.

    En PostgreSQL pregunta a ``cotizat_security.organization_has_license``,
    la función SECURITY DEFINER de la revisión ``b7c4a9e2d31f``: la sesión de
    un cliente no puede leer ``licencias`` (RLS de operador), así que el corte
    no podría consultar la tabla directamente. La función devuelve un simple
    booleano y solo sirve para la organización del propio claim de sesión.

    En SQLite —escritorio y pruebas— la consulta directa es suficiente: no
    hay RLS y la tabla está al alcance del proceso.
    """
    if db.get_bind().dialect.name == "postgresql":
        try:
            resultado = db.execute(
                text("SELECT cotizat_security.organization_has_license(:org)"),
                {"org": int(organizacion_id)},
            ).scalar()
            return bool(resultado)
        except Exception:
            try:
                db.rollback()
            except Exception:
                pass
            return False
    return licencia_vigente(db, organizacion_id, hoy=hoy) is not None


def resumen_licencia_cliente(
    db: Session, organizacion_id: int, *, hoy: date | None = None
) -> dict:
    """Estado del plan visible para la **propia** organización.

    La sesión del cliente no puede leer ``licencias`` (RLS de operador), así
    que en PostgreSQL se consulta una función SECURITY DEFINER que solo
    devuelve la fila de la organización del propio claim de sesión. En SQLite
    (escritorio/pruebas) basta la consulta directa.

    Devuelve ``{activo, plan_label, vence, dias_restantes, metodo_cobro}``.

    **Importante:** esta función **no** hace rollback si la consulta falla. El
    único llamador en el flujo de request es
    :func:`app.database._resumen_licencia_para_request`, que envuelve la
    llamada en ``try/except`` y libera la transacción. Llamarla directamente
    desde otra ruta sin esa protección envenenaría la sesión de psycopg y la
    siguiente consulta del mismo handler fallaría con
    ``InFailedSqlTransaction`` (regresión real en Vercel, 18/08/2026).
    """
    hoy = hoy or date.today()
    if db.get_bind().dialect.name == "postgresql":
        fila = None
        try:
            fila = db.execute(
                text(
                    "SELECT activo, plan_label, vence, dias_restantes, metodo_cobro "
                    "FROM cotizat_security.organization_license_info(:org)"
                ),
                {"org": int(organizacion_id)},
            ).first()
        except Exception as exc:
            # La función puede faltar si la BD no está migrada o el RLS la
            # oculta por un owner incorrecto; se hace rollback para no
            # envenenar la transacción y se intenta un fallback.
            try:
                db.rollback()
            except Exception:
                pass
            # Fallback: si organization_has_license indica acceso, mostramos
            # un plan activo genérico en lugar de "Sin plan" para no confundir
            # al usuario que sí puede usar la app.
            try:
                if organizacion_tiene_acceso(db, organizacion_id, hoy=hoy):
                    return {
                        "activo": True,
                        "plan_label": "Plan activo",
                        "vence": None,
                        "dias_restantes": 0,
                        "metodo_cobro": "",
                    }
            except Exception:
                try:
                    db.rollback()
                except Exception:
                    pass
            return {
                "activo": False,
                "plan_label": "",
                "vence": None,
                "dias_restantes": 0,
                "metodo_cobro": "",
            }
        if fila is None:
            # Sin fila pero quizá el corte aún da acceso (p. ej. función
            # desactualizada que no devuelve fila por un bug de RLS). Si hay
            # acceso, preferimos mostrar activo genérico antes que "Sin plan".
            try:
                if organizacion_tiene_acceso(db, organizacion_id, hoy=hoy):
                    return {
                        "activo": True,
                        "plan_label": "Plan activo",
                        "vence": None,
                        "dias_restantes": 0,
                        "metodo_cobro": "",
                    }
            except Exception:
                try:
                    db.rollback()
                except Exception:
                    pass
            return {
                "activo": False,
                "plan_label": "",
                "vence": None,
                "dias_restantes": 0,
                "metodo_cobro": "",
            }
        return {
            "activo": bool(fila[0]),
            "plan_label": str(fila[1] or ""),
            "vence": fila[2],
            "dias_restantes": int(fila[3] or 0),
            "metodo_cobro": str(fila[4] or ""),
        }

    licencia = licencia_vigente(db, organizacion_id, hoy=hoy)
    if licencia is None:
        return {
            "activo": False,
            "plan_label": "",
            "vence": None,
            "dias_restantes": 0,
            "metodo_cobro": "",
        }
    # La etiqueta y el método salen de la licencia que da acceso hoy; la fecha
    # y los días, del final de la cadena (suma de las renovaciones).
    vence_total = (
        vence_cadena(
            licencias_de_organizacion(db, organizacion_id, hoy=hoy), hoy
        )
        or licencia.vence
    )
    return {
        "activo": True,
        "plan_label": _plan_label_cliente(licencia),
        "vence": vence_total,
        "dias_restantes": max((vence_total - hoy).days, 0),
        "metodo_cobro": licencia.metodo_cobro,
    }


def _plan_label_cliente(licencia: Licencia) -> str:
    if licencia.origen == "pago":
        return {
            89.0: "Plan anual",
            9.99: "Plan mensual",
        }.get(round(licencia.importe, 2), "Plan de pago")
    return {
        "prueba": "Prueba",
        "cortesia": "Cortesía",
        "compensacion": "Compensación",
    }.get(licencia.origen, licencia.origen)


# ---------------------------------------------------------------------------
# Avisos de vencimiento por correo (E1-060, segunda parte)
# ---------------------------------------------------------------------------

#: La nota deja constancia de cada envío y evita repetir el aviso el mismo día.
_MARCA_AVISO = "Aviso de vencimiento enviado"


def correos_administradores(db: Session, organizacion_id: int) -> list[str]:
    """Correos de propietario/administrador activos de la organización.

    En PostgreSQL pasa por ``cotizat_security.organization_admin_emails``
    (revisión ``b7c4a9e2d31f``): las membresías de un cliente están fuera del
    alcance del operador por RLS, así que la función —guardada por la marca
    de operador— es la única vía honesta de conocerlos. En SQLite se usa la
    consulta directa equivalente.
    """
    if db.get_bind().dialect.name == "postgresql":
        filas = db.execute(
            text(
                "SELECT email FROM cotizat_security.organization_admin_emails(:org)"
            ),
            {"org": int(organizacion_id)},
        ).all()
        return [str(fila[0]) for fila in filas if fila and fila[0]]
    filas = (
        db.query(Usuario.email)
        .join(Membresia, Membresia.usuario_id == Usuario.id)
        .filter(
            Membresia.organizacion_id == int(organizacion_id),
            Membresia.activa.is_(True),
            Membresia.rol.in_(["propietario", "administrador"]),
            Usuario.activo.is_(True),
        )
        .order_by(Usuario.id)
        .all()
    )
    return [str(email) for (email,) in filas if email]


def aviso_enviado_hoy(licencia: Licencia, hoy: date) -> bool:
    """Evita mandar dos avisos el mismo día si el operador pulsa dos veces."""
    return f"[{hoy.strftime('%Y-%m-%d')}] {_MARCA_AVISO}" in (licencia.notas or "")


def registrar_aviso_enviado(
    licencia: Licencia, destinatarios: list[str], *, hoy: date
) -> None:
    """Anota el envío en la propia licencia: el registro se audita a sí mismo."""
    nota = (
        f"[{hoy.strftime('%Y-%m-%d')}] {_MARCA_AVISO} a "
        + ", ".join(destinatarios)
    )
    licencia.notas = f"{licencia.notas or ''}\n{nota}".strip()


def enviar_avisos_vencimiento(
    db: Session,
    *,
    remitente,
    dias_aviso: int = 15,
    hoy: date | None = None,
) -> dict:
    """Envía el aviso de vencimiento a las organizaciones que están por vencer.

    Lo dispara el operador desde el panel (no hay trabajos programados en un
    despliegue serverless). ``remitente`` es la función de envío
    (``app.services.email.enviar_aviso_licencia``); se inyecta para poder
    probar el flujo sin red.

    Devuelve un resumen con listas de correos, así el panel puede mostrar
    exactamente qué pasó sin esconder fallos del proveedor.
    ``EmailNotConfigured`` (falta Resend en el despliegue) no se cuenta como
    fallo por organización: se propaga para avisar al operador de que el
    correo no está configurado.

    """
    hoy = hoy or date.today()
    resultado = {
        "avisadas": [],       # (organización, [correos]) con envío confirmado
        "omitidas": [],       # organizaciones ya avisadas hoy
        "sin_correo": [],     # organizaciones sin administrador alcanzable
        "fallidas": [],       # (organización, error) del proveedor de correo
    }
    for fila in resumen_organizaciones(db, hoy=hoy, dias_aviso=dias_aviso):
        licencia = fila["vigente"]
        if not fila["por_vencer"] or licencia is None:
            continue
        nombre = fila["organizacion"].nombre
        if aviso_enviado_hoy(licencia, hoy):
            resultado["omitidas"].append(nombre)
            continue
        destinatarios = correos_administradores(db, fila["organizacion"].id)
        if not destinatarios:
            resultado["sin_correo"].append(nombre)
            continue
        from .email import EmailNotConfigured

        try:
            for destinatario in destinatarios:
                remitente(
                    email=destinatario,
                    organizacion_nombre=nombre,
                    vence=fila["vence"] or licencia.vence,
                    dias_restantes=fila["dias_restantes"],
                )
        except EmailNotConfigured:
            raise
        except Exception as exc:  # el proveedor decide qué lanza
            resultado["fallidas"].append((nombre, str(exc)))
            continue
        registrar_aviso_enviado(licencia, destinatarios, hoy=hoy)
        resultado["avisadas"].append((nombre, destinatarios))
    db.flush()
    return resultado


# ---------------------------------------------------------------------------
# Recordatorios de vencimiento automáticos (cron)
# ---------------------------------------------------------------------------
#
# El aviso anterior (`enviar_avisos_vencimiento`) lo dispara el operador a
# mano y cubre una ventana amplia (15 días). El recordatorio, en cambio, lo
# dispara el programador de Vercel y solo se envía en dos hitos exactos —5 y
# 1 día antes de vencer— para no atosigar al cliente y para que cada hito
# llegue una única vez por licencia.

#: Hitos de aviso: a 5 días (previsión) y a 1 día (última llamada).
RECORDATORIOS_DIAS = (5, 1)

#: Marca estable en `licencias.notas` que evita repetir un mismo hito.
_MARCA_RECORDATORIO = "Recordatorio de vencimiento enviado"


def _marca_recordatorio(dias: int) -> str:
    return f"{_MARCA_RECORDATORIO} ({dias} días)"


def recordatorio_enviado(licencia: Licencia, dias: int) -> bool:
    """Indica si el hito de ``dias`` días ya se envió para esta licencia.

    La marca es por hito y por licencia (no por día): renovar crea una
    licencia nueva sin marca, de modo que el conteo regresivo vuelve a empezar
    correctamente en lugar de heredar el aviso de la licencia anterior.
    """
    return _marca_recordatorio(dias) in (licencia.notas or "")


def registrar_recordatorio_enviado(
    licencia: Licencia, destinatarios: list[str], *, dias: int, hoy: date
) -> None:
    """Anota el hito enviado en la propia licencia (el registro se audita a sí mismo)."""
    nota = (
        f"[{hoy.strftime('%Y-%m-%d')}] {_marca_recordatorio(dias)} a "
        + ", ".join(destinatarios)
    )
    licencia.notas = f"{licencia.notas or ''}\n{nota}".strip()


def enviar_recordatorios_vencimiento(
    db: Session,
    *,
    remitente,
    hoy: date | None = None,
) -> dict:
    """Envía los recordatorios automáticos de vencimiento en sus hitos exactos.

    ``remitente`` es la función de envío
    (``app.services.email.enviar_recordatorio_vencimiento``); se inyecta para
    probar el flujo sin red. Solo avisa a organizaciones cuyo acceso vigente
    vence exactamente a 5 o a 1 días, y una única vez por hito y licencia.

    Devuelve un resumen equivalente al de `enviar_avisos_vencimiento` para que
    el cron pueda devolver qué pasó sin esconder fallos del proveedor.
    """
    hoy = hoy or date.today()
    resultado = {
        "avisadas": [],       # (organización, dias, [correos]) con envío confirmado
        "omitidas": [],       # organizaciones ya avisadas en ese hito
        "sin_correo": [],     # organizaciones sin administrador alcanzable
        "fallidas": [],       # (organización, error) del proveedor de correo
    }
    for fila in resumen_organizaciones(
        db, hoy=hoy, dias_aviso=max(RECORDATORIOS_DIAS)
    ):
        licencia = fila["vigente"]
        if not fila["por_vencer"] or licencia is None:
            continue
        dias = fila["dias_restantes"]
        if dias not in RECORDATORIOS_DIAS:
            continue
        nombre = fila["organizacion"].nombre
        if recordatorio_enviado(licencia, dias):
            resultado["omitidas"].append(nombre)
            continue
        destinatarios = correos_administradores(db, fila["organizacion"].id)
        if not destinatarios:
            resultado["sin_correo"].append(nombre)
            continue
        es_prueba = licencia.origen == "prueba"
        plan_nombre = (
            "Prueba gratuita" if es_prueba else _plan_label_cliente(licencia)
        )
        from .email import EmailNotConfigured

        try:
            for destinatario in destinatarios:
                remitente(
                    email=destinatario,
                    organizacion_nombre=nombre,
                    plan_nombre=plan_nombre,
                    es_prueba=es_prueba,
                    vence=fila["vence"] or licencia.vence,
                    dias_restantes=dias,
                )
        except EmailNotConfigured:
            raise
        except Exception as exc:  # el proveedor decide qué lanza
            resultado["fallidas"].append((nombre, str(exc)))
            continue
        registrar_recordatorio_enviado(licencia, destinatarios, dias=dias, hoy=hoy)
        resultado["avisadas"].append((nombre, dias, destinatarios))
    db.flush()
    return resultado
