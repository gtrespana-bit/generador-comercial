"""Servicio de Asistente de Inteligencia Artificial para CotizaT.

Proporciona soporte conversacional, asistencia en navegación, redacción
técnica de partidas y sugerencias de presupuestos de obra.

Arquitectura:
- Modelo de alto rendimiento: OpenAI GPT OSS 120B vía Groq Cloud API
  (OpenAI-compatible REST).
- Usa la capa de uso disponible de Groq; la cuenta y sus límites dependen del
  plan del proveedor.
- Inyección de contexto RAG: manual del sistema, atajos, descompuestos CYPE,
  monedas y catálogo propio de la organización activa.
- Modo de degradación elegante: si la clave no está configurada, el asistente
  responde a dudas frecuentes de CotizaT mediante el índice local de conocimiento
  e indica cómo activar la clave de Groq.
"""
from __future__ import annotations

import json
import logging
import os
import re
import urllib.error
import urllib.request
from math import ceil
from typing import Any, Generator
from urllib.parse import quote_plus

from sqlalchemy.orm import Session, load_only

log = logging.getLogger("cotizat")

# Configuración por omisión
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODELO_DEFAULT = "openai/gpt-oss-120b"
MODELO_LIGERO = "openai/gpt-oss-20b"

# Groq retiró estos identificadores el 16/08/2026. Se conservan como alias
# para que una instalación que aún los tenga en COTIZAT_IA_MODEL no falle con
# HTTP 404 después de actualizar la aplicación.
MODELOS_REEMPLAZO = {
    "llama-3.3-70b-versatile": MODELO_DEFAULT,
    "llama-3.1-8b-instant": MODELO_LIGERO,
}


def obtener_clave_ia() -> str:
    """Devuelve la clave de API de Groq configurada en el entorno o archivo .env."""
    clave = (
        os.environ.get("GROQ_API_KEY", "").strip()
        or os.environ.get("COTIZAT_GROQ_API_KEY", "").strip()
    )
    if clave:
        return clave
    try:
        from dotenv import dotenv_values
        from pathlib import Path
        env_path = Path(__file__).resolve().parents[2] / ".env"
        if env_path.is_file():
            valores = dotenv_values(env_path)
            return (
                (valores.get("GROQ_API_KEY") or "").strip()
                or (valores.get("COTIZAT_GROQ_API_KEY") or "").strip()
            )
    except Exception:
        pass
    return ""


def obtener_modelo_ia() -> str:
    """Devuelve el modelo configurado o el predeterminado.

    También lee ``COTIZAT_IA_MODEL`` del ``.env`` cuando la aplicación se
    arranca directamente con Uvicorn (sin pasar por ``run.py``). Los modelos
    retirados por Groq se traducen a su reemplazo vigente para evitar un 404.
    """
    modelo = os.environ.get("COTIZAT_IA_MODEL", "").strip()
    if not modelo:
        try:
            from dotenv import dotenv_values
            from pathlib import Path

            env_path = Path(__file__).resolve().parents[2] / ".env"
            if env_path.is_file():
                modelo = (dotenv_values(env_path).get("COTIZAT_IA_MODEL") or "").strip()
        except Exception:
            pass
    modelo = modelo or MODELO_DEFAULT
    return MODELOS_REEMPLAZO.get(modelo, modelo)


def asistente_configurado() -> bool:
    """Indica si la API de IA externa tiene credencial lista."""
    return bool(obtener_clave_ia())


def estado_asistente() -> dict[str, Any]:
    """Resumen público del estado del asistente para la interfaz."""
    clave_ok = asistente_configurado()
    return {
        "ok": True,
        "configurado": clave_ok,
        "proveedor": "Groq (LPU Inference)",
        "modelo": obtener_modelo_ia(),
        # Compatibilidad de contrato: ``None`` significa que CotizaT no promete
        # gratuidad del proveedor externo. Las herramientas locales sí son
        # explícitamente independientes de consumo y cuota.
        "gratuito": None,
        "herramientas_locales_sin_consumo": True,
        "generacion_sujeta_a_cuotas_proveedor": True,
        "mensaje_activacion": (
            "" if clave_ok else
            "Para activar respuestas con GPT OSS 120B en tiempo real, "
            "configura tu clave de Groq en .env (GROQ_API_KEY=gsk_...)."
        ),
    }


# ---------------------------------------------------------------------------
# Base de Conocimiento Interna de CotizaT
# ---------------------------------------------------------------------------

