"""Incorporación de los anexos PDF como páginas del presupuesto.

Antes, marcar «incluir anexos» solo añadía un índice con los nombres de los
archivos adjuntos: el cliente recibía una lista de documentos que no estaban
en ninguna parte. Ahora los anexos se **fusionan** al final del PDF del
presupuesto, de modo que un único archivo contiene el presupuesto y todos sus
documentos de apoyo, y el índice explica exactamente dónde encontrarlos.

Reglas de la fusión
-------------------

* **Tope de tamaño.** El endpoint que sirve el PDF devuelve el binario
  completo en el cuerpo de la respuesta y una función de Vercel no puede
  responder más de 4,5 MB (límite de infraestructura, no configurable). Por
  eso el documento final se mantiene por debajo de :data:`LIMITE_TOTAL_BYTES`:
  los anexos que no caben no se incorporan y el índice lo dice con claridad,
  en lugar de producir un error 413 que el usuario no sabría interpretar.
* **Degradación elegante.** Un anexo que ya no existe en el almacenamiento,
  que está cifrado o que no es un PDF legible nunca rompe la descarga: se
  omite y el índice lo señala como entrega por separado.
* **Sin código ajeno.** De los anexos solo se copian las páginas. Los
  formularios (widgets), las acciones adicionales y las anotaciones con
  JavaScript se descartan para que un archivo subido no pueda inyectar
  comportamiento en el documento comercial ni interferir con el formulario
  del PDF interactivo.
"""
from __future__ import annotations

import io
import logging
from dataclasses import dataclass

from pypdf import PdfReader, PdfWriter
from pypdf.generic import ArrayObject, NameObject

from ..storage import StorageError, read_reference

log = logging.getLogger("cotizat")

# Tamaño objetivo del PDF final. Vercel corta la respuesta en 4,5 MB; se deja
# medio megabyte de margen para las cabeceras y para la diferencia entre el
# tamaño de los anexos y el que ocupan una vez fusionados.
LIMITE_TOTAL_BYTES = 4_000_000
# Tope infranqueable: si tras fusionar se superara, se descarta la fusión
# completa y se entrega el presupuesto solo (nunca una descarga rota).
LIMITE_DURO_BYTES = 4_400_000
# Los objetos fusionados pueden ocupar algo más que el archivo original.
_MARGEN_FUSION = 1.03
# Reserva para el propio índice y las estructuras que añade la fusión.
_RESERVA_BYTES = 24_000

MOTIVO_ILEGIBLE = "ilegible"
MOTIVO_TAMANO = "tamano"

_PAGINA_PROVISIONAL = 99


@dataclass
class Anexo:
    """Un anexo del presupuesto ya resuelto contra el almacenamiento."""

    nombre: str
    datos: bytes = b""
    paginas: int = 0
    motivo: str = ""          # "" cuando el archivo es fusionable
    incorporado: bool = False
    pagina_inicio: int = 0

    @property
    def tamano(self) -> int:
        return len(self.datos)


# ---------------------------------------------------------------------------
# Lectura
# ---------------------------------------------------------------------------

def cargar(presupuesto) -> list[Anexo]:
    """Devuelve los anexos del presupuesto listos para fusionar.

    Lista vacía cuando la opción está desactivada o no hay adjuntos: en ese
    caso el PDF se genera exactamente igual que antes.
    """
    if not getattr(presupuesto, "incluir_anexos", False):
        return []
    adjuntos = getattr(presupuesto, "anexos", None) or []
    return [_leer(adjunto) for adjunto in adjuntos]


def _leer(adjunto) -> Anexo:
    nombre = str(getattr(adjunto, "nombre", "") or "Anexo").strip()[:250] or "Anexo"
    anexo = Anexo(nombre=nombre)
    referencia = str(getattr(adjunto, "archivo", "") or "")
    try:
        datos = read_reference(referencia)
    except (StorageError, OSError, ValueError) as exc:
        log.warning("Anexo '%s' no disponible (%s): %s", nombre, referencia, exc)
        anexo.motivo = MOTIVO_ILEGIBLE
        return anexo
    try:
        lector = PdfReader(io.BytesIO(datos))
        if lector.is_encrypted:
            # Solo se admite el cifrado vacío (PDF «protegido» sin contraseña).
            lector.decrypt("")
        paginas = len(lector.pages)
    except Exception as exc:  # pypdf lanza tipos muy variados ante un PDF roto
        log.warning("Anexo '%s' ilegible: %s", nombre, exc)
        anexo.motivo = MOTIVO_ILEGIBLE
        return anexo
    if paginas <= 0:
        anexo.motivo = MOTIVO_ILEGIBLE
        return anexo
    anexo.datos = datos
    anexo.paginas = paginas
    return anexo


def medir(buf) -> tuple[int, int]:
    """Tamaño en bytes y número de páginas de un PDF ya generado."""
    datos = buf.getvalue()
    try:
        paginas = len(PdfReader(io.BytesIO(datos)).pages)
    except Exception:  # pragma: no cover - nuestro propio PDF siempre es legible
        paginas = 0
    return len(datos), paginas


# ---------------------------------------------------------------------------
# Planificación (qué anexos caben y en qué página empieza cada uno)
# ---------------------------------------------------------------------------

