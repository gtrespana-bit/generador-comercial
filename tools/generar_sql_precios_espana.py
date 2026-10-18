"""Compatibilidad: genera el SQL de carga de España.

Antiguamente este archivo contenía su propia copia del generador SQL. La lógica
vive ahora en ``tools/generar_sql_precios_pais.py``, común a todos los mercados;
este envoltorio mantiene el punto de entrada que usan los tests y la documentación
histórica.

Uso:
    python3 tools/generar_sql_precios_espana.py
"""
from __future__ import annotations

from generar_sql_precios_pais import generar


def main() -> int:
    filas, codigos, salida = generar("ES")
    print(f"SQL generado en {salida}: {filas} filas / {codigos} recursos")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
