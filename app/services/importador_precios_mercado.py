"""Importador validado de la matriz nacional de precios.

Por defecto solo procesa referencias investigadas. Las filas pendientes nunca
se convierten en cero y los respaldos por tipo de cambio requieren una opción
explícita. Antes de escribir se valida **toda** la matriz para evitar cargas
parciales con unidad, rango, país o moneda incoherentes.
"""
from __future__ import annotations

import csv
import io
from datetime import date
from pathlib import Path

from sqlalchemy.orm import Session

from ..models import PrecioRecursoMercado, Recurso
from .precios_mercado import guardar_precio
from .unidades_precio import convertir_precio_unidad, sistema_unidades_pais

# Moneda de referencia de cada mercado. Debe cubrir LOS 23 de ``app.paises``:
# el que falte aquí es un mercado al que no se le puede cargar una matriz de
# precios, porque la validación de abajo rechaza el país. Australia, Canadá,
# Irlanda y Estados Unidos estuvieron fuera mucho tiempo sin que nada lo
# delatara (tests/test_latam.py::test_monedas_cubiertas lo vigila desde ahora).
MONEDA_PAIS = {"CO": "COP", "PE": "PEN", "MX": "MXN", "EC": "USD", "PA": "USD", "SV": "USD", "CL": "CLP", "AR": "ARS", "DO": "DOP", "UY": "UYU", "PY": "PYG", "BO": "BOB", "CR": "CRC", "GT": "GTQ", "HN": "HNL", "NI": "NIO", "VE": "USD", "ES": "EUR", "GB": "GBP", "IE": "EUR", "AU": "AUD", "CA": "CAD", "US": "USD"}
CONFIANZAS = {"confirmado", "referencia", "derivado", "provisional"}
IVA_VALIDO = {"si", "no", "no_aplica", "no_confirmado", "por_verificar"}
TRANSPORTE_VALIDO = {"si", "no", "no_aplica", "no_confirmado", "por_verificar"}

#: Contrato del CSV, en el orden en que se publica. El panel de operador lo
#: muestra como ayuda y el validador lo exige: una sola definición para que la
#: ayuda nunca se quede atrás respecto a la validación.
COLUMNAS_MATRIZ: tuple[str, ...] = (
    "codigo_recurso", "descripcion", "categoria", "unidad_fuente",
    "pais_codigo", "moneda", "precio_referencia", "precio_min",
    "precio_max", "fuente", "fecha_consulta", "confianza",
    "incluye_iva", "incluye_transporte", "origen", "observaciones",
)


def _texto(row: dict, clave: str) -> str:
    return str(row.get(clave) or "").strip()


def _numero(row: dict, clave: str, *, obligatorio: bool = False) -> float | None:
    bruto = _texto(row, clave).replace(",", ".")
    if not bruto:
        if obligatorio:
            raise ValueError(f"falta {clave}")
        return None
    valor = float(bruto)
    if valor <= 0:
        raise ValueError(f"{clave} debe ser mayor que cero")
    return valor


def _fecha(row: dict, clave: str, *, obligatoria: bool = False) -> date | None:
    bruto = _texto(row, clave)
    if not bruto:
        if obligatoria:
            raise ValueError(f"falta {clave}")
        return None
    try:
        return date.fromisoformat(bruto)
    except ValueError as exc:
        raise ValueError(f"{clave} no es ISO AAAA-MM-DD") from exc


def _unidad(valor: str) -> str:
    """Forma canónica de una unidad.

    Delegamos en ``unidades_precio.normalizar_unidad`` para que los alias
    (incluidos los imperiales) vivan en un solo sitio.
    """
    from .unidades_precio import normalizar_unidad

    return normalizar_unidad(valor)


def _texto_matriz(fuente) -> str:
    """Contenido de la matriz desde una ruta, unos bytes o un stream abierto.

    El panel de operador recibe el fichero subido como bytes; la herramienta de
    línea de comandos pasa una ruta. Un único punto de lectura evita que las
    dos vías validen de forma distinta.
    """
    if isinstance(fuente, (str, Path)):
        return Path(fuente).read_text(encoding="utf-8-sig")
    if isinstance(fuente, (bytes, bytearray)):
        return bytes(fuente).decode("utf-8-sig")
    if hasattr(fuente, "read"):
        bruto = fuente.read()
        if isinstance(bruto, (bytes, bytearray)):
            return bytes(bruto).decode("utf-8-sig")
        return str(bruto)
    raise TypeError("fuente debe ser una ruta, bytes o un stream de lectura")