MANUAL_COTIZAT = """
=== MANUAL Y CAPACIDADES DE COTIZAT ===
CotizaT es un software browser-first de presupuestos, descompuestos (APU) y control comercial de obras y remodelaciones.

RUTAS Y NAVEGACIÓN PRINCIPAL:
- /inicio: Dashboard general con métricas de facturación, estado de presupuestos, margen estimado, tasa de conversión y accesos rápidos.
- /presupuestos: Listado de presupuestos con filtros por estado (Borrador, Enviado, Aprobado, Rechazado, Vencido), cliente y fechas.
- /presupuestos/nuevo: Constructor visual de presupuestos con capítulos ilimitados, partidas, mediciones desglosadas y productos.
- /clientes: Directorio de clientes con RIF/NIT/C.I., contacto, dirección y teléfono.
- /partidas: Catálogo de partidas reutilizables con análisis de precios unitarios (APU), descomposición de materiales/mano de obra/equipos y rendimientos.
- /recursos: Cuadro de precios de recursos (materiales, horas de mano de obra y alquiler de maquinaria).
- /productos: Catálogo de productos/materiales presupuestados con fotografía y precio unitario.
- /plantillas: Modelos y estructuras de presupuestos prearmados para reutilizar con un clic.
- /recetas: Packs de partidas por tipo de estancia (Baño estándar, Cocina integral, Pintura general, etc.).
- /facturas: Generación y control de documentos de cobro comerciales no fiscales (DC-2026-001).
- /reportes: Informes comerciales, exportación de balances y análisis de márgenes.
- /buscar: Búsqueda global instantánea en clientes, presupuestos, partidas, productos y notas.
- /configuracion: Datos fiscales de la empresa, logo con control de tamaño en PDF, moneda, IVA, tasa de cambio BCV/manual, copias de seguridad.
- /guia-rapida: Manual de referencia rápida y flujo de trabajo.

ATAJOS DE TECLADO EN EL EDITOR DE PRESUPUESTOS:
- Alt + P: Añadir una nueva partida inmediatamente.
- Alt + C: Añadir un nuevo capítulo.
- Ctrl + K (o presionar /): Abrir y enfocar el buscador instantáneo del catálogo de partidas.
- Enter dentro de los campos de la partida: Avanza secuencialmente (Título → Cantidad → Precio unitario) sin saltar de fila ni crear partidas vacías.
- Ctrl + Z: Deshacer cambios estructurales recientes.
- Ctrl + Enter: Guardar el presupuesto actual.
- Arrastrar y soltar: Reordenar partidas entre capítulos.

FUNCIONES AVANZADAS:
- Mediciones desglosadas: Cada partida permite detallar zonas/estancias (ej. Baño 4.50 m², Pasillo 2.20 m²); la suma calcula la cantidad automáticamente.
- Importación CYPE (.xlsx): Admite plantillas de 8 y 10 columnas (DPT020 / RBE010). Clasifica en materiales, mano de obra, directos complementarios y otros. Permite editar rendimientos y precios unitarios.
- Monedas y Tasa de Cambio: Soporta USD, Bs (VES), COP, MXN, EUR, etc. Incluye actualización automática o manual de tasa de cambio y cláusula cambiaria.
- PDF Profesional ReportLab: Encabezado corporativo, caja de empresa con faja navy, marca de agua por estado (BORRADOR, RECHAZADO, VENCIDO), firmas digitales (cliente y empresa), anexo de garantías por familia de obra y portada opcional con foto del proyecto.
- Documentos de Cobro (DC): Desde un presupuesto aprobado se emite el documento de cobro comercial aclarando que no sustituye una factura fiscal.
- Envío por WhatsApp: Abre wa.me con el texto resumen del presupuesto redactado para enviar al cliente.
"""


# Palabras conversacionales que no deben convertirse en filtros del catálogo.
# El problema original era precisamente tomar las tres primeras palabras de
# «qué partida es para demolición de porcelanato»: se buscaba ``qué partida
# para`` y nunca se llegaba a los términos técnicos.
_PALABRAS_VACIAS_CONSULTA_PARTIDAS = frozenset({
    "a", "al", "algo", "cual", "cuales", "como", "con", "cualquiera",
    "de", "debo", "del", "dime", "el", "ella", "en", "es", "esa", "ese",
    "esta", "este", "hay", "la", "las", "le", "lo", "los", "me", "mi",
    "necesito", "para", "partida", "partidas", "por", "puede", "puedo",
    "que", "quiero", "se", "seria", "sirve", "su", "tengo", "tiene",
    "tu", "una", "uno", "usar", "uso", "utilizar", "y",
    "busca", "buscar", "buscame", "encuentra", "encontrar", "localiza",
    "recomienda", "recomendar", "sugiere", "sugerir", "catalogo",
})

_PATRONES_INTENCION_PARTIDAS = (
    r"\b(?:que|cual|cuales)\s+(?:es\s+|son\s+|seria\s+|serian\s+)?(?:la\s+|las\s+)?partidas?\b",
    r"\bpartidas?\s+(?:de|para|correspondiente)\b",
    r"\b(?:necesito|quiero|uso|usar)\s+(?:una\s+|la\s+)?partida\b",
    r"\b(?:busca|buscar|buscame|encuentra|encontrar|localiza|recomienda|sugiere)\w*\b.*\bpartidas?\b",
    r"\bpartidas?\b.*\b(?:busca|buscar|encuentra|localiza|recomienda|sugiere)\w*\b",
)


def es_consulta_busqueda_partidas(consulta: str) -> bool:
    """Reconoce peticiones que deben ejecutar una búsqueda, no explicarla."""
    from .busqueda_catalogo import normalizar

    texto = normalizar(consulta)
    if not texto or "partida" not in texto:
        return False
    # «Qué capítulos y partidas incluyo para remodelar un baño» es una
    # planificación de alcance; la FAQ/IA puede resolverla mejor que una lista
    # plana. Una petición explícita de búsqueda sí consulta el catálogo.
    if (
        "capitulos y partidas" in texto
        and not re.search(r"\b(busca|buscar|encuentra|localiza)\w*\b", texto)
    ):
        return False
    return any(re.search(patron, texto) for patron in _PATRONES_INTENCION_PARTIDAS)


