#!/usr/bin/env python3
"""Punto de entrada de la aplicación.

Abre la app en el navegador automáticamente y la sirve en el puerto 8000.

Uso:
    python run.py

Variables de entorno opcionales:
    PRESUPUESTOS_PORT=8000        Puerto del servidor
    PRESUPUESTOS_NO_BROWSER=1     No abrir el navegador (servidores sin interfaz)
"""
import os
import threading
import webbrowser

import uvicorn

HOST = os.environ.get("PRESUPUESTOS_HOST", "0.0.0.0")
PORT = int(os.environ.get("PRESUPUESTOS_PORT", "8000"))


def _abrir_navegador(url: str):
    try:
        webbrowser.open(url)
    except Exception:
        pass  # en equipos sin interfaz gráfica simplemente no se abre


if __name__ == "__main__":
    if os.environ.get("PRESUPUESTOS_NO_BROWSER") != "1":
        # Pequeña espera para dar tiempo a que el servidor arranque
        threading.Timer(1.2, _abrir_navegador, args=(f"http://localhost:{PORT}/",)).start()
    uvicorn.run("app.main:app", host=HOST, port=PORT, log_level="info")
