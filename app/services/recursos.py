"""Gestión central de precios unitarios (recursos).

Un Recurso es un precio unitario reutilizable que puede aparecer en la
descomposición de muchas partidas (catálogo y presupuestos). Cambiar el
precio aquí debe propagarse a todas las filas que lo usan.
"""
import json
import re
import unicodedata
from datetime import datetime

from sqlalchemy.orm import Session

from ..models import DescomposicionFila, DescomposicionPartida, Partida, Recurso


def normalizar(texto: str) -> str:
    t = unicodedata.normalize("NFD", str(texto or "").strip().lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "", t)


def clave_recurso(codigo: str, descripcion: str, unidad: str, categoria: str) -> str:
    cod = normalizar(codigo)
    if cod:
        return f"cod:{cod}"
    return f"desc:{normalizar(descripcion)}|{normalizar(unidad)}|{normalizar(categoria)}"


def clave_desde_fila(codigo: str, descripcion: str, unidad: str, categoria: str) -> str:
    return clave_recurso(codigo, descripcion, unidad, categoria)


def clave_desde_recurso(rec: Recurso) -> str:
    return clave_recurso(rec.codigo, rec.descripcion, rec.unidad, rec.categoria)


def recurso_match(recurso: Recurso, fila_codigo: str, fila_desc: str, fila_unidad: str, fila_categoria: str) -> bool:
    """¿Esta fila corresponde a este recurso?"""
    # Si recurso tiene código, matchear solo por código
    if (recurso.codigo or "").strip():
        return normalizar(recurso.codigo) == normalizar(fila_codigo)
    # Si no, por descripción+unidad+categoría (normalizado)
    return (
        normalizar(recurso.descripcion) == normalizar(fila_desc)
        and normalizar(recurso.unidad) == normalizar(fila_unidad)
        and normalizar(recurso.categoria) == normalizar(fila_categoria)
    )


def _recalcular_filas_catalogo(filas: list[dict]) -> dict:
    """Usa la misma lógica CYPE para recalcular costes de una lista de filas dict."""
    from .importer import recalcular_descompuesto_cype
    return recalcular_descompuesto_cype(filas)


