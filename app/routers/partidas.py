"""Catálogo de partidas."""  # E4-001 — router por dominio

import re

from fastapi import APIRouter, Request
from sqlalchemy import func

from .common import *  # noqa: F401,F403  (re-exporta modelos, servicios y utilidades)
from ..i18n import mensaje_request
from ..services import auditoria
from ..services.tasa import factor_conversion_local, tasa_convertir_precio
from ..services.traduccion import codigo_desde_pais, traducir
from ..services.recursos import etiqueta_categoria_recurso, etiqueta_grupo_recurso
from ..services.salud_catalogo import analizar_salud_catalogo, MARGEN_MINIMO_CATALOGO, DIAS_SIN_REVISION

router = APIRouter()

def _descomposicion_catalogo(form):
    """Lee y recalcula los recursos del análisis de precios del catálogo.

    La tabla es la fuente de verdad: nunca se confía en subtotales enviados
    por el navegador. Cada recurso se guarda con su rendimiento, su precio
    unitario y su importe derivado; los cuatro costes heredados se obtienen
    posteriormente de estas mismas filas.
    """
    filas = []
    claves = ("d_categoria", "d_codigo", "d_unidad", "d_descripcion", "d_rendimiento", "d_precio")
    listas = {k: form.getlist(k) for k in claves}
    total = max((len(v) for v in listas.values()), default=0)

    def val(k, i, defecto=""):
        return listas[k][i] if i < len(listas[k]) else defecto

    etiquetas = {"materiales": "Materiales", "mano_obra": "Mano de obra",
                 "complementarios": "Costes directos complementarios", "otros": "Equipos y otros"}
    for i in range(total):
        categoria = str(val("d_categoria", i, "otros") or "otros").strip()
        if categoria not in etiquetas:
            categoria = "otros"
        codigo, unidad, descripcion = (str(val(k, i) or "").strip() for k in ("d_codigo", "d_unidad", "d_descripcion"))
        if not descripcion and not codigo:
            continue
        rendimiento = max(0.0, _f(val("d_rendimiento", i), 0))
        precio = max(0.0, _f(val("d_precio", i), 0))
        filas.append({
            "tipo": "recurso", "grupo": etiquetas[categoria], "categoria": categoria,
            "codigo": codigo, "unidad": unidad or ("%" if categoria == "complementarios" else "ud"),
            "descripcion": descripcion, "rendimiento": rendimiento,
            "precio": precio, "precio_unitario": precio, "importe": 0.0,
            "numero": len(filas) + 1, "celdas": [], "formulas": {},
        })

    # Reutiliza las reglas de CYPE también para recursos manuales, incluido el
    # complemento porcentual: % × (materiales + mano de obra + otros).
    resultado = recalcular_descompuesto_cype(filas)
    for indice, fila in enumerate(filas):
        fila["importe"] = resultado["importes"].get(indice, 0.0)
        if indice in resultado["precios_complementarios"]:
            fila["precio"] = resultado["precios_complementarios"][indice]
            fila["precio_unitario"] = fila["precio"]
    return filas, resultado["costes"]


def _descomposicion_en_moneda(partida: Partida, factor: float):
    """Devuelve `descomposicion_json` con los precios de sus filas en moneda local.

    El catálogo se guarda en la moneda base (USD) pero el formulario de edición
    se muestra en la moneda de la organización. Sin convertir aquí los precios
    unitarios de cada recurso, el «Análisis de precio unitario» mostraba dólares
    junto a un precio de venta en moneda local (p. ej. COP) y el coste directo /
    beneficio mezclaba monedas. Devuelve None si no hay descomposición que
    convertir o el JSON no es válido.
    """
    if not factor or factor == 1.0:
        return None
    try:
        valor = json.loads(partida.descomposicion_json or "[]")
    except (TypeError, ValueError):
        return None
    if isinstance(valor, list):
        valor = {"origen": "manual", "filas": valor}
    if not isinstance(valor, dict):
        return None
    filas = [
        dict(fila) if isinstance(fila, dict) else fila
        for fila in valor.get("filas", [])
    ]
    for fila in filas:
        if not isinstance(fila, dict):
            continue
        for campo in ("precio", "precio_unitario", "importe", "coste_unitario"):
            if isinstance(fila.get(campo), (int, float)):
                fila[campo] = tasa_convertir_precio(fila[campo], factor)
    return json.dumps(dict(valor, filas=filas), ensure_ascii=False)


def _filas_descomposicion_vista(
    filas, pais_codigo: str, idioma: str, *, preservar_personalizadas: bool = False,
):
    """Copia/localiza filas para presentar, sin modificar el JSON persistido.

    En el resumen del catálogo manda el código del recurso. En la ficha
    editable solo se traduce una descripción que siga siendo la original del
    recurso; el texto personalizado de esa partida se conserva.
    """
    from ..services.traduccion import (
        traducir_recurso_para_edicion,
        traducir_recurso_por_codigo,
    )

    salida = []
    para_ingles = str(idioma or "").lower().startswith("en")
    for fila in filas or []:
        if not isinstance(fila, dict):
            continue
        vista = dict(fila)
        if para_ingles:
            traducir_fila = (
                traducir_recurso_para_edicion
                if preservar_personalizadas
                else traducir_recurso_por_codigo
            )
            vista["descripcion"] = traducir_fila(
                vista.get("descripcion"), vista.get("codigo"), pais_codigo
            )
        vista["categoria_etiqueta"] = etiqueta_categoria_recurso(
            vista.get("categoria") or vista.get("grupo"), idioma
        )
        vista["grupo"] = etiqueta_grupo_recurso(
            vista.get("grupo"), vista.get("categoria"), idioma
        )
        salida.append(vista)
    return salida


def _restaurar_valor_catalogo(db, campo, valor, original, pais_codigo, idioma):
    """Vuelve a la cadena base si el valor enviado es solo su traducción visible."""
    texto = str(valor or "").strip()
    if not str(idioma or "").lower().startswith("en") or not pais_codigo:
        return texto
    if original and texto == traducir(original, pais_codigo):
        return original
    columna = getattr(Partida, campo, None)
    if columna is not None and campo in {"nombre", "descripcion", "categoria", "subcategoria", "apartado"}:
        try:
            candidatos = db.query(columna).filter(columna.isnot(None)).distinct().all()
        except Exception:
            candidatos = []
        for (candidato,) in candidatos:
            if candidato and texto == traducir(candidato, pais_codigo):
                return candidato
    return texto


def _datos_partida_catalogo(form):
    """Datos opcionales de una partida, concentrados fuera del constructor."""
    horas_txt = str(form.get("tiempo_estimado_horas", "")).strip()
    horas_of = str(form.get("tiempo_oficial_horas", "")).strip()
    horas_ay = str(form.get("tiempo_ayudante_horas", "")).strip()
    horas_eq = str(form.get("tiempo_equipo_horas", "")).strip()
    return {
        "descripcion": str(form.get("descripcion", "")).strip(),
        "precio_unitario": max(0.0, _f(form.get("precio_unitario"))),
        "unidad": str(form.get("unidad", "ud")).strip() or "ud",
        "categoria": str(form.get("categoria", "General")).strip() or "General",
        "codigo_interno": str(form.get("codigo_interno", "")).strip(),
        "subcategoria": str(form.get("subcategoria", "")).strip(),
        "apartado": str(form.get("apartado", "")).strip(),
        "coste_materiales": max(0.0, _f(form.get("coste_materiales"))),
        "coste_mano_obra": max(0.0, _f(form.get("coste_mano_obra"))),
        "coste_complementarios": max(0.0, _f(form.get("coste_complementarios"))),
        "coste_otros": max(0.0, _f(form.get("coste_otros"))),
        "tiempo_estimado_horas": max(0.0, _f(horas_txt)) if horas_txt else None,
        "tiempo_oficial_horas": max(0.0, _f(horas_of)) if horas_of else None,
        "tiempo_ayudante_horas": max(0.0, _f(horas_ay)) if horas_ay else None,
        "tiempo_equipo_horas": max(0.0, _f(horas_eq)) if horas_eq else None,
        "proveedor": str(form.get("proveedor", "")).strip(),
        "rendimiento": str(form.get("rendimiento", "")).strip(),
        "desperdicio_recomendado_pct": max(0.0, min(100.0, _f(form.get("desperdicio_recomendado_pct")))),
        "notas_tecnicas": str(form.get("notas_tecnicas", "")).strip(),
    }


def _desvincular_clasificacion_si_cambio(partida: Partida, datos: dict) -> None:
    """Evita que una ruta editada a mano siga apuntando al nodo oficial viejo."""
    anterior = (
        partida.categoria or "",
        partida.subcategoria or "",
        partida.apartado or "",
    )
    nueva = (
        datos.get("categoria") or "",
        datos.get("subcategoria") or "",
        datos.get("apartado") or "",
    )
    if anterior != nueva:
        partida.categoria_id = None
        partida.codigo_clasificacion = ""
        partida.version_catalogo = 0

