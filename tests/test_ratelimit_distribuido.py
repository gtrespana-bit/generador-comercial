"""El límite de Auth debe sobrevivir a un despliegue con varias instancias.

Estas pruebas cubren el fallo real que motivó `app/ratelimit.py`: en Vercel
cada invocación puede ejecutarse en un proceso nuevo, así que un contador en
memoria arranca vacío una y otra vez y el límite de `/registro` o `/acceso`
deja de aplicarse. La prueba central (`test_dos_instancias_comparten...`) lo
demuestra por contraste: el mismo escenario falla con el contador de memoria y
se sostiene con el distribuido.

El servicio se simula con un servidor HTTP real, no con un doble en memoria,
para ejercitar de verdad la construcción del pipeline, las cabeceras y el
parseo de la respuesta.
"""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from app.ratelimit import (
    MemoryRateLimit,
    UpstashRateLimit,
    build_rate_limiter,
    estado_configuracion,
)
from app.security import AuthRateLimitMiddleware


class _RedisFalso(BaseHTTPRequestHandler):
    """Implementa lo justo de la API REST de Upstash: INCR y EXPIRE."""

    almacen: dict[str, int] = {}
    expiraciones: dict[str, int] = {}
    peticiones: list[dict] = []
    autorizaciones: list[str] = []
    fallar = False

    def log_message(self, *args):  # silencia el log del servidor de pruebas
        pass

    def do_POST(self):  # noqa: N802 (nombre impuesto por BaseHTTPRequestHandler)
        longitud = int(self.headers.get("Content-Length", "0"))
        cuerpo = json.loads(self.rfile.read(longitud).decode("utf-8"))
        type(self).peticiones.append(cuerpo)
        type(self).autorizaciones.append(self.headers.get("Authorization", ""))

        if type(self).fallar:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"{}")
            return

        respuesta = []
        for comando in cuerpo:
            nombre = comando[0].upper()
            clave = comando[1]
            if nombre == "INCR":
                type(self).almacen[clave] = type(self).almacen.get(clave, 0) + 1
                respuesta.append({"result": type(self).almacen[clave]})
            elif nombre == "EXPIRE":
                type(self).expiraciones[clave] = int(comando[2])
                respuesta.append({"result": 1})
            else:  # pragma: no cover - no se usan otros comandos
                respuesta.append({"error": f"comando no soportado: {nombre}"})

        crudo = json.dumps(respuesta).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(crudo)))
        self.end_headers()
        self.wfile.write(crudo)


@pytest.fixture
def redis_falso():
    _RedisFalso.almacen = {}
    _RedisFalso.expiraciones = {}
    _RedisFalso.peticiones = []
    _RedisFalso.autorizaciones = []
    _RedisFalso.fallar = False

    servidor = HTTPServer(("127.0.0.1", 0), _RedisFalso)
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    puerto = servidor.server_address[1]
    try:
        yield {
            "url": f"http://127.0.0.1:{puerto}",
            "handler": _RedisFalso,
            "servidor": servidor,
        }
    finally:
        servidor.shutdown()
        servidor.server_close()


def _limitador(redis_falso, **kwargs) -> UpstashRateLimit:
    """Construye el backend saltando la validación de https del constructor.

    El servidor de pruebas es http en localhost; exigir https es correcto en
    producción (y se prueba aparte en `test_rechaza_url_no_https`).
    """
    limitador = UpstashRateLimit.__new__(UpstashRateLimit)
    limitador.url = redis_falso["url"]
    limitador._token = "token-de-prueba"
    limitador.respaldo = kwargs.get("respaldo") or MemoryRateLimit()
    limitador.timeout = kwargs.get("timeout", 3)
    return limitador


def endpoint(request):  # noqa: ARG001
    return PlainTextResponse("ok")


def _app(backend):
    return Starlette(
        routes=[Route("/registro", endpoint, methods=["POST"])],
        middleware=[
            Middleware(
                AuthRateLimitMiddleware,
                limits={"/registro": 3},
                window_seconds=300,
                backend=backend,
            )
        ],
    )


