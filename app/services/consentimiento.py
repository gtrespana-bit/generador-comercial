"""Registro de la aceptación de términos y privacidad (E4-038).

El flujo de alta tiene una particularidad: la persona acepta los términos en
el **formulario de registro**, cuando todavía no hay sesión (el correo debe
confirmarse después). Por eso el registro no puede depender de las políticas
de una sesión autenticada:

- **PostgreSQL (producción):** ``consentimientos`` tiene RLS de operador
  (FORCE), así que una sesión anónima o de cliente no puede escribir ni leer
  la tabla directamente. Las escrituras entran por
  ``cotizat_security.record_consent`` y las lecturas por
  ``cotizat_security.obtener_consentimiento``, ambas SECURITY DEFINER
  definidas en la migración ``b6d9e4c2a8f1``.
- **SQLite (escritorio y pruebas):** sin RLS, se inserta y consulta directo,
  con la misma unicidad (``email``, ``version``) como cierre de la carrera.
"""

from datetime import datetime

from sqlalchemy import text

from ..models import Consentimiento, Usuario


def registrar_consentimiento(
    db,
    *,
    email: str,
    nombre: str = "",
    version: str,
    ip_hash: str = "",
) -> bool:
    """Registra una aceptación de forma idempotente y devuelve si se insertó.

    Segunda llamada con el mismo ``email`` y ``version`` devuelve ``False``
    sin error: la persona ya consta como aceptante de esa versión. La versión
    vacía se rechaza igual que en la función PostgreSQL: un consentimiento sin
    versión no significa nada.

    Nunca lanza por problemas de base: el consentimiento no puede impedir el
    alta. Los errores de motor se reportan con ``False`` (y el registro se
    considera pendiente hasta que la cuenta entre por /cuenta).
    """
    email = str(email or "").strip().lower()
    version = str(version or "").strip()[:20]
    if not email or not version:
        return False
    if db.bind is not None and db.bind.dialect.name == "postgresql":
        fila = db.execute(
            text(
                "SELECT cotizat_security.record_consent("
                " :email, :nombre, :version, :ip_hash)"
            ),
            {
                "email": email,
                "nombre": (nombre or "")[:200],
                "version": version,
                "ip_hash": (ip_hash or "")[:64],
            },
        ).scalar()
        return bool(fila)
    try:
        db.add(
            Consentimiento(
                email=email,
                nombre=(nombre or "")[:200],
                version=version,
                ip_hash=(ip_hash or "")[:64],
                aceptado_en=datetime.utcnow(),
            )
        )
        db.commit()
        return True
    except Exception:  # IntegrityError y cualquier otro fallo del motor
        db.rollback()
        return False


def aplicar_consentimiento_a_usuario(db, usuario: Usuario) -> bool:
    """Rellena la marca del perfil desde el último consentimiento registrado.

    Se usa al aceptar desde /cuenta: registra la fila y actualiza el resumen
    del perfil en el mismo paso. Devuelve si el perfil quedó marcado.
    """
    if not usuario.acepto_terminos_version:
        from ..models import _consentimiento_mas_reciente

        consentimiento = _consentimiento_mas_reciente(db, usuario.email)
        if consentimiento is not None:
            usuario.acepto_terminos_version = consentimiento.version
            usuario.acepto_terminos_at = consentimiento.aceptado_en
            return True
    return bool(usuario.acepto_terminos_version)
