"""Pantallas del panel de operador: seis áreas con sus pestañas.

Aquí solo hay **lectura**: cada ruta monta el contexto de su pestaña activa y lo
pinta. Las acciones (conceder, activar una compra, publicar un aviso, cambiar un
rol) están en ``app/routers/admin.py``, junto a los cron que las sustentan; la
navegación, los filtros y las pestañas se calculan una sola vez en
``app/services/panel_contextos.py``.

Por qué un módulo aparte: hasta ahora cada página del panel era una ruta con su
propio contexto suelto, y así el panel llegó a tener 21 entradas de menú con la
misma información repetida y tres formas distintas de filtrar lo mismo. Aquí las
seis áreas comparten un único mecanismo de filtros (query string), de orden y de
vistas guardadas.
"""  # E4-001 — router por dominio, como el resto de app/routers
from __future__ import annotations

import json
from datetime import date

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from .common import TEMPLATES, Session, _csv_response, log  # noqa: F401
from ..database import get_operator_db
from ..panel_arquitectura import (
    RUTAS_ANTIGUAS,
    modulo_de_vistas,
    pestana_ficha_valida,
    pestana_valida,
    redireccion_de,
    ruta_panel,
)
from ..services.panel_contextos import (
    ALCANCES_ROL,
    DESCRIPCIONES_CRM,
    ESTADOS_ACCESO,
    ESTADOS_COMPRA,
    FILTROS_PLAN,
    NOTAS_CHEQUEOS,
    ORDENES,
    RENOVACION_ESTADOS,
    TIPOS_COBRO,
    BADGES_TIPO_COBRO,
    ETIQUETAS_ESTADO_COBRO,
    ETIQUETAS_TIPO_COBRO,
    contexto_base,
    contadores_panel,
    enlace_filtro,
    enlace_orden,
    filtrar_filas,
    filtros_json,
    chips,
    opciones_con_contadores,
    ordenar_filas,
    periodo_mes,
    url_filtros,
    url_panel,
    vistas_en_barra,
)

router = APIRouter()

#: Pestañas de Ingresos con su constructor de contexto. Cada una lee un servicio
#: distinto pero comparten barra de filtros, vistas guardadas, CSV y navegación.
_constructor = {}


# ---------------------------------------------------------------------------
# Utilidades comunes
# ---------------------------------------------------------------------------


def _respuesta(request: Request, plantilla: str, contexto: dict, status_code: int = 200):
    """Render del panel: sin caché (los números cambian con cada acción)."""
    return TEMPLATES.TemplateResponse(
        request,
        f"admin/{plantilla}",
        contexto,
        status_code=status_code,
        headers={"Cache-Control": "no-store"},
    )


def _texto(request: Request, *nombres: str) -> dict:
    """Parámetros de query limpios: la cadena vacía significa «sin filtro»."""
    salida = {}
    for nombre in nombres:
        bruto = request.query_params.get(nombre)
        if isinstance(bruto, list):
            bruto = bruto[0] if bruto else ""
        salida[nombre] = str(bruto or "").strip()
    return salida


def _entero(valor, por_defecto: int = 0) -> int:
    try:
        return int(str(valor).strip())
    except (TypeError, ValueError):
        return por_defecto


def _mes(valor) -> date:
    """``AAAA-MM`` al primer día del mes; el mes actual si viene vacío o roto."""
    hoy = date.today()
    texto = str(valor or "").strip()
    if not texto:
        return hoy.replace(day=1)
    try:
        año, mes = (int(parte) for parte in texto.split("-", 1))
        return date(año, mes, 1)
    except (TypeError, ValueError):
        return hoy.replace(day=1)


def _seleccionar(opciones, valor: str, permitidos=None) -> str:
    """Deja solo los valores conocidos: un filtro inventado no rompe la página."""
    válidos = {v for v, _ in opciones} if permitidos is None else set(permitidos)
    return valor if valor in válidos else ""


def _barra_vistas(db, *, seccion: str, pestana: str, ruta: str, actuales: dict, vistas_activa: int = 0) -> dict:
    """Chips de vistas guardadas + lo que necesita el formulario de «guardar actual»."""
    modulo = modulo_de_vistas(seccion, pestana)
    return {
        "vistas": vistas_en_barra(db, modulo, ruta=ruta, pestana=pestana) if modulo else [],
        "vista_id": vistas_activa,
        "vista_modulo": modulo,
        "dict_filtros": filtros_json(actuales),
        "url_filtros": url_filtros(actuales),
    }


# ---------------------------------------------------------------------------
# Área 1 · Hoy (``/admin``)
# ---------------------------------------------------------------------------


