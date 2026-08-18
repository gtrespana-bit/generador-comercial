"""E4-016 — auditoría de acceso directo por identificadores (inventario completo).

La prueba inicial de tenencia solo cubría ``Cliente`` y ``Capitulo``. Este
módulo convierte la auditoría en un inventario exhaustivo: construye una
instancia de **cada** modelo ``TenantMixin`` en la organización A y comprueba,
desde la organización B, que ``db.get(Modelo, id)`` devuelve ``None``.

El inventario es auto-mantenido: ``_modelos_tenant()`` se deriva de los
mappers de SQLAlchemy, de modo que añadir un modelo nuevo sin añadirlo al grafo
de ``_construir_grafo`` hace fallar ``test_el_inventario_cubre_todos_los_modelos``
con el nombre del modelo que quedó sin cobertura.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import (
    AnexoPresupuesto,
    ArchivoAlmacenado,
    BorradorPresupuesto,
    CambioAlcance,
    CambioAlcanceItem,
    Capitulo,
    CategoriaPartida,
    Cliente,
    CompraPlan,
    Configuracion,
    DescomposicionFila,
    DescomposicionPartida,
    EnlacePropuesta,
    Factura,
    FacturaCapitulo,
    FacturaItem,
    InvitacionOrganizacion,
    Licencia,
    Medicion,
    Membresia,
    NotaSeguimiento,
    Organizacion,
    Pago,
    Partida,
    Plantilla,
    Presupuesto,
    PresupuestoItem,
    PresupuestoItemProducto,
    PresupuestoVersion,
    Producto,
    Proyecto,
    RecetaEstancia,
    Recurso,
    TenantMixin,
    Usuario,
    usar_organizacion,
)


def _modelos_tenant() -> list:
    """Todos los modelos de negocio con propietario obligatorio de organización.

    Se excluyen las identidades globales (``Organizacion``, ``Usuario``,
    ``Membresia``) y ``Licencia``, que es un dato del titular sobre una
    organización y se protege con RLS propia, no con el filtro de tenant.
    """
    globales = {Organizacion, Usuario, Membresia}
    no_tenant = {Licencia}
    return sorted(
        (
            mapper.class_
            for mapper in Base.registry.mappers
            if mapper.class_ not in globales
            and mapper.class_ not in no_tenant
            and issubclass(mapper.class_, TenantMixin)
        ),
        key=lambda modelo: modelo.__name__,
    )


def _construir_grafo(db, organizacion_id: int) -> dict:
    """Crea una instancia de cada modelo tenant en la organización dada.

    Devuelve ``{Modelo: [ids]}`` con los identificadores primarios de cada
    fila creada. Usa las relaciones con cascade para que el ``before_flush``
    propague ``organizacion_id`` y las claves foráneas se asignen solas.
    """
    usar_organizacion(db, organizacion_id)

    # --- Identidad periférica de la organización -------------------------
    db.add(Configuracion(empresa_nombre="Empresa A"))
    db.add(InvitacionOrganizacion(
        email="invitado@example.com",
        rol="miembro",
        token_hash="a" * 64,
        expires_at=datetime.utcnow() + timedelta(days=1),
    ))
    db.add(ArchivoAlmacenado(
        object_key=f"organizaciones/{organizacion_id}/anexos/doc.pdf",
        categoria="anexos",
        content_type="application/pdf",
        tamano_bytes=123,
        sha256="b" * 64,
        nombre_original="doc.pdf",
    ))

    # --- Catálogos independientes ----------------------------------------
    db.add(CategoriaPartida(categoria="Pintura"))
    db.add(Partida(nombre="Partida inventario", categoria="Pintura"))
    db.add(Producto(nombre="Producto inventario"))
    db.add(Recurso(descripcion="Recurso inventario"))
    db.add(Plantilla(nombre="Plantilla inventario", datos="[]"))
    db.add(RecetaEstancia(nombre="Receta inventario"))

    # --- Cliente y presupuesto (agregado completo) -----------------------
    cliente = Cliente(nombre="Cliente inventario")
    db.add(cliente)
    db.flush()

    presupuesto = Presupuesto(numero="P-INV-001", year=2026, client_id=cliente.id)
    capitulo = Capitulo(nombre="CAPÍTULO")
    presupuesto.capitulos.append(capitulo)
    item = PresupuestoItem(nombre="Partida de presupuesto", cantidad=1, precio_unitario=10)
    capitulo.partidas.append(item)
    item.mediciones.append(Medicion(concepto="Zona", cantidad=1))
    item.productos_opciones.append(PresupuestoItemProducto(nombre="Opción", precio=10))
    descomp = DescomposicionPartida(codigo="DPT020")
    descomp.filas.append(DescomposicionFila(tipo="recurso", descripcion="fila"))
    item.descomposicion_cype = descomp
    presupuesto.anexos.append(AnexoPresupuesto(nombre="anexo", archivo="storage://x"))
    presupuesto.notas_seguimiento.append(NotaSeguimiento(texto="nota de seguimiento"))
    db.add(presupuesto)
    db.flush()

    version = PresupuestoVersion(
        presupuesto_id=presupuesto.id, numero_version=1, estado="aprobado", total=0.0
    )
    db.add(version)
    db.flush()

    db.add(EnlacePropuesta(
        presupuesto_id=presupuesto.id,
        presupuesto_version_id=version.id,
        presupuesto_version_numero=1,
        token_hash="c" * 64,
        pdf_snapshot="storage://x",
        fecha_presupuesto=date.today(),
        valido_hasta=date.today() + timedelta(days=7),
        expires_at=datetime.utcnow() + timedelta(days=7),
    ))
    db.add(BorradorPresupuesto(presupuesto_id=presupuesto.id, datos="{}"))

    # --- Documento de cobro ----------------------------------------------
    factura = Factura(numero="DC-001", year=2026, client_id=cliente.id)
    factura_capitulo = FacturaCapitulo(nombre="CAP")
    factura.capitulos.append(factura_capitulo)
    factura_capitulo.partidas.append(
        FacturaItem(nombre="item", cantidad=1, precio_unitario=10)
    )
    db.add(factura)
    db.flush()

    # --- Proyecto, cambios de alcance y pagos ----------------------------
    proyecto = Proyecto(presupuesto_id=presupuesto.id, nombre="Proyecto")
    cambio = CambioAlcance(numero=1)
    cambio.items.append(CambioAlcanceItem(nombre="cambio item"))
    proyecto.cambios.append(cambio)
    proyecto.pagos.append(Pago(importe=100))
    db.add(proyecto)

    # --- Compra de plan (pago manual) -------------------------------------
    db.add(CompraPlan(
        plan="mensual",
        metodo_pago="usdt",
        importe=9.99,
        estado="pendiente",
        comprobante_reference="storage://x/comprobante.png",
        comprobante_nombre="comprobante.png",
        comprobante_mime="image/png",
    ))

    db.commit()

    return {
        modelo: [fila.id for fila in db.query(modelo).all()]
        for modelo in _modelos_tenant()
    }


def _sesion_inventario():
    engine = create_engine("sqlite://")

    @event.listens_for(engine, "connect")
    def _foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine)


def _alta_organizacion(db, nombre: str, slug: str, usuario: Usuario, rol: str) -> int:
    """Crea una organización con una membresía del usuario y devuelve su id."""
    organizacion = Organizacion(nombre=nombre, slug=slug)
    db.add(organizacion)
    db.flush()
    db.add(Membresia(
        usuario_id=usuario.id, organizacion_id=organizacion.id, rol=rol
    ))
    db.flush()
    return organizacion.id


def test_el_inventario_cubre_todos_los_modelos_tenant():
    """Cada modelo ``TenantMixin`` tiene al menos una fila en el grafo.

    Si se añade un modelo nuevo sin incluirlo en ``_construir_grafo``, esta
    prueba falla nombrando el modelo sin cobertura: el inventario no puede
    quedarse desactualizado en silencio.
    """
    engine, Session = _sesion_inventario()
    try:
        with Session() as db:
            usuario = Usuario(email="propietario@example.com", nombre="Propietario")
            db.add(usuario)
            db.flush()
            org_id = _alta_organizacion(db, "Org Inventario", "org-inventario", usuario, "propietario")
            ids = _construir_grafo(db, org_id)
        for modelo in _modelos_tenant():
            assert ids.get(modelo), (
                f"{modelo.__name__} no está cubierto por el inventario de "
                "aislamiento; añádelo a `_construir_grafo`."
            )
    finally:
        engine.dispose()


def test_acceso_directo_por_id_queda_bloqueado_para_cada_modelo():
    """Desde la organización B, ningún id de A es legible por su clave primaria.

    El filtro ``with_loader_criteria`` se aplica también a ``Session.get``, de
    modo que la lectura directa por identificador devuelve ``None`` aunque el
    id exista en la base. Se comprueba para todos los modelos tenant.
    """
    engine, Session = _sesion_inventario()
    try:
        with Session() as db:
            usuario = Usuario(email="propietario@example.com", nombre="Propietario")
            db.add(usuario)
            db.flush()
            org_a = _alta_organizacion(db, "Org A", "org-a", usuario, "propietario")
            org_b = _alta_organizacion(db, "Org B", "org-b", usuario, "administrador")
            db.commit()

        # El grafo se construye en A.
        with Session() as db_a:
            ids = _construir_grafo(db_a, org_a)

        # Desde B, ninguna fila de A es alcanzable por su id.
        with Session() as db_b:
            usar_organizacion(db_b, org_b)
            for modelo, filas_ids in ids.items():
                assert filas_ids, f"{modelo.__name__} sin filas que auditar"
                for fila_id in filas_ids:
                    assert db_b.get(modelo, fila_id) is None, (
                        f"Fuga de aislamiento: {modelo.__name__} id={fila_id} "
                        "es legible desde otra organización por su id."
                    )

        # Y dentro de A el id sí resuelve (sanity: no estamos filtrando de más).
        with Session() as db_a:
            usar_organizacion(db_a, org_a)
            for modelo, filas_ids in ids.items():
                for fila_id in filas_ids:
                    assert db_a.get(modelo, fila_id) is not None
    finally:
        engine.dispose()