def propagar_precio_recurso(db: Session, recurso: Recurso, precio_anterior: float, batch_size: int = 1000) -> dict:
    """Propaga el nuevo precio de un recurso a todas las partidas y descomposiciones.

    Retorna dict con contadores: {partidas_afectadas, filas_partidas, filas_presupuesto}
    
    Usa yield_per para no cargar todas las filas en memoria a la vez.
    """
    nuevo = float(recurso.precio or 0)
    if abs(nuevo - float(precio_anterior or 0)) < 1e-9:
        return {"partidas_afectadas": 0, "filas_partidas": 0, "filas_presupuesto": 0}

    partidas_afectadas = 0
    filas_partidas = 0
    filas_presupuesto = 0
    filas_por_descomp: dict[int, list[DescomposicionFila]] = {}

    # --- Catálogo de Partidas (descomposicion_json) ---
    # Usar yield_per para no cargar todo en memoria
    for partida in db.query(Partida).yield_per(batch_size):
        raw = partida.descomposicion_json or "[]"
        try:
            data = json.loads(raw)
        except Exception:
            continue
        # Puede ser dict con {filas: [...]} o lista directa
        if isinstance(data, dict):
            filas = data.get("filas", [])
            is_dict = True
        elif isinstance(data, list):
            filas = data
            is_dict = False
        else:
            continue
        if not isinstance(filas, list) or not filas:
            continue
        # Buscar filas que matcheen
        changed = False
        for fila in filas:
            if not isinstance(fila, dict):
                continue
            if fila.get("tipo") not in (None, "recurso", "recurso "):
                # En catálogo, tipo puede faltar pero asumimos recurso si tiene descripcion
                # Si tiene tipo y no es recurso, skip
                if fila.get("tipo") and fila.get("tipo") != "recurso":
                    continue
            if recurso_match(recurso, fila.get("codigo", ""), fila.get("descripcion", ""), fila.get("unidad", ""), fila.get("categoria", "")):
                # Actualizar precio
                fila["precio"] = nuevo
                fila["precio_unitario"] = nuevo
                # Recalcular importe si hay rendimiento
                rend = fila.get("rendimiento")
                try:
                    rend_f = float(str(rend).replace(",", ".") ) if rend not in (None, "") else None
                except Exception:
                    rend_f = None
                if rend_f is not None:
                    # Si unidad es %, el precio es base y el importe se recalcula luego
                    if str(fila.get("unidad", "")).strip() == "%":
                        # No recalcular importe aún, se hará en recalc global
                        pass
                    else:
                        fila["importe"] = round(rend_f * nuevo, 2)
                changed = True
                filas_partidas += 1
        if not changed:
            continue
        # Recalcular costes globales con helper
        # Necesitamos lista de dicts con estructura que espera recalcular_descompuesto_cype
        # Para catálogo, las filas dict ya tienen formato compatible
        try:
            res = _recalcular_filas_catalogo(filas)
            costes = res.get("costes", {})
            # Actualizar costes en partida
            partida.coste_materiales = float(costes.get("materiales", 0))
            partida.coste_mano_obra = float(costes.get("mano_obra", 0))
            partida.coste_complementarios = float(costes.get("complementarios", 0))
            partida.coste_otros = float(costes.get("otros", 0))
            # Actualizar importes de filas con resultados del recalc (para % y subtotales)
            for idx, imp in res.get("importes", {}).items():
                if 0 <= idx < len(filas):
                    filas[idx]["importe"] = imp
            for idx, precio_comp in res.get("precios_complementarios", {}).items():
                if 0 <= idx < len(filas):
                    filas[idx]["precio"] = precio_comp
                    filas[idx]["precio_unitario"] = precio_comp
            # Guardar JSON
            if is_dict:
                data["filas"] = filas
                partida.descomposicion_json = json.dumps(data, ensure_ascii=False)
            else:
                partida.descomposicion_json = json.dumps(filas, ensure_ascii=False)
            partida.fecha_actualizacion_precio = datetime.utcnow()
            partidas_afectadas += 1
        except Exception:
            # Fallback: al menos guardar el precio cambiado
            if is_dict:
                data["filas"] = filas
                partida.descomposicion_json = json.dumps(data, ensure_ascii=False)
            else:
                partida.descomposicion_json = json.dumps(filas, ensure_ascii=False)
            partidas_afectadas += 1

    # --- Descomposiciones de presupuestos (DescomposicionFila ORM) ---
    # Usar yield_per para no cargar todo en memoria
    for fila in db.query(DescomposicionFila).filter(DescomposicionFila.tipo == "recurso").yield_per(batch_size):
        if fila.tipo != "recurso":
            continue
        if not recurso_match(recurso, fila.codigo or "", fila.descripcion or "", fila.unidad or "", fila.categoria or ""):
            continue
        # Actualizar precio
        fila.precio_unitario = nuevo
        # Recalcular importe si no es %
        if (fila.unidad or "").strip() != "%":
            rend = float(fila.rendimiento or 0)
            fila.importe = round(rend * nuevo, 2)
        filas_presupuesto += 1
        filas_por_descomp.setdefault(fila.descomposicion_id, []).append(fila)

    # Recalcular cada descomposición afectada
    for descomp_id in list(filas_por_descomp.keys()):
        descomp = db.get(DescomposicionPartida, descomp_id) if 'DescomposicionPartida' in globals() else db.query(DescomposicionPartida).get(descomp_id)
        # fallback query
        if descomp is None:
            descomp = db.query(DescomposicionPartida).filter(DescomposicionPartida.id == descomp_id).first()
        if not descomp:
            continue
        # Necesitamos todas las filas de esa descomposición para recalc
        filas = list(descomp.filas)  # ya incluye las actualizadas
        try:
            from .importer import recalcular_descompuesto_cype
            res = recalcular_descompuesto_cype(filas)
            # Actualizar importes y precios de complementarios
            for idx, imp in res.get("importes", {}).items():
                if 0 <= idx < len(filas):
                    filas[idx].importe = imp
            for idx, precio_comp in res.get("precios_complementarios", {}).items():
                if 0 <= idx < len(filas):
                    filas[idx].precio_unitario = precio_comp
            # Sincronizar celdas si hay
            # (simplificado: no tocamos celdas_json aquí)
            # Actualizar costes en partida presupuestaria y descomp
            costes = res.get("costes", {})
            # Buscar la partida presupuestaria asociada
            partida_item = descomp.partida
            if partida_item is not None:
                partida_item.coste_materiales = float(costes.get("materiales", 0))
                partida_item.coste_mano_obra = float(costes.get("mano_obra", 0))
                partida_item.coste_complementarios = float(costes.get("complementarios", 0))
                partida_item.coste_otros = float(costes.get("otros", 0))
            descomp.coste_directo_unitario = float(res.get("coste_directo", 0))
            # Actualizar JSON de filas_originales
            try:
                filas_json = []
                for f in filas:
                    filas_json.append({
                        "numero": f.numero_fila_excel,
                        "celdas": json.loads(f.celdas_json or "[]"),
                        "formulas": json.loads(f.formulas_json or "{}"),
                        "tipo": f.tipo,
                        "grupo": f.grupo,
                        "categoria": f.categoria,
                        "codigo": f.codigo,
                        "unidad": f.unidad,
                        "descripcion": f.descripcion,
                        "rendimiento": f.rendimiento,
                        "precio_unitario": f.precio_unitario,
                        "importe": f.importe,
                    })
                descomp.filas_originales_json = json.dumps(filas_json, ensure_ascii=False)
            except Exception:
                pass
        except Exception:
            pass

    # Actualizar metadatos del recurso
    recurso.fecha_actualizacion_precio = datetime.utcnow()
    recurso.ultimo_uso = datetime.utcnow()

    return {"partidas_afectadas": partidas_afectadas, "filas_partidas": filas_partidas, "filas_presupuesto": filas_presupuesto}


