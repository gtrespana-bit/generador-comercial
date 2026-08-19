"""Carga del catálogo propio de partidas y recursos (basedatos_partidas).

La base de datos de precios vive fuera de la app, en `basedatos_partidas/`,
como fuente de verdad editable. Este módulo la traduce al modelo de CotizaT
(partidas con descomposición, categorías y recursos) sin pasar por Excel.

Se usa al sembrar el modo demo y, una sola vez, al actualizar instalaciones
que todavía tenían el catálogo de prueba antiguo.
"""
from __future__ import annotations

import importlib.util
import json
import logging
import sys
from functools import lru_cache
from pathlib import Path

from sqlalchemy import func, or_, update
from sqlalchemy.orm import Session

from ..models import CategoriaPartida, Configuracion, Partida, Recurso

log = logging.getLogger("cotizat")

# basedatos_partidas/ está al lado de app/
_RAIZ = Path(__file__).resolve().parents[2]
_BASE_DATOS = _RAIZ / "basedatos_partidas"
_DESCOMPUESTOS = _BASE_DATOS / "datos" / "descompuestos"
_RECURSOS = _BASE_DATOS / "datos" / "recursos.json"
_CLASIFICACION = _BASE_DATOS / "datos" / "clasificacion.json"

# Mismo margen por defecto que basedatos_partidas/descompuestos.py
MARGEN_DEFECTO = 0.30
# Versión del catálogo propio. Cada ampliación del catálogo que añade partidas
# nuevas debe subir esta versión: ``actualizar_taxonomia_catalogo_propio`` solo
# incorpora conceptos cuyo ``version_alta_catalogo`` sea posterior a la versión
# ya aplicada a una organización. Las partidas nuevas (sin ``codigo_legacy``)
# heredan esta versión como su ``version_alta_catalogo``.
CATALOGO_VERSION = 3

# Unidades del generador → las que acepta el validador de la app
_EQUIV_UNIDADES = {
    "m²": "m2", "M2": "m2", "M²": "m2",
    "m³": "m3", "M3": "m3", "M³": "m3",
    "u": "ud", "und": "ud", "uds": "ud", "UD": "ud", "Ud": "ud",
    "h": "hora", "hr": "hora", "H": "hora",
    "Kg": "kg", "KG": "kg",
    "ML": "ml", "Ml": "ml",
    "pa": "glb", "PA": "glb",
}

# Grupo del cuadro de precios → categoría de coste de la app
_GRUPO_A_CATEGORIA = {
    "materiales": "materiales",
    "mano_obra": "mano_obra",
    "maquinaria": "otros",
    "equipos": "otros",
    "otros": "otros",
    "complementarios": "complementarios",
}

_ETIQUETA_GRUPO = {
    "materiales": "Materiales",
    "mano_obra": "Mano de obra",
    "maquinaria": "Equipo y maquinaria",
    "equipos": "Equipo y maquinaria",
    "otros": "Equipos y otros",
    "complementarios": "Costes directos complementarios",
}


def disponible() -> bool:
    """True si el catálogo propio está empaquetado junto a la aplicación."""
    return (
        _DESCOMPUESTOS.is_dir()
        and any(_DESCOMPUESTOS.glob("*.json"))
        and _RECURSOS.is_file()
        and _CLASIFICACION.is_file()
    )


def _cargar_modulo_descompuestos():
    """Carga basedatos_partidas/descompuestos.py sin instalarlo como paquete."""
    ruta = _BASE_DATOS / "descompuestos.py"
    if not ruta.is_file():
        raise FileNotFoundError(f"No se encuentra {ruta}")
    nombre = "cotizat_basedatos_descompuestos"
    if nombre in sys.modules:
        return sys.modules[nombre]
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    if spec is None or spec.loader is None:
        raise ImportError(f"No se pudo cargar {ruta}")
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = modulo
    spec.loader.exec_module(modulo)
    return modulo


def _unidad(valor: str) -> str:
    texto = str(valor or "ud").strip() or "ud"
    return _EQUIV_UNIDADES.get(texto, texto)


def _categoria_coste(grupo: str) -> str:
    return _GRUPO_A_CATEGORIA.get(str(grupo or "").strip().lower(), "otros")


def _redondear2(valor: float) -> float:
    return round(float(valor or 0) + 1e-12, 2)


