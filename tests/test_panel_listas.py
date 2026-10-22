"""Listas del panel: paginación, búsqueda, orden y CSV coherentes (Fase 1).

La auditoría del 22/10/2026 encontró que de nueve listas solo una se podía
interrogar y ninguna paginaba. Estas pruebas fijan el contrato de Compras y
Soporte, las dos primeras migradas al patrón común:

- la página 2 trae lo que no cabe en la 1 (y no repite filas);
- buscar encuentra un mensaje viejo aunque no esté entre los últimos 25;
- el CSV exporta el mismo conjunto filtrado que la pantalla;
- el ``volver`` de una acción conserva los filtros;
- el badge de Clientes cuenta el buzón de soporte.
"""
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

from app.database import Base, get_operator_db
from app.health import HealthStatus, liveness
from app.main import app
from app.models import CompraPlan, Membresia, MensajeSoporte, Organizacion, Usuario
from app.panel_arquitectura import nav_panel
from app.services.panel_listas import meta_pagina, paginador

BASE = datetime(2026, 10, 1, 8, 0, 0)


@pytest.fixture
def entorno_admin():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    with Session() as seed:
        norte = Organizacion(nombre="Obras Norte", slug="obras-norte")
        sur = Organizacion(nombre="Reformas Sur", slug="reformas-sur")
        usuario = Usuario(auth_user_id="auth-listas", email="u@example.com", nombre="U")
        seed.add_all([norte, sur, usuario])
        seed.flush()
        seed.add(
            Membresia(organizacion_id=norte.id, usuario_id=usuario.id, rol="propietario")
        )

        # 30 compras: la más antigua es de cliente0 y solo cabe en la página 2.
        for indice in range(30):
            seed.add(
                CompraPlan(
                    organizacion_id=norte.id,
                    plan="anual",
                    metodo_pago="usdt",
                    importe=89.0,
                    moneda="USD",
                    datos_verificacion="{}",
                    comprobante_nombre=f"comprobante-{indice}.png",
                    estado="pendiente",
                    creada_por_email=f"cliente{indice}@example.com",
                    created_at=BASE + timedelta(days=indice),
                )
            )

        # 30 mensajes: el más antiguo (antiguo@example.com) tampoco cabe en la 1.
        for indice in range(30):
            seed.add(
                MensajeSoporte(
                    nombre=f"Persona {indice}",
                    email=(
                        "antiguo@example.com" if indice == 0 else f"soporte{indice}@example.com"
                    ),
                    tipo="consulta",
                    asunto=f"Asunto {indice}",
                    mensaje=f"Mensaje número {indice}",
                    estado="nuevo",
                    created_at=BASE + timedelta(days=indice),
                )
            )
        seed.commit()
        datos = {"norte": norte.id, "sur": sur.id}

    def _db_operador():
        db = Session()
        db.info["es_operador"] = True
        db.info["auth_email"] = "op@example.com"
        db.info["operador_rol"] = "superadmin"
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_operator_db] = _db_operador
    try:
        yield TestClient(app), Session, datos
    finally:
        app.dependency_overrides.pop(get_operator_db, None)
        engine.dispose()


# ---------------------------------------------------------------------------
# Compras: paginación, búsqueda y CSV
# ---------------------------------------------------------------------------


def test_compras_pagina_de_25_y_la_segunda_trae_el_resto(entorno_admin):
    cliente, _Session, _datos = entorno_admin
    primera = cliente.get("/admin/ingresos?tab=compras")
    segunda = cliente.get("/admin/ingresos?tab=compras&pagina=2")

    assert primera.status_code == 200 and segunda.status_code == 200
    assert "30 compras" in primera.text
    assert "1–25 de 30" in primera.text
    assert "26–30 de 30" in segunda.text
    # La compra más antigua está en la página 2, no en la 1.
    assert "cliente0@example.com" not in primera.text
    assert "cliente0@example.com" in segunda.text
    # Y la más reciente no se repite en la página 2.
    assert "cliente29@example.com" not in segunda.text


def test_buscar_una_compra_por_correo_antiguo_la_encuentra(entorno_admin):
    cliente, _Session, _datos = entorno_admin
    respuesta = cliente.get("/admin/ingresos?tab=compras&q=cliente0@example.com")

    assert respuesta.status_code == 200
    assert "cliente0@example.com" in respuesta.text
    assert "1 compra" in respuesta.text
    assert "cliente1@example.com" not in respuesta.text


def test_el_csv_de_compras_exporta_lo_filtrado_y_no_todo(entorno_admin):
    cliente, _Session, _datos = entorno_admin
    csv = cliente.get("/admin/ingresos.csv?tab=compras&q=cliente0@example.com")

    assert csv.status_code == 200
    assert "text/csv" in csv.headers["content-type"]
    assert "cliente0@example.com" in csv.text
    assert "cliente1@example.com" not in csv.text


