@echo off
REM Abre CotizaT en su propia VENTANA (sin navegador).
REM Necesita Python y las dependencias instaladas (ver INICIAR.bat la primera vez).
cd /d "%~dp0"

set "PY="
if exist ".venv\Scripts\python.exe" (
    set "PY=.venv\Scripts\python.exe"
) else (
    where py >nul 2>&1 && set "PY=py"
    if not defined PY (
        where python >nul 2>&1 && set "PY=python"
    )
)

if not defined PY (
    echo [ERROR] No se encontro Python en este equipo.
    echo Ejecuta primero INICIAR.bat o instala Python desde https://www.python.org/downloads/
    pause
    exit /b 1
)

REM --- Comprobar el motor de ventana nativa (pywebview + pythonnet) ---
%PY% -c "import webview, clr; from importlib.metadata import version; assert int(version('pywebview').split('.')[0]) >= 6" >nul 2>&1
if errorlevel 1 (
    echo Preparando el motor de ventana nativa...
    %PY% -m pip install --upgrade -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] No se pudieron instalar las dependencias de escritorio.
        echo Revisa tu conexion a internet y vuelve a intentarlo.
        pause
        exit /b 1
    )
)

%PY% desktop.py
