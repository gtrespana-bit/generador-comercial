"""Invitaciones de un solo uso y permisos de administración de equipo."""
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.testclient import TestClient

from app.database import Base
from app.models import InvitacionOrganizacion, Membresia, Organizacion, Usuario
from app.services.invitations import (
    GestionEquipoError,
    aceptar_invitacion,
    actualizar_membresia,
    crear_invitacion,
    revocar_invitacion,
)


def _db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine)()


def _equipo(db):
    organizacion = Organizacion(nombre="Constructora", slug="constructora-invitaciones")
    propietario = Usuario(email="duena@example.com", nombre="Dueña")
    invitado = Usuario(
        email="persona@example.com",
        nombre="Persona",
        email_verificado_at=datetime(2026, 8, 13),
    )
    db.add_all([organizacion, propietario, invitado])
    db.flush()
    membresia = Membresia(
        organizacion_id=organizacion.id,
        usuario_id=propietario.id,
        rol="propietario",
    )
    db.add(membresia)
    db.commit()
    return organizacion, propietario, invitado, membresia


def test_vista_publica_no_confirma_si_el_token_existe_y_no_se_cachea():
    from app.main import app

    with TestClient(app) as client:
        valida = client.get("/invitaciones/" + "a" * 43)
        invalida = client.get("/invitaciones/corta")
    assert valida.status_code == invalida.status_code == 200
    assert valida.headers["cache-control"] == "no-store"
    assert valida.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert "Te invitaron" in valida.text
    assert "Te invitaron" in invalida.text


def test_aceptar_invitacion_responde_por_get_para_redireccion_tras_login():
    """El `?next=` posterior al login llega por GET; la ruta debe existir.

    Regresión: antes la ruta /aceptar solo estaba registrada como POST, así
    que el navegador recibía 405 Method Not Allowed después de iniciar sesión.
    Sin sesión, la página ofrece iniciar sesión (no el formulario).
    """
    from app.main import app

    with TestClient(app) as client:
        respuesta = client.get("/invitaciones/" + "a" * 43 + "/aceptar")
    assert respuesta.status_code == 200
    assert "Te invitaron" in respuesta.text
    assert "/acceso?next=" in respuesta.text
    # El enlace conserva la ruta de aceptación para volver tras el login.
    assert "/invitaciones/" in respuesta.text and "/aceptar" in respuesta.text
    # Sin cookie de sesión no se muestra el formulario de autoenvío.
    assert 'id="aceptar-invitacion"' not in respuesta.text


def test_aceptar_invitacion_con_sesion_muestra_formulario_post_y_autoenvio():
    """Con sesión activa, la página GET muestra el formulario POST protegido
    por CSRF y un script que lo autoenvía (un clic menos tras el login)."""
    from app.auth import ACCESS_COOKIE
    from app.main import app

    with TestClient(app) as client:
        client.cookies.set(ACCESS_COOKIE, "sesion-ficticia")
        respuesta = client.get("/invitaciones/" + "a" * 43 + "/aceptar")
    assert respuesta.status_code == 200
    assert 'id="aceptar-invitacion"' in respuesta.text
    assert 'method="post"' in respuesta.text
    assert 'action="/invitaciones/' in respuesta.text and respuesta.text.count("/aceptar") >= 1
    # El autoenvío usa un script nonce (CSP) y no un handler inline.
    assert "form.submit()" in respuesta.text
    assert 'nonce="' in respuesta.text
    assert " onsubmit=" not in respuesta.text


def test_aceptar_invitacion_sin_sesion_no_autoenvia():
    """Sin cookie de sesión no debe haber script de autoenvío: el usuario
    todavía tiene que autenticarse."""
    from app.main import app

    with TestClient(app) as client:
        respuesta = client.get("/invitaciones/" + "a" * 43 + "/aceptar")
    assert "form.submit()" not in respuesta.text


