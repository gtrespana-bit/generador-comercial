"""Prueba gratuita de 7 días y su defensa contra el reciclaje de cuentas.

El valor de la prueba automática depende por completo de que no se pueda
repetir: si alguien puede registrarse cada semana con un alias del mismo buzón,
el producto es gratis y el corte por licencia no sirve de nada. Por eso la
mayoría de estos tests no comprueban que la prueba *se conceda* —eso es lo
fácil— sino que **no se conceda dos veces** por los caminos por los que un
usuario espabilado lo intentaría.
"""
from datetime import date, timedelta

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base, Licencia, Organizacion, PruebaConcedida
from app.services.identidad_registro import es_desechable, normalizar_email
from app.services.licencias import organizacion_tiene_acceso
from app.services.prueba_gratuita import (
    DIAS_PRUEBA_POR_DEFECTO,
    conceder_prueba,
    dias_de_prueba,
    hash_ip,
    prueba_activada,
    prueba_ya_usada,
)


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _fk(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as sesion:
        yield sesion


def _org(db, nombre="Empresa", slug=None):
    org = Organizacion(nombre=nombre, slug=slug or nombre.lower().replace(" ", "-"))
    db.add(org)
    db.flush()
    return org


# --------------------------------------------------------------------------
# Normalización de identidad: la base de toda la defensa
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "alias",
    [
        "fulano.detal@gmail.com",
        "fulanodetal@gmail.com",
        "FulanoDetal@Gmail.com",
        "fulano.detal+cotizat@gmail.com",
        "f.u.l.a.n.o.d.e.t.a.l+otra@googlemail.com",
        "  FulanoDetal@GMAIL.COM  ",
    ],
)
def test_alias_del_mismo_buzon_son_la_misma_identidad(alias):
    """Todas las variantes que Gmail entrega al mismo buzón cuentan como una.

    Este es el ataque barato: sin normalizar, cada punto de más es una cuenta
    nueva y una prueba nueva, indefinidamente.
    """
    assert normalizar_email(alias) == "fulanodetal@gmail.com"


def test_los_puntos_solo_se_borran_donde_el_proveedor_los_ignora():
    """En un dominio corporativo los puntos separan personas distintas.

    Fundir `fulano.detal@` con `fulanodetal@` en una empresa dejaría a un empleado
    real sin su prueba por culpa de un compañero.
    """
    assert normalizar_email("fulano.detal@miempresa.com") == "fulano.detal@miempresa.com"
    assert normalizar_email("fulanodetal@miempresa.com") == "fulanodetal@miempresa.com"
    assert normalizar_email("mengana.b@outlook.com") != normalizar_email("menganab@outlook.com")


def test_la_subdireccion_se_recorta_en_proveedores_que_la_soportan():
    assert normalizar_email("mengana+lo-que-sea@outlook.com") == "mengana@outlook.com"
    assert normalizar_email("mengana+x@proton.me") == "mengana@proton.me"


def test_email_ilegible_no_se_fusiona_con_nadie():
    """Ante la duda, no se inventan identidades: se devuelve tal cual."""
    assert normalizar_email("sin-arroba") == "sin-arroba"
    assert normalizar_email("") == ""
    assert normalizar_email("+solo@gmail.com") == "+solo@gmail.com"


@pytest.mark.parametrize(
    "correo",
    [
        "x@mailinator.com",
        "x@YOPMAIL.com",
        "x@algo.mailinator.com",
        "x@guerrillamail.com",
        "x@temp-mail.org",
    ],
)
def test_desechables_reconocidos(correo):
    assert es_desechable(correo)


@pytest.mark.parametrize(
    "correo", ["mengana@gmail.com", "ana@miempresa.com", "ana@universidad.edu"]
)
def test_correos_normales_no_son_desechables(correo):
    assert not es_desechable(correo)


# --------------------------------------------------------------------------
# Concesión de la prueba
# --------------------------------------------------------------------------


def test_la_prueba_dura_siete_dias_y_da_acceso(db):
    """Siete días, decisión del titular, y acceso real desde el minuto uno."""
    org = _org(db)
    hoy = date(2026, 8, 18)

    resultado = conceder_prueba(
        db, organizacion_id=org.id, email="ana@example.com", hoy=hoy, es_sqlite=True
    )

    assert resultado.concedida
    assert resultado.dias == 7 == DIAS_PRUEBA_POR_DEFECTO
    assert resultado.vence == date(2026, 8, 24)

    licencia = db.query(Licencia).filter_by(organizacion_id=org.id).one()
    assert licencia.origen == "prueba"
    assert licencia.importe == 0
    assert organizacion_tiene_acceso(db, org.id, hoy=hoy)


