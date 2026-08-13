@echo off
REM ============================================================================
REM  Empaqueta CotizaT como aplicacion de escritorio (.exe)
REM  Requisito: Python 3.10+ instalado (con "Add to Python PATH" marcado).
REM
REM  Resultado:  dist\CotizaT.exe
REM  - Es una aplicacion de VENTANA PROPIA (pywebview): se abre en su propia
REM    ventana, sin navegador y sin consola negra.
REM  - Copia el archivo dist\CotizaT.exe a cualquier PC con Windows y haz
REM    doble clic (no necesita Python instalado).
REM  - Para entregar la app a otras personas usa mejor CREAR_INSTALADOR.bat:
REM    incluye la instalación automática de WebView2 si el PC lo necesita.
REM ============================================================================
cd /d "%~dp0"

echo [1/3] Comprobando Python y PyInstaller...

REM --- Localizar ejecutable de Python (.venv, py launcher o python) ---
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
    echo.
    echo [ERROR] No se encontro Python en este equipo.
    echo Descargalo e instalalo desde https://www.python.org/downloads/
    echo IMPORTANTE: marca la casilla "Add Python to PATH" durante la instalacion.
    pause
    exit /b 1
)

REM --- Comprobar e instalar PyInstaller y dependencias ---
echo Comprobando PyInstaller y dependencias (FastAPI, Uvicorn, etc.)...
%PY% -c "import PyInstaller, fastapi, uvicorn, sqlalchemy, jinja2, reportlab, webview, clr, multipart, PIL; from importlib.metadata import version; assert int(version('pywebview').split('.')[0]) >= 6" >nul 2>&1
if errorlevel 1 (
    echo Instalando / actualizando PyInstaller y dependencias del proyecto...
    %PY% -m pip install --upgrade pip
    %PY% -m pip install pyinstaller -r requirements-desktop.txt
    if errorlevel 1 (
        echo [ERROR] No se pudieron instalar las dependencias o PyInstaller. Revisa tu conexion a internet.
        pause
        exit /b 1
    )
)

echo [2/3] Empaquetando (tarda unos minutos)...
%PY% -m PyInstaller presupuestos.spec --noconfirm --clean
if errorlevel 1 (
    echo.
    echo ERROR empaquetando la aplicacion.
    pause
    exit /b 1
)

echo [3/3] Hecho.
echo.
echo La aplicacion esta en:  dist\CotizaT.exe
echo Copialo a cualquier PC con Windows y haz doble clic:
echo se abrira en su propia ventana (sin navegador).
echo.
echo IMPORTANTE: una instalacion nueva guarda los datos en %%LOCALAPPDATA%%\CotizaT.
echo Si ya existe %%LOCALAPPDATA%%\Presupuestos con datos de una version anterior,
echo CotizaT conserva esa ubicacion. Actualizar no borra presupuestos ni backups.
pause
