"""Detección y reparación de precios imposibles en el catálogo.

Contexto del fallo que motiva este módulo
-----------------------------------------
El catálogo se guarda SIEMPRE en la moneda base (USD) y el editor muestra los
importes en la moneda del presupuesto (COP, MXN, PEN…). Hasta la corrección de
``_guardar_en_catalogos`` el guardado automático de un presupuesto escribía en
el catálogo el precio TAL CUAL lo veía el usuario, es decir en moneda local.
La siguiente vez que esa partida se usaba, el editor volvía a multiplicarla por
la tasa y aparecían cifras absurdas del tipo «46.897.962 COP/m² por demoler un
piso cerámico» (4,79 USD × 3.128,65 × 3.128,65).

Este módulo encuentra esos registros y los devuelve a su moneda base. No borra
nada ni inventa precios: solo deshace una multiplicación que nunca debió
ocurrir, y siempre exige que el resultado sea plausible.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from ..models import Configuracion, Partida, Producto

#: Precio unitario (en USD, moneda base del catálogo) por encima del cual una
#: partida de obra deja de ser creíble. El catálogo oficial más caro ronda los
#: 750 USD/ud (un ascensor); se deja un margen amplio para catálogos propios
#: con partidas «llave en mano».
UMBRAL_SOSPECHOSO_USD = 20_000.0

#: Por encima de este valor no hay duda posible: es un error de moneda.
UMBRAL_CRITICO_USD = 250_000.0

#: Rango en el que un precio ya reparado se considera plausible.
MAXIMO_PLAUSIBLE_USD = 20_000.0

CAMPOS_MONETARIOS = (
    "precio_unitario",
    "coste_materiales",
    "coste_mano_obra",
    "coste_complementarios",
    "coste_otros",
)


@dataclass
class Anomalia:
    """Un registro del catálogo con un precio que no puede ser correcto."""

    tipo: str  # "partida" | "producto"
    id: int
    nombre: str
    unidad: str
    precio: float
    precio_sugerido: float
    factor: float
    motivo: str
    gravedad: str  # "critica" | "sospechosa"
    reparable: bool = True
    detalle: dict = field(default_factory=dict)

    def como_dict(self) -> dict:
        return {
            "tipo": self.tipo,
            "id": self.id,
            "nombre": self.nombre,
            "unidad": self.unidad,
            "precio": round(self.precio, 2),
            "precio_sugerido": round(self.precio_sugerido, 2),
            "factor": round(self.factor, 4),
            "motivo": self.motivo,
            "gravedad": self.gravedad,
            "reparable": self.reparable,
            **self.detalle,
        }


def _tasas_candidatas(db: Session) -> list[float]:
    """Factores con los que se pudo haber inflado un precio.

    Se prueban, por este orden: la tasa de la organización, las tasas
    congeladas por sus presupuestos y las tasas de referencia conocidas. Nunca
    se inventa un divisor arbitrario.
    """
    from .tasa import TASAS_SUGERIDAS

    candidatas: list[float] = []

    def _añadir(valor) -> None:
        try:
            tasa = float(valor or 0)
        except (TypeError, ValueError):
            return
        if tasa > 1.0 and all(abs(tasa - x) > 1e-6 for x in candidatas):
            candidatas.append(tasa)

    try:
        cfg = db.query(Configuracion).first()
        _añadir(getattr(cfg, "tasa_cambio", None))
    except Exception:  # pragma: no cover - configuración ilegible
        pass
    try:
        from ..models import Presupuesto

        for (tipo_cambio,) in db.query(Presupuesto.tipo_cambio).distinct().all():
            _añadir(tipo_cambio)
    except Exception:  # pragma: no cover - esquema antiguo
        pass
    for tasa in TASAS_SUGERIDAS.values():
        _añadir(tasa)
    return candidatas


def _mejor_factor(precio: float, tasas: list[float]) -> float:
    """Divisor que devuelve el precio a un rango plausible.

    Se prefiere el factor más pequeño que arregla el importe: si un precio se
    multiplicó una sola vez por la tasa basta con dividir una vez; si el ciclo
    se repitió (guardar → reutilizar → guardar) puede hacer falta la tasa al
    cuadrado, y también se contempla.
    """
    mejores: list[float] = []
    for tasa in tasas:
        for exponente in (1, 2, 3):
            factor = tasa ** exponente
            resultado = precio / factor
            if 0.01 <= resultado <= MAXIMO_PLAUSIBLE_USD:
                mejores.append(factor)
                break
    if not mejores:
        return 0.0
    # El factor más pequeño es el que menos supone: deshace lo justo.
    return min(mejores)


def _coste_total(registro) -> float:
    return sum(float(getattr(registro, campo, 0) or 0) for campo in CAMPOS_MONETARIOS[1:])


def _indice_precios_oficiales(db: Session) -> dict[str, float]:
    """Precio de referencia del catálogo oficial por nombre normalizado.

    Sirve para reconocer al «gemelo inflado»: el duplicado que el guardado
    automático creaba con el nombre traducido y el precio ya convertido.
    """
    from .busqueda_catalogo import normalizar
    from .traduccion import codigo_desde_pais, traducir

    try:
        codigo = codigo_desde_pais(getattr(db.query(Configuracion).first(), "empresa_pais", ""))
    except Exception:  # pragma: no cover - configuración ilegible
        codigo = ""
    indice: dict[str, float] = {}
    consulta = db.query(Partida.nombre, Partida.precio_unitario, Partida.es_oficial)
    for nombre, precio, es_oficial in consulta.all():
        if not es_oficial or not precio:
            continue
        claves = {normalizar(nombre or "")}
        if codigo:
            claves.add(normalizar(traducir(nombre or "", codigo)))
        for clave in claves:
            if clave:
                indice.setdefault(clave, float(precio))
    return indice


def _medianas_por_categoria(db: Session) -> dict[str, float]:
    """Mediana de precio por categoría, como escala de lo «normal»."""
    from statistics import median

    valores: dict[str, list[float]] = {}
    for categoria, precio in db.query(Partida.categoria, Partida.precio_unitario).all():
        if not precio or precio <= 0:
            continue
        valores.setdefault(str(categoria or ""), []).append(float(precio))
    return {cat: median(lista) for cat, lista in valores.items() if len(lista) >= 5}


def _factor_por_referencia(precio: float, referencia: float, tasas: list[float]) -> float:
    """Factor que explica ``precio`` como ``referencia`` multiplicada por una tasa."""
    if referencia <= 0 or precio <= 0:
        return 0.0
    for tasa in tasas:
        for exponente in (1, 2, 3):
            factor = tasa ** exponente
            proporcion = precio / (referencia * factor)
            if 0.5 <= proporcion <= 2.0:
                return factor
    return 0.0


def detectar_precios_anomalos(db: Session, incluir_productos: bool = True) -> list[dict]:
    """Registros del catálogo cuyo precio solo se explica por un error de moneda.

    Tres reglas, de más a menos evidencia, y ninguna «a ojo»:

    1. **Gemela oficial**: existe la misma partida en el catálogo oficial y el
       importe es el suyo multiplicado por una tasa real (el duplicado que
       creaba el guardado automático fuera de Venezuela).
    2. **Fuera de escala de su capítulo**: vale más de 50 veces la mediana de
       su categoría y dividirla por una tasa conocida la devuelve a esa escala.
    3. **Imposible en términos absolutos**: por encima de
       :data:`UMBRAL_CRITICO_USD` no existe unidad de obra que lo justifique.

    Lo que supera :data:`UMBRAL_SOSPECHOSO_USD` sin encajar en ninguna regla se
    informa igualmente, pero como «revisar a mano»: no se toca automáticamente
    para no estropear una partida cara legítima (una instalación llave en mano).
    """
    from .busqueda_catalogo import normalizar

    tasas = _tasas_candidatas(db)
    oficiales = _indice_precios_oficiales(db)
    medianas = _medianas_por_categoria(db)
    anomalias: list[Anomalia] = []

    for p in db.query(Partida).all():
        precio = float(p.precio_unitario or 0)
        coste = _coste_total(p)
        referencia = max(precio, coste)
        if referencia <= 0:
            continue

        factor = 0.0
        motivo = ""
        gravedad = "sospechosa"

        # Regla 1 — gemela del catálogo oficial.
        if not getattr(p, "es_oficial", False):
            precio_oficial = oficiales.get(normalizar(p.nombre or ""))
            if precio_oficial:
                factor = _factor_por_referencia(referencia, precio_oficial, tasas)
                if factor:
                    motivo = (
                        "Duplicado de una partida del catálogo con el precio ya "
                        f"convertido a moneda local (×{factor:,.2f})."
                    )
                    gravedad = "critica"

        # Regla 2 — fuera de la escala de su capítulo.
        if not factor:
            mediana = medianas.get(str(p.categoria or ""), 0.0)
            if mediana > 0 and referencia > mediana * 50:
                candidato = _mejor_factor(referencia, tasas)
                if candidato and (mediana / 5) <= (referencia / candidato) <= (mediana * 5):
                    factor = candidato
                    motivo = (
                        f"Vale {referencia / mediana:,.0f} veces la mediana de su "
                        f"capítulo; el importe es el precio en moneda local (×{factor:,.2f})."
                    )
                    gravedad = "critica"

        # Regla 3 — imposible en términos absolutos.
        if not factor and referencia > UMBRAL_CRITICO_USD:
            factor = _mejor_factor(referencia, tasas)
            motivo = (
                "Importe imposible para una unidad de obra: es el precio en "
                f"moneda local guardado como moneda base (×{factor:,.2f})."
                if factor else
                "Importe imposible para una unidad de obra; revísalo a mano."
            )
            gravedad = "critica"

        if not factor:
            if referencia <= UMBRAL_SOSPECHOSO_USD:
                continue
            motivo = motivo or (
                "Precio muy alto para una unidad de obra. Si es correcto, "
                "ignóralo; si no, corrígelo a mano."
            )
            anomalias.append(Anomalia(
                tipo="partida", id=p.id, nombre=p.nombre or "", unidad=p.unidad or "",
                precio=precio, precio_sugerido=precio, factor=0.0, motivo=motivo,
                gravedad=gravedad, reparable=False, detalle={"coste": round(coste, 2)},
            ))
            continue

        anomalias.append(Anomalia(
            tipo="partida",
            id=p.id,
            nombre=p.nombre or "",
            unidad=p.unidad or "",
            precio=precio,
            precio_sugerido=precio / factor,
            factor=factor,
            motivo=motivo,
            gravedad=gravedad,
            reparable=True,
            detalle={"coste": round(coste, 2)},
        ))

    if incluir_productos:
        from sqlalchemy import func, or_

        filtro_producto = or_(
            func.coalesce(Producto.precio_unitario, 0) > UMBRAL_SOSPECHOSO_USD,
            func.coalesce(Producto.precio_compra, 0) > UMBRAL_SOSPECHOSO_USD,
        )
        for pr in db.query(Producto).filter(filtro_producto).all():
            precio = float(pr.precio_unitario or 0)
            compra = float(pr.precio_compra or 0)
            referencia = max(precio, compra)
            factor = _mejor_factor(referencia, tasas) if referencia > UMBRAL_CRITICO_USD else 0.0
            anomalias.append(Anomalia(
                tipo="producto",
                id=pr.id,
                nombre=pr.nombre or "",
                unidad=pr.unidad or "",
                precio=precio,
                precio_sugerido=(precio / factor) if factor else precio,
                factor=factor,
                motivo=(
                    "Precio de producto guardado en moneda local sobre un catálogo "
                    f"en moneda base (×{factor:,.2f})."
                    if factor else
                    "Precio de producto muy alto; revísalo a mano."
                ),
                gravedad="critica" if referencia > UMBRAL_CRITICO_USD else "sospechosa",
                reparable=bool(factor),
            ))

    anomalias.sort(key=lambda a: a.precio, reverse=True)
    return [a.como_dict() for a in anomalias]


def _reparar_descomposicion(partida: Partida, factor: float) -> None:
    """Divide también los precios del APU para no dejar el desglose desfasado."""
    bruto = getattr(partida, "descomposicion_json", None)
    if not bruto:
        return
    try:
        datos = json.loads(bruto)
    except (TypeError, ValueError):
        return
    filas = datos.get("filas") if isinstance(datos, dict) else datos
    if not isinstance(filas, list):
        return
    for fila in filas:
        if not isinstance(fila, dict):
            continue
        for campo in ("precio", "precio_unitario", "importe", "coste_unitario"):
            valor = fila.get(campo)
            if isinstance(valor, (int, float)) and not isinstance(valor, bool):
                fila[campo] = round(float(valor) / factor, 4)
    partida.descomposicion_json = json.dumps(datos, ensure_ascii=False)


def reparar_precios_anomalos(db: Session, ids_partidas: list[int] | None = None,
                             ids_productos: list[int] | None = None) -> dict:
    """Devuelve a la moneda base los precios inflados por la tasa.

    Solo se tocan los registros que la detección considera reparables (existe
    un factor conocido que deja el importe en un rango creíble). Devuelve un
    resumen para poder informar al usuario de qué se ha corregido.
    """
    anomalias = detectar_precios_anomalos(db)
    corregidas: list[dict] = []
    pendientes: list[dict] = []

    for anomalia in anomalias:
        if not anomalia["reparable"]:
            pendientes.append(anomalia)
            continue
        factor = float(anomalia["factor"])
        if anomalia["tipo"] == "partida":
            if ids_partidas is not None and anomalia["id"] not in ids_partidas:
                continue
            partida = db.get(Partida, anomalia["id"])
            if partida is None:
                continue
            for campo in CAMPOS_MONETARIOS:
                valor = getattr(partida, campo, None)
                if valor:
                    setattr(partida, campo, round(float(valor) / factor, 2))
            _reparar_descomposicion(partida, factor)
        else:
            if ids_productos is not None and anomalia["id"] not in ids_productos:
                continue
            producto = db.get(Producto, anomalia["id"])
            if producto is None:
                continue
            for campo in ("precio_unitario", "precio_compra"):
                valor = getattr(producto, campo, None)
                if valor:
                    setattr(producto, campo, round(float(valor) / factor, 2))
        corregidas.append(anomalia)

    if corregidas:
        db.commit()
    return {
        "ok": True,
        "corregidas": corregidas,
        "total_corregidas": len(corregidas),
        "pendientes": pendientes,
        "total_pendientes": len(pendientes),
    }


def ids_partidas_anomalas(db: Session) -> list[int]:
    """Ids de las partidas con precio imposible, para filtrar la lista.

    El panel de salud y el filtro ``/partidas?salud=precio_absurdo`` usan esta
    misma fuente: el número que se enseña y las filas que se abren siempre
    coinciden.
    """
    try:
        return [a["id"] for a in detectar_precios_anomalos(db, incluir_productos=False)]
    except Exception:  # pragma: no cover - nunca debe tumbar la vista
        return []


def contar_precios_anomalos(db: Session) -> int:
    """Recuento para el panel de salud del catálogo."""
    return len(ids_partidas_anomalas(db))
