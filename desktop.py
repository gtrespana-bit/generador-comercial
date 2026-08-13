#!/usr/bin/env python3
"""Modo escritorio: abre CotizaT en su propia ventana.

Usa pywebview (ventana nativa con WebView2 en Windows / WKWebView en macOS)
para mostrar la aplicación sin necesidad de navegador. El servidor local
arranca en segundo plano en 127.0.0.1 y se cierra al cerrar la ventana.

Uso:
    python desktop.py                     # ventana propia (recomendado)
    python desktop.py --navegador         # modo clásico: abre el navegador

Variables de entorno opcionales:
    COTIZAT_PORT=8000        Puerto fijo (por defecto: uno libre)
    COTIZAT_NO_WINDOW=1      Sin ventana ni navegador (solo servidor,
                             útil en servidores o para pruebas)
    COTIZAT_ESPERA=120       Segundos máximos que se espera al servidor local.

Los nombres PRESUPUESTOS_* anteriores siguen aceptándose como alias.

Diagnóstico de una instalación nueva:
    %LOCALAPPDATA%\CotizaT\logs\inicio.log
Las instalaciones actualizadas conservan su carpeta histórica si contiene datos.
"""
import ctypes
import logging
import os
import socket
import sys
import threading
import time
import traceback
import webbrowser
from pathlib import Path

from app.branding import PRODUCT_NAME, resolve_data_directory

NOMBRE_APP = PRODUCT_NAME


def asegurar_consola_inexistente() -> None:
    """Evita el fallo de arranque en el .exe sin consola.

    PyInstaller (console=False) deja sys.stdout y sys.stderr en None.
    Librerías como Uvicorn llaman a sys.stdout.isatty() al configurar su
    logging, lo que provocaba:

        AttributeError: 'NoneType' object has no attribute 'isatty'
        ValueError: Unable to configure formatter 'default'

    y el .exe se instalaba pero nunca abría su ventana. Al sustituirlos por
    /dev/null todas esas llamadas (write, flush, isatty, fileno) funcionan
    de forma segura, y el diagnóstico sigue yendo al archivo inicio.log.
    """
    if not getattr(sys, "frozen", False):
        return
    for nombre in ("stdout", "stderr"):
        if getattr(sys, nombre) is None:
            try:
                setattr(sys, nombre, open(os.devnull, "w", encoding="utf-8"))
            except OSError:
                logging.getLogger(__name__).exception(
                    "No se pudo sustituir sys.%s por /dev/null", nombre
                )


def directorio_datos() -> Path:
    """Devuelve una ubicación escribible incluso cuando se ejecuta el .exe."""
    if getattr(sys, "frozen", False):
        raiz = Path(
            os.environ.get("LOCALAPPDATA")
            or os.environ.get("APPDATA")
            or str(Path.home())
        )
        return resolve_data_directory(raiz)
    return Path(__file__).resolve().parent


def configurar_diagnostico() -> Path:
    """Registra los errores que normalmente ocultaría un .exe sin consola."""
    ruta_log = directorio_datos() / "logs" / "inicio.log"
    ruta_log.parent.mkdir(parents=True, exist_ok=True)

    handlers: list[logging.Handler] = [
        logging.FileHandler(ruta_log, encoding="utf-8"),
    ]
    # Al ejecutar desde código resulta útil conservar también la salida normal.
    if not getattr(sys, "frozen", False):
        handlers.append(logging.StreamHandler())
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
        force=True,
    )

    def excepcion_no_controlada(tipo, valor, tb):
        logging.getLogger(__name__).critical(
            "Error no controlado:\n%s", "".join(traceback.format_exception(tipo, valor, tb))
        )

    def excepcion_hilo(args):
        logging.getLogger(__name__).critical(
            "Error no controlado en el hilo %s:\n%s",
            args.thread.name if args.thread else "desconocido",
            "".join(traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback)),
        )

    sys.excepthook = excepcion_no_controlada
    threading.excepthook = excepcion_hilo
    return ruta_log


def cola_log(ruta_log: Path | None, lineas: int = 30, max_chars: int = 2000) -> str:
    """Últimas líneas de inicio.log, para mostrarlas en el propio cuadro de error.

    Así el usuario ve la causa sin tener que buscar el archivo (que a veces
    parece «vacío» porque solo contiene avisos informativos).
    """
    if ruta_log is None:
        return ""
    try:
        contenido = ruta_log.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return ""
    seleccion = contenido[-lineas:]
    texto = "\n".join(seleccion)
    if len(texto) > max_chars:
        texto = texto[-max_chars:]
    return f"\n\nÚltimas líneas del registro:\n{texto}"


