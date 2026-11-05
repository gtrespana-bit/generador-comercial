"""Lectura de configuración que sobrevive a un despliegue sin migración.

El patrón que ha reventado tres veces en producción (``b1c2d3e4f5a6`` con
``recorrido_inicial_oculto``, ``h1c4b7e9a3d2`` con
``mostrar_desglose_precio`` y ``t9b4d7e2c5f8`` con
``onboarding_precios_revisados``) es siempre el mismo: un deploy sube el código
antes de que nadie pegue el SQL de la migración. A partir de ahí **cualquier**
``db.query(Configuracion)`` es un ``SELECT`` con todas las columnas del modelo
y PostgreSQL responde ``UndefinedColumn``: 500 en la página y el panel de salud
en rojo hasta que alguien aplica la migración a mano.

Este módulo centraliza la lectura para que ese desfase sea aburrido:

``leer_configuracion``
    Devuelve la configuración del tenant. Si el ``SELECT`` completo falla
    porque una columna aún no existe, se reintenta pidiendo solo las columnas
    que la base **sí** tiene (leídas de ``information_schema``); las que faltan
    se completan con el valor por defecto del modelo. La página abre con los
    datos reales que existen: no se inventa ni se escribe nada.

No hace DDL ni pide permisos de escritura. En Vercel el rol de la aplicación no
es dueño de las tablas, así que un ``ALTER`` desde aquí fallaría igual. La vía
para crear la columna sigue siendo ``alembic upgrade head`` o el SQL manual; lo
que cambia es que la web **sigue sirviendo** mientras tanto.
"""
from __future__ import annotations

import logging
import threading

from sqlalchemy import inspect, text

from ..models import Configuracion

log = logging.getLogger("cotizat")

#: Columnas reales por tabla y motor. La clave incluye el motor porque una misma
#: instalación puede atender varias bases (SQLite local y PostgreSQL de la web)
#: y, sobre todo, porque un esquema cambia: cachear por nombre de tabla servía
#: una lista obsoleta en cuanto se aplicaba la migración.
_CACHE: dict[tuple[int, str], set[str]] = {}
_LOCK = threading.Lock()

def olvidar_columnas(tabla: str | None = None) -> None:
    """Vacía la caché (tras aplicar la migración, o en las pruebas)."""
    with _LOCK:
        if tabla is None:
            _CACHE.clear()
            return
        for clave in [c for c in _CACHE if c[1] == tabla]:
            _CACHE.pop(clave, None)


def columnas_faltantes(db, modelo) -> list[str]:
    """Columnas del modelo que la base todavía no tiene."""
    disponibles = columnas_disponibles(db, modelo)
    if disponibles is None:
        return []
    return [c for c in _columnas_del_modelo(modelo) if c not in disponibles]


def consulta(db, modelo):
    """``db.query(modelo)`` que no pide las columnas que la base no tiene.

    Es el mismo patrón que ``_config`` pero para las tablas grandes: en un
    despliegue sin migración, ``SELECT recursos.*`` falla entero por una sola
    columna nueva (``precio_revisado_at`` el 04/11/2026) y tumba el catálogo.
    Con ``defer`` la columna ausente ni se pide y el resto se lee normal.

    Comprobar las columnas cuesta una lectura de ``information_schema`` por
    tabla y proceso (queda cacheada); cuando el esquema está al día la consulta
    que se devuelve es exactamente la de siempre.
    """
    base = db.query(modelo)
    faltan = columnas_faltantes(db, modelo)
    if not faltan:
        return base
    from sqlalchemy.orm import defer

    return base.options(*[defer(getattr(modelo, nombre)) for nombre in faltan])


def _tabla_de(modelo) -> str:
    return getattr(modelo, "__tablename__", "") or ""


def columnas_disponibles(db, modelo) -> set[str] | None:
    """Columnas reales de la tabla de ``modelo`` según la base conectada.

    ``None`` significa «no se pudo averiguar»: quien llama debe seguir con el
    ``SELECT`` normal en vez de armar una consulta a ciegas.
    """
    tabla = _tabla_de(modelo)
    if not tabla:
        return None
    try:
        bind = db.get_bind()
    except Exception:
        return None
    clave = (id(bind), tabla)
    with _LOCK:
        cacheado = _CACHE.get(clave)
    if cacheado:
        return cacheado
    try:
        # Inspeccionar **la conexión de la sesión**, no el motor: pedir una
        # conexión al pool la devuelve al terminar y SQLAlchemy hace
        # ``rollback`` al devolverla. Con ``StaticPool`` (SQLite en pruebas)
        # esa conexión es la misma de la sesión, así que el ``rollback`` tiraba
        # los cambios pendientes (recursos recién añadidos) y luego el
        # ``INSERT`` del precio rompía por clave foránea.
        columnas = {
            columna["name"] for columna in inspect(db.connection()).get_columns(tabla)
        }
    except Exception:
        return None
    if not columnas:
        return None
    with _LOCK:
        _CACHE[clave] = columnas
    return columnas


def _columnas_del_modelo(modelo) -> list[str]:
    return [columna.name for columna in modelo.__table__.columns]


