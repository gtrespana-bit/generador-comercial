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

from sqlalchemy.orm import Session

from ..models import CategoriaPartida, Partida, Recurso

log = logging.getLogger("cotizat")

# basedatos_partidas/ está al lado de app/
_RAIZ = Path(__file__).resolve().parents[2]
_BASE_DATOS = _RAIZ / "basedatos_partidas"
_DESCOMPUESTOS = _BASE_DATOS / "datos" / "descompuestos"
_RECURSOS = _BASE_DATOS / "datos" / "recursos.json"
_CLASIFICACION = _BASE_DATOS / "datos" / "clasificacion.json"

# Mismo margen por defecto que basedatos_partidas/descompuestos.py
MARGEN_DEFECTO = 0.30

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
    """Resuelve las 540 partidas y el cuadro de precios en memoria.

    El resultado se cachea: sembrar el catálogo y migrar una instalación
    antigua no vuelven a recorrer los JSON.
    """
    if not disponible():
        return {"partidas": [], "recursos": [], "categorias": [], "ok": False}

    mod = _cargar_modulo_descompuestos()
    catalogo_recursos = mod.cargar_recursos()
    taxonomia = mod.cargar_clasificacion()

    categorias: list[tuple[str, str]] = []
    for _cod, cap in (taxonomia.get("capitulos") or {}).items():
        nombre_cap = str(cap.get("nombre") or "").strip()
        if not nombre_cap:
            continue
        subs = cap.get("subcapitulos") or {}
        if not subs:
            categorias.append((nombre_cap, ""))
            continue
        for _sc, nombre_sub in subs.items():
            categorias.append((nombre_cap, str(nombre_sub or "").strip()))

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
        # La barra lateral agrupa por categoria (capítulo) y subcategoria.
        # Se guardan los nombres legibles, no el código CT-CC.
        notas = f"Coste directo {coste_directo:.2f} USD + margen {margen * 100:.0f}%"
        pc = partida.get("producto_cliente")
        if isinstance(pc, dict) and pc:
            notas += (
                f" | NO INCLUYE el producto de elección del cliente: "
                f"{pc.get('tipo', '')} "
                f"({pc.get('consumo', '')} {pc.get('unidad', '')}/{unidad})"
            )

        partidas_out.append({
            "codigo": codigo,
            "nombre": str(partida.get("titulo") or codigo).strip(),
            "descripcion": str(partida.get("descripcion") or "").strip(),
            "unidad": unidad,
            "precio_unitario": precio_venta,
            "categoria": nombre_cap or "General",
            "subcategoria": nombre_sub,
            "coste_materiales": costes["materiales"],
            "coste_mano_obra": costes["mano_obra"],
            "coste_complementarios": costes["complementarios"],
            "coste_otros": costes["otros"],
            "tiempo_estimado_horas": round(horas_mo, 4) if horas_mo else None,
            "rendimiento": f"{horas_mo:.3f} h/{unidad}" if horas_mo else "",
            "notas_tecnicas": notas,
            "descomposicion_json": json.dumps({
                "origen": "catalogo_propio",
                "codigo": codigo,
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


def _sembrar_categorias(db: Session, categorias: list[tuple[str, str]]) -> None:
    existentes = {
        (c.categoria or "", c.subcategoria or "")
        for c in db.query(CategoriaPartida).all()
    }
    for categoria, subcategoria in categorias:
        clave = (categoria[:80], (subcategoria or "")[:80])
        if not clave[0] or clave in existentes:
            continue
        db.add(CategoriaPartida(categoria=clave[0], subcategoria=clave[1]))
        existentes.add(clave)


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


def _sembrar_partidas(db: Session, partidas: list[dict]) -> int:
    """Crea partidas del catálogo propio que aún no existan (por nombre)."""
    existentes = {p.nombre for p in db.query(Partida.nombre).all()}
    creadas = 0
    for item in partidas:
        nombre = (item.get("nombre") or "").strip()
        if not nombre or nombre in existentes:
            continue
        db.add(Partida(
            nombre=nombre[:200],
            descripcion=item.get("descripcion") or "",
            precio_unitario=float(item.get("precio_unitario") or 0),
            unidad=(item.get("unidad") or "ud")[:30],
            categoria=(item.get("categoria") or "General")[:80],
            subcategoria=(item.get("subcategoria") or "")[:80],
            codigo_interno=(item.get("codigo") or "")[:80],
            codigo_externo=(item.get("codigo") or "")[:100],
            coste_materiales=float(item.get("coste_materiales") or 0),
            coste_mano_obra=float(item.get("coste_mano_obra") or 0),
            coste_complementarios=float(item.get("coste_complementarios") or 0),
            coste_otros=float(item.get("coste_otros") or 0),
            tiempo_estimado_horas=item.get("tiempo_estimado_horas"),
            rendimiento=(item.get("rendimiento") or "")[:120],
            notas_tecnicas=item.get("notas_tecnicas") or "",
            descomposicion_json=item.get("descomposicion_json") or "[]",
        ))
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

    _sembrar_categorias(db, datos["categorias"])
    n_rec = _sembrar_recursos(db, datos["recursos"])
    n_par = _sembrar_partidas(db, datos["partidas"])
    db.commit()
    log.info(
        "Catálogo propio sembrado: %s partidas nuevas, %s recursos nuevos "
        "(fuente: %s partidas / %s recursos).",
        n_par, n_rec, datos["n_partidas"], datos["n_recursos"],
    )
    return {"ok": True, "partidas": n_par, "recursos": n_rec,
            "total_partidas": datos["n_partidas"], "total_recursos": datos["n_recursos"]}


# Nombres del catálogo de demostración antiguo (app/seeds.CATALOGO_PARTIDAS +
# PARTIDAS_NUEVAS). Se eliminan al migrar a la base propia; no se tocan
# partidas con código CT-* ni las creadas por el usuario.
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


def _parece_catalogo_prueba(db: Session) -> bool:
    """True si el catálogo actual es (o es solo) el de demostración antiguo."""
    total = db.query(Partida).count()
    if total == 0:
        return False
    # Si ya hay partidas del catálogo propio (código CT-…), no tocar.
    propias = (
        db.query(Partida)
        .filter(Partida.codigo_interno.like("CT-%"))
        .count()
    )
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

    - No borra partidas con código CT-* ni las que el usuario haya creado
      con otro nombre.
    - Desvincula las líneas de presupuesto que apuntaban a las partidas
      eliminadas (el precio ya está copiado en la línea).
    - Es idempotente: si ya hay partidas CT-* no hace nada destructivo.
    """
    from ..models import PresupuestoItem

    if not disponible():
        return {"ok": False, "motivo": "catalogo_no_disponible"}

    propias_antes = (
        db.query(Partida).filter(Partida.codigo_interno.like("CT-%")).count()
    )
    if propias_antes >= 100:
        # Ya migrado / sembrado: solo rellenar huecos (idempotente).
        return {"ok": True, "ya_migrado": True, **sembrar_catalogo_propio(db)}

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
    """Migración perezosa al abrir catálogo / editor.

    Si la organización todavía tiene el catálogo de prueba (~50 partidas sin
    código CT-*) lo sustituye por el propio. Si ya está migrado, no hace nada
    costoso (un COUNT sobre codigo_interno). No toca instalaciones en limpio
    (0 partidas): esas se rellenan solo con el modo demo o importando.
    """
    if not disponible():
        return None
    try:
        propias = (
            db.query(Partida)
            .filter(Partida.codigo_interno.like("CT-%"))
            .count()
        )
    except Exception:
        return None
    if propias >= 100:
        return None
    try:
        total = db.query(Partida).count()
    except Exception:
        return None
    # Limpio o sin datos: no inyectar el catálogo a la fuerza.
    if total == 0:
        return None
    if not _parece_catalogo_prueba(db) and propias == 0:
        # Tiene partidas del usuario (nombres propios): no las borramos ni
        # mezclamos 540 de golpe; puede importar cuando quiera.
        return None
    try:
        return migrar_catalogo_prueba_a_propio(db)
    except Exception:
        log.exception("No se pudo migrar el catálogo de prueba al propio.")
        try:
            db.rollback()
        except Exception:
            pass
        return None
