#!/usr/bin/env python3
"""Prueba reproducible del editor y la gestión con 5.000 partidas.

Crea una SQLite temporal, nunca toca la base configurada por el usuario y
falla si se superan los umbrales acordados para la fase 1.
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
            inicio = time.perf_counter()
            editor = client.get("/presupuestos/nuevo")
            segundos_editor = time.perf_counter() - inicio
            match = re.search(
                r'id="datos-catalogo"[^>]*>\s*(.*?)\s*</script>',
                editor.text,
                re.DOTALL,
            )
            indice = json.loads(match.group(1)) if match else []

            inicio = time.perf_counter()
            gestion = client.get("/partidas")
            segundos_gestion = time.perf_counter() - inicio

        resultado = {
            "partidas": len(indice),
            "editor_status": editor.status_code,
            "editor_segundos": round(segundos_editor, 3),
            "editor_bytes_sin_comprimir": len(editor.content),
            "gestion_status": gestion.status_code,
            "gestion_segundos": round(segundos_gestion, 3),
            "gestion_bytes_sin_comprimir": len(gestion.content),
            "gestion_filas_renderizadas": gestion.text.count('class="partida-tr"'),
        }
        print(json.dumps(resultado, ensure_ascii=False, indent=2))

        engine.dispose()
        if editor.status_code != 200 or gestion.status_code != 200:
            return 1
        if len(indice) != cantidad:
            return 1
        if segundos_editor > 2.5 or len(editor.content) > 5_000_000:
            return 1
        if segundos_gestion > 1.0 or gestion.text.count('class="partida-tr"') > 100:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
