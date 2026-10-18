"""Parser e importador FIEBDC-3 / BC3 para CotizaT.

Soporta lectura de .bc3 reales (BCCA Andalucía, Extremadura, etc.) y los
convierte al formato interno que ya usa el importador tabular:

- Detecta encoding (utf-8-sig, utf-8, windows-1252, iso-8859-1)
- Parsea registros ~V, ~K, ~C, ~D, ~T, ~M, ~L
- Construye árbol capítulo -> partida a partir de ~D
- Extrae mediciones ~M y descripciones largas ~T
- Devuelve estructura compatible con _capitulos_importados_para_editor

Referencia: Formato FIEBDC-3/2020 y /2024 de fiebdc.es
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any

MAX_BYTES = 8 * 1024 * 1024
MAX_CONCEPTOS = 10000  # protección contra .bc3 gigantes (bases completas)
MAX_FILAS = 5000

class ErrorBC3(ValueError):
    """Error comprensible para el asistente de importación BC3."""


def normalizar(texto: str) -> str:
    t = unicodedata.normalize("NFD", str(texto or "").strip().lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "", t)


def texto_celda(valor: Any) -> str:
    if valor is None:
        return ""
    return str(valor).strip()


def numero_local(valor: Any) -> float | None:
    if valor is None or str(valor).strip() == "":
        return None
    txt = str(valor).strip().replace(" ", "").replace(",", ".")
    # BC3 usa punto como decimal según spec, pero toleramos coma
    if txt.count(".") > 1:
        # caso 1.234.56 no válido, último punto decimal
        parts = txt.split(".")
        txt = "".join(parts[:-1]) + "." + parts[-1]
    try:
        n = float(txt)
    except (TypeError, ValueError):
        return None
    return n if n == n and abs(n) != float("inf") else None


def _detectar_encoding_y_texto(contenido: bytes) -> str:
    if len(contenido) > MAX_BYTES:
        raise ErrorBC3("El archivo BC3 supera el límite de 8 MB.")
    # BOM
    if contenido.startswith(b"\xef\xbb\xbf"):
        try:
            return contenido.decode("utf-8-sig")
        except UnicodeDecodeError:
            pass
    for enc in ("utf-8", "windows-1252", "iso-8859-1", "latin-1", "cp850"):
        try:
            return contenido.decode(enc)
        except UnicodeDecodeError:
            continue
    raise ErrorBC3("No se pudo leer el BC3. Guárdalo como ANSI o UTF-8.")


def _split_registros(texto: str) -> list[tuple[str, str]]:
    """
    Devuelve lista de (tipo, contenido_crudo) donde contenido_crudo es todo
    después de ~X|...
    El archivo es secuencia de registros ~L. Se ignora lo anterior al primer ~.
    """
    # Normalizar fin de línea
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
    # Cortar por ~ pero conservar tipo
    # El spec permite texto entre registros que debe ignorarse.
    partes = texto.split("~")
    registros = []
    for parte in partes:
        parte = parte.strip()
        if not parte:
            continue
        # Primera letra es tipo de registro
        tipo = parte[0].upper()
        if not tipo.isalpha():
            continue
        contenido = parte[1:]  # incluye el | inicial normalmente
        # Quitar salto inicial si lo hay
        if contenido.startswith("|"):
            contenido = contenido[1:]
        # El contenido puede tener \n internos pero no ~ (ya split)
        registros.append((tipo, contenido))
    return registros


def _split_campos(contenido: str) -> list[str]:
    """
    Campos separados por |. Respeta que | puede estar dentro de texto?
    Según spec no, texto no contiene | sin escapar. Simplificamos.
    Se eliminan blancos antes de separador.
    """
    # Ignorar espacios antes de |
    # No usamos csv porque | es separador fijo
    campos = []
    # Split conservando vacíos
    raw = contenido.split("|")
    for c in raw:
        # Trim solo espacios/tabs alrededor, no contenido interno
        campos.append(c.strip())
    # Eliminar últimos vacíos por spec (no necesarios)
    while campos and campos[-1] == "":
        campos.pop()
    return campos


def _split_subcampos(campo: str) -> list[str]:
    """Subcampos separados por \\"""
    if not campo:
        return []
    return [s.strip() for s in campo.split("\\")]


def _codigo_limpio(codigo: str) -> str:
    """Quita # y ## y espacios, devuelve código primario"""
    c = str(codigo or "").strip()
    # El código puede tener sinónimos separados por \ -> tomamos primero
    if "\\" in c:
        c = c.split("\\")[0]
    c = c.strip()
    # Quitar sufijos ## y #
    c = c.rstrip("#")
    return c.strip()


def _es_capitulo_codigo(codigo_raw: str) -> bool:
    """En BC3 los capítulos llevan # o ## en su registro ~C"""
    c = str(codigo_raw or "").strip()
    return c.endswith("#") or c.endswith("##")