@lru_cache(maxsize=1)
def construir_catalogo() -> dict:
    """Resuelve las partidas del catálogo y el cuadro de precios en memoria.

    El resultado se cachea: sembrar el catálogo y migrar una instalación
    antigua no vuelven a recorrer los JSON.
    """
    if not disponible():
        return {"partidas": [], "recursos": [], "categorias": [], "ok": False}

    mod = _cargar_modulo_descompuestos()
    catalogo_recursos = mod.cargar_recursos()
    taxonomia = mod.cargar_clasificacion()

    # Nodos normalizados del árbol. Las etiquetas denormalizadas viajan
    # también en cada nodo para mantener compatibles las vistas y copias v1.
    categorias: list[dict] = []
    for cod_cap, cap in (taxonomia.get("capitulos") or {}).items():
        nombre_cap = str(cap.get("nombre") or "").strip()
        if not nombre_cap:
            continue
        etiqueta_cap = f"{cod_cap} {nombre_cap}"
        categorias.append({
            "codigo": cod_cap,
            "segmento": cod_cap,
            "nombre": nombre_cap,
            "nivel": 1,
            "parent_codigo": None,
            "categoria": etiqueta_cap,
            "subcategoria": "",
        })
        for cod_sub, sub in (cap.get("subcapitulos") or {}).items():
            nombre_sub = str(sub.get("nombre") or "").strip()
            codigo_sub = f"{cod_cap}.{cod_sub}"
            etiqueta_sub = f"{codigo_sub} {nombre_sub}"
            categorias.append({
                "codigo": codigo_sub,
                "segmento": cod_sub,
                "nombre": nombre_sub,
                "nivel": 2,
                "parent_codigo": cod_cap,
                "categoria": etiqueta_cap,
                "subcategoria": etiqueta_sub,
            })
            for cod_ap, nombre_ap in (sub.get("apartados") or {}).items():
                codigo_ap = f"{codigo_sub}.{cod_ap}"
                categorias.append({
                    "codigo": codigo_ap,
                    "segmento": cod_ap,
                    "nombre": str(nombre_ap or "").strip(),
                    "nivel": 3,
                    "parent_codigo": codigo_sub,
                    "categoria": etiqueta_cap,
                    "subcategoria": etiqueta_sub,
                })

    recursos_out: list[dict] = []
    for codigo, ficha in catalogo_recursos.items():
        # Los compuestos (morteros) se abren en sus componentes dentro de cada
        # partida; en el cuadro de precios solo viven las líneas físicas.
        if ficha.get("composicion"):
            continue
        grupo = str(ficha.get("grupo") or "otros")
        categoria = _categoria_coste(grupo)
        recursos_out.append({
            "codigo": str(codigo),
            "descripcion": str(ficha.get("descripcion") or codigo),
            "unidad": _unidad(ficha.get("unidad") or "ud"),
            "categoria": categoria,
            "grupo": _ETIQUETA_GRUPO.get(grupo, grupo.replace("_", " ").title()),
            "precio": float(ficha.get("precio") or 0),
        })

    partidas_out: list[dict] = []
    for fuente in sorted(_DESCOMPUESTOS.glob("*.json")):
        partida = json.loads(fuente.read_text(encoding="utf-8"))
        try:
            recursos = mod.resolver_recursos(partida, catalogo_recursos)
            ubicacion = mod.ubicar(partida, taxonomia)
        except Exception as exc:
            log.warning("Partida %s omitida al resolver catálogo: %s", fuente.name, exc)
            continue

        filas: list[dict] = []
        costes = {"materiales": 0.0, "mano_obra": 0.0, "complementarios": 0.0, "otros": 0.0}
        horas_mo = 0.0
        for recurso in recursos:
            grupo = str(recurso.get("grupo") or "otros")
            categoria = _categoria_coste(grupo)
            rendimiento = float(recurso.get("rendimiento") or 0)
            precio = float(recurso.get("precio") or 0)
            importe = _redondear2(rendimiento * precio)
            costes[categoria] = _redondear2(costes[categoria] + importe)
            if categoria == "mano_obra":
                horas_mo += rendimiento
            filas.append({
                "tipo": "recurso",
                "grupo": _ETIQUETA_GRUPO.get(grupo, grupo.replace("_", " ").title()),
                "categoria": categoria,
                "codigo": str(recurso.get("codigo") or ""),
                "unidad": _unidad(recurso.get("unidad") or "ud"),
                "descripcion": str(recurso.get("descripcion") or ""),
                "rendimiento": rendimiento,
                "precio": precio,
                "precio_unitario": precio,
                "importe": importe,
                "numero": len(filas) + 1,
                "celdas": [],
                "formulas": {},
            })

        # Costes directos complementarios (% sobre la suma de los demás),
        # igual que en la hoja de descompuesto.
        pct = float(partida.get("complementarios_pct", 2) or 0)
        base = _redondear2(sum(costes.values()))
        if pct:
            importe_comp = _redondear2(base * pct / 100.0)
            costes["complementarios"] = _redondear2(
                costes["complementarios"] + importe_comp
            )
            filas.append({
                "tipo": "recurso",
                "grupo": _ETIQUETA_GRUPO["complementarios"],
                "categoria": "complementarios",
                "codigo": "",
                "unidad": "%",
                "descripcion": "Costes directos complementarios",
                "rendimiento": pct,
                "precio": base,
                "precio_unitario": base,
                "importe": importe_comp,
                "numero": len(filas) + 1,
                "celdas": [],
                "formulas": {},
            })

        coste_directo = _redondear2(sum(costes.values()))
        margen = float(partida.get("margen", MARGEN_DEFECTO) or 0)
        precio_venta = _redondear2(coste_directo * (1.0 + margen))
        unidad = _unidad(partida.get("unidad") or "ud")
        codigo = str(partida.get("codigo") or fuente.stem)
        nombre_cap = str(ubicacion.get("capitulo") or "").strip()
        nombre_sub = str(ubicacion.get("subcapitulo") or "").strip()
        nombre_apartado = str(ubicacion.get("apartado") or "").strip()
        cod_cap = ubicacion["capitulo_cod"]
        cod_sub = f"{cod_cap}.{ubicacion['subcapitulo_cod']}"
        cod_apartado = f"{cod_sub}.{ubicacion['apartado_cod']}"
        etiqueta_cap = f"{cod_cap} {nombre_cap}"
        etiqueta_sub = f"{cod_sub} {nombre_sub}"
        etiqueta_apartado = f"{cod_apartado} {nombre_apartado}"
        notas = f"Coste directo {coste_directo:.2f} USD + margen {margen * 100:.0f}%"
        pc = partida.get("producto_cliente")
        if isinstance(pc, dict) and pc:
            notas += (
                f" | NO INCLUYE el producto de elección del cliente: "
                f"{pc.get('tipo', '')} "
                f"({pc.get('consumo', '')} {pc.get('unidad', '')}/{unidad})"
            )

        codigo_legacy = str(partida.get("codigo_legacy") or "")
        catalogo_uid = str(partida.get("catalogo_uid") or codigo_legacy or codigo)
        version_alta = int(
            partida.get("version_alta_catalogo")
            or (2 if codigo_legacy else CATALOGO_VERSION)
        )
        partidas_out.append({
            "codigo": codigo,
            "codigo_legacy": codigo_legacy,
            "catalogo_uid": catalogo_uid,
            "version_alta_catalogo": version_alta,
            "codigo_clasificacion": cod_apartado,
            "nombre": str(partida.get("titulo") or codigo).strip(),
            "descripcion": str(partida.get("descripcion") or "").strip(),
            "unidad": unidad,
            "precio_unitario": precio_venta,
            "categoria": etiqueta_cap or "99 Partidas personalizadas",
            "subcategoria": etiqueta_sub,
            "apartado": etiqueta_apartado,
            "coste_materiales": costes["materiales"],
            "coste_mano_obra": costes["mano_obra"],
            "coste_complementarios": costes["complementarios"],
            "coste_otros": costes["otros"],
            "tiempo_estimado_horas": round(horas_mo, 4) if horas_mo else None,
            "rendimiento": f"{horas_mo:.3f} h/{unidad}" if horas_mo else "",
            "notas_tecnicas": notas,
            "descomposicion_json": json.dumps({
                "origen": "catalogo_propio",
                "version_catalogo": CATALOGO_VERSION,
                "codigo": codigo,
                "codigo_legacy": str(partida.get("codigo_legacy") or ""),
                "unidad": unidad,
                "filas": filas,
            }, ensure_ascii=False),
        })

    return {
        "ok": True,
        "partidas": partidas_out,
        "recursos": recursos_out,
        "categorias": categorias,
        "n_partidas": len(partidas_out),
        "n_recursos": len(recursos_out),
    }


