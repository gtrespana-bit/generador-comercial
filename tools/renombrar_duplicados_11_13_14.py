#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Renombra las partidas nuevas que colisionaron de título con las existentes."""
import json
from pathlib import Path

DESCOMP = Path("basedatos_partidas/datos/descompuestos")

RENOMBRES = {
    "11.08.01.070": "Canalón de alero de cubierta.",
    "11.08.01.080": "Bajante de aguas lluvias con fijaciones.",
    "11.08.01.090": "Boquilla de desagüe de cubierta con rejilla.",
    "11.08.01.100": "Remate de borde de cubierta con goterón.",
    "11.08.01.110": "Revisión y limpieza de cubierta con informe.",
    "11.08.01.120": "Reparación de membrana de cubierta plana.",
    "11.04.01.070": "Cubierta de panel sándwich con núcleo de poliuretano.",
    "11.06.01.040": "Estructura de madera de techo a dos aguas.",
    "11.06.01.060": "Correas de madera aserrada para cubierta.",

    "13.01.01.070": "Mueble bajo de cocina con fregadero.",
    "13.01.01.080": "Mueble alto de cocina con entrepaños.",
    "13.01.01.090": "Isla de cocina con mesón.",
    "13.01.01.100": "Instalación de campana extractora con ducto.",
    "13.01.01.110": "Instalación de electrodoméstico con conexiones.",
    "13.01.01.120": "Despensa de cocina con gavetas.",
    "13.02.01.050": "Mesón de granito pulido.",
    "13.02.01.060": "Mesón de concreto con acabado pulido.",
    "13.02.01.070": "Salpicadero de mesón en piedra.",
    "13.02.01.080": "Mesón de lavadero con escurridor.",
    "13.03.01.040": "Mueble de baño suspendido con lavamanos.",
    "13.03.01.050": "Botiquín de baño con espejo integrado.",
    "13.03.01.060": "Mesón de baño con lavamanos integrado.",
    "13.04.01.040": "Closet de vestidor a medida.",
    "13.04.01.050": "Puerta corrediza de closet con riel.",
    "13.04.01.060": "Organizadores interiores de closet.",
    "13.06.01.030": "Barra de apoyo de acero inoxidable.",
    "13.06.01.040": "Herrajes y tiradores de mobiliario.",
    "13.07.01.020": "Señalización de seguridad pintada en piso.",
    "13.08.01.030": "Estantería fija de pared.",
    "13.08.01.040": "Mueble fijo con entrepaños y puertas.",
    "13.08.01.050": "Mampara de oficina con perfilería.",

    "14.01.01.060": "Piso de concreto exterior alisado.",
    "14.01.01.070": "Pavimento de adoquín con confinamiento.",
    "14.01.01.080": "Pavimento de gravilla compactada.",
    "14.01.01.090": "Rampa vehicular de concreto armado.",
    "14.01.01.100": "Escalera exterior de concreto armado.",
    "14.02.01.030": "Bordillo de concreto vaciado en sitio.",
    "14.02.01.040": "Acera de concreto con juntas.",
    "14.03.01.030": "Canal de drenaje con rejilla metálica.",
    "14.03.01.040": "Registro de drenaje con tapa.",
    "14.04.01.030": "Cerca de bloque con columnas.",
    "14.04.01.040": "Cerca de malla ciclónica sobre postes.",
    "14.05.01.020": "Portón vehicular corredizo.",
    "14.06.01.030": "Siembra de grama en panes.",
    "14.06.01.040": "Plantación de árbol ornamental.",
    "14.07.01.020": "Red de riego por aspersión.",
    "14.08.01.020": "Punto de agua exterior con manguera.",
    "14.09.01.020": "Iluminación exterior de caminería.",
    "14.11.01.030": "Pérgola de madera tratada.",
    "14.11.01.040": "Jardinera de bloque revestido.",
}


def main() -> int:
    n = 0
    for codigo, titulo in RENOMBRES.items():
        ruta = DESCOMP / f"{codigo}.json"
        if not ruta.exists():
            raise SystemExit(f"No existe {ruta}")
        partida = json.loads(ruta.read_text(encoding="utf-8"))
        partida["titulo"] = titulo
        ruta.write_text(json.dumps(partida, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        n += 1
    print(f"Renombradas {n} partidas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
