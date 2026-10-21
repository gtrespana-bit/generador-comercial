"""Monitorización y diagnóstico de la operación web (E3-024).

Dos piezas, en la misma filosofía de honestidad que el resto del producto:

1. **Registro de errores no capturados.** Un middleware ASGI recoge cada
   excepción que escapa de las rutas (las que hoy terminan en un 500
   genérico), la registra en un buffer acotado **en memoria** y la vuelve a
   lanzar para no cambiar el comportamiento HTTP existente. El panel del
   operador muestra las últimas entradas agregadas por ruta + tipo + mensaje,
   con fecha del primer y del último fallo y número de ocurrencias.

   El buffer en memoria sigue siendo la vista instantánea del proceso,
   pero desde la Fase 0.2 de la hoja de ruta ya no es el único sumidero:
   el middleware también persiste cada huella —con su traza— en la tabla
   ``errores_internos`` mediante ``app/services/errores_internos.py``
   (best-effort, solo cuando ya hay un 500, con correo al titular ante
   huellas nuevas). El panel lee de la base cuando puede y cae a este
   buffer con la nota honesta de siempre si la tabla aún no está.

2. **Diagnóstico del despliegue.** Reutiliza los mismos chequeos que
   `/readyz` (sin duplicar la lógica) y los presenta junto a los hechos
   operativos: backend, modo efímero, head de Alembic esperado, almacenamiento,
   contador de frecuencia, exigencia de licencias y operadores configurados.

**Privacidad**: las rutas se registran sin query string (los enlaces
públicos y tokens viajan ahí) y los segmentos con forma de token se sustituyen
por ``<token>``; los mensajes se sanean igual que en ``/readyz`` para no
filtrar credenciales. Para seguimiento, el registro durable conserva solo el
nombre y email de la identidad verificada más reciente; los errores anónimos
no guardan identidad.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ..database import (
    DATABASE_BACKEND,
    DATABASE_IS_SQLITE,
    DATOS_EFIMEROS,
    EXPECTED_ALEMBIC_HEAD,
)
from ..health import run_readiness
from ..operadores import operadores_configurados
from ..ratelimit import estado_configuracion

MAXIMO_ERRORES = 200
MAXIMO_POR_PAGINA = 50
_INICIO_PROCESO = datetime.utcnow()


def _saneamiento_mensaje(exc: Exception) -> str:
    """Mensaje sin credenciales: se corta lo que siga a user:pass en URLs."""
    texto = str(exc) or exc.__class__.__name__
    if "://" in texto and "@" in texto:
        texto = texto.split("@", 1)[-1]
    return texto[:300]


def _saneamiento_ruta(ruta: str) -> str:
    """Ruta sin query string y con los segmentos-token sustituidos."""
    valor = str(ruta or "").split("?", 1)[0]
    if not valor.startswith("/"):
        valor = "/" + valor
    partes = []
    for segmento in valor.split("/"):
        if len(segmento) >= 28 and all(
            c.isalnum() or c in "_-" for c in segmento
        ):
            segmento = "<token>"
        partes.append(segmento)
    saneado = "/".join(partes)[:160]
    return saneado or "/"


@dataclass(frozen=True)
class ErrorRegistrado:
    """Una entrada agregada del registro de errores."""

    metodo: str
    ruta: str
    tipo: str
    mensaje: str
    primera_vez: str
    ultima_vez: str
    ocurrencias: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "metodo": self.metodo,
            "ruta": self.ruta,
            "tipo": self.tipo,
            "mensaje": self.mensaje,
            "primera_vez": self.primera_vez,
            "ultima_vez": self.ultima_vez,
            "ocurrencias": self.ocurrencias,
        }


class RegistroErrores:
    """Buffer acotado en memoria de excepciones no capturadas.

    Agrega por (método, ruta, tipo, mensaje): repetir el mismo fallo solo
    incrementa ``ocurrencias`` y actualiza la última vez. Es un singleton del
    proceso; su límite evita que un fallo en bucle agote la memoria.
    """

    def __init__(self, maximo: int = MAXIMO_ERRORES) -> None:
        self.maximo = maximo
        self._indice: dict[tuple[str, str, str, str], dict[str, Any]] = {}
        self._orden: deque[tuple[str, str, str, str]] = deque()

    def registrar(
        self,
        metodo: str,
        ruta: str,
        tipo: str,
        mensaje: str,
        ahora: datetime | None = None,
    ) -> None:
        ahora = ahora or datetime.utcnow()
        clave = (str(metodo).upper()[:10], ruta, tipo, mensaje)
        entrada = self._indice.get(clave)
        if entrada is None:
            entrada = {
                "metodo": clave[0],
                "ruta": clave[1],
                "tipo": clave[2],
                "mensaje": clave[3],
                "primera_vez": ahora,
                "ultima_vez": ahora,
                "ocurrencias": 1,
            }
            self._indice[clave] = entrada
            self._orden.append(clave)
            while len(self._orden) > self.maximo:
                antigua = self._orden.popleft()
                self._indice.pop(antigua, None)
        else:
            entrada["ultima_vez"] = ahora
            entrada["ocurrencias"] += 1
            # El fallo vuelve al final de la lista de más recientes.
            try:
                self._orden.remove(clave)
            except ValueError:  # pragma: no cover - no debería pasar
                pass
            self._orden.append(clave)

    def ultimos(self, limite: int = MAXIMO_POR_PAGINA) -> list[ErrorRegistrado]:
        claves = list(reversed(self._orden))[:limite]
        return [
            ErrorRegistrado(
                metodo=self._indice[c]["metodo"],
                ruta=self._indice[c]["ruta"],
                tipo=self._indice[c]["tipo"],
                mensaje=self._indice[c]["mensaje"],
                primera_vez=self._indice[c]["primera_vez"].strftime("%d/%m/%Y %H:%M UTC"),
                ultima_vez=self._indice[c]["ultima_vez"].strftime("%d/%m/%Y %H:%M UTC"),
                ocurrencias=self._indice[c]["ocurrencias"],
            )
            for c in claves
        ]

    def limpiar(self) -> None:
        self._indice.clear()
        self._orden.clear()

    def __len__(self) -> int:
        return len(self._orden)


#: Singleton del proceso; los tests pueden sustituirlo por una instancia nueva.
REGISTRO_ERRORES = RegistroErrores()


def datos_error(scope: dict, exc: Exception) -> dict:
    """Los hechos saneados de una excepción, para memoria y para BD.

    La traza (redactada y recortada en ``errores_internos.traza_de``) solo
    viaja a la base: el buffer en memoria conserva la forma ligera de
    siempre (tipo + mensaje), que es lo que cabe en un vistazo rápido.
    """
    from .errores_internos import traza_de

    # El state lo comparten los middlewares ASGI y las dependencias ya
    # ejecutadas. Solo guardamos datos de la identidad validada (nunca los
    # parámetros del formulario); un fallo antes del login queda anónimo.
    state = scope.get("state") or {}
    identity = state.get("supabase_identity") if isinstance(state, dict) else None
    usuario = state.get("usuario") if isinstance(state, dict) else None
    email = str(
        getattr(identity, "email", "") or getattr(usuario, "email", "") or ""
    ).strip()[:254]
    nombre = str(
        getattr(identity, "name", "") or getattr(usuario, "nombre", "") or ""
    ).strip()[:200]
    return {
        "metodo": str(scope.get("method") or "?").upper(),
        "ruta": _saneamiento_ruta(str(scope.get("path") or "")),
        "tipo": type(exc).__name__,
        "mensaje": _saneamiento_mensaje(exc),
        "usuario_email": email,
        "usuario_nombre": nombre,
        "traza": traza_de(exc),
        "ahora": datetime.utcnow(),
    }


def capturar_excepcion(scope: dict, exc: Exception) -> dict:
    """Registra una excepción no capturada sin exponer secretos.

    Devuelve los datos saneados por si el llamante quiere persistirlos
    (el middleware los pasa a ``errores_internos.persistir_y_avisar``).
    """
    datos = datos_error(scope, exc)
    REGISTRO_ERRORES.registrar(
        datos["metodo"],
        datos["ruta"],
        datos["tipo"],
        datos["mensaje"],
        ahora=datos["ahora"],
    )
    return datos


class RegistroErroresMiddleware:
    """Captura excepciones no manejadas y las vuelve a lanzar intactas.

    No cambia la semántica HTTP: el 500 lo sigue produciendo el servidor
    como hasta ahora. Solo deja constancia para el diagnóstico: en el
    buffer en memoria de siempre y, desde la Fase 0.2, en la tabla
    ``errores_internos`` vía un hilo (la persistencia es síncrona y no
    debe bloquear el bucle; solo ocurre cuando ya hay un 500).
    """

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        try:
            await self.app(scope, receive, send)
        except Exception as exc:
            if scope.get("type") == "http":
                try:
                    datos = capturar_excepcion(scope, exc)
                    from .errores_internos import (
                        persistir_y_avisar,
                        registro_bd_activado,
                    )

                    if registro_bd_activado():
                        from starlette.concurrency import run_in_threadpool

                        await run_in_threadpool(persistir_y_avisar, datos)
                except Exception:  # pragma: no cover - el diagnóstico nunca rompe
                    pass
            raise


def diagnostico_operacion(db=None) -> dict[str, Any]:
    """Diagnóstico completo para el panel del operador (sin datos de tenant).

    Con ``db`` (sesión de operador) la lista de errores viene de la tabla
    durable ``errores_internos`` —todas las instancias, con traza y
    gestión de resueltos—. Sin sesión, o si la tabla aún no existe (la
    ventana entre desplegar el código y correr la migración), se cae al
    buffer en memoria de siempre y la nota lo dice sin disimulo.
    """
    salud = run_readiness()
    from ..config import resumen_configuracion
    from ..storage import get_storage_backend

    try:
        storage = get_storage_backend().name
    except Exception:  # pragma: no cover - infraestructura
        storage = "no-configurado"
    rate_limit, _rate_limit_error = estado_configuracion()
    from .licencias import exigencia_licencia_activada

    errores: list[dict[str, Any]] = [
        error.to_dict() for error in REGISTRO_ERRORES.ultimos()
    ]
    errores_fuente = "memoria"
    errores_registrados = len(REGISTRO_ERRORES)
    nota_errores = (
        "El registro de errores vive en la memoria de esta instancia y se "
        "pierde al reiniciar; en despliegues serverless cada instancia "
        "guarda el suyo."
    )
    if db is not None:
        from .errores_internos import (
            contar_errores,
            listar_errores_recientes,
            registro_bd_activado,
        )

        try:
            errores = listar_errores_recientes(db)
            errores_registrados = contar_errores(db)
            errores_fuente = "bd"
            nota_errores = (
                "Registro durable en la base de datos (todas las "
                "instancias): una fila por huella con la traza de la "
                "última ocurrencia. Una huella nueva —o una que reaparece "
                "tras marcarla resuelta— avisa por correo al buzón de "
                "avisos; el cron diario resume las activas y poda las "
                "resueltas antiguas."
            )
            if not registro_bd_activado():
                nota_errores += (
                    " La persistencia está apagada (COTIZAT_ERRORES_BD): "
                    "lo que ves es el histórico guardado, sin entradas "
                    "nuevas."
                )
        except Exception:
            db.rollback()
            nota_errores += (
                " No se pudo leer la tabla durable (¿migración "
                "«errores_internos» pendiente de aplicar?)."
            )

    return {
        "salud": salud.to_dict(),
        "hechos": {
            "backend": DATABASE_BACKEND,
            "efimero": bool(DATOS_EFIMEROS),
            "head_esperado": EXPECTED_ALEMBIC_HEAD,
            "storage": storage,
            "rate_limit": rate_limit,
            "licencias_exigidas": (
                "no-aplica (escritorio)"
                if DATABASE_IS_SQLITE
                else ("exigida" if exigencia_licencia_activada() else "no-exigida")
            ),
            "operadores": sorted(operadores_configurados()),
            "configuracion": resumen_configuracion(),
            "arrancado_hace_segundos": int(
                (datetime.utcnow() - _INICIO_PROCESO).total_seconds()
            ),
            "errores_registrados": errores_registrados,
        },
        "errores": errores,
        "errores_fuente": errores_fuente,
        "nota_errores": nota_errores,
    }