def _sembrar_categorias(
    db: Session, categorias: list[dict]
) -> dict[str, CategoriaPartida]:
    """Crea/actualiza el árbol oficial y devuelve sus nodos por código."""
    existentes = {
        c.codigo_completo: c
        for c in db.query(CategoriaPartida).filter(
            CategoriaPartida.codigo_completo.isnot(None)
        ).all()
        if c.codigo_completo
    }
    # Primero padres y después hijos; el flush asigna ids para las FK.
    for item in sorted(categorias, key=lambda c: (c["nivel"], c["codigo"])):
        codigo = item["codigo"]
        nodo = existentes.get(codigo)
        parent = existentes.get(item.get("parent_codigo"))
        if nodo is None:
            nodo = CategoriaPartida(categoria=item["categoria"][:80])
            db.add(nodo)
            existentes[codigo] = nodo
        nodo.categoria = item["categoria"][:80]
        nodo.subcategoria = (item.get("subcategoria") or "")[:80]
        nodo.parent = parent
        nodo.codigo_segmento = item["segmento"]
        nodo.codigo_completo = codigo
        nodo.nombre = item["nombre"][:120]
        nodo.nivel = int(item["nivel"])
        nodo.orden = int(item["segmento"])
        nodo.ambito = "reforma"
        nodo.activa = True
        nodo.oficial = True
        db.flush()
    return existentes


