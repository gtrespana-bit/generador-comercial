"""Genera la matriz nacional auditada de precios de recursos LatAm.

Publica observaciones directas y completa el resto con referencias derivadas
de la canasta investigada de cada país/familia. No promete una cotización de
tienda: cada fila conserva rango, fecha, metodología y confianza.

Todas las cifras se expresan en la unidad física de ``recursos.json``. Los
rangos de presentaciones (saco, placa, rollo) se normalizan aquí una sola vez
y se conservan en ``precio_min``/``precio_max`` para poder auditarlos.
"""
from __future__ import annotations

import csv
import json
import statistics
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "basedatos_partidas/datos/recursos.json"
OUT = ROOT / "basedatos_partidas/salida/precios_recursos_latam.csv"
PAISES = (("CO", "COP"), ("PE", "PEN"), ("MX", "MXN"), ("EC", "USD"), ("PA", "USD"), ("SV", "USD"), ("CL", "CLP"), ("AR", "ARS"))
FECHA = "2026-08-25"
FECHA_METODOLOGIA = "2026-08-20"

R1 = "docs/INVESTIGACION_PRECIOS_RONDA_1.md"
R2 = "docs/INVESTIGACION_PRECIOS_RONDA_2.md"
R3 = "docs/INVESTIGACION_PRECIOS_RONDA_3.md"
R4 = "docs/INVESTIGACION_PRECIOS_RONDA_4.md"
R5 = "docs/INVESTIGACION_PRECIOS_RONDA_5_MANO_OBRA.md"
R6 = "docs/INVESTIGACION_PRECIOS_RONDA_6_EQUIPOS.md"
RPA = "docs/INVESTIGACION_PRECIOS_PA_SV.md"
RCL = "docs/INVESTIGACION_PRECIOS_CL_AR.md"
RAR = "docs/INVESTIGACION_PRECIOS_CL_AR.md"
METODOLOGIA = "docs/METODOLOGIA_PRECIOS_REFERENCIA_LATAM.md"
# Tasas de corte usadas solo para normalizar el precio base USD antes de
# aplicarle el factor de mercado observado. El resultado queda congelado en
# moneda nacional y con fecha; no se recalcula silenciosamente en producción.
TASAS_CORTE = {"CO": 3128.65, "PE": 3.37, "MX": 17.06, "EC": 1.0, "PA": 1.0, "SV": 1.0, "CL": 925.90, "AR": 1497.38}


@dataclass(frozen=True)
class Referencia:
    precio: float
    minimo: float
    maximo: float
    fuente: str
    confianza: str = "referencia"
    observaciones: str = "Referencia nacional normalizada; puede variar por proveedor, marca, disponibilidad, IVA y volumen."
    incluye_iva: str = "por_verificar"
    incluye_transporte: str = "no_confirmado"


def ref(precio, minimo, maximo, fuente, **kwargs) -> Referencia:
    """Crea y valida una referencia en la unidad física del catálogo."""
    precio, minimo, maximo = map(float, (precio, minimo, maximo))
    if minimo <= 0 or maximo < minimo or not minimo <= precio <= maximo:
        raise ValueError(f"Rango inválido: {minimo} <= {precio} <= {maximo}")
    return Referencia(precio, minimo, maximo, fuente, **kwargs)


