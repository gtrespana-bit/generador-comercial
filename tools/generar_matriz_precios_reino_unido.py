#!/usr/bin/env python3
"""Genera la matriz de precios de recursos para el Reino Unido (GBP).

Replica el contrato de ``generar_matriz_precios_espana.py``:

* Los precios base de ``basedatos_partidas/datos/recursos.json`` están en USD
  con ámbito **Venezuela**. No son precios internacionales, así que ninguna
  conversión de divisa puede producir un precio británico. La matriz se
  construye desde precios británicos reales.
* Las anclas investigadas se publican tal cual, con rango, fuente y fecha.
* El resto se cubre con un **factor de mercado por familia**, calculado como la
  mediana de la relación entre el precio británico investigado y el precio base
  de cada ancla de esa familia.
* La mano de obra no usa factores: los 17 oficios salen del modelo de coste
  empresa de ``coste_empresa_reino_unido.py``, igual que en España.

Mejora respecto al generador de España: allí el factor era único por categoría
(«materiales»), con lo que una cámara CCTV heredaba el factor del cemento. Aquí
el factor es por familia, y solo si una familia no tiene anclas se cae al factor
de la categoría.

Uso:
    python3 tools/generar_matriz_precios_reino_unido.py
"""
from __future__ import annotations

import csv
import json
import statistics
from dataclasses import dataclass, replace
from pathlib import Path

from coste_empresa_reino_unido import (
    CIJC as COSTE_CIJC,
    HORAS_FACTURABLES,
    OFICIOS,
    coste_empresa,
)

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "basedatos_partidas/datos/recursos.json"
OUT = ROOT / "basedatos_partidas/salida/precios_recursos_reino_unido.csv"
PAISES = (("GB", "GBP"),)
FECHA = "2026-10-18"

R_UK = "docs/INVESTIGACION_PRECIOS_REINO_UNIDO.md"
METODOLOGIA = "docs/METODOLOGIA_PRECIOS_REFERENCIA_REINO_UNIDO.md"
# GBP/USD 1,3330 (16/10/2026, exchangerates.org.uk mid-market; Yahoo 1,3330;
# BoE serie diaria 1,3160 el 14/10) -> 1 USD = 0,7502 GBP.
# Solo normaliza el precio base antes de aplicar el factor de mercado; el
# resultado queda congelado en GBP y con fecha.
TASAS_CORTE = {"GB": 0.7502}

