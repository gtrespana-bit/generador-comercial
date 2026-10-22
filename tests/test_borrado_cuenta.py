"""Reglas del borrado de cuenta: alcance y defensas previas a la supresión."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import CompraPlan, Membresia, Organizacion, Usuario
from app.services.baja import BajaError
from app.services.borrado_cuenta import (
    BorradoCuentaError,
    ejecutar_borrado_local,
    resumen_borrado_cuenta,
)

AUTH_ID = "0691d7f2-ae24-4b7f-9e45-87ad16fdc94c"


@pytest.fixture
def cuenta_db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def test_resumen_distingue_empresas_propias_y_membresias_ajenas(cuenta_db):
    usuario = Usuario(auth_user_id=AUTH_ID, email="persona@example.com", nombre="Persona")
    propia = Organizacion(nombre="Empresa propia", slug="empresa-propia")
    ajena = Organizacion(nombre="Empresa ajena", slug="empresa-ajena")
    cuenta_db.add_all([usuario, propia, ajena])
    cuenta_db.flush()
    equipo = Usuario(
        auth_user_id="31af6ed4-6959-4bfa-80f2-810d08d1b68c",
        email="equipo@example.com",
        nombre="Equipo",
    )
    cuenta_db.add(equipo)
    cuenta_db.flush()
    cuenta_db.add_all([
        Membresia(usuario_id=usuario.id, organizacion_id=propia.id, rol="propietario", activa=True),
        Membresia(usuario_id=equipo.id, organizacion_id=propia.id, rol="miembro", activa=True),
        Membresia(usuario_id=usuario.id, organizacion_id=ajena.id, rol="miembro", activa=True),
    ])
    cuenta_db.commit()

    alcance = resumen_borrado_cuenta(cuenta_db, usuario.id)

    assert [(fila["nombre"], fila["se_borrara"], fila["miembros"]) for fila in alcance] == [
        ("Empresa propia", True, 2),
        ("Empresa ajena", False, None),
    ]


def test_borrado_local_rechaza_identidad_que_no_coincide(cuenta_db):
    usuario = Usuario(auth_user_id=AUTH_ID, email="persona@example.com", nombre="Persona")
    cuenta_db.add(usuario)
    cuenta_db.commit()

    with pytest.raises(BorradoCuentaError, match="no coincide"):
        ejecutar_borrado_local(
            cuenta_db,
            usuario_id=usuario.id,
            auth_user_id="31af6ed4-6959-4bfa-80f2-810d08d1b68c",
            email="persona@example.com",
        )


def test_borrado_local_no_repite_un_tombstone(cuenta_db):
    usuario = Usuario(
        auth_user_id=AUTH_ID,
        email="borrado+0691d7f2ae244b7f9e4587ad16fdc94c@invalid.cotizat",
        nombre="",
        activo=False,
        borrado_pendiente=True,
    )
    cuenta_db.add(usuario)
    cuenta_db.commit()

    with pytest.raises(BorradoCuentaError, match="en proceso"):
        ejecutar_borrado_local(
            cuenta_db,
            usuario_id=usuario.id,
            auth_user_id=AUTH_ID,
            email=usuario.email,
        )


def test_borrado_cuenta_conserva_su_cancelacion_programada_sin_duplicarla(
    cuenta_db, monkeypatch
):
    """La baja reutilizada no debe volver a cancelar inmediatamente."""
    usuario = Usuario(auth_user_id=AUTH_ID, email="persona@example.com", nombre="Persona")
    propia = Organizacion(nombre="Empresa propia", slug="empresa-propia")
    cuenta_db.add_all([usuario, propia])
    cuenta_db.flush()
    cuenta_db.add_all([
        Membresia(
            usuario_id=usuario.id,
            organizacion_id=propia.id,
            rol="propietario",
            activa=True,
        ),
        CompraPlan(
            organizacion_id=propia.id,
            plan="mensual",
            metodo_pago="stripe",
            estado="activa",
            stripe_subscription_id="sub_cuenta_123",
        ),
    ])
    cuenta_db.commit()

    programadas = []
    monkeypatch.setattr(
        "app.services.stripe.fijar_cancelacion_al_vencer",
        lambda subscription_id, cancelar: programadas.append(
            (subscription_id, cancelar)
        ) or {"status": "active", "cancel_at_period_end": True},
    )
    parametros_baja = {}

    def _detener_antes_de_borrar(db, **kwargs):
        parametros_baja.update(kwargs)
        raise BajaError("Detención deliberada antes de borrar")

    monkeypatch.setattr("app.services.baja.ejecutar_baja", _detener_antes_de_borrar)

    with pytest.raises(BorradoCuentaError):
        ejecutar_borrado_local(
            cuenta_db,
            usuario_id=usuario.id,
            auth_user_id=AUTH_ID,
            email=usuario.email,
        )

    assert programadas == [("sub_cuenta_123", True)]
    assert parametros_baja["cancelar_suscripciones"] is False
