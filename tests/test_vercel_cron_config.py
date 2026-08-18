"""El cron de Vercel: vercel.json declara lo que la aplicación registra.

Vercel crea el trabajo programado a partir de ``vercel.json`` → ``crons`` y
solo en despliegues de **producción**; cada invocación se autentica con
``Authorization: Bearer $CRON_SECRET``. Estas pruebas garantizan que la ruta
declarada existe de verdad en la aplicación (método GET) y que el horario es
válido para el plan Hobby (máximo una vez al día), de modo que un cambio de
código no pueda dejar un cron huérfano en silencio.
"""
import json
from pathlib import Path

from app.main import app

RAIZ = Path(__file__).resolve().parents[1]
VERCEL_JSON = RAIZ / "vercel.json"


def _crons() -> list[dict]:
    with VERCEL_JSON.open(encoding="utf-8") as fh:
        data = json.load(fh)
    assert data.get("framework") == "fastapi", (
        "vercel.json debe declarar el preset fastapi (entrada app/main.py)."
    )
    assert "crons" in data, "vercel.json debe declarar el bloque crons."
    crons = data["crons"]
    assert crons, "El bloque crons no puede estar vacío."
    return crons


def test_cada_ruta_de_cron_existe_como_get_en_la_aplicacion():
    from app.routers import admin

    # FastAPI 0.141 incluye los routers de forma perezosa (_IncludedRouter),
    # así que la tabla fiable es la del router que declara el cron.
    rutas = {
        getattr(r, "path", None): set(getattr(r, "methods", []) or [])
        for r in admin.router.routes
    }
    for cron in _crons():
        ruta = cron["path"]
        assert ruta in rutas, (
            f"El cron {ruta} de vercel.json no está registrado en la aplicación."
        )
        assert "GET" in rutas[ruta], (
            f"El cron {ruta} debe responder a GET (Vercel invoca con GET)."
        )


def test_cada_ruta_de_cron_es_alcanzable_en_la_app_completa():
    """/api/cron/... existe en el stack real: nunca 404.

    En SQLite local la dependencia responde 403 (el cron solo existe en el
    despliegue web); en web sin `CRON_SECRET` responde 401; con el secreto
    correcto, 200. Las tres prueban que Vercel no caerá en un 404.
    """
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        for cron in _crons():
            respuesta = client.get(cron["path"])
            assert respuesta.status_code != 404, (
                f"El cron {cron['path']} devuelve 404: la ruta no se sirve."
            )


def test_cada_cron_es_diario_compatible_con_el_plan_hobby():
    # Hobby: máximo una vez al día (minuto y hora fijos; día, mes y
    # día-de-semana en '*'). Además Vercel no admite fijar a la vez día del
    # mes y día de la semana.
    for cron in _crons():
        partes = cron["schedule"].split()
        assert len(partes) == 5, f"Expresión inválida: {cron['schedule']}"
        minuto, hora, dom, mes, dow = partes
        assert minuto.isdigit() and hora.isdigit(), (
            f"{cron['schedule']} corre más de una vez al día: no es válida en Hobby."
        )
        assert (dom, mes, dow) == ("*", "*", "*"), (
            f"{cron['schedule']} fija día del mes o día de la semana: Vercel "
            "no permite ambos a la vez."
        )


def test_readyz_publica_el_estado_del_cron(monkeypatch):
    """/readyz debe delatar un CRON_SECRET ausente y confirmar la ruta."""
    from app.health import readiness

    monkeypatch.delenv("CRON_SECRET", raising=False)
    checks = readiness().checks
    assert checks["cron_secret"] == "no-configurado"
    assert "registrada" in checks["cron"]

    monkeypatch.setenv("CRON_SECRET", "secreto-de-prueba-largo")
    checks = readiness().checks
    assert checks["cron_secret"] == "configurado"
    # El valor del secreto jamás puede filtrarse a la respuesta.
    assert "secreto-de-prueba" not in str(checks)