@router.get("/admin", response_class=HTMLResponse, include_in_schema=False)
def pagina_hoy(request: Request, db: Session = Depends(get_operator_db)):
    """Agenda del día: qué necesita una decisión ahora, no un muro de KPIs."""
    from ..services.audit_admin import resumen_auditoria_admin
    from ..services.licencias import exigencia_licencia_activada
    from ..services.panel_admin import resumen_admin
    from ..services.panel_finanzas import resumen_financiero
    from ..services.panel_notificaciones import notificaciones_admin
    from ..services.panel_renovaciones import proximas_renovaciones

    contadores = contadores_panel(db)
    contexto = contexto_base(request, db, seccion="hoy", contadores=contadores)
    contexto.update({
        "resumen": resumen_admin(db),
        "finanzas": resumen_financiero(db),
        "proximas": proximas_renovaciones(db, limite=6),
        "eventos": resumen_auditoria_admin(db, limite=6),
        "pendientes": notificaciones_admin(db),
        "exigencia_licencias": exigencia_licencia_activada(),
        "atajos": (
            {"nombre": "Directorio de clientes", "ruta": ruta_panel("clientes"),
             "descripcion": "Buscar una empresa y abrir su ficha"},
            {"nombre": "Compras por activar", "ruta": ruta_panel("ingresos", "compras"),
             "descripcion": "Verificar comprobantes y conceder el plan"},
            {"nombre": "Renovaciones del mes", "ruta": ruta_panel("ingresos", "renovaciones"),
             "descripcion": "Avisar y renovar antes del vencimiento"},
            {"nombre": "Cobros del mes", "ruta": ruta_panel("ingresos", "cobros"),
             "descripcion": "Licencias, compras, facturas y pagos"},
            {"nombre": "Contenido de la web", "ruta": ruta_panel("web", "contenido"),
             "descripcion": "Editar la landing y publicarla"},
            {"nombre": "Equipo y roles", "ruta": ruta_panel("sistema", "equipo"),
             "descripcion": "Quién puede administrar el panel"},
        ),
    })
    return _respuesta(request, "dashboard.html", contexto)


# ---------------------------------------------------------------------------
# Área 2 · Clientes (directorio + pipeline) y ficha de cliente
# ---------------------------------------------------------------------------


def _crm_por_organizacion(db) -> dict:
    """CRM indexado por organización: el directorio lo necesita en cada fila.

    Se lee de una vez (``listar_crm`` ya trae la organización) en lugar de
    consultar por cliente: con 300 filas serían 300 consultas para pintar una
    tabla.
    """
    from ..services.web_admin import listar_crm

    try:
        return {fila["organizacion"].id: fila for fila in listar_crm(db)}
    except Exception:
        db.rollback()
        log.warning("El panel no pudo leer el CRM del canal.\n%s", _traza())
        return {}


def _traza() -> str:
    import traceback

    return traceback.format_exc()


def _estados_crm() -> list:
    from ..services.web_admin import ESTADOS_CRM, ESTADOS_CRM_ETIQUETA

    return [(clave, ESTADOS_CRM_ETIQUETA[clave]) for clave in ESTADOS_CRM]


def _resumen_crm(db) -> dict:
    from ..services.web_admin import resumen_crm

    try:
        return resumen_crm(db)
    except Exception:
        return {"total": 0, "por_estado": {}, "proximos": []}


def _filtros_guardados(db, vista_id: int) -> dict:
    """Filtros de una vista guardada, para aplicarlos desde la URL (``?vista=3``)."""
    from ..services.web_admin import listar_vistas

    if not vista_id:
        return {}
    for vista in listar_vistas(db):
        if vista.id == vista_id:
            filtros = vista.filtros_dict() or {}
            return {
                clave: str(valor)
                for clave, valor in filtros.items()
                if isinstance(valor, (str, int, float)) and clave in ("q", "estado", "plan", "crm", "tipo", "mes")
            }
    return {}


@router.get("/admin/clientes", response_class=HTMLResponse, include_in_schema=False)
def pagina_clientes(request: Request, db: Session = Depends(get_operator_db)):
    """Directorio y embudo comercial sobre las MISMAS filas (antes eran dos listas)."""
    from ..services.panel_admin import resumen_admin

    pestana = pestana_valida("clientes", _texto(request, "tab")["tab"])
    pedidos = _texto(request, "q", "estado", "plan", "crm", "orden", "dir")
    vista_id = _entero(request.query_params.get("vista"))
    guardados = _filtros_guardados(db, vista_id)
    filtros = {**guardados, **{k: v for k, v in pedidos.items() if v}}
    filtros["vista"] = str(vista_id) if vista_id else ""
    filtros["orden"] = pedidos["orden"] or "nombre"
    filtros["dir"] = "desc" if pedidos["dir"] == "desc" else "asc"
    filtros["estado"] = _seleccionar(ESTADOS_ACCESO, filtros.get("estado", ""))
    filtros["plan"] = _seleccionar(FILTROS_PLAN, filtros.get("plan", ""))
    filtros["crm"] = _seleccionar(
        _opciones_crm(),
        filtros.get("crm", ""),
        permitidos={"", "sin_asignar", *(clave for clave, _ in _estados_crm())},
    )

    crm_por_org = _crm_por_organizacion(db)
    resumen = resumen_admin(db)
    visibles = filtrar_filas(
        resumen["filas"],
        q=filtros.get("q", ""),
        estado=filtros.get("estado", ""),
        plan=filtros.get("plan", ""),
        crm=filtros.get("crm", ""),
        crm_por_org=crm_por_org,
    )
    visibles = ordenar_filas(visibles, filtros["orden"], filtros["dir"])
    resumen = {
        **resumen,
        "filas": visibles,
        "totales": {**resumen["totales"], "filtradas": len(visibles)},
    }

    ruta = ruta_panel("clientes")
    actuales = {
        "tab": pestana,
        **{k: v for k, v in filtros.items() if v and k not in ("vista", "orden", "dir")},
    }
    contexto = contexto_base(request, db, seccion="clientes", pestana=pestana)
    contexto.update({
        "resumen": resumen,
        "crm_por_org": crm_por_org,
        "pipeline": _tablero_pipeline(crm_por_org, visibles),
        "columnas_pipeline": _estados_crm() + [("", "Sin asignar")],
        "descripciones_crm": DESCRIPCIONES_CRM,
        "resumen_crm": _resumen_crm(db),
        "estados_crm": _estados_crm(),
        "opciones_estado": ESTADOS_ACCESO,
        "opciones_plan": FILTROS_PLAN,
        "opciones_crm": _opciones_crm(),
        "q": filtros.get("q", ""),
        "filtro_estado": filtros.get("estado", ""),
        "filtro_plan": filtros.get("plan", ""),
        "filtro_crm": filtros.get("crm", ""),
        "orden": filtros["orden"],
        "dir": filtros["dir"],
        "etiquetas_orden": ORDENES,
        "hay_filtros": any(filtros.get(k) for k in ("q", "estado", "plan", "crm", "vista")),
        "filtros_activos": _filtros_como_etiquetas(filtros),
        "ruta_filtro": enlace_filtro(ruta, actuales),
        "enlace_orden": enlace_orden(ruta, actuales),
        "actuales": actuales,
    })
    contexto.update(
        _barra_vistas(db, seccion="clientes", pestana=pestana, ruta=ruta,
                      actuales=actuales, vistas_activa=vista_id)
    )
    return _respuesta(request, "clientes.html", contexto)