def planificar(anexos: list[Anexo], tam_base: int, paginas_base: int) -> list[Anexo]:
    """Decide qué anexos se incorporan sin superar el tope de tamaño."""
    disponible = LIMITE_TOTAL_BYTES - tam_base - _RESERVA_BYTES
    pagina = paginas_base + 1
    for anexo in anexos:
        if anexo.motivo == MOTIVO_TAMANO:
            anexo.motivo = ""       # se replanifica en cada pasada
        anexo.incorporado = False
        anexo.pagina_inicio = 0
        if anexo.motivo:
            continue
        coste = int(anexo.tamano * _MARGEN_FUSION)
        if coste > disponible:
            anexo.motivo = MOTIVO_TAMANO
            continue
        disponible -= coste
        anexo.incorporado = True
        anexo.pagina_inicio = pagina
        pagina += anexo.paginas
    return anexos


def paginas_incorporadas(anexos: list[Anexo]) -> int:
    """Páginas que la fusión añadirá al final del presupuesto."""
    return sum(a.paginas for a in anexos if a.incorporado)


def descartar_todos(anexos: list[Anexo]) -> list[Anexo]:
    """Marca todos los anexos como entrega separada (fusión imposible)."""
    for anexo in anexos:
        anexo.incorporado = False
        anexo.pagina_inicio = 0
        if not anexo.motivo:
            anexo.motivo = MOTIVO_TAMANO
    return anexos


def plan_provisional(anexos: list[Anexo]) -> list[Anexo]:
    """Plan optimista para la pasada de medición.

    Se usa antes de conocer el tamaño real del presupuesto: mantiene el mismo
    número de líneas y de dígitos que el índice definitivo, para que la
    paginación medida en esa pasada sea la del documento final.
    """
    for anexo in anexos:
        if anexo.motivo and anexo.motivo != MOTIVO_TAMANO:
            continue
        anexo.motivo = ""
        anexo.incorporado = True
        anexo.pagina_inicio = _PAGINA_PROVISIONAL
    return anexos


# ---------------------------------------------------------------------------
# Texto del índice que ve el cliente
# ---------------------------------------------------------------------------

def texto(anexos: list[Anexo]) -> str:
    """Índice de anexos que explica **cómo** se entrega cada documento."""
    if not anexos:
        return ""
    incorporados = [a for a in anexos if a.incorporado]
    aparte = [a for a in anexos if not a.incorporado]

    lineas: list[str] = []
    if incorporados and not aparte:
        lineas.append(
            "Los anexos que se relacionan a continuación forman parte de este "
            "presupuesto y se entregan dentro de este mismo archivo: están "
            "añadidos como páginas adicionales al final del documento, en el "
            "orden indicado y conservando su formato y su numeración originales."
        )
    elif incorporados:
        lineas.append(
            "Los anexos que se relacionan a continuación forman parte de este "
            "presupuesto. Los marcados con la página de inicio están añadidos "
            "al final de este mismo archivo, tras la última página del "
            "presupuesto; el resto se entrega como archivo independiente."
        )
    else:
        lineas.append(
            "Los anexos que se relacionan a continuación forman parte de este "
            "presupuesto y se entregan como archivos independientes, junto a "
            "este documento."
        )
    lineas.append("")
    for numero, anexo in enumerate(anexos, 1):
        lineas.append(f"• Anexo {numero} · {anexo.nombre} — {_detalle(anexo)}")
    return "\n".join(lineas)


def _detalle(anexo: Anexo) -> str:
    if anexo.incorporado:
        plural = "página" if anexo.paginas == 1 else "páginas"
        return (
            f"{anexo.paginas} {plural}, desde la página {anexo.pagina_inicio} "
            "de este archivo."
        )
    if anexo.motivo == MOTIVO_TAMANO:
        return (
            "se entrega como archivo independiente para no superar el tamaño "
            "máximo de este PDF."
        )
    return "se entrega como archivo independiente."


# ---------------------------------------------------------------------------
# Fusión
# ---------------------------------------------------------------------------

def fusionar(buf, anexos: list[Anexo]):
    """Añade las páginas de los anexos incorporados al final del PDF."""
    incorporados = [a for a in anexos if a.incorporado and a.datos]
    if not incorporados:
        buf.seek(0)
        return buf

    buf.seek(0)
    # `clone_from` conserva el catálogo del documento: formulario AcroForm y
    # JavaScript del PDF interactivo, metadatos y marca de agua incluidos.
    escritor = PdfWriter(clone_from=buf)
    for anexo in incorporados:
        lector = PdfReader(io.BytesIO(anexo.datos))
        if lector.is_encrypted:
            lector.decrypt("")
        for pagina in lector.pages:
            _sanear(escritor.add_page(pagina))
    salida = io.BytesIO()
    escritor.write(salida)
    escritor.close()
    salida.seek(0)
    return salida


def _sanear(pagina) -> None:
    """Quita del anexo widgets y anotaciones con código ejecutable."""
    try:
        anotaciones = pagina.get("/Annots")
    except Exception:  # pragma: no cover - página sin diccionario válido
        return
    if not anotaciones:
        return
    seguras = []
    for referencia in anotaciones:
        try:
            objeto = referencia.get_object()
        except Exception:
            continue
        if objeto.get("/Subtype") == "/Widget" or "/AA" in objeto:
            continue
        accion = objeto.get("/A")
        try:
            accion = accion.get_object() if accion is not None else None
        except Exception:
            accion = None
        if accion is not None and accion.get("/S") == "/JavaScript":
            continue
        seguras.append(referencia)
    if len(seguras) == len(anotaciones):
        return
    if seguras:
        pagina[NameObject("/Annots")] = ArrayObject(seguras)
    else:
        try:
            del pagina[NameObject("/Annots")]
        except Exception:  # pragma: no cover
            pass
