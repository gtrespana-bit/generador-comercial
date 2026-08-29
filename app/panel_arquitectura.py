"""Mapa de información del panel de operador: secciones, pestañas y rutas.

El panel había crecido sumando páginas sueltas (21 entradas en el menú) y
varias de ellas mostraban las mismas organizaciones desde ángulos distintos:
``/admin``, ``/admin/licencias``, ``/admin/clientes``, ``/admin/cobros``,
``/admin/renovaciones``, ``/admin/compras`` y ``/admin/crm`` recorrían la misma
lista de empresas. Este módulo es el **único punto de verdad** de la
navegación: aquí se decide qué secciones existen, qué pestañas tiene cada una y
a dónde van a parar las rutas antiguas.

Criterio de agrupación (una pregunta por área):

- **Hoy** — qué hay que hacer ahora mismo.
- **Clientes** — quién es el cliente y cómo lo gestiono (incluye el CRM).
- **Ingresos** — el dinero: cobros, renovaciones, compras y contratos.
- **Web** — lo que ve el público: contenido, avisos y versiones.
- **Analítica** — cómo va el producto.
- **Sistema** — operación, automatizaciones, equipo, accesos y auditoría.

Una sola pestaña visible = cada pantalla pinta lo que hay que tocar, nada más.
Las pestañas se resuelven en el servidor (``?tab=``): cada vista tiene URL
propia, se puede enlazar desde el buscador ⌘K o desde una notificación y sigue
funcionando sin JavaScript.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import parse_qs, urlsplit

#: Trazado SVG (viewBox 0 0 24 24, trazo, sin relleno) de cada icono del menú.
#: Se guardan aquí y no en las plantillas para que el sidebar se dibuje solo a
#: partir de la definición de secciones.
ICONOS: dict[str, tuple[str, ...]] = {
    "hoy": (
        "M3 3h7v7H3z",
        "M14 3h7v7h-7z",
        "M14 14h7v7h-7z",
        "M3 14h7v7H3z",
    ),
    "clientes": (
        "M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2",
        "M13 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0z",
        "M23 21v-2a4 4 0 0 0-3-3.87",
        "M16 3.13a4 4 0 0 1 0 7.75",
    ),
    "ingresos": (
        "M2 6.5A2.5 2.5 0 0 1 4.5 4h15A2.5 2.5 0 0 1 22 6.5v11A2.5 2.5 0 0 1 19.5 20h-15A2.5 2.5 0 0 1 2 17.5z",
        "M2 9.5h20",
        "M6 14.5h5",
    ),
    "web": (
        "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z",
        "M2 12h20",
        "M12 2a15 15 0 0 1 0 20 15 15 0 0 1 0-20z",
    ),
    "analitica": (
        "M18 20V10",
        "M12 20V4",
        "M6 20v-6",
    ),
    "sistema": (
        "M4 21v-7",
        "M4 10V3",
        "M12 21v-9",
        "M12 8V3",
        "M20 21v-5",
        "M20 12V3",
        "M1 14h6",
        "M9 8h6",
        "M17 16h6",
    ),
}


@dataclass(frozen=True)
class Pestana:
    """Una vista dentro de un área del panel."""

    id: str
    nombre: str
    descripcion: str = ""
    #: Módulo de `vistas_guardadas` si esta pestaña admite filtros persistidos.
    vista_modulo: str = ""

    @property
    def clave(self) -> str:
        return self.id


@dataclass(frozen=True)
class Seccion:
    """Un área del panel (un enlace del menú lateral)."""

    id: str
    nombre: str
    ruta: str
    descripcion: str
    icono: str = ""
    #: Letra del atajo «G + letra» del panel. Se declara junto al área para que
    #: añadir una sección añada también su atajo, y no haya que acordarse de
    #: editar el JavaScript a mano.
    atajo: str = ""
    pestanas: tuple[Pestana, ...] = ()

    @property
    def tiene_pestanas(self) -> bool:
        return len(self.pestanas) > 1


#: El panel completo. Añadir una página aquí es añadir su navegación, su breadcrumb
#: y su destino desde el buscador; no hay que tocar las plantillas.
SECCIONES: tuple[Seccion, ...] = (
    Seccion(
        id="hoy",
        nombre="Hoy",
        ruta="/admin",
        descripcion="Lo que necesita una decisión antes de que cierre el día.",
        icono="hoy",
        atajo="h",
    ),
    Seccion(
        id="clientes",
        nombre="Clientes",
        ruta="/admin/clientes",
        descripcion="La ficha de cada empresa: acceso, cobros, CRM y notas de gestión.",
        icono="clientes",
        atajo="c",
        pestanas=(
            Pestana(
                "directorio",
                "Directorio",
                "Todas las empresas con su plan, vencimiento e ingresos.",
                vista_modulo="clientes",
            ),
            Pestana(
                "pipeline",
                "Pipeline comercial",
                "El estado comercial de cada cliente: lead, prueba, activo, riesgo o inactivo.",
            ),
        ),
    ),
    Seccion(
        id="ingresos",
        nombre="Ingresos",
        ruta="/admin/ingresos",
        descripcion="El ciclo completo del cobro: contratos, compras, renovaciones y cobros del mes.",
        icono="ingresos",
        atajo="i",
        pestanas=(
            Pestana(
                "renovaciones",
                "Renovaciones",
                "Qué vence este mes, cuánto importa y a quién hay que empujar.",
                vista_modulo="renovaciones",
            ),
            Pestana(
                "compras",
                "Compras por revisar",
                "Comprobantes enviados por clientes: verificar y activar, o rechazar.",
                vista_modulo="compras",
            ),
            Pestana(
                "cobros",
                "Cobros del mes",
                "Licencias, compras, facturas y pagos del mes natural.",
                vista_modulo="cobros",
            ),
            Pestana(
                "contratos",
                "Contratos y licencias",
                "El registro de acceso: quién está dentro, hasta cuándo y por qué importe.",
            ),
        ),
    ),
    Seccion(
        id="web",
        nombre="Web",
        ruta="/admin/web",
        descripcion="La landing, el SEO, los avisos y el changelog, sin tocar código.",
        icono="web",
        atajo="w",
        pestanas=(
            Pestana(
                "contenido",
                "Contenido y SEO",
                "Textos de la landing y de las páginas SEO. El borrador no sale al público hasta que publicas.",
            ),
            Pestana(
                "avisos",
                "Avisos y banners",
                "Mantenimiento programado, avisos legales y anuncios con ventana de vigencia.",
            ),
            Pestana(
                "versiones",
                "Versiones",
                "Notas de versión publicadas en /novedades.",
            ),
        ),
    ),
    Seccion(
        id="analitica",
        nombre="Analítica",
        ruta="/admin/analitica",
        descripcion="Embudo, retención, cohes y uso de funciones medidos en el servidor.",
        icono="analitica",
        atajo="a",
    ),
    Seccion(
        id="sistema",
        nombre="Sistema",
        ruta="/admin/sistema",
        descripcion="Operación, automatizaciones, datos, equipo, accesos y auditoría del panel.",
        icono="sistema",
        atajo="s",
        pestanas=(
            Pestana(
                "estado",
                "Estado del servicio",
                "Los mismos chequeos de /readyz, con respaldo, correo y errores del proceso.",
            ),
            Pestana(
                "automatizaciones",
                "Automatizaciones",
                "Las reglas que corren por cron y su efecto hoy, con disparo manual.",
                vista_modulo="automatizaciones",
            ),
            Pestana(
                "datos",
                "Salud de datos",
                "Catálogo y configuración: huecos, precios anómalos y estado del despliegue de datos.",
            ),
            Pestana(
                "equipo",
                "Equipo",
                "Quién puede administrar el panel y con qué rol.",
            ),
            Pestana(
                "accesos",
                "Flags y claves",
                "Interruptores de funcionalidad y claves de integración.",
            ),
            Pestana(
                "auditoria",
                "Auditoría",
                "Registro de cada acción tomada desde el panel.",
            ),
            Pestana(
                "correos",
                "Correos de prueba",
                "Enviar cualquier correo transaccional a un buzón real y revisarlo.",
            ),
        ),
    ),
)

#: Pestañas de la ficha de cliente. Es la única pantalla con pestañas que no
#: cuelga de un área: vive bajo ``/admin/clientes/{id}`` y sustituye a la pila
#: interminable de tarjetas que obligaba a scrollear para encontrar un dato.
FICHA_PESTANAS: tuple[Pestana, ...] = (
    Pestana(
        "resumen",
        "Resumen",
        "Qué tiene contratado, cuánto paga y desde cuándo.",
    ),
    Pestana(
        "acceso",
        "Acceso y licencias",
        "La cadena de licencias completa: conceder, renovar, recibo y suspensión.",
    ),
    Pestana(
        "cobros",
        "Cobros",
        "Compras de plan, facturas y pagos del cliente.",
    ),
    Pestana(
        "gestion",
        "CRM y notas",
        "Estado comercial, próximo contacto y notas internas del equipo.",
    ),
    Pestana(
        "actividad",
        "Actividad",
        "Últimos movimientos del cliente y acciones tomadas desde el panel.",
    ),
)


def pestana_ficha_valida(pestana: str) -> str:
    pedida = (pestana or "").strip().lower()
    for definida in FICHA_PESTANAS:
        if definida.id == pedida:
            return definida.id
    return FICHA_PESTANAS[0].id


def ficha_pestanas_panel(organizacion_id: int, activa: str) -> list[dict]:
    base = f"/admin/clientes/{int(organizacion_id)}"
    return [
        {
            "id": definida.id,
            "nombre": definida.nombre,
            "descripcion": definida.descripcion,
            "ruta": f"{base}?tab={definida.id}",
            "activa": definida.id == activa,
            "contador": 0,
            "modulo_vistas": "",
        }
        for definida in FICHA_PESTANAS
    ]


# ---------------------------------------------------------------------------
# Navegación: una sola fuente para el menú, las pestañas y el breadcrumb
# ---------------------------------------------------------------------------
#
# Todo se deriva de `SECCIONES`. Añadir un área o una pestaña ahí actualiza el
# menú, las pestañas, el breadcrumb, los atajos de teclado y el destino desde el
# que una acción devuelve al operador; no hay que tocar las plantillas.


def seccion(seccion_id: str) -> Seccion:
    for actual in SECCIONES:
        if actual.id == seccion_id:
            return actual
    raise KeyError(seccion_id)


def pestanas_de(seccion_id: str) -> tuple[Pestana, ...]:
    """Pestañas definidas para un área (tupla vacía si el área no las tiene)."""
    try:
        return seccion(seccion_id).pestanas
    except KeyError:
        return ()


def pestana_valida(seccion_id: str, pestana: str) -> str:
    """Pestaña pedida, o la primera si no existe.

    La URL de una pestaña se comparte y se guarda en favoritos; un `?tab=`
    escrito a mano o que quedó viejo no puede devolver un 404 en el panel.
    """
    pedida = (pestana or "").strip().lower()
    definidas = pestanas_de(seccion_id)
    if not pedida and definidas:
        return definidas[0].id
    for definida in definidas:
        if definida.id == pedida:
            return definida.id
    return definidas[0].id if definidas else ""


def ruta_panel(seccion_id: str, pestana: str = "") -> str:
    """URL de un área (o de una de sus pestañas)."""
    base = seccion(seccion_id).ruta
    if not pestana:
        return base
    return f"{base}?tab={pestana}"


def modulo_de_vistas(seccion_id: str, pestana: str) -> str:
    """Módulo de vistas guardadas que corresponde a una pestaña (``''`` si no admite)."""
    objetivo = (seccion_id, pestana)
    for modulo, destino in VISTAS_EN_PANEL.items():
        if destino == objetivo:
            return modulo
    return ""


def pestanas_panel(seccion_id: str, activa: str, contadores: dict | None = None) -> list[dict]:
    """Barra de pestañas del área activa, con el contador que le corresponde.

    Un área con una sola pestaña devuelve lista vacía: no se pinta barra, porque
    una pestaña única es ruido (y era uno de los defectos del panel anterior).
    """
    contadores = contadores or {}
    definidas = pestanas_de(seccion_id)
    if len(definidas) < 2:
        return []
    base = seccion(seccion_id).ruta
    salida = []
    for definida in definidas:
        salida.append({
            "id": definida.id,
            "nombre": definida.nombre,
            "descripcion": definida.descripcion,
            "ruta": f"{base}?tab={definida.id}",
            "activa": definida.id == activa,
            "contador": int(contadores.get(definida.id, 0) or 0),
            "modulo_vistas": definida.vista_modulo,
        })
    return salida


def nav_panel(contadores: dict | None = None) -> list[dict]:
    """Enlaces del menú lateral. Seis, ni uno más.

    El contador solo se muestra donde hay algo que atender (hoy Ingresos); un
    badge en cada entrada sería decoración.
    """
    contadores = contadores or {}
    return [
        {
            "id": actual.id,
            "nombre": actual.nombre,
            "ruta": actual.ruta,
            "descripcion": actual.descripcion,
            "icono": ICONOS.get(actual.icono, ()),
            "atajo": actual.atajo,
            "contador": int(contadores.get(actual.id, 0) or 0),
            "pestanas": pestanas_de(actual.id),
        }
        for actual in SECCIONES
    ]


def cabecera_panel(seccion_id: str, pestana: str = "") -> dict:
    """Título, subtítulo y breadcrumb de la pantalla.

    El breadcrumb se construye a partir del área y la pestaña para que la ficha
    de un cliente sepa «dónde está» sin que cada plantilla lo repita.
    """
    try:
        actual = seccion(seccion_id)
    except KeyError:
        return {"titulo": "Panel", "subtitulo": "", "seccion": seccion_id, "migas": []}
    migas = [{"nombre": actual.nombre, "ruta": actual.ruta}]
    titulo = actual.nombre
    subtitulo = actual.descripcion
    for definida in actual.pestanas:
        if definida.id == pestana:
            migas.append({"nombre": definida.nombre, "ruta": ruta_panel(seccion_id, definida.id)})
            titulo = definida.nombre
            subtitulo = definida.descripcion or actual.descripcion
            break
    return {
        "titulo": titulo,
        "subtitulo": subtitulo,
        "seccion": actual.id,
        "migas": migas,
        "pestanas": len(actual.pestanas),
    }


#: Módulos de vistas guardadas → (área, pestaña) que los muestra. Una vista
#: guardada deja de ser una página aparte: es un filtro con nombre que vive en
#: la barra de herramientas de su lista.
VISTAS_EN_PANEL: dict[str, tuple[str, str]] = {
    "clientes": ("clientes", "directorio"),
    "cobros": ("ingresos", "cobros"),
    "renovaciones": ("ingresos", "renovaciones"),
    "compras": ("ingresos", "compras"),
    "contratos": ("ingresos", "contratos"),
    "automatizaciones": ("sistema", "automatizaciones"),
}

#: Páginas que se fusionaron en un área con pestañas. Siguen vivas como
#: redirección: los enlaces guardados, las notificaciones y los favoritos del
#: operador no se rompen.
RUTAS_ANTIGUAS: dict[str, tuple[str, str]] = {
    "/admin/licencias": ("ingresos", "contratos"),
    "/admin/compras": ("ingresos", "compras"),
    "/admin/cobros": ("ingresos", "cobros"),
    "/admin/renovaciones": ("ingresos", "renovaciones"),
    "/admin/automatizaciones": ("sistema", "automatizaciones"),
    "/admin/operacion": ("sistema", "estado"),
    "/admin/salud-datos": ("sistema", "datos"),
    "/admin/equipo": ("sistema", "equipo"),
    "/admin/flags": ("sistema", "accesos"),
    "/admin/api-keys": ("sistema", "accesos"),
    "/admin/auditoria": ("sistema", "auditoria"),
    "/admin/emails": ("sistema", "correos"),
    "/admin/avisos": ("web", "avisos"),
    "/admin/releases": ("web", "versiones"),
    "/admin/crm": ("clientes", "pipeline"),
    "/admin/vistas": ("clientes", "directorio"),
}

#: Rutas del panel aceptadas como destino de vuelta de un formulario. Se valida
#: contra esta lista en vez de aceptar cualquier URL: un ``volver`` libre en un
#: POST es una redirección abierta hacia donde elija quien envíe el formulario.
RUTAS_PANEL: frozenset[str] = frozenset(["/admin", *(s.ruta for s in SECCIONES)])

_FICHA_RE = r"/admin/clientes/\d+"


def pestanas_de_ruta(ruta: str) -> tuple[str, ...]:
    """Identificadores de pestaña válidos para una ruta del panel."""
    for actual in SECCIONES:
        if actual.ruta == ruta:
            return tuple(definida.id for definida in actual.pestanas)
    return ()


def es_destino_panel(destino: str) -> bool:
    """Si ``destino`` es una pantalla del panel (con o sin ``?tab=``).

    Acepta solo path absoluto del propio panel: sin esquema, sin host y sin
    protocolo. Cualquier otra forma (``//evil.com``, ``http://…``) se rechaza.
    """
    texto = str(destino or "").strip()
    if not texto.startswith("/admin"):
        return False
    dividido = urlsplit(texto)
    if dividido.scheme or dividido.netloc:
        return False
    if re.fullmatch(_FICHA_RE, dividido.path):
        return True
    if dividido.path not in RUTAS_PANEL:
        return False
    parametros = parse_qs(dividido.query or "")
    pedida = (parametros.get("tab") or [""])[0].strip().lower()
    permitidas = pestanas_de_ruta(dividido.path)
    if pedida and permitidas and pedida not in permitidas:
        return False
    return True


def redireccion_de(path: str) -> str | None:
    """URL nueva que sustituye a una página antigua del panel (si la hay)."""
    anterior = RUTAS_ANTIGUAS.get(path)
    return ruta_panel(*anterior) if anterior else None
