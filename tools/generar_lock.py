"""Regenera `requirements.lock` con el cierre completo de dependencias.

`requirements.txt` fija las dependencias directas. Este archivo produce además
el cierre transitivo exacto (dependencias de las dependencias) para que la
integración continua instale siempre el mismo conjunto de paquetes.

Uso:
    python tools/generar_lock.py

Crea un entorno virtual temporal, instala `requirements-dev.txt` dentro y
escribe el resultado de `pip freeze` en `requirements.lock`.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LOCK = REPO / "requirements.lock"

CABECERA = """# Cierre completo de dependencias (generado, no editar a mano).
#
# Regenerar con:  python tools/generar_lock.py
# Fuente:         requirements-dev.txt (que incluye requirements.txt)
#
# Se usa en integración continua para que las pruebas se ejecuten siempre
# contra el mismo conjunto exacto de paquetes, incluidas las transitivas.
"""


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="cotizat-lock-") as tmp:
        entorno = Path(tmp) / "venv"
        print(f"Creando entorno temporal en {entorno} ...")
        subprocess.run([sys.executable, "-m", "venv", str(entorno)], check=True)

        pip = entorno / "bin" / "pip"
        if not pip.exists():  # Windows
            pip = entorno / "Scripts" / "pip.exe"

        print("Instalando requirements-dev.txt ...")
        subprocess.run(
            [str(pip), "install", "--quiet", "-r", str(REPO / "requirements-dev.txt")],
            check=True,
        )

        print("Calculando cierre con pip freeze ...")
        freeze = subprocess.run(
            [str(pip), "freeze"], check=True, capture_output=True, text=True
        ).stdout

    lineas = sorted(
        (l for l in freeze.splitlines() if l.strip() and not l.startswith("-e ")),
        key=str.lower,
    )
    LOCK.write_text(CABECERA + "\n".join(lineas) + "\n", encoding="utf-8")
    print(f"Escrito {LOCK} con {len(lineas)} paquetes ✅")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
