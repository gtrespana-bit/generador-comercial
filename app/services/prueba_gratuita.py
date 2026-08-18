"""Concesión automática de la prueba gratuita al crear la primera organización.

Sin esto, exigir licencia (``COTIZAT_EXIGIR_LICENCIA=true``) deja suspendida a
toda organización recién registrada en el mismo segundo del alta: el cliente
paga antes de ver el producto. Con esto, el alta concede 7 días de acceso
completo y el corte solo aparece cuando la prueba se agota.

La regla, en una frase: **una prueba por identidad de correo, para siempre.**

Por qué la defensa vive en la base de datos
-------------------------------------------
La tentación es comprobar en Python «¿ya tuvo prueba este correo?» antes de
insertar. Eso falla exactamente cuando importa: dos altas simultáneas leen
«no» a la vez y ambas conceden. La protección real es la restricción única
sobre ``pruebas_concedidas.email_normalizado``; el código de aquí se limita a
intentar la inserción y a interpretar el choque como «ya la gastó». La
comprobación previa se mantiene solo para dar un mensaje decente en el caso
normal, no como control de seguridad.

Qué **no** hace este módulo
---------------------------
- **No bloquea por IP.** La IP se guarda hasheada y sirve para *mirar* patrones
  en el panel. Bloquear por IP castiga a oficinas, coworkings y redes móviles,
  donde cientos de clientes legítimos comparten dirección.
- **No deja a nadie sin salida.** Si no hay prueba disponible, la organización
  se crea igual y la persona aterriza en la pantalla de planes. Negar la prueba
  nunca debe impedir *pagar*.
"""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from datetime import date

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import Licencia, PruebaConcedida
from .identidad_registro import es_desechable, normalizar_email

#: Duración de la prueba. Decisión del titular: 7 días, no 14. Configurable por
#: entorno para poder alargarla en una campaña sin tocar código ni desplegar.
DIAS_PRUEBA_POR_DEFECTO = 7

#: Tope defensivo: un error de tecleo en la variable de entorno no debe
#: convertirse en licencias de años.
MAXIMO_DIAS_PRUEBA = 90


@dataclass(frozen=True)
class ResultadoPrueba:
    """Qué pasó al intentar conceder la prueba.

    Nunca es un error: que no haya prueba es un desenlace normal del alta.
    ``motivo`` existe para poder decir la verdad en la interfaz y para
    diagnosticar sin releer los registros.
    """

    concedida: bool
    dias: int = 0
    vence: date | None = None
    motivo: str = ""

    @property
    def mensaje(self) -> str:
        """Texto listo para enseñar a la persona que acaba de registrarse."""
        if self.concedida:
            return (
                f"Tienes {self.dias} días de prueba gratuita, "
                f"con acceso completo hasta el {self.vence:%d/%m/%Y}."
            )
        if self.motivo == "ya_usada":
            return (
                "Ya disfrutaste tu prueba gratuita con este correo. "
                "Elige un plan para seguir usando CotizaT."
            )
        return "Elige un plan para empezar a usar CotizaT."


def dias_de_prueba() -> int:
    """Duración configurada, saneada contra valores absurdos."""
    crudo = (os.getenv("COTIZAT_DIAS_PRUEBA") or "").strip()
    if not crudo:
        return DIAS_PRUEBA_POR_DEFECTO
    try:
        dias = int(crudo)
    except ValueError:
        return DIAS_PRUEBA_POR_DEFECTO
    if dias < 1:
        return 0  # 0 = prueba desactivada a propósito.
    return min(dias, MAXIMO_DIAS_PRUEBA)


def prueba_activada() -> bool:
    """La prueba se puede apagar sin desplegar, poniendo la duración a 0."""
    return dias_de_prueba() > 0


def hash_ip(ip: str) -> str:
    """SHA-256 de la IP con sal del despliegue.

    Se guarda el hash y nunca la IP: para el único uso previsto —ver si varias
    altas salen del mismo sitio— comparar hashes vale igual que comparar
    direcciones, y un volcado de la tabla no expone la ubicación de nadie.

    Sin sal configurada el hash de una IPv4 sería trivial de revertir por
    fuerza bruta (hay solo 4.300 millones), así que se usa la clave del
    proyecto como sal.
    """
    limpia = (ip or "").strip()
    if not limpia:
        return ""
    sal = (
        os.getenv("COTIZAT_HASH_SALT")
        or os.getenv("SUPABASE_SECRET_KEY")
        or "cotizat-sal-local"
    )
    return hashlib.sha256(f"{sal}|{limpia}".encode("utf-8")).hexdigest()