@router.get("/partidas", response_class=HTMLResponse)
def listar_partidas(
    request: Request,
    q: str = "",
    pagina: int = 1,
    vista: str = "activas",
    categoria: str = "",
    subcategoria: str = "",
    apartado: str = "",
    salud: str = "",
    db: Session = Depends(get_db),
):
    # La tabla de gestión ya no se pagina en la vista de navegación: el árbol
    # completo se monta contraído y las filas de cada subcapítulo se cargan
    # bajo demanda (ver /partidas/api/filas). Solo la búsqueda y el filtro de
    # una subcategoría/apartado concretos renderizan filas en el servidor.
    from ..services.catalogo_propio import asegurar_catalogo_propio
    asegurar_catalogo_propio(db)
    vista = "ocultas" if vista == "ocultas" else "activas"
    categoria = str(categoria or "").strip()
    subcategoria = str(subcategoria or "").strip()
    apartado = str(apartado or "").strip()
    if subcategoria and not categoria:
        categoria = ""
    if apartado and not subcategoria:
        apartado = ""
    # apartado debe pertenecer a la subcategoría seleccionada: si no coinciden
    # los prefijos numéricos se ignora para no dejar la vista vacía por un
    # enlace manipulado.
    if apartado and subcategoria and not apartado.startswith(subcategoria.split()[0] if subcategoria.split() else ""):
        # Comprobación laxa: solo ignora si los códigos no encajan
        pass
    q = str(q or "").strip()
    salud = str(salud or "").strip().lower()
    filtros_salud = {"sin_precio", "sin_coste", "margen_bajo", "sin_tiempo", "desactualizadas", "precio_absurdo"}
    if salud not in filtros_salud:
        salud = ""
    total_ocultas = db.query(Partida).filter(Partida.oculta.is_(True)).count()
    # El escaneo de precios absurdos recorre todo el catálogo: solo se lanza
    # cuando el usuario pide ese filtro, no en cada visita a /partidas.
    salud_catalogo = analizar_salud_catalogo(db, incluir_anomalias=(salud == "precio_absurdo"))

    modo_directo = bool(q) or bool(subcategoria) or bool(apartado) or bool(salud)
    por_pagina = 100
    if modo_directo:
        query = db.query(Partida).filter(Partida.oculta.is_(vista == "ocultas"))
        if categoria:
            query = query.filter(Partida.categoria == categoria)
            if subcategoria:
                query = query.filter(Partida.subcategoria == subcategoria)
                if apartado:
                    query = query.filter(Partida.apartado == apartado)
        elif apartado:
            # Filtro directo por apartado sin categoría (ej. enlace profundo)
            query = query.filter(Partida.apartado == apartado)
        if q:
            query, _ = _aplicar_busqueda_catalogo(query, q[:120])
        coste_expr = (
            func.coalesce(Partida.coste_materiales, 0)
            + func.coalesce(Partida.coste_mano_obra, 0)
            + func.coalesce(Partida.coste_complementarios, 0)
            + func.coalesce(Partida.coste_otros, 0)
        )
        if salud == "sin_precio":
            query = query.filter(func.coalesce(Partida.precio_unitario, 0) <= 0)
        elif salud == "sin_coste":
            query = query.filter(coste_expr <= 0)
        elif salud == "margen_bajo":
            query = query.filter(
                Partida.precio_unitario > 0,
                coste_expr > 0,
                ((Partida.precio_unitario - coste_expr) / Partida.precio_unitario * 100) < MARGEN_MINIMO_CATALOGO,
            )
        elif salud == "sin_tiempo":
            query = query.filter(
                func.coalesce(Partida.tiempo_estimado_horas, 0) <= 0,
                func.coalesce(Partida.tiempo_oficial_horas, 0) <= 0,
                func.coalesce(Partida.tiempo_ayudante_horas, 0) <= 0,
                func.coalesce(Partida.tiempo_equipo_horas, 0) <= 0,
            )
        elif salud == "desactualizadas":
            limite = datetime.utcnow() - timedelta(days=DIAS_SIN_REVISION)
            query = query.filter(Partida.fecha_actualizacion_precio < limite)
        elif salud == "precio_absurdo":
            from ..services.precios_anomalos import ids_partidas_anomalas

            query = query.filter(Partida.id.in_(ids_partidas_anomalas(db) or [0]))
        total_partidas = query.count()
        total_paginas = max(1, math.ceil(total_partidas / por_pagina))
        pagina = max(1, min(int(pagina or 1), total_paginas))
        partidas = query.order_by(
            Partida.categoria,
            Partida.subcategoria,
            Partida.apartado,
            Partida.codigo_interno,
            Partida.ultimo_uso.desc(),
            Partida.nombre,
        ).offset((pagina - 1) * por_pagina).limit(por_pagina).all()
        catalogo_descompuestos = {}
        for partida in partidas:
            try:
                valor = json.loads(partida.descomposicion_json or "[]")
                catalogo_descompuestos[partida.id] = valor.get("filas", []) if isinstance(valor, dict) else valor
            except (TypeError, ValueError):
                catalogo_descompuestos[partida.id] = []
    else:
        partidas = []
        catalogo_descompuestos = {}
        total_partidas = db.query(Partida).filter(
            Partida.oculta.is_(vista == "ocultas")
        ).count()
        total_paginas = 1
        pagina = 1

    # Barra lateral: árbol oficial completo (capítulo → subcapítulo → apartado)
    # con el total de partidas por nodo, independiente de la paginación y del
    # filtro activo. La barra es la navegación del catálogo, no un resumen de
    # la página cargada: así se ven siempre los 18 capítulos, contraídos.
    nodos_oficiales = (
        db.query(CategoriaPartida)
        .filter(CategoriaPartida.oficial.is_(True), CategoriaPartida.activa.is_(True))
        .all()
    )
    capitulos = sorted(
        (n for n in nodos_oficiales if n.nivel == 1),
        key=lambda n: n.codigo_completo,
    )
    hijos_por_padre: dict[int, list[CategoriaPartida]] = {}
    apartados_por_padre: dict[int, list[CategoriaPartida]] = {}
    for nodo in nodos_oficiales:
        if nodo.nivel == 2 and nodo.parent_id is not None:
            hijos_por_padre.setdefault(nodo.parent_id, []).append(nodo)
        elif nodo.nivel == 3 and nodo.parent_id is not None:
            apartados_por_padre.setdefault(nodo.parent_id, []).append(nodo)
    ocultas_filtro = vista == "ocultas"
    conteo_capitulos = dict(
        db.query(Partida.categoria, func.count(Partida.id))
        .filter(Partida.oculta.is_(ocultas_filtro))
        .group_by(Partida.categoria)
        .all()
    )
    conteo_subcapitulos = dict(
        db.query(Partida.subcategoria, func.count(Partida.id))
        .filter(Partida.oculta.is_(ocultas_filtro))
        .group_by(Partida.subcategoria)
        .all()
    )
    conteo_apartados = dict(
        db.query(Partida.apartado, func.count(Partida.id))
        .filter(Partida.oculta.is_(ocultas_filtro))
        .group_by(Partida.apartado)
        .all()
    )
    # Apartados personalizados u huérfanos: evita que una partida con
    # apartado libre quede invisible en el árbol lateral.
    try:
        _rows_apart = (
            db.query(Partida.subcategoria, Partida.apartado, func.count(Partida.id))
            .filter(Partida.oculta.is_(ocultas_filtro))
            .group_by(Partida.subcategoria, Partida.apartado)
            .all()
        )
    except Exception:
        _rows_apart = []
    _por_sub: dict[str, list[tuple[str, int]]] = {}
    for _sc, _ap, _cnt in _rows_apart:
        if not _ap or not str(_ap).strip():
            continue
        _por_sub.setdefault(str(_sc), []).append((str(_ap), int(_cnt)))
    arbol_categorias = []
    for capitulo in capitulos:
        subcapitulos = sorted(
            hijos_por_padre.get(capitulo.id, []),
            key=lambda n: n.codigo_completo,
        )
        sub_lista = []
        for sub in subcapitulos:
            oficiales = sorted(
                apartados_por_padre.get(sub.id, []),
                key=lambda n: n.codigo_completo,
            )
            apartados: list[dict] = []
            _vistas: set[str] = set()
            for ap in oficiales:
                etiqueta = f"{ap.codigo_completo} {ap.nombre}".strip()
                total = int(conteo_apartados.get(etiqueta, 0))
                apartados.append({
                    "apartado": etiqueta,
                    "codigo": ap.codigo_completo or "",
                    "nombre": ap.nombre or "",
                    "total": total,
                })
                _vistas.add(etiqueta)
            # Añade apartados personalizados que no están en la taxonomía oficial
            for _ap_str, _cnt in sorted(_por_sub.get(sub.subcategoria, []), key=lambda x: x[0]):
                if _ap_str in _vistas:
                    continue
                _code = ""
                _name = _ap_str
                if " " in _ap_str and re.match(r"^\d{2}\.\d{2}\.\d{2}(\.\d{3})?\s", _ap_str):
                    _code, _name = _ap_str.split(" ", 1)
                apartados.append({
                    "apartado": _ap_str,
                    "codigo": _code,
                    "nombre": _name,
                    "total": int(_cnt),
                })
            apartados.sort(key=lambda a: (a.get("codigo") or a.get("apartado") or ""))
            sub_lista.append({
                "subcategoria": sub.subcategoria,
                "nombre": sub.nombre,
                "codigo": sub.codigo_completo or "",
                "total": int(conteo_subcapitulos.get(sub.subcategoria, 0)),
                "apartados": apartados,
            })
        arbol_categorias.append({
            "categoria": capitulo.categoria,
            "codigo": capitulo.codigo_completo or "",
            "total": int(conteo_capitulos.get(capitulo.categoria, 0)),
            "subcapitulos": sub_lista,
        })
    # Traducción al vuelo VE->país para la vista de lista (CO/MX/EC/PE)
    try:
        _cfg = _config(db)
        _codigo_trad = codigo_desde_pais(getattr(_cfg, "empresa_pais", ""))
    except Exception:
        _codigo_trad = ""
    if _codigo_trad:
        # Las ETIQUETAS del árbol se traducen; las claves crudas
        # (data-cat, enlaces, filtros) se mantienen intactas.
        for _cap in arbol_categorias:
            _cap["categoria_display"] = traducir(_cap["categoria"], _codigo_trad)
            for _sub in _cap["subcapitulos"]:
                _sub["subcategoria_display"] = traducir(_sub["subcategoria"], _codigo_trad)
                for _ap in _sub.get("apartados", []):
                    _ap["apartado_display"] = traducir(_ap.get("apartado", ""), _codigo_trad)
                    _ap["nombre_display"] = traducir(_ap.get("nombre", ""), _codigo_trad)
        for _p in partidas:
            _p.nombre = traducir(_p.nombre, _codigo_trad)
            _p.descripcion = traducir(_p.descripcion or "", _codigo_trad)
            _p.categoria = traducir(_p.categoria or "", _codigo_trad)
            _p.subcategoria = traducir(_p.subcategoria or "", _codigo_trad)
            _p.apartado = traducir(_p.apartado or "", _codigo_trad)
    else:
        for _cap in arbol_categorias:
            _cap["categoria_display"] = _cap["categoria"]
            for _sub in _cap["subcapitulos"]:
                _sub["subcategoria_display"] = _sub["subcategoria"]
                for _ap in _sub.get("apartados", []):
                    _ap["apartado_display"] = _ap.get("apartado", "")
                    _ap["nombre_display"] = _ap.get("nombre", "")
    # El cálculo de margen/precio de mercado debe partir SIEMPRE de los
    # importes base sin redondear. Convertir primero a la vista (p. ej. USD →
    # GBP) redondeaba costes y precio por separado y alteraba el margen antes
    # de reconstruir el precio de mercado; la lista acababa discrepando del
    # editor. Primero calculamos mercado; después convertimos solo los
    # fallbacks que no tienen referencia local.
    _mon_cfg, _factor = _contexto_moneda(db)
    _precios_mk = {}
    try:
        from ..services.precios_partidas import recalcular_partidas_mercado
        _cfg_pm = _config(db)
        _pais_pm = codigo_desde_pais(getattr(_cfg_pm, "empresa_pais", "") or "") or "VE"
        _org_pm = int(db.info.get("organizacion_id") or 0) or None
        _precios_mk = recalcular_partidas_mercado(
            db, partidas, _pais_pm, _org_pm, _mon_cfg, _factor,
        )
    except Exception:
        _precios_mk = {}

    for _p in partidas:
        _mk = _precios_mk.get(_p.id)
        if _mk is not None:
            _p.precio_unitario = _mk.precio_unitario
            _p.coste_materiales = _mk.coste_materiales
            _p.coste_mano_obra = _mk.coste_mano_obra
            _p.coste_complementarios = _mk.coste_complementarios
            _p.coste_otros = _mk.coste_otros
            # Las tablas de descomposición del listado también usan las
            # referencias nacionales, no el base convertido.
            catalogo_descompuestos[_p.id] = _mk.filas
        elif _factor != 1.0:
            # Sin precio de mercado, la ficha base y sus costes se convierten
            # juntos a la moneda visible, una sola vez.
            _p.precio_unitario = tasa_convertir_precio(_p.precio_unitario or 0, _factor)
            _p.coste_materiales = tasa_convertir_precio(_p.coste_materiales or 0, _factor)
            _p.coste_mano_obra = tasa_convertir_precio(_p.coste_mano_obra or 0, _factor)
            _p.coste_complementarios = tasa_convertir_precio(_p.coste_complementarios or 0, _factor)
            _p.coste_otros = tasa_convertir_precio(_p.coste_otros or 0, _factor)

    # La conversión de unidades es la última capa: primero se resuelven país y
    # moneda, después precio/coste por unidad métrica pasan juntos a la unidad
    # estadounidense. Se hace también en el modo de búsqueda, que renderiza
    # filas en servidor en vez de pedirlas a /api/filas.
    try:
        from ..services.unidades_precio import (
            es_imperial_codigo,
            ficha_catalogo_a_mostrada,
            filas_descomposicion_a_mostrada,
        )

        if es_imperial_codigo(_codigo_trad):
            for _p in partidas:
                _unidad_metrica = _p.unidad
                _vista_imp = ficha_catalogo_a_mostrada({
                    "unidad": _p.unidad,
                    "precio_unitario": _p.precio_unitario,
                    "coste_materiales": _p.coste_materiales,
                    "coste_mano_obra": _p.coste_mano_obra,
                    "coste_complementarios": _p.coste_complementarios,
                    "coste_otros": _p.coste_otros,
                }, True)
                for _campo, _valor in _vista_imp.items():
                    setattr(_p, _campo, _valor)
                if _p.id in catalogo_descompuestos:
                    catalogo_descompuestos[_p.id] = filas_descomposicion_a_mostrada(
                        catalogo_descompuestos[_p.id], _unidad_metrica, True
                    )
    except Exception:
        pass
    return TEMPLATES.TemplateResponse(request, "partidas/list.html", {
        "partidas": partidas,
        # Los importes de la lista ya están convertidos: la vista los etiqueta
        # con este código ISO en lugar de un «$» que no dice de qué país es.
        "moneda_vista": _mon_cfg,
        "q": q,
        "catalogo_descompuestos": catalogo_descompuestos,
        "arbol_categorias": arbol_categorias,
        "categoria_actual": categoria,
        "subcategoria_actual": subcategoria,
        "apartado_actual": apartado,
        "total_partidas": total_partidas,
        "pagina": pagina,
        "total_paginas": total_paginas,
        "por_pagina": por_pagina,
        "vista": vista,
        "total_ocultas": total_ocultas,
        "salud": salud,
        "salud_catalogo": salud_catalogo,
    })


