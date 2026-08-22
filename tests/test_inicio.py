"""Regresiones del panel de inicio."""

from datetime import date

from fastapi.responses import JSONResponse

from app.models import Configuracion, Presupuesto
from app.routers import inicio as inicio_router


def test_panel_entrega_contadores_mensuales_como_enteros(
    entorno, cliente_web, monkeypatch
):
    """Los recuentos optimizados no son listas y no admiten ``len()``.

    La optimización del panel cambió estos valores de colecciones ORM a
    contadores enteros. El endpoint debe entregar directamente esos enteros a
    la plantilla, tanto para presupuestos enviados como aprobados.
    """
    Session, _ids, _rol = entorno
    with Session() as db:
        cfg = db.query(Configuracion).one()
        cfg.onboarding_completado = True
        presupuestos = db.query(Presupuesto).order_by(Presupuesto.id).all()
        assert len(presupuestos) == 2
        presupuestos[0].fecha = date.today()
        presupuestos[0].estado = "aprobado"
        presupuestos[1].fecha = date.today()
        presupuestos[1].estado = "enviado"
        db.commit()

    def _capturar_contexto(request, nombre, contexto):  # noqa: ARG001
        return JSONResponse({
            "presupuestos_mes": contexto["presupuestos_mes"],
            "enviados_mes": contexto["enviados_mes"],
            "aprobados_mes": contexto["aprobados_mes"],
        })

    monkeypatch.setattr(
        inicio_router.TEMPLATES,
        "TemplateResponse",
        _capturar_contexto,
    )

    respuesta = cliente_web.get("/inicio")

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "presupuestos_mes": 2,
        "enviados_mes": 1,
        "aprobados_mes": 1,
    }
