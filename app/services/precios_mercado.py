"""Resolución de precios de recursos por mercado nacional.

Jerarquía: override de organización -> referencia nacional -> None.
La ausencia de precio local no se oculta: el resultado incluye un aviso.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from sqlalchemy import or_
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


def _aviso_precio(propio: bool, elegido) -> str:
    if propio or (elegido.confianza == "confirmado"):
        return ""
    if elegido.confianza == "provisional" or "respaldo" in (elegido.fuente or "").lower():
        return "Precio provisional de respaldo; verifica con tu proveedor"
    return "Usando precio nacional de referencia"


def resolver_precios_lote(db: Session, recursos, pais_codigo: str,
                          organizacion_id: int | None = None) -> dict[int, PrecioResuelto]:
    """Resuelve el precio de mercado de muchos recursos con UNA consulta.

    Sustituye a llamar a :func:`resolver_precio` una vez por recurso (dos
    SELECT por recurso: con ~400 recursos eran ~800 viajes a la base, la
    mayor parte del tiempo de carga de /recursos y del editor). La jerarquía
    de selección es idéntica: override de organización → referencia
    nacional → precio base USD → sin precio.
    """
    recursos = list(recursos)
    if not recursos:
        return {}
    pais = str(pais_codigo or "").upper()
    filtro_org = [PrecioRecursoMercado.organizacion_id.is_(None)]
    if organizacion_id:
        filtro_org.append(PrecioRecursoMercado.organizacion_id == organizacion_id)
    filas = (
        db.query(PrecioRecursoMercado)
        .filter(
            PrecioRecursoMercado.recurso_id.in_([r.id for r in recursos]),
            PrecioRecursoMercado.pais_codigo == pais,
            PrecioRecursoMercado.activo.is_(True),
            or_(*filtro_org),
        )
        .all()
    )
    propios: dict[int, PrecioRecursoMercado] = {}
    nacionales: dict[int, PrecioRecursoMercado] = {}
    for fila in filas:
        destino = propios if fila.organizacion_id is not None else nacionales
        # Igual que ``.first()`` de la versión individual: se conserva la
        # primera fila encontrada por recurso y ámbito.
        destino.setdefault(fila.recurso_id, fila)

    salida: dict[int, PrecioResuelto] = {}
    for recurso in recursos:
        propio = propios.get(recurso.id)
        nacional = nacionales.get(recurso.id)
        elegido = propio or nacional
        if elegido:
            salida[recurso.id] = PrecioResuelto(
                float(elegido.precio), elegido.moneda,
                "organizacion" if propio else "nacional",
                elegido.confianza or "referencia",
                _aviso_precio(propio is not None, elegido),
            )
        elif recurso.moneda == "USD":
            salida[recurso.id] = PrecioResuelto(
                float(recurso.precio or 0), "USD", "base", "respaldo",
                "No existe precio nacional confirmado para este recurso",
            )
        else:
            salida[recurso.id] = PrecioResuelto(
                None, None, "sin_precio", "faltante",
                "Falta precio local para este recurso y país",
            )
    return salida


def guardar_precio(db: Session, recurso_id: int, pais_codigo: str, precio: float,
                   moneda: str, *, organizacion_id: int | None = None,
                   fuente: str = "", proveedor: str = "", confianza: str = "referencia",
                   fecha_vigencia=None) -> PrecioRecursoMercado:
    """Crea o actualiza precio nacional u override de organización.

    ``organizacion_id`` nulo = referencia nacional. Un identificador no válido
    (0, negativo) no puede tratarse como «nacional» por descuido: escribiría un
    precio visible para todas las empresas.
    """
    if organizacion_id is not None and int(organizacion_id) <= 0:
        raise ValueError(
            "organizacion_id debe ser una organización real o None (precio nacional)."
        )
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


def resolver_precios_para_presupuesto_lote(db: Session, recursos, pais_codigo: str,
                                           organizacion_id: int | None,
                                           moneda_presupuesto: str,
                                           tasa_usd_presupuesto: float | None = None) -> dict[int, dict]:
    """Versión por lote de :func:`resolver_precio_para_presupuesto`.

    Una única consulta de precios de mercado para todos los recursos; la
    conversión de moneda es cálculo puro y se hace en memoria. Mismas claves
    y valores que la versión individual, indexados por ``recurso.id``.
    """
    from .monedas import convertir
    resueltos = resolver_precios_lote(db, recursos, pais_codigo, organizacion_id)
    salida: dict[int, dict] = {}
    for recurso in recursos:
        res = resueltos.get(recurso.id)
        if res is None:
            continue
        if res.precio is None:
            salida[recurso.id] = {"precio": None, "moneda": None, "origen": res.origen, "confianza": res.confianza, "aviso": res.aviso, "requiere_tasa": False}
            continue
        origen = res.moneda or "USD"
        destino = str(moneda_presupuesto or "USD").upper()
        try:
            convertido = convertir(res.precio, origen, destino,
                                   tasa_usd_destino=tasa_usd_presupuesto,
                                   tasa_usd_origen=None)
            salida[recurso.id] = {"precio": float(convertido), "moneda": destino, "origen": res.origen, "confianza": res.confianza, "aviso": res.aviso, "requiere_tasa": False}
        except ValueError:
            salida[recurso.id] = {"precio": res.precio, "moneda": origen, "origen": res.origen, "confianza": res.confianza, "aviso": "Falta tasa para convertir el precio al presupuesto", "requiere_tasa": True}
    return salida
