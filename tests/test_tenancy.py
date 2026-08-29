"""Propiedad empresarial y aislamiento automático de la base web."""
import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import (
    ApiKeyOperador,
    AvisoWeb,
    Capitulo,
    Cliente,
    Configuracion,
    Consentimiento,
    ContenidoWeb,
    ContextoOrganizacionError,
    CrmCliente,
    EventoAdmin,
    EventoAuditoria,
    EventoProducto,
    FeatureFlag,
    HistorialPrecioRecurso,
    NotaOperador,
    OperadorProducto,
    ReleaseWeb,
    Licencia,
    VistaGuardada,
    Membresia,
    Organizacion,
    PrecioRecursoMercado,
    PruebaConcedida,
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
    """Todo dato de negocio pertenece a una organización.

    Las excepciones son deliberadas y están enumeradas aquí, para que añadir un
    modelo sin `organizacion_id` obligue a justificarlo en esta lista:

    - `Organizacion`, `Usuario` y `Membresia` son la identidad global.
    - `Licencia` es un dato del **titular del producto** sobre una organización
      (cuánto paga y hasta cuándo), no un dato *de* esa organización. Si
      heredara de `TenantMixin`, el filtro automático se la mostraría al propio
      cliente. Su aislamiento lo aportan `get_operator_db` y las políticas RLS
      `cotizat_licencia_*` (revisión `f4c1d8e37a95`).
    - `PruebaConcedida` registra qué identidad de correo ya gastó su prueba
      gratuita. Atarla a una organización la haría inútil: la defensa consiste
      precisamente en recordar la prueba **después** de que su organización
      desaparezca, y en reconocer a la misma persona cuando crea otra distinta.
      Se aísla con las políticas `cotizat_prueba_*` (revisión `a3d9c1e75b28`).
    - `Consentimiento` registra la aceptación de términos y privacidad de una
      persona (E4-038). Es un dato del **titular sobre sus clientes** —como
      `Licencia` o `PruebaConcedida`—, no un dato *de* la organización: la
      aceptación se produce en el registro, antes de existir organización, y
      debe sobrevivir a su borrado. Se aísla con las políticas
      `cotizat_consentimiento_*` (revisión `b6d9e4c2a8f1`).
    - `EventoAuditoria` (E4-026/027) tiene `organizacion_id` **nullable a
      propósito**: los eventos de sesión (login/logout/cambio de clave) y la
      constancia de una baja ocurren sin organización, así que no puede
      heredar de `TenantMixin` (que lo exige NOT NULL). Toda consulta filtra
      la organización explícitamente y en PostgreSQL lo aíslan las políticas
      `cotizat_evento_*` (revisión `d2a7c9e4f1b3`); las filas sin organización
      solo las ve el operador.
    - `PrecioRecursoMercado` e `HistorialPrecioRecurso` (precios por mercado
      nacional) tienen `organizacion_id` **nullable a propósito**: NULL es la
      referencia nacional que comparten todas las empresas del país y solo
      escribe el operador; con valor es el precio negociado por una empresa.
      `TenantMixin` lo exige NOT NULL, así que las consultas filtran la
      organización explícitamente (`resolver_precio`, panel `/recursos/mercado`)
      y en PostgreSQL lo aíslan las políticas `cotizat_precio_mercado_*` y
      `cotizat_historial_precio_*` (revisión `e7b3c1d5a204`).
    """
    identidades_globales = {Organizacion, Usuario, Membresia}
    no_tenant_justificados = {
        Licencia,
        PruebaConcedida,
        Consentimiento,
        EventoAuditoria,
        EventoProducto,
        OperadorProducto,
        EventoAdmin,
        NotaOperador,
        PrecioRecursoMercado,
        HistorialPrecioRecurso,
        ContenidoWeb,
        AvisoWeb,
        ReleaseWeb,
        VistaGuardada,
        FeatureFlag,
        CrmCliente,
        ApiKeyOperador,
    }
    sin_propietario = []
    for mapper in Base.registry.mappers:
        modelo = mapper.class_
        if (
            modelo not in identidades_globales
            and modelo not in no_tenant_justificados
            and not issubclass(modelo, TenantMixin)
        ):
            sin_propietario.append(modelo.__name__)
    assert not sin_propietario, f"Modelos comerciales sin organización: {sin_propietario}"


def test_la_licencia_no_es_una_tabla_de_tenant():
    """Regresión explícita: convertirla en tenant la filtraría al cliente."""
    assert not issubclass(Licencia, TenantMixin), (
        "Licencia no puede heredar de TenantMixin: el filtro por organización "
        "la haría visible al cliente sobre el que informa."
    )


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
