#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Terminología de obra: cambiar una palabra en todo el catálogo de una vez.

El presupuesto lo lee el cliente. Si la palabra no es la suya, el documento
pierde credibilidad por mucho que el número esté bien. Y las palabras cambian:
lo que aquí es «afirmado» en otro sitio es «contrapiso» o «recrecido».

Por eso el vocabulario no se corrige a mano archivo por archivo, sino desde
`datos/glosario.json`, y se aplica a los tres sitios donde vive el texto:
el cuadro de recursos, la clasificación y las 540 partidas.

    python3 basedatos_partidas/terminologia.py auditar   # busca términos peninsulares
    python3 basedatos_partidas/terminologia.py listar    # qué cambiaría el glosario
    python3 basedatos_partidas/terminologia.py aplicar   # lo escribe y regenera

La sustitución respeta la mayúscula inicial y los plurales simples, así que
«Contrapiso», «contrapisos» y «contrapiso» quedan bien los tres.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
RAIZ = BASE.parent
DATOS = BASE / "datos"
GLOSARIO = DATOS / "glosario.json"
RECURSOS = DATOS / "recursos.json"
CLASIFICACION = DATOS / "clasificacion.json"
DESCOMPUESTOS = DATOS / "descompuestos"


def cargar_glosario() -> dict:
    if not GLOSARIO.exists():
        sys.exit(f"No existe {GLOSARIO}")
    return json.loads(GLOSARIO.read_text(encoding="utf-8"))


def archivos() -> list[Path]:
    return [RECURSOS, CLASIFICACION, *sorted(DESCOMPUESTOS.glob("*.json"))]


# --------------------------------------------------------------------------- #
# Sustitución respetuosa con mayúsculas y plurales
# --------------------------------------------------------------------------- #

def _mismo_caso(origen: str, destino: str) -> str:
    if origen[:1].isupper():
        return destino[:1].upper() + destino[1:]
    return destino


def sustituir(texto: str, de: str, a: str) -> tuple[str, int]:
    """Cambia «de» por «a» conservando mayúscula inicial y plural en -s/-es."""
    patron = re.compile(rf"\b({re.escape(de)})(es|s)?\b", re.IGNORECASE)
    cuenta = 0

    def _rep(m: re.Match) -> str:
        nonlocal cuenta
        cuenta += 1
        plural = m.group(2) or ""
        nuevo = _mismo_caso(m.group(1), a)
        if not plural:
            return nuevo
        # El plural se recalcula sobre la palabra nueva, no se copia el sufijo:
        # «contrapisos» -> «afirmados», no «afirmados» + «es».
        return nuevo + ("es" if nuevo[-1:] not in "aeiou" else "s")

    return patron.sub(_rep, texto), cuenta


def recorrer(valor, transformar):
    """Aplica `transformar` a todas las cadenas de una estructura JSON."""
    if isinstance(valor, str):
        return transformar(valor)
    if isinstance(valor, list):
        return [recorrer(v, transformar) for v in valor]
    if isinstance(valor, dict):
        return {k: recorrer(v, transformar) for k, v in valor.items()}
    return valor


# Campos que acaban impresos en el presupuesto del cliente. El resto
# (`fuente`, `nota`, `_comentario`) son apuntes internos de procedencia que
# citan nombres comerciales tal cual los publica el vendedor: ahí no manda
# nuestro glosario, y auditarlos solo produce falsos positivos.
CAMPOS_CLIENTE = {"titulo", "descripcion", "nombre", "unidad"}


