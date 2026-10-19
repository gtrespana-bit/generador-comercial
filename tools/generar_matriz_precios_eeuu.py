#!/usr/bin/env python3
"""Genera la matriz de precios de recursos para Estados Unidos (USD).

Replica el contrato de ``generar_matriz_precios_irlanda.py``,
``generar_matriz_precios_australia.py`` y
``generar_matriz_precios_canada.py``:

* Los precios base de ``basedatos_partidas/datos/recursos.json`` están en USD
  con ámbito **Venezuela**. Que coincida la moneda no los convierte en
  precios estadounidenses: la matriz se construye desde precios de EE. UU.
  reales y el factor de familia se calcula sin conversión de divisa
  (tasa de corte 1,0).
* Las anclas investigadas se publican tal cual, con rango, fuente y fecha.
* El resto se cubre con un **factor de mercado por familia**, calculado como
  la mediana de la relación entre el precio de EE. UU. investigado y el
  precio base de cada ancla de esa familia.
* La mano de obra no usa factores: los 17 oficios salen del modelo de coste
  empresa de ``coste_empresa_eeuu.py``.

Particularidades de Estados Unidos (el único mercado imperial del producto):

* **El precio publicado es siempre antes de impuestos.** El «sales tax» se
  añade en caja y varía por estado/condado/ciudad, así que la cifra de
  estantería (Home Depot, Lowe's) y las listas de planta ya son sin
  impuesto y entran tal cual, como en Canadá. En la mayoría de los estados,
  además, es el contratista quien soporta ese impuesto al comprar (ver el
  análisis de mercado), así que el precio de referencia ex-impuesto es el
  comparable con el resto de matrices.
* **El formato comercial es imperial y la matriz se publica convertida a
  la unidad métrica del recurso**: hormigón por yarda cúbica y clase PSI,
  cemento en sacos de 94 lb, placa de yeso de 4×8 ft, bloque CMU de
  8×8×16", adhesivos en sacos de 50 lb, pintura por galón US, tubería por
  pie, alquiler por día. Cada conversión queda en la observación del
  ancla, con el formato nativo citado (1 yd³ = 0,7646 m³; 1 gal US =
  3,785 l; 1 lb = 0,4536 kg; 1 ft = 0,3048 m). Publicar la matriz en
  unidades imperiales rompería la carga por SQL, que inserta el precio
  tal cual (la conversión automática solo existe en el importador del
  panel, como red de seguridad para ficheros del operador).
* Equivalencias de mercado declaradas: la tubería de agua es PEX (el PPR
  es residual); el conductor de referencia es el THHN de cobre en bobina
  de 500 ft (no el «Romex», que es cable completo); el adhesivo
  cementoso corriente es el «thinset» modificado ANSI A118.4/.11; la
  clase de hormigón se mapea kg/cm² → PSI (180≈2.500; 210≈3.000;
  250≈3.500; 300≈4.000).
* Sin escala legal sectorial: la mano de obra parte de la **mediana
  nacional del BLS (OEWS)**, con rango −15 % / +35 % por la dispersión
  estatal/metro y sindical.

Uso:
    python3 tools/generar_matriz_precios_eeuu.py
"""
from __future__ import annotations

import csv
import json
import statistics
from dataclasses import dataclass, replace
from pathlib import Path

from coste_empresa_eeuu import HORAS_FACTURABLES, OFICIOS, WC, coste_empresa

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "basedatos_partidas/datos/recursos.json"
OUT = ROOT / "basedatos_partidas/salida/precios_recursos_estados_unidos.csv"
PAISES = (("US", "USD"),)
FECHA = "2026-10-19"

R_US = "docs/INVESTIGACION_PRECIOS_ESTADOS_UNIDOS.md"
METODOLOGIA = "docs/METODOLOGIA_PRECIOS_REFERENCIA_ESTADOS_UNIDOS.md"
# La base del catálogo ya está en USD (ámbito Venezuela): no hay conversión
# de divisa, solo de nivel de precio. La tasa 1,0 hace explícito que el
# factor de familia es precio EE. UU. ÷ precio base en la misma moneda.
TASAS_CORTE = {"US": 1.0}