def _opciones_crm() -> list:
    return [("", "Cualquier estado comercial"), ("sin_asignar", "Sin asignar")] + _estados_crm()


def _filtros_como_etiquetas(filtros: dict) -> dict:
    """Resumen legible de lo filtrado, para el badge de la cabecera."""
    etiquetas = dict(ESTADOS_ACCESO) | dict(FILTROS_PLAN) | dict(_opciones_crm())
    salida = {}
    for clave, nombre in (("estado", "Acceso"), ("plan", "Plan"), ("crm", "Comercial")):
        valor = filtros.get(clave) or ""
        if valor:
            salida[nombre] = etiquetas.get(valor, valor)
    if filtros.get("q"):
        salida["Texto"] = filtros["q"]
    return salida


def _tablero_pipeline(crm_por_org: dict, filas) -> dict:
    """Reparte las filas visibles por estado comercial, con su acceso al lado."""
    hoy = date.today()
    columnas: dict[str, list] = {clave: [] for clave, _ in _estados_crm()}
    columnas[""] = []
    for fila in filas:
        org = fila["organizacion"]
        crm = crm_por_org.get(org.id) or {}
        proximo = crm.get("proximo_contacto")
        vigente = fila.get("vigente")
        if vigente and fila.get("vence"):
            acceso = f"vence {fila['vence']:%d/%m/%Y}"
        elif vigente:
            acceso = "activo"
        else:
            acceso = ""
        columnas.setdefault(crm.get("estado", ""), []).append({
            "organizacion": org,
            "acceso": acceso,
            "ingresos": fila.get("ingresos", 0),
            "proximo_contacto": proximo.isoformat() if proximo else "",
            "vence_hoy": bool(proximo and proximo <= hoy),
            "notas": crm.get("notas", ""),
        })
    return columnas


@router.get("/admin/clientes.csv", include_in_schema=False)
def exportar_clientes_csv(request: Request, db: Session = Depends(get_operator_db)):
    """CSV del directorio **con los filtros activos** (antes exportaba siempre todo)."""
    from ..services.panel_admin import resumen_admin

    pedidos = _texto(request, "q", "estado", "plan", "crm")
    crm_por_org = _crm_por_organizacion(db)
    filas = filtrar_filas(
        resumen_admin(db)["filas"],
        q=pedidos["q"],
        estado=pedidos["estado"],
        plan=pedidos["plan"],
        crm=pedidos["crm"],
        crm_por_org=crm_por_org,
    )
    contenido = [[
        "Cliente", "Slug", "Emails", "Estado", "Plan", "Inicio", "Vence", "Días",
        "Ingresos US$", "Estado comercial", "Próximo contacto", "Compras pendientes",
    ]]
    for fila in filas:
        org = fila["organizacion"]
        crm = crm_por_org.get(org.id) or {}
        contenido.append([
            org.nombre,
            org.slug,
            " ".join(fila.get("emails") or []),
            fila.get("estado_label", ""),
            fila.get("plan_label") or "",
            f"{fila['inicio']:%Y-%m-%d}" if fila.get("inicio") else "",
            f"{fila['vence']:%Y-%m-%d}" if fila.get("vence") else "",
            str(fila.get("dias_restantes", "")),
            f"{fila.get('ingresos', 0):.2f}",
            crm.get("estado_etiqueta", "") if crm else "",
            f"{crm['proximo_contacto']:%Y-%m-%d}" if crm and crm.get("proximo_contacto") else "",
            str(len(fila.get("compras_pendientes") or [])),
        ])
    return _csv_response(contenido, "clientes.csv")


