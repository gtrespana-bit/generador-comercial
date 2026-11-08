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
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "basedatos_partidas/datos/recursos.json"
OUT = ROOT / "basedatos_partidas/salida/precios_recursos_espana.csv"
PAISES = (("ES", "EUR"),)
FECHA = "2026-08-25"
FECHA_METODOLOGIA = "2026-08-25"

R_ES = "docs/INVESTIGACION_PRECIOS_ESPANA.md"
METODOLOGIA = "docs/METODOLOGIA_PRECIOS_REFERENCIA_ESPANA.md"
REVISION_MO = "docs/auditoria_precios/ESPANA_REFERENCIA_OPERATIVA_2026.md"
FUENTES_MO = ROOT / "docs/auditoria_precios/espana_mano_obra_provincias_2026.csv"
FECHA_REVISION_MO = "2026-11-06"
REVISION_MATERIALES = "docs/auditoria_precios/ESPANA_MATERIALES_2026.md"
FUENTES_MATERIALES = ROOT / "docs/auditoria_precios/espana_materiales_ofertas_2026.csv"
FECHA_REVISION_MATERIALES = "2026-11-06"
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
                    "Importe histórico por hora; alcance de costes empresariales pendiente de verificación."
                    if directo else
                    "Importe histórico derivado del oficial general; alcance de costes empresariales pendiente de verificación."
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


def referencias_mano_obra_revisadas() -> dict[str, dict[str, Referencia]]:
    """Promedio simple Madrid/Barcelona de escenarios empresariales 2026.

    Retribución de tabla más pensión se usa como aproximación de ambas bases;
    incluye cuotas empresa del 37,35 % y cuota FLC del 0,35 %, sin aplicar
    reducciones. Las 1.736 h son jornada de convenio, no horas productivas.
    El resultado es una referencia derivada, no coste real garantizado.
    """
    with FUENTES_MO.open(encoding="utf-8-sig", newline="") as fh:
        datos = {(r["provincia"], r["categoria_fuente"]): r
                 for r in csv.DictReader(fh, delimiter=";")}
    categorias = {
        "MO-AYU": ("Peón suelto", "Peón ordinario"),
        "MO-AYU-ESP": ("Peón especializado", "Peón especialista"),
        "MO-OF1": ("Oficial primera de oficio", "Oficial primera"),
        "MO-OF1-ALB": ("Oficial primera de oficio", "Oficial primera"),
        "MO-OF1-MON": ("Oficial primera de oficio", "Oficial primera"),
        "MO-OF1-CARPM": ("Oficial primera de oficio", "Oficial primera"),
        "MO-OF1-PISO": ("Oficial primera de oficio", "Oficial primera"),
        "MO-OF1-ALI": ("Oficial primera de oficio", "Oficial primera"),
        "MO-OF1-CAB": ("Oficial primera de oficio", "Oficial primera"),

    }
    centimo = Decimal("0.01")
    salida = {}
    for codigo, nombres in categorias.items():
        importes = []
        for provincia, nombre in zip(("Madrid", "Barcelona"), nombres):
            dato = datos[(provincia, nombre)]
            if dato["ano_tabla"] != "2026" or not dato["pension_empresa_anual_eur"]:
                raise ValueError(f"Fuente incompleta o de otro año: {provincia}/{nombre}")
            salario = Decimal(dato["retribucion_tablas_anual_eur"])
            pension = Decimal(dato["pension_empresa_anual_eur"])
            horas = Decimal(dato["jornada_convenio_horas"])
            if salario <= 0 or pension <= 0 or horas <= 0:
                raise ValueError(f"Fuente inválida: {provincia}/{nombre}")
            importes.append((salario + pension) * Decimal("1.377") / horas)
        redondear = lambda v: v.quantize(centimo, rounding=ROUND_HALF_UP)
        central = redondear(sum(importes) / len(importes))
        minimo, maximo = redondear(min(importes)), redondear(max(importes))
        salida[codigo] = {"ES": ref(
            central, minimo, maximo, REVISION_MO, confianza="derivado",
            incluye_iva="no_aplica", incluye_transporte="no_confirmado",
            observaciones=("Punto medio estimado Madrid/Barcelona 2026: tabla, pensión, "
                "cuotas empresa y FLC bajo convenio de construcción; bases aproximadas y jornada de convenio. "
                "No incluye todos los costes indirectos ni beneficio; consultar metodología."),
        )}
    return salida


REFERENCIAS.update(referencias_mano_obra_revisadas())


def referencias_materiales_revisadas() -> dict[str, dict[str, Referencia]]:
    """Promedio de dos ofertas sin IVA, por unidad física, sin porte.

    Son precios puntuales de productos comparables, no una encuesta nacional.
    No se redondea cada oferta antes de calcular la media.
    """
    agrupadas = {}
    unidades = {"MT-SAC-ESC": "ud", "MT-CEMENTO": "kg", "MT-ADH-C2TE": "kg",
                "MT-PYL-PLACA125": "m2", "MT-PYL-MONT": "m",
                "MT-PYL-CANAL": "m", "MT-JUN-CG2": "kg", "MT-SIL-SAN": "ud",
                "MT-ELECTRODO": "kg", "MT-MORT-REP-EST": "kg",
                "MT-MALLA-OBRA": "m2", "MT-SELLA-ELAST": "l", "MT-MORT-IMPER": "kg",
                "MT-PYL-BANDA": "m", "MT-PYL-PLACA": "m2",
                "MT-PYL-PASTA-AGARRE": "kg", "MT-ELE-TUB20": "m",
                "MT-MALLA-FACH": "m2", "MT-AUT-NIV": "kg"}
    with FUENTES_MATERIALES.open(encoding="utf-8-sig", newline="") as fh:
        for fila in csv.DictReader(fh, delimiter=";"):
            codigo = fila["codigo_recurso"]
            if codigo not in unidades or fila["unidad"] != unidades[codigo]:
                raise ValueError(f"Código o unidad inesperados: {codigo}/{fila['unidad']}")
            precio, cantidad, iva = (Decimal(fila[k]) for k in
                                     ("precio_con_iva_eur", "cantidad_unidades_catalogo", "iva_decimal"))
            if (not all(v.is_finite() for v in (precio, cantidad, iva))
                    or precio <= 0 or cantidad <= 0 or not 0 <= iva <= 1):
                raise ValueError(f"Oferta inválida: {codigo}")
            if fila["fecha_consulta"] != FECHA_REVISION_MATERIALES or not fila["url"]:
                raise ValueError(f"Oferta sin fecha o fuente válida: {codigo}")
            agrupadas.setdefault(codigo, []).append(precio / (1 + iva) / cantidad)
    if set(agrupadas) != set(unidades) or any(len(v) != 2 for v in agrupadas.values()):
        raise ValueError("Se requieren exactamente dos ofertas por material revisado")
    observaciones = {
        "MT-SAC-ESC": "Media de dos ofertas de 10 sacos 50x80 cm; resistencia exacta sin verificar.",
        "MT-CEMENTO": "Media de dos ofertas CEM I 42,5 R; una sulforresistente.",
        "MT-ADH-C2TE": "Media de dos ofertas C2 TE para porcelánico; marcas y color pueden diferir.",
        "MT-PYL-PLACA125": "Media de placas estándar 12,5 mm; Bauhaus la denomina BA 13.",
        "MT-PYL-MONT": "Media de montantes galvanizados de 70 mm; verificar espesor del sistema.",
        "MT-PYL-CANAL": "Media de canales galvanizados de 70 mm; espesores 0,55 y 0,6 mm.",
        "MT-JUN-CG2": "Media de morteros CG2 WA; color y precio final sujetos a confirmación.",
        "MT-SIL-SAN": "Media de cartuchos sanitarios de 300 ml; comprobar compatibilidad del soporte.",
        "MT-ELECTRODO": "Media de E7018 3,2 mm; comprobar procedimiento, homologación y conservación.",
        "MT-MORT-REP-EST": "Media de Morcemseal Todo1 R4; verificar condiciones de aplicación estructural.",
        "MT-MALLA-OBRA": "Media de mallas naranjas 1x50 m; gramaje de una oferta no indicado.",
        "MT-SELLA-ELAST": "Media de Soudaflex 45FC en bolsas de 600 ml; juntas hasta capacidad del producto.",
        "MT-MORT-IMPER": "Media de SikaTop 107 Plus; movimientos de fisura no cubiertos; verificar sistema.",
        "MT-PYL-BANDA": "Media de bandas estancas de polietileno autoadhesivo para perfiles de 70 mm.",
        "MT-PYL-PLACA": "Media de placas estándar Pladur BA 15 mm; confirmar stock y disponibilidad.",
        "MT-PYL-PASTA-AGARRE": "Media de pasta Pladur PA en saco de 20 kg; no usar con aislante adherido.",
        "MT-ELE-TUB20": "Media de tubo PVC corrugado de 20 mm; comprobar reacción al fuego y normativa.",
        "MT-MALLA-FACH": "Media de mallas antiálcalis SATE de 160 g/m2; validar sistema completo.",
        "MT-AUT-NIV": "Media de Niveland 10 para 2 a 10 mm; validar disponibilidad y aplicación.",
    }
    salida = {}
    for codigo, importes in agrupadas.items():
        redondear = lambda v: v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        salida[codigo] = {"ES": ref(
            redondear(sum(importes) / len(importes)), redondear(min(importes)),
            redondear(max(importes)), REVISION_MATERIALES, confianza="derivado",
            incluye_iva="no", incluye_transporte="no",
            observaciones=(observaciones[codigo] + " Sin IVA deducible ni porte; "
                "ofertas puntuales, no media estadística nacional ni coste garantizado."),
        )}
    return salida



# Segundo lote: fotografía independiente; no modifica la fecha de las ofertas anteriores.
REVISION_MATERIALES_07 = "docs/auditoria_precios/ESPANA_MATERIALES_2026-11-07.md"
FUENTES_MATERIALES_07 = ROOT / "docs/auditoria_precios/espana_materiales_ofertas_2026-11-07.csv"
FECHA_MATERIALES_07 = "2026-11-07"