@dataclass
class ConceptoBC3:
    codigo_raw: str
    codigo: str  # limpio sin #
    codigos_sinonimos: list[str] = field(default_factory=list)
    unidad: str = ""
    resumen: str = ""
    precio: float = 0.0
    precios: list[float] = field(default_factory=list)
    fecha: str = ""
    tipo: int = 0  # 0 sin clasificar, 1 mano obra, 2 maquinaria, 3 material, etc.
    es_raiz: bool = False
    es_capitulo: bool = False
    texto_largo: str = ""
    # descomposición
    hijos: list[dict] = field(default_factory=list)  # cada hijo {codigo, factor, rendimiento, porcentaje}


@dataclass
class MedicionBC3:
    codigo_padre: str | None
    codigo_hijo: str
    posicion: str = ""
    total: float | None = None
    lineas: list[dict] = field(default_factory=list)  # {tipo, comentario, uds, long, lat, alt, etiqueta}


def parse_bc3(contenido: bytes) -> dict:
    """
    Parsea un .bc3 y devuelve estructura intermedia.
    Lanza ErrorBC3 si no es válido.
    """
    texto = _detectar_encoding_y_texto(contenido)
    if "~C|" not in texto and "~D|" not in texto and "~V|" not in texto:
        raise ErrorBC3("No parece un archivo BC3 válido (faltan registros ~V/~C/~D).")

    registros = _split_registros(texto)

    conceptos: dict[str, ConceptoBC3] = {}
    conceptos_raw_map: dict[str, str] = {}  # raw -> limpio
    textos: dict[str, str] = {}
    descomposiciones_raw: dict[str, list[dict]] = {}
    mediciones: list[MedicionBC3] = []
    version_info: dict = {}
    coeficientes: dict = {}

    for tipo, cont in registros:
        campos = _split_campos(cont)
        if tipo == "V":
            # ~V | PROPIEDAD | VERSION\FECHA | PROGRAMA | CABECERA\{ROTULOS} | JUEGO | COMENTARIO | TIPO | NUM_CERT | FECHA_CERT | URL_BASE
            try:
                version_info = {
                    "propiedad": campos[0] if len(campos) > 0 else "",
                    "version": _split_subcampos(campos[1])[0] if len(campos) > 1 else "",
                    "programa": campos[2] if len(campos) > 2 else "",
                    "comentario": campos[5] if len(campos) > 5 else "",
                    "tipo_info": campos[6] if len(campos) > 6 else "",
                }
            except Exception:
                version_info = {}
        elif tipo == "K":
            # Coeficientes, lo guardamos bruto
            coeficientes["raw"] = cont
        elif tipo == "C":
            if len(campos) < 1:
                continue
            # Campos: 0=codigos, 1=unidad, 2=resumen, 3=precio(s), 4=fecha, 5=tipo
            codigo_raw_field = campos[0] if len(campos) > 0 else ""
            codigos = _split_subcampos(codigo_raw_field)
            if not codigos:
                continue
            codigo_raw = codigos[0]
            codigo_limpio = _codigo_limpio(codigo_raw)
            if not codigo_limpio:
                continue
            if len(conceptos) >= MAX_CONCEPTOS:
                raise ErrorBC3(f"El BC3 supera el límite de {MAX_CONCEPTOS} conceptos. Usa un presupuesto, no la base completa.")

            unidad = campos[1] if len(campos) > 1 else ""
            resumen = campos[2] if len(campos) > 2 else ""
            precio_field = campos[3] if len(campos) > 3 else "0"
            precios_sub = _split_subcampos(precio_field)
            precios = []
            for p in precios_sub:
                v = numero_local(p)
                if v is not None:
                    precios.append(v)
            precio = precios[0] if precios else 0.0

            fecha = campos[4] if len(campos) > 4 else ""
            tipo_field = campos[5] if len(campos) > 5 else "0"
            tipo_sub = _split_subcampos(tipo_field)
            try:
                tipo_val = int(float(tipo_sub[0])) if tipo_sub and tipo_sub[0] else 0
            except Exception:
                tipo_val = 0

            es_cap = _es_capitulo_codigo(codigo_raw)
            es_raiz = codigo_raw.endswith("##")

            # Guardar
            concepto = ConceptoBC3(
                codigo_raw=codigo_raw,
                codigo=codigo_limpio,
                codigos_sinonimos=[_codigo_limpio(c) for c in codigos[1:] if _codigo_limpio(c)],
                unidad=unidad,
                resumen=resumen,
                precio=precio,
                precios=precios,
                fecha=fecha,
                tipo=tipo_val,
                es_raiz=es_raiz,
                es_capitulo=es_cap,
            )
            conceptos[codigo_limpio] = concepto
            conceptos_raw_map[codigo_raw] = codigo_limpio
            # También mapear sinónimos y variantes con #
            conceptos_raw_map[codigo_limpio] = codigo_limpio
            # Mapear código con # para búsqueda rápida
            if es_cap or es_raiz:
                conceptos_raw_map[codigo_raw] = codigo_limpio

        elif tipo == "T":
            # ~T|CODIGO|TEXTO|
            if len(campos) < 2:
                continue
            codigo_raw = campos[0]
            codigo_limpio = _codigo_limpio(codigo_raw)
            # El texto puede contener |, así que si hay más de 2 campos, unir resto con |
            texto_largo = campos[1] if len(campos) > 1 else ""
            if len(campos) > 2:
                # Reconstruir porque split por | rompió texto que tenía |
                # Pero spec dice texto no debería tener |, por si acaso
                texto_largo = "|".join(campos[1:])
            if codigo_limpio:
                textos[codigo_limpio] = texto_largo
                if codigo_limpio in conceptos:
                    conceptos[codigo_limpio].texto_largo = texto_largo

        elif tipo == "D":
            # ~D|CODIGO_PADRE|<HIJO\FACTOR\RENDIMIENTO>|
            if len(campos) < 2:
                continue
            padre_raw = campos[0]
            padre_limpio = _codigo_limpio(padre_raw)
            if not padre_limpio:
                continue
            hijos = []
            for hijo_field in campos[1:]:
                if not hijo_field.strip():
                    continue
                sub = _split_subcampos(hijo_field)
                if not sub:
                    continue
                # Repeticiones HIJO/FACTOR/RENDIMIENTO dentro del mismo campo.
                for offset in range(0, len(sub), 3):
                    grupo = sub[offset:offset + 3]
                    hijo_codigo_raw = grupo[0].strip()
                    if not hijo_codigo_raw:
                        continue
                    # Detectar porcentaje: código contiene % o &
                    es_porcentaje = "%" in hijo_codigo_raw or "&" in hijo_codigo_raw
                    hijo_codigo_limpio = _codigo_limpio(hijo_codigo_raw) if not es_porcentaje else hijo_codigo_raw
                    factor = 1.0
                    rendimiento = 1.0
                    if len(grupo) > 1:
                        f = numero_local(grupo[1])
                        if f is not None:
                            factor = f
                    if len(grupo) > 2:
                        r = numero_local(grupo[2])
                        if r is not None:
                            rendimiento = r
                    # Caso especial: porcentaje como OP%N0001 \ \ 0.03 \ -> factor vacío, rendimiento es %
                    if es_porcentaje and len(grupo) > 1:
                        # El rendimiento puede estar en grupo[1] si factor vacío
                        # Intentar buscar último numérico
                        for s in reversed(grupo[1:]):
                            v = numero_local(s)
                            if v is not None:
                                rendimiento = v
                                break

                    hijos.append({
                        "codigo_raw": hijo_codigo_raw,
                        "codigo": hijo_codigo_limpio,
                        "factor": factor,
                        "rendimiento": rendimiento,
                        "es_porcentaje": es_porcentaje,
                    })
            if hijos:
                descomposiciones_raw.setdefault(padre_limpio, []).extend(hijos)
                # También guardar en concepto si existe
                if padre_limpio in conceptos:
                    conceptos[padre_limpio].hijos.extend(hijos)

        elif tipo == "M":
            # ~M|[PADRE\]HIJO|POS|TOTAL|{TIPO\COMENT\UDS\LONG\LAT\ALT}|
            if len(campos) < 2:
                continue
            codigo_combo = campos[0]
            # Puede ser PADRE\HIJO o solo HIJO
            if "\\" in codigo_combo:
                parts = codigo_combo.split("\\")
                # último es hijo, resto padre (normalmente 1)
                hijo_raw = parts[-1]
                padre_raw = "\\".join(parts[:-1]) if len(parts) > 1 else ""
                padre_limpio = _codigo_limpio(padre_raw) if padre_raw else None
                hijo_limpio = _codigo_limpio(hijo_raw)
            else:
                padre_limpio = None
                hijo_limpio = _codigo_limpio(codigo_combo)

            posicion = campos[1] if len(campos) > 1 else ""
            total_raw = campos[2] if len(campos) > 2 else ""
            total = numero_local(total_raw)

            lineas = []
            for linea_field in campos[3:]:
                if not linea_field.strip():
                    continue
                sub = _split_subcampos(linea_field)
                if not sub:
                    continue
                # Seis subcampos por medición, repetidos sin separadores |.
                for offset in range(0, len(sub), 6):
                    grupo = sub[offset:offset + 6]
                    if not any(grupo):
                        continue
                    # Formato: TIPO\COMENTARIO\UDS\LONG\LAT\ALT
                    tipo_m = grupo[0] if len(grupo) > 0 else ""
                    comentario = grupo[1] if len(grupo) > 1 else ""
                    uds = numero_local(grupo[2]) if len(grupo) > 2 else None
                    longi = numero_local(grupo[3]) if len(grupo) > 3 else None
                    lat = numero_local(grupo[4]) if len(grupo) > 4 else None
                    alt = numero_local(grupo[5]) if len(grupo) > 5 else None
                    etiqueta = ""
                    lineas.append({
                        "tipo": tipo_m,
                        "comentario": comentario,
                        "uds": uds,
                        "long": longi,
                        "lat": lat,
                        "alt": alt,
                        "etiqueta": etiqueta,
                    })

            mediciones.append(MedicionBC3(
                codigo_padre=padre_limpio,
                codigo_hijo=hijo_limpio,
                posicion=posicion,
                total=total,
                lineas=lineas,
            ))

    # Post-proceso: asignar textos largos que llegaron después
    for cod, txt in textos.items():
        if cod in conceptos and not conceptos[cod].texto_largo:
            conceptos[cod].texto_largo = txt

    # Enlazar descomposiciones que no estaban en conceptos (por si concepto no existía)
    for padre, hijos in descomposiciones_raw.items():
        if padre not in conceptos:
            # Crear concepto placeholder capítulo si es necesario
            conceptos[padre] = ConceptoBC3(
                codigo_raw=padre,
                codigo=padre,
                resumen=padre,
                es_capitulo=True,
            )
            conceptos[padre].hijos = hijos

    return {
        "conceptos": conceptos,
        "textos": textos,
        "descomposiciones": descomposiciones_raw,
        "mediciones": mediciones,
        "version": version_info,
        "coeficientes": coeficientes,
        "total_conceptos": len(conceptos),
    }


