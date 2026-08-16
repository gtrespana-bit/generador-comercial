"""Exportación de datos abierta y portátil por organización (E3-022).

La exportación es el paquete para **llevarse los datos fuera de CotizaT**:
mientras el respaldo (E3-020) está pensado para restaurar dentro del producto
con fidelidad completa, la exportación añade capas legibles por cualquier
herramienta:

- ``cotizat-respaldo.zip`` — el paquete verificable de E3-020 completo
  (restaurable en cualquier CotizaT desde Configuración → Respaldo);
- ``csv/`` — una hoja CSV por tabla (UTF-8 con BOM, abre directo en Excel y
  LibreOffice), con las mismas filas y omisiones del respaldo;
- ``archivos_con_nombre/`` — los archivos con su nombre original (prefijado
  con 12 caracteres de su SHA-256 para evitar colisiones);
- ``manifest_exportacion.json`` — formato, versión, conteos y omisiones;
- ``LEEME_EXPORTACION.txt`` — instrucciones en lenguaje claro.

Honestidad compartida con el respaldo: no viajan cuentas, licencias,
invitaciones, enlaces públicos ni datos de demostración, y la identidad de la
organización se declara pero no se impone al destino.
"""
from __future__ import annotations

import csv
import io
import json
import re
import zipfile
from datetime import datetime

from sqlalchemy.orm import Session

from ..models import Organizacion
from .respaldo import (
    ARCHIVO_CONFIGURACION,
    ARCHIVO_HISTORIAL_ENLACES,
    ARCHIVO_MEMBRESIAS,
    ErrorRespaldo,
    TABLAS_RESPALDO,
    generar_respaldo,
    recopilar_datos,
)

FORMATO_EXPORTACION = "cotizat-export"
VERSION_EXPORTACION = 1
LIMITE_EXPORTACION_BYTES = 350 * 1024 * 1024  # respaldo (300) + CSVs y nombres
NOMBRE_EMBEBIDO = "cotizat-respaldo.zip"


def _nombre_seguro(nombre: str) -> str:
    """Nombre de archivo legible sin caracteres problemáticos ni rutas."""
    valor = str(nombre or "archivo").replace("\\", "/").split("/")[-1]
    valor = re.sub(r"[^A-Za-z0-9._-]+", "-", valor).strip(".-")[:80]
    return valor or "archivo"


def _filas_a_csv(filas: list[dict], columnas: list[str] | None = None) -> bytes:
    """CSV con BOM UTF-8 para que Excel/LibreOffice lo abran directo.

    Las columnas se derivan del modelo cuando la tabla viene vacía, para que
    el CSV conserve su encabezado incluso sin filas.
    """
    if columnas is None:
        columnas = [clave for clave in filas[0].keys() if clave != "_id"] if filas else []
    buffer = io.StringIO()
    escritor = csv.writer(buffer, quoting=csv.QUOTE_MINIMAL, lineterminator="\r\n")
    escritor.writerow(columnas)
    for fila in filas:
        escritor.writerow(["" if fila.get(columna) is None else fila.get(columna) for columna in columnas])
    return ("\ufeff" + buffer.getvalue()).encode("utf-8")


def _columnas_modelo(modelo) -> list[str]:
    """Columnas de la tabla tal como viajan en el respaldo (sin id ni tenant)."""
    from .respaldo import CONFIG_IDENTIDAD, CONFIG_PROCESO

    excluidas = {"id", "organizacion_id"}
    if modelo.__tablename__ == "configuracion":
        excluidas |= set(CONFIG_IDENTIDAD) | set(CONFIG_PROCESO)
    return [
        columna.name
        for columna in modelo.__table__.columns
        if columna.name not in excluidas
    ]


def _leeme_exportacion(manifest: dict[str, object]) -> str:
    omitido = "\n".join(
        f"  · {clave.replace('_', ' ')}: {motivo}"
        for clave, motivo in manifest["omitido"].items()
    )
    return (
        "Exportación de datos de CotizaT\n"
        "================================\n"
        f"Formato: {manifest['formato']} v{manifest['version']}\n"
        f"Creada:  {manifest['creado_en']}\n"
        f"Organización: {manifest['organizacion']['nombre']}\n"
        "\n"
        "Qué contiene:\n"
        "  · cotizat-respaldo.zip → copia verificable completa (para restaurarla\n"
        "    en otro CotizaT: Configuración → Respaldo y restauración web →\n"
        "    Restaurar copia).\n"
        "  · csv/ → una hoja CSV por tabla (abre directo en Excel o\n"
        "    LibreOffice; columnas con encabezados legibles).\n"
        "  · archivos_con_nombre/ → tus archivos (fotos, PDFs, anexos) con su\n"
        "    nombre original; el prefijo de 12 caracteres es parte de su huella\n"
        "    SHA-256 para evitar nombres repetidos.\n"
        "\n"
        "Qué NO incluye (y por qué):\n"
        f"{omitido}\n"
        "\n"
        "Verificación: cada archivo del respaldo embebido viaja bajo su huella\n"
        "SHA-256; la restauración comprueba todas antes de escribir nada.\n"
    )