def extraer_consulta_partidas(consulta: str) -> str:
    """Conserva únicamente los conceptos técnicos, incluidas sus tildes."""
    from .busqueda_catalogo import normalizar

    salida: list[str] = []
    vistos: set[str] = set()
    for original in re.findall(r"[\w.-]+", str(consulta or "").lower(), flags=re.UNICODE):
        limpio = normalizar(original)
        if (
            not limpio
            or len(limpio) < 2
            or limpio in _PALABRAS_VACIAS_CONSULTA_PARTIDAS
            or limpio in vistos
        ):
            continue
        vistos.add(limpio)
        salida.append(original)
        if len(salida) >= 6:
            break
    return " ".join(salida)


def _consulta_parece_tecnica(consulta: str) -> bool:
    """Evita recorrer el catálogo al preguntar «hola» o por navegación."""
    from .busqueda_catalogo import grupos_sinonimos, normalizar

    if es_consulta_busqueda_partidas(consulta):
        return True
    tokens = set(normalizar(extraer_consulta_partidas(consulta)).split())
    if not tokens:
        return False
    for grupo in grupos_sinonimos():
        for termino in grupo["terminos"]:
            if tokens.intersection(termino.split()):
                return True
    return False


def _coincide_variante(texto_normal: str, variante: str) -> bool:
    """Coincidencia normalizada tolerante con plurales y formas de oficio."""
    from .busqueda_catalogo import normalizar

    termino = normalizar(variante)
    if not termino:
        return False
    if termino in texto_normal:
        return True
    # ``picar`` debe reconocer ``picado`` y ``demoler`` a ``demolido``. Solo
    # se usa para términos suficientemente largos para evitar falsos positivos.
    if " " not in termino and len(termino) >= 5 and termino.endswith(("ar", "er", "ir")):
        return termino[:-1] in texto_normal
    return False


def _puntuar_partida(partida, grupos: list[list[str]]) -> tuple[int, int]:
    """Devuelve (grupos coincidentes, relevancia) para una partida."""
    from .busqueda_catalogo import normalizar

    nombre = normalizar(partida.nombre or "")
    ruta = normalizar(" ".join((
        partida.categoria or "",
        partida.subcategoria or "",
        partida.apartado or "",
    )))
    descripcion = normalizar(partida.descripcion or "")
    codigo = normalizar(" ".join((
        partida.codigo_interno or "",
        partida.codigo_legacy or "",
        partida.codigo_externo or "",
    )))
    coincidencias = 0
    puntuacion = min(int(partida.usos or 0), 50)
    for variantes in grupos:
        mejor = 0
        for variante in variantes:
            if _coincide_variante(nombre, variante):
                mejor = max(mejor, 90)
            elif _coincide_variante(codigo, variante):
                mejor = max(mejor, 80)
            elif _coincide_variante(ruta, variante):
                mejor = max(mejor, 45)
            elif _coincide_variante(descripcion, variante):
                mejor = max(mejor, 20)
        if mejor:
            coincidencias += 1
            puntuacion += mejor
    # El resultado completo manda siempre sobre uno popular pero parcial.
    return coincidencias, coincidencias * 1000 + puntuacion


