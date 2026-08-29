"""Contextos de las pantallas del panel (reorganización de 2026-08-30).

``app/routers/admin_paginas.py`` monta la respuesta HTTP y aquí se calcula lo que
cada pantalla necesita para pintarse: navegación común, pestañas, filtros, orden,
vistas guardadas y contadores. Separarlo permite que las seis áreas se comporten
**igual** —misma barra de filtros, mismos chips, mismo CSV— sin copiar y pegar lo
mismo en doce rutas, que es exactamente como el panel había crecido.

Convención: todo el estado de una lista viaja por query string
(``?tab=&q=&estado=&orden=&mes=``). Así un filtro es enlazable desde el buscador
⌘K, desde la campana de notificaciones o desde la ficha de un cliente, y la
pantalla sigue funcionando sin JavaScript.
"""
from __future__ import annotations

from datetime import date, timedelta
from urllib.parse import urlencode

from ..models import CompraPlan, Licencia, ORIGENES_LICENCIA, ORIGENES_LICENCIA_ETIQUETA
from ..panel_arquitectura import (
    cabecera_panel,
    modulo_de_vistas,
    nav_panel,
    pestana_valida,
    pestanas_panel,
)

MESES = (
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
)

#: Estado del acceso. Es el MISMO criterio en el directorio, en los contratos y
#: en las renovaciones: una sola palabra para «por vencer», con su umbral de 15
#: días definido por ``resumen_admin``.
ESTADOS_ACCESO = (
    ("", "Todos"),
    ("activa", "Activo"),
    ("por_vencer", "Por vencer (≤15 d)"),
    ("vencida", "Vencido"),
    ("sin_licencia", "Sin plan"),
)

FILTROS_PLAN = (
    ("", "Todos los planes"),
    ("anual", "Anual"),
    ("mensual", "Mensual"),
    ("prueba", "En prueba"),
    ("cortesia", "Cortesía o compensación"),
    ("sin", "Sin plan"),
)

ESTADOS_COMPRA = (
    ("pendiente", "Por revisar"),
    ("activa", "Activadas"),
    ("rechazada", "Rechazadas"),
    ("todas", "Todas"),
)

TIPOS_COBRO = (
    ("", "Todos los movimientos"),
    ("licencia", "Licencias de pago"),
    ("compra", "Compras de plan"),
    ("factura", "Facturas de clientes"),
    ("pago", "Pagos de clientes"),
)

RENOVACION_ESTADOS = (
    ("", "Todas"),
    ("por_renovar", "Por renovar"),
    ("vencida", "Vencidas"),
    ("activa", "Aún activas"),
)

#: Columnas ordenables del directorio: la clave va en la URL, la etiqueta en la
#: cabecera de la tabla.
ORDENES = {
    "nombre": "Cliente",
    "plan": "Plan",
    "vence": "Vencimiento",
    "ingresos": "Ingresos",
    "estado": "Estado",
}
PESO_ESTADO = {"por_vencer": 0, "vencida": 1, "sin_licencia": 2, "activa": 3}

#: Qué significa cada estado comercial, para que el panel lo explique en vez de
#: dejar al operador adivinando si «riesgo» es un problema o una etapa normal.
DESCRIPCIONES_CRM = {
    "lead": "No ha probado el producto: hay que enseñárselo.",
    "prueba": "Dentro con acceso temporal: decide antes de que venza.",
    "activo": "Renovó o paga: mantener el contacto.",
    "riesgo": "Problema o desacuerdo abierto: llamar antes del vencimiento.",
    "inactivo": "Dejó de usarlo: saber por qué antes de darle de baja.",
}

ETIQUETAS_ORIGEN = dict(ORIGENES_LICENCIA_ETIQUETA)

#: Etiquetas de los movimientos de cobro: el servicio devuelve estados crudos
#: (``pagada``, ``emitida``, ``sin_cobro``…) y el operador necesita leerlos.
ETIQUETAS_ESTADO_COBRO = {
    "pagada": "Cobrada",
    "confirmado": "Confirmado",
    "emitida": "Emitida",
    "vencida": "Vencida",
    "pendiente": "Pendiente",
    "Pendiente": "Pendiente",
    "Activada": "Activada",
    "sin_cobro": "Sin cobro",
    "rechazada": "Rechazada",
}
ETIQUETAS_TIPO_COBRO = {
    "licencia": "Licencia",
    "compra": "Compra",
    "factura": "Factura",
    "pago": "Pago",
}
BADGES_TIPO_COBRO = {
    "licencia": "badge-success",
    "compra": "badge-info",
    "factura": "badge-neutral",
    "pago": "badge-success",
}