def referencias_materiales_07() -> dict[str, dict[str, Referencia]]:
    unidades = {"MT-CABLE-DATOS": "m", "MT-DESMOLD": "l", "MT-ALAMBRE": "kg"}
    observaciones = {
        "MT-CABLE-DATOS": "Media de dos bobinas Cat6 UTP cobre sólido AWG24 Dca LSZH de 305 m; verificar especificaciones del proyecto.",
        "MT-DESMOLD": "Media de dos ofertas Sika LN 25 l listo al uso; principalmente metálicos, compatible con madera; otras formulaciones pueden costar menos.",
        "MT-ALAMBRE": "Media de dos ofertas del mismo alambre recocido 1,3 mm en bobinas de 1 kg; posible proveedor común, precio minorista no extrapolable a volumen.",
    }
    agrupadas = {}
    proveedores = {}
    with FUENTES_MATERIALES_07.open(encoding="utf-8-sig", newline="") as fh:
        for fila in csv.DictReader(fh, delimiter=";"):
            codigo = fila["codigo_recurso"]
            if codigo not in unidades or fila["unidad"] != unidades[codigo]:
                raise ValueError(f"Código o unidad inesperados: {codigo}/{fila['unidad']}")
            precio, cantidad, iva = (Decimal(fila[k]) for k in
                                     ("precio_con_iva_eur", "cantidad_unidades_catalogo", "iva_decimal"))
            if (not all(v.is_finite() for v in (precio, cantidad, iva))
                    or precio <= 0 or cantidad <= 0 or not 0 <= iva <= 1):
                raise ValueError(f"Oferta inválida: {codigo}")
            if fila["fecha_consulta"] != FECHA_MATERIALES_07 or not fila["url"] or not fila["proveedor"]:
                raise ValueError(f"Oferta sin fecha, proveedor o fuente válida: {codigo}")
            agrupadas.setdefault(codigo, []).append(precio / (1 + iva) / cantidad)
            proveedores.setdefault(codigo, set()).add(fila["proveedor"])
    if set(agrupadas) != set(unidades) or any(len(v) != 2 for v in agrupadas.values()) or any(len(v) != 2 for v in proveedores.values()):
        raise ValueError("Se requieren exactamente dos ofertas de proveedores distintos por material")
    redondear = lambda v: v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return {codigo: {"ES": ref(
        redondear(sum(importes) / 2), redondear(min(importes)), redondear(max(importes)),
        REVISION_MATERIALES_07, confianza="derivado", incluye_iva="no", incluye_transporte="no",
        observaciones=(observaciones[codigo] + " Sin IVA deducible ni porte; ofertas puntuales, no media estadística nacional ni coste garantizado."),
    )} for codigo, importes in agrupadas.items()}



REVISION_LOTE_REGIONAL = "docs/auditoria_precios/ESPANA_LOTE_REGIONAL_2026-11-07.md"
FUENTES_LOTE_REGIONAL = ROOT / "docs/auditoria_precios/espana_fuentes_lote_regional_2026-11-07.csv"


def referencias_lote_regional() -> dict[str, dict[str, Referencia]]:
    unidades = {"MT-AGUA-OBRA": "m3", "MT-MALLA-ELEC": "m2", "MT-CLAVOS": "kg"}
    notas = {
        "MT-AGUA-OBRA": "Agua genérica, media de Palencia y Extremadura. IVA y alcance de suministro no confirmados.",
        "MT-MALLA-ELEC": "Malla nominal 6 mm 15x15; Palencia y oferta minorista, calidad comercial y condiciones fiscales de Palencia no confirmadas; otros diámetros pueden diferir.",
        "MT-CLAVOS": "Clavos planos 20x100 en paquetes de 2,5 kg; no representa necesariamente tornillos ni otras fijaciones incluidas en el recurso.",
    }
    return _referencias_dos_fuentes(FUENTES_LOTE_REGIONAL, unidades, notas, REVISION_LOTE_REGIONAL,
                                    {"MT-CLAVOS"})


REVISION_LOTE_COMERCIAL = "docs/auditoria_precios/ESPANA_LOTE_COMERCIAL_2026-11-07.md"
FUENTES_LOTE_COMERCIAL = ROOT / "docs/auditoria_precios/espana_fuentes_lote_comercial_2026-11-07.csv"


def referencias_lote_comercial() -> dict[str, dict[str, Referencia]]:
    unidades = {"MT-MADERA-LISTON": "m", "MT-PIN-FONDO": "l",
                "MT-SEPARADOR": "ud", "MT-GEOTEXTIL": "m2"}
    notas = {
        "MT-MADERA-LISTON": "Rastreles tratados 40x30 mm, no representa todas las secciones y calidades de listones de obra.",
        "MT-PIN-FONDO": "Fijador acrílico al agua, calidades muy dispersas; disponibilidad de Pintakolor incierta.",
        "MT-SEPARADOR": "Separadores de 25 y 30 mm; uno de mortero, otro universal de material no especificado; no todos los recubrimientos.",
        "MT-GEOTEXTIL": "Geotextil no tejido poliéster 150 g/m2, uno con venta solo en Mallorca; no representa todos los gramajes o prestaciones.",
    }
    return _referencias_dos_fuentes(FUENTES_LOTE_COMERCIAL, unidades, notas, REVISION_LOTE_COMERCIAL,
                                    set(unidades))


REVISION_LOTE_PRIORITARIO = "docs/auditoria_precios/ESPANA_LOTE_PRIORITARIO_2026-11-07.md"
FUENTES_LOTE_PRIORITARIO = ROOT / "docs/auditoria_precios/espana_fuentes_lote_prioritario_2026-11-07.csv"


def referencias_lote_prioritario() -> dict[str, dict[str, Referencia]]:
    unidades = {"MT-PYL-LANA": "m2", "MT-PLO-PPR20": "m",
                "MT-TUB-PPR25": "m", "MT-PIN-CAUCHO": "l"}
    notas = {
        "MT-PYL-LANA": "Panel 60 mm URSA TERRA BASE; una oferta palet y otra paquete con descripción contradictoria sobre revestimiento; contrastar antes de comprar.",
        "MT-PLO-PPR20": "PPR 20x3,4 PN20, solo suministro de tubo; accesorios y termofusión aparte.",
        "MT-TUB-PPR25": "PPR 25x4,2 PN20, solo suministro de tubo; otras presiones, accesorios y termofusión aparte.",
        "MT-PIN-CAUCHO": "Pintura acrílica mate blanca, una referencia sin tintabilidad especificada y otra lavabilidad clase 4; no representa todas las calidades.",
    }
    return _referencias_dos_fuentes(FUENTES_LOTE_PRIORITARIO, unidades, notas, REVISION_LOTE_PRIORITARIO, set(unidades))


REVISION_LOTE_TIENDAS = "docs/auditoria_precios/ESPANA_LOTE_TIENDAS_2026-11-07.md"
FUENTES_LOTE_TIENDAS = ROOT / "docs/auditoria_precios/espana_fuentes_lote_tiendas_2026-11-07.csv"


def referencias_lote_tiendas() -> dict[str, dict[str, Referencia]]:
    unidades = {"MT-PINT-ANTICORR": "l", "MT-POLIESTIRENO-EXT": "m2",
                "MT-BANDA-REF": "m", "MT-CURADOR": "l", "MT-YESO-REP": "kg", "MT-PIN-ESMALTE": "l",
                "MT-PLO-ABASTO": "ud", "MT-POLIUR-LIQ": "kg"}
    notas = {
        "MT-PINT-ANTICORR": "Imprimaciones sintéticas de uso general; distintas formulaciones y colores, compatibilidad con acabado y corrosividad por validar.",
        "MT-POLIESTIRENO-EXT": "XPS 40 mm en paquetes, no representa otros espesores ni resistencias mecánicas.",
        "MT-BANDA-REF": "Bandas de caucho de 130 mm de variantes Mapeband; compatibilidad con el sistema de impermeabilización por validar.",
        "MT-CURADOR": "Antisol 3E en envase de 25 kg; volumen estimado usando densidad nominal 0,975 kg/l, sujeta a tolerancia.",
        "MT-YESO-REP": "Yeso rápido manual para rozas, no representa morteros alternativos ni yesos especiales.",
        "MT-PIN-ESMALTE": "Esmaltes sintéticos blancos brillantes de dos calidades; confirmar preparación e imprimación del soporte.",
        "MT-PLO-ABASTO": "Latiguillo 40 cm M-H 3/8 con racores; no representa todas las conexiones, longitudes ni accesorios adicionales.",
        "MT-POLIUR-LIQ": "Membranas monocomponentes de 25 kg; propiedades de sistema, imprimación y resistencia a tránsito por verificar.",
    }
    return _referencias_dos_fuentes(FUENTES_LOTE_TIENDAS, unidades, notas, REVISION_LOTE_TIENDAS, set(unidades) - {"MT-PINT-ANTICORR", "MT-PLO-ABASTO", "MT-POLIUR-LIQ"})


REVISION_LOTE_POSTERIOR = "docs/auditoria_precios/ESPANA_LOTE_POSTERIOR_2026-11-07.md"
FUENTES_LOTE_POSTERIOR = ROOT / "docs/auditoria_precios/espana_fuentes_lote_posterior_2026-11-07.csv"


def referencias_lote_posterior():
    # La rutina de dos fuentes se aplica a un fichero parcial temporal en memoria
    # conceptualmente: cada grupo incluye dos ofertas, incluso los componentes.
    unidades = {"MT-CABLE-ALARMA": "m", "MT-TORN-TECHO": "ud", "PASTA": "kg", "CINTA": "m"}
    notas = {k: "Oferta puntual para el lote posterior." for k in unidades}
    grupos = _referencias_dos_fuentes(FUENTES_LOTE_POSTERIOR, unidades, notas, REVISION_LOTE_POSTERIOR, set())
    # No usar los valores redondeados de Referencia: calcular desde importes originales.
    componentes = {}
    with FUENTES_LOTE_POSTERIOR.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f, delimiter=";"):
            if row["codigo_recurso"] in {"PASTA", "CINTA"}:
                valor = Decimal(row["importe_eur"]) / Decimal(row["cantidad"]) / (1 + Decimal(row["iva_decimal"]))
                componentes.setdefault(row["codigo_recurso"], []).append(valor)
    pasta, cinta = componentes["PASTA"], componentes["CINTA"]
    ratio = Decimal("1.30") / Decimal("0.34")
    q = lambda x: x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    precio = q(sum(pasta) / 2 + ratio * sum(cinta) / 2)
    minimo, maximo = q(min(pasta) + ratio * min(cinta)), q(max(pasta) + ratio * max(cinta))
    grupos["MT-PYL-PASTA"] = {"ES": ref(precio, minimo, maximo, REVISION_LOTE_POSTERIOR,
        confianza="derivado", incluye_iva="no", incluye_transporte="no_confirmado",
        observaciones="Pasta y cinta: hipótesis 1,30 m de cinta por 0,34 kg de pasta, dependiente del sistema; sin mermas ni mano de obra. Provisional, no media nacional.")}
    del grupos["PASTA"], grupos["CINTA"]
    # Ambas ofertas incluyen IVA, pero sus portes no están confirmados.
    for codigo, nota in {
        "MT-CABLE-ALARMA": "Cable apantallado 4x0,22+2x0,75; trenzado en pares no acreditado y plazo por confirmar.",
        "MT-TORN-TECHO": "Tornillos cincados con EPDM, 63 y 35 mm: medidas y precio por volumen distintos; verificar fijación para la cubierta.",
    }.items():
        dato = grupos[codigo]["ES"]
        grupos[codigo] = {"ES": ref(dato.precio, dato.minimo, dato.maximo, REVISION_LOTE_POSTERIOR,
            confianza="derivado", incluye_iva="no", incluye_transporte="no_confirmado",
            observaciones=nota + " Estimación provisional, no media nacional ni precio garantizado.")}
    return grupos