def _sembrar_recursos(db: Session, recursos: list[dict]) -> int:
    from .recursos import clave_recurso

    existentes = {r.clave for r in db.query(Recurso).all()}
    creados = 0
    for item in recursos:
        clave = clave_recurso(
            item["codigo"], item["descripcion"], item["unidad"], item["categoria"]
        )
        if clave in existentes:
            continue
        db.add(Recurso(
            codigo=item["codigo"][:80],
            descripcion=item["descripcion"][:250],
            unidad=item["unidad"][:30],
            categoria=item["categoria"][:30],
            grupo=str(item.get("grupo") or "")[:250],
            precio=float(item.get("precio") or 0),
        ))
        existentes.add(clave)
        creados += 1
    return creados


def _crear_partida_oficial(
    item: dict,
    nodos: dict[str, CategoriaPartida],
) -> Partida:
    codigo = str(item.get("codigo") or "")
    return Partida(
        nombre=str(item.get("nombre") or codigo)[:200],
        descripcion=item.get("descripcion") or "",
        precio_unitario=float(item.get("precio_unitario") or 0),
        unidad=(item.get("unidad") or "ud")[:30],
        categoria=(item.get("categoria") or "General")[:80],
        subcategoria=(item.get("subcategoria") or "")[:80],
        apartado=(item.get("apartado") or "")[:120],
        nodo_categoria=nodos.get(item.get("codigo_clasificacion")),
        codigo_clasificacion=(item.get("codigo_clasificacion") or "")[:20],
        codigo_legacy=(item.get("codigo_legacy") or "")[:80],
        version_catalogo=CATALOGO_VERSION,
        catalogo_uid=(item.get("catalogo_uid") or "")[:100] or None,
        es_oficial=True,
        oculta=False,
        version_alta_catalogo=int(item.get("version_alta_catalogo") or CATALOGO_VERSION),
        codigo_interno=codigo[:80],
        codigo_externo=codigo[:100],
        coste_materiales=float(item.get("coste_materiales") or 0),
        coste_mano_obra=float(item.get("coste_mano_obra") or 0),
        coste_complementarios=float(item.get("coste_complementarios") or 0),
        coste_otros=float(item.get("coste_otros") or 0),
        tiempo_estimado_horas=item.get("tiempo_estimado_horas"),
        rendimiento=(item.get("rendimiento") or "")[:120],
        notas_tecnicas=item.get("notas_tecnicas") or "",
        descomposicion_json=item.get("descomposicion_json") or "[]",
    )