#: Qué comprueba cada línea de ``/readyz``. El diagnóstico dice *qué* falla; sin
#: esto el operador ve «email: False» sin saber si eso rompe algo o no.
NOTAS_CHEQUEOS = {
    "base_datos": "Conexión a la base y último esquema aplicado.",
    "storage": "Que los anexos y comprobantes se puedan leer y escribir.",
    "email": "Resend configurado: sin esto, los avisos de vencimiento no salen.",
    "supabase": "Proveedor de autenticación accesible.",
    "rate_limit": "Contador de frecuencia de intentos (bloqueos).",
    "licencias": "Corte automático de acceso por licencia vencida.",
    "errores": "Errores no capturados acumulados por el proceso.",
}

#: Alcances por rol, para no dejar el rol como una palabra mágica en la tabla.
ALCANCES_ROL = (
    ("superadmin", "Equipo completo: roles, altas y suspensiones."),
    ("admin", "Clientes, ingresos, web y sistema; no gestiona el equipo."),
    ("soporte", "Ficha del cliente y estado del acceso para atender incidencias."),
    ("analista", "Solo lectura de analítica y cifras: no concede accesos."),
)


# ---------------------------------------------------------------------------
# URLs y navegación
# ---------------------------------------------------------------------------


def url_panel(ruta: str, **parametros) -> str:
    """URL del panel con los parámetros no vacíos, en el orden recibido."""
    consulta = _consulta_url(parametros)
    return f"{ruta}?{consulta}" if consulta else ruta


def _consulta_url(parametros: dict) -> str:
    limpio = {
        clave: valor
        for clave, valor in parametros.items()
        if valor not in (None, "") and valor is not False
    }
    return urlencode(limpio)


def _aplicar_cambios(actuales: dict, cambios: dict) -> dict:
    """Combina los filtros de la URL con los que la plantilla pide cambiar.

    Repetir el valor activo lo quita: es el gesto que se espera de una chip, y
    ahorra el botón «limpiar» en cada barra.
    """
    resultado = dict(actuales)
    for clave, valor in cambios.items():
        if valor in (None, ""):
            resultado.pop(clave, None)
        elif resultado.get(clave) == valor:
            resultado.pop(clave, None)
        else:
            resultado[clave] = valor
    return resultado


def enlace_filtro(ruta: str, actuales: dict):
    """Función de plantilla: ``ruta_filtro(estado='vencida')`` → URL con filtro."""

    def enlace(**cambios):
        return url_panel(ruta, **_aplicar_cambios(actuales, cambios))

    return enlace


def enlace_orden(ruta: str, actuales: dict):
    """Función de plantilla para las cabeceras de tabla ordenables.

    Devuelve un dict —no HTML— para que el marcado siga siendo de la plantilla:
    ``{% set e = enlace_orden('vence', 'Vencimiento') %}<a href="{{ e.url }}">…``
    """

    def enlace(campo: str, etiqueta: str):
        activo = actuales.get("orden", "nombre") == campo
        direccion = "desc" if (activo and actuales.get("dir", "asc") == "asc") else "asc"
        return {
            "etiqueta": etiqueta,
            "url": url_panel(ruta, **{**actuales, "orden": campo, "dir": direccion}),
            "flecha": ("↑" if direccion == "asc" else "↓") if activo else "",
            "activo": activo,
        }

    return enlace


def chips(ruta: str, actuales: dict, opciones, clave: str, contadores: dict | None = None):
    """Chips de filtrado (estado, tipo…) con su contador y su URL montada.

    Se construyen en el servidor porque el contador depende de los MISMOS
    filtros que ya están activos: hacerlo en la plantilla obligaría a repetir la
    lógica de recuento.
    """
    contadores = contadores or {}
    activo = actuales.get(clave, "")
    salida = []
    for opcion in opciones:
        valor, etiqueta = opcion[0], opcion[1]
        # La opción «todos» (valor vacío) no se puede quitar pulsando: enlaza a
        # la URL sin ese filtro.
        cambios = {clave: valor} if valor else {clave: ""}
        salida.append({
            "valor": valor,
            "etiqueta": etiqueta,
            "url": url_panel(ruta, **_aplicar_cambios(actuales, cambios)),
            "activo": (activo or "") == valor,
            "contador": int(contadores.get(valor, 0) or 0),
        })
    return salida