@router.get("/admin/clientes/{organizacion_id}", response_class=HTMLResponse, include_in_schema=False)
def pagina_ficha_cliente(organizacion_id: int, request: Request, db: Session = Depends(get_operator_db)):
    """Ficha del cliente en cinco pestañas (antes: ocho tarjetas apiladas)."""
    from ..services.panel_admin import ETIQUETA_ORIGEN, PLAN_POR_IMPORTE
    from ..services.panel_clientes import resumen_cliente

    ficha = resumen_cliente(db, organizacion_id)
    if ficha is None:
        return _redirect_cliente_inexistente()
    pestana = pestana_ficha_valida(_texto(request, "tab")["tab"])

    vigente = ficha.get("vigente")
    if vigente is None:
        plan_label = "—"
    elif vigente.origen == "pago":
        plan_label = PLAN_POR_IMPORTE.get(round(vigente.importe, 2), "Pago")
    else:
        plan_label = ETIQUETA_ORIGEN.get(vigente.origen, vigente.origen)

    hoy = date.today()
    contexto = contexto_base(request, db, seccion="clientes")
    contexto.update({
        "pestanas": _pestanas_ficha(organizacion_id, pestana),
        "pestana": pestana,
        "pestana_nombre": _nombre_ficha(pestana),
        "cabecera": {"titulo": "", "subtitulo": "", "migas": [], "seccion": "clientes"},
        "ficha": ficha,
        "plan_label": plan_label,
        "crm": _crm_por_organizacion(db).get(organizacion_id),
        "estados_crm": _estados_crm(),
        "proximos_contactos": [
            fila
            for fila in _crm_por_organizacion(db).values()
            if fila.get("proximo_contacto") and fila["proximo_contacto"] <= hoy
        ][:20],
    })
    return _respuesta(request, "cliente_detalle.html", contexto)


def _redirect_cliente_inexistente() -> RedirectResponse:
    from .common import _redirect

    return _redirect(ruta_panel("clientes"), error="El cliente indicado no existe.")


def _pestanas_ficha(organizacion_id: int, activa: str) -> list[dict]:
    from ..panel_arquitectura import ficha_pestanas_panel

    return ficha_pestanas_panel(organizacion_id, activa)


def _nombre_ficha(pestana: str) -> str:
    from ..panel_arquitectura import FICHA_PESTANAS

    for definida in FICHA_PESTANAS:
        if definida.id == pestana:
            return definida.nombre
    return ""


# ---------------------------------------------------------------------------
# Área 3 · Ingresos (renovaciones, compras, cobros, contratos)
# ---------------------------------------------------------------------------


@router.get("/admin/ingresos", response_class=HTMLResponse, include_in_schema=False)
def pagina_ingresos(request: Request, db: Session = Depends(get_operator_db)):
    """Lo que vence, lo que espera, lo que se cobró y lo contratado."""
    pedidos = _texto(request, "tab")
    pestana = pestana_valida("ingresos", pedidos["tab"])
    contexto = _constructor[pestana](request, db, pestana)
    return _respuesta(request, "ingresos.html", contexto)


def _base_ingresos(request: Request, db, pestana: str, actuales: dict, vistas_activa: int = 0) -> dict:
    ruta = ruta_panel("ingresos")
    contexto = contexto_base(request, db, seccion="ingresos", pestana=pestana)
    contexto.update({
        "ruta_filtro": enlace_filtro(ruta, actuales),
        "actuales": actuales,
    })
    contexto.update(
        _barra_vistas(db, seccion="ingresos", pestana=pestana, ruta=ruta,
                      actuales=actuales, vistas_activa=vistas_activa)
    )
    return contexto


def _ingresos_renovaciones(request: Request, db, pestana: str) -> dict:
    from ..services.panel_renovaciones import renovaciones_del_mes

    mes = _mes(request.query_params.get("mes"))
    datos = renovaciones_del_mes(db, mes=mes)
    estado = _seleccionar(RENOVACION_ESTADOS, _texto(request, "estado")["estado"])
    contadores = {
        "": datos["total"],
        "por_renovar": datos["por_renovar"],
        "vencida": sum(1 for fila in datos["filas"] if fila["estado"] == "vencida"),
        "activa": sum(1 for fila in datos["filas"] if fila["estado"] == "activa"),
    }
    filas = [f for f in datos["filas"] if not estado or f["estado"] == estado]
    actuales = {"tab": pestana, "mes": mes.strftime("%Y-%m")}
    if estado:
        actuales["estado"] = estado
    contexto = _base_ingresos(request, db, pestana, actuales)
    contexto.update({
        "renovaciones": {**datos, "filas": filas},
        "periodo": periodo_mes(mes, ruta=ruta_panel("ingresos"), pestana=pestana, actuales=actuales),
        "opciones_estado": opciones_con_contadores(contadores, RENOVACION_ESTADOS),
        "chips_estado": chips(ruta_panel("ingresos"), actuales, RENOVACION_ESTADOS, "estado", contadores),
        "filtro_estado": estado,
        "avisos_hoy": sum(1 for fila in datos["filas"] if fila.get("avisado_hoy")),
    })
    return contexto


def _ingresos_compras(request: Request, db, pestana: str) -> dict:
    from ..services.compras import resumen_compras

    pedidos = _texto(request, "estado")
    estado = pedidos["estado"] or "pendiente"
    if estado not in {clave for clave, _ in ESTADOS_COMPRA}:
        estado = "pendiente"
    compra_id = _entero(request.query_params.get("compra"))
    todas = resumen_compras(db)
    contadores = {"todas": len(todas)}
    for clave, _ in ESTADOS_COMPRA:
        if clave != "todas":
            contadores[clave] = sum(1 for fila in todas if fila["compra"].estado == clave)
    visibles = [
        fila for fila in todas
        if (estado == "todas" or fila["compra"].estado == estado)
        and (not compra_id or fila["compra"].id == compra_id)
    ]
    actuales = {"tab": pestana, "estado": estado}
    if compra_id:
        actuales["compra"] = str(compra_id)
    contexto = _base_ingresos(request, db, pestana, actuales)
    contexto.update({
        "compras": visibles,
        "compra_concreta": compra_id or None,
        "filtro_estado": estado,
        "opciones_estado": opciones_con_contadores(contadores, ESTADOS_COMPRA),
        "chips_estado": chips(ruta_panel("ingresos"), actuales, ESTADOS_COMPRA, "estado", contadores),
        "etiqueta_estado": dict(ESTADOS_COMPRA),
    })
    return contexto


