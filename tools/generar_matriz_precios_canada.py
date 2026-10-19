#!/usr/bin/env python3
"""Genera la matriz de precios de recursos para Canadá (CAD).

Replica el contrato de ``generar_matriz_precios_irlanda.py`` y
``generar_matriz_precios_australia.py``:

* Los precios base de ``basedatos_partidas/datos/recursos.json`` están en USD
  con ámbito **Venezuela**. No son precios internacionales, así que ninguna
  conversión de divisa puede producir un precio canadiense. La matriz se
  construye desde precios canadienses reales.
* Las anclas investigadas se publican tal cual, con rango, fuente y fecha.
* El resto se cubre con un **factor de mercado por familia**, calculado como
  la mediana de la relación entre el precio canadiense investigado y el
  precio base de cada ancla de esa familia.
* La mano de obra no usa factores: los 17 oficios salen del modelo de coste
  empresa de ``coste_empresa_canada.py``.

Particularidades de Canadá frente a España, GB, Irlanda y Australia:

* **Los precios de estantería se publican sin impuestos.** Al contrario que
  en AU (GST incluido en Bunnings), en Canadá el precio retail (Home Depot,
  RONA) es «+ taxes»: la cifra observada ya es sin GST/HST y entra tal cual.
  El impuesto aplicable varía por provincia (HST 13 % en Ontario; GST 5 %
  federal como tipo de referencia de la aplicación).
* Canadá es **métrico en el precio pero imperial en el formato**: el bloque
  es el CMU de 8×8×16" (190×190×390 mm), la placa de yeso es de 4×8 ft
  (2,97 m²), el cemento se vende en sacos de 40 kg, los adhesivos en sacos
  de 50 lb (22,7 kg) y los áridos a granel por yarda cúbica o tonelada.
  Todas las conversiones quedan en la observación de cada ancla.
* No existe escala legal sectorial: la mano de obra parte de la **mediana
  salarial** (Job Bank, como la ONS en GB), así que el rango sí baja un
  10 % y sube un 25 % (dispersión provincial; el paquete sindical ICI del
  GTA queda por encima, documentado en la investigación).
* Equivalencias de mercado declaradas: el desagüe estándar es ABS (no PVC);
  la tubería de agua es PEX (el PPR es residual, como en AU); el cable
  residencial es el NMD90 (el «Romex» canadiense); la malla electrosoldada
  corriente es la 6×6 W2.9 en hojas de 4×8 ft.

Uso:
    python3 tools/generar_matriz_precios_canada.py
"""
from __future__ import annotations

import csv
import json
import statistics
from dataclasses import dataclass, replace
from pathlib import Path

from coste_empresa_canada import (
    HORAS_FACTURABLES,
    OFICIOS,
    WSIB,
    coste_empresa,
)

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "basedatos_partidas/datos/recursos.json"
OUT = ROOT / "basedatos_partidas/salida/precios_recursos_canada.csv"
PAISES = (("CA", "CAD"),)
FECHA = "2026-10-19"

R_CA = "docs/INVESTIGACION_PRECIOS_CANADA.md"
METODOLOGIA = "docs/METODOLOGIA_PRECIOS_REFERENCIA_CANADA.md"
# Banco de Canadá, cierre 16/10/2026: USD/CAD 1,4154 -> 1 USD = 1,4154 CAD
# (el mismo corte que app/services/tasa.py). Solo normaliza el precio base
# antes de aplicar el factor de mercado; el resultado queda congelado en
# CAD y con fecha.
TASAS_CORTE = {"CA": 1.4154}

OBS_REFERENCIA = (
    "Precio de mercado canadiense observado (sin GST/HST — en Canadá el "
    "precio de estantería ya se publica sin impuestos —, sin porte salvo "
    "indicación); puede variar por proveedor, marca, volumen y provincia."
)
OBS_DERIVADO = (
    "Precio referencial derivado del factor de mercado de su familia, calculado "
    "sobre la canasta canadiense investigada; no es una cotización de tienda."
)


@dataclass(frozen=True)
class Referencia:
    precio: float
    minimo: float
    maximo: float
    fuente: str
    confianza: str = "referencia"
    observaciones: str = OBS_REFERENCIA
    incluye_iva: str = "no"
    incluye_transporte: str = "no_confirmado"