def opciones_con_contadores(contadores: dict, pares) -> list:
    """``[(valor, etiqueta)]`` → ``[(valor, etiqueta, contador)]`` para los chips.

    Los contadores salen del conjunto **ya filtrado** por lo demás, así que cada
    chip dice cuántas filas quedarían si se pulsa.
    """
    return [
        (valor, etiqueta, int(contadores.get(valor, 0) or 0)) for valor, etiqueta in pares
    ]


def contadores_panel(db) -> dict:
    """Cifras de los badges del menú y de las pestañas.

    Solo dos consultas con índice (compras pendientes y licencias por vencer):
    decorar la navegación no puede suponer recorrer la base en cada petición.
    """
    hoy = date.today()
    try:
        compras = db.query(CompraPlan).filter(CompraPlan.estado == "pendiente").count()
    except Exception:
        db.rollback()
        compras = 0
    try:
        por_vencer = (
            db.query(Licencia)
            .filter(
                Licencia.estado == "activa",
                Licencia.vence >= hoy,
                Licencia.vence <= hoy + timedelta(days=15),
            )
            .count()
        )
    except Exception:
        db.rollback()
        por_vencer = 0
    return {"ingresos": compras + por_vencer, "compras": compras, "renovaciones": por_vencer}


def contexto_base(
    request,
    db,
    *,
    seccion: str,
    pestana: str = "",
    msg: str = "",
    error: str = "",
    contadores: dict | None = None,
    cabecera: dict | None = None,
) -> dict:
    """Menú, pestañas, título, mensajes y opciones compartidas de los formularios."""
    if contadores is None:
        contadores = contadores_panel(db)
    pestana_activa = pestana_valida(seccion, pestana)
    from ..services.licencias import DURACIONES

    return {
        "request": request,
        "secciones": nav_panel(contadores),
        "seccion_activa": seccion,
        "pestanas": pestanas_panel(seccion, pestana_activa, contadores),
        "pestana": pestana_activa,
        "pestana_nombre": _nombre_pestanas(seccion, pestana_activa),
        "cabecera": cabecera or cabecera_panel(seccion, pestana_activa),
        "operador": db.info.get("auth_email", ""),
        "operador_rol": str(db.info.get("operador_rol") or "").lower(),
        "hoy": date.today(),
        "contadores": contadores,
        "msg": msg or request.query_params.get("msg", ""),
        "error": error or request.query_params.get("error", ""),
        "etiquetas_origen": ETIQUETAS_ORIGEN,
        # Los formularios de concesión comparten estas listas con el servicio:
        # si mañana hay una duración nueva, el panel la ofrece sin tocar nada.
        "duraciones": [(clave, texto) for clave, (texto, _) in DURACIONES.items()],
        "origenes": [(origen, ETIQUETAS_ORIGEN[origen]) for origen in ORIGENES_LICENCIA],
    }


def _nombre_pestanas(seccion: str, pestana: str) -> str:
    for definida in pestanas_panel(seccion, ""):
        if definida["id"] == pestana:
            return definida["nombre"]
    return ""


# ---------------------------------------------------------------------------
# Filtros y orden del directorio (la tabla y su CSV comparten el criterio)
# ---------------------------------------------------------------------------


def _encaja_plan(fila, plan: str) -> bool:
    licencia = fila.get("vigente")
    if plan == "sin":
        return licencia is None
    if licencia is None:
        return False
    if plan in ("anual", "mensual"):
        return fila.get("plan_label") == ("Anual" if plan == "anual" else "Mensual")
    if plan == "prueba":
        return licencia.origen == "prueba"
    if plan == "cortesia":
        return licencia.origen in ("cortesia", "compensacion")
    return True


def filtrar_filas(
    filas, *, q: str = "", estado: str = "", plan: str = "", crm: str = "",
    crm_por_org: dict | None = None,
):
    """Deja las filas de cliente que pasan todos los filtros activos."""
    texto = (q or "").strip().lower()
    salida = []
    for fila in filas:
        org = fila["organizacion"]
        if texto and texto not in f"{org.nombre} {org.slug}".lower():
            continue
        if estado and fila.get("estado") != estado:
            continue
        if plan and not _encaja_plan(fila, plan):
            continue
        if crm:
            etiqueta = ((crm_por_org or {}).get(org.id) or {}).get("estado", "")
            if crm == "sin_asignar":
                if etiqueta:
                    continue
            elif etiqueta != crm:
                continue
        salida.append(fila)
    return salida