def _sembrar_partidas(
    db: Session,
    partidas: list[dict],
    nodos: dict[str, CategoriaPartida],
) -> int:
    """Crea partidas oficiales ausentes en una instalación nueva."""
    existentes = {p.nombre for p in db.query(Partida.nombre).all()}
    creadas = 0
    for item in partidas:
        nombre = (item.get("nombre") or "").strip()
        if not nombre or nombre in existentes:
            continue
        db.add(_crear_partida_oficial(item, nodos))
        existentes.add(nombre)
        creadas += 1
    return creadas


def sembrar_catalogo_propio(db: Session) -> dict:
    """Siembra partidas, recursos y categorías del catálogo propio.

    Idempotente: no duplica por nombre (partidas) ni por clave (recursos).
    Devuelve contadores {partidas, recursos, ok}.
    """
    datos = construir_catalogo()
    if not datos.get("ok"):
        log.warning(
            "Catálogo propio no disponible en %s; no se siembran partidas.",
            _BASE_DATOS,
        )
        return {"ok": False, "partidas": 0, "recursos": 0}

    nodos = _sembrar_categorias(db, datos["categorias"])
    n_rec = _sembrar_recursos(db, datos["recursos"])
    n_par = _sembrar_partidas(db, datos["partidas"], nodos)
    cfg = db.query(Configuracion).first()
    if cfg is not None:
        cfg.version_catalogo = CATALOGO_VERSION
    db.commit()
    log.info(
        "Catálogo propio sembrado: %s partidas nuevas, %s recursos nuevos "
        "(fuente: %s partidas / %s recursos).",
        n_par, n_rec, datos["n_partidas"], datos["n_recursos"],
    )
    return {"ok": True, "partidas": n_par, "recursos": n_rec,
            "total_partidas": datos["n_partidas"], "total_recursos": datos["n_recursos"]}