def buscar_partidas_catalogo(
    db: Session,
    consulta: str,
    limite: int = 5,
) -> dict[str, Any]:
    """Busca y ordena partidas reales del tenant activo.

    La evaluación final se hace con texto normalizado en Python porque SQLite
    no ofrece una comparación fiable sin tildes. Con el catálogo habitual
    (unos pocos miles de conceptos y solo los campos ligeros) el recorrido es
    pequeño, evita depender del proveedor de IA y conserva el aislamiento por
    organización aplicado por la sesión ORM.
    """
    from ..models import Configuracion, Partida
    from .busqueda_catalogo import variantes_consulta

    consulta_tecnica = extraer_consulta_partidas(consulta)
    grupos = variantes_consulta(consulta_tecnica)
    limite = max(1, min(int(limite or 5), 10))
    if not grupos:
        return {
            "consulta": consulta_tecnica,
            "resultados": [],
            "coincidencia_exacta": False,
            "total_grupos": 0,
        }

    campos = (
        Partida.id,
        Partida.nombre,
        Partida.descripcion,
        Partida.precio_unitario,
        Partida.unidad,
        Partida.categoria,
        Partida.subcategoria,
        Partida.apartado,
        Partida.codigo_interno,
        Partida.codigo_legacy,
        Partida.codigo_externo,
        Partida.usos,
        Partida.oculta,
    )
    candidatas = (
        db.query(Partida)
        .filter(Partida.oculta.is_(False))
        .options(load_only(*campos))
        .all()
    )
    puntuadas = []
    for partida in candidatas:
        coincidencias, puntuacion = _puntuar_partida(partida, grupos)
        if coincidencias:
            puntuadas.append((coincidencias, puntuacion, partida))

    total_grupos = len(grupos)
    exactas = [fila for fila in puntuadas if fila[0] == total_grupos]
    coincidencia_exacta = bool(exactas)
    if exactas:
        seleccion = exactas
    elif puntuadas:
        max_coincidencias = max(fila[0] for fila in puntuadas)
        minimo_util = max(1, ceil(total_grupos / 2))
        seleccion = [
            fila for fila in puntuadas
            if fila[0] == max_coincidencias and fila[0] >= minimo_util
        ]
    else:
        seleccion = []
    seleccion.sort(key=lambda fila: (-fila[1], (fila[2].nombre or "").lower()))

    cfg = db.query(Configuracion).first()
    moneda = str(getattr(cfg, "moneda_default", "USD") or "USD").strip().upper()
    factor = 1.0
    codigo_pais = ""
    try:
        from .tasa import factor_conversion_local
        from .traduccion import codigo_desde_pais

        factor = factor_conversion_local(moneda, getattr(cfg, "tasa_cambio", None))
        codigo_pais = codigo_desde_pais(getattr(cfg, "empresa_pais", ""))
    except Exception:
        pass

    resultados = []
    for _, puntuacion, partida in seleccion[:limite]:
        nombre = partida.nombre or ""
        descripcion = partida.descripcion or ""
        categoria = partida.categoria or ""
        subcategoria = partida.subcategoria or ""
        apartado = partida.apartado or ""
        if codigo_pais:
            try:
                from .traduccion import traducir

                nombre = traducir(nombre, codigo_pais)
                descripcion = traducir(descripcion, codigo_pais)
                categoria = traducir(categoria, codigo_pais)
                subcategoria = traducir(subcategoria, codigo_pais)
                apartado = traducir(apartado, codigo_pais)
            except Exception:
                pass
        precio = float(partida.precio_unitario or 0)
        if factor != 1.0:
            try:
                from .tasa import tasa_convertir_precio

                precio = tasa_convertir_precio(precio, factor)
            except Exception:
                pass
        resultados.append({
            "id": partida.id,
            "codigo": (
                partida.codigo_interno
                or partida.codigo_externo
                or partida.codigo_legacy
                or "PARTIDA"
            ),
            "nombre": nombre,
            "descripcion": descripcion,
            "unidad": partida.unidad or "ud",
            "precio": precio,
            "moneda": moneda,
            "categoria": categoria,
            "subcategoria": subcategoria,
            "apartado": apartado,
            "puntuacion": puntuacion,
        })
    return {
        "consulta": consulta_tecnica,
        "resultados": resultados,
        "coincidencia_exacta": coincidencia_exacta,
        "total_grupos": total_grupos,
    }


def _texto_catalogo_seguro(valor: str) -> str:
    """Evita que datos editables del catálogo se interpreten como Markdown."""
    return re.sub(r"[\[\]*`]", "", str(valor or "")).strip()


def responder_busqueda_partidas(
    db: Session,
    consulta: str,
    contexto: dict[str, Any] | None = None,
) -> str:
    """Construye una respuesta accionable a partir de resultados verificados."""
    busqueda = buscar_partidas_catalogo(db, consulta, limite=5)
    termino = busqueda["consulta"] or extraer_consulta_partidas(consulta)
    enlace_busqueda = f"/partidas?q={quote_plus(termino)}" if termino else "/partidas"
    resultados = busqueda["resultados"]
    if not resultados:
        log.warning(
            "asistente_busqueda_sin_resultados",
            extra={
                "evento": "asistente_busqueda_sin_resultados",
                "organizacion_id": db.info.get("organizacion_id"),
                "tipo": "partida",
                "consulta": termino[:120],
            },
        )
        return (
            "### 🔎 Búsqueda realizada en tu catálogo\n\n"
            f"He buscado **{_texto_catalogo_seguro(termino)}** entre las partidas activas, "
            "pero no hay una coincidencia suficientemente fiable. No voy a inventar un código ni un precio.\n\n"
            f"[Abrir el catálogo con esta búsqueda]({enlace_busqueda}) · "
            "[Crear una partida nueva](/partidas/nueva)"
        )

    encabezado = (
        "### 🔎 Partidas encontradas en tu catálogo\n\n"
        f"He buscado **{_texto_catalogo_seguro(termino)}** en el catálogo activo."
    )
    if not busqueda["coincidencia_exacta"]:
        encabezado += " No existe una coincidencia completa; estas son las más cercanas."
    lineas = [encabezado, ""]
    for indice, partida in enumerate(resultados, start=1):
        codigo = _texto_catalogo_seguro(partida["codigo"])
        nombre = _texto_catalogo_seguro(partida["nombre"])
        ruta = " › ".join(
            _texto_catalogo_seguro(valor)
            for valor in (
                partida["categoria"], partida["subcategoria"], partida["apartado"]
            )
            if str(valor or "").strip()
        )
        precio = float(partida["precio"] or 0)
        precio_texto = (
            f"{precio:,.2f} {partida['moneda']}"
            if precio > 0 else "sin precio de referencia"
        )
        lineas.extend((
            f"{indice}. **{codigo} · {nombre}**",
            f"   - Unidad: `{_texto_catalogo_seguro(partida['unidad'])}` · Catálogo: **{precio_texto}**",
            f"   - Ubicación: {ruta or 'Catálogo general'}",
            f"   - [Ver o editar esta partida](/partidas/{partida['id']}/editar)",
        ))
        pagina_actual = str((contexto or {}).get("pagina") or "")
        if (contexto or {}).get("presupuesto_id") and re.fullmatch(
            r"/presupuestos/\d+/editar", pagina_actual
        ):
            lineas.append(
                f"   - [Añadir al presupuesto abierto](/api/ia/accion/agregar-partida?partida_id={partida['id']})"
            )

    consulta_normal = termino.lower()
    if (
        ("porcelanato" in consulta_normal or "ceram" in consulta_normal)
        and not any(zona in consulta_normal for zona in ("piso", "pared", "rodapie", "rodapié"))
    ):
        lineas.extend((
            "",
            "**Para afinar la elección:** dime si se trata de **piso, pared o rodapié**; "
            "son alcances y unidades diferentes.",
        ))
    lineas.extend((
        "",
        f"[Ver todos los resultados en Partidas]({enlace_busqueda})",
        "Los importes son referencias del catálogo activo; revisa el alcance y el APU antes de presupuestar.",
    ))
    return "\n".join(lineas)


