#!/usr/bin/env python3
"""Genera la matriz de precios de recursos para Irlanda (EUR).

Replica el contrato de ``generar_matriz_precios_reino_unido.py``:

* Los precios base de ``basedatos_partidas/datos/recursos.json`` están en USD
  con ámbito **Venezuela**. No son precios internacionales, así que ninguna
  conversión de divisa puede producir un precio irlandés. La matriz se
  construye desde precios irlandeses reales.
* Las anclas investigadas se publican tal cual, con rango, fuente y fecha.
* El resto se cubre con un **factor de mercado por familia**, calculado como
  la mediana de la relación entre el precio irlandés investigado y el precio
  base de cada ancla de esa familia.
* La mano de obra no usa factores: los 17 oficios salen del modelo de coste
  empresa de ``coste_empresa_irlanda.py``.

Particularidades de Irlanda frente a España y el Reino Unido:

* El IVA de los materiales no es único: hormigón y bloques tributan al
  13,5 % y el resto de materiales al 23 %. Los comercios irlandeses
  (TJ O'Mahony, McMahons, Brooks) publican el precio sin IVA junto al
  precio con IVA; la matriz toma siempre la cifra «ex VAT» del comercio,
  nunca una división casera.
* El hormigón y los bloques llevan dentro el Defective Concrete Products
  Levy (DCPL) del 5 %, que se devenga en la primera venta: ya forma parte
  del precio de lista observado y no se suma dos veces.
* La mano de obra parte del mínimo legal o pactado (SEO / AECI / Connect),
  así que el rango no baja un 10 % como en el Reino Unido: −3 % / +20 %.
* Las anclas sin tarifa irlandesa publicada (maquinaria especialista y
  algún material) se publican con confianza ``derivado`` y precio explícito
  por analogía documentada, en lugar de fingir una observación.

Uso:
    python3 tools/generar_matriz_precios_irlanda.py
"""
from __future__ import annotations

import csv
import json
import statistics
from dataclasses import dataclass, replace
from pathlib import Path

from coste_empresa_irlanda import (
    HORAS_FACTURABLES,
    OFICIOS,
    coste_empresa,
)

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "basedatos_partidas/datos/recursos.json"
OUT = ROOT / "basedatos_partidas/salida/precios_recursos_irlanda.csv"
PAISES = (("IE", "EUR"),)
FECHA = "2026-10-19"

R_IE = "docs/INVESTIGACION_PRECIOS_IRLANDA.md"
METODOLOGIA = "docs/METODOLOGIA_PRECIOS_REFERENCIA_IRLANDA.md"
# Tipo de referencia del BCE del 16/10/2026: 1 EUR = 1,1253 USD
# -> 1 USD = 0,8886 EUR.
# Solo normaliza el precio base antes de aplicar el factor de mercado; el
# resultado queda congelado en EUR y con fecha.
TASAS_CORTE = {"IE": 0.8886}

