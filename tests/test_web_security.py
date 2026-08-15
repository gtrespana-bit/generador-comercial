import ast
from pathlib import Path
import re

from fastapi.routing import APIRoute
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.responses import HTMLResponse, PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from app import main as main_module
from app.database import get_authenticated_db, get_db
from app.main import app as cotizat_app
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
    style_directive = first_csp.split("style-src ", 1)[1].split(";", 1)[0]
    assert f"'nonce-{first_nonce}'" in script_directive
    assert f"'nonce-{first_nonce}'" in style_directive
    assert "'unsafe-inline'" not in script_directive
    assert "'unsafe-inline'" not in style_directive
    assert "script-src-attr 'none'" in first_csp
    assert "style-src-attr 'none'" in first_csp
    assert first_nonce != second_nonce


def test_plantillas_no_contienen_handlers_y_inline_usa_nonce():
    event_attribute = re.compile(
        r"\son(?:click|change|input|submit|load|error|blur|focus|keydown|keyup)\s*=",
        re.IGNORECASE,
    )
    inline_script = re.compile(r"<script(?![^>]*\bsrc=)[^>]*>", re.IGNORECASE)
    style_element = re.compile(r"<style[^>]*>", re.IGNORECASE)
    style_attribute = re.compile(r"\sstyle\s*=", re.IGNORECASE)
    for path in Path("app/templates").rglob("*.html"):
        template = path.read_text(encoding="utf-8")
        assert not event_attribute.search(template), path
        assert not style_attribute.search(template), path
        assert all("nonce=" in tag for tag in inline_script.findall(template)), path
        assert all("nonce=" in tag for tag in style_element.findall(template)), path


def test_respuesta_real_publica_nonce_para_hoja_dinamica_sin_estilos_inline():
    with TestClient(cotizat_app) as client:
        response = client.get("/")
    nonce = response.headers["content-security-policy"].split("'nonce-", 1)[1].split("'", 1)[0]
    assert f'<script nonce="{nonce}" src="/static/js/csp_styles.js"></script>' in response.text
    assert not re.search(r"\sstyle\s*=", response.text, re.IGNORECASE)


def test_frontend_no_usa_sinks_html_de_inyeccion():
    dangerous = re.compile(
        r"\b(?:innerHTML|outerHTML|insertAdjacentHTML|document\.write|"
        r"createContextualFragment|DOMParser)\b",
        re.IGNORECASE,
    )
    style_api = re.compile(r"\.style(?:\.|\[|\s*=)|style\.cssText", re.IGNORECASE)
    for root in (Path("app/static/js"), Path("app/templates")):
        for path in root.rglob("*"):
            if path.suffix not in {".js", ".html"}:
                continue
            source = path.read_text(encoding="utf-8")
            assert not dangerous.search(source), path
            if path.name != "csp_styles.js":
                assert not style_api.search(source), path


def test_hojas_style_dinamicas_inyectadas_exigen_nonce():
    # Un <style> creado en JS sin nonce queda bloqueado por la CSP
    # (style-src solo autoriza 'self', el nonce de la respuesta y Google Fonts).
    # Solo debe crearse en csp_styles.js, que le asigna el nonce capturado.
    crear_style = re.compile(r'createElement\(["\']style["\']\)')
    asigna_nonce = re.compile(r'\.nonce\s*=')
    for path in Path("app/static/js").rglob("*.js"):
        source = path.read_text(encoding="utf-8")
        if crear_style.search(source):
            assert asigna_nonce.search(source), path


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


def test_rutas_get_no_hacen_escrituras_empresariales_directas():
    tree = ast.parse(Path("app/main.py").read_text(encoding="utf-8"))
    mutaciones = []
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        is_get = any(
            isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Attribute)
            and decorator.func.attr == "get"
            for decorator in node.decorator_list
        )
        if not is_get:
            continue
        for call in (item for item in ast.walk(node) if isinstance(item, ast.Call)):
            if (
                isinstance(call.func, ast.Attribute)
                and isinstance(call.func.value, ast.Name)
                and call.func.value.id == "db"
                and call.func.attr in {"add", "delete", "flush", "commit"}
            ) or (
                isinstance(call.func, ast.Name)
                and call.func.id in {"asegurar_config", "marcar_vencidos"}
            ):
                mutaciones.append((node.name, call.lineno))
    assert not mutaciones, mutaciones


def test_toda_ruta_comercial_exige_sesion_salvo_fronteras_publicas_o_locales():
    publicas = {
        ("GET", "/acceso"),
        ("POST", "/acceso"),
        ("POST", "/registro"),
        ("POST", "/salir"),
        ("GET", "/recuperar-acceso"),
        ("POST", "/recuperar-acceso"),
        ("GET", "/restablecer-clave"),
        ("POST", "/restablecer-clave"),
        ("GET", "/invitaciones/{token}"),
        ("GET", "/invitaciones/{token}/aceptar"),
        ("GET", "/favicon.ico"),
        # Salud: fronteras públicas de infraestructura (no exponen datos de
        # tenant ni secretos; readiness devuelve 503 si algo falta).
        ("GET", "/healthz"),
        ("GET", "/readyz"),
    }
    solo_sqlite_local = {
        ("GET", "/configuracion/backup"),
        ("POST", "/configuracion/restaurar"),
    }
    sin_proteccion = []
    for route in cotizat_app.routes:
        if not isinstance(route, APIRoute):
            continue
        dependencias = {dep.call for dep in route.dependant.dependencies}
        protegida = bool({get_db, get_authenticated_db} & dependencias)
        for method in route.methods - {"HEAD", "OPTIONS"}:
            key = (method, route.path)
            if key not in publicas | solo_sqlite_local and not protegida:
                sin_proteccion.append(key)
    assert not sin_proteccion, sorted(sin_proteccion)


def test_sincronizacion_de_vencidos_respeta_rol_lectura(monkeypatch):
    class ReadOnlyDB:
        info = {"rol_membresia": "lectura"}

    monkeypatch.setattr(
        main_module,
        "marcar_vencidos",
        lambda _db: (_ for _ in ()).throw(AssertionError("no debe escribir")),
    )
    assert main_module.actualizar_presupuestos_vencidos(ReadOnlyDB()) == {
        "ok": True,
        "actualizados": 0,
    }

    class WriteDB:
        info = {"rol_membresia": "miembro"}

    monkeypatch.setattr(main_module, "marcar_vencidos", lambda _db: 3)
    assert main_module.actualizar_presupuestos_vencidos(WriteDB()) == {
        "ok": True,
        "actualizados": 3,
    }


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
    # El estado vive ahora en el backend intercambiable, no en el middleware.
    assert len(middleware.backend._attempts) == 2


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