def actualizar_taxonomia_catalogo_propio(db: Session) -> dict:
    """Reclasifica partidas oficiales v1 sin alterar precios del usuario.

    Se busca por código legado/actual y se conserva el mismo ``Partida.id``;
    por eso las líneas de presupuestos siguen vinculadas. Solo cambian ruta,
    código visible y metadatos de versión. Conserva la visibilidad elegida por
    la organización e incorpora únicamente altas de versiones posteriores.

    Rendimiento: la lectura inicial trae solo las columnas de identidad (sin
    ``descomposicion_json``), los descompuestos de las filas afectadas se
    leen a demanda por bloques de ids y la escritura se hace con un UPDATE
    ejecutado en lote (executemany) en lugar de una sentencia por partida.
    """
    datos = construir_catalogo()
    if not datos.get("ok"):
        return {"ok": False, "actualizadas": 0}
    nodos = _sembrar_categorias(db, datos["categorias"])
    cfg = db.query(Configuracion).first()
    version_previa = int(getattr(cfg, "version_catalogo", 0) or 0)

    # Escaneo ligero: columnas de identidad únicamente (sin JSON pesados).
    filas_ligeras = db.query(
        Partida.id,
        Partida.nombre,
        Partida.catalogo_uid,
        Partida.codigo_legacy,
        Partida.codigo_interno,
        Partida.codigo_externo,
    ).all()
    ids_por_uid: dict[str, int] = {}
    ids_por_codigo: dict[str, int] = {}
    nombres = set()
    for fila in filas_ligeras:
        nombres.add(fila.nombre)
        if fila.catalogo_uid:
            ids_por_uid.setdefault(str(fila.catalogo_uid), fila.id)
        for codigo in (fila.codigo_legacy, fila.codigo_interno, fila.codigo_externo):
            codigo = str(codigo or "").strip()
            if codigo:
                ids_por_codigo.setdefault(codigo, fila.id)

    def _json_por_ids(ids: list[int]) -> dict[int, str]:
        resultado: dict[int, str] = {}
        for inicio in range(0, len(ids), 400):
            bloque = ids[inicio:inicio + 400]
            for pid, bruto in db.query(
                Partida.id, Partida.descomposicion_json
            ).filter(Partida.id.in_(bloque)).all():
                resultado[pid] = bruto or "[]"
        return resultado

    actualizaciones: list[dict] = []
    incorporadas = 0
    for item in datos["partidas"]:
        uid = str(item.get("catalogo_uid") or "")
        legacy = str(item.get("codigo_legacy") or "")
        nuevo = str(item.get("codigo") or "")
        version_alta = int(item.get("version_alta_catalogo") or CATALOGO_VERSION)
        partida_id = ids_por_uid.get(uid) or ids_por_codigo.get(legacy) or ids_por_codigo.get(nuevo)
        if partida_id is None:
            # En v2 se respetan los borrados físicos anteriores. A partir de
            # ahí, solo se incorporan conceptos cuya versión de alta sea
            # posterior a la versión ya aplicada a la organización.
            if (
                version_previa >= 2
                and version_alta > version_previa
                and str(item.get("nombre") or "") not in nombres
            ):
                db.add(_crear_partida_oficial(item, nodos))
                nombres.add(str(item.get("nombre") or ""))
                incorporadas += 1
            continue
        nodo = nodos.get(item.get("codigo_clasificacion"))
        actualizaciones.append({
            "id": partida_id,
            "categoria": item["categoria"][:80],
            "subcategoria": item["subcategoria"][:80],
            "apartado": item["apartado"][:120],
            "categoria_id": nodo.id if nodo is not None else None,
            "codigo_clasificacion": item["codigo_clasificacion"][:20],
            "codigo_legacy": legacy[:80],
            "codigo_interno": nuevo[:80],
            "codigo_externo": nuevo[:100],
            "version_catalogo": CATALOGO_VERSION,
            "catalogo_uid": uid[:100] or None,
            "es_oficial": True,
            # Nunca se fuerza ``oculta``: es una preferencia de la organización.
            "version_alta_catalogo": version_alta,
        })
        ids_por_uid[uid] = partida_id

    # El descompuesto puede haber sido ajustado por la organización. Solo se
    # actualizan sus metadatos de identidad, nunca recursos ni precios: se
    # leen los JSON de las filas afectadas por bloques y se parchean en lote.
    if actualizaciones:
        json_por_id = _json_por_ids([a["id"] for a in actualizaciones])
        for datos_fila in actualizaciones:
            try:
                descomp = json.loads(json_por_id.get(datos_fila["id"], "[]"))
            except (TypeError, ValueError):
                descomp = []
            if isinstance(descomp, dict):
                descomp["codigo"] = datos_fila["codigo_interno"]
                descomp["codigo_legacy"] = datos_fila["codigo_legacy"]
                descomp["version_catalogo"] = CATALOGO_VERSION
                datos_fila["descomposicion_json"] = json.dumps(
                    descomp, ensure_ascii=False
                )
        for inicio in range(0, len(actualizaciones), 400):
            db.execute(
                update(Partida),
                actualizaciones[inicio:inicio + 400],
            )
        db.flush()

    if cfg is not None:
        cfg.version_catalogo = CATALOGO_VERSION
    else:
        # Organización sin fila de configuración: se crea YA con la versión
        # aplicada para que esta migración no se repita en la visita
        # siguiente (la columna tiene server_default 0 en la base).
        try:
            db.add(Configuracion(
                organizacion_id=int(db.info.get("organizacion_id") or 1) or 1,
                version_catalogo=CATALOGO_VERSION,
            ))
        except Exception:
            log.warning("No se pudo crear la configuración al migrar el catálogo.")
    db.commit()
    log.info(
        "Catálogo v%s aplicado: %s actualizadas, %s nuevas.",
        CATALOGO_VERSION,
        len(actualizaciones),
        incorporadas,
    )
    return {
        "ok": True,
        "version": CATALOGO_VERSION,
        "actualizadas": len(actualizaciones),
        "incorporadas": incorporadas,
        "total_fuente": datos["n_partidas"],
    }


