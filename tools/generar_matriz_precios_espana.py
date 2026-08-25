"""Genera la matriz nacional auditada de precios de recursos para España.

Publica observaciones directas (documentadas en
``docs/INVESTIGACION_PRECIOS_ESPANA.md``) y completa el resto con
referencias derivadas de la canasta investigada por categoría. No promete
una cotización de tienda: cada fila conserva rango, fecha, metodología y
confianza.

Todas las cifras se expresan en EUR y en la unidad física de
``recursos.json``. Los rangos observados se conservan en
``precio_min``/``precio_max`` para poder auditarlos.

Uso:
    python3 tools/generar_matriz_precios_espana.py
"""
from __future__ import annotations

import csv
import json
import statistics
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "basedatos_partidas/datos/recursos.json"
OUT = ROOT / "basedatos_partidas/salida/precios_recursos_espana.csv"
PAISES = (("ES", "EUR"),)
FECHA = "2026-08-25"
FECHA_METODOLOGIA = "2026-08-25"

R_ES = "docs/INVESTIGACION_PRECIOS_ESPANA.md"
METODOLOGIA = "docs/METODOLOGIA_PRECIOS_REFERENCIA_ESPANA.md"
# Tasa de corte usada solo para normalizar el precio base USD antes de
# aplicarle el factor de mercado observado. El resultado queda congelado en
# EUR y con fecha; no se recalcula silenciosamente en producción.
# EUR/USD 1,1677 (xe.com 22/08/2026; BCE 21/08: 1,1681) -> 1 USD = 0,8564 EUR.
TASAS_CORTE = {"ES": 0.8564}


@dataclass(frozen=True)
class Referencia:
    precio: float
    minimo: float
    maximo: float
    fuente: str
    confianza: str = "referencia"
    observaciones: str = "Referencia nacional normalizada; puede variar por proveedor, marca, disponibilidad, IVA y volumen."
    incluye_iva: str = "no"
    incluye_transporte: str = "no_confirmado"


def ref(precio, minimo, maximo, fuente, **kwargs) -> Referencia:
    """Crea y valida una referencia en la unidad física del catálogo."""
    precio, minimo, maximo = map(float, (precio, minimo, maximo))
    if minimo <= 0 or maximo < minimo or not minimo <= precio <= maximo:
        raise ValueError(f"Rango inválido: {minimo} <= {precio} <= {maximo}")
    return Referencia(precio, minimo, maximo, fuente, **kwargs)


