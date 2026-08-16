"""Monitorización y diagnóstico de la operación web (E3-024).

Dos piezas, en la misma filosofía de honestidad que el resto del producto:

1. **Registro de errores no capturados.** Un middleware ASGI recoge cada
   excepción que escapa de las rutas (las que hoy terminan en un 500
   genérico), la registra en un buffer acotado **en memoria** y la vuelve a
   lanzar para no cambiar el comportamiento HTTP existente. El panel del
   operador muestra las últimas entradas agregadas por ruta + tipo + mensaje,
   con fecha del primer y del último fallo y número de ocurrencias.

   Limitación declarada, no escondida: el buffer vive en el proceso. En un
   despliegue serverless cada instancia tiene su propio contador y se pierde
   al reiniciar. Para operación seria con varias instancias habría que
   publicar los errores a un sumidero externo (p. ej. Vercel Log Drains);
   queda fuera de este bloque a propósito y el panel lo dice.

2. **Diagnóstico del despliegue.** Reutiliza los mismos chequeos que
   `/readyz` (sin duplicar la lógica) y los presenta junto a los hechos
   operativos: backend, modo efímero, head de Alembic esperado, almacenamiento,
   contador de frecuencia, exigencia de licencias y operadores configurados.

**Privacidad**: las rutas se registran sin query string (los enlaces
públicos y tokens viajan ahí) y los segmentos con forma de token se sustituyen
por ``<token>``; los mensajes se sanean igual que en ``/readyz`` para no
filtrar credenciales.
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


def capturar_excepcion(scope: dict, exc: Exception) -> None:
    """Registra una excepción no capturada sin exponer secretos."""
    metodo = str(scope.get("method") or "?").upper()
    ruta = _saneamiento_ruta(str(scope.get("path") or ""))
    REGISTRO_ERRORES.registrar(
        metodo, ruta, type(exc).__name__, _saneamiento_mensaje(exc)
    )


class RegistroErroresMiddleware:
    """Captura excepciones no manejadas y las vuelve a lanzar intactas.

    No cambia la semántica HTTP: el 500 lo sigue produciendo el servidor
    como hasta ahora. Solo deja constancia para el diagnóstico.
    """

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        try:
            await self.app(scope, receive, send)
        except Exception as exc:
            if scope.get("type") == "http":
                try:
                    capturar_excepcion(scope, exc)
                except Exception:  # pragma: no cover - el diagnóstico nunca rompe
                    pass
            raise


def diagnostico_operacion() -> dict[str, Any]:
    """Diagnóstico completo para el panel del operador (sin datos de tenant)."""
    salud = run_readiness()
    from ..storage import get_storage_backend

    try:
        storage = get_storage_backend().name
    except Exception:  # pragma: no cover - infraestructura
        storage = "no-configurado"
    rate_limit, _rate_limit_error = estado_configuracion()
    from .licencias import exigencia_licencia_activada

    errores = REGISTRO_ERRORES.ultimos()
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
            "arrancado_hace_segundos": int(
                (datetime.utcnow() - _INICIO_PROCESO).total_seconds()
            ),
            "errores_registrados": len(REGISTRO_ERRORES),
        },
        "errores": [error.to_dict() for error in errores],
        "nota_errores": (
            "El registro de errores vive en la memoria de esta instancia y se "
            "pierde al reiniciar; en despliegues serverless cada instancia "
            "guarda el suyo. Para operación seria con varias instancias, "
            "conectar un sumidero externo (p. ej. Vercel Log Drains) sería el "
            "siguiente paso y queda fuera de este bloque."
        ),
    }
