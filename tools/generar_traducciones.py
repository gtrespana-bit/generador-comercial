#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera las tablas de traducción precalculadas del catálogo.

Para qué sirve
--------------
``traducir`` resolvía cada cadena recorriendo el glosario con expresiones
regulares y guardaba el resultado en una caché LRU de 32.768 entradas. El
catálogo tiene unas 7.000 cadenas distintas y hay 22 mercados, así que
caben más de 150.000 pares (texto, mercado): la caché se desborda y vuelve
a traducir lo que ya estaba traducido.

Este script recorre el catálogo una vez y escribe, por mercado, un
diccionario «cadena original -> cadena traducida». En runtime eso es una
lectura de diccionario. Lo que no esté en la tabla (la partida propia que
acaba de escribir un cliente) se sigue calculando con el glosario, así que
la tabla es una aceleración, no un requisito: si falta, el programa
funciona igual.

Por qué no se genera un catálogo traducido
------------------------------------------
Porque el catálogo no es solo texto: cada partida lleva precio y desglose
de costes. Duplicarlo por idioma obligaría a repetir cada actualización de
precios en cada copia, y la que se olvidara daría un precio equivocado en
ese idioma, que es bastante peor que tardar unos milisegundos más. La tabla
solo contiene texto, así que por construcción no puede corromper un precio.

Por qué hay una sola tabla para los cinco mercados ingleses
-----------------------------------------------------------
Comparten glosario: lo que los distingue no es la traducción sino el
vocabulario de obra (field layout / setting out, shoring / propping), y eso
lo aplica ``variante_ingles`` al final, en runtime. Generar cinco tablas
casi idénticas sería multiplicar por cinco el riesgo de que una se quede
vieja.

Uso
---
    python tools/generar_traducciones.py              # regenera
    python tools/generar_traducciones.py --comprobar  # verifica sin escribir
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from app.paises import PAISES, resolver_mercado          # noqa: E402
from app.services.traduccion import (                     # noqa: E402
    BASE_GLOSARIOS,
    SALIDA_TRADUCCIONES,
    _traducir_reglas,
)

# Campos que la aplicación traduce al vuelo (app/routers/partidas.py y
# app/routers/common.py). No se incluyen «unidad» ni «rendimiento»: son
# notación («m2», «1.200 h/ud»), no prosa, y traducirlos rompería las medidas.
CAMPOS = ("nombre", "descripcion", "categoria", "subcategoria", "apartado")

CATALOGO = RAIZ / "basedatos_partidas" / "salida" / "catalogo_partidas.json"
ARBOL = RAIZ / "basedatos_partidas" / "salida" / "arbol_catalogo.json"
RECURSOS = RAIZ / "basedatos_partidas" / "datos" / "recursos.json"


def _recoger_cadenas(glosario: str | None = None) -> list[str]:
    """Todas las cadenas traducibles del catálogo, sin repeticiones y ordenadas.

    Ordenadas para que el fichero sea estable: dos generaciones sobre el
    mismo catálogo producen el mismo JSON, y el diff de git sigue siendo
    legible.

    Los 388 recursos solo entran en la tabla EN. En los mercados hispanos se
    dejan fuera a propósito: sus glosarios son de término suelto y, al no
    concertar género ni número, producen «forjado nervada» o «Lámina asfáltica
    prefabricado», y en algún caso cambian el sentido («vaciado» del contenedor
    pasa a «hormigonado»). Precalcular esos fallos sería peor que dejarlos
    como están: en runtime caen en el glosario igual que hasta ahora, así que
    el comportamiento de esos mercados no cambia. El inglés no tiene ese
    problema porque los recursos van traducidos uno a uno.
    """
    vistas: set[str] = set()

    def _visitar(nodo) -> None:
        if isinstance(nodo, dict):
            for clave, valor in nodo.items():
                if clave in CAMPOS and isinstance(valor, str) and valor.strip():
                    vistas.add(valor)
                else:
                    _visitar(valor)
        elif isinstance(nodo, list):
            for elemento in nodo:
                _visitar(elemento)

    for ruta in (CATALOGO, ARBOL):
        if not ruta.is_file():
            print(f"  aviso: no está {ruta.name}, se omite", file=sys.stderr)
            continue
        _visitar(json.loads(ruta.read_text(encoding="utf-8")))

    # Los recursos (mano de obra, materiales y maquinaria) también se ven en
    # pantalla y hay que traducirlos. Sin esto sus 388 descripciones caían en
    # el glosario genérico y salían como calcos del español.
    if glosario == "EN" and RECURSOS.is_file():
        datos = json.loads(RECURSOS.read_text(encoding="utf-8"))
        for categoria in datos.values():
            if not isinstance(categoria, dict):
                continue
            for item in categoria.values():
                if not isinstance(item, dict):
                    continue
                # Los compuestos no son un recurso físico: son una receta que
                # se arma con otros. No se muestran, así que no se traducen.
                if "composicion" in item:
                    continue
                texto = item.get("descripcion")
                if isinstance(texto, str) and texto.strip():
                    vistas.add(texto)
    elif not RECURSOS.is_file():
        print(f"  aviso: no está {RECURSOS.name}, se omite", file=sys.stderr)
    return sorted(vistas)


