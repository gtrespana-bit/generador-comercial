#!/usr/bin/env python3
"""Genera la matriz de precios de recursos para Australia (AUD).

Replica el contrato de ``generar_matriz_precios_irlanda.py``:

* Los precios base de ``basedatos_partidas/datos/recursos.json`` están en USD
  con ámbito **Venezuela**. No son precios internacionales, así que ninguna
  conversión de divisa puede producir un precio australiano. La matriz se
  construye desde precios australianos reales.
* Las anclas investigadas se publican tal cual, con rango, fuente y fecha.
* El resto se cubre con un **factor de mercado por familia**, calculado como
  la mediana de la relación entre el precio australiano investigado y el
  precio base de cada ancla de esa familia.
* La mano de obra no usa factores: los 17 oficios salen del modelo de coste
  empresa de ``coste_empresa_australia.py``.

Particularidades de Australia frente a España, el Reino Unido e Irlanda:

* El GST es único (10 %) y el comercio minorista (Bunnings) publica con GST:
  la cifra sin GST se obtiene dividiendo por 1,1 y así se declara en la
  observación de cada ancla. El comercio profesional (Reece, Tradelink,
  Lawrence & Hanson, Coates, Kennards) **no publica precios**: trabaja con
  cuentas y cotizaciones. Por eso la canasta observada (15 %) es menor que
  la irlandesa (27 %) y hay más anclas «derivado» con precio explícito y
  analogía documentada — se prefiere eso a fingir una observación.
* El residuo es el renglón más caro del mundo anglófono: el waste levy de
  NSW (180,20 $/t en el área metropolitana desde el 1/07/2026, el mayor del
  país) hace que un skip de 6 m³ en Sídney cueste 845-911 $.
* La mano de obra parte del mínimo legal nacional (awards de la Fair Work
  Commission), así que el rango no baja un 10 % como en el Reino Unido:
  −3 % / +20 %, igual que en Irlanda.
* Equivalencias de mercado declaradas: el PPR es residual (se usa PEX y
  cobre), el bloque es el «besser block» de 390×190 mm (series 90/140/190),
  la placa estándar es de 10-13 mm y el OSB apenas se usa (contrachapado).

Uso:
    python3 tools/generar_matriz_precios_australia.py
"""
from __future__ import annotations

import csv
import json
import statistics
from dataclasses import dataclass, replace
from pathlib import Path

from coste_empresa_australia import (
    HORAS_FACTURABLES,
    OFICIOS,
    coste_empresa,
)

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "basedatos_partidas/datos/recursos.json"
OUT = ROOT / "basedatos_partidas/salida/precios_recursos_australia.csv"
PAISES = (("AU", "AUD"),)
FECHA = "2026-10-19"

R_AU = "docs/INVESTIGACION_PRECIOS_AUSTRALIA.md"
METODOLOGIA = "docs/METODOLOGIA_PRECIOS_REFERENCIA_AUSTRALIA.md"
# Tipo del Banco de la Reserva de Australia del 16/10/2026: AUD/USD 0,6947
# -> 1 USD = 1,4395 AUD (el mismo corte que app/services/tasa.py).
# Solo normaliza el precio base antes de aplicar el factor de mercado; el
# resultado queda congelado en AUD y con fecha.
TASAS_CORTE = {"AU": 1.4395}

