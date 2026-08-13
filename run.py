#!/usr/bin/env python3
"""Punto de entrada de la aplicación.

Abre la app en el navegador automáticamente y la sirve en el puerto 8000.

Uso:
    python run.py

Variables de entorno opcionales:
    COTIZAT_HOST=127.0.0.1        Interfaz local (usar 0.0.0.0 solo deliberadamente)
    COTIZAT_PORT=8000             Puerto del servidor
    COTIZAT_NO_BROWSER=1          No abrir el navegador

Los nombres PRESUPUESTOS_* continúan aceptándose por compatibilidad.
"""
import os
import threading
import webbrowser

import uvicorn

HOST = os.environ.get("COTIZAT_HOST") or os.environ.get("PRESUPUESTOS_HOST") or "127.0.0.1"
PORT = int(os.environ.get("COTIZAT_PORT") or os.environ.get("PRESUPUESTOS_PORT") or "8000")


def _abrir_navegador(url: str):
    try:
        webbrowser.open(url)
    except Exception:
        pass  # en equipos sin interfaz gráfica simplemente no se abre


if __name__ == "__main__":
    no_browser = os.environ.get("COTIZAT_NO_BROWSER") or os.environ.get("PRESUPUESTOS_NO_BROWSER")
    if no_browser != "1":
        # Pequeña espera para dar tiempo a que el servidor arranque
        threading.Timer(1.2, _abrir_navegador, args=(f"http://localhost:{PORT}/",)).start()
    uvicorn.run("app.main:app", host=HOST, port=PORT, log_level="info")