def _glosarios_disponibles() -> list[str]:
    """Glosarios con fichero, ordenados con EN primero."""
    codigos = sorted(p.stem for p in BASE_GLOSARIOS.glob("*.json")
                     if not p.stem.endswith(".excepciones"))
    return (["EN"] if "EN" in codigos else []) + [c for c in codigos if c != "EN"]


def _huella(cadenas: list[str], glosario: str) -> str:
    """Hashes del catálogo y del glosario: si cambian, hay que regenerar."""
    h = hashlib.sha256()
    for cadena in cadenas:
        h.update(cadena.encode("utf-8"))
        h.update(b"\x00")
    glos = BASE_GLOSARIOS / f"{glosario}.json"
    if glos.is_file():
        h.update(glos.read_bytes())
    excep = BASE_GLOSARIOS / f"{glosario}.excepciones.json"
    if excep.is_file():
        h.update(excep.read_bytes())
    return h.hexdigest()[:16]


def construir(cadenas: list[str], glosario: str) -> dict:
    """Calcula la tabla de un mercado. Usa las reglas, nunca la tabla.

    Si llamara a ``traducir``, consultaría la tabla que estamos generando y
    el resultado dependería del artefacto anterior.
    """
    mercado = resolver_mercado("en" if glosario == "EN" else glosario)
    tabla: dict[str, str] = {}
    for cadena in cadenas:
        salida = _traducir_reglas(cadena, mercado, glosario)
        # Solo se guarda lo que cambia: lo demás ya es correcto tal cual y
        # duplicarlo solo haría el fichero más grande.
        if salida != cadena:
            tabla[cadena] = salida
    return tabla


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comprobar", action="store_true",
                        help="verifica sin escribir; sale con 1 si algo no cuadra")
    args = parser.parse_args()

    base = _recoger_cadenas()
    if not base:
        print("No se han encontrado cadenas; ¿falta el catálogo?", file=sys.stderr)
        return 1
    print(f"Cadenas traducibles: {len(base):,}")

    glosarios = _glosarios_disponibles()
    SALIDA_TRADUCCIONES.mkdir(parents=True, exist_ok=True)

    desincronizados: list[str] = []
    indice: dict[str, dict] = {}
    total = 0

    for glosario in glosarios:
        # Solo el inglés añade los recursos; ver _recoger_cadenas.
        cadenas = _recoger_cadenas(glosario) if glosario == "EN" else base
        tabla = construir(cadenas, glosario)
        huella = _huella(cadenas, glosario)
        ruta = SALIDA_TRADUCCIONES / f"{glosario}.json"
        documento = {
            "_glosario": glosario,
            "_generado": date.today().isoformat(),
            "_huella": huella,
            "_cadenas_origen": len(cadenas),
            "_cadenas_traducidas": len(tabla),
            "_nota": ("Derivado del catálogo y del glosario. Regenerar con "
                      "tools/generar_traducciones.py; verificar con "
                      "tools/verificar_traducciones.py."),
            "cadenas": tabla,
        }
        bytes_doc = len(json.dumps(documento, ensure_ascii=False, indent=1))
        total += bytes_doc

        if args.comprobar:
            actual = json.loads(ruta.read_text(encoding="utf-8")) if ruta.is_file() else {}
            if actual.get("_huella") != huella or actual.get("cadenas") != tabla:
                desincronizados.append(glosario)
                print(f"  ✗ {glosario:3} desincronizado")
            else:
                print(f"  ✓ {glosario:3} al día")
            continue

        ruta.write_text(json.dumps(documento, ensure_ascii=False, indent=1) + "\n",
                        encoding="utf-8")
        indice[glosario] = {"cadenas": len(tabla), "bytes": bytes_doc, "huella": huella}
        porc = 100 * len(tabla) / len(cadenas)
        print(f"  {glosario:3} {len(tabla):6,} cadenas ({porc:4.1f}%)  {bytes_doc/1024:6.0f} KB")

    if args.comprobar:
        if desincronizados:
            print(f"\n{len(desincronizados)} tablas desincronizadas: "
                  f"{', '.join(desincronizados)}", file=sys.stderr)
            print("Ejecuta: python tools/generar_traducciones.py", file=sys.stderr)
            return 1
        print("\nTodas las tablas están al día.")
        return 0

    (SALIDA_TRADUCCIONES / "_indice.json").write_text(
        json.dumps({
            "_generado": date.today().isoformat(),
            "_cadenas_origen": len(cadenas),
            "_glosarios": indice,
        }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\n{len(glosarios)} tablas en {SALIDA_TRADUCCIONES.relative_to(RAIZ)} "
          f"({total/1024/1024:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