def resolver_accion_funcional(
    db: Session,
    consulta: str,
    contexto: dict[str, Any] | None = None,
) -> str | None:
    """Ejecuta acciones deterministas antes de recurrir al texto generativo."""
    from .herramientas_ia import resolver_herramienta_ia

    respuesta = resolver_herramienta_ia(db, consulta, contexto)
    if respuesta:
        return respuesta
    if es_consulta_busqueda_partidas(consulta):
        return responder_busqueda_partidas(db, consulta, contexto)
    return None


def _construir_contexto_organizacion(db: Session, consulta_usuario: str) -> str:
    """Extrae configuración y resultados verificados del catálogo activo."""
    contexto = []
    try:
        from ..models import Configuracion

        cfg = db.query(Configuracion).first()
        if cfg:
            contexto.append(
                f"ORGANIZACIÓN ACTIVA:\n"
                f"- Empresa: {cfg.empresa_nombre}\n"
                f"- País: {cfg.empresa_pais}\n"
                f"- Moneda: {cfg.moneda_default}\n"
                f"- IVA: {cfg.iva_default}%\n"
                f"- Tasa de cambio: {cfg.tasa_cambio or '1.0'}\n"
            )

        partidas_encontradas = []
        if _consulta_parece_tecnica(consulta_usuario):
            busqueda = buscar_partidas_catalogo(db, consulta_usuario, limite=5)
            for partida in busqueda["resultados"]:
                partidas_encontradas.append(
                    f"• ID={partida['id']} [{partida['codigo']}] {partida['nombre']} "
                    f"({partida['unidad']} - {partida['precio']:.2f} {partida['moneda']}) "
                    f"Ruta interna: /partidas/{partida['id']}/editar"
                )
        if partidas_encontradas:
            contexto.append(
                "RESULTADOS VERIFICADOS DEL CATÁLOGO ACTIVO (datos reales, no inventar otros):\n"
                + "\n".join(partidas_encontradas)
            )
    except Exception as exc:
        log.debug("No se pudo extraer contexto completo de la organización: %s", exc)

    return "\n\n".join(contexto)


def construir_system_prompt(
    db: Session,
    consulta: str = "",
    contexto: dict[str, Any] | None = None,
) -> str:
    """Construye el prompt con manual, catálogo y pantalla actual verificada."""
    from .herramientas_ia import contexto_pagina_verificado

    contexto_org = _construir_contexto_organizacion(db, consulta)
    contexto_pagina = contexto_pagina_verificado(db, contexto)
    return (
        "Eres el Asistente Inteligente de CotizaT, un copiloto experto en presupuestos, "
        "remodelaciones, análisis de precios unitarios (APU), especificaciones técnicas y uso del software.\n\n"
        "TUS OBJETIVOS:\n"
        "1. Resolver la tarea concreta antes de explicarla. Si el contexto contiene RESULTADOS VERIFICADOS "
        "DEL CATÁLOGO ACTIVO, muestra esas partidas con código, unidad, precio y enlace; nunca respondas "
        "solamente 've al buscador' ni afirmes que no puedes consultar el catálogo.\n"
        "2. Responder dudas de uso del software con instrucciones exactas, indicando nombres de botones, "
        "rutas (como /presupuestos/nuevo, /configuracion) y atajos de teclado (Alt+P, Alt+C, Ctrl+K, Ctrl+Enter).\n"
        "3. Asistir a contratistas, arquitectos y constructores en cómo estructurar presupuestos de obra "
        "(capítulos, partidas lógicas, mediciones, rendimientos).\n"
        "4. Redactar descripciones técnicas profesionales para partidas de construcción cuando se te solicite.\n"
        "5. Ser directo, conciso, educado y orientado a la acción. Empieza por el resultado y usa viñetas, "
        "negritas y enlaces internos en formato Markdown. No inventes IDs, códigos, precios ni partidas.\n"
        "6. REGLA ESTRICTA DE CÁLCULOS: Para sumas o totales finales, indica al usuario cómo CotizaT los calcula "
        "automáticamente en el servidor para evitar descuadres o discrepancias matemáticas.\n\n"
        f"{MANUAL_COTIZAT}\n\n"
        f"{contexto_org}\n\n"
        f"{contexto_pagina}"
    )


# ---------------------------------------------------------------------------
# Motor de Respuestas Locales (Fallback sin API Key)
# ---------------------------------------------------------------------------