def test_el_csv_de_contratos_existe_y_respeta_el_filtro(entorno_admin):
    """La pestaña enlazaba a /admin/contratos.csv, que no tenía ruta: 404."""
    cliente, _Session, _datos = entorno_admin
    completo = cliente.get("/admin/contratos.csv")
    filtrado = cliente.get("/admin/contratos.csv?q=Reformas")

    assert completo.status_code == 200
    assert "text/csv" in completo.headers["content-type"]
    assert "Obras Norte" in completo.text and "Reformas Sur" in completo.text
    assert filtrado.status_code == 200
    assert "Reformas Sur" in filtrado.text
    assert "Obras Norte" not in filtrado.text


def test_el_enlace_del_buscador_abre_la_compra_concreta(entorno_admin):
    """⌘K ya sabía qué compra era: el enlace no puede dejarla a buscar a ojo."""
    cliente, Session, _datos = entorno_admin
    with Session() as db:
        compra = (
            db.query(CompraPlan)
            .filter(CompraPlan.creada_por_email == "cliente0@example.com")
            .one()
        )
        compra_id = compra.id

    respuesta = cliente.get(
        f"/admin/ingresos?tab=compras&estado=todas&compra={compra_id}"
    )

    assert respuesta.status_code == 200
    assert f"Filtro por compra #{compra_id}" in respuesta.text
    assert "cliente0@example.com" in respuesta.text
    assert "1 compra" in respuesta.text


# ---------------------------------------------------------------------------
# Soporte: paginación, búsqueda en todo el buzón y volver con filtros
# ---------------------------------------------------------------------------


def test_soporte_pagina_y_encuentra_un_mensaje_fuera_de_la_primera_pagina(entorno_admin):
    cliente, _Session, _datos = entorno_admin
    primera = cliente.get("/admin/clientes?tab=soporte")
    segunda = cliente.get("/admin/clientes?tab=soporte&pagina=2")
    buscado = cliente.get("/admin/clientes?tab=soporte&q=antiguo@example.com")

    assert primera.status_code == 200
    assert "30 mensajes" in primera.text
    assert "antiguo@example.com" not in primera.text
    assert "antiguo@example.com" in segunda.text
    # El filtro va en SQL: encuentra el mensaje aunque no esté entre los 25
    # últimos. Antes se filtraba en Python después del LIMIT 200.
    assert buscado.status_code == 200
    assert "antiguo@example.com" in buscado.text
    assert "1 mensaje" in buscado.text


def test_el_volver_de_soporte_conserva_los_filtros(entorno_admin):
    cliente, _Session, _datos = entorno_admin
    pagina = cliente.get("/admin/clientes?tab=soporte&estado=nuevo&q=antiguo")

    assert pagina.status_code == 200
    assert 'name="volver"' in pagina.text
    # El valor del campo conserva pestaña, estado, texto y orden; el HTML
    # escapa los & como &amp;.
    assert 'value="/admin/clientes?tab=soporte&amp;estado=nuevo&amp;q=antiguo' in pagina.text


def test_el_csv_de_soporte_respeta_el_filtro(entorno_admin):
    cliente, _Session, _datos = entorno_admin
    csv = cliente.get("/admin/soporte.csv?q=antiguo@example.com")

    assert csv.status_code == 200
    assert "antiguo@example.com" in csv.text
    assert "soporte1@example.com" not in csv.text


# ---------------------------------------------------------------------------
# Piezas compartidas
# ---------------------------------------------------------------------------


def test_el_badge_de_clientes_cuenta_los_mensajes_sin_atender():
    """El contador ya se calculaba; el menú buscaba una clave que no existía."""
    entradas = {entrada["id"]: entrada for entrada in nav_panel({"soporte": 4})}
    assert entradas["clientes"]["contador"] == 4


def test_el_paginador_omite_la_pagina_uno_y_conserva_los_filtros():
    meta = meta_pagina(total=60, pagina=1, por_pagina=25)
    barra = paginador("/admin/ingresos", {"tab": "compras", "estado": "pendiente"}, meta)

    assert barra["siguiente"] == "/admin/ingresos?tab=compras&estado=pendiente&pagina=2"
    assert barra["anterior"] == ""
    assert barra["info"] == "1–25 de 60"


def test_la_ventana_de_paginas_resume_los_saltos_con_elipsis():
    meta = meta_pagina(total=25 * 20, pagina=10, por_pagina=25)
    numeros = paginador("/admin/x", {}, meta)["numeros"]
    visibles = [n["numero"] for n in numeros if n["numero"]]

    assert visibles[0] == 1 and visibles[-1] == 20
    assert 10 in visibles
    assert any(n["numero"] is None for n in numeros)


def test_una_pagina_fuera_de_rango_cae_en_la_ultima():
    assert meta_pagina(total=60, pagina=99, por_pagina=25)["numero"] == 3
    assert meta_pagina(total=0, pagina=4, por_pagina=25)["numero"] == 1


def test_la_gravedad_de_salud_viaja_con_el_chequeo_y_no_se_adivina():
    """Sistema › Estado ya no decide el color con `'error' in valor`."""
    estado = HealthStatus(
        ok=True,
        checks={"cron_secret": "no-configurado", "auth": "configurado"},
        severidades={"cron_secret": "info", "auth": "ok"},
    )
    assert estado.to_dict()["severidades"]["cron_secret"] == "info"
    # /healthz conserva su contrato exacto: sin gravedades no se publica la clave.
    assert "severidades" not in liveness().to_dict()