def _referencias_dos_fuentes(archivo, unidades, notas, revision, condiciones_conocidas):
    grupos, fuentes = {}, {}
    with archivo.open(encoding="utf-8-sig", newline="") as fh:
        for fila in csv.DictReader(fh, delimiter=";"):
            codigo = fila["codigo_recurso"]
            if codigo not in unidades or fila["unidad"] != unidades[codigo]:
                raise ValueError(f"Código o unidad inesperados: {codigo}")
            importe, cantidad = Decimal(fila["importe_eur"]), Decimal(fila["cantidad"])
            iva = Decimal(fila["iva_decimal"]) if fila["iva_decimal"] else None
            if (not importe.is_finite() or not cantidad.is_finite() or importe <= 0 or cantidad <= 0
                    or (iva is not None and (not iva.is_finite() or not 0 <= iva <= 1))
                    or not fila["fuente"] or not fila["url"] or fila["fecha_consulta"] != "2026-11-07"):
                raise ValueError(f"Fuente inválida: {codigo}")
            grupos.setdefault(codigo, []).append(importe / cantidad / (1 + iva if iva is not None else 1))
            fuentes.setdefault(codigo, set()).add(fila["fuente"])
    if set(grupos) != set(unidades) or any(len(v) != 2 for v in grupos.values()) or any(len(v) != 2 for v in fuentes.values()):
        raise ValueError("Se requieren exactamente dos fuentes distintas por recurso")
    def redondear(n):
        return n.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return {codigo: {"ES": ref(
        redondear(sum(valores) / 2), redondear(min(valores)), redondear(max(valores)),
        revision, confianza="derivado",
        incluye_iva="no" if codigo in condiciones_conocidas else "no_confirmado",
        incluye_transporte="no" if codigo in condiciones_conocidas else "no_confirmado",
        observaciones=notas[codigo] + " Estimación provisional, no media estadística nacional ni precio garantizado."
    )} for codigo, valores in grupos.items()}

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


REVISION_LOTE_BANCO = "docs/auditoria_precios/ESPANA_LOTE_BANCO_2026-11-07.md"
FUENTES_LOTE_BANCO = ROOT / "docs/auditoria_precios/espana_fuentes_lote_banco_2026-11-07.csv"


def referencias_lote_banco() -> dict[str, dict[str, Referencia]]:
    """Referencias provisionales individuales, sin fingir rango de mercado."""
    esperados = {"MT-ACERO-CAB", "MT-ELE-CABLE", "MT-CABLE-8", "MT-ELE-MECA", "MT-BREAKER", "MT-REJILLA-VENT", "MT-PLACA-CEM", "MT-PROT-OBRA", "MT-PROT-PLAST", "MT-PROT-CARTON"}
    resultado = {}
    catalogo = json.loads(SRC.read_text(encoding="utf-8"))
    unidades = {codigo: item.get("unidad", "ud") for codigo, _, item in iter_recursos(catalogo)}
    with FUENTES_LOTE_BANCO.open(encoding="utf-8-sig", newline="") as f:
        for fila in csv.DictReader(f, delimiter=";"):
            codigo = fila["codigo_recurso"]
            if codigo not in esperados or codigo in resultado or fila["unidad"] != unidades.get(codigo) or not fila["url"] or not fila["codigo_fuente"] or not fila["alcance_y_reservas"] or fila["fecha_consulta"] != "2026-11-07":
                raise ValueError(f"Fuente inválida o duplicada: {codigo}")
            precio = Decimal(fila["precio_eur"])
            if not precio.is_finite() or precio <= 0:
                raise ValueError(f"Precio inválido: {codigo}")
            resultado[codigo] = {"ES": ref(precio, precio, precio, REVISION_LOTE_BANCO, confianza="derivado", incluye_iva="no_confirmado", incluye_transporte="no_confirmado", observaciones="Estimación provisional de una sola descomposición; extremos iguales no son rango de mercado. " + fila["alcance_y_reservas"])}
    if set(resultado) != esperados:
        raise ValueError("Lote de banco incompleto")
    return resultado


REVISION_LOTE_CUADROS = "docs/auditoria_precios/ESPANA_LOTE_CUADROS_2026-11-07.md"
FUENTES_LOTE_CUADROS = ROOT / "docs/auditoria_precios/espana_fuentes_cuadros_2026-11-07.csv"


def referencias_lote_cuadros() -> dict[str, dict[str, Referencia]]:
    """Básicos provinciales/regionales: valor individual, no rango ni media nacional."""
    esperados = {"MT-MANTO-ASF", "MT-LANA-ROCA", "MT-TIERRA-ABON", "MT-AISL-TERM", "MT-LAMINA-OSB", "MT-LAMINA-DREN", "MT-VIGUETA", "MT-MALLA-DREN"}
    catalogo = json.loads(SRC.read_text(encoding="utf-8"))
    unidades = {codigo: item.get("unidad", "ud") for codigo, _, item in iter_recursos(catalogo)}
    resultado = {}
    with FUENTES_LOTE_CUADROS.open(encoding="utf-8-sig", newline="") as f:
        for fila in csv.DictReader(f, delimiter=";"):
            codigo = fila["codigo_recurso"]
            if codigo not in esperados or codigo in resultado or fila["unidad"] != unidades.get(codigo) or not fila["url"] or not fila["codigo_fuente"] or not fila["alcance_y_reservas"] or fila["ambito"] not in {"Palencia", "Extremadura"} or fila["fecha_consulta"] != "2026-11-07":
                raise ValueError(f"Fuente inválida o duplicada: {codigo}")
            precio = Decimal(fila["precio_eur"])
            if not precio.is_finite() or precio <= 0:
                raise ValueError(f"Precio inválido: {codigo}")
            resultado[codigo] = {"ES": ref(precio, precio, precio, REVISION_LOTE_CUADROS, confianza="derivado", incluye_iva="no_confirmado", incluye_transporte="no_confirmado", observaciones="Estimación provisional de un cuadro de " + fila["ambito"] + "; extremos iguales no son rango de mercado. " + fila["alcance_y_reservas"])}
    if set(resultado) != esperados:
        raise ValueError("Lote de cuadros incompleto")
    return resultado


REVISION_LOTE_MATERIALES = "docs/auditoria_precios/ESPANA_LOTE_MATERIALES_2026-11-07.md"
FUENTES_LOTE_MATERIALES = ROOT / "docs/auditoria_precios/espana_fuentes_lote_materiales_2026-11-07.csv"


def referencias_lote_materiales() -> dict[str, dict[str, Referencia]]:
    """Básicos individuales: procedencia verificable, no media nacional."""
    esperados = {'MT-ADH-C1', 'MT-LADRILLO', 'MT-ADH-VINIL', 'MT-PERFIL-TRANS', 'MT-PYL-PLACA-RH', 'MT-PYL-PLACA-IG', 'MT-LAMINA-ZINC'}
    catalogo = json.loads(SRC.read_text(encoding="utf-8"))
    unidades = {codigo: item.get("unidad", "ud") for codigo, _, item in iter_recursos(catalogo)}
    resultado = {}
    with FUENTES_LOTE_MATERIALES.open(encoding="utf-8-sig", newline="") as f:
        for fila in csv.DictReader(f, delimiter=";"):
            codigo = fila["codigo_recurso"]
            if (codigo not in esperados or codigo in resultado or fila["unidad"] != unidades.get(codigo)
                or not fila["url"] or not fila["codigo_fuente"] or not fila["alcance_y_reservas"]
                or fila["ambito"] not in {"Extremadura", "CYPE España"} or fila["fecha_consulta"] != "2026-11-07"):
                raise ValueError(f"Fuente inválida o duplicada: {codigo}")
            precio = Decimal(fila["precio_eur"])
            if not precio.is_finite() or precio <= 0:
                raise ValueError(f"Precio inválido: {codigo}")
            resultado[codigo] = {"ES": ref(precio, precio, precio, REVISION_LOTE_MATERIALES, confianza="derivado", incluye_iva="no_confirmado", incluye_transporte="no_confirmado", observaciones="Estimación provisional individual; extremos iguales no son rango de mercado. " + fila["alcance_y_reservas"])}
    if set(resultado) != esperados:
        raise ValueError("Lote de materiales incompleto")
    return resultado


REVISION_LOTE_CADENAS = "docs/auditoria_precios/ESPANA_LOTE_CADENAS_2026-11-07.md"
FUENTES_LOTE_CADENAS = ROOT / "docs/auditoria_precios/espana_fuentes_cadenas_2026-11-07.csv"