def ordenar_filas(filas, orden: str, direccion: str):
    """Orden en el servidor: la URL se puede compartir y el CSV sale igual."""
    clave = orden if orden in ORDENES else "nombre"
    invertido = direccion == "desc"

    def valor(fila):
        if clave == "nombre":
            return fila["organizacion"].nombre.lower()
        if clave == "plan":
            return (fila.get("plan_label") or "").lower()
        if clave == "vence":
            vence = fila.get("vence")
            # Sin fecha de vencimiento va al final en ambas direcciones.
            return (1, vence.toordinal()) if vence else (2, 0)
        if clave == "ingresos":
            return float(fila.get("ingresos") or 0)
        return PESO_ESTADO.get(fila.get("estado", ""), 9)

    return sorted(filas, key=valor, reverse=invertido)


# ---------------------------------------------------------------------------
# Vistas guardadas (A5): chips en la barra de la propia lista
# ---------------------------------------------------------------------------


def vistas_en_barra(db, modulo: str, *, ruta: str, pestana: str) -> list:
    """Vistas guardadas del módulo, convertidas en enlaces con sus filtros.

    Antes eran una página aparte donde había que teclear el JSON a mano y que no
    se aplicaba en ningún sitio. Una vista es ahora el set de filtros de la URL
    guardado con nombre; al pincharla se reconstruye esa URL.
    """
    from ..services.web_admin import listar_vistas

    vistas = []
    for vista in listar_vistas(db, modulo):
        filtros = vista.filtros_dict() or {}
        parametros = {k: v for k, v in filtros.items() if v}
        if pestana:
            parametros["tab"] = pestana
        url = url_panel(ruta, **{k: v for k, v in sorted(parametros.items())})
        vistas.append({
            "id": vista.id,
            "nombre": vista.nombre,
            "url": url,
            "filtros_texto": ", ".join(f"{k}: {v}" for k, v in filtros.items()) or "sin filtros",
        })
    return vistas


def filtros_json(actuales: dict) -> dict:
    """Dict que se guarda en ``vistas_guardadas.filtros`` desde la URL actual.

    Excluye ``tab``/``orden``/``dir``: una vista guarda *a quién se busca*, no
    en qué pestaña estaba el operador ni cómo estaba ordenada la tabla.
    """
    return {
        clave: valor
        for clave, valor in actuales.items()
        if valor and clave not in ("tab", "orden", "dir", "vista")
    }


def url_filtros(actuales: dict) -> str:
    """Query string de los filtros activos (para el CSV y para la vista)."""
    return _consulta_url(filtros_json(actuales))


def modulo_de_vistas_seguro(seccion: str, pestana: str) -> str:
    try:
        return modulo_de_vistas(seccion, pestana)
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Periodo mensual (cobros y renovaciones)
# ---------------------------------------------------------------------------


def vecinos_del_mes(mes: date) -> tuple[str, str]:
    """ ``(anterior, siguiente)`` en ``AAAA-MM``.

    Se calcula aquí y no en la plantilla: Jinja no suma meses y ``mes - 1`` en
    diciembre es el tipo de fallo que se cuela justo en el cierre del año.
    """
    anterior = (mes.replace(day=1) - timedelta(days=1)).replace(day=1)
    if mes.month == 12:
        siguiente = mes.replace(year=mes.year + 1, month=1, day=1)
    else:
        siguiente = mes.replace(month=mes.month + 1, day=1)
    return anterior.strftime("%Y-%m"), siguiente.strftime("%Y-%m")


def fin_de_mes(mes: date) -> date:
    return (mes.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)


def periodo_mes(mes: date, *, ruta: str, pestana: str, actuales: dict) -> dict:
    """Bloque de navegación mensual que comparten cobros y renovaciones."""
    anterior, siguiente = vecinos_del_mes(mes)
    sin_mes = {k: v for k, v in actuales.items() if k not in ("mes", "tab") and v}
    return {
        "actual": mes.strftime("%Y-%m"),
        "etiqueta": f"{MESES[mes.month - 1].capitalize()} de {mes.year}",
        "rango": f"{mes.strftime('%d/%m')} – {fin_de_mes(mes).strftime('%d/%m/%Y')}",
        "anterior": url_panel(ruta, **{**sin_mes, "tab": pestana, "mes": anterior}),
        "siguiente": url_panel(ruta, **{**sin_mes, "tab": pestana, "mes": siguiente}),
        "accion": ruta,
        # Lo que el formulario de «ir a otro mes» debe reenviar para no perder
        # la pestaña ni el filtro al navegar.
        "ocultos": {**sin_mes, "tab": pestana},
    }