# Nombres del catálogo de demostración antiguo (app/seeds.CATALOGO_PARTIDAS +
# PARTIDAS_NUEVAS). Se eliminan al migrar a la base propia; no se tocan
# partidas oficiales (v1/v2) ni las creadas por el usuario.
NOMBRES_CATALOGO_PRUEBA = frozenset({
    "Demolición de partición interior de bloque",
    "Demolición de pavimento cerámico",
    "Demolición de enchape / alicatado",
    "Apertura de hueco para puerta o ventana",
    "Remates tras demoliciones",
    "Desmontaje de conjunto de mobiliario de cocina",
    "Desmontaje de aparato sanitario",
    "Hoja de partición interior de bloque de concreto",
    "Pañete / Repello de paredes",
    "Pañete de paredes para cocina o baño",
    "Solado de porcelanato rectificado gran formato",
    "Solado de baldosas cerámicas en capa fina",
    "Solado de baldosas cerámicas en exterior",
    "Zoclo lacado en blanco",
    "Zoclo de madera",
    "Losa de concreto con malla electrosoldada",
    "Afirmado / Acabado de concreto aligerado",
    "Cielo raso de tablaroca <3m",
    "Cielo raso de tablaroca con iluminación indirecta",
    "Falso techo de tablaroca con iluminación indirecta",
    "Instalación eléctrica completa vivienda",
    "Instalar tomacorriente nuevo",
    "Instalación de mecanismo (tomacorriente)",
    "Instalación de mecanismo (interruptor)",
    "Instalar punto de luz 10A",
    "Colocación de foco / aplique",
    "Instalar jack telefónico nuevo",
    "Instalar jack de antena nuevo",
    "Cuadro eléctrico provisional de obra",
    "Instalación de plomería para baño completo",
    "Instalación de plomería para cocina",
    "Instalación interior para lavadora y termo",
    "Instalación de saneamiento",
    "Revestimiento interior con cerámica gran formato",
    "Enchape de azulejo cerámico gran formato",
    "Instalación de plato / base de ducha",
    "Suministro y montaje de kit grifo para ducha",
    "Instalación de inodoro",
    "Instalación de mueble / gabinete de baño",
    "Suministro e instalación de mampara",
    "Puerta de entrada blindada",
    "Puerta interior de roble con herrajes ocultos",
    "Montaje de puerta corrediza de paso",
    "Balconera practicable de aluminio blanca",
    "Ventana PVC abrible blanca",
    "Ventana de aluminio corrediza blanca",
    "Pintura premium sobre pañete <3m a pistola",
    "Pintura premium sobre pañete <3m",
    "Montaje de cocina completa",
    "Colocación de mobiliario de cocina",
    "Grúa para obra",
    "Excavación de zanjas para zapatas <2m",
    "Forjado sanitario ventilado",
    "Zapatas aisladas de concreto",
    "Levantado de pavimento laminado",
    "Preparación y nivelación suelo existente",
    "Rodapie lacado en blanco",
    "Material Cerámico para Suelos",
})


def _cantidad_partidas_oficiales(db: Session) -> int:
    """Cuenta solo códigos que pertenecen realmente a nuestra fuente.

    Versión de recuento: un ``SELECT count(*)`` en vez de cargar las filas
    completas (con ``descomposicion_json`` de varios KiB cada una). Con un
    catálogo de ~3.000 partidas la versión anterior transfería megabytes y
    hidrataba miles de objetos ORM **en cada carga de /partidas**.
    """
    propias = int(
        db.query(func.count(Partida.id))
        .filter(or_(
            Partida.codigo_legacy.like("CT-%"),
            Partida.version_catalogo >= CATALOGO_VERSION,
        ))
        .scalar()
        or 0
    )
    if propias:
        return propias
    # Instalaciones v1 previas a ``codigo_legacy``: solo distinguibles por
    # ``codigo_interno`` CT- presente en la fuente. Dos counts baratos lo
    # cubren sin cargar filas; el set de códigos fuente está cacheado.
    internas_ct = int(
        db.query(func.count(Partida.id))
        .filter(Partida.codigo_interno.like("CT-%"))
        .scalar()
        or 0
    )
    if not internas_ct:
        return 0
    codigos_v1 = {
        str(p.get("codigo_legacy") or "")
        for p in construir_catalogo().get("partidas", [])
    }
    codigos_v1.discard("")
    if not codigos_v1:
        return 0
    return int(
        db.query(func.count(Partida.id))
        .filter(Partida.codigo_interno.in_(codigos_v1))
        .scalar()
        or 0
    )


def _identidades_partidas_oficiales(db: Session) -> list:
    """Solo las columnas de identidad de las partidas con código CT-.

    Sirve para detectar filas antiguas o sin identidad sin leer sus
    descompuestos: viajan unas pocas cadenas cortas por fila.
    """
    return (
        db.query(
            Partida.codigo_interno,
            Partida.codigo_legacy,
            Partida.es_oficial,
            Partida.catalogo_uid,
        )
        .filter(or_(
            Partida.codigo_interno.like("CT-%"),
            Partida.codigo_legacy.like("CT-%"),
        ))
        .all()
    )