def test_la_prueba_caduca_al_octavo_dia(db):
    """El día siguiente al vencimiento el acceso se corta de verdad."""
    org = _org(db)
    hoy = date(2026, 8, 18)
    conceder_prueba(
        db, organizacion_id=org.id, email="ana@example.com", hoy=hoy, es_sqlite=True
    )

    assert organizacion_tiene_acceso(db, org.id, hoy=date(2026, 8, 24))
    assert not organizacion_tiene_acceso(db, org.id, hoy=date(2026, 8, 25))


def test_la_prueba_no_cuenta_como_ingreso(db):
    """Una prueba que sumara a la facturación mentiría en el panel."""
    org = _org(db)
    conceder_prueba(
        db, organizacion_id=org.id, email="ana@example.com", es_sqlite=True
    )
    licencia = db.query(Licencia).filter_by(organizacion_id=org.id).one()
    assert not licencia.es_ingreso


# --------------------------------------------------------------------------
# Anti-abuso: el corazón de la funcionalidad
# --------------------------------------------------------------------------


def test_una_sola_prueba_por_identidad_aunque_cambie_de_organizacion(db):
    """El ataque principal: crear otra empresa para encadenar otra prueba.

    La marca se guarda por identidad de correo, no por organización, así que
    la segunda empresa nace sin licencia y ve la pantalla de planes.
    """
    primera = _org(db, "Primera", "primera")
    segunda = _org(db, "Segunda", "segunda")

    uno = conceder_prueba(
        db, organizacion_id=primera.id, email="ana@example.com", es_sqlite=True
    )
    dos = conceder_prueba(
        db, organizacion_id=segunda.id, email="ana@example.com", es_sqlite=True
    )

    assert uno.concedida
    assert not dos.concedida
    assert dos.motivo == "ya_usada"
    assert db.query(Licencia).filter_by(organizacion_id=segunda.id).count() == 0
    assert not organizacion_tiene_acceso(db, segunda.id)


def test_los_alias_del_mismo_buzon_no_consiguen_una_segunda_prueba(db):
    """Registrarse con `nombre+loquesea@` es el intento más habitual."""
    primera = _org(db, "Primera", "primera")
    segunda = _org(db, "Segunda", "segunda")

    conceder_prueba(
        db,
        organizacion_id=primera.id,
        email="fulano.detal@gmail.com",
        es_sqlite=True,
    )
    reintento = conceder_prueba(
        db,
        organizacion_id=segunda.id,
        email="FulanoDetal+cotizat2@googlemail.com",
        es_sqlite=True,
    )

    assert not reintento.concedida
    assert reintento.motivo == "ya_usada"


def test_la_marca_sobrevive_al_borrado_de_la_organizacion(db):
    """Borrar la empresa no devuelve la prueba: se gastó igual.

    Si la marca cayera con la organización, bastaría con darse de baja y
    volver a empezar cada semana.
    """
    org = _org(db)
    conceder_prueba(
        db, organizacion_id=org.id, email="ana@example.com", es_sqlite=True
    )
    db.query(Licencia).filter_by(organizacion_id=org.id).delete()
    db.query(Organizacion).filter_by(id=org.id).delete()
    db.flush()

    marca = db.query(PruebaConcedida).one()
    assert marca.organizacion_id is None  # SET NULL, no borrado en cascada
    assert marca.email_normalizado == "ana@example.com"
    assert prueba_ya_usada(db, "ana@example.com")


def test_la_unicidad_la_garantiza_la_base_no_el_codigo(db):
    """Dos altas simultáneas no pueden conseguir dos pruebas.

    La comprobación previa en Python no cubre la carrera; la restricción única
    sí. Se fuerza aquí insertando la marca a mano.
    """
    from sqlalchemy.exc import IntegrityError

    db.add(PruebaConcedida(email_normalizado="ana@example.com", dias=7))
    db.flush()
    db.add(PruebaConcedida(email_normalizado="ana@example.com", dias=7))
    with pytest.raises(IntegrityError):
        db.flush()


