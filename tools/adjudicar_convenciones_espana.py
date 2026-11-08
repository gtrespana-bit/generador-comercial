#!/usr/bin/env python3
"""Aplica la convención de medida típica allí donde el banco tiene la ficha.

Política fijada por el titular: cuando el recurso no fija medida o clase, **no se
deja bloqueado**: se adopta la especificación media de la práctica española
(bloque exterior 20-25 cm, interior 15 cm, caja de registro 100x100, tornillo de
placa 3,5x25, etc.), se declara en el criterio y se busca la ficha del banco con
esa medida exacta. Si el banco no tiene la ficha con esa medida, el recurso queda
`pendiente_cotizacion` con la convención ya escrita, para que la siguiente ronda
sea mecánica.

Lee `espana_convenciones_medida_2026-11-07.csv` (una fila por recurso sin medida)
y reescribe en la tabla de adjudicación solo las filas `adoptado_banco`:

* ``decision = aplicar_fuente_unica_coherente`` (una sola fuente, el banco);
* ``precio_adoptado`` = precio de la ficha del banco;
* ``criterio`` con la convención adoptada y por qué es la media;
* ``reserva`` recordando que la medida es una convención, no un dato del recurso.

No toca la base de datos, no ejecuta SQL y no despliega.

Uso:
    python tools/adjudicar_convenciones_espana.py            # simulación
    python tools/adjudicar_convenciones_espana.py --aplicar  # reescribe la tabla
"""
from __future__ import annotations

import argparse
import csv
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DOC = RAIZ / "docs/auditoria_precios"
FECHA = "2026-11-07"
CONVENCIONES = DOC / f"espana_convenciones_medida_{FECHA}.csv"
ADJUDICACION = DOC / f"espana_adjudicacion_{FECHA}.csv"
DECISION = "aplicar_fuente_unica_coherente"
CODIGO_FUENTE = f"CONV-{FECHA}"
FUENTE = ("Base de Precios de Construcción de Extremadura 2026 "
          f"(BCEXTGREM_26_v1.bc3) con convención de medida propia {FECHA}")
ESTADO = "adoptado_banco"
RESERVA = ("La medida o clase es una convención de práctica, no un dato del recurso: "
           "si el proyecto fija otra medida, el precio hay que recalcularlo con esa ficha.")


def leer(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as manejador:
        return list(csv.DictReader(manejador, delimiter=";"))


def escribir(path: Path, campos: list[str], filas: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as manejador:
        escritor = csv.DictWriter(manejador, fieldnames=campos, delimiter=";",
                                  lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(filas)


def numero(valor) -> Decimal | None:
    texto = str(valor or "").strip().replace(",", ".")
    if not texto:
        return None
    try:
        numero_decimal = Decimal(texto)
    except InvalidOperation:
        return None
    return numero_decimal if numero_decimal > 0 else None


def criterio(convencion: dict) -> str:
    return (f"Convención de medida {FECHA}: el recurso no fija medida o clase y se adopta "
            f"«{convencion['especificacion_convencional']}» porque "
            f"{convencion['criterio_convencion'].rstrip('.')}. "
            f"Ficha del banco {convencion['codigo_fuente']} "
            f"({convencion['descripcion_fuente']}) a {convencion['precio_fuente']} EUR.")


def construir(convenciones: list[dict], adjudicacion: list[dict]) -> tuple[list[dict], list[str]]:
    por_codigo = {fila["codigo_recurso"]: fila for fila in convenciones}
    avisos: list[str] = []
    salida = []
    for fila in adjudicacion:
        convencion = por_codigo.get(fila["codigo_recurso"])
        if convencion is None or convencion["estado"] != ESTADO:
            salida.append(fila)
            continue
        precio = numero(convencion["precio_fuente"]).quantize(Decimal("0.01"),
                                                              rounding=ROUND_HALF_UP)
        actual = numero(fila["precio_matriz"]) or Decimal("0")
        desviacion = ((precio / actual - 1) * 100).quantize(Decimal("0.1")) if actual else None
        if desviacion is None or abs(desviacion) > 50:
            avisos.append(f"{fila['codigo_recurso']}: {fila['precio_matriz']} → {precio} "
                          f"({desviacion} %) con la convención "
                          f"«{convencion['especificacion_convencional'][:48]}…»")
        salida.append({**fila,
                       "decision": DECISION,
                       "precio_adoptado": f"{precio:.2f}",
                       "precio_fuente": f"{precio:.2f}",
                       "fuente": FUENTE,
                       "codigo_fuente": convencion["codigo_fuente"],
                       "edicion_fecha": FECHA,
                       "desviacion_pct": "" if desviacion is None else f"{desviacion}",
                       "criterio": criterio(convencion),
                       "reserva": RESERVA})
    return salida, avisos


def main() -> int:
    analizador = argparse.ArgumentParser(description=__doc__,
                                         formatter_class=argparse.RawDescriptionHelpFormatter)
    analizador.add_argument("--convenciones", type=Path, default=CONVENCIONES)
    analizador.add_argument("--adjudicacion", type=Path, default=ADJUDICACION)
    analizador.add_argument("--aplicar", action="store_true")
    argumentos = analizador.parse_args()

    convenciones = leer(argumentos.convenciones)
    adjudicacion = leer(argumentos.adjudicacion)
    salida, avisos = construir(convenciones, adjudicacion)

    adoptadas = [f for f in salida if f["fuente"] == FUENTE]
    print(f"{len(adoptadas)} recursos con convención adoptada de {len(convenciones)}:")
    for fila in adoptadas:
        print(f"  {fila['codigo_recurso']:22} {fila['usos']:>4} usos  "
              f"{fila['precio_matriz']:>9} → {fila['precio_adoptado']:>8} "
              f"({fila['desviacion_pct']} %)")
    for aviso in avisos:
        print(f"  AVISO {aviso}")
    if not argumentos.aplicar:
        print("Simulación: no se ha escrito nada. Usa --aplicar para reescribir la tabla.")
        return 0
    escribir(argumentos.adjudicacion, list(adjudicacion[0].keys()), salida)
    print(f"Escrito {argumentos.adjudicacion.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
