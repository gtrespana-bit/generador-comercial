# -*- mode: python ; coding: utf-8 -*-
# Especificación de PyInstaller para empaquetar el Generador de Presupuestos
# como aplicación de escritorio con VENTANA PROPIA (pywebview, sin navegador).
# Uso:  pyinstaller presupuestos.spec --noconfirm
# Resultado:  dist/Presupuestos.exe
#
# · Los datos del usuario (presupuestos.db, backups/, uploads/) se guardan
#   en %LOCALAPPDATA%\Presupuestos (ver app/database.py), nunca dentro del
#   .exe, para que la app instalada no necesite permisos de administrador
#   y no pierda datos al actualizar.
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules

# Recolectar explícitamente todos los módulos del backend y frameworks
# (muchos de ellos usan importaciones dinámicas que PyInstaller podría pasar por alto)
hiddenimports = [
    "webview",
    "webview.guilib",
    "webview.platforms.winforms",
    "webview.platforms.edgechromium",
    "webview.platforms.mshtml",
    "clr",
    "fastapi",
    "fastapi.responses",
    "fastapi.staticfiles",
    "fastapi.templating",
    "uvicorn",
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.loops.asyncio",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.http.h11_impl",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "uvicorn.lifespan.off",
    "starlette",
    "starlette.responses",
    "starlette.staticfiles",
    "starlette.templating",
    "starlette.formparsers",
    "pydantic",
    "sqlalchemy",
    "sqlalchemy.dialects.sqlite",
    "jinja2",
    "reportlab",
    "multipart",
    "PIL",
    "email_validator",
    "sqlite3",
    "app",
    "app.main",
    "app.database",
    "app.models",
    "app.services",
    "app.services.pdf",
    "app.utils",
    "app.seeds",
]

for mod in [
    "fastapi",
    "uvicorn",
    "starlette",
    "pydantic",
    "sqlalchemy",
    "reportlab",
    "webview",
    "anyio",
]:
    try:
        hiddenimports += collect_submodules(mod)
    except Exception:
        pass

# pywebview carga en tiempo de ejecución sus archivos JavaScript, los ensamblados
# Microsoft.Web.WebView2.* y WebView2Loader.dll. `collect_submodules` no incluye
# esos recursos: si faltan, el .exe se instala pero no llega a crear su ventana.
datas = [
    ("app/static", "app/static"),      # css, js, fuentes Lato, icono
    ("app/templates", "app/templates"),
    ("icono.ico", "."),
]
binaries = []
try:
    datas += collect_data_files("webview", includes=["js/**", "lib/**"])
    binaries += collect_dynamic_libs("webview")
except Exception:
    pass
try:
    datas += collect_data_files("fastapi")
except Exception:
    pass

a = Analysis(
    ["desktop.py"],
    pathex=["."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "numpy", "pandas", "PyQt5", "PyQt6", "PySide2", "PySide6"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name="Presupuestos",
    debug=False,
    console=False,       # app de ventana: errores en %LOCALAPPDATA%\Presupuestos\logs
    icon="icono.ico",
    uac_admin=False,
)

# (Un único archivo ejecutable autónomo: más fácil de instalar y copiar)
