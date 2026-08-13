@echo off
REM ============================================================================
REM  Crea el INSTALADOR de Windows de CotizaT.
REM  Necesita (solo la primera vez):
REM    1. Python 3.10+  ->  https://www.python.org/downloads/  (marca "Add to PATH")
REM    2. Inno Setup 6  ->  https://jrsoftware.org/isdl.php   (instalación por defecto)
REM
REM  Resultado:  instalador\Instalador_CotizaT.exe
REM  Ese archivo se puede copiar a cualquier PC con Windows: al ejecutarlo
REM  instala la app "como un programa normal": acceso directo en el escritorio,
REM  menú Inicio, desinstalador y ventana propia (sin navegador). Si al equipo
REM  le falta WebView2, el instalador lo descarga e instala silenciosamente.
REM ============================================================================
cd /d "%~dp0"

echo [1/4] Comprobando Python y PyInstaller...

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
%PY% -c "import PyInstaller, fastapi, uvicorn, sqlalchemy, jinja2, reportlab, webview, clr, multipart, PIL, openpyxl; from importlib.metadata import version; assert int(version('pywebview').split('.')[0]) >= 6" >nul 2>&1
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

echo [2/4] Empaquetando la aplicacion (tarda unos minutos)...
%PY% -m PyInstaller presupuestos.spec --noconfirm --clean
if errorlevel 1 (
    echo.
    echo ERROR empaquetando la aplicacion.
    pause
    exit /b 1
)

REM --- Incluir el bootstrapper oficial de Microsoft WebView2 ---
REM Solo el equipo que CREA el instalador necesita internet para descargar este
REM archivo (unos 2 MB). Los destinatarios no tienen que buscar ni instalar nada.
echo [3/4] Preparando el motor WebView2 para los destinatarios...
set "WEBVIEW2_DIR=recursos"
set "WEBVIEW2_BOOTSTRAPPER=%WEBVIEW2_DIR%\MicrosoftEdgeWebview2Setup.exe"
set "WEBVIEW2_TMP=%WEBVIEW2_BOOTSTRAPPER%.tmp"
set "WEBVIEW2_URL=https://go.microsoft.com/fwlink/p/?LinkId=2124703"

if not exist "%WEBVIEW2_BOOTSTRAPPER%" (
    if not exist "%WEBVIEW2_DIR%" mkdir "%WEBVIEW2_DIR%"
    del /q "%WEBVIEW2_TMP%" >nul 2>&1
    echo Descargando el componente oficial de Microsoft ^(solo una vez^)...
    where curl.exe >nul 2>&1
    if not errorlevel 1 (
        curl.exe -L --fail --retry 3 -o "%WEBVIEW2_TMP%" "%WEBVIEW2_URL%"
    ) else (
        powershell -NoProfile -ExecutionPolicy Bypass -Command "try { Invoke-WebRequest -UseBasicParsing -Uri '%WEBVIEW2_URL%' -OutFile '%WEBVIEW2_TMP%' } catch { exit 1 }"
    )
    if errorlevel 1 (
        echo [ERROR] No se pudo descargar el componente WebView2 de Microsoft.
        echo Revisa la conexion a internet y vuelve a ejecutar este archivo.
        del /q "%WEBVIEW2_TMP%" >nul 2>&1
        pause
        exit /b 1
    )
    move /y "%WEBVIEW2_TMP%" "%WEBVIEW2_BOOTSTRAPPER%" >nul
)

if not exist "%WEBVIEW2_BOOTSTRAPPER%" (
    echo [ERROR] No se pudo preparar el componente WebView2.
    pause
    exit /b 1
)

for %%A in ("%WEBVIEW2_BOOTSTRAPPER%") do if %%~zA LSS 500000 (
    echo [ERROR] El componente WebView2 descargado no es valido. Intenta de nuevo.
    del /q "%WEBVIEW2_BOOTSTRAPPER%" >nul 2>&1
    pause
    exit /b 1
)

REM Verifica que el fichero descargado conserva una firma válida de Microsoft.
powershell -NoProfile -ExecutionPolicy Bypass -Command "$s = Get-AuthenticodeSignature -FilePath '%WEBVIEW2_BOOTSTRAPPER%'; if ($s.Status -ne 'Valid' -or $s.SignerCertificate.Subject -notlike '*Microsoft Corporation*') { exit 1 }"
if errorlevel 1 (
    echo [ERROR] La firma del componente WebView2 no es valida.
    del /q "%WEBVIEW2_BOOTSTRAPPER%" >nul 2>&1
    pause
    exit /b 1
)

echo [4/4] Buscando Inno Setup...
set "ISCC="
where ISCC >nul 2>nul && set "ISCC=ISCC"
if not defined ISCC if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%LOCALAPPDATA%\Inno Setup 6\ISCC.exe" set "ISCC=%LOCALAPPDATA%\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%USERPROFILE%\AppData\Local\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%USERPROFILE%\AppData\Local\Programs\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%USERPROFILE%\AppData\Local\Inno Setup 6\ISCC.exe" set "ISCC=%USERPROFILE%\AppData\Local\Inno Setup 6\ISCC.exe"
if not defined ISCC (
    echo.
    echo No se encontro Inno Setup 6.
    echo Descargalo gratis en  https://jrsoftware.org/isdl.php  e instalalo,
    echo y vuelve a ejecutar este archivo.
    echo.
    echo Si ya lo tienes instalado, verifica la ubicacion e intenta:
    echo   - Agregar la carpeta de Inno Setup al PATH del sistema
    echo   - O ejecutar este archivo como administrador
    pause
    exit /b 1
)

echo Compilando el instalador...
"%ISCC%" instalador.iss

echo.
echo ============================================================================
echo  LISTO. Revisa la carpeta  instalador\  ->  Instalador_CotizaT.exe
echo  Copialo a cualquier PC con Windows y ejecutalo: instalara la aplicacion
echo  con acceso directo, menu Inicio y desinstalador, en su propia ventana.
echo ============================================================================
pause