# Referencias materiales/equipos que sí pueden ligarse a un código y una
# unidad concretos. No convertir filas que la investigación dejó «pendiente».
REFERENCIAS: dict[str, dict[str, Referencia]] = {
    "MT-CEMENTO": {
        "CO": ref(28_000 / 50, 23_500 / 50, 44_900 / 50, R1),
        "PE": ref(31 / 42.5, 27.5 / 42.5, 35.5 / 42.5, R1),
        "MX": ref(240 / 50, 185 / 50, 295 / 50, R1),
        "EC": ref(8.5 / 50, 7.63 / 50, 10.5 / 50, R1),
        "PA": ref(8.25 / 42.5, 7.99 / 42.5, 8.60 / 42.5, RPA),
        "SV": ref(8.73 / 42.5, 7.90 / 42.5, 9.85 / 42.5, RPA),
        "CL": ref(4790 / 25, 3590 / 25, 5090 / 25, RCL),
        "AR": ref(11433 / 50, 9050 / 50, 14000 / 50, RAR),
    },
    "MT-ARENA": {
        "CO": ref(100_000, 80_000, 220_000, R1),
        "PE": ref(85, 50, 110, R1),
        "MX": ref(600, 280, 900, R1),
        "EC": ref(20, 18, 28, R1),
        "PA": ref(34, 30, 38, RPA),
        "SV": ref(35, 17, 38, RPA),
        "CL": ref(33190, 16379, 38190, RCL),
        "AR": ref(33500, 28000, 47644, RAR),
    },
    "MT-PIEDRA-PIC": {
        "CO": ref(115_000, 90_000, 240_000, R1),
        "PE": ref(100, 65, 140, R1),
        "MX": ref(500, 320, 750, R1),
        "EC": ref(20, 16, 25, R1),
        "PA": ref(35, 30, 40, RPA),
        "SV": ref(45.05, 22, 50, RPA),
        "CL": ref(34500, 32190, 36190, RCL),
        "AR": ref(40000, 31445, 67900, RAR),
    },
    "MT-ACERO-CAB": {
        "CO": ref(4_000, 3_650, 4_350, R1),
        # Perú quedó por diámetro/pieza; no se inventa una conversión a kg.
        "MX": ref(22, 17.5, 26, R1),
        "EC": ref(0.98, 0.85, 1.10, R1),
        "PA": ref(1.10, 0.95, 1.25, RPA),
        "SV": ref(1.15, 1.0, 1.35, RPA),
        "CL": ref(1100, 900, 1300, RCL),
        "AR": ref(1200, 1000, 1500, RAR),
    },
    "MT-BLQ-15": {
        "CO": ref(2_600, 2_000, 3_200, R1),
        "MX": ref(17, 12, 22, R1),
        "EC": ref(0.43, 0.35, 0.50, R1),
        "PA": ref(0.95, 0.71, 0.99, RPA),
        "SV": ref(0.40, 0.35, 0.45, RPA),
        "CL": ref(1840, 990, 1840, RCL),
        "AR": ref(1500, 1300, 1800, RAR),
    },
    "MT-LADRILLO": {
        "CO": ref(1_000, 500, 1_200, R1),
        "PE": ref(1.5, 1.2, 1.8, R1),
        "MX": ref(6.4, 5.8, 7.0, R1),
    },
    "MT-ALAMBRE": {
        "CO": ref(4_500, 3_500, 5_500, R1),
        "PE": ref(140 / 25, 120 / 25, 160 / 25, R1),
        "MX": ref(33, 33, 33, R1, observaciones="Referencia puntual aproximada por kg; requiere segundo proveedor."),
    },
    "MT-CONC-210": {
        "CO": ref(525_000, 350_000, 700_000, R1, incluye_transporte="por_verificar"),
        "EC": ref(105, 95, 115, R1, incluye_transporte="por_verificar"),
        "PA": ref(125, 100, 150, RPA, incluye_transporte="por_verificar"),
        "SV": ref(135.35, 130, 145, RPA, incluye_transporte="por_verificar"),
        "CL": ref(110000, 80000, 118405, RCL, incluye_transporte="por_verificar"),
        "AR": ref(168478, 137655, 199876, RAR, incluye_transporte="por_verificar"),
    },
    "MT-PYL-PLACA125": {
        "CO": ref(48_900 / 2.9768, 48_900 / 2.9768, 48_900 / 2.9768, R2),
        "PE": ref(30.15 / 2.9768, 28.3 / 2.9768, 32 / 2.9768, R2),
        "MX": ref(210 / 2.9768, 190 / 2.9768, 230 / 2.9768, R2, incluye_iva="no_confirmado"),
        "EC": ref(10.67 / 2.9768, 10.67 / 2.9768, 10.67 / 2.9768, R2, incluye_iva="si"),
    },
    "MT-PYL-PLACA-RH": {
        "CO": ref(91_700 / 2.9768, 91_700 / 2.9768, 91_700 / 2.9768, R2),
        "PE": ref(51.45 / 2.9768, 49.9 / 2.9768, 53 / 2.9768, R2),
        "MX": ref(327 / 2.9768, 289 / 2.9768, 365 / 2.9768, R2, incluye_iva="no"),
        "EC": ref(18.085 / 2.9768, 17.11 / 2.9768, 19.06 / 2.9768, R2, incluye_iva="si"),
    },
    "MT-PIN-CAUCHO": {
        "CO": ref(36_500 / 3.785, 28_000 / 3.785, 45_000 / 3.785, R3),
        "EC": ref(17 / 3.785, 12 / 3.785, 22 / 3.785, R3),
    },
    "MT-PLO-PVC4": {
        "CO": ref(21_750, 21_750, 21_750, R3, observaciones="Referencia regional por metro lineal; requiere contraste local."),
        "PE": ref(4.10, 4.10, 4.10, R3, observaciones="Referencia regional por metro lineal; requiere contraste local."),
        "EC": ref(4.80, 4.80, 4.80, R3, observaciones="Referencia regional por metro lineal; requiere contraste local."),
    },
    "MT-ELE-CABLE": {
        "CO": ref(3_975, 3_975, 3_975, R3, observaciones="Referencia regional THW 12 AWG por metro; confirmar rollo y marca."),
        "EC": ref(0.90, 0.90, 0.90, R3, observaciones="Referencia regional THW 12 AWG por metro; confirmar rollo y marca."),
    },
    "MT-ADH-C2TE": {
        "CO": ref(59_125 / 25, 31_900 / 25, 86_350 / 25, R4),
        "PE": ref(36.9 / 25, 16.9 / 25, 42 / 25, R4),
        "MX": ref(401 / 25, 401 / 25, 401 / 25, R4),
    },
    # El extremo bajo de la familia se usa solo como derivación para C1; no se
    # presenta como observación independiente de un producto C1 específico.
    "MT-ADH-C1": {
        "CO": ref(31_900 / 25, 31_900 / 25, 31_900 / 25, R4, confianza="derivado", observaciones="Derivado del extremo inferior de la familia de adhesivos; validar producto C1 concreto."),
        "PE": ref(16.9 / 25, 16.9 / 25, 16.9 / 25, R4, confianza="derivado", observaciones="Derivado del extremo inferior de la familia de adhesivos; validar producto C1 concreto."),
    },
    "MQ-RETRO": {
        "CO": ref(120_000, 90_000, 150_000, R6, incluye_iva="por_verificar", incluye_transporte="no_confirmado"),
        "PE": ref(160, 150, 170, R6, incluye_transporte="si"),
        "MX": ref(1_100, 800, 1_500, R6, incluye_transporte="no_confirmado"),
        "EC": ref(30, 30, 30, R6, incluye_transporte="no_confirmado", observaciones="Tarifa municipal por hora; validar equipo, operador, combustible y flete."),
        "PA": ref(35, 30, 45, RPA, incluye_transporte="no_confirmado", observaciones="Tarifa horaria retroexcavadora en Panamá; validar operador, combustible y flete."),
        "SV": ref(30, 25, 35, RPA, incluye_transporte="no_confirmado", observaciones="Tarifa horaria retroexcavadora en El Salvador; validar operador, combustible y flete."),
        "CL": ref(30000, 25000, 35000, RCL, incluye_transporte="no_confirmado", observaciones="Tarifa horaria retroexcavadora en Chile; validar operador, combustible y flete."),
        "AR": ref(35000, 30000, 40000, RAR, incluye_transporte="no_confirmado", observaciones="Tarifa horaria retroexcavadora en Argentina; validar operador, combustible y flete."),
    },
    "MQ-VOLQ": {
        "PE": ref(125, 110, 140, R6, incluye_transporte="si", observaciones="Tarifa horaria de volquete; confirmar capacidad, operador, combustible y mínimo."),
    },
}


