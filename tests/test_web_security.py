from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from app.security import WebSecurityMiddleware


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