OBS_REFERENCIA = (
    "Precio de mercado de Estados Unidos observado (sin «sales tax» — el "
    "precio publicado en EE. UU. es siempre antes de impuestos —, sin porte "
    "salvo indicación); puede variar por proveedor, marca, volumen y estado."
)
OBS_DERIVADO = (
    "Precio referencial derivado del factor de mercado de su familia, calculado "
    "sobre la canasta de precios de Estados Unidos investigada; no es una cotización de tienda."
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


def ref(precio, minimo, maximo, fuente=R_US, **kwargs) -> Referencia:
    precio, minimo, maximo = map(float, (precio, minimo, maximo))
    if minimo <= 0 or maximo < minimo or not minimo <= precio <= maximo:
        raise ValueError(f"Rango inválido: {minimo} <= {precio} <= {maximo}")
    return Referencia(precio, minimo, maximo, fuente, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Mano de obra — modelo de coste empresa de Estados Unidos
# ─────────────────────────────────────────────────────────────────────────────

def referencias_mano_obra() -> dict[str, dict[str, Referencia]]:
    salida: dict[str, dict[str, Referencia]] = {}
    for codigo, (oficio, salario, escala, clase) in OFICIOS.items():
        coste = coste_empresa(salario, WC[clase])["coste_hora_facturable"]
        # La base es la mediana nacional OEWS, no un mínimo legal, así que
        # el rango baja −15 % (estados del interior/sur, residencial rural)
        # y sube +35 % (metros costeras, tracción sindical, empleador con
        # seguro médico y 401(k)). Los paquetes sindicales de las grandes
        # metros quedan aun por encima y se documentan en la investigación.
        salida[codigo] = {
            "US": ref(
                coste,
                coste * 0.85,
                coste * 1.35,
                R_US,
                confianza="referencia",
                incluye_iva="no_aplica",
                incluye_transporte="no_aplica",
                observaciones=(
                    f"Coste empresa por hora trabajada. {oficio}. Salario "
                    f"ordinario {salario:.2f} $/h ({escala}, a octubre de "
                    f"2026) × 2.080 h pagadas, FICA empresarial 7,65 % "
                    f"(Seguridad Social con base 184.500 $), FUTA neto 0,6 % "
                    f"y SUTA 2,7 % representativos, workers' compensation "
                    f"de la clase {clase} ({WC[clase] * 100:.2f} $/100 $ de "
                    f"nómina) y gastos fijos, dividido por "
                    f"{HORAS_FACTURABLES:,.0f} h trabajadas/año (239 días de "
                    f"8 h tras vacaciones, festivos y bajas). No es tarifa "
                    f"de subcontrata: el catálogo ya aplica un 35 % de "
                    f"margen sobre el coste directo."
                ),
            )
        }
    return salida


# ─────────────────────────────────────────────────────────────────────────────
# 2. Maquinaria — tarifas de alquiler de Estados Unidos
#
#    United Rentals publica tarifas «online exclusive» por mercado (las
#    agregan las guías por metro de 2026) y Home Depot Tool Rental fija
#    precios por tienda con mínimo de 4 h; las anclas reproducibles son la
#    banda UR por día para plancha/miniexcavadora y las listas públicas de
#    alquileres independientes (doitatdukes, Central Tool Rental
#    Cincinnati, Grants Pass Rental mar-2026, TC Rentals). El resto se
#    publica «derivado» con precio explícito por analogía documentada.
#    Día de 8 h, sin «sales tax» ni combustible; con operador solo donde
#    se indica (bomba, grúa, perforadora, volqueta).
# ─────────────────────────────────────────────────────────────────────────────

def _alquiler(dia, minimo, maximo, nota="", confianza="referencia") -> Referencia:
    return ref(
        dia / 8.0, minimo / 8.0, maximo / 8.0, R_US,
        confianza=confianza,
        observaciones=(
            f"Alquiler en EE. UU. {minimo:.0f}-{maximo:.0f} $/día (jornada de 8 h), "
            f"sin «sales tax» ni combustible. {nota}".strip()
        ),
    )


MAQUINARIA: dict[str, Referencia] = {
    # Corte y demolición
    "MQ-CORT-AGUA": _alquiler(58, 45, 75, "Sierra húmeda de cerámica: banda "
                              "de Home Depot Tool Rental y guías 2026 "
                              "(55-60 $/día típico)."),
    "MQ-ROZAD": _alquiler(95, 75, 125, "Rozadora con aspiración; analogía "
                          "con la banda de corte de hormigón de alquiler.",
                          confianza="derivado"),
    "MQ-MART-ELEC": _alquiler(65, 50, 85, "Martillo demoledor eléctrico de "
                              "15-35 lb (40-70 $/día en guías 2026; «electric "
                              "jack hammer» 85 $/día en listas públicas)."),
    "MQ-AMOLA": _alquiler(30, 20, 45, "Amoladora angular grande (7\"): banda "
                          "de herramienta pequeña de alquiler por día."),
    "MQ-SIERRA": _alquiler(75, 60, 100, "Motosierra de 16-20\": listas "
                           "públicas 2026 entre 65 $/día (16\") y 90-100 $/día "
                           "(20\" con cadena nueva y combustible)."),
    "MQ-OXICORTE": _alquiler(80, 60, 105, "Equipo de oxicorte con botellas.",
                             confianza="derivado"),
    "MQ-CIZALLA": _alquiler(90, 70, 120, "Corta-dobladora de barra de "
                            "alquiler especializado.", confianza="derivado"),
    "MQ-ESMERIL": _alquiler(105, 85, 135, "Amoladora/pulidora de suelo de "
                            "mano.", confianza="derivado"),
    # Hormigón
    "MQ-MEZCL": _alquiler(80, 60, 110, "Hormigonera de 3,5-6 ft³.",
                          confianza="derivado"),
    "MQ-BATID": _alquiler(45, 35, 60, "Batidora de paleta.",
                          confianza="derivado"),
    "MQ-VIBRADOR": _alquiler(65, 50, 85, "Vibrador de aguja con unidad "
                             "motriz.", confianza="derivado"),
    "MQ-ALISADORA": _alquiler(115, 90, 145, "Alisadora helicóptero (power "
                              "trowel).", confianza="derivado"),
    "MQ-BOMBA-CONC": _alquiler(1500, 1200, 1900, "Bomba de hormigón **con "
                               "operador**: se cobra por salida más $/yd³ "
                               "bombeada; jornada estimada.",
                               confianza="derivado"),
    "MQ-PROYECT-MORT": _alquiler(190, 150, 240, "Bomba de estuco/mortero "
                                 "con compresor.", confianza="derivado"),
    # Compactación y movimiento de tierras
    "MQ-COMPACT-SALTO": _alquiler(95, 80, 120, "Pisón de impacto («jumping "
                                  "jack»/rammer), banda UR 2026.",
                                  confianza="derivado"),
    "MQ-PLANCHA-COMP": _alquiler(105, 85, 130, "Plancha vibratoria: "
                                 "tarifas por día de United Rentals en "
                                 "metros 2026 entre 95 y 115 $."),
    "MQ-RETRO": _alquiler(475, 395, 600, "Miniexcavadora de ≈3,5-5 t en "
                          "seco (United Rentals 280-420 $/día según metro "
                          "y tamaño) + martillo hidráulico (≈80-120 $/día); "
                          "el operador va en la mano de obra de la partida."),
    "MQ-MART-NEUM": _alquiler(230, 190, 290, "Compresor de obra con "
                              "martillo neumático.", confianza="derivado"),
    "MQ-PERF-PILOTE": _alquiler(3000, 2400, 3800, "Equipo de perforación "
                                "de pilotes **con operador**; alquiler "
                                "especializado por proyecto, sin tarifa "
                                "pública.", confianza="derivado"),
    # Elevación y acceso
    "MQ-ANDAMIO": _alquiler(110, 85, 150, "Torre móvil de andamio; como "
                            "banda, la plataforma de tijera de 19 ft se "
                            "alquila en EE. UU. a 120-200 $/día.",
                            confianza="derivado"),
    "MQ-MONTAC": _alquiler(155, 120, 200, "Montacargas de material / "
                           "elevador tipo Genie.", confianza="derivado"),
    "MQ-VENT-SUC": _alquiler(40, 30, 55, "Juego de ventosas de elevación "
                             "de gran formato.", confianza="derivado"),
    "MQ-GRUA": _alquiler(1600, 1300, 2000, "Grúa móvil **con operador** "
                         "(«wet hire» ≈180-240 $/h).", confianza="derivado"),
    # Instalaciones y acabados
    "MQ-ATORN": _alquiler(35, 25, 50, "Atornilladora para placa («screw "
                          "gun»).", confianza="derivado"),
    "MQ-LIJAD": _alquiler(75, 60, 100, "Lijadora de pared con aspiración.",
                          confianza="derivado"),
    "MQ-PULIDORA": _alquiler(95, 75, 120, "Pulidora de piedra/hormigón.",
                             confianza="derivado"),
    "MQ-LIJAD-PISO": _alquiler(125, 100, 160, "Lijadora de tambor de pisos "
                               "+ orilladora (juego de alquiler).",
                               confianza="derivado"),
    "MQ-ESTAMP": _alquiler(135, 105, 170, "Moldes de hormigón impreso "
                           "(juego).", confianza="derivado"),
    "MQ-SOLDADORA": _alquiler(65, 50, 85, "Soldadora MIG/inverter.",
                              confianza="derivado"),
    "MQ-TERMOF": _alquiler(55, 40, 75, "La termofusión PPR es residual en "
                           "EE. UU. (PEX de expansión/crimpado): equipo de "
                           "expansión PEX por analogía.",
                           confianza="derivado"),
    "MQ-DOBLAD-TUBO": _alquiler(40, 30, 55, "Dobladora de tubo y kit de "
                                "abocardado.", confianza="derivado"),
    "MQ-RECUP-GAS": _alquiler(105, 85, 140, "Recuperadora de refrigerante "
                              "y bomba de vacío.", confianza="derivado"),
    "MQ-INYECTORA": _alquiler(115, 90, 150, "Equipo de inyección de "
                              "resinas a baja presión.",
                              confianza="derivado"),
    "MQ-RODILLO": _alquiler(22, 15, 30, "Equipo de aplicación: rodillos, "
                            "brochas, cubetas y escalera, amortizado.",
                            confianza="derivado"),
    # Limpieza, achique y seguridad
    "MQ-ASPIR": _alquiler(60, 45, 80, "Aspirador industrial con filtro "
                          "HEPA.", confianza="derivado"),
    "MQ-HIDROLAV": _alquiler(65, 50, 85, "Hidrolavadora de gasolina "
                             "2.400-3.100 psi: 60-65 $/día en Home Depot "
                             "Tool Rental y listas públicas 2026."),
    "MQ-BOMBA-ACHI": _alquiler(45, 35, 60, "Bomba de achique: sumergible "
                               "eléctrica de 2\" a 30-35 $/día y «trash "
                               "pump» de gasolina de 2\" a 40-56 $/día en "
                               "listas públicas 2026."),
    "MQ-DESBROZ": _alquiler(50, 40, 65, "Desbrozadora («brush cutter»).",
                            confianza="derivado"),
    # Medición y detección
    "MQ-NIVEL-LASER": _alquiler(70, 55, 90, "Nivel láser rotativo.",
                                confianza="derivado"),
    "MQ-DETECTOR": _alquiler(80, 60, 105, "Localizador de servicios "
                             "enterrados («line locator»).",
                             confianza="derivado"),
    "MQ-TALADRO": _alquiler(45, 35, 65, "Taladro percutor SDS.",
                            confianza="derivado"),
    "MQ-TELUROMETRO": _alquiler(95, 75, 130, "Medidor de resistencia de "
                                "tierra y equipo de comprobación eléctrica.",
                                confianza="derivado"),
    # Transporte
    "MQ-VOLQ": _alquiler(950, 800, 1200, "Camión volqueta **con chofer** "
                         "(«dump truck» con conductor ≈110-150 $/h).",
                         confianza="derivado"),
    # Unidad distinta: el baño portátil se alquila por mes.
    "MQ-BANO-PORT": ref(
        260, 210, 330, R_US,
        confianza="derivado",
        observaciones=(
            "Alquiler mensual de baño portátil de obra («porta-potty») con "
            "servicio semanal (recurso medido en unidades, no en horas). "
            "Sin «sales tax». Banda de mercado de EE. UU. 2026."
        ),
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# 3. Materiales — precios de proveedor de Estados Unidos
#
#    Todos los precios son sin «sales tax» (la estantería estadounidense
#    publica antes de impuestos y entra tal cual). Fuentes: Home Depot y
#    Lowe's (retail nacional, oct-2026), listas publicadas de plantas de
#    hormigón (Supreme Concrete sep-2026; Gehring Construction lista
#    01/01/2026; American Concrete Augusta abr-2026) con la media NRMCA
#    como contraste, mercado siderúrgico (Kallanish/IndexBox oct-2026) y
#    guías nacionales 2026 para áridos y gestión de residuos. Todas las
#    conversiones imperial→métrico quedan en la observación de cada ancla.
# ─────────────────────────────────────────────────────────────────────────────

MATERIALES: dict[str, Referencia] = {
    # Hormigón preparado: listas publicadas $/yd³ por clase PSI (el
    # recurso se mide en m³: ×1,30795). Supreme Concrete (New York, sep-2026):
    # 3.000 PSI 127,05 · 4.000 132,00 · 5.000 137,50; Gehring (Nebraska,
    # lista 01/01/2026): 3.000 PSI 148; American Concrete (Georgia, abr-2026):
    # 3.000 174 · 4.000 182; media de productores NRMCA 2023 ≈160 $/yd³.
    # Se adoptan puntos medios de lista; recargos de carga corta y porte
    # fuera de zona quedan fuera.
    "MT-CONC-180": ref(189.65, 172.00, 215.00, R_US, observaciones=(
        "Hormigón preparado ≈2.500 PSI a 145 $/yd³ de lista → $/m³ "
        "(×1,30795). Clase 180 kg/cm² ≈ 2.560 psi.")),
    "MT-CONC-210": ref(198.81, 180.00, 225.00, R_US, observaciones=(
        "Hormigón preparado 3.000 PSI a 152 $/yd³ de lista → $/m³. Es la "
        "clase corriente de losas y cimentación residencial.")),
    "MT-CONC-250": ref(209.27, 190.00, 238.00, R_US, observaciones=(
        "Hormigón preparado 3.500 PSI a 160 $/yd³ de lista → $/m³.")),
    "MT-CONC-300": ref(219.74, 199.00, 250.00, R_US, observaciones=(
        "Hormigón preparado 4.000 PSI a 168 $/yd³ de lista → $/m³.")),
    # Cemento Portland en saco de 94 lb (42,64 kg): estantería Home Depot /
    # Lowe's oct-2026 entre 17,21 y 20,49 $ según metro (18,44-19,77 lo
    # corriente); se adoptan 19,00 $/saco.
    "MT-CEMENTO": ref(0.446, 0.399, 0.481, R_US, observaciones=(
        "Cemento Portland tipo I/II en saco de 94 lb a 19,00 $ → $/kg.")),
    # Áridos a granel por yarda cúbica recogidos en planta (guías
    # nacionales 2026 y tarifas de cantera publicadas), ×1,30795 a m³.
    "MT-ARENA": ref(52.32, 39.00, 65.00, R_US, observaciones=(
        "Arena de construcción/«mason sand» a granel a 40 $/yd³ (banda "
        "30-45) → $/m³, recogida en planta.")),
    "MT-PIEDRA-PIC": ref(65.40, 46.00, 85.00, R_US, observaciones=(
        "Piedra triturada de ¾\" (#57) a 50 $/yd³ (banda 35-65 $/yd³ o "
        "35-58 $/t) → $/m³, recogida en cantera.")),
    "MT-MAT-PRESTAMO": ref(49.70, 33.00, 65.00, R_US, observaciones=(
        "Granular de base («crusher run» / «road base») a 38 $/yd³ → "
        "$/m³, recogido en planta.")),
    "MT-AGUA-OBRA": ref(4.20, 3.40, 5.20, R_US, confianza="derivado",
                        observaciones=(
        "Agua de obra: suministro municipal temporal y pérdidas, por "
        "analogía con las matrices anglófonas.")),
    "MT-ADITIVO": ref(4.00, 2.90, 5.40, R_US, confianza="derivado",
                      observaciones=(
        "Aditivo plastificante/acelerante en envase profesional, por "
        "analogía de familia con el cemento.")),
    "MT-CURADOR": ref(5.50, 4.00, 7.00, R_US, confianza="derivado",
                      observaciones=(
        "Compuesto de curado en bidón profesional (equivalentes tipo "
        "«cure & seal») por analogía.")),
    "MT-DESMOLD": ref(6.00, 4.50, 7.80, R_US, confianza="derivado",
                      observaciones=(
        "Desencofrante («form release») en bidón profesional por "
        "analogía.")),
    # Acero de refuerzo: «spot» doméstico #4 en barras de 20 ft a
    # 870-970 $/t corta (Kallanish ene-oct 2026; IndexBox 09/10/2026:
    # 1.033 $/t EXW); el precio de suministro al contratista en largos
    # comerciales se adopta a 1.200 $/t corta (0,60 $/lb → 1,32 $/kg). El
    # equivalente de estantería (barras sueltas) llega a ≈0,94 $/lb y
    # queda dentro del rango.
    "MT-ACERO-CAB": ref(1.32, 1.05, 1.65, R_US, observaciones=(
        "Barra corrugada Grado 60 a 1.200 $/tonelada corta de suministro "
        "(0,60 $/lb) → $/kg; sin corte ni doblado.")),
    "MT-MALLA-ELEC": ref(5.50, 4.75, 8.75, R_US, observaciones=(
        "Malla electrosoldada 6×6 en hoja («remesh sheet» 42\"×84\" a "
        "10,87-19,98 $ en Home Depot) → $/m².")),
    "MT-PERFIL-ACERO": ref(2.40, 2.00, 3.00, R_US, confianza="derivado",
                           observaciones=(
        "Perfiles y angulares de almacén siderúrgico por analogía con "
        "la barra (el estructural de molino cotiza a 2.340-2.480 $/t).")),
    "MT-PLANCHA-ACERO": ref(2.70, 2.20, 3.40, R_US, confianza="derivado",
                            observaciones=(
        "Chapa de acero de almacén por analogía con el perfil.")),
    "MT-FORM-MADERA": ref(9.00, 7.00, 11.50, R_US, confianza="derivado",
                          observaciones=(
        "Madera de encofrado amortizada por reutilización (tablas y "
        "contrachapado de obra) por analogía con el listón.")),
    "MT-POLIET": ref(0.50, 0.35, 0.70, R_US, confianza="derivado",
                     observaciones=(
        "Lámina de polietileno de obra (6 mil) en rollo por analogía.")),
    # Bloque CMU estándar 8×8×16" (hueco): Home Depot oct-2026 entre 1,85
    # y 2,85 $ según región (2,38 lo corriente); guías 2026: 1,90-2,60.
    "MT-BLQ-20": ref(2.40, 1.85, 2.90, R_US, observaciones=(
        "Bloque de hormigón hueco de 8×8×16\" (≈20×20×40 cm) de "
        "estantería nacional.")),
    "MT-BLQ-15": ref(2.30, 1.85, 2.75, R_US, confianza="derivado",
                     observaciones=(
        "Bloque de 6×8×16\" por escalado del de 8\" (la estantería lo "
        "sitúa apenas por debajo: 2,38-2,70 $).")),
    "MT-BLQ-10": ref(1.75, 1.40, 2.10, R_US, confianza="derivado",
                     observaciones=(
        "Bloque de 4×8×16\" por escalado del de 8\" (guías 2026: "
        "1,30-1,90 $).")),
    "MT-LADRILLO-VISTO": ref(0.85, 0.65, 1.15, R_US, confianza="derivado",
                             observaciones=(
        "Ladrillo cara vista modular por analogía con el bloque (la "
        "estantería de «face brick» ronda 0,60-1,00 $/ud).")),
    # Placa de yeso ½" 4×8 ft (2,967 m²): USG UltraLight en Home Depot
    # oct-2026 entre 12,98 y 16,68 $ según metro (10,64-14,18 por
    # volumen ≥34); se adoptan 15,00 $/hoja.
    "MT-PYL-PLACA125": ref(5.05, 4.37, 5.62, R_US, observaciones=(
        "Panel de yeso estándar de ½\" en hoja de 4×8 ft a 15,00 $ → "
        "$/m².")),
    "MT-PYL-PLACA": ref(6.20, 5.20, 7.40, R_US, confianza="derivado",
                        observaciones=(
        "Panel de ⅝\" por escalado del de ½\" (hoja 4×8 ≈18-19 $).")),
    "MT-PYL-PLACA-IG": ref(6.55, 5.50, 7.80, R_US, confianza="derivado",
                           observaciones=(
        "Panel resistente al fuego ⅝\" tipo X por escalado del "
        "estándar.")),
    "MT-PYL-PLACA-RH": ref(7.45, 6.20, 8.90, R_US, confianza="derivado",
                           observaciones=(
        "Panel resistente a humedad/moho («Mold Tough» ½\" a "
        "19,98-24,58 $/hoja 4×8) → $/m².")),
    "MT-PYL-PLACA-HD": ref(8.10, 6.80, 9.70, R_US, confianza="derivado",
                           observaciones=(
        "Panel de alta dureza/abuso por escalado del resistente a la "
        "humedad.")),
    "MT-PLACA-CEM": ref(11.50, 9.40, 14.00, R_US, confianza="derivado",
                        observaciones=(
        "Placa de cemento («cement board»): ¼\" 4×8 a 27,98 $ (≈9,4 "
        "$/m²) y ½\" 3×5 ft (≈11,5 $/m²) en Home Depot.")),
    "MT-PYL-MONT": ref(2.40, 2.00, 3.00, R_US, confianza="derivado",
                       observaciones=(
        "Montante metálico 3-⅝\" de 10 ft (≈7,3 $) → $/m.")),
    "MT-PYL-CANAL": ref(2.20, 1.85, 2.75, R_US, confianza="derivado",
                        observaciones=(
        "Canal/track metálico por escalado del montante.")),
    # Pasta de juntas preparada: USG Plus 3 en cubo de 4,5 gal US
    # (17,0 l ≈ 21,8 kg) a 22,45-24,50 $ (19,08-20,83 por volumen);
    # se adoptan 23,50 $.
    "MT-PYL-PASTA": ref(1.08, 0.95, 1.25, R_US, observaciones=(
        "Pasta de juntas lista para usar en cubo de 4,5 gal a 23,50 $ → "
        "$/kg (incluye la cinta por analogía de familia).")),
    # Compuesto de fraguado («hot mud»): USG Easy Sand 90 en saco de
    # 18 lb (8,16 kg) ≈14 $.
    "MT-PYL-PASTA-AGARRE": ref(1.71, 1.45, 2.00, R_US, observaciones=(
        "Pasta de agarre/fraguado tipo Easy Sand 90 en saco de 18 lb a "
        "≈14 $ → $/kg.")),
    "MT-MALLA-ESQ": ref(0.85, 0.65, 1.10, R_US, confianza="derivado",
                        observaciones=(
        "Guardavivos («corner bead») de 8-10 ft por analogía con el "
        "perfil metálico.")),
    "MT-YESO-REP": ref(2.30, 1.75, 3.00, R_US, confianza="derivado",
                       observaciones=(
        "Yeso de reparación («plaster») en saco pequeño por analogía "
        "con la pasta de fraguado.")),
    # Lana mineral en manta: ROCKWOOL Safe'n'Sound de 3" a 1,40 $/ft² en
    # Home Depot (banda de mercado 1,40-2,10 $/ft² para R-15); el recurso
    # es de 60 mm y el mercado vende 3" (76 mm): se publica el formato
    # comercial equivalente, ×10,7639 a $/m².
    "MT-PYL-LANA": ref(15.07, 13.50, 19.50, R_US, observaciones=(
        "Manta de lana de roca de 3\" (formato comercial del recurso de "
        "60 mm) a 1,40 $/ft² → $/m².")),
    # Adhesivos de baldosa en saco de 50 lb (22,68 kg) en Home Depot:
    # VersaBond (C1≈A118.4) 14,97 $; VersaBond-LFT (C2TE≈A118.11)
    # 19,97-21,97 $.
    "MT-ADH-C2TE": ref(0.92, 0.85, 1.10, R_US, observaciones=(
        "Thinset modificado de gran formato (VersaBond-LFT, saco de "
        "50 lb a 20,97 $) → $/kg.")),
    "MT-ADH-C1": ref(0.66, 0.59, 0.79, R_US, observaciones=(
        "Thinset estándar modificado (VersaBond, saco de 50 lb a "
        "14,97 $) → $/kg.")),
    "MT-JUN-CG2": ref(1.41, 1.28, 1.76, R_US, observaciones=(
        "Mortero de juntas con arena de altas prestaciones (Polyblend "
        "Plus ANSI A118.7, saco de 25 lb a ≈16 $) → $/kg.")),
    "MT-AUT-NIV": ref(1.94, 1.80, 2.05, R_US, observaciones=(
        "Autonivelante cementoso (Quikrete Fast-Setting Self-Leveling, "
        "saco de 50 lb a 44 $) → $/kg.")),
    "MT-IMP-PRIM": ref(8.00, 5.75, 10.75, R_US, confianza="derivado",
                       observaciones=(
        "Imprimación selladora profesional (≈30 $/gal) por analogía "
        "con la pintura.")),
    "MT-GROUT": ref(1.01, 0.93, 1.10, R_US, observaciones=(
        "Grout fluido sin retracción (Quikrete Non-Shrink Precision "
        "Grout, saco de 50 lb a 22,97 $) → $/kg.")),
    "MT-GROUT-CELDA": ref(215, 195, 245, R_US, confianza="derivado",
                          observaciones=(
        "Grout de relleno de celdas servido como hormigón fino de "
        "planta, por analogía con el MT-CONC-210 (+8 % por el árido "
        "fino).")),
    "MT-TORN": ref(0.016, 0.011, 0.024, R_US, confianza="derivado",
                   observaciones=(
        "Tornillo para placa a granel de contratista (caja de 25 lb) "
        "por analogía de familia.")),
    "MT-SIL-SAN": ref(11.00, 8.00, 14.00, R_US, confianza="derivado",
                      observaciones=(
        "Silicona sanitaria en cartucho de 10,1 oz de estantería "
        "profesional.")),
    # Pintura látex interior de contratista: ProMar 200 con cuenta
    # profesional a 28-36 $/gal (lista 40-50; contrato institucional
    # 2025-26: 26,24-29,32); se adoptan 40 $/gal US como precio
    # corriente sin cuenta especial → $/l (÷3,785).
    "MT-PIN-CAUCHO": ref(10.57, 7.93, 14.52, R_US, observaciones=(
        "Pintura látex acrílica mate de contratista a 40 $/gal US → "
        "$/l.")),
    "MT-PIN-SEMIBRILLO": ref(12.95, 10.30, 16.30, R_US,
                             confianza="derivado", observaciones=(
        "Semibrillo de la misma gama (≈49 $/gal) por escalado del mate.")),
    "MT-PIN-ESMALTE": ref(13.75, 10.80, 17.40, R_US, confianza="derivado",
                          observaciones=(
        "Esmalte de gama profesional (≈52 $/gal) por escalado.")),
    "MT-ESMALTE-AGUA": ref(14.50, 11.40, 18.50, R_US, confianza="derivado",
                           observaciones=(
        "Esmalte al agua (≈55 $/gal) por escalado.")),
    "MT-PIN-FONDO": ref(8.45, 6.30, 11.10, R_US, confianza="derivado",
                        observaciones=(
        "Fondo/imprimación de contratista (≈32 $/gal) por escalado.")),
    "MT-PIN-MASILLA": ref(6.00, 4.50, 8.00, R_US, confianza="derivado",
                          observaciones=(
        "Masilla («spackle»/relleno) por analogía con la pasta de "
        "juntas.")),
    "MT-PIN-CAL": ref(0.50, 0.38, 0.68, R_US, confianza="derivado",
                      observaciones=(
        "Cal hidratada en saco de 50 lb por analogía con el cemento.")),
    "MT-BARNIZ-MARINO": ref(19.00, 15.00, 24.00, R_US, confianza="derivado",
                            observaciones=(
        "Barniz marino («spar urethane», ≈72 $/gal) por escalado de "
        "la pintura.")),
    "MT-LASUR": ref(15.00, 11.50, 19.00, R_US, confianza="derivado",
                    observaciones=(
        "Lasur protector de madera exterior (≈57 $/gal) por escalado.")),
    "MT-TINTE-MAD": ref(16.50, 12.50, 21.50, R_US, confianza="derivado",
                        observaciones=(
        "Tinte para madera interior por escalado.")),
    # Fontanería: el PPR es residual; el equivalente comercial del tubo
    # de 20 mm es el PEX-B de ½" en rollo de 100 ft a 27,97-33,30 $
    # (28-33 ¢/ft; PEX-A 39-40 ¢/ft) → $/m (×3,2808).
    "MT-PLO-PPR20": ref(1.08, 0.92, 1.31, R_US, observaciones=(
        "Tubería PEX-B de ½\" a 33 ¢/ft (rollo de 100 ft) → $/m. El PPR "
        "apenas se vende en EE. UU.; el PEX es el equivalente de mercado.")),
    "MT-PLO-ACC20": ref(3.40, 2.25, 5.00, R_US, confianza="derivado",
                        observaciones=(
        "Accesorio PEX de ½\" en latón (media de codo, te y unión de "
        "crimpado).")),
    "MT-PLO-PVC4": ref(9.50, 7.00, 12.50, R_US, confianza="derivado",
                       observaciones=(
        "Tubo PVC DWV de 4\" en tramo de 10 ft (≈29 $) → $/m.")),
    "MT-PLO-ACC4": ref(7.50, 4.50, 14.00, R_US, confianza="derivado",
                       observaciones=(
        "Accesorio DWV de 4\" (media de codo, te sanitaria y "
        "reducción).")),
    "MT-PLO-LLAVE": ref(8.00, 6.00, 11.00, R_US, confianza="derivado",
                        observaciones=(
        "Llave de esfera de latón de ½\" (crimpado ≈6-8 $; «push-fit» "
        "9-11 $). El factor de la familia (tubo PEX) daría un valor "
        "menor que el de cualquier válvula de estantería.")),
    "MT-PLO-ABASTO": ref(7.00, 5.00, 10.00, R_US, confianza="derivado",
                         observaciones=(
        "Latiguillo trenzado de abasto («braided supply line») con "
        "racores.")),
    "MT-PLO-DESAG": ref(12.00, 8.00, 17.00, R_US, confianza="derivado",
                        observaciones=(
        "Kit de desagüe de aparato (sifón tipo P de PVC/ABS con brazo "
        "y adaptadores).")),
    "MT-ELE-CAJA": ref(2.50, 1.70, 3.80, R_US, confianza="derivado",
                       observaciones=(
        "Caja de mecanismo de 1 elemento («1-gang box») de "
        "estantería.")),
    # Conductor THHN/THWN-2 de cobre 12 AWG: bobina de 500 ft a
    # 150-155 $ (30 ¢/ft) en Home Depot y distribuidor eléctrico → $/m.
    # Los rollos cortos de 100 ft cotizan a 82-88 ¢/ft (recargo de
    # menudeo) y quedan fuera de la referencia de contratista.
    "MT-ELE-CABLE": ref(1.00, 0.92, 1.20, R_US, observaciones=(
        "Conductor THHN de cobre 12 AWG a 30 ¢/ft en bobina de 500 ft "
        "→ $/m.")),
    "MT-ELE-MECA": ref(8.50, 5.50, 13.50, R_US, confianza="derivado",
                       observaciones=(
        "Mecanismo eléctrico de gama media (tomacorriente o interruptor "
        "decorativo; el GFCI queda en el techo del rango).")),
    "MT-POLIESTIRENO-EXT": ref(20.50, 17.00, 25.00, R_US,
                               confianza="derivado", observaciones=(
        "Panel XPS de 2\" en hoja 4×8 ft (≈58-65 $) → $/m², por "
        "analogía de familia con la lana de roca.")),
    # Panel rígido de lana de roca (tipo «ComfortBoard»): banda de
    # mercado 2,00-2,80 $/ft² para tableros densos.
    "MT-LANA-ROCA": ref(25.83, 21.50, 30.10, R_US, observaciones=(
        "Panel rígido de lana de roca de 2\" a 2,40 $/ft² → $/m².")),
    "MT-GEOTEXTIL": ref(1.05, 0.70, 1.70, R_US, confianza="derivado",
                        observaciones=(
        "Geotextil/malla antihierbas profesional en rollo por "
        "analogía.")),
    # Tubo de drenaje corrugado perforado de 4" con calcetín filtrante:
    # rollo de 100 ft a 129-207 $ (1,29-2,07 $/ft) en Home Depot → $/m.
    "MT-TUBO-DREN": ref(5.09, 4.23, 6.79, R_US, observaciones=(
        "Tubería de drenaje perforada de 4\" con calcetín geotextil a "
        "1,55 $/ft → $/m.")),
    "MT-MADERA-EST": ref(560, 450, 700, R_US, confianza="derivado",
                         observaciones=(
        "Madera estructural aserrada («framing lumber»): ≈1,25 $/bf de "
        "estantería → $/m³ (1 m³ = 423,8 bf). Precio volátil: revisar "
        "en cada actualización.")),
    # Listón: montante de madera 2×4×8 ft SPF a ≈3,90 $ de estantería
    # (banda 3,25-4,50 según metro y semana) → $/m.
    "MT-MADERA-LISTON": ref(1.60, 1.30, 2.10, R_US, observaciones=(
        "«Stud» de madera de 2×4×8 ft a 3,90 $ → $/m. La madera es el "
        "precio más volátil de la matriz.")),
    "MT-MADERA-PERGOLA": ref(10.00, 7.50, 15.00, R_US, confianza="derivado",
                             observaciones=(
        "Madera tratada a presión para pérgola (postes 6×6 a "
        "≈16-18 $/m y vigas 2×8 a ≈5 $/m, mezcla corriente). El factor "
        "de la familia sale del listón SPF y no representa la madera "
        "tratada de exterior.")),
    "MT-LAMINA-OSB": ref(8.50, 6.75, 11.25, R_US, confianza="derivado",
                         observaciones=(
        "Tablero OSB de 7/16\" en hoja 4×8 ft (≈25 $) → $/m². Precio "
        "volátil con el de la madera.")),
    # Canon de vertido de RCD mixto: contenedor «roll-off» de 20 yd³ a
    # 350-680 $ (media nacional ≈475) con 2-3 t incluidas y exceso a
    # 60-110 $/t (canon medio de vertido C&D ≈66 $/t, EREF 2024); una
    # carga mixta corriente (≈5 t en 20 yd³) sale a ≈33 $/yd³ → 43 $/m³.
    "MT-CANON": ref(45, 32, 68, R_US, observaciones=(
        "Gestión de RCD mixto vía contenedor «roll-off» de 20 yd³ "
        "(alquiler + canon de vertido + exceso de tonelaje) → $/m³. "
        "Sin regulación de excedentes de suelo como la de Ontario.")),
    "MT-CANON-TIERRA": ref(32, 22, 48, R_US, confianza="derivado",
                           observaciones=(
        "Tierra limpia de excavación a acopio autorizado: en EE. UU. "
        "el relleno limpio es más barato que el RCD mixto (a menudo "
        "sin canon, solo acarreo), al contrario que en Ontario.")),
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
        referencias[codigo] = {"US": dato}
    for codigo, dato in MATERIALES.items():
        if codigo in referencias:
            raise ValueError(f"{codigo} definido dos veces")
        referencias[codigo] = {"US": dato}
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

    El factor es la mediana de (precio de Estados Unidos investigado / precio
    base) de las anclas de esa familia — ambas cifras en USD, sin conversión
    de divisa —. Si la familia no tiene anclas se usa la mediana de la
    categoría.
    """
    fichas = {c: (cat, item) for c, cat, item in iter_recursos(data)}

    # Factores por (categoría, familia)
    por_familia: dict[tuple[str, str], list[float]] = {}
    por_categoria: dict[str, list[float]] = {}
    for codigo, por_pais in referencias.items():
        ficha = fichas.get(codigo)
        dato = por_pais.get("US")
        if ficha is None or dato is None or dato.confianza != "referencia":
            continue
        categoria = ficha[0]
        if categoria == "mano_obra":
            continue
        base_local = float(ficha[1]["precio"]) * TASAS_CORTE["US"]
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
        if referencias.get(codigo, {}).get("US") is not None:
            continue
        base_local = float(item["precio"]) * TASAS_CORTE["US"]
        factor = factores_familia.get((categoria, _familia(codigo)))
        origen = f"familia {_familia(codigo)}"
        if factor is None:
            factor = factores_categoria[categoria]
            origen = f"categoría {categoria}"
        referencias.setdefault(codigo, {})["US"] = replace(
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
        dato = referencias.get(codigo, {}).get("US")
        if dato is None:
            raise SystemExit(f"Sin referencia para {codigo}")
        filas.append({
            "codigo_recurso": codigo,
            "descripcion": item["descripcion"],
            "categoria": categoria,
            "unidad_fuente": item["unidad"],
            "pais_codigo": "US",
            "moneda": "USD",
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
    print(f"Matriz de Estados Unidos escrita en {OUT.relative_to(ROOT)}")
    print(f"  {total} recursos · {investigados} investigados "
          f"({investigados / total:.0%}) · {derivados} derivados por factor")
    print(f"  tasa de corte: 1 USD = {TASAS_CORTE['US']:.1f} USD (la base ya es USD; sin conversión)")
    print()
    print("  Factores por categoría (mediana de precio EE. UU. / base):")
    for categoria, factor in sorted(factores_categoria.items()):
        print(f"    {categoria:12s} {factor:8.3f}")
    print()
    print(f"  Familias con ancla propia: {len(factores_familia)}")
    for (categoria, familia), factor in sorted(factores_familia.items()):
        n = len([1 for c, d in referencias.items()
                 if d.get("US") and d["US"].confianza == "referencia"
                 and _familia(c) == familia and c in
                 {x for x, cat, _ in iter_recursos(data) if cat == categoria}])
        print(f"    {familia:22s} {factor:8.3f}  ({n} anclas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