def test_dos_instancias_comparten_el_contador(redis_falso):
    """El fallo real: dos procesos deben sumar intentos, no empezar de cero.

    Se reparten 4 intentos entre dos aplicaciones distintas, cada una con su
    propio middleware, igual que dos invocaciones serverless. Con el límite en
    3, el cuarto debe rechazarse aunque caiga en la instancia que solo ha visto
    un intento.
    """
    instancia_a = _app(_limitador(redis_falso))
    instancia_b = _app(_limitador(redis_falso))

    with TestClient(instancia_a) as cliente_a, TestClient(instancia_b) as cliente_b:
        assert cliente_a.post("/registro").status_code == 200
        assert cliente_b.post("/registro").status_code == 200
        assert cliente_a.post("/registro").status_code == 200
        # Cuarto intento: la instancia B solo ha atendido uno, pero el contador
        # compartido ya suma tres.
        bloqueado = cliente_b.post("/registro")

    assert bloqueado.status_code == 429
    assert int(bloqueado.headers["Retry-After"]) > 0


def test_el_contador_en_memoria_no_habria_detectado_el_abuso():
    """Contraste que justifica el módulo: sin backend compartido no hay límite.

    Es el mismo escenario de la prueba anterior. Si algún día esta prueba
    empieza a fallar porque el cuarto intento se bloquea, significaría que la
    de arriba ya no demuestra nada.
    """
    instancia_a = _app(MemoryRateLimit())
    instancia_b = _app(MemoryRateLimit())

    with TestClient(instancia_a) as cliente_a, TestClient(instancia_b) as cliente_b:
        assert cliente_a.post("/registro").status_code == 200
        assert cliente_b.post("/registro").status_code == 200
        assert cliente_a.post("/registro").status_code == 200
        # Con contadores por proceso el abuso pasa desapercibido.
        assert cliente_b.post("/registro").status_code == 200


def test_respeta_el_limite_exacto(redis_falso):
    """Se permiten `limite` intentos y se rechaza el siguiente."""
    limitador = _limitador(redis_falso)
    for _ in range(5):
        assert limitador.hit("/acceso|192.0.2.10", 5, 300).permitido
    decision = limitador.hit("/acceso|192.0.2.10", 5, 300)
    assert not decision.permitido
    assert decision.reintentar_en > 0


def test_cada_ip_y_ruta_tienen_su_propio_contador(redis_falso):
    """Agotar una IP no puede bloquear a las demás ni a otras rutas."""
    limitador = _limitador(redis_falso)
    for _ in range(3):
        limitador.hit("/acceso|192.0.2.10", 3, 300)
    assert not limitador.hit("/acceso|192.0.2.10", 3, 300).permitido
    assert limitador.hit("/acceso|198.51.100.7", 3, 300).permitido
    assert limitador.hit("/registro|192.0.2.10", 3, 300).permitido


def test_la_ip_no_viaja_en_claro_al_servicio_externo(redis_falso):
    """La clave es un resumen: el tercero no recibe direcciones IP."""
    limitador = _limitador(redis_falso)
    limitador.hit("/acceso|203.0.113.45", 5, 300)

    enviado = json.dumps(redis_falso["handler"].peticiones)
    assert "203.0.113.45" not in enviado
    assert "cotizat:rl:" in enviado


def test_fija_caducidad_para_no_acumular_claves(redis_falso):
    """Sin EXPIRE, cada ventana dejaría una clave residual para siempre."""
    limitador = _limitador(redis_falso)
    limitador.hit("/acceso|192.0.2.10", 5, 300)

    expiraciones = redis_falso["handler"].expiraciones
    assert expiraciones, "No se fijó ninguna caducidad."
    for segundos in expiraciones.values():
        assert 0 < segundos <= 300


def test_envia_el_token_como_bearer(redis_falso):
    limitador = _limitador(redis_falso)
    limitador.hit("/acceso|192.0.2.10", 5, 300)
    assert redis_falso["handler"].autorizaciones == ["Bearer token-de-prueba"]


def test_un_solo_viaje_por_intento(redis_falso):
    """INCR y EXPIRE van en un pipeline: el login no paga dos latencias."""
    limitador = _limitador(redis_falso)
    limitador.hit("/acceso|192.0.2.10", 5, 300)

    peticiones = redis_falso["handler"].peticiones
    assert len(peticiones) == 1
    assert [c[0].upper() for c in peticiones[0]] == ["INCR", "EXPIRE"]


