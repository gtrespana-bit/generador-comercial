"""Los comandos de la paleta (⌘K): hacer, no solo buscar.

La paleta nació como buscador y se quedó a medias: encontraba la ficha de un
cliente, pero para cualquier acción había que cerrarla, navegar y buscar el
botón. Aquí vive el catálogo de lo que se puede lanzar desde el teclado.

Tres reglas, y ninguna es negociable:

- **Solo rutas que existen.** Cada comando apunta a una ruta real del panel
  («ir a» = GET, «acción» = POST). Nada de lógica nueva escondida en el
  catálogo: si un comando puede hacer algo, la ruta ya lo hacía antes.
- **El rol filtra la lista**, igual que el menú. Y el servidor vuelve a
  comprobarlo al ejecutar: la paleta es una comodidad, no una puerta.
- **Lo que cambia estado se confirma.** Un «Enter» nunca envía un correo a los
  clientes: los comandos con `confirmacion` piden un segundo Enter y la paleta
  enseña exactamente qué va a pasar.

Añadir un comando es añadir una entrada a `COMANDOS`; la paleta y el endpoint
se enteran solos.
"""
from __future__ import annotations

from dataclasses import dataclass, field

#: Todos los roles del panel (el mismo conjunto que usa el menú).
TODOS = ("superadmin", "admin", "soporte", "analista")


@dataclass(frozen=True)
class Comando:
    """Una entrada de la paleta.

    ``url`` es una ruta existente del panel. ``metodo`` distingue navegar
    (``GET``) de ejecutar (``POST``). En los ``POST``, ``confirmacion`` es el
    texto que se enseña antes de enviar: describe el efecto real, no un «¿seguro?».
    """

    id: str
    titulo: str
    descripcion: str
    url: str
    grupo: str = "Ir a"
    metodo: str = "GET"
    roles: tuple[str, ...] = TODOS
    confirmacion: str = ""
    #: Palabras extra para encontrar el comando escribiendo otra cosa.
    alias: tuple[str, ...] = field(default_factory=tuple)

    @property
    def es_accion(self) -> bool:
        return self.metodo.upper() == "POST"

    def como_dict(self) -> dict:
        return {
            "id": self.id,
            "titulo": self.titulo,
            "descripcion": self.descripcion,
            "url": self.url,
            "grupo": self.grupo,
            "metodo": self.metodo,
            "accion": self.es_accion,
            "confirmacion": self.confirmacion,
        }