def mostrar_error(mensaje: str, ruta_log: Path | None = None) -> None:
    """Muestra un error visible en Windows y deja el detalle técnico en el log."""
    detalle = mensaje
    detalle += cola_log(ruta_log)
    if ruta_log:
        detalle += f"\n\nDetalle técnico: {ruta_log}"
    logging.getLogger(__name__).error(detalle)

    if os.name == "nt":
        try:
            ctypes.windll.user32.MessageBoxW(  # type: ignore[attr-defined]
                0, detalle, NOMBRE_APP, 0x10  # MB_ICONERROR
            )
            return
        except Exception:
            logging.getLogger(__name__).exception("No se pudo mostrar el cuadro de error de Windows")
    print(detalle, file=sys.stderr)


def puerto_libre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def puerto_configurado() -> int:
    valor = (os.environ.get("COTIZAT_PORT") or os.environ.get("PRESUPUESTOS_PORT") or "").strip()
    if not valor:
        return puerto_libre()
    try:
        puerto = int(valor)
        if 1 <= puerto <= 65535:
            return puerto
    except ValueError:
        pass
    logging.getLogger(__name__).warning(
        "COTIZAT_PORT=%r no es un puerto válido; se usará uno libre.", valor
    )
    return puerto_libre()


def _espera_maxima_segundos() -> float:
    """Segundos máximos que se espera a que el servidor local arranque.

    La primera ejecución en equipos lentos (antivirus escaneando el .exe,
    disco mecánico, migraciones y datos de ejemplo creándose) puede tardar
    bastante más de 10 segundos; por defecto se esperan 120. Se puede subir
    con COTIZAT_ESPERA (también se acepta el nombre histórico).
    """
    valor = (os.environ.get("COTIZAT_ESPERA") or os.environ.get("PRESUPUESTOS_ESPERA") or "").strip()
    try:
        segundos = float(valor)
        if segundos > 0:
            return segundos
    except ValueError:
        pass
    if valor:
        logging.getLogger(__name__).warning(
            "COTIZAT_ESPERA=%r no es válido; se esperarán 120 segundos.", valor
        )
    return 120.0


def servidor_listo(
    host: str,
    puerto: int,
    hilo: threading.Thread,
    estado: dict,
    espera_maxima: float | None = None,
) -> bool:
    """Espera a que Uvicorn haya completado el arranque de la aplicación.

    Devuelve True en cuanto el servidor acepta conexiones. Solo devuelve
    False cuando el hilo del servidor ha muerto (el error queda registrado
    en ``estado["error"]`` y en inicio.log) o cuando se agota
    ``espera_maxima`` (120 s por defecto), registrando igualmente el motivo
    para que el diagnóstico nunca quede vacío.
    """
    log = logging.getLogger(__name__)
    limite = espera_maxima if espera_maxima is not None else _espera_maxima_segundos()
    inicio_espera = time.monotonic()
    ultimo_aviso = inicio_espera

    while True:
        try:
            with socket.create_connection((host, puerto), timeout=0.25):
                log.info(
                    "Servidor local listo en %.1f s (http://%s:%s/)",
                    time.monotonic() - inicio_espera,
                    host,
                    puerto,
                )
                return True
        except OSError:
            pass

        if not hilo.is_alive():
            log.error(
                "El hilo del servidor terminó antes de aceptar conexiones. "
                "Error capturado: %r",
                estado.get("error"),
            )
            return False

        transcurrido = time.monotonic() - inicio_espera
        if transcurrido >= limite:
            log.error(
                "El servidor local no respondió en %.0f s (fase actual: %s). "
                "El equipo puede estar muy lento o el antivirus estar "
                "bloqueando la aplicación.",
                transcurrido,
                estado.get("fase", "desconocida"),
            )
            return False

        # Aviso periódico para que el registro muestre progreso y no parezca
        # que "no hay información" cuando el arranque simplemente tarda.
        if time.monotonic() - ultimo_aviso >= 5:
            ultimo_aviso = time.monotonic()
            log.info(
                "Esperando al servidor local... %.0f s (fase: %s)",
                transcurrido,
                estado.get("fase", "desconocida"),
            )
        time.sleep(0.1)