def _construir_arbol_capitulos(parsed: dict) -> dict:
    """
    Construye jerarquía capítulo -> partidas usando ~D.
    Devuelve {capitulos: [{codigo, nombre, partidas: [codigos]}]}
    """
    conceptos: dict[str, ConceptoBC3] = parsed["conceptos"]
    descomposiciones: dict[str, list[dict]] = parsed["descomposiciones"]

    # Encontrar raíces: conceptos ## o conceptos que nunca aparecen como hijo
    todos_hijos = set()
    for hijos in descomposiciones.values():
        for h in hijos:
            if not h.get("es_porcentaje"):
                todos_hijos.add(h["codigo"])

    raices = [c for c in conceptos.values() if c.es_raiz]
    if not raices:
        # Si no hay raíz explícita, los que no son hijos y son capítulos son raíces
        raices = [c for c in conceptos.values() if c.codigo not in todos_hijos and c.es_capitulo]
    if not raices:
        # Fallback: cualquier concepto que no es hijo
        raices = [c for c in conceptos.values() if c.codigo not in todos_hijos]

    # Si aún vacío, tomar primer concepto
    if not raices and conceptos:
        raices = [next(iter(conceptos.values()))]

    # BFS para asignar capítulos
    # Un capítulo en CotizaT es un concepto que en BC3 es capítulo y contiene partidas o subcapítulos
    visitados = set()
    capitulos_map: dict[str, dict] = {}  # codigo -> {nombre, partidas: [], subcapitulos: []}
    partidas_por_capitulo: dict[str, list[str]] = {}

    def es_partida_final(codigo: str) -> bool:
        c = conceptos.get(codigo)
        if not c:
            return True
        # Si no tiene descomposición o su descomposición solo tiene materiales/mano obra (tipo 1,2,3) -> es partida final
        hijos = descomposiciones.get(codigo, [])
        if not hijos:
            return True
        # Si todos los hijos son materiales (no tienen a su vez descomposición de obra) -> es partida
        # Heurística: si hijos son tipo material (1,2,3) o porcentaje, es partida
        for h in hijos:
            if h.get("es_porcentaje"):
                continue
            hijo_concept = conceptos.get(h["codigo"])
            if hijo_concept and hijo_concept.es_capitulo:
                return False
            # Si hijo tiene a su vez descomposición que no es solo recursos, entonces padre es capítulo
            if h["codigo"] in descomposiciones and len(descomposiciones[h["codigo"]]) > 0:
                # Ver si esos nietos son capítulos
                for nieto in descomposiciones[h["codigo"]]:
                    if conceptos.get(nieto["codigo"], ConceptoBC3("", "")).es_capitulo:
                        return False
        return True

    # Recorrer desde raíces
    cola = [(r.codigo, None, 0) for r in raices]  # (codigo, capitulo_padre, nivel)
    # capitulo_actual es el último capítulo encontrado en la rama
    while cola:
        codigo, capitulo_actual, nivel = cola.pop(0)
        if codigo in visitados and nivel > 5:
            continue
        visitados.add(codigo)
        concepto = conceptos.get(codigo)
        if not concepto:
            continue

        hijos = descomposiciones.get(codigo, [])

        if concepto.es_capitulo or (concepto.es_raiz and nivel == 0):
            # Registrar capítulo si no es raíz
            if not concepto.es_raiz:
                if codigo not in capitulos_map:
                    capitulos_map[codigo] = {
                        "codigo": codigo,
                        "codigo_raw": concepto.codigo_raw,
                        "nombre": (concepto.resumen or concepto.codigo).strip().upper()[:200],
                        "descripcion": concepto.texto_largo[:1000],
                        "partidas": [],
                    }
                # Si tiene padre capítulo, podríamos anidar, pero CotizaT usa capítulos planos
                # Mantenemos referencia
            # Sus hijos pueden ser subcapítulos o partidas
            for h in reversed(hijos):  # reversed para mantener orden con pop(0)
                if h.get("es_porcentaje"):
                    continue
                hijo_cod = h["codigo"]
                if hijo_cod not in conceptos:
                    continue
                hijo_conc = conceptos[hijo_cod]
                if hijo_conc.es_capitulo:
                    cola.append((hijo_cod, codigo if not concepto.es_raiz else None, nivel + 1))
                else:
                    # Es partida
                    cap_dest = codigo if not concepto.es_raiz else (capitulo_actual or "CAPITULO_GENERAL")
                    if cap_dest not in capitulos_map and cap_dest != "CAPITULO_GENERAL":
                        # Si padre es raíz, crear capítulo general
                        cap_dest = "CAPITULO_GENERAL"
                    if cap_dest == "CAPITULO_GENERAL" and "CAPITULO_GENERAL" not in capitulos_map:
                        capitulos_map["CAPITULO_GENERAL"] = {
                            "codigo": "CAPITULO_GENERAL",
                            "codigo_raw": "CAPITULO_GENERAL",
                            "nombre": "PARTIDAS BC3",
                            "descripcion": "",
                            "partidas": [],
                        }
                    capitulos_map.setdefault(cap_dest, {
                        "codigo": cap_dest,
                        "codigo_raw": cap_dest,
                        "nombre": "PARTIDAS BC3",
                        "descripcion": "",
                        "partidas": [],
                    })
                    capitulos_map[cap_dest]["partidas"].append(hijo_cod)
                    # También encolamos la partida para explorar sus recursos (no para capítulos)
                    # No encolamos como capítulo
        else:
            # Es partida que a su vez descompone en recursos, no en capítulos
            # Si estamos dentro de un capítulo, ya fue asignada
            # Si no, asignar a capítulo general
            if capitulo_actual:
                capitulos_map.setdefault(capitulo_actual, {
                    "codigo": capitulo_actual,
                    "codigo_raw": capitulo_actual,
                    "nombre": "PARTIDAS BC3",
                    "descripcion": "",
                    "partidas": [],
                })
                if codigo not in capitulos_map[capitulo_actual]["partidas"]:
                    capitulos_map[capitulo_actual]["partidas"].append(codigo)
            else:
                capitulos_map.setdefault("CAPITULO_GENERAL", {
                    "codigo": "CAPITULO_GENERAL",
                    "codigo_raw": "CAPITULO_GENERAL",
                    "nombre": "PARTIDAS BC3",
                    "descripcion": "",
                    "partidas": [],
                })
                if codigo not in capitulos_map["CAPITULO_GENERAL"]["partidas"]:
                    capitulos_map["CAPITULO_GENERAL"]["partidas"].append(codigo)

    # Si no se construyó nada, fallback: todas las partidas no-capítulo a capítulo general
    if not capitulos_map:
        capitulos_map["CAPITULO_GENERAL"] = {
            "codigo": "CAPITULO_GENERAL",
            "codigo_raw": "CAPITULO_GENERAL",
            "nombre": "PARTIDAS BC3",
            "descripcion": "",
            "partidas": [c.codigo for c in conceptos.values() if not c.es_capitulo and not c.es_raiz],
        }

    # Limpiar capítulos vacíos (solo si tienen subcapítulos con partidas)
    # Mantener orden de aparición en BC3
    orden_capitulos = []
    for codigo in capitulos_map:
        if capitulos_map[codigo]["partidas"] or codigo == "CAPITULO_GENERAL":
            orden_capitulos.append(capitulos_map[codigo])

    # Si capítulo general está vacío y hay otros, eliminarlo
    if len(orden_capitulos) > 1:
        orden_capitulos = [c for c in orden_capitulos if not (c["codigo"] == "CAPITULO_GENERAL" and not c["partidas"])]
    if not orden_capitulos:
        orden_capitulos = [{
            "codigo": "CAPITULO_GENERAL",
            "codigo_raw": "CAPITULO_GENERAL",
            "nombre": "PARTIDAS BC3",
            "descripcion": "",
            "partidas": [c.codigo for c in conceptos.values() if not c.es_capitulo and not c.es_raiz][:MAX_FILAS],
        }]

    return {"capitulos": orden_capitulos}