#: El catálogo. Orden = orden en la paleta: primero lo del día, luego el dinero,
#: luego lo que se atiende, y al final las acciones que mandan correos.
COMANDOS: tuple[Comando, ...] = (
    Comando(
        id="hoy-decisiones",
        titulo="Hoy · lo que espera una decisión",
        descripcion="La agenda del día: vencimientos, compras y avisos.",
        url="/admin",
        alias=("agenda", "pendientes", "dia"),
    ),
    Comando(
        id="compras-revisar",
        titulo="Compras por revisar",
        descripcion="Comprobantes enviados por clientes, sin verificar.",
        url="/admin/ingresos?tab=compras",
        roles=("superadmin", "admin"),
        alias=("comprobantes", "pagos", "stripe"),
    ),
    Comando(
        id="renovaciones",
        titulo="Renovaciones del mes",
        descripcion="Qué vence, por cuánto y a quién hay que empujar.",
        url="/admin/ingresos?tab=renovaciones",
        roles=("superadmin", "admin"),
        alias=("vence", "vencimientos", "renovar"),
    ),
    Comando(
        id="cobros",
        titulo="Cobros del mes y movimiento del MRR",
        descripcion="El libro del mes y de dónde sale el cambio del recurrente.",
        url="/admin/ingresos?tab=cobros",
        roles=("superadmin", "admin"),
        alias=("mrr", "facturado", "ingresos"),
    ),
    Comando(
        id="soporte",
        titulo="Buzón de soporte",
        descripcion="Lo que escriben clientes y visitantes, sin atender.",
        url="/admin/clientes?tab=soporte",
        roles=("superadmin", "admin", "soporte"),
        alias=("mensajes", "buzon", "ayuda"),
    ),
    Comando(
        id="riesgo-baja",
        titulo="Clientes en riesgo de baja",
        descripcion="Pagan pero no usan el producto en los últimos días.",
        url="/admin/analitica?tab=clientes",
        alias=("churn", "riesgo", "baja"),
    ),
    Comando(
        id="errores",
        titulo="Estado del servicio y errores internos",
        descripcion="Los mismos chequeos de /readyz y los fallos sin resolver.",
        url="/admin/sistema?tab=estado",
        roles=("superadmin",),
        alias=("readyz", "500", "fallos", "salud"),
    ),
    Comando(
        id="auditoria",
        titulo="Auditoría del panel",
        descripcion="Cada acción tomada desde el panel, con quién y cuándo.",
        url="/admin/sistema?tab=auditoria",
        roles=("superadmin", "admin", "soporte", "analista"),
        alias=("registro", "log", "quien hizo"),
    ),
    Comando(
        id="automatizaciones",
        titulo="Automatizaciones",
        descripcion="Las reglas del cron, su efecto de hoy y el disparo manual.",
        url="/admin/sistema?tab=automatizaciones",
        roles=("superadmin", "admin"),
        alias=("cron", "reglas"),
    ),
    Comando(
        id="avisos-vencimiento",
        titulo="Enviar avisos de vencimiento",
        descripcion="Correo a los clientes cuyo acceso vence en 15 días.",
        url="/admin/automatizaciones/avisos_vencimiento/ejecutar",
        grupo="Acción",
        metodo="POST",
        roles=("superadmin", "admin"),
        confirmacion=(
            "Se enviarán correos a los clientes que vencen en los próximos 15 "
            "días. No se repite el mismo día."
        ),
        alias=("avisar", "vence", "correo"),
    ),
    Comando(
        id="recordatorios",
        titulo="Ejecutar recordatorios de vencimiento",
        descripcion="Aviso a 5 días y última llamada a 1 día, una vez por hito.",
        url="/admin/automatizaciones/recordatorios/ejecutar",
        grupo="Acción",
        metodo="POST",
        roles=("superadmin", "admin"),
        confirmacion=(
            "Se enviarán los recordatorios pendientes de cada licencia. "
            "Cada hito se avisa una sola vez."
        ),
        alias=("recordar", "ultima llamada"),
    ),
)


def _permite(rol: str | None, roles: tuple[str, ...]) -> bool:
    """Mismo criterio que el menú: sin rol declarado no se filtra nada.

    No es la autorización —esa la hace ``exigir_rol`` al ejecutar— sino la
    presentación: enseñar un comando que va a rebotar sería ruido.
    """
    if not roles:
        return True
    if not rol:
        return True
    return rol.strip().lower() in {r.lower() for r in roles}


def comandos_panel(rol: str | None = None) -> list[dict]:
    """Comandos visibles para ese rol, en el orden del catálogo."""
    return [c.como_dict() for c in COMANDOS if _permite(rol, c.roles)]


def _normalizar(texto: str) -> str:
    """Minúsculas y sin acentos: «buzón» y «buzon» deben encontrar lo mismo."""
    reemplazos = str.maketrans("áéíóúüñ", "aeiouun")
    return (texto or "").strip().lower().translate(reemplazos)


def buscar_comandos(rol: str | None, q: str = "") -> list[dict]:
    """Comandos que encajan con lo escrito, por título, descripción o alias."""
    visibles = [c for c in COMANDOS if _permite(rol, c.roles)]
    consulta = _normalizar(q)
    if not consulta:
        return [c.como_dict() for c in visibles]
    encontrados = []
    for comando in visibles:
        pajar = _normalizar(
            " ".join([comando.titulo, comando.descripcion, comando.id, *comando.alias])
        )
        if consulta in pajar:
            encontrados.append(comando.como_dict())
    return encontrados
