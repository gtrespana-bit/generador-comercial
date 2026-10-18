"""Valida que una matriz de precios sea aceptada por el importador real.

Pasa el CSV por ``app.services.importador_precios_mercado.importar_matriz_csv``
en modo seco (``aplicar=False``), que ejecuta todas las validaciones y construye
el plan de carga sin escribir en base de datos. Así se detecta antes del despliegue
cualquier fila que la aplicación rechazaría (moneda, unidad, rango, confianza…).

La sesión se simula con un objeto mínimo: solo se consulta el catálogo de
recursos, que se levanta de ``basedatos_partidas/datos/recursos.json``.

Uso:
    python3 tools/verificar_matriz_importable.py GB
    python3 tools/verificar_matriz_importable.py ES
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class _Recurso:
    """Solo los atributos que el importador consulta."""

    def __init__(self, codigo: str, unidad: str, indice: int) -> None:
        self.codigo = codigo
        self.unidad = unidad
        self.id = indice


class _Query:
    def __init__(self, recursos: list[_Recurso]) -> None:
        self._recursos = recursos

    def all(self) -> list[_Recurso]:
        return list(self._recursos)


class _Sesion:
    """Stub de SQLAlchemy Session: el importador solo usa ``db.query(Recurso)``."""

    def __init__(self, recursos: list[_Recurso]) -> None:
        self._recursos = recursos

    def query(self, _modelo):
        return _Query(self._recursos)


def _cargar_recursos() -> list[_Recurso]:
    ruta = ROOT / "basedatos_partidas/datos/recursos.json"
    with ruta.open(encoding="utf-8") as fh:
        data = json.load(fh)

    recursos: list[_Recurso] = []
    indice = 0
    for categoria in ("mano_obra", "materiales", "maquinaria"):
        items = data.get(categoria) or {}
        if not isinstance(items, dict):
            continue
        for codigo, item in items.items():
            if not isinstance(item, dict):
                continue
            # El importador omite los compuestos, igual que el generador.
            if "composicion" in item:
                continue
            indice += 1
            recursos.append(_Recurso(
                str(codigo).strip(),
                str(item.get("unidad") or "").strip(),
                indice,
            ))
    return recursos


def verificar(mercado: str) -> int:
    from app.services.importador_precios_mercado import (
        MONEDA_PAIS,
        importar_matriz_csv,
    )

    mercado = mercado.strip().upper()
    sufijo = {"ES": "espana", "GB": "reino_unido"}.get(mercado)
    if sufijo is None:
        raise SystemExit(f"Mercado no soportado: {mercado}")
    matriz = ROOT / f"basedatos_partidas/salida/precios_recursos_{sufijo}.csv"
    if not matriz.exists():
        raise SystemExit(f"No existe la matriz: {matriz}")

    print(f"Mercado {mercado} · moneda esperada {MONEDA_PAIS.get(mercado)}")
    print(f"Matriz: {matriz.relative_to(ROOT)}")

    recursos = _cargar_recursos()
    print(f"Recursos en catálogo: {len(recursos)}")

    resultado = importar_matriz_csv(_Sesion(recursos), matriz, aplicar=False)

    print(f"  filas                    {resultado['filas']}")
    print(f"  aplicables               {resultado['aplicables']}")
    print(f"  pendientes               {resultado['pendientes']}")
    print(f"  no encontrados           {resultado['no_encontrados']}")
    print(f"  errores                  {len(resultado['errores'])}")
    for error in resultado["errores"][:20]:
        print(f"    - {error}")
    if len(resultado["errores"]) > 20:
        print(f"    … y {len(resultado['errores']) - 20} más")

    if resultado["errores"]:
        print("\n✗ La matriz NO es importable tal como está.")
        return 1
    if resultado["aplicables"] != len(recursos):
        print(
            f"\n✗ Cobertura incompleta: {resultado['aplicables']} aplicables "
            f"frente a {len(recursos)} recursos del catálogo."
        )
        return 1
    print(f"\n✓ {resultado['aplicables']} filas importables, 0 errores.")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Uso: python3 tools/verificar_matriz_importable.py <MERCADO>")
        return 2
    return verificar(argv[1])


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