def _ingresos_cobros(request: Request, db, pestana: str) -> dict:
    from ..services.panel_cobros import resumen_cobros

    mes = _mes(request.query_params.get("mes"))
    datos = resumen_cobros(db, mes=mes)
    tipo = _seleccionar(TIPOS_COBRO, _texto(request, "tipo")["tipo"])
    contadores = {"": len(datos["movimientos"])}
    for clave, _ in TIPOS_COBRO:
        if clave:
            contadores[clave] = sum(1 for m in datos["movimientos"] if m["tipo"] == clave)
    movimientos = [m for m in datos["movimientos"] if not tipo or m["tipo"] == tipo]
    actuales = {"tab": pestana, "mes": mes.strftime("%Y-%m")}
    if tipo:
        actuales["tipo"] = tipo
    contexto = _base_ingresos(request, db, pestana, actuales)
    contexto.update({
        "cobros": {**datos, "movimientos": movimientos},
        "periodo": periodo_mes(mes, ruta=ruta_panel("ingresos"), pestana=pestana, actuales=actuales),
        "opciones_tipo": opciones_con_contadores(contadores, TIPOS_COBRO),
        "chips_estado": chips(ruta_panel("ingresos"), actuales, TIPOS_COBRO, "tipo", contadores),
        "filtro_tipo": tipo,
        "etiquetas_tipo": ETIQUETAS_TIPO_COBRO,
        "etiquetas_estado": ETIQUETAS_ESTADO_COBRO,
        "etiquetas_badge": BADGES_TIPO_COBRO,
    })
    return contexto


def _ingresos_contratos(request: Request, db, pestana: str) -> dict:
    from ..services.licencias import exigencia_licencia_activada
    from ..services.panel_admin import resumen_admin

    pedidos = _texto(request, "q", "estado")
    estado = _seleccionar(ESTADOS_ACCESO, pedidos["estado"])
    visibles = ordenar_filas(
        filtrar_filas(resumen_admin(db)["filas"], q=pedidos["q"], estado=estado),
        "vence",
        "asc",
    )
    actuales = {"tab": pestana}
    if pedidos["q"]:
        actuales["q"] = pedidos["q"]
    if estado:
        actuales["estado"] = estado
    contexto = _base_ingresos(request, db, pestana, actuales)
    contexto.update({
        "resumen": {"filas": visibles, "totales": _totales_contratos(visibles), "hoy": date.today()},
        "totales": _totales_contratos(visibles),
        "exigencia_licencias": exigencia_licencia_activada(),
        "opciones_estado": ESTADOS_ACCESO,
        "filtro_estado": estado,
        "q": pedidos["q"],
    })
    return contexto


def _totales_contratos(filas) -> dict:
    hoy = date.today()
    return {
        "organizaciones": len(filas),
        "con_licencia": sum(1 for f in filas if f.get("vigente")),
        "sin_licencia": sum(1 for f in filas if not f.get("vigente")),
        "por_vencer": sum(1 for f in filas if f.get("estado") == "por_vencer"),
        "ingresos": sum(float(f.get("ingresos") or 0) for f in filas),
        "hoy": hoy,
    }


_constructor.update({
    "renovaciones": _ingresos_renovaciones,
    "compras": _ingresos_compras,
    "cobros": _ingresos_cobros,
    "contratos": _ingresos_contratos,
})


# ---------------------------------------------------------------------------
# CSV de Ingresos: el mismo filtro, en archivo
# ---------------------------------------------------------------------------


@router.get("/admin/ingresos.csv", include_in_schema=False)
def exportar_ingresos_csv(request: Request, db: Session = Depends(get_operator_db)):
    """CSV de la pestaña activa (renovaciones, cobros o contratos)."""
    pestana = pestana_valida("ingresos", _texto(request, "tab")["tab"])
    if pestana not in _EXPORTADORES:
        pestana = "renovaciones"
    filas, nombre = _EXPORTADORES[pestana](request, db)
    return _csv_response(filas, nombre)


def _csv_renovaciones(request: Request, db):
    from ..services.panel_renovaciones import renovaciones_del_mes

    mes = _mes(request.query_params.get("mes"))
    estado = _seleccionar(RENOVACION_ESTADOS, _texto(request, "estado")["estado"])
    datos = renovaciones_del_mes(db, mes=mes)
    filas = [["Cliente", "Slug", "Vence", "Días", "Importe US$", "Origen", "Estado", "Avisado hoy"]]
    for fila in datos["filas"]:
        if estado and fila["estado"] != estado:
            continue
        filas.append([
            fila["organizacion"].nombre,
            fila["organizacion"].slug,
            f"{fila['vence']:%Y-%m-%d}",
            str(fila["dias_restantes"]),
            f"{fila['importe']:.2f}",
            fila.get("origen", ""),
            fila["estado"],
            "Sí" if fila.get("avisado_hoy") else "No",
        ])
    return filas, f"renovaciones_{datos['mes']:%Y-%m}.csv"


