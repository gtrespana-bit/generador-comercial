"""Importación controlada de una instalación SQLite local hacia la web (E1W-012).

Regla de honestidad que gobierna este módulo: **nunca se migran datos privados
a un servidor sin acción y confirmación del propietario**. El flujo tiene dos
pasos separados — analizar y confirmar — y el segundo exige volver a subir el
mismo archivo (verificado por SHA-256) junto con una confirmación explícita.
Así el servidor no guarda el archivo entre pasos, lo que además lo hace
compatible con despliegues serverless donde cada petición puede caer en una
instancia distinta.

Decisiones de diseño:

- **La fuente se lee con ``sqlite3`` crudo, en modo solo lectura**, no con el
  ORM: una instalación antigua puede carecer de tablas o columnas añadidas
  después, y eso no debe impedir la importación. Cada columna ausente toma el
  valor por defecto del modelo actual.
- **El destino se escribe con la sesión ORM del usuario autenticado**, de modo
  que la tenencia (``organizacion_id``), el rol (``lectura`` bloqueado) y RLS
  se aplican exactamente igual que en cualquier otra escritura de la app.
- **Los archivos binarios no viajan**: la base local referencia imágenes y
  PDFs de su disco. Esas referencias se limpian y se informa cuántas eran.
  Los anexos de presupuesto (que son archivos) no se importan.
- **Sin duplicación silenciosa**: presupuestos y documentos de cobro cuyo
  número ya existe en el destino se omiten y se listan ANTES de confirmar;
  partidas, productos, recursos, recetas, plantillas y categorías que ya
  existen se reutilizan. Reimportar el mismo archivo no duplica datos.
- **Los datos de demostración no migran** (``es_demo``): un servidor nuevo no
  debe heredar contenido ficticio como si fuera trabajo real.
- **La configuración de empresa no se importa**: la organización web ya tiene
  su propia identidad (nombre, logo, valores por defecto).
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import sqlite3
import tempfile
import zipfile
from collections import Counter
from datetime import date, datetime
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, Float, Integer

from ..models import (
    CambioAlcance,
    CambioAlcanceItem,
    Capitulo,
    CategoriaPartida,
    Cliente,
    DescomposicionFila,
    DescomposicionPartida,
    Factura,
    FacturaCapitulo,
    FacturaItem,
    Medicion,
    Pago,
    Partida,
    PermisoOrganizacionError,
    Plantilla,
    Presupuesto,
    PresupuestoItem,
    PresupuestoItemProducto,
    PresupuestoVersion,
    Producto,
    Proyecto,
    NotaSeguimiento,
    RecetaEstancia,
    Recurso,
)

LIMITE_BYTES = 50 * 1024 * 1024  # una base sin binarios rara vez supera unos MB
_MAGIA_SQLITE = b"SQLite format 3\x00"
_MAGIA_ZIP = b"PK\x03\x04"


class ErrorInstalacion(ValueError):
    """El archivo subido no es una instalación importable."""


# ---------------------------------------------------------------------------
# Lectura de la fuente
# ---------------------------------------------------------------------------

def _extraer_db(contenido: bytes) -> tuple[bytes, int]:
    """Devuelve (bytes de la base, nº de archivos del zip que no se importan)."""
    if not contenido:
        raise ErrorInstalacion("El archivo está vacío.")
    if len(contenido) > LIMITE_BYTES:
        raise ErrorInstalacion("El archivo supera el límite de 50 MB.")
    if contenido.startswith(_MAGIA_SQLITE):
        return contenido, 0
    if contenido.startswith(_MAGIA_ZIP):
        try:
            with zipfile.ZipFile(io.BytesIO(contenido)) as z:
                miembro_db = None
                otros = 0
                for info in z.infolist():
                    if info.is_dir():
                        continue
                    nombre = info.filename.replace("\\", "/")
                    if nombre == "presupuestos.db" or nombre.endswith("/presupuestos.db"):
                        miembro_db = info
                    elif nombre != "LEEME_BACKUP.txt":
                        otros += 1
                if miembro_db is None:
                    raise ErrorInstalacion(
                        "La copia .zip no contiene el archivo presupuestos.db."
                    )
                if miembro_db.file_size > LIMITE_BYTES:
                    raise ErrorInstalacion("La base dentro del .zip supera 50 MB.")
                datos = z.read(miembro_db)
        except zipfile.BadZipFile as exc:
            raise ErrorInstalacion("El archivo no es un .zip válido.") from exc
        if not datos.startswith(_MAGIA_SQLITE):
            raise ErrorInstalacion("El presupuestos.db del .zip no es una base SQLite.")
        return datos, otros
    raise ErrorInstalacion(
        "El archivo debe ser una base SQLite (.db) o la copia de seguridad .zip de CotizaT."
    )


def _abrir_fuente(db_bytes: bytes):
    """Conexión de solo lectura sobre un archivo temporal propio."""
    tmp = tempfile.NamedTemporaryFile(prefix="cotizat_import_", suffix=".db", delete=False)
    try:
        tmp.write(db_bytes)
        tmp.close()
        con = sqlite3.connect(f"file:{tmp.name}?mode=ro", uri=True)
        con.row_factory = sqlite3.Row
        try:
            con.execute("SELECT count(*) FROM sqlite_master").fetchone()
        except sqlite3.DatabaseError as exc:
            con.close()
            raise ErrorInstalacion("El archivo no es una base de datos SQLite válida.") from exc
        return con, tmp.name
    except ErrorInstalacion:
        os.unlink(tmp.name)
        raise
    except Exception:
        os.unlink(tmp.name)
        raise


def _tablas(con) -> set[str]:
    return {
        fila[0]
        for fila in con.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }


def _columnas(con, tabla: str) -> set[str]:
    return {fila[1] for fila in con.execute(f"PRAGMA table_info({tabla})")}


def _filas(con, tabla: str, espacio: int | None) -> list[dict]:
    """Todas las filas de una tabla, tolerando tablas y columnas ausentes."""
    if tabla not in _tablas(con):
        return []
    columnas = _columnas(con, tabla)
    if "organizacion_id" in columnas and espacio is not None:
        cursor = con.execute(
            f"SELECT * FROM {tabla} WHERE organizacion_id = ?", (espacio,)
        )
    else:
        cursor = con.execute(f"SELECT * FROM {tabla}")
    return [dict(fila) for fila in cursor.fetchall()]


def _espacio_dominante(con) -> tuple[int | None, int]:
    """Espacio local con más datos y cuántos registros quedan en otros.

    Una base anterior a la multiempresa no tiene la columna: se devuelven
    ``(None, 0)`` y se leen todas las filas.
    """
    conteo: Counter = Counter()
    for tabla in ("clientes", "presupuestos", "partidas", "productos"):
        if tabla not in _tablas(con) or "organizacion_id" not in _columnas(con, tabla):
            continue
        for espacio, cantidad in con.execute(
            f"SELECT organizacion_id, COUNT(*) FROM {tabla} GROUP BY organizacion_id"
        ):
            conteo[espacio] += cantidad
    if not conteo:
        return None, 0
    dominante = conteo.most_common(1)[0][0]
    otros = sum(cantidad for espacio, cantidad in conteo.items() if espacio != dominante)
    return dominante, otros


# ---------------------------------------------------------------------------
# Conversión de filas crudas a modelos actuales
# ---------------------------------------------------------------------------

def _convertir(col, valor: Any) -> Any:
    if valor is None:
        return None
    tipo = col.type
    try:
        if isinstance(tipo, Boolean):
            return bool(valor)
        if isinstance(tipo, DateTime):
            if isinstance(valor, datetime):
                return valor
            return datetime.fromisoformat(str(valor))
        if isinstance(tipo, Date):
            if isinstance(valor, date):
                return valor
            return date.fromisoformat(str(valor)[:10])
        if isinstance(tipo, Float):
            return float(valor)
        if isinstance(tipo, Integer):
            return int(valor)
    except (TypeError, ValueError):
        return None
    return valor


def _kwargs_modelo(modelo, fila: dict, excluir: tuple[str, ...] = ()) -> dict:
    """Campos de la fila fuente aplicables al modelo actual.

    Solo viajan columnas que existen en ambos lados; el resto queda con el
    valor por defecto del modelo. ``id``/``organizacion_id`` nunca se copian
    (el destino asigna los suyos) ni las claves foráneas, que se remapean.
    """
    kwargs = {}
    for col in modelo.__table__.columns:
        nombre = col.name
        if nombre in ("id", "organizacion_id") or nombre in excluir:
            continue
        if nombre not in fila:
            continue
        valor = _convertir(col, fila[nombre])
        if valor is None:
            continue
        kwargs[nombre] = valor
    return kwargs


def _limpiar_archivos(kwargs: dict, campos: tuple[str, ...]) -> int:
    """Vacía referencias a archivos locales y devuelve cuántas había."""
    limpiados = 0
    for campo in campos:
        valor = kwargs.get(campo)
        if campo == "imagenes":
            try:
                lista = json.loads(valor or "[]")
            except (TypeError, ValueError):
                lista = []
            limpiados += len(lista) if isinstance(lista, list) else 0
            kwargs["imagenes"] = "[]"
            continue
        if valor:
            limpiados += 1
            kwargs[campo] = ""
    return limpiados


def _es_demo(fila: dict) -> bool:
    return bool(fila.get("es_demo"))


# ---------------------------------------------------------------------------
# Carga de la fuente y resumen previo
# ---------------------------------------------------------------------------

_TABLAS_FUENTE = (
    "clientes",
    "categorias_partidas",
    "recursos",
    "partidas",
    "productos",
    "recetas_estancia",
    "plantillas",
    "presupuestos",
    "capitulos",
    "presupuesto_items",
    "mediciones",
    "presupuesto_item_productos",
    "descomposiciones_partida",
    "descomposicion_filas",
    "notas_seguimiento",
    "presupuesto_versiones",
    "presupuesto_anexos",
    "facturas",
    "factura_capitulos",
    "factura_items",
    "proyectos",
    "cambios_alcance",
    "cambio_alcance_items",
    "pagos",
)


def _cargar_fuente(contenido: bytes) -> dict:
    """Lee la instalación completa a memoria y devuelve fuente + metadatos."""
    db_bytes, archivos_zip = _extraer_db(contenido)
    con, ruta = _abrir_fuente(db_bytes)
    try:
        tablas = _tablas(con)
        if "clientes" not in tablas or "presupuestos" not in tablas:
            raise ErrorInstalacion(
                "La base no parece una instalación de CotizaT: faltan sus tablas principales."
            )
        espacio, fuera_de_espacio = _espacio_dominante(con)
        datos = {tabla: _filas(con, tabla, espacio) for tabla in _TABLAS_FUENTE}
        empresa = ""
        for fila in _filas(con, "configuracion", espacio):
            nombre = str(fila.get("empresa_nombre") or "").strip()
            if nombre and nombre.lower() != "mi empresa":
                empresa = nombre
                break
    finally:
        con.close()
        os.unlink(ruta)
    return {
        "datos": datos,
        "empresa": empresa,
        "espacio": espacio,
        "fuera_de_espacio": fuera_de_espacio,
        "archivos_zip": archivos_zip,
        "sha256": hashlib.sha256(contenido).hexdigest(),
    }


_CAMPOS_ARCHIVO_POR_TABLA = {
    "presupuestos": ("foto_proyecto", "firma_cliente"),
    "presupuesto_items": ("producto_imagen",),
    "presupuesto_item_productos": ("imagen",),
    "partidas": ("imagen",),
    "productos": ("imagen", "ficha_tecnica", "imagenes"),
    "presupuesto_versiones": ("pdf_snapshot",),
    "descomposiciones_partida": ("archivo_origen",),
    "pagos": ("comprobante",),
}


def _contar_referencias_archivos(datos: dict) -> int:
    total = 0
    for tabla, campos in _CAMPOS_ARCHIVO_POR_TABLA.items():
        for fila in datos.get(tabla, []):
            for campo in campos:
                valor = fila.get(campo)
                if campo == "imagenes":
                    try:
                        lista = json.loads(valor or "[]")
                    except (TypeError, ValueError):
                        lista = []
                    total += len(lista) if isinstance(lista, list) else 0
                elif valor:
                    total += 1
    return total


def analizar_instalacion(db, contenido: bytes) -> dict:
    """Resumen previo a la confirmación: qué entrará, qué no y por qué."""
    _exigir_permiso(db)
    fuente = _cargar_fuente(contenido)
    datos = fuente["datos"]

    numeros_presupuestos = {n for (n,) in db.query(Presupuesto.numero).all()}
    numeros_facturas = {n for (n,) in db.query(Factura.numero).all()}
    partidas_existentes = {n for (n,) in db.query(Partida.nombre).all()}
    productos_existentes = {n for (n,) in db.query(Producto.nombre).all()} if datos["productos"] else set()

    presupuestos_reales = [f for f in datos["presupuestos"] if not _es_demo(f)]
    clientes_reales = [f for f in datos["clientes"] if not _es_demo(f)]
    conflictos_presupuestos = sorted(
        str(f.get("numero", "")) for f in presupuestos_reales
        if str(f.get("numero", "")) in numeros_presupuestos
    )
    conflictos_facturas = sorted(
        str(f.get("numero", "")) for f in datos["facturas"]
        if str(f.get("numero", "")) in numeros_facturas
    )

    advertencias: list[str] = []
    if fuente["archivos_zip"]:
        advertencias.append(
            f"La copia incluye {fuente['archivos_zip']} archivo(s) (imágenes, anexos…) "
            "que no se importan: la web guarda los archivos en su propio almacenamiento."
        )
    referencias = _contar_referencias_archivos(datos)
    if referencias:
        advertencias.append(
            f"{referencias} referencia(s) a archivos locales (imágenes, PDFs) se "
            "omitirán: vuelve a subir esos archivos desde la web cuando los necesites."
        )
    anexos = len(datos["presupuesto_anexos"])
    if anexos:
        advertencias.append(f"{anexos} anexo(s) de presupuesto no se importan (son archivos locales).")
    if fuente["fuera_de_espacio"]:
        advertencias.append(
            f"La base contiene {fuente['fuera_de_espacio']} registro(s) de otros espacios "
            "de trabajo locales; solo se importa el espacio con más datos."
        )
    demo_clientes = len(datos["clientes"]) - len(clientes_reales)
    demo_presupuestos = len(datos["presupuestos"]) - len(presupuestos_reales)
    if demo_clientes or demo_presupuestos:
        advertencias.append(
            "Los datos de demostración no se importan "
            f"({demo_clientes} cliente(s) y {demo_presupuestos} presupuesto(s) demo)."
        )
    if conflictos_presupuestos:
        advertencias.append(
            "Estos presupuestos NO se importarán porque su número ya existe aquí: "
            + ", ".join(conflictos_presupuestos) + "."
        )
    if conflictos_facturas:
        advertencias.append(
            "Estos documentos de cobro NO se importarán porque su número ya existe aquí: "
            + ", ".join(conflictos_facturas) + "."
        )
    duplicadas = sum(
        1 for f in datos["partidas"] if str(f.get("nombre", "")).strip() in partidas_existentes
    )
    if duplicadas:
        advertencias.append(
            f"{duplicadas} partida(s) del catálogo ya existen con el mismo nombre y no se duplicarán."
        )
    advertencias.append(
        "La configuración de empresa (nombre, logo, valores por defecto) no se "
        "importa: la organización web conserva la suya."
    )

    return {
        "sha256": fuente["sha256"],
        "empresa": fuente["empresa"],
        "conteos": {
            "clientes": len(clientes_reales),
            "partidas_catalogo": len(datos["partidas"]),
            "productos": len(datos["productos"]),
            "recursos": len(datos["recursos"]),
            "recetas": len(datos["recetas_estancia"]),
            "plantillas": len(datos["plantillas"]),
            "presupuestos": len(presupuestos_reales) - len(conflictos_presupuestos),
            "documentos_cobro": len(datos["facturas"]) - len(conflictos_facturas),
            "proyectos": len(datos["proyectos"]),
        },
        "conflictos": {
            "presupuestos": conflictos_presupuestos,
            "facturas": conflictos_facturas,
            "partidas_existentes": duplicadas,
            "productos_existentes": sum(
                1 for f in datos["productos"]
                if str(f.get("nombre", "")).strip() in productos_existentes
            ),
        },
        "advertencias": advertencias,
    }


# ---------------------------------------------------------------------------
# Importación real
# ---------------------------------------------------------------------------

def _exigir_permiso(db) -> None:
    rol = db.info.get("rol_membresia")
    if rol == "lectura":
        raise PermisoOrganizacionError(
            "Tu rol es de solo lectura y no permite importar datos."
        )
    if rol is not None and rol not in {"propietario", "administrador"}:
        raise PermisoOrganizacionError(
            "Solo el propietario o un administrador pueden importar una instalación."
        )


def importar_instalacion(db, contenido: bytes, sha256_esperado: str = "") -> dict:
    """Importa la instalación al espacio de la organización activa.

    ``sha256_esperado`` — obligatorio cuando viene del flujo web de dos pasos:
    garantiza que el archivo confirmado es exactamente el analizado.
    El llamador hace ``commit``; aquí solo se hace ``flush``.
    """
    _exigir_permiso(db)
    fuente = _cargar_fuente(contenido)
    if sha256_esperado and fuente["sha256"] != sha256_esperado.strip().lower():
        raise ErrorInstalacion(
            "El archivo confirmado no coincide con el analizado. "
            "Vuelve a analizarlo para revisar el resumen actualizado."
        )
    datos = fuente["datos"]
    advertencias: list[str] = []
    archivos_omitidos = 0
    importados: Counter = Counter()
    omitidos: Counter = Counter()

    # --- Catálogos reutilizables -------------------------------------------
    categorias_existentes = {
        (
            c.codigo_completo or "",
            c.categoria,
            c.subcategoria or "",
            c.nombre or "",
        ): c
        for c in db.query(CategoriaPartida).all()
    }
    mapa_categorias: dict[int, int] = {}
    # Padres antes que hijos para poder reconstruir la FK autorreferente.
    filas_categorias = sorted(
        datos["categorias_partidas"],
        key=lambda f: (int(f.get("nivel") or 1), str(f.get("codigo_completo") or "")),
    )
    for fila in filas_categorias:
        clave = (
            str(fila.get("codigo_completo") or "").strip(),
            str(fila.get("categoria", "")).strip(),
            str(fila.get("subcategoria") or "").strip(),
            str(fila.get("nombre") or "").strip(),
        )
        if not clave[1]:
            omitidos["categorias"] += 1
            continue
        existente = categorias_existentes.get(clave)
        if existente is not None:
            mapa_categorias[int(fila.get("id") or 0)] = existente.id
            omitidos["categorias"] += 1
            continue
        kwargs = _kwargs_modelo(CategoriaPartida, fila, ("parent_id",))
        parent_origen = int(fila.get("parent_id") or 0)
        if parent_origen:
            kwargs["parent_id"] = mapa_categorias.get(parent_origen)
        nodo = CategoriaPartida(**kwargs)
        db.add(nodo)
        db.flush()
        mapa_categorias[int(fila.get("id") or 0)] = nodo.id
        categorias_existentes[clave] = nodo
        importados["categorias"] += 1

    claves_recursos = {r.clave for r in db.query(Recurso).all()}
    for fila in datos["recursos"]:
        recurso = Recurso(**_kwargs_modelo(Recurso, fila))
        if not (recurso.descripcion or "").strip() or recurso.clave in claves_recursos:
            omitidos["recursos"] += 1
            continue
        db.add(recurso)
        claves_recursos.add(recurso.clave)
        importados["recursos"] += 1

    partidas_por_nombre = {p.nombre: p for p in db.query(Partida).all()}
    mapa_partidas: dict[int, int] = {}
    partidas_nuevas: list[tuple[int, Partida]] = []
    for fila in datos["partidas"]:
        nombre = str(fila.get("nombre", "")).strip()
        if not nombre:
            omitidos["partidas_catalogo"] += 1
            continue
        existente = partidas_por_nombre.get(nombre)
        if existente is not None:
            mapa_partidas[fila["id"]] = existente.id
            omitidos["partidas_catalogo"] += 1
            continue
        kwargs = _kwargs_modelo(Partida, fila, ("categoria_id",))
        categoria_origen = int(fila.get("categoria_id") or 0)
        if categoria_origen:
            kwargs["categoria_id"] = mapa_categorias.get(categoria_origen)
        archivos_omitidos += _limpiar_archivos(kwargs, ("imagen",))
        partida = Partida(**kwargs)
        db.add(partida)
        partidas_por_nombre[nombre] = partida
        partidas_nuevas.append((fila["id"], partida))
        importados["partidas_catalogo"] += 1
    db.flush()
    for fila_id, partida in partidas_nuevas:
        mapa_partidas[fila_id] = partida.id

    productos_existentes = {p.nombre for p in db.query(Producto).all()}
    for fila in datos["productos"]:
        nombre = str(fila.get("nombre", "")).strip()
        if not nombre or nombre in productos_existentes:
            omitidos["productos"] += 1
            continue
        kwargs = _kwargs_modelo(Producto, fila)
        archivos_omitidos += _limpiar_archivos(kwargs, ("imagen", "ficha_tecnica", "imagenes"))
        db.add(Producto(**kwargs))
        productos_existentes.add(nombre)
        importados["productos"] += 1

    recetas_existentes = {r.nombre for r in db.query(RecetaEstancia).all()}
    for fila in datos["recetas_estancia"]:
        nombre = str(fila.get("nombre", "")).strip()
        if not nombre or nombre in recetas_existentes:
            omitidos["recetas"] += 1
            continue
        db.add(RecetaEstancia(**_kwargs_modelo(RecetaEstancia, fila)))
        recetas_existentes.add(nombre)
        importados["recetas"] += 1

    plantillas_existentes = {p.nombre for p in db.query(Plantilla).all()}
    for fila in datos["plantillas"]:
        nombre = str(fila.get("nombre", "")).strip()
        if not nombre or nombre in plantillas_existentes:
            omitidos["plantillas"] += 1
            continue
        db.add(Plantilla(**_kwargs_modelo(Plantilla, fila)))
        plantillas_existentes.add(nombre)
        importados["plantillas"] += 1

    # --- Clientes ------------------------------------------------------------
    clientes_fuente = {fila["id"]: fila for fila in datos["clientes"]}
    clientes_por_nombre = {c.nombre: c for c in db.query(Cliente).all()}
    mapa_clientes: dict[int, Cliente] = {}

    def _cliente_destino(cliente_id) -> Cliente | None:
        """Cliente ya mapeado, reutilizado por nombre o creado bajo demanda."""
        if cliente_id in mapa_clientes:
            return mapa_clientes[cliente_id]
        fila = clientes_fuente.get(cliente_id)
        if fila is None:
            return None
        nombre = str(fila.get("nombre", "")).strip()
        if not nombre:
            return None
        existente = clientes_por_nombre.get(nombre)
        if existente is not None:
            mapa_clientes[cliente_id] = existente
            omitidos["clientes"] += 1
            return existente
        cliente = Cliente(**_kwargs_modelo(Cliente, fila))
        db.add(cliente)
        clientes_por_nombre[nombre] = cliente
        mapa_clientes[cliente_id] = cliente
        importados["clientes"] += 1
        return cliente

    for fila in datos["clientes"]:
        if not _es_demo(fila):
            _cliente_destino(fila["id"])
    db.flush()

    # --- Presupuestos y todo su grafo ---------------------------------------
    numeros_existentes = {n for (n,) in db.query(Presupuesto.numero).all()}
    mapa_presupuestos: dict[int, Presupuesto] = {}
    for fila in datos["presupuestos"]:
        numero = str(fila.get("numero", ""))
        if _es_demo(fila):
            omitidos["presupuestos_demo"] += 1
            continue
        if numero in numeros_existentes:
            omitidos["presupuestos_conflicto"] += 1
            advertencias.append(f"No se importó el presupuesto {numero}: ese número ya existe.")
            continue
        cliente = _cliente_destino(fila.get("client_id"))
        if cliente is None:
            omitidos["presupuestos_sin_cliente"] += 1
            advertencias.append(f"No se importó el presupuesto {numero}: su cliente no está en la copia.")
            continue
        kwargs = _kwargs_modelo(Presupuesto, fila, excluir=("client_id",))
        archivos_omitidos += _limpiar_archivos(kwargs, ("foto_proyecto", "firma_cliente"))
        presupuesto = Presupuesto(cliente=cliente, **kwargs)
        db.add(presupuesto)
        mapa_presupuestos[fila["id"]] = presupuesto
        numeros_existentes.add(numero)
        importados["presupuestos"] += 1
    db.flush()

    mapa_capitulos: dict[int, Capitulo] = {}
    for fila in datos["capitulos"]:
        presupuesto = mapa_presupuestos.get(fila.get("presupuesto_id"))
        if presupuesto is None:
            continue
        capitulo = Capitulo(
            presupuesto_id=presupuesto.id,
            **_kwargs_modelo(Capitulo, fila, excluir=("presupuesto_id",)),
        )
        db.add(capitulo)
        mapa_capitulos[fila["id"]] = capitulo
    db.flush()

    mapa_items: dict[int, PresupuestoItem] = {}
    for fila in datos["presupuesto_items"]:
        capitulo = mapa_capitulos.get(fila.get("capitulo_id"))
        if capitulo is None:
            continue
        kwargs = _kwargs_modelo(
            PresupuestoItem, fila, excluir=("capitulo_id", "partida_catalogo_id")
        )
        archivos_omitidos += _limpiar_archivos(kwargs, ("producto_imagen",))
        item = PresupuestoItem(
            capitulo_id=capitulo.id,
            partida_catalogo_id=mapa_partidas.get(fila.get("partida_catalogo_id")),
            **kwargs,
        )
        db.add(item)
        mapa_items[fila["id"]] = item
    db.flush()

    for fila in datos["mediciones"]:
        item = mapa_items.get(fila.get("partida_id"))
        if item is None:
            continue
        db.add(Medicion(partida_id=item.id, **_kwargs_modelo(Medicion, fila, excluir=("partida_id",))))

    for fila in datos["presupuesto_item_productos"]:
        item = mapa_items.get(fila.get("partida_id"))
        if item is None:
            continue
        kwargs = _kwargs_modelo(PresupuestoItemProducto, fila, excluir=("partida_id",))
        archivos_omitidos += _limpiar_archivos(kwargs, ("imagen",))
        db.add(PresupuestoItemProducto(partida_id=item.id, **kwargs))

    mapa_descomposiciones: dict[int, DescomposicionPartida] = {}
    for fila in datos["descomposiciones_partida"]:
        item = mapa_items.get(fila.get("partida_id"))
        if item is None:
            continue
        kwargs = _kwargs_modelo(DescomposicionPartida, fila, excluir=("partida_id",))
        archivos_omitidos += _limpiar_archivos(kwargs, ("archivo_origen",))
        descomposicion = DescomposicionPartida(partida_id=item.id, **kwargs)
        db.add(descomposicion)
        mapa_descomposiciones[fila["id"]] = descomposicion
    db.flush()

    for fila in datos["descomposicion_filas"]:
        descomposicion = mapa_descomposiciones.get(fila.get("descomposicion_id"))
        if descomposicion is None:
            continue
        db.add(DescomposicionFila(
            descomposicion_id=descomposicion.id,
            **_kwargs_modelo(DescomposicionFila, fila, excluir=("descomposicion_id",)),
        ))

    for fila in datos["notas_seguimiento"]:
        presupuesto = mapa_presupuestos.get(fila.get("presupuesto_id"))
        if presupuesto is None or not str(fila.get("texto") or "").strip():
            continue
        db.add(NotaSeguimiento(
            presupuesto_id=presupuesto.id,
            **_kwargs_modelo(NotaSeguimiento, fila, excluir=("presupuesto_id",)),
        ))

    mapa_versiones: dict[int, PresupuestoVersion] = {}
    for fila in datos["presupuesto_versiones"]:
        presupuesto = mapa_presupuestos.get(fila.get("presupuesto_id"))
        if presupuesto is None:
            continue
        kwargs = _kwargs_modelo(PresupuestoVersion, fila, excluir=("presupuesto_id",))
        archivos_omitidos += _limpiar_archivos(kwargs, ("pdf_snapshot",))
        version = PresupuestoVersion(presupuesto_id=presupuesto.id, **kwargs)
        db.add(version)
        mapa_versiones[fila["id"]] = version
    db.flush()

    # --- Documentos de cobro --------------------------------------------------
    numeros_facturas = {n for (n,) in db.query(Factura.numero).all()}
    mapa_facturas: dict[int, Factura] = {}
    for fila in datos["facturas"]:
        numero = str(fila.get("numero", ""))
        if numero in numeros_facturas:
            omitidos["facturas_conflicto"] += 1
            advertencias.append(f"No se importó el documento de cobro {numero}: ese número ya existe.")
            continue
        cliente = _cliente_destino(fila.get("client_id"))
        if cliente is None:
            omitidos["facturas_sin_cliente"] += 1
            continue
        presupuesto = mapa_presupuestos.get(fila.get("presupuesto_id"))
        version = mapa_versiones.get(fila.get("presupuesto_version_id"))
        if fila.get("presupuesto_id") and presupuesto is None:
            advertencias.append(
                f"El documento de cobro {numero} se importó sin su presupuesto vinculado."
            )
        factura = Factura(
            client_id=cliente.id,
            presupuesto_id=presupuesto.id if presupuesto else None,
            presupuesto_version_id=version.id if version else None,
            **_kwargs_modelo(
                Factura, fila,
                excluir=("client_id", "presupuesto_id", "presupuesto_version_id"),
            ),
        )
        db.add(factura)
        mapa_facturas[fila["id"]] = factura
        numeros_facturas.add(numero)
        importados["documentos_cobro"] += 1
    db.flush()

    mapa_factura_capitulos: dict[int, FacturaCapitulo] = {}
    for fila in datos["factura_capitulos"]:
        factura = mapa_facturas.get(fila.get("factura_id"))
        if factura is None:
            continue
        capitulo = FacturaCapitulo(
            factura_id=factura.id,
            **_kwargs_modelo(FacturaCapitulo, fila, excluir=("factura_id",)),
        )
        db.add(capitulo)
        mapa_factura_capitulos[fila["id"]] = capitulo
    db.flush()

    for fila in datos["factura_items"]:
        capitulo = mapa_factura_capitulos.get(fila.get("capitulo_id"))
        if capitulo is None:
            continue
        db.add(FacturaItem(
            capitulo_id=capitulo.id,
            **_kwargs_modelo(FacturaItem, fila, excluir=("capitulo_id",)),
        ))

    # --- Proyectos, cambios de alcance y pagos --------------------------------
    proyectos_con_presupuesto = {
        pid for (pid,) in db.query(Proyecto.presupuesto_id).all()
    }
    mapa_proyectos: dict[int, Proyecto] = {}
    for fila in datos["proyectos"]:
        presupuesto = mapa_presupuestos.get(fila.get("presupuesto_id"))
        if presupuesto is None or presupuesto.id in proyectos_con_presupuesto:
            omitidos["proyectos"] += 1
            continue
        version = mapa_versiones.get(fila.get("presupuesto_version_id"))
        proyecto = Proyecto(
            presupuesto_id=presupuesto.id,
            presupuesto_version_id=version.id if version else None,
            **_kwargs_modelo(
                Proyecto, fila, excluir=("presupuesto_id", "presupuesto_version_id")
            ),
        )
        db.add(proyecto)
        mapa_proyectos[fila["id"]] = proyecto
        proyectos_con_presupuesto.add(presupuesto.id)
        importados["proyectos"] += 1
    db.flush()

    mapa_cambios: dict[int, CambioAlcance] = {}
    for fila in datos["cambios_alcance"]:
        proyecto = mapa_proyectos.get(fila.get("proyecto_id"))
        if proyecto is None:
            continue
        cambio = CambioAlcance(
            proyecto_id=proyecto.id,
            **_kwargs_modelo(CambioAlcance, fila, excluir=("proyecto_id",)),
        )
        db.add(cambio)
        mapa_cambios[fila["id"]] = cambio
    db.flush()

    for fila in datos["cambio_alcance_items"]:
        cambio = mapa_cambios.get(fila.get("cambio_id"))
        if cambio is None:
            continue
        db.add(CambioAlcanceItem(
            cambio_id=cambio.id,
            **_kwargs_modelo(CambioAlcanceItem, fila, excluir=("cambio_id",)),
        ))

    for fila in datos["pagos"]:
        proyecto = mapa_proyectos.get(fila.get("proyecto_id"))
        presupuesto = mapa_presupuestos.get(fila.get("presupuesto_id"))
        factura = mapa_facturas.get(fila.get("factura_id"))
        referencias_perdidas = any(
            fila.get(campo) and destino is None
            for campo, destino in (
                ("proyecto_id", proyecto),
                ("presupuesto_id", presupuesto),
                ("factura_id", factura),
            )
        )
        if referencias_perdidas:
            omitidos["pagos"] += 1
            continue
        kwargs = _kwargs_modelo(
            Pago, fila, excluir=("proyecto_id", "presupuesto_id", "factura_id")
        )
        archivos_omitidos += _limpiar_archivos(kwargs, ("comprobante",))
        db.add(Pago(
            proyecto_id=proyecto.id if proyecto else None,
            presupuesto_id=presupuesto.id if presupuesto else None,
            factura_id=factura.id if factura else None,
            **kwargs,
        ))
        importados["pagos"] += 1
    db.flush()

    anexos = len(datos["presupuesto_anexos"])
    if anexos:
        advertencias.append(f"{anexos} anexo(s) de presupuesto no se importaron (archivos locales).")
    if archivos_omitidos:
        advertencias.append(
            f"{archivos_omitidos} referencia(s) a archivos locales se omitieron; "
            "vuelve a subir esas imágenes o PDFs desde la web."
        )
    if fuente["fuera_de_espacio"]:
        advertencias.append(
            f"{fuente['fuera_de_espacio']} registro(s) de otros espacios locales no se importaron."
        )

    return {
        "importados": dict(importados),
        "omitidos": dict(omitidos),
        "advertencias": advertencias,
        "sha256": fuente["sha256"],
    }