# Referencias de materiales/equipos ligadas a un código y una unidad
# concretos. Precios observados el 22/08/2026 (ver documento de fuentes).
REFERENCIAS: dict[str, dict[str, Referencia]] = {
    "MT-CEMENTO": {
        "ES": ref(0.14, 0.10, 0.19, R_ES, observaciones="Saco 25 kg a 2,50-4,75 € según almacén o retail; sin IVA ni porte."),
    },
    "MT-ARENA": {
        "ES": ref(28, 20, 38, R_ES, incluye_transporte="si", observaciones="Arena lavada puesta en obra; 15-25 €/t en acopio más porte."),
    },
    "MT-PIEDRA-PIC": {
        "ES": ref(30, 22, 40, R_ES, incluye_transporte="si", observaciones="Grava puesta en obra; 12-20 €/t en acopio más porte."),
    },
    "MT-ACERO-CAB": {
        "ES": ref(1.15, 0.95, 1.40, R_ES, observaciones="B500S a 700-900 €/t en base; suministro cortado y puesto en obra."),
    },
    "MT-ALAMBRE": {
        "ES": ref(2.1, 1.7, 2.6, R_ES),
    },
    "MT-MALLA-ELEC": {
        "ES": ref(5.5, 4.0, 7.0, R_ES),
    },
    "MT-PYL-PLACA125": {
        "ES": ref(4.0, 3.2, 5.0, R_ES, observaciones="Placa estándar BA-13; observación directa Leroy Merlin/Obramat/Pladur."),
    },
    "MT-PYL-PLACA": {
        "ES": ref(4.9, 4.0, 6.2, R_ES, observaciones="Placa estándar BA-15."),
    },
    "MT-PYL-PLACA-RH": {
        "ES": ref(8.2, 7.0, 9.5, R_ES, observaciones="Placa H1 resistente a la humedad 12,5-13 mm."),
    },
    "MT-PYL-LANA": {
        "ES": ref(8.0, 6.0, 12.0, R_ES),
    },
    "MT-PYL-PASTA": {
        "ES": ref(1.2, 0.9, 1.6, R_ES),
    },
    "MT-ADH-C2TE": {
        "ES": ref(0.36, 0.24, 0.48, R_ES, observaciones="Adhesivo C2 TE saco 25 kg a 6-12 €."),
    },
    # El extremo bajo de la familia se usa como derivación para C1; no se
    # presenta como observación independiente de un producto C1 específico.
    "MT-ADH-C1": {
        "ES": ref(0.20, 0.16, 0.24, R_ES, confianza="derivado", observaciones="Derivado del extremo inferior de la familia de adhesivos; validar producto C1 concreto."),
    },
    "MT-JUN-CG2": {
        "ES": ref(3.2, 2.2, 4.5, R_ES),
    },
    "MT-AUT-NIV": {
        "ES": ref(0.44, 0.32, 0.56, R_ES, observaciones="Autonivelante saco 25 kg a 8-14 €."),
    },
    "MT-PASTA-YESO": {
        "ES": ref(0.42, 0.30, 0.60, R_ES),
    },
    "MT-PIN-CAUCHO": {
        "ES": ref(4.5, 3.0, 7.0, R_ES, observaciones="Pintura plástica mate; el catálogo VE la llama de caucho."),
    },
    "MT-PIN-ESMALTE": {
        "ES": ref(10.0, 8.0, 14.0, R_ES),
    },
    "MT-BLQ-20": {
        "ES": ref(2.3, 1.8, 2.8, R_ES),
    },
    "MT-BLQ-15": {
        "ES": ref(1.5, 1.2, 1.9, R_ES),
    },
    "MT-BLQ-10": {
        "ES": ref(1.1, 0.9, 1.4, R_ES),
    },
    "MT-BLQ-ARC-15": {
        "ES": ref(0.45, 0.35, 0.55, R_ES, observaciones="Ladrillo hueco doble a 180-280 €/millar."),
    },
    "MT-LADRILLO": {
        "ES": ref(0.35, 0.25, 0.45, R_ES),
    },
    "MT-MADERA-EST": {
        "ES": ref(520, 420, 620, R_ES),
    },
    "MT-CONC-180": {
        "ES": ref(92, 82, 105, R_ES, incluye_transporte="si"),
    },
    "MT-CONC-210": {
        "ES": ref(100, 90, 115, R_ES, incluye_transporte="si", observaciones="Hormigón HA-25 puesto en obra."),
    },
    "MT-CONC-250": {
        "ES": ref(108, 96, 122, R_ES, incluye_transporte="si"),
    },
    "MT-CONC-300": {
        "ES": ref(118, 105, 132, R_ES, incluye_transporte="si"),
    },
    "MT-MANTO-ASF": {
        "ES": ref(8.5, 6.0, 12.0, R_ES, observaciones="Lámina asfáltica prefabricada con armadura de poliéster."),
    },
    "MT-AISL-TERM": {
        "ES": ref(10.0, 6.0, 18.0, R_ES),
    },
    "MT-PANEL-SAND": {
        "ES": ref(38, 28, 50, R_ES),
    },
    "MT-LAMINA-ZINC": {
        "ES": ref(16, 12, 22, R_ES, observaciones="Chapa grecada/prelacada de cubierta."),
    },
    "MT-TEJA-CRIOLLA": {
        "ES": ref(1.0, 0.8, 1.3, R_ES, observaciones="Teja árabe curva; 12-22 €/m² de cubierta."),
    },
    "MT-CANON": {
        "ES": ref(7, 4, 12, R_ES, observaciones="Canon de vertido RCD en vertedero autorizado."),
    },
    "MT-GEOTEXTIL": {
        "ES": ref(1.1, 0.8, 1.5, R_ES),
    },
    "MT-POLIET": {
        "ES": ref(0.6, 0.4, 0.9, R_ES),
    },
    "MT-FORM-MADERA": {
        "ES": ref(10, 8, 14, R_ES, observaciones="Encofrado de madera amortizado por uso."),
    },
    "MT-PERFIL-ACERO": {
        "ES": ref(2.0, 1.6, 2.4, R_ES),
    },
    "MT-ELECTRODO": {
        "ES": ref(4.5, 3.0, 6.0, R_ES),
    },
    "MT-PLO-PPR20": {
        "ES": ref(2.2, 1.5, 3.0, R_ES),
    },
    "MT-PLO-PVC4": {
        "ES": ref(5.0, 4.0, 7.0, R_ES, observaciones="PVC saneamiento DN110."),
    },
    "MT-ELE-CABLE": {
        "ES": ref(0.65, 0.45, 0.90, R_ES, observaciones="Equivalente peninsular H07V-K 2,5 mm²."),
    },
    "MT-ELE-TUB20": {
        "ES": ref(0.45, 0.30, 0.70, R_ES),
    },
    "MT-ELE-MECA": {
        "ES": ref(5.0, 3.0, 8.0, R_ES),
    },
    "MT-BREAKER": {
        "ES": ref(8.5, 6.0, 12.0, R_ES, observaciones="Interruptor magnetotérmico."),
    },
    "MT-DIFERENCIAL": {
        "ES": ref(32, 25, 45, R_ES),
    },
    "MT-VIDRIO-6": {
        "ES": ref(38, 30, 50, R_ES),
    },
    "MT-CIELO-DESM": {
        "ES": ref(11, 8, 14, R_ES, observaciones="Falso techo desmontable de fibra mineral 60x60."),
    },
    "MQ-RETRO": {
        "ES": ref(45, 35, 55, R_ES, incluye_iva="por_verificar", observaciones="Retroexcavadora/mixta con operador y martillo hidráulico."),
    },
    "MQ-VOLQ": {
        "ES": ref(50, 40, 60, R_ES, incluye_transporte="si", observaciones="Camión volquete 6 m³ con chófer."),
    },
    "MQ-BOMBA-CONC": {
        "ES": ref(78, 65, 95, R_ES, incluye_transporte="si"),
    },
    "MQ-GRUA": {
        "ES": ref(70, 55, 85, R_ES),
    },
    "MQ-MEZCL": {
        "ES": ref(3.0, 2.0, 4.5, R_ES, observaciones="Hormigonera de obra; alquiler ~25 €/día prorrateado."),
    },
    "MQ-MART-NEUM": {
        "ES": ref(11, 8, 15, R_ES),
    },
    "MQ-ANDAMIO": {
        "ES": ref(2.8, 2.0, 4.0, R_ES),
    },
    "MQ-BANO-PORT": {
        "ES": ref(110, 85, 140, R_ES, observaciones="Alquiler mensual de caseta/baño portátil con mantenimiento."),
    },
}


