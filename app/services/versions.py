"""Snapshots inmutables de presupuestos."""
import json
from datetime import datetime

from ..models import PresupuestoVersion

ESTADOS_CONGELABLES = {"enviado", "reenviado", "aprobado", "aprobado_parcialmente", "en_ejecucion", "finalizado"}


def _linea(item):
    descompuesto = getattr(item, "descomposicion_cype", None)
    datos_cype = None
    if descompuesto is not None:
        try:
            filas_cype = json.loads(descompuesto.filas_originales_json or "[]")
        except (TypeError, ValueError):
            filas_cype = []
        datos_cype = {
            "codigo": descompuesto.codigo,
            "unidad": descompuesto.unidad,
            "hoja": descompuesto.nombre_hoja,
            "archivo_origen": descompuesto.archivo_origen,
            "rango_original": descompuesto.rango_original,
            "columnas": descompuesto.columnas,
            "rangos_combinados": descompuesto.rangos_combinados,
            "filas": filas_cype,
            "coste_directo_unitario": descompuesto.coste_directo_unitario,
        }
    return {
        "codigo_externo": getattr(item, "codigo_externo", ""),
        "nombre": item.nombre, "descripcion": item.descripcion, "unidad": item.unidad,
        "cantidad": item.cantidad, "cantidad_total": item.cantidad_total,
        "precio_unitario": item.precio_unitario, "importe": item.importe,
        "producto_nombre": item.producto_nombre, "producto_precio": item.producto_precio,
        "producto_coste": item.producto_coste,
        "producto_unidad": item.producto_unidad, "tipo_partida": item.tipo_partida,
        "seleccionada": bool(item.seleccionada), "grupo_alternativa": item.grupo_alternativa,
        "coste_materiales": item.coste_materiales, "coste_mano_obra": item.coste_mano_obra,
        "coste_complementarios": getattr(item, "coste_complementarios", 0.0),
        "coste_otros": item.coste_otros, "desperdicio_pct": item.desperdicio_pct,
        "margen_pct": item.margen_pct,
        "descompuesto_cype": datos_cype,
        "mediciones": [{"concepto": m.concepto, "cantidad": m.cantidad} for m in item.mediciones],
    }


def serializar_presupuesto(p):
    """Representación autocontenida, apta para conservar el documento histórico."""
    return {
        "schema_version": 1, "numero": p.numero, "fecha": p.fecha.isoformat() if p.fecha else "",
        "titulo": p.titulo, "cliente": {"nombre": p.cliente.nombre, "rif": p.cliente.rif},
        "direccion_obra": p.direccion_obra, "codigo_postal": p.codigo_postal,
        "validez_dias": p.validez_dias, "moneda": p.moneda, "tipo_cambio": p.tipo_cambio,
        "impuesto_pct": p.impuesto_pct, "descuento_pct": p.descuento_pct, "estado": p.estado,
        "notas": p.notas, "condiciones": p.condiciones,
        "mostrar_garantias": bool(getattr(p, "mostrar_garantias", False)),
        "garantias_familias": p.garantias_familias if getattr(p, "mostrar_garantias", False) else [],
        "garantias_nota_legal": p.garantias_nota_legal if getattr(p, "mostrar_garantias", False) else "",
        "avanzado": bool(p.usar_funciones_avanzadas),
        "capitulos": [{"nombre": c.nombre, "partidas": [_linea(i) for i in c.partidas]} for c in p.capitulos],
        "totales": {"subtotal": p.subtotal, "opcionales": p.subtotal_opcional,
                    "alternativas": p.subtotal_alternativas,
                    "total_productos": p.total_productos, "subtotal_obra": p.subtotal_obra,
                    "coste_interno": p.coste_interno,
                    "margen_obra": p.margen_obra, "margen_obra_pct": p.margen_obra_pct,
                    "margen_productos": p.margen_productos, "margen_productos_pct": p.margen_productos_pct,
                    "margen": p.margen, "margen_pct": p.margen_pct,
                    "base": p.base,
                    "descuento": p.descuento_monto, "iva": p.impuesto_monto, "total": p.total},
    }


def crear_version(db, presupuesto, motivo=""):
    ultima = db.query(PresupuestoVersion).filter_by(presupuesto_id=presupuesto.id).order_by(PresupuestoVersion.numero_version.desc()).first()
    version = PresupuestoVersion(
        presupuesto_id=presupuesto.id, numero_version=(ultima.numero_version + 1 if ultima else 1),
        fecha=datetime.utcnow(), motivo=(motivo or "Instantánea del presupuesto").strip(),
        estado=presupuesto.estado, total=presupuesto.total,
        datos_snapshot=json.dumps(serializar_presupuesto(presupuesto), ensure_ascii=False),
    )
    db.add(version)
    return version


def leer_snapshot(version):
    try:
        return json.loads(version.datos_snapshot or "{}")
    except (TypeError, json.JSONDecodeError):
        return {}
