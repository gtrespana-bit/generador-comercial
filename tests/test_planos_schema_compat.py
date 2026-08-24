"""Regresión para despliegues donde código y esquema de planos se desfasan."""
from __future__ import annotations

import asyncio
import json
from datetime import datetime

import pytest
from sqlalchemy import Column, MetaData, Table, create_engine, event
from sqlalchemy.orm import Session

from app.models import PlanoObra
from app.routers import planos as router_planos
from app.services.planos_compat import (
    COLUMNAS_PLANOS_VECTORIALES,
    ESQUEMA_PLANOS_LEGACY,
    completar_plano_legacy,
    detectar_esquema_planos,
    opciones_columnas_compatibles,
)


VALORES_VECTORIALES = {
    "origen": "mixto",
    "grosor_tabique_cm": 17.5,
    "ancho_lienzo_m": 12.0,
    "alto_lienzo_m": 8.0,
}
VALORES_LEGACY = {
    "origen": "subido",
    "grosor_tabique_cm": 10.0,
    "ancho_lienzo_m": None,
    "alto_lienzo_m": None,
}


def _sesion_con_planos_sin(*columnas_ausentes: str) -> tuple[Session, object]:
    """Crea una tabla pre-migración sin activar el auto-upgrade SQLite."""
    engine = create_engine("sqlite+pysqlite:///:memory:")
    metadata = MetaData()
    columnas = []
    for original in PlanoObra.__table__.columns:
        if original.name in columnas_ausentes:
            continue
        columnas.append(
            Column(
                original.name,
                original.type.copy(),
                primary_key=original.primary_key,
                # El objetivo es probar la proyección SELECT, no replicar FKs
                # ni defaults del esquema real.
                nullable=not original.primary_key,
            )
        )
    tabla = Table("planos_obra", metadata, *columnas)
    metadata.create_all(engine)

    valores = {columna.name: None for columna in tabla.columns}
    valores.update(
        {
            "id": 1,
            "organizacion_id": 13,
            "presupuesto_id": 14,
            "nombre": "Planta existente",
            "archivo": "storage://plano.png",
            "content_type": "image/png",
            "ancho_px": 1200,
            "alto_px": 800,
            "unidad_calibracion": "m",
            "created_at": datetime(2026, 8, 24),
            "updated_at": datetime(2026, 8, 24),
        }
    )
    valores.update(
        {
            nombre: valor
            for nombre, valor in VALORES_VECTORIALES.items()
            if nombre in tabla.columns
        }
    )
    with engine.begin() as connection:
        connection.execute(tabla.insert().values(**valores))
    return Session(engine), engine


@pytest.mark.parametrize("columna_ausente", sorted(COLUMNAS_PLANOS_VECTORIALES))
def test_cada_columna_vectorial_ausente_se_difiere_y_recibe_default(
    columna_ausente: str,
):
    """No basta con tratar ``origen``: las cuatro columnas son opcionales."""
    db, _engine = _sesion_con_planos_sin(columna_ausente)
    try:
        esquema = detectar_esquema_planos(db)
        assert not esquema.tiene_columna(columna_ausente)

        plano = (
            db.query(PlanoObra)
            .options(*opciones_columnas_compatibles(esquema))
            .one()
        )
        completar_plano_legacy(plano, esquema)

        for nombre in COLUMNAS_PLANOS_VECTORIALES:
            esperado = (
                VALORES_LEGACY[nombre]
                if nombre == columna_ausente
                else VALORES_VECTORIALES[nombre]
            )
            assert getattr(plano, nombre) == esperado
    finally:
        db.close()


def test_esquema_prevectorial_completo_abre_sin_lazy_loads_de_columnas_o_elementos():
    """Reproduce producción: faltan cuatro columnas y ``planos_elementos``."""
    db, engine = _sesion_con_planos_sin(*COLUMNAS_PLANOS_VECTORIALES)
    sentencias: list[str] = []

    @event.listens_for(engine, "before_cursor_execute")
    def _capturar(_conn, _cursor, statement, _parameters, _context, _many):
        sentencias.append(statement)

    try:
        esquema = detectar_esquema_planos(db)
        assert not esquema.columnas_vectoriales_completas
        assert not esquema.editor_vectorial_disponible
        assert not esquema.tiene_tabla_elementos

        sentencias.clear()
        plano = (
            db.query(PlanoObra)
            .options(*opciones_columnas_compatibles(esquema))
            .one()
        )
        completar_plano_legacy(plano, esquema)

        select_principal = next(sql for sql in sentencias if "FROM planos_obra" in sql)
        for nombre in COLUMNAS_PLANOS_VECTORIALES:
            assert nombre not in select_principal
            assert getattr(plano, nombre) == VALORES_LEGACY[nombre]

        consultas_antes = len(sentencias)
        assert plano.elementos == []
        # Acceder desde Jinja/exportación no puede intentar consultar una tabla
        # que todavía no existe.
        assert len(sentencias) == consultas_antes
    finally:
        db.close()


def test_escritura_vectorial_devuelve_503_controlado_si_migracion_pendiente(monkeypatch):
    """Una acción nueva no debe convertirse en otro ProgrammingError/500."""
    monkeypatch.setattr(
        router_planos,
        "detectar_esquema_planos",
        lambda _db: ESQUEMA_PLANOS_LEGACY,
    )

    respuesta = asyncio.run(
        router_planos.actualizar_grosor_endpoint(1, request=object(), db=object())
    )
    assert respuesta.status_code == 503
    assert respuesta.headers["retry-after"] == "300"
    cuerpo = json.loads(respuesta.body)
    assert cuerpo["ok"] is False
    assert cuerpo["codigo"] == "migracion_planos_pendiente"
    assert "actualizando" in cuerpo["error"]