def test_invitacion_guarda_hash_revoca_anterior_y_no_el_secreto():
    engine, db = _db()
    try:
        organizacion, propietario, _invitado, _ = _equipo(db)
        ahora = datetime(2026, 8, 13, 12)
        primera, primer_token = crear_invitacion(
            db,
            organizacion_id=organizacion.id,
            actor_usuario_id=propietario.id,
            email=" Persona@Example.com ",
            rol="miembro",
            ahora=ahora,
        )
        segunda, segundo_token = crear_invitacion(
            db,
            organizacion_id=organizacion.id,
            actor_usuario_id=propietario.id,
            email="persona@example.com",
            rol="lectura",
            ahora=ahora + timedelta(minutes=1),
        )

        assert primera.revoked_at == ahora + timedelta(minutes=1)
        assert segunda.email == "persona@example.com"
        assert segunda.expires_at == ahora + timedelta(days=7, minutes=1)
        assert len(segunda.token_hash) == 64
        assert segundo_token != segunda.token_hash
        assert primer_token != segundo_token
        assert not hasattr(segunda, "token")
    finally:
        db.close()
        engine.dispose()


def test_solo_propietario_puede_invitar_administradores():
    engine, db = _db()
    try:
        organizacion, propietario, _invitado, _ = _equipo(db)
        administrador = Usuario(email="admin@example.com")
        miembro = Usuario(email="miembro@example.com")
        db.add_all([administrador, miembro])
        db.flush()
        db.add_all([
            Membresia(
                organizacion_id=organizacion.id,
                usuario_id=administrador.id,
                rol="administrador",
            ),
            Membresia(
                organizacion_id=organizacion.id,
                usuario_id=miembro.id,
                rol="miembro",
            ),
        ])
        db.flush()

        with pytest.raises(GestionEquipoError, match="Solo la persona propietaria"):
            crear_invitacion(
                db,
                organizacion_id=organizacion.id,
                actor_usuario_id=administrador.id,
                email="otra@example.com",
                rol="administrador",
            )
        with pytest.raises(GestionEquipoError, match="rol no permite"):
            crear_invitacion(
                db,
                organizacion_id=organizacion.id,
                actor_usuario_id=miembro.id,
                email="otra@example.com",
                rol="lectura",
            )
        invitacion, _ = crear_invitacion(
            db,
            organizacion_id=organizacion.id,
            actor_usuario_id=propietario.id,
            email="admin-nueva@example.com",
            rol="administrador",
        )
        assert invitacion.rol == "administrador"
    finally:
        db.close()
        engine.dispose()


def test_aceptacion_exige_email_verificado_coincidente_y_consume_token():
    engine, db = _db()
    try:
        organizacion, propietario, invitado, _ = _equipo(db)
        invitacion, token = crear_invitacion(
            db,
            organizacion_id=organizacion.id,
            actor_usuario_id=propietario.id,
            email=invitado.email,
            rol="miembro",
            ahora=datetime(2026, 8, 13, 12),
        )
        intruso = Usuario(
            email="intruso@example.com",
            email_verificado_at=datetime(2026, 8, 13),
        )
        db.add(intruso)
        db.flush()

        with pytest.raises(GestionEquipoError, match="mismo email"):
            aceptar_invitacion(
                db,
                token=token,
                usuario=intruso,
                email_verificado=True,
                ahora=datetime(2026, 8, 13, 13),
            )
        with pytest.raises(GestionEquipoError, match="Confirma tu email"):
            aceptar_invitacion(
                db,
                token=token,
                usuario=invitado,
                email_verificado=False,
                ahora=datetime(2026, 8, 13, 13),
            )

        membresia = aceptar_invitacion(
            db,
            token=token,
            usuario=invitado,
            email_verificado=True,
            ahora=datetime(2026, 8, 13, 13),
        )
        db.commit()

        assert membresia.organizacion_id == organizacion.id
        assert membresia.usuario_id == invitado.id
        assert membresia.rol == "miembro"
        assert invitacion.aceptada_por_usuario_id == invitado.id
        with pytest.raises(GestionEquipoError, match="no es válida"):
            aceptar_invitacion(
                db,
                token=token,
                usuario=invitado,
                email_verificado=True,
                ahora=datetime(2026, 8, 13, 14),
            )
    finally:
        db.close()
        engine.dispose()


