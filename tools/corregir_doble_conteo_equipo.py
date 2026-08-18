#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Corrige las partidas nuevas que declararon el equipo en producto_cliente pero
aún lo mantenían embebido en los recursos (doble conteo).

Elimina de `recursos` el material de EQUIPO que ya está descrito en
`producto_cliente`, dejando solo la mano de obra y los consumibles de
instalación.
"""
import json
from pathlib import Path

DESCOMP = Path("basedatos_partidas/datos/descompuestos")

# codigo -> refs de equipo a retirar de los recursos
A_RETIRAR = {
    "13.06.01.050": ["MT-BARRA-APOYO"],
    "18.06.01.070": ["MT-DOM-PERSIANA"],
    "18.06.01.080": ["MT-DOM-SENSOR-LUZ"],
    "18.07.01.020": ["MT-DOM-TERMOSTATO"],
    "18.07.01.090": ["MT-DOM-ACTUADOR"],
    "18.08.01.020": ["MT-DOM-SENSOR-MOV"],
    "18.08.01.040": ["MT-DOM-DIMMER"],
    "18.08.01.050": ["MT-DOM-SENSOR-LUZ"],
    "18.08.01.060": ["MT-DOM-SENSOR-LUZ"],
    "18.08.01.080": ["MT-DOM-TECLADO"],
    "18.08.01.110": ["MT-DOM-ENCHUFE"],
    "18.09.01.010": ["MT-PANEL-SOLAR"],
    "18.09.01.020": ["MT-INVERSOR"],
    "18.09.01.030": ["MT-BATERIA"],
    "18.09.01.090": ["MT-BATERIA", "MT-INVERSOR"],
}


def main() -> int:
    n = 0
    for codigo, refs in A_RETIRAR.items():
        ruta = DESCOMP / f"{codigo}.json"
        if not ruta.exists():
            print(f"  (omitido) no existe {codigo}")
            continue
        d = json.loads(ruta.read_text(encoding="utf-8"))
        antes = len(d["recursos"])
        d["recursos"] = [r for r in d["recursos"] if r["ref"] not in refs]
        despues = len(d["recursos"])
        if antes != despues:
            ruta.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            n += 1
            print(f"  {codigo}: {antes}→{despues} recursos (-{', '.join(refs)})")
    print(f"Corregidas {n} partidas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
