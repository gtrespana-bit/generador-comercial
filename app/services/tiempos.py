"""Estimación del tiempo de ejecución de una obra — motor profesional.

Mejoras clave respecto a la versión básica:

* Desglose por oficio: distingue **horas de oficial**, **horas de ayudante/peón**,
  **horas de capataz/encargado** y **horas de equipos/maquinaria** a partir de
  la descripción de cada fila de recurso (p. ej. «Oficial 1ª», «Peón ordinario»).
* Override manual por partida: si la partida tiene ``tiempo_manual_*`` informado,
  ese valor tiene prioridad máxima (permite asignar horas en segundos a partidas
  sin datos desde la propia página de tiempo).
* Duración crítica: además de las horas-hombre totales, se calcula la
  **duración** (max de roles en paralelo) por partida y para la obra completa.
  Es la base para convertir horas en días con una cuadrilla real
  (p. ej. 1 oficial + 1 ayudante trabajan en paralelo → duración = max).
* Catálogo con desglose: el catálogo puede guardar oficial/ayudante/equipo
  por separado; si solo guarda el total se reparte 60/40 por defecto.
* Salida rica para la UI profesional: totales por rol, desglose por capítulo
  con roles, horas por fuente (incluida «manual»), cobertura, etc.
"""

from dataclasses import dataclass, field

from .calculations import partida_activa
from .importer import categoria_coste_cype

# Unidades de tiempo reconocidas en la columna «Unidad» de una fila de
# recursos. Normalizadas en minúsculas y sin acentos.
_UNIDADES_HORA = {
    "h", "hr", "hrs", "hs", "hora", "horas",
}
_UNIDADES_DIA = {
    "d", "dia", "dias", "j", "jornada", "jornadas", "jornal",
}

# Palabras clave para clasificar el rol dentro de mano de obra
_KW_CAPATAZ = ["capataz", "encargado", "jefe", "supervisor", "coordinador", "maestro de obra"]
_KW_OFICIAL = ["oficial", "ofic.", "especialista", "maestro"]
_KW_AYUDANTE = ["ayudante", "ayte", "peon", "auxiliar", "operario", "peon ordinario", "ayud."]

def _normalizar_unidad(unidad) -> str:
    """Normaliza la unidad de una fila: «H.» → «h», «DÍAS» → «dias»…"""
    import unicodedata

    u = unicodedata.normalize("NFD", str(unidad or "").strip().lower())
    u = "".join(c for c in u if unicodedata.category(c) != "Mn")
    return u.replace(".", "").replace(" ", "").replace("/", "")