def test_una_carrera_perdida_no_deja_licencia_huerfana(db):
    """Si la marca ya existe, no debe crearse licencia por otro camino."""
    org = _org(db)
    db.add(PruebaConcedida(email_normalizado="ana@example.com", dias=7))
    db.flush()

    resultado = conceder_prueba(
        db, organizacion_id=org.id, email="ana@example.com", es_sqlite=True
    )

    assert not resultado.concedida
    assert db.query(Licencia).count() == 0


def test_un_correo_desechable_no_recibe_prueba(db):
    """Cinturón y tirantes: el registro ya los bloquea antes de llegar aquí."""
    org = _org(db)
    resultado = conceder_prueba(
        db, organizacion_id=org.id, email="ana@mailinator.com", es_sqlite=True
    )
    assert not resultado.concedida
    assert resultado.motivo == "desechable"
    assert db.query(Licencia).count() == 0


def test_un_email_ilegible_no_recibe_prueba(db):
    org = _org(db)
    resultado = conceder_prueba(
        db, organizacion_id=org.id, email="", es_sqlite=True
    )
    assert not resultado.concedida
    assert resultado.motivo == "email_invalido"


# --------------------------------------------------------------------------
# IP: se guarda, no se bloquea
# --------------------------------------------------------------------------


def test_la_ip_se_guarda_hasheada_nunca_en_claro(db):
    """La tabla no debe contener direcciones legibles.

    Un volcado del registro no puede revelar dónde vive un cliente.
    """
    org = _org(db)
    conceder_prueba(
        db,
        organizacion_id=org.id,
        email="ana@example.com",
        ip="203.0.113.45",
        es_sqlite=True,
    )
    marca = db.query(PruebaConcedida).one()
    assert marca.ip_hash
    assert "203.0.113.45" not in marca.ip_hash
    assert len(marca.ip_hash) == 64


def test_la_misma_ip_no_impide_una_prueba_legitima(db):
    """Decisión explícita del titular: la IP marca, no bloquea.

    Dos compañeros de oficina, o dos clientes de la misma red móvil, comparten
    IP y ambos tienen derecho a su prueba.
    """
    una = _org(db, "Una", "una")
    otra = _org(db, "Otra", "otra")

    primera = conceder_prueba(
        db,
        organizacion_id=una.id,
        email="ana@example.com",
        ip="198.51.100.7",
        es_sqlite=True,
    )
    segunda = conceder_prueba(
        db,
        organizacion_id=otra.id,
        email="luis@example.com",
        ip="198.51.100.7",
        es_sqlite=True,
    )

    assert primera.concedida and segunda.concedida
    hashes = {m.ip_hash for m in db.query(PruebaConcedida).all()}
    assert len(hashes) == 1  # misma IP, mismo hash: el panel puede agruparlas


def test_el_hash_de_ip_es_estable_y_distingue_direcciones():
    assert hash_ip("203.0.113.1") == hash_ip("203.0.113.1")
    assert hash_ip("203.0.113.1") != hash_ip("203.0.113.2")
    assert hash_ip("") == ""


# --------------------------------------------------------------------------
# Configuración
# --------------------------------------------------------------------------


def test_la_duracion_se_puede_cambiar_sin_desplegar(monkeypatch):
    monkeypatch.setenv("COTIZAT_DIAS_PRUEBA", "14")
    assert dias_de_prueba() == 14


def test_una_duracion_absurda_se_recorta(monkeypatch):
    """Un tecleo de más no puede regalar años de producto."""
    monkeypatch.setenv("COTIZAT_DIAS_PRUEBA", "99999")
    assert dias_de_prueba() == 90


def test_valor_no_numerico_cae_al_valor_por_defecto(monkeypatch):
    monkeypatch.setenv("COTIZAT_DIAS_PRUEBA", "muchos")
    assert dias_de_prueba() == 7


def test_la_prueba_se_puede_desactivar(monkeypatch, db):
    monkeypatch.setenv("COTIZAT_DIAS_PRUEBA", "0")
    assert not prueba_activada()
    org = _org(db)
    resultado = conceder_prueba(
        db, organizacion_id=org.id, email="ana@example.com", es_sqlite=True
    )
    assert not resultado.concedida
    assert resultado.motivo == "desactivada"
    assert db.query(Licencia).count() == 0