PREGUNTAS_FRECUENTES_LOCALES = [
    {
        "patrones": [r"atajo", r"teclado", r"shortcut", r"rapido", r"hands-free"],
        "respuesta": (
            "### ⌨️ Atajos de teclado en el Editor de Presupuestos:\n\n"
            "- **`Alt + P`**: Añadir una nueva partida inmediatamente.\n"
            "- **`Alt + C`**: Añadir un nuevo capítulo.\n"
            "- **`Ctrl + K`** (o tecla **`/`**): Abrir y enfocar el buscador del catálogo de partidas.\n"
            "- **`Enter`** (dentro de una partida): Avanza secuencialmente por los campos: *Título → Cantidad → Precio unitario* sin crear partidas vacías.\n"
            "- **`Ctrl + Z`**: Deshacer cambios estructurales recientes.\n"
            "- **`Ctrl + Enter`**: Guardar el presupuesto actual.\n\n"
            "💡 *Pruébalos en [Crear Presupuesto](/presupuestos/nuevo).*"
        ),
    },
    {
        "patrones": [r"cype", r"excel", r"descompuesto", r"dpt020", r"rbe010", r"importar"],
        "respuesta": (
            "### 📑 Importación de descompuestos CYPE (.xlsx):\n\n"
            "CotizaT permite importar matrices de descompuestos exportadas desde CYPE/Arquímedes:\n\n"
            "1. Ve a **Presupuestos** → [Importar Descompuesto](/presupuestos/importar-descompuesto) o dentro del propio editor.\n"
            "2. Sube tu archivo `.xlsx` (detecta formatos de 8 columnas tipo `DPT020` y 10 columnas tipo `RBE010`).\n"
            "3. CotizaT clasifica automáticamente los costes en: **Materiales, Mano de Obra, Directos Complementarios y Otros**.\n"
            "4. Puedes editar los rendimientos y precios unitarios en cualquier momento desde la vista del descompuesto para recalcular la cascada de costes."
        ),
    },
    {
        "patrones": [r"tasa", r"moneda", r"dolar", r"dólar", r"bolivar", r"bolívar", r"bcv", r"cambio", r"cop", r"mxn"],
        "respuesta": (
            "### 💱 Configuración de Moneda y Tasa de Cambio:\n\n"
            "1. Ve a [Configuración](/configuracion).\n"
            "2. En la sección **Moneda por defecto**, selecciona tu moneda principal (USD, VES, COP, MXN, etc.).\n"
            "3. Si utilizas moneda local junto con dólares, activa la casilla **Tasa de cambio** e introduce el valor del día o pulsa *Obtener tasa oficial*.\n"
            "4. En el PDF puedes mostrar u ocultar la **cláusula cambiaria** y la referencia de conversión."
        ),
    },
    {
        "patrones": [r"baño", r"bano", r"sanitario", r"ducha", r"remodelar baño"],
        "respuesta": (
            "### 🛁 Estructura recomendada para remodelación de Baño:\n\n"
            "Te sugerimos organizar el presupuesto en los siguientes capítulos y partidas:\n\n"
            "1. **Demoliciones y Desmontajes:**\n"
            "   - Desmontaje de sanitarios y accesorios existentes.\n"
            "   - Picado y retiro de revestimiento cerámico en paredes y piso.\n"
            "2. **Instalaciones Sanitarias y Fontanería:**\n"
            "   - Reubicación/adecuación de puntos de aguas blancas (PVC/termofusión).\n"
            "   - Adecuación de desagües y bote de ducha sifonado.\n"
            "3. **Impermeabilización y Revestimientos:**\n"
            "   - Aplicación de membrana impermeabilizante en zona de ducha.\n"
            "   - Enchapado de paredes y colocación de porcelanato en piso.\n"
            "4. **Aparatos Sanitarios y Grifería:**\n"
            "   - Instalación de inodoro, lavamanos con mueble, grifería y columna de ducha.\n\n"
            "💡 *Puedes insertar directamente un pack prearmado desde [Packs de Estancias](/recetas).*"
        ),
    },
    {
        "patrones": [r"cobro", r"factura", r"recibo", r"documento de cobro", r"dc-"],
        "respuesta": (
            "### 💵 Documentos de Cobro (DC):\n\n"
            "En CotizaT puedes emitir documentos de cobro comerciales no fiscales a partir de un presupuesto aprobado:\n\n"
            "1. Abre un presupuesto con estado **Aprobado**.\n"
            "2. Pulsa el botón **Generar Documento de Cobro**.\n"
            "3. Se creará un documento correlativo (`DC-2026-001`) con su propio PDF descargable e historial en [/facturas](/facturas).\n"
            "*(El documento aclara que es un comprobante comercial no fiscal).*"
        ),
    },
    {
        "patrones": [r"pdf", r"logo", r"firma", r"marca de agua", r"personalizar"],
        "respuesta": (
            "### 📄 Personalización del PDF Comercial:\n\n"
            "En [Configuración](/configuracion) puedes personalizar el diseño de tus presupuestos:\n\n"
            "- **Logotipo:** Sube el logo de tu empresa y ajusta el ancho máximo en puntos para que encaje perfecto.\n"
            "- **Color corporativo:** Define el color principal de las bandas del PDF.\n"
            "- **Firmas digitales:** Dibuja o captura la firma del cliente y de la empresa para insertarlas en el pie de página.\n"
            "- **Portada con foto:** Activa la portada de presentación con imagen del proyecto.\n"
            "- **Marcas de agua:** Se aplican automáticamente como BORRADOR, RECHAZADO o VENCIDO según el estado."
        ),
    },
]