def _normalizar_texto(txt) -> str:
    import unicodedata
    t = unicodedata.normalize("NFD", str(txt or "").lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return t

def factor_unidad_tiempo(unidad, horas_jornada: float = 8.0):
    """Horas reales que aporta una fila cuya unidad es de tiempo.

    Devuelve ``1`` para unidades horarias, ``horas_jornada`` para unidades
    de día/jornada y ``None`` si la unidad no es de tiempo.
    """
    u = _normalizar_unidad(unidad)
    if not u:
        return None
    if u in _UNIDADES_HORA:
        return 1.0
    if u in _UNIDADES_DIA:
        return max(0.1, float(horas_jornada or 8.0))
    return None


def _campo(fila, nombre):
    return fila.get(nombre) if isinstance(fila, dict) else getattr(fila, nombre, None)


def categoria_fila(fila) -> str:
    """Categoría de coste de una fila: la explícita si existe, si no la
    derivada del grupo/código CYPE (misma regla que el resto del generador)."""
    categoria = str(_campo(fila, "categoria") or "").strip()
    if categoria in {"materiales", "mano_obra", "complementarios", "otros"}:
        return categoria
    return categoria_coste_cype(_campo(fila, "grupo") or "", _campo(fila, "codigo") or "")

def rol_mano_obra(fila) -> str:
    """Clasifica una fila de mano de obra en rol: oficial / ayudante / capataz / otros_mo."""
    # Texto combinado para buscar palabras clave
    txt = _normalizar_texto(" ".join([
        str(_campo(fila, "descripcion") or ""),
        str(_campo(fila, "grupo") or ""),
        str(_campo(fila, "codigo") or ""),
    ]))
    # Capataz tiene prioridad
    for kw in _KW_CAPATAZ:
        if kw in txt:
            return "capataz"
    # Oficial
    for kw in _KW_OFICIAL:
        # evita falso positivo con "no oficial" ? simple
        if kw in txt:
            return "oficial"
    # Ayudante / peón
    for kw in _KW_AYUDANTE:
        if kw in txt:
            return "ayudante"
    # Si no hay pista, miramos si la descripción contiene "peon" sin tilde ya capturado
    # Fallback genérico: si la fila es mano de obra pero no se reconoce, se marca como otros_mo
    # para que la UI pueda agruparlo como ayudante si quiere.
    return "ayudante" if txt else "otros_mo"

def _rol_etiqueta(rol: str) -> str:
    return {
        "oficial": "Oficial",
        "ayudante": "Ayudante / Peón",
        "capataz": "Capataz / Encargado",
        "otros_mo": "Otros MO",
        "equipos": "Equipos",
    }.get(rol, rol)

def horas_por_unidad_descompuesto(filas, horas_jornada: float = 8.0) -> dict:
    """Horas por unidad de partida que aportan las filas de un descompuesto.

    Devuelve::

        {
            "mano_obra": float,   # horas de mano de obra por unidad
            "oficial": float,
            "ayudante": float,
            "capataz": float,
            "otros_mo": float,
            "equipos": float,     # horas de otras filas de tiempo (maquinaria…)
            "total": float,       # mano_obra + equipos
            "duracion": float,    # duración crítica por unidad (max roles en paralelo)
            "detalle": [ {descripcion, codigo, grupo, unidad, categoria,
                          rol, rendimiento, horas_por_unidad} ... ],
        }

    Las filas de porcentaje (``%``), las derivadas (subtotales/totales) y las
    de materiales (unidades que no son de tiempo) no aportan horas.
    """
    mano_obra = 0.0
    oficial = 0.0
    ayudante = 0.0
    capataz = 0.0
    otros_mo = 0.0
    equipos = 0.0
    detalle = []
    for fila in filas:
        if _campo(fila, "tipo") not in (None, "recurso", "recurso "):
            continue
        unidad = str(_campo(fila, "unidad") or "").strip()
        if unidad == "%":
            continue
        factor = factor_unidad_tiempo(unidad, horas_jornada)
        if factor is None:
            continue
        try:
            rendimiento = float(_campo(fila, "rendimiento") or 0.0)
        except (TypeError, ValueError):
            rendimiento = 0.0
        if rendimiento <= 0:
            continue
        horas = round(rendimiento * factor, 4)
        es_mano_obra = categoria_fila(fila) == "mano_obra"
        rol = None
        if es_mano_obra:
            rol = rol_mano_obra(fila)
            mano_obra += horas
            if rol == "oficial":
                oficial += horas
            elif rol == "ayudante":
                ayudante += horas
            elif rol == "capataz":
                capataz += horas
            else:
                otros_mo += horas
                # para totales, otros_mo se suma a ayudante en la vista compacta si se quiere
        else:
            equipos += horas
            rol = "equipos"
        detalle.append(
            {
                "descripcion": str(_campo(fila, "descripcion") or "").strip(),
                "codigo": str(_campo(fila, "codigo") or "").strip(),
                "grupo": str(_campo(fila, "grupo") or "").strip(),
                "unidad": unidad,
                "categoria": "mano_obra" if es_mano_obra else categoria_fila(fila),
                "rol": rol,
                "rol_etiqueta": _rol_etiqueta(rol) if es_mano_obra else "Equipos",
                "rendimiento": rendimiento,
                "horas_por_unidad": horas,
            }
        )
    mano_obra = round(mano_obra, 4)
    oficial = round(oficial, 4)
    ayudante = round(ayudante, 4)
    capataz = round(capataz, 4)
    otros_mo = round(otros_mo, 4)
    equipos = round(equipos, 4)
    total = round(mano_obra + equipos, 4)
    # Duración crítica por unidad: si hay desglose por rol, la cuadrilla puede trabajar en paralelo,
    # duración = max(oficial, ayudante, capataz, otros_mo, equipos?) -> equipos suele ser paralelo también
    # Tomamos max entre roles de MO y equipos si equipos>0 (maquinaria en paralelo). Si no hay roles, duración=mano_obra.
    if mano_obra > 0 or equipos > 0:
        candidatos = [v for v in [oficial, ayudante, capataz, otros_mo] if v > 0]
        # Si hay varios roles, la duración es el máximo (trabajo en paralelo). Si solo hay uno, es ese.
        duracion_mo = max(candidatos) if candidatos else mano_obra
        # Equipos puede ser en paralelo con MO, por lo que duración total = max(duracion_mo, equipos)
        # Si equipos es corto, no alarga; si es largo, sí.
        duracion = round(max(duracion_mo, equipos) if equipos else duracion_mo, 4)
        # Fallback: si no se pudo determinar max (mano_obra genérica sin rol), usar mano_obra
        if duracion == 0:
            duracion = mano_obra
    else:
        duracion = 0.0
    return {
        "mano_obra": mano_obra,
        "oficial": oficial,
        "ayudante": ayudante,
        "capataz": capataz,
        "otros_mo": otros_mo,
        "equipos": equipos,
        "total": total,
        "duracion": duracion,
        "detalle": detalle,
    }


FUENTES = ("descompuesto", "catalogo", "coste", "manual", "sin_datos")

ETIQUETAS_FUENTE = {
    "descompuesto": "Rendimientos del descompuesto",
    "catalogo": "Tiempo estimado del catálogo",
    "coste": "Estimación por coste de mano de obra",
    "manual": "Tiempo asignado manualmente",
    "sin_datos": "Sin datos de tiempo",
}

def _horas_catalogo_detalle(catalogo_entry, horas_jornada: float = 8.0):
    """Normaliza la entrada del catálogo a desglose por rol.

    catalogo_entry puede ser:
      - float (horas totales)  -> reparte 60/40
      - dict {total, oficial, ayudante, equipo} -> usa lo que tenga
    """
    if catalogo_entry is None:
        return None
    if isinstance(catalogo_entry, (int, float)):
        total = float(catalogo_entry)
        if total <= 0:
            return None
        oficial = round(total * 0.6, 4)
        ayudante = round(total * 0.4, 4)
        return {"total": total, "oficial": oficial, "ayudante": ayudante, "capataz": 0.0, "otros_mo": 0.0, "equipos": 0.0, "duracion": oficial if oficial>ayudante else ayudante}
    if isinstance(catalogo_entry, dict):
        total = float(catalogo_entry.get("total") or catalogo_entry.get("horas") or 0)
        oficial = float(catalogo_entry.get("oficial") or catalogo_entry.get("tiempo_oficial_horas") or 0)
        ayudante = float(catalogo_entry.get("ayudante") or catalogo_entry.get("tiempo_ayudante_horas") or 0)
        equipo = float(catalogo_entry.get("equipos") or catalogo_entry.get("tiempo_equipo_horas") or 0)
        if total <= 0 and (oficial+ayudante+equipo) <= 0:
            return None
        if total <= 0:
            total = oficial+ayudante+equipo
        # Si total está pero no desglose, reparte
        if oficial==0 and ayudante==0 and total>0:
            oficial = round(total*0.6,4)
            ayudante = round(total*0.4,4)
        return {"total": round(total,4), "oficial": round(oficial,4), "ayudante": round(ayudante,4), "capataz": 0.0, "otros_mo": 0.0, "equipos": round(equipo,4), "duracion": round(max(oficial, ayudante, equipo) if max(oficial,ayudante,equipo)>0 else total,4)}
    return None

def tiempos_partida(
    partida,
    horas_jornada: float = 8.0,
    tarifa_hora_media: float = 8.0,
    usar_estimacion_coste: bool = True,
    catalogo_tiempos: dict | None = None,
) -> dict:
    """Estimación de horas de una única partida del presupuesto.

    ``catalogo_tiempos`` es un mapa ``{partida_catalogo_id: horas_por_unidad}``
    precargado para no consultar la base de datos por partida. Puede contener
    float o dict con desglose.
    """
    cantidad = float(getattr(partida, "cantidad_total", 0) or 0)
    coste_mo = float(getattr(partida, "coste_mano_obra", 0) or 0)
    descompuesto = getattr(partida, "descomposicion_cype", None)

    # Campos manuales (override)
    manual_total = getattr(partida, "tiempo_manual_horas", None)
    manual_of = getattr(partida, "tiempo_manual_oficial_horas", None)
    manual_ay = getattr(partida, "tiempo_manual_ayudante_horas", None)
    manual_eq = getattr(partida, "tiempo_manual_equipo_horas", None)

    horas_por_unidad = 0.0
    mano_obra_por_unidad = 0.0
    oficial_por_unidad = 0.0
    ayudante_por_unidad = 0.0
    capataz_por_unidad = 0.0
    otros_mo_por_unidad = 0.0
    equipos_por_unidad = 0.0
    duracion_por_unidad = 0.0
    fuente = "sin_datos"
    detalle = []
    nota = ""

    # 0) Override manual — máxima prioridad
    tiene_manual = any(v is not None and str(v).strip() != "" for v in [manual_total, manual_of, manual_ay, manual_eq]) if any(isinstance(v, str) for v in [manual_total, manual_of, manual_ay, manual_eq]) else any(v is not None for v in [manual_total, manual_of, manual_ay, manual_eq])
    # Normalizar: tratamos "" como None, y convertimos a float si es posible
    def _to_float(v):
        if v is None or v == "":
            return None
        try:
            f = float(v)
            return f if f >= 0 else None
        except (TypeError, ValueError):
            return None
    m_total = _to_float(manual_total)
    m_of = _to_float(manual_of)
    m_ay = _to_float(manual_ay)
    m_eq = _to_float(manual_eq)
    # Consideramos manual si alguno está informado y >=0 (0 también es válido para forzar 0)
    if any(v is not None for v in [m_total, m_of, m_ay, m_eq]):
        # Si se informó desglose, el total es la suma; si solo total, repartimos
        if m_of is not None or m_ay is not None or m_eq is not None:
            oficial_por_unidad = m_of or 0.0
            ayudante_por_unidad = m_ay or 0.0
            equipos_por_unidad = m_eq or 0.0
            # Si total también está informado y difiere, priorizamos suma de desglose si desglose>0
            if m_total is not None and (oficial_por_unidad + ayudante_por_unidad + equipos_por_unidad) == 0:
                # solo total informado
                horas_por_unidad = m_total
                mano_obra_por_unidad = m_total
                # repartir total 60/40 a oficial/ayudante
                oficial_por_unidad = round(m_total * 0.6, 4)
                ayudante_por_unidad = round(m_total * 0.4, 4)
                equipos_por_unidad = 0.0
            else:
                horas_por_unidad = round(oficial_por_unidad + ayudante_por_unidad + equipos_por_unidad, 4)
                # Si total manual también existe y es mayor, puede ser que quiera forzar total distinto; respetamos suma de roles
                # Si quiere total exacto, debería ajustarlo vía roles.
                mano_obra_por_unidad = round(oficial_por_unidad + ayudante_por_unidad, 4)
        elif m_total is not None:
            horas_por_unidad = float(m_total)
            mano_obra_por_unidad = horas_por_unidad
            oficial_por_unidad = round(horas_por_unidad * 0.6, 4)
            ayudante_por_unidad = round(horas_por_unidad * 0.4, 4)
            equipos_por_unidad = 0.0
        # duración manual = max de roles en paralelo
        duracion_por_unidad = round(max(oficial_por_unidad, ayudante_por_unidad, capataz_por_unidad, equipos_por_unidad) if max(oficial_por_unidad, ayudante_por_unidad, equipos_por_unidad) > 0 else horas_por_unidad, 4)
        fuente = "manual"
        detalle = []  # manual no tiene detalle de recursos, solo valores directos

    if fuente == "sin_datos" and descompuesto is not None:
        res = horas_por_unidad_descompuesto(descompuesto.filas or [], horas_jornada)
        if res["total"] > 0:
            horas_por_unidad = res["total"]
            mano_obra_por_unidad = res["mano_obra"]
            oficial_por_unidad = res["oficial"]
            ayudante_por_unidad = res["ayudante"]
            capataz_por_unidad = res["capataz"]
            otros_mo_por_unidad = res["otros_mo"]
            equipos_por_unidad = res["equipos"]
            duracion_por_unidad = res["duracion"]
            detalle = res["detalle"]
            fuente = "descompuesto"
        else:
            nota = "El descompuesto no tiene filas con unidad de tiempo (h, día…)."

    if fuente == "sin_datos":
        catalogo_id = getattr(partida, "partida_catalogo_id", None)
        if catalogo_id and catalogo_tiempos:
            t = catalogo_tiempos.get(catalogo_id)
            if t is not None:
                det = _horas_catalogo_detalle(t, horas_jornada)
                if det:
                    horas_por_unidad = det["total"]
                    mano_obra_por_unidad = det["total"] - det["equipos"]
                    oficial_por_unidad = det["oficial"]
                    ayudante_por_unidad = det["ayudante"]
                    capataz_por_unidad = det.get("capataz", 0.0)
                    equipos_por_unidad = det["equipos"]
                    duracion_por_unidad = det["duracion"]
                    fuente = "catalogo"

    if fuente == "sin_datos":
        if usar_estimacion_coste and coste_mo > 0 and tarifa_hora_media > 0:
            horas_por_unidad = round(coste_mo / tarifa_hora_media, 4)
            mano_obra_por_unidad = horas_por_unidad
            oficial_por_unidad = round(horas_por_unidad * 0.6, 4)
            ayudante_por_unidad = round(horas_por_unidad * 0.4, 4)
            duracion_por_unidad = round(max(oficial_por_unidad, ayudante_por_unidad), 4)
            fuente = "coste"

    # Horas totales por partida
    horas = round(cantidad * horas_por_unidad, 2)
    mano_obra_h = round(cantidad * mano_obra_por_unidad, 2)
    oficial_h = round(cantidad * oficial_por_unidad, 2)
    ayudante_h = round(cantidad * ayudante_por_unidad, 2)
    capataz_h = round(cantidad * capataz_por_unidad, 2)
    otros_mo_h = round(cantidad * otros_mo_por_unidad, 2)
    equipos_h = round(cantidad * equipos_por_unidad, 2)
    duracion_h = round(cantidad * duracion_por_unidad, 2)

    return {
        "partida_id": getattr(partida, "id", None),
        "capitulo": getattr(getattr(partida, "capitulo", None), "nombre", ""),
        "nombre": getattr(partida, "nombre", ""),
        "unidad": getattr(partida, "unidad", "") or "ud",
        "cantidad": cantidad,
        "horas_por_unidad": round(horas_por_unidad, 4),
        "horas": horas,
        "mano_obra_por_unidad": round(mano_obra_por_unidad, 4),
        "oficial_por_unidad": round(oficial_por_unidad, 4),
        "ayudante_por_unidad": round(ayudante_por_unidad, 4),
        "capataz_por_unidad": round(capataz_por_unidad, 4),
        "otros_mo_por_unidad": round(otros_mo_por_unidad, 4),
        "equipos_por_unidad": round(equipos_por_unidad, 4),
        "duracion_por_unidad": round(duracion_por_unidad, 4),
        "mano_obra_h": mano_obra_h,
        "oficial_h": oficial_h,
        "ayudante_h": ayudante_h,
        "capataz_h": capataz_h,
        "otros_mo_h": otros_mo_h,
        "equipos_h": equipos_h,
        "duracion_h": duracion_h,
        "fuente": fuente,
        "fuente_etiqueta": ETIQUETAS_FUENTE[fuente],
        "detalle": detalle,
        "nota": nota,
        "coste_mano_obra": coste_mo,
        "activa": bool(partida_activa(partida)),
        # Para edición rápida
        "manual_total": m_total,
        "manual_oficial": m_of,
        "manual_ayudante": m_ay,
        "manual_equipo": m_eq,
    }


def calcular_tiempos_presupuesto(
    presupuesto,
    db=None,
    horas_jornada: float = 8.0,
    tarifa_hora_media: float = 8.0,
    usar_estimacion_coste: bool = True,
) -> dict:
    """Estimación completa de tiempos de un presupuesto.

    Devuelve totales (horas, días laborables, semanas), desglose por
    capítulo, desglose por partida y el resumen de fuentes de datos para
    saber qué parte de la estimación es medida y cuál estimada.
    """
    # Mapa partida_catalogo_id → tiempo_estimado_horas (una sola consulta)
    catalogo_tiempos: dict = {}
    if db is not None:
        ids = {
            getattr(p, "partida_catalogo_id", None)
            for cap in presupuesto.capitulos
            for p in cap.partidas
            if getattr(p, "partida_catalogo_id", None)
        }
        if ids:
            from ..models import Partida

            for cat in db.query(Partida).filter(Partida.id.in_(ids)).all():
                # Prioridad: desglose oficial/ayudante si existe, si no total
                if getattr(cat, "tiempo_oficial_horas", None) is not None or getattr(cat, "tiempo_ayudante_horas", None) is not None:
                    catalogo_tiempos[cat.id] = {
                        "total": cat.tiempo_estimado_horas or 0,
                        "oficial": cat.tiempo_oficial_horas or 0,
                        "ayudante": cat.tiempo_ayudante_horas or 0,
                        "equipos": cat.tiempo_equipo_horas or 0,
                    }
                    # Si total no está pero hay desglose, calcular total
                    if not catalogo_tiempos[cat.id]["total"]:
                        catalogo_tiempos[cat.id]["total"] = (catalogo_tiempos[cat.id]["oficial"] or 0) + (catalogo_tiempos[cat.id]["ayudante"] or 0) + (catalogo_tiempos[cat.id]["equipos"] or 0)
                elif getattr(cat, "tiempo_estimado_horas", None):
                    catalogo_tiempos[cat.id] = cat.tiempo_estimado_horas

    partidas = []
    total_horas = 0.0
    total_mano_obra = 0.0
    total_oficial = 0.0
    total_ayudante = 0.0
    total_capataz = 0.0
    total_otros_mo = 0.0
    total_equipos = 0.0
    total_duracion = 0.0
    resumen_fuentes = {f: 0 for f in FUENTES}
    horas_fuentes = {f: 0.0 for f in FUENTES}
    horas_oficial_fuentes = {f: 0.0 for f in FUENTES}
    horas_ayudante_fuentes = {f: 0.0 for f in FUENTES}
    sin_datos = []
    por_capitulo: dict[str, dict] = {}

    for cap in presupuesto.capitulos:
        for p in cap.partidas:
            t = tiempos_partida(
                p,
                horas_jornada=horas_jornada,
                tarifa_hora_media=tarifa_hora_media,
                usar_estimacion_coste=usar_estimacion_coste,
                catalogo_tiempos=catalogo_tiempos,
            )
            partidas.append(t)
            if not t["activa"]:
                continue
            total_horas += t["horas"]
            total_mano_obra += t["mano_obra_h"]
            total_oficial += t["oficial_h"]
            total_ayudante += t["ayudante_h"]
            total_capataz += t["capataz_h"]
            total_otros_mo += t["otros_mo_h"]
            total_equipos += t["equipos_h"]
            total_duracion += t["duracion_h"]
            resumen_fuentes[t["fuente"]] += 1
            horas_fuentes[t["fuente"]] += t["horas"]
            horas_oficial_fuentes[t["fuente"]] += t["oficial_h"]
            horas_ayudante_fuentes[t["fuente"]] += t["ayudante_h"]
            capitulo_nombre = t["capitulo"] or cap.nombre
            if capitulo_nombre not in por_capitulo:
                por_capitulo[capitulo_nombre] = {"horas": 0.0, "oficial": 0.0, "ayudante": 0.0, "equipos": 0.0, "duracion": 0.0, "n_partidas": 0}
            por_capitulo[capitulo_nombre]["horas"] += t["horas"]
            por_capitulo[capitulo_nombre]["oficial"] += t["oficial_h"]
            por_capitulo[capitulo_nombre]["ayudante"] += t["ayudante_h"]
            por_capitulo[capitulo_nombre]["equipos"] += t["equipos_h"]
            por_capitulo[capitulo_nombre]["duracion"] += t["duracion_h"]
            por_capitulo[capitulo_nombre]["n_partidas"] += 1
            if t["fuente"] == "sin_datos":
                sin_datos.append(t["nombre"])

    total_horas = round(total_horas, 2)
    total_mano_obra = round(total_mano_obra, 2)
    total_oficial = round(total_oficial, 2)
    total_ayudante = round(total_ayudante, 2)
    total_capataz = round(total_capataz, 2)
    total_otros_mo = round(total_otros_mo, 2)
    total_equipos = round(total_equipos, 2)
    total_duracion = round(total_duracion, 2)
    jornada = max(0.1, float(horas_jornada or 8.0))
    total_dias = round(total_horas / jornada, 1)
    total_dias_duracion = round(total_duracion / jornada, 1)
    total_semanas = round(total_dias / 5.0, 1)
    total_semanas_duracion = round(total_dias_duracion / 5.0, 1)

    capitulos = [
        {
            "nombre": nombre,
            "horas": round(datos["horas"], 2),
            "oficial_h": round(datos["oficial"], 2),
            "ayudante_h": round(datos["ayudante"], 2),
            "equipos_h": round(datos["equipos"], 2),
            "duracion_h": round(datos["duracion"], 2),
            "pct": round(datos["horas"] / total_horas * 100, 1) if total_horas else 0.0,
            "pct_duracion": round(datos["duracion"] / total_duracion * 100, 1) if total_duracion else 0.0,
            "n_partidas": datos["n_partidas"],
        }
        for nombre, datos in sorted(
            por_capitulo.items(), key=lambda kv: kv[1]["horas"], reverse=True
        )
    ]

    # Estimación de cuadrillas recomendadas
    # Suponiendo cuadrilla estándar 1 oficial + 1 ayudante trabajando en paralelo,
    # la duración ya es max(oficial, ayudante) por partida. Para estimar nº operarios totales:
    # oficial_dias = total_oficial / jornada, ayudante_dias similar.
    oficial_dias = round(total_oficial / jornada, 1) if total_oficial else 0.0
    ayudante_dias = round(total_ayudante / jornada, 1) if total_ayudante else 0.0

    return {
        "horas_jornada": jornada,
        "tarifa_hora_media": float(tarifa_hora_media or 0),
        "usar_estimacion_coste": bool(usar_estimacion_coste),
        "total_horas": total_horas,
        "total_mano_obra_h": total_mano_obra,
        "total_oficial_h": total_oficial,
        "total_ayudante_h": total_ayudante,
        "total_capataz_h": total_capataz,
        "total_otros_mo_h": total_otros_mo,
        "total_equipos_h": total_equipos,
        "total_duracion_h": total_duracion,
        "total_dias": total_dias,
        "total_dias_duracion": total_dias_duracion,
        "total_semanas": total_semanas,
        "total_semanas_duracion": total_semanas_duracion,
        "oficial_dias": oficial_dias,
        "ayudante_dias": ayudante_dias,
        "n_partidas": len(partidas),
        "n_partidas_activas": sum(1 for t in partidas if t["activa"]),
        "n_con_datos": sum(
            1 for t in partidas if t["activa"] and t["fuente"] != "sin_datos"
        ),
        "resumen_fuentes": resumen_fuentes,
        "horas_fuentes": {k: round(v, 2) for k, v in horas_fuentes.items()},
        "horas_oficial_fuentes": {k: round(v, 2) for k, v in horas_oficial_fuentes.items()},
        "horas_ayudante_fuentes": {k: round(v, 2) for k, v in horas_ayudante_fuentes.items()},
        "sin_datos": sin_datos,
        "capitulos": capitulos,
        "partidas": partidas,
        "etiquetas_fuente": ETIQUETAS_FUENTE,
    }
