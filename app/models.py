"""Modelos de datos del generador de presupuestos.

Estructura de un presupuesto (fiel al formato de referencia):

    Presupuesto
    └── Capitulo            p. ej. MUROS Y PARTICIONES (con subtotal propio)
        └── PresupuestoItem (partida: título + descripción técnica larga,
                             unidad, cantidad y precio unitario)
            ├── Medicion    desglose de la cantidad por zonas/conceptos
            └── producto    (opcional) "Producto presupuestado" con imagen
"""
from datetime import date, datetime, timedelta
import json
from types import SimpleNamespace

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Index,
    String,
    Text,
    UniqueConstraint,
    event,
    inspect,
    text,
    Boolean,
)
from sqlalchemy.orm import Session as OrmSession, declared_attr, relationship, with_loader_criteria

from .database import Base

# Estados posibles de un presupuesto
ESTADOS = ["borrador", "en_revision", "enviado", "cambios_solicitados", "reenviado", "aprobado", "aprobado_parcialmente", "en_ejecucion", "finalizado", "rechazado", "vencido", "cancelado", "archivado"]

ESTADOS_ETIQUETA = {
    "borrador": "Borrador", "en_revision": "En revisión", "enviado": "Enviado",
    "cambios_solicitados": "Cambios solicitados", "reenviado": "Reenviado",
    "aprobado": "Aprobado", "aprobado_parcialmente": "Aprobado parcialmente",
    "en_ejecucion": "En ejecución", "finalizado": "Finalizado",
    "rechazado": "Rechazado", "vencido": "Vencido", "cancelado": "Cancelado", "archivado": "Archivado",
}

ROLES_MEMBRESIA = {"propietario", "administrador", "miembro", "lectura"}


class VinculoIdentidadError(RuntimeError):
    """La identidad autenticada entra en conflicto con un perfil existente."""


class LicenciaSuspendidaError(RuntimeError):
    """La organización no tiene una licencia vigente y el despliegue la exige.

    Solo se levanta cuando ``COTIZAT_EXIGIR_LICENCIA`` está activa, es decir,
    cuando el titular decidió que el producto ya no se usa sin licencia. El
    mensaje se muestra al propio miembro de la organización, así que puede
    (y debe) nombrarla.
    """


class OrganizacionNoAutorizadaError(RuntimeError):
    """El usuario intentó seleccionar una organización sin membresía activa."""


class PermisoOrganizacionError(RuntimeError):
    """El rol de membresía no permite la escritura solicitada."""


class Organizacion(Base):
    """Empresa aislada dentro de la futura aplicación web."""

    __tablename__ = "organizaciones"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(200), nullable=False)
    slug = Column(String(120), nullable=False, unique=True)
    activa = Column(Boolean, nullable=False, default=True)
    creada_por_usuario_id = Column(
        Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    membresias = relationship("Membresia", back_populates="organizacion", cascade="all, delete-orphan")


class Usuario(Base):
    """Perfil de aplicación vinculado a una identidad de Supabase Auth."""

    __tablename__ = "usuarios"
    __table_args__ = (
        UniqueConstraint("auth_user_id", name="uq_usuarios_auth_user_id"),
    )

    id = Column(Integer, primary_key=True)
    # UUID de auth.users representado como texto para conservar compatibilidad
    # con SQLite. La contraseña nunca se copia desde Supabase a esta tabla.
    auth_user_id = Column(String(36), nullable=True)
    email = Column(String(254), nullable=False, unique=True)
    nombre = Column(String(200), default="")
    password_hash = Column(String(255), default="")
    activo = Column(Boolean, nullable=False, default=True)
    email_verificado_at = Column(DateTime, nullable=True)
    ultimo_acceso_at = Column(DateTime, nullable=True)
    # Marca visible «en la cuenta» de la aceptación de términos (E4-038). El
    # registro completo (versión, nombre, IP con hash, fecha) vive en
    # `consentimientos`; estas columnas son el resumen de lectura rápida que
    # se muestra en /cuenta y queda rellenado por `sincronizar_usuario_auth`
    # o por la aceptación explícita desde el panel de cuenta.
    acepto_terminos_version = Column(String(20), nullable=False, default="", server_default="")
    acepto_terminos_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    membresias = relationship("Membresia", back_populates="usuario", cascade="all, delete-orphan")


class Consentimiento(Base):
    """Registro de la aceptación de términos y privacidad (E4-038).

    **No es una tabla de tenant**: es información del titular sobre sus
    clientes (como ``licencias`` o ``pruebas_concedidas``), así que lleva RLS
    de operador: FORCE ROW LEVEL SECURITY y políticas que exigen la marca
    ``cotizat.es_operador``. Ninguna sesión de cliente la lee ni la escribe
    directamente; las escrituras del registro entran por la función
    ``cotizat_security.record_consent`` y las lecturas del perfil por
    ``cotizat_security.obtener_consentimiento`` (ambas SECURITY DEFINER).

    La unicidad (``email``, ``version``) hace idempotente el registro: una
    misma persona aceptando la misma versión dos veces no duplica filas. El
    ``aceptado_en`` es el momento de la aceptación, no el del alta en Auth.
    """

    __tablename__ = "consentimientos"
    __table_args__ = (
        UniqueConstraint("email", "version", name="uq_consentimiento_email_version"),
    )

    id = Column(Integer, primary_key=True)
    email = Column(String(254), nullable=False, index=True)
    nombre = Column(String(200), nullable=False, default="", server_default="")
    version = Column(String(20), nullable=False)
    ip_hash = Column(String(64), nullable=False, default="", server_default="")
    aceptado_en = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=text("CURRENT_TIMESTAMP"),
    )


class Membresia(Base):
    """Relación y rol de un usuario dentro de una organización."""

    __tablename__ = "membresias"
    __table_args__ = (
        UniqueConstraint("usuario_id", "organizacion_id", name="uq_membresia_usuario_organizacion"),
        CheckConstraint(
            "rol IN ('propietario', 'administrador', 'miembro', 'lectura')",
            name="ck_membresia_rol_valido",
        ),
    )

    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    organizacion_id = Column(Integer, ForeignKey("organizaciones.id", ondelete="CASCADE"), nullable=False, index=True)
    rol = Column(String(30), nullable=False, default="miembro")
    activa = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    usuario = relationship("Usuario", back_populates="membresias")
    organizacion = relationship("Organizacion", back_populates="membresias")


def sincronizar_usuario_auth(
    db,
    auth_user_id: str,
    email: str,
    nombre: str = "",
    email_verificado: bool = False,
) -> Usuario:
    """Vincula de forma idempotente una identidad verificada por Supabase.

    El email permite enlazar perfiles creados antes de incorporar Auth. Una vez
    vinculado, un UUID diferente nunca puede apropiarse de ese mismo perfil.
    """
    auth_user_id = str(auth_user_id or "").strip()
    email = str(email or "").strip().lower()
    if not auth_user_id or not email:
        raise VinculoIdentidadError("La identidad autenticada no es válida.")

    usuario = db.query(Usuario).filter(Usuario.auth_user_id == auth_user_id).first()
    por_email = db.query(Usuario).filter(Usuario.email == email).first()
    if usuario is not None and por_email is not None and usuario.id != por_email.id:
        raise VinculoIdentidadError("La identidad y el email pertenecen a perfiles distintos.")
    if usuario is None:
        usuario = por_email
    if usuario is None:
        # Los defaults Python de SQLAlchemy se aplican durante el INSERT, no al
        # construir la instancia. Fijarlo aquí evita interpretar ``None`` como
        # una cuenta desactivada antes del primer flush.
        usuario = Usuario(
            auth_user_id=auth_user_id,
            email=email,
            nombre=nombre[:200],
            activo=True,
        )
        db.add(usuario)
    elif usuario.auth_user_id not in {None, "", auth_user_id}:
        raise VinculoIdentidadError("El perfil ya está vinculado a otra identidad.")
    else:
        usuario.auth_user_id = auth_user_id
        usuario.email = email
        if nombre and not usuario.nombre:
            usuario.nombre = nombre[:200]

    if usuario.activo is False:
        raise VinculoIdentidadError("La cuenta de CotizaT está desactivada.")
    if email_verificado and usuario.email_verificado_at is None:
        usuario.email_verificado_at = datetime.utcnow()
    # E4-038: si el perfil todavía no tiene la marca de aceptación, se rellena
    # desde el registro de consentimientos (la persona pudo aceptar en el
    # formulario de registro, antes de que esta fila existiera). Es idempotente
    # y nunca pisa una marca ya asentada.
    if not usuario.acepto_terminos_version:
        consentimiento = _consentimiento_mas_reciente(db, email)
        if consentimiento is not None:
            usuario.acepto_terminos_version = consentimiento.version
            usuario.acepto_terminos_at = consentimiento.aceptado_en
    db.flush()
    return usuario


def _consentimiento_mas_reciente(db, email: str):
    """Última aceptación registrada para un correo, o ``None``.

    En PostgreSQL la lectura pasa por ``cotizat_security.obtener_consentimiento``
    (SECURITY DEFINER): la tabla tiene RLS de operador y una sesión de cliente
    no puede leerla directamente. En SQLite (escritorio y pruebas) no hay RLS
    y se consulta la tabla como cualquier otra.
    """
    if db.bind is not None and db.bind.dialect.name == "postgresql":
        from sqlalchemy import text as _text

        fila = db.execute(
            _text(
                "SELECT version, aceptado_en "
                "FROM cotizat_security.obtener_consentimiento(:email)"
            ),
            {"email": email},
        ).first()
        if fila is None:
            return None
        return SimpleNamespace(version=fila.version, aceptado_en=fila.aceptado_en)
    return (
        db.query(Consentimiento)
        .filter(Consentimiento.email == email)
        .order_by(Consentimiento.aceptado_en.desc(), Consentimiento.id.desc())
        .first()
    )


def reservar_id_organizacion(db) -> int | None:
    """Reserva el identificador de la nueva empresa desde su secuencia.

    Solo aplica a PostgreSQL. Devuelve ``None`` en SQLite, donde no hay RLS y
    el autoincremento del motor sigue siendo la vía natural.

    ``nextval`` no consulta la tabla, así que no lo alcanza ninguna política de
    fila: es la única forma de conocer el ``id`` **antes** de insertarlo y, por
    tanto, de emitir un ``INSERT`` sin ``RETURNING``. Ver
    :func:`crear_organizacion_con_propietario` para el motivo exacto.
    """
    if db.get_bind().dialect.name != "postgresql":
        return None
    return int(
        db.execute(
            text("SELECT nextval(pg_get_serial_sequence('public.organizaciones', 'id'))")
        ).scalar_one()
    )


def crear_organizacion_con_propietario(
    db,
    *,
    nombre: str,
    slug: str,
    usuario_id: int,
) -> Organizacion:
    """Crea la primera empresa de un usuario sin que RLS bloquee el alta.

    El bootstrap de una organización es circular: ``cotizat_org_select`` exige
    membresía para leer la fila, pero la membresía no puede existir hasta que
    la organización esté creada. ``INSERT ... RETURNING organizaciones.id`` —el
    SQL que SQLAlchemy genera por defecto para recuperar la clave primaria—
    ejecuta implícitamente esa política de lectura sobre la fila recién
    insertada y falla con ``InsufficientPrivilege`` aunque el ``WITH CHECK`` de
    ``cotizat_org_insert`` sí se cumpla.

    La corrección no relaja ninguna política: se reserva el ``id`` con
    ``nextval`` sobre ``organizaciones_id_seq`` y se inserta la fila con la
    clave primaria ya explícita, de modo que el ``INSERT`` no necesita
    ``RETURNING`` y nunca dispara la política ``SELECT``. La membresía de
    ``propietario`` se crea en la misma transacción, que es justo lo que
    ``cotizat_security.can_create_owner_membership`` autoriza.
    """
    organizacion = Organizacion(
        id=reservar_id_organizacion(db),
        nombre=nombre,
        slug=slug,
        activa=True,
        creada_por_usuario_id=usuario_id,
    )
    db.add(organizacion)
    # ``render_nulls`` no interviene aquí: con el id ya presente SQLAlchemy
    # omite el RETURNING. En SQLite (id None) conserva el autoincremento.
    db.flush()
    db.add(Membresia(
        usuario_id=usuario_id,
        organizacion_id=organizacion.id,
        rol="propietario",
        activa=True,
    ))
    db.flush()
    return organizacion


def membresias_activas(db, usuario_id: int) -> list[Membresia]:
    """Devuelve únicamente membresías y organizaciones activas."""
    return (
        db.query(Membresia)
        .join(Organizacion, Organizacion.id == Membresia.organizacion_id)
        .filter(
            Membresia.usuario_id == usuario_id,
            Membresia.activa.is_(True),
            Organizacion.activa.is_(True),
        )
        .order_by(Organizacion.nombre, Membresia.id)
        .all()
    )


def resolver_membresia_activa(
    db,
    usuario_id: int,
    organizacion_solicitada: int | None = None,
) -> Membresia | None:
    """Resuelve la empresa activa sin confiar en el identificador de cookie."""
    membresias = membresias_activas(db, usuario_id)
    if organizacion_solicitada is not None:
        for membresia in membresias:
            if membresia.organizacion_id == organizacion_solicitada:
                return membresia
        raise OrganizacionNoAutorizadaError(
            "No tienes una membresía activa en la organización solicitada."
        )
    if len(membresias) == 1:
        return membresias[0]
    return None


class TenantMixin:
    """Marca un agregado cuyo propietario obligatorio es una organización."""

    @declared_attr
    def organizacion_id(cls):
        return Column(
            Integer,
            ForeignKey("organizaciones.id", ondelete="RESTRICT"),
            nullable=False,
            default=1,  # compatibilidad temporal con la única empresa local
            index=True,
        )