def buscar_respuesta_local(consulta: str) -> str | None:
    """Busca una respuesta en el índice local de conocimiento de CotizaT."""
    texto = consulta.lower().strip()
    for item in PREGUNTAS_FRECUENTES_LOCALES:
        for patron in item["patrones"]:
            if re.search(patron, texto, re.IGNORECASE):
                return item["respuesta"]
    return None


# ---------------------------------------------------------------------------
# Cliente HTTP hacia Groq Cloud API
# ---------------------------------------------------------------------------

def _ejecutar_peticion_groq(
    payload: dict[str, Any],
    api_key: str,
    stream: bool = False,
    timeout: int = 30,
) -> urllib.request.Request | str:
    """Prepara y ejecuta la llamada HTTP hacia la API de Groq."""
    datos_json = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        GROQ_API_URL,
        data=datos_json,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream" if stream else "application/json",
            "User-Agent": "CotizaT-AI-Assistant/1.0",
        },
        method="POST",
    )
    return req


def consultar_asistente_stream(
    db: Session,
    mensajes: list[dict[str, str]],
    contexto: dict[str, Any] | None = None,
) -> Generator[str, None, None]:
    """Generador que emite fragmentos de texto en formato SSE (Server-Sent Events)."""
    api_key = obtener_clave_ia()
    ultimo_mensaje = mensajes[-1].get("content", "") if mensajes else ""

    # Las acciones sobre datos propios se ejecutan siempre en el servidor,
    # antes del modelo externo. Así una búsqueda devuelve resultados reales
    # incluso sin clave y el modelo no puede sustituirla por consejos genéricos.
    respuesta_funcional = resolver_accion_funcional(db, ultimo_mensaje, contexto)
    if respuesta_funcional:
        yield f"data: {json.dumps({'texto': respuesta_funcional, 'finalizado': False})}\n\n"
        yield f"data: {json.dumps({'texto': '', 'finalizado': True})}\n\n"
        return

    # Si no hay clave de API configurada, utiliza el motor de respuesta local
    if not api_key:
        respuesta_local = buscar_respuesta_local(ultimo_mensaje)
        if respuesta_local:
            yield f"data: {json.dumps({'texto': respuesta_local, 'finalizado': False})}\n\n"
            yield f"data: {json.dumps({'texto': '', 'finalizado': True})}\n\n"
            return
        else:
            guia_activacion = (
                "### 💬 Asistente CotizaT (Herramientas locales activas)\n\n"
                "Sin una clave externa puedo buscar datos, revisar borradores, calcular mediciones, preparar partidas, detectar faltantes y resolver dudas frecuentes.\n\n"
                "⚡ **Para añadir conversación y redacción generativa con GPT OSS 120B:**\n"
                "1. Obtén tu clave en [console.groq.com/keys](https://console.groq.com/keys).\n"
                "2. Agrégala en tu archivo `.env` como `GROQ_API_KEY=gsk_...`.\n\n"
                "¿En qué apartado o función de CotizaT te gustaría que te ayude hoy?"
            )
            yield f"data: {json.dumps({'texto': guia_activacion, 'finalizado': False})}\n\n"
            yield f"data: {json.dumps({'texto': '', 'finalizado': True})}\n\n"
            return

    # Preparar el contexto del sistema y los mensajes para Groq
    system_prompt = construir_system_prompt(db, ultimo_mensaje, contexto)
    historial = [{"role": "system", "content": system_prompt}]
    for m in mensajes[-10:]:  # Mantener los últimos 10 turnos de conversación
        rol = m.get("role", "user")
        contenido = m.get("content", "").strip()
        if rol in ("user", "assistant") and contenido:
            historial.append({"role": rol, "content": contenido})

    payload = {
        "model": obtener_modelo_ia(),
        "messages": historial,
        "temperature": 0.3,
        "max_tokens": 1024,
        "stream": True,
    }

    req = _ejecutar_peticion_groq(payload, api_key, stream=True)

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            for linea_bytes in response:
                linea = linea_bytes.decode("utf-8", errors="replace").strip()
                if not linea or not linea.startswith("data:"):
                    continue
                cuerpo = linea[5:].strip()
                if cuerpo == "[DONE]":
                    break
                try:
                    trozo = json.loads(cuerpo)
                    delta = trozo.get("choices", [{}])[0].get("delta", {})
                    texto = delta.get("content", "")
                    if texto:
                        yield f"data: {json.dumps({'texto': texto, 'finalizado': False})}\n\n"
                except Exception:
                    continue
        yield f"data: {json.dumps({'texto': '', 'finalizado': True})}\n\n"
    except urllib.error.HTTPError as err:
        log.error("Error HTTP al consultar Groq: %s", err)
        respuesta_local = buscar_respuesta_local(ultimo_mensaje)
        if respuesta_local:
            yield f"data: {json.dumps({'texto': respuesta_local, 'finalizado': False})}\n\n"
            yield f"data: {json.dumps({'texto': '', 'finalizado': True})}\n\n"
        else:
            error_msg = f"⚠️ Error al comunicar con la IA (HTTP {err.code})."
            yield f"data: {json.dumps({'texto': error_msg, 'finalizado': True, 'error': True})}\n\n"
    except Exception as exc:
        log.error("Fallo general en la consulta de IA: %s", exc)
        respuesta_local = buscar_respuesta_local(ultimo_mensaje)
        if respuesta_local:
            yield f"data: {json.dumps({'texto': respuesta_local, 'finalizado': False})}\n\n"
            yield f"data: {json.dumps({'texto': '', 'finalizado': True})}\n\n"
        else:
            yield f"data: {json.dumps({'texto': '⚠️ No se pudo conectar con el servicio de IA en este momento.', 'finalizado': True, 'error': True})}\n\n"