def _csv_cobros(request: Request, db):
    from ..services.panel_cobros import resumen_cobros

    mes = _mes(request.query_params.get("mes"))
    tipo = _seleccionar(TIPOS_COBRO, _texto(request, "tipo")["tipo"])
    datos = resumen_cobros(db, mes=mes)
    filas = [["Fecha", "Mes", "Tipo", "Número", "Cliente", "Importe", "Moneda", "Estado"]]
    for movimiento in datos["movimientos"]:
        if tipo and movimiento["tipo"] != tipo:
            continue
        filas.append([
            f"{movimiento['fecha']:%Y-%m-%d}" if movimiento.get("fecha") else "",
            f"{datos['mes']:%Y-%m}",
            movimiento["tipo"],
            movimiento["numero"],
            movimiento["organizacion_nombre"],
            f"{movimiento['importe']:.2f}",
            movimiento["moneda"],
            movimiento["estado"],
        ])
    return filas, f"cobros_{datos['mes']:%Y-%m}.csv"


def _csv_contratos(request: Request, db):
    from ..services.panel_admin import resumen_admin

    pedidos = _texto(request, "q", "estado")
    filas_clientes = filtrar_filas(
        resumen_admin(db)["filas"], q=pedidos["q"], estado=_seleccionar(ESTADOS_ACCESO, pedidos["estado"])
    )
    contenido = [[
        "Cliente", "Slug", "Estado", "Plan", "Origen", "Inicio", "Vence", "Días restantes",
        "Importe vigente", "Moneda", "Método de cobro", "Ingresos totales", "Licencias",
    ]]
    for fila in filas_clientes:
        org = fila["organizacion"]
        vigente = fila.get("vigente")
        contenido.append([
            org.nombre,
            org.slug,
            fila.get("estado_label", ""),
            fila.get("plan_label") or "",
            vigente.origen if vigente else "",
            f"{fila['inicio']:%Y-%m-%d}" if fila.get("inicio") else "",
            f"{fila['vence']:%Y-%m-%d}" if fila.get("vence") else "",
            str(fila.get("dias_restantes", "")),
            f"{vigente.importe:.2f}" if vigente else "",
            vigente.moneda if vigente else "",
            vigente.metodo_cobro if vigente else "",
            f"{fila.get('ingresos', 0):.2f}",
            str(len(fila.get("licencias") or [])),
        ])
    return contenido, "contratos.csv"


def _csv_compras(request: Request, db):
    """La cola de verificación, con lo que hace falta para decidir.

    No había CSV de compras: exportar la cola significaba descargar el histórico
    y cruzarlo a mano con los comprobantes. Va con el mismo filtro por estado que
    la pestaña, por eso mismo.
    """
    from ..services.compras import resumen_compras

    estado = _texto(request, "estado")["estado"] or "pendiente"
    if estado not in {clave for clave, _ in ESTADOS_COMPRA}:
        estado = "pendiente"
    filas = [["Compra", "Cliente", "Plan", "Método", "Importe", "Moneda", "Estado",
              "Fecha", "Verificación", "Comprobante"]]
    for fila in resumen_compras(db):
        compra = fila["compra"]
        if estado != "todas" and compra.estado != estado:
            continue
        verificacion = fila.get("verificacion") or {}
        filas.append([
            str(compra.id),
            fila["organizacion_nombre"],
            fila["plan_nombre"],
            fila["metodo_nombre"],
            f"{compra.importe:.2f}",
            compra.moneda,
            compra.estado,
            f"{compra.created_at:%Y-%m-%d %H:%M}" if compra.created_at else "",
            "; ".join(f"{k}: {v}" for k, v in verificacion.items() if v),
            compra.comprobante_nombre or "",
        ])
    return filas, "compras.csv"


_EXPORTADORES = {
    "renovaciones": _csv_renovaciones,
    "cobros": _csv_cobros,
    "compras": _csv_compras,
    "contratos": _csv_contratos,
}


@router.get("/admin/renovaciones.csv", include_in_schema=False)
def exportar_renovaciones_csv(request: Request, db: Session = Depends(get_operator_db)):
    """URL histórica: mismo CSV, mismo filtro (enlaces ya repartidos)."""
    filas, nombre = _csv_renovaciones(request, db)
    return _csv_response(filas, nombre)


@router.get("/admin/cobros.csv", include_in_schema=False)
def exportar_cobros_csv(request: Request, db: Session = Depends(get_operator_db)):
    filas, nombre = _csv_cobros(request, db)
    return _csv_response(filas, nombre)


# ---------------------------------------------------------------------------
# Área 4 · Web (contenido, avisos y versiones)
# ---------------------------------------------------------------------------


@router.get("/admin/web", response_class=HTMLResponse, include_in_schema=False)
def pagina_web(request: Request, db: Session = Depends(get_operator_db)):
    """La web del producto se edita y se publica desde un solo sitio."""
    from ..services.web_admin import listar_contenido

    pestana = pestana_valida("web", _texto(request, "tab")["tab"])
    contexto = contexto_base(request, db, seccion="web", pestana=pestana)
    if pestana == "contenido":
        contexto.update(_web_contenido(db, listar_contenido(db)))
    elif pestana == "avisos":
        contexto.update(_web_avisos(db))
    else:
        contexto.update(_web_versiones(db))
    return _respuesta(request, "web.html", contexto)