def _parece_catalogo_prueba(db: Session) -> bool:
    """True si el catálogo actual es (o es solo) el de demostración antiguo."""
    total = db.query(Partida).count()
    if total == 0:
        return False
    # Si ya hay partidas propias v1 o v2, no tocar.
    propias = _cantidad_partidas_oficiales(db)
    if propias > 0:
        return False
    if total > 80:
        # Catálogo grande sin códigos CT: probablemente del usuario.
        return False
    nombres = {p.nombre for p in db.query(Partida.nombre).all()}
    interseccion = nombres & NOMBRES_CATALOGO_PRUEBA
    # Bastan unas pocas coincidencias: el catálogo viejo tenía ~55 partidas.
    return len(interseccion) >= 10


def migrar_catalogo_prueba_a_propio(db: Session) -> dict:
    """Sustituye el catálogo de prueba por el propio si aún no se ha hecho.

    - No borra partidas oficiales v1/v2 ni las creadas por el usuario.
    - Desvincula las líneas de presupuesto que apuntaban a las partidas
      eliminadas (el precio ya está copiado en la línea).
    - Es idempotente y aplica la taxonomía vigente sin trabajo destructivo.
    """
    from ..models import PresupuestoItem

    if not disponible():
        return {"ok": False, "motivo": "catalogo_no_disponible"}

    propias_antes = _cantidad_partidas_oficiales(db)
    if propias_antes > 0:
        return {"ok": True, "ya_migrado": True, **actualizar_taxonomia_catalogo_propio(db)}

    borradas = 0
    if _parece_catalogo_prueba(db):
        a_borrar = (
            db.query(Partida)
            .filter(Partida.nombre.in_(NOMBRES_CATALOGO_PRUEBA))
            .all()
        )
        ids = [p.id for p in a_borrar]
        if ids:
            db.query(PresupuestoItem).filter(
                PresupuestoItem.partida_catalogo_id.in_(ids)
            ).update(
                {PresupuestoItem.partida_catalogo_id: None},
                synchronize_session=False,
            )
            for partida in a_borrar:
                db.delete(partida)
                borradas += 1
            db.flush()
            log.info(
                "Eliminadas %s partidas del catálogo de prueba antiguo.",
                borradas,
            )

    resultado = sembrar_catalogo_propio(db)
    resultado["partidas_prueba_eliminadas"] = borradas
    return resultado


def asegurar_catalogo_propio(db: Session) -> dict | None:
    """Aplica de forma perezosa la semilla antigua y la taxonomía v2.

    Una organización que ya tiene el catálogo oficial se reclasifica una sola
    vez conservando ids, precios y borrados. Una instalación limpia o con un
    catálogo exclusivamente particular nunca recibe 540 partidas por sorpresa.

    Rendimiento: el caso normal (catálogo ya migrado) se resuelve con dos
    consultas de metadatos (fila de configuración + recuento). Antes esta
    función cargaba el catálogo completo —incluidos los descompuestos JSON de
    ~3.000 partidas— hasta tres veces por visita a /partidas, /recursos o el
    editor de presupuestos.
    """
    if not disponible():
        return None
    try:
        cfg = db.query(Configuracion).first()
        propias = _cantidad_partidas_oficiales(db)
        version = int(getattr(cfg, "version_catalogo", 0) or 0)
    except Exception:
        return None

    try:
        if propias > 0:
            # La marca ``version_catalogo`` la escribe la propia migración al
            # confirmar; con la versión vigente aplicada no hay nada que
            # auditar y no se construye el catálogo fuente (coste CPU alto).
            if version >= CATALOGO_VERSION:
                return None
            return actualizar_taxonomia_catalogo_propio(db)

        total = db.query(Partida).count()
        # Limpio o con partidas solo del usuario: no inyectar el catálogo.
        if total == 0 or not _parece_catalogo_prueba(db):
            return None
        return migrar_catalogo_prueba_a_propio(db)
    except Exception:
        log.exception("No se pudo actualizar el catálogo propio.")
        try:
            db.rollback()
        except Exception:
            pass
        return None
