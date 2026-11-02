"""Recalcula partidas del catálogo con los precios de mercado del país.

El catálogo se guardó históricamente con los precios base (Venezuela, USD).
Cuando una organización cotiza para España, Colombia, México, Perú… los
recursos tienen referencias nacionales en ``precios_recursos_mercado`` y esas
referencias son las que deben alimentar el APU y el precio de venta de la
partida, no el valor base convertido con una tasa.

Este módulo:

* Resuelve el precio de mercado de cada recurso de la descomposición (una
  sola consulta por lote).
* Sustituye el precio unitario de cada fila por el de mercado.
* Recalcula la cascada de costes (materiales, mano de obra, complementarios,
  otros) con la misma lógica CYPE del editor.
* Conserva el margen que tuvo la partida base (beneficio unitario) y aplica
  ese margen sobre el coste directo de mercado.

Si la organización no tiene precios de mercado para un recurso, la fila
vuelve a su precio base convertido a la moneda de la vista y se señala el
fallback, para no inventar cifras.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from ..models import Partida, Recurso
from ..paises import PAISES, resolver_mercado
from . import precios_publicos as pp
from .monedas import convertir, definicion
from .recursos import normalizar
from .tasa import factor_conversion_local, tasa_convertir_precio, tasa_sugerida
from .unidades_precio import convertir_precio_entre_unidades


@dataclass(frozen=True)
class ResultadoPartidaMercado:
    precio_unitario: float
    coste_materiales: float
    coste_mano_obra: float
    coste_complementarios: float
    coste_otros: float
    filas: list[dict]
    con_precio_mercado: bool


def _fila_precio_base(fila: dict, factor: float) -> float:
    try:
        valor = float(fila.get("precio") if fila.get("precio") is not None else fila.get("precio_unitario") or 0)
    except (TypeError, ValueError):
        valor = 0.0
    return tasa_convertir_precio(valor, factor)


def _filas_partida(partida: Partida) -> list[dict]:
    try:
        valor = json.loads(partida.descomposicion_json or "[]")
    except (TypeError, ValueError):
        valor = []
    filas = valor.get("filas", []) if isinstance(valor, dict) else valor
    return [dict(fila) if isinstance(fila, dict) else fila for fila in filas]


def _recurso_de_fila(recurso: Recurso, fila: dict) -> bool:
    cod_recurso = normalizar(recurso.codigo)
    cod_fila = normalizar(fila.get("codigo"))
    if cod_recurso and cod_fila:
        return cod_recurso == cod_fila
    return (
        normalizar(recurso.descripcion) == normalizar(fila.get("descripcion"))
        and normalizar(recurso.unidad) == normalizar(fila.get("unidad"))
        and normalizar(recurso.categoria) == normalizar(fila.get("categoria"))
    )


def _buscar_recursos(db: Session, filas: list[dict]) -> list[Recurso]:
    """Busca los recursos de la BD que corresponden a las filas del APU."""
    codigos = {normalizar(f.get("codigo")) for f in filas if f.get("codigo")}
    filas_sin_codigo = [f for f in filas if not (f.get("codigo") or "").strip()]
    if codigos and not filas_sin_codigo:
        return [
            r for r in db.query(Recurso).filter(Recurso.codigo != "").all()
            if normalizar(r.codigo) in codigos
        ]
    # Con filas sin código el volumen es pequeño: se barre la tabla local.
    recursos = db.query(Recurso).all()
    salida: list[Recurso] = []
    visto: set[int] = set()
    for fila in filas:
        for recurso in recursos:
            if recurso.id in visto:
                continue
            if _recurso_de_fila(recurso, fila):
                salida.append(recurso)
                visto.add(recurso.id)
                break
    return salida


def _precios_filas_desde_efectivos(
    filas: list[dict], recursos: list[Recurso], efectivos: dict[int, dict],
) -> dict[str, float]:
    """Proyecta precios de mercado a las claves de las filas de un APU."""
    por_id = {r.id: r for r in recursos}
    salida: dict[str, float] = {}
    for recurso in por_id.values():
        efectivo = efectivos.get(recurso.id)
        # Solo se consideran precios reales de este país: referencia nacional
        # o precio fijado por la organización. El precio base de la partida
        # original (Venezuela convertida) no debe alimentar el APU mostrado.
        if (
            efectivo is not None
            and efectivo.get("precio") is not None
            and not efectivo.get("requiere_tasa")
            and (efectivo.get("origen") or "base") in ("nacional", "organizacion")
        ):
            salida[normalizar(recurso.codigo)] = float(efectivo["precio"])
    # Filas sin código: match por descripción, unidad y categoría. Solo se
    # guardan las que tienen una referencia nacional real; las demás vuelven
    # al precio base.
    for fila in filas:
        codigo = normalizar(fila.get("codigo"))
        if codigo and codigo in salida:
            continue
        clave = (
            f"desc:{normalizar(fila.get('descripcion'))}|"
            f"{normalizar(fila.get('unidad'))}|{normalizar(fila.get('categoria'))}"
        )
        for recurso in por_id.values():
            if _recurso_de_fila(recurso, fila):
                efectivo = efectivos.get(recurso.id)
                if (
                    efectivo is not None
                    and efectivo.get("precio") is not None
                    and not efectivo.get("requiere_tasa")
                    and (efectivo.get("origen") or "base") in ("nacional", "organizacion")
                ):
                    salida.setdefault(clave, float(efectivo["precio"]))
                break
    return salida


def _resolver_precios_filas(
    db: Session, filas: list[dict], pais: str, org_id: int | None,
    moneda: str, factor: float,
) -> dict[str, float]:
    """Devuelve {clave_fila: precio de mercado en moneda de la vista}.

    La clave es el código normalizado cuando existe y, si no, una cadena
    derivada de descripción/unidad/categoría.
    """
    from .precios_mercado import resolver_precios_para_presupuesto_lote

    recursos = _buscar_recursos(db, filas)
    if not recursos:
        return {}
    efectivos = resolver_precios_para_presupuesto_lote(
        db, recursos, pais, org_id, moneda, tasa_usd_presupuesto=factor,
    )
    return _precios_filas_desde_efectivos(filas, recursos, efectivos)


def _resultado_partida_mercado(
    partida: Partida, filas: list[dict], precios: dict[str, float], factor: float,
) -> ResultadoPartidaMercado | None:
    """Aplica precios ya resueltos y recalcula costes con las reglas CYPE."""
    if not filas or not precios:
        return None

    desde_mercado = False
    nuevas_filas: list[dict] = []
    for fila in filas:
        nueva = dict(fila)
        codigo = fila.get("codigo")
        clave = normalizar(codigo) if codigo else ""
        if not clave or clave not in precios:
            clave = (
                f"desc:{normalizar(fila.get('descripcion'))}|"
                f"{normalizar(fila.get('unidad'))}|{normalizar(fila.get('categoria'))}"
            )
        precio = precios.get(clave)
        if precio is None:
            precio = _fila_precio_base(fila, factor)
        nueva["precio"] = precio
        nueva["precio_unitario"] = precio
        # El importe lo recalcula la cascada CYPE; aquí solo mantenemos el
        # precio por si la fila es un % de complementarios.
        nuevas_filas.append(nueva)
        if clave in precios:
            desde_mercado = True

    if not desde_mercado:
        return None
    from .importer import recalcular_descompuesto_cype

    resultado = recalcular_descompuesto_cype(nuevas_filas)
    costes = resultado.get("costes", {})
    coste_directo = float(resultado.get("coste_directo", 0) or 0)

    # Margen conservado de la partida base (USD). Si la partida no tenía
    # coste o precio usamos el margen por defecto del catálogo (35 % desde
    # 2026-08-25).
    coste_base = (
        float(partida.coste_materiales or 0)
        + float(partida.coste_mano_obra or 0)
        + float(partida.coste_complementarios or 0)
        + float(partida.coste_otros or 0)
    )
    precio_base = float(partida.precio_unitario or 0)
    margen = (precio_base - coste_base) / coste_base if coste_base > 0 else 0.35
    precio_venta = round(coste_directo * (1.0 + margen), 2)

    # Aplica los precios de la cascada (para las filas de % se usa el precio
    # base recalculado).
    for idx, precio_comp in resultado.get("precios_complementarios", {}).items():
        if 0 <= idx < len(nuevas_filas):
            nuevas_filas[idx]["precio"] = precio_comp
            nuevas_filas[idx]["precio_unitario"] = precio_comp
    for idx, importe in resultado.get("importes", {}).items():
        if 0 <= idx < len(nuevas_filas):
            nuevas_filas[idx]["importe"] = importe

    return ResultadoPartidaMercado(
        precio_unitario=precio_venta,
        coste_materiales=float(costes.get("materiales", 0) or 0),
        coste_mano_obra=float(costes.get("mano_obra", 0) or 0),
        coste_complementarios=float(costes.get("complementarios", 0) or 0),
        coste_otros=float(costes.get("otros", 0) or 0),
        filas=nuevas_filas,
        con_precio_mercado=desde_mercado,
    )


def recalcular_partida_mercado(
    db: Session,
    partida: Partida,
    pais: str,
    org_id: int | None,
    moneda: str,
    factor: float,
) -> ResultadoPartidaMercado | None:
    """Recalcula una partida con los precios de mercado de su país."""
    filas = [
        fila for fila in _filas_partida(partida)
        if isinstance(fila, dict) and fila.get("tipo") == "recurso"
    ]
    if not filas:
        return None
    precios = _resolver_precios_filas(db, filas, pais, org_id, moneda, factor)
    return _resultado_partida_mercado(partida, filas, precios, factor)


def _indice_recursos(recursos: list[Recurso]) -> dict:
    """Índice en memoria para no volver a recorrer recursos por cada fila."""
    por_codigo: dict[str, list[Recurso]] = {}
    por_descripcion: dict[tuple[str, str, str], list[Recurso]] = {}
    por_descripcion_sin_codigo: dict[tuple[str, str, str], list[Recurso]] = {}
    posicion: dict[int, int] = {}
    for indice, recurso in enumerate(recursos):
        posicion[recurso.id] = indice
        codigo = normalizar(recurso.codigo)
        clave = (
            normalizar(recurso.descripcion),
            normalizar(recurso.unidad),
            normalizar(recurso.categoria),
        )
        if codigo:
            por_codigo.setdefault(codigo, []).append(recurso)
        else:
            por_descripcion_sin_codigo.setdefault(clave, []).append(recurso)
        por_descripcion.setdefault(clave, []).append(recurso)
    return {
        "por_codigo": por_codigo,
        "por_descripcion": por_descripcion,
        "por_descripcion_sin_codigo": por_descripcion_sin_codigo,
        "posicion": posicion,
    }


def _buscar_recursos_en_indice(filas: list[dict], recursos: list[Recurso], indice: dict) -> list[Recurso]:
    """Equivalente en memoria de ``_buscar_recursos``, conservando su orden."""
    codigos = {normalizar(fila.get("codigo")) for fila in filas if fila.get("codigo")}
    filas_sin_codigo = [
        fila for fila in filas if not (fila.get("codigo") or "").strip()
    ]
    if codigos and not filas_sin_codigo:
        return [
            recurso for recurso in recursos
            if recurso.codigo is not None
            and recurso.codigo != ""
            and normalizar(recurso.codigo) in codigos
        ]

    salida: list[Recurso] = []
    vistos: set[int] = set()
    for fila in filas:
        codigo = normalizar(fila.get("codigo"))
        clave = (
            normalizar(fila.get("descripcion")),
            normalizar(fila.get("unidad")),
            normalizar(fila.get("categoria")),
        )
        if codigo:
            candidatos = list(indice["por_codigo"].get(codigo, ()))
            candidatos.extend(indice["por_descripcion_sin_codigo"].get(clave, ()))
            candidatos.sort(key=lambda recurso: indice["posicion"][recurso.id])
        else:
            candidatos = indice["por_descripcion"].get(clave, ())
        for recurso in candidatos:
            if recurso.id in vistos:
                continue
            salida.append(recurso)
            vistos.add(recurso.id)
            break
    return salida


def recalcular_partidas_mercado(
    db: Session,
    partidas: list[Partida],
    pais: str,
    org_id: int | None,
    moneda: str,
    factor: float,
) -> dict[int, ResultadoPartidaMercado]:
    """Recalcula un conjunto de partidas con dos lecturas, no N+1 consultas.

    La lista de recursos se consulta una vez; las referencias del mercado de
    todos ellos se resuelven en lote en otra consulta. Los precios y el APU se
    calculan en memoria por partida.
    """
    partidas_con_filas: list[tuple[Partida, list[dict]]] = []
    for partida in partidas or []:
        filas = [
            fila for fila in _filas_partida(partida)
            if isinstance(fila, dict) and fila.get("tipo") == "recurso"
        ]
        if filas:
            partidas_con_filas.append((partida, filas))
    if not partidas_con_filas:
        return {}

    try:
        from sqlalchemy.orm import load_only

        query = db.query(Recurso)
        solo_codigos = not any(
            not (fila.get("codigo") or "").strip()
            for _, filas in partidas_con_filas
            for fila in filas
        )
        if solo_codigos:
            query = query.filter(Recurso.codigo != "")
        try:
            query = query.options(load_only(
                Recurso.id,
                Recurso.codigo,
                Recurso.descripcion,
                Recurso.unidad,
                Recurso.categoria,
                Recurso.precio,
                Recurso.moneda,
            ))
        except (AttributeError, TypeError):
            pass
        recursos_disponibles = query.all()
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
        return {}

    indice = _indice_recursos(recursos_disponibles)
    recursos_por_partida: list[tuple[Partida, list[dict], list[Recurso]]] = []
    recursos_unicos: dict[int, Recurso] = {}
    for partida, filas in partidas_con_filas:
        recursos = _buscar_recursos_en_indice(filas, recursos_disponibles, indice)
        recursos_por_partida.append((partida, filas, recursos))
        for recurso in recursos:
            recursos_unicos.setdefault(recurso.id, recurso)
    if not recursos_unicos:
        return {}

    from .precios_mercado import resolver_precios_para_presupuesto_lote

    try:
        efectivos = resolver_precios_para_presupuesto_lote(
            db,
            list(recursos_unicos.values()),
            pais,
            org_id,
            moneda,
            tasa_usd_presupuesto=factor,
        )
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
        return {}

    salida: dict[int, ResultadoPartidaMercado] = {}
    for partida, filas, recursos in recursos_por_partida:
        try:
            precios = _precios_filas_desde_efectivos(filas, recursos, efectivos)
            resultado = _resultado_partida_mercado(partida, filas, precios, factor)
            if resultado is not None:
                salida[partida.id] = resultado
        except Exception:
            continue
    return salida


# ===========================================================================
# Precio de venta desde la matriz pública de precios
# ===========================================================================
#
# Lo de arriba resuelve el precio con las referencias de recurso que cada
# organización tiene en ``precios_recursos_mercado``. Cuando esa tabla no tiene
# nada para el país —el caso de la mayoría de las cuentas nuevas— la partida se
# queda con el precio base venezolano.
#
# Lo de abajo lee la matriz de precios pública, que ya está en el repositorio
# por país, y devuelve el precio de venta local. Es la misma cifra que se
# publica en las fichas de precios, así que lo que se anuncia y lo que se
# cobra son el mismo número. Medido el 02/11/2026, el precio base se queda
# corto entre 2 y 3 veces en España y entre 4 y 5 en Estados Unidos.
#
# ===========================================================================

#: Grupo de la matriz de recursos → categoría de coste del editor.
#: La matriz usa «maquinaria»; el editor enseña ese dinero en ``coste_otros``.
_CATEGORIA_POR_GRUPO = {
    "materiales": "materiales",
    "mano_obra": "mano_obra",
    "maquinaria": "equipo",
}

#: Recargo por costes directos complementarios cuando la partida no lo declara.
_COMPLEMENTARIOS_DEFECTO = 0.0

#: Margen por defecto del catálogo propio (``catalogo_propio.MARGEN_DEFECTO``).
_MARGEN_DEFECTO = 0.35


@dataclass(frozen=True)
class PrecioPartida:
    """Precio de una partida con su desglose, ya en la unidad del catálogo.

    ``origen`` vale ``"mercado"`` cuando el precio sale de la matriz del país y
    ``"catalogo"`` cuando no hay dato y se devuelve el base tal cual.
    """

    precio: float
    moneda: str
    origen: str
    confianza: str = ""
    aviso: str = ""
    coste_materiales: float | None = None
    coste_mano_obra: float | None = None
    coste_equipo: float | None = None
    filas: tuple[dict, ...] = field(default_factory=tuple)

    @property
    def coste_total(self) -> float | None:
        if self.coste_materiales is None:
            return None
        return (
            (self.coste_materiales or 0.0)
            + (self.coste_mano_obra or 0.0)
            + (self.coste_equipo or 0.0)
        )

    @property
    def margen_pct(self) -> float | None:
        """Beneficio sobre venta (0,267 = 26,7 %), como lo enseña el editor."""
        coste = self.coste_total
        if not coste or not self.precio:
            return None
        return 1 - coste / self.precio


# ---------------------------------------------------------------------------
# Utilidades internas
# ---------------------------------------------------------------------------


def _numero(valor) -> float:
    try:
        return float(valor)
    except (TypeError, ValueError):
        return 0.0


def _codigo_de_la_partida(partida) -> str:
    """Código con el que la partida se publica en el catálogo de precios.

    El orden importa: ``codigo_interno`` es el código de la matriz pública;
    ``codigo_externo`` y ``codigo_legacy`` solo sirven si el primero no está.
    """
    for atributo in ("codigo_interno", "codigo_externo", "codigo_legacy"):
        valor = str(getattr(partida, atributo, "") or "").strip()
        if valor:
            return valor
    return ""


def _filas_de_la_partida(partida) -> list[dict]:
    """Filas del descompuesto guardado en la partida (JSON o dict)."""
    bruto = getattr(partida, "descomposicion_json", None)
    if not bruto:
        return []
    try:
        datos = json.loads(bruto) if isinstance(bruto, str) else bruto
    except (TypeError, ValueError):
        return []
    if isinstance(datos, dict):
        datos = datos.get("filas") or []
    if not isinstance(datos, list):
        return []
    return [dict(fila) for fila in datos if isinstance(fila, dict)]


def _es_fila_de_recurso(fila: dict) -> bool:
    """La fila de cierre de complementarios no es un recurso: es un porcentaje.

    Viene con ``codigo`` vacío, ``categoria = "complementarios"`` y un
    ``rendimiento`` que es el porcentaje a aplicar —no una cantidad—. Pedirle
    precio a la matriz es lo que hacía que el desglose entero se descartara.
    """
    categoria = str(fila.get("categoria") or "").strip().lower()
    if categoria == "complementarios":
        return False
    if str(fila.get("tipo") or "").strip().lower() in ("porcentaje", "complementarios"):
        return False
    return bool(str(fila.get("codigo") or "").strip())


def _complementarios_pct(filas: Iterable[dict]) -> float:
    """Porcentaje de costes directos complementarios declarado en la partida."""
    for fila in filas:
        if str(fila.get("categoria") or "").strip().lower() == "complementarios":
            return _numero(fila.get("rendimiento"))
    for fila in filas:
        if "complementario" in str(fila.get("grupo") or "").lower():
            return _numero(fila.get("rendimiento"))
    return _COMPLEMENTARIOS_DEFECTO


def _ficha_del_mercado(codigo: str, cc: str) -> dict | None:
    """Ficha publicada de esa partida en ese país, o ``None`` si no la publica."""
    indice = pp._indice(cc)
    if not indice:
        return None
    destino = (indice.get("por_codigo") or {}).get(codigo)
    if not destino:
        return None
    ficha = (indice.get("partidas") or {}).get(tuple(destino))
    return ficha if isinstance(ficha, dict) else None


def _lineas_por_codigo(ficha: dict) -> dict[str, dict]:
    """{código_recurso: línea publicada}.

    Se casa **por código**, no por orden ni por nombre: unir por posición
    cruzaba el precio de «Adhesivo» con el de «Mortero» en cuanto una partida
    aparecía en dos apartados con líneas parecidas.
    """
    salida: dict[str, dict] = {}
    for linea in ficha.get("lineas") or ():
        ref = str(linea.get("codigo") or "").strip()
        if ref:
            salida[ref] = linea
    return salida


def _grupo_de(fila: dict) -> str:
    grupo = str(fila.get("grupo") or "").strip().lower()
    if grupo in _CATEGORIA_POR_GRUPO:
        return _CATEGORIA_POR_GRUPO[grupo]
    if "mano" in grupo:
        return "mano_obra"
    if "equipo" in grupo or "maquinaria" in grupo:
        return "equipo"
    return _CATEGORIA_POR_GRUPO.get(
        str(fila.get("categoria") or "").strip().lower(), "materiales"
    )


def _margen(ficha: dict, partida) -> float:
    """Margen del catálogo en esa partida, en tanto por uno."""
    for valor in (ficha.get("margen"), getattr(partida, "margen", None)):
        try:
            numero = float(valor)
        except (TypeError, ValueError):
            continue
        if 0 <= numero < 1:
            return numero
        if 1 <= numero <= 100:
            return numero / 100.0
    return _MARGEN_DEFECTO


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------


def precio_de_partida(
    partida,
    *,
    pais: str,
    moneda_documento: str | None = None,
    tasa: float | None = None,
    con_desglose: bool = True,
) -> PrecioPartida:
    """Precio de venta de ``partida`` en el mercado ``pais``.

    ``pais`` admite nombre, código ISO o alias (``"España"``, ``"ES"``,
    ``"Mexico"``). ``moneda_documento`` es la moneda en la que se va a emitir
    el presupuesto; si se indica y no coincide con la del mercado, se convierte
    con ``tasa`` (``1 USD = tasa moneda``). Sin tasa no se convierte: se
    devuelve el precio del mercado en su moneda y **no** un número con la
    etiqueta equivocada.

    ``con_desglose=False`` se salta el cálculo de costes y líneas: es la ruta
    del editor cuando solo quiere el precio y hay 3.000 partidas en pantalla.
    """
    base = _numero(getattr(partida, "precio_unitario", 0.0))
    codigo = _codigo_de_la_partida(partida)
    mercado = resolver_mercado(pais or "")
    cc = str((mercado or {}).get("codigo") or "").strip().upper()

    if not cc or not codigo:
        return _sin_dato(
            partida, base, moneda_documento, tasa,
            "Precio del catálogo base: no hay precio de referencia para este mercado.",
        )

    moneda_mercado = str((PAISES.get(cc) or {}).get("moneda") or "USD").strip().upper()
    ficha = _ficha_del_mercado(codigo, cc)
    if ficha is None:
        return _sin_dato(partida, base, moneda_documento, tasa, _aviso_sin_dato(cc, ""))
    if str(ficha.get("moneda") or "").strip().upper() != moneda_mercado:
        # Un mercado que publica en una moneda que no es la suya es un dato
        # corrupto: el precio estaría bien y la etiqueta mal.
        return _sin_dato(partida, base, moneda_documento, tasa, _aviso_sin_dato(cc, ""))

    calculo = _calcular(partida, cc, ficha, con_desglose=con_desglose)
    if calculo is None:
        return _sin_dato(partida, base, moneda_documento, tasa, _aviso_sin_dato(cc, moneda_mercado))

    precio, costes, filas = calculo
    moneda = moneda_mercado
    if moneda_documento:
        destino = str(moneda_documento).strip().upper()
        if destino and destino != moneda_mercado:
            convertido = _convertir_todo(precio, costes, filas, moneda_mercado, destino, tasa)
            if convertido is not None:
                precio, costes, filas = convertido
                moneda = destino
        elif destino:
            moneda = destino

    return PrecioPartida(
        precio=round(precio, 4),
        moneda=moneda,
        origen="mercado",
        confianza=_confianza(ficha),
        coste_materiales=round(costes["materiales"], 4),
        coste_mano_obra=round(costes["mano_obra"], 4),
        coste_equipo=round(costes["equipo"], 4),
        filas=tuple(filas),
    )


def _sin_dato(
    partida, base: float, moneda_documento: str | None, tasa: float | None, aviso: str
) -> PrecioPartida:
    """La partida se devuelve con su precio de catálogo y un aviso."""
    precio = base
    moneda = "USD"
    destino = str(moneda_documento or "").strip().upper()
    if destino and destino not in ("", "USD"):
        try:
            precio = float(convertir(base, "USD", destino, tasa_usd_destino=tasa))
            moneda = destino
        except ValueError:
            aviso = (
                f"{aviso} No hay tasa de cambio verificada: el importe está en USD."
            ).strip()
    return PrecioPartida(precio=round(precio, 4), moneda=moneda, origen="catalogo", aviso=aviso)


def _aviso_sin_dato(cc: str, moneda_mercado: str) -> str:
    if cc == "VE":
        return "Venezuela usa el catálogo base en USD: es su propio mercado de origen."
    pais = (PAISES.get(cc) or {}).get("nombre") or cc
    return (
        f"Sin precio de referencia en {pais} para esta partida: se usa el "
        "precio del catálogo base. Revisa el precio antes de enviarlo."
    )


def _confianza(ficha: dict) -> str:
    """Cómo de sólido es el precio: cuántas líneas de coste lo sostienen."""
    lineas = ficha.get("lineas") or ()
    if len(lineas) >= 5:
        return "nacional"
    if len(lineas) >= 3:
        return "parcial"
    return "respaldo"


def _tasa_a_usd(moneda: str) -> float | None:
    """Tasa verificada ``1 USD = X moneda``, o ``None`` si no hay una buena."""
    valor = tasa_sugerida(moneda) or factor_conversion_local(moneda, tasa_sugerida(moneda))
    try:
        numero = float(valor or 0)
    except (TypeError, ValueError):
        return None
    return numero if numero > 0 else None


def _tasa_de(moneda: str, tasa_documento: float | None, moneda_documento: str | None) -> float | None:
    """Tasa USD→``moneda``: la del documento si es esa moneda, si no la verificada.

    La tasa del presupuesto se define como «1 USD = tasa moneda_del_presupuesto»,
    así que solo sirve para la moneda del documento. Aplicarla a la moneda del
    mercado es el error clásico: 17,06 (pesos por dólar) sobre un precio en
    euros no convierte nada, solo cambia la etiqueta.
    """
    moneda = str(moneda or "").strip().upper()
    if moneda in ("", "USD", "PAB"):
        return 1.0
    documento = str(moneda_documento or "").strip().upper()
    if documento == moneda:
        try:
            numero = float(tasa_documento or 0)
        except (TypeError, ValueError):
            numero = 0.0
        if numero > 0:
            return numero
    return _tasa_a_usd(moneda)


def _convertir_todo(precio, costes, filas, origen: str, destino: str, tasa):
    """Convierte precio, costes y líneas con la MISMA tasa, o ``None``.

    La tasa del documento es ``1 USD = tasa moneda``, que sirve para ir y para
    volver a USD; cuando falta una de las dos patas (presupuesto en pesos
    sobre un precio en euros) se completa con la tasa verificada de esa
    moneda. Si no hay ninguna de las dos, no se convierte.
    """
    tasa_destino = _tasa_de(destino, tasa, destino)
    tasa_origen = _tasa_de(origen, tasa, destino)
    if tasa_destino is None or tasa_origen is None:
        return None
    try:
        precio_conv = float(
            convertir(
                precio, origen, destino,
                tasa_usd_destino=tasa_destino, tasa_usd_origen=tasa_origen,
            )
        )
        costes_conv = {
            clave: float(
                convertir(
                    valor, origen, destino,
                    tasa_usd_destino=tasa_destino, tasa_usd_origen=tasa_origen,
                )
            )
            for clave, valor in costes.items()
        }
        filas_conv = [
            {
                **fila,
                "precio": float(
                    convertir(
                        fila["precio"], origen, destino,
                        tasa_usd_destino=tasa_destino, tasa_usd_origen=tasa_origen,
                    )
                ),
                "importe": float(
                    convertir(
                        fila["importe"], origen, destino,
                        tasa_usd_destino=tasa_destino, tasa_usd_origen=tasa_origen,
                    )
                ),
            }
            for fila in filas
        ]
    except (ValueError, KeyError, TypeError):
        return None
    return precio_conv, costes_conv, filas_conv


def _calcular(partida, cc: str, ficha: dict, *, con_desglose: bool):
    """(precio, costes, filas) en la unidad del catálogo, o ``None``.

    Dos caminos, y la diferencia importa:

    * **sin desglose** (ruta rápida del editor, 3.000 partidas): se toma el
      precio de venta ya publicado y solo se cambia de unidad. No se recompone
      nada, así que no hay ningún margen que inventar.
    * **con desglose**: se recompone desde el descompuesto de la partida con
      los precios de recurso del país, aplicando la misma regla que la ficha
      pública (``coste × (1 + margen)``). Lo que se enseña como beneficio es
      la diferencia real entre ese precio y esos costes.
    """
    unidad_catalogo = str(getattr(partida, "unidad", "") or "")
    unidad_publicada = str(ficha.get("unidad") or "")

    if not con_desglose:
        factor = convertir_precio_entre_unidades(1.0, unidad_publicada, unidad_catalogo)
        precio = _numero(ficha.get("pu"))
        if factor is None or precio <= 0:
            return None
        # El desglose no hace falta para esta cifra: los costes quedan en cero
        # para que el editor no pinte un beneficio del 100 % con datos que no
        # ha pedido. Quien quiera el desglose lo pide.
        return precio * factor, {"materiales": 0.0, "mano_obra": 0.0, "equipo": 0.0}, []

    lineas = _lineas_por_codigo(ficha)
    if not lineas:
        return None
    if any(_numero(linea.get("precio")) <= 0 for linea in lineas.values()):
        return None

    filas_partida = _filas_de_la_partida(partida)
    margen = _margen(ficha, partida)

    if filas_partida:
        resultado = _desde_descompuesto(
            filas_partida, lineas, unidad_catalogo, ficha
        )
    else:
        resultado = _desde_ficha(lineas, unidad_catalogo, ficha, unidad_publicada)
    if resultado is None:
        return None

    precio, costes, salida, complementarios_pct = resultado
    if precio <= 0 or not salida:
        return None
    return precio, costes, salida


def _desde_descompuesto(filas_partida, lineas, unidad_catalogo, ficha):
    """Recompone la partida con los precios de recurso del país."""
    salida: list[dict] = []
    costes = {"materiales": 0.0, "mano_obra": 0.0, "equipo": 0.0}
    directo = 0.0
    for fila in filas_partida:
        if not _es_fila_de_recurso(fila):
            continue
        ref = str(fila.get("codigo") or "").strip()
        publicada = lineas.get(ref)
        if publicada is None:
            return None
        # El precio del recurso llega en la unidad del recurso (``lb``, ``h``)
        # y la base lo guarda en métrico: esa es la que se convierte.
        precio_recurso = convertir_precio_entre_unidades(
            _numero(publicada.get("precio")),
            publicada.get("unidad"),
            fila.get("unidad") or publicada.get("unidad"),
        )
        # El rendimiento guardado ya está por unidad de la partida del catálogo
        # (``m2``): convertir otra vez lo multiplicaría por 10,76 y un
        # alicatado saldría diez veces caro en Estados Unidos.
        if precio_recurso is None:
            return None
        rendimiento = _numero(fila.get("rendimiento"))
        if rendimiento <= 0:
            continue
        importe = rendimiento * precio_recurso
        directo += importe
        categoria = _grupo_de(fila)
        costes[categoria] += importe
        salida.append(
            {
                "codigo": ref,
                "descripcion": str(fila.get("descripcion") or ""),
                "categoria": categoria,
                "unidad": str(fila.get("unidad") or ""),
                "rendimiento": round(rendimiento, 6),
                "precio": round(precio_recurso, 6),
                "importe": round(importe, 6),
            }
        )
    if directo <= 0 or not salida:
        return None
    complementarios_pct = _complementarios_pct(filas_partida) / 100.0
    if complementarios_pct <= 0:
        complementarios_pct = _numero(ficha.get("compl_pct")) / 100.0
    return _cerrar(directo, costes, salida, complementarios_pct, ficha)


def _desde_ficha(lineas, unidad_catalogo, ficha, unidad_publicada):
    """Sin descompuesto propio: se reconstruye desde la ficha publicada."""
    salida: list[dict] = []
    costes = {"materiales": 0.0, "mano_obra": 0.0, "equipo": 0.0}
    directo = 0.0
    for publicada in lineas.values():
        rendimiento = convertir_precio_entre_unidades(
            _numero(publicada.get("rendimiento")), unidad_publicada, unidad_catalogo
        )
        precio_recurso = _numero(publicada.get("precio"))
        if rendimiento is None or precio_recurso <= 0:
            return None
        importe = rendimiento * precio_recurso
        directo += importe
        categoria = _grupo_de(publicada)
        costes[categoria] += importe
        salida.append(
            {
                "codigo": str(publicada.get("codigo") or ""),
                "descripcion": str(publicada.get("nombre") or ""),
                "categoria": categoria,
                "unidad": str(publicada.get("unidad") or ""),
                "rendimiento": round(rendimiento, 6),
                "precio": round(precio_recurso, 6),
                "importe": round(importe, 6),
            }
        )
    if directo <= 0 or not salida:
        return None
    return _cerrar(
        directo, costes, salida, _numero(ficha.get("compl_pct")) / 100.0, ficha
    )


def _margen_publicado(ficha: dict) -> float:
    """Margen que la ficha pública aplicó, deducido de sus propias cifras.

    El artefacto no guarda el margen, pero sí el precio de venta y las líneas
    que lo componen: ``margen = pu / (directo × (1 + complementarios)) − 1``.
    Deducirlo de ahí es lo único que garantiza que el precio recompuesto no se
    invente un margen distinto del que se publica.
    """
    directo = 0.0
    for linea in ficha.get("lineas") or ():
        directo += _numero(linea.get("rendimiento")) * _numero(linea.get("precio"))
    pu = _numero(ficha.get("pu"))
    complementarios_pct = _numero(ficha.get("compl_pct")) / 100.0
    if directo <= 0 or pu <= 0:
        return _MARGEN_DEFECTO
    margen = pu / (directo * (1 + complementarios_pct)) - 1
    return margen if 0 <= margen < 1 else _MARGEN_DEFECTO


def _cerrar(directo, costes, salida, complementarios_pct, ficha):
    """Aplica complementarios y margen, como la ficha pública."""
    coste_directo = directo * (1 + complementarios_pct)
    margen = _margen_publicado(ficha)
    precio = coste_directo * (1 + margen)
    if precio <= 0:
        return None
    # El recargo de complementarios no es una categoría del editor: se reparte
    # en proporción para que materiales + mano + equipo cuadre con el coste
    # real y el beneficio que ve el usuario sea el verdadero.
    if complementarios_pct > 0:
        costes = {clave: valor * (1 + complementarios_pct) for clave, valor in costes.items()}
    # El desglose que se enseña es el de venta: cada línea lleva su parte del
    # margen, igual que en la ficha pública. Si se enseñara el coste, las
    # líneas sumarían 20,14 bajo un precio de 27,46 y el cliente vería un
    # documento que no cuadra.
    salida = _filas_de_venta(salida, precio / coste_directo)
    return precio, costes, salida, complementarios_pct


def _filas_de_venta(filas: list[dict], factor: float) -> list[dict]:
    """Lleva las líneas de coste al precio de venta, con el mismo factor."""
    if not filas or factor <= 0:
        return filas
    salida = []
    for fila in filas:
        salida.append(
            {
                **fila,
                "precio": round(fila["precio"] * factor, 6),
                "importe": round(fila["importe"] * factor, 6),
            }
        )
    return salida


def precio_de_partida_catalogo(
    db,
    partida,
    *,
    pais: str | None = None,
    moneda: str | None = None,
    tasa: float | None = None,
    con_desglose: bool = True,
) -> PrecioPartida:
    """Como :func:`precio_de_partida`, tomando país/moneda de la configuración.

    Es el atajo del editor: la organización define su mercado y su moneda en un
    solo sitio (``Configuracion``) y no en cada llamada.
    """
    from ..models import Configuracion

    cfg = db.query(Configuracion).first()
    if pais is None:
        pais = getattr(cfg, "empresa_pais", "") or ""
    if moneda is None:
        moneda = getattr(cfg, "moneda_default", "USD")
    if tasa is None:
        tasa = getattr(cfg, "tasa_cambio", None)
    return precio_de_partida(
        partida, pais=pais, moneda_documento=moneda, tasa=tasa, con_desglose=con_desglose
    )


def pais_con_matriz(codigo_pais: str | None) -> bool:
    """Si ese mercado tiene matriz de precios propia."""
    cc = str(codigo_pais or "").strip().upper()
    try:
        return cc in pp.PAISES_PRECIOS_PUBLICOS
    except AttributeError:  # pragma: no cover - versión antigua del servicio
        return False


def decimales_de(moneda: str | None) -> int:
    """Decimales con los que se enseña esa moneda."""
    return definicion(moneda).decimales
