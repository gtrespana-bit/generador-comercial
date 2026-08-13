from pathlib import Path
import re

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.responses import HTMLResponse, PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from app.security import AuthRateLimitMiddleware, WebSecurityMiddleware


async def endpoint(_request):
    return PlainTextResponse("ok")


def cliente_seguro():
    app = Starlette(
        routes=[
            Route("/leer", endpoint, methods=["GET"]),
            Route("/escribir", endpoint, methods=["POST"]),
        ],
        middleware=[Middleware(WebSecurityMiddleware, enforce_csrf=True)],
    )
    return TestClient(app, base_url="https://cotizat.test")


def test_csrf_acepta_origin_exacto():
    with cliente_seguro() as client:
        response = client.post(
            "/escribir", headers={"Origin": "https://cotizat.test"}
        )
    assert response.status_code == 200


def test_csrf_acepta_referer_same_origin_si_origin_no_existe():
    with cliente_seguro() as client:
        response = client.post(
            "/escribir", headers={"Referer": "https://cotizat.test/formulario"}
        )
    assert response.status_code == 200


def test_csrf_rechaza_origin_cruzado_y_fetch_metadata():
    with cliente_seguro() as client:
        response = client.post(
            "/escribir",
            headers={
                "Origin": "https://atacante.example",
                "Sec-Fetch-Site": "cross-site",
            },
        )
    assert response.status_code == 403
    assert "CSRF" in response.text


def test_csrf_rechaza_escritura_sin_procedencia_en_web():
    with cliente_seguro() as client:
        response = client.post("/escribir")
    assert response.status_code == 403


def test_cabeceras_defensivas_y_hsts_en_https():
    with cliente_seguro() as client:
        response = client.get("/leer")
    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert response.headers["cross-origin-opener-policy"] == "same-origin"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
    assert response.headers["strict-transport-security"].startswith("max-age=31536000")


def test_csp_usa_nonce_unico_y_bloquea_handlers_inline():
    async def html_con_nonce(request):
        nonce = request.state.csp_nonce
        return HTMLResponse(f'<script nonce="{nonce}">window.ok=true</script>')

    app = Starlette(
        routes=[Route("/html", html_con_nonce)],
        middleware=[Middleware(WebSecurityMiddleware, enforce_csrf=True)],
    )
    with TestClient(app, base_url="https://cotizat.test") as client:
        first = client.get("/html")
        second = client.get("/html")

    first_csp = first.headers["content-security-policy"]
    first_nonce = first.text.split('nonce="', 1)[1].split('"', 1)[0]
    second_nonce = second.text.split('nonce="', 1)[1].split('"', 1)[0]
    script_directive = first_csp.split("script-src ", 1)[1].split(";", 1)[0]
    assert f"'nonce-{first_nonce}'" in script_directive
    assert "'unsafe-inline'" not in script_directive
    assert "script-src-attr 'none'" in first_csp
    assert first_nonce != second_nonce


def test_plantillas_no_contienen_handlers_y_inline_usa_nonce():
    event_attribute = re.compile(
        r"\son(?:click|change|input|submit|load|error|blur|focus|keydown|keyup)\s*=",
        re.IGNORECASE,
    )
    inline_script = re.compile(r"<script(?![^>]*\bsrc=)[^>]*>", re.IGNORECASE)
    style_element = re.compile(r"<style[^>]*>", re.IGNORECASE)
    for path in Path("app/templates").rglob("*.html"):
        template = path.read_text(encoding="utf-8")
        assert not event_attribute.search(template), path
        assert all("nonce=" in tag for tag in inline_script.findall(template)), path
        assert all("nonce=" in tag for tag in style_element.findall(template)), path