OBS_REFERENCIA = (
    "Precio de mercado británico observado (sin IVA, sin porte salvo indicación); "
    "puede variar por proveedor, marca, volumen y región."
)
OBS_DERIVADO = (
    "Precio referencial derivado del factor de mercado de su familia, calculado "
    "sobre la canasta británica investigada; no es una cotización de tienda."
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


def ref(precio, minimo, maximo, fuente=R_UK, **kwargs) -> Referencia:
    precio, minimo, maximo = map(float, (precio, minimo, maximo))
    if minimo <= 0 or maximo < minimo or not minimo <= precio <= maximo:
        raise ValueError(f"Rango inválido: {minimo} <= {precio} <= {maximo}")
    return Referencia(precio, minimo, maximo, fuente, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Mano de obra — modelo de coste empresa británico
# ─────────────────────────────────────────────────────────────────────────────

def referencias_mano_obra() -> dict[str, dict[str, Referencia]]:
    salida: dict[str, dict[str, Referencia]] = {}
    for codigo, (oficio, salario, cijc_clave) in OFICIOS.items():
        base = max(salario, COSTE_CIJC[cijc_clave])
        coste = coste_empresa(base)["coste_hora_facturable"]
        # El rango refleja la dispersión regional: de Escocia/Irlanda del Norte
        # (−10 %) al área de Londres (+20 %).
        salida[codigo] = {
            "GB": ref(
                coste,
                coste * 0.90,
                coste * 1.20,
                R_UK,
                confianza="referencia",
                incluye_iva="no_aplica",
                incluye_transporte="no_aplica",
                observaciones=(
                    f"Coste empresa por hora facturable. {oficio}. Salario ONS ASHE "
                    f"{salario:.2f} £/h (nunca por debajo del CIJC {cijc_clave} "
                    f"{COSTE_CIJC[cijc_clave]:.2f} £/h) + NI empresa 15 %, pensión 3 %, "
                    f"CITB 0,35 %, vacaciones 31 días y bajas, todo dividido por "
                    f"{HORAS_FACTURABLES:,.0f} h facturables/año. No es tarifa de "
                    f"autónomo: el catálogo ya aplica un 35 % de margen sobre el "
                    f"coste directo."
                ),
            )
        }
    return salida


# ─────────────────────────────────────────────────────────────────────────────
# 2. Maquinaria — tarifas de alquiler británicas
#
#    Las tarifas británicas se cotizan por día (8 h) o por semana. Se adopta el
#    día de 8 horas y se publica el equivalente horario. Excluyen IVA,
#    combustible y operador salvo que el recurso lo indique.
# ─────────────────────────────────────────────────────────────────────────────

# (precio/día, mínimo/día, máximo/día) -> referencia horaria
def _alquiler(dia, minimo, maximo, nota="") -> Referencia:
    return ref(
        dia / 8.0, minimo / 8.0, maximo / 8.0, R_UK,
        observaciones=(
            f"Alquiler británico {minimo:.0f}-{maximo:.0f} £/día (jornada de 8 h), "
            f"sin IVA ni combustible. {nota}".strip()
        ),
    )


MAQUINARIA: dict[str, Referencia] = {
    # Corte y demolición
    "MQ-CORT-AGUA": _alquiler(70, 55, 95, "Sierra de banco húmeda para cerámica."),
    "MQ-ROZAD": _alquiler(40, 34, 53, "Rozadora de doble disco con aspiración."),
    "MQ-MART-ELEC": _alquiler(33, 30, 45, "Martillo eléctrico de 5 kg."),
    "MQ-AMOLA": _alquiler(14, 11, 21, "Amoladora angular de 230 mm."),
    "MQ-SIERRA": _alquiler(32, 30, 40, "Sierra circular o motosierra de 14\"."),
    "MQ-OXICORTE": _alquiler(30, 25, 40, "Equipo de oxicorte."),
    "MQ-CIZALLA": _alquiler(40, 35, 55, "Cizalla y dobladora de armadura."),
    "MQ-ESMERIL": _alquiler(28, 25, 40, "Esmeriladora y cepillo de púas."),
    # Hormigón
    "MQ-MEZCL": _alquiler(22, 15, 27, "Hormigonera eléctrica de un saco."),
    "MQ-BATID": _alquiler(30, 20, 38, "Batidora de doble varilla con taladro."),
    "MQ-VIBRADOR": _alquiler(40, 36, 76, "Vibrador de aguja."),
    "MQ-ALISADORA": _alquiler(85, 60, 109, "Alisadora helicóptero."),
    "MQ-BOMBA-CONC": _alquiler(600, 480, 780, "Bomba de hormigón **con operador**."),
    "MQ-PROYECT-MORT": _alquiler(110, 90, 145, "Máquina de proyectar mortero y yeso."),
    # Compactación y movimiento de tierras
    "MQ-COMPACT-SALTO": _alquiler(130, 126, 145, "Compactador de zanja tipo canguro."),
    "MQ-PLANCHA-COMP": _alquiler(38, 32, 55, "Plancha compactadora vibratoria."),
    "MQ-RETRO": _alquiler(250, 210, 290, "Retroexcavadora de 3 t con martillo."),
    "MQ-MART-NEUM": _alquiler(75, 60, 100, "Martillo neumático con compresor."),
    "MQ-PERF-PILOTE": _alquiler(1200, 950, 1500, "Equipo de perforación de pilotes."),
    # Elevación y acceso
    # El recurso dice «andamio tubular o de borriquetas» para trabajos en
    # altura: en el Reino Unido eso es una torre móvil de aluminio, no un
    # caballete. Tarifa de torre pequeña (2,2 m), no de borriqueta.
    "MQ-ANDAMIO": _alquiler(33.5, 24, 54, "Torre móvil de aluminio de 2,2 m (tarifa diaria; "
                                          "por semana sale mucho más barata)."),
    "MQ-MONTAC": _alquiler(45, 30, 127, "Montacargas o pluma de fachada."),
    "MQ-VENT-SUC": _alquiler(77, 60, 95, "Ventosas de elevación y panel lifter."),
    "MQ-GRUA": _alquiler(450, 380, 600, "Camión grúa **con operador**."),
    # Instalaciones y acabados
    "MQ-ATORN": _alquiler(18, 14, 24, "Atornilladora para placa de yeso."),
    "MQ-LIJAD": _alquiler(45, 35, 60, "Lijadora de pared con aspiración."),
    "MQ-PULIDORA": _alquiler(35, 25, 55, "Pulidora abrillantadora de piedra."),
    "MQ-LIJAD-PISO": _alquiler(60, 50, 80, "Lijadora de banda y orilladora."),
    "MQ-ESTAMP": _alquiler(80, 65, 105, "Moldes y rodillos para hormigón impreso."),
    "MQ-SOLDADORA": _alquiler(45, 38, 60, "Equipo de soldadura por arco."),
    "MQ-TERMOF": _alquiler(35, 28, 48, "Termofusora para tubería de plástico."),
    "MQ-DOBLAD-TUBO": _alquiler(22, 18, 30, "Dobladora y abocardadora."),
    "MQ-RECUP-GAS": _alquiler(50, 42, 68, "Recuperadora de gas y bomba de vacío."),
    "MQ-INYECTORA": _alquiler(60, 48, 80, "Equipo de inyección de resina."),
    "MQ-RODILLO": _alquiler(10, 8, 15, "Equipo de aplicación: rodillos, brochas, cubetas."),
    # Limpieza, achique y seguridad
    "MQ-ASPIR": _alquiler(30, 18, 52, "Aspirador industrial clase M."),
    "MQ-HIDROLAV": _alquiler(45, 30, 60, "Hidrolavadora de presión."),
    "MQ-BOMBA-ACHI": _alquiler(25, 15, 30, "Bomba sumergible de achique."),
    "MQ-DESBROZ": _alquiler(35, 28, 45, "Desbrozadora de motor."),
    # Medición y detección
    "MQ-NIVEL-LASER": _alquiler(45, 36, 71, "Nivel láser rotativo autonivelante."),
    "MQ-DETECTOR": _alquiler(40, 30, 66, "Detector de instalaciones empotradas (CAT)."),
    "MQ-TALADRO": _alquiler(18, 9, 25, "Taladro percutor SDS con brocas."),
    "MQ-TELUROMETRO": _alquiler(40, 30, 55, "Telurómetro / medidor de resistencia de tierra."),
    # Transporte
    "MQ-VOLQ": _alquiler(350, 300, 430, "Camión volqueta de 6 m³ **con chofer**."),
    # Unidad distinta: el baño portátil se alquila por mes.
    "MQ-BANO-PORT": ref(
        150, 120, 200, R_UK,
        observaciones=(
            "Alquiler mensual de baño portátil de obra con mantenimiento "
            "(recurso medido en unidades, no en horas). Sin IVA."
        ),
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# 3. Materiales — precios de proveedor británico
# ─────────────────────────────────────────────────────────────────────────────

MATERIALES: dict[str, Referencia] = {
    # ── Hormigón y áridos ────────────────────────────────────────────────────
    "MT-CONC-180": ref(105, 92, 115, R_UK,
                       observaciones="Hormigón premezclado ≈ C16/20 (180 kg/cm² ≈ 17,7 MPa), puesto en obra."),
    "MT-CONC-210": ref(114, 100, 128, R_UK,
                       observaciones="Hormigón premezclado ≈ C20/25 (210 kg/cm² ≈ 20,6 MPa), puesto en obra."),
    "MT-CONC-250": ref(122, 108, 136, R_UK,
                       observaciones="Hormigón premezclado ≈ C25/30 (250 kg/cm² ≈ 24,5 MPa), puesto en obra."),
    "MT-CONC-300": ref(130, 115, 145, R_UK,
                       observaciones="Hormigón premezclado ≈ C30/37 (300 kg/cm² ≈ 29,4 MPa), puesto en obra."),
    "MT-CEMENTO": ref(0.271, 0.26, 0.32, R_UK,
                      observaciones="Cemento Portland CEM I en saco de 25 kg (6,78-7,73 £ ex IVA en Travis Perkins)."),
    "MT-ARENA": ref(54, 45, 63, R_UK,
                    observaciones="Arena lavada. 30-42 £/t suelta × 1,5 t/m³; incluye canon de áridos."),
    "MT-PIEDRA-PIC": ref(60, 48, 72, R_UK,
                         observaciones="Árido triturado. 32-48 £/t × 1,5 t/m³."),
    "MT-MAT-PRESTAMO": ref(45, 30, 60, R_UK,
                           observaciones="Material granular seleccionado / zahorra (MOT Type 1), 28-38 £/t × 2,1 t/m³."),
    "MT-AGUA-OBRA": ref(2.20, 1.80, 2.80, R_UK,
                        observaciones="Agua de obra; tarifa industrial por m³."),
    "MT-ADITIVO": ref(3.50, 2.80, 4.50, R_UK,
                      observaciones="Aditivo plastificante reductor de agua, por litro."),
    "MT-CURADOR": ref(4.00, 3.20, 5.20, R_UK,
                      observaciones="Curador químico de membrana para hormigón, por litro."),
    "MT-ACERO-CAB": ref(0.62, 0.52, 0.68, R_UK,
                        observaciones="Armadura corrugada B500, 520-680 £/t."),
    "MT-ALAMBRE": ref(1.60, 1.30, 2.00, R_UK,
                      observaciones="Alambre recocido de atado."),
    "MT-MALLA-ELEC": ref(6.50, 5.20, 8.50, R_UK,
                         observaciones="Malla electrosoldada de acero para losas, por m²."),
    "MT-SEPARADOR": ref(0.10, 0.07, 0.15, R_UK,
                        observaciones="Separador de plástico para recubrimiento, por unidad."),
    "MT-FORM-MADERA": ref(22, 18, 28, R_UK,
                          observaciones="Encofrado de madera con puntales y arriostramiento, por m² y uso."),
    "MT-DESMOLD": ref(4.20, 3.40, 5.50, R_UK,
                      observaciones="Desmoldeante para encofrados, por litro."),
    "MT-POLIET": ref(0.75, 0.55, 1.00, R_UK,
                     observaciones="Lámina de polietileno como barrera de vapor, por m²."),
    "MT-PERFIL-ACERO": ref(1.85, 1.50, 2.40, R_UK,
                           observaciones="Perfil estructural de acero laminado, por kg."),
    "MT-PLANCHA-ACERO": ref(2.10, 1.70, 2.70, R_UK,
                            observaciones="Chapa de acero para placas base y cartelas, por kg."),
    "MT-ELECTRODO": ref(7.50, 6.00, 9.50, R_UK,
                        observaciones="Electrodo revestido para soldadura, por kg."),
    # ── Fábrica y bloques ────────────────────────────────────────────────────
    "MT-BLQ-10": ref(2.20, 1.80, 2.60, R_UK,
                     observaciones="Bloque denso de hormigón de 100 mm (formato británico 440×215 mm)."),
    "MT-BLQ-12": ref(2.60, 2.20, 3.10, R_UK,
                     observaciones="Bloque denso de hormigón de 140 mm."),
    # El bloque de vidrio no guarda relación de precio con el bloque de
    # hormigón, así que lleva ancla propia en lugar de heredar el factor
    # de la familia MT-BLQ.
    "MT-BLQ-VIDRIO": ref(5.50, 4.00, 8.00, R_UK,
                         observaciones="Bloque de vidrio de 190×190×80 mm, por unidad."),
    "MT-LADRILLO-VISTO": ref(0.65, 0.45, 0.95, R_UK,
                             observaciones="Ladrillo de cara vista estándar (wirecut), 450-700 £/1.000 "
                                           "ex IVA; las gamas premium pasan de 850 £/1.000."),
    # ── Yeso laminado y tabiquería ───────────────────────────────────────────
    "MT-PYL-PLACA": ref(4.15, 3.60, 5.20, R_UK,
                        observaciones="Placa de yeso laminado de 15 mm; hoja 2400×1200 (2,88 m²) a 11,50 £."),
    "MT-PYL-PLACA125": ref(3.30, 2.80, 4.20, R_UK,
                           observaciones="Placa de yeso laminado de 12,5 mm; hoja de 2,88 m² a 8,92-10,38 £ ex IVA."),
    "MT-PYL-PLACA-HD": ref(5.20, 4.40, 6.50, R_UK,
                           observaciones="Placa de alta dureza de 12,5 mm."),
    "MT-PYL-PLACA-IG": ref(5.80, 4.86, 7.20, R_UK,
                           observaciones="Placa resistente al fuego tipo F de 15 mm (14-16,50 £ por hoja)."),
    "MT-PYL-MONT": ref(4.50, 3.60, 5.60, R_UK,
                       observaciones="Montante de acero galvanizado de 70 mm, por metro."),
    "MT-PYL-CANAL": ref(3.50, 2.80, 4.40, R_UK,
                        observaciones="Canal de arranque de acero galvanizado de 70 mm, por metro."),
    "MT-PYL-LANA": ref(5.50, 4.40, 7.20, R_UK,
                       observaciones="Panel de lana mineral de 60 mm (lana de roca 100 mm a 8,57 £/m²)."),
    "MT-PYL-BANDA": ref(0.60, 0.45, 0.85, R_UK,
                        observaciones="Banda estanca autoadhesiva de junta perimetral, por metro."),
    "MT-PYL-PASTA": ref(0.85, 0.65, 1.15, R_UK,
                        observaciones="Pasta de juntas y cinta de papel microperforada, por kg."),
    "MT-PYL-PASTA-AGARRE": ref(0.70, 0.55, 0.95, R_UK,
                               observaciones="Pasta de agarre de base yeso (25 kg a 12,50 £), por kg."),
    "MT-TORN": ref(0.012, 0.008, 0.020, R_UK,
                   observaciones="Tornillería para placa de yeso, por unidad."),
    "MT-MALLA-ESQ": ref(1.20, 0.90, 1.70, R_UK,
                        observaciones="Cantonera metálica de esquina, por metro."),
    # ── Revestimientos cerámicos y adhesivos ─────────────────────────────────
    "MT-ADH-C2TE": ref(1.23, 1.05, 1.45, R_UK,
                       observaciones="Adhesivo cementoso C2 TE S1, saco de 20 kg a 24,66 £ (tarifa profesional)."),
    "MT-ADH-C1": ref(0.70, 0.55, 0.90, R_UK,
                     observaciones="Adhesivo cementoso normal C1, saco de 20 kg."),
    "MT-JUN-CG2": ref(3.26, 2.80, 4.00, R_UK,
                      observaciones="Mortero de juntas CG2, saco de 5 kg a 16,32 £."),
    "MT-AUT-NIV": ref(0.85, 0.70, 1.10, R_UK,
                      observaciones="Mortero autonivelante de base cementosa, por kg."),
    "MT-IMP-PRIM": ref(4.50, 3.20, 6.00, R_UK,
                       observaciones="Imprimación tapaporos acrílica, por litro."),
    "MT-PER-BANDA": ref(0.80, 0.60, 1.05, R_UK,
                        observaciones="Banda perimetral de polietileno expandido, por metro."),
    "MT-SIL-SAN": ref(12.00, 9.97, 14.14, R_UK,
                      observaciones="Cartucho de silicona sanitaria de 310 ml."),
    "MT-SELLA-FISURA": ref(6.50, 5.00, 8.50, R_UK,
                           observaciones="Sellador elástico de poliuretano, por kg."),
    # ── Pintura ──────────────────────────────────────────────────────────────
    "MT-PIN-CAUCHO": ref(6.50, 4.50, 9.50, R_UK,
                         observaciones="Emulsión vinílica mate de grado profesional (Johnstone's/Dulux Trade), por litro."),
    "MT-PIN-SEMIBRILLO": ref(7.50, 5.50, 10.50, R_UK,
                             observaciones="Emulsión satinada lavable, por litro."),
    "MT-PIN-FONDO": ref(5.00, 3.50, 7.50, R_UK,
                        observaciones="Fondo fijador o sellador acrílico, por litro."),
    "MT-PIN-ESMALTE": ref(9.50, 8.00, 11.70, R_UK,
                          observaciones="Esmalte brillante sintético, grado profesional, por litro."),
    "MT-ESMALTE-AGUA": ref(9.25, 7.50, 11.50, R_UK,
                           observaciones="Esmalte satinado al agua para carpintería, por litro."),
    "MT-PIN-MASILLA": ref(2.50, 1.80, 3.50, R_UK,
                          observaciones="Masilla de reparación en pasta, por kg."),
    "MT-PIN-CAL": ref(1.20, 0.90, 1.70, R_UK,
                      observaciones="Cal hidratada para pintura mineral, por kg."),
    "MT-BARNIZ-MARINO": ref(14.00, 11.00, 18.00, R_UK,
                            observaciones="Barniz marino de exterior, por litro."),
    "MT-LASUR": ref(12.00, 9.50, 15.50, R_UK,
                    observaciones="Lasur protector para madera exterior, por litro."),
    "MT-TINTE-MAD": ref(10.00, 8.00, 13.00, R_UK,
                        observaciones="Tinte para madera, por litro."),
    "MT-LACA-MADERA": ref(11.00, 8.50, 14.50, R_UK,
                          observaciones="Laca para acabado de carpintería, por litro."),
    # ── Fontanería ───────────────────────────────────────────────────────────
    # Nota de mercado: en el Reino Unido la tubería de PPR es residual; el
    # equivalente funcional es el tubo barrera de polietileno (Speedfit/Hep2O).
    "MT-PLO-PPR20": ref(2.10, 1.80, 2.60, R_UK,
                        observaciones="Tubería barrera de 15 mm (Speedfit 47,20 £/25 m; Hep2O 47,16 £/25 m). "
                                      "El PPR es residual en el mercado británico."),
    "MT-PLO-ACC20": ref(2.60, 2.20, 3.30, R_UK,
                        observaciones="Accesorios de fontanería de 15 mm: codos, tes, uniones (codo 2,24-2,34 £)."),
    "MT-PLO-PVC4": ref(4.50, 3.50, 6.00, R_UK,
                       observaciones="Tubería de saneamiento enterrado de 110 mm (4\"), por metro."),
    "MT-PLO-ACC4": ref(6.50, 5.00, 9.00, R_UK,
                       observaciones="Accesorios de saneamiento de 110 mm, por unidad."),
    "MT-PLO-SOP": ref(0.60, 0.45, 0.85, R_UK,
                      observaciones="Abrazaderas y soportes de fijación, por unidad."),
    "MT-PLO-LLAVE": ref(7.50, 6.00, 10.00, R_UK,
                        observaciones="Llave de paso de esfera de 15 mm, por unidad."),
    # ── Electricidad ─────────────────────────────────────────────────────────
    "MT-ELE-CABLE": ref(0.77, 0.74, 0.96, R_UK,
                        observaciones="Cable 6242Y de 2,5 mm² (bobina de 100 m a 88,69-96 £ IVA incl.)."),
    "MT-ELE-TUB20": ref(1.20, 0.90, 1.70, R_UK,
                        observaciones="Tubo conduit corrugado de 20 mm, por metro."),
    "MT-ELE-CAJA": ref(0.90, 0.65, 1.30, R_UK,
                       observaciones="Caja de empotrar de mecanismo, por unidad."),
    "MT-ELE-MECA": ref(4.50, 3.20, 7.00, R_UK,
                       observaciones="Mecanismo de interruptor o enchufe con placa, gama media, por unidad."),
    "MT-ELE-PROV": ref(3.00, 2.30, 4.20, R_UK,
                       observaciones="Cable para instalación provisional de obra, por metro."),
    "MT-TABLERO-PROV": ref(85, 65, 120, R_UK,
                           observaciones="Cuadro eléctrico provisional de obra con diferencial."),
    "MT-LAMP-OBRA": ref(18, 12, 28, R_UK,
                        observaciones="Reflector o lámpara de obra con portalámparas."),
    "MT-CABLE-COBRE-DESN": ref(5.50, 4.20, 7.50, R_UK,
                               observaciones="Cable de cobre desnudo de 35 mm² para bajante, por metro."),
    # ── Aislamiento e impermeabilización ─────────────────────────────────────
    "MT-POLIESTIRENO-EXT": ref(14.00, 11.00, 18.00, R_UK,
                               observaciones="Panel de poliestireno extruido (XPS), por m²."),
    "MT-LANA-ROCA": ref(8.57, 6.00, 12.00, R_UK,
                        observaciones="Panel de lana de roca de 100 mm (Rockwool RWA45), por m²."),
    "MT-MEMBRANA-PVC": ref(16.00, 12.00, 22.00, R_UK,
                           observaciones="Membrana impermeabilizante de PVC armado, por m²."),
    "MT-LAMINA-DREN": ref(8.50, 6.50, 11.00, R_UK,
                          observaciones="Lámina drenante nodular, por m²."),
    "MT-GEOTEXTIL": ref(1.60, 1.10, 2.20, R_UK,
                        observaciones="Geotextil no tejido, por m²."),
    "MT-TUBO-DREN": ref(5.00, 3.80, 6.80, R_UK,
                        observaciones="Tubería de drenaje perforada con geotextil, por metro."),
    "MT-IMPERM-ASF": ref(6.00, 4.50, 8.50, R_UK,
                         observaciones="Impermeabilizante asfáltico en emulsión, por litro."),
    "MT-BENTONITA": ref(12.00, 9.00, 17.00, R_UK,
                        observaciones="Geocompuesto de bentonita sódica, por m²."),
    "MT-SELLA-BENTONITA": ref(5.50, 4.20, 7.50, R_UK,
                              observaciones="Cordón de bentonita expansiva, por metro."),
    "MT-RESINA-INYEC": ref(24.00, 18.00, 32.00, R_UK,
                           observaciones="Resina de inyección para sellado de fisuras, por litro."),
    "MT-SILOXANO": ref(9.50, 7.50, 13.00, R_UK,
                       observaciones="Hidrofugante de siloxano para fachadas, por litro."),
    "MT-HIDROFUG-FACH": ref(10.00, 8.00, 14.00, R_UK,
                            observaciones="Hidrofugante incoloro de impregnación, por litro."),
    # ── Madera y tableros ────────────────────────────────────────────────────
    "MT-MADERA-EST": ref(620, 400, 800, R_UK,
                         observaciones="Madera estructural aserrada y cepillada C16/C24, por m³."),
    "MT-MADERA-LISTON": ref(2.60, 2.00, 3.60, R_UK,
                            observaciones="Listón de madera de obra, por metro."),
    "MT-LAMINA-OSB": ref(9.00, 7.00, 11.50, R_UK,
                         observaciones="Tablero OSB de 18 mm; hoja 2440×1220 (2,98 m²) a 21-34 £."),
    "MT-VIGA-APEO": ref(4.50, 3.50, 6.00, R_UK,
                        observaciones="Madera de reparto para apeos, por metro."),
    "MT-MADERA-ENTIB": ref(5.50, 4.20, 7.50, R_UK,
                           observaciones="Tablón y puntal para entibación de zanja, por m²."),
    "MT-MADERA-PERGOLA": ref(9.50, 7.50, 13.00, R_UK,
                             observaciones="Viga y listón de madera tratada, por metro."),
    "MT-PRESERV-MAD": ref(8.50, 6.50, 11.50, R_UK,
                          observaciones="Preservante fungicida e insecticida, por litro."),
    # ── Residuos ─────────────────────────────────────────────────────────────
    # El impuesto de vertedero británico (Landfill Tax) explica que estos
    # recursos sean varias veces más caros que en España. Desde el 1 de abril
    # de 2026: tipo general 130,75 £/t y tipo reducido para inertes 8,65 £/t
    # (el reducido subió un 114 % ese año). Densidades: cascote de ladrillo
    # 1,8 t/m³, de hormigón 2,2 t/m³, tierra 1,5 t/m³.
    "MT-CANON": ref(45, 32, 65, R_UK,
                    observaciones="Retirada y vertido de escombro inerte (muck-away) por m³: "
                                  "8,65 £/t de Landfill Tax (tipo reducido) × 2,2 t/m³ más "
                                  "puerta de vertedero. El residuo mezclado tributa al tipo "
                                  "general, 130,75 £/t."),
    "MT-CANON-TIERRA": ref(28, 20, 42, R_UK,
                           observaciones="Retirada de tierra y material de excavación, por m³ "
                                         "a tipo reducido (8,65 £/t × 1,5 t/m³ más puerta)."),
    # ── Protecciones y consumibles ───────────────────────────────────────────
    "MT-PROT-OBRA": ref(0.55, 0.40, 0.80, R_UK,
                        observaciones="Protección de plástico, cartón y cinta, por m²."),
    "MT-PROT-CARTON": ref(0.70, 0.50, 1.00, R_UK,
                          observaciones="Cartón corrugado en rollo para protección, por m²."),
    "MT-PROT-PLAST": ref(0.45, 0.30, 0.70, R_UK,
                         observaciones="Lámina de polietileno para protección, por m²."),
    "MT-CINTA-ENM": ref(1.60, 1.10, 2.40, R_UK,
                        observaciones="Rollo de cinta de enmascarar y de embalaje."),
    "MT-CLAVOS": ref(3.80, 2.80, 5.50, R_UK,
                     observaciones="Clavos, tornillos y fijaciones en general, por kg."),
    "MT-CONS-DEM": ref(1.80, 1.30, 2.60, R_UK,
                       observaciones="Consumibles de demolición: puntas y cinceles."),
    "MT-SAC-ESC": ref(1.10, 0.80, 1.60, R_UK,
                      observaciones="Saco de rafia para retirada manual de escombros."),
    "MT-SENAL-OBRA": ref(7.50, 5.50, 11.00, R_UK,
                         observaciones="Señal de advertencia, cinta de peligro y conos."),
    "MT-MALLA-OBRA": ref(1.40, 1.00, 2.00, R_UK,
                         observaciones="Malla plástica de señalización perimetral, por m²."),
    "MT-MANGUERA": ref(1.40, 1.00, 2.00, R_UK,
                       observaciones="Manguera reforzada para red provisional de agua, por metro."),
    # ── Yesos y morteros ─────────────────────────────────────────────────────
    "MT-YESO-REP": ref(0.98, 0.85, 1.20, R_UK,
                       observaciones="Yeso de reparación; Thistle MultiFinish 25 kg a 9,79 £ ex IVA."),
    "MT-DECAP": ref(9.00, 7.00, 12.50, R_UK,
                    observaciones="Decapante químico en gel, por litro."),
    "MT-DISOL-ADH": ref(7.00, 5.50, 9.50, R_UK,
                        observaciones="Disolvente removedor de adhesivos, por litro."),
    "MT-LIMP-QUIM": ref(11.00, 8.50, 15.00, R_UK,
                        observaciones="Limpiador químico específico para fachadas, por litro."),
    "MT-FUNGICIDA": ref(8.50, 6.50, 12.00, R_UK,
                        observaciones="Solución fungicida y algicida, por litro."),
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
        referencias[codigo] = {"GB": dato}
    for codigo, dato in MATERIALES.items():
        if codigo in referencias:
            raise ValueError(f"{codigo} definido dos veces")
        referencias[codigo] = {"GB": dato}
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

    El factor es la mediana de (precio británico investigado / precio base
    convertido) de las anclas de esa familia. Si la familia no tiene anclas se
    usa la mediana de la categoría, y si aun así no hubiera anclas, la mediana
    global de la categoría calculada sobre todas las anclas.
    """
    fichas = {c: (cat, item) for c, cat, item in iter_recursos(data)}

    # Factores por (categoría, familia)
    por_familia: dict[tuple[str, str], list[float]] = {}
    por_categoria: dict[str, list[float]] = {}
    for codigo, por_pais in referencias.items():
        ficha = fichas.get(codigo)
        dato = por_pais.get("GB")
        if ficha is None or dato is None or dato.confianza != "referencia":
            continue
        categoria = ficha[0]
        if categoria == "mano_obra":
            continue
        base_local = float(ficha[1]["precio"]) * TASAS_CORTE["GB"]
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
        if referencias.get(codigo, {}).get("GB") is not None:
            continue
        base_local = float(item["precio"]) * TASAS_CORTE["GB"]
        factor = factores_familia.get((categoria, _familia(codigo)))
        origen = f"familia {_familia(codigo)}"
        if factor is None:
            factor = factores_categoria[categoria]
            origen = f"categoría {categoria}"
        referencias.setdefault(codigo, {})["GB"] = replace(
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
        dato = referencias.get(codigo, {}).get("GB")
        if dato is None:
            raise SystemExit(f"Sin referencia para {codigo}")
        filas.append({
            "codigo_recurso": codigo,
            "descripcion": item["descripcion"],
            "categoria": categoria,
            "unidad_fuente": item["unidad"],
            "pais_codigo": "GB",
            "moneda": "GBP",
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
        w = csv.DictWriter(fh, fieldnames=campos, delimiter=";", lineterminator="\n")
        w.writeheader()
        w.writerows(filas)

    total = len(filas)
    investigados = sum(1 for f in filas if f["confianza"] == "referencia")
    print(f"Matriz británica escrita en {OUT.relative_to(ROOT)}")
    print(f"  {total} recursos · {investigados} investigados "
          f"({investigados / total:.0%}) · {derivados} derivados")
    print(f"  tasa de corte: 1 USD = {TASAS_CORTE['GB']:.4f} GBP (GBP/USD 1,3330, 16/10/2026)")
    print()
    print("  Factores por categoría (mediana de precio británico / base convertida):")
    for categoria, factor in sorted(factores_categoria.items()):
        print(f"    {categoria:12s} {factor:8.3f}")
    print()
    print(f"  Familias con ancla propia: {len(factores_familia)}")
    for (categoria, familia), factor in sorted(factores_familia.items()):
        n = len([1 for c, d in referencias.items()
                 if d.get("GB") and d["GB"].confianza == "referencia"
                 and _familia(c) == familia and c in
                 {x for x, cat, _ in iter_recursos(data) if cat == categoria}])
        print(f"    {familia:22s} {factor:8.3f}  ({n} anclas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