OFICIALES = {
    "MO-OF1", "MO-OF1-PISO", "MO-OF1-ALI", "MO-OF1-ALB", "MO-OF1-MON",
    "MO-OF1-PIN", "MO-OF1-PLO", "MO-OF1-ELE", "MO-OF1-CAB",
    "MO-OF1-CARP", "MO-OF1-SOLD", "MO-OF1-CARPM", "MO-OF1-VIDR",
    "MO-OF1-AC", "MO-OF1-JARD",
}
# precio, mínimo y máximo por jornada de 8 h (€/jornada) — COSTE EMPRESA, no tarifa autónomo con margen
# Metodología 2026-08-25: se usa coste empresa (bruto convenio + SS 32.15% + costes fijos) como referencia nacional,
# no tarifa autónomo facturada (22-32 €/h oficial 1ª) que ya incluye beneficio del autónomo.
# Así el catálogo aplica su propio margen (30%) sin doble margen.
# Fuentes: Convenio General Construcción 2024-2026 BOE, tablas Barcelona 2025 (BOP 17/03/2026), Presupix coste empresa 19.80 €/h,
# Autopromotor coste mensual 3.431,76 € → 20.50 €/h, ObraHub bruto oficial 1ª 11.50-13.50 €/h → coste empresa 15.18-17.82 + costes → 20.50,
# Motordepresupuestos tarifa mercado oficial 1ª 22-32 €/h (con beneficio), oficial 2ª 18-25, peón 15-21.
ESPECIALIDAD_DIRECTA = {
    "MO-OF1-ELE": {"ES": (192, 160, 224)},  # electricista 24 €/h central (20-28), +15% vs albañil general por especialidad SEC
    "MO-OF1-PLO": {"ES": (184, 152, 216)},  # fontanero 23 €/h central (19-27)
    "MO-OF1-PIN": {"ES": (160, 128, 192)},  # pintor 20 €/h central (16-24), banda baja oficial
    "MO-OF1-SOLD": {"ES": (200, 160, 240)}, # soldador 25 €/h central (20-30), oficio escaso pero coste empresa no tarifa País Vasco 36-50
    "MO-OF1-ALI": {"ES": (176, 144, 208)},  # alicatador 22 €/h central (18-26)
    "MO-OF1-PISO": {"ES": (176, 144, 208)}, # solador 22 €/h central (18-26)
}
OFICIAL_GENERAL = {
    "ES": (168, 144, 200),  # albañil oficial 1ª 21 €/h central (18-25) coste empresa, no tarifa autónomo 27 (22-32) que incluía beneficio
}
AYUDANTE = {
    "ES": (120, 96, 144),   # peón/ayudante 15 €/h central (12-18) coste empresa, no 18 (15-21) tarifa autónomo
}