@router.get("/partidas/api/filas")
def filas_subcategoria_catalogo(
    categoria: str,
    subcategoria: str,
    vista: str = "activas",
    db: Session = Depends(get_db),
):
    """Devuelve las partidas de un subcapítulo como JSON.

    La vista de navegación monta el árbol completo contraído y pide aquí las
    filas de cada subcapítulo solo cuando el usuario lo despliega, para que la
    primera carga sea instantánea aunque el catálogo tenga miles de partidas.
    El navegador construye las filas con el DOM API (sin inyectar HTML), de
    acuerdo con la política CSP estricta del proyecto.
    """
    vista = "ocultas" if vista == "ocultas" else "activas"
    filas = (
        db.query(Partida)
        .filter(
            Partida.oculta.is_(vista == "ocultas"),
            Partida.categoria == categoria,
            Partida.subcategoria == subcategoria,
        )
        .order_by(Partida.apartado, Partida.codigo_interno, Partida.nombre)
        .all()
    )
    partidas = []
    try:
        _cfg_api = _config(db)
        _codigo_api = codigo_desde_pais(getattr(_cfg_api, "empresa_pais", ""))
        _mon_api = str(getattr(_cfg_api, "moneda_default", "USD") or "USD").strip().upper()
        _tasa_api = getattr(_cfg_api, "tasa_cambio", None)
        _factor_api = factor_conversion_local(_mon_api, _tasa_api)
    except Exception:
        _cfg_api = None
        _codigo_api = ""
        _mon_api = "USD"
        _factor_api = 1.0
    # Recalcula cada partida con las referencias nacionales cuando existen.
    _precios_mk_api = {}
    try:
        from ..services.precios_partidas import recalcular_partidas_mercado
        _pais_api = codigo_desde_pais(getattr(_cfg_api, "empresa_pais", "") or "") or "VE"
        _org_api = int(db.info.get("organizacion_id") or 0) or None
        _precios_mk_api = recalcular_partidas_mercado(
            db, filas, _pais_api, _org_api, _mon_api, _factor_api,
        )
    except Exception:
        pass
    for p in filas:
        try:
            valor = json.loads(p.descomposicion_json or "[]")
            descomp = valor.get("filas", []) if isinstance(valor, dict) else valor
        except (TypeError, ValueError):
            descomp = []
        n_recursos = sum(
            1 for f in descomp
            if isinstance(f, dict) and f.get("tipo") == "recurso"
        )
        # Precio Y costes convertidos a moneda local con el MISMO factor:
        # las filas del navegador calculan margen = precio - coste y no
        # deben mezclar monedas.
        _mk_api = _precios_mk_api.get(p.id)
        _precio_api = _mk_api.precio_unitario if _mk_api else (p.precio_unitario or 0.0)
        _coste_mat_api = _mk_api.coste_materiales if _mk_api else (p.coste_materiales or 0.0)
        _coste_mo_api = _mk_api.coste_mano_obra if _mk_api else (p.coste_mano_obra or 0.0)
        _coste_comp_api = _mk_api.coste_complementarios if _mk_api else (p.coste_complementarios or 0.0)
        _coste_otros_api = _mk_api.coste_otros if _mk_api else (p.coste_otros or 0.0)
        if not _mk_api and _factor_api != 1.0:
            _precio_api = tasa_convertir_precio(_precio_api, _factor_api)
            _coste_mat_api = tasa_convertir_precio(_coste_mat_api, _factor_api)
            _coste_mo_api = tasa_convertir_precio(_coste_mo_api, _factor_api)
            _coste_comp_api = tasa_convertir_precio(_coste_comp_api, _factor_api)
            _coste_otros_api = tasa_convertir_precio(_coste_otros_api, _factor_api)
        _fila_api = {
            "id": p.id,
            "nombre": traducir(p.nombre or "", _codigo_api) if _codigo_api else (p.nombre or ""),
            "descripcion": traducir(p.descripcion or "", _codigo_api) if _codigo_api else (p.descripcion or ""),
            "unidad": p.unidad or "ud",
            "precio": _precio_api,
            "categoria": traducir(p.categoria or "", _codigo_api) if _codigo_api else (p.categoria or ""),
            "subcategoria": traducir(p.subcategoria or "", _codigo_api) if _codigo_api else (p.subcategoria or ""),
            "apartado": traducir(p.apartado or "", _codigo_api) if _codigo_api else (p.apartado or ""),
            "codigo": p.codigo_interno or p.codigo_externo or "",
            "proveedor": p.proveedor or "",
            "usos": p.usos or 0,
            "imagen": bool(p.imagen),
            "es_oficial": bool(p.es_oficial),
            "coste_materiales": _coste_mat_api,
            "coste_mano_obra": _coste_mo_api,
            "coste_complementarios": _coste_comp_api,
            "coste_otros": _coste_otros_api,
            "recursos": n_recursos,
        }
        try:
            from ..services.unidades_precio import (
                es_imperial_codigo,
                ficha_catalogo_a_mostrada,
            )

            if es_imperial_codigo(_codigo_api):
                _fila_api = ficha_catalogo_a_mostrada(_fila_api, True)
        except Exception:
            pass
        partidas.append(_fila_api)
    return {"ok": True, "partidas": partidas}


@router.get("/partidas/api/buscar")
def buscar_partidas_catalogo_api(
    q: str = "",
    limite: int = 60,
    moneda: str = "",
    tasa: str = "",
    db: Session = Depends(get_db),
):
    """Búsqueda técnica bajo demanda sin descargar fichas/descompuestos."""
    consulta = str(q or "").strip()[:120]
    limite = max(1, min(int(limite or 60), 100))
    query = db.query(Partida).filter(
        Partida.oculta.is_(False)
    ).options(load_only(*_CAMPOS_INDICE_CATALOGO))
    if not consulta:
        # Sin texto: sugerencias inmediatas (lo más usado y lo más reciente).
        # El editor las pide nada más enfocar el buscador, así que el usuario
        # tiene partidas que insertar sin esperar a que baje el índice completo
        # del catálogo.
        partidas = query.order_by(
            Partida.usos.desc(),
            Partida.ultimo_uso.desc(),
            Partida.nombre,
        ).limit(limite).all()
    else:
        query, grupos = _aplicar_busqueda_catalogo(query, consulta)
        candidatas = query.order_by(
            Partida.usos.desc(), Partida.ultimo_uso.desc(), Partida.nombre
        ).limit(max(100, min(500, limite * 8))).all() if grupos else []
        partidas = sorted(
            candidatas,
            key=lambda p: (-_puntuar_busqueda_catalogo(p, consulta, grupos), p.nombre),
        )[:limite]
    try:
        _cfg_b = _config(db)
        _codigo_b = codigo_desde_pais(getattr(_cfg_b, "empresa_pais", ""))
    except Exception:
        _codigo_b = ""
    resultados = []
    # El editor pasa la moneda y la tasa del presupuesto; la lista de Partidas
    # no las envía y usa las de la organización.
    _mon_b, _factor_b = _contexto_moneda(db, moneda, tasa)
    for _pp in partidas:
        _idx = _partida_catalogo_indice(_pp)
        if _codigo_b:
            _idx["nombre"] = traducir(_idx.get("nombre", ""), _codigo_b)
            _idx["categoria"] = traducir(_idx.get("categoria", ""), _codigo_b)
            _idx["subcategoria"] = traducir(_idx.get("subcategoria", ""), _codigo_b)
            _idx["apartado"] = traducir(_idx.get("apartado", ""), _codigo_b)
        _idx["moneda"] = _mon_b
        if _factor_b != 1.0:
            # Precio y costes en la misma moneda que el resto de la vista
            _idx["precio"] = tasa_convertir_precio(_idx.get("precio", 0), _factor_b)
            for _k in ("coste_materiales", "coste_mano_obra", "coste_complementarios", "coste_otros"):
                _idx[_k] = tasa_convertir_precio(_idx.get(_k, 0), _factor_b)
        resultados.append(_idx)
    try:
        from ..services.unidades_precio import (
            es_imperial_codigo,
            ficha_catalogo_a_mostrada,
        )

        if es_imperial_codigo(_codigo_b):
            resultados = [ficha_catalogo_a_mostrada(r, True) for r in resultados]
    except Exception:
        pass
    return {
        "ok": True,
        "q": consulta,
        "moneda": _mon_b,
        "resultados": resultados,
    }


