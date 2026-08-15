"""Contadores de frecuencia compartidos entre instancias.

`AuthRateLimitMiddleware` nació con un contador en memoria del proceso. Eso
protege un servidor único, pero **no protege un despliegue serverless**: en
Vercel cada invocación puede ejecutarse en un proceso nuevo, así que el
diccionario arranca vacío una y otra vez y el límite de «5 intentos por cada 5
minutos» deja de aplicarse en la práctica. Quien quiera probar contraseñas solo
necesita que sus peticiones caigan en instancias distintas.

Este módulo separa la decisión («¿permito este intento?») de dónde se guarda la
cuenta, y añade un backend sobre Upstash Redis por API REST. Se eligió REST y no
un cliente Redis con conexión persistente porque una función serverless no puede
mantener sockets abiertos entre invocaciones, y porque evita sumar dependencias
al runtime: se usa `urllib`, igual que `app/auth.py` y `app/storage.py`.

Ventana fija por tramo temporal
-------------------------------
La clave incluye el índice de la ventana (`now // window`), de modo que:

* el contador caduca solo, sin tareas de limpieza;
* renovar el TTL con «lo que queda de esta ventana» es idempotente, así que
  basta un único viaje de ida y vuelta (`INCR` + `EXPIRE` en un pipeline);
* dos instancias distintas calculan exactamente la misma clave.

Es menos preciso que una ventana deslizante en la frontera entre tramos, pero
esa imprecisión es acotada y conocida, y a cambio no requiere sorted sets ni
scripts Lua.

Degradación
-----------
Si Upstash no responde, la petición **no se rechaza ni se acepta a ciegas**:
cae al contador en memoria, que es exactamente la protección que había antes.
Un fallo del servicio degrada la defensa, no la convierte en denegación de
servicio para todos los usuarios ni en barra libre.

Privacidad
----------
En el servicio externo no se guardan direcciones IP en claro: la clave es un
resumen SHA-256 truncado de `ruta|ip`. Es determinista entre instancias (que es
lo único que el contador necesita) pero no reconstruible.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass
import hashlib
import json
import logging
import os
from threading import Lock
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request as UrlRequest, urlopen

logger = logging.getLogger("cotizat.ratelimit")

PREFIJO_CLAVE = "cotizat:rl"


@dataclass(frozen=True)
class Decision:
    """Resultado de consultar el contador."""

    permitido: bool
    reintentar_en: int = 0


class RateLimitBackend(ABC):
    """Contador de intentos por clave lógica y ventana temporal."""

    #: Nombre corto para diagnósticos (`/readyz`).
    name = "desconocido"
    #: ¿Comparte el contador entre instancias?
    distribuido = False

    @abstractmethod
    def hit(self, identidad: str, limite: int, ventana: int) -> Decision:
        """Registra un intento y decide si se permite."""
        raise NotImplementedError


class MemoryRateLimit(RateLimitBackend):
    """Ventana deslizante en la memoria del proceso.

    Sirve para desarrollo local, para el modo escritorio y como red de
    seguridad cuando el contador distribuido no responde. No comparte estado
    entre instancias.
    """

    name = "memoria"
    distribuido = False

    def __init__(self, max_buckets: int = 10_000):
        self.max_buckets = max(1, int(max_buckets))
        self._attempts: dict[str, deque[float]] = {}
        self._lock = Lock()

    def hit(self, identidad: str, limite: int, ventana: int) -> Decision:
        now = time.monotonic()
        threshold = now - ventana
        with self._lock:
            if identidad not in self._attempts and len(self._attempts) >= self.max_buckets:
                stale = [
                    clave
                    for clave, valores in self._attempts.items()
                    if not valores or valores[-1] <= threshold
                ]
                for clave in stale:
                    self._attempts.pop(clave, None)
                if len(self._attempts) >= self.max_buckets:
                    self._attempts.pop(next(iter(self._attempts)))
            attempts = self._attempts.setdefault(identidad, deque())
            while attempts and attempts[0] <= threshold:
                attempts.popleft()
            if len(attempts) >= limite:
                return Decision(False, max(1, int(ventana - (now - attempts[0]))))
            attempts.append(now)
            return Decision(True)


class UpstashRateLimit(RateLimitBackend):
    """Contador compartido sobre Upstash Redis por API REST.

    Se usa la API REST porque una función serverless no conserva conexiones
    entre invocaciones. Cada comprobación es un `INCR` más un `EXPIRE` enviados
    en un solo pipeline, es decir un único viaje de ida y vuelta.
    """

    name = "upstash"
    distribuido = True

    def __init__(
        self,
        url: str,
        token: str,
        respaldo: RateLimitBackend | None = None,
        timeout: int = 3,
    ):
        limpia = str(url or "").strip().rstrip("/")
        partes = urlparse(limpia)
        if partes.scheme != "https" or not partes.netloc:
            raise ValueError(
                "UPSTASH_REDIS_REST_URL debe ser una URL https completa."
            )
        if not str(token or "").strip():
            raise ValueError("Falta UPSTASH_REDIS_REST_TOKEN.")
        self.url = limpia
        self._token = str(token).strip()
        # El respaldo conserva la protección local si Upstash falla.
        self.respaldo = respaldo or MemoryRateLimit()
        # Un timeout corto es deliberado: el contador no debe convertirse en el
        # componente que decide cuánto tarda un inicio de sesión.
        self.timeout = max(1, int(timeout))

    @staticmethod
    def _clave(identidad: str, ventana: int, ahora: float) -> tuple[str, int]:
        """Clave de la ventana actual y segundos que le quedan."""
        indice = int(ahora // ventana)
        # La IP no viaja en claro a un servicio de terceros.
        digest = hashlib.sha256(identidad.encode("utf-8")).hexdigest()[:32]
        restante = max(1, int((indice + 1) * ventana - ahora))
        return f"{PREFIJO_CLAVE}:{digest}:{indice}", restante

    def _pipeline(self, comandos: list[list[str]]) -> list[int]:
        cuerpo = json.dumps(comandos).encode("utf-8")
        request = UrlRequest(
            f"{self.url}/pipeline",
            data=cuerpo,
            headers={
                "Authorization": f"Bearer {self._token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "CotizaT/1.0",
            },
            method="POST",
        )
        with urlopen(request, timeout=self.timeout) as respuesta:  # noqa: S310
            crudo = respuesta.read(64 * 1024)
        datos = json.loads(crudo.decode("utf-8"))
        if not isinstance(datos, list) or not datos:
            raise ValueError("Upstash devolvió una respuesta inesperada.")
        resultados: list[int] = []
        for entrada in datos:
            if not isinstance(entrada, dict) or "error" in entrada:
                raise ValueError("Upstash devolvió un error en el pipeline.")
            resultados.append(int(entrada.get("result") or 0))
        return resultados

    def hit(self, identidad: str, limite: int, ventana: int) -> Decision:
        ahora = time.time()
        clave, restante = self._clave(identidad, ventana, ahora)
        try:
            resultados = self._pipeline(
                [["INCR", clave], ["EXPIRE", clave, str(restante)]]
            )
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            # No se puede fallar abierto (sería quitar el límite justo cuando
            # alguien satura el servicio) ni cerrado (dejaría a todo el mundo
            # sin poder entrar por una caída de un tercero). Se degrada a la
            # protección que existía antes de este módulo.
            logger.warning(
                "Contador distribuido no disponible (%s); se usa el contador local.",
                type(exc).__name__,
            )
            return self.respaldo.hit(identidad, limite, ventana)
        usados = resultados[0] if resultados else 0
        if usados > limite:
            return Decision(False, restante)
        return Decision(True)


def _entorno(nombre: str) -> str:
    return str(os.environ.get(nombre, "")).strip()


def build_rate_limiter() -> RateLimitBackend:
    """Construye el contador según el entorno.

    Con `UPSTASH_REDIS_REST_URL` y `UPSTASH_REDIS_REST_TOKEN` definidas se usa
    el contador compartido; en cualquier otro caso, el de memoria. Una
    configuración inválida no impide arrancar: se registra y se degrada, porque
    dejar la aplicación caída es peor que dejarla con el límite anterior.
    """
    url = _entorno("UPSTASH_REDIS_REST_URL")
    token = _entorno("UPSTASH_REDIS_REST_TOKEN")
    if not url and not token:
        return MemoryRateLimit()
    try:
        return UpstashRateLimit(url, token)
    except ValueError as exc:
        logger.warning("Contador distribuido mal configurado (%s); se usa memoria.", exc)
        return MemoryRateLimit()


def estado_configuracion() -> tuple[str, str | None]:
    """Describe el contador para `/readyz`.

    Devuelve `(estado, error)`. El error solo se emite cuando el despliegue
    exige explícitamente un contador distribuido con
    `COTIZAT_REQUIRE_DISTRIBUTED_RATELIMIT=true`.
    """
    exigido = _entorno("COTIZAT_REQUIRE_DISTRIBUTED_RATELIMIT").lower() in {
        "1", "true", "yes", "on",
    }
    url = _entorno("UPSTASH_REDIS_REST_URL")
    token = _entorno("UPSTASH_REDIS_REST_TOKEN")
    if url or token:
        try:
            UpstashRateLimit(url, token)
        except ValueError as exc:
            return "mal-configurado", (
                f"El contador de frecuencia distribuido está incompleto: {exc}"
            )
        return "distribuido:upstash", None
    if exigido:
        return "memoria", (
            "COTIZAT_REQUIRE_DISTRIBUTED_RATELIMIT exige un contador compartido, "
            "pero faltan UPSTASH_REDIS_REST_URL y UPSTASH_REDIS_REST_TOKEN. "
            "Con varias instancias el límite de Auth no se aplica de verdad."
        )
    return "memoria", None