def test_aceptacion_no_usa_select_for_update_y_falla_si_ya_se_consumio():
    """La reclamación del token es un UPDATE condicional; si otra petición ya
    lo consumió, ``rowcount`` es 0 y se rechaza.

    Regresión del error 500 en producción: ``SELECT ... FOR UPDATE`` sobre
    ``invitaciones_organizacion`` exigía el privilegio UPDATE a nivel de
    tabla, pero el rol de aplicación solo lo tiene a nivel de columna.
    """
    engine, db = _db()
    try:
        organizacion, propietario, invitado, _ = _equipo(db)
        invitacion, token = crear_invitacion(
            db,
            organizacion_id=organizacion.id,
            actor_usuario_id=propietario.id,
            email=invitado.email,
            rol="miembro",
            ahora=datetime(2026, 8, 13, 12),
        )
        # Simula que otra transacción ya aceptó la invitación.
        invitacion.accepted_at = datetime(2026, 8, 13, 12, 5)
        invitacion.aceptada_por_usuario_id = propietario.id
        db.commit()

        with pytest.raises(GestionEquipoError, match="no es válida"):
            aceptar_invitacion(
                db,
                token=token,
                usuario=invitado,
                email_verificado=True,
                ahora=datetime(2026, 8, 13, 13),
            )
    finally:
        db.close()
        engine.dispose()


def test_invitacion_caducada_o_revocada_no_se_acepta():
    engine, db = _db()
    try:
        organizacion, propietario, invitado, _ = _equipo(db)
        invitacion, token = crear_invitacion(
            db,
            organizacion_id=organizacion.id,
            actor_usuario_id=propietario.id,
            email=invitado.email,
            rol="lectura",
            ahora=datetime(2026, 8, 1),
        )
        with pytest.raises(GestionEquipoError, match="caducó"):
            aceptar_invitacion(
                db,
                token=token,
                usuario=invitado,
                email_verificado=True,
                ahora=datetime(2026, 8, 9),
            )

        revocar_invitacion(
            db,
            invitacion=invitacion,
            organizacion_id=organizacion.id,
            actor_usuario_id=propietario.id,
        )
        assert invitacion.revoked_at is not None
    finally:
        db.close()
        engine.dispose()


def test_administracion_protege_propietario_y_otros_administradores():
    engine, db = _db()
    try:
        organizacion, propietario, invitado, membresia_propietaria = _equipo(db)
        membresia_invitado = Membresia(
            organizacion_id=organizacion.id,
            usuario_id=invitado.id,
            rol="administrador",
        )
        db.add(membresia_invitado)
        db.flush()

        with pytest.raises(GestionEquipoError, match="propietaria"):
            actualizar_membresia(
                db,
                membresia=membresia_propietaria,
                organizacion_id=organizacion.id,
                actor_usuario_id=propietario.id,
                rol="miembro",
                activa=True,
            )
        with pytest.raises(GestionEquipoError, match="modificar administradores"):
            actualizar_membresia(
                db,
                membresia=membresia_invitado,
                organizacion_id=organizacion.id,
                actor_usuario_id=invitado.id,
                rol="miembro",
                activa=False,
            )

        actualizada = actualizar_membresia(
            db,
            membresia=membresia_invitado,
            organizacion_id=organizacion.id,
            actor_usuario_id=propietario.id,
            rol="lectura",
            activa=False,
        )
        assert actualizada.rol == "lectura"
        assert not actualizada.activa
    finally:
        db.close()
        engine.dispose()