def prueba_ya_usada(db: Session, email: str) -> bool:
    """¿Esta identidad de correo ya gastó su prueba?

    Informativo: la garantía real es la restricción única de la tabla.
    """
    normalizado = normalizar_email(email)
    if not normalizado:
        return False
    return (
        db.query(PruebaConcedida.id)
        .filter(PruebaConcedida.email_normalizado == normalizado)
        .first()
        is not None
    )


def _conceder_en_postgres(
    db: Session,
    *,
    organizacion_id: int,
    email_normalizado: str,
    email_original: str,
    ip_hash: str,
    dias: int,
) -> bool:
    """Delega en la función ``SECURITY DEFINER`` de la base.

    Hace falta porque la RLS de ``licencias`` solo admite escrituras de una
    sesión marcada como operador, y quien se está registrando es un cliente.
    La función inserta la licencia y la marca de prueba **en la misma
    transacción**, de modo que no puede existir una licencia de prueba sin su
    marca (prueba infinita) ni una marca sin licencia (cliente sin sus días).
    """
    fila = db.execute(
        text(
            "SELECT cotizat_security.grant_trial_license("
            " :org, :email_norm, :email_orig, :ip_hash, :dias)"
        ),
        {
            "org": organizacion_id,
            "email_norm": email_normalizado,
            "email_orig": email_original,
            "ip_hash": ip_hash,
            "dias": dias,
        },
    ).scalar()
    return bool(fila)


def _conceder_en_sqlite(
    db: Session,
    *,
    organizacion_id: int,
    email_normalizado: str,
    email_original: str,
    ip_hash: str,
    dias: int,
    hoy: date,
) -> bool:
    """Camino de escritorio y de pruebas: sin RLS, escritura directa.

    Se apoya igualmente en la restricción única, así que la carrera se
    resuelve de la misma forma en ambos motores.
    """
    from .licencias import crear_licencia

    licencia = crear_licencia(
        db,
        organizacion_id=organizacion_id,
        origen="prueba",
        dias=dias,
        operador_email="sistema@cotizat",
        notas="Prueba gratuita automática al crear la organización.",
        hoy=hoy,
    )
    db.add(
        PruebaConcedida(
            email_normalizado=email_normalizado,
            email_original=email_original,
            organizacion_id=organizacion_id,
            licencia_id=licencia.id,
            ip_hash=ip_hash,
            dias=dias,
        )
    )
    db.flush()
    return True


def conceder_prueba(
    db: Session,
    *,
    organizacion_id: int,
    email: str,
    ip: str = "",
    hoy: date | None = None,
    es_sqlite: bool | None = None,
) -> ResultadoPrueba:
    """Concede la prueba si esta identidad no la ha usado nunca.

    Devuelve siempre un ``ResultadoPrueba``: **no lanza excepciones**. Un fallo
    aquí no puede tumbar el alta de la organización, que ya está creada y es lo
    que la persona pidió. Como mucho se queda sin prueba y ve la pantalla de
    planes, que es un desenlace recuperable; perder la organización no lo es.
    """
    hoy = hoy or date.today()
    dias = dias_de_prueba()
    if dias <= 0:
        return ResultadoPrueba(False, motivo="desactivada")

    normalizado = normalizar_email(email)
    if not normalizado:
        return ResultadoPrueba(False, motivo="email_invalido")
    if es_desechable(email):
        # Cinturón y tirantes: el registro ya los bloquea antes de llegar aquí.
        return ResultadoPrueba(False, motivo="desechable")

    if prueba_ya_usada(db, email):
        return ResultadoPrueba(False, motivo="ya_usada")

    if es_sqlite is None:
        es_sqlite = db.bind is not None and db.bind.dialect.name == "sqlite"

    datos = {
        "organizacion_id": organizacion_id,
        "email_normalizado": normalizado,
        "email_original": (email or "").strip()[:254],
        "ip_hash": hash_ip(ip),
        "dias": dias,
    }

    punto = db.begin_nested()
    try:
        if es_sqlite:
            ok = _conceder_en_sqlite(db, hoy=hoy, **datos)
        else:
            ok = _conceder_en_postgres(db, **datos)
    except IntegrityError:
        # Otra alta ganó la carrera por la misma identidad. Es el caso que la
        # comprobación previa no puede cubrir, y aquí se cierra de verdad.
        punto.rollback()
        return ResultadoPrueba(False, motivo="ya_usada")
    except Exception:
        punto.rollback()
        return ResultadoPrueba(False, motivo="error")
    punto.commit()

    if not ok:
        # La función de Postgres devuelve FALSE si la identidad ya constaba.
        return ResultadoPrueba(False, motivo="ya_usada")

    from datetime import timedelta

    return ResultadoPrueba(
        True, dias=dias, vence=hoy + timedelta(days=dias - 1), motivo="concedida"
    )
