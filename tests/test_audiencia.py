"""El middleware de audiencia debe contar de verdad las visitas públicas.

Motivo (incidente del 05/11/2026): `AudienciaMiddleware` hasheaba la IP con
`ip_de_request`, un nombre que `app/main.py` **nunca importaba**. El
`NameError` saltaba en cada página vista y el `except Exception` del middleware
—que existe para no romper nunca la respuesta del visitante— lo descartaba sin
dejar rastro. Resultado: la tabla `visitas_pagina` se creó, se migró y se
permisionó, y aun así /admin/analitica mostraba cero audiencia siempre.

La prueba recorre el camino real (petición HTTP → middleware → fila) para que
un fallo así no pueda volver a pasar inadvertido: los tests de `resumen_analitica`
parten de filas ya escritas a mano y nunca ejercitaban el middleware.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import VisitaPagina


def _visitas() -> list[VisitaPagina]:
    with SessionLocal() as db:
        return db.query(VisitaPagina).order_by(VisitaPagina.id).all()


def _limpiar() -> None:
    with SessionLocal() as db:
        db.query(VisitaPagina).delete()
        db.commit()


@pytest.fixture(autouse=True)
def _audiencia_limpia():
    _limpiar()
    yield
    _limpiar()


NAVEGADOR = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/140.0",
    "accept": "text/html,application/xhtml+xml",
    "sec-fetch-mode": "navigate",
}


def test_una_visita_publica_queda_registrada_con_ip_hasheada():
    with TestClient(app) as cliente:
        respuesta = cliente.get("/?audiencia=1", headers=NAVEGADOR)
    assert respuesta.status_code == 200

    filas = _visitas()
    assert len(filas) == 1, "la visita pública no se registró"
    visita = filas[0]
    assert visita.ruta == "/"
    # 64 caracteres = SHA-256 en hexadecimal. La IP nunca se guarda en claro.
    assert len(visita.ip_hash) == 64
    assert "127.0.0.1" not in visita.ip_hash
    assert visita.usuario_agent and "firefox" in visita.usuario_agent.lower()


def test_las_rutas_de_sistema_y_de_producto_no_cuentan_como_audiencia():
    with TestClient(app) as cliente:
        cliente.get("/healthz", headers=NAVEGADOR)
        cliente.get("/acceso", headers=NAVEGADOR)
    assert _visitas() == []


def test_un_buscador_no_es_un_visitante():
    with TestClient(app) as cliente:
        cliente.get(
            "/",
            headers={
                "user-agent": "Mozilla/5.0 (compatible; Googlebot/2.1)",
                "accept": "text/html",
            },
        )
    assert _visitas() == []


# ---------------------------------------------------------------------------
# Regresión del 06/11/2026: con la audiencia por fin escribiendo filas, el
# panel empezó a devolver 500 con
# ``AttributeError: 'datetime.date' object has no attribute 'date'`` en
# ``app/services/audiencia.py``. El trozo de serie diaria solo se ejecuta
# cuando hay visitas, así que con la tabla vacía nunca se había probado.
# ---------------------------------------------------------------------------

from datetime import date, datetime  # noqa: E402

from app.services.analitica import resumen_analitica  # noqa: E402
from app.services.audiencia import resumen_audiencia  # noqa: E402

HOY = date(2026, 11, 5)
AYER = date(2026, 11, 4)


def _sembrar_dos_visitas() -> None:
    with SessionLocal() as db:
        db.add_all(
            [
                VisitaPagina(
                    ruta="/",
                    ip_hash="a" * 64,
                    referente="https://www.google.com/",
                    created_at=datetime(2026, 11, 4, 10, 0),
                ),
                VisitaPagina(
                    ruta="/precios",
                    ip_hash="b" * 64,
                    created_at=datetime(2026, 11, 5, 11, 30),
                ),
                # Segunda visita del mismo visitante: no suma visitante nuevo.
                VisitaPagina(
                    ruta="/precios",
                    ip_hash="b" * 64,
                    created_at=datetime(2026, 11, 5, 12, 0),
                ),
            ]
        )
        db.commit()


def test_la_serie_diaria_se_arma_cuando_hay_visitas():
    _sembrar_dos_visitas()
    with SessionLocal() as db:
        datos = resumen_audiencia(db, dias=7, hoy=HOY)

    assert datos["disponible"] is True
    assert len(datos["serie"]) == 7
    assert datos["serie"][-1]["fecha"] == HOY
    assert datos["serie"][-1]["vistas"] == 2
    assert datos["serie"][-1]["visitantes"] == 1
    assert datos["serie"][-2]["fecha"] == AYER
    assert datos["serie"][-2]["vistas"] == 1
    assert datos["vistas_ventana"] == 3
    assert datos["visitantes_hoy"] == 1
    assert datos["paginas_top"][0] == {"ruta": "/precios", "vistas": 2}


def test_resumen_audiencia_acepta_fechas_y_datetimes():
    """El panel pasa ``date``; la API pública del servicio tolera ambos."""
    _sembrar_dos_visitas()
    with SessionLocal() as db:
        en_dias = resumen_audiencia(db, dias=7, hoy=HOY)
        en_datetimes = resumen_audiencia(
            db, dias=7, hoy=datetime(2026, 11, 5, 18, 0)
        )
    assert len(en_dias["serie"]) == len(en_datetimes["serie"]) == 7
    assert en_dias["vistas_ventana"] == en_datetimes["vistas_ventana"] == 3


def test_el_panel_de_analitica_pinta_la_audiencia_sin_romperse():
    """El 500 real: ``resumen_analitica`` con filas en ``visitas_pagina``."""
    _sembrar_dos_visitas()
    with SessionLocal() as db:
        resumen = resumen_analitica(db, hoy=HOY, dias=30)

    audiencia = resumen["audiencia"]
    assert audiencia["disponible"] is True
    assert audiencia["vistas_ventana"] == 3
    assert audiencia["serie"][-1]["fecha"] == HOY


# ---------------------------------------------------------------------------
# Regresión del 17/11/2026: contención de egress y tamaño de visitas_pagina.
# ---------------------------------------------------------------------------


def test_idioma_redirecciones_404_y_head_no_ensucian_visitas_pagina():
    with TestClient(app) as cliente:
        r_idioma = cliente.get(
            "/idioma/en?destino=/", headers=NAVEGADOR, follow_redirects=False
        )
        assert r_idioma.status_code == 307
        r_404 = cliente.get(
            "/pagina-inexistente-audiencia-xyz", headers=NAVEGADOR
        )
        assert r_404.status_code == 404
        cliente.head("/", headers=NAVEGADOR)
        cliente.get("/en/acceso", headers=NAVEGADOR, follow_redirects=False)
        cliente.get("/baja-marketing", headers=NAVEGADOR, follow_redirects=False)
    assert _visitas() == []


@pytest.mark.parametrize(
    "agente",
    [
        "",
        "curl/8.5.0",
        "python-requests/2.32.0",
        "Go-http-client/2.0",
        "Mozilla/5.0 HeadlessChrome/140.0.0.0 Safari/537.36",
        "facebookexternalhit/1.1",
        "meta-externalagent/1.1",
        # User-Agents sintéticos imposibles (fake-useragent en proxies):
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_7_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.6834.83 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.6613.137 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 15.2; rv:134.0) Gecko/20100101 Firefox/134.0",
        "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:128.0) Gecko/20100101 Firefox/128.0",
    ],
)
def test_clientes_automatizados_y_sin_user_agent_no_cuentan(agente):
    with TestClient(app) as cliente:
        cliente.get("/", headers={"user-agent": agente, "accept": "text/html"})
    assert _visitas() == []


def test_https_exige_sec_fetch_mode_navigate_y_acepta_navegadores_reales():
    ua_chrome_real = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    )
    with TestClient(app, base_url="https://cotizat.test") as cliente:
        # Sin Sec-Fetch-Mode en HTTPS -> scraper HTTP, no se cuenta.
        cliente.get(
            "/?bot=1",
            headers={"user-agent": ua_chrome_real, "accept": "text/html"},
        )
        # Modo cors o prefetch -> no es navegación real.
        cliente.get(
            "/?bot=2",
            headers={
                "user-agent": ua_chrome_real,
                "accept": "text/html",
                "sec-fetch-mode": "cors",
            },
        )
        cliente.get(
            "/?bot=3",
            headers={
                "user-agent": ua_chrome_real,
                "accept": "text/html",
                "sec-fetch-mode": "navigate",
                "sec-purpose": "prefetch",
            },
        )
        assert _visitas() == []
        # Navegación real de Chrome con UA reducido -> sí se cuenta.
        cliente.get(
            "/?real=1",
            headers={
                "user-agent": ua_chrome_real,
                "accept": "text/html",
                "sec-fetch-mode": "navigate",
            },
        )
        assert len(_visitas()) == 1


def test_referer_sintetico_sin_barra_final_no_cuenta_pero_real_si():
    with TestClient(app, base_url="https://cotizat.test") as cliente:
        cliente.get(
            "/?scraper=1",
            headers={**NAVEGADOR, "referer": "https://cotizat.test"},
        )
        assert _visitas() == []
        cliente.get(
            "/?humano=1",
            headers={**NAVEGADOR, "referer": "https://cotizat.test/"},
        )
        assert len(_visitas()) == 1


def test_interruptor_audiencia_bd_apaga_escrituras(monkeypatch):
    monkeypatch.setenv("COTIZAT_AUDIENCIA_BD", "false")
    with TestClient(app) as cliente:
        r = cliente.get("/?audiencia=off", headers=NAVEGADOR)
    assert r.status_code == 200
    assert _visitas() == []


def test_resumen_audiencia_agrega_en_sql_sin_descargar_tabla_cruda():
    from sqlalchemy import event

    from app.database import engine

    with SessionLocal() as db:
        db.add_all(
            [
                # Fuera de ventana: no debe entrar.
                VisitaPagina(
                    ruta="/vieja",
                    ip_hash="c" * 64,
                    created_at=datetime(2026, 9, 1, 8, 0),
                ),
                # Ruido histórico de /idioma: se excluye.
                VisitaPagina(
                    ruta="/idioma/en",
                    ip_hash="d" * 64,
                    created_at=datetime(2026, 11, 5, 9, 0),
                ),
                # Visita válida hace 10 días (entra en 30d, no en 7d).
                VisitaPagina(
                    ruta="/es/precios",
                    ip_hash="e" * 64,
                    referente="https://bing.com/",
                    created_at=datetime(2026, 10, 26, 10, 0),
                ),
                # Visita válida hoy.
                VisitaPagina(
                    ruta="/",
                    ip_hash="f" * 64,
                    referente="https://www.google.com/",
                    created_at=datetime(2026, 11, 5, 12, 0),
                ),
            ]
        )
        db.commit()

    sentencias: list[str] = []

    def _capturar(_conn, _cursor, statement, _params, _ctx, _many):
        if "visitas_pagina" in statement.lower():
            sentencias.append(statement.upper())

    event.listen(engine, "before_cursor_execute", _capturar)
    try:
        with SessionLocal() as db:
            datos = resumen_audiencia(db, dias=30, hoy=HOY)
    finally:
        event.remove(engine, "before_cursor_execute", _capturar)

    assert sentencias, "no se consultó visitas_pagina"
    assert all("GROUP BY" in s and "WHERE" in s for s in sentencias), sentencias
    assert datos["vistas_hoy"] == 1
    assert datos["visitantes_hoy"] == 1
    assert datos["visitantes_7d"] == 1
    assert datos["visitantes_ventana"] == 2
    assert datos["vistas_ventana"] == 2
    rutas = {p["ruta"] for p in datos["paginas_top"]}
    assert rutas == {"/", "/es/precios"}
    assert len(datos["referentes_top"]) == 2


def test_purgar_visitas_audiencia_elimina_antiguas_e_idioma():
    from app.services.audiencia import purgar_visitas_audiencia

    with SessionLocal() as db:
        db.add_all(
            [
                VisitaPagina(
                    ruta="/antigua",
                    ip_hash="1" * 64,
                    created_at=datetime(2026, 9, 20, 10, 0),
                ),
                VisitaPagina(
                    ruta="/idioma/en",
                    ip_hash="2" * 64,
                    created_at=datetime(2026, 11, 5, 10, 0),
                ),
                VisitaPagina(
                    ruta="/vigente",
                    ip_hash="3" * 64,
                    created_at=datetime(2026, 11, 4, 10, 0),
                ),
            ]
        )
        db.commit()

    with SessionLocal() as db:
        resultado = purgar_visitas_audiencia(db, dias=30, hoy=HOY)

    assert resultado["ok"] is True
    assert resultado["eliminadas"] == 2
    restantes = _visitas()
    assert [v.ruta for v in restantes] == ["/vigente"]


def test_robots_y_conmutador_de_idioma_frenan_rastreo_de_idioma():
    with TestClient(app) as cliente:
        robots = cliente.get("/robots.txt").text
        portada = cliente.get("/", headers=NAVEGADOR).text

    assert "Disallow: /idioma" in robots
    assert 'rel="nofollow"' in portada