def sincronizar_recursos_desde_catalogo(db: Session) -> int:
    """Crea Recursos faltantes a partir de descomposiciones existentes (catálogo + presupuestos).

    Retorna número de recursos creados.
    """
    existentes_claves = set()
    for r in db.query(Recurso).all():
        existentes_claves.add(r.clave)

    nuevos = 0
    # De catálogo Partida
    for partida in db.query(Partida).all():
        raw = partida.descomposicion_json or "[]"
        try:
            data = json.loads(raw)
        except Exception:
            continue
        filas = data.get("filas", []) if isinstance(data, dict) else data if isinstance(data, list) else []
        for fila in filas:
            if not isinstance(fila, dict):
                continue
            if fila.get("tipo") and fila.get("tipo") != "recurso":
                continue
            codigo = str(fila.get("codigo", "") or "").strip()
            desc = str(fila.get("descripcion", "") or "").strip()
            if not desc:
                continue
            unidad = str(fila.get("unidad", "") or "ud").strip() or "ud"
            categoria = str(fila.get("categoria", "") or fila.get("grupo", "") or "otros").strip().lower()
            # Normalizar categoria a valores permitidos
            if categoria not in ("materiales", "mano_obra", "complementarios", "otros"):
                # intentar mapear grupo
                from .importer import categoria_coste_cype
                categoria = categoria_coste_cype(fila.get("grupo", ""), codigo)
            precio = None
            try:
                precio = float(str(fila.get("precio") or fila.get("precio_unitario") or 0).replace(",", "."))
            except Exception:
                precio = 0
            if not precio:
                try:
                    precio = float(str(fila.get("importe", 0)).replace(",", ".")) if fila.get("rendimiento") else 0
                except Exception:
                    precio = 0
            clave = clave_recurso(codigo, desc, unidad, categoria)
            if clave in existentes_claves:
                continue
            db.add(Recurso(
                codigo=codigo,
                descripcion=desc,
                unidad=unidad,
                categoria=categoria,
                grupo=str(fila.get("grupo", "") or ""),
                precio=float(precio or 0),
            ))
            existentes_claves.add(clave)
            nuevos += 1

    # De presupuestos DescomposicionFila
    for fila in db.query(DescomposicionFila).filter(DescomposicionFila.tipo == "recurso").all():
        codigo = str(fila.codigo or "").strip()
        desc = str(fila.descripcion or "").strip()
        if not desc:
            continue
        unidad = str(fila.unidad or "ud").strip() or "ud"
        categoria = str(fila.categoria or "otros").strip().lower()
        if categoria not in ("materiales", "mano_obra", "complementarios", "otros"):
            categoria = "otros"
        clave = clave_recurso(codigo, desc, unidad, categoria)
        if clave in existentes_claves:
            continue
        db.add(Recurso(
            codigo=codigo,
            descripcion=desc,
            unidad=unidad,
            categoria=categoria,
            grupo=str(fila.grupo or ""),
            precio=float(fila.precio_unitario or 0),
        ))
        existentes_claves.add(clave)
        nuevos += 1

    if nuevos:
        db.commit()
    return nuevos


def actualizar_usos_recursos(db: Session):
    """Recalcula usos (cuántas partidas/presupuestos usan cada recurso)."""
    # Mapear clave -> count
    clave_to_count: dict[str, int] = {}
    # Catálogo
    for partida in db.query(Partida).all():
        raw = partida.descomposicion_json or "[]"
        try:
            data = json.loads(raw)
            filas = data.get("filas", []) if isinstance(data, dict) else data if isinstance(data, list) else []
        except Exception:
            continue
        for fila in filas:
            if not isinstance(fila, dict):
                continue
            if fila.get("tipo") and fila.get("tipo") != "recurso":
                continue
            clave = clave_recurso(str(fila.get("codigo", "")), str(fila.get("descripcion", "")), str(fila.get("unidad", "")), str(fila.get("categoria", "")))
            clave_to_count[clave] = clave_to_count.get(clave, 0) + 1
    # Presupuestos
    for fila in db.query(DescomposicionFila).filter(DescomposicionFila.tipo == "recurso").all():
        clave = clave_recurso(str(fila.codigo or ""), str(fila.descripcion or ""), str(fila.unidad or ""), str(fila.categoria or ""))
        clave_to_count[clave] = clave_to_count.get(clave, 0) + 1

    for recurso in db.query(Recurso).all():
        recurso.usos = clave_to_count.get(recurso.clave, 0)
    db.commit()