def test_acciones_declarativas_tienen_handler_registrado():
    templates = "\n".join(
        path.read_text(encoding="utf-8")
        for path in Path("app/templates").rglob("*.html")
    )
    scripts = "\n".join(
        path.read_text(encoding="utf-8")
        for path in Path("app/static/js").rglob("*.js")
    ) + "\n" + templates
    used = set(re.findall(
        r'data-cotizat-(?:click|change|input|keyup)="([a-z0-9-]+)"',
        templates,
    ))
    registered = set(re.findall(
        r'(?:CotizatActions\.)?register\(["\']([a-z0-9-]+)["\']',
        scripts,
    ))
    assert used <= registered, sorted(used - registered)


def test_rate_limit_bloquea_rafaga_y_publica_retry_after():
    app = Starlette(
        routes=[Route("/acceso", endpoint, methods=["POST"])],
        middleware=[Middleware(
            AuthRateLimitMiddleware,
            limits={"/acceso": 2},
            window_seconds=60,
        )],
    )
    with TestClient(app) as client:
        assert client.post("/acceso").status_code == 200
        assert client.post("/acceso").status_code == 200
        blocked = client.post("/acceso")
    assert blocked.status_code == 429
    assert int(blocked.headers["retry-after"]) >= 1


def test_rate_limit_separa_direcciones_ip():
    app = Starlette(
        routes=[Route("/registro", endpoint, methods=["POST"])],
        middleware=[Middleware(
            AuthRateLimitMiddleware,
            limits={"/registro": 1},
            window_seconds=60,
            trust_forwarded_for=True,
        )],
    )
    with TestClient(app) as client:
        assert client.post(
            "/registro", headers={"X-Forwarded-For": "192.0.2.10"}
        ).status_code == 200
        assert client.post(
            "/registro", headers={"X-Forwarded-For": "192.0.2.11"}
        ).status_code == 200
        assert client.post(
            "/registro", headers={"X-Forwarded-For": "192.0.2.10"}
        ).status_code == 429


def test_rate_limit_ignora_forwarded_for_si_proxy_no_es_confiable():
    app = Starlette(
        routes=[Route("/acceso", endpoint, methods=["POST"])],
        middleware=[Middleware(
            AuthRateLimitMiddleware,
            limits={"/acceso": 1},
            window_seconds=60,
        )],
    )
    with TestClient(app) as client:
        assert client.post(
            "/acceso", headers={"X-Forwarded-For": "192.0.2.20"}
        ).status_code == 200
        assert client.post(
            "/acceso", headers={"X-Forwarded-For": "192.0.2.21"}
        ).status_code == 429


def test_rate_limit_acota_contadores_en_memoria():
    middleware = AuthRateLimitMiddleware(
        Starlette(),
        limits={"/acceso": 1},
        window_seconds=60,
        max_buckets=2,
    )
    assert middleware._permitido(("/acceso", "192.0.2.30"), 1)[0]
    assert middleware._permitido(("/acceso", "192.0.2.31"), 1)[0]
    assert middleware._permitido(("/acceso", "192.0.2.32"), 1)[0]
    assert len(middleware._attempts) == 2


def test_rate_limit_no_afecta_lecturas_ni_otras_rutas():
    app = Starlette(
        routes=[
            Route("/acceso", endpoint, methods=["GET", "POST"]),
            Route("/otra", endpoint, methods=["POST"]),
        ],
        middleware=[Middleware(
            AuthRateLimitMiddleware,
            limits={"/acceso": 1},
            window_seconds=60,
        )],
    )
    with TestClient(app) as client:
        for _ in range(3):
            assert client.get("/acceso").status_code == 200
            assert client.post("/otra").status_code == 200


def test_middleware_no_sobrescribe_csp_mas_restrictiva_de_archivo():
    async def archivo(_request):
        return PlainTextResponse(
            "privado", headers={"Content-Security-Policy": "sandbox"}
        )

    app = Starlette(
        routes=[Route("/archivo", archivo)],
        middleware=[Middleware(WebSecurityMiddleware, enforce_csrf=True)],
    )
    with TestClient(app, base_url="https://cotizat.test") as client:
        response = client.get("/archivo")
    assert response.headers["content-security-policy"] == "sandbox"
