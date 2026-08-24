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
    recurso = db.get(Recurso, recurso_id)
    pais = str(pais_codigo or "").upper()
    q = db.query(PrecioRecursoMercado).filter(
        PrecioRecursoMercado.pais_codigo == pais,
        PrecioRecursoMercado.activo.is_(True),
    )
    propio = q.filter(
        PrecioRecursoMercado.recurso_id == recurso_id,
        PrecioRecursoMercado.organizacion_id == organizacion_id,
    ).first() if organizacion_id else None
    filtro_nacional = [PrecioRecursoMercado.recurso_id == recurso_id]
    if recurso is not None and (recurso.codigo or "").strip():
        filtro_nacional.append(
            PrecioRecursoMercado.codigo_recurso == recurso.codigo.strip()
        )
    nacional = q.filter(
        PrecioRecursoMercado.organizacion_id.is_(None),
        or_(*filtro_nacional),
    ).first()
    elegido = propio or nacional
    if elegido:
        return PrecioResuelto(
            float(elegido.precio), elegido.moneda,
            "organizacion" if propio else "nacional",
            elegido.confianza or "referencia",
            _aviso_precio(propio is not None, elegido),
        )
    if recurso and recurso.moneda == "USD":
        return PrecioResuelto(float(recurso.precio or 0), "USD", "base", "respaldo", "No existe precio nacional confirmado para este recurso")
    return PrecioResuelto(None, None, "sin_precio", "faltante", "Falta precio local para este recurso y país")


def _aviso_precio(propio: bool, elegido) -> str:
    if propio or (elegido.confianza == "confirmado"):
        return ""
    if elegido.confianza == "provisional" or "respaldo" in (elegido.fuente or "").lower():
        return "Precio provisional de respaldo; puede variar según mercado y proveedor"
    if elegido.confianza == "derivado":
        return "Precio referencial nacional derivado de la canasta de mercado"
    return "Precio referencial nacional; puede variar según mercado y proveedor"


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
    ids = [r.id for r in recursos]
    codigos = [str(r.codigo).strip() for r in recursos if (r.codigo or "").strip()]
    filtro_identidad = [PrecioRecursoMercado.recurso_id.in_(ids)]
    if codigos:
        filtro_identidad.append(PrecioRecursoMercado.codigo_recurso.in_(codigos))
    filas = (
        db.query(PrecioRecursoMercado)
        .filter(
            or_(*filtro_identidad),
            PrecioRecursoMercado.pais_codigo == pais,
            PrecioRecursoMercado.activo.is_(True),
            or_(*filtro_org),
        )
        .all()
    )
    propios: dict[int, PrecioRecursoMercado] = {}
    nacionales_id: dict[int, PrecioRecursoMercado] = {}
    nacionales_codigo: dict[str, PrecioRecursoMercado] = {}
    for fila in filas:
        if fila.organizacion_id is not None:
            propios.setdefault(fila.recurso_id, fila)
        else:
            nacionales_id.setdefault(fila.recurso_id, fila)
            codigo = str(fila.codigo_recurso or "").strip()
            if codigo:
                nacionales_codigo.setdefault(codigo, fila)

    salida: dict[int, PrecioResuelto] = {}
    for recurso in recursos:
        propio = propios.get(recurso.id)
        nacional = (
            nacionales_id.get(recurso.id)
            or nacionales_codigo.get(str(recurso.codigo or "").strip())
        )
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
                   fecha_vigencia=None, precio_min: float | None = None,
                   precio_max: float | None = None, unidad_referencia: str | None = None,
                   fecha_consulta=None, incluye_iva: str | None = None,
                   incluye_transporte: str | None = None,
                   observaciones: str | None = None) -> PrecioRecursoMercado:
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
    recurso = db.get(Recurso, recurso_id)
    codigo_recurso = str(getattr(recurso, "codigo", "") or "").strip()
    query = db.query(PrecioRecursoMercado).filter(
        PrecioRecursoMercado.pais_codigo == codigo,
        PrecioRecursoMercado.organizacion_id == organizacion_id,
    )
    if organizacion_id is None and codigo_recurso:
        # Una sola referencia nacional por código estable, aunque cada tenant
        # tenga su propia copia/ID del recurso.
        row = query.filter(or_(
            PrecioRecursoMercado.codigo_recurso == codigo_recurso,
            PrecioRecursoMercado.recurso_id == recurso_id,
        )).first()
    else:
        row = query.filter(PrecioRecursoMercado.recurso_id == recurso_id).first()
    if row is None:
        row = PrecioRecursoMercado(
            recurso_id=recurso_id,
            codigo_recurso=codigo_recurso,
            pais_codigo=codigo,
            organizacion_id=organizacion_id,
        )
        db.add(row)
    elif codigo_recurso and not row.codigo_recurso:
        row.codigo_recurso = codigo_recurso
    anterior = row.precio if row.id is not None else None
    valor = float(precio)
    if valor <= 0:
        raise ValueError("El precio debe ser mayor que cero.")
    minimo = float(precio_min) if precio_min is not None else None
    maximo = float(precio_max) if precio_max is not None else None
    if minimo is not None and minimo <= 0:
        raise ValueError("El precio mínimo debe ser mayor que cero.")
    if maximo is not None and (maximo <= 0 or (minimo is not None and maximo < minimo)):
        raise ValueError("El rango de precios no es válido.")
    if minimo is not None and valor < minimo or maximo is not None and valor > maximo:
        raise ValueError("El precio de referencia debe estar dentro de su rango.")

    row.precio = valor
    row.moneda = str(moneda or "USD").strip().upper()
    if minimo is not None:
        row.precio_min = minimo
    if maximo is not None:
        row.precio_max = maximo
    if unidad_referencia is not None:
        row.unidad_referencia = str(unidad_referencia).strip()[:30]
    row.fuente = str(fuente or "").strip()[:200]
    row.proveedor = str(proveedor or "").strip()[:150]
    row.confianza = str(confianza or "referencia").strip()[:20]
    if fecha_consulta is not None:
        row.fecha_consulta = fecha_consulta
    if fecha_vigencia is not None:
        row.fecha_vigencia = fecha_vigencia
    if incluye_iva is not None:
        row.incluye_iva = str(incluye_iva).strip()[:20]
    if incluye_transporte is not None:
        row.incluye_transporte = str(incluye_transporte).strip()[:20]
    if observaciones is not None:
        row.observaciones = str(observaciones).strip()
    row.fecha_actualizacion = date.today()
    if anterior is not None and abs(float(anterior) - row.precio) > 1e-9:
        from ..models import HistorialPrecioRecurso
        db.add(HistorialPrecioRecurso(precio_mercado=row, precio_anterior=anterior, precio_nuevo=row.precio, moneda=row.moneda, motivo="Actualización de referencia", fuente=row.fuente))
    return row

def eliminar_precio_organizacion(db: Session, recurso_id: int, pais_codigo: str,
                                 organizacion_id: int) -> bool:
    """Elimina el precio propio de una organización para un recurso y país.

    Usado cuando el usuario borra su valor en el formulario: a partir de ese
    momento vuelve a mandar la referencia nacional de mercado.
    """
    if organizacion_id is None or int(organizacion_id) <= 0:
        return False
    pais = str(pais_codigo or "").strip().upper()
    row = db.query(PrecioRecursoMercado).filter(
        PrecioRecursoMercado.recurso_id == recurso_id,
        PrecioRecursoMercado.pais_codigo == pais,
        PrecioRecursoMercado.organizacion_id == int(organizacion_id),
    ).first()
    if row is None:
        return False
    db.delete(row)
    return True


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