def test_un_fallo_al_conceder_no_tumba_el_alta(db, monkeypatch):
    """La organización ya está creada: perderla sería mucho peor que la prueba."""
    import app.services.prueba_gratuita as modulo

    def _explota(*_a, **_k):
        raise RuntimeError("base caída")

    monkeypatch.setattr(modulo, "_conceder_en_sqlite", _explota)
    org = _org(db)

    resultado = conceder_prueba(
        db, organizacion_id=org.id, email="ana@example.com", es_sqlite=True
    )

    assert not resultado.concedida
    assert resultado.motivo == "error"
    assert db.query(Organizacion).filter_by(id=org.id).count() == 1


def test_el_mensaje_de_prueba_agotada_ofrece_salida(db):
    """Sin prueba no puede haber callejón sin salida: siempre se puede pagar."""
    primera = _org(db, "Primera", "primera")
    segunda = _org(db, "Segunda", "segunda")
    conceder_prueba(
        db, organizacion_id=primera.id, email="ana@example.com", es_sqlite=True
    )
    resultado = conceder_prueba(
        db, organizacion_id=segunda.id, email="ana@example.com", es_sqlite=True
    )
    assert "plan" in resultado.mensaje.lower()


# --------------------------------------------------------------------------
# Bloqueo en el registro (extremo HTTP)
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "correo", ["nuevo@mailinator.com", "nuevo@yopmail.com", "n@temp-mail.org"]
)
def test_el_registro_rechaza_correos_desechables(cliente_web, correo):
    """No se llega ni a crear la cuenta en el proveedor de identidad.

    Se comprueba por el redirect a `/acceso` con error: si el bloqueo fallara,
    la petición seguiría hacia Supabase y el fallo sería otro (configuración
    ausente), no este mensaje.
    """
    respuesta = cliente_web.post(
        "/registro",
        data={
            "email": correo,
            "password": "clave-larga-segura",
            "password_confirmation": "clave-larga-segura",
            "nombre": "Prueba",
            "acepto_terminos": "1",
        },
        headers={"origin": "https://cotizat.test"},
        follow_redirects=False,
    )

    assert respuesta.status_code == 303
    destino = respuesta.headers["location"]
    assert destino.startswith("/acceso?error=")
    assert "temporal" in destino.lower() or "temporal" in destino


def test_el_rechazo_de_desechables_no_revela_si_el_correo_existe(cliente_web):
    """El mensaje habla del proveedor, nunca de la cuenta.

    Diferenciar «ya registrado» de «no registrado» permitiría enumerar
    clientes, que es justo lo que el resto del flujo evita con cuidado.
    """
    respuesta = cliente_web.post(
        "/registro",
        data={
            "email": "quien-sea@mailinator.com",
            "password": "clave-larga-segura",
            "password_confirmation": "clave-larga-segura",
            "nombre": "Prueba",
            "acepto_terminos": "1",
        },
        headers={"origin": "https://cotizat.test"},
        follow_redirects=False,
    )

    destino = respuesta.headers["location"].lower()
    assert "existe" not in destino
    assert "registrad" not in destino


# --------------------------------------------------------------------------
# Invariantes del SQL de la migración
#
# Sin PostgreSQL en el entorno de pruebas no se puede ejecutar la función, y
# es justo el camino que corre en producción. Estas comprobaciones son la red
# que queda: verifican sobre el texto del SQL las propiedades cuya ausencia
# convertiría un SECURITY DEFINER en un agujero.
# --------------------------------------------------------------------------


@pytest.fixture(scope="module")
def sql_funcion():
    from migrations.versions import (
        a3d9c1e75b28_prueba_gratuita_registro as migracion,
    )

    return migracion.TRIAL_FUNCTION_SQL


def test_la_funcion_fija_su_search_path(sql_funcion):
    """Sin `SET search_path`, un esquema malicioso secuestra la función.

    Es el fallo clásico de SECURITY DEFINER en PostgreSQL.
    """
    assert "SET search_path = pg_catalog, public" in sql_funcion


def test_la_funcion_solo_concede_a_la_organizacion_de_la_sesion(sql_funcion):
    """Sin esta guarda, cualquiera regala licencias a organizaciones ajenas."""
    assert "current_setting('cotizat.organization_id', true)" in sql_funcion
    assert "<> p_organization_id::text" in sql_funcion
    assert "RETURN FALSE" in sql_funcion


