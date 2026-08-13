#!/bin/bash
# ============================================================
#   CotizaT - Inicio rápido (Linux)
#   Puedes hacer doble clic (Ejecutar) o ejecutarlo en terminal.
# ============================================================
cd "$(dirname "$0")" || exit 1

echo
echo "  COTIZAT"
echo

PY=python3
if ! command -v "$PY" >/dev/null 2>&1; then
  echo "  [ERROR] No se encontró Python 3."
  echo "  Instálalo con:  sudo apt install python3 python3-venv python3-pip"
  exit 1
fi

if [ ! -x ".venv/bin/python" ]; then
  echo "  Primera ejecución: creando entorno virtual..."
  "$PY" -m venv .venv || { echo "  [ERROR] No se pudo crear el entorno. ¿Falta python3-venv?"; exit 1; }
fi

if ! .venv/bin/python -c "import fastapi, sqlalchemy, reportlab, PIL, openpyxl" >/dev/null 2>&1; then
  echo "  Instalando dependencias (una sola vez)..."
  .venv/bin/python -m pip install --quiet --upgrade pip
  .venv/bin/python -m pip install --quiet -r requirements.txt || {
    echo "  [ERROR] No se pudieron instalar las dependencias."
    exit 1
  }
fi

echo "  Aplicación disponible en http://localhost:8000"
echo "  Pulsa Ctrl+C para detenerla."
echo

exec .venv/bin/python run.py