OBS_REFERENCIA = (
    "Precio de mercado australiano observado (sin GST, sin porte salvo indicación); "
    "puede variar por proveedor, marca, volumen y estado."
)
OBS_DERIVADO = (
    "Precio referencial derivado del factor de mercado de su familia, calculado "
    "sobre la canasta australiana investigada; no es una cotización de tienda."
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


def ref(precio, minimo, maximo, fuente=R_AU, **kwargs) -> Referencia:
    precio, minimo, maximo = map(float, (precio, minimo, maximo))
    if minimo <= 0 or maximo < minimo or not minimo <= precio <= maximo:
        raise ValueError(f"Rango inválido: {minimo} <= {precio} <= {maximo}")
    return Referencia(precio, minimo, maximo, fuente, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Mano de obra — modelo de coste empresa australiano
# ─────────────────────────────────────────────────────────────────────────────

def referencias_mano_obra() -> dict[str, dict[str, Referencia]]:
    salida: dict[str, dict[str, Referencia]] = {}
    for codigo, (oficio, salario, escala) in OFICIOS.items():
        coste = coste_empresa(salario)["coste_hora_facturable"]
        # El rango refleja la dispersión entre estados y entre award y EBA:
        # −3 % (el salario es el mínimo legal nacional y no admite la rebaja
        # del 10 % usada en el Reino Unido) y +20 % (Sídney y obra comercial
        # con convenio de empresa pagan muy por encima del award).
        salida[codigo] = {
            "AU": ref(
                coste,
                coste * 0.97,
                coste * 1.20,
                R_AU,
                confianza="referencia",
                incluye_iva="no_aplica",
                incluye_transporte="no_aplica",
                observaciones=(
                    f"Coste empresa por hora trabajada. {oficio}. Salario "
                    f"ordinario {salario:.2f} $/h ({escala}) × 1.976 h pagadas "
                    f"+ superannuation 12 %, workers comp NSW 4,95 %, leave "
                    f"loading 17,5 %, travel 22,41 $/día y provisión de long "
                    f"service leave, dividido por {HORAS_FACTURABLES:,.0f} h "
                    f"trabajadas/año (211 días de 8 h tras vacaciones, festivos "
                    f"y RDO). No es tarifa de subcontrata: el catálogo ya "
                    f"aplica un 35 % de margen sobre el coste directo."
                ),
            )
        }
    return salida


# ─────────────────────────────────────────────────────────────────────────────
# 2. Maquinaria — tarifas de alquiler australianas
#
#    Coates y Kennards no publican tarifas (cotizan por cuenta), así que las
#    anclas «referencia» salen de catálogos públicos de hire regionales con
#    precio por día (Elimbah Hire, Perth Hills Hire, STK Hire) y de las
#    guías de iseekplant/hireseeking. El resto se publica «derivado» con
#    precio explícito por analogía documentada. Día de 8 h, sin GST ni
#    combustible; con operador solo donde se indica (bomba, grúa,
#    perforadora, volqueta).
# ─────────────────────────────────────────────────────────────────────────────

def _alquiler(dia, minimo, maximo, nota="", confianza="referencia") -> Referencia:
    return ref(
        dia / 8.0, minimo / 8.0, maximo / 8.0, R_AU,
        confianza=confianza,
        observaciones=(
            f"Alquiler australiano {minimo:.0f}-{maximo:.0f} $/día (jornada de 8 h), "
            f"sin GST ni combustible. {nota}".strip()
        ),
    )


MAQUINARIA: dict[str, Referencia] = {
    # Corte y demolición
    "MQ-CORT-AGUA": _alquiler(95, 75, 120, "Sierra de banco húmeda para cerámica; "
                              "sin tarifa pública localizada: analogía con la "
                              "banda de sierras de los catálogos de hire.",
                              confianza="derivado"),
    "MQ-ROZAD": _alquiler(110, 90, 140, "Rozadora (wall chaser); analogía con "
                          "equipo de corte con aspiración.", confianza="derivado"),
    "MQ-MART-ELEC": _alquiler(80, 65, 110, "Martillo demoledor de mano de 5 kg; el "
                              "jackhammer pesado de suelo llega a 210 $/día con GST "
                              "(Perth Hills Hire)."),
    "MQ-AMOLA": _alquiler(48, 38, 60, "Amoladora angular de 230 mm.",
                          confianza="derivado"),
    "MQ-SIERRA": _alquiler(60, 45, 95, "Sierra circular a motosierra de gasolina.",
                           confianza="derivado"),
    "MQ-OXICORTE": _alquiler(85, 65, 110, "Equipo de oxicorte con botellas.",
                             confianza="derivado"),
    "MQ-CIZALLA": _alquiler(95, 75, 125, "Cizalla/dobladora de barra (reo cutter-"
                            "bender de hire especializado).", confianza="derivado"),
    "MQ-ESMERIL": _alquiler(120, 95, 150, "Amoladora de suelo de mano a 145 $/día "
                            "con GST (Perth Hills Hire) → 132 $ sin GST."),
    # Hormigón
    "MQ-MEZCL": _alquiler(65, 55, 90, "Hormigonera eléctrica: 65 $/día + GST "
                          "(Elimbah Hire); la de 100 l llega a 140 $ con GST."),
    "MQ-BATID": _alquiler(55, 45, 75, "Batidora de paleta (paddle mixer).",
                          confianza="derivado"),
    "MQ-VIBRADOR": _alquiler(75, 60, 95, "Vibrador de aguja con unidad motriz.",
                             confianza="derivado"),
    "MQ-ALISADORA": _alquiler(130, 110, 160, "Alisadora helicóptero (power trowel).",
                              confianza="derivado"),
    "MQ-BOMBA-CONC": _alquiler(1250, 1000, 1600, "Bomba de línea **con operador**. "
                               "En Australia se cobra por salida (mínimos de "
                               "≈800 $) más $/m³ bombeado: jornada estimada.",
                               confianza="derivado"),
    "MQ-PROYECT-MORT": _alquiler(220, 170, 280, "Máquina de proyectar mortero/render "
                                 "con compresor.", confianza="derivado"),
    # Compactación y movimiento de tierras
    "MQ-COMPACT-SALTO": _alquiler(88, 75, 105, "Compactador de impacto (rammer).",
                                  confianza="derivado"),
    "MQ-PLANCHA-COMP": _alquiler(70, 60, 95, "Plancha compactadora: 70 $/día + GST "
                                 "(Elimbah Hire)."),
    "MQ-RETRO": _alquiler(470, 400, 560, "Miniexcavadora de 3,5 t en seco "
                          "(280-330 $/día + GST, STK Hire y guías) + martillo "
                          "hidráulico (≈150 $/día); el operador va en la mano de "
                          "obra de la partida."),
    "MQ-MART-NEUM": _alquiler(260, 220, 320, "Compresor de obra con martillo "
                              "neumático (jackhammer).", confianza="derivado"),
    "MQ-PERF-PILOTE": _alquiler(2800, 2300, 3500, "Equipo de perforación de pilotes "
                                "**con operador**; alquiler especializado por "
                                "proyecto, sin tarifa pública.", confianza="derivado"),
    # Elevación y acceso
    "MQ-ANDAMIO": _alquiler(120, 95, 160, "Torre móvil de andamio; como referencia "
                            "de la banda, la tijera de 19 ft se alquila a "
                            "180 $/día + GST (Elimbah Hire).", confianza="derivado"),
    "MQ-MONTAC": _alquiler(180, 140, 240, "Montacargas de material / tile lifter "
                           "de tejado.", confianza="derivado"),
    "MQ-VENT-SUC": _alquiler(45, 35, 60, "Juego de ventosas de elevación de gran "
                             "formato.", confianza="derivado"),
    "MQ-GRUA": _alquiler(1650, 1350, 2000, "Grúa móvil/Franna **con operador** "
                         "(wet hire ≈180-220 $/h en Sídney).", confianza="derivado"),
    # Instalaciones y acabados
    "MQ-ATORN": _alquiler(45, 35, 60, "Atornilladora para placa (screw gun).",
                          confianza="derivado"),
    "MQ-LIJAD": _alquiler(85, 70, 110, "Lijadora jirafa de pared con aspiración.",
                          confianza="derivado"),
    "MQ-PULIDORA": _alquiler(110, 90, 135, "Pulidora húmeda de piedra/hormigón a "
                             "120 $/día con GST (Perth Hills Hire)."),
    "MQ-LIJAD-PISO": _alquiler(140, 115, 175, "Lijadora de banda de pisos + "
                               "orilladora (juego).", confianza="derivado"),
    "MQ-ESTAMP": _alquiler(150, 120, 190, "Moldes de hormigón impreso.",
                           confianza="derivado"),
    "MQ-SOLDADORA": _alquiler(72, 58, 95, "Soldadora MIG/inverter de hire general.",
                              confianza="derivado"),
    "MQ-TERMOF": _alquiler(65, 50, 85, "La termofusión PPR es residual en Australia "
                           "(PEX de crimpado y cobre); analogía con herramienta de "
                           "fontanería.", confianza="derivado"),
    "MQ-DOBLAD-TUBO": _alquiler(45, 35, 60, "Dobladora de tubo de cobre y kit de "
                                "abocardado.", confianza="derivado"),
    "MQ-RECUP-GAS": _alquiler(120, 95, 155, "Recuperadora de refrigerante y bomba "
                              "de vacío.", confianza="derivado"),
    "MQ-INYECTORA": _alquiler(130, 100, 170, "Equipo de inyección de resinas a baja "
                              "presión.", confianza="derivado"),
    "MQ-RODILLO": _alquiler(25, 18, 35, "Equipo de aplicación: rodillos, brochas, "
                            "cubetas y escalera, amortizado.", confianza="derivado"),
    # Limpieza, achique y seguridad
    "MQ-ASPIR": _alquiler(70, 55, 90, "Aspirador industrial con filtro M/H.",
                          confianza="derivado"),
    "MQ-HIDROLAV": _alquiler(95, 78, 120, "Hidrolavadora de gasolina "
                             "(pressure washer).", confianza="derivado"),
    "MQ-BOMBA-ACHI": _alquiler(60, 48, 80, "Bomba sumergible de achique con "
                               "manguera.", confianza="derivado"),
    "MQ-DESBROZ": _alquiler(55, 45, 70, "Desbrozadora (brushcutter).",
                            confianza="derivado"),
    # Medición y detección
    "MQ-NIVEL-LASER": _alquiler(60, 50, 75, "Nivel láser rotativo: 65 $/día con GST "
                                "(Elimbah Hire) → 59 $ sin GST."),
    "MQ-DETECTOR": _alquiler(85, 65, 110, "Localizador de servicios enterrados (CAT).",
                             confianza="derivado"),
    "MQ-TALADRO": _alquiler(55, 45, 75, "Taladro percutor SDS.",
                            confianza="derivado"),
    "MQ-TELUROMETRO": _alquiler(110, 85, 145, "Medidor de resistencia de tierra y "
                                "equipo de comprobación eléctrica.",
                                confianza="derivado"),
    # Transporte
    "MQ-VOLQ": _alquiler(1150, 950, 1400, "Camión volqueta **con chofer** (tipper "
                         "wet hire ≈130-160 $/h en área metropolitana).",
                         confianza="derivado"),
    # Unidad distinta: el baño portátil se alquila por mes.
    "MQ-BANO-PORT": ref(
        240, 200, 290, R_AU,
        confianza="derivado",
        observaciones=(
            "Alquiler mensual de baño portátil de obra con mantenimiento "
            "(recurso medido en unidades, no en horas). Sin GST. Estimación "
            "de mercado (Sídney ≈220-300 $/mes con GST)."
        ),
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# 3. Materiales — precios de proveedor australiano
#
#    Todos los precios son «ex GST». Bunnings y el comercio minorista
#    publican con GST (10 %): la cifra sin GST divide por 1,1 y así se
#    declara. Sydney Building Materials, ARC y los mayoristas eléctricos
#    publican parte de su tarifa «ex GST» y se toman tal cual.
# ─────────────────────────────────────────────────────────────────────────────

MATERIALES: dict[str, Referencia] = {
    # ── Hormigón y áridos ────────────────────────────────────────────────────
    # Ningún productor (Boral, Hanson/Heidelberg, Holcim) publica lista: el
    # precio sale de los agregadores con tarifa por grado (MixHub, ago-2026,
    # Sídney) contrastados con las guías por estado (BuiltSimple). Material
    # en carga completa metropolitana, sin GST; el porte corto y la carga
    # parcial suben el m³ efectivo un 20-30 %.
    "MT-CONC-180": ref(300, 270, 340, R_AU,
                       observaciones="Hormigón premezclado N20 (180 kg/cm² ≈ 17,7 MPa). "
                                     "Sídney 320-340 $/m³ de material (MixHub, ago-2026); "
                                     "adoptado el tramo bajo-metropolitano sin GST."),
    "MT-CONC-210": ref(310, 280, 350, R_AU,
                       observaciones="Hormigón premezclado ≈ N20/N25 (210 kg/cm² ≈ 20,6 MPa), "
                                     "interpolado entre los grados australianos N20 y N25."),
    "MT-CONC-250": ref(325, 295, 370, R_AU,
                       observaciones="Hormigón premezclado N25 (250 kg/cm² ≈ 24,5 MPa), el "
                                     "grado residencial estándar: 340-370 $/m³ de material "
                                     "en Sídney (MixHub), 250-300 $ en guías por estado."),
    "MT-CONC-300": ref(355, 320, 400, R_AU,
                       observaciones="Hormigón premezclado N32 (300 kg/cm² ≈ 29,4 MPa): "
                                     "370-400 $/m³ de material en Sídney (MixHub, ago-2026)."),
    "MT-CEMENTO": ref(0.45, 0.41, 0.50, R_AU,
                      observaciones="Cemento GP/GB en saco de 20 kg: 9,01-10,70 $ con GST en "
                                    "Bunnings → 8,19-9,73 $ sin GST → 0,41-0,49 $/kg."),
    "MT-ARENA": ref(105, 85, 135, R_AU,
                    observaciones="Arena lavada a granel entregada en Sídney (≈70 $/t sin "
                                  "GST en carga de volqueta; el suministro de jardinería "
                                  "cobra 89-110 $/t con GST) × 1,5 t/m³."),
    "MT-PIEDRA-PIC": ref(98, 78, 125, R_AU,
                         observaciones="Árido triturado «blue metal» de 20 mm a ≈65 $/t sin "
                                       "GST a granel (91 $/t con GST en suministro menor, "
                                       "ANL) × 1,5 t/m³."),
    "MT-MAT-PRESTAMO": ref(126, 100, 160, R_AU,
                           observaciones="Road base de 20 mm a ≈60 $/t sin GST a granel "
                                         "(78-86 $/t con GST al por menor) × 2,1 t/m³ "
                                         "compactado."),
    "MT-AGUA-OBRA": ref(3.00, 2.50, 3.60, R_AU,
                        confianza="derivado",
                        observaciones="Agua de obra: tarifa de uso de Sydney Water "
                                      "(≈2,5-3,1 $/kL en 2025-26) por m³."),
    "MT-ADITIVO": ref(4.20, 3.00, 5.50, R_AU,
                      confianza="derivado",
                      observaciones="Plastificante de mortero/hormigón en envase de 5-20 l "
                                    "de comercio australiano; sin precio por litro publicado."),
    "MT-CURADOR": ref(5.50, 4.20, 7.00, R_AU,
                      confianza="derivado",
                      observaciones="Compuesto de curado en bidón de 20 l (Sika/Fosroc vía "
                                    "distribuidores AU); estimación por litro."),
    "MT-DESMOLD": ref(6.00, 4.50, 7.50, R_AU,
                      confianza="derivado",
                      observaciones="Desmoldante en envase de 20 l de comercio AU; "
                                    "estimación por litro."),
    # ── Acero ────────────────────────────────────────────────────────────────
    "MT-ACERO-CAB": ref(1.60, 1.35, 1.90, R_AU,
                        observaciones="Barra corrugada 500N: guías de mercado de "
                                      "1.000-1.400 $/t para grado ligero y precios por "
                                      "barra en comercio (≈2,2-2,4 $/kg minorista); se "
                                      "adopta la banda de suministro trade."),
    "MT-MALLA-ELEC": ref(6.30, 5.00, 8.50, R_AU,
                         observaciones="Malla SL72 de 6,0 × 2,4 m (14,4 m²): 79,20-106 $ "
                                       "con GST por hoja (VSV, SaveBuild, ARC) → "
                                       "5,0-6,7 $/m² sin GST; la SL82 sube a ≈8,5 $/m²."),
    "MT-PERFIL-ACERO": ref(2.60, 2.10, 3.20, R_AU,
                           confianza="derivado",
                           observaciones="Perfil UB/UC de suministro en almacén de acero "
                                         "AU, estimado por kg (sin fabricación)."),
    "MT-PLANCHA-ACERO": ref(2.90, 2.30, 3.60, R_AU,
                            confianza="derivado",
                            observaciones="Chapa de acero estimada sobre el perfil de "
                                          "almacén AU; sin lista pública por kg."),
    "MT-FORM-MADERA": ref(9.50, 7.50, 12.00, R_AU,
                          confianza="derivado",
                          observaciones="Encofrado de madera amortizado (≈8 usos): formply "
                                        "F17 y madera de comercio AU prorrateados por uso. "
                                        "No es precio de compra por m²."),
    "MT-POLIET": ref(0.60, 0.45, 0.85, R_AU,
                     confianza="derivado",
                     observaciones="Lámina de polietileno de 200 µm («builder's plastic / "
                                   "fortecon») en rollo de 200 m² de comercio AU."),
    # ── Fábrica y bloques ────────────────────────────────────────────────────
    # Formato australiano 390 × 190 mm (series 90/140/190); el recurso
    # describe 40 × 20 cm: mismo bloque funcional (12,5 ud/m² de muro).
    "MT-BLQ-10": ref(3.34, 2.90, 4.10, R_AU,
                     observaciones="Besser block serie 90 (390×190×90) a 3,67 $ con GST "
                                   "(Brighton Masonry en Bunnings) → 3,34 $ sin GST."),
    "MT-BLQ-15": ref(3.92, 3.40, 4.60, R_AU,
                     observaciones="Besser block serie 140 (390×190×140) a 4,31 $ con GST "
                                   "→ 3,92 $ sin GST."),
    "MT-BLQ-20": ref(4.31, 3.80, 5.00, R_AU,
                     observaciones="Besser block serie 190 (390×190×190) a 4,74 $ con GST "
                                   "→ 4,31 $ sin GST; guías 2026: 3,80-5,50 $ sin GST."),
    "MT-LADRILLO-VISTO": ref(1.45, 0.85, 2.60, R_AU,
                             observaciones="Ladrillo caravista de arcilla 230×110×76: lista "
                                           "Austral Bricks 1.729-3.453 $/1.000 con GST y "
                                           "guías trade 900-1.200 $/1.000; adoptada la "
                                           "banda media por unidad sin GST."),
    # ── Yeso laminado y tabiquería ───────────────────────────────────────────
    "MT-PYL-PLACA125": ref(11.50, 9.50, 13.50, R_AU,
                           observaciones="Placa Gyprock de 13 mm, hoja 2400×1200 (2,88 m²): "
                                         "29,25-30,86 $ en Network Building y 42,57 $ en "
                                         "Bunnings Trade (con GST) → 9,2-13,4 $/m² sin GST."),
    "MT-PYL-PLACA": ref(13.50, 11.50, 16.00, R_AU,
                        confianza="derivado",
                        observaciones="Placa de 15-16 mm (Gyprock de techo/fuego ligero): "
                                      "estimada sobre la hoja de 13 mm observada."),
    "MT-PYL-PLACA-IG": ref(15.50, 13.00, 18.50, R_AU,
                           confianza="derivado",
                           observaciones="Placa cortafuego tipo Fyrchek de 16 mm, estimada "
                                         "sobre la gama Gyprock AU."),
    "MT-PYL-PLACA-RH": ref(14.50, 12.00, 17.00, R_AU,
                           confianza="derivado",
                           observaciones="Placa resistente a humedad tipo Aquachek, "
                                         "estimada sobre la gama Gyprock AU."),
    "MT-PYL-PLACA-HD": ref(15.00, 12.50, 18.00, R_AU,
                           confianza="derivado",
                           observaciones="Placa acústica/de impacto tipo Soundchek, "
                                         "estimada sobre la gama Gyprock AU."),
    "MT-PLACA-CEM": ref(13.00, 10.50, 16.00, R_AU,
                        confianza="derivado",
                        observaciones="Placa de fibrocemento de 6 mm (Villaboard) de "
                                      "comercio AU, por m² de hoja."),
    "MT-PYL-MONT": ref(3.30, 2.90, 4.20, R_AU,
                       observaciones="Montante Rondo de 64 mm 0,50 BMT × 3,0 m a 9,62 $ "
                                     "sin GST (Sydney Building Materials) → 3,21 $/m; "
                                     "0,75 BMT más caro."),
    "MT-PYL-CANAL": ref(3.10, 2.70, 3.90, R_AU,
                        confianza="derivado",
                        observaciones="Canal Rondo de 64 mm: paquetes de 10 desde 118,40 $ "
                                      "(PMC); estimado por metro en línea con el montante."),
    "MT-PYL-PASTA": ref(2.55, 2.20, 3.10, R_AU,
                        observaciones="Base Coat 45/60 de 20 kg a 48,48-52,90 $ con GST en "
                                      "Bunnings (62,50-68,67 $ en especialistas) → "
                                      "2,2-3,1 $/kg sin GST."),
    "MT-PYL-PASTA-AGARRE": ref(2.75, 2.40, 3.20, R_AU,
                               observaciones="Equivalente australiano de la pasta de "
                                             "agarre: Cornice Cement de 20 kg a "
                                             "55,28-67,28 $ con GST → 2,5-3,1 $/kg sin GST."),
    "MT-MALLA-ESQ": ref(1.10, 0.85, 1.45, R_AU,
                        confianza="derivado",
                        observaciones="Cantonera metálica de 2,4-3,0 m de comercio AU, "
                                      "por metro."),
    "MT-YESO-REP": ref(2.80, 2.20, 3.60, R_AU,
                       confianza="derivado",
                       observaciones="Masilla/yeso de reparación (multipurpose filler) "
                                     "de comercio AU, por kg."),
    "MT-PYL-LANA": ref(10.50, 8.50, 12.50, R_AU,
                       observaciones="Paneles Earthwool R2.5HD de 90 mm: 99,67-115 $ con "
                                     "GST por paquete de 9,4 m² → 9,6-11,1 $/m² sin GST."),
    # ── Adhesivos, juntas y nivelación ───────────────────────────────────────
    "MT-ADH-C2TE": ref(1.70, 1.45, 2.15, R_AU,
                       observaciones="Adhesivo flexible C2S1 de 20 kg: Dunlop Rubber "
                                     "Modified 37,74 $ con GST → 1,72 $/kg sin GST; Davco "
                                     "SMP Evo 32,29 $ → 1,47 $/kg."),
    "MT-ADH-C1": ref(1.35, 1.15, 1.60, R_AU,
                     observaciones="Adhesivo cementoso estándar de 20 kg: Davco Powder "
                                   "Mastic 29,40 $ con GST → 1,34 $/kg sin GST."),
    "MT-JUN-CG2": ref(5.50, 4.20, 6.60, R_AU,
                      observaciones="Mortero de juntas flexible de 5 kg a 32,82 $ con GST "
                                    "(Dunlop) → 5,97 $/kg sin GST; formatos trade bajan "
                                    "el kilo."),
    "MT-AUT-NIV": ref(2.45, 2.00, 3.00, R_AU,
                      observaciones="Autonivelante Dunlop Ardit de 20 kg a 53,96 $ con GST "
                                    "→ 2,45 $/kg sin GST."),
    "MT-IMP-PRIM": ref(9.50, 7.00, 12.50, R_AU,
                       confianza="derivado",
                       observaciones="Imprimación de agarre (primer acrílico) en envase "
                                     "de 4 l de comercio AU."),
    "MT-GROUT": ref(1.55, 0.95, 1.70, R_AU,
                    observaciones="Grout de construcción de 20 kg: Dunlop 33,78 $ con GST "
                                  "→ 1,54 $/kg sin GST (gama GP desde 21,04 $ → 0,96 $/kg)."),
    "MT-GROUT-CELDA": ref(335, 300, 380, R_AU,
                          confianza="derivado",
                          observaciones="Hormigón fluido de relleno de celdas (core fill) "
                                        "por m³: se valora como un premezclado N20/N25 "
                                        "bombeable, en línea con MT-CONC-250. El factor "
                                        "de la familia MT-GROUT (sacos de 20 kg) daría "
                                        "un precio sin sentido por m³."),
    "MT-TORN": ref(0.020, 0.014, 0.028, R_AU,
                   confianza="derivado",
                   observaciones="Tornillos de placa en caja de 1.000 de comercio AU "
                                 "(≈20-28 $ con GST por caja) → ≈0,02 $/ud sin GST."),
    "MT-SIL-SAN": ref(14.20, 8.00, 15.50, R_AU,
                      observaciones="Silicona sanitaria 300 g: Selleys Wet Area 15,60 $ "
                                    "con GST → 14,18 $ sin GST; gama Parfix desde "
                                    "8,85 $ con GST."),
    # ── Pinturas y tratamientos de madera ────────────────────────────────────
    "MT-PIN-CAUCHO": ref(21.50, 18.00, 26.00, R_AU,
                         observaciones="Pintura lavable Dulux Wash&Wear Low Sheen 10 l a "
                                       "239 $ con GST → 21,73 $/l sin GST."),
    "MT-PIN-SEMIBRILLO": ref(24.00, 20.00, 29.00, R_AU,
                             observaciones="Gama semibrillo lavable: Dulux Wash&Wear "
                                           "+PLUS Semi Gloss 10 l a 290 $ con GST → "
                                           "26,36 $/l sin GST."),
    "MT-PIN-ESMALTE": ref(23.00, 18.00, 30.00, R_AU,
                          confianza="derivado",
                          observaciones="Esmalte sintético (Dulux Super Enamel) en envase "
                                        "de 4 l de comercio AU."),
    "MT-ESMALTE-AGUA": ref(24.00, 19.00, 31.00, R_AU,
                           confianza="derivado",
                           observaciones="Esmalte al agua (Dulux Aquanamel) en envase de "
                                         "4 l de comercio AU."),
    "MT-PIN-FONDO": ref(15.00, 10.00, 22.00, R_AU,
                        confianza="derivado",
                        observaciones="Fondo sellador tipo Dulux 1Step Prep: entre el "
                                      "sellador a granel y el envase de 4 l (≈15 $/l "
                                      "sin GST)."),
    "MT-PIN-MASILLA": ref(7.50, 5.50, 10.00, R_AU,
                          confianza="derivado",
                          observaciones="Masilla lista al uso (Polyfilla/Selleys) por kg "
                                        "de comercio AU."),
    "MT-PIN-CAL": ref(0.55, 0.40, 0.75, R_AU,
                      confianza="derivado",
                      observaciones="Cal hidratada en saco de 20 kg (≈12 $ con GST); el "
                                    "factor de la familia de pinturas daría un precio "
                                    "absurdo para un mineral a granel."),
    "MT-BARNIZ-MARINO": ref(30.00, 23.00, 38.00, R_AU,
                            confianza="derivado",
                            observaciones="Barniz exterior (Cabot's/Feast Watson) por litro "
                                          "en envase de 1-4 l."),
    "MT-LASUR": ref(20.00, 15.00, 26.00, R_AU,
                    confianza="derivado",
                    observaciones="Protector/lasur de madera exterior (decking oil y "
                                  "stain) en envase de 4 l."),
    "MT-TINTE-MAD": ref(22.00, 16.00, 29.00, R_AU,
                        confianza="derivado",
                        observaciones="Tinte de madera interior (Feast Watson Proof Tint) "
                                      "por litro."),
    # ── Fontanería ───────────────────────────────────────────────────────────
    # Nota de mercado: en Australia el PPR es residual; el equivalente
    # funcional es el PEX de crimpado de 16-20 mm (y el cobre para vistas).
    "MT-PLO-PPR20": ref(1.60, 1.00, 2.60, R_AU,
                        observaciones="Tubo PEX de 16 mm: bobinas de 100 m a 99-120 $ "
                                      "(0,90-1,20 $/m) en mayoristas y 56,89 $/20 m con "
                                      "GST en Bunnings (2,59 $/m sin GST al por menor)."),
    "MT-PLO-ACC20": ref(4.20, 2.80, 6.00, R_AU,
                        confianza="derivado",
                        observaciones="Accesorios de crimpado PEX de 16-20 mm (codos, tes) "
                                      "de mayorista AU; precio medio por pieza."),
    "MT-PLO-PVC4": ref(8.00, 6.50, 10.00, R_AU,
                       observaciones="Tubería PVC DWV de 100 mm en largos de 6 m a "
                                     "45-60 $ con GST → 6,8-9,1 $/m sin GST."),
    "MT-PLO-ACC4": ref(9.50, 5.50, 18.00, R_AU,
                       confianza="derivado",
                       observaciones="Accesorios DWV de 100 mm (codos, tes, uniones) de "
                                     "comercio AU; precio medio de pieza corriente."),
    # ── Electricidad ─────────────────────────────────────────────────────────
    "MT-ELE-CAJA": ref(3.20, 2.20, 4.80, R_AU,
                       confianza="derivado",
                       observaciones="Caja de mecanismo/mounting block de PVC de "
                                     "mayorista eléctrico AU."),
    "MT-ELE-CABLE": ref(2.15, 1.95, 2.45, R_AU,
                        observaciones="Cable TPS twin & earth de 2,5 mm²: bobina de 100 m "
                                      "a 194-242 $ sin GST (MJS, Sparky Direct, Arck) → "
                                      "1,94-2,42 $/m."),
    "MT-ELE-MECA": ref(13.50, 9.00, 20.00, R_AU,
                       confianza="derivado",
                       observaciones="Mecanismo doble GPO estándar (Clipsal 2000/HPM) de "
                                     "mayorista eléctrico AU, con placa."),
    # ── Aislamiento e impermeabilización ─────────────────────────────────────
    "MT-POLIESTIRENO-EXT": ref(24.00, 18.00, 32.00, R_AU,
                               confianza="derivado",
                               observaciones="Panel XPS de 50 mm (Foamex/Knauf) de "
                                             "distribuidor AU, por m²."),
    "MT-LANA-ROCA": ref(16.00, 12.00, 22.00, R_AU,
                        confianza="derivado",
                        observaciones="Panel de lana de roca (Bradford/Rockwool) de "
                                      "distribuidor AU, sobre la banda Earthwool."),
    "MT-GEOTEXTIL": ref(1.10, 0.70, 1.80, R_AU,
                        confianza="derivado",
                        observaciones="Geotextil tipo Bidim A14 en rollo de distribuidor "
                                      "AU, por m²."),
    "MT-TUBO-DREN": ref(4.50, 3.40, 6.00, R_AU,
                        confianza="derivado",
                        observaciones="Tubo de drenaje corrugado de 100 mm con funda "
                                      "(socked aggi) en bobina, por metro."),
    # ── Madera y tableros ────────────────────────────────────────────────────
    "MT-MADERA-EST": ref(980, 820, 1200, R_AU,
                         confianza="derivado",
                         observaciones="Pino estructural MGP10: el precio minorista por "
                                       "metro lineal (5,36 $/m con GST el 90×45) implica "
                                       "≈1.200 $/m³; en paquete trade baja a "
                                       "820-1.000 $/m³. Se adopta 980 $."),
    "MT-MADERA-LISTON": ref(4.90, 4.20, 5.80, R_AU,
                            observaciones="Listón MGP10 de 90×45 mm a 5,36 $/m con GST "
                                          "(Bunnings) → 4,87 $/m sin GST; tratado H2 a "
                                          "5,82 $/m con GST."),
    "MT-LAMINA-OSB": ref(19.00, 15.00, 24.00, R_AU,
                         confianza="derivado",
                         observaciones="El OSB es escaso en Australia: equivalente "
                                       "funcional en contrachapado CD de 17-19 mm por m² "
                                       "de hoja 2400×1200."),
    # ── Residuos ─────────────────────────────────────────────────────────────
    # El waste levy metropolitano de NSW es 180,20 $/t desde el 1/07/2026 (el
    # mayor de Australia) y está dentro del precio del skip: 6 m³ en Sídney
    # cuesta 845-911 $ con GST (guías e índice de precios, sep-2026).
    "MT-CANON": ref(125, 95, 165, R_AU,
                    observaciones="Retirada de escombro mezclado por m³ vía skip de 6 m³ "
                                  "(845-911 $ con GST en Sídney ≈ 128 $/m³ sin GST a "
                                  "plena carga), con el waste levy de 180,20 $/t ya "
                                  "repercutido."),
    "MT-CANON-TIERRA": ref(110, 75, 155, R_AU,
                           confianza="derivado",
                           observaciones="Tierra inerte vía skip de residuo pesado "
                                         "(4 m³ ≈700 $ con GST) y puertas de reciclaje; "
                                         "el suelo limpio VENM puede salir más barato "
                                         "en cantera."),
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
        referencias[codigo] = {"AU": dato}
    for codigo, dato in MATERIALES.items():
        if codigo in referencias:
            raise ValueError(f"{codigo} definido dos veces")
        referencias[codigo] = {"AU": dato}
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

    El factor es la mediana de (precio australiano investigado / precio base
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
        dato = por_pais.get("AU")
        if ficha is None or dato is None or dato.confianza != "referencia":
            continue
        categoria = ficha[0]
        if categoria == "mano_obra":
            continue
        base_local = float(ficha[1]["precio"]) * TASAS_CORTE["AU"]
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
        if referencias.get(codigo, {}).get("AU") is not None:
            continue
        base_local = float(item["precio"]) * TASAS_CORTE["AU"]
        factor = factores_familia.get((categoria, _familia(codigo)))
        origen = f"familia {_familia(codigo)}"
        if factor is None:
            factor = factores_categoria[categoria]
            origen = f"categoría {categoria}"
        referencias.setdefault(codigo, {})["AU"] = replace(
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
        dato = referencias.get(codigo, {}).get("AU")
        if dato is None:
            raise SystemExit(f"Sin referencia para {codigo}")
        filas.append({
            "codigo_recurso": codigo,
            "descripcion": item["descripcion"],
            "categoria": categoria,
            "unidad_fuente": item["unidad"],
            "pais_codigo": "AU",
            "moneda": "AUD",
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
    print(f"Matriz australiana escrita en {OUT.relative_to(ROOT)}")
    print(f"  {total} recursos · {investigados} investigados "
          f"({investigados / total:.0%}) · {derivados} derivados por factor")
    print(f"  tasa de corte: 1 USD = {TASAS_CORTE['AU']:.4f} AUD (AUD/USD 0,6947, RBA 16/10/2026)")
    print()
    print("  Factores por categoría (mediana de precio australiano / base convertida):")
    for categoria, factor in sorted(factores_categoria.items()):
        print(f"    {categoria:12s} {factor:8.3f}")
    print()
    print(f"  Familias con ancla propia: {len(factores_familia)}")
    for (categoria, familia), factor in sorted(factores_familia.items()):
        n = len([1 for c, d in referencias.items()
                 if d.get("AU") and d["AU"].confianza == "referencia"
                 and _familia(c) == familia and c in
                 {x for x, cat, _ in iter_recursos(data) if cat == categoria}])
        print(f"    {familia:22s} {factor:8.3f}  ({n} anclas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