@router.post("/partidas/api/busqueda-sin-resultados")
async def registrar_busqueda_catalogo_sin_resultados(
    request: Request,
    db: Session = Depends(get_db),
):
    """Métrica interna para cubrir faltantes antes de que generen abandono."""
    try:
        payload = await request.json()
    except (TypeError, ValueError):
        payload = {}
    consulta = re.sub(r"\s+", " ", str(payload.get("q") or "").strip())[:120]
    if len(consulta) >= 2:
        log.warning(
            "catalogo_busqueda_sin_resultados",
            extra={
                "evento": "catalogo_busqueda_sin_resultados",
                "organizacion_id": db.info.get("organizacion_id"),
                "consulta": consulta,
            },
        )
    return {"ok": True}


@router.get("/partidas/{partida_id}/ficha")
def ficha_partida_catalogo(
    request: Request, partida_id: int,
    moneda: str = "",
    tasa: str = "",
    db: Session = Depends(get_db),
):
    """Ficha completa bajo demanda para preview, edición o inserción.

    ``moneda``/``tasa`` son el contexto del presupuesto que la pide. El
    catálogo vive en USD, así que sin ellos el editor abría la ficha con el
    precio unitario y la descomposición en dólares mientras el total de la
    partida ya estaba en la moneda del presupuesto.
    """
    partida = db.get(Partida, partida_id)
    if partida is None:
        return JSONResponse(
            status_code=404,
            content={"ok": False, "error": mensaje_request(request, "Partida no encontrada.")},
        )
    try:
        _cfg_f = _config(db)
        _codigo_f = codigo_desde_pais(getattr(_cfg_f, "empresa_pais", ""))
    except Exception:
        _codigo_f = ""
    _j = _partida_catalogo_json(partida)
    if _codigo_f:
        _j["nombre"] = traducir(_j.get("nombre",""), _codigo_f)
        _j["descripcion"] = traducir(_j.get("descripcion",""), _codigo_f)
        _j["categoria"] = traducir(_j.get("categoria",""), _codigo_f)
        _j["subcategoria"] = traducir(_j.get("subcategoria",""), _codigo_f)
        _j["apartado"] = traducir(_j.get("apartado",""), _codigo_f)
    _moneda_f, _factor_f = _contexto_moneda(db, moneda, tasa)
    # Reemplaza el precio base de la ficha por la referencia de mercado del
    # país cuando existe, para que la vista previa y la inserción de una
    # partida no cotice con la partida original convertida.
    _j_mercado = False
    try:
        from ..services.precios_partidas import recalcular_partida_mercado
        _pais_f = codigo_desde_pais(getattr(_config(db), "empresa_pais", "") or "") or "VE"
        _org_f = int(db.info.get("organizacion_id") or 0) or None
        _mk_f = recalcular_partida_mercado(db, partida, _pais_f, _org_f, _moneda_f, _factor_f)
        if _mk_f is not None and _mk_f.con_precio_mercado:
            _j["precio"] = _mk_f.precio_unitario
            _j["precio_unitario"] = _mk_f.precio_unitario
            _j["coste_materiales"] = _mk_f.coste_materiales
            _j["coste_mano_obra"] = _mk_f.coste_mano_obra
            _j["coste_complementarios"] = _mk_f.coste_complementarios
            _j["coste_otros"] = _mk_f.coste_otros
            _j["moneda"] = _moneda_f
            if isinstance(_j.get("descomposicion"), dict):
                _j["descomposicion"]["filas"] = _mk_f.filas
            _j_mercado = True
    except Exception:
        pass
    if not _j_mercado:
        _j = _ficha_en_moneda(_j, _moneda_f, _factor_f)
    try:
        # Mercado imperial: la ficha entra en el editor con el precio por
        # sq ft/ft/cu yd y los rendimientos reescalados; el catálogo en la
        # base no se toca (sigue en métrico).
        from ..services.unidades_precio import (
            es_imperial_codigo,
            ficha_catalogo_a_mostrada,
        )

        if es_imperial_codigo(_codigo_f):
            _j = ficha_catalogo_a_mostrada(_j, True)
    except Exception:
        pass
    return {"ok": True, "partida": _j, "moneda": _moneda_f}


@router.get("/partidas/{partida_id}/descomposicion")
def descomposicion_partida(
    request: Request, partida_id: int,
    moneda: str = "",
    tasa: str = "",
    db: Session = Depends(get_db),
):
    """Filas de recursos de una partida del catálogo (carga bajo demanda).

    La página de Partidas ya no emite las ~540 tablas de descomposición en el
    HTML inicial: cada una se pide aquí solo cuando el usuario la despliega,
    lo que reduce el peso y el DOM de la lista a una fracción.
    """
    partida = db.get(Partida, partida_id)
    if partida is None:
        return {"ok": False, "error": mensaje_request(request, "Partida no encontrada.")}
    try:
        valor = json.loads(partida.descomposicion_json or "[]")
    except (TypeError, ValueError):
        valor = []
    filas = valor.get("filas", []) if isinstance(valor, dict) else valor
    filas = [f for f in filas if isinstance(f, dict) and f.get("tipo") == "recurso"]
    _mon_d, _factor_d = _contexto_moneda(db, moneda, tasa)
    _idioma_d = _idioma(request)
    _filas_mercado = False
    try:
        _pais_d = codigo_desde_pais(getattr(_config(db), "empresa_pais", "") or "") or "VE"
    except Exception:
        _pais_d = "VE"
    # Referencias nacionales primero: si el país tiene precio de mercado para
    # los recursos, la descomposición debe mostrar la referencia real y no el
    # base convertido de la partida original.
    try:
        from ..services.precios_partidas import recalcular_partida_mercado
        _org_d = int(db.info.get("organizacion_id") or 0) or None
        mk = recalcular_partida_mercado(db, partida, _pais_d, _org_d, _mon_d, _factor_d)
        if mk is not None and mk.con_precio_mercado:
            filas = mk.filas
            _filas_mercado = True
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
    # Si no hay referencia nacional (o el recálculo falla), las filas se
    # convierten al contexto monetario de la vista con el mismo factor que el
    # resto de importes.
    if not _filas_mercado and _factor_d != 1.0:
        for _f in filas:
            if isinstance(_f.get("precio"), (int, float)):
                _f["precio"] = tasa_convertir_precio(_f["precio"], _factor_d)
            if isinstance(_f.get("importe"), (int, float)):
                _f["importe"] = tasa_convertir_precio(_f["importe"], _factor_d)
    filas = _filas_descomposicion_vista(filas, _pais_d, _idioma_d)
    try:
        from ..services.unidades_precio import (
            es_imperial_codigo,
            filas_descomposicion_a_mostrada,
        )

        if es_imperial_codigo(_pais_d):
            # Cada rendimiento tiene dimensión recurso / unidad de partida:
            # además de pasar el denominador m²→sq ft, kg/l/m de las filas se
            # presentan como lb/gal/ft con su precio unitario reescalado.
            filas = filas_descomposicion_a_mostrada(
                filas, partida.unidad or "ud", True
            )
    except Exception:
        pass
    return {"ok": True, "filas": filas, "moneda": _mon_d}


def _cabeceras_csv(etiquetas, idioma) -> list[str]:
    """Mismo vocabulario que el Excel (app/services/excel_export.py)."""
    from ..services.excel_export import cabeceras

    return cabeceras(etiquetas, idioma)


def _idioma(request) -> str:
    """Idioma ya resuelto por el middleware (``request.state.lang``).

    Las variantes regionales (``/en-mx/``) comparten vocabulario: lo que
    decide la lengua del libro exportado es la lengua, no el país.
    """
    return str(getattr(getattr(request, "state", None), "lang", "es") or "es")


@router.get("/partidas/exportar")
def exportar_partidas(
    request: Request,
    formato: str = "csv",
    incluir_ocultas: bool = False,
    db: Session = Depends(get_db),
):
    idioma = _idioma(request)
    """Exporta las partidas visibles; las ocultas son opt-in."""
    query = db.query(Partida)
    if not incluir_ocultas:
        query = query.filter(Partida.oculta.is_(False))
    partidas = query.order_by(
        Partida.categoria, Partida.subcategoria, Partida.apartado,
        Partida.codigo_interno, Partida.nombre,
    ).all()

    # Las exportaciones deben reflejar el mercado del país igual que la lista:
    # se recalcula el APU con las referencias nacionales y se sobreescriben los
    # importes en los objetos antes de escribirlos (la exportación no guarda).
    _moneda_exp, _factor_exp = _contexto_moneda(db)
    try:
        _cfg_exp = _config(db)
        _pais_exp = codigo_desde_pais(
            getattr(_cfg_exp, "empresa_pais", "") or ""
        ) or "VE"
    except Exception:
        _pais_exp = ""
    try:
        from ..services.precios_partidas import recalcular_partidas_mercado

        _org_exp = int(db.info.get("organizacion_id") or 0) or None
        _precios_exp = recalcular_partidas_mercado(
            db, partidas, _pais_exp or "VE", _org_exp, _moneda_exp, _factor_exp,
        )
        for _p in partidas:
            _mk_exp = _precios_exp.get(_p.id)
            if _mk_exp is None:
                if _factor_exp != 1.0:
                    for _campo_moneda in (
                        "precio_unitario", "coste_materiales", "coste_mano_obra",
                        "coste_complementarios", "coste_otros",
                    ):
                        setattr(
                            _p, _campo_moneda,
                            tasa_convertir_precio(
                                getattr(_p, _campo_moneda, 0) or 0, _factor_exp
                            ),
                        )
                continue
            _p.precio_unitario = _mk_exp.precio_unitario
            _p.coste_materiales = _mk_exp.coste_materiales
            _p.coste_mano_obra = _mk_exp.coste_mano_obra
            _p.coste_complementarios = _mk_exp.coste_complementarios
            _p.coste_otros = _mk_exp.coste_otros
    except Exception:
        pass

    # CSV/XLSX son una salida visible del catálogo: mantienen el almacén
    # métrico, pero para una organización US exportan unidad, precio, costes y
    # horas por la misma unidad imperial que la tabla y el editor.
    try:
        from ..services.unidades_precio import (
            es_imperial_codigo,
            ficha_catalogo_a_mostrada,
        )

        if es_imperial_codigo(_pais_exp):
            for _p in partidas:
                _vista_exp = ficha_catalogo_a_mostrada({
                    "unidad": _p.unidad,
                    "precio_unitario": _p.precio_unitario,
                    "coste_materiales": _p.coste_materiales,
                    "coste_mano_obra": _p.coste_mano_obra,
                    "coste_complementarios": _p.coste_complementarios,
                    "coste_otros": _p.coste_otros,
                    "tiempo_estimado_horas": _p.tiempo_estimado_horas,
                    "tiempo_oficial_horas": getattr(_p, "tiempo_oficial_horas", None),
                    "tiempo_ayudante_horas": getattr(_p, "tiempo_ayudante_horas", None),
                    "tiempo_equipo_horas": getattr(_p, "tiempo_equipo_horas", None),
                }, True)
                for _campo_exp, _valor_exp in _vista_exp.items():
                    setattr(_p, _campo_exp, _valor_exp)
    except Exception:
        pass

    if formato.lower() == "excel" or formato.lower() == "xlsx":
        from ..services.excel_export import exportar_catalogo_partidas_excel
        buf = exportar_catalogo_partidas_excel(partidas, idioma=idioma)
        return Response(
            content=buf.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=partidas.xlsx"},
        )

    filas = [_cabeceras_csv([
        "Código", "Código anterior", "Nombre", "Descripción", "Unidad", "Precio unitario",
        "Capítulo", "Subcapítulo", "Apartado", "Coste materiales", "Coste mano de obra", "Coste complementarios", "Otros costes", "Tiempo estimado (h)", "Proveedor",
        "Rendimiento", "Desperdicio recomendado (%)", "Notas técnicas", "Última actualización de precio", "Usos",
    ], idioma)]
    for p in partidas:
        filas.append([
            p.codigo_interno, p.codigo_legacy, p.nombre, p.descripcion, p.unidad,
            f"{p.precio_unitario:.2f}".replace(".", ","),
            p.categoria, p.subcategoria, p.apartado,
            f"{(p.coste_materiales or 0):.2f}".replace(".", ","),
            f"{(p.coste_mano_obra or 0):.2f}".replace(".", ","),
            f"{(p.coste_complementarios or 0):.2f}".replace(".", ","),
            f"{(p.coste_otros or 0):.2f}".replace(".", ","),
            "" if p.tiempo_estimado_horas is None else str(p.tiempo_estimado_horas).replace(".", ","),
            p.proveedor, p.rendimiento,
            f"{(p.desperdicio_recomendado_pct or 0):.2f}".replace(".", ","),
            p.notas_tecnicas,
            p.fecha_actualizacion_precio.isoformat() if p.fecha_actualizacion_precio else "",
            p.usos or 0,
        ])
    return _csv_response(filas, "partidas.csv")