def analizar_bc3(contenido: bytes) -> dict:
    """
    API pública usada por el router de importación.
    Devuelve dict con formato compatible con el importador existente.
    """
    parsed = parse_bc3(contenido)
    conceptos = parsed["conceptos"]
    mediciones = parsed["mediciones"]

    # Indexar mediciones por hijo (y padre)
    mediciones_por_codigo: dict[str, list[MedicionBC3]] = {}
    for m in mediciones:
        mediciones_por_codigo.setdefault(m.codigo_hijo, []).append(m)

    arbol = _construir_arbol_capitulos(parsed)

    filas = []
    advertencias = []
    capitulos_nombres = set()

    for cap in arbol["capitulos"]:
        cap_nombre = cap["nombre"] or "PARTIDAS BC3"
        capitulos_nombres.add(cap_nombre)
        for cod_partida in cap["partidas"][:MAX_FILAS]:
            if len(filas) >= MAX_FILAS:
                advertencias.append({"fila": 0, "mensaje": f"Se limita la importación a {MAX_FILAS} partidas."})
                break
            conc = conceptos.get(cod_partida)
            if not conc:
                continue
            # Cantidad: suma de mediciones o 1
            cantidad = 1.0
            meds = mediciones_por_codigo.get(cod_partida, [])
            medicion_total = None
            mediciones_desglose = []
            if meds:
                # Si hay mediciones con total, usar total del primer grupo
                for mm in meds:
                    if mm.total is not None:
                        medicion_total = mm.total
                        break
                # Desglose por líneas
                for mm in meds:
                    for linea in mm.lineas:
                        concepto_med = linea.get("comentario") or linea.get("etiqueta") or f"Med {mm.posicion}"
                        # Calcular cantidad de línea si hay uds*long*lat*alt
                        cant_linea = None
                        uds = linea.get("uds")
                        longi = linea.get("long")
                        lat = linea.get("lat")
                        alt = linea.get("alt")
                        if uds is not None:
                            cant_linea = uds
                            if longi is not None:
                                cant_linea *= longi
                            if lat is not None:
                                cant_linea *= lat
                            if alt is not None:
                                cant_linea *= alt
                        else:
                            # Si solo dimensiones, multiplicar
                            dims = [d for d in [longi, lat, alt] if d is not None]
                            if dims:
                                cant_linea = 1.0
                                for d in dims:
                                    cant_linea *= d
                        if cant_linea is None:
                            cant_linea = 0.0
                        mediciones_desglose.append({
                            "concepto": concepto_med[:250],
                            "cantidad": cant_linea,
                        })
                if medicion_total is not None:
                    cantidad = medicion_total
                elif mediciones_desglose:
                    cantidad = sum(m["cantidad"] for m in mediciones_desglose) or 1.0

            # Precio: si es 0 y tiene descomposición, calcular por recursos? Por ahora dejar 0 y advertir
            precio = conc.precio or 0.0

            # Descripción larga
            descripcion = conc.texto_largo or conc.resumen or ""

            # Unidad
            unidad = conc.unidad or "ud"
            unidad = unidad.strip()[:30] or "ud"

            # Categoría: si tipo 1,2,3 mapear, si no capítulo
            tipo_map = {1: "Mano de obra", 2: "Maquinaria", 3: "Materiales"}
            categoria = tipo_map.get(conc.tipo, "BC3")
            if cap_nombre != "PARTIDAS BC3":
                categoria = cap_nombre

            # Costes: si tiene descomposición, separar materiales/mano obra
            costes = {"materiales": 0.0, "mano_obra": 0.0, "complementarios": 0.0, "otros": 0.0}
            descom = parsed["descomposiciones"].get(conc.codigo, [])
            coste_directo = 0.0
            for hijo in descom:
                if hijo.get("es_porcentaje"):
                    continue
                hijo_conc = conceptos.get(hijo["codigo"])
                if not hijo_conc:
                    continue
                imp = (hijo["rendimiento"] * hijo["factor"] * hijo_conc.precio)
                coste_directo += imp
                if hijo_conc.tipo == 1:
                    costes["mano_obra"] += imp
                elif hijo_conc.tipo == 3:
                    costes["materiales"] += imp
                elif hijo_conc.tipo == 2:
                    costes["otros"] += imp
                else:
                    # Si hijo es partida compuesta, poner en otros
                    costes["otros"] += imp

            if precio == 0 and coste_directo > 0:
                precio = round(coste_directo, 2)

            filas.append({
                "codigo": conc.codigo,
                "codigo_externo": conc.codigo,
                "capitulo": cap_nombre,
                "nombre": (conc.resumen or conc.codigo)[:250],
                "descripcion": descripcion[:5000],
                "unidad": unidad,
                "cantidad": cantidad,
                "precio": precio,
                "categoria": categoria[:80],
                "tipo_partida": "included",
                "costes": costes,
                "coste_directo_unitario": round(coste_directo, 2) if coste_directo else precio,
                "mediciones": mediciones_desglose[:50],  # limitar
                "descomposicion_bc3": descom,
            })

    if not filas:
        raise ErrorBC3("El BC3 no contiene partidas importables (solo capítulos o conceptos sin descomposición).")

    # Generar resumen
    return {
        "formato": "bc3",
        "capitulo": "PARTIDAS BC3",
        "capitulos_detectados": len(arbol["capitulos"]),
        "conceptos_detectados": parsed["total_conceptos"],
        "filas_detectadas": len(filas),
        "filas": filas,
        "capitulos": arbol["capitulos"],
        "advertencias": advertencias,
        "version": parsed["version"],
    }


