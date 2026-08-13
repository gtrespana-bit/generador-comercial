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

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    inspect,
    text,
    Boolean,
)
from sqlalchemy.orm import relationship

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


class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(200), nullable=False)
    rif = Column(String(50), default="")
    pais = Column(String(80), default="Venezuela")
    telefono = Column(String(50), default="")
    email = Column(String(200), default="")
    direccion = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    presupuestos = relationship("Presupuesto", back_populates="cliente")


class Presupuesto(Base):
    __tablename__ = "presupuestos"

    id = Column(Integer, primary_key=True)
    numero = Column(String(20), nullable=False, unique=True)
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
    notas = Column(Text, default="")
    condiciones = Column(Text, default="")
    con_portada = Column(Boolean, default=False)
    foto_proyecto = Column(String(300), default="")
    mostrar_firmas = Column(Boolean, default=False)
    mostrar_resumen_capitulos = Column(Boolean, default=False)
    mostrar_garantias = Column(Boolean, default=False)
    firma_cliente = Column(String(300), default="")   # ruta bajo app/static
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


class PresupuestoVersion(Base):
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



class Capitulo(Base):
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


class PresupuestoItem(Base):
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
    producto_imagen = Column(String(300), default="")   # ruta bajo app/static
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


class DescomposicionPartida(Base):
    """Descompuesto técnico CYPE asociado a una partida de presupuesto.

    ``filas_originales_json`` preserva la matriz completa (incluidas las filas
    vacías intencionales, fórmulas y columnas), mientras que
    :class:`DescomposicionFila` permite calcular y mostrar cada recurso sin
    volver a interpretar el Excel original. El archivo fuente también queda
    guardado bajo uploads para una trazabilidad completamente reversible.
    """

    __tablename__ = "descomposiciones_partida"

    id = Column(Integer, primary_key=True)
    partida_id = Column(Integer, ForeignKey("presupuesto_items.id"), nullable=False, unique=True)
    codigo = Column(String(100), default="")
    unidad = Column(String(30), default="")
    nombre_hoja = Column(String(200), default="")
    archivo_origen = Column(String(300), default="")  # ruta relativa a UPLOADS_DIR
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


class DescomposicionFila(Base):
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


class Medicion(Base):
    """Línea de desglose de una partida (zona/concepto + cantidad)."""

    __tablename__ = "mediciones"

    id = Column(Integer, primary_key=True)
    partida_id = Column(Integer, ForeignKey("presupuesto_items.id"), nullable=False)
    concepto = Column(String(250), default="")
    cantidad = Column(Float, default=0.0)
    orden = Column(Integer, default=0)

    partida = relationship("PresupuestoItem", back_populates="mediciones")


class PresupuestoItemProducto(Base):
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


class Configuracion(Base):
    __tablename__ = "configuracion"

    id = Column(Integer, primary_key=True)
    # Datos de la empresa
    empresa_nombre = Column(String(200), default="Mi Empresa")
    empresa_legal = Column(String(250), default="")       # razón social
    empresa_rif = Column(String(50), default="")
    empresa_direccion = Column(Text, default="")
    empresa_telefono = Column(String(50), default="")
    empresa_email = Column(String(200), default="")
    empresa_web = Column(String(200), default="")
    logo = Column(String(300), default="")                # ruta bajo app/static
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
    # Estimación de tiempos de obra
    horas_jornada = Column(Float, default=8.0)          # horas por jornada laboral
    tarifa_hora_media = Column(Float, default=8.0)      # moneda/h para estimar horas desde el coste
    estimar_tiempo_por_coste = Column(Boolean, default=True)
    # Control de siembra inicial: una vez se crea el catálogo por primera vez
    # no se vuelve a inyectar automáticamente (evita que partidas borradas
    # reaparezcan tras una actualización).
    semilla_catalogo_aplicada = Column(Boolean, default=False)
    semilla_productos_aplicada = Column(Boolean, default=False)
    semilla_recetas_aplicada = Column(Boolean, default=False)


class Plantilla(Base):
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


class RecetaEstancia(Base):
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


class CategoriaPartida(Base):
    """Estructura explícita del catálogo, incluso cuando aún no tiene partidas."""

    __tablename__ = "categorias_partidas"

    id = Column(Integer, primary_key=True)
    categoria = Column(String(80), nullable=False)
    subcategoria = Column(String(80), default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class Partida(Base):
    """Catálogo de partidas reutilizables para remodelaciones de lujo."""

    __tablename__ = "partidas"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(200), nullable=False, unique=True)
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

    @property
    def coste(self) -> float:
        return round(
            (self.coste_materiales or 0.0)
            + (self.coste_mano_obra or 0.0)
            + (self.coste_complementarios or 0.0)
            + (self.coste_otros or 0.0),
            2,
        )


