"""Precios de referencia y divisa: cobertura de los 23 mercados.

Australia y Canadá llevaban meses sin tasa verificada y cuatro mercados (AU,
CA, IE, US) no podían ni importar una matriz de precios porque su moneda no
estaba en el importador. Nada lo delataba: el signo de registro cogía la tasa
de la API y el importador solo se usa de vez en cuando.

Estas pruebas son la alarma. Si se añade un mercado y se le olvida la moneda o
la tasa, aquí salta, no en producción.
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.paises import PAISES
from app.services.importador_precios_mercado import MONEDA_PAIS
from app.services.tasa import TASAS_SUGERIDAS, tasa_fecha_verificacion, tasa_sugerida
from app.services.unidades_precio import (
    convertir_precio_unidad,
    normalizar_unidad,
    sistema_unidades_pais,
)
from app.services.vigencia_precios import (
    CADUCADA,
    OBSOLETA,
    POR_REVISAR,
    SIN_FECHA,
    VIGENTE,
    Vigencia,
    evaluar_vigencia,
)


# ─────────────────────────────────────────────────────────────────────────────
# Divisa: ningún mercado se queda atrás
# ─────────────────────────────────────────────────────────────────────────────

def test_todo_mercado_tiene_moneda_en_el_importador():
    """Sin moneda en el importador, ese mercado no puede cargar precios."""
    faltan = sorted(set(PAISES) - set(MONEDA_PAIS))
    assert faltan == [], f"mercados sin moneda en MONEDA_PAIS: {faltan}"


def test_todo_mercado_tiene_tasa_verificada():
    """La moneda de cada mercado tiene tasa comprobada, no un hueco en blanco.

    Ecuador, Panamá, El Salvador, Venezuela y Estados Unidos usan USD (o un
    balboa a la par), así que entran con 1.0.
    """
    sin_tasa = {}
    for codigo, pais in PAISES.items():
        if tasa_sugerida(pais["moneda"]) is None:
            sin_tasa[codigo] = pais["moneda"]
    assert sin_tasa == {}, f"mercados sin tasa verificada: {sin_tasa}"


def test_la_moneda_del_importador_coincide_con_la_del_mercado():
    """Dos listas que dicen lo mismo no pueden discrepar."""
    for codigo, moneda in MONEDA_PAIS.items():
        assert PAISES[codigo]["moneda"] == moneda, (
            f"{codigo}: el importador espera {moneda} y el mercado usa "
            f"{PAISES[codigo]['moneda']}"
        )


def test_aud_y_cad_tienen_tasa_y_son_creibles():
    """Los dos huecos que había. Cifras de los bancos centrales, 16/10/2026."""
    assert tasa_sugerida("AUD") == pytest.approx(1.4395, abs=1e-4)
    assert tasa_sugerida("CAD") == pytest.approx(1.4154, abs=1e-4)
    # 1 USD compra más de un dólar australiano y más de un canadiense.
    for moneda in ("AUD", "CAD"):
        assert 1.2 < tasa_sugerida(moneda) < 1.8, moneda


def test_cada_tasa_lleva_la_fecha_en_que_se_comprobo():
    """Una sola fecha para toda la tabla deja de ser cierta en cuanto se
    verifica una moneda en otro día."""
    assert tasa_fecha_verificacion("AUD") == "2026-10-16"
    assert tasa_fecha_verificacion("CAD") == "2026-10-16"
    assert tasa_fecha_verificacion("GBP") == "2026-10-16"
    # La revisión general sigue siendo la referencia para las de agosto.
    assert tasa_fecha_verificacion("COP") == "2026-08-25"


def test_una_moneda_sin_tasa_no_luce_fecha_de_comprobacion():
    """Ponerle fecha a un número que no existe lo haría parecer verificado."""
    assert tasa_sugerida("BRL") is None
    assert tasa_fecha_verificacion("BRL") == ""
    assert tasa_fecha_verificacion("XXX") == ""


def test_la_libra_sigue_en_la_tasa_de_corte_de_la_matriz_britanica():
    """Fase 0 fijó 1 USD = 0,7502 GBP para construir los precios GB. Si esto se
    mueve, la matriz y el cambio de divisas dejan de contar lo mismo."""
    assert TASAS_SUGERIDAS["GBP"] == pytest.approx(0.7502, abs=1e-9)


# ─────────────────────────────────────────────────────────────────────────────
# Unidades: el mercado imperial
# ─────────────────────────────────────────────────────────────────────────────

def test_solo_estados_unidos_mide_en_imperial():
    imperiales = [c for c in PAISES if sistema_unidades_pais(c) == "imperial"]
    assert imperiales == ["US"]
    assert sistema_unidades_pais("GB") == "metrico"
    assert sistema_unidades_pais("AU") == "metrico"


def test_normalizar_unidad_recoge_las_formas_de_escribirlas():
    assert normalizar_unidad("m²") == "m2"
    assert normalizar_unidad("m³") == "m3"
    assert normalizar_unidad("h") == "hora"
    assert normalizar_unidad("und") == "ud"
    assert normalizar_unidad("sqft") == "ft2"
    assert normalizar_unidad("cuyd") == "yd3"
    assert normalizar_unidad("") == ""


@pytest.mark.parametrize(
    "precio,origen,destino,esperado",
    [
        # Un metro cuadrado tiene 10,76 pies cuadrados: el precio por metro es
        # 10,76 veces el del pie, no 0,09 veces.
        (12.50, "ft2", "m2", 134.55),
        (3.20, "lb", "kg", 7.05),
        (4.80, "gal", "l", 1.27),
        (2.10, "ft", "m", 6.89),
        (185.0, "yd3", "m3", 241.97),
        (45.0, "yd2", "m2", 53.82),
        (1.0, "in", "m", 39.37),
    ],
)
def test_conversion_de_precios_imperial_a_metrico(precio, origen, destino, esperado):
    assert convertir_precio_unidad(precio, origen, destino) == pytest.approx(esperado, abs=0.01)


def test_la_misma_unidad_devuelve_el_precio_intacto():
    assert convertir_precio_unidad(7.5, "m2", "m2") == 7.5
    assert convertir_precio_unidad(7.5, "kg", "kg") == 7.5


def test_sin_conversion_posible_devuelve_none_nunca_el_precio_original():
    """Devolver el importe sin tocar guardaría un precio correcto en apariencia
    y nueve veces equivocado en la realidad."""
    assert convertir_precio_unidad(5.0, "ft2", "kg") is None
    assert convertir_precio_unidad(5.0, "hora", "m2") is None
    assert convertir_precio_unidad(5.0, "", "m2") is None
    assert convertir_precio_unidad(5.0, "m2", "") is None


def test_el_galon_es_el_estadounidense():
    """El galón US (3,785 l) y el imperial (4,546 l) no son lo mismo. Aquí
    aplica el US porque solo convierte Estados Unidos."""
    assert convertir_precio_unidad(3.785411784, "gal", "l") == pytest.approx(1.0, abs=1e-6)


# ─────────────────────────────────────────────────────────────────────────────
# Vigencia de los precios
# ─────────────────────────────────────────────────────────────────────────────

HOY = date(2026, 10, 18)


def _hace(dias: int) -> date:
    return HOY - timedelta(days=dias)


@pytest.mark.parametrize(
    "dias,confianza,esperado",
    [
        (0, "referencia", VIGENTE),
        (179, "referencia", VIGENTE),
        (180, "referencia", VIGENTE),      # el límite aún es vigente
        (181, "referencia", POR_REVISAR),
        (364, "referencia", POR_REVISAR),
        (365, "referencia", POR_REVISAR),  # el límite aún es «por revisar»
        (366, "referencia", OBSOLETA),
        (900, "referencia", OBSOLETA),
        # Lo provisional tiene la mitad de plazo.
        (89, "provisional", VIGENTE),
        (91, "provisional", POR_REVISAR),
        (179, "provisional", POR_REVISAR),
        (181, "provisional", OBSOLETA),
    ],
)
def test_umbrales_de_antiguedad(dias, confianza, esperado):
    v = evaluar_vigencia(_hace(dias), None, confianza, hoy=HOY)
    assert v.estado == esperado, f"{dias} días, {confianza}: {v.estado} != {esperado}"
    assert v.dias == dias


def test_la_fecha_de_vigencia_vencida_pesa_mas_que_la_consulta_reciente():
    """Si el proveedor dijo «hasta ayer», da igual que lo consultáramos hoy."""
    v = evaluar_vigencia(
        fecha_consulta=HOY,
        fecha_vigencia=HOY - timedelta(days=1),
        confianza="confirmado",
        hoy=HOY,
    )
    assert v.estado == CADUCADA
    assert v.requiere_revision is True
    assert v.presentable is False


def test_vigencia_futura_no_cuenta_como_caducada():
    v = evaluar_vigencia(
        fecha_consulta=_hace(400),
        fecha_vigencia=HOY + timedelta(days=30),
        hoy=HOY,
    )
    assert v.estado == OBSOLETA  # por antigüedad de la consulta, no caducada


def test_sin_ninguna_fecha_no_se_inventa_que_esta_vigente():
    """Un precio sin datar no es un precio vigente: es uno del que no se sabe."""
    v = evaluar_vigencia(None, None, "referencia", hoy=HOY)
    assert v.estado == SIN_FECHA
    assert v.dias is None
    assert v.requiere_revision is True
    # Sin fecha no es tan grave como caducado: se puede usar avisando.
    assert v.presentable is True


def test_fecha_en_iso_o_datetime_se_entiende_igual():
    v = evaluar_vigencia(_hace(200).isoformat(), None, "referencia", hoy=HOY)
    assert v.estado == POR_REVISAR
    assert v.fecha_consulta == _hace(200)


def test_fecha_futura_no_se_premia():
    """Dato mal cargado: se trata como recién consultado en vez de romper."""
    v = evaluar_vigencia(HOY + timedelta(days=30), None, "referencia", hoy=HOY)
    assert v.estado == VIGENTE
    assert v.dias == 0


def test_etiquetas_en_los_dos_idiomas():
    v = evaluar_vigencia(_hace(10), None, "referencia", hoy=HOY)
    assert v.etiqueta() == "Vigente"
    assert v.etiqueta("en") == "Current"
    caducada = evaluar_vigencia(HOY, _hace(1), "referencia", hoy=HOY)
    assert caducada.etiqueta() == "Caducado"
    assert caducada.etiqueta("en") == "Expired"


def test_solo_lo_vigente_no_pide_revision():
    assert Vigencia(VIGENTE).requiere_revision is False
    for estado in (POR_REVISAR, OBSOLETA, CADUCADA, SIN_FECHA):
        assert Vigencia(estado).requiere_revision is True

# ─────────────────────────────────────────────────────────────────────────────
# El importador, de verdad
# ─────────────────────────────────────────────────────────────────────────────

CABECERA = (
    "codigo_recurso;descripcion;categoria;unidad_fuente;pais_codigo;moneda;"
    "precio_referencia;precio_min;precio_max;fuente;fecha_consulta;confianza;"
    "incluye_iva;incluye_transporte;origen;observaciones"
)


def _escribir_csv(ruta, filas):
    ruta.write_text("\n".join([CABECERA] + filas) + "\n", encoding="utf-8")
    return ruta


def _fila(codigo, unidad, precio, pais="US", moneda="USD", minimo="", maximo=""):
    """Fila de matriz. La referencia nacional exige rango, así que si no se
    dan se deriva del precio (±10 %)."""
    precio_f = float(precio)
    minimo = minimo or f"{precio_f * 0.9:.4f}"
    maximo = maximo or f"{precio_f * 1.1:.4f}"
    return (
        f"{codigo};{codigo};materiales;{unidad};{pais};{moneda};{precio};"
        f"{minimo};{maximo};docs/INVESTIGACION_PRECIOS_REINO_UNIDO.md;"
        f"2026-10-18;referencia;no;no;nacional;"
    )


def test_el_importador_convierte_una_matriz_imperial(entorno, tmp_path):
    """Una matriz de Estados Unidos cotizada en pies cuadrados y libras entra
    y se guarda en metros cuadrados y kilos, que es como cuenta el recurso."""
    from app.models import Recurso
    from app.services.importador_precios_mercado import importar_matriz_csv

    Session, ids, _ = entorno
    db = Session()
    db.info["organizacion_id"] = ids[0]
    # El recurso mide en métrico: es el catálogo, no la tarifa del proveedor.
    db.add(Recurso(organizacion_id=ids[0], codigo="MT-PISO", descripcion="Suelo",
                   unidad="m2", precio=1, moneda="USD"))
    db.add(Recurso(organizacion_id=ids[0], codigo="MT-CEM", descripcion="Cemento",
                   unidad="kg", precio=1, moneda="USD"))
    db.commit()

    csv = _escribir_csv(tmp_path / "us.csv", [
        _fila("MT-PISO", "ft2", "12.50"),   # 12,50 $/ft² -> 134,55 $/m²
        _fila("MT-CEM", "lb", "3.20"),      # 3,20 $/lb  -> 7,05 $/kg
    ])
    resultado = importar_matriz_csv(db, csv, aplicar=True)
    db.commit()

    assert not resultado["errores"], resultado["errores"]
    assert resultado["creadas_o_actualizadas"] == 2

    guardados = {
        p.codigo_recurso: p.precio
        for p in db.query(
            __import__("app.models", fromlist=["PrecioRecursoMercado"]).PrecioRecursoMercado
        ).all()
    }
    assert guardados["MT-PISO"] == pytest.approx(134.55, abs=0.01)
    assert guardados["MT-CEM"] == pytest.approx(7.05, abs=0.01)


def test_un_mercado_metrico_no_acepta_unidades_imperiales(entorno, tmp_path):
    """Lo que salva a Estados Unidos no puede colarse en España: allí un pie
    cuadrado es un dato mal puesto, no una unidad distinta."""
    from app.models import Recurso
    from app.services.importador_precios_mercado import importar_matriz_csv

    Session, ids, _ = entorno
    db = Session()
    db.info["organizacion_id"] = ids[0]
    db.add(Recurso(organizacion_id=ids[0], codigo="MT-PISO", descripcion="Suelo",
                   unidad="m2", precio=1, moneda="USD"))
    db.commit()

    csv = _escribir_csv(tmp_path / "es.csv", [_fila("MT-PISO", "ft2", "12.50",
                                                    pais="ES", moneda="EUR")])
    resultado = importar_matriz_csv(db, csv, aplicar=True)
    assert resultado["creadas_o_actualizadas"] == 0
    assert any("unidad" in e for e in resultado["errores"])


def test_unidades_incompatibles_se_rechazan_incluso_en_imperial(entorno, tmp_path):
    """Horas contra metros no hay conversión que valga."""
    from app.models import Recurso
    from app.services.importador_precios_mercado import importar_matriz_csv

    Session, ids, _ = entorno
    db = Session()
    db.info["organizacion_id"] = ids[0]
    db.add(Recurso(organizacion_id=ids[0], codigo="MT-PISO", descripcion="Suelo",
                   unidad="m2", precio=1, moneda="USD"))
    db.commit()

    csv = _escribir_csv(tmp_path / "us.csv", [_fila("MT-PISO", "lb", "3.20")])
    resultado = importar_matriz_csv(db, csv, aplicar=True)
    assert resultado["creadas_o_actualizadas"] == 0
    assert any("unidad" in e for e in resultado["errores"])


def test_antes_de_escribir_se_valida_toda_la_matriz(entorno, tmp_path):
    """Una fila mala no puede dejar media matriz cargada."""
    from app.models import Recurso
    from app.services.importador_precios_mercado import importar_matriz_csv

    Session, ids, _ = entorno
    db = Session()
    db.info["organizacion_id"] = ids[0]
    db.add(Recurso(organizacion_id=ids[0], codigo="MT-PISO", descripcion="Suelo",
                   unidad="m2", precio=1, moneda="USD"))
    db.commit()

    csv = _escribir_csv(tmp_path / "us.csv", [
        _fila("MT-PISO", "ft2", "12.50"),
        _fila("MT-INEXISTENTE", "ft2", "9.90"),
    ])
    resultado = importar_matriz_csv(db, csv, aplicar=True)
    assert any("no encontrado" in e for e in resultado["errores"])


def test_irlanda_australia_y_canada_ya_pueden_importar(entorno, tmp_path):
    """Los tres mercados que faltaban. Métricos: entran sin convertir."""
    from app.models import Recurso
    from app.services.importador_precios_mercado import importar_matriz_csv

    Session, ids, _ = entorno
    db = Session()
    db.info["organizacion_id"] = ids[0]
    db.add(Recurso(organizacion_id=ids[0], codigo="MT-PISO", descripcion="Suelo",
                   unidad="m2", precio=1, moneda="USD"))
    db.commit()

    for pais, moneda in (("IE", "EUR"), ("AU", "AUD"), ("CA", "CAD")):
        csv = _escribir_csv(tmp_path / f"{pais}.csv",
                            [_fila("MT-PISO", "m2", "48.00", pais=pais, moneda=moneda)])
        resultado = importar_matriz_csv(db, csv, aplicar=True)
        assert not resultado["errores"], (pais, resultado["errores"])
        assert resultado["creadas_o_actualizadas"] == 1


def test_el_rango_se_convierte_con_el_mismo_factor_que_el_precio(entorno, tmp_path):
    """Si el precio pasa de pies cuadrados a metros y el rango se queda en
    pies, la ficha dice «134,55 $/m² (11–14)» y el rango deja de cuadrar.

    Fue un descuido real al montar la conversión: se convirtió
    ``precio_referencia`` y se dejaron ``precio_min`` y ``precio_max`` como
    venían.
    """
    from app.models import PrecioRecursoMercado, Recurso
    from app.services.importador_precios_mercado import importar_matriz_csv

    Session, ids, _ = entorno
    db = Session()
    db.info["organizacion_id"] = ids[0]
    db.add(Recurso(organizacion_id=ids[0], codigo="MT-PISO", descripcion="Suelo",
                   unidad="m2", precio=1, moneda="USD"))
    db.commit()

    csv = _escribir_csv(tmp_path / "us.csv", [
        _fila("MT-PISO", "ft2", "12.50", minimo="10.00", maximo="15.00"),
    ])
    resultado = importar_matriz_csv(db, csv, aplicar=True)
    db.commit()
    assert not resultado["errores"], resultado["errores"]

    guardado = db.query(PrecioRecursoMercado).first()
    # 12,50 $/ft² = 134,55 $/m²; el rango 10–15 $/ft² = 107,64–161,46 $/m².
    assert guardado.precio == pytest.approx(134.55, abs=0.01)
    assert guardado.precio_min == pytest.approx(107.64, abs=0.01)
    assert guardado.precio_max == pytest.approx(161.46, abs=0.01)
    # Y el precio sigue dentro de su rango, como debe.
    assert guardado.precio_min <= guardado.precio <= guardado.precio_max


# ─────────────────────────────────────────────────────────────────────────────
# Efecto secundario: el detector de precios inflados
# ─────────────────────────────────────────────────────────────────────────────

def test_una_divisa_casi_a_la_par_no_hace_sospechoso_un_precio_correcto():
    """Regresión: al añadir AUD (1,4395) y CAD (1,4154), el detector de precios
    inflados empezó a ver conversiones donde no las había.

    Con una tolerancia amplia, 4,89 «se explica» como 3,40 multiplicado por
    1,4395, y una partida bien puesta pasaba a repararse sola. Una tasa cercana
    a 1 no demuestra nada: que dos partidas se parezcan en precio es normal,
    no es un error de divisa.

    Por eso las candidatas exigen un multiplicador mínimo: la divisa más
    barata de la tabla ronda 3,4 por dólar, así que por debajo de 3 es ruido.
    """
    from app.services.precios_anomalos import (
        FACTOR_MINIMO_CREIBLE,
        _factor_por_referencia,
    )

    # 4,89 frente a una gemela oficial de 3,40: un 44 % más caro, sin más.
    assert _factor_por_referencia(4.89, 3.40, [1.4395, 1.4154]) == 0.0
    # Con una tasa de verdad sí hay caso: 4,89 × 3128,65.
    assert _factor_por_referencia(4.89 * 3128.65, 4.89, [3128.65]) == pytest.approx(3128.65)
    # Y el umbral deja fuera, por diseño, a las divisas casi a la par.
    assert FACTOR_MINIMO_CREIBLE > 1.4395
    for tasa in TASAS_SUGERIDAS.values():
        if tasa and tasa > 1.0:
            assert tasa >= FACTOR_MINIMO_CREIBLE or tasa in (1.4395, 1.4154), tasa


def test_las_divisas_casi_a_la_par_no_se_usan_para_reparar(entorno):
    """Una partida bien puesta sigue estándolo después de reparar el catálogo."""
    from app.models import Partida

    Session, _ids, _rol = entorno
    with Session() as db:
        db.add(Partida(nombre="Retirada de rodapié existente.", unidad="m",
                       precio_unitario=4.89))
        db.commit()
        from app.services.precios_anomalos import detectar_precios_anomalos

        assert detectar_precios_anomalos(db) == []