class InvitacionOrganizacion(TenantMixin, Base):
    """Invitación de un solo uso; únicamente persiste el hash del secreto."""

    __tablename__ = "invitaciones_organizacion"
    __table_args__ = (
        CheckConstraint(
            "rol IN ('administrador', 'miembro', 'lectura')",
            name="ck_invitacion_rol_valido",
        ),
        UniqueConstraint("token_hash", name="uq_invitacion_token_hash"),
        Index(
            "ix_invitaciones_organizacion_email",
            "organizacion_id",
            "email",
        ),
    )

    id = Column(Integer, primary_key=True)
    email = Column(String(254), nullable=False)
    rol = Column(String(30), nullable=False, default="miembro")
    token_hash = Column(String(64), nullable=False)
    invitada_por_usuario_id = Column(
        Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    aceptada_por_usuario_id = Column(
        Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    expires_at = Column(DateTime, nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    organizacion = relationship("Organizacion")
    invitada_por = relationship("Usuario", foreign_keys=[invitada_por_usuario_id])
    aceptada_por = relationship("Usuario", foreign_keys=[aceptada_por_usuario_id])


class ArchivoAlmacenado(TenantMixin, Base):
    """Metadatos de un objeto privado; el binario vive fuera de PostgreSQL."""

    __tablename__ = "archivos_almacenados"
    __table_args__ = (
        UniqueConstraint(
            "organizacion_id", "object_key", name="uq_archivo_organizacion_clave"
        ),
        CheckConstraint(
            "object_key LIKE 'organizaciones/' || organizacion_id || '/%'",
            name="ck_archivo_clave_pertenece_organizacion",
        ),
    )

    id = Column(Integer, primary_key=True)
    object_key = Column(String(900), nullable=False)
    categoria = Column(String(80), nullable=False)
    content_type = Column(String(150), nullable=False)
    tamano_bytes = Column(Integer, nullable=False)
    sha256 = Column(String(64), nullable=False)
    nombre_original = Column(String(300), nullable=False)
    metadata_json = Column(Text, nullable=False, default="{}")


class Cliente(TenantMixin, Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(200), nullable=False)
    rif = Column(String(50), default="")
    pais = Column(String(80), default="")  # vacío: hereda el país de la organización (LatAm)
    telefono = Column(String(50), default="")
    email = Column(String(200), default="")
    direccion = Column(Text, default="")
    es_demo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    presupuestos = relationship("Presupuesto", back_populates="cliente")


class Presupuesto(TenantMixin, Base):
    __tablename__ = "presupuestos"
    __table_args__ = (
        UniqueConstraint("organizacion_id", "numero", name="uq_presupuesto_organizacion_numero"),
    )

    id = Column(Integer, primary_key=True)
    numero = Column(String(20), nullable=False)
    year = Column(Integer, nullable=False)
    fecha = Column(Date, nullable=False, default=date.today)
    # Proyecto / obra
    titulo = Column(String(250), default="")
    direccion_obra = Column(String(300), default="")
    codigo_postal = Column(String(20), default="")
    # Condiciones comerciales
    validez_dias = Column(Integer, default=30)
    moneda = Column(String(10), default="USD")
    tipo_cambio = Column(Float, nullable=True)  # Bs por USD (solo referencia)
    impuesto_pct = Column(Float, default=16.0)
    descuento_pct = Column(Float, default=0.0)
    estado = Column(String(20), default="borrador")
    es_demo = Column(Boolean, default=False)
    notas = Column(Text, default="")
    condiciones = Column(Text, default="")
    con_portada = Column(Boolean, default=False)
    foto_proyecto = Column(String(300), default="")
    mostrar_firmas = Column(Boolean, default=False)
    mostrar_resumen_capitulos = Column(Boolean, default=False)
    mostrar_garantias = Column(Boolean, default=False)
    firma_cliente = Column(String(300), default="")   # referencia lógica o ruta local histórica
    # Funciones económicas avanzadas (apagadas por defecto para conservar
    # el creador simple).
    usar_funciones_avanzadas = Column(Boolean, default=False)
    gastos_indirectos_pct = Column(Float, default=0.0)
    imprevistos_pct = Column(Float, default=0.0)
    transporte_monto = Column(Float, default=0.0)
    otros_cargos_monto = Column(Float, default=0.0)
    estilo_pdf = Column(String(30), default="elegante")
    mostrar_ahorro = Column(Boolean, default=False)
    incluir_anexos = Column(Boolean, default=False)
    numero_control = Column(String(80), default="")
    fecha_tipo_cambio = Column(Date, nullable=True)
    retencion_pct = Column(Float, default=0.0)
    operacion_exenta = Column(Boolean, default=False)
    clausula_cambiaria = Column(Text, default="")
    client_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    cliente = relationship("Cliente", back_populates="presupuestos")
    capitulos = relationship(
        "Capitulo",
        back_populates="presupuesto",
        cascade="all, delete-orphan",
        order_by="Capitulo.orden, Capitulo.id",
    )
    anexos = relationship("AnexoPresupuesto", back_populates="presupuesto", cascade="all, delete-orphan", order_by="AnexoPresupuesto.id")
    versiones = relationship("PresupuestoVersion", back_populates="presupuesto", cascade="all, delete-orphan", order_by="PresupuestoVersion.numero_version.desc()")
    enlaces_publicos = relationship(
        "EnlacePropuesta",
        back_populates="presupuesto",
        cascade="all, delete-orphan",
        order_by="EnlacePropuesta.created_at.desc()",
    )
    notas_seguimiento = relationship(
        "NotaSeguimiento",
        back_populates="presupuesto",
        cascade="all, delete-orphan",
        order_by="NotaSeguimiento.created_at.desc(), NotaSeguimiento.id.desc()",
    )

    # ---- Partidas (todos los capítulos, en orden) ---------------------
    @property
    def todas_partidas(self):
        return [p for cap in self.capitulos for p in cap.partidas]

    # ---- Totales calculados -------------------------------------------
    @property
    def _totales(self):
        from .services.calculations import calcular_totales
        return calcular_totales(self)

    @property
    def subtotal(self):
        return float(self._totales.subtotal)

    @property
    def subtotal_opcional(self):
        return float(self._totales.subtotal_opcional)

    @property
    def subtotal_alternativas(self):
        return float(self._totales.subtotal_alternativas)

    @property
    def costes_adicionales(self):
        return float(self._totales.costes_adicionales)

    @property
    def descuento_monto(self):
        return float(self._totales.descuento)

    @property
    def base(self):
        return float(self._totales.base)

    @property
    def impuesto_monto(self):
        return float(self._totales.impuesto)

    @property
    def coste_interno(self):
        return float(self._totales.coste_interno)

    @property
    def margen(self):
        return float(self._totales.margen)

    @property
    def margen_pct(self):
        return float(self._totales.margen_pct)

    @property
    def total_productos(self):
        return float(self._totales.total_productos)

    @property
    def coste_productos(self):
        return float(self._totales.coste_productos)

    @property
    def margen_productos(self):
        return float(self._totales.margen_productos)

    @property
    def margen_productos_pct(self):
        return float(self._totales.margen_productos_pct)

    @property
    def subtotal_obra(self):
        return float(self._totales.subtotal_obra)

    @property
    def coste_obra(self):
        return float(self._totales.coste_obra)

    @property
    def margen_obra(self):
        return float(self._totales.margen_obra)

    @property
    def margen_obra_pct(self):
        return float(self._totales.margen_obra_pct)

    @property
    def total(self):
        return float(self._totales.total)

    @property
    def garantias_familias(self):
        from .services.garantias import familias_para_pdf
        return familias_para_pdf(self)

    @property
    def garantias_nota_legal(self):
        from .services.garantias import NOTA_LEGAL
        return NOTA_LEGAL


class PresupuestoVersion(TenantMixin, Base):
    """Instantánea inmutable creada al enviar, aprobar o versionar un documento."""
    __tablename__ = "presupuesto_versiones"

    id = Column(Integer, primary_key=True)
    presupuesto_id = Column(Integer, ForeignKey("presupuestos.id"), nullable=False)
    numero_version = Column(Integer, nullable=False)
    fecha = Column(DateTime, default=datetime.utcnow)
    motivo = Column(String(500), default="")
    estado = Column(String(30), default="borrador")
    total = Column(Float, default=0.0)
    datos_snapshot = Column(Text, nullable=False, default="{}")
    pdf_snapshot = Column(String(300), default="")

    presupuesto = relationship("Presupuesto", back_populates="versiones")



class EnlacePropuesta(TenantMixin, Base):
    """Acceso público revocable a una versión congelada de un presupuesto.

    Solo persiste el hash del secreto. Los datos duplicados aquí son el
    subconjunto deliberadamente público de la propuesta: la ruta sin sesión no
    necesita ni puede leer las demás tablas del tenant bajo RLS.
    """

    __tablename__ = "enlaces_propuesta"
    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_enlace_propuesta_token_hash"),
        CheckConstraint(
            "length(token_hash) = 64",
            name="ck_enlace_propuesta_token_hash_sha256",
        ),
        CheckConstraint(
            "respuesta IN ('pendiente', 'aceptada', 'rechazada')",
            name="ck_enlace_propuesta_respuesta_valida",
        ),
        Index(
            "ix_enlaces_propuesta_presupuesto_creado",
            "presupuesto_id",
            "created_at",
        ),
    )

    id = Column(Integer, primary_key=True)
    presupuesto_id = Column(
        Integer, ForeignKey("presupuestos.id", ondelete="CASCADE"), nullable=False
    )
    presupuesto_version_id = Column(
        Integer,
        ForeignKey("presupuesto_versiones.id", ondelete="CASCADE"),
        nullable=False,
    )
    presupuesto_version_numero = Column(Integer, nullable=False)
    token_hash = Column(String(64), nullable=False)
    token_prefix = Column(String(12), nullable=False, default="")
    pdf_snapshot = Column(String(900), nullable=False)
    empresa_nombre = Column(String(200), nullable=False, default="")
    cliente_nombre = Column(String(200), nullable=False, default="")
    presupuesto_numero = Column(String(20), nullable=False, default="")
    presupuesto_titulo = Column(String(250), nullable=False, default="")
    total = Column(Float, nullable=False, default=0.0)
    moneda = Column(String(10), nullable=False, default="USD")
    fecha_presupuesto = Column(Date, nullable=False)
    valido_hasta = Column(Date, nullable=False)
    creado_por_usuario_id = Column(
        Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    respuesta = Column(String(20), nullable=False, default="pendiente")
    respondido_por_nombre = Column(String(200), nullable=False, default="")
    respondido_por_email = Column(String(254), nullable=False, default="")
    respuesta_comentario = Column(Text, nullable=False, default="")
    responded_at = Column(DateTime, nullable=True)
    estado_presupuesto_actualizado = Column(Boolean, nullable=False, default=False)
    notificacion_enviada_at = Column(DateTime, nullable=True)
    notificacion_destinatarios = Column(Text, nullable=False, default="")
    notificacion_error = Column(Text, nullable=False, default="")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    presupuesto = relationship("Presupuesto", back_populates="enlaces_publicos")
    version = relationship("PresupuestoVersion")
    creado_por = relationship("Usuario")

    def vigente(self, ahora: datetime | None = None) -> bool:
        ahora = ahora or datetime.utcnow()
        return self.revoked_at is None and self.expires_at > ahora


class Capitulo(TenantMixin, Base):
    """Capítulo del presupuesto (MUROS Y PARTICIONES, ELECTRICIDAD…)."""

    __tablename__ = "capitulos"

    id = Column(Integer, primary_key=True)
    presupuesto_id = Column(Integer, ForeignKey("presupuestos.id"), nullable=False)
    nombre = Column(String(200), nullable=False)
    orden = Column(Integer, default=0)

    presupuesto = relationship("Presupuesto", back_populates="capitulos")
    partidas = relationship(
        "PresupuestoItem",
        back_populates="capitulo",
        cascade="all, delete-orphan",
        order_by="PresupuestoItem.orden, PresupuestoItem.id",
    )

    @property
    def subtotal(self):
        from .services.calculations import money
        total = 0.0
        avanzadas = bool(getattr(self.presupuesto, "usar_funciones_avanzadas", False))
        for partida in self.partidas:
            tipo = (getattr(partida, "tipo_partida", "included") or "included").lower()
            if avanzadas and tipo in {"excluded", "optional", "alternative"} and not getattr(partida, "seleccionada", False):
                continue
            total += partida.importe
        # `partida.importe` ya viene redondeado con ROUND_HALF_UP; el round
        # final corrige el error de coma flotante de la suma.
        return float(money(total))


class PresupuestoItem(TenantMixin, Base):
    """Partida: obra o material con cantidad y precio unitario.

    La cantidad total sale de la suma de sus mediciones; si no tiene,
    se usa el campo `cantidad` directamente.
    """

    __tablename__ = "presupuesto_items"

    id = Column(Integer, primary_key=True)
    capitulo_id = Column(Integer, ForeignKey("capitulos.id"), nullable=True)
    nombre = Column(String(250), default="")
    descripcion = Column(Text, default="")
    unidad = Column(String(20), default="ud")
    cantidad = Column(Float, default=0.0)          # usada si no hay mediciones
    precio_unitario = Column(Float, default=0.0)
    orden = Column(Integer, default=0)
    # Partida maestra del catálogo desde la que se insertó. Permite distinguir
    # un cambio «solo en este presupuesto» de una actualización del catálogo
    # sin afectar a presupuestos ya creados (sus precios están copiados aquí).
    partida_catalogo_id = Column(Integer, ForeignKey("partidas.id"), nullable=True)
    # Producto presupuestado (opcional)
    producto_nombre = Column(String(250), default="")
    producto_precio = Column(Float, nullable=True)
    # Coste de compra congelado al asociar el producto, para que el margen del
    # presupuesto no cambie al actualizar el catálogo posteriormente.
    producto_coste = Column(Float, nullable=True)
    producto_unidad = Column(String(20), default="")
    producto_imagen = Column(String(300), default="")   # referencia lógica o ruta local histórica
    # Campos avanzados, invisibles en el modo básico.
    tipo_partida = Column(String(20), default="included")
    seleccionada = Column(Boolean, default=False)
    coste_materiales = Column(Float, default=0.0)
    coste_mano_obra = Column(Float, default=0.0)
    coste_complementarios = Column(Float, default=0.0)  # costes directos complementarios CYPE
    coste_otros = Column(Float, default=0.0)
    desperdicio_pct = Column(Float, default=0.0)
    margen_pct = Column(Float, default=0.0)
    grupo_alternativa = Column(String(120), default="")
    mostrar_en_pdf = Column(Boolean, default=True)
    # Código de la base de precios / exportación técnica (p. ej. DPT020).
    # Es independiente del nombre comercial de la partida.
    codigo_externo = Column(String(100), default="")
    # Tiempo manual override (horas por unidad). Si se informa, tiene prioridad
    # máxima sobre descompuesto / catálogo / coste. Permite asignar horas
    # de forma rápida a partidas sin datos y detallar oficial/ayudante/equipo.
    tiempo_manual_horas = Column(Float, nullable=True)
    tiempo_manual_oficial_horas = Column(Float, nullable=True)
    tiempo_manual_ayudante_horas = Column(Float, nullable=True)
    tiempo_manual_equipo_horas = Column(Float, nullable=True)

    capitulo = relationship("Capitulo", back_populates="partidas")
    descomposicion_cype = relationship(
        "DescomposicionPartida",
        back_populates="partida",
        uselist=False,
        cascade="all, delete-orphan",
    )
    mediciones = relationship(
        "Medicion",
        back_populates="partida",
        cascade="all, delete-orphan",
        order_by="Medicion.orden, Medicion.id",
    )
    productos_opciones = relationship(
        "PresupuestoItemProducto",
        back_populates="partida",
        cascade="all, delete-orphan",
        order_by="PresupuestoItemProducto.orden, PresupuestoItemProducto.id",
    )

    @property
    def producto_seleccionado(self):
        """Devuelve la opción marcada por el cliente, o None si no hay
        ninguna marcada (en ese caso, el primario sigue siendo el que manda
        en el PDF y los totales).
        """
        for op in (self.productos_opciones or []):
            if op.seleccionado:
                return op
        return None

    @property
    def producto_para_pdf(self):
        """Producto que debe mostrarse en el PDF como «Producto presupuestado».

        Prioridad:
          1) opción marcada como seleccionada
          2) el campo primario de la partida (compatibilidad hacia atrás)
        """
        sel = self.producto_seleccionado
        if sel is not None:
            return sel
        return self

    @property
    def productos_multiples(self):
        """Lista COMPLETA de productos candidatos que debe mostrar el PDF.

        El cliente tiene que poder ver todas las alternativas aunque ya haya
        una marcada: es justo la información que necesita para decidir (y lo
        que permite que el PDF interactivo recalcule el precio al pulsar
        sobre cualquiera de ellas).

        La regla es:
          · Si la partida no tiene opciones alternativas, se devuelve el
            producto primario (compatibilidad hacia atrás).
          · Si las tiene, se devuelven TODAS. El producto primario se
            antepone como una opción más cuando no está ya representado en
            la lista (su nombre no coincide con ninguna opción), porque el
            primario es «el producto elegido ahora mismo» y sin él la lista
            estaría incompleta.

        La opción marcada como elegida se identifica con
        :attr:`indice_producto_elegido`.
        """
        opciones = list(self.productos_opciones or [])
        # Sin opciones alternativas: el primario manda
        if not opciones:
            return [self]
        # El primario solo se antepone si aporta un producto distinto. Al
        # marcar una opción como elegida, el editor copia sus datos al
        # primario: en ese caso el primario YA está en la lista y no debe
        # duplicarse.
        nombre_primario = (self.producto_nombre or "").strip().lower()
        if nombre_primario:
            nombres = {(op.nombre or "").strip().lower() for op in opciones}
            if nombre_primario not in nombres:
                return [self] + opciones
        return opciones

    @property
    def indice_producto_elegido(self):
        """Posición (en `productos_multiples`) del producto elegido.

        Prioridad: la opción marcada con ``seleccionado``; si no hay ninguna,
        la que coincide con el producto primario de la partida; y en último
        caso la primera de la lista. Nunca devuelve None, para que el PDF
        siempre tenga un precio de partida coherente con lo que se muestra.
        """
        lista = self.productos_multiples
        for i, op in enumerate(lista):
            if op is not self and getattr(op, "seleccionado", False):
                return i
        nombre_primario = (self.producto_nombre or "").strip().lower()
        if nombre_primario:
            for i, op in enumerate(lista):
                if (getattr(op, "nombre", "") or getattr(op, "producto_nombre", "") or "").strip().lower() == nombre_primario:
                    return i
        return 0

    @property
    def precio_base_sin_producto(self):
        """Precio unitario de la partida SIN el producto asociado.

        `precio_unitario` es siempre «precio de obra + precio del producto
        elegido». Al cambiar de producto solo varía el segundo sumando, así
        que esta base es la que permite recalcular la partida entera cuando
        el cliente elige otra alternativa.
        """
        precio = float(self.precio_unitario or 0.0)
        producto = self.producto_precio
        if producto is None:
            # Sin producto primario: si hay una opción elegida con precio,
            # ese importe también está incluido en el precio unitario.
            lista = self.productos_opciones or []
            elegido = self.producto_seleccionado
            if elegido is None and lista:
                elegido = None
            producto = float(elegido.precio or 0.0) if elegido is not None else 0.0
        return round(precio - float(producto or 0.0), 2)

    @property
    def cantidad_total(self):
        if self.mediciones:
            return sum(m.cantidad for m in self.mediciones)
        return self.cantidad or 0.0

    @property
    def importe(self):
        """Importe de la partida redondeado con la MISMA regla que los
        totales (ROUND_HALF_UP a 2 decimales).

        Antes se devolvía el producto sin redondear: al sumar varias partidas
        (capítulo, subtotal del PDF) el resultado podía diferir un céntimo del
        total calculado por `calcular_totales`, que redondea partida a
        partida. Con este cambio fila, capítulo, resumen y total coinciden
        siempre al céntimo.
        """
        from .services.calculations import money
        return float(money(self.cantidad_total * self.precio_unitario))

    @property
    def tiene_costes(self):
        """¿La partida dispone de datos de coste interno (materiales, mano de obra…)?"""
        return bool(
            (self.coste_materiales or 0) + (self.coste_mano_obra or 0)
            + (self.coste_complementarios or 0) + (self.coste_otros or 0)
        )

    @property
    def coste(self):
        from .services.calculations import coste_partida
        return float(coste_partida(self))

    @property
    def beneficio(self):
        from .services.calculations import beneficio_partida
        return float(beneficio_partida(self))

    @property
    def margen_beneficio_pct(self):
        from .services.calculations import margen_partida_pct
        return float(margen_partida_pct(self))

    @property
    def tiene_producto(self):
        # Considera también las opciones alternativas: una partida puede
        # no tener producto primario pero sí una lista de candidatos que
        # el cliente debe elegir.
        if self.producto_nombre or self.producto_imagen or self.producto_precio:
            return True
        return any(
            (op.nombre or op.imagen or op.precio)
            for op in (self.productos_opciones or [])
        )


class DescomposicionPartida(TenantMixin, Base):
    """Descompuesto técnico CYPE asociado a una partida de presupuesto.

    ``filas_originales_json`` preserva la matriz completa (incluidas las filas
    vacías intencionales, fórmulas y columnas), mientras que
    :class:`DescomposicionFila` permite calcular y mostrar cada recurso sin
    volver a interpretar el Excel original. El archivo fuente también queda
    guardado en Storage privado para una trazabilidad completamente reversible.
    """

    __tablename__ = "descomposiciones_partida"

    id = Column(Integer, primary_key=True)
    partida_id = Column(Integer, ForeignKey("presupuesto_items.id"), nullable=False, unique=True)
    codigo = Column(String(100), default="")
    unidad = Column(String(30), default="")
    nombre_hoja = Column(String(200), default="")
    archivo_origen = Column(String(300), default="")  # referencia lógica o ruta local histórica
    nombre_archivo_origen = Column(String(300), default="")
    rango_original = Column(String(100), default="")
    columnas_json = Column(Text, default="[]")
    rangos_combinados_json = Column(Text, default="[]")
    filas_originales_json = Column(Text, default="[]")
    coste_directo_unitario = Column(Float, default=0.0)
    # Procedencia de la descomposición: «cype» (importada de un .xlsx de CYPE,
    # conserva la matriz técnica original) o «manual» (creada/editada a mano
    # dentro del generador de presupuestos).
    origen = Column(String(20), default="manual")
    created_at = Column(DateTime, default=datetime.utcnow)

    partida = relationship("PresupuestoItem", back_populates="descomposicion_cype")
    filas = relationship(
        "DescomposicionFila",
        back_populates="descomposicion",
        cascade="all, delete-orphan",
        order_by="DescomposicionFila.orden, DescomposicionFila.id",
    )

    @staticmethod
    def _json_lista(valor):
        import json

        try:
            resultado = json.loads(valor or "[]")
        except (TypeError, ValueError):
            resultado = []
        return resultado if isinstance(resultado, list) else []

    @property
    def columnas(self):
        return self._json_lista(self.columnas_json)

    @property
    def rangos_combinados(self):
        return self._json_lista(self.rangos_combinados_json)


class DescomposicionFila(TenantMixin, Base):
    """Una fila física de un Excel CYPE, incluso si está vacía o es subtotal."""

    __tablename__ = "descomposicion_filas"

    id = Column(Integer, primary_key=True)
    descomposicion_id = Column(Integer, ForeignKey("descomposiciones_partida.id"), nullable=False)
    orden = Column(Integer, default=0)
    numero_fila_excel = Column(Integer, default=0)
    tipo = Column(String(30), default="otro")  # cabecera/grupo/recurso/subtotal/total/vacia
    grupo = Column(String(250), default="")
    # Categoría de coste explícita de la fila (materiales/mano_obra/
    # complementarios/otros). En las filas importadas de CYPE se deriva del
    # grupo y el código; en las filas creadas a mano el usuario la elige.
    categoria = Column(String(30), default="")
    codigo = Column(String(120), default="")
    unidad = Column(String(30), default="")
    descripcion = Column(Text, default="")
    rendimiento = Column(Float, nullable=True)
    precio_unitario = Column(Float, nullable=True)
    importe = Column(Float, nullable=True)
    celdas_json = Column(Text, default="[]")
    formulas_json = Column(Text, default="{}")

    descomposicion = relationship("DescomposicionPartida", back_populates="filas")

    @property
    def celdas(self):
        return DescomposicionPartida._json_lista(self.celdas_json)

    @property
    def formulas(self):
        import json

        try:
            resultado = json.loads(self.formulas_json or "{}")
        except (TypeError, ValueError):
            resultado = {}
        return resultado if isinstance(resultado, dict) else {}


class Medicion(TenantMixin, Base):
    """Línea de desglose de una partida (zona/concepto + cantidad)."""

    __tablename__ = "mediciones"

    id = Column(Integer, primary_key=True)
    partida_id = Column(Integer, ForeignKey("presupuesto_items.id"), nullable=False)
    concepto = Column(String(250), default="")
    cantidad = Column(Float, default=0.0)
    orden = Column(Integer, default=0)

    partida = relationship("PresupuestoItem", back_populates="mediciones")


class PresupuestoItemProducto(TenantMixin, Base):
    """Producto alternativo asociado a una partida.

    Cada partida puede tener varios productos a elegir para el cliente. La
    lógica de selección es la siguiente:

      · Si hay UN producto con ``seleccionado=True``, ese es el que aparece
        como "Producto presupuestado" en el PDF (y es el que se factura).
      · Si NINGUNO está marcado como seleccionado, el PDF muestra todos los
        productos como "opciones disponibles" con sus precios respectivos.
      · El producto "primario" (``PresupuestoItem.producto_nombre``, etc.)
        sigue siendo el que se muestra cuando la partida no tiene opciones
        extra (compatibilidad hacia atrás).

    La cantidad/precio mostrada en el PDF pertenece a cada producto concreto,
    de modo que el cliente puede ver "Porcelanato A: 68,00 $ / m2" y
    "Porcelanato B: 92,00 $ / m2" lado a lado antes de decidirse.
    """

    __tablename__ = "presupuesto_item_productos"

    id = Column(Integer, primary_key=True)
    partida_id = Column(Integer, ForeignKey("presupuesto_items.id"), nullable=False)
    nombre = Column(String(250), default="")
    descripcion = Column(Text, default="")
    precio = Column(Float, default=0.0)
    coste = Column(Float, nullable=True)
    unidad = Column(String(20), default="")
    categoria = Column(String(80), default="")
    marca = Column(String(120), default="")
    modelo = Column(String(120), default="")
    sku = Column(String(120), default="")
    color = Column(String(80), default="")
    acabado = Column(String(120), default="")
    imagen = Column(String(300), default="")
    seleccionado = Column(Boolean, default=False)
    orden = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    partida = relationship("PresupuestoItem", back_populates="productos_opciones")


class Configuracion(TenantMixin, Base):
    __tablename__ = "configuracion"

    id = Column(Integer, primary_key=True)
    # Datos de la empresa
    empresa_nombre = Column(String(200), default="Mi Empresa")
    empresa_legal = Column(String(250), default="")       # razón social
    empresa_rif = Column(String(50), default="")
    empresa_pais = Column(String(80), default="Venezuela")
    empresa_ciudad = Column(String(120), default="")
    empresa_direccion = Column(Text, default="")
    empresa_telefono = Column(String(50), default="")
    empresa_email = Column(String(200), default="")
    empresa_web = Column(String(200), default="")
    logo = Column(String(300), default="")                # referencia lógica o ruta local histórica
    # Primer inicio y recorrido hasta el primer PDF real.
    onboarding_completado = Column(Boolean, default=False)
    onboarding_modo = Column(String(20), default="")      # demo / limpio / existente
    onboarding_iniciado_at = Column(DateTime, nullable=True)
    onboarding_completado_at = Column(DateTime, nullable=True)
    onboarding_catalogo_revisado = Column(Boolean, default=False)
    onboarding_pdf_descargado = Column(Boolean, default=False)
    primer_pdf_at = Column(DateTime, nullable=True)
    # Valores por defecto para presupuestos nuevos
    iva_default = Column(Float, default=16.0)
    moneda_default = Column(String(10), default="USD")
    validez_default = Column(Integer, default=30)
    notas_default = Column(Text, default="")
    condiciones_default = Column(Text, default="")
    pdf_color = Column(String(10), default="#04265D")
    logo_ancho_pdf = Column(Float, default=360.0)   # ancho máx. del logo en el PDF (puntos)
    con_portada_default = Column(Boolean, default=False)
    mostrar_firmas_default = Column(Boolean, default=False)
    mostrar_resumen_capitulos_default = Column(Boolean, default=False)
    mostrar_garantias_default = Column(Boolean, default=False)
    activar_funciones_avanzadas = Column(Boolean, default=False)
    mostrar_costes_internos = Column(Boolean, default=False)
    mostrar_alternativas = Column(Boolean, default=False)
    mostrar_cargos_adicionales = Column(Boolean, default=False)
    activar_funciones_venezuela = Column(Boolean, default=False)
    mostrar_numero_control = Column(Boolean, default=False)
    mostrar_tasa_cambio = Column(Boolean, default=False)
    mostrar_total_bs = Column(Boolean, default=False)
    mostrar_retenciones = Column(Boolean, default=False)
    mostrar_clausula_cambiaria = Column(Boolean, default=False)
    datos_bancarios = Column(Text, default="")
    # Semana 2 — Bloque A: etiqueta fiscal genérica por país (RIF, NIT, RUT, CUIT, RUC, RFC…)
    etiqueta_id_fiscal = Column(String(20), default="RIF")
    # Tasa de referencia para conversión USD -> moneda local (bloque moneda/tasa auto)
    # Ej: 3128.65 COP por 1 USD. NULL = 1 (cuando moneda_default es USD).
    tasa_cambio = Column(Float, nullable=True)
    fecha_tasa = Column(Date, nullable=True)

    # Alias LatAm para el flag regional (Semana 2). El nombre histórico
    # `activar_funciones_venezuela` se mantiene en la base; el nuevo
    # `activar_funciones_regionales` mapea a la misma columna para no
    # exigir una migración de rename en este bloque. El próximo bloque
    # migrará el nombre físico cuando toque.
    @property
    def activar_funciones_regionales(self) -> bool:
        return bool(getattr(self, "activar_funciones_venezuela", False))

    @activar_funciones_regionales.setter
    def activar_funciones_regionales(self, valor: bool) -> None:
        self.activar_funciones_venezuela = bool(valor)
    # Estimación de tiempos de obra
    horas_jornada = Column(Float, default=8.0)          # horas por jornada laboral
    tarifa_hora_media = Column(Float, default=8.0)      # moneda/h para estimar horas desde el coste
    estimar_tiempo_por_coste = Column(Boolean, default=True)
    # Control de siembra inicial: una vez se crea el catálogo por primera vez
    # no se vuelve a inyectar automáticamente (evita que partidas borradas
    # reaparezcan tras una actualización).
    semilla_catalogo_aplicada = Column(Boolean, default=False)
    # Versión estructural del catálogo oficial aplicada a la organización.
    # Es independiente de la bandera de semilla: una actualización puede
    # reclasificar partidas oficiales existentes sin resucitar las borradas.
    version_catalogo = Column(Integer, default=0)
    semilla_productos_aplicada = Column(Boolean, default=False)
    semilla_recetas_aplicada = Column(Boolean, default=False)


class Plantilla(TenantMixin, Base):
    """Plantilla de presupuesto reutilizable.

    Guarda la estructura (capítulos, partidas y mediciones) en formato JSON
    para crear presupuestos nuevos a partir de ella sin necesidad de volver a
    escribirlos. No incluye cliente, obra ni condiciones comerciales.
    """

    __tablename__ = "plantillas"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(200), nullable=False)
    datos = Column(Text, default="")            # JSON con los capítulos
    created_at = Column(DateTime, default=datetime.utcnow)


class RecetaEstancia(TenantMixin, Base):
    """Pack / Receta de estancia para armar capítulos de obra con 1 clic.

    Guarda la plantilla de un capítulo completo (ej. 'Baño Principal de Lujo')
    con un multiplicador o fórmula proporcional de cantidad respecto a la
    medida base de la estancia (m² o und).
    """

    __tablename__ = "recetas_estancia"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(String(300), default="")
    categoria = Column(String(80), default="Baños")  # Baños, Cocinas, Suelos, Habitaciones, Electricidad, Otros
    unidad_base = Column(String(20), default="m²")
    cantidad_base_default = Column(Float, default=10.0)
    datos = Column(Text, default="[]")  # JSON con lista de partidas del pack y sus coeficientes / datos
    created_at = Column(DateTime, default=datetime.utcnow)


class CategoriaPartida(TenantMixin, Base):
    """Nodo del árbol capítulo → subcapítulo → apartado.

    ``categoria`` y ``subcategoria`` se mantienen durante la transición para
    copias antiguas y categorías creadas por el usuario. Los campos nuevos
    representan la jerarquía de forma normalizada y permiten ordenar por
    código en lugar de por texto.
    """

    __tablename__ = "categorias_partidas"
    __table_args__ = (
        UniqueConstraint(
            "organizacion_id", "codigo_completo",
            name="uq_categoria_partida_organizacion_codigo",
        ),
    )

    id = Column(Integer, primary_key=True)
    categoria = Column(String(80), nullable=False)
    subcategoria = Column(String(80), default="")
    parent_id = Column(
        Integer,
        ForeignKey("categorias_partidas.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    codigo_segmento = Column(String(2), default="")
    # NULL para categorías libres: PostgreSQL/SQLite permiten varios NULL bajo
    # la restricción única, mientras los nodos oficiales sí quedan protegidos.
    codigo_completo = Column(String(8), nullable=True)
    nombre = Column(String(120), default="")
    nivel = Column(Integer, default=1)
    orden = Column(Integer, default=0)
    ambito = Column(String(30), default="reforma")
    activa = Column(Boolean, default=True)
    oficial = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    parent = relationship(
        "CategoriaPartida",
        remote_side="CategoriaPartida.id",
        back_populates="hijos",
    )
    hijos = relationship(
        "CategoriaPartida",
        back_populates="parent",
        cascade="all, delete-orphan",
        single_parent=True,
    )
    partidas = relationship("Partida", back_populates="nodo_categoria")


class Partida(TenantMixin, Base):
    """Catálogo editable y privado de una organización."""

    __tablename__ = "partidas"
    __table_args__ = (
        UniqueConstraint("organizacion_id", "nombre", name="uq_partida_organizacion_nombre"),
        UniqueConstraint(
            "organizacion_id", "catalogo_uid",
            name="uq_partida_organizacion_catalogo_uid",
        ),
    )

    id = Column(Integer, primary_key=True)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text, default="")
    precio_unitario = Column(Float, default=0.0)
    unidad = Column(String(30), default="ud")          # m2, ud, ml, juego, etc.
    categoria = Column(String(80), default="General")  # Pintura, Carpintería, Marmolería, etc.
    usos = Column(Integer, default=0)                  # nº de veces insertada en presupuestos
    ultimo_uso = Column(DateTime, nullable=True)        # para priorizar el trabajo usado recientemente
    # Información técnica del catálogo. Es opcional para no convertir el
    # constructor de presupuestos en un formulario complejo.
    codigo_interno = Column(String(80), default="")
    subcategoria = Column(String(80), default="")
    apartado = Column(String(120), default="")
    categoria_id = Column(
        Integer,
        ForeignKey("categorias_partidas.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    codigo_clasificacion = Column(String(20), default="")
    codigo_legacy = Column(String(80), default="")
    version_catalogo = Column(Integer, default=0)
    # Identidad estable del registro oficial, independiente de su código/ruta.
    # NULL identifica partidas creadas por la propia organización.
    catalogo_uid = Column(String(100), nullable=True)
    es_oficial = Column(Boolean, default=False)
    oculta = Column(Boolean, default=False)
    version_alta_catalogo = Column(Integer, default=0)
    coste_materiales = Column(Float, default=0.0)
    coste_mano_obra = Column(Float, default=0.0)
    coste_complementarios = Column(Float, default=0.0)  # costes directos complementarios CYPE
    coste_otros = Column(Float, default=0.0)
    tiempo_estimado_horas = Column(Float, nullable=True)
    # Desglose opcional por rol para el catálogo. Si no se informan, el tiempo
    # total se reparte (60% oficial / 40% ayudante) al usar la partida.
    tiempo_oficial_horas = Column(Float, nullable=True)
    tiempo_ayudante_horas = Column(Float, nullable=True)
    tiempo_equipo_horas = Column(Float, nullable=True)
    proveedor = Column(String(150), default="")
    rendimiento = Column(String(120), default="")
    desperdicio_recomendado_pct = Column(Float, default=0.0)
    imagen = Column(String(300), default="")
    notas_tecnicas = Column(Text, default="")
    # Descomposición editable del catálogo. Se guarda como JSON para que una
    # partida creada/importada fuera de un presupuesto conserve sus recursos.
    codigo_externo = Column(String(100), default="")
    descomposicion_json = Column(Text, default="[]")
    fecha_actualizacion_precio = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    nodo_categoria = relationship("CategoriaPartida", back_populates="partidas")

    @property
    def ruta_catalogo(self) -> str:
        """Ruta legible sin segmentos vacíos para vistas y exportaciones."""
        return " › ".join(
            valor for valor in (self.categoria, self.subcategoria, self.apartado)
            if (valor or "").strip()
        )

    @property
    def coste(self) -> float:
        return round(
            (self.coste_materiales or 0.0)
            + (self.coste_mano_obra or 0.0)
            + (self.coste_complementarios or 0.0)
            + (self.coste_otros or 0.0),
            2,
        )


class Producto(TenantMixin, Base):
    """Catálogo de productos reutilizables (p. ej. materiales con foto).

    Los productos son independientes de las partidas: una partida («Solado
    de porcelanato») puede tener asociado cualquiera de estos productos
    («Porcelanato 60x60», «Porcelanato 90x90», …). Los productos nuevos que
    se escriben mientras se crea un presupuesto se guardan aquí
    automáticamente para poder reutilizarlos en el futuro.
    """

    __tablename__ = "productos"
    __table_args__ = (
        UniqueConstraint("organizacion_id", "nombre", name="uq_producto_organizacion_nombre"),
    )

    id = Column(Integer, primary_key=True)
    nombre = Column(String(250), nullable=False)
    descripcion = Column(Text, default="")
    precio_unitario = Column(Float, default=0.0)
    unidad = Column(String(30), default="ud")
    categoria = Column(String(80), default="General")
    imagen = Column(String(300), default="")           # referencia lógica o ruta local histórica
    # El precio unitario existente se conserva como precio de venta para no
    # alterar presupuestos ni catálogos creados con versiones anteriores.
    precio_compra = Column(Float, nullable=True)
    fecha_actualizacion_precio = Column(DateTime, default=datetime.utcnow)
    marca = Column(String(120), default="")
    modelo = Column(String(120), default="")
    sku = Column(String(120), default="")
    proveedor = Column(String(150), default="")
    color = Column(String(80), default="")
    acabado = Column(String(120), default="")
    formato = Column(String(120), default="")
    tiempo_entrega_dias = Column(Integer, nullable=True)
    variantes = Column(Text, default="")
    ficha_tecnica = Column(String(300), default="")    # referencia lógica del PDF o ruta histórica
    imagenes = Column(Text, default="[]")              # galería JSON; `imagen` es la principal
    usos = Column(Integer, default=0)
    ultimo_uso = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    @property
    def imagenes_lista(self):
        """Galería tolerante a datos antiguos/corruptos, sin duplicar portada."""
        import json

        try:
            rutas = json.loads(self.imagenes or "[]")
        except (TypeError, ValueError):
            rutas = []
        if not isinstance(rutas, list):
            rutas = []
        limpias = []
        for ruta in ([self.imagen] if self.imagen else []) + rutas:
            if isinstance(ruta, str) and ruta and ruta not in limpias:
                limpias.append(ruta)
        return limpias


class Recurso(TenantMixin, Base):
    """Catálogo central de precios unitarios (recursos).

    Cada fila es un precio unitario reutilizable (mano de obra, material,
    equipo, etc.) que puede aparecer en la descomposición de muchas partidas.
    Cambiar el precio aquí propaga el cambio a todas las partidas que lo
    usan (tanto del catálogo de Partidas como de los DescomposicionFila de
    presupuestos), recalculando importes y costes directos.

    La clave de matching es:
      · si tiene código → código normalizado
      · si no → descripción + unidad normalizadas
    La categoría (materiales/mano_obra/complementarios/otros) sirve para
    organizar la pestaña por familias.
    """

    __tablename__ = "recursos"

    id = Column(Integer, primary_key=True)
    codigo = Column(String(80), default="")
    descripcion = Column(String(250), nullable=False)
    unidad = Column(String(30), default="ud")
    categoria = Column(String(30), default="otros")  # materiales, mano_obra, complementarios, otros
    grupo = Column(String(250), default="")
    precio = Column(Float, default=0.0)
    proveedor = Column(String(150), default="")
    # Metadatos
    usos = Column(Integer, default=0)
    ultimo_uso = Column(DateTime, nullable=True)
    fecha_actualizacion_precio = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    @property
    def clave(self) -> str:
        """Clave estable para matching (código si existe, si no desc+unidad)."""
        import unicodedata, re
        def norm(v: str) -> str:
            t = unicodedata.normalize("NFD", str(v or "").strip().lower())
            t = "".join(c for c in t if unicodedata.category(c) != "Mn")
            return re.sub(r"[^a-z0-9]+", "", t)
        cod = norm(self.codigo)
        if cod:
            return f"cod:{cod}"
        return f"desc:{norm(self.descripcion)}|{norm(self.unidad)}|{norm(self.categoria)}"


class NotaSeguimiento(TenantMixin, Base):
    """Nota interna de seguimiento sobre un presupuesto.

    «Llamé al cliente y quiere cambiar el piso del baño», etc. Solo la ve
    la empresa; no aparece en el PDF.
    """

    __tablename__ = "notas_seguimiento"

    id = Column(Integer, primary_key=True)
    presupuesto_id = Column(Integer, ForeignKey("presupuestos.id"), nullable=False)
    texto = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    presupuesto = relationship("Presupuesto", back_populates="notas_seguimiento")


class Factura(TenantMixin, Base):
    """Factura generada a partir de un presupuesto aprobado.

    Copia la estructura del presupuesto (capítulos y partidas) en el
    momento de la conversión, de modo que las modificaciones posteriores
    del presupuesto no alteran la factura emitida.
    """

    __tablename__ = "facturas"
    __table_args__ = (
        UniqueConstraint("organizacion_id", "numero", name="uq_factura_organizacion_numero"),
    )

    id = Column(Integer, primary_key=True)
    numero = Column(String(20), nullable=False)
    year = Column(Integer, nullable=False)
    fecha = Column(Date, nullable=False, default=date.today)
    titulo = Column(String(250), default="")
    direccion_obra = Column(String(300), default="")
    codigo_postal = Column(String(20), default="")
    moneda = Column(String(10), default="USD")
    impuesto_pct = Column(Float, default=16.0)
    descuento_pct = Column(Float, default=0.0)
    estado = Column(String(20), default="emitida")     # emitida / anulada
    notas = Column(Text, default="")
    condiciones = Column(Text, default="")
    presupuesto_id = Column(Integer, ForeignKey("presupuestos.id"), nullable=True)
    presupuesto_version_id = Column(Integer, ForeignKey("presupuesto_versiones.id"), nullable=True)
    client_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    cliente = relationship("Cliente")
    presupuesto = relationship("Presupuesto")
    presupuesto_version = relationship("PresupuestoVersion")
    capitulos = relationship(
        "FacturaCapitulo",
        back_populates="factura",
        cascade="all, delete-orphan",
        order_by="FacturaCapitulo.orden, FacturaCapitulo.id",
    )

    # Campos que el motor del PDF espera en un presupuesto y que una
    # factura no utiliza (la cabecera los omite si son falsy).
    validez_dias = None
    tipo_cambio = None
    con_portada = False
    foto_proyecto = ""
    mostrar_firmas = False
    mostrar_resumen_capitulos = False
    mostrar_garantias = False
    firma_cliente = ""

    @property
    def todas_partidas(self):
        return [p for cap in self.capitulos for p in cap.partidas]

    @property
    def subtotal(self):
        from .services.calculations import money
        # `importe` de cada FacturaItem ya viene redondeado con la misma
        # regla que el presupuesto; el redondeo final corrige el error de
        # coma flotante de la suma.
        return float(money(sum(p.importe for p in self.todas_partidas)))

    @property
    def descuento_monto(self):
        from .services.calculations import money
        return float(money(self.subtotal * self.descuento_pct / 100.0))

    @property
    def base(self):
        from .services.calculations import money
        return float(money(self.subtotal - self.descuento_monto))

    @property
    def impuesto_monto(self):
        from .services.calculations import money
        return float(money(self.base * self.impuesto_pct / 100.0))

    @property
    def total(self):
        from .services.calculations import money
        return float(money(self.base + self.impuesto_monto))


class FacturaCapitulo(TenantMixin, Base):
    __tablename__ = "factura_capitulos"

    id = Column(Integer, primary_key=True)
    factura_id = Column(Integer, ForeignKey("facturas.id"), nullable=False)
    nombre = Column(String(200), nullable=False)
    orden = Column(Integer, default=0)

    factura = relationship("Factura", back_populates="capitulos")
    partidas = relationship(
        "FacturaItem",
        back_populates="capitulo",
        cascade="all, delete-orphan",
        order_by="FacturaItem.orden, FacturaItem.id",
    )

    @property
    def subtotal(self):
        from .services.calculations import money
        return float(money(sum(p.importe for p in self.partidas)))


class FacturaItem(TenantMixin, Base):
    __tablename__ = "factura_items"

    id = Column(Integer, primary_key=True)
    capitulo_id = Column(Integer, ForeignKey("factura_capitulos.id"), nullable=False)
    nombre = Column(String(250), default="")
    descripcion = Column(Text, default="")
    unidad = Column(String(20), default="ud")
    cantidad = Column(Float, default=0.0)
    precio_unitario = Column(Float, default=0.0)
    orden = Column(Integer, default=0)

    capitulo = relationship("FacturaCapitulo", back_populates="partidas")

    # Mismo «contrato» que PresupuestoItem para reutilizar el motor del PDF
    @property
    def cantidad_total(self):
        return self.cantidad or 0.0

    @property
    def importe(self):
        from .services.calculations import money
        return float(money(self.cantidad_total * self.precio_unitario))

    @property
    def mediciones(self):
        return []

    @property
    def tiene_producto(self):
        return False

    producto_nombre = ""
    producto_precio = None
    producto_unidad = ""
    producto_imagen = ""


DATOS_EMPRESA_DEFECTO = {
    "empresa_nombre": "Mi Empresa",
    "empresa_pais": "Venezuela",
    "empresa_ciudad": "",
    "empresa_telefono": "",
    "empresa_email": "",
    "empresa_web": "",
    "empresa_direccion": "",
    "onboarding_completado": False,
}


def asegurar_organizacion_local(db) -> Organizacion:
    """Conserva los datos históricos dentro de una organización transitoria.

    Esta organización permite seguir desarrollando en el navegador sin fingir
    que ya existe autenticación. En la versión web cada sesión elegirá una
    organización a través de su membresía.
    """
    organizacion = db.query(Organizacion).filter(
        Organizacion.slug == "espacio-local"
    ).first()
    if organizacion is None:
        organizacion = Organizacion(nombre="Espacio local", slug="espacio-local")
        db.add(organizacion)
        db.flush()
    return organizacion


def asegurar_config(db):
    """Crea configuración neutra dentro de la organización activa."""
    organizacion_id = db.info.get("organizacion_id")
    if organizacion_id is None:
        organizacion_id = asegurar_organizacion_local(db).id
        usar_organizacion(db, organizacion_id)
    cfg = db.query(Configuracion).first()
    if cfg is None:
        db.add(Configuracion(
            organizacion_id=organizacion_id,
            **DATOS_EMPRESA_DEFECTO,
        ))
    # También persiste la organización recién creada cuando la configuración
    # ya existía en una base local anterior.
    db.commit()


def proximo_numero(db, year):
    """Calcula el siguiente número de presupuesto para el año dado.

    Formato: P-<año>-<secuencial de 3 dígitos>, p. ej. P-2026-001
    """
    numeros = db.query(Presupuesto.numero).filter(Presupuesto.year == year).all()
    max_sec = 0
    for (numero,) in numeros:
        try:
            sec = int(numero.rsplit("-", 1)[-1])
            max_sec = max(max_sec, sec)
        except (ValueError, IndexError):
            continue
    return f"P-{year}-{max_sec + 1:03d}"


def proximo_numero_factura(db, year):
    """Calcula el siguiente número de documento de cobro para el año dado.

    Formato: DC-<año>-<secuencial de 3 dígitos>, p. ej. DC-2026-001.
    Se consideran también los números históricos F-* para continuar la
    secuencia sin alterar documentos existentes.
    """
    numeros = db.query(Factura.numero).filter(Factura.year == year).all()
    max_sec = 0
    for (numero,) in numeros:
        try:
            sec = int(numero.rsplit("-", 1)[-1])
            max_sec = max(max_sec, sec)
        except (ValueError, IndexError):
            continue
    return f"DC-{year}-{max_sec + 1:03d}"


def marcar_vencidos(db):
    """Pasa a «vencido» los presupuestos enviados cuya validez ya expiró.

    Se ejecuta mediante una escritura same-origin al abrir el dashboard o el
    historial; las rutas GET permanecen libres de efectos empresariales.
    """
    hoy = date.today()
    cambiados = 0
    for p in db.query(Presupuesto).filter(Presupuesto.estado == "enviado").all():
        if p.validez_dias and p.fecha + timedelta(days=p.validez_dias) < hoy:
            p.estado = "vencido"
            cambiados += 1
    if cambiados:
        db.commit()
    return cambiados


# ---------------------------------------------------------------------------
# Migraciones ligeras para bases de datos creadas con versiones anteriores
# ---------------------------------------------------------------------------

def _columnas(engine, tabla):
    insp = inspect(engine)
    if not insp.has_table(tabla):
        return None
    return {c["name"] for c in insp.get_columns(tabla)}


def _sql_defecto(columna):
    """Valor DEFAULT seguro para un ALTER TABLE, deducido del modelo."""
    defecto = columna.default
    valor = getattr(defecto, "arg", None) if defecto is not None else None
    if defecto is None or callable(valor):
        return None  # sin default o calculado en Python (p. ej. datetime.utcnow)
    if isinstance(valor, bool):
        return "1" if valor else "0"
    if isinstance(valor, (int, float)):
        return str(valor)
    if isinstance(valor, str):
        escapado = valor.replace("'", "''")
        return f"'{escapado}'"
    return None


def _sincronizar_columnas_modelos(engine, conn):
    """Red de seguridad: añade las columnas del modelo que falten en la base.

    Las migraciones de ``aditivas`` se escriben a mano y es fácil olvidar una
    al añadir un campo nuevo (ocurrió con ``mostrar_garantias_default``: la
    aplicación arrancaba contra una base antigua, SQLAlchemy pedía la columna
    inexistente y el arranque moría con «no such column», que Uvicorn traduce
    a ``SystemExit: 3`` sin abrir la ventana).

    Aquí se compara el esquema declarado en los modelos con el real y se
    añaden las columnas que falten. Solo se tocan columnas ampliables sin
    riesgo (anulables o con valor por defecto constante); las demás se dejan
    a las migraciones manuales. Nunca borra ni modifica datos existentes.
    """
    añadidas = []
    for tabla in Base.metadata.sorted_tables:
        existentes = _columnas(engine, tabla.name)
        if existentes is None:
            continue  # tabla nueva: create_all ya la habrá creado
        for columna in tabla.columns:
            if columna.name in existentes or columna.primary_key:
                continue
            defecto = _sql_defecto(columna)
            if not columna.nullable and defecto is None:
                continue  # SQLite no admite NOT NULL sin default al ampliar
            try:
                tipo = columna.type.compile(engine.dialect)
            except Exception:
                continue  # tipo no representable: lo cubre la migración manual
            sql = f"ALTER TABLE {tabla.name} ADD COLUMN {columna.name} {tipo}"
            if defecto is not None:
                sql += f" DEFAULT {defecto}"
            try:
                conn.execute(text(sql))
                añadidas.append(f"{tabla.name}.{columna.name}")
            except Exception:
                pass  # no impedir el arranque por una columna concreta
    return añadidas


def migrar(engine):
    """Añade columnas nuevas y reubica los datos antiguos.

    - clientes / presupuestos / configuracion: sólo reciben columnas
      nuevas → ALTER TABLE ... ADD COLUMN (seguro en SQLite).
    - presupuesto_items: la tabla antigua tenía presupuesto_id NOT NULL y
      una sola columna `descripcion`; se reconstruye con el esquema nuevo y
      cada partida antigua queda envuelta en un «CAPÍTULO GENERAL».
    """
    aditivas = {
        "clientes": [
            ("pais", "VARCHAR(80) DEFAULT 'Venezuela'"),
            ("es_demo", "BOOLEAN DEFAULT 0"),
        ],
        "presupuestos": [
            ("titulo", "VARCHAR(250) DEFAULT ''"),
            ("es_demo", "BOOLEAN DEFAULT 0"),
            ("direccion_obra", "VARCHAR(300) DEFAULT ''"),
            ("codigo_postal", "VARCHAR(20) DEFAULT ''"),
            ("con_portada", "BOOLEAN DEFAULT 0"),
            ("foto_proyecto", "VARCHAR(300) DEFAULT ''"),
            ("mostrar_firmas", "BOOLEAN DEFAULT 0"),
            ("mostrar_resumen_capitulos", "BOOLEAN DEFAULT 0"),
            ("mostrar_garantias", "BOOLEAN DEFAULT 0"),
            ("firma_cliente", "VARCHAR(300) DEFAULT ''"),
            ("usar_funciones_avanzadas", "BOOLEAN DEFAULT 0"),
            ("gastos_indirectos_pct", "FLOAT DEFAULT 0"),
            ("imprevistos_pct", "FLOAT DEFAULT 0"),
            ("transporte_monto", "FLOAT DEFAULT 0"),
            ("otros_cargos_monto", "FLOAT DEFAULT 0"),
            ("estilo_pdf", "VARCHAR(30) DEFAULT 'elegante'"),
            ("mostrar_ahorro", "BOOLEAN DEFAULT 0"),
            ("incluir_anexos", "BOOLEAN DEFAULT 0"),
            ("numero_control", "VARCHAR(80) DEFAULT ''"), ("fecha_tipo_cambio", "DATE"),
            ("retencion_pct", "FLOAT DEFAULT 0"), ("operacion_exenta", "BOOLEAN DEFAULT 0"), ("clausula_cambiaria", "TEXT DEFAULT ''"),
        ],
        "configuracion": [
            ("empresa_legal", "VARCHAR(250) DEFAULT ''"),
            ("empresa_pais", "VARCHAR(80) DEFAULT 'Venezuela'"),
            ("empresa_ciudad", "VARCHAR(120) DEFAULT ''"),
            ("empresa_web", "VARCHAR(200) DEFAULT ''"),
            ("logo", "VARCHAR(300) DEFAULT ''"),
            ("onboarding_completado", "BOOLEAN DEFAULT 0"),
            ("onboarding_modo", "VARCHAR(20) DEFAULT ''"),
            ("onboarding_iniciado_at", "DATETIME"),
            ("onboarding_completado_at", "DATETIME"),
            ("onboarding_catalogo_revisado", "BOOLEAN DEFAULT 0"),
            ("onboarding_pdf_descargado", "BOOLEAN DEFAULT 0"),
            ("primer_pdf_at", "DATETIME"),
            ("condiciones_default", "TEXT DEFAULT ''"),
            ("pdf_color", "VARCHAR(10) DEFAULT '#04265D'"),
            ("logo_ancho_pdf", "FLOAT DEFAULT 360"),
            ("con_portada_default", "BOOLEAN DEFAULT 0"),
            ("mostrar_firmas_default", "BOOLEAN DEFAULT 0"),
            ("mostrar_resumen_capitulos_default", "BOOLEAN DEFAULT 0"),
            ("mostrar_garantias_default", "BOOLEAN DEFAULT 0"),
            ("activar_funciones_avanzadas", "BOOLEAN DEFAULT 0"),
            ("mostrar_costes_internos", "BOOLEAN DEFAULT 0"),
            ("mostrar_alternativas", "BOOLEAN DEFAULT 0"),
            ("mostrar_cargos_adicionales", "BOOLEAN DEFAULT 0"),
            ("activar_funciones_venezuela", "BOOLEAN DEFAULT 0"), ("mostrar_numero_control", "BOOLEAN DEFAULT 0"),
            ("mostrar_tasa_cambio", "BOOLEAN DEFAULT 0"), ("mostrar_total_bs", "BOOLEAN DEFAULT 0"),
            ("mostrar_retenciones", "BOOLEAN DEFAULT 0"), ("mostrar_clausula_cambiaria", "BOOLEAN DEFAULT 0"),
            ("datos_bancarios", "TEXT DEFAULT ''"),
            ("etiqueta_id_fiscal", "VARCHAR(20) DEFAULT 'RIF'"),
            ("tasa_cambio", "FLOAT"),
            ("fecha_tasa", "DATE"),
            ("horas_jornada", "FLOAT DEFAULT 8"),
            ("tarifa_hora_media", "FLOAT DEFAULT 8"),
            ("estimar_tiempo_por_coste", "BOOLEAN DEFAULT 1"),
            ("semilla_catalogo_aplicada", "BOOLEAN DEFAULT 0"),
            ("version_catalogo", "INTEGER DEFAULT 0"),
            ("semilla_productos_aplicada", "BOOLEAN DEFAULT 0"),
            ("semilla_recetas_aplicada", "BOOLEAN DEFAULT 0"),
        ],
        "categorias_partidas": [
            ("parent_id", "INTEGER REFERENCES categorias_partidas(id)"),
            ("codigo_segmento", "VARCHAR(2) DEFAULT ''"),
            ("codigo_completo", "VARCHAR(8)"),
            ("nombre", "VARCHAR(120) DEFAULT ''"),
            ("nivel", "INTEGER DEFAULT 1"),
            ("orden", "INTEGER DEFAULT 0"),
            ("ambito", "VARCHAR(30) DEFAULT 'reforma'"),
            ("activa", "BOOLEAN DEFAULT 1"),
            ("oficial", "BOOLEAN DEFAULT 0"),
        ],
        "partidas": [
            ("usos", "INTEGER DEFAULT 0"),
            ("ultimo_uso", "DATETIME"),
            ("codigo_interno", "VARCHAR(80) DEFAULT ''"),
            ("subcategoria", "VARCHAR(80) DEFAULT ''"),
            ("apartado", "VARCHAR(120) DEFAULT ''"),
            ("categoria_id", "INTEGER REFERENCES categorias_partidas(id)"),
            ("codigo_clasificacion", "VARCHAR(20) DEFAULT ''"),
            ("codigo_legacy", "VARCHAR(80) DEFAULT ''"),
            ("version_catalogo", "INTEGER DEFAULT 0"),
            ("catalogo_uid", "VARCHAR(100)"),
            ("es_oficial", "BOOLEAN DEFAULT 0"),
            ("oculta", "BOOLEAN DEFAULT 0"),
            ("version_alta_catalogo", "INTEGER DEFAULT 0"),
            ("coste_materiales", "FLOAT DEFAULT 0"),
            ("coste_mano_obra", "FLOAT DEFAULT 0"),
            ("coste_complementarios", "FLOAT DEFAULT 0"),
            ("coste_otros", "FLOAT DEFAULT 0"),
            ("tiempo_estimado_horas", "FLOAT"),
            ("tiempo_oficial_horas", "FLOAT"),
            ("tiempo_ayudante_horas", "FLOAT"),
            ("tiempo_equipo_horas", "FLOAT"),
            ("proveedor", "VARCHAR(150) DEFAULT ''"),
            ("rendimiento", "VARCHAR(120) DEFAULT ''"),
            ("desperdicio_recomendado_pct", "FLOAT DEFAULT 0"),
            ("imagen", "VARCHAR(300) DEFAULT ''"),
            ("notas_tecnicas", "TEXT DEFAULT ''"),
            ("codigo_externo", "VARCHAR(100) DEFAULT ''"),
            ("descomposicion_json", "TEXT DEFAULT '[]'"),
            ("fecha_actualizacion_precio", "DATETIME"),
        ],
        "productos": [
            ("precio_compra", "FLOAT"),
            ("fecha_actualizacion_precio", "DATETIME"),
            ("marca", "VARCHAR(120) DEFAULT ''"),
            ("modelo", "VARCHAR(120) DEFAULT ''"),
            ("sku", "VARCHAR(120) DEFAULT ''"),
            ("proveedor", "VARCHAR(150) DEFAULT ''"),
            ("color", "VARCHAR(80) DEFAULT ''"),
            ("acabado", "VARCHAR(120) DEFAULT ''"),
            ("formato", "VARCHAR(120) DEFAULT ''"),
            ("tiempo_entrega_dias", "INTEGER"),
            ("variantes", "TEXT DEFAULT ''"),
            ("ficha_tecnica", "VARCHAR(300) DEFAULT ''"),
            ("imagenes", "TEXT DEFAULT '[]'"),
            ("usos", "INTEGER DEFAULT 0"),
            ("ultimo_uso", "DATETIME"),
        ],
        "facturas": [
            ("presupuesto_version_id", "INTEGER"),
        ],
        "presupuesto_items": [
            ("partida_catalogo_id", "INTEGER REFERENCES partidas(id)"),
            ("tipo_partida", "VARCHAR(20) DEFAULT 'included'"),
            ("seleccionada", "BOOLEAN DEFAULT 0"),
            ("coste_materiales", "FLOAT DEFAULT 0"),
            ("coste_mano_obra", "FLOAT DEFAULT 0"),
            ("coste_complementarios", "FLOAT DEFAULT 0"),
            ("coste_otros", "FLOAT DEFAULT 0"),
            ("desperdicio_pct", "FLOAT DEFAULT 0"),
            ("margen_pct", "FLOAT DEFAULT 0"),
            ("grupo_alternativa", "VARCHAR(120) DEFAULT ''"),
            ("mostrar_en_pdf", "BOOLEAN DEFAULT 1"),
            ("codigo_externo", "VARCHAR(100) DEFAULT ''"),
            ("producto_coste", "FLOAT"),
            ("tiempo_manual_horas", "FLOAT"),
            ("tiempo_manual_oficial_horas", "FLOAT"),
            ("tiempo_manual_ayudante_horas", "FLOAT"),
            ("tiempo_manual_equipo_horas", "FLOAT"),
        ],
        "compras_plan": [
            # Período concedido, copiado de la licencia al activar la compra
            # (E1-061). Permite al comprador descargar su recibo sin leer
            # `licencias`, que el RLS reserva al operador.
            ("licencia_inicio", "DATE"),
            ("licencia_vence", "DATE"),
        ],
        "descomposiciones_partida": [
            ("origen", "VARCHAR(20) DEFAULT 'manual'"),
        ],
        "descomposicion_filas": [
            ("categoria", "VARCHAR(30) DEFAULT ''"),
        ],
    }
    with engine.begin() as conn:
        partidas_existentes = _columnas(engine, "partidas") is not None
        for tabla, cols in aditivas.items():
            existentes = _columnas(engine, tabla)
            if existentes is None:
                continue
            for nombre, definicion in cols:
                if nombre not in existentes:
                    conn.execute(text(f"ALTER TABLE {tabla} ADD COLUMN {nombre} {definicion}"))

        # Cualquier columna del modelo que las listas de arriba no cubran
        # (por olvido al añadir un campo nuevo) se crea automáticamente, para
        # que actualizar la aplicación sobre una base antigua nunca impida
        # abrirla.
        _sincronizar_columnas_modelos(engine, conn)

        # Todo dato local anterior pertenece al espacio transitorio 1. Los
        # índices mantienen rápidas las consultas cuando el catálogo contiene
        # miles de partidas. Las tablas nuevas ya traen ambos desde create_all.
        for tabla in Base.metadata.sorted_tables:
            if "organizacion_id" not in tabla.columns:
                continue
            nombre = tabla.name
            if "organizacion_id" not in (_columnas(engine, nombre) or set()):
                continue
            conn.execute(text(
                f"UPDATE {nombre} SET organizacion_id = 1 "
                "WHERE organizacion_id IS NULL"
            ))
            conn.execute(text(
                f"CREATE INDEX IF NOT EXISTS ix_{nombre}_organizacion_id "
                f"ON {nombre} (organizacion_id)"
            ))

        # Las instalaciones SQLite anteriores reciben también la unicidad del
        # vínculo con Supabase Auth. PostgreSQL obtiene el constraint mediante
        # Alembic; múltiples NULL siguen permitidos hasta vincular cada perfil.
        columnas_usuarios = _columnas(engine, "usuarios") or set()
        if "auth_user_id" in columnas_usuarios:
            conn.execute(text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ux_usuarios_auth_user_id "
                "ON usuarios (auth_user_id)"
            ))

        # Recupera el vínculo con la partida maestra en presupuestos creados
        # antes de existir esta columna. El nombre de Partida es único.
        if partidas_existentes and "partida_catalogo_id" in (_columnas(engine, "presupuesto_items") or set()):
            conn.execute(text(
                "UPDATE presupuesto_items SET partida_catalogo_id = ("
                "  SELECT partidas.id FROM partidas "
                "  WHERE partidas.nombre = presupuesto_items.nombre"
                ") WHERE partida_catalogo_id IS NULL AND EXISTS ("
                "  SELECT 1 FROM partidas WHERE partidas.nombre = presupuesto_items.nombre"
                ")"
            ))

        # Las descomposiciones que ya guardaban archivo de origen provienen de
        # la importación CYPE; el resto (nuevas) se marcan como manuales.
        columnas_descomp = _columnas(engine, "descomposiciones_partida") or set()
        if "origen" in columnas_descomp:
            conn.execute(text(
                "UPDATE descomposiciones_partida SET origen = 'cype' "
                "WHERE origen = 'manual' AND archivo_origen IS NOT NULL AND archivo_origen != ''"
            ))

        # Las filas de versiones anteriores no tienen fecha de precio; la
        # fecha de alta es la mejor referencia disponible y evita mostrar un
        # dato vacío en las sugerencias del constructor.
        for tabla in ("partidas", "productos"):
            columnas = _columnas(engine, tabla) or set()
            if "fecha_actualizacion_precio" in columnas and "created_at" in columnas:
                conn.execute(text(
                    f"UPDATE {tabla} SET fecha_actualizacion_precio = created_at "
                    "WHERE fecha_actualizacion_precio IS NULL"
                ))

        # Tabla independiente: create_all la crea en instalaciones nuevas; esto cubre las existentes.
        conn.execute(text("""CREATE TABLE IF NOT EXISTS presupuesto_versiones (
            id INTEGER PRIMARY KEY, presupuesto_id INTEGER NOT NULL REFERENCES presupuestos(id),
            numero_version INTEGER NOT NULL, fecha DATETIME, motivo VARCHAR(500) DEFAULT '',
            estado VARCHAR(30) DEFAULT 'borrador', total FLOAT DEFAULT 0,
            datos_snapshot TEXT NOT NULL DEFAULT '{}', pdf_snapshot VARCHAR(300) DEFAULT ''
        )"""))

        conn.execute(text("CREATE TABLE IF NOT EXISTS presupuesto_anexos (id INTEGER PRIMARY KEY, presupuesto_id INTEGER NOT NULL REFERENCES presupuestos(id), nombre VARCHAR(250) NOT NULL, archivo VARCHAR(300) NOT NULL, created_at DATETIME)"))

        # Borrador del autoguardado del editor (una fila por presupuesto)
        conn.execute(text("""CREATE TABLE IF NOT EXISTS borradores_presupuesto (
            id INTEGER PRIMARY KEY, presupuesto_id INTEGER NOT NULL UNIQUE REFERENCES presupuestos(id),
            datos TEXT NOT NULL DEFAULT '{}', updated_at DATETIME
        )"""))

        # Descompuestos de precios CYPE. Se conserva la matriz de cada hoja y
        # también cada fila como registro consultable para cálculos de coste.
        conn.execute(text("""CREATE TABLE IF NOT EXISTS descomposiciones_partida (
            id INTEGER PRIMARY KEY, partida_id INTEGER NOT NULL UNIQUE REFERENCES presupuesto_items(id),
            codigo VARCHAR(100) DEFAULT '', unidad VARCHAR(30) DEFAULT '', nombre_hoja VARCHAR(200) DEFAULT '',
            archivo_origen VARCHAR(300) DEFAULT '', nombre_archivo_origen VARCHAR(300) DEFAULT '',
            rango_original VARCHAR(100) DEFAULT '', columnas_json TEXT DEFAULT '[]',
            rangos_combinados_json TEXT DEFAULT '[]', filas_originales_json TEXT DEFAULT '[]',
            coste_directo_unitario FLOAT DEFAULT 0, created_at DATETIME
        )"""))
        conn.execute(text("""CREATE TABLE IF NOT EXISTS descomposicion_filas (
            id INTEGER PRIMARY KEY, descomposicion_id INTEGER NOT NULL REFERENCES descomposiciones_partida(id),
            orden INTEGER DEFAULT 0, numero_fila_excel INTEGER DEFAULT 0, tipo VARCHAR(30) DEFAULT 'otro',
            grupo VARCHAR(250) DEFAULT '', codigo VARCHAR(120) DEFAULT '', unidad VARCHAR(30) DEFAULT '',
            descripcion TEXT DEFAULT '', rendimiento FLOAT, precio_unitario FLOAT, importe FLOAT,
            celdas_json TEXT DEFAULT '[]', formulas_json TEXT DEFAULT '{}'
        )"""))

        # Opciones de producto por partida: un mismo partida puede tener
        # varios productos candidatos entre los que el cliente elige uno
        # (o ninguno). Cada uno con su precio, imagen y selección.
        conn.execute(text("""CREATE TABLE IF NOT EXISTS presupuesto_item_productos (
            id INTEGER PRIMARY KEY,
            partida_id INTEGER NOT NULL REFERENCES presupuesto_items(id),
            nombre VARCHAR(250) DEFAULT '',
            descripcion TEXT DEFAULT '',
            precio FLOAT DEFAULT 0,
            coste FLOAT,
            unidad VARCHAR(20) DEFAULT '',
            categoria VARCHAR(80) DEFAULT '',
            marca VARCHAR(120) DEFAULT '',
            modelo VARCHAR(120) DEFAULT '',
            sku VARCHAR(120) DEFAULT '',
            color VARCHAR(80) DEFAULT '',
            acabado VARCHAR(120) DEFAULT '',
            imagen VARCHAR(300) DEFAULT '',
            seleccionado BOOLEAN DEFAULT 0,
            orden INTEGER DEFAULT 0,
            created_at DATETIME
        )"""))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_partida_productos_opciones_orden ON presupuesto_item_productos (partida_id, orden, id)"))

        # Catálogo central de recursos / precios unitarios
        conn.execute(text("""CREATE TABLE IF NOT EXISTS recursos (
            id INTEGER PRIMARY KEY,
            codigo VARCHAR(80) DEFAULT '',
            descripcion VARCHAR(250) NOT NULL,
            unidad VARCHAR(30) DEFAULT 'ud',
            categoria VARCHAR(30) DEFAULT 'otros',
            grupo VARCHAR(250) DEFAULT '',
            precio FLOAT DEFAULT 0,
            proveedor VARCHAR(150) DEFAULT '',
            usos INTEGER DEFAULT 0,
            ultimo_uso DATETIME,
            fecha_actualizacion_precio DATETIME,
            created_at DATETIME
        )"""))
        # Marcar semillas como aplicadas en BDs ya existentes con datos (evita que borrados reaparezcan)
        try:
            has_cfg = _columnas(engine, "configuracion") is not None
            if has_cfg and "semilla_catalogo_aplicada" in (_columnas(engine, "configuracion") or set()):
                # Si hay partidas o presupuestos ya, la semilla se considera aplicada
                cnt_part = conn.execute(text("SELECT COUNT(*) FROM partidas")).scalar() if _columnas(engine, "partidas") else 0
                cnt_pres = conn.execute(text("SELECT COUNT(*) FROM presupuestos")).scalar() if _columnas(engine, "presupuestos") else 0
                if cnt_part or cnt_pres:
                    conn.execute(text("UPDATE configuracion SET semilla_catalogo_aplicada = 1 WHERE semilla_catalogo_aplicada = 0"))
                    conn.execute(text("UPDATE configuracion SET semilla_productos_aplicada = 1 WHERE semilla_productos_aplicada = 0"))
        except Exception:
            pass

        # Entidades de ejecución de obra y pagos (fase 6) + Recetas de Estancia.
        for sql in (
            "CREATE TABLE IF NOT EXISTS proyectos (id INTEGER PRIMARY KEY, presupuesto_id INTEGER NOT NULL UNIQUE REFERENCES presupuestos(id), presupuesto_version_id INTEGER REFERENCES presupuesto_versiones(id), nombre VARCHAR(250) DEFAULT '', estado VARCHAR(30) DEFAULT 'en_ejecucion', fecha_inicio DATE, fecha_estimada_fin DATE, fecha_fin DATE, notas TEXT DEFAULT '', created_at DATETIME)",
            "CREATE TABLE IF NOT EXISTS cambios_alcance (id INTEGER PRIMARY KEY, proyecto_id INTEGER NOT NULL REFERENCES proyectos(id), numero INTEGER NOT NULL, descripcion TEXT DEFAULT '', estado VARCHAR(20) DEFAULT 'borrador', fecha DATE, diferencia_total FLOAT DEFAULT 0, notas TEXT DEFAULT '')",
            "CREATE TABLE IF NOT EXISTS cambio_alcance_items (id INTEGER PRIMARY KEY, cambio_id INTEGER NOT NULL REFERENCES cambios_alcance(id), tipo VARCHAR(15) DEFAULT 'agregado', nombre VARCHAR(250) DEFAULT '', cantidad FLOAT DEFAULT 0, precio_unitario FLOAT DEFAULT 0)",
            "CREATE TABLE IF NOT EXISTS pagos (id INTEGER PRIMARY KEY, proyecto_id INTEGER REFERENCES proyectos(id), presupuesto_id INTEGER REFERENCES presupuestos(id), factura_id INTEGER REFERENCES facturas(id), fecha DATE, importe FLOAT DEFAULT 0, moneda VARCHAR(10) DEFAULT 'USD', metodo VARCHAR(80) DEFAULT 'transferencia', referencia VARCHAR(150) DEFAULT '', estado VARCHAR(20) DEFAULT 'confirmado', comprobante VARCHAR(300) DEFAULT '', notas TEXT DEFAULT '')",
            "CREATE TABLE IF NOT EXISTS recetas_estancia (id INTEGER PRIMARY KEY, nombre VARCHAR(200) NOT NULL, descripcion VARCHAR(300) DEFAULT '', categoria VARCHAR(80) DEFAULT 'Baños', unidad_base VARCHAR(20) DEFAULT 'm²', cantidad_base_default FLOAT DEFAULT 10.0, datos TEXT DEFAULT '[]', created_at DATETIME)",
        ):
            conn.execute(text(sql))

        # Índices para que los listados y filtros sean instantáneos
        for sql in (
            "CREATE INDEX IF NOT EXISTS ix_presupuestos_client_id ON presupuestos (client_id)",
            "CREATE INDEX IF NOT EXISTS ix_presupuestos_estado ON presupuestos (estado)",
            "CREATE INDEX IF NOT EXISTS ix_versiones_presupuesto ON presupuesto_versiones (presupuesto_id, numero_version)",
            "CREATE INDEX IF NOT EXISTS ix_cambios_proyecto ON cambios_alcance (proyecto_id)",
            "CREATE INDEX IF NOT EXISTS ix_pagos_proyecto ON pagos (proyecto_id)",
            "CREATE INDEX IF NOT EXISTS ix_recetas_categoria ON recetas_estancia (categoria)",
            "CREATE INDEX IF NOT EXISTS ix_presupuestos_fecha ON presupuestos (fecha)",
            "CREATE INDEX IF NOT EXISTS ix_presupuestos_numero ON presupuestos (numero)",
            "CREATE INDEX IF NOT EXISTS ix_facturas_cliente ON facturas (client_id)",
            "CREATE INDEX IF NOT EXISTS ix_items_capitulo ON presupuesto_items (capitulo_id)",
            "CREATE INDEX IF NOT EXISTS ix_partidas_categoria_id ON partidas (categoria_id)",
            "CREATE INDEX IF NOT EXISTS ix_partidas_catalogo_uid ON partidas (catalogo_uid)",
            "CREATE INDEX IF NOT EXISTS ix_partidas_oculta ON partidas (oculta)",
            "CREATE INDEX IF NOT EXISTS ix_categorias_partidas_parent_id ON categorias_partidas (parent_id)",
            "CREATE INDEX IF NOT EXISTS ix_categorias_partidas_codigo ON categorias_partidas (codigo_completo)",
            "CREATE INDEX IF NOT EXISTS ix_descomposiciones_partida ON descomposiciones_partida (partida_id)",
            "CREATE INDEX IF NOT EXISTS ix_descomposicion_filas_orden ON descomposicion_filas (descomposicion_id, orden)",
            "CREATE INDEX IF NOT EXISTS ix_recursos_categoria ON recursos (categoria)",
            "CREATE INDEX IF NOT EXISTS ix_recursos_codigo ON recursos (codigo)",
            "CREATE INDEX IF NOT EXISTS ix_recursos_descripcion ON recursos (descripcion)",
        ):
            try:
                conn.execute(text(sql))
            except Exception:
                pass  # la tabla puede no existir aún en instalaciones muy antiguas

        items = _columnas(engine, "presupuesto_items")
        if items is None:
            return  # instalación nueva: create_all ya generó el esquema final
        if "capitulo_id" in items:
            return  # ya migrada previamente
        if "presupuesto_id" not in items:
            return  # esquema desconocido: no tocar

        # Capítulo general por cada presupuesto que tenga partidas antiguas
        mapa_cap = {}
        for (pid,) in conn.execute(
            text("SELECT DISTINCT presupuesto_id FROM presupuesto_items WHERE presupuesto_id IS NOT NULL")
        ).fetchall():
            cur = conn.execute(
                text("INSERT INTO capitulos (presupuesto_id, nombre, orden) VALUES (:pid, 'CAPÍTULO GENERAL', 0)"),
                {"pid": pid},
            )
            mapa_cap[pid] = cur.lastrowid

        filas = conn.execute(
            text("SELECT id, presupuesto_id, descripcion, cantidad, precio_unitario FROM presupuesto_items")
        ).fetchall()
        conn.execute(text("DROP TABLE presupuesto_items"))
        conn.execute(
            text(
                """
                CREATE TABLE presupuesto_items (
                    id INTEGER PRIMARY KEY,
                    capitulo_id INTEGER REFERENCES capitulos(id),
                    nombre VARCHAR(250) DEFAULT '',
                    descripcion TEXT,
                    unidad VARCHAR(20) DEFAULT 'ud',
                    cantidad FLOAT,
                    precio_unitario FLOAT,
                    orden INTEGER DEFAULT 0,
                    producto_nombre VARCHAR(250) DEFAULT '',
                    producto_precio FLOAT,
                    producto_coste FLOAT,
                    producto_unidad VARCHAR(20) DEFAULT '',
                    producto_imagen VARCHAR(300) DEFAULT '',
                    tipo_partida VARCHAR(20) DEFAULT 'included',
                    seleccionada BOOLEAN DEFAULT 0,
                    coste_materiales FLOAT DEFAULT 0,
                    coste_mano_obra FLOAT DEFAULT 0,
                    coste_complementarios FLOAT DEFAULT 0,
                    coste_otros FLOAT DEFAULT 0,
                    desperdicio_pct FLOAT DEFAULT 0,
                    margen_pct FLOAT DEFAULT 0,
                    grupo_alternativa VARCHAR(120) DEFAULT '',
                    mostrar_en_pdf BOOLEAN DEFAULT 1
                )
                """
            )
        )
        for iid, pid, desc, cant, precio in filas:
            conn.execute(
                text(
                    """
                    INSERT INTO presupuesto_items
                        (id, capitulo_id, nombre, descripcion, unidad, cantidad, precio_unitario, orden,
                         producto_nombre, producto_unidad, producto_imagen)
                    VALUES (:id, :cap, :nombre, :desc, 'ud', :cant, :precio, :orden, '', '', '')
                    """
                ),
                {
                    "id": iid,
                    "cap": mapa_cap.get(pid),
                    "nombre": (desc or "Partida")[:80],
                    "desc": desc or "",
                    "cant": cant or 0,
                    "precio": precio or 0,
                    "orden": iid,
                },
            )

class AnexoPresupuesto(TenantMixin, Base):
    __tablename__ = "presupuesto_anexos"
    id = Column(Integer, primary_key=True)
    presupuesto_id = Column(Integer, ForeignKey("presupuestos.id"), nullable=False)
    nombre = Column(String(250), nullable=False)
    archivo = Column(String(300), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    presupuesto = relationship("Presupuesto", back_populates="anexos")


class BorradorPresupuesto(TenantMixin, Base):
    """Borrador del editor persistido por el autoguardado del servidor.

    Un único borrador por presupuesto (se sobrescribe en cada guardado del
    autosave). No sustituye al presupuesto: solo conserva la estructura en
    curso cuando el navegador cierra sin guardar, y se borra en cuanto el
    usuario hace un guardado completo del formulario.
    """

    __tablename__ = "borradores_presupuesto"

    id = Column(Integer, primary_key=True)
    presupuesto_id = Column(Integer, ForeignKey("presupuestos.id"), nullable=False, unique=True)
    datos = Column(Text, nullable=False, default="{}")   # JSON: {capitulos, ts}
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    presupuesto = relationship("Presupuesto")


class Proyecto(TenantMixin, Base):
    __tablename__ = "proyectos"
    id = Column(Integer, primary_key=True)
    presupuesto_id = Column(Integer, ForeignKey("presupuestos.id"), nullable=False, unique=True)
    presupuesto_version_id = Column(Integer, ForeignKey("presupuesto_versiones.id"), nullable=True)
    nombre = Column(String(250), default="")
    estado = Column(String(30), default="en_ejecucion")
    fecha_inicio = Column(Date, nullable=True)
    fecha_estimada_fin = Column(Date, nullable=True)
    fecha_fin = Column(Date, nullable=True)
    notas = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    presupuesto = relationship("Presupuesto")
    presupuesto_version = relationship("PresupuestoVersion")
    cambios = relationship("CambioAlcance", back_populates="proyecto", cascade="all, delete-orphan", order_by="CambioAlcance.numero")
    pagos = relationship("Pago", back_populates="proyecto", cascade="all, delete-orphan", order_by="Pago.fecha.desc(), Pago.id.desc()")

    @property
    def total_contratado(self):
        return float(self.presupuesto_version.total if self.presupuesto_version else self.presupuesto.total)
    @property
    def total_cambios_aprobados(self):
        return round(sum(c.diferencia_total for c in self.cambios if c.estado in ("aprobado", "aplicado")), 2)
    @property
    def total_actual(self): return round(self.total_contratado + self.total_cambios_aprobados, 2)
    @property
    def total_pagado(self): return round(sum(p.importe for p in self.pagos if p.estado == "confirmado"), 2)
    @property
    def saldo_pendiente(self): return round(self.total_actual - self.total_pagado, 2)

class CambioAlcance(TenantMixin, Base):
    __tablename__ = "cambios_alcance"
    id = Column(Integer, primary_key=True)
    proyecto_id = Column(Integer, ForeignKey("proyectos.id"), nullable=False)
    numero = Column(Integer, nullable=False)
    descripcion = Column(Text, default="")
    estado = Column(String(20), default="borrador")
    fecha = Column(Date, default=date.today)
    diferencia_total = Column(Float, default=0.0)
    notas = Column(Text, default="")
    proyecto = relationship("Proyecto", back_populates="cambios")
    items = relationship("CambioAlcanceItem", back_populates="cambio", cascade="all, delete-orphan", order_by="CambioAlcanceItem.id")

class CambioAlcanceItem(TenantMixin, Base):
    __tablename__ = "cambio_alcance_items"
    id = Column(Integer, primary_key=True)
    cambio_id = Column(Integer, ForeignKey("cambios_alcance.id"), nullable=False)
    tipo = Column(String(15), default="agregado")
    nombre = Column(String(250), default="")
    cantidad = Column(Float, default=0.0)
    precio_unitario = Column(Float, default=0.0)
    cambio = relationship("CambioAlcance", back_populates="items")
    @property
    def importe(self): return round((self.cantidad or 0) * (self.precio_unitario or 0), 2)

class Pago(TenantMixin, Base):
    __tablename__ = "pagos"
    id = Column(Integer, primary_key=True)
    proyecto_id = Column(Integer, ForeignKey("proyectos.id"), nullable=True)
    presupuesto_id = Column(Integer, ForeignKey("presupuestos.id"), nullable=True)
    factura_id = Column(Integer, ForeignKey("facturas.id"), nullable=True)
    fecha = Column(Date, default=date.today)
    importe = Column(Float, default=0.0)
    moneda = Column(String(10), default="USD")
    metodo = Column(String(80), default="transferencia")
    referencia = Column(String(150), default="")
    estado = Column(String(20), default="confirmado")
    comprobante = Column(String(300), default="")
    notas = Column(Text, default="")
    proyecto = relationship("Proyecto", back_populates="pagos")
    presupuesto = relationship("Presupuesto")
    factura = relationship("Factura")


#: Estados del ciclo de vida de una licencia.
ESTADOS_LICENCIA = ("activa", "vencida", "cancelada")

#: Origen de la licencia. Distinguirlos importa para no confundir ingresos
#: reales con cortesías al leer el panel: una prueba y un mes regalado valen
#: 0 y no deben sumar a la facturación.
ORIGENES_LICENCIA = ("pago", "prueba", "cortesia", "compensacion")

ORIGENES_LICENCIA_ETIQUETA = {
    "pago": "Pago",
    "prueba": "Prueba gratuita",
    "cortesia": "Cortesía",
    "compensacion": "Compensación por incidencia",
}


class Licencia(Base):
    """Licencia de uso de CotizaT concedida a una organización cliente.

    **No es una tabla de tenant y no debe serlo.** Las tablas con
    ``TenantMixin`` contienen datos *de* un cliente y se filtran por su
    organización; una licencia es un dato del negocio del titular *sobre* una
    organización: cuánto paga, hasta cuándo y por qué. Si heredara de
    ``TenantMixin`` el filtro automático la haría visible al propio cliente.

    Por eso queda fuera del filtro ORM y, en PostgreSQL, se protege con
    políticas RLS propias que exigen la marca de operador en la sesión (ver la
    revisión ``f4c1d8e37a95``). Una sesión de cliente no obtiene ni una fila.
    """

    __tablename__ = "licencias"
    __table_args__ = (
        CheckConstraint(
            "estado IN ('activa', 'vencida', 'cancelada')",
            name="ck_licencia_estado_valido",
        ),
        CheckConstraint(
            "origen IN ('pago', 'prueba', 'cortesia', 'compensacion')",
            name="ck_licencia_origen_valido",
        ),
        CheckConstraint("importe >= 0", name="ck_licencia_importe_no_negativo"),
        Index("ix_licencias_organizacion_inicio", "organizacion_id", "inicio"),
    )

    id = Column(Integer, primary_key=True)
    organizacion_id = Column(
        Integer,
        ForeignKey("organizaciones.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    estado = Column(String(20), nullable=False, default="activa")
    origen = Column(String(20), nullable=False, default="pago")
    inicio = Column(Date, nullable=False, default=date.today)
    #: Último día con acceso, inclusive.
    vence = Column(Date, nullable=False)
    importe = Column(Float, nullable=False, default=0.0)
    moneda = Column(String(10), nullable=False, default="USD")
    metodo_cobro = Column(String(80), default="")
    referencia = Column(String(150), default="")
    notas = Column(Text, default="")
    #: Auditoría: quién concedió la licencia y desde qué correo. Se guarda el
    #: email además del id porque el operador puede no ser miembro de la
    #: organización y su usuario podría no existir en el futuro.
    creada_por_email = Column(String(254), nullable=False, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organizacion = relationship("Organizacion")

    @property
    def es_ingreso(self) -> bool:
        """Solo las licencias de pago cuentan como facturación."""
        return self.origen == "pago" and self.importe > 0

    def vigente(self, hoy: date | None = None) -> bool:
        """Indica si la licencia da acceso en la fecha indicada."""
        hoy = hoy or date.today()
        return self.estado == "activa" and self.inicio <= hoy <= self.vence

    def dias_restantes(self, hoy: date | None = None) -> int:
        """Días que quedan de acceso (0 si ya venció)."""
        hoy = hoy or date.today()
        return max((self.vence - hoy).days, 0)


class PruebaConcedida(Base):
    """Registro de que una identidad ya consumió su prueba gratuita.

    **No es una tabla de tenant**, igual que ``Licencia``: es un dato del
    negocio del titular *sobre* quién ha usado ya su cortesía inicial, no un
    dato de un cliente. Se protege con RLS de operador.

    Existe como tabla propia, y no como una consulta sobre ``licencias``, por
    dos razones que importan:

    1. **La prueba se ata al correo, no a la organización.** Buscar en
       ``licencias`` diría si *esta empresa* tuvo prueba, no si *esta persona*
       ya gastó la suya creando otra empresa antes. Sin este registro, una
       misma cuenta abre organizaciones en cadena y encadena pruebas.
    2. **El registro sobrevive al borrado.** Si la organización desaparece, la
       marca sigue: la prueba se gastó igual.

    La unicidad va sobre ``email_normalizado`` (ver
    ``app/services/identidad_registro.py``), de modo que los alias con punto y
    con ``+`` del mismo buzón cuentan como una sola identidad. La restricción
    vive en la base de datos y no en código: es la única forma de que dos altas
    simultáneas no consigan dos pruebas.
    """

    __tablename__ = "pruebas_concedidas"
    __table_args__ = (
        UniqueConstraint("email_normalizado", name="uq_prueba_email_normalizado"),
        Index("ix_pruebas_concedidas_creada", "created_at"),
        Index("ix_pruebas_concedidas_ip", "ip_hash"),
    )

    id = Column(Integer, primary_key=True)
    #: Identidad de correo reducida a su forma canónica. Es la clave real.
    email_normalizado = Column(String(254), nullable=False)
    #: Correo tal y como lo escribió la persona, para poder auditar y explicar
    #: una decisión sin tener que deshacer la normalización a mano.
    email_original = Column(String(254), nullable=False, default="")
    #: Organización a la que se concedió. Se conserva aunque se borre (SET NULL):
    #: lo que importa es que la prueba se gastó, no dónde.
    organizacion_id = Column(
        Integer,
        ForeignKey("organizaciones.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    licencia_id = Column(
        Integer,
        ForeignKey("licencias.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    #: SHA-256 de la IP con sal del despliegue, nunca la IP en claro. Sirve
    #: para *ver* patrones en el panel (varias pruebas desde el mismo sitio),
    #: jamás para bloquear: oficinas y redes móviles comparten IP y bloquear
    #: por ella produce falsos positivos sobre clientes reales.
    ip_hash = Column(String(64), nullable=False, default="")
    dias = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    organizacion = relationship("Organizacion")
    licencia = relationship("Licencia")


class CompraPlan(TenantMixin, Base):
    """Compra de un plan registrada por un cliente con su comprobante.

    Es una tabla **tenant**: la compra pertenece a la organización que la
    pagó (el cliente la ve en su confirmación). El operador del producto la
    lee a través de una política RLS propia marcada por ``es_operador``, que
    es la única vía por la que una sesión sin esa organización accede a la
    fila (ver la migración ``<rev_compras>``).

    El comprobante vive en el almacenamiento privado; aquí solo se guarda la
    referencia, el nombre original y el MIME para poder reenviarlo por email
    y mostrarlo en el panel del operador.
    """

    __tablename__ = "compras_plan"
    __table_args__ = (
        CheckConstraint(
            "plan IN ('anual', 'mensual')",
            name="ck_compra_plan_valido",
        ),
        CheckConstraint(
            "metodo_pago IN ('pago_movil', 'binance', 'kontigo', 'usdt')",
            name="ck_compra_metodo_valido",
        ),
        CheckConstraint(
            "estado IN ('pendiente', 'activa', 'rechazada')",
            name="ck_compra_estado_valido",
        ),
        CheckConstraint("importe >= 0", name="ck_compra_importe_no_negativo"),
        Index("ix_compras_plan_estado", "organizacion_id", "estado", "created_at"),
    )

    id = Column(Integer, primary_key=True)
    #: Plan comprado: ``anual`` o ``mensual`` (ver ``app/datos_pago.py``).
    plan = Column(String(20), nullable=False)
    metodo_pago = Column(String(30), nullable=False)
    importe = Column(Float, nullable=False, default=0.0)
    moneda = Column(String(10), nullable=False, default="USD")
    #: Datos de verificación según el método (banco, operación, hash, …),
    #: serializados como JSON. Los devuelve el propio comprador.
    datos_verificacion = Column(Text, nullable=False, default="{}")
    #: Referencia del comprobante en el almacenamiento privado.
    comprobante_reference = Column(String(500), nullable=False, default="")
    comprobante_nombre = Column(String(255), nullable=False, default="")
    comprobante_mime = Column(String(150), nullable=False, default="")
    estado = Column(String(20), nullable=False, default="pendiente")
    creada_por_usuario_id = Column(
        Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    creada_por_email = Column(String(254), nullable=False, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    #: Licencia concedida al activar la compra (si se activó).
    licencia_id = Column(
        Integer, ForeignKey("licencias.id", ondelete="SET NULL"), nullable=True
    )
    #: Período de acceso concedido, copiado de la licencia al activar.
    #:
    #: Es una desnormalización deliberada. ``licencias`` está protegida por
    #: RLS de operador: la sesión del cliente no obtiene ni una fila, así que
    #: sin estas dos fechas el comprador no podría montar su propio recibo
    #: (tendría que pedírselo al titular). Copiarlas aquí —tabla tenant que el
    #: cliente sí lee— le da el comprobante sin abrir ni un resquicio en el
    #: aislamiento. Además congela lo que se compró: si la licencia se cancela
    #: o se reajusta después, el recibo sigue describiendo el cobro real.
    licencia_inicio = Column(Date, nullable=True)
    #: Último día de acceso concedido, inclusive.
    licencia_vence = Column(Date, nullable=True)
    revisado_por_email = Column(String(254), nullable=False, default="")
    revisado_at = Column(DateTime, nullable=True)

    organizacion = relationship("Organizacion")
    licencia = relationship("Licencia")

    @property
    def etiqueta_estado(self) -> str:
        return {
            "pendiente": "Pendiente",
            "activa": "Activada",
            "rechazada": "Rechazada",
        }.get(self.estado, self.estado)

    def datos_verificacion_dict(self) -> dict:
        try:
            datos = json.loads(self.datos_verificacion or "{}")
        except (TypeError, ValueError):
            return {}
        return datos if isinstance(datos, dict) else {}


class EventoAuditoria(Base):
    """Registro inmutable de quién hizo qué (E4-026 / E4-027).

    **No usa TenantMixin a propósito**: ``organizacion_id`` es *nullable*
    porque los eventos de sesión (inicio, cierre, cambio de clave) ocurren
    antes o fuera del contexto de una organización. Consecuencias directas:

    - El filtro automático de tenant no se aplica: toda consulta debe filtrar
      ``organizacion_id`` explícitamente (la vista «Actividad» lo hace; la
      baja también).
    - La asignación automática de tenencia tampoco: el servicio
      ``app.services.auditoria`` fija la organización de forma explícita.

    Inmutabilidad: la aplicación solo inserta y lee. En PostgreSQL el rol
    runtime ni siquiera recibe GRANT de UPDATE/DELETE sobre la tabla (la
    migración lo garantiza); los eventos sin organización entran por la
    función SECURITY DEFINER ``cotizat_security.registrar_evento_global``,
    que valida la acción contra una lista cerrada. El detalle se guarda como
    JSON pequeño y **sin datos sensibles** (nunca contraseñas, tokens ni
    números completos).
    """

    __tablename__ = "eventos_auditoria"
    __table_args__ = (
        Index("ix_eventos_auditoria_org_fecha", "organizacion_id", "created_at"),
    )

    id = Column(Integer, primary_key=True)
    #: Organización a la que pertenece el evento; NULL en eventos de sesión
    #: globales (solo visibles para el operador).
    organizacion_id = Column(
        Integer,
        ForeignKey("organizaciones.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    #: Correo de quien ejecutó la acción (el de la sesión autenticada).
    actor_email = Column(String(254), nullable=False, default="")
    #: Rol de membresía en el momento de la acción ('' si no aplica).
    actor_rol = Column(String(20), nullable=False, default="")
    #: Acción en formato ``dominio.verbo`` (p. ej. ``presupuesto.estado``).
    accion = Column(String(60), nullable=False, index=True)
    #: Tipo de entidad afectada ('' si no aplica), p. ej. ``presupuesto``.
    entidad = Column(String(40), nullable=False, default="")
    #: Identificador de la entidad afectada (si aplica).
    entidad_id = Column(Integer, nullable=True)
    #: Contexto del cambio como JSON pequeño y sin datos sensibles
    #: (p. ej. ``{"de": "borrador", "a": "enviado"}``).
    detalle = Column(Text, nullable=False, default="{}")
    #: Hash de la IP de origen (mismo criterio que ``consentimientos``).
    ip_hash = Column(String(64), nullable=False, default="")
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    organizacion = relationship("Organizacion")

    def detalle_dict(self) -> dict:
        try:
            datos = json.loads(self.detalle or "{}")
        except (TypeError, ValueError):
            return {}
        return datos if isinstance(datos, dict) else {}


class ContextoOrganizacionError(RuntimeError):
    """Una lectura o escritura intentó cruzar el límite de organización."""


def usar_organizacion(db, organizacion_id: int) -> None:
    """Activa el filtro obligatorio para todas las entidades empresariales."""
    organizacion_id = int(organizacion_id)
    if organizacion_id <= 0:
        raise ContextoOrganizacionError("La organización activa no es válida.")
    db.info["organizacion_id"] = organizacion_id


@event.listens_for(OrmSession, "do_orm_execute")
def _filtrar_por_organizacion(estado):
    """Aplica aislamiento y bloquea DML para membresías de solo lectura."""
    organizacion_id = estado.session.info.get("organizacion_id")
    if (
        (estado.is_update or estado.is_delete)
        and estado.session.info.get("rol_membresia") == "lectura"
    ):
        raise PermisoOrganizacionError(
            "Tu rol es de solo lectura y no permite modificar datos."
        )
    if (
        (estado.is_select or estado.is_update or estado.is_delete)
        and organizacion_id is not None
        and not estado.execution_options.get("sin_filtro_organizacion", False)
    ):
        estado.statement = estado.statement.options(
            with_loader_criteria(
                TenantMixin,
                lambda modelo: modelo.organizacion_id == organizacion_id,
                include_aliases=True,
            )
        )


@event.listens_for(OrmSession, "before_flush")
def _proteger_escrituras_por_organizacion(db, _flush_context, _instances):
    """Asigna propietario y aplica tenencia/rol antes de escribir."""
    organizacion_id = db.info.get("organizacion_id")
    if organizacion_id is None:
        return  # migraciones, importador legado y pruebas unitarias sin contexto
    entidades_tenant = {
        entidad
        for entidad in set(db.new).union(db.dirty).union(db.deleted)
        if isinstance(entidad, TenantMixin)
    }
    if entidades_tenant and db.info.get("rol_membresia") == "lectura":
        raise PermisoOrganizacionError(
            "Tu rol es de solo lectura y no permite modificar datos."
        )
    for entidad in db.new:
        if not isinstance(entidad, TenantMixin):
            continue
        if entidad.organizacion_id is None:
            entidad.organizacion_id = organizacion_id
        elif entidad.organizacion_id != organizacion_id:
            raise ContextoOrganizacionError(
                "No se puede crear un registro para otra organización."
            )
    for entidad in set(db.dirty).union(db.deleted):
        if (
            isinstance(entidad, TenantMixin)
            and entidad.organizacion_id != organizacion_id
        ):
            raise ContextoOrganizacionError(
                "No se puede modificar un registro de otra organización."
            )
