"""Propiedad empresarial y aislamiento automático de la base web."""
import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import (
    Capitulo,
    Cliente,
    Configuracion,
    ContextoOrganizacionError,
    Membresia,
    Organizacion,
    Presupuesto,
    Usuario,
    TenantMixin,
    asegurar_config,
    proximo_numero,
    usar_organizacion,
)


def _sesiones():
    engine = create_engine("sqlite://")

    @event.listens_for(engine, "connect")
    def _foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as db:
        a = Organizacion(nombre="Empresa A", slug="empresa-a")
        b = Organizacion(nombre="Empresa B", slug="empresa-b")
        usuario = Usuario(email="propietario@example.com", nombre="Propietario")
        db.add_all([a, b, usuario])
        db.flush()
        db.add_all([
            Membresia(usuario_id=usuario.id, organizacion_id=a.id, rol="propietario"),
            Membresia(usuario_id=usuario.id, organizacion_id=b.id, rol="administrador"),
        ])
        db.commit()
        ids = a.id, b.id
    return engine, Session, ids


def test_todo_modelo_comercial_declara_propietario():
    identidades_globales = {Organizacion, Usuario, Membresia}
    sin_propietario = []
    for mapper in Base.registry.mappers:
        modelo = mapper.class_
        if modelo not in identidades_globales and not issubclass(modelo, TenantMixin):
            sin_propietario.append(modelo.__name__)
    assert not sin_propietario, f"Modelos comerciales sin organización: {sin_propietario}"


def test_configuracion_y_numeracion_son_independientes_por_empresa():
    engine, Session, (org_a, org_b) = _sesiones()
    try:
        with Session() as db_a:
            usar_organizacion(db_a, org_a)
            asegurar_config(db_a)
            cfg_a = db_a.query(Configuracion).one()
            cfg_a.empresa_nombre = "Configuración A"
            cliente_a = Cliente(nombre="Cliente compartido")
            db_a.add(cliente_a)
            db_a.flush()
            db_a.add(Presupuesto(
                numero="P-2026-001", year=2026, client_id=cliente_a.id
            ))
            db_a.commit()
            assert proximo_numero(db_a, 2026) == "P-2026-002"

        with Session() as db_b:
            usar_organizacion(db_b, org_b)
            asegurar_config(db_b)
            cfg_b = db_b.query(Configuracion).one()
            cfg_b.empresa_nombre = "Configuración B"
            cliente_b = Cliente(nombre="Cliente compartido")
            db_b.add(cliente_b)
            db_b.flush()
            # El número se puede repetir porque su unicidad pertenece a la empresa.
            db_b.add(Presupuesto(
                numero="P-2026-001", year=2026, client_id=cliente_b.id
            ))
            db_b.commit()
            assert proximo_numero(db_b, 2026) == "P-2026-002"
            assert [c.nombre for c in db_b.query(Cliente).all()] == ["Cliente compartido"]
            assert db_b.query(Configuracion).one().empresa_nombre == "Configuración B"

        with Session() as db_a:
            usar_organizacion(db_a, org_a)
            assert db_a.query(Configuracion).one().empresa_nombre == "Configuración A"
            assert db_a.query(Cliente).count() == 1
    finally:
        engine.dispose()


def test_filtro_cubre_entidades_hijas_y_acceso_directo_por_id():
    engine, Session, (org_a, org_b) = _sesiones()
    try:
        with Session() as db_a:
            usar_organizacion(db_a, org_a)
            cliente = Cliente(nombre="Privado A")
            db_a.add(cliente)
            db_a.flush()
            presupuesto = Presupuesto(
                numero="P-2026-007", year=2026, client_id=cliente.id
            )
            presupuesto.capitulos.append(Capitulo(nombre="CAPÍTULO PRIVADO"))
            db_a.add(presupuesto)
            db_a.commit()
            cliente_id = cliente.id
            capitulo_id = presupuesto.capitulos[0].id
            assert presupuesto.capitulos[0].organizacion_id == org_a

        with Session() as db_b:
            usar_organizacion(db_b, org_b)
            assert db_b.get(Cliente, cliente_id) is None
            assert db_b.get(Capitulo, capitulo_id) is None
            assert db_b.query(Presupuesto).count() == 0
            assert db_b.query(Capitulo).count() == 0
    finally:
        engine.dispose()


def test_escritura_explicita_en_otra_empresa_es_rechazada():
    engine, Session, (org_a, org_b) = _sesiones()
    try:
        with Session() as db_b:
            usar_organizacion(db_b, org_b)
            db_b.add(Cliente(nombre="Intruso", organizacion_id=org_a))
            with pytest.raises(ContextoOrganizacionError, match="otra organización"):
                db_b.commit()
            db_b.rollback()

        with Session() as db_a:
            usar_organizacion(db_a, org_a)
            cliente = Cliente(nombre="Original")
            db_a.add(cliente)
            db_a.commit()

        with Session() as db_b:
            usar_organizacion(db_b, org_b)
            cliente_ajeno = db_b.execute(
                select(Cliente).execution_options(sin_filtro_organizacion=True)
            ).scalar_one()
            cliente_ajeno.nombre = "Modificado por B"
            with pytest.raises(ContextoOrganizacionError, match="otra organización"):
                db_b.commit()
    finally:
        engine.dispose()


def test_actualizaciones_y_borrados_masivos_tambien_quedan_aislados():
    engine, Session, (org_a, org_b) = _sesiones()
    try:
        for org_id, nombre in ((org_a, "Cliente A"), (org_b, "Cliente B")):
            with Session() as db:
                usar_organizacion(db, org_id)
                db.add(Cliente(nombre=nombre))
                db.commit()

        with Session() as db_a:
            usar_organizacion(db_a, org_a)
            actualizados = db_a.query(Cliente).update({Cliente.nombre: "Solo A"})
            assert actualizados == 1
            db_a.commit()

        with Session() as db_b:
            usar_organizacion(db_b, org_b)
            assert db_b.query(Cliente).one().nombre == "Cliente B"

        with Session() as db_a:
            usar_organizacion(db_a, org_a)
            eliminados = db_a.query(Cliente).delete()
            assert eliminados == 1
            db_a.commit()

        with Session() as db_b:
            usar_organizacion(db_b, org_b)
            assert db_b.query(Cliente).count() == 1
    finally:
        engine.dispose()


def test_membresia_impide_duplicar_usuario_en_la_misma_empresa():
    engine, Session, (org_a, _org_b) = _sesiones()
    try:
        with Session() as db:
            usuario_id = db.query(Usuario.id).one()[0]
            db.add(Membresia(
                usuario_id=usuario_id,
                organizacion_id=org_a,
                rol="lectura",
            ))
            with pytest.raises(IntegrityError):
                db.commit()
    finally:
        engine.dispose()
