#!/bin/bash
# ============================================================
#   CotizaT - Inicio con doble clic (macOS)
#   No cierres esta ventana mientras uses la aplicación.
# ============================================================
cd "$(dirname "$0")" || exit 1

echo
echo "  ============================================"
echo "    COTIZAT"
echo "  ============================================"
echo

# --- Localizar Python 3 ---
PY=python3
if ! command -v "$PY" >/dev/null 2>&1; then
  echo "  [ERROR] No se encontró Python 3 en este equipo."
  echo
  echo "  Instálalo desde https://www.python.org/downloads/"
  echo "  y vuelve a hacer doble clic en este archivo."
  echo
  read -r -p "  Pulsa Enter para salir..."
  exit 1
fi

# --- Crear el entorno virtual solo la primera vez ---
if [ ! -x ".venv/bin/python" ]; then
  echo "  Primera ejecución: preparando el entorno..."
  echo "  (solo ocurre una vez, tarda 1-2 minutos)"
  echo
  "$PY" -m venv .venv || { echo "  [ERROR] No se pudo crear el entorno virtual."; read -r -p "  Pulsa Enter..."; exit 1; }
fi

# --- Instalar dependencias si faltan ---
if ! .venv/bin/python -c "import fastapi, sqlalchemy, reportlab, PIL, openpyxl" >/dev/null 2>&1; then
  echo "  Instalando dependencias (una sola vez)..."
  .venv/bin/python -m pip install --quiet --upgrade pip
  if ! .venv/bin/python -m pip install --quiet -r requirements.txt; then
    echo "  [ERROR] No se pudieron instalar las dependencias."
    echo "  Revisa tu conexión a internet y vuelve a intentarlo."
    read -r -p "  Pulsa Enter..."
    exit 1
  fi
fi

echo "  Todo listo. Se abrirá el navegador en"
echo "  http://localhost:8000"
echo
echo "  ------------------------------------------------"
echo "  NO CIERRES ESTA VENTANA mientras trabajes."
echo "  Cuando termines, ciérrala y la app se detiene."
echo "  ------------------------------------------------"
echo

# --- Arrancar la aplicación (run.py abre el navegador solo) ---
.venv/bin/python run.py

echo
echo "  Aplicación detenida. Puedes cerrar esta ventana."
