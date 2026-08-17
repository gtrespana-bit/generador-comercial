"""Restauración controlada de una copia de seguridad web (E3-021).

Regla de honestidad, idéntica a la importación de instalaciones locales
(E1W-012): **nunca se escriben datos privados sin acción y confirmación del
propietario**. El flujo HTTP exige dos subidas del MISMO archivo (verificado
por SHA-256) y una casilla de confirmación explícita; este módulo, además:

- verifica el ``manifest.json`` (formato y versión) y la huella SHA-256 de
  cada archivo **antes** de escribir nada;
- restaura por **fusión con reutilización**: lo que ya existe con la misma
  clave natural se reutiliza y lo que falta se crea; nada existente se borra
  ni se sobrescribe, de modo que repetir la restauración es idempotente y
  restaurar tras una pérdida parcial solo repone lo perdido;
- reescribe las referencias de archivos de las filas NUEVAS hacia objetos
  verificados del almacenamiento privado del destino (los objetos con la misma
  huella se reutilizan; nunca se duplican bytes);
- nunca restaura cuentas, licencias, invitaciones ni enlaces (sus razones
  están declaradas en ``app/services/respaldo.py``) y conserva la identidad de
  la organización destino.

La escritura ocurre dentro de la sesión ORM del usuario autenticado, así que
la tenencia (``organizacion_id``), el rol (``lectura`` bloqueado) y RLS se
aplican exactamente igual que en cualquier otra escritura de la aplicación.
El compromiso (``commit``) lo hace el llamante; si falla algo se hace
``rollback`` y los objetos de almacenamiento recién creados se retiran
(best-effort) para no dejar huérfanos.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
import hashlib
import json
from pathlib import Path
from typing import Any
import zipfile

from sqlalchemy.orm import Session

from ..models import (
    ArchivoAlmacenado,
    Configuracion,
    Membresia,
    NotaSeguimiento,
    Partida,
    Presupuesto,
    Usuario,
)
from ..storage import (
    MAX_OBJECT_SIZE,
    get_storage_backend,
    save_object,
    storage_reference,
)
from .respaldo import (
    ARCHIVO_CONFIGURACION,
    ARCHIVO_HISTORIAL_ENLACES,
    ARCHIVO_MEMBRESIAS,
    CONFIG_IDENTIDAD,
    CONFIG_PROCESO,
    FORMATO_RESPALDO,
    LIMITE_ARCHIVO_DATOS_BYTES,
    LIMITE_FILAS_POR_TABLA,
    LIMITE_MANIFESTO_BYTES,
    TABLAS_RESPALDO,
    VERSION_RESPALDO,
    ErrorRespaldo,
)

ROLES_VALIDOS = {"propietario", "administrador", "miembro", "lectura"}
CATEGORIAS_PERMITIDAS = {
    "anexos", "firmas", "fotos-proyecto", "fichas-tecnicas",
    "importaciones", "manifiestos-importacion", "logos", "partidas",
    "productos", "presupuestos",
}


@dataclass
class ResumenRespaldo:
    """Análisis previo a la restauración: nada se ha escrito todavía."""

    organizacion: dict[str, str]
    conteos: dict[str, int]
    archivos: list[dict[str, Any]]
    total_bytes: int
    avisos: list[str]
    omitido: dict[str, str]
    sha256_paquete: str = ""
    reutilizables: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class ResultadoRestauracion:
    """Resultado de una restauración confirmada y verificada."""

    restaurados: dict[str, int] = field(default_factory=dict)
    reutilizados: dict[str, int] = field(default_factory=dict)
    avisos: list[str] = field(default_factory=list)
    archivos_restaurados: int = 0
    archivos_reutilizados: int = 0
    configuracion: str = "sin cambios"
    filas_nuevas: list[tuple[dict[str, Any], Any]] = field(
        default_factory=list, repr=False
    )


class _FilaOmitida(Exception):
    """Control interno: la fila no se puede restaurar y ya quedó anotada."""


def _leer_paquete(ruta: Path):
    """Abre el .zip y valida estructura, formato y versión (sin extraer nada)."""
    try:
        paquete = zipfile.ZipFile(ruta)
    except Exception as exc:
        raise ErrorRespaldo("El archivo no es una copia de seguridad .zip válida.") from exc
    nombres = paquete.namelist()
    for nombre in nombres:
        partes = nombre.replace("\\", "/").split("/")
        if nombre.startswith("/") or ".." in partes:
            raise ErrorRespaldo("La copia contiene rutas no válidas y fue rechazada.")
        if nombre not in {"manifest.json", "LEEME_RESTAURACION.txt"} and not (
            nombre.startswith("datos/") or nombre.startswith("archivos/")
        ):
            raise ErrorRespaldo(
                f"La copia contiene una entrada no esperada ({nombre}) y fue rechazada."
            )
    if "manifest.json" not in nombres:
        raise ErrorRespaldo("La copia no contiene manifest.json y no es restaurable.")
    try:
        crudo = paquete.read("manifest.json")
    except Exception as exc:
        raise ErrorRespaldo("No se pudo leer el manifest.json de la copia.") from exc
    if len(crudo) > LIMITE_MANIFESTO_BYTES:
        raise ErrorRespaldo("El manifest.json de la copia supera el tamaño permitido.")
    try:
        manifest = json.loads(crudo.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise ErrorRespaldo("El manifest.json de la copia no es JSON válido.") from exc
    if not isinstance(manifest, dict):
        raise ErrorRespaldo("El manifest.json de la copia no es válido.")
    if manifest.get("formato") != FORMATO_RESPALDO:
        raise ErrorRespaldo("El archivo no es una copia de seguridad web de CotizaT.")
    if manifest.get("version") != VERSION_RESPALDO:
        raise ErrorRespaldo(
            f"La copia usa una versión no soportada ({manifest.get('version')}); "
            f"se admite la {VERSION_RESPALDO}."
        )
    if not isinstance(manifest.get("archivos"), list):
        raise ErrorRespaldo("El manifest.json no lista los archivos de la copia.")
    return paquete, manifest


def _verificar_integridad(paquete, manifest: dict[str, Any]) -> None:
    """Verifica la huella y el tamaño de cada archivo antes de escribir nada."""
    nombres = paquete.namelist()
    for entrada in manifest.get("archivos", []):
        sha256 = entrada.get("sha256")
        tamano = entrada.get("tamano")
        if not isinstance(sha256, str) or not sha256.isalnum() or len(sha256) != 64:
            raise ErrorRespaldo("La copia declara una huella de archivo no válida.")
        if not isinstance(tamano, int) or tamano <= 0 or tamano > MAX_OBJECT_SIZE:
            raise ErrorRespaldo("La copia declara un tamaño de archivo no válido.")
        nombre = f"archivos/{sha256}"
        if nombre not in nombres:
            raise ErrorRespaldo("La copia está incompleta: falta un archivo declarado.")
        try:
            contenido = paquete.read(nombre)
        except Exception as exc:
            raise ErrorRespaldo("No se pudo leer un archivo de la copia.") from exc
        if len(contenido) != tamano or hashlib.sha256(contenido).hexdigest() != sha256:
            raise ErrorRespaldo(
                "La copia fue alterada: un archivo no coincide con su huella SHA-256."
            )


def _cargar_datos(paquete, manifest: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Carga los datos JSON declarados y comprueba los conteos del manifest."""
    esperados = {
        spec.archivo for spec in TABLAS_RESPALDO
    } | {ARCHIVO_MEMBRESIAS, ARCHIVO_HISTORIAL_ENLACES, ARCHIVO_CONFIGURACION}
    datos: dict[str, list[dict[str, Any]]] = {}
    for nombre in esperados:
        ruta = f"datos/{nombre}"
        if ruta not in paquete.namelist():
            raise ErrorRespaldo(f"La copia está incompleta: falta {ruta}.")
        try:
            crudo = paquete.read(ruta)
        except Exception as exc:
            raise ErrorRespaldo(f"No se pudo leer {ruta} de la copia.") from exc
        if len(crudo) > LIMITE_ARCHIVO_DATOS_BYTES:
            raise ErrorRespaldo(f"La sección {ruta} supera el tamaño permitido.")
        try:
            filas = json.loads(crudo.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as exc:
            raise ErrorRespaldo(f"La sección {ruta} no es JSON válida.") from exc
        if not isinstance(filas, list) or len(filas) > LIMITE_FILAS_POR_TABLA:
            raise ErrorRespaldo(f"La sección {ruta} tiene un formato no válido.")
        if manifest.get("conteos", {}).get(nombre, len(filas)) != len(filas):
            raise ErrorRespaldo(
                "La copia está alterada: los conteos del manifest no coinciden."
            )
        datos[nombre] = filas
    return datos


def _convertir_valor(columna: Any, valor: Any, contexto: str) -> Any:
    """Devuelve el valor JSON convertido al tipo de la columna de destino."""
    if valor is None:
        return None
    try:
        tipo = columna.type.python_type
        if isinstance(valor, tipo) and not isinstance(valor, bool):
            return valor
        if tipo is datetime:
            return datetime.fromisoformat(str(valor))
        if tipo is date:
            return date.fromisoformat(str(valor))
        if tipo is bool:
            return bool(valor)
        if tipo is int:
            return int(valor)
        if tipo is float:
            return float(valor)
        if tipo is str:
            return str(valor)
    except (TypeError, ValueError) as exc:
        raise ErrorRespaldo(
            f"La copia contiene un valor no válido en {contexto}.{columna.name}."
        ) from exc
    return valor


def _buscar_existente(db: Session, especificacion, valores: dict[str, Any]):
    """Fila ya existente con la misma clave natural (para reutilizar, no duplicar)."""
    if all(valores.get(nombre) is None for nombre in especificacion.dedup):
        return None
    consulta = db.query(especificacion.modelo)
    for nombre in especificacion.dedup:
        valor = valores.get(nombre)
        columna = getattr(especificacion.modelo, nombre)
        consulta = consulta.filter(
            columna.is_(None) if valor is None else columna == valor
        )
    return consulta.first()


def _restaurar_tabla(
    db: Session,
    especificacion,
    filas: list[dict[str, Any]],
    mapas: dict[str, dict[int, int]],
    resultado: ResultadoRestauracion,
) -> None:
    columnas = {
        columna.name: columna
        for columna in especificacion.modelo.__table__.columns
        if columna.name not in {"id", "organizacion_id"}
    }
    tabla_nombre = especificacion.modelo.__tablename__
    mapa = mapas.setdefault(tabla_nombre, {})
    if tabla_nombre == "categorias_partidas":
        # La tabla es autorreferente: restaura padres antes que hijos.
        filas = sorted(
            filas,
            key=lambda f: (
                int(f.get("nivel") or 1),
                str(f.get("codigo_completo") or ""),
            ),
        )
    for fila in filas:
        try:
            valores: dict[str, Any] = {}
            for nombre, columna in columnas.items():
                if nombre not in fila:
                    continue
                valores[nombre] = _convertir_valor(
                    columna, fila.get(nombre), especificacion.archivo
                )
            for nombre, columna in columnas.items():
                claves_foraneas = list(columna.foreign_keys)
                if not claves_foraneas or nombre not in valores:
                    continue
                if valores[nombre] is None:
                    continue
                tabla_padre = claves_foraneas[0].column.table.name
                destino = mapas.get(tabla_padre, {}).get(int(valores[nombre]))
                if destino is None:
                    if columna.nullable:
                        valores[nombre] = None
                        continue
                    raise _FilaOmitida
                valores[nombre] = destino

            existente = _buscar_existente(db, especificacion, valores)
            if existente is not None:
                mapa[int(fila["_id"])] = int(existente.id)
                resultado.reutilizados[especificacion.archivo] = (
                    resultado.reutilizados.get(especificacion.archivo, 0) + 1
                )
                continue

            instancia = especificacion.modelo(**valores)
            db.add(instancia)
            db.flush()
            mapa[int(fila["_id"])] = int(instancia.id)
            resultado.restaurados[especificacion.archivo] = (
                resultado.restaurados.get(especificacion.archivo, 0) + 1
            )
            resultado.filas_nuevas.append((fila, instancia))
        except _FilaOmitida:
            resultado.avisos.append(
                f"{especificacion.archivo}: una fila se omitió porque su registro "
                "padre original no existe en la copia."
            )
        except ErrorRespaldo:
            raise
        except Exception as exc:
            raise ErrorRespaldo(
                f"No se pudo restaurar una fila de {especificacion.archivo}: {exc}"
            ) from exc


def _restaurar_membresias(
    db: Session, filas: list[dict[str, Any]], resultado: ResultadoRestauracion
) -> None:
    if not filas:
        return
    organizacion_id = int(db.info.get("organizacion_id") or 0)
    usuarios_por_email = {
        usuario.email.lower(): usuario for usuario in db.query(Usuario).all()
    }
    membresias = (
        db.query(Membresia)
        .filter(Membresia.organizacion_id == organizacion_id)
        .all()
    )
    por_usuario = {membresia.usuario_id: membresia for membresia in membresias}
    hay_propietario = any(
        membresia.rol == "propietario" for membresia in por_usuario.values()
    )
    for fila in filas:
        email = str(fila.get("email") or "").strip().lower()
        rol = fila.get("rol")
        if not email or rol not in ROLES_VALIDOS:
            resultado.avisos.append(
                "membresias.json: se omitió una membresía con datos no válidos."
            )
            continue
        usuario = usuarios_por_email.get(email)
        if usuario is None:
            resultado.avisos.append(
                f"No se restauró el acceso de {email}: no existe una cuenta con "
                "ese correo en la plataforma."
            )
            continue
        existente = por_usuario.get(usuario.id)
        if existente is not None:
            if existente.rol != rol:
                resultado.avisos.append(
                    f"El acceso de {email} ya existe con rol «{existente.rol}» "
                    f"y no se cambió a «{rol}»."
                )
            continue
        if rol == "propietario" and hay_propietario:
            resultado.avisos.append(
                f"No se creó otro propietario ({email}): la organización ya tiene uno."
            )
            continue
        db.add(Membresia(usuario_id=usuario.id, organizacion_id=organizacion_id, rol=rol))
        por_usuario[usuario.id] = True
        if rol == "propietario":
            hay_propietario = True
        resultado.restaurados[ARCHIVO_MEMBRESIAS] = (
            resultado.restaurados.get(ARCHIVO_MEMBRESIAS, 0) + 1
        )


def _texto_historial(fila: dict[str, Any]) -> str:
    respuesta = fila.get("respuesta") or "respondida"
    nombre = (fila.get("respondido_por_nombre") or "").strip()
    email = (fila.get("respondido_por_email") or "").strip()
    comentario = (fila.get("respuesta_comentario") or "").strip()
    quien = nombre or email or "el cliente"
    texto = f"Historial de propuesta (restaurado): {respuesta} por {quien}"
    if email and nombre and email != nombre:
        texto += f" <{email}>"
    fecha = fila.get("responded_at")
    if fecha:
        texto += f" el {fecha}"
    if comentario:
        texto += f". Comentario: {comentario}"
    return texto + "."


def _restaurar_historial_enlaces(
    db: Session,
    filas: list[dict[str, Any]],
    mapas: dict[str, dict[int, int]],
    resultado: ResultadoRestauracion,
) -> None:
    mapa_presupuestos = mapas.get("presupuestos", {})
    for fila in filas:
        destino = mapa_presupuestos.get(int(fila.get("presupuesto_id") or 0))
        if destino is None:
            resultado.avisos.append(
                "enlaces_historial.json: se omitió una respuesta histórica porque "
                "su presupuesto no existe en la copia."
            )
            continue
        texto = _texto_historial(fila)
        existente = (
            db.query(NotaSeguimiento)
            .filter(
                NotaSeguimiento.presupuesto_id == destino,
                NotaSeguimiento.texto == texto,
            )
            .first()
        )
        if existente is not None:
            resultado.reutilizados[ARCHIVO_HISTORIAL_ENLACES] = (
                resultado.reutilizados.get(ARCHIVO_HISTORIAL_ENLACES, 0) + 1
            )
            continue
        fecha = None
        if fila.get("responded_at"):
            try:
                fecha = datetime.fromisoformat(str(fila["responded_at"]))
            except ValueError:
                fecha = None
        db.add(NotaSeguimiento(
            presupuesto_id=destino,
            texto=texto,
            **({"created_at": fecha} if fecha else {}),
        ))
        resultado.restaurados[ARCHIVO_HISTORIAL_ENLACES] = (
            resultado.restaurados.get(ARCHIVO_HISTORIAL_ENLACES, 0) + 1
        )


def _restaurar_configuracion(
    db: Session, filas: list[dict[str, Any]], resultado: ResultadoRestauracion
) -> None:
    if not filas:
        return
    fila = filas[0]
    configuracion = db.query(Configuracion).first()
    if configuracion is None:
        configuracion = Configuracion()
        db.add(configuracion)
        db.flush()
    aplicados = 0
    for nombre, valor in fila.items():
        if nombre == "_id" or nombre in CONFIG_IDENTIDAD or nombre in CONFIG_PROCESO:
            continue
        columna = Configuracion.__table__.columns.get(nombre)
        if columna is None:
            continue
        setattr(configuracion, nombre, _convertir_valor(columna, valor, "configuracion"))
        aplicados += 1
    resultado.configuracion = (
        f"{aplicados} ajustes comerciales aplicados" if aplicados else "sin cambios"
    )


def _restaurar_archivos(
    db: Session,
    paquete,
    manifest: dict[str, Any],
    resultado: ResultadoRestauracion,
) -> None:
    referencias: dict[str, dict[str, Any]] = {}
    por_sha: dict[str, dict[str, Any]] = {}
    for entrada in manifest.get("archivos", []):
        por_sha[entrada["sha256"]] = entrada
        for referencia in entrada.get("referencias", []):
            referencias[referencia] = entrada
    if not referencias:
        return

    resueltas: dict[str, str] = {}
    creadas: list[str] = []

    def resolver(sha256: str) -> str:
        if sha256 in resueltas:
            return resueltas[sha256]
        existente = (
            db.query(ArchivoAlmacenado)
            .filter(ArchivoAlmacenado.sha256 == sha256)
            .first()
        )
        if existente is not None:
            referencia = storage_reference(existente.object_key)
            resueltas[sha256] = referencia
            resultado.archivos_reutilizados += 1
            return referencia
        entrada = por_sha[sha256]
        contenido = paquete.read(f"archivos/{sha256}")
        categoria = entrada.get("categoria")
        if categoria not in CATEGORIAS_PERMITIDAS:
            categoria = "anexos"
        guardado = save_object(
            db,
            contenido,
            categoria,
            entrada.get("nombre_original") or "archivo",
            entrada.get("content_type") or "application/octet-stream",
        )
        creadas.append(guardado.object_key)
        resueltas[sha256] = guardado.reference
        resultado.archivos_restaurados += 1
        return guardado.reference

    try:
        for fila, instancia in resultado.filas_nuevas:
            for nombre, valor in fila.items():
                if nombre == "_id" or not hasattr(instancia, nombre):
                    continue
                entrada = referencias.get(valor) if isinstance(valor, str) else None
                if entrada is not None:
                    setattr(instancia, nombre, resolver(entrada["sha256"]))
    except Exception:
        # Mejor esfuerzo: retirar del almacenamiento lo recién creado para no
        # dejar objetos huérfanos si la transacción se deshace.
        backend = get_storage_backend()
        for clave in creadas:
            try:
                backend.delete(clave)
            except Exception:
                pass
        raise


def analizar_respaldo(db: Session, ruta: Path) -> ResumenRespaldo:
    """Lee y verifica la copia sin escribir nada; devuelve un resumen honesto."""
    paquete, manifest = _leer_paquete(ruta)
    try:
        _verificar_integridad(paquete, manifest)
        _cargar_datos(paquete, manifest)
    finally:
        paquete.close()

    reutilizables: dict[str, list[str]] = {}
    numeros = {n for (n,) in db.query(Presupuesto.numero).all()}
    if numeros:
        conteo = manifest.get("conteos", {}).get("presupuestos.json", 0)
        reutilizables["presupuestos.json"] = [
            f"{conteo} presupuesto(s) de la copia ya existen por número y se "
            "reutilizarán sin duplicarse."
        ]
    nombres_partidas = {n for (n,) in db.query(Partida.nombre).all()}
    if nombres_partidas:
        conteo = manifest.get("conteos", {}).get("partidas.json", 0)
        reutilizables["partidas.json"] = [
            f"{conteo} partida(s) de catálogo de la copia ya existen por nombre "
            "y se reutilizarán."
        ]

    return ResumenRespaldo(
        organizacion=manifest.get("organizacion", {}),
        conteos=manifest.get("conteos", {}),
        archivos=manifest.get("archivos", []),
        total_bytes=int(manifest.get("total_bytes") or 0),
        avisos=list(manifest.get("avisos") or []),
        omitido=manifest.get("omitido", {}),
        reutilizables=reutilizables,
    )


def restaurar_respaldo(db: Session, ruta: Path) -> ResultadoRestauracion:
    """Ejecuta la restauración verificada dentro de la sesión (sin commit)."""
    organizacion_id = int(db.info.get("organizacion_id") or 0)
    if organizacion_id <= 0:
        raise ErrorRespaldo("No hay una organización activa donde restaurar la copia.")
    paquete, manifest = _leer_paquete(ruta)
    try:
        _verificar_integridad(paquete, manifest)
        datos = _cargar_datos(paquete, manifest)
        resultado = ResultadoRestauracion()
        mapas: dict[str, dict[int, int]] = {}
        for especificacion in TABLAS_RESPALDO:
            _restaurar_tabla(
                db, especificacion, datos.get(especificacion.archivo, []), mapas, resultado
            )
        _restaurar_membresias(db, datos.get(ARCHIVO_MEMBRESIAS, []), resultado)
        _restaurar_historial_enlaces(
            db, datos.get(ARCHIVO_HISTORIAL_ENLACES, []), mapas, resultado
        )
        _restaurar_configuracion(db, datos.get(ARCHIVO_CONFIGURACION, []), resultado)
        _restaurar_archivos(db, paquete, manifest, resultado)
        return resultado
    finally:
        paquete.close()