def textos_de_cliente():
    """Genera (archivo, campo, texto) de todo lo que lee el cliente."""
    # Cuadro de recursos: solo la descripción de cada recurso.
    recursos = json.loads(RECURSOS.read_text(encoding="utf-8"))
    for grupo in ("materiales", "maquinaria", "mano_obra"):
        for codigo, ficha in (recursos.get(grupo) or {}).items():
            if ficha.get("descripcion"):
                yield ("recursos.json", codigo, ficha["descripcion"])

    # Clasificación: nombres de capítulo, subcapítulo y apartado.
    clasif = json.loads(CLASIFICACION.read_text(encoding="utf-8"))
    for cod, cap in (clasif.get("capitulos") or {}).items():
        yield ("clasificacion.json", f"cap {cod}", cap.get("nombre", ""))
        for sub, nodo_sub in (cap.get("subcapitulos") or {}).items():
            yield (
                "clasificacion.json",
                f"sub {cod}.{sub}",
                nodo_sub.get("nombre", ""),
            )
            for apartado, nombre in (nodo_sub.get("apartados") or {}).items():
                yield (
                    "clasificacion.json",
                    f"apartado {cod}.{sub}.{apartado}",
                    nombre,
                )

    # Partidas: título y descripción larga.
    for ruta in sorted(DESCOMPUESTOS.glob("*.json")):
        partida = json.loads(ruta.read_text(encoding="utf-8"))
        for campo in ("titulo", "descripcion"):
            if partida.get(campo):
                yield (ruta.stem, campo, partida[campo])


# --------------------------------------------------------------------------- #
# Órdenes
# --------------------------------------------------------------------------- #

def orden_auditar() -> int:
    glosario = cargar_glosario()
    prohibidos = {k: v for k, v in glosario.get("_prohibidos", {}).items()
                  if not k.startswith("_")}
    matizados = {k: v for k, v in glosario.get("_matizados", {}).items()
                 if not k.startswith("_")}
    hallazgos: dict[str, list[tuple[str, str]]] = {}
    avisos: dict[str, int] = {}

    for ruta, campo, texto in textos_de_cliente():
        for malo, bueno in prohibidos.items():
            for m in re.finditer(rf"\b{re.escape(malo)}\w*\b", texto, re.IGNORECASE):
                contexto = texto[max(0, m.start() - 45):m.end() + 45].replace("\n", " ")
                hallazgos.setdefault(f"{malo} -> {bueno}", []).append(
                    (f"{ruta}·{campo}", contexto.strip())
                )
        for palabra in matizados:
            n = len(re.findall(rf"\b{re.escape(palabra)}\w*\b", texto, re.IGNORECASE))
            if n:
                avisos[palabra] = avisos.get(palabra, 0) + n

    if hallazgos:
        print("Términos peninsulares en texto que lee el cliente:\n")
        for clave, casos in sorted(hallazgos.items()):
            print(f"  {clave}   ({len(casos)} apariciones)")
            for nombre, contexto in casos[:4]:
                print(f"      {nombre}: …{contexto}…")
            if len(casos) > 4:
                print(f"      … y {len(casos) - 4} más")
            print()
    else:
        print("Auditoría de terminología sobre el texto que lee el cliente.")
        print("Sin términos peninsulares. El vocabulario es venezolano de principio a fin.\n")

    if avisos:
        print("Palabras que dependen del contexto (no son error, pero conviene mirarlas"
              " al añadir partidas nuevas):")
        for palabra, n in sorted(avisos.items()):
            print(f"  «{palabra}» ×{n} — {matizados[palabra]}")
        print()

    return 1 if hallazgos else 0


def _aplica_a(ruta: Path, cambio: dict) -> bool:
    """¿Este cambio afecta a este archivo?

    `solo_en` acota la sustitución a una lista de archivos. Sirve para las
    palabras que son correctas en un contexto e incorrectas en otro: en
    Venezuela «pavimento» está bien en exteriores (pavimento de adoquín) y
    mal en interiores, donde es «piso».
    """
    solo = cambio.get("solo_en")
    if not solo:
        return True
    return ruta.stem in solo or ruta.name in solo


def _plan(glosario: dict) -> list[dict]:
    plan = []
    for cambio in glosario.get("cambios", []):
        de, a = cambio["de"], cambio["a"]
        total, tocados = 0, []
        for ruta in archivos():
            if not _aplica_a(ruta, cambio):
                continue
            texto = ruta.read_text(encoding="utf-8")
            _, n = sustituir(texto, de, a)
            if n:
                total += n
                tocados.append((ruta.name, n))
        plan.append({**cambio, "total": total, "archivos": tocados})
    return plan