OBS_REFERENCIA = (
    "Precio de mercado irlandés observado (sin IVA, sin porte salvo indicación); "
    "puede variar por proveedor, marca, volumen y región."
)
OBS_DERIVADO = (
    "Precio referencial derivado del factor de mercado de su familia, calculado "
    "sobre la canasta irlandesa investigada; no es una cotización de tienda."
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


def ref(precio, minimo, maximo, fuente=R_IE, **kwargs) -> Referencia:
    precio, minimo, maximo = map(float, (precio, minimo, maximo))
    if minimo <= 0 or maximo < minimo or not minimo <= precio <= maximo:
        raise ValueError(f"Rango inválido: {minimo} <= {precio} <= {maximo}")
    return Referencia(precio, minimo, maximo, fuente, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Mano de obra — modelo de coste empresa irlandés
# ─────────────────────────────────────────────────────────────────────────────

def referencias_mano_obra() -> dict[str, dict[str, Referencia]]:
    salida: dict[str, dict[str, Referencia]] = {}
    for codigo, (oficio, salario, escala) in OFICIOS.items():
        coste = coste_empresa(salario)["coste_hora_facturable"]
        # El rango refleja la dispersión regional y de mercado: −3 % (el
        # salario es mínimo legal o pactado a nivel nacional y no admite la
        # rebaja del 10 % usada en el Reino Unido) y +20 % (Dublín y pagas
        # por encima del SEO en obra grande).
        salida[codigo] = {
            "IE": ref(
                coste,
                coste * 0.97,
                coste * 1.20,
                R_IE,
                confianza="referencia",
                incluye_iva="no_aplica",
                incluye_transporte="no_aplica",
                observaciones=(
                    f"Coste empresa por hora facturable. {oficio}. Salario "
                    f"{salario:.2f} €/h ({escala}) + PRSI empresa 11,40 % "
                    f"(desde 01/10/2026), CWPS 36,43 €/semana, 21 días de "
                    f"vacaciones de la industria + 10 festivos y bajas, todo "
                    f"dividido por {HORAS_FACTURABLES:,.0f} h facturables/año. "
                    f"No es tarifa de autónomo: el catálogo ya aplica un 35 % "
                    f"de margen sobre el coste directo."
                ),
            )
        }
    return salida


# ─────────────────────────────────────────────────────────────────────────────
# 2. Maquinaria — tarifas de alquiler irlandesas
#
#    Las tarifas irlandesas se cotizan por día (8 h) o por semana. Se adopta
#    el día de 8 horas y se publica el equivalente horario. Excluyen IVA,
#    combustible y operador salvo que el recurso lo indique (bomba de
#    hormigón, grúa, perforadora y volqueta se alquilan con operador).
#    Fuente principal: lista pública ex-VAT de Mr Hire, contrastada con
#    Laois Hire (semanal) y guías de DCM Hire / Kerwin.
# ─────────────────────────────────────────────────────────────────────────────

def _alquiler(dia, minimo, maximo, nota="", confianza="referencia") -> Referencia:
    return ref(
        dia / 8.0, minimo / 8.0, maximo / 8.0, R_IE,
        confianza=confianza,
        observaciones=(
            f"Alquiler irlandés {minimo:.0f}-{maximo:.0f} €/día (jornada de 8 h), "
            f"sin IVA ni combustible. {nota}".strip()
        ),
    )


MAQUINARIA: dict[str, Referencia] = {
    # Corte y demolición
    "MQ-CORT-AGUA": _alquiler(85, 45, 110, "Sierra de banco húmeda para cerámica "
                              "(tile saw table 100 €/día; clipper grande 45 €/día)."),
    "MQ-ROZAD": _alquiler(80, 70, 95, "Rozadora de doble disco (wall chaser)."),
    "MQ-MART-ELEC": _alquiler(35, 30, 50, "Martillo eléctrico de 5 kg (Hilti "
                              "TE500/TE70); el TE1000 sube a 50 €/día."),
    "MQ-AMOLA": _alquiler(22, 18, 30, "Amoladora angular de 9\" (20 €/día) a 12\" (30 €/día)."),
    "MQ-SIERRA": _alquiler(40, 25, 80, "Sierra circular 25 €/día; motosierra de "
                           "gasolina 80 €/día."),
    "MQ-OXICORTE": _alquiler(45, 35, 65, "Sin tarifa publicada en Irlanda: estimado "
                             "por analogía con equipo de soldadura y botellas.",
                             confianza="derivado"),
    "MQ-CIZALLA": _alquiler(50, 35, 70, "Sin tarifa publicada en Irlanda: estimado "
                            "por analogía con herramienta eléctrica pesada de la "
                            "misma lista (cortadora de pernos 15 €/día es manual).",
                            confianza="derivado"),
    "MQ-ESMERIL": _alquiler(30, 25, 40, "Esmeriladora de disco de 12\"."),
    # Hormigón
    "MQ-MEZCL": _alquiler(30, 25, 40, "Hormigonera eléctrica de un saco "
                          "(30 €/día, 90 €/semana)."),
    "MQ-BATID": _alquiler(30, 25, 40, "Batidora mezcladora (plaster drill mixer)."),
    "MQ-VIBRADOR": _alquiler(40, 35, 50, "Vibrador de aguja (poker)."),
    "MQ-ALISADORA": _alquiler(70, 60, 85, "Alisadora helicóptero (power float)."),
    "MQ-BOMBA-CONC": _alquiler(650, 500, 850, "Bomba de hormigón **con operador**. "
                               "En Irlanda se cotiza por vertido, sin tarifa "
                               "pública: estimación por jornada de equipo.",
                               confianza="derivado"),
    "MQ-PROYECT-MORT": _alquiler(120, 90, 160, "Sin tarifa publicada: estimado por "
                               "analogía con el equipo industrial de proyección "
                               "(100 €/día) más compresor.",
                               confianza="derivado"),
    # Compactación y movimiento de tierras
    "MQ-COMPACT-SALTO": _alquiler(45, 40, 60, "Compactador de impacto "
                                  "(elephant's foot / trench rammer)."),
    "MQ-PLANCHA-COMP": _alquiler(40, 35, 55, "Plancha compactadora de gasolina "
                                 "35 €/día, diésel 50 €/día."),
    "MQ-RETRO": _alquiler(300, 240, 380, "Miniexcavadora de 3 t (180 €/día) + "
                          "martillo hidráulico (120 €/día), alquiler seco; el "
                          "operador va en la mano de obra de la partida."),
    "MQ-MART-NEUM": _alquiler(180, 150, 230, "Compresor de obra (road compressor "
                              "150 €/día) con martillo neumático."),
    "MQ-PERF-PILOTE": _alquiler(1500, 1200, 1900, "Equipo de perforación de "
                                "pilotes **con operador**; sin tarifa pública en "
                                "Irlanda (alquiler especializado por proyecto).",
                                confianza="derivado"),
    # Elevación y acceso
    "MQ-ANDAMIO": _alquiler(45, 35, 70, "Torre móvil de andamio de 8-12 pies "
                            "(40-50 €/día; la de 32 pies llega a 100 €/día)."),
    "MQ-MONTAC": _alquiler(100, 80, 130, "Elevador de escombro/material "
                           "(rubble elevator 105 €/día)."),
    "MQ-VENT-SUC": _alquiler(30, 20, 45, "Juego de ventosas triples de elevación "
                             "(20 €/día) y manipulación de gran formato."),
    "MQ-GRUA": _alquiler(575, 400, 800, "Grúa móvil **con operador**: grúa urbana "
                         "350-450 €/día, telescópica 500-800 €/día (guía Kerwin)."),
    # Instalaciones y acabados
    "MQ-ATORN": _alquiler(30, 25, 35, "Atornilladora para placa de yeso (screw gun)."),
    "MQ-LIJAD": _alquiler(45, 35, 60, "Lijadora de pared/pulidora rotativa con aspiración."),
    "MQ-PULIDORA": _alquiler(50, 40, 65, "Pulidora/fregadora de pisos (floor scrubber)."),
    "MQ-LIJAD-PISO": _alquiler(65, 50, 85, "Lijadora de banda de pisos (50 €/día) + "
                               "orilladora (25 €/día), juego completo."),
    "MQ-ESTAMP": _alquiler(90, 70, 120, "Moldes de hormigón impreso; sin tarifa "
                           "pública irlandesa.", confianza="derivado"),
    "MQ-SOLDADORA": _alquiler(40, 30, 55, "Soldadora eléctrica 30 €/día; grupo "
                              "electrógeno soldador 50 €/día."),
    "MQ-TERMOF": _alquiler(40, 30, 55, "Herramienta de tubería (probador de presión "
                           "30 €/día como análogo); la termofusión PPR es residual "
                           "en Irlanda.", confianza="derivado"),
    "MQ-DOBLAD-TUBO": _alquiler(30, 22, 45, "Sin tarifa publicada: estimado por "
                                "analogía con herramienta de tubería de la lista.",
                                confianza="derivado"),
    "MQ-RECUP-GAS": _alquiler(60, 45, 85, "Sin tarifa publicada: estimado por "
                              "analogía con equipo de medición/refrigeración.",
                              confianza="derivado"),
    "MQ-INYECTORA": _alquiler(70, 50, 95, "Sin tarifa publicada: estimado por "
                              "analogía con equipo de proyección/bombeo menor.",
                              confianza="derivado"),
    "MQ-RODILLO": _alquiler(15, 10, 25, "Equipo de aplicación: rodillos, brochas, "
                            "cubetas y andamio bajo, amortizado.",
                            confianza="derivado"),
    # Limpieza, achique y seguridad
    "MQ-ASPIR": _alquiler(40, 35, 50, "Aspirador industrial."),
    "MQ-HIDROLAV": _alquiler(55, 45, 70, "Hidrolavadora de gasolina (power washer)."),
    "MQ-BOMBA-ACHI": _alquiler(30, 25, 40, "Bomba de agua/achique."),
    "MQ-DESBROZ": _alquiler(30, 25, 40, "Desbrozadora (strimmer)."),
    # Medición y detección
    "MQ-NIVEL-LASER": _alquiler(40, 30, 55, "Nivel láser; estimado sobre la banda "
                                "de equipos de medición de la lista (CAT 30 €/día).",
                                confianza="derivado"),
    "MQ-DETECTOR": _alquiler(30, 25, 40, "Detector de servicios enterrados (CAT scan)."),
    "MQ-TALADRO": _alquiler(28, 22, 35, "Taladro percutor/SDS (25-30 €/día)."),
    "MQ-TELUROMETRO": _alquiler(55, 40, 75, "Sin tarifa publicada: estimado por "
                                "analogía con equipos de comprobación eléctrica.",
                                confianza="derivado"),
    # Transporte
    "MQ-VOLQ": _alquiler(500, 400, 620, "Camión volqueta **con chofer**. El grab "
                         "hire irlandés (camión con pulpo) cobra 350-400 € por "
                         "carga de ~16 t; jornada completa estimada.",
                         confianza="derivado"),
    # Unidad distinta: el baño portátil se alquila por mes.
    "MQ-BANO-PORT": ref(
        195, 160, 240, R_IE,
        confianza="derivado",
        observaciones=(
            "Alquiler mensual de baño portátil de obra con mantenimiento "
            "(recurso medido en unidades, no en horas). Sin IVA. Sin tarifa "
            "pública irlandesa localizada: estimación de mercado."
        ),
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# 3. Materiales — precios de proveedor irlandés
#
#    Todos los precios son «ex VAT». TJ O'Mahony, McMahons y Brooks publican
#    la pareja con/sin IVA (13,5 % en hormigón y bloques, 23 % en el resto);
#    en Screwfix IE, que solo muestra precio con IVA (23 % salvo hormigón),
#    la cifra sin IVA se obtiene dividiendo por 1,23 y así se declara en la
#    observación de cada ancla.
# ─────────────────────────────────────────────────────────────────────────────

MATERIALES: dict[str, Referencia] = {
    # ── Hormigón y áridos ────────────────────────────────────────────────────
    # Hanly Quarries es el único productor de la República con lista pública
    # por m³ (Roscommon). Precio con el DCPL del 5 % ya incluido, IVA del
    # 13,5 % aparte. El máximo cubre Dublín y cargas pequeñas (la prensa
    # agraria situaba el m³ «cerca de 150 €» en 2026).
    "MT-CONC-180": ref(114, 108, 132, R_IE,
                       observaciones="Hormigón premezclado ≈ C16/20 (180 kg/cm² ≈ 17,7 MPa). "
                                     "Hanly Quarries 114 €/m³ ex IVA, DCPL 5 % incluido."),
    "MT-CONC-210": ref(120, 114, 138, R_IE,
                       observaciones="Hormigón premezclado ≈ C20/25 (210 kg/cm² ≈ 20,6 MPa). "
                                     "Hanly Quarries 120 €/m³ ex IVA, DCPL 5 % incluido."),
    "MT-CONC-250": ref(126, 120, 145, R_IE,
                       observaciones="Hormigón premezclado ≈ C25/30 (250 kg/cm² ≈ 24,5 MPa). "
                                     "Hanly Quarries 126 €/m³ ex IVA, DCPL 5 % incluido."),
    "MT-CONC-300": ref(132, 126, 152, R_IE,
                       observaciones="Hormigón premezclado ≈ C30/37 (300 kg/cm² ≈ 29,4 MPa). "
                                     "Hanly Quarries 132 €/m³ ex IVA, DCPL 5 % incluido."),
    "MT-CEMENTO": ref(0.32, 0.30, 0.36, R_IE,
                      observaciones="Cemento CEM II en saco de 25 kg: 7,72 € ex IVA en "
                                    "TJ O'Mahony y 8,46 € en McMahons (0,31-0,34 €/kg)."),
    "MT-ARENA": ref(54, 45, 70, R_IE,
                    observaciones="Arena lavada suelta 35,94 €/t ex IVA (Hanly Quarries, "
                                  "mínimo 18 t) × 1,5 t/m³. La arena es cara en Irlanda "
                                  "por escasez de extracción autorizada."),
    "MT-PIEDRA-PIC": ref(24, 21, 40, R_IE,
                         observaciones="Piedra triturada de 20-25 mm: 14 €/t ex IVA en cantera "
                                       "(Hanly Quarries) × 1,5 t/m³, con margen de porte corto. "
                                       "La caliza local es abundante: es el árido barato."),
    "MT-MAT-PRESTAMO": ref(28, 24, 42, R_IE,
                           observaciones="Material granular Clause 804 (T1): 12,50 €/t ex IVA "
                                         "(Hanly Quarries) × 2,1 t/m³ compactado. En big-bag de "
                                         "comercio sube a 51-62 €/t (TJ O'Mahony)."),
    "MT-AGUA-OBRA": ref(3.00, 2.40, 4.20, R_IE,
                        observaciones="Agua de obra: tarifa no doméstica de Uisce Éireann "
                                      "(suministro + saneamiento, banda baja)."),
    "MT-ADITIVO": ref(2.60, 1.80, 3.80, R_IE,
                      confianza="derivado",
                      observaciones="Plastificante en envase de 5-25 l de comercio irlandés "
                                    "(Sika vía Brooks); sin precio por litro publicado."),
    "MT-CURADOR": ref(3.60, 2.80, 4.60, R_IE,
                      observaciones="Curador de membrana Sika Antisol-3 E: 81,29 € ex IVA el "
                                    "envase industrial (Brooks), ≈3,3-4,1 €/l según envase "
                                    "de 20-25 l."),
    "MT-DESMOLD": ref(3.80, 2.80, 5.20, R_IE,
                      observaciones="Desmoldeante Sika Release Oil 5 l a 21,67 € en comercio "
                                    "irlandés (4,33 €/l en envase pequeño; menos a granel)."),
    # ── Acero ────────────────────────────────────────────────────────────────
    "MT-ACERO-CAB": ref(1.22, 1.00, 1.50, R_IE,
                        observaciones="Barra corrugada de 12 mm × 6 m a 6,50 € ex IVA "
                                      "(5,32 kg por barra → 1,22 €/kg), comercio irlandés."),
    "MT-MALLA-ELEC": ref(5.00, 2.50, 6.80, R_IE,
                         observaciones="Malla electrosoldada en panel de 4,8 × 2,4 m: A142 "
                                       "28,41 €, A252 48,74 €, A393 65,00-78,05 € ex IVA "
                                       "(TJ O'Mahony / McMahons) → 2,47-6,78 €/m² según tipo."),
    "MT-PERFIL-ACERO": ref(1.70, 1.40, 2.20, R_IE,
                           observaciones="Viga universal (RSJ) cortada a medida: 203×133 a "
                                         "35-50 €/m (25-30 kg/m) en guías y comercio irlandés "
                                         "→ 1,4-1,7 €/kg; secciones pequeñas desde 30,82 €/m."),
    "MT-PLANCHA-ACERO": ref(1.85, 1.50, 2.40, R_IE,
                            confianza="derivado",
                            observaciones="Chapa de acero: sin lista pública por kg en Irlanda; "
                                          "estimada sobre el precio del perfil cortado a medida."),
    "MT-FORM-MADERA": ref(6.80, 5.50, 8.50, R_IE,
                          confianza="derivado",
                          observaciones="Encofrado de madera amortizado (≈10 usos): tablero y "
                                        "madera de comercio irlandés prorrateados por uso. No "
                                        "es precio de compra por m²."),
    "MT-POLIET": ref(0.75, 0.60, 1.60, R_IE,
                     observaciones="Membrana de polietileno DPM 1000-1200 ga: 67,58 € ex IVA el "
                                   "rollo de 100 m² (Irish Flooring); la de 2000 ga sube a "
                                   "1,59 €/m² (TJ O'Mahony)."),
    # ── Fábrica y bloques ────────────────────────────────────────────────────
    # Formato irlandés 440 × 215 mm (el recurso describe 40 × 20 cm: mismo
    # bloque funcional; el rendimiento por m² de muro apenas cambia). IVA del
    # 13,5 % ya retirado por el propio comercio; DCPL incluido en el precio.
    "MT-BLQ-10": ref(1.45, 1.37, 1.65, R_IE,
                     observaciones="Bloque macizo de 100 mm (440×215, 7,5 N): 1,37 € ex IVA en "
                                   "TJ O'Mahony, 1,44-1,65 € en McMahons."),
    "MT-BLQ-15": ref(2.45, 2.28, 2.60, R_IE,
                     observaciones="Bloque macizo de 150 mm (440×215): 2,28-2,60 € ex IVA "
                                   "(TJ O'Mahony / McMahons)."),
    "MT-BLQ-20": ref(2.45, 2.29, 2.60, R_IE,
                     observaciones="Bloque hueco de cámara de 215 mm (440×215), equivalente "
                                   "funcional irlandés del bloque de 20 cm: 2,29-2,60 € ex IVA."),
    "MT-LADRILLO-VISTO": ref(1.55, 1.30, 1.90, R_IE,
                             observaciones="Ladrillo caravista Tobermore a 1,54 € ex IVA por "
                                           "unidad en comercio irlandés."),
    # ── Yeso laminado y tabiquería ───────────────────────────────────────────
    "MT-PYL-PLACA125": ref(5.60, 4.90, 6.20, R_IE,
                           observaciones="Placa de 12,5 mm, hoja 2438×1200 (2,93 m²): Gyproc "
                                         "17,85 € ex IVA (6,10 €/m²) en TJ O'Mahony; Knauf "
                                         "14,59 € (4,99 €/m²); SIG 5,19 €/m². Irlanda paga la "
                                         "placa claramente más cara que el Reino Unido."),
    "MT-PYL-PLACA": ref(7.00, 6.40, 7.60, R_IE,
                        observaciones="Placa estándar de 15 mm: Gyproc WallBoard 2700×1200 "
                                      "(3,24 m²) a 22,72 € ex IVA en TJ O'Mahony → 7,01 €/m²."),
    "MT-PYL-PLACA-IG": ref(9.85, 8.40, 10.50, R_IE,
                           observaciones="Placa cortafuego Gyproc FireLine de 15 mm, hoja "
                                         "2400×1200 (2,88 m²) a 28,41 € ex IVA en TJ O'Mahony "
                                         "→ 9,86 €/m² (la de 12,5 mm: 8,45 €/m²)."),
    "MT-PYL-PLACA-RH": ref(9.00, 8.20, 9.80, R_IE,
                           observaciones="Placa hidrófuga Gyproc Moisture Resistant de 12,5 mm, "
                                         "hoja de 2,88 m² a 25,98 € ex IVA en TJ O'Mahony → "
                                         "9,02 €/m²."),
    "MT-PYL-PLACA-HD": ref(7.50, 6.80, 8.60, R_IE,
                           observaciones="Placa de alta densidad: Gyproc SoundBloc de 12,5 mm, "
                                         "hoja 2438×1200 a 21,91 € ex IVA en TJ O'Mahony → "
                                         "7,49 €/m² (equivalente comercial de la placa de "
                                         "alta dureza)."),
    "MT-PLACA-CEM": ref(10.50, 9.00, 13.00, R_IE,
                        observaciones="Placa de cemento PermaBase 1220×1200×6 mm a 15,41 € ex "
                                      "IVA en TJ O'Mahony → 10,53 €/m²."),
    "MT-PYL-MONT": ref(1.70, 1.45, 2.00, R_IE,
                       observaciones="Montante C de 70 mm × 3,6 m a 6,06 € ex IVA "
                                     "(TJ O'Mahony) → 1,68 €/m."),
    "MT-PYL-CANAL": ref(1.60, 1.40, 1.80, R_IE,
                        observaciones="Canal U de 72 mm × 3,0 m a 4,55-4,96 € ex IVA "
                                      "(Goodwins / TJ O'Mahony) → 1,52-1,65 €/m."),
    "MT-PYL-PASTA": ref(1.75, 1.55, 1.95, R_IE,
                        observaciones="Pasta de juntas Gyproc Joint Filler 25 kg a "
                                      "40,61-48,22 € ex IVA (TJ O'Mahony / Brooks / M.D. O'Shea) "
                                      "→ 1,62-1,93 €/kg."),
    "MT-PYL-PASTA-AGARRE": ref(0.68, 0.60, 0.80, R_IE,
                               observaciones="Adhesivo de placa Gyproc Plasterboard Compound "
                                             "25 kg a 17,03 € ex IVA (TJ O'Mahony) → 0,68 €/kg."),
    "MT-MALLA-ESQ": ref(0.80, 0.70, 1.00, R_IE,
                        observaciones="Cantonera de malla fina de 2,4 m a 1,83 € ex IVA "
                                      "(TJ O'Mahony) → 0,76 €/m."),
    "MT-YESO-REP": ref(0.65, 0.50, 0.75, R_IE,
                       observaciones="Yeso de acabado Gyproc Skimcoat / Carlite Finish 25 kg a "
                                     "13,01-18,54 € ex IVA (McMahons / TJ O'Mahony / M.D. O'Shea) "
                                     "→ 0,52-0,74 €/kg."),
    # ── Adhesivos, juntas y nivelación ───────────────────────────────────────
    "MT-ADH-C2TE": ref(1.15, 1.00, 1.35, R_IE,
                       observaciones="Adhesivo flexible de baldosas 20 kg (Arc Flex/Proflex) a "
                                     "22,36-23,88 € ex IVA (McMahons / Brooks) → 1,12-1,19 €/kg."),
    "MT-ADH-C1": ref(0.80, 0.65, 0.95, R_IE,
                     observaciones="Adhesivo cementoso estándar 20 kg: Arc Rapid Set 16,50 € ex "
                                   "IVA (McMahons); gama económica de Screwfix IE ≈0,71 €/kg "
                                   "sin IVA."),
    "MT-JUN-CG2": ref(2.60, 2.20, 3.20, R_IE,
                      observaciones="Mortero de juntas Arc Pro-Line 5 kg a 12,90 € ex IVA "
                                    "(McMahons) → 2,58 €/kg."),
    "MT-AUT-NIV": ref(1.05, 0.85, 1.30, R_IE,
                      observaciones="Autonivelante 20-25 kg: Evo-Stik 18,09 € ex IVA/20 kg "
                                    "(M.D. O'Shea), Larsen SLC 23,50 €/20 kg, Mapei Ultraplan "
                                    "≈1,06 €/kg sin IVA (Screwfix IE)."),
    "MT-IMP-PRIM": ref(10.50, 8.00, 13.50, R_IE,
                       observaciones="Imprimación de agarre para soportes (Botament BotaGreen "
                                     "Primer 5 kg a 56,52 € ex IVA, Irwin Tiles) → 11,30 €/kg."),
    "MT-GROUT": ref(1.75, 1.40, 2.20, R_IE,
                    observaciones="Grout de retracción compensada SikaGrout-340, saco de 25 kg "
                                  "a 43,50 € ex IVA (M.D. O'Shea) → 1,74 €/kg."),
    "MT-TORN": ref(0.014, 0.010, 0.020, R_IE,
                   observaciones="Tornillos de placa 3,5×25 en caja de 1.000: 10,70-13,70 € ex "
                                 "IVA en McMahons (0,011-0,014 €/ud); en Screwfix IE llegada a "
                                 "0,018 €/ud sin IVA."),
    "MT-SIL-SAN": ref(9.00, 6.50, 12.00, R_IE,
                      observaciones="Silicona sanitaria 310 ml: 8,55-14,45 € con IVA en "
                                    "Screwfix IE → 6,95-11,75 € sin IVA por cartucho."),
    # ── Pinturas y tratamientos de madera ────────────────────────────────────
    # Screwfix IE publica con IVA (23 %): las cifras sin IVA dividen por 1,23.
    "MT-PIN-CAUCHO": ref(5.90, 5.20, 7.00, R_IE,
                         observaciones="Emulsión mate lavable Dulux Trade Vinyl Matt 10 l a "
                                       "69,95-75,95 € con IVA → 5,69-6,17 €/l sin IVA."),
    "MT-PIN-SEMIBRILLO": ref(7.50, 6.00, 10.50, R_IE,
                             observaciones="Emulsión satinada lavable: Dulux Easycare 10 l a "
                                           "75,95 € con IVA (6,17 €/l sin IVA); la gama Diamond "
                                           "llega a 13,65 €/l."),
    "MT-PIN-ESMALTE": ref(16.00, 13.00, 24.00, R_IE,
                          observaciones="Esmalte brillante Dulux Trade High Gloss 2,5 l a "
                                        "47,95 € con IVA → 15,59 €/l sin IVA (el envase de 1 l "
                                        "llega a 24,35 €/l)."),
    "MT-ESMALTE-AGUA": ref(20.00, 16.00, 26.00, R_IE,
                           observaciones="Esmalte al agua satinado Dulux Trade 2,5 l a 62,45 € "
                                         "con IVA → 20,31 €/l sin IVA."),
    "MT-PIN-FONDO": ref(12.00, 7.00, 20.00, R_IE,
                        confianza="derivado",
                        observaciones="Fondo/imprimación: entre el sellador acrílico a granel y "
                                      "el undercoat Dulux Trade de 1 l (23 €/l sin IVA en "
                                      "Screwfix IE). Sin precio único de referencia."),
    "MT-PIN-MASILLA": ref(6.20, 4.50, 7.00, R_IE,
                          observaciones="Masilla/pasta lista al uso: Gyproc Promix Finisher 3 l "
                                        "a 20,04 € ex IVA (Brooks) → 6,68 €/l."),
    "MT-PIN-CAL": ref(0.55, 0.40, 0.80, R_IE,
                      confianza="derivado",
                      observaciones="Cal hidratada en saco de 25 kg de comercio irlandés; "
                                    "estimación (el factor de la familia de pinturas daría "
                                    "un precio absurdo para un mineral a granel)."),
    "MT-BARNIZ-MARINO": ref(24.00, 18.00, 30.00, R_IE,
                            observaciones="Barniz para madera Ronseal 750 ml a 24,45 € con IVA "
                                          "→ 26,5 €/l sin IVA (Screwfix IE); envases mayores "
                                          "bajan el litro."),
    "MT-LASUR": ref(15.50, 12.00, 20.00, R_IE,
                    observaciones="Lasur/protector V33 2,5 l a 44,95-51,45 € con IVA → "
                                  "14,6-16,7 €/l sin IVA (Screwfix IE)."),
    "MT-TINTE-MAD": ref(14.00, 10.00, 19.00, R_IE,
                        confianza="derivado",
                        observaciones="Tinte para madera: estimado sobre la banda de lasures y "
                                      "tintes de Screwfix IE."),
    # ── Fontanería ───────────────────────────────────────────────────────────
    # Nota de mercado: en Irlanda la tubería de PPR es residual; el
    # equivalente funcional es el tubo barrera PE-X de 15 mm (Qual-Pex /
    # Speedfit) o el cobre (15 mm a ≈5,54 €/m sin IVA).
    "MT-PLO-PPR20": ref(1.50, 1.20, 1.90, R_IE,
                        observaciones="Tubo barrera PE-X de 15 mm: bobinas de 25-100 m a "
                                      "1,25-1,85 €/m sin IVA (Screwfix IE). El PPR es "
                                      "residual en el mercado irlandés."),
    "MT-PLO-ACC20": ref(2.80, 2.20, 4.20, R_IE,
                        observaciones="Accesorios push-fit de 15 mm (equivalente irlandés del "
                                      "accesorio de 20 mm): codo JG Speedfit 2,95 € con IVA "
                                      "(2,40 € sin IVA), te 4,95 € con IVA (4,02 € sin IVA) "
                                      "en Screwfix IE."),
    "MT-PLO-PVC4": ref(5.60, 4.80, 6.80, R_IE,
                       observaciones="Tubería de saneamiento enterrado de 110 mm × 3 m a "
                                     "20,45 € con IVA (Screwfix IE) → 5,54 €/m sin IVA."),
    "MT-PLO-ACC4": ref(8.00, 5.00, 16.00, R_IE,
                       observaciones="Accesorios de 110 mm: manguito 5,65 € sin IVA; codo "
                                     "ajustable 20,28 € sin IVA (Screwfix IE). Precio medio "
                                     "de accesorio corriente."),
    # ── Electricidad ─────────────────────────────────────────────────────────
    "MT-ELE-CAJA": ref(1.40, 1.10, 1.90, R_IE,
                       observaciones="Caja de mecanismo de empotrar de 2 módulos: acero "
                                     "galvanizado 1,45-1,65 € con IVA (1,18-1,34 € sin IVA); "
                                     "de superficie 2,15 € con IVA, en Screwfix IE."),
    "MT-ELE-CABLE": ref(1.60, 1.40, 2.10, R_IE,
                        observaciones="Cable twin & earth de 2,5 mm²: bobina de 100 m a "
                                      "174-188 € con IVA en Screwfix IE (1,42-1,53 €/m sin "
                                      "IVA); almacén eléctrico irlandés a 2,09 €/m neto."),
    # ── Aislamiento e impermeabilización ─────────────────────────────────────
    "MT-POLIESTIRENO-EXT": ref(13.50, 9.00, 20.00, R_IE,
                               confianza="derivado",
                               observaciones="XPS de 50-75 mm de comercio irlandés; como techo "
                                             "de la banda, el PIR de 100 mm observado a "
                                             "19,7-22,2 €/m² sin IVA (TJ O'Mahony / Brooks)."),
    "MT-LANA-ROCA": ref(14.00, 11.00, 20.00, R_IE,
                        observaciones="Panel de lana de roca de 100 mm (Rockwool FLEXI) a "
                                      "13,88 €/m² sin IVA en comercio; la lista oficial "
                                      "Rockwool ROI (36,05 €/m²) es precio antes de descuento."),
    "MT-GEOTEXTIL": ref(0.65, 0.45, 1.20, R_IE,
                        observaciones="Geotextil Tencate en rollo: TS1000 226,83 € ex IVA/450 m² "
                                      "(0,50 €/m²) y Polyfelt TS40 325,16 €/400 m² (0,81 €/m²), "
                                      "TJ O'Mahony."),
    "MT-TUBO-DREN": ref(3.20, 2.60, 4.50, R_IE,
                        observaciones="Tubo de drenaje perforado de 110 mm × 6 m a "
                                      "15,69-18,70 € ex IVA (Goodwins) → 2,61-3,12 €/m, con "
                                      "recargo por la funda de geotextil."),
    # ── Madera y tableros ────────────────────────────────────────────────────
    "MT-MADERA-EST": ref(560, 480, 720, R_IE,
                         observaciones="Madera tratada C16 de 100×44×4,8 m a 10,37 € ex IVA la "
                                       "pieza (TJ O'Mahony) → 491 €/m³; C24 y secciones "
                                       "mayores llegan a ≈720 €/m³."),
    "MT-MADERA-LISTON": ref(2.20, 1.60, 3.20, R_IE,
                            observaciones="Listón tratado de 100×44 mm a 10,37 € ex IVA los "
                                          "4,8 m (TJ O'Mahony) → 2,16 €/m."),
    "MT-LAMINA-OSB": ref(9.50, 8.00, 11.00, R_IE,
                         observaciones="OSB3 de 18 mm, hoja 2440×1220 (2,98 m²) a "
                                       "29,95-39,95 € con IVA → 8,18-10,91 €/m² sin IVA."),
    # ── Residuos ─────────────────────────────────────────────────────────────
    # Desde septiembre de 2024 el residuo de construcción y demolición paga
    # 10 €/t (recovery levy y tipo reducido de vertedero, S.I. 442/2024);
    # el vertido general sigue a 85 €/t. El canon mezclado se valora por la
    # vía real de la obra pequeña: el contenedor (skip) de 6 yardas cuesta
    # 349-400 € con IVA en Dublín para ≈4,6 m³.
    "MT-CANON": ref(55, 42, 75, R_IE,
                    observaciones="Retirada de escombro mezclado por m³ vía skip de 6 yardas "
                                  "(349-400 € con IVA ≈ 62-71 €/m³ sin IVA a plena carga), "
                                  "con el gravamen de 10 €/t del residuo C&D ya repercutido."),
    "MT-CANON-TIERRA": ref(30, 20, 45, R_IE,
                           observaciones="Vertido de tierra inerte en instalación de recuperación: "
                                         "gravamen de 10 €/t + puerta de 10-20 €/t, a 1,6 t/m³."),
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
        referencias[codigo] = {"IE": dato}
    for codigo, dato in MATERIALES.items():
        if codigo in referencias:
            raise ValueError(f"{codigo} definido dos veces")
        referencias[codigo] = {"IE": dato}
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

    El factor es la mediana de (precio irlandés investigado / precio base
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
        dato = por_pais.get("IE")
        if ficha is None or dato is None or dato.confianza != "referencia":
            continue
        categoria = ficha[0]
        if categoria == "mano_obra":
            continue
        base_local = float(ficha[1]["precio"]) * TASAS_CORTE["IE"]
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
        if referencias.get(codigo, {}).get("IE") is not None:
            continue
        base_local = float(item["precio"]) * TASAS_CORTE["IE"]
        factor = factores_familia.get((categoria, _familia(codigo)))
        origen = f"familia {_familia(codigo)}"
        if factor is None:
            factor = factores_categoria[categoria]
            origen = f"categoría {categoria}"
        referencias.setdefault(codigo, {})["IE"] = replace(
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
        dato = referencias.get(codigo, {}).get("IE")
        if dato is None:
            raise SystemExit(f"Sin referencia para {codigo}")
        filas.append({
            "codigo_recurso": codigo,
            "descripcion": item["descripcion"],
            "categoria": categoria,
            "unidad_fuente": item["unidad"],
            "pais_codigo": "IE",
            "moneda": "EUR",
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
    print(f"Matriz irlandesa escrita en {OUT.relative_to(ROOT)}")
    print(f"  {total} recursos · {investigados} investigados "
          f"({investigados / total:.0%}) · {derivados} derivados por factor")
    print(f"  tasa de corte: 1 USD = {TASAS_CORTE['IE']:.4f} EUR (EUR/USD 1,1253, BCE 16/10/2026)")
    print()
    print("  Factores por categoría (mediana de precio irlandés / base convertida):")
    for categoria, factor in sorted(factores_categoria.items()):
        print(f"    {categoria:12s} {factor:8.3f}")
    print()
    print(f"  Familias con ancla propia: {len(factores_familia)}")
    for (categoria, familia), factor in sorted(factores_familia.items()):
        n = len([1 for c, d in referencias.items()
                 if d.get("IE") and d["IE"].confianza == "referencia"
                 and _familia(c) == familia and c in
                 {x for x, cat, _ in iter_recursos(data) if cat == categoria}])
        print(f"    {familia:22s} {factor:8.3f}  ({n} anclas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