def consultar_asistente_sync(
    db: Session,
    mensajes: list[dict[str, str]],
    contexto: dict[str, Any] | None = None,
) -> str:
    """Consulta síncrona que devuelve la respuesta de texto completa."""
    api_key = obtener_clave_ia()
    ultimo_mensaje = mensajes[-1].get("content", "") if mensajes else ""

    respuesta_funcional = resolver_accion_funcional(db, ultimo_mensaje, contexto)
    if respuesta_funcional:
        return respuesta_funcional

    if not api_key:
        respuesta_local = buscar_respuesta_local(ultimo_mensaje)
        return respuesta_local or (
            "Para activar respuestas completas con IA, añade tu clave gratuita de Groq en .env (GROQ_API_KEY)."
        )

    system_prompt = construir_system_prompt(db, ultimo_mensaje, contexto)
    historial = [{"role": "system", "content": system_prompt}]
    for m in mensajes[-6:]:
        rol = m.get("role", "user")
        contenido = m.get("content", "").strip()
        if rol in ("user", "assistant") and contenido:
            historial.append({"role": rol, "content": contenido})

    payload = {
        "model": obtener_modelo_ia(),
        "messages": historial,
        "temperature": 0.3,
        "max_tokens": 1024,
        "stream": False,
    }

    req = _ejecutar_peticion_groq(payload, api_key, stream=False)

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
    except Exception as exc:
        log.error("Fallo en consulta síncrona de IA: %s", exc)
        respuesta_local = buscar_respuesta_local(ultimo_mensaje)
        return respuesta_local or (
            "⚠️ No se pudo conectar con el servicio de IA en este momento. Inténtalo de nuevo."
        )


# ---------------------------------------------------------------------------
# Asistentes Específicos (Redacción Técnica y Estructura)
# ---------------------------------------------------------------------------

def redactar_descripcion_partida(
    db: Session,
    titulo: str,
    categoria: str = "",
    unidad: str = "m2",
) -> str:
    """Genera una descripción técnica comercial detallada para una partida de obra."""
    titulo = titulo.strip()
    if not titulo:
        return ""

    api_key = obtener_clave_ia()
    if not api_key:
        # Generación determinista técnica según palabras clave
        return _redaccion_tecnica_fallback(titulo, unidad)

    prompt = (
        f"Redacta una especificación técnica rigurosa y comercial para una partida de presupuesto de obra.\n"
        f"Título de la partida: {titulo}\n"
        f"Unidad de medida: {unidad}\n"
        f"Categoría: {categoria or 'General'}\n\n"
        "Reglas:\n"
        "- Máximo 3 o 4 oraciones precisas.\n"
        "- Detalla preparación del soporte, materiales, mano de obra especializada, medios auxiliares y acabado.\n"
        "- No inventes precios ni cantidades.\n"
        "- No uses introducciones como 'Aquí tienes la descripción'; devuelve solo el texto de la especificación técnica."
    )

    mensajes = [{"role": "user", "content": prompt}]
    return consultar_asistente_sync(db, mensajes)


def _redaccion_tecnica_fallback(titulo: str, unidad: str) -> str:
    """Generador técnico determinista local cuando no hay conexión a internet/IA."""
    t_min = titulo.lower()
    if "porcelanato" in t_min or "ceramica" in t_min or "cerámica" in t_min or "enchap" in t_min or "piso" in t_min:
        return (
            f"Suministro e instalación de {titulo}. Incluye preparación y limpieza de la superficie soporte, "
            f"aplicación de mortero adhesivo de alta adherencia, colocación de piezas con junta nivelada, "
            f"emboquillado con pasta impermeable antimoho, limpieza final y retiro de escombros. Medido en {unidad} de superficie ejecutada."
        )
    if "pintura" in t_min or "friso" in t_min or "estuco" in t_min or "pared" in t_min:
        return (
            f"Ejecución de {titulo}. Incluye preparación previa del paramento mediante lijado y saneado, "
            f"aplicación de imprimación fijadora, manos de acabado según especificaciones de fabricante, "
            f"protección de carpinterías y elementos adyacentes con cinta de enmascarar, y limpieza final. Medido en {unidad} terminada."
        )
    if "demolicion" in t_min or "demolición" in t_min or "picado" in t_min or "desmontaje" in t_min:
        return (
            f"Trabajos de {titulo} mediante medios manuales y mecánicos. Incluye acopio de material residual, "
            f"desalojo, carga manual o mecánica y transporte de escombros a botadero autorizado, con protección de áreas colindantes. Medido en {unidad} real."
        )
    return (
        f"Ejecución completa de {titulo}. Incluye materiales necesarios, mano de obra calificada, "
        f"herramientas, medios auxiliares, pruebas de funcionamiento y limpieza final de la zona de trabajo. Totalmente terminado y medido en {unidad}."
    )