def test_si_el_servicio_falla_degrada_al_contador_local(redis_falso):
    """Una caída del tercero no puede quitar el límite ni tumbar el acceso."""
    respaldo = MemoryRateLimit()
    limitador = _limitador(redis_falso, respaldo=respaldo)
    redis_falso["handler"].fallar = True

    # Sigue limitando (no falla abierto)...
    for _ in range(3):
        assert limitador.hit("/acceso|192.0.2.10", 3, 300).permitido
    assert not limitador.hit("/acceso|192.0.2.10", 3, 300).permitido
    # ...y no bloquea a quien no ha consumido intentos (no falla cerrado).
    assert limitador.hit("/acceso|198.51.100.7", 3, 300).permitido


def test_si_el_servicio_no_responde_no_propaga_la_excepcion(redis_falso):
    """Un puerto muerto no puede convertirse en un 500 en el login."""
    respaldo = MemoryRateLimit()
    limitador = _limitador(redis_falso, respaldo=respaldo, timeout=1)
    redis_falso["servidor"].shutdown()
    redis_falso["servidor"].server_close()

    assert limitador.hit("/acceso|192.0.2.10", 3, 300).permitido


def test_rechaza_url_no_https():
    """Enviar el token por http expondría la credencial en tránsito."""
    with pytest.raises(ValueError):
        UpstashRateLimit("http://ejemplo.upstash.io", "token")
    with pytest.raises(ValueError):
        UpstashRateLimit("no-es-una-url", "token")


def test_rechaza_token_vacio():
    with pytest.raises(ValueError):
        UpstashRateLimit("https://ejemplo.upstash.io", "   ")


def test_sin_variables_usa_memoria(monkeypatch):
    monkeypatch.delenv("UPSTASH_REDIS_REST_URL", raising=False)
    monkeypatch.delenv("UPSTASH_REDIS_REST_TOKEN", raising=False)
    limitador = build_rate_limiter()
    assert isinstance(limitador, MemoryRateLimit)
    assert not limitador.distribuido


def test_con_variables_usa_upstash(monkeypatch):
    monkeypatch.setenv("UPSTASH_REDIS_REST_URL", "https://ejemplo.upstash.io")
    monkeypatch.setenv("UPSTASH_REDIS_REST_TOKEN", "token")
    limitador = build_rate_limiter()
    assert isinstance(limitador, UpstashRateLimit)
    assert limitador.distribuido


def test_configuracion_incompleta_no_impide_arrancar(monkeypatch):
    """Media configuración degrada a memoria; caerse sería peor."""
    monkeypatch.setenv("UPSTASH_REDIS_REST_URL", "https://ejemplo.upstash.io")
    monkeypatch.delenv("UPSTASH_REDIS_REST_TOKEN", raising=False)
    assert isinstance(build_rate_limiter(), MemoryRateLimit)


def test_readyz_avisa_de_configuracion_incompleta(monkeypatch):
    """Pero readiness sí debe señalarla, para que no pase inadvertida."""
    monkeypatch.setenv("UPSTASH_REDIS_REST_URL", "https://ejemplo.upstash.io")
    monkeypatch.delenv("UPSTASH_REDIS_REST_TOKEN", raising=False)
    estado, error = estado_configuracion()
    assert estado == "mal-configurado"
    assert error


def test_readyz_reporta_el_contador_distribuido(monkeypatch):
    monkeypatch.setenv("UPSTASH_REDIS_REST_URL", "https://ejemplo.upstash.io")
    monkeypatch.setenv("UPSTASH_REDIS_REST_TOKEN", "token")
    estado, error = estado_configuracion()
    assert estado == "distribuido:upstash"
    assert error is None


def test_readyz_exige_contador_compartido_si_se_declara(monkeypatch):
    """`COTIZAT_REQUIRE_DISTRIBUTED_RATELIMIT` convierte el aviso en error."""
    monkeypatch.delenv("UPSTASH_REDIS_REST_URL", raising=False)
    monkeypatch.delenv("UPSTASH_REDIS_REST_TOKEN", raising=False)

    monkeypatch.setenv("COTIZAT_REQUIRE_DISTRIBUTED_RATELIMIT", "false")
    estado, error = estado_configuracion()
    assert estado == "memoria" and error is None

    monkeypatch.setenv("COTIZAT_REQUIRE_DISTRIBUTED_RATELIMIT", "true")
    estado, error = estado_configuracion()
    assert estado == "memoria"
    assert error and "UPSTASH" in error
