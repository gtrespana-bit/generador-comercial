#!/usr/bin/env python3
"""Prueba reproducible del editor, la gestión y /recursos con 5.000 partidas.

Crea una SQLite temporal, nunca toca la base configurada por el usuario y
falla si se superan los umbrales acordados para las rutas principales.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import tempfile
import time
import sys

from sqlalchemy import event

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--partidas", type=int, default=5000)
    args = parser.parse_args()
    cantidad = max(1, args.partidas)

    with tempfile.TemporaryDirectory(prefix="cotizat-benchmark-") as temporal:
        ruta = Path(temporal) / "benchmark.db"
        os.environ.pop("DATABASE_URL", None)
        os.environ["COTIZAT_DB"] = str(ruta)

        # Se importa después de fijar COTIZAT_DB: app.database resuelve la URL
        # al cargar el módulo.
        from fastapi.testclient import TestClient
        from app.database import SessionLocal, engine, init_db
        from app.main import app
        from app.models import Partida
        from app.services.onboarding import completar_onboarding

        init_db()
        with SessionLocal() as db:
            completar_onboarding(
                db,
                {"empresa_nombre": "Benchmark catálogo", "moneda_default": "USD"},
                "limpio",
            )
            for indice in range(cantidad):
                cap = indice % 18 + 1
                sub = indice % 30 + 1
                apartado = indice % 20 + 1
                db.add(Partida(
                    nombre=f"Partida técnica de rendimiento {indice:04d}",
                    descripcion=(
                        "Suministro, colocación, preparación del soporte, prueba y "
                        "puesta en marcha con materiales especializados para "
                        "construcción y rehabilitación. "
                    ) * 3,
                    precio_unitario=10 + indice / 100,
                    unidad="m2",
                    categoria=f"{cap:02d} Capítulo de prueba {cap:02d}",
                    subcategoria=f"{cap:02d}.{sub:02d} Subcapítulo técnico {sub:02d}",
                    apartado=(
                        f"{cap:02d}.{sub:02d}.{apartado:02d} "
                        f"Apartado especializado {apartado:02d}"
                    ),
                    codigo_interno=f"{cap:02d}.{sub:02d}.{apartado:02d}.{indice:03d}",
                    descomposicion_json=json.dumps({
                        "filas": [{
                            "tipo": "recurso",
                            "codigo": "MO",
                            "descripcion": "Oficial",
                            "rendimiento": 1,
                            "precio": 5,
                        }],
                    }),
                ))
            db.commit()

        with TestClient(app) as client:
            def medir_recursos():
                selects = 0

                def contar_select(_conexion, _cursor, statement, _params, _contexto, _many):
                    nonlocal selects
                    if statement.lstrip().upper().startswith("SELECT"):
                        selects += 1

                event.listen(engine, "before_cursor_execute", contar_select)
                try:
                    inicio = time.perf_counter()
                    respuesta = client.get("/recursos")
                    segundos = time.perf_counter() - inicio
                finally:
                    event.remove(engine, "before_cursor_execute", contar_select)
                return respuesta, segundos, selects

            recursos_primera, segundos_recursos_primera, recursos_primera_selects = medir_recursos()
            recursos_repetida, segundos_recursos_repetida, recursos_repetida_selects = medir_recursos()

            inicio = time.perf_counter()
            editor = client.get("/presupuestos/nuevo")
            segundos_editor = time.perf_counter() - inicio

            inicio = time.perf_counter()
            datos = client.get("/presupuestos/editor/datos")
            segundos_datos = time.perf_counter() - inicio
            indice = (datos.json() or {}).get("partidas") or []

            inicio = time.perf_counter()
            datos_arbol = client.get("/presupuestos/editor/datos?fase=indice")
            segundos_arbol = time.perf_counter() - inicio

            inicio = time.perf_counter()
            datos_catalogos = client.get("/presupuestos/editor/datos?fase=resto")
            segundos_catalogos = time.perf_counter() - inicio

            inicio = time.perf_counter()
            gestion = client.get("/partidas")
            segundos_gestion = time.perf_counter() - inicio

            busqueda_selects = 0

            def contar_select(_conexion, _cursor, statement, _params, _contexto, _many):
                nonlocal busqueda_selects
                if statement.lstrip().upper().startswith("SELECT"):
                    busqueda_selects += 1

            event.listen(engine, "before_cursor_execute", contar_select)
            try:
                inicio = time.perf_counter()
                gestion_busqueda = client.get("/partidas", params={"q": "rendimiento"})
                segundos_busqueda = time.perf_counter() - inicio
            finally:
                event.remove(engine, "before_cursor_execute", contar_select)

        resultado = {
            "partidas": len(indice),
            "recursos_primera_status": recursos_primera.status_code,
            "recursos_primera_segundos": round(segundos_recursos_primera, 3),
            "recursos_primera_selects": recursos_primera_selects,
            "recursos_primera_bytes": len(recursos_primera.content),
            "recursos_repetida_status": recursos_repetida.status_code,
            "recursos_repetida_segundos": round(segundos_recursos_repetida, 3),
            "recursos_repetida_selects": recursos_repetida_selects,
            "editor_status": editor.status_code,
            "editor_segundos": round(segundos_editor, 3),
            "editor_bytes_sin_comprimir": len(editor.content),
            "datos_status": datos.status_code,
            "datos_segundos": round(segundos_datos, 3),
            "arbol_status": datos_arbol.status_code,
            "arbol_segundos": round(segundos_arbol, 3),
            "arbol_bytes_sin_comprimir": len(datos_arbol.content),
            "catalogos_status": datos_catalogos.status_code,
            "catalogos_segundos": round(segundos_catalogos, 3),
            "catalogos_bytes_sin_comprimir": len(datos_catalogos.content),
            "gestion_status": gestion.status_code,
            "gestion_segundos": round(segundos_gestion, 3),
            "gestion_bytes_sin_comprimir": len(gestion.content),
            "gestion_filas_renderizadas": gestion.text.count('class="partida-tr"'),
            "busqueda_status": gestion_busqueda.status_code,
            "busqueda_segundos": round(segundos_busqueda, 3),
            "busqueda_selects": busqueda_selects,
            "busqueda_bytes_sin_comprimir": len(gestion_busqueda.content),
            "busqueda_filas_renderizadas": gestion_busqueda.text.count('class="partida-tr"'),
        }
        print(json.dumps(resultado, ensure_ascii=False, indent=2))

        engine.dispose()
        if any(respuesta.status_code != 200 for respuesta in (
            recursos_primera, recursos_repetida, editor, datos, datos_arbol,
            datos_catalogos, gestion, gestion_busqueda,
        )):
            return 1
        if len(indice) != cantidad:
            return 1
        if (
            segundos_recursos_primera > 2.5
            or recursos_primera_selects > 50
            or segundos_recursos_repetida > 1.0
            or recursos_repetida_selects > 30
        ):
            return 1
        if segundos_editor > 2.5 or len(editor.content) > 500_000:
            return 1
        if segundos_datos > 2.5:
            return 1
        if segundos_gestion > 1.0 or gestion.text.count('class="partida-tr"') > 100:
            return 1
        # 5.000 partidas pueden producir hasta 100 coincidencias visibles,
        # pero el número de viajes SQL no debe crecer con esas filas.
        if (
            segundos_busqueda > 2.5
            or busqueda_selects > 40
            or gestion_busqueda.text.count('class="partida-tr"') > 100
        ):
            return 1
        if segundos_arbol > 2.5 or segundos_catalogos > 2.5:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