def referencias_mano_obra() -> dict[str, dict[str, Referencia]]:
    """Precio por hora para los 17 roles, con directos y derivados explícitos."""
    salida: dict[str, dict[str, Referencia]] = {}
    for codigo in sorted(OFICIALES):
        salida[codigo] = {}
        for pais, general in OFICIAL_GENERAL.items():
            jornal = ESPECIALIDAD_DIRECTA.get(codigo, {}).get(pais)
            directo = jornal is not None or codigo in {"MO-OF1", "MO-OF1-ALB"}
            precio, minimo, maximo = jornal or general
            salida[codigo][pais] = ref(
                precio / 8, minimo / 8, maximo / 8, R_ES,
                confianza="referencia" if directo else "derivado",
                incluye_iva="no_aplica",
                incluye_transporte="no_aplica",
                observaciones=(
                    "Jornal del oficio normalizado a 8 h; tarifa facturada, no incluye automáticamente cargas del empleador."
                    if directo else
                    "Tarifa derivada del oficial general por falta de jornal local del oficio; no incluye automáticamente cargas del empleador."
                ),
            )
    salida["MO-AYU"] = {
        pais: ref(
            p / 8, mn / 8, mx / 8, R_ES,
            incluye_iva="no_aplica", incluye_transporte="no_aplica",
            observaciones="Jornal de peón/ayudante normalizado a 8 h; tarifa facturada, no incluye automáticamente cargas del empleador.",
        )
        for pais, (p, mn, mx) in AYUDANTE.items()
    }
    salida["MO-AYU-ESP"] = {}
    for pais, (ayu, ayu_min, ayu_max) in AYUDANTE.items():
        oficial, of_min, of_max = OFICIAL_GENERAL[pais]
        salida["MO-AYU-ESP"][pais] = ref(
            (ayu + oficial) / 16,
            (ayu_min + of_min) / 16,
            (ayu_max + of_max) / 16,
            R_ES,
            confianza="derivado",
            incluye_iva="no_aplica", incluye_transporte="no_aplica",
            observaciones="Tarifa horaria derivada del punto medio entre ayudante y oficial; validar con la empresa.",
        )
    return salida


REFERENCIAS.update(referencias_mano_obra())


def iter_recursos(data):
    for categoria in ("mano_obra", "materiales", "maquinaria"):
        for codigo, item in (data.get(categoria) or {}).items():
            if not isinstance(item, dict) or "descripcion" not in item:
                continue
            # Los compuestos se abren en sus componentes y no existen como
            # recurso físico en la base de datos de la aplicación.
            if item.get("composicion"):
                continue
            yield codigo, categoria, item