def generar_exportacion(db: Session) -> bytes:
    """Genera el .zip de exportación de la organización activa."""
    organizacion_id = int(db.info.get("organizacion_id") or 0)
    if organizacion_id <= 0:
        raise ErrorRespaldo("No hay una organización activa para exportar.")
    organizacion = db.get(Organizacion, organizacion_id)
    if organizacion is None:
        raise ErrorRespaldo("La organización activa no existe.")

    paquete_respaldo = generar_respaldo(db)
    with zipfile.ZipFile(io.BytesIO(paquete_respaldo)) as lectura:
        manifest_respaldo = json.loads(lectura.read("manifest.json"))
        archivos = manifest_respaldo.get("archivos", [])
        contenido_archivos = {
            entrada["sha256"]: lectura.read(f"archivos/{entrada['sha256']}")
            for entrada in archivos
        }

    datos = recopilar_datos(db)
    total_csv_bytes = sum(len(_filas_a_csv(filas)) for filas in datos.values())
    total_archivos_bytes = sum(len(contenido) for contenido in contenido_archivos.values())
    total = len(paquete_respaldo) + total_csv_bytes + total_archivos_bytes
    if total > LIMITE_EXPORTACION_BYTES:
        raise ErrorRespaldo(
            "La exportación superaría los 350 MB; reduce los archivos adjuntos "
            "antes de volver a generarla."
        )

    manifest_exportacion = {
        "formato": FORMATO_EXPORTACION,
        "version": VERSION_EXPORTACION,
        "creado_en": datetime.utcnow().isoformat() + "Z",
        "organizacion": manifest_respaldo["organizacion"],
        "conteos": manifest_respaldo["conteos"],
        "omitido": manifest_respaldo["omitido"],
        "avisos": manifest_respaldo["avisos"],
        "archivos": [
            {
                "sha256": entrada["sha256"],
                "nombre_original": entrada["nombre_original"],
                "referencias": entrada["referencias"],
            }
            for entrada in archivos
        ],
        "respaldo_embebido": NOMBRE_EMBEBIDO,
    }

    from ..models import Configuracion

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as paquete:
        paquete.writestr(NOMBRE_EMBEBIDO, paquete_respaldo)
        for especificacion in TABLAS_RESPALDO:
            paquete.writestr(
                f"csv/{especificacion.archivo.replace('.json', '.csv')}",
                _filas_a_csv(
                    datos[especificacion.archivo],
                    _columnas_modelo(especificacion.modelo),
                ),
            )
        paquete.writestr(
            f"csv/{ARCHIVO_MEMBRESIAS.replace('.json', '.csv')}",
            _filas_a_csv(datos[ARCHIVO_MEMBRESIAS], ["email", "rol"]),
        )
        paquete.writestr(
            f"csv/{ARCHIVO_HISTORIAL_ENLACES.replace('.json', '.csv')}",
            _filas_a_csv(datos[ARCHIVO_HISTORIAL_ENLACES], [
                "presupuesto_id", "respuesta", "respondido_por_nombre",
                "respondido_por_email", "respuesta_comentario", "responded_at",
            ]),
        )
        paquete.writestr(
            f"csv/{ARCHIVO_CONFIGURACION.replace('.json', '.csv')}",
            _filas_a_csv(datos[ARCHIVO_CONFIGURACION], _columnas_modelo(Configuracion)),
        )
        for entrada in archivos:
            nombre_legible = (
                f"{entrada['sha256'][:12]}_{_nombre_seguro(entrada['nombre_original'])}"
            )
            paquete.writestr(
                f"archivos_con_nombre/{nombre_legible}",
                contenido_archivos[entrada["sha256"]],
            )
        paquete.writestr(
            "manifest_exportacion.json",
            json.dumps(manifest_exportacion, ensure_ascii=False, indent=2),
        )
        paquete.writestr("LEEME_EXPORTACION.txt", _leeme_exportacion(manifest_exportacion))
    return buffer.getvalue()
