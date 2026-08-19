"""Resolución de precios de recursos por mercado nacional.

Jerarquía: override de organización -> referencia nacional -> None.
La ausencia de precio local no se oculta: el resultado incluye un aviso.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from sqlalchemy.orm import Session
from ..models import PrecioRecursoMercado, Recurso

@dataclass(frozen=True)
class PrecioResuelto:
    precio: float | None
    moneda: str | None
    origen: str
    confianza: str
    aviso: str = ""


def resolver_precio(db: Session, recurso_id: int, pais_codigo: str,
                    organizacion_id: int | None = None) -> PrecioResuelto:
    q = db.query(PrecioRecursoMercado).filter(
        PrecioRecursoMercado.recurso_id == recurso_id,
        PrecioRecursoMercado.pais_codigo == str(pais_codigo or "").upper(),
        PrecioRecursoMercado.activo.is_(True),
    )
    propio = q.filter(PrecioRecursoMercado.organizacion_id == organizacion_id).first() if organizacion_id else None
    nacional = q.filter(PrecioRecursoMercado.organizacion_id.is_(None)).first()
    elegido = propio or nacional
    if elegido:
        return PrecioResuelto(
            float(elegido.precio), elegido.moneda,
            "organizacion" if propio else "nacional",
            elegido.confianza or "referencia",
            "" if propio or (elegido.confianza == "confirmado") else ("Precio provisional de respaldo; verifica con tu proveedor" if elegido.confianza == "provisional" or "respaldo" in (elegido.fuente or "").lower() else "Usando precio nacional de referencia"),
        )
    recurso = db.get(Recurso, recurso_id)
    if recurso and recurso.moneda == "USD":
        return PrecioResuelto(float(recurso.precio or 0), "USD", "base", "respaldo", "No existe precio nacional confirmado para este recurso")
    return PrecioResuelto(None, None, "sin_precio", "faltante", "Falta precio local para este recurso y país")


def guardar_precio(db: Session, recurso_id: int, pais_codigo: str, precio: float,
                   moneda: str, *, organizacion_id: int | None = None,
                   fuente: str = "", proveedor: str = "", confianza: str = "referencia",
                   fecha_vigencia=None) -> PrecioRecursoMercado:
    """Crea o actualiza precio nacional u override de organización."""
    codigo = str(pais_codigo or "").strip().upper()
    row = db.query(PrecioRecursoMercado).filter_by(
        recurso_id=recurso_id, pais_codigo=codigo, organizacion_id=organizacion_id
    ).first()
    if row is None:
        row = PrecioRecursoMercado(recurso_id=recurso_id, pais_codigo=codigo, organizacion_id=organizacion_id)
        db.add(row)
    anterior = row.precio if row.id is not None else None
    row.precio = max(0.0, float(precio))
    row.moneda = str(moneda or "USD").strip().upper()
    row.fuente = str(fuente or "").strip()[:200]
    row.proveedor = str(proveedor or "").strip()[:150]
    row.confianza = str(confianza or "referencia").strip()[:20]
    row.fecha_vigencia = fecha_vigencia
    row.fecha_actualizacion = date.today()
    if anterior is not None and abs(float(anterior) - row.precio) > 1e-9:
        from ..models import HistorialPrecioRecurso
        db.add(HistorialPrecioRecurso(precio_mercado=row, precio_anterior=anterior, precio_nuevo=row.precio, moneda=row.moneda, motivo="Actualización de referencia", fuente=row.fuente))
    return row

def resolver_precio_para_presupuesto(db: Session, recurso_id: int, pais_codigo: str,
                                     organizacion_id: int | None, moneda_presupuesto: str,
                                     tasa_mercado_a_usd: float | None = None,
                                     tasa_usd_presupuesto: float | None = None) -> dict:
    """Devuelve precio efectivo listo para una nueva descomposición."""
    from .monedas import convertir
    res = resolver_precio(db, recurso_id, pais_codigo, organizacion_id)
    if res.precio is None:
        return {"precio": None, "moneda": None, "origen": res.origen, "confianza": res.confianza, "aviso": res.aviso, "requiere_tasa": False}
    origen = res.moneda or "USD"
    destino = str(moneda_presupuesto or "USD").upper()
    try:
        convertido = convertir(res.precio, origen, destino,
                               tasa_usd_destino=tasa_usd_presupuesto,
                               tasa_usd_origen=tasa_mercado_a_usd)
        return {"precio": float(convertido), "moneda": destino, "origen": res.origen, "confianza": res.confianza, "aviso": res.aviso, "requiere_tasa": False}
    except ValueError:
        return {"precio": res.precio, "moneda": origen, "origen": res.origen, "confianza": res.confianza, "aviso": "Falta tasa para convertir el precio al presupuesto", "requiere_tasa": True}