def test_la_funcion_no_puede_fabricar_una_licencia_de_pago(sql_funcion):
    """Aunque se llame con parámetros hostiles, solo crea pruebas de valor 0."""
    assert "'prueba'" in sql_funcion
    assert "'pago'" not in sql_funcion


def test_la_duracion_esta_acotada_dentro_de_la_base(sql_funcion):
    """El tope no puede depender solo de la aplicación."""
    assert "LEAST(GREATEST(COALESCE(p_dias, 0), 1), 90)" in sql_funcion


def test_la_carrera_se_resuelve_de_forma_atomica(sql_funcion):
    """`ON CONFLICT DO NOTHING` sobre la clave única es lo que cierra el abuso."""
    assert "ON CONFLICT (email_normalizado) DO NOTHING" in sql_funcion
    assert "IF v_marca_id IS NULL THEN" in sql_funcion


def test_no_concede_si_la_organizacion_ya_tuvo_licencia(sql_funcion):
    assert "FROM public.licencias WHERE organizacion_id = p_organization_id" in sql_funcion


def test_la_marca_de_operador_se_restaura_en_todas_las_salidas(sql_funcion):
    """Una marca de operador filtrada dejaría al cliente con privilegios.

    Hay cuatro salidas tras la elevación (licencia previa, marca duplicada,
    éxito y excepción) y todas deben restaurar el valor anterior.
    """
    cuerpo = sql_funcion.split("PERFORM pg_catalog.set_config('cotizat.es_operador', 'on', true);")[1]
    restauraciones = cuerpo.count("'cotizat.es_operador', v_operador_previo, true") + cuerpo.count(
        "'cotizat.es_operador', COALESCE(v_operador_previo, 'off'), true"
    )
    assert restauraciones == 4, f"salidas sin restaurar: {restauraciones} de 4"
    assert "EXCEPTION WHEN OTHERS THEN" in sql_funcion
    assert "RAISE;" in sql_funcion


def test_la_elevacion_ocurre_antes_de_leer_licencias(sql_funcion):
    """Si se leyera `licencias` bajo RLS, el EXISTS daría siempre falso.

    Ese orden invertido concedería prueba a quien ya la tuvo: fallo abierto.
    """
    pos_elevacion = sql_funcion.index("set_config('cotizat.es_operador', 'on', true)")
    pos_lectura = sql_funcion.index("FROM public.licencias")
    assert pos_elevacion < pos_lectura


def test_la_tabla_de_pruebas_esta_cerrada_a_los_clientes():
    """Como `licencias`: sin marca de operador no se ve ni una fila."""
    from migrations.versions import (
        a3d9c1e75b28_prueba_gratuita_registro as migracion,
    )

    fuente = open(migracion.__file__, encoding="utf-8").read()
    assert "FORCE ROW LEVEL SECURITY" in fuente
    assert "ENABLE ROW LEVEL SECURITY" in fuente
    # Sin política de DELETE: el registro de pruebas gastadas no se borra, o el
    # anti-abuso se podría deshacer desde la propia aplicación.
    assert "cotizat_prueba_delete" not in fuente


def test_la_migracion_encadena_con_la_cabeza_anterior():
    """La prueba gratuita ya no es la cabeza: el consentimiento (E4-038), el
    registro de auditoría (E4-026/027) y las migraciones LatAm (S2) de
    etiqueta fiscal y tasa la siguen, en ese orden."""
    from app.database import EXPECTED_ALEMBIC_HEAD
    from migrations.versions import (
        a3d9c1e75b28_prueba_gratuita_registro as migracion,
        b6d9e4c2a8f1_consentimiento_terminos as consentimiento_migracion,
        c8f1a2b3d4e5_add_etiqueta_fiscal_latam as etiqueta_migracion,
        d2a7c9e4f1b3_audit_log_and_complete_baja as auditoria_migracion,
        d9e2f3a4b5c6_add_tasa_cambio_latam as tasa_migracion,
    )

    from migrations.versions import (
        c5d6e7f8a9b0_merge_currency_heads as merge_migracion,
        e7b3c1d5a204_market_prices_grants_and_rls as precios_migracion,
    )
    # La cabeza actual son los índices de rendimiento, colgados del hotfix
    # de permisos/RLS de los precios por mercado, que a su vez cuelga de la
    # fusión de las ramas de moneda.
    from migrations.versions import (
        b9f4d8a2c6e1_rendimiento_indices_calientes as indices_migracion,
    )
    assert indices_migracion.revision == EXPECTED_ALEMBIC_HEAD
    assert indices_migracion.down_revision == precios_migracion.revision
    assert precios_migracion.down_revision == merge_migracion.revision
    assert tasa_migracion.down_revision == etiqueta_migracion.revision
    assert etiqueta_migracion.down_revision == auditoria_migracion.revision
    assert auditoria_migracion.down_revision == consentimiento_migracion.revision
    assert consentimiento_migracion.down_revision == migracion.revision
    assert migracion.down_revision == "c7f1a3b9d425"