def _web_contenido(db, contenido) -> dict:
    """JSON de cada clave, preformateado y con el estado «hay borrador sin publicar».

    El ``json.dumps`` y la comparación borrador/publicado se hacen aquí para que
    la plantilla no tenga que saber de sangrías ni de dicts: solo pinta.
    """
    pendientes = 0
    filas = []
    for item in contenido:
        borrador = item.get("borrador") or {}
        publicado = item.get("publicado") or {}
        texto = json.dumps(borrador, ensure_ascii=False, indent=2) if borrador else "{}"
        pendiente = bool(borrador) and borrador != publicado
        pendientes += 1 if pendiente else 0
        filas.append({
            **item,
            "borrador_texto": texto,
            # Un textarea demasiado alto es tan inútil como uno de dos líneas.
            "filas": max(6, min(22, texto.count("\n") + 2)),
            "campos": sorted(set(borrador) | set(publicado)),
            "pendiente": pendiente,
        })
    return {"contenido": filas, "pendientes_publicar": pendientes}


def _web_avisos(db) -> dict:
    from ..services.web_admin import NIVELES_AVISO, TIPOS_AVISO, listar_avisos

    hoy = date.today()
    avisos = []
    visibles = 0
    for aviso in listar_avisos(db):
        en_ventana = (not aviso.inicio or aviso.inicio <= hoy) and (not aviso.fin or aviso.fin >= hoy)
        if aviso.activo and en_ventana:
            visibles += 1
        avisos.append({
            "id": aviso.id,
            "tipo": aviso.tipo,
            "nivel": aviso.nivel,
            "titulo": aviso.titulo,
            "mensaje": aviso.mensaje or "",
            "inicio": aviso.inicio,
            "fin": aviso.fin,
            "activo": bool(aviso.activo),
            "en_ventana": en_ventana,
        })
    return {
        "avisos": avisos,
        "visibles": visibles,
        "tipos": list(TIPOS_AVISO),
        "niveles": list(NIVELES_AVISO),
    }


def _web_versiones(db) -> dict:
    from ..services.web_admin import listar_releases

    releases = listar_releases(db)
    return {"releases": releases, "publicadas": sum(1 for r in releases if r.publicado)}


# ---------------------------------------------------------------------------
# Área 5 · Analítica
# ---------------------------------------------------------------------------


@router.get("/admin/analitica", response_class=HTMLResponse, include_in_schema=False)
def pagina_analitica(request: Request, dias: int = 30, db: Session = Depends(get_operator_db)):
    """Analítica de producto medida en el servidor (E5-012).

    La ventana se valida aquí: ``dias`` acaba en una consulta SQL y no puede
    venir de cualquier valor que escriba el navegador.
    """
    from ..services.analitica import resumen_analitica

    ventana = dias if dias in (7, 30, 90) else 30
    contexto = contexto_base(request, db, seccion="analitica")
    contexto.update({"resumen": resumen_analitica(db, dias=ventana), "dias": ventana})
    return _respuesta(request, "analitica.html", contexto)


# ---------------------------------------------------------------------------
# Área 6 · Sistema (estado, automatizaciones, datos, equipo, accesos, auditoría, correos)
# ---------------------------------------------------------------------------


def contexto_sistema(
    request: Request,
    db,
    *,
    pestana: str = "",
    msg: str = "",
    error: str = "",
    extra: dict | None = None,
) -> dict:
    """Contexto de Sistema. Lo reutilizan las acciones de ``admin.py`` (API keys).

    Antes cada bloque tenía su página —y su copia del menú—; ahora son pestañas
    del mismo área y comparten el constructor de contexto.
    """
    activa = pestana_valida("sistema", pestana)
    contexto = contexto_base(request, db, seccion="sistema", pestana=activa, msg=msg, error=error)
    try:
        _RELLENOS[activa](request, db, contexto)
    except Exception:
        db.rollback()
        log.exception("El panel no pudo montar la pestaña «%s» de Sistema.", activa)
        contexto["error"] = error or (
            "No se pudo leer este bloque. Revisa la configuración de la base y vuelve a intentarlo."
        )
    if extra:
        contexto.update(extra)
    return contexto


def _sistema_estado(request: Request, db, contexto: dict) -> None:
    from ..services.licencias import exigencia_licencia_activada
    from ..services.operacion import diagnostico_operacion

    contexto.update({
        "diagnostico": diagnostico_operacion(),
        "notas_chequeos": NOTAS_CHEQUEOS,
        "exigencia_licencias": exigencia_licencia_activada(),
    })


def _sistema_automatizaciones(request: Request, db, contexto: dict) -> None:
    from ..routers.admin import CRON_MANTENIMIENTO_PATH, CRON_RECORDATORIOS_PATH
    from ..services.automatizaciones_admin import REGLAS, estado_automatizaciones

    contexto.update({
        "reglas": REGLAS,
        "estado": estado_automatizaciones(db),
        "cron_recordatorios": CRON_RECORDATORIOS_PATH,
        "cron_mantenimiento": CRON_MANTENIMIENTO_PATH,
    })


def _sistema_datos(request: Request, db, contexto: dict) -> None:
    from ..config import resumen_configuracion
    from ..services.salud_catalogo import analizar_salud_catalogo

    try:
        salud = analizar_salud_catalogo(db, incluir_anomalias=True)
    except Exception:
        db.rollback()
        # Sin contexto de organización el análisis de catálogo puede fallar: se
        # explica en la pantalla en vez de dejar el panel en rojo.
        salud = {"error": "No se pudo auditar el catálogo en este contexto."}
    contexto.update({
        "salud": salud,
        "config": resumen_configuracion(),
        "etiquetas_problemas": ETIQUETAS_PROBLEMAS,
    })