def _valor_por_defecto(modelo, columna: str):
    """Valor que la columna tendría si existiera (default del modelo o del tipo)."""
    col = modelo.__table__.columns.get(columna)
    if col is None:
        return None
    defecto = col.default
    if defecto is not None and getattr(defecto, "is_scalar", False):
        return defecto.arg
    if col.nullable:
        return None
    # Columna NOT NULL sin default constante: manda el tipo. ``False`` para
    # booleanos, 0 para números, cadena vacía para texto.
    try:
        tipo = col.type.python_type
        if tipo is bool:
            return False
        if tipo in (int, float):
            return tipo(0)
        if tipo is str:
            return ""
    except Exception:
        pass
    return None


def _es_columna_faltante(exc: Exception) -> bool:
    """¿El fallo es «esta columna no existe» y no otra cosa?"""
    texto = str(exc).lower()
    return (
        "undefinedcolumn" in texto
        or "no such column" in texto
        or "does not exist" in texto
        or "no column" in texto
    )


def fila_a_objeto(modelo, fila):
    """Objeto del modelo relleno con las columnas que sí existen.

    Las ausentes quedan con su valor por defecto escritas directamente en
    ``__dict__``, que es lo que SQLAlchemy considera «cargado»: si se dejaran
    sin tocar, el primer acceso dispararía un ``SELECT`` de la columna que
    falta y volveríamos al 500.
    """
    objeto = modelo()
    for columna in _columnas_del_modelo(modelo):
        if columna in fila._mapping:
            valor = fila._mapping[columna]
        else:
            valor = _valor_por_defecto(modelo, columna)
        objeto.__dict__[columna] = valor
    return objeto


def _consulta_parcial(db, disponibles: set[str]):
    """``SELECT`` con las columnas que existen.

    Bajo RLS basta ``LIMIT 1`` (las políticas ya acotan a la organización), pero
    en SQLite local la tabla es común a todos los espacios: cuando la sesión no
    trae organización se devuelve la primera fila ordenada por ``id``, que es la
    que crea ``asegurar_config`` en el alta.
    """
    presentes = [c for c in _columnas_del_modelo(Configuracion) if c in disponibles]
    if not presentes:
        return None
    sql = f"SELECT {', '.join(presentes)} FROM configuracion"
    parametros: dict[str, object] = {}
    org_id = db.info.get("organizacion_id")
    if org_id is not None and "organizacion_id" in disponibles:
        sql += " WHERE organizacion_id = :org_id"
        parametros["org_id"] = int(org_id)
    if "id" in disponibles:
        sql += " ORDER BY id"
    sql += " LIMIT 1"
    return db.execute(text(sql), parametros).first()


def obtener(db, modelo, ident):
    """``db.get(modelo, ident)`` sin pedir columnas que la base no tiene."""
    faltan = columnas_faltantes(db, modelo)
    if not faltan:
        return db.get(modelo, ident)
    return consulta(db, modelo).filter(modelo.id == ident).first()


def atributo(obj, nombre: str, defecto=None):
    """Lee un atributo del modelo sin romper si su columna no existe.

    Las pantallas leen ``recurso.precio_revisado_at``. Con el esquema
    atrasado, SQLAlchemy intenta un ``SELECT`` de esa columna al primer acceso
    y falla; aquí se degrada a «sin dato» (que es la verdad: no hay fecha
    guardable todavía) en vez de tumbar la página.
    """
    try:
        return getattr(obj, nombre)
    except Exception:
        try:
            obj.__dict__[nombre] = defecto
        except Exception:
            pass
        return defecto


def detectar_desfase(db) -> bool:
    """¿La base va por detrás del modelo? (columnas de configuración o recursos)"""
    try:
        from ..models import Recurso

        return bool(
            columnas_faltantes(db, Configuracion)
            or columnas_faltantes(db, Recurso)
        )
    except Exception:
        return False


def leer_configuracion(db, *, crear=None):
    """Configuración del tenant, tolerando columnas que aún no existen.

    ``crear`` es el callable que asegura la fila (``asegurar_config``). Se pasa
    como argumento para no importar routers desde aquí y evitar ciclos.

    Sin organización en ``db.info`` (SQLite local) se devuelve la fila de menor
    ``id``, igual que hacía ``SELECT ... LIMIT 1`` sin filtro: crear una
    organización «espacio local» solo para leer la configuración dejaría el
    tenant vacío y la pantalla sin datos.
    """
    try:
        cfg = db.query(Configuracion).first()
        if cfg is None and crear is not None:
            crear(db)
            cfg = db.query(Configuracion).first()
        return cfg
    except Exception as exc:
        if not _es_columna_faltante(exc):
            raise
        log.warning(
            "configuracion no tiene todas las columnas del modelo (despliegue "
            "sin migración): se lee con las que existen. %s",
            exc,
        )
        try:
            db.rollback()
        except Exception:
            pass

    # Vía tolerante: solo las columnas que la base tiene de verdad.
    disponibles = columnas_disponibles(db, Configuracion)
    if disponibles is None:
        raise RuntimeError(
            "No se pudieron leer las columnas de configuracion; "
            "ejecuta `alembic upgrade head`."
        )
    try:
        fila = _consulta_parcial(db, disponibles)
        if fila is None and crear is not None:
            crear(db)
            fila = _consulta_parcial(db, disponibles)
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
        raise
    if fila is None:
        return None
    return fila_a_objeto(Configuracion, fila)