def ejecutar_servidor(host: str, puerto: int, estado: dict) -> None:
    """Arranca FastAPI en el hilo secundario y registra cualquier excepción.

    El error concreto se guarda en ``estado["error"]`` para que el cuadro de
    diálogo pueda mostrar la causa real en lugar de un mensaje genérico.
    """
    log = logging.getLogger(__name__)
    try:
        # Se mantienen como importaciones explícitas para que PyInstaller las
        # detecte, pero se hacen aquí para poder registrar fallos de importación.
        estado["fase"] = "importando módulos"
        import uvicorn
        from app.main import app

        # Preparar la base de datos ANTES de arrancar Uvicorn. Si algo falla
        # aquí (una base de una versión anterior a la que le falta una
        # columna, un disco sin permisos...) el error real se propaga con su
        # traza completa. Dentro de Uvicorn ese mismo fallo ocurriría en el
        # lifespan y sólo se vería como «SystemExit: 3», que no dice nada al
        # usuario. Es idempotente: el lifespan volverá a llamarla sin efecto.
        estado["fase"] = "preparando la base de datos"
        from app.database import DB_PATH, init_db

        log.info("Base de datos: %s", DB_PATH)
        init_db()

        estado["fase"] = "arrancando servidor"
        log.info("Iniciando servidor local en http://%s:%s/", host, puerto)
        # log_config=None: Uvicorn no reconfigura el logging con formateadores
        # de consola (que requieren sys.stdout). Así los mensajes de Uvicorn
        # siguen propagándose al archivo inicio.log configurado arriba.
        uvicorn.run(app, host=host, port=puerto, log_level="warning", log_config=None)
        estado["fase"] = "servidor detenido"
    except BaseException as exc:
        estado["error"] = exc
        estado["fase"] = "error"
        log.exception("El servidor local no pudo iniciarse")


def describir_error(error: BaseException) -> str:
    """Convierte el error interno en algo que el usuario pueda entender.

    Uvicorn aborta el arranque con ``sys.exit(3)`` cuando la aplicación falla
    al iniciarse (o cuando el puerto está ocupado). Ese ``SystemExit: 3`` no
    explica nada por sí solo, así que aquí se acompaña de la causa probable y
    se remite a las líneas del registro, donde sí queda la traza real.
    """
    if isinstance(error, SystemExit) and error.code == 3:
        return (
            "el servidor abortó el arranque (SystemExit: 3). Suele deberse a "
            "un error al preparar la base de datos o a que el puerto está "
            "ocupado. El detalle exacto aparece en las líneas del registro."
        )
    return f"{type(error).__name__}: {error}"


def abrir_navegador(url: str) -> bool:
    try:
        abierto = webbrowser.open(url, new=2)
        if abierto:
            logging.getLogger(__name__).info("Aplicación abierta en el navegador: %s", url)
        else:
            logging.getLogger(__name__).error("El sistema no encontró un navegador predeterminado.")
        return abierto
    except Exception:
        logging.getLogger(__name__).exception("No se pudo abrir el navegador")
        return False


def habilitar_menus_contextuales_webview() -> None:
    """Activa el menú contextual nativo de WebView2 sin activar modo depuración.

    pywebview desactiva los menús contextuales en Windows cuando la aplicación
    se ejecuta fuera de `debug=True`. Ese menú es precisamente el que muestra
    las sugerencias ortográficas y permite corregir la palabra marcada en rojo.
    Aquí se parchea únicamente el backend EdgeChromium/WinForms para que los
    menús contextuales estén habilitados, manteniendo las herramientas de
    desarrollo desactivadas.
    """
    if os.name != "nt":
        return

    try:
        from webview.platforms import edgechromium

        on_webview_ready_original = edgechromium.EdgeChrome.on_webview_ready

        def on_webview_ready_con_corrector(self, sender, args):
            on_webview_ready_original(self, sender, args)
            try:
                if args.IsSuccess and sender.CoreWebView2 is not None:
                    sender.CoreWebView2.Settings.AreDefaultContextMenusEnabled = True
                    # Que exista el menú no debe abrir DevTools en producción.
                    sender.CoreWebView2.Settings.AreDevToolsEnabled = False
                    sender.CoreWebView2.Settings.AreBrowserAcceleratorKeysEnabled = False
                    logging.getLogger(__name__).info(
                        "Menú contextual de WebView2 habilitado para corrección ortográfica."
                    )
            except Exception:
                logging.getLogger(__name__).exception(
                    "No se pudieron aplicar los ajustes del corrector ortográfico de WebView2"
                )

        edgechromium.EdgeChrome.on_webview_ready = on_webview_ready_con_corrector
        logging.getLogger(__name__).info(
            "Parche de menús contextuales de WebView2 preparado para autocorrección."
        )
    except Exception:
        logging.getLogger(__name__).exception(
            "No se pudo preparar el corrector ortográfico nativo de WebView2; "
            "se continuará con la configuración predeterminada."
        )