# --------------------------------------------------------------------------
# Anuncio público de la prueba
#
# Una prueba gratuita que el visitante no ve no sirve de nada. Y al revés:
# anunciarla cuando está apagada es prometer algo que el registro no dará.
# Ambos lados importan, así que se comprueban los dos.
# --------------------------------------------------------------------------


# Jinja cachea las plantillas compiladas, no su resultado, y las globales son
# funciones evaluadas en cada render: para cambiar lo que se anuncia basta con
# mover la variable de entorno, sin tocar la caché.


def _paginas_publicas(cliente):
    return {
        "/": cliente.get("/").text,
        "/conocer": cliente.get("/conocer").text,
        "/como-funciona": cliente.get("/como-funciona").text,
        "/pago": cliente.get("/pago").text,
        "/acceso": cliente.get("/acceso").text,
    }


def test_la_prueba_se_anuncia_en_las_paginas_publicas(cliente_web, monkeypatch):
    monkeypatch.setenv("COTIZAT_DIAS_PRUEBA", "7")
    for ruta, html in _paginas_publicas(cliente_web).items():
        assert "7 días gratis" in html or "7 d&iacute;as gratis" in html, (
            f"{ruta} no anuncia la prueba"
        )


def test_el_anuncio_usa_la_duracion_configurada(cliente_web, monkeypatch):
    """Si mañana son 14 días, la landing no puede seguir diciendo 7."""
    monkeypatch.setenv("COTIZAT_DIAS_PRUEBA", "14")
    html = cliente_web.get("/").text
    assert "14 días gratis" in html
    assert "7 días gratis" not in html


def test_apagar_la_prueba_retira_el_anuncio(cliente_web, monkeypatch):
    """El caso que de verdad importa: no prometer lo que no se va a dar.

    Con la prueba apagada, ninguna página pública puede seguir ofreciéndola;
    sería publicidad falsa y el registro la desmentiría acto seguido.
    """
    monkeypatch.setenv("COTIZAT_DIAS_PRUEBA", "0")
    for ruta, html in _paginas_publicas(cliente_web).items():
        assert "días gratis" not in html, f"{ruta} sigue anunciando la prueba"
        assert "d&iacute;as gratis" not in html, f"{ruta} sigue anunciándola"
        assert "gratis" not in html.lower() or ruta == "/pago", (
            f"{ruta} menciona 'gratis' con la prueba apagada"
        )


def test_sin_prueba_la_landing_sigue_llevando_a_los_planes(cliente_web, monkeypatch):
    """Retirar el anuncio no puede dejar la página sin llamada a la acción."""
    monkeypatch.setenv("COTIZAT_DIAS_PRUEBA", "0")
    html = cliente_web.get("/").text
    assert "Ver planes" in html
    assert 'href="/pago"' in html


def test_el_anuncio_promete_lo_mismo_que_hace_el_registro(cliente_web, monkeypatch):
    """La landing dice «sin tarjeta»; el registro no debe pedir ninguna."""
    monkeypatch.setenv("COTIZAT_DIAS_PRUEBA", "7")
    html = cliente_web.get("/acceso").text
    assert "No pedimos tarjeta" in html
    for campo in ("tarjeta", "card", "cvv", "iban"):
        assert f'name="{campo}"' not in html.lower()


def test_no_se_ofrece_la_prueba_a_quien_ya_la_agoto(cliente_web, monkeypatch):
    """`/pago` con un aviso es el destino de quien no tiene derecho a prueba.

    Repetirle allí la oferta sería una burla, así que el bloque se calla.
    """
    monkeypatch.setenv("COTIZAT_DIAS_PRUEBA", "7")
    html = cliente_web.get(
        "/pago", params={"msg": "Ya disfrutaste tu prueba gratuita con este correo."}
    ).text
    assert "Ya disfrutaste tu prueba" in html
    assert "Empieza con 7" not in html