def ref(precio, minimo, maximo, fuente=R_CA, **kwargs) -> Referencia:
    precio, minimo, maximo = map(float, (precio, minimo, maximo))
    if minimo <= 0 or maximo < minimo or not minimo <= precio <= maximo:
        raise ValueError(f"Rango inválido: {minimo} <= {precio} <= {maximo}")
    return Referencia(precio, minimo, maximo, fuente, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Mano de obra — modelo de coste empresa canadiense
# ─────────────────────────────────────────────────────────────────────────────

def referencias_mano_obra() -> dict[str, dict[str, Referencia]]:
    salida: dict[str, dict[str, Referencia]] = {}
    for codigo, (oficio, salario, escala, clase) in OFICIOS.items():
        coste = coste_empresa(salario, WSIB[clase])["coste_hora_facturable"]
        # La base es la mediana salarial (Job Bank), no un mínimo legal,
        # así que el rango puede bajar como en el Reino Unido: −10 %
        # (provincias atlánticas, residencial rural) y +25 % (GTA, Alberta,
        # BC y tracción sindical). El «total package» ICI del GTA queda aun
        # por encima y se documenta en la investigación.
        salida[codigo] = {
            "CA": ref(
                coste,
                coste * 0.90,
                coste * 1.25,
                R_CA,
                confianza="referencia",
                incluye_iva="no_aplica",
                incluye_transporte="no_aplica",
                observaciones=(
                    f"Coste empresa por hora trabajada. {oficio}. Salario "
                    f"ordinario {salario:.2f} $/h ({escala}, a octubre de "
                    f"2026) × 1.976 h pagadas + vacation pay 4 %, CPP "
                    f"empresa 5,95 % con techo (YMPE 74.600 $) y CPP2 4 %, "
                    f"EI empresa 2,282 % con techo (68.900 $) y WSIB Ontario "
                    f"clase {clase}, dividido por {HORAS_FACTURABLES:,.0f} h "
                    f"trabajadas/año (238 días de 8 h tras vacaciones ESA, "
                    f"festivos y bajas no pagadas). No es tarifa de "
                    f"subcontrata: el catálogo ya aplica un 35 % de margen "
                    f"sobre el coste directo."
                ),
            )
        }
    return salida


# ─────────────────────────────────────────────────────────────────────────────
# 2. Maquinaria — tarifas de alquiler canadienses
#
#    United Rentals y Sunbelt publican tarifas en su marketplace, pero el
#    ancla reproducible sale de las listas públicas por día de hire del GTA
#    (Toronto Rental Equipment, 2025-26; guías de mercado 2026 para
#    excavadoras y plataformas). El resto se publica «derivado» con precio
#    explícito por analogía documentada. Día de 8 h, sin GST/HST ni
#    combustible; con operador solo donde se indica (bomba, grúa,
#    perforadora, volqueta).
# ─────────────────────────────────────────────────────────────────────────────

def _alquiler(dia, minimo, maximo, nota="", confianza="referencia") -> Referencia:
    return ref(
        dia / 8.0, minimo / 8.0, maximo / 8.0, R_CA,
        confianza=confianza,
        observaciones=(
            f"Alquiler canadiense {minimo:.0f}-{maximo:.0f} $/día (jornada de 8 h), "
            f"sin GST/HST ni combustible. {nota}".strip()
        ),
    )


MAQUINARIA: dict[str, Referencia] = {
    # Corte y demolición
    "MQ-CORT-AGUA": _alquiler(87, 70, 105, "Sierra húmeda de cerámica de 7\" a "
                              "87 $/día (Toronto Rental Equipment, 2025)."),
    "MQ-ROZAD": _alquiler(105, 85, 135, "Rozadora con aspiración; analogía con "
                          "equipo de corte de los catálogos del GTA.",
                          confianza="derivado"),
    "MQ-MART-ELEC": _alquiler(82, 70, 100, "Martillo demoledor de 20 lb a "
                              "82 $/día y breaker de suelo a 95 $/día "
                              "(Toronto Rental Equipment, 2025)."),
    "MQ-AMOLA": _alquiler(50, 40, 65, "Amoladora angular de 4-1/2\" a 50 $/día "
                          "(Toronto Rental Equipment, 2025)."),
    "MQ-SIERRA": _alquiler(75, 60, 95, "Motosierra de 18\" a 75 $/día (Toronto "
                           "Rental Equipment, 2025); la sierra circular de "
                           "mano se alquila por ≈26 $/día."),
    "MQ-OXICORTE": _alquiler(85, 65, 110, "Equipo de oxicorte con botellas.",
                             confianza="derivado"),
    "MQ-CIZALLA": _alquiler(95, 75, 125, "Corta-dobladora de barra de hire "
                            "especializado.", confianza="derivado"),
    "MQ-ESMERIL": _alquiler(115, 90, 145, "Amoladora/pulidora de suelo de mano; "
                            "analogía con la banda de esmeriles del GTA.",
                            confianza="derivado"),
    # Hormigón
    "MQ-MEZCL": _alquiler(85, 65, 115, "Hormigonera de 3-6 ft³: listas de "
                          "Ontario de 70 $/día (eléctrica) a 110 $/día "
                          "(gasolina) en 2022, actualizadas.",
                          confianza="derivado"),
    "MQ-BATID": _alquiler(50, 40, 70, "Batidora de paleta.", confianza="derivado"),
    "MQ-VIBRADOR": _alquiler(70, 55, 90, "Vibrador de aguja con unidad motriz.",
                             confianza="derivado"),
    "MQ-ALISADORA": _alquiler(125, 100, 155, "Alisadora helicóptero (power "
                              "trowel).", confianza="derivado"),
    "MQ-BOMBA-CONC": _alquiler(1600, 1300, 2000, "Bomba de hormigón **con "
                               "operador**. En el GTA se cobra por salida más "
                               "$/m³ bombeado: jornada estimada.",
                               confianza="derivado"),
    "MQ-PROYECT-MORT": _alquiler(210, 165, 270, "Máquina de proyectar "
                                 "mortero/estuco con compresor.",
                                 confianza="derivado"),
    # Compactación y movimiento de tierras
    "MQ-COMPACT-SALTO": _alquiler(100, 85, 120, "Compactador de impacto "
                                  "(jumping jack): listas de Ontario en "
                                  "90 $/día (2022), actualizadas.",
                                  confianza="derivado"),
    "MQ-PLANCHA-COMP": _alquiler(95, 80, 115, "Plancha compactadora de 13\" a "
                                 "95 $/día (Toronto Rental Equipment, 2025)."),
    "MQ-RETRO": _alquiler(550, 450, 700, "Miniexcavadora de ≈3,5 t en seco "
                          "(250-450 $/día según guías y marketplaces del GTA, "
                          "2026; media DOZR ≈399 $) + martillo hidráulico "
                          "(≈150 $/día); el operador va en la mano de obra "
                          "de la partida."),
    "MQ-MART-NEUM": _alquiler(250, 210, 310, "Compresor de obra con martillo "
                              "neumático.", confianza="derivado"),
    "MQ-PERF-PILOTE": _alquiler(3200, 2600, 4000, "Equipo de perforación de "
                                "pilotes **con operador**; alquiler "
                                "especializado por proyecto, sin tarifa "
                                "pública.", confianza="derivado"),
    # Elevación y acceso
    "MQ-ANDAMIO": _alquiler(120, 95, 160, "Torre móvil de andamio; como banda "
                            "de referencia, la plataforma de tijera de 19 ft "
                            "se alquila a 120-216 $/día en Toronto (2026).",
                            confianza="derivado"),
    "MQ-MONTAC": _alquiler(170, 135, 220, "Montacargas de material / elevador "
                           "de tejado.", confianza="derivado"),
    "MQ-VENT-SUC": _alquiler(45, 35, 60, "Juego de ventosas de elevación de "
                             "gran formato.", confianza="derivado"),
    "MQ-GRUA": _alquiler(1750, 1400, 2100, "Grúa móvil **con operador** (wet "
                         "hire ≈200-250 $/h en el GTA).", confianza="derivado"),
    # Instalaciones y acabados
    "MQ-ATORN": _alquiler(40, 30, 55, "Atornilladora para placa (screw gun).",
                          confianza="derivado"),
    "MQ-LIJAD": _alquiler(80, 65, 105, "Lijadora jirafa de pared con "
                          "aspiración.", confianza="derivado"),
    "MQ-PULIDORA": _alquiler(105, 85, 130, "Pulidora de piedra/hormigón.",
                             confianza="derivado"),
    "MQ-LIJAD-PISO": _alquiler(135, 110, 170, "Lijadora de banda de pisos + "
                               "orilladora (juego).", confianza="derivado"),
    "MQ-ESTAMP": _alquiler(145, 115, 185, "Moldes de hormigón impreso.",
                           confianza="derivado"),
    "MQ-SOLDADORA": _alquiler(70, 55, 90, "Soldadora MIG/inverter de hire "
                              "general.", confianza="derivado"),
    "MQ-TERMOF": _alquiler(60, 45, 80, "La termofusión PPR es residual en "
                           "Canadá (PEX de expansión/crimpado): equipo de "
                           "expansión PEX por analogía.", confianza="derivado"),
    "MQ-DOBLAD-TUBO": _alquiler(45, 35, 60, "Dobladora de tubo de cobre y kit "
                                "de abocardado.", confianza="derivado"),
    "MQ-RECUP-GAS": _alquiler(115, 90, 150, "Recuperadora de refrigerante y "
                              "bomba de vacío.", confianza="derivado"),
    "MQ-INYECTORA": _alquiler(125, 95, 165, "Equipo de inyección de resinas a "
                              "baja presión.", confianza="derivado"),
    "MQ-RODILLO": _alquiler(25, 18, 35, "Equipo de aplicación: rodillos, "
                            "brochas, cubetas y escalera, amortizado.",
                            confianza="derivado"),
    # Limpieza, achique y seguridad
    "MQ-ASPIR": _alquiler(65, 50, 85, "Aspirador industrial con filtro HEPA.",
                          confianza="derivado"),
    "MQ-HIDROLAV": _alquiler(87, 70, 110, "Hidrolavadora de gasolina "
                             "2.000-3.000 psi a 87 $/día (Toronto Rental "
                             "Equipment, 2025)."),
    "MQ-BOMBA-ACHI": _alquiler(89, 70, 110, "Bomba de achique (trash pump de "
                               "2\") a 89 $/día (Toronto Rental Equipment, "
                               "2025)."),
    "MQ-DESBROZ": _alquiler(55, 45, 70, "Desbrozadora (brush cutter).",
                            confianza="derivado"),
    # Medición y detección
    "MQ-NIVEL-LASER": _alquiler(75, 60, 95, "Nivel láser rotativo de hire "
                                "general del GTA.", confianza="derivado"),
    "MQ-DETECTOR": _alquiler(85, 65, 110, "Localizador de servicios enterrados "
                             "( line locator).", confianza="derivado"),
    "MQ-TALADRO": _alquiler(50, 40, 70, "Taladro percutor SDS.",
                            confianza="derivado"),
    "MQ-TELUROMETRO": _alquiler(105, 80, 140, "Medidor de resistencia de "
                                "tierra y equipo de comprobación eléctrica.",
                                confianza="derivado"),
    # Transporte
    "MQ-VOLQ": _alquiler(1050, 850, 1300, "Camión volqueta **con chofer** "
                         "(dump truck wet hire ≈110-150 $/h en el GTA).",
                         confianza="derivado"),
    # Unidad distinta: el baño portátil se alquila por mes.
    "MQ-BANO-PORT": ref(
        285, 230, 350, R_CA,
        confianza="derivado",
        observaciones=(
            "Alquiler mensual de baño portátil de obra con servicio "
            "semanal (recurso medido en unidades, no en horas). Sin "
            "GST/HST. Estimación de mercado de Ontario."
        ),
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# 3. Materiales — precios de proveedor canadiense
#
#    Todos los precios son sin GST/HST: en Canadá el precio publicado es
#    «+ taxes» y entra tal cual (al contrario que en Australia). Fuentes:
#    Home Depot Canadá y RONA (retail), la guía de precios 2026 de
#    Hamilton Builders' Supply (mayorista de Ontario), las listas de planta
#    de Canada Building Materials / Ontario Redi-Mix (ene-2026) y guías de
#    mercado del GTA para lo que no tiene estantería (rebar, madera).
# ─────────────────────────────────────────────────────────────────────────────

MATERIALES: dict[str, Referencia] = {
    # ── Hormigón y áridos ────────────────────────────────────────────────────
    # Dos productores publican lista de planta 2026 para el GTA (CBM desde el
    # 15/01/2026 y Ontario Redi-Mix): 20 MPa a 240-254 $/m³, 25 MPa a
    # 245-266, 30 MPa a 255-275, 35 MPa a 270-290. Precio de planta, sin
    # GST/HST, recargos de entrega/medioambiente (≈9-15 $/m³) ni cargas
    # cortas. Las guías «SEO» que anuncian 175-225 $/m³ entregado quedan por
    # debajo de ambas listas y no se adoptan.
    "MT-CONC-180": ref(245, 225, 285, R_CA,
                       observaciones="Hormigón premezclado ≈20 MPa (180 kg/cm² ≈ 17,7 MPa). "
                                     "Listas de planta GTA 2026: 15 MPa 235-246 $/m³ y "
                                     "20 MPa 240-254 $/m³ (CBM / Ontario Redi-Mix)."),
    "MT-CONC-210": ref(255, 235, 295, R_CA,
                       observaciones="Hormigón premezclado ≈20-25 MPa (210 kg/cm² ≈ 20,6 MPa), "
                                     "interpolado entre los grados de las listas GTA 2026."),
    "MT-CONC-250": ref(260, 240, 300, R_CA,
                       observaciones="Hormigón premezclado 25 MPa (250 kg/cm² ≈ 24,5 MPa), el "
                                     "grado residencial estándar: 245 $/m³ (CBM GTA) a "
                                     "266 $/m³ (Ontario Redi-Mix) en lista 2026."),
    "MT-CONC-300": ref(270, 250, 310, R_CA,
                       observaciones="Hormigón premezclado 30 MPa (300 kg/cm² ≈ 29,4 MPa): "
                                     "255-275 $/m³ en las listas de planta GTA 2026."),
    "MT-CEMENTO": ref(0.56, 0.50, 0.62, R_CA,
                      observaciones="Cemento Portland GU en saco de 40 kg: 19,99-24,68 $ "
                                    "(Home Depot, Turkstra, IHL; guía HBS 2026: 21,90 $) "
                                    "→ 0,50-0,62 $/kg. Precio sin impuestos."),
    "MT-ARENA": ref(79, 60, 100, R_CA,
                    observaciones="Arena de hormigón a granel a 60,16 $/yd³ (guía HBS "
                                  "2026, Hamilton ON) × 1,308 yd³/m³ ≈ 79 $/m³, recogida "
                                  "en patio; el reparto en volqueta la mueve en la banda."),
    "MT-PIEDRA-PIC": ref(95, 75, 120, R_CA,
                         observaciones="Piedra triturada de 3/4\" (19 mm clear stone) a "
                                       "72,50 $/yd³ (guía HBS 2026) × 1,308 ≈ 95 $/m³."),
    "MT-MAT-PRESTAMO": ref(72, 55, 95, R_CA,
                           observaciones="Material granular de base (Granular A) a "
                                         "54,12 $/yd³ (guía HBS 2026) × 1,308 ≈ 71 $/m³."),
    "MT-AGUA-OBRA": ref(4.70, 3.80, 5.60, R_CA,
                        confianza="derivado",
                        observaciones="Agua de obra: tarifas municipales medidas de "
                                      "Ontario (agua + alcantarillado ≈4-5 $/m³ en 2026)."),
    "MT-ADITIVO": ref(4.50, 3.20, 6.00, R_CA,
                      confianza="derivado",
                      observaciones="Plastificante de mortero/hormigón en envase de 4-20 l "
                                    "de comercio canadiense; sin precio por litro publicado."),
    "MT-CURADOR": ref(6.00, 4.50, 7.50, R_CA,
                      confianza="derivado",
                      observaciones="Compuesto de curado en bidón de 20 l (Sika/W.R. Meadows "
                                    "vía HBS); estimación por litro."),
    "MT-DESMOLD": ref(6.50, 5.00, 8.50, R_CA,
                      confianza="derivado",
                      observaciones="Desmoldante (form release) en envase de 20 l de "
                                    "comercio canadiense; estimación por litro."),
    # ── Acero ────────────────────────────────────────────────────────────────
    "MT-ACERO-CAB": ref(2.00, 1.80, 2.20, R_CA,
                        observaciones="Barra corrugada 15M suministrada en el GTA a "
                                      "1.800-2.200 $/t (guía de mercado de Ontario, "
                                      "jul-2026). La fabricación y colocación van aparte."),
    "MT-MALLA-ELEC": ref(7.50, 5.50, 10.00, R_CA,
                         observaciones="Malla electrosoldada 6×6 W2.9 en hoja de 4×8 ft "
                                       "(2,97 m²): 19,22 $ (HBS 2025) a 25-40 $ (GTA 2026) "
                                       "→ ≈6,5-13 $/m²; adoptada la banda de suministro."),
    "MT-PERFIL-ACERO": ref(2.80, 2.30, 3.40, R_CA,
                           confianza="derivado",
                           observaciones="Perfil W de suministro en almacén de acero "
                                         "canadiense, estimado por kg (sin fabricación)."),
    "MT-PLANCHA-ACERO": ref(3.10, 2.50, 3.90, R_CA,
                            confianza="derivado",
                            observaciones="Chapa de acero estimada sobre el perfil de "
                                          "almacén canadiense; sin lista pública por kg."),
    "MT-FORM-MADERA": ref(10.00, 8.00, 12.50, R_CA,
                          confianza="derivado",
                          observaciones="Encofrado de madera amortizado (≈8 usos): "
                                        "contrachapado de encofrado y madera SPF "
                                        "prorrateados por uso. No es precio de compra."),
    "MT-POLIET": ref(0.55, 0.40, 0.80, R_CA,
                     confianza="derivado",
                     observaciones="Lámina de polietileno de 6 mil («poly sheeting») en "
                                   "rollo de comercio canadiense, por m²."),
    # ── Fábrica y bloques ────────────────────────────────────────────────────
    # Formato canadiense CMU de 390×190 mm (series 90/140/190 = 4"/6"/8"):
    # mismo bloque funcional que el del recurso (12,5 ud/m² de muro).
    "MT-BLQ-20": ref(4.40, 3.90, 5.20, R_CA,
                     observaciones="Bloque hueco de 8\" (190 mm) a 4,19 $ (Chamberlain "
                                   "Timber Mart, ON) llevado a 2026; la estantería ON "
                                   "se mueve en 3,90-5,20 $."),
    "MT-BLQ-15": ref(3.80, 3.30, 4.50, R_CA,
                     confianza="derivado",
                     observaciones="Bloque de 6\" (140 mm): estimado por proporción de "
                                   "material sobre el de 8\" observado."),
    "MT-BLQ-10": ref(3.30, 2.80, 4.00, R_CA,
                     confianza="derivado",
                     observaciones="Bloque de 4\" (90 mm): estimado por proporción de "
                                   "material sobre el de 8\" observado."),
    "MT-LADRILLO-VISTO": ref(0.95, 0.70, 1.30, R_CA,
                             confianza="derivado",
                             observaciones="Ladrillo caravista de arcilla modular. Los "
                                           "fabricantes ca (Brampton Brick) cotizan por "
                                           "cuenta; banda de mercado norteamericana por "
                                           "unidad entregada en obra."),
    # ── Yeso laminado y tabiquería ───────────────────────────────────────────
    "MT-PYL-PLACA125": ref(5.55, 4.70, 6.60, R_CA,
                           observaciones="Placa CGC Sheetrock de 1/2\" (12,5 mm), hoja "
                                         "4×8 ft (2,97 m²) a 16,52 $ en Home Depot Canadá "
                                         "y 14-18 $ en guías del GTA (jul-2026) "
                                         "→ 4,7-6,1 $/m²."),
    "MT-PYL-PLACA": ref(6.80, 5.80, 8.20, R_CA,
                        confianza="derivado",
                        observaciones="Placa de 5/8\" (15,9 mm): estimada sobre la hoja "
                                      "de 1/2\" observada."),
    "MT-PYL-PLACA-IG": ref(7.20, 6.10, 8.60, R_CA,
                           confianza="derivado",
                           observaciones="Placa cortafuego Type X de 5/8\", estimada "
                                         "sobre la gama CGC canadiense."),
    "MT-PYL-PLACA-RH": ref(8.50, 7.20, 10.20, R_CA,
                           confianza="derivado",
                           observaciones="Placa resistente a humedad/moho (Mold Tough), "
                                         "estimada sobre la gama CGC canadiense."),
    "MT-PYL-PLACA-HD": ref(9.00, 7.60, 10.80, R_CA,
                           confianza="derivado",
                           observaciones="Placa de abuso/impacto, estimada sobre la "
                                         "gama CGC canadiense."),
    "MT-PLACA-CEM": ref(14.00, 11.50, 17.00, R_CA,
                        confianza="derivado",
                        observaciones="Placa de cemento tipo Durock en hoja de 3×5 ft "
                                      "(1,39 m²) de comercio canadiense, por m²."),
    "MT-PYL-MONT": ref(2.60, 2.20, 3.20, R_CA,
                       confianza="derivado",
                       observaciones="Montante metálico de 3-5/8\" cal. 25 en largos de "
                                     "10 ft de comercio canadiense, por metro; sin "
                                     "tarifa pública capturada en este corte."),
    "MT-PYL-CANAL": ref(2.40, 2.00, 3.00, R_CA,
                        confianza="derivado",
                        observaciones="Canal (track) de 3-5/8\" cal. 25, en línea con el "
                                      "montante."),
    "MT-PYL-PASTA": ref(1.50, 1.25, 1.90, R_CA,
                        observaciones="Compuesto de juntas premezclado CGC All-Purpose "
                                      "Lite, cubo de 17 l a 31,75 $ (≈23 kg) en Home "
                                      "Depot Canadá → ≈1,4 $/kg."),
    "MT-PYL-PASTA-AGARRE": ref(2.70, 2.30, 3.20, R_CA,
                               observaciones="Equivalente canadiense de fraguado "
                                             "químico: CGC Durabond 90 en saco de 15 kg "
                                             "a 40,88 $ → 2,73 $/kg."),
    "MT-MALLA-ESQ": ref(0.95, 0.75, 1.25, R_CA,
                        confianza="derivado",
                        observaciones="Cantonera metálica (corner bead) de 8-10 ft de "
                                      "comercio canadiense, por metro."),
    "MT-YESO-REP": ref(2.60, 2.00, 3.40, R_CA,
                       confianza="derivado",
                       observaciones="Masilla/yeso de reparación de comercio "
                                     "canadiense, por kg."),
    "MT-PYL-LANA": ref(10.00, 8.40, 11.60, R_CA,
                       observaciones="Paneles de fibra de vidrio R-20: material a "
                                     "0,78-1,08 $/ft² en Ontario (2026) "
                                     "→ 8,4-11,6 $/m²."),
    # ── Adhesivos, juntas y nivelación ───────────────────────────────────────
    "MT-ADH-C2TE": ref(1.50, 1.30, 1.80, R_CA,
                       observaciones="Adhesivo premium de gran formato MAPEI Ultraflex "
                                     "LFT, saco de 50 lb (22,7 kg) a 34,30 $ en Home "
                                     "Depot Canadá → 1,51 $/kg."),
    "MT-ADH-C1": ref(0.90, 0.75, 1.10, R_CA,
                     observaciones="Adhesivo modificado estándar VersaBond, saco de "
                                   "50 lb (22,7 kg) a 19,98 $ en Home Depot Canadá "
                                   "→ 0,88 $/kg."),
    "MT-JUN-CG2": ref(4.50, 2.80, 6.90, R_CA,
                      observaciones="Mortero de juntas polimérico Polyblend Plus: "
                                    "formatos de 7-10 lb a 22,86-31,18 $ en Home Depot "
                                    "Canadá (6,9-7,2 $/kg minorista); el formato trade "
                                    "de 25 lb baja el kilo a la banda adoptada."),
    "MT-AUT-NIV": ref(1.70, 1.60, 1.85, R_CA,
                      observaciones="Autonivelante de 50 lb (22,7 kg): LevelQuik a "
                                    "36,98 $ y Sika Level-125CA a 40,38 $ en Home "
                                    "Depot Canadá → 1,63-1,78 $/kg."),
    "MT-IMP-PRIM": ref(9.00, 6.50, 12.00, R_CA,
                       confianza="derivado",
                       observaciones="Imprimación de agarre en envase de 3,78 l de "
                                     "comercio canadiense."),
    "MT-GROUT": ref(1.15, 0.95, 1.40, R_CA,
                    observaciones="Grout expansivo Quikrete de 22,7 kg a 26,55 $ en "
                                  "Home Depot Canadá → 1,17 $/kg."),
    "MT-GROUT-CELDA": ref(275, 250, 310, R_CA,
                          confianza="derivado",
                          observaciones="Grout fluido de relleno de celdas de bloque "
                                        "(core-fill grout) por m³: se valora como un "
                                        "premezclado bombeable de 25-30 MPa, en línea "
                                        "con MT-CONC-300. El factor de la familia "
                                        "MT-GROUT (sacos) daría un precio sin sentido "
                                        "por m³."),
    "MT-TORN": ref(0.018, 0.012, 0.026, R_CA,
                   confianza="derivado",
                   observaciones="Tornillos de placa en caja de 1.000 de comercio "
                                 "canadiense → ≈0,02 $/ud."),
    "MT-SIL-SAN": ref(12.50, 9.00, 15.50, R_CA,
                      confianza="derivado",
                      observaciones="Silicona sanitaria en cartucho de ≈300 ml de "
                                    "comercio canadiense; sin precio capturado en "
                                    "este corte."),
    # ── Pinturas y tratamientos de madera ────────────────────────────────────
    "MT-PIN-CAUCHO": ref(15.50, 12.00, 20.00, R_CA,
                         observaciones="Pintura látex interior estándar a 60-80 $/galón "
                                       "(3,78 l) en 2026 → 15,9-21,2 $/l; la línea de "
                                       "contratista baja a 40-55 $/galón. Adoptado el "
                                       "tramo medio por litro."),
    "MT-PIN-SEMIBRILLO": ref(19.00, 15.00, 24.00, R_CA,
                             confianza="derivado",
                             observaciones="Gama semibrillo premium, sobre la banda "
                                           "interior observada (las líneas premium "
                                           "llegan a 80-120 $/galón exterior)."),
    "MT-PIN-ESMALTE": ref(20.00, 15.00, 26.00, R_CA,
                          confianza="derivado",
                          observaciones="Esmalte alquídico en envase de 3,78 l de "
                                        "comercio canadiense."),
    "MT-ESMALTE-AGUA": ref(21.00, 16.00, 27.00, R_CA,
                           confianza="derivado",
                           observaciones="Esmalte acrílico al agua en envase de 3,78 l "
                                         "de comercio canadiense."),
    "MT-PIN-FONDO": ref(12.00, 8.50, 17.00, R_CA,
                        confianza="derivado",
                        observaciones="Fondo/imprimación (primer) en envase de 3,78 l."),
    "MT-PIN-MASILLA": ref(7.00, 5.00, 9.50, R_CA,
                          confianza="derivado",
                          observaciones="Masilla lista al uso por kg de comercio "
                                        "canadiense."),
    "MT-PIN-CAL": ref(0.50, 0.38, 0.70, R_CA,
                      confianza="derivado",
                      observaciones="Cal hidratada en saco de ≈22,7 kg; el factor de la "
                                    "familia de pinturas daría un precio absurdo para "
                                    "un mineral a granel."),
    "MT-BARNIZ-MARINO": ref(26.00, 20.00, 34.00, R_CA,
                            confianza="derivado",
                            observaciones="Barniz exterior por litro en envase de "
                                          "0,946-3,78 l."),
    "MT-LASUR": ref(17.00, 13.00, 22.00, R_CA,
                    confianza="derivado",
                    observaciones="Protector/lasur de madera exterior (deck stain) en "
                                  "envase de 3,78 l."),
    "MT-TINTE-MAD": ref(19.00, 14.00, 25.00, R_CA,
                        confianza="derivado",
                        observaciones="Tinte de madera interior por litro."),
    # ── Fontanería ───────────────────────────────────────────────────────────
    # Nota de mercado: en Canadá el PPR es residual; el equivalente
    # funcional es el PEX de 1/2"-3/4" (y el cobre). El desagüe estándar es
    # ABS negro, no PVC.
    "MT-PLO-PPR20": ref(1.25, 1.05, 1.60, R_CA,
                        observaciones="Tubo PEX de 1/2\": bobina de 100 ft (30,5 m) a "
                                      "37,95 $ (Apollo) y de 300 ft a 99 $ en Home "
                                      "Depot Canadá → 1,08-1,24 $/m; el PEX-A "
                                      "(SharkBite) sube a 1,87 $/m."),
    "MT-PLO-ACC20": ref(3.80, 2.50, 5.50, R_CA,
                        confianza="derivado",
                        observaciones="Accesorios PEX de latón de 1/2\" (codos, tes) de "
                                      "comercio canadiense; precio medio por pieza."),
    "MT-PLO-PVC4": ref(11.00, 8.00, 14.50, R_CA,
                       confianza="derivado",
                       observaciones="Equivalente canadiense: tubería ABS DWV de 4\" "
                                     "(100 mm) en largos de 10-12 ft. En Canadá el "
                                     "desagüe interior estándar es ABS, no PVC."),
    "MT-PLO-ACC4": ref(8.50, 5.00, 16.00, R_CA,
                       confianza="derivado",
                       observaciones="Accesorios ABS DWV de 4\" (codos, tes, yes) de "
                                     "comercio canadiense; precio medio de pieza "
                                     "corriente."),
    # El factor de la familia MT-PLO sale del tubo PEX (muy barato por
    # metro en Canadá) y dejaría las piezas de latón y los kits por debajo
    # de cualquier estantería: precio explícito para las tres corrientes.
    "MT-PLO-LLAVE": ref(7.50, 5.50, 10.50, R_CA,
                        confianza="derivado",
                        observaciones="Llave de paso de esfera PEX de 1/2\" de latón "
                                      "de comercio canadiense. El factor de la "
                                      "familia (tubo PEX) daría ≈3,8 $, por debajo "
                                      "del precio de la pieza."),
    "MT-PLO-ABASTO": ref(9.00, 6.50, 12.50, R_CA,
                         confianza="derivado",
                         observaciones="Latiguillo trenzado de abasto con racores "
                                       "(braided supply line) de comercio "
                                       "canadiense."),
    "MT-PLO-DESAG": ref(14.00, 10.00, 19.00, R_CA,
                        confianza="derivado",
                        observaciones="Kit de desagüe de aparato (sifón ABS tipo P "
                                      "con brazo) de comercio canadiense."),
    # ── Electricidad ─────────────────────────────────────────────────────────
    "MT-ELE-CAJA": ref(2.80, 1.90, 4.20, R_CA,
                       confianza="derivado",
                       observaciones="Caja de mecanismo (device box) de acero/PVC de "
                                     "comercio eléctrico canadiense."),
    "MT-ELE-CABLE": ref(2.50, 1.90, 3.20, R_CA,
                        observaciones="Cable NMD90 (equivalente al twin & earth): la "
                                      "bobina 14/2 de 150 m cuesta 228-270 $ en Home "
                                      "Depot Canadá (1,52-1,80 $/m); el recurso ≈2,5 mm² "
                                      "se valora como el 12/2, ≈45 % por encima."),
    "MT-ELE-MECA": ref(9.50, 6.00, 15.00, R_CA,
                       confianza="derivado",
                       observaciones="Mecanismo tomacorriente dúplex TR con placa "
                                     "(Leviton/Hubbell) de comercio eléctrico "
                                     "canadiense."),
    # ── Aislamiento, drenaje e impermeabilización ────────────────────────────
    "MT-POLIESTIRENO-EXT": ref(23.00, 19.00, 28.00, R_CA,
                               confianza="derivado",
                               observaciones="Panel XPS de 2\" (50 mm) 4×8 ft de "
                                             "comercio canadiense, por m² de hoja."),
    "MT-LANA-ROCA": ref(17.00, 14.50, 19.90, R_CA,
                        observaciones="Paneles de lana mineral R-20: material a "
                                      "1,35-1,85 $/ft² en Ontario (2026) "
                                      "→ 14,5-19,9 $/m²."),
    "MT-GEOTEXTIL": ref(1.20, 0.80, 1.90, R_CA,
                        confianza="derivado",
                        observaciones="Geotextil de drenaje en rollo de distribuidor "
                                      "canadiense, por m²."),
    "MT-TUBO-DREN": ref(5.75, 5.00, 6.60, R_CA,
                        observaciones="Tubo de drenaje corrugado de 4\" («weeping "
                                      "tile») perforado a 1,73-1,75 $/ft (guía HBS "
                                      "2026) → 5,7 $/m; con filtro, 2,00 $/ft "
                                      "(6,6 $/m)."),
    # ── Madera y tableros ────────────────────────────────────────────────────
    "MT-MADERA-EST": ref(620, 500, 780, R_CA,
                         confianza="derivado",
                         observaciones="SPF estructural: el precio de molino/guía del "
                                       "2×6 (700-900 $/MBF, GTA jul-2026) equivale a "
                                       "≈300-380 $/m³ nominal; con margen de patio y "
                                       "sección real se adopta 620 $/m³. Canadá es "
                                       "productor: la madera es el material "
                                       "estructural barato del mercado."),
    "MT-MADERA-LISTON": ref(1.90, 1.55, 2.30, R_CA,
                            observaciones="Listón SPF 2×4 (38×89 mm): a 700-900 $/MBF el "
                                          "pie de 8 ft (5,33 bf) sale a 3,73-4,80 $ → "
                                          "1,53-1,97 $/m; la estantería ON se mueve "
                                          "en la banda adoptada."),
    "MT-MADERA-PERGOLA": ref(11.00, 8.00, 16.00, R_CA,
                             confianza="derivado",
                             observaciones="Madera tratada a presión para pérgola "
                                           "(postes 6×6 y vigas 2×6/2×8): el "
                                           "factor de la familia sale del listón "
                                           "SPF sin tratar y la infravaloraría."),
    "MT-LAMINA-OSB": ref(9.50, 7.50, 12.50, R_CA,
                         confianza="derivado",
                         observaciones="OSB estructural de 7/16\"-3/4\" en hoja de "
                                       "4×8 ft de comercio canadiense, por m²."),
    # ── Residuos ─────────────────────────────────────────────────────────────
    # Sin levy provincial al estilo NSW: el canon sale del precio del bin
    # (contenedor roll-off) del GTA con su tonelaje incluido y el exceso a
    # 120-130 $/t. La tierra está regulada (O. Reg. 406/19, exceso de suelo)
    # y no es el renglón barato.
    "MT-CANON": ref(60, 45, 85, R_CA,
                    observaciones="Retirada de escombro mezclado por m³ vía bin de "
                                  "14 yd³ (10,7 m³) a 439 $ con 2 t incluidas y "
                                  "exceso a 120-130 $/t (tarifas públicas del GTA, "
                                  "2026): una carga típica de ≈3,5 t sale a "
                                  "≈58 $/m³ (con HST serían ≈65)."),
    "MT-CANON-TIERRA": ref(70, 50, 100, R_CA,
                           confianza="derivado",
                           observaciones="Tierra limpia vía bin de carga única "
                                         "(5 yd³ a ≈359 $/carga en el GTA) y gestión "
                                         "del exceso de suelo (O. Reg. 406/19 de "
                                         "Ontario); coste por m³ suelto equivalente."),
}


# ─────────────────────────────────────────────────────────────────────────────
# 4. Ensamblado
# ─────────────────────────────────────────────────────────────────────────────

def _familia(codigo: str) -> str:
    """Familia de mercado: el prefijo del código, con un mínimo de dos tramos."""
    partes = codigo.split("-")
    if len(partes) < 2:
        return codigo
    return "-".join(partes[:2])


def _construir_referencias() -> dict[str, dict[str, Referencia]]:
    referencias: dict[str, dict[str, Referencia]] = {}
    referencias.update(referencias_mano_obra())
    for codigo, dato in MAQUINARIA.items():
        referencias[codigo] = {"CA": dato}
    for codigo, dato in MATERIALES.items():
        if codigo in referencias:
            raise ValueError(f"{codigo} definido dos veces")
        referencias[codigo] = {"CA": dato}
    return referencias


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


def derivar_referencias(data, referencias):
    """Cubre los recursos sin observación con un factor por familia.

    El factor es la mediana de (precio canadiense investigado / precio base
    convertido) de las anclas de esa familia. Si la familia no tiene anclas
    se usa la mediana de la categoría, y si aun así no hubiera anclas, la
    mediana global de la categoría calculada sobre todas las anclas.
    """
    fichas = {c: (cat, item) for c, cat, item in iter_recursos(data)}

    # Factores por (categoría, familia)
    por_familia: dict[tuple[str, str], list[float]] = {}
    por_categoria: dict[str, list[float]] = {}
    for codigo, por_pais in referencias.items():
        ficha = fichas.get(codigo)
        dato = por_pais.get("CA")
        if ficha is None or dato is None or dato.confianza != "referencia":
            continue
        categoria = ficha[0]
        if categoria == "mano_obra":
            continue
        base_local = float(ficha[1]["precio"]) * TASAS_CORTE["CA"]
        if base_local <= 0:
            continue
        razon = dato.precio / base_local
        por_categoria.setdefault(categoria, []).append(razon)
        por_familia.setdefault((categoria, _familia(codigo)), []).append(razon)

    factores_familia = {k: statistics.median(v) for k, v in por_familia.items()}
    factores_categoria = {k: statistics.median(v) for k, v in por_categoria.items()}

    derivados = 0
    for codigo, categoria, item in iter_recursos(data):
        if categoria == "mano_obra":
            continue
        if referencias.get(codigo, {}).get("CA") is not None:
            continue
        base_local = float(item["precio"]) * TASAS_CORTE["CA"]
        factor = factores_familia.get((categoria, _familia(codigo)))
        origen = f"familia {_familia(codigo)}"
        if factor is None:
            factor = factores_categoria[categoria]
            origen = f"categoría {categoria}"
        referencias.setdefault(codigo, {})["CA"] = replace(
            ref(base_local * factor, base_local * factor * 0.80,
                base_local * factor * 1.25, METODOLOGIA,
                confianza="derivado", observaciones=OBS_DERIVADO),
            observaciones=f"{OBS_DERIVADO} Factor {factor:.3f} de la {origen}.",
        )
        derivados += 1
    return factores_familia, factores_categoria, derivados


def _numero(valor: float) -> str:
    return f"{valor:.6f}".rstrip("0").rstrip(".")


def main() -> int:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    referencias = _construir_referencias()
    factores_familia, factores_categoria, derivados = derivar_referencias(data, referencias)

    filas = []
    for codigo, categoria, item in iter_recursos(data):
        dato = referencias.get(codigo, {}).get("CA")
        if dato is None:
            raise SystemExit(f"Sin referencia para {codigo}")
        filas.append({
            "codigo_recurso": codigo,
            "descripcion": item["descripcion"],
            "categoria": categoria,
            "unidad_fuente": item["unidad"],
            "pais_codigo": "CA",
            "moneda": "CAD",
            "precio_referencia": _numero(dato.precio),
            "precio_min": _numero(dato.minimo),
            "precio_max": _numero(dato.maximo),
            "fuente": dato.fuente,
            "fecha_consulta": FECHA,
            "confianza": dato.confianza,
            "incluye_iva": dato.incluye_iva,
            "incluye_transporte": dato.incluye_transporte,
            "origen": "nacional",
            "observaciones": dato.observaciones,
        })

    campos = list(filas[0].keys())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=campos, delimiter=";")
        w.writeheader()
        w.writerows(filas)

    total = len(filas)
    investigados = sum(1 for f in filas if f["confianza"] == "referencia")
    print(f"Matriz canadiense escrita en {OUT.relative_to(ROOT)}")
    print(f"  {total} recursos · {investigados} investigados "
          f"({investigados / total:.0%}) · {derivados} derivados por factor")
    print(f"  tasa de corte: 1 USD = {TASAS_CORTE['CA']:.4f} CAD (Banco de Canadá, 16/10/2026)")
    print()
    print("  Factores por categoría (mediana de precio canadiense / base convertida):")
    for categoria, factor in sorted(factores_categoria.items()):
        print(f"    {categoria:12s} {factor:8.3f}")
    print()
    print(f"  Familias con ancla propia: {len(factores_familia)}")
    for (categoria, familia), factor in sorted(factores_familia.items()):
        n = len([1 for c, d in referencias.items()
                 if d.get("CA") and d["CA"].confianza == "referencia"
                 and _familia(c) == familia and c in
                 {x for x, cat, _ in iter_recursos(data) if cat == categoria}])
        print(f"    {familia:22s} {factor:8.3f}  ({n} anclas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
