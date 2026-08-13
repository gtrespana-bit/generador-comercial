@echo off
REM ============================================================
REM   CotizaT - Inicio con doble clic (Windows)
REM   No cierres esta ventana mientras uses la aplicacion.
REM   Para salir, cierra esta ventana.
REM ============================================================
cd /d "%~dp0"
title CotizaT

echo.
echo   ============================================
echo     COTIZAT
echo   ============================================
echo.

REM --- Localizar Python (primero el launcher py, luego python) ---
set "PY="
where py >nul 2>&1 && set "PY=py"
if not defined PY (
  where python >nul 2>&1 && set "PY=python"
)
if not defined PY (
  echo   [ERROR] No se encontro Python en este equipo.
  echo.
  echo   Instala Python desde https://www.python.org/downloads/
  echo   IMPORTANTE: marca la casilla "Add Python to PATH".
  echo   Luego vuelve a hacer doble clic en este archivo.
  echo.
  pause
  exit /b 1
)

REM --- Crear el entorno virtual solo la primera vez ---
if not exist ".venv\Scripts\python.exe" (
  echo   Primera ejecucion: preparando el entorno...
  echo   ^(solo ocurre una vez, tarda 1-2 minutos^)
  echo.
  %PY% -m venv .venv
  if errorlevel 1 (
    echo   [ERROR] No se pudo crear el entorno virtual.
    pause
    exit /b 1
  )
)

REM --- Instalar dependencias si faltan ---
".venv\Scripts\python.exe" -c "import fastapi, sqlalchemy, reportlab, PIL, openpyxl" >nul 2>&1
if errorlevel 1 (
  echo   Instalando dependencias ^(una sola vez^)...
  ".venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
  ".venv\Scripts\python.exe" -m pip install --quiet -r requirements.txt
  if errorlevel 1 (
    echo   [ERROR] No se pudieron instalar las dependencias.
    echo   Revisa tu conexion a internet y vuelve a intentarlo.
    pause
    exit /b 1
  )
)

echo   Todo listo. Se abrira el navegador en
echo   http://localhost:8000
echo.
echo   ------------------------------------------------
echo   NO CIERRES ESTA VENTANA mientras trabajes.
echo   Cuando termines, cierrala y la app se detiene.
echo   ------------------------------------------------
echo.

REM --- Arrancar la aplicacion (run.py abre el navegador solo) ---
".venv\Scripts\python.exe" run.py

echo.
echo   Aplicacion detenida. Puedes cerrar esta ventana.
pause