def es_formato_bc3(contenido: bytes) -> bool:
    if len(contenido) > MAX_BYTES:
        return False
    try:
        texto = _detectar_encoding_y_texto(contenido[:4096])
    except ErrorBC3:
        return False
    # Heurística rápida
    return "~C|" in texto or "~D|" in texto or "~V|" in texto


def bc3_a_filas_cotizat(resultado_bc3: dict) -> list[dict]:
    """Convierte resultado BC3 al formato tabular que espera validar_filas"""
    filas = []
    for f in resultado_bc3.get("filas", []):
        filas.append({
            "codigo": f.get("codigo", ""),
            "capitulo": f.get("capitulo", "CAPÍTULO GENERAL"),
            "partida": f.get("nombre", ""),
            "descripcion": f.get("descripcion", ""),
            "unidad": f.get("unidad", "ud"),
            "cantidad": f.get("cantidad", 1.0),
            "precio": f.get("precio", 0.0),
            "categoria": f.get("categoria", "BC3"),
            "tipo_partida": f.get("tipo_partida", "included"),
            "costes": f.get("costes", {}),
            "coste_directo_unitario": f.get("coste_directo_unitario", 0.0),
            "mediciones": f.get("mediciones", []),
        })
    return filas


# ---------------------------------------------------------------------------
# Export BC3
# ---------------------------------------------------------------------------