class Producto(Base):
    """Catálogo de productos reutilizables (p. ej. materiales con foto).

    Los productos son independientes de las partidas: una partida («Solado
    de porcelanato») puede tener asociado cualquiera de estos productos
    («Porcelanato 60x60», «Porcelanato 90x90», …). Los productos nuevos que
    se escriben mientras se crea un presupuesto se guardan aquí
    automáticamente para poder reutilizarlos en el futuro.
    """

    __tablename__ = "productos"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(250), nullable=False, unique=True)
    descripcion = Column(Text, default="")
    precio_unitario = Column(Float, default=0.0)
    unidad = Column(String(30), default="ud")
    categoria = Column(String(80), default="General")
    imagen = Column(String(300), default="")           # ruta bajo app/static
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
    ficha_tecnica = Column(String(300), default="")    # PDF bajo uploads/
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


class Recurso(Base):
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


class NotaSeguimiento(Base):
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


class Factura(Base):
    """Factura generada a partir de un presupuesto aprobado.

    Copia la estructura del presupuesto (capítulos y partidas) en el
    momento de la conversión, de modo que las modificaciones posteriores
    del presupuesto no alteran la factura emitida.
    """

    __tablename__ = "facturas"

    id = Column(Integer, primary_key=True)
    numero = Column(String(20), nullable=False, unique=True)
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


class FacturaCapitulo(Base):
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


class FacturaItem(Base):
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
    "empresa_nombre": "RemodelaT Venezuela",
    "empresa_telefono": "04227997043",
    "empresa_email": "contacto@remodelat.net",
    "empresa_web": "www.remodelat.net",
    "empresa_direccion": "San Diego, Carabobo",
}


def asegurar_config(db):
    """Si no existe configuración, crea una con los datos de RemodelaT.

    En instalaciones nuevas la configuración ya viene rellena con los datos
    de la empresa (nombre, teléfono, web, email y dirección). Si la base de
    datos es antigua y todavía conserva el placeholder genérico («Mi
    Empresa»), también se autorellena una única vez; si el usuario ya la
    personalizó, no se toca.
    """
    cfg = db.query(Configuracion).first()
    if cfg is None:
        cfg = Configuracion(**DATOS_EMPRESA_DEFECTO)
        db.add(cfg)
        db.commit()
        return
    if cfg.empresa_nombre in ("", "Mi Empresa") and not cfg.empresa_email:
        for campo, valor in DATOS_EMPRESA_DEFECTO.items():
            setattr(cfg, campo, valor)
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
    """Calcula el siguiente número de factura para el año dado.

    Formato: F-<año>-<secuencial de 3 dígitos>, p. ej. F-2026-001
    """
    numeros = db.query(Factura.numero).filter(Factura.year == year).all()
    max_sec = 0
    for (numero,) in numeros:
        try:
            sec = int(numero.rsplit("-", 1)[-1])
            max_sec = max(max_sec, sec)
        except (ValueError, IndexError):
            continue
    return f"F-{year}-{max_sec + 1:03d}"


def marcar_vencidos(db):
    """Pasa a «vencido» los presupuestos enviados cuya validez ya expiró.

    Se ejecuta al abrir el dashboard o el historial; así el estado se
    mantiene al día sin necesidad de tareas programadas.
    """
    hoy = date.today()
    cambiados = 0
    for p in db.query(Presupuesto).filter(Presupuesto.estado == "enviado").all():
        if p.validez_dias and p.fecha + timedelta(days=p.validez_dias) < hoy:
            p.estado = "vencido"
            cambiados += 1
    if cambiados:
        db.commit()


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
        ],
        "presupuestos": [
            ("titulo", "VARCHAR(250) DEFAULT ''"),
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
            ("empresa_web", "VARCHAR(200) DEFAULT ''"),
            ("logo", "VARCHAR(300) DEFAULT ''"),
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
            ("horas_jornada", "FLOAT DEFAULT 8"),
            ("tarifa_hora_media", "FLOAT DEFAULT 8"),
            ("estimar_tiempo_por_coste", "BOOLEAN DEFAULT 1"),
            ("semilla_catalogo_aplicada", "BOOLEAN DEFAULT 0"),
            ("semilla_productos_aplicada", "BOOLEAN DEFAULT 0"),
            ("semilla_recetas_aplicada", "BOOLEAN DEFAULT 0"),
        ],
        "partidas": [
            ("usos", "INTEGER DEFAULT 0"),
            ("ultimo_uso", "DATETIME"),
            ("codigo_interno", "VARCHAR(80) DEFAULT ''"),
            ("subcategoria", "VARCHAR(80) DEFAULT ''"),
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

class AnexoPresupuesto(Base):
    __tablename__ = "presupuesto_anexos"
    id = Column(Integer, primary_key=True)
    presupuesto_id = Column(Integer, ForeignKey("presupuestos.id"), nullable=False)
    nombre = Column(String(250), nullable=False)
    archivo = Column(String(300), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    presupuesto = relationship("Presupuesto", back_populates="anexos")


class BorradorPresupuesto(Base):
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


class Proyecto(Base):
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

class CambioAlcance(Base):
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

class CambioAlcanceItem(Base):
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

class Pago(Base):
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
