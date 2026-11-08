#!/usr/bin/env python3
"""Cierra la auditoría de precios de España a partir de la adjudicación revisada.

Lee la tabla de adjudicación (una fila por recurso, con la decisión y su
evidencia), la valida y, con ``--aplicar``:

* actualiza el registro maestro ``espana_2026-11-06.csv`` (estado, precio
  revisado, fuente, evidencia y fecha de revisión);
* escribe las referencias aceptadas que consume el generador de la matriz;
* deja un libro de decisiones con el estado final de cada recurso.

Sin ``--aplicar`` solo comprueba y resume, sin escribir nada. El comando no
toca la base de datos, no ejecuta SQL y no despliega.

Uso:
    python tools/cerrar_auditoria_espana.py            # comprobación
    python tools/cerrar_auditoria_espana.py --aplicar  # escribe artefactos
"""
from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

DOC = Path(__file__).resolve().parents[1] / "docs/auditoria_precios"
REGISTRO = DOC / "espana_2026-11-06.csv"
MATRIZ = Path(__file__).resolve().parents[1] / "basedatos_partidas/salida/precios_recursos_espana.csv"
ADJUDICACION = DOC / "espana_adjudicacion_2026-11-07.csv"
REFERENCIAS = DOC / "espana_referencias_cierre_2026-11-07.csv"
LIBRO = DOC / "espana_cierre_decisiones_2026-11-07.csv"
FECHA = "2026-11-07"
MARCA = "Cierre 2026-11-07"
MARCA_CONFIRMA = "Contraste de cierre 2026-11-07"

APLICA = {"aplicar_mano_obra_dos_fuentes", "aplicar_media_dos_bancos",
          "aplicar_fuente_unica_coherente"}
CONFIRMA = {"confirmar_referencia"}
SIN_PRECIO = {"alerta_divergencia", "sin_equivalente_verificado", "agregado_heterogeneo",
              "requiere_modelo_propio", "mantener_sin_cambio_coherente", "cierre_barrido_previo"}
DECISIONES = APLICA | CONFIRMA | SIN_PRECIO
TOLERANCIA_CONFIRMA = Decimal("0.15")

CAMPOS_REFERENCIAS = ["codigo_recurso", "precio", "minimo", "maximo", "fuente", "criterio",
                      "reserva", "incluye_iva", "incluye_transporte"]
CAMPOS_LIBRO = ["codigo_recurso", "categoria", "unidad", "usos", "decision",
                "estado_previo", "estado_final", "precio_previo", "precio_final",
                "fuente", "codigo_fuente", "fecha_revision", "criterio", "reserva"]