def orden_listar() -> int:
    plan = _plan(cargar_glosario())
    if not plan:
        print("El glosario no tiene cambios declarados.")
        return 0
    for cambio in plan:
        print(f"«{cambio['de']}» -> «{cambio['a']}»   {cambio['total']} apariciones "
              f"en {len(cambio['archivos'])} archivos")
        if cambio.get("motivo"):
            print(f"   motivo: {cambio['motivo']}")
        for codigo_viejo, codigo_nuevo in (cambio.get("codigos") or {}).items():
            print(f"   además renombra el recurso {codigo_viejo} -> {codigo_nuevo}")
        for nombre, n in cambio["archivos"][:6]:
            print(f"      {nombre} ({n})")
        if len(cambio["archivos"]) > 6:
            print(f"      … y {len(cambio['archivos']) - 6} archivos más")
        print()
    print("Para escribirlo:  python3 basedatos_partidas/terminologia.py aplicar")
    return 0


def orden_aplicar(regenerar: bool = True) -> int:
    glosario = cargar_glosario()
    cambios = glosario.get("cambios", [])
    if not cambios:
        print("El glosario no tiene cambios declarados.")
        return 0

    sello = f"{datetime.now():%Y%m%d-%H%M%S}"
    copia = DATOS / f"_copia-terminologia-{sello}"
    copia.mkdir(parents=True, exist_ok=True)
    for ruta in (RECURSOS, CLASIFICACION):
        shutil.copy2(ruta, copia / ruta.name)
    shutil.copytree(DESCOMPUESTOS, copia / "descompuestos")

    total_global = 0
    for cambio in cambios:
        de, a = cambio["de"], cambio["a"]
        renombres = cambio.get("codigos") or {}
        n_cambio = 0

        for ruta in archivos():
            if not _aplica_a(ruta, cambio):
                continue
            texto = ruta.read_text(encoding="utf-8")
            nuevo, n = sustituir(texto, de, a)
            # El renombrado de códigos es literal salvo por una cosa: un código
            # puede ser prefijo de otro. `MO-OF1-SOL` (solador) vive dentro de
            # `MO-OF1-SOLD` (soldador), y un replace a secas convertía el
            # soldador en «MO-OF1-PISOD». Se exige que el código no siga con
            # más caracteres de código ni por delante ni por detrás.
            for viejo, moderno in renombres.items():
                nuevo = re.sub(
                    rf"(?<![A-Za-z0-9-]){re.escape(viejo)}(?![A-Za-z0-9-])",
                    moderno,
                    nuevo,
                )
            if nuevo != texto:
                ruta.write_text(nuevo, encoding="utf-8")
                n_cambio += n
        total_global += n_cambio
        print(f"«{de}» -> «{a}»: {n_cambio} apariciones")
        for viejo, moderno in renombres.items():
            print(f"   recurso renombrado: {viejo} -> {moderno}")

    print(f"\nCopia de seguridad -> {copia.relative_to(RAIZ)}")
    print(f"{total_global} sustituciones en total.")

    if not regenerar:
        return 0
    print("\nRegenerando las 540 partidas…")
    for script in ("descompuestos.py", "construir.py"):
        res = subprocess.run([sys.executable, str(BASE / script)], cwd=RAIZ,
                             capture_output=True, text=True)
        if res.returncode != 0:
            print(res.stdout[-3000:]); print(res.stderr[-3000:])
            return res.returncode
    print("Listo.")
    return 0


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "listar"
    if modo == "auditar":
        raise SystemExit(orden_auditar())
    if modo == "listar":
        raise SystemExit(orden_listar())
    if modo == "aplicar":
        raise SystemExit(orden_aplicar("--sin-regenerar" not in sys.argv))
    sys.exit("Uso: terminologia.py [auditar|listar|aplicar]")