def referencias_lote_cadenas() -> dict[str, dict[str, Referencia]]:
    """Normaliza ofertas minoristas sin extrapolarlas a media nacional."""
    esperados = {'MT-SILICONA-EST': 1, 'MT-PIN-MASILLA': 2, 'MT-LASUR': 1, 'MT-DECAP': 1, 'MT-PRESERV-MAD': 1, 'MT-PINT-TRAFICO': 1, 'MT-ESMALTE-AGUA': 1, 'MT-PIN-TIZA': 1, 'MT-SELLA-PIEDRA': 1, 'MT-BLQ-10': 1, 'MT-BLQ-15': 1, 'MT-BLQ-20': 1, 'MT-PYL-PLACA-HD': 1, 'MT-MOSQUITERO': 1, 'MT-ASPERSOR': 1, 'MT-DETECT-HUMO': 1, 'MT-ESPEJO': 1, 'MT-PERFIL-REMATE': 1, 'MT-BARNIZ-PISO': 1, 'MT-PIN-ANTIMOHO': 1}
    catalogo = json.loads(SRC.read_text(encoding="utf-8"))
    unidades = {codigo: item.get("unidad", "ud") for codigo, _, item in iter_recursos(catalogo)}
    agrupados = {}
    with FUENTES_LOTE_CADENAS.open(encoding="utf-8-sig", newline="") as f:
        for fila in csv.DictReader(f, delimiter=";"):
            codigo = fila["codigo_recurso"]
            if (codigo not in esperados or fila["unidad"] != unidades.get(codigo) or not fila["url"]
                    or not fila["producto"] or not fila["reserva"] or fila["vendedor"] not in {"Obramat", "Leroy Merlin"}
                    or not fila["vendedor_identificado"] or fila["criterio_iva"] not in {"IVA 21% supuesto sobre PVP", "neto de ficha Obramat"}
                    or fila["fecha_consulta"] != "2026-11-07"):
                raise ValueError(f"Fuente de cadenas inválida: {codigo}")
            precio, cantidad = Decimal(fila["importe_envase_sin_impuestos"]), Decimal(fila["cantidad_recurso"])
            pvp = Decimal(fila["precio_envase_iva"])
            if not pvp.is_finite() or pvp <= 0 or not precio.is_finite() or not cantidad.is_finite() or precio <= 0 or cantidad <= 0:
                raise ValueError(f"Precio o cantidad inválidos: {codigo}")
            if fila["criterio_iva"] == "IVA 21% supuesto sobre PVP" and abs(precio - pvp / Decimal("1.21")) > Decimal("0.000001"):
                raise ValueError(f"IVA supuesto incoherente: {codigo}")
            normalizado = (precio / cantidad).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if normalizado != Decimal(fila["precio_normalizado"]):
                raise ValueError(f"Normalización incoherente: {codigo}")
            agrupados.setdefault(codigo, []).append(fila)
    if {k: len(v) for k, v in agrupados.items()} != esperados:
        raise ValueError("Lote de cadenas incompleto o duplicado")
    resultado = {}
    for codigo, filas in agrupados.items():
        urls = {f["url"] for f in filas}
        if len(urls) != len(filas):
            raise ValueError(f"Fuente duplicada: {codigo}")
        precio = (sum(Decimal(f["precio_normalizado"]) for f in filas) / len(filas)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        notas = " ".join(f["reserva"] for f in filas)
        resultado[codigo] = {"ES": ref(precio, precio, precio, REVISION_LOTE_CADENAS, confianza="derivado", incluye_iva="no", incluye_transporte="no_confirmado", observaciones="Estimación provisional minorista; no es media nacional ni rango de mercado. " + notas)}
    return resultado


REVISION_LOTE_PRIORIDAD = "docs/auditoria_precios/ESPANA_LOTE_PRIORIDAD_2026-11-07.md"
FUENTES_LOTE_PRIORIDAD = ROOT / "docs/auditoria_precios/espana_fuentes_prioridad_2026-11-07.csv"


def referencias_lote_prioridad() -> dict[str, dict[str, Referencia]]:
    """Suma componentes de ofertas puntuales sin confundirlos con una media."""
    esperados = {
        'MT-PERNO-ANCLA': 2, 'MT-PERFIL-ACERO': 1, 'MT-PUENTE-ADH': 1,
        'MT-CINTA-ENM': 2, 'MT-MANTA-ACUS': 1, 'MT-HIDROFUGO': 1,
        'MT-SILOXANO': 1, 'MT-HIDROFUG-FACH': 1, 'MT-LIMP-QUIM': 1,
        'MT-IMPRIM-ASF': 1, 'MT-CIELO-DESM': 1, 'MT-LACA-MADERA': 1,
        'MT-BARNIZ-MARINO': 1, 'MT-PEGA-MURAL': 1, 'MT-TINTE-MAD': 1,
        'MT-CERRADURA-MULTI': 1, 'MT-PIN-MAGNETICA': 1, 'MT-SELLA-CONC': 1,
    }
    catalogo = json.loads(SRC.read_text(encoding="utf-8"))
    unidades = {codigo: item.get("unidad", "ud") for codigo, _, item in iter_recursos(catalogo)}
    grupos = {}
    with FUENTES_LOTE_PRIORIDAD.open(encoding="utf-8-sig", newline="") as f:
        for fila in csv.DictReader(f, delimiter=";"):
            codigo = fila['codigo_recurso']
            criterio = fila['criterio_iva']
            if (codigo not in esperados or fila['unidad'] != unidades.get(codigo)
                    or not all(fila[k] for k in ('producto', 'fuente', 'url', 'url_precio', 'reserva'))
                    or not fila['url'].startswith(('https://', 'http://'))
                    or not fila['url_precio'].startswith(('https://', 'http://'))
                    or (codigo in {'MT-PUENTE-ADH', 'MT-HIDROFUGO', 'MT-SILOXANO', 'MT-HIDROFUG-FACH'}
                        and not fila['url_tecnica'].startswith(('https://', 'http://')))
                    or fila['fecha_consulta'] != '2026-11-07'
                    or criterio not in {'neto de ficha Obramat', 'IVA 21% supuesto', 'IVA no confirmado'}
                    or (criterio == 'neto de ficha Obramat' and fila['fuente'] != 'Obramat')
                    or (criterio == 'IVA no confirmado' and fila['fuente'] != 'CYPE')):
                raise ValueError(f"Fuente de prioridad inválida: {codigo}")
            base, divisor, cantidad = (Decimal(fila[k]) for k in ('importe_base', 'cantidad_por_envase', 'cantidad_por_recurso'))
            if any(not x.is_finite() or x <= 0 for x in (base, divisor, cantidad)):
                raise ValueError(f"Precio o cantidad inválidos: {codigo}")
            if criterio == 'IVA no confirmado':
                if fila['precio_bruto']:
                    raise ValueError(f"IVA no confirmado incompatible con PVP: {codigo}")
            else:
                bruto = Decimal(fila['precio_bruto'])
                if not bruto.is_finite() or bruto <= 0:
                    raise ValueError(f"PVP inválido: {codigo}")
                tolerancia = Decimal('0.000001') if criterio == 'IVA 21% supuesto' else Decimal('0.01')
                if abs(base - bruto / Decimal('1.21')) > tolerancia:
                    raise ValueError(f"IVA incoherente: {codigo}")
            grupos.setdefault(codigo, []).append(fila)
    if {k: len(v) for k, v in grupos.items()} != esperados:
        raise ValueError("Lote de prioridad incompleto o duplicado")
    resultado = {}
    for codigo, filas in grupos.items():
        if len({f['producto'] for f in filas}) != len(filas):
            raise ValueError(f"Componente duplicado: {codigo}")
        precio = sum(Decimal(f['importe_base']) / Decimal(f['cantidad_por_envase']) * Decimal(f['cantidad_por_recurso']) for f in filas).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        if any(Decimal(f['precio_resultante']) != precio for f in filas):
            raise ValueError(f"Normalización incoherente: {codigo}")
        iva = 'por_verificar' if any(f['criterio_iva'] == 'IVA no confirmado' for f in filas) else 'no'
        reservas = ' '.join(dict.fromkeys(f['reserva'] for f in filas))
        resultado[codigo] = {'ES': ref(precio, precio, precio, REVISION_LOTE_PRIORIDAD,
            confianza='derivado', incluye_iva=iva, incluye_transporte='no_confirmado',
            observaciones='Estimación provisional puntual; no es media nacional ni rango de mercado. ' + reservas)}
    return resultado


REVISION_LOTE_ALTA_FRECUENCIA = "docs/auditoria_precios/ESPANA_LOTE_ALTA_FRECUENCIA_2026-11-07.md"
FUENTES_LOTE_ALTA_FRECUENCIA = ROOT / "docs/auditoria_precios/espana_fuentes_alta_frecuencia_2026-11-07.csv"


def referencias_lote_alta_frecuencia() -> dict[str, dict[str, Referencia]]:
    """Suma componentes de ofertas puntuales sin confundirlos con una media."""
    esperados = {'MT-PLO-SOP': 1, 'MT-TUB-FRIGO': 2, 'MT-FLOTANTE': 2, 'MT-MACHIH-MAD': 1, 'MT-MELAMINA': 1}
    catalogo = json.loads(SRC.read_text(encoding="utf-8"))
    unidades = {codigo: item.get("unidad", "ud") for codigo, _, item in iter_recursos(catalogo)}
    grupos = {}
    with FUENTES_LOTE_ALTA_FRECUENCIA.open(encoding="utf-8-sig", newline="") as f:
        for fila in csv.DictReader(f, delimiter=";"):
            codigo = fila['codigo_recurso']
            criterio = fila['criterio_iva']
            if (codigo not in esperados or fila['unidad'] != unidades.get(codigo)
                    or not all(fila[k] for k in ('producto', 'fuente', 'url', 'url_precio', 'reserva'))
                    or not fila['url'].startswith(('https://', 'http://'))
                    or not fila['url_precio'].startswith(('https://', 'http://'))
                    or fila['fecha_consulta'] != '2026-11-07'
                    or criterio not in {'neto de ficha Obramat', 'IVA 21% supuesto', 'IVA no confirmado'}
                    or (criterio == 'neto de ficha Obramat' and fila['fuente'] != 'Obramat')
                    or (criterio == 'IVA no confirmado' and fila['fuente'] != 'CYPE')):
                raise ValueError(f"Fuente de alta frecuencia inválida: {codigo}")
            base, divisor, cantidad = (Decimal(fila[k]) for k in ('importe_base', 'cantidad_por_envase', 'cantidad_por_recurso'))
            if any(not x.is_finite() or x <= 0 for x in (base, divisor, cantidad)):
                raise ValueError(f"Precio o cantidad inválidos: {codigo}")
            if criterio == 'IVA no confirmado':
                if fila['precio_bruto']:
                    raise ValueError(f"IVA no confirmado incompatible con PVP: {codigo}")
            else:
                bruto = Decimal(fila['precio_bruto'])
                if not bruto.is_finite() or bruto <= 0:
                    raise ValueError(f"PVP inválido: {codigo}")
                tolerancia = Decimal('0.000001') if criterio == 'IVA 21% supuesto' else Decimal('0.01')
                if abs(base - bruto / Decimal('1.21')) > tolerancia:
                    raise ValueError(f"IVA incoherente: {codigo}")
            grupos.setdefault(codigo, []).append(fila)
    if {k: len(v) for k, v in grupos.items()} != esperados:
        raise ValueError("Lote de alta frecuencia incompleto o duplicado")
    resultado = {}
    for codigo, filas in grupos.items():
        if len({f['producto'] for f in filas}) != len(filas):
            raise ValueError(f"Componente duplicado: {codigo}")
        precio = sum(Decimal(f['importe_base']) / Decimal(f['cantidad_por_envase']) * Decimal(f['cantidad_por_recurso']) for f in filas).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        if any(Decimal(f['precio_resultante']) != precio for f in filas):
            raise ValueError(f"Normalización incoherente: {codigo}")
        iva = 'por_verificar' if any(f['criterio_iva'] == 'IVA no confirmado' for f in filas) else 'no'
        reservas = ' '.join(dict.fromkeys(f['reserva'] for f in filas))
        resultado[codigo] = {'ES': ref(precio, precio, precio, REVISION_LOTE_ALTA_FRECUENCIA,
            confianza='derivado', incluye_iva=iva, incluye_transporte='no_confirmado',
            observaciones='Estimación provisional puntual; no es media nacional ni rango de mercado. ' + reservas)}
    return resultado


REVISION_LOTE_FAMILIAS = "docs/auditoria_precios/ESPANA_LOTE_FAMILIAS_2026-11-07.md"
FUENTES_LOTE_FAMILIAS = ROOT / "docs/auditoria_precios/espana_fuentes_familias_2026-11-07.csv"


def referencias_lote_familias() -> dict[str, dict[str, Referencia]]:
    """Suma componentes de ofertas puntuales sin confundirlos con una media."""
    esperados = {'MT-IMP-PRIM': 1, 'MT-GRANO-MARMOL': 1, 'MT-MANGUERA': 1, 'MT-CINTA-ANTIDES': 1, 'MT-CANAL-DREN': 1, 'MT-TEJA-CRIOLLA': 1, 'MT-REGISTRO': 1, 'MT-CIERRA-PUERTA': 1, 'MT-SELLA-FISURA': 1, 'MT-REFUERZO-PYL': 1, 'MT-PANEL-SAND': 1, 'MT-MEMBRANA-PVC': 1, 'MT-GROUT': 1, 'MT-ADH-MADERA': 1, 'MT-SELLA-BENTONITA': 1, 'MT-CONECTOR-CORTE': 1, 'MT-VIDRIO-LAM': 1, 'MT-VIDRIO-DOBLE': 1, 'MT-DUCTO-VENT': 1, 'MT-TUB-GAS': 1, 'MT-VALV-CHECK': 2, 'MT-DPS-1': 1, 'MT-DPS-2': 1, 'MT-DIFERENCIAL': 1, 'MT-ANTI-GRAFFITI': 1, 'MT-DESMOLD-COLOR': 1, 'MT-FUNGICIDA': 1, 'MT-PLOT-REG': 1}
    catalogo = json.loads(SRC.read_text(encoding="utf-8"))
    unidades = {codigo: item.get("unidad", "ud") for codigo, _, item in iter_recursos(catalogo)}
    grupos = {}
    with FUENTES_LOTE_FAMILIAS.open(encoding="utf-8-sig", newline="") as f:
        for fila in csv.DictReader(f, delimiter=";"):
            codigo = fila['codigo_recurso']
            criterio = fila['criterio_iva']
            if (codigo not in esperados or fila['unidad'] != unidades.get(codigo)
                    or not all(fila[k] for k in ('producto', 'fuente', 'url', 'url_precio', 'reserva'))
                    or not fila['url'].startswith(('https://', 'http://'))
                    or not fila['url_precio'].startswith(('https://', 'http://'))
                    or fila['fecha_consulta'] != '2026-11-07'
                    or criterio not in {'neto de ficha Obramat', 'IVA 21% supuesto', 'IVA no confirmado'}
                    or (criterio == 'neto de ficha Obramat' and fila['fuente'] != 'Obramat')
                    or (criterio == 'IVA no confirmado' and fila['fuente'] != 'CYPE')):
                raise ValueError(f"Fuente de familias inválida: {codigo}")
            base, divisor, cantidad = (Decimal(fila[k]) for k in ('importe_base', 'cantidad_por_envase', 'cantidad_por_recurso'))
            if any(not x.is_finite() or x <= 0 for x in (base, divisor, cantidad)):
                raise ValueError(f"Precio o cantidad inválidos: {codigo}")
            if criterio == 'IVA no confirmado':
                if fila['precio_bruto']:
                    raise ValueError(f"IVA no confirmado incompatible con PVP: {codigo}")
            else:
                bruto = Decimal(fila['precio_bruto'])
                if not bruto.is_finite() or bruto <= 0:
                    raise ValueError(f"PVP inválido: {codigo}")
                tolerancia = Decimal('0.000001') if criterio == 'IVA 21% supuesto' else Decimal('0.01')
                if abs(base - bruto / Decimal('1.21')) > tolerancia:
                    raise ValueError(f"IVA incoherente: {codigo}")
            grupos.setdefault(codigo, []).append(fila)
    if {k: len(v) for k, v in grupos.items()} != esperados:
        raise ValueError("Lote de familias incompleto o duplicado")
    resultado = {}
    for codigo, filas in grupos.items():
        if len({f['producto'] for f in filas}) != len(filas):
            raise ValueError(f"Componente duplicado: {codigo}")
        precio = sum(Decimal(f['importe_base']) / Decimal(f['cantidad_por_envase']) * Decimal(f['cantidad_por_recurso']) for f in filas).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        if any(Decimal(f['precio_resultante']) != precio for f in filas):
            raise ValueError(f"Normalización incoherente: {codigo}")
        iva = 'por_verificar' if any(f['criterio_iva'] == 'IVA no confirmado' for f in filas) else 'no'
        reservas = ' '.join(dict.fromkeys(f['reserva'] for f in filas))
        resultado[codigo] = {'ES': ref(precio, precio, precio, REVISION_LOTE_FAMILIAS,
            confianza='derivado', incluye_iva=iva, incluye_transporte='no_confirmado',
            observaciones='Estimación provisional puntual; no es media nacional ni rango de mercado. ' + reservas)}
    return resultado



REVISION_LOTE_COMPONENTES = "docs/auditoria_precios/ESPANA_LOTE_COMPONENTES_2026-11-07.md"
FUENTES_LOTE_COMPONENTES = ROOT / "docs/auditoria_precios/espana_fuentes_componentes_2026-11-07.csv"


def referencias_lote_componentes() -> dict[str, dict[str, Referencia]]:
    """Suma componentes de ofertas puntuales sin confundirlos con una media."""
    esperados = {'MT-PYL-PERF-CR': 9, 'MT-MALLA-JUNTA': 1, 'MT-ELE-PROV': 1, 'MT-DINTEL-PREF': 1, 'MT-POLICARB': 2, 'MT-ESTUCO-FINO': 1, 'MT-BAJANTE-PVC': 3, 'MT-PER-BANDA': 1}
    catalogo = json.loads(SRC.read_text(encoding="utf-8"))
    unidades = {codigo: item.get("unidad", "ud") for codigo, _, item in iter_recursos(catalogo)}
    grupos = {}
    with FUENTES_LOTE_COMPONENTES.open(encoding="utf-8-sig", newline="") as f:
        for fila in csv.DictReader(f, delimiter=";"):
            codigo = fila['codigo_recurso']
            criterio = fila['criterio_iva']
            if (codigo not in esperados or fila['unidad'] != unidades.get(codigo)
                    or not all(fila[k] for k in ('producto', 'fuente', 'url', 'url_precio', 'reserva'))
                    or not fila['url'].startswith(('https://', 'http://'))
                    or not fila['url_precio'].startswith(('https://', 'http://'))
                    or fila['fecha_consulta'] != '2026-11-07'
                    or criterio not in {'neto de ficha Obramat', 'IVA 21% supuesto', 'IVA no confirmado'}
                    or (criterio == 'neto de ficha Obramat' and fila['fuente'] != 'Obramat')
                    or (criterio == 'IVA no confirmado' and fila['fuente'] != 'CYPE')):
                raise ValueError(f"Fuente de componentes inválida: {codigo}")
            base, divisor, cantidad = (Decimal(fila[k]) for k in ('importe_base', 'cantidad_por_envase', 'cantidad_por_recurso'))
            if any(not x.is_finite() or x <= 0 for x in (base, divisor, cantidad)):
                raise ValueError(f"Precio o cantidad inválidos: {codigo}")
            if criterio == 'IVA no confirmado':
                if fila['precio_bruto']:
                    raise ValueError(f"IVA no confirmado incompatible con PVP: {codigo}")
            else:
                bruto = Decimal(fila['precio_bruto'])
                if not bruto.is_finite() or bruto <= 0:
                    raise ValueError(f"PVP inválido: {codigo}")
                tolerancia = Decimal('0.000001') if criterio == 'IVA 21% supuesto' else Decimal('0.01')
                if abs(base - bruto / Decimal('1.21')) > tolerancia:
                    raise ValueError(f"IVA incoherente: {codigo}")
            grupos.setdefault(codigo, []).append(fila)
    if {k: len(v) for k, v in grupos.items()} != esperados:
        raise ValueError("Lote de componentes incompleto o duplicado")
    resultado = {}
    for codigo, filas in grupos.items():
        if len({f['producto'] for f in filas}) != len(filas):
            raise ValueError(f"Componente duplicado: {codigo}")
        precio = sum(Decimal(f['importe_base']) / Decimal(f['cantidad_por_envase']) * Decimal(f['cantidad_por_recurso']) for f in filas).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        if any(Decimal(f['precio_resultante']) != precio for f in filas):
            raise ValueError(f"Normalización incoherente: {codigo}")
        iva = 'por_verificar' if any(f['criterio_iva'] == 'IVA no confirmado' for f in filas) else 'no'
        reservas = ' '.join(dict.fromkeys(f['reserva'] for f in filas))
        resultado[codigo] = {'ES': ref(precio, precio, precio, REVISION_LOTE_COMPONENTES,
            confianza='derivado', incluye_iva=iva, incluye_transporte='no_confirmado',
            observaciones='Estimación provisional puntual; no es media nacional ni rango de mercado. ' + reservas)}
    return resultado



REVISION_LOTE_SISTEMAS = "docs/auditoria_precios/ESPANA_LOTE_SISTEMAS_2026-11-07.md"
FUENTES_LOTE_SISTEMAS = ROOT / "docs/auditoria_precios/espana_fuentes_sistemas_2026-11-07.csv"


def referencias_lote_sistemas() -> dict[str, dict[str, Referencia]]:
    """Suma componentes de ofertas puntuales sin confundirlos con una media."""
    esperados = {'MT-PERF-DESM': 9, 'MT-MADERA-EST': 1, 'MT-FIBRA-CARB': 2, 'MT-CAJON-PERS': 3, 'MT-BENTONITA': 1, 'MT-PASTA-YESO': 1, 'MT-ADITIVO': 1}
    catalogo = json.loads(SRC.read_text(encoding="utf-8"))
    unidades = {codigo: item.get("unidad", "ud") for codigo, _, item in iter_recursos(catalogo)}
    grupos = {}
    with FUENTES_LOTE_SISTEMAS.open(encoding="utf-8-sig", newline="") as f:
        for fila in csv.DictReader(f, delimiter=";"):
            codigo = fila['codigo_recurso']
            criterio = fila['criterio_iva']
            if (codigo not in esperados or fila['unidad'] != unidades.get(codigo)
                    or not all(fila[k] for k in ('producto', 'fuente', 'url', 'url_precio', 'reserva'))
                    or not fila['url'].startswith(('https://', 'http://'))
                    or not fila['url_precio'].startswith(('https://', 'http://'))
                    or fila['fecha_consulta'] != '2026-11-07'
                    or criterio not in {'neto de ficha Obramat', 'IVA 21% supuesto', 'IVA no confirmado'}
                    or (criterio == 'neto de ficha Obramat' and fila['fuente'] != 'Obramat')
                    or (criterio == 'IVA no confirmado' and fila['fuente'] != 'CYPE')):
                raise ValueError(f"Fuente de sistemas inválida: {codigo}")
            base, divisor, cantidad = (Decimal(fila[k]) for k in ('importe_base', 'cantidad_por_envase', 'cantidad_por_recurso'))
            if any(not x.is_finite() or x <= 0 for x in (base, divisor, cantidad)):
                raise ValueError(f"Precio o cantidad inválidos: {codigo}")
            if criterio == 'IVA no confirmado':
                if fila['precio_bruto']:
                    raise ValueError(f"IVA no confirmado incompatible con PVP: {codigo}")
            else:
                bruto = Decimal(fila['precio_bruto'])
                if not bruto.is_finite() or bruto <= 0:
                    raise ValueError(f"PVP inválido: {codigo}")
                tolerancia = Decimal('0.000001') if criterio == 'IVA 21% supuesto' else Decimal('0.01')
                if abs(base - bruto / Decimal('1.21')) > tolerancia:
                    raise ValueError(f"IVA incoherente: {codigo}")
            grupos.setdefault(codigo, []).append(fila)
    if {k: len(v) for k, v in grupos.items()} != esperados:
        raise ValueError("Lote de sistemas incompleto o duplicado")
    resultado = {}
    for codigo, filas in grupos.items():
        if len({f['producto'] for f in filas}) != len(filas):
            raise ValueError(f"Componente duplicado: {codigo}")
        precio = sum(Decimal(f['importe_base']) / Decimal(f['cantidad_por_envase']) * Decimal(f['cantidad_por_recurso']) for f in filas).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        if any(Decimal(f['precio_resultante']) != precio for f in filas):
            raise ValueError(f"Normalización incoherente: {codigo}")
        iva = 'por_verificar' if any(f['criterio_iva'] == 'IVA no confirmado' for f in filas) else 'no'
        reservas = ' '.join(dict.fromkeys(f['reserva'] for f in filas))
        resultado[codigo] = {'ES': ref(precio, precio, precio, REVISION_LOTE_SISTEMAS,
            confianza='derivado', incluye_iva=iva, incluye_transporte='no_confirmado',
            observaciones='Estimación provisional puntual; no es media nacional ni rango de mercado. ' + reservas)}
    return resultado



REVISION_LOTE_BLOQUE_AMPLIO = "docs/auditoria_precios/ESPANA_LOTE_BLOQUE_AMPLIO_2026-11-07.md"
FUENTES_LOTE_BLOQUE_AMPLIO = ROOT / "docs/auditoria_precios/espana_fuentes_bloque_amplio_2026-11-07.csv"


def referencias_lote_bloque_amplio() -> dict[str, dict[str, Referencia]]:
    """Suma componentes de ofertas puntuales sin confundirlos con una media."""
    esperados = {'MT-CANAL-PVC': 1, 'MT-ESCALERILLA': 1, 'MT-TOMA-DATOS': 3, 'MT-LADRILLO-VISTO': 1, 'MT-TORNILLO-EST': 1, 'MT-STEELDECK': 1, 'MT-CANON-TIERRA': 1, 'MT-ENDURECEDOR': 1, 'MT-BARRERA-ANTICAP': 1, 'MT-ANCLA-PIEDRA': 1, 'MT-EXTINTOR': 1, 'MT-ARNES': 1}
    catalogo = json.loads(SRC.read_text(encoding="utf-8"))
    unidades = {codigo: item.get("unidad", "ud") for codigo, _, item in iter_recursos(catalogo)}
    grupos = {}
    with FUENTES_LOTE_BLOQUE_AMPLIO.open(encoding="utf-8-sig", newline="") as f:
        for fila in csv.DictReader(f, delimiter=";"):
            codigo = fila['codigo_recurso']
            criterio = fila['criterio_iva']
            if (codigo not in esperados or fila['unidad'] != unidades.get(codigo)
                    or not all(fila[k] for k in ('producto', 'fuente', 'url', 'url_precio', 'reserva'))
                    or not fila['url'].startswith(('https://', 'http://'))
                    or not fila['url_precio'].startswith(('https://', 'http://'))
                    or fila['fecha_consulta'] != '2026-11-07'
                    or criterio not in {'neto en ficha', 'IVA 21% supuesto', 'IVA no confirmado'}
                    or (criterio == 'neto en ficha' and fila['fuente'] != 'Jorge Fernández')
                    or (criterio == 'IVA no confirmado' and fila['fuente'] != 'CYPE')):
                raise ValueError(f"Fuente de bloque_amplio inválida: {codigo}")
            base, divisor, cantidad = (Decimal(fila[k]) for k in ('importe_base', 'cantidad_por_envase', 'cantidad_por_recurso'))
            if any(not x.is_finite() or x <= 0 for x in (base, divisor, cantidad)):
                raise ValueError(f"Precio o cantidad inválidos: {codigo}")
            if criterio == 'IVA no confirmado':
                if fila['precio_bruto']:
                    raise ValueError(f"IVA no confirmado incompatible con PVP: {codigo}")
            elif criterio == 'neto en ficha':
                if fila['precio_bruto']:
                    raise ValueError(f'Neto no debe llevar PVP: {codigo}')
            else:
                bruto = Decimal(fila['precio_bruto'])
                if not bruto.is_finite() or bruto <= 0:
                    raise ValueError(f"PVP inválido: {codigo}")
                tolerancia = Decimal('0.000001') if criterio == 'IVA 21% supuesto' else Decimal('0.01')
                if abs(base - bruto / Decimal('1.21')) > tolerancia:
                    raise ValueError(f"IVA incoherente: {codigo}")
            grupos.setdefault(codigo, []).append(fila)
    if {k: len(v) for k, v in grupos.items()} != esperados:
        raise ValueError("Lote de bloque_amplio incompleto o duplicado")
    resultado = {}
    for codigo, filas in grupos.items():
        if len({f['producto'] for f in filas}) != len(filas):
            raise ValueError(f"Componente duplicado: {codigo}")
        precio = sum(Decimal(f['importe_base']) / Decimal(f['cantidad_por_envase']) * Decimal(f['cantidad_por_recurso']) for f in filas).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        if any(Decimal(f['precio_resultante']) != precio for f in filas):
            raise ValueError(f"Normalización incoherente: {codigo}")
        iva = 'por_verificar' if any(f['criterio_iva'] == 'IVA no confirmado' for f in filas) else 'no'
        reservas = ' '.join(dict.fromkeys(f['reserva'] for f in filas))
        resultado[codigo] = {'ES': ref(precio, precio, precio, REVISION_LOTE_BLOQUE_AMPLIO,
            confianza='derivado', incluye_iva=iva, incluye_transporte='no_confirmado',
            observaciones='Estimación provisional puntual; no es media nacional ni rango de mercado. ' + reservas)}
    return resultado



REVISION_LOTE_VERIFICACION = "docs/auditoria_precios/ESPANA_LOTE_VERIFICACION_2026-11-07.md"
FUENTES_LOTE_VERIFICACION = ROOT / "docs/auditoria_precios/espana_fuentes_verificacion_2026-11-07.csv"


def referencias_lote_verificacion() -> dict[str, dict[str, Referencia]]:
    """Suma componentes de ofertas puntuales sin confundirlos con una media."""
    esperados = {'MT-MOLDURA-YESO': 2, 'MT-CORNISA': 1, 'MT-JUNTA-DILAT': 1, 'MT-HERRAJE-MAD': 1, 'MT-TABIQUE-MOVIL': 1, 'MT-MASTIC-CORTAFUEGO': 1, 'MT-TUBO-DREN': 1}
    catalogo = json.loads(SRC.read_text(encoding="utf-8"))
    unidades = {codigo: item.get("unidad", "ud") for codigo, _, item in iter_recursos(catalogo)}
    grupos = {}
    with FUENTES_LOTE_VERIFICACION.open(encoding="utf-8-sig", newline="") as f:
        for fila in csv.DictReader(f, delimiter=";"):
            codigo = fila['codigo_recurso']
            criterio = fila['criterio_iva']
            if (codigo not in esperados or fila['unidad'] != unidades.get(codigo)
                    or not all(fila[k] for k in ('producto', 'fuente', 'url', 'url_precio', 'reserva'))
                    or not fila['url'].startswith(('https://', 'http://'))
                    or not fila['url_precio'].startswith(('https://', 'http://'))
                    or fila['fecha_consulta'] != '2026-11-07'
                    or criterio not in {'neto en ficha', 'IVA 21% supuesto', 'IVA no confirmado'}
                    or (criterio == 'neto en ficha' and fila['fuente'] != 'Distriplac')
                    or (criterio == 'IVA no confirmado' and fila['fuente'] != 'CYPE')):
                raise ValueError(f"Fuente de verificacion inválida: {codigo}")
            base, divisor, cantidad = (Decimal(fila[k]) for k in ('importe_base', 'cantidad_por_envase', 'cantidad_por_recurso'))
            if any(not x.is_finite() or x <= 0 for x in (base, divisor, cantidad)):
                raise ValueError(f"Precio o cantidad inválidos: {codigo}")
            if criterio == 'IVA no confirmado':
                if fila['precio_bruto']:
                    raise ValueError(f"IVA no confirmado incompatible con PVP: {codigo}")
            elif criterio == 'neto en ficha':
                if fila['precio_bruto']:
                    raise ValueError(f'Neto no debe llevar PVP: {codigo}')
            else:
                bruto = Decimal(fila['precio_bruto'])
                if not bruto.is_finite() or bruto <= 0:
                    raise ValueError(f"PVP inválido: {codigo}")
                tolerancia = Decimal('0.000001') if criterio == 'IVA 21% supuesto' else Decimal('0.01')
                if abs(base - bruto / Decimal('1.21')) > tolerancia:
                    raise ValueError(f"IVA incoherente: {codigo}")
            grupos.setdefault(codigo, []).append(fila)
    if {k: len(v) for k, v in grupos.items()} != esperados:
        raise ValueError("Lote de verificacion incompleto o duplicado")
    resultado = {}
    for codigo, filas in grupos.items():
        if len({f['producto'] for f in filas}) != len(filas):
            raise ValueError(f"Componente duplicado: {codigo}")
        precio = sum(Decimal(f['importe_base']) / Decimal(f['cantidad_por_envase']) * Decimal(f['cantidad_por_recurso']) for f in filas).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        if any(Decimal(f['precio_resultante']) != precio for f in filas):
            raise ValueError(f"Normalización incoherente: {codigo}")
        iva = 'por_verificar' if any(f['criterio_iva'] == 'IVA no confirmado' for f in filas) else 'no'
        reservas = ' '.join(dict.fromkeys(f['reserva'] for f in filas))
        resultado[codigo] = {'ES': ref(precio, precio, precio, REVISION_LOTE_VERIFICACION,
            confianza='derivado', incluye_iva=iva, incluye_transporte='no_confirmado',
            observaciones='Estimación provisional puntual; no es media nacional ni rango de mercado. ' + reservas)}
    return resultado



REVISION_LOTE_CONTINUACION = "docs/auditoria_precios/ESPANA_LOTE_CONTINUACION_2026-11-07.md"
FUENTES_LOTE_CONTINUACION = ROOT / "docs/auditoria_precios/espana_fuentes_continuacion_2026-11-07.csv"


def referencias_lote_continuacion() -> dict[str, dict[str, Referencia]]:
    """Suma componentes de ofertas puntuales sin confundirlos con una media."""
    esperados = {'MT-GRAVILLA': 1, 'MT-CRU-NIV': 2, 'MT-MAMPARA-OFI': 1, 'MT-PANEL-PVC-BANO': 1, 'MT-MOSAICO': 1, 'MT-ADH-PIEDRA': 1}
    catalogo = json.loads(SRC.read_text(encoding="utf-8"))
    unidades = {codigo: item.get("unidad", "ud") for codigo, _, item in iter_recursos(catalogo)}
    grupos = {}
    with FUENTES_LOTE_CONTINUACION.open(encoding="utf-8-sig", newline="") as f:
        for fila in csv.DictReader(f, delimiter=";"):
            codigo = fila['codigo_recurso']
            criterio = fila['criterio_iva']
            if (codigo not in esperados or fila['unidad'] != unidades.get(codigo)
                    or not all(fila[k] for k in ('producto', 'fuente', 'url', 'url_precio', 'reserva'))
                    or not fila['url'].startswith(('https://', 'http://'))
                    or not fila['url_precio'].startswith(('https://', 'http://'))
                    or fila['fecha_consulta'] != '2026-11-07'
                    or criterio not in {'neto en ficha', 'IVA 21% supuesto', 'IVA no confirmado'}
                    or (criterio == 'neto en ficha' and fila['fuente'] != 'Distriplac')
                    or (criterio == 'IVA no confirmado' and fila['fuente'] != 'CYPE')):
                raise ValueError(f"Fuente de continuacion inválida: {codigo}")
            base, divisor, cantidad = (Decimal(fila[k]) for k in ('importe_base', 'cantidad_por_envase', 'cantidad_por_recurso'))
            if any(not x.is_finite() or x <= 0 for x in (base, divisor, cantidad)):
                raise ValueError(f"Precio o cantidad inválidos: {codigo}")
            if criterio == 'IVA no confirmado':
                if fila['precio_bruto']:
                    raise ValueError(f"IVA no confirmado incompatible con PVP: {codigo}")
            elif criterio == 'neto en ficha':
                if fila['precio_bruto']:
                    raise ValueError(f'Neto no debe llevar PVP: {codigo}')
            else:
                bruto = Decimal(fila['precio_bruto'])
                if not bruto.is_finite() or bruto <= 0:
                    raise ValueError(f"PVP inválido: {codigo}")
                tolerancia = Decimal('0.000001') if criterio == 'IVA 21% supuesto' else Decimal('0.01')
                if abs(base - bruto / Decimal('1.21')) > tolerancia:
                    raise ValueError(f"IVA incoherente: {codigo}")
            grupos.setdefault(codigo, []).append(fila)
    if {k: len(v) for k, v in grupos.items()} != esperados:
        raise ValueError("Lote de continuacion incompleto o duplicado")
    resultado = {}
    for codigo, filas in grupos.items():
        if len({f['producto'] for f in filas}) != len(filas):
            raise ValueError(f"Componente duplicado: {codigo}")
        precio = sum(Decimal(f['importe_base']) / Decimal(f['cantidad_por_envase']) * Decimal(f['cantidad_por_recurso']) for f in filas).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        if any(Decimal(f['precio_resultante']) != precio for f in filas):
            raise ValueError(f"Normalización incoherente: {codigo}")
        iva = 'por_verificar' if any(f['criterio_iva'] == 'IVA no confirmado' for f in filas) else 'no'
        reservas = ' '.join(dict.fromkeys(f['reserva'] for f in filas))
        resultado[codigo] = {'ES': ref(precio, precio, precio, REVISION_LOTE_CONTINUACION,
            confianza='derivado', incluye_iva=iva, incluye_transporte='no_confirmado',
            observaciones='Estimación provisional puntual; no es media nacional ni rango de mercado. ' + reservas)}
    return resultado



REVISION_LOTE_EVACUACION_EPOXI = "docs/auditoria_precios/ESPANA_LOTE_EVACUACION_EPOXI_2026-11-07.md"
FUENTES_LOTE_EVACUACION_EPOXI = ROOT / "docs/auditoria_precios/espana_fuentes_evacuacion_epoxi_2026-11-07.csv"


def referencias_lote_evacuacion_epoxi() -> dict[str, dict[str, Referencia]]:
    """Suma componentes de ofertas puntuales sin confundirlos con una media."""
    esperados = {'MT-PLO-PVC4': 3, 'MT-TRAGANTE': 1, 'MT-EPOXI-ANCLA': 1}
    catalogo = json.loads(SRC.read_text(encoding="utf-8"))
    unidades = {codigo: item.get("unidad", "ud") for codigo, _, item in iter_recursos(catalogo)}
    grupos = {}
    with FUENTES_LOTE_EVACUACION_EPOXI.open(encoding="utf-8-sig", newline="") as f:
        for fila in csv.DictReader(f, delimiter=";"):
            codigo = fila['codigo_recurso']
            criterio = fila['criterio_iva']
            if (codigo not in esperados or fila['unidad'] != unidades.get(codigo)
                    or not all(fila[k] for k in ('producto', 'fuente', 'url', 'url_precio', 'reserva'))
                    or not fila['url'].startswith(('https://', 'http://'))
                    or not fila['url_precio'].startswith(('https://', 'http://'))
                    or fila['fecha_consulta'] != '2026-11-07'
                    or criterio not in {'neto en ficha', 'IVA 21% supuesto', 'IVA no confirmado'}
                    or (criterio == 'neto en ficha' and fila['fuente'] != 'Tapas y Registros')
                    or (criterio == 'IVA no confirmado' and fila['fuente'] != 'CYPE')):
                raise ValueError(f"Fuente de evacuacion_epoxi inválida: {codigo}")
            base, divisor, cantidad = (Decimal(fila[k]) for k in ('importe_base', 'cantidad_por_envase', 'cantidad_por_recurso'))
            if any(not x.is_finite() or x <= 0 for x in (base, divisor, cantidad)):
                raise ValueError(f"Precio o cantidad inválidos: {codigo}")
            if criterio == 'IVA no confirmado':
                if fila['precio_bruto']:
                    raise ValueError(f"IVA no confirmado incompatible con PVP: {codigo}")
            elif criterio == 'neto en ficha':
                if fila['precio_bruto']:
                    raise ValueError(f'Neto no debe llevar PVP: {codigo}')
            else:
                bruto = Decimal(fila['precio_bruto'])
                if not bruto.is_finite() or bruto <= 0:
                    raise ValueError(f"PVP inválido: {codigo}")
                tolerancia = Decimal('0.000001') if criterio == 'IVA 21% supuesto' else Decimal('0.01')
                if abs(base - bruto / Decimal('1.21')) > tolerancia:
                    raise ValueError(f"IVA incoherente: {codigo}")
            grupos.setdefault(codigo, []).append(fila)
    if {k: len(v) for k, v in grupos.items()} != esperados:
        raise ValueError("Lote de evacuacion_epoxi incompleto o duplicado")
    resultado = {}
    for codigo, filas in grupos.items():
        if len({f['producto'] for f in filas}) != len(filas):
            raise ValueError(f"Componente duplicado: {codigo}")
        precio = sum(Decimal(f['importe_base']) / Decimal(f['cantidad_por_envase']) * Decimal(f['cantidad_por_recurso']) for f in filas).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        if any(Decimal(f['precio_resultante']) != precio for f in filas):
            raise ValueError(f"Normalización incoherente: {codigo}")
        iva = 'por_verificar' if any(f['criterio_iva'] == 'IVA no confirmado' for f in filas) else 'no'
        reservas = ' '.join(dict.fromkeys(f['reserva'] for f in filas))
        resultado[codigo] = {'ES': ref(precio, precio, precio, REVISION_LOTE_EVACUACION_EPOXI,
            confianza='derivado', incluye_iva=iva, incluye_transporte='no_confirmado',
            observaciones='Estimación provisional puntual; no es media nacional ni rango de mercado. ' + reservas)}
    return resultado



REVISION_LOTE_30 = "docs/auditoria_precios/ESPANA_LOTE_30_2026-11-07.md"
FUENTES_LOTE_30 = ROOT / "docs/auditoria_precios/espana_fuentes_lote_30_2026-11-07.csv"


def referencias_lote_treinta() -> dict[str, dict[str, Referencia]]:
    """Suma componentes de ofertas puntuales sin confundirlos con una media."""
    esperados = {'MT-TUB-RIEGO': 1, 'MT-CUARZO-COLOR': 1, 'MT-POLIUREA': 1, 'MT-DOM-ACTUADOR': 1, 'MT-DOM-DIMMER': 1, 'MT-DOM-SENSOR-INUND': 1, 'MT-DOM-SENSOR-MOV': 1, 'MT-DOM-SENSOR-LUZ': 1, 'MT-DOM-SENSOR-PUERTA': 1}
    catalogo = json.loads(SRC.read_text(encoding="utf-8"))
    unidades = {codigo: item.get("unidad", "ud") for codigo, _, item in iter_recursos(catalogo)}
    grupos = {}
    with FUENTES_LOTE_30.open(encoding="utf-8-sig", newline="") as f:
        for fila in csv.DictReader(f, delimiter=";"):
            codigo = fila['codigo_recurso']
            criterio = fila['criterio_iva']
            if (codigo not in esperados or fila['unidad'] != unidades.get(codigo)
                    or not all(fila[k] for k in ('producto', 'fuente', 'url', 'url_precio', 'reserva'))
                    or not fila['url'].startswith(('https://', 'http://'))
                    or not fila['url_precio'].startswith(('https://', 'http://'))
                    or fila['fecha_consulta'] != '2026-11-07'
                    or criterio not in {'neto en ficha', 'IVA 21% supuesto', 'IVA no confirmado'}
                    or (criterio == 'neto en ficha' and fila['fuente'] != 'Tapas y Registros')
                    or (criterio == 'IVA no confirmado' and fila['fuente'] != 'CYPE')):
                raise ValueError(f"Fuente de 30 inválida: {codigo}")
            base, divisor, cantidad = (Decimal(fila[k]) for k in ('importe_base', 'cantidad_por_envase', 'cantidad_por_recurso'))
            if any(not x.is_finite() or x <= 0 for x in (base, divisor, cantidad)):
                raise ValueError(f"Precio o cantidad inválidos: {codigo}")
            if criterio == 'IVA no confirmado':
                if fila['precio_bruto']:
                    raise ValueError(f"IVA no confirmado incompatible con PVP: {codigo}")
            elif criterio == 'neto en ficha':
                if fila['precio_bruto']:
                    raise ValueError(f'Neto no debe llevar PVP: {codigo}')
            else:
                bruto = Decimal(fila['precio_bruto'])
                if not bruto.is_finite() or bruto <= 0:
                    raise ValueError(f"PVP inválido: {codigo}")
                tolerancia = Decimal('0.000001') if criterio == 'IVA 21% supuesto' else Decimal('0.01')
                if abs(base - bruto / Decimal('1.21')) > tolerancia:
                    raise ValueError(f"IVA incoherente: {codigo}")
            grupos.setdefault(codigo, []).append(fila)
    if {k: len(v) for k, v in grupos.items()} != esperados:
        raise ValueError("Lote de 30 incompleto o duplicado")
    resultado = {}
    for codigo, filas in grupos.items():
        if len({f['producto'] for f in filas}) != len(filas):
            raise ValueError(f"Componente duplicado: {codigo}")
        precio = sum(Decimal(f['importe_base']) / Decimal(f['cantidad_por_envase']) * Decimal(f['cantidad_por_recurso']) for f in filas).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        if any(Decimal(f['precio_resultante']) != precio for f in filas):
            raise ValueError(f"Normalización incoherente: {codigo}")
        iva = 'por_verificar' if any(f['criterio_iva'] == 'IVA no confirmado' for f in filas) else 'no'
        reservas = ' '.join(dict.fromkeys(f['reserva'] for f in filas))
        resultado[codigo] = {'ES': ref(precio, precio, precio, REVISION_LOTE_30,
            confianza='derivado', incluye_iva=iva, incluye_transporte='no_confirmado',
            observaciones='Estimación provisional puntual; no es media nacional ni rango de mercado. ' + reservas)}
    return resultado



REVISION_OTROS_30 = "docs/auditoria_precios/ESPANA_LOTE_OTROS_30_2026-11-07.md"
FUENTES_OTROS_30 = ROOT / "docs/auditoria_precios/espana_fuentes_otros_30_2026-11-07.csv"


def referencias_otros_treinta() -> dict[str, dict[str, Referencia]]:
    """Suma componentes de ofertas puntuales sin confundirlos con una media."""
    esperados = {'MT-APEO': 3}
    catalogo = json.loads(SRC.read_text(encoding="utf-8"))
    unidades = {codigo: item.get("unidad", "ud") for codigo, _, item in iter_recursos(catalogo)}
    grupos = {}
    with FUENTES_OTROS_30.open(encoding="utf-8-sig", newline="") as f:
        for fila in csv.DictReader(f, delimiter=";"):
            codigo = fila['codigo_recurso']
            criterio = fila['criterio_iva']
            if (codigo not in esperados or fila['unidad'] != unidades.get(codigo)
                    or not all(fila[k] for k in ('producto', 'fuente', 'url', 'url_precio', 'reserva'))
                    or not fila['url'].startswith(('https://', 'http://'))
                    or not fila['url_precio'].startswith(('https://', 'http://'))
                    or fila['fecha_consulta'] != '2026-11-07'
                    or criterio not in {'neto en ficha', 'IVA 21% supuesto', 'IVA no confirmado'}
                    or (criterio == 'neto en ficha' and fila['fuente'] != 'Tapas y Registros')
                    or (criterio == 'IVA no confirmado' and fila['fuente'] != 'CYPE')):
                raise ValueError(f"Fuente de 30 inválida: {codigo}")
            base, divisor, cantidad = (Decimal(fila[k]) for k in ('importe_base', 'cantidad_por_envase', 'cantidad_por_recurso'))
            if any(not x.is_finite() or x <= 0 for x in (base, divisor, cantidad)):
                raise ValueError(f"Precio o cantidad inválidos: {codigo}")
            if criterio == 'IVA no confirmado':
                if fila['precio_bruto']:
                    raise ValueError(f"IVA no confirmado incompatible con PVP: {codigo}")
            elif criterio == 'neto en ficha':
                if fila['precio_bruto']:
                    raise ValueError(f'Neto no debe llevar PVP: {codigo}')
            else:
                bruto = Decimal(fila['precio_bruto'])
                if not bruto.is_finite() or bruto <= 0:
                    raise ValueError(f"PVP inválido: {codigo}")
                tolerancia = Decimal('0.000001') if criterio == 'IVA 21% supuesto' else Decimal('0.01')
                if abs(base - bruto / Decimal('1.21')) > tolerancia:
                    raise ValueError(f"IVA incoherente: {codigo}")
            grupos.setdefault(codigo, []).append(fila)
    if {k: len(v) for k, v in grupos.items()} != esperados:
        raise ValueError("Lote de 30 incompleto o duplicado")
    resultado = {}
    for codigo, filas in grupos.items():
        if len({f['producto'] for f in filas}) != len(filas):
            raise ValueError(f"Componente duplicado: {codigo}")
        precio = sum(Decimal(f['importe_base']) / Decimal(f['cantidad_por_envase']) * Decimal(f['cantidad_por_recurso']) for f in filas).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        if any(Decimal(f['precio_resultante']) != precio for f in filas):
            raise ValueError(f"Normalización incoherente: {codigo}")
        iva = 'por_verificar' if any(f['criterio_iva'] == 'IVA no confirmado' for f in filas) else 'no'
        reservas = ' '.join(dict.fromkeys(f['reserva'] for f in filas))
        resultado[codigo] = {'ES': ref(precio, precio, precio, REVISION_OTROS_30,
            confianza='derivado', incluye_iva=iva, incluye_transporte='no_confirmado',
            observaciones='Estimación provisional puntual; no es media nacional ni rango de mercado. ' + reservas)}
    return resultado



REVISION_CIERRE = "docs/auditoria_precios/ESPANA_CIERRE_2026-11-07.md"
BANCO_EX = "Base de Precios de Construcción de Extremadura 2026 (BCEXTGREM_26_v1.bc3)"
FUENTES_CIERRE = ROOT / "docs/auditoria_precios/espana_referencias_cierre_2026-11-07.csv"


def referencias_cierre_2026_11_07() -> dict[str, dict[str, Referencia]]:
    """Precios de cierre de la auditoría, aplicados desde una tabla validada.

    Es la vía data-driven para futuros lotes: no se añade código por recurso,
    solo filas nuevas en el CSV de referencias aceptadas.
    """
    catalogo = json.loads(SRC.read_text(encoding="utf-8"))
    unidades = {codigo: item.get("unidad", "ud") for codigo, _, item in iter_recursos(catalogo)}
    resultado = {}
    with FUENTES_CIERRE.open(encoding="utf-8-sig", newline="") as manejador:
        for fila in csv.DictReader(manejador, delimiter=";"):
            codigo = fila["codigo_recurso"]
            if codigo not in unidades or codigo in resultado:
                raise ValueError(f"Referencia de cierre duplicada o inexistente: {codigo}")
            precio = Decimal(fila["precio"])
            minimo, maximo = Decimal(fila["minimo"]), Decimal(fila["maximo"])
            if (not precio.is_finite() or precio <= 0 or minimo <= 0 or maximo < minimo
                    or not fila["fuente"].strip() or not fila["criterio"].strip()):
                raise ValueError(f"Referencia de cierre inválida: {codigo}")
            # Un precio igual a la ficha del banco, adoptado sin transformar, es un
            # ancla observada; la convención de medida solo elige la ficha, no la cifra.
            ancla = (fila["fuente"] == BANCO_EX
                     or fila["fuente"].startswith(BANCO_EX + " con convención de medida"))
            resultado[codigo] = {"ES": ref(
                precio, minimo, maximo, REVISION_CIERRE,
                confianza=("referencia" if ancla else "derivado"),
                incluye_iva=("no" if fila["incluye_iva"] == "no" else "no_confirmado"),
                incluye_transporte=("no" if fila["incluye_transporte"] == "no" else "no_confirmado"),
                observaciones=(f"{fila['fuente']}. {fila['criterio']} Reserva: {fila['reserva']} "
                               "Referencia operativa de cierre; no es garantía de precio universal."),
            )}
    if not resultado:
        raise ValueError("La tabla de referencias de cierre está vacía")
    return resultado


def _numero(valor: float) -> str:
    return f"{valor:.6f}".rstrip("0").rstrip(".")


def main():
    data = json.loads(SRC.read_text(encoding="utf-8"))
    # La canasta histórica se mantiene congelada: una revisión individual no
    # debe recalibrar silenciosamente cientos de recursos aún pendientes.
    factores = completar_referencias_derivadas(data)
    referencias_finales = {**REFERENCIAS, **referencias_materiales_revisadas(), **referencias_materiales_07(), **referencias_lote_regional(), **referencias_lote_comercial(), **referencias_lote_prioritario(), **referencias_lote_tiendas(), **referencias_lote_posterior(), **referencias_lote_banco(), **referencias_lote_cuadros(), **referencias_lote_materiales(), **referencias_lote_cadenas(), **referencias_lote_prioridad(), **referencias_lote_alta_frecuencia(), **referencias_lote_familias(), **referencias_lote_componentes(), **referencias_lote_sistemas(), **referencias_lote_bloque_amplio(), **referencias_lote_verificacion(), **referencias_lote_continuacion(), **referencias_lote_evacuacion_epoxi(), **referencias_lote_treinta(), **referencias_otros_treinta(), **referencias_cierre_2026_11_07()}
    rows = []
    codigos = set()
    for codigo, categoria, item in iter_recursos(data):
        codigos.add(codigo)
        for pais, moneda in PAISES:
            dato = referencias_finales.get(codigo, {}).get(pais)
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
                    else FECHA_REVISION_MO if dato and dato.fuente == REVISION_MO
                    else FECHA_MATERIALES_07 if dato and dato.fuente in (REVISION_MATERIALES_07, REVISION_LOTE_REGIONAL, REVISION_LOTE_COMERCIAL, REVISION_LOTE_PRIORITARIO, REVISION_LOTE_TIENDAS, REVISION_LOTE_POSTERIOR, REVISION_LOTE_BANCO, REVISION_LOTE_CUADROS, REVISION_LOTE_MATERIALES, REVISION_LOTE_CADENAS, REVISION_LOTE_PRIORIDAD, REVISION_LOTE_ALTA_FRECUENCIA, REVISION_LOTE_FAMILIAS, REVISION_LOTE_COMPONENTES, REVISION_LOTE_SISTEMAS, REVISION_LOTE_BLOQUE_AMPLIO, REVISION_LOTE_VERIFICACION, REVISION_LOTE_CONTINUACION, REVISION_LOTE_EVACUACION_EPOXI, REVISION_LOTE_30, REVISION_OTROS_30, REVISION_CIERRE)
                    else FECHA_REVISION_MATERIALES if dato and dato.fuente == REVISION_MATERIALES
                    else FECHA if dato else ""
                ),
                "confianza": dato.confianza if dato else "pendiente",
                "incluye_iva": dato.incluye_iva if dato else "por_verificar",
                "incluye_transporte": dato.incluye_transporte if dato else "no_confirmado",
                "origen": "nacional" if dato else "pendiente",
                "observaciones": dato.observaciones if dato else "Pendiente de investigación específica.",
            })

    referencias_huerfanas = sorted(set(referencias_finales) - codigos)
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