@router.post("/partidas/categorias")
async def crear_categoria_partida(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    categoria = str(form.get("categoria") or "").strip()
    subcategoria = str(form.get("subcategoria") or "").strip()
    if not categoria:
        return _redirect("/partidas", error="Escribe el nombre de la categoría.")
    existe = db.query(CategoriaPartida).filter(
        CategoriaPartida.categoria == categoria, CategoriaPartida.subcategoria == subcategoria
    ).first()
    if not existe:
        db.add(CategoriaPartida(categoria=categoria, subcategoria=subcategoria))
        db.commit()
    etiqueta = f"«{categoria} · {subcategoria}»" if subcategoria else f"«{categoria}»"
    return _redirect("/partidas", msg=f"Creada {etiqueta}. Ya puedes arrastrar partidas a ella.")


@router.get("/partidas/ajustar/previsualizar", response_class=HTMLResponse)
def previsualizar_ajuste_precios(request: Request, porcentaje: str = "0", db: Session = Depends(get_db)):
    pct = _f(porcentaje)
    if pct < -100:
        return _redirect("/partidas", error="El porcentaje no puede ser menor que -100.")
    partidas = db.query(Partida).filter(Partida.oculta.is_(False)).order_by(Partida.categoria, Partida.nombre).all()
    _moneda, _factor = _contexto_moneda(db)
    total = len(partidas)
    suma_actual = sum(float(p.precio_unitario or 0) for p in partidas)
    suma_nueva = sum(round(float(p.precio_unitario or 0) * (1 + pct / 100), 2) for p in partidas)
    muestras = []
    for p in partidas[:12]:
        antes = tasa_convertir_precio(p.precio_unitario or 0, _factor)
        despues = tasa_convertir_precio(round(float(p.precio_unitario or 0) * (1 + pct / 100), 2), _factor)
        muestras.append({"nombre": p.nombre, "antes": antes, "despues": despues})
    return TEMPLATES.TemplateResponse(request, "partidas/ajustar_preview.html", {
        "porcentaje": pct,
        "total": total,
        "promedio_actual": tasa_convertir_precio((suma_actual / total) if total else 0, _factor),
        "promedio_nuevo": tasa_convertir_precio((suma_nueva / total) if total else 0, _factor),
        "muestras": muestras,
        "moneda_vista": _moneda,
    })


@router.post("/partidas/ajustar")
def ajustar_precios(porcentaje: str = Form("0"), db: Session = Depends(get_db)):
    """Aplica un % de ajuste al catálogo; no toca presupuestos ya emitidos."""
    pct = _f(porcentaje)
    if pct < -100:
        return _redirect("/partidas", error="El porcentaje no puede ser menor que -100.")
    partidas = db.query(Partida).all()
    if not partidas:
        return _redirect("/partidas", error="No hay partidas en el catálogo.")
    ahora = datetime.utcnow()
    for partida in partidas:
        partida.precio_unitario = round((partida.precio_unitario or 0) * (1 + pct / 100), 2)
        partida.fecha_actualizacion_precio = ahora
    db.commit()
    auditoria.registrar_evento(
        db,
        "catalogo.precios_ajustados",
        entidad="partida",
        detalle={"porcentaje": pct, "partidas": len(partidas)},
    )
    return _redirect("/partidas", msg=f"Precios ajustados un {fmt_num(pct)} % en {len(partidas)} partidas.")


@router.get("/partidas/precios/anomalos")
def listar_precios_anomalos(db: Session = Depends(get_db)):
    """Diagnóstico de precios imposibles (JSON) para revisar antes de reparar."""
    from ..services.precios_anomalos import detectar_precios_anomalos

    anomalias = detectar_precios_anomalos(db)
    return {
        "ok": True,
        "total": len(anomalias),
        "reparables": sum(1 for a in anomalias if a["reparable"]),
        "anomalias": anomalias,
    }


@router.post("/partidas/precios/reparar")
def reparar_precios_anomalos_catalogo(db: Session = Depends(get_db)):
    """Devuelve a la moneda base los precios inflados por la tasa de cambio.

    Es la contraparte del fallo de guardado automático: hasta su corrección,
    un presupuesto en moneda local podía escribir en el catálogo el importe ya
    convertido, y el editor lo multiplicaba otra vez al reutilizar la partida.
    """
    from ..services.precios_anomalos import reparar_precios_anomalos

    resultado = reparar_precios_anomalos(db)
    total = resultado["total_corregidas"]
    pendientes = resultado["total_pendientes"]
    if not total and not pendientes:
        return _redirect("/partidas", msg="No hay precios imposibles en el catálogo.")
    if total:
        auditoria.registrar_evento(
            db,
            "catalogo.precios_reparados",
            entidad="partida",
            detalle={
                "corregidas": total,
                "pendientes": pendientes,
                "ejemplos": [
                    {"id": a["id"], "de": a["precio"], "a": a["precio_sugerido"]}
                    for a in resultado["corregidas"][:10]
                ],
            },
        )
    mensaje = f"{total} precio(s) devueltos a su moneda base."
    if pendientes:
        mensaje += f" Quedan {pendientes} para revisar a mano."
    return _redirect("/partidas?salud=precio_absurdo" if pendientes else "/partidas", msg=mensaje)


@router.post("/partidas/{partida_id}/usar")
def usar_partida(partida_id: int, db: Session = Depends(get_db)):
    """Punto de compatibilidad para clientes antiguos del constructor."""
    partida = db.get(Partida, partida_id)
    if partida:
        partida.usos = (partida.usos or 0) + 1
        partida.ultimo_uso = datetime.utcnow()
        db.commit()
    return {"ok": True}


@router.post("/partidas/{partida_id}/actualizar-precio")
async def actualizar_precio_partida_desde_presupuesto(partida_id: int, request: Request, db: Session = Depends(get_db)):
    """Actualiza solo el precio de la partida maestra.

    Se utiliza cuando, al editar una línea dentro de un presupuesto, el
    usuario elige explícitamente «cambiar partida / catálogo». Modifica la
    partida reutilizable para presupuestos futuros, pero **no** recorre ni
    cambia presupuestos ya guardados: esos documentos conservan su propio
    ``precio_unitario`` copiado en ``presupuesto_items``.
    """
    partida = db.get(Partida, partida_id)
    if partida is None:
        return {"ok": False, "error": mensaje_request(request, "Partida del catálogo no encontrada.")}
    try:
        payload = await request.json()
    except (TypeError, ValueError):
        payload = {}
    nuevo_precio = _f(payload.get("precio"), 0)
    if nuevo_precio < 0:
        return {"ok": False, "error": mensaje_request(request, "El precio no puede ser negativo.")}
    # El editor muestra (y envía) el precio en la moneda del presupuesto; el
    # catálogo se guarda en la moneda base. Sin este paso, «actualizar el
    # catálogo» desde un presupuesto en MXN escribía el importe en pesos como
    # si fueran dólares y multiplicaba el precio por la tasa.
    _moneda_p, _factor_p = _contexto_moneda(db, payload.get("moneda"), payload.get("tasa"))
    nuevo_precio = _a_moneda_base(nuevo_precio, _factor_p)
    # Misma idea con la unidad: en un mercado imperial el editor muestra (y
    # envía) el precio por sq ft, pero el catálogo se guarda por m². Sin
    # este paso, «actualizar el catálogo» desde un presupuesto estadounidense
    # dividía el precio maestro entre 10,76 en cada edición.
    _imperial_p = False
    try:
        from ..services.unidades_precio import es_imperial_config, factor_cantidad

        _imperial_p = es_imperial_config(_config(db))
        if _imperial_p:
            _factor_u_p = factor_cantidad(partida.unidad)
            if _factor_u_p:
                nuevo_precio = float(nuevo_precio) * _factor_u_p
    except Exception:
        _imperial_p = False
    if abs((partida.precio_unitario or 0.0) - nuevo_precio) > 1e-9:
        precio_anterior = partida.precio_unitario or 0.0
        partida.precio_unitario = nuevo_precio
        partida.fecha_actualizacion_precio = datetime.utcnow()
        db.commit()
        db.refresh(partida)
        auditoria.registrar_evento(
            db,
            "catalogo.precio_partida",
            entidad="partida",
            entidad_id=partida.id,
            detalle={"de": precio_anterior, "a": nuevo_precio},
        )
    # La respuesta vuelve al editor: se devuelve en su misma moneda para que
    # la línea no se repinte con el importe en dólares.
    _ficha_p = _ficha_en_moneda(_partida_catalogo_json(partida), _moneda_p, _factor_p)
    if _imperial_p:
        try:
            from ..services.unidades_precio import ficha_catalogo_a_mostrada

            _ficha_p = ficha_catalogo_a_mostrada(_ficha_p, True)
        except Exception:
            pass
    return {
        "ok": True,
        "partida": _ficha_p,
        "moneda": _moneda_p,
    }


@router.post("/partidas/guardar-desde-presupuesto")
async def guardar_partida_desde_presupuesto(request: Request, db: Session = Depends(get_db)):
    """Crea o actualiza el catálogo desde la ficha completa del constructor.

    Usa los mismos lectores, validaciones, cálculo de descomposición e imagen
    que las rutas de la pestaña Partidas. Devuelve JSON para permanecer en el
    presupuesto y seguir trabajando.
    """
    form = await request.form()
    partida_id = int(_f(form.get("partida_catalogo_id"), 0))
    partida = db.get(Partida, partida_id) if partida_id else None
    nombre = str(form.get("nombre", "")).strip()
    if not nombre:
        return {"ok": False, "error": mensaje_request(request, "El nombre de la partida es obligatorio.")}
    # Una línea importada o antigua puede no conservar el id del catálogo;
    # su nombre único permite recuperar la misma ficha en vez de duplicarla.
    if partida is None:
        partida = db.query(Partida).filter(Partida.nombre == nombre).first()
    repetida = db.query(Partida).filter(Partida.nombre == nombre)
    if partida is not None:
        repetida = repetida.filter(Partida.id != partida.id)
    if repetida.first():
        return {"ok": False, "error": mensaje_request(request, "Ya existe otra partida con ese nombre.")}

    datos = _datos_partida_catalogo(form)
    filas_catalogo, costes_calculados = _descomposicion_catalogo(form)
    # La ficha se edita en la moneda del presupuesto (o la de la organización
    # si el formulario no la envía) y el catálogo se guarda en la base: hay
    # que deshacer la conversión antes de persistir.
    _mon_u, _factor_u = _contexto_moneda(db, form.get("moneda"), form.get("tasa"))
    if _factor_u != 1.0:
        datos["precio_unitario"] = _a_moneda_base(datos.get("precio_unitario", 0), _factor_u)
        for k in ("coste_materiales", "coste_mano_obra", "coste_complementarios", "coste_otros"):
            datos[k] = _a_moneda_base(datos.get(k, 0), _factor_u)
        for fila in filas_catalogo:
            fila["precio"] = _a_moneda_base(fila.get("precio", 0), _factor_u)
        costes_calculados = {
            k: _a_moneda_base(v, _factor_u) for k, v in costes_calculados.items()
        }
    # Unidad: la ficha imperial llega en «sq ft» y el catálogo guarda en
    # métrico (la unidad es la marca; ver unidades_precio).
    _imperial_u = False
    try:
        from ..services.unidades_precio import normalizar_ficha_catalogo_a_metrico

        _imperial_u = normalizar_ficha_catalogo_a_metrico(
            datos, filas_catalogo, costes_calculados
        )
    except Exception:
        _imperial_u = False
    if filas_catalogo:
        datos.update({f"coste_{k}": v for k, v in costes_calculados.items()})
    datos["descomposicion_json"] = json.dumps({
        "origen": "manual",
        "codigo": str(form.get("codigo_externo", "")).strip(),
        "unidad": datos["unidad"],
        "filas": filas_catalogo,
    }, ensure_ascii=False)
    datos["codigo_externo"] = str(form.get("codigo_externo", "")).strip()

    if partida is None:
        partida = Partida(nombre=nombre)
        db.add(partida)
        precio_anterior = None
    else:
        precio_anterior = partida.precio_unitario or 0.0
        _desvincular_clasificacion_si_cambio(partida, datos)
    partida.nombre = nombre
    for campo, valor in datos.items():
        setattr(partida, campo, valor)
    if precio_anterior is None or precio_anterior != partida.precio_unitario:
        partida.fecha_actualizacion_precio = datetime.utcnow()

    if form.get("quitar_imagen"):
        anterior = partida.imagen
        partida.imagen = ""
        _borrar_imagen(anterior, db)
    else:
        archivo = form.get("imagen")
        if isinstance(archivo, UploadFileStarlette) and archivo.filename:
            vieja = partida.imagen
            ruta = await _guardar_imagen(archivo, f"partidas/cat_{partida.id or 'nueva'}", db)
            if ruta:
                partida.imagen = ruta
                _borrar_imagen(vieja, db)

    db.commit()
    db.refresh(partida)
    _sincronizar_recursos(db)
    _ficha_u = _ficha_en_moneda(_partida_catalogo_json(partida), _mon_u, _factor_u)
    if _imperial_u:
        try:
            from ..services.unidades_precio import ficha_catalogo_a_mostrada

            _ficha_u = ficha_catalogo_a_mostrada(_ficha_u, True)
        except Exception:
            pass
    return {
        "ok": True,
        "partida": _ficha_u,
        "moneda": _mon_u,
    }


@router.get("/partidas/nueva", response_class=HTMLResponse)
def nueva_partida_form(request: Request, db: Session = Depends(get_db)):
    # El editor de partida trabaja en la moneda de la organización (igual que
    # la lista y el POST, que revierte la conversión al guardar).
    try:
        from ..services.monedas import simbolo as _simbolo_iso
        _moneda_n, _factor_n = _contexto_moneda(db)
        _simbolo_n = _simbolo_iso(_moneda_n)
    except Exception:
        _moneda_n, _simbolo_n = "USD", "$"
    try:
        from ..services.unidades_precio import es_imperial_config
        _imperial_n = es_imperial_config(_config(db))
    except Exception:
        _imperial_n = False
    return TEMPLATES.TemplateResponse(request, "partidas/form.html", {
        "partida": None,
        "categorias": _categorias(db),
        "moneda_local": _moneda_n,
        "simbolo_local": _simbolo_n,
        "unidades_imperiales": _imperial_n,
        "error": request.query_params.get("error", ""),
    })


@router.post("/partidas/nueva")
async def crear_partida(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    nombre = str(form.get("nombre", "")).strip()
    if not nombre:
        return _redirect("/partidas/nueva", error="El nombre es obligatorio.")
    if db.query(Partida).filter(Partida.nombre == nombre).first():
        return _redirect("/partidas/nueva", error="Ya existe una partida con ese nombre.")
    datos = _datos_partida_catalogo(form)
    filas_catalogo, costes_calculados = _descomposicion_catalogo(form)
    # El formulario se edita en la moneda de la organización y el catálogo se
    # guarda en la base: se deshace la conversión antes de persistir. Los
    # costes recalculados desde las filas también, o el precio quedaría en
    # dólares y sus costes en moneda local.
    _mon_u, _factor_u = _contexto_moneda(db)
    if _factor_u != 1.0:
        datos["precio_unitario"] = _a_moneda_base(datos.get("precio_unitario", 0), _factor_u)
        for k in ("coste_materiales", "coste_mano_obra", "coste_complementarios", "coste_otros"):
            datos[k] = _a_moneda_base(datos.get(k, 0), _factor_u)
        for fila in filas_catalogo:
            fila["precio"] = _a_moneda_base(fila.get("precio", 0), _factor_u)
        costes_calculados = {
            k: _a_moneda_base(v, _factor_u) for k, v in costes_calculados.items()
        }
    if filas_catalogo:
        datos.update({f"coste_{k}": v for k, v in costes_calculados.items()})
    try:
        from ..services.unidades_precio import normalizar_ficha_catalogo_a_metrico

        if normalizar_ficha_catalogo_a_metrico(datos, filas_catalogo, costes_calculados) and filas_catalogo:
            datos.update({f"coste_{k}": v for k, v in costes_calculados.items()})
    except Exception:
        pass
    datos["descomposicion_json"] = json.dumps({"origen": "manual", "codigo": str(form.get("codigo_externo", "")), "unidad": datos["unidad"], "filas": filas_catalogo}, ensure_ascii=False)
    datos["codigo_externo"] = str(form.get("codigo_externo", "")).strip()
    imagen = ""
    archivo = form.get("imagen")
    if isinstance(archivo, UploadFileStarlette) and archivo.filename:
        imagen = await _guardar_imagen(archivo, "partidas/cat", db)
    partida = Partida(nombre=nombre, imagen=imagen, **datos)
    db.add(partida)
    db.commit()
    _sincronizar_recursos(db)
    return _redirect("/partidas", msg="Partida creada correctamente.")


@router.get("/partidas/{partida_id}/editar", response_class=HTMLResponse)
def editar_partida_form(partida_id: int, request: Request, db: Session = Depends(get_db)):
    partida = db.get(Partida, partida_id)
    if partida is None:
        return _redirect("/partidas", error="Partida no encontrada.")

    from copy import copy

    # Todo se prepara sobre una copia: el editor nunca muta la ficha base ni
    # guarda traducciones/precios de mercado en la moneda del catálogo.
    partida_vista = copy(partida)
    try:
        cfg = _config(db)
        pais_codigo = codigo_desde_pais(getattr(cfg, "empresa_pais", "") or "") or "VE"
    except Exception:
        cfg = None
        pais_codigo = "VE"
    moneda_vista, factor_vista = _contexto_moneda(db)
    idioma = _idioma(request)

    mercado = None
    try:
        from ..services.precios_partidas import recalcular_partida_mercado
        mercado = recalcular_partida_mercado(
            db,
            partida,
            pais_codigo,
            int(db.info.get("organizacion_id") or 0) or None,
            moneda_vista,
            factor_vista,
        )
    except Exception:
        # La ficha original sigue siendo utilizable como fallback si no hay
        # referencias disponibles o falla la consulta de mercado.
        try:
            db.rollback()
        except Exception:
            pass
        mercado = None

    if mercado is not None and mercado.con_precio_mercado:
        # Debe coincidir con la fila y el editor del catálogo: mismas
        # referencias nacionales, moneda y recálculo de costes/cascada.
        partida_vista.precio_unitario = mercado.precio_unitario
        partida_vista.coste_materiales = mercado.coste_materiales
        partida_vista.coste_mano_obra = mercado.coste_mano_obra
        partida_vista.coste_complementarios = mercado.coste_complementarios
        partida_vista.coste_otros = mercado.coste_otros
        try:
            descomp_vista = json.loads(partida.descomposicion_json or "[]")
        except (TypeError, ValueError):
            descomp_vista = {}
        if isinstance(descomp_vista, list):
            descomp_vista = {"origen": "manual", "filas": descomp_vista}
        if not isinstance(descomp_vista, dict):
            descomp_vista = {}
        descomp_vista = dict(descomp_vista)
        descomp_vista["filas"] = mercado.filas
        partida_vista.descomposicion_json = json.dumps(descomp_vista, ensure_ascii=False)
    else:
        # Fallback de catálogo: convierte precio, costes y filas con el mismo
        # factor; nunca etiqueta importes USD como GBP si falta la tasa.
        for campo in (
            "precio_unitario", "coste_materiales", "coste_mano_obra",
            "coste_complementarios", "coste_otros",
        ):
            setattr(
                partida_vista,
                campo,
                tasa_convertir_precio(getattr(partida, campo, 0) or 0, factor_vista),
            )
        descomp_local = _descomposicion_en_moneda(partida, factor_vista)
        if descomp_local is not None:
            partida_vista.descomposicion_json = descomp_local

    # Traducciones y rótulos son una capa de vista. Las claves de categoría y
    # los textos originales permanecen intactos en la fila ORM.
    try:
        descomp_vista = json.loads(partida_vista.descomposicion_json or "[]")
    except (TypeError, ValueError):
        descomp_vista = []
    if isinstance(descomp_vista, list):
        descomp_vista = {"origen": "manual", "filas": descomp_vista}
    if isinstance(descomp_vista, dict):
        descomp_vista = dict(descomp_vista)
        descomp_vista["filas"] = _filas_descomposicion_vista(
            descomp_vista.get("filas", []), pais_codigo, idioma,
            preservar_personalizadas=True,
        )
        partida_vista.descomposicion_json = json.dumps(descomp_vista, ensure_ascii=False)

    # El CRUD del catálogo es también una superficie de trabajo: una empresa
    # estadounidense debe editar sq ft/lb/gal, no abrir una ficha imperial en
    # el buscador y volver de pronto a m²/kg al pulsar el lápiz. La copia se
    # convierte al final, después de mercado, moneda y traducción.
    try:
        from ..services.unidades_precio import (
            es_imperial_codigo,
            ficha_catalogo_a_mostrada,
        )

        if es_imperial_codigo(pais_codigo):
            _ficha_vista = ficha_catalogo_a_mostrada(
                _partida_catalogo_json(partida_vista), True
            )
            for _campo_imp in (
                "unidad", "precio_unitario", "coste_materiales",
                "coste_mano_obra", "coste_complementarios", "coste_otros",
                "tiempo_estimado_horas", "tiempo_oficial_horas",
                "tiempo_ayudante_horas", "tiempo_equipo_horas",
            ):
                if _campo_imp in _ficha_vista:
                    setattr(partida_vista, _campo_imp, _ficha_vista[_campo_imp])
            partida_vista.descomposicion_json = json.dumps(
                _ficha_vista.get("descomposicion") or {}, ensure_ascii=False
            )
    except Exception:
        pass

    categorias = _categorias(db)
    if idioma.lower().startswith("en") and pais_codigo:
        partida_vista.nombre = traducir(partida.nombre or "", pais_codigo)
        partida_vista.descripcion = traducir(partida.descripcion or "", pais_codigo)
        for campo in ("categoria", "subcategoria", "apartado"):
            setattr(
                partida_vista,
                campo,
                traducir(getattr(partida, campo, "") or "", pais_codigo),
            )
        categorias = [traducir(categoria, pais_codigo) for categoria in categorias]

    try:
        from ..services.monedas import simbolo as _simbolo_iso
        simbolo_local = _simbolo_iso(moneda_vista)
    except Exception:
        simbolo_local = ""
    return TEMPLATES.TemplateResponse(request, "partidas/form.html", {
        "partida": partida_vista,
        "categorias": categorias,
        "moneda_local": moneda_vista,
        "simbolo_local": simbolo_local,
        "unidades_imperiales": pais_codigo == "US",
        "error": request.query_params.get("error", ""),
    })

@router.post("/partidas/{partida_id}/editar")
async def actualizar_partida(partida_id: int, request: Request, db: Session = Depends(get_db)):
    partida = db.get(Partida, partida_id)
    if partida is None:
        return _redirect("/partidas", error="Partida no encontrada.")
    form = await request.form()
    idioma = _idioma(request)
    try:
        cfg = _config(db)
        pais_codigo = codigo_desde_pais(getattr(cfg, "empresa_pais", "") or "") or "VE"
    except Exception:
        pais_codigo = "VE"
    moneda_vista, factor_vista = _contexto_moneda(db)

    # El mismo cálculo de mercado que usa la lista y el GET del editor. Así se
    # puede distinguir un importe de GBP mostrado del precio base realmente
    # almacenado, y un guardado sin cambios no contamina el catálogo USD.
    mercado = None
    try:
        from ..services.precios_partidas import recalcular_partida_mercado
        mercado = recalcular_partida_mercado(
            db,
            partida,
            pais_codigo,
            int(db.info.get("organizacion_id") or 0) or None,
            moneda_vista,
            factor_vista,
        )
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
        mercado = None
    mercado_visible = mercado if mercado is not None and mercado.con_precio_mercado else None

    nombre_enviado = str(form.get("nombre", "")).strip()
    nombre = _restaurar_valor_catalogo(
        db, "nombre", nombre_enviado, partida.nombre, pais_codigo, idioma
    )
    if not nombre:
        return _redirect(f"/partidas/{partida_id}/editar", error="El nombre es obligatorio.")
    if db.query(Partida).filter(Partida.nombre == nombre, Partida.id != partida_id).first():
        return _redirect(f"/partidas/{partida_id}/editar", error="Ya existe otra partida con ese nombre.")

    datos = _datos_partida_catalogo(form)
    for campo in ("descripcion", "categoria", "subcategoria", "apartado"):
        datos[campo] = _restaurar_valor_catalogo(
            db, campo, datos.get(campo), getattr(partida, campo, ""), pais_codigo, idioma
        )

    filas_catalogo, _costes_formulario = _descomposicion_catalogo(form)
    # El formulario estadounidense envía la partida por sq ft y sus recursos
    # por lb/gal/ft. Normalizamos antes de comparar con las referencias de
    # mercado y con la ficha original, que siempre viven en métrico. Unidad y
    # moneda son factores independientes y sus conversiones conmutan.
    try:
        from ..services.unidades_precio import normalizar_ficha_catalogo_a_metrico

        normalizar_ficha_catalogo_a_metrico(
            datos, filas_catalogo, _costes_formulario
        )
    except Exception:
        pass
    try:
        valor_original = json.loads(partida.descomposicion_json or "[]")
    except (TypeError, ValueError):
        valor_original = []
    originales = valor_original.get("filas", []) if isinstance(valor_original, dict) else valor_original
    originales = [
        fila for fila in originales
        if isinstance(fila, dict) and fila.get("tipo") == "recurso"
    ]
    filas_mercado = mercado_visible.filas if mercado_visible else []

    def _codigo_fila(fila):
        return str((fila or {}).get("codigo") or "").strip().casefold()

    def _misma_fila(a, b):
        if not isinstance(a, dict) or not isinstance(b, dict):
            return False
        codigo_a, codigo_b = _codigo_fila(a), _codigo_fila(b)
        if codigo_a or codigo_b:
            return bool(codigo_a and codigo_a == codigo_b)
        return (
            str(a.get("unidad") or "").strip().casefold() == str(b.get("unidad") or "").strip().casefold()
            and str(a.get("categoria") or "").strip().casefold() == str(b.get("categoria") or "").strip().casefold()
            and str(a.get("descripcion") or "").strip().casefold() == str(b.get("descripcion") or "").strip().casefold()
        )

    def _buscar_fila(fila, candidatas, usadas):
        indice = len(usadas)
        if indice < len(candidatas) and indice not in usadas and _misma_fila(fila, candidatas[indice]):
            usadas.add(indice)
            return candidatas[indice]
        for i, candidata in enumerate(candidatas):
            if i not in usadas and _misma_fila(fila, candidata):
                usadas.add(i)
                return candidata
        return None

    indices_originales_usados = set()
    indices_mercado_usados = set()
    from ..services.traduccion import traducir_recurso_por_codigo
    for indice, fila in enumerate(filas_catalogo):
        original = _buscar_fila(fila, originales, indices_originales_usados)
        fila_mercado = _buscar_fila(fila, filas_mercado, indices_mercado_usados) if filas_mercado else None
        if original is not None and idioma.lower().startswith("en"):
            descripcion_original = str(original.get("descripcion") or "")
            descripcion_visible = traducir_recurso_por_codigo(
                descripcion_original, original.get("codigo"), pais_codigo
            )
            if str(fila.get("descripcion") or "").strip() == str(descripcion_visible or "").strip():
                fila["descripcion"] = descripcion_original

        unidad = str(fila.get("unidad") or "").strip()
        if unidad == "%":
            # El precio de la fila porcentual es derivado y lo recalcula la
            # cascada desde las filas base de coste.
            fila["precio"] = 0.0
            fila["precio_unitario"] = 0.0
            continue

        precio_enviado = float(fila.get("precio") or 0.0)
        precio_original = None
        if original is not None:
            try:
                precio_original = float(
                    original.get("precio") if original.get("precio") is not None
                    else original.get("precio_unitario") or 0.0
                )
            except (TypeError, ValueError):
                precio_original = 0.0
        precio_mostrado = None
        if fila_mercado is not None:
            try:
                precio_mostrado = float(
                    fila_mercado.get("precio") if fila_mercado.get("precio") is not None
                    else fila_mercado.get("precio_unitario") or 0.0
                )
            except (TypeError, ValueError):
                precio_mostrado = None
        elif precio_original is not None:
            precio_mostrado = tasa_convertir_precio(precio_original, factor_vista)

        sin_cambios = (
            precio_original is not None
            and precio_mostrado is not None
            and abs(precio_enviado - precio_mostrado) <= max(1e-6, abs(precio_mostrado) * 1e-8)
        )
        precio_base = precio_original if sin_cambios else _a_moneda_base(precio_enviado, factor_vista)
        fila["precio"] = max(0.0, float(precio_base or 0.0))
        fila["precio_unitario"] = fila["precio"]

    # Recalcula y guarda únicamente importes/costes en moneda base. Las filas
    # visibles de mercado no se escriben como si fueran USD; al volver a abrir
    # la lista el mercado las resolverá de nuevo desde los recursos.
    resultado_base = recalcular_descompuesto_cype(filas_catalogo)
    for indice, fila in enumerate(filas_catalogo):
        fila["importe"] = resultado_base.get("importes", {}).get(indice, 0.0)
        if indice in resultado_base.get("precios_complementarios", {}):
            fila["precio"] = resultado_base["precios_complementarios"][indice]
            fila["precio_unitario"] = fila["precio"]
    if filas_catalogo:
        datos.update({f"coste_{k}": v for k, v in resultado_base.get("costes", {}).items()})
    elif originales:
        # El usuario eliminó todas las filas de una descomposición existente.
        datos.update({
            "coste_materiales": 0.0,
            "coste_mano_obra": 0.0,
            "coste_complementarios": 0.0,
            "coste_otros": 0.0,
        })
    else:
        # Las fichas antiguas sin filas pueden tener costes manuales que no se
        # editan en este formulario: conservarlos si no hay tabla que recalcular.
        for campo in ("coste_materiales", "coste_mano_obra", "coste_complementarios", "coste_otros"):
            datos[campo] = float(getattr(partida, campo, 0) or 0)

    # ``datos`` ya está normalizado a precio por unidad métrica; leer de nuevo
    # el valor crudo del formulario reintroduciría el precio por sq ft.
    precio_enviado = max(0.0, float(datos.get("precio_unitario") or 0.0))
    precio_base_original = float(partida.precio_unitario or 0.0)
    if mercado_visible is not None:
        precio_mostrado = float(mercado_visible.precio_unitario or 0.0)
        if abs(precio_enviado - precio_mostrado) <= max(0.005, abs(precio_mostrado) * 1e-8):
            # No convertir el precio GB mostrado en una sustitución del precio
            # base solo porque el usuario abrió/guardó la ficha.
            datos["precio_unitario"] = precio_base_original
        else:
            coste_base = sum(float(getattr(partida, campo, 0) or 0) for campo in (
                "coste_materiales", "coste_mano_obra", "coste_complementarios", "coste_otros"
            ))
            coste_mercado = sum(float(getattr(mercado_visible, campo, 0) or 0) for campo in (
                "coste_materiales", "coste_mano_obra", "coste_complementarios", "coste_otros"
            ))
            # Conserva la intención de precio/margen en el mercado y guarda un
            # valor base coherente, no el número GBP etiquetado como USD.
            datos["precio_unitario"] = (
                coste_base * precio_enviado / coste_mercado
                if coste_base > 0 and coste_mercado > 0
                else _a_moneda_base(precio_enviado, factor_vista)
            )
    else:
        precio_base_mostrado = tasa_convertir_precio(precio_base_original, factor_vista)
        if abs(precio_enviado - precio_base_mostrado) <= max(0.005, abs(precio_base_mostrado) * 1e-8):
            datos["precio_unitario"] = precio_base_original
        else:
            datos["precio_unitario"] = _a_moneda_base(precio_enviado, factor_vista)

    datos["descomposicion_json"] = json.dumps({
        "origen": "manual",
        "codigo": str(form.get("codigo_externo", "")),
        "unidad": datos["unidad"],
        "filas": filas_catalogo,
    }, ensure_ascii=False)
    datos["codigo_externo"] = str(form.get("codigo_externo", "")).strip()
    precio_anterior = partida.precio_unitario or 0
    _desvincular_clasificacion_si_cambio(partida, datos)
    partida.nombre = nombre
    for campo, valor in datos.items():
        setattr(partida, campo, valor)
    if precio_anterior != partida.precio_unitario:
        partida.fecha_actualizacion_precio = datetime.utcnow()
    if form.get("quitar_imagen"):
        anterior = partida.imagen
        partida.imagen = ""
        _borrar_imagen(anterior, db)
    else:
        archivo = form.get("imagen")
        if isinstance(archivo, UploadFileStarlette) and archivo.filename:
            vieja = partida.imagen
            ruta = await _guardar_imagen(archivo, f"partidas/cat_{partida_id}", db)
            if ruta:
                partida.imagen = ruta
                _borrar_imagen(vieja, db)
    db.commit()
    _sincronizar_recursos(db)
    if precio_anterior != partida.precio_unitario:
        auditoria.registrar_evento(
            db,
            "catalogo.precio_partida",
            entidad="partida",
            entidad_id=partida.id,
            detalle={"de": precio_anterior, "a": partida.precio_unitario or 0},
        )
    return _redirect("/partidas", msg="Partida actualizada.")


def _desvincular_partidas_del_catalogo(db: Session, partida_ids) -> None:
    """Corta el vínculo de las líneas de presupuesto con partidas del catálogo.

    ``presupuesto_items.partida_catalogo_id`` solo recuerda de qué partida
    maestra se copió una línea; el precio ya está copiado en la propia línea.
    Borrar una partida personalizada no debe borrar presupuestos: se anula la
    referencia (FK a NULL) antes del borrado para no violar la integridad
    referencial.
    """
    if not partida_ids:
        return
    db.query(PresupuestoItem).filter(
        PresupuestoItem.partida_catalogo_id.in_(partida_ids)
    ).update(
        {PresupuestoItem.partida_catalogo_id: None},
        synchronize_session=False,
    )


def _es_partida_oficial(partida: Partida) -> bool:
    return bool(
        partida.es_oficial
        or partida.catalogo_uid
        or (
            (partida.codigo_legacy or "").startswith("CT-")
            and (partida.version_catalogo or 0) >= 2
        )
    )


@router.post("/partidas/{partida_id}/eliminar")
def eliminar_partida(partida_id: int, db: Session = Depends(get_db)):
    partida = db.get(Partida, partida_id)
    if partida is None:
        return _redirect("/partidas", error="Partida no encontrada.")
    if _es_partida_oficial(partida):
        partida.es_oficial = True
        partida.oculta = True
        db.commit()
        return _redirect(
            "/partidas",
            msg="Partida oficial ocultada para esta organización.",
        )
    referencia = partida.imagen
    _desvincular_partidas_del_catalogo(db, [partida_id])
    db.delete(partida)
    _borrar_imagen(referencia, db)
    db.commit()
    return _redirect("/partidas", msg="Partida personalizada eliminada.")


@router.post("/partidas/{partida_id}/restaurar")
def restaurar_partida(partida_id: int, db: Session = Depends(get_db)):
    partida = db.get(Partida, partida_id)
    if partida is None:
        return _redirect("/partidas?vista=ocultas", error="Partida no encontrada.")
    partida.oculta = False
    db.commit()
    return _redirect(
        "/partidas?vista=ocultas",
        msg="Partida restaurada en el catálogo activo.",
    )

@router.post("/partidas/bulk-delete")
async def bulk_delete_partidas(request: Request, db: Session = Depends(get_db)):
    # Support both regular form post and JSON
    ids = []
    try:
        form = await request.form()
        ids = [int(x) for x in form.getlist("ids") if str(x).strip()]
    except Exception:
        pass
    if not ids:
        try:
            data = await request.json()
            ids = [int(x) for x in (data.get("ids") or [])]
        except Exception:
            pass
    if not ids:
        return _redirect("/partidas", error="No se seleccionaron partidas.")
    partidas = [p for p in db.query(Partida).filter(Partida.id.in_(ids)).all()]
    oficiales = [p for p in partidas if _es_partida_oficial(p)]
    personalizadas = [p for p in partidas if not _es_partida_oficial(p)]
    if not oficiales and not personalizadas:
        return _redirect("/partidas", error="No se encontraron las partidas seleccionadas.")
    for partida in oficiales:
        partida.es_oficial = True
        partida.oculta = True
    ids_personalizadas = [p.id for p in personalizadas]
    _desvincular_partidas_del_catalogo(db, ids_personalizadas)
    referencias = {p.imagen for p in personalizadas if p.imagen}
    for partida in personalizadas:
        db.delete(partida)
    db.flush()
    for referencia in referencias:
        _borrar_imagen(referencia, db)
    db.commit()
    partes = []
    if oficiales:
        partes.append(f"{len(oficiales)} oficial(es) ocultada(s)")
    if personalizadas:
        partes.append(f"{len(personalizadas)} personalizada(s) eliminada(s)")
    return _redirect("/partidas", msg="; ".join(partes) + ".")


@router.post("/partidas/bulk-restore")
async def bulk_restore_partidas(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    ids = [int(x) for x in form.getlist("ids") if str(x).strip()]
    if not ids:
        return _redirect(
            "/partidas?vista=ocultas", error="No se seleccionaron partidas."
        )
    partidas = db.query(Partida).filter(
        Partida.id.in_(ids), Partida.oculta.is_(True)
    ).all()
    for partida in partidas:
        partida.oculta = False
    db.commit()
    return _redirect(
        "/partidas?vista=ocultas",
        msg=f"Se restauraron {len(partidas)} partidas.",
    )

@router.post("/partidas/bulk-export-selected")
async def bulk_export_selected_partidas(request: Request, db: Session = Depends(get_db)):
    ids = []
    try:
        form = await request.form()
        ids = [int(x) for x in form.getlist("ids") if str(x).strip()]
    except Exception:
        pass
    if not ids:
        try:
            data = await request.json()
            ids = [int(x) for x in (data.get("ids") or [])]
        except Exception:
            pass
    if not ids:
        return _csv_response([], "partidas_seleccionadas.csv")

    partidas = db.query(Partida).filter(Partida.id.in_(ids)).all()
    filas = [[
        "Código", "Nombre", "Descripción", "Unidad", "Precio unitario", "Categoría",
        "Coste materiales", "Coste mano de obra", "Coste complementarios", "Otros",
        "Usos"
    ]]
    for p in partidas:
        filas.append([
            p.codigo_interno or "",
            p.nombre,
            p.descripcion or "",
            p.unidad,
            f"{p.precio_unitario:.2f}".replace(".", ","),
            p.categoria or "",
            f"{(p.coste_materiales or 0):.2f}".replace(".", ","),
            f"{(p.coste_mano_obra or 0):.2f}".replace(".", ","),
            f"{(p.coste_complementarios or 0):.2f}".replace(".", ","),
            f"{(p.coste_otros or 0):.2f}".replace(".", ","),
            p.usos or 0,
        ])
    return _csv_response(filas, "partidas_seleccionadas.csv")

@router.post("/partidas/bulk-move-category")
async def bulk_move_partidas_category(request: Request, db: Session = Depends(get_db)):
    ids = []
    new_cat = ""
    try:
        form = await request.form()
        ids = [int(x) for x in form.getlist("ids") if str(x).strip()]
        new_cat = (form.get("new_category") or "").strip()
    except Exception:
        pass
    if not ids or not new_cat:
        return _redirect("/partidas", error="Selecciona partidas y una categoría destino.")
    count = 0
    for pid in ids:
        p = db.get(Partida, pid)
        if p:
            p.categoria = new_cat
            count += 1
    # Una categoría nueva no hereda una subcategoría posiblemente ajena.
    for pid in ids:
        p = db.get(Partida, pid)
        if p:
            p.subcategoria = ""
            p.apartado = ""
            p.categoria_id = None
            p.codigo_clasificacion = ""
            p.version_catalogo = 0
    db.commit()
    return _redirect("/partidas", msg=f"Se movieron {count} partidas a «{new_cat}».")


@router.post("/partidas/bulk-move-subcategory")
async def bulk_move_partidas_subcategory(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    ids = [int(x) for x in form.getlist("ids") if str(x).strip()]
    categoria = str(form.get("new_category") or "").strip()
    subcategoria = str(form.get("new_subcategory") or "").strip()
    if not ids or not categoria or not subcategoria:
        return _redirect("/partidas", error="Selecciona partidas, su categoría y una subcategoría destino.")
    partidas = db.query(Partida).filter(Partida.id.in_(ids)).all()
    # La jerarquía se protege en servidor: no se puede saltar entre categorías
    # al cambiar únicamente la subcategoría.
    if len(partidas) != len(set(ids)) or any((p.categoria or "") != categoria for p in partidas):
        return _redirect("/partidas", error="Solo puedes mover a una subcategoría partidas que ya pertenecen a esa categoría.")
    for partida in partidas:
        partida.subcategoria = subcategoria
        partida.apartado = ""
        partida.categoria_id = None
        partida.codigo_clasificacion = ""
        partida.version_catalogo = 0
    db.commit()
    return _redirect("/partidas", msg=f"Se movieron {len(partidas)} partidas a «{categoria} · {subcategoria}».")