def resolver_recursos(db: Session, *, nacional: bool = False) -> dict[str, Recurso]:
    """Recursos por código normalizado.

    En modo **nacional** la búsqueda se hace sin filtro de organización: una
    referencia nacional sirve a todas las empresas, de modo que no puede
    resolverse solo dentro de la organización que carga el fichero. Si varias
    organizaciones tienen el mismo código manda el identificador más bajo, el
    mismo criterio del SQL de carga, porque la referencia queda ligada al
    código estable y no a una copia concreta del recurso.
    """
    consulta = db.query(Recurso)
    if nacional:
        consulta = consulta.execution_options(sin_filtro_organizacion=True)
    salida: dict[str, Recurso] = {}
    for recurso in consulta.all():
        codigo = str(recurso.codigo or "").strip()
        if not codigo:
            continue
        actual = salida.get(codigo)
        if actual is None or recurso.id < actual.id:
            salida[codigo] = recurso
    return salida


#: Filas que se enseñan en la vista previa del panel. El informe completo va
#: por contadores; la muestra solo sirve para comprobar que el fichero es el
#: que se cree antes de pulsar «cargar».
MUESTRA_MAXIMA = 12

#: Campos que se comparan para decidir si una fila cambia de verdad. El
#: precio solo no basta: una referencia puede moverse de moneda o de rango
#: manteniendo el número, y eso también es un cambio que hay que contar.
CAMPOS_COMPARABLES = (
    "precio", "moneda", "precio_min", "precio_max",
    "unidad_referencia", "confianza", "incluye_iva", "incluye_transporte",
)


#: Estado de cada fila -> clave del contador en el resultado.
CONTADOR_ESTADO = {
    "creada": "creadas",
    "actualizada": "actualizadas",
    "sin_cambios": "sin_cambios",
}


def _referencias_nacionales(db: Session, paises: list[str]) -> list[PrecioRecursoMercado]:
    """Referencias nacionales activas de los países indicados."""
    if not paises:
        return []
    return (
        db.query(PrecioRecursoMercado)
        .filter(
            PrecioRecursoMercado.pais_codigo.in_(paises),
            PrecioRecursoMercado.organizacion_id.is_(None),
            PrecioRecursoMercado.activo.is_(True),
        )
        .all()
    )


def _indice_existentes(db: Session, paises: list[str]) -> dict[tuple, PrecioRecursoMercado]:
    """Índice por código estable y por identificador, como `guardar_precio`."""
    indice: dict[tuple, PrecioRecursoMercado] = {}
    for fila in _referencias_nacionales(db, paises):
        codigo = str(fila.codigo_recurso or "").strip()
        if codigo:
            indice[("cod", codigo, fila.pais_codigo)] = fila
        indice[("id", fila.recurso_id, fila.pais_codigo)] = fila
    return indice


def _buscar_existente(indice: dict[tuple, PrecioRecursoMercado], recurso: Recurso, pais: str):
    """El código manda sobre el identificador: sobrevive a copias del recurso."""
    codigo = str(recurso.codigo or "").strip()
    if codigo:
        fila = indice.get(("cod", codigo, pais))
        if fila is not None:
            return fila
    return indice.get(("id", recurso.id, pais))


def _mismo_precio(fila: PrecioRecursoMercado, dato: dict) -> bool:
    """¿La fila que ya existe es equivalente a la que traería el fichero?"""
    for campo in CAMPOS_COMPARABLES:
        actual = getattr(fila, campo, None)
        nuevo = dato.get(campo)
        if isinstance(actual, float) or isinstance(nuevo, float):
            try:
                if abs(float(actual or 0.0) - float(nuevo or 0.0)) > 1e-9:
                    return False
                continue
            except (TypeError, ValueError):
                return False
        if (actual or None) != (nuevo or None):
            return False
    return True


