"""Copia de seguridad web completa y verificable por organización (E3-020).

El paquete que descarga el propietario es un .zip con formato declarado
(``cotizat-backup`` v1) que viaja con tres garantías:

- **Integridad:** cada archivo binario se guarda bajo su SHA-256 y el
  ``manifest.json`` lista la huella, el tamaño y las referencias originales.
  La restauración verifica todo antes de escribir nada.
- **Completitud honesta:** viajan todas las tablas de negocio de la
  organización (clientes, catálogo, presupuestos con sus capítulos, partidas,
  mediciones, descomposiciones, versiones congeladas, notas, anexos, proyectos,
  cambios, pagos, facturas y configuración comercial) y todos los archivos
  referenciados desde cualquiera de ellas. Lo que NO viaja — y por qué — queda
  declarado en el ``manifest.json`` y en el ``LEEME_RESTAURACION.txt``.
- **Determinismo:** re-descargar la copia produce los mismos hashes y
  restaurarla dos veces no duplica datos (E3-021 reutiliza lo que coincide).

Qué NO viaja (decisión deliberada, no olvido):

- **Cuentas de usuario y contraseñas:** viven en Supabase Auth; el paquete
  solo incluye las membresías como pares (correo, rol) y la restauración las
  aplica únicamente si la cuenta sigue existiendo.
- **Licencias:** las gestiona el operador; restaurar una licencia caducada
  desde una copia podría alterar el acceso de forma incorrecta.
- **Enlaces públicos de propuesta:** el secreto solo existe como SHA-256 y es
  imposible reconstruirlo. Las respuestas históricas (aceptada/rechazada)
  viajan como notas de seguimiento para no perder la trazabilidad.
- **Invitaciones pendientes:** se regeneran desde Configuración → Equipo.
- **Datos de demostración** (``es_demo``): un servidor restaurado no debe
  heredar contenido ficticio como si fuera trabajo real.
- **Identidad de la empresa destino** (nombre, RIF, logo, datos de contacto):
  la restauración aplica los ajustes comerciales (IVA, moneda, validez,
  opciones del PDF) pero nunca pisa la identidad de la organización activa.

Límites: paquete de hasta 300 MB; cada archivo individual conserva el máximo
del almacenamiento privado (12 MB).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import hashlib
import io
import json
import mimetypes
import re
from pathlib import Path
from typing import Any
import zipfile

from sqlalchemy.orm import Session

from ..models import (
    AnexoPresupuesto,
    ArchivoAlmacenado,
    BorradorPresupuesto,
    CambioAlcance,
    CambioAlcanceItem,
    Capitulo,
    CategoriaPartida,
    Cliente,
    Configuracion,
    DescomposicionFila,
    DescomposicionPartida,
    EnlacePropuesta,
    Factura,
    FacturaCapitulo,
    FacturaItem,
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
    Usuario,
)
from ..storage import MAX_OBJECT_SIZE, object_key_from_reference, read_reference

FORMATO_RESPALDO = "cotizat-backup"
VERSION_RESPALDO = 1
LIMITE_RESPALDO_BYTES = 300 * 1024 * 1024
LIMITE_MANIFESTO_BYTES = 1024 * 1024
LIMITE_ARCHIVO_DATOS_BYTES = 10 * 1024 * 1024
LIMITE_FILAS_POR_TABLA = 100_000

# Configuración: la identidad y el estado de proceso del destino se respetan
# siempre; solo se restauran los ajustes comerciales y de apariencia.
CONFIG_IDENTIDAD = frozenset({
    "empresa_nombre", "empresa_legal", "empresa_rif", "empresa_pais",
    "empresa_ciudad", "empresa_direccion", "empresa_telefono",
    "empresa_email", "empresa_web", "logo",
})
CONFIG_PROCESO = frozenset({
    "onboarding_completado", "onboarding_modo", "onboarding_iniciado_at",
    "onboarding_completado_at", "onboarding_catalogo_revisado",
    "onboarding_pdf_descargado", "primer_pdf_at",
    "semilla_catalogo_aplicada", "semilla_productos_aplicada",
    "semilla_recetas_aplicada",
})

_OMITIDO = {
    "usuarios": (
        "las cuentas viven en Supabase Auth y no viajan en la copia; "
        "las membresías se restauran solo para cuentas existentes"
    ),
    "licencias": (
        "las gestiona el operador; restaurarlas desde una copia podría "
        "alterar el acceso de forma incorrecta"
    ),
    "invitaciones_pendientes": "se regeneran desde Configuración → Equipo",
    "enlaces_propuesta": (
        "el secreto solo existe como hash y no se puede reconstruir; las "
        "respuestas históricas viajan como notas de seguimiento"
    ),
    "identidad_configuracion": (
        "nombre, RIF, logo y datos de contacto de la organización destino "
        "se conservan; los ajustes comerciales sí se restauran"
    ),
    "datos_demo": "los registros de demostración no viajan",
}

_REFERENCIA_ARCHIVO_RE = re.compile(
    r"^(storage://[A-Za-z0-9._~/-]+|(static/)?uploads/[^\s]+|importaciones/[^\s]+)$"
)


class ErrorRespaldo(ValueError):
    """La copia no se puede generar, leer o restaurar de forma segura."""


@dataclass(frozen=True)
class TablaRespaldo:
    """Cómo viaja y se deduplica una tabla dentro del paquete."""

    modelo: Any
    archivo: str
    dedup: tuple[str, ...]
    excluir: tuple[str, ...] = ()
    sin_demo: bool = False


# Orden de exportación y restauración: los padres van antes que los hijos.
TABLAS_RESPALDO: tuple[TablaRespaldo, ...] = (
    TablaRespaldo(CategoriaPartida, "categorias_partidas.json", ("categoria", "subcategoria")),
    TablaRespaldo(Partida, "partidas.json", ("nombre",)),
    TablaRespaldo(Producto, "productos.json", ("nombre",)),
    TablaRespaldo(Recurso, "recursos.json", ("codigo", "descripcion")),
    TablaRespaldo(Plantilla, "plantillas.json", ("nombre",)),
    TablaRespaldo(RecetaEstancia, "recetas_estancia.json", ("nombre",)),
    TablaRespaldo(Cliente, "clientes.json", ("nombre", "rif"), sin_demo=True),
    TablaRespaldo(Presupuesto, "presupuestos.json", ("numero",), sin_demo=True),
    TablaRespaldo(Capitulo, "capitulos.json", ("presupuesto_id", "orden", "nombre")),
    TablaRespaldo(
        PresupuestoItem, "presupuesto_items.json",
        ("capitulo_id", "orden", "nombre"),
    ),
    TablaRespaldo(
        DescomposicionPartida, "descomposiciones_partida.json", ("partida_id",),
    ),
    TablaRespaldo(
        DescomposicionFila, "descomposicion_filas.json",
        ("descomposicion_id", "orden", "numero_fila_excel"),
    ),
    TablaRespaldo(Medicion, "mediciones.json", ("partida_id", "orden", "concepto")),
    TablaRespaldo(
        PresupuestoItemProducto, "presupuesto_item_productos.json",
        ("partida_id", "orden", "nombre"),
    ),
    TablaRespaldo(
        NotaSeguimiento, "notas_seguimiento.json",
        ("presupuesto_id", "texto", "created_at"),
    ),
    TablaRespaldo(AnexoPresupuesto, "presupuesto_anexos.json", ("presupuesto_id", "nombre")),
    TablaRespaldo(BorradorPresupuesto, "borradores_presupuesto.json", ("presupuesto_id",)),
    TablaRespaldo(
        PresupuestoVersion, "presupuesto_versiones.json",
        ("presupuesto_id", "numero_version"),
    ),
    TablaRespaldo(Proyecto, "proyectos.json", ("presupuesto_id",)),
    TablaRespaldo(CambioAlcance, "cambios_alcance.json", ("proyecto_id", "numero")),
    TablaRespaldo(
        CambioAlcanceItem, "cambio_alcance_items.json",
        ("cambio_id", "tipo", "nombre", "cantidad", "precio_unitario"),
    ),
    TablaRespaldo(
        Pago, "pagos.json",
        ("proyecto_id", "presupuesto_id", "factura_id", "fecha", "importe",
         "metodo", "referencia"),
    ),
    TablaRespaldo(Factura, "facturas.json", ("numero",)),
    TablaRespaldo(FacturaCapitulo, "factura_capitulos.json", ("factura_id", "orden", "nombre")),
    TablaRespaldo(FacturaItem, "factura_items.json", ("capitulo_id", "orden", "nombre")),
)

ARCHIVO_HISTORIAL_ENLACES = "enlaces_historial.json"
ARCHIVO_MEMBRESIAS = "membresias.json"
ARCHIVO_CONFIGURACION = "configuracion.json"


def _valor_json(valor: Any) -> Any:
    """Convierte un valor de columna a JSON sin perder precisión temporal."""
    if valor is None:
        return None
    if isinstance(valor, (datetime, date)):
        return valor.isoformat()
    if isinstance(valor, (bool, int, float, str)):
        return valor
    return str(valor)


def _serializar_fila(
    modelo: Any, instancia: Any, excluir: tuple[str, ...] = ()
) -> dict[str, Any]:
    """Fila JSON de una instancia, con su id original (``_id``) para rehacer FK."""
    fila: dict[str, Any] = {}
    for columna in modelo.__table__.columns:
        if columna.name in {"id", "organizacion_id", *excluir}:
            continue
        fila[columna.name] = _valor_json(getattr(instancia, columna.name))
    fila["_id"] = int(instancia.id)
    return fila


def _es_referencia_archivo(valor: Any) -> bool:
    return isinstance(valor, str) and bool(_REFERENCIA_ARCHIVO_RE.fullmatch(valor))


def _recolectar_referencias(filas: dict[str, list[dict[str, Any]]]) -> list[str]:
    """Referencias de archivo únicas que aparecen en cualquier valor de texto."""
    referencias: set[str] = set()
    for filas_tabla in filas.values():
        for fila in filas_tabla:
            for clave, valor in fila.items():
                if clave == "_id":
                    continue
                if _es_referencia_archivo(valor):
                    referencias.add(valor)
    return sorted(referencias)


def _informacion_archivo(db: Session, referencia: str) -> tuple[str, str, str]:
    """(categoría, content_type, nombre original) de una referencia conocida."""
    clave = object_key_from_reference(referencia)
    if clave is not None:
        metadata = (
            db.query(ArchivoAlmacenado)
            .filter(ArchivoAlmacenado.object_key == clave)
            .first()
        )
        if metadata is not None:
            return (
                metadata.categoria,
                metadata.content_type,
                metadata.nombre_original,
            )
    nombre = Path(referencia).name or "archivo"
    return (
        "anexos",
        mimetypes.guess_type(nombre)[0] or "application/octet-stream",
        nombre,
    )


def _configuracion_exportable(db: Session) -> dict[str, Any]:
    """Ajustes comerciales de la configuración, sin identidad ni proceso."""
    configuracion = db.query(Configuracion).first()
    if configuracion is None:
        return {}
    fila = _serializar_fila(
        Configuracion, configuracion, tuple(CONFIG_IDENTIDAD | CONFIG_PROCESO)
    )
    fila.pop("_id", None)
    return fila


def _membresias_exportables(db: Session, organizacion_id: int) -> list[dict[str, str]]:
    """Pares (correo, rol) de la organización; las cuentas no viajan."""
    filas: list[dict[str, str]] = []
    for membresia in (
        db.query(Membresia)
        .filter(Membresia.organizacion_id == organizacion_id)
        .order_by(Membresia.id)
        .all()
    ):
        usuario = db.get(Usuario, membresia.usuario_id)
        if usuario is None or not usuario.activo:
            continue
        filas.append({"email": usuario.email, "rol": membresia.rol})
    return filas


def _historial_enlaces(db: Session) -> list[dict[str, Any]]:
    """Respuestas históricas de propuestas, convertidas a trazabilidad segura."""
    filas: list[dict[str, Any]] = []
    for enlace in (
        db.query(EnlacePropuesta)
        .filter(EnlacePropuesta.respuesta != "pendiente")
        .order_by(EnlacePropuesta.id)
        .all()
    ):
        filas.append({
            "presupuesto_id": int(enlace.presupuesto_id),
            "respuesta": enlace.respuesta,
            "respondido_por_nombre": enlace.respondido_por_nombre,
            "respondido_por_email": enlace.respondido_por_email,
            "respuesta_comentario": enlace.respuesta_comentario,
            "responded_at": _valor_json(enlace.responded_at),
        })
    return filas


def _leeme_restauracion(manifest: dict[str, Any]) -> str:
    omitido = "\n".join(f"  · {motivo}" for motivo in manifest["omitido"].values())
    return (
        "Copia de seguridad web de CotizaT\n"
        "=================================\n"
        f"Formato: {manifest['formato']} v{manifest['version']}\n"
        f"Creada:  {manifest['creado_en']}\n"
        f"Organización: {manifest['organizacion']['nombre']}\n"
        "\n"
        "Cómo restaurarla:\n"
        "  Configuración → Respaldo y restauración web → Restaurar copia.\n"
        "  El asistente pide dos veces el MISMO archivo y una confirmación\n"
        "  explícita; nada se escribe en el primer paso.\n"
        "\n"
        "Qué NO viaja en esta copia (y por qué):\n"
        f"{omitido}\n"
        "\n"
        "Verificación: cada archivo se guarda bajo su huella SHA-256 y la\n"
        "restauración comprueba todas las huellas antes de escribir.\n"
    )


def recopilar_datos(db: Session) -> dict[str, list[dict[str, Any]]]:
    """Datos serializables de la organización activa (tablas, membresías,
    historial de propuestas y configuración comercial).

    Es la base compartida por el respaldo (E3-020) y la exportación legible
    (E3-022); ambos garantizan así los mismos contenidos y omisiones.
    """
    organizacion_id = int(db.info.get("organizacion_id") or 0)
    if organizacion_id <= 0:
        raise ErrorRespaldo("No hay una organización activa para generar la copia.")
    filas: dict[str, list[dict[str, Any]]] = {}
    for especificacion in TABLAS_RESPALDO:
        filas_tabla: list[dict[str, Any]] = []
        for instancia in (
            db.query(especificacion.modelo)
            .order_by(especificacion.modelo.id)
            .all()
        ):
            if especificacion.sin_demo and getattr(instancia, "es_demo", False):
                continue
            filas_tabla.append(_serializar_fila(
                especificacion.modelo, instancia, especificacion.excluir
            ))
        filas[especificacion.archivo] = filas_tabla

    filas[ARCHIVO_MEMBRESIAS] = _membresias_exportables(db, organizacion_id)
    filas[ARCHIVO_HISTORIAL_ENLACES] = _historial_enlaces(db)
    filas[ARCHIVO_CONFIGURACION] = [_configuracion_exportable(db)]
    return filas


def generar_respaldo(db: Session) -> bytes:
    """Genera el .zip completo y verificable de la organización activa."""
    organizacion_id = int(db.info.get("organizacion_id") or 0)
    if organizacion_id <= 0:
        raise ErrorRespaldo("No hay una organización activa para generar la copia.")
    organizacion = db.get(Organizacion, organizacion_id)
    if organizacion is None:
        raise ErrorRespaldo("La organización activa no existe.")

    filas = recopilar_datos(db)
    referencias = _recolectar_referencias(filas)
    avisos: list[str] = []
    archivos_por_referencia: dict[str, dict[str, Any]] = {}
    for referencia in referencias:
        try:
            contenido = read_reference(referencia)
        except Exception as exc:  # StorageError y derivados: se declara, no se oculta
            avisos.append(
                f"El archivo referenciado no se pudo leer y NO viaja en la copia: "
                f"{referencia} ({exc}). La referencia se conserva en los datos."
            )
            continue
        if len(contenido) > MAX_OBJECT_SIZE:
            avisos.append(
                f"El archivo {referencia} supera el máximo de 12 MB y no se incluyó."
            )
            continue
        sha256 = hashlib.sha256(contenido).hexdigest()
        categoria, content_type, nombre_original = _informacion_archivo(db, referencia)
        archivos_por_referencia[referencia] = {
            "sha256": sha256,
            "tamano": len(contenido),
            "categoria": categoria,
            "content_type": content_type,
            "nombre_original": nombre_original,
            "contenido": contenido,
            "referencias": [referencia],
        }

    # Varias referencias pueden apuntar al mismo contenido: un único archivo.
    por_sha: dict[str, dict[str, Any]] = {}
    for referencia, informacion in archivos_por_referencia.items():
        destino = por_sha.get(informacion["sha256"])
        if destino is None:
            por_sha[informacion["sha256"]] = informacion
        else:
            destino["referencias"].append(referencia)

    total_bytes = sum(info["tamano"] for info in por_sha.values())
    if total_bytes > LIMITE_RESPALDO_BYTES:
        raise ErrorRespaldo(
            "La copia superaría los 300 MB; reduce los archivos adjuntos "
            "antes de volver a generarla."
        )

    manifest: dict[str, Any] = {
        "formato": FORMATO_RESPALDO,
        "version": VERSION_RESPALDO,
        "creado_en": datetime.utcnow().isoformat() + "Z",
        "organizacion": {"nombre": organizacion.nombre, "slug": organizacion.slug},
        "conteos": {
            **{spec.archivo: len(filas[spec.archivo]) for spec in TABLAS_RESPALDO},
            ARCHIVO_MEMBRESIAS: len(filas[ARCHIVO_MEMBRESIAS]),
            ARCHIVO_HISTORIAL_ENLACES: len(filas[ARCHIVO_HISTORIAL_ENLACES]),
            ARCHIVO_CONFIGURACION: len(filas[ARCHIVO_CONFIGURACION]),
        },
        "omitido": dict(_OMITIDO),
        "avisos": avisos,
        "archivos": sorted(
            (
                {
                    "sha256": info["sha256"],
                    "tamano": info["tamano"],
                    "nombre_original": info["nombre_original"],
                    "content_type": info["content_type"],
                    "categoria": info["categoria"],
                    "referencias": sorted(set(info["referencias"])),
                }
                for info in por_sha.values()
            ),
            key=lambda entrada: entrada["sha256"],
        ),
        "total_bytes": total_bytes,
    }

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as paquete:
        paquete.writestr(
            "manifest.json",
            json.dumps(manifest, ensure_ascii=False, indent=2),
        )
        for especificacion in TABLAS_RESPALDO:
            paquete.writestr(
                f"datos/{especificacion.archivo}",
                json.dumps(filas[especificacion.archivo], ensure_ascii=False),
            )
        paquete.writestr(
            f"datos/{ARCHIVO_MEMBRESIAS}",
            json.dumps(filas[ARCHIVO_MEMBRESIAS], ensure_ascii=False),
        )
        paquete.writestr(
            f"datos/{ARCHIVO_HISTORIAL_ENLACES}",
            json.dumps(filas[ARCHIVO_HISTORIAL_ENLACES], ensure_ascii=False),
        )
        paquete.writestr(
            f"datos/{ARCHIVO_CONFIGURACION}",
            json.dumps(filas[ARCHIVO_CONFIGURACION], ensure_ascii=False),
        )
        for entrada in manifest["archivos"]:
            paquete.writestr(
                f"archivos/{entrada['sha256']}",
                por_sha[entrada["sha256"]]["contenido"],
            )
        paquete.writestr("LEEME_RESTAURACION.txt", _leeme_restauracion(manifest))
    return buffer.getvalue()