def leer(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as manejador:
        return list(csv.DictReader(manejador, delimiter=";"))


def escribir(path: Path, campos: list[str], filas: list[dict]) -> None:
    """Escribe el CSV conservando el BOM que ya tuviera el archivo.

    El registro maestro se creó sin BOM: reescribirlo con BOM cambiaría la
    cabecera de todos los cortes. Los artefactos nuevos se escriben con BOM,
    que es la convención del resto de la auditoría.
    """
    con_bom = True
    if path.exists():
        with path.open("rb") as binario:
            con_bom = binario.read(3) == b"\xef\xbb\xbf"
    with path.open("w", encoding="utf-8-sig" if con_bom else "utf-8", newline="") as manejador:
        escritor = csv.DictWriter(manejador, fieldnames=campos, delimiter=";",
                                  lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(filas)


def decimal(valor, nombre: str) -> Decimal:
    try:
        numero = Decimal(str(valor).replace(",", "."))
    except (InvalidOperation, ValueError):
        raise ValueError(f"Precio no numérico en {nombre}: {valor!r}") from None
    if not numero.is_finite() or numero <= 0:
        raise ValueError(f"Precio no positivo en {nombre}: {valor!r}")
    return numero


def validar(adjudicacion: list[dict], registro: dict, matriz: dict) -> None:
    vistos = set()
    for fila in adjudicacion:
        codigo = fila["codigo_recurso"]
        if codigo in vistos:
            raise ValueError(f"Recurso duplicado en la adjudicación: {codigo}")
        vistos.add(codigo)
        if codigo not in registro or codigo not in matriz:
            raise ValueError(f"Recurso inexistente: {codigo}")
        recurso = registro[codigo]
        if fila["unidad"] != recurso["unidad"] or fila["categoria"] != recurso["categoria"]:
            raise ValueError(f"Categoría o unidad incompatible en {codigo}")
        decision = fila["decision"]
        if decision not in DECISIONES:
            raise ValueError(f"Decisión no reconocida en {codigo}: {decision}")
        if decision in APLICA:
            decimal(fila["precio_adoptado"], codigo)
            for campo in ("fuente", "codigo_fuente", "criterio"):
                if not fila[campo].strip():
                    raise ValueError(f"{codigo}: la decisión {decision} exige {campo}")
        elif decision in CONFIRMA:
            revisado = decimal(recurso["precio_revisado"], codigo)
            referencia = decimal(fila["precio_fuente"], codigo)
            if abs(referencia / revisado - 1) > TOLERANCIA_CONFIRMA:
                raise ValueError(f"{codigo}: confirmación fuera de la banda del 15 %")
            if not fila["codigo_fuente"].strip():
                raise ValueError(f"{codigo}: la confirmación exige código de fuente")
        elif fila["precio_adoptado"].strip():
            raise ValueError(f"{codigo}: la decisión {decision} no puede adoptar precio")
    faltan = {c for c, r in registro.items()
              if r["estado_auditoria"] != "confirmado_referencia"} - vistos
    if faltan:
        raise ValueError(f"Recursos sin decisión de cierre: {sorted(faltan)}")


def unir(texto: str, nuevo: str) -> str:
    """Añade una fuente sin duplicarla ni perder las observaciones anteriores."""
    texto = (texto or "").strip()
    if not nuevo.strip():
        return texto
    return texto if nuevo in texto else (f"{texto} | {nuevo}" if texto else nuevo)


# Anotaciones que se añaden *después* del cierre (confirmaciones y contrastes).
# Sin esta lista, volver a aplicar la adjudicación borraba la confirmación que
# ya se había escrito, porque el reemplazo llegaba hasta el final del texto.
POSTERIORES = ("Confirmación 2026-11-07:", "Contraste de cierre 2026-11-07:")


def limpiar_marca(texto: str, marca: str) -> str:
    """Quita la anotación de cierre previa sin borrar lo añadido después."""
    texto = texto or ""
    encontrado = re.search(rf"\s*{re.escape(marca)}:", texto, flags=re.S)
    if not encontrado:
        return texto.strip()
    fin = len(texto)
    for posterior in POSTERIORES:
        posicion = texto.find(posterior, encontrado.end())
        if posicion != -1:
            fin = min(fin, posicion)
    return (texto[:encontrado.start()] + texto[fin:]).strip()


def texto_evidencia(fila: dict) -> str:
    partes = [f"{MARCA}: {fila['criterio']}"]
    if fila["reserva"].strip():
        partes.append(f"Reserva: {fila['reserva']}")
    return " ".join(partes)


def aplicar(adjudicacion: list[dict], registro: dict, matriz: dict) -> tuple[list[dict], list[dict]]:
    referencias, libro = [], []
    for fila in adjudicacion:
        codigo = fila["codigo_recurso"]
        recurso = registro[codigo]
        decision = fila["decision"]
        previo = matriz[codigo]["precio_referencia"]
        base = limpiar_marca(recurso["evidencia_y_pendientes"], MARCA)
        final = previo
        if decision in APLICA:
            precio = decimal(fila["precio_adoptado"], codigo)
            # Adoptar un precio no puede degradar un recurso ya confirmado:
            # la adjudicación se puede reejecutar sin perder verificaciones.
            if recurso["estado_auditoria"] != "confirmado_referencia":
                recurso["estado_auditoria"] = "en_revision"
            recurso["precio_revisado"] = str(precio.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
            # Se conserva la observación previa (es evidencia) y se añade la del cierre.
            recurso["fuente_observada"] = unir(recurso["fuente_observada"], fila["fuente"])
            recurso["codigo_fuente"] = unir(recurso["codigo_fuente"], fila["codigo_fuente"])
            recurso["edicion_fuente"] = unir(recurso["edicion_fuente"], fila["edicion_fecha"])
            if "Modelo propio" in fila["fuente"]:
                ambito = "España (modelo propio, sin banco)"
            elif "Composición" in fila["fuente"]:
                ambito = "España (composición declarada)"
            elif "horquilla de mercado" in fila["fuente"]:
                ambito = "España (contraste de mercado, sin banco)"
            elif "BCCA" in fila["fuente"]:
                ambito = "Andalucía (BCCA)"
            else:
                ambito = "provincial (Palencia/Extremadura)"
            recurso["ambito_fuente"] = unir(recurso["ambito_fuente"], ambito)
            recurso["criterio_revisado"] = fila["criterio"] + " " + fila["reserva"]
            recurso["fecha_revision"] = FECHA
            final = recurso["precio_revisado"]
            referencias.append({
                "codigo_recurso": codigo, "precio": recurso["precio_revisado"],
                "minimo": recurso["precio_revisado"], "maximo": recurso["precio_revisado"],
                "fuente": fila["fuente"], "criterio": fila["criterio"],
                "reserva": fila["reserva"], "incluye_iva": "no_confirmado",
                "incluye_transporte": "no_confirmado",
            })
        elif decision in CONFIRMA:
            recurso["estado_auditoria"] = "confirmado_referencia"
            recurso["fecha_revision"] = FECHA
            recurso["criterio_revisado"] = limpiar_marca(
                recurso["criterio_revisado"], MARCA_CONFIRMA
            ) + f" {MARCA_CONFIRMA}: {fila['criterio']} {fila['reserva']}"
        else:
            if recurso["estado_auditoria"] == "pendiente":
                recurso["estado_auditoria"] = "en_revision"
            recurso["fecha_revision"] = FECHA
        recurso["evidencia_y_pendientes"] = (base + (" " if base else "") +
                                             texto_evidencia(fila)).strip()
        libro.append({
            "codigo_recurso": codigo, "categoria": recurso["categoria"],
            "unidad": recurso["unidad"], "usos": recurso["partidas_que_lo_usan"],
            "decision": decision, "estado_previo": fila["estado_previo"],
            "estado_final": recurso["estado_auditoria"], "precio_previo": previo,
            "precio_final": final, "fuente": fila["fuente"],
            "codigo_fuente": fila["codigo_fuente"], "fecha_revision": FECHA,
            "criterio": fila["criterio"], "reserva": fila["reserva"],
        })
    libro.sort(key=lambda f: (-int(f["usos"]), f["codigo_recurso"]))
    return referencias, libro


def main() -> int:
    analizador = argparse.ArgumentParser(description=__doc__)
    analizador.add_argument("--aplicar", action="store_true",
                            help="escribe registro, referencias aceptadas y libro de decisiones")
    argumentos = analizador.parse_args()

    registro_filas = leer(REGISTRO)
    campos_registro = list(registro_filas[0])
    registro = {r["codigo_recurso"]: r for r in registro_filas}
    matriz = {r["codigo_recurso"]: r for r in leer(MATRIZ) if r["pais_codigo"] == "ES"}
    adjudicacion = leer(ADJUDICACION)
    validar(adjudicacion, registro, matriz)
    referencias, libro = aplicar(adjudicacion, registro, matriz)

    resumen = Counter(f["decision"] for f in libro)
    print(f"Adjudicación válida: {len(adjudicacion)} recursos; "
          f"{len(registro) - len(adjudicacion)} ya confirmados sin cambios")
    for decision, cuantos in resumen.most_common():
        print(f"  {decision:34} {cuantos}")
    print(f"  precios nuevos aplicados: {len(referencias)}")
    if not argumentos.aplicar:
        print("Comprobación sin escritura. Use --aplicar para generar los artefactos.")
        return 0

    escribir(REGISTRO, campos_registro, [registro[r["codigo_recurso"]] for r in registro_filas])
    escribir(REFERENCIAS, CAMPOS_REFERENCIAS, referencias)
    escribir(LIBRO, CAMPOS_LIBRO, libro)
    estados = Counter(r["estado_auditoria"] for r in registro.values())
    print(f"Escrito {REGISTRO.name}: {dict(estados)}")
    print(f"Escrito {REFERENCIAS.name}: {len(referencias)} referencias aceptadas")
    print(f"Escrito {LIBRO.name}: {len(libro)} decisiones")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