def main() -> None:
    asegurar_consola_inexistente()
    ruta_log = configurar_diagnostico()
    log = logging.getLogger(__name__)
    log.info(
        "=== Arranque de la aplicación de escritorio === (frozen=%s, Python %s, exe=%s)",
        getattr(sys, "frozen", False),
        sys.version.split()[0],
        sys.executable,
    )
    log.info("Datos y registro en: %s", directorio_datos())

    host = "127.0.0.1"
    puerto = puerto_configurado()
    url = f"http://{host}:{puerto}/"

    estado: dict = {"fase": "pendiente", "error": None}
    hilo = threading.Thread(
        target=ejecutar_servidor,
        args=(host, puerto, estado),
        name="servidor-cotizat",
        daemon=True,
    )
    hilo.start()
    if not servidor_listo(host, puerto, hilo, estado):
        error = estado.get("error")
        if error is not None:
            mensaje = (
                "No se pudo iniciar el servidor local de CotizaT.\n\n"
                f"Causa: {describir_error(error)}"
            )
        else:
            mensaje = (
                "El servidor local de CotizaT tardó demasiado en arrancar.\n\n"
                "Suele ocurrir la primera vez, mientras el antivirus escanea la "
                "aplicación o se preparan la base de datos y los datos de "
                "ejemplo. Vuelve a intentarlo; si se repite en un equipo lento, "
                "aumenta la variable COTIZAT_ESPERA (segundos)."
            )
        mostrar_error(mensaje, ruta_log)
        return

    if (os.environ.get("COTIZAT_NO_WINDOW") or os.environ.get("PRESUPUESTOS_NO_WINDOW")) == "1":
        logging.getLogger(__name__).info("Modo sin ventana solicitado.")
        hilo.join()  # Solo servidor (modo headless / pruebas).
        return

    if "--navegador" in sys.argv:
        if not abrir_navegador(url):
            mostrar_error("No se encontró un navegador para abrir la aplicación.", ruta_log)
            return
        hilo.join()
        return

    # --- Ventana nativa con pywebview -------------------------------------
    try:
        import webview
    except ImportError:
        logging.getLogger(__name__).exception("pywebview no está disponible")
        if abrir_navegador(url):
            hilo.join()
        else:
            mostrar_error("No se pudo cargar la ventana de la aplicación.", ruta_log)
        return

    habilitar_menus_contextuales_webview()

    try:
        webview.create_window(
            title="CotizaT — Presupuestos de obra",
            url=url,
            width=1360,
            height=860,
            min_size=(1060, 680),
        )

        # `icon` es un argumento de start(), no de create_window(). Pasarlo
        # a create_window provoca TypeError y hacía que el .exe nunca mostrase
        # su ventana. En Windows el icono del ejecutable cubre además el caso
        # de pywebview/WinForms.
        icono = Path(__file__).resolve().parent / "icono.ico"
        perfil_webview = directorio_datos() / "webview"
        perfil_webview.mkdir(parents=True, exist_ok=True)
        opciones_inicio = {
            "private_mode": False,
            "storage_path": str(perfil_webview),
        }
        if icono.exists():
            opciones_inicio["icon"] = str(icono)
        webview.start(**opciones_inicio)
    except BaseException:
        logging.getLogger(__name__).exception("No se pudo abrir la ventana nativa")
        if abrir_navegador(url):
            hilo.join()
        else:
            mostrar_error(
                "No se pudo abrir la ventana de CotizaT ni el navegador. "
                "Revise el archivo de diagnóstico.",
                ruta_log,
            )


if __name__ == "__main__":
    main()