def importar_matriz_csv(
    db: Session,
    fuente,
    *,
    aplicar: bool = False,
    incluir_respaldo: bool = False,
    nacional: bool = False,
    reemplazar: bool = False,
) -> dict:
    resultado = {
        "filas": 0,
        "aplicables": 0,
        "creadas_o_actualizadas": 0,
        "pendientes": 0,
        "no_encontrados": 0,
        "creadas": 0,
        "actualizadas": 0,
        "sin_cambios": 0,
        "eliminadas": 0,
        "paises": [],
        "muestra": [],
        "errores": [],
    }
    recursos = resolver_recursos(db, nacional=nacional)
    vistos: set[tuple[str, str]] = set()
    planes: list[tuple[Recurso, dict]] = []

    with io.StringIO(_texto_matriz(fuente), newline="") as fh:
        reader = csv.DictReader(fh, delimiter=";")
        faltantes = sorted(set(COLUMNAS_MATRIZ) - set(reader.fieldnames or []))
        if faltantes:
            resultado["errores"].append(
                "Faltan columnas obligatorias: " + ", ".join(faltantes)
            )
            return resultado

        for numero_fila, row in enumerate(reader, start=2):
            resultado["filas"] += 1
            codigo = _texto(row, "codigo_recurso")
            pais = _texto(row, "pais_codigo").upper()
            clave = (codigo, pais)
            prefijo = f"fila {numero_fila} ({codigo or 'sin código'}/{pais or 'sin país'})"
            if clave in vistos:
                resultado["errores"].append(f"{prefijo}: fila duplicada")
                continue
            vistos.add(clave)

            origen = _texto(row, "origen")
            precio_raw = _texto(row, "precio_referencia")
            if not precio_raw:
                resultado["pendientes"] += 1
                if origen != "pendiente" or _texto(row, "confianza") != "pendiente":
                    resultado["errores"].append(
                        f"{prefijo}: una fila sin precio debe ser pendiente/pendiente"
                    )
                continue
            if origen == "base" and not incluir_respaldo:
                resultado["pendientes"] += 1
                continue
            if origen not in {"nacional", "base"}:
                resultado["errores"].append(f"{prefijo}: origen no permitido «{origen}»")
                continue

            recurso = recursos.get(codigo)
            if recurso is None:
                resultado["no_encontrados"] += 1
                resultado["errores"].append(f"{prefijo}: recurso no encontrado")
                continue
            try:
                if pais not in MONEDA_PAIS:
                    raise ValueError("país no soportado")
                moneda = _texto(row, "moneda").upper()
                if moneda != MONEDA_PAIS[pais]:
                    raise ValueError(
                        f"moneda {moneda or 'vacía'}; se esperaba {MONEDA_PAIS[pais]}"
                    )
                unidad_fila = _unidad(_texto(row, "unidad_fuente"))
                unidad_recurso = _unidad(recurso.unidad)
                factor_precio = 1.0
                if unidad_fila != unidad_recurso:
                    # Un mercado imperial (hoy solo Estados Unidos) cotiza en
                    # libras, galones, pies y yardas mientras el recurso cuenta
                    # en kilos, litros y metros. Se convierte el PRECIO, no la
                    # cantidad. Sin conversión posible la fila se rechaza:
                    # guardar el número tal cual daría un precio correcto en
                    # apariencia y desproporcionado en la realidad.
                    convertido = convertir_precio_unidad(
                        1.0, unidad_fila, unidad_recurso
                    )
                    if convertido is None or sistema_unidades_pais(pais) != "imperial":
                        raise ValueError(
                            f"unidad {_texto(row, 'unidad_fuente') or 'vacía'}; "
                            f"el recurso usa {recurso.unidad}"
                        )
                    factor_precio = convertido
                precio = _numero(row, "precio_referencia", obligatorio=True) * factor_precio
                # El rango se convierte con el mismo factor que el precio: si
                # no, la referencia diría «134,55 $/m² (10–15)» con el rango
                # todavía en pies cuadrados.
                minimo = _numero(row, "precio_min")
                maximo = _numero(row, "precio_max")
                if factor_precio != 1.0:
                    if minimo is not None:
                        minimo = minimo * factor_precio
                    if maximo is not None:
                        maximo = maximo * factor_precio
                if origen == "nacional" and (minimo is None or maximo is None):
                    raise ValueError("la referencia nacional debe conservar precio_min y precio_max")
                if minimo is not None and maximo is not None and maximo < minimo:
                    raise ValueError("precio_max es menor que precio_min")
                if minimo is not None and precio < minimo or maximo is not None and precio > maximo:
                    raise ValueError("precio_referencia queda fuera del rango")
                confianza = _texto(row, "confianza")
                if confianza not in CONFIANZAS:
                    raise ValueError(f"confianza no válida «{confianza}»")
                fuente = _texto(row, "fuente")
                if not fuente:
                    raise ValueError("falta fuente")
                consulta = _fecha(row, "fecha_consulta", obligatoria=True)
                iva = _texto(row, "incluye_iva")
                transporte = _texto(row, "incluye_transporte")
                if iva not in IVA_VALIDO:
                    raise ValueError(f"incluye_iva no válido «{iva}»")
                if transporte not in TRANSPORTE_VALIDO:
                    raise ValueError(f"incluye_transporte no válido «{transporte}»")
            except (TypeError, ValueError) as exc:
                resultado["errores"].append(f"{prefijo}: {exc}")
                continue

            planes.append((recurso, {
                "pais": pais,
                "precio": precio,
                "moneda": moneda,
                "precio_min": minimo,
                "precio_max": maximo,
                "unidad_referencia": _texto(row, "unidad_fuente"),
                "fuente": fuente,
                "confianza": confianza,
                "fecha_consulta": consulta,
                "incluye_iva": iva,
                "incluye_transporte": transporte,
                "observaciones": _texto(row, "observaciones"),
            }))

    resultado["aplicables"] = len(planes)
    resultado["paises"] = sorted({dato["pais"] for _, dato in planes})

    # Clasificación de la vista previa. Se resuelve con la misma regla que usa
    # `guardar_precio` (por código estable y, si no, por identificador) para
    # que el número prometido sea exactamente el número escrito.
    existentes = _indice_existentes(db, resultado["paises"])
    for recurso, dato in planes:
        fila = _buscar_existente(existentes, recurso, dato["pais"])
        estado = "creada"
        if fila is not None:
            estado = "sin_cambios" if _mismo_precio(fila, dato) else "actualizada"
        resultado[CONTADOR_ESTADO[estado]] = resultado[CONTADOR_ESTADO[estado]] + 1
        if len(resultado["muestra"]) < MUESTRA_MAXIMA:
            resultado["muestra"].append({
                "codigo": str(recurso.codigo or "").strip(),
                "descripcion": str(recurso.descripcion or "").strip(),
                "unidad": str(recurso.unidad or "").strip(),
                "pais": dato["pais"],
                "precio": dato["precio"],
                "moneda": dato["moneda"],
                "precio_anterior": (fila.precio if fila is not None else None),
                "estado": estado,
            })

    # Huérfanas: referencias nacionales del país que el fichero no menciona.
    # Solo se retiran en modo «reemplazar» y nunca se borran: se desactivan,
    # que para el cálculo de precios es lo mismo (`resolver_precio` filtra por
    # `activo`) pero conserva el histórico y se puede deshacer.
    huerfanas: list[PrecioRecursoMercado] = []
    if reemplazar and planes and not resultado["errores"]:
        cubiertos: set[tuple] = set()
        for recurso, dato in planes:
            codigo = str(recurso.codigo or "").strip()
            if codigo:
                cubiertos.add(("cod", codigo, dato["pais"]))
            cubiertos.add(("id", recurso.id, dato["pais"]))
        for fila in _referencias_nacionales(db, resultado["paises"]):
            codigo = str(fila.codigo_recurso or "").strip()
            if ("id", fila.recurso_id, fila.pais_codigo) in cubiertos:
                continue
            if codigo and ("cod", codigo, fila.pais_codigo) in cubiertos:
                continue
            huerfanas.append(fila)
    resultado["eliminadas"] = len(huerfanas)

    # La carga es todo-o-nada: un rango corrupto no puede convivir con las
    # filas que sí alcanzaron a guardarse antes del error.
    if aplicar and not resultado["errores"]:
        try:
            for recurso, dato in planes:
                guardar_precio(
                    db,
                    recurso.id,
                    dato["pais"],
                    dato["precio"],
                    dato["moneda"],
                    fuente=dato["fuente"],
                    confianza=dato["confianza"],
                    fecha_consulta=dato["fecha_consulta"],
                    precio_min=dato["precio_min"],
                    precio_max=dato["precio_max"],
                    unidad_referencia=dato["unidad_referencia"],
                    incluye_iva=dato["incluye_iva"],
                    incluye_transporte=dato["incluye_transporte"],
                    observaciones=dato["observaciones"],
                )
            for fila in huerfanas:
                fila.activo = False
            db.commit()
            resultado["creadas_o_actualizadas"] = len(planes)
        except Exception:
            db.rollback()
            raise
    return resultado