def _sistema_equipo(request: Request, db, contexto: dict) -> None:
    from ..models import ROLES_OPERADOR, ROLES_OPERADOR_ETIQUETA
    from ..services.operadores_admin import listar_operadores

    operadores = listar_operadores(db)
    rol_actual = str(db.info.get("operador_rol") or "").lower()
    contexto.update({
        "operadores": operadores,
        "roles": [(rol, ROLES_OPERADOR_ETIQUETA[rol]) for rol in ROLES_OPERADOR],
        "rol_actual": rol_actual,
        "es_superadmin": rol_actual == "superadmin",
        "superadmins": sum(1 for op in operadores if op["rol"] == "superadmin" and op["activo"]),
        "suspendidos": sum(1 for op in operadores if not op["activo"]),
        "desde_env": sum(1 for op in operadores if op["origen"] != "tabla"),
        "alcances_rol": ALCANCES_ROL,
    })


def _sistema_accesos(request: Request, db, contexto: dict) -> None:
    from ..services.web_admin import listar_api_keys, listar_flags

    contexto.update({
        "flags": listar_flags(db),
        "claves": listar_api_keys(db),
        "token_nuevo": "",
    })


def _sistema_auditoria(request: Request, db, contexto: dict) -> None:
    from ..services.audit_admin import (
        ACCIONES_LECIBLES,
        RESULTADOS_AUDITORIA,
        resumen_auditoria_admin,
    )

    pedidos = _texto(request, "actor", "accion", "resultado")
    organizacion_id = _entero(request.query_params.get("organizacion_id"))
    accion = _seleccionar(ACCIONES_LECIBLES.items(), pedidos["accion"])
    eventos = resumen_auditoria_admin(
        db,
        actor=pedidos["actor"],
        accion=accion,
        resultado=_seleccionar(RESULTADOS_AUDITORIA, pedidos["resultado"]),
        organizacion_id=organizacion_id or None,
        limite=250,
    )
    contexto.update({
        "eventos": eventos,
        "acciones": sorted(ACCIONES_LECIBLES.items()),
        "etiquetas_acciones": ACCIONES_LECIBLES,
        "resultados": list(RESULTADOS_AUDITORIA),
        "filtros": {
            "actor": pedidos["actor"],
            "accion": accion,
            "resultado": pedidos["resultado"],
            "organizacion_id": organizacion_id,
        },
        "filtros_activos": any(pedidos.values()) or bool(organizacion_id),
    })


def _sistema_correos(request: Request, db, contexto: dict) -> None:
    from ..services.correos_prueba import catalogo_correos

    contexto.update({
        "correos": catalogo_correos(),
        # El destino queda en la URL para que, tras el envío, el formulario no
        # vuelva a vacío (el operador repite destino a mano).
        "destino": _texto(request, "destino")["destino"] or str(db.info.get("auth_email") or ""),
    })


_RELLENOS = {
    "estado": _sistema_estado,
    "automatizaciones": _sistema_automatizaciones,
    "datos": _sistema_datos,
    "equipo": _sistema_equipo,
    "accesos": _sistema_accesos,
    "auditoria": _sistema_auditoria,
    "correos": _sistema_correos,
}

#: Explicaciones de los problemas de catálogo que devuelve `analizar_salud_catalogo`.
ETIQUETAS_PROBLEMAS = {
    "sin_precio": "Aparecen en el catálogo pero no se pueden presupuestar.",
    "sin_coste": "Sin coste no hay margen visible: se cobra a ciegas.",
    "margen_bajo": "Por debajo del mínimo considerado razonable.",
    "sin_tiempo": "No se puede planificar la ejecución.",
    "desactualizadas": "Precio sin revisar desde hace demasiado.",
    "precio_absurdo": "Fuera del rango del país: casi siempre una conversión mal aplicada.",
}


@router.get("/admin/sistema", response_class=HTMLResponse, include_in_schema=False)
def pagina_sistema(request: Request, db: Session = Depends(get_operator_db)):
    contexto = contexto_sistema(request, db, pestana=_texto(request, "tab")["tab"])
    return _respuesta(request, "sistema.html", contexto)


# ---------------------------------------------------------------------------
# URLs antiguas → pestaña correspondiente
# ---------------------------------------------------------------------------
#
# El panel tuvo 21 entradas de menú. Las páginas que se fusionaron siguen
# respondiendo con un 302 a su pestaña, para que no queden enlaces muertos en
# favoritos, en el correo de una notificación o en las notas internas del
# equipo. Los parámetros se reenvían (salvo ``tab``, que es el que se sustituye),
# de modo que ``/admin/cobros?mes=2026-07`` aterriza en el mismo mes.


def _redireccion_area(destino_original: str):
    def redireccion(request: Request):
        nuevo = redireccion_de(destino_original) or ruta_panel("hoy")
        ruta, _, consulta = nuevo.partition("?")
        fijos = [parte for parte in consulta.split("&") if parte]
        reenviados = [
            parte for parte in str(request.query_params or "").split("&")
            if parte and not parte.lower().startswith("tab=")
        ]
        unida = "&".join([*fijos, *reenviados])
        respuesta = RedirectResponse(f"{ruta}?{unida}" if unida else ruta, status_code=302)
        respuesta.headers["Cache-Control"] = "no-store"
        return respuesta

    return redireccion


def _montar_redirecciones() -> None:
    for antigua in sorted(RUTAS_ANTIGUAS):
        router.add_api_route(
            antigua,
            _redireccion_area(antigua),
            methods=["GET"],
            include_in_schema=False,
            response_class=HTMLResponse,
        )


_montar_redirecciones()