OFICIALES = {
    "MO-OF1", "MO-OF1-PISO", "MO-OF1-ALI", "MO-OF1-ALB", "MO-OF1-MON",
    "MO-OF1-PIN", "MO-OF1-PLO", "MO-OF1-ELE", "MO-OF1-CAB",
    "MO-OF1-CARP", "MO-OF1-SOLD", "MO-OF1-CARPM", "MO-OF1-VIDR",
    "MO-OF1-AC", "MO-OF1-JARD",
}
ESPECIALIDAD_DIRECTA = {
    "MO-OF1-ELE": {
        "CO": (125_000, 100_000, 150_000), "MX": (1_125, 950, 1_300), "EC": (22.71, 22.71, 22.71),
    },
    "MO-OF1-PLO": {
        "CO": (120_000, 95_000, 145_000), "MX": (1_050, 900, 1_200), "EC": (22.29, 22.29, 22.29),
    },
    "MO-OF1-PIN": {
        "CO": (87_500, 65_000, 110_000), "MX": (700, 600, 800), "EC": (20.83, 20.83, 20.83),
    },
    "MO-OF1-SOLD": {
        "CO": (137_500, 110_000, 165_000), "MX": (1_350, 1_100, 1_600), "EC": (27.08, 27.08, 27.08),
    },
}
# precio, mínimo y máximo por jornada de 8 h
OFICIAL_GENERAL = {
    "CO": (110_000, 90_000, 130_000),
    "PE": (69.75, 69.75, 69.75),
    "MX": (750, 650, 850),
    "EC": (21.67, 21.67, 21.67),
    "PA": (45, 40, 50),
    "SV": (28, 25, 35),
    "CL": (55000, 45000, 65000),
    "AR": (45624, 41136, 50784),
}
AYUDANTE = {
    "CO": (72_500, 60_000, 85_000),
    "PE": (62.80, 62.80, 62.80),
    "MX": (400, 350, 450),
    "EC": (20.315, 20.00, 20.63),
    "PA": (35, 30, 40),
    "SV": (16, 13, 20),
    "CL": (35000, 30000, 40000),
    "AR": (38808, 34992, 43192),
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
                precio / 8, minimo / 8, maximo / 8, R5,
                confianza="referencia" if directo else "derivado",
                incluye_iva="no_aplica",
                incluye_transporte="no_aplica",
                observaciones=(
                    "Jornal del oficio normalizado a 8 h; no incluye automáticamente cargas del empleador."
                    if directo else
                    "Tarifa derivada del oficial general por falta de jornal local del oficio; no incluye automáticamente cargas del empleador."
                ),
            )
    salida["MO-AYU"] = {
        pais: ref(
            p / 8, mn / 8, mx / 8, R5,
            incluye_iva="no_aplica", incluye_transporte="no_aplica",
            observaciones="Jornal de ayudante/peón normalizado a 8 h; no incluye automáticamente cargas del empleador.",
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
            R5,
            confianza="derivado",
            incluye_iva="no_aplica",
            incluye_transporte="no_aplica",
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
    corte. Los límites usan las medianas equivalentes de los rangos observados.
    Así se localiza el nivel de mercado sin fingir una cotización de tienda.
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

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]), delimiter=";", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    investigadas = sum(r["origen"] == "nacional" for r in rows)
    directas = sum(r["confianza"] == "referencia" for r in rows)
    derivadas = sum(r["confianza"] == "derivado" for r in rows)
    print(
        f"Generadas {len(rows)} filas: {directas} directas + "
        f"{derivadas} derivadas ({investigadas} referencias trazables) en {OUT}"
    )
    for (pais, categoria), (centro, minimo, maximo) in sorted(factores.items()):
        print(f"  {pais}/{categoria}: factor {centro:.3f} ({minimo:.3f}–{maximo:.3f})")


if __name__ == "__main__":
    main()