def completar_referencias_derivadas(data: dict) -> dict[tuple[str, str], tuple[float, float, float]]:
    """Cubre recursos sin observación individual con una canasta nacional.

    Para cada país y familia se calcula la mediana de la relación entre los
    precios locales investigados y el precio base USD convertido a la tasa de
    corte. Los límites usan las medianas equivalentes de los rangos
    observados. Así se localiza el nivel de mercado sin fingir una cotización
    de tienda.
    """
    fichas = {
        codigo: (categoria, item)
        for codigo, categoria, item in iter_recursos(data)
    }
    factores: dict[tuple[str, str], tuple[float, float, float]] = {}
    for pais, _moneda in PAISES:
        for categoria in ("materiales", "maquinaria"):
            centrales, minimos, maximos = [], [], []
            for codigo, por_pais in REFERENCIAS.items():
                dato = por_pais.get(pais)
                ficha = fichas.get(codigo)
                if (
                    dato is None
                    or ficha is None
                    or ficha[0] != categoria
                    or dato.confianza != "referencia"
                ):
                    continue
                base_local = float(ficha[1]["precio"]) * TASAS_CORTE[pais]
                if base_local <= 0:
                    continue
                centrales.append(dato.precio / base_local)
                minimos.append(dato.minimo / base_local)
                maximos.append(dato.maximo / base_local)
            if not centrales:
                raise ValueError(f"No hay anclas para calibrar {categoria}/{pais}")
            central = statistics.median(centrales)
            minimo = min(central, statistics.median(minimos))
            maximo = max(central, statistics.median(maximos))
            factores[(pais, categoria)] = (central, minimo, maximo)

    for codigo, categoria, item in iter_recursos(data):
        if categoria == "mano_obra":
            continue  # los 17 roles ya tienen referencia propia o derivada
        for pais, _moneda in PAISES:
            if REFERENCIAS.get(codigo, {}).get(pais) is not None:
                continue
            central, minimo, maximo = factores[(pais, categoria)]
            base_local = float(item["precio"]) * TASAS_CORTE[pais]
            REFERENCIAS.setdefault(codigo, {})[pais] = ref(
                base_local * central,
                base_local * minimo,
                base_local * maximo,
                METODOLOGIA,
                confianza="derivado",
                observaciones=(
                    "Precio referencial nacional derivado de la canasta de mercado "
                    "investigada para esta familia; no es una cotización de tienda."
                ),
            )
    return factores


def _numero(valor: float) -> str:
    return f"{valor:.6f}".rstrip("0").rstrip(".")


def main():
    data = json.loads(SRC.read_text(encoding="utf-8"))
    factores = completar_referencias_derivadas(data)
    rows = []
    codigos = set()
    for codigo, categoria, item in iter_recursos(data):
        codigos.add(codigo)
        for pais, moneda in PAISES:
            dato = REFERENCIAS.get(codigo, {}).get(pais)
            rows.append({
                "codigo_recurso": codigo,
                "descripcion": item["descripcion"],
                "categoria": categoria,
                "unidad_fuente": item.get("unidad", "ud"),
                "pais_codigo": pais,
                "moneda": moneda,
                "precio_referencia": _numero(dato.precio) if dato else "",
                "precio_min": _numero(dato.minimo) if dato else "",
                "precio_max": _numero(dato.maximo) if dato else "",
                "fuente": dato.fuente if dato else "",
                "fecha_consulta": (
                    FECHA_METODOLOGIA if dato and dato.fuente == METODOLOGIA
                    else FECHA if dato else ""
                ),
                "confianza": dato.confianza if dato else "pendiente",
                "incluye_iva": dato.incluye_iva if dato else "por_verificar",
                "incluye_transporte": dato.incluye_transporte if dato else "no_confirmado",
                "origen": "nacional" if dato else "pendiente",
                "observaciones": dato.observaciones if dato else "Pendiente de investigación específica.",
            })

    referencias_huerfanas = sorted(set(REFERENCIAS) - codigos)
    if referencias_huerfanas:
        raise ValueError(f"Referencias de recursos inexistentes: {referencias_huerfanas}")
    pendientes = [r for r in rows if r["origen"] == "pendiente"]
    if pendientes:
        raise ValueError(f"Filas sin referencia: {[r['codigo_recurso'] for r in pendientes]}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]), delimiter=";", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    directas = sum(r["confianza"] == "referencia" for r in rows)
    derivadas = sum(r["confianza"] == "derivado" for r in rows)
    print(
        f"Generadas {len(rows)} filas: {directas} directas + "
        f"{derivadas} derivadas en {OUT}"
    )
    for (pais, categoria), (centro, minimo, maximo) in sorted(factores.items()):
        print(f"  {pais}/{categoria}: factor {centro:.3f} ({minimo:.3f}–{maximo:.3f})")


if __name__ == "__main__":
    main()