def _sanear_codigo(codigo: str, fallback: str) -> str:
    """Código BC3 válido: A-Z, 0-9, ., $, #, %, &, _ (max 20)"""
    raw = str(codigo or fallback or "").strip()
    if not raw:
        raw = fallback
    # Reemplazar espacios y caracteres no permitidos por _
    raw = re.sub(r"[^A-Za-z0-9.\$\#\%\&\_]+", "_", raw)
    # Quitar _ al inicio/fin
    raw = raw.strip("_")
    # Limitar a 20
    return raw[:20] or fallback[:20]


def _sanear_texto_bc3(texto: str, max_len: int = 5000) -> str:
    """Elimina caracteres que rompen BC3: ~ | \\ y controla longitud"""
    t = str(texto or "").replace("~", "").replace("|", " ").replace("\\", " ").replace("\r", " ").replace("\n", " ")
    t = " ".join(t.split())  # colapsar espacios
    return t[:max_len]


def exportar_presupuesto_bc3(presupuesto, cfg=None) -> bytes:
    """Exporta conceptos, árbol y mediciones FIEBDC-3/2020 en ANSI.

    Cada padre tiene un único registro ~D; cada línea ~M ocupa seis
    subcampos. Los códigos son únicos incluso tras sanearlos/truncarlos.
    Los precios contractuales se conservan al recalcular el descompuesto
    mediante un ajuste explícito al precio de venta (no un recurso ficticio).
    """
    from decimal import Decimal
    from .calculations import partida_activa, money

    usados = set()

    def codigo(raw, fallback, sufijo=""):
        base = _sanear_codigo(raw, fallback).replace("#", "").replace("%", "_").replace("&", "_") or fallback
        limite = 20 - len(sufijo)
        candidato = base[:limite]
        n = 1
        while candidato in usados:
            cola = f"_{n}"
            candidato = base[:limite - len(cola)] + cola
            n += 1
        usados.add(candidato)
        return candidato + sufijo

    def num(valor):
        # No perder cantidades pequeñas ni precios con más de dos decimales.
        return format(Decimal(str(valor or 0)), "f")

    empresa = _sanear_texto_bc3(getattr(cfg, "empresa_nombre", "") or "CotizaT", 200)
    titulo = getattr(presupuesto, "titulo", "") or f"Presupuesto {getattr(presupuesto, 'numero', '')}"
    comentario = _sanear_texto_bc3(f"{empresa} - {titulo}", 200)
    moneda = _sanear_texto_bc3(getattr(presupuesto, "moneda", "") or "USD", 3).upper()
    iva = num(getattr(presupuesto, "impuesto_pct", 0))
    descuento = num(getattr(presupuesto, "descuento_pct", 0))
    lineas = [
        f"~V|{empresa}|FIEBDC-3/2020|CotizaT|Precio|ANSI|{comentario}|2||",
        f"~K|2\\2\\2\\3\\2\\2\\2\\2\\{moneda}\\|0\\0\\0\\{descuento}\\{iva}|",
    ]

    def concepto(cod, unidad, resumen, precio, tipo=0):
        lineas.append(
            f"~C|{cod}|{_sanear_texto_bc3(unidad, 20)}|"
            f"{_sanear_texto_bc3(resumen, 64)}|{num(precio)}||{tipo}|"
        )

    def descomposicion(padre, hijos):
        if hijos:
            detalle = "".join(f"{hijo}\\1\\{num(cantidad)}\\" for hijo, cantidad in hijos)
            lineas.append(f"~D|{padre}|{detalle}|")

    raiz = codigo(getattr(presupuesto, "numero", ""), "PRESUPUESTO", "##")
    # Se reserva el código de todos los capítulos antes de generar partidas.
    capitulos = list(getattr(presupuesto, "capitulos", []) or [])
    codigos_cap = [codigo(f"{i:02d}", f"CAP{i}", "#") for i in range(1, len(capitulos) + 1)]
    # Los recargos de CotizaT no son costes internos: forman parte de la
    # oferta y deben viajar también en el árbol económico del presupuesto.
    subtotal = money(getattr(presupuesto, "subtotal", 0))
    recargos = [
        ("Transporte", money(getattr(presupuesto, "transporte_monto", 0))),
        ("Otros cargos", money(getattr(presupuesto, "otros_cargos_monto", 0))),
        ("Gastos indirectos", money(subtotal * Decimal(str(getattr(presupuesto, "gastos_indirectos_pct", 0) or 0)) / 100)),
        ("Imprevistos", money(subtotal * Decimal(str(getattr(presupuesto, "imprevistos_pct", 0) or 0)) / 100)),
    ]
    concepto(raiz, "", titulo, subtotal + sum(importe for _, importe in recargos))
    hijos_raiz = []
    recursos = {}
    avanzadas = bool(getattr(presupuesto, "usar_funciones_avanzadas", False))
    for i, (cap, cod_cap) in enumerate(zip(capitulos, codigos_cap), 1):
        concepto(cod_cap, "", getattr(cap, "nombre", "") or f"CAPITULO {i}", getattr(cap, "subtotal", 0))
        hijos_raiz.append((cod_cap, 1))
        hijos_cap = []
        for j, part in enumerate(getattr(cap, "partidas", []) or [], 1):
            if avanzadas and not partida_activa(part):
                continue
            descom = getattr(part, "descomposicion_cype", None)
            raw = (getattr(part, "codigo_externo", "") or getattr(part, "codigo", "")
                   or getattr(descom, "codigo", ""))
            cod_part = codigo(raw, f"{i:02d}.{j:02d}")
            precio = getattr(part, "precio_unitario", 0) or 0
            concepto(cod_part, getattr(part, "unidad", "") or "ud", getattr(part, "nombre", "") or cod_part, precio)
            texto = _sanear_texto_bc3(getattr(part, "descripcion", ""), 5000)
            if texto:
                lineas.append(f"~T|{cod_part}|{texto}|")
            cantidad = getattr(part, "cantidad_total", None)
            if cantidad is None:
                cantidad = getattr(part, "cantidad", 0) or 0
            hijos_cap.append((cod_part, cantidad))

            hijos_part = []
            coste = Decimal("0")
            filas = [f for f in (getattr(descom, "filas", []) or [])
                     if getattr(f, "tipo", "") == "recurso"]
            tasa = getattr(presupuesto, "tipo_cambio", None)
            # Validar todas las monedas antes de emitir conceptos, evitando
            # recursos huérfanos cuando solo una fila no puede convertirse.
            if any(
                (getattr(f, "moneda", None) or moneda) != moneda
                and not (getattr(f, "moneda", None) == "USD" and tasa and tasa > 0)
                for f in filas
            ):
                filas = []
            for fila in filas:
                precio_rec = Decimal(str(getattr(fila, "precio_unitario", 0) or 0))
                moneda_rec = getattr(fila, "moneda", None) or moneda
                if moneda_rec != moneda:
                    precio_rec *= Decimal(str(tasa))
                rendimiento = getattr(fila, "rendimiento", None)
                if rendimiento is None:
                    rendimiento = 1
                unidad = _sanear_texto_bc3(getattr(fila, "unidad", "") or "ud", 20)
                resumen = _sanear_texto_bc3(getattr(fila, "descripcion", ""), 64)
                tipo = {"mano_obra": 1, "otros": 2, "materiales": 3}.get(getattr(fila, "categoria", ""), 0)
                clave = (getattr(fila, "codigo", ""), unidad, resumen, precio_rec, tipo)
                cod_rec = recursos.get(clave)
                if cod_rec is None:
                    cod_rec = codigo(clave[0], f"R{len(recursos) + 1}")
                    recursos[clave] = cod_rec
                    concepto(cod_rec, unidad, resumen or cod_rec, precio_rec, tipo)
                hijos_part.append((cod_rec, rendimiento))
                coste += precio_rec * Decimal(str(rendimiento))
            if hijos_part:
                ajuste = Decimal(str(precio)) - coste
                if ajuste:
                    cod_ajuste = codigo(f"{cod_part}_AJ", "AJUSTE")
                    concepto(cod_ajuste, "ud", "Ajuste al precio de venta", ajuste)
                    hijos_part.append((cod_ajuste, 1))
                descomposicion(cod_part, hijos_part)

            mediciones = getattr(part, "mediciones", []) or []
            detalle = "".join(
                "0\\" + _sanear_texto_bc3(getattr(m, "concepto", ""), 64)
                + "\\" + num(getattr(m, "cantidad", 0)) + "\\1\\1\\1\\"
                for m in mediciones
            )
            # POS es la posición del hijo en su padre, no el número de líneas.
            lineas.append(f"~M|{cod_cap}\\{cod_part}|{len(hijos_cap)}|{num(cantidad)}|{detalle}|")
        descomposicion(cod_cap, hijos_cap)
    recargos = [(nombre, importe) for nombre, importe in recargos if importe]
    if recargos:
        cod_cap = codigo("CARGOS", "CARGOS", "#")
        concepto(cod_cap, "", "Cargos adicionales", sum(importe for _, importe in recargos))
        hijos_raiz.append((cod_cap, 1))
        hijos = []
        for i, (nombre, importe) in enumerate(recargos, 1):
            cod = codigo(f"CARGO{i}", f"CARGO{i}")
            concepto(cod, "ud", nombre, importe)
            hijos.append((cod, 1))
        descomposicion(cod_cap, hijos)
    descomposicion(raiz, hijos_raiz)
    return ("\r\n".join(lineas) + "\r\n").encode("windows-1252", errors="replace")
