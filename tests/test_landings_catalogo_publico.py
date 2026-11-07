"""Las landings de CL/ES venden el software, no el catálogo público gratuito."""

import pytest


@pytest.mark.parametrize("cc", ("cl", "es"))
def test_cl_es_no_muestran_catalogo_publico_en_el_cuerpo(cliente_web, cc):
    response = cliente_web.get(f"/{cc}/")
    assert response.status_code == 200
    main = response.text.split("<main", 1)[1].split("</main>", 1)[0]

    # No hay tabla, índice público ni tarjeta que saque al usuario del funnel.
    assert 'class="mercados-precios"' not in main
    assert "Explorar precios de obra" not in main
    assert f'href="/{cc}/precios' not in main
    assert 'id="precios-mercado"' not in main

    # Sí se explica el catálogo cargado que el cliente recibe dentro del plan.
    assert "Tu catálogo ya viene cargado" in main
    assert 'id="primer-valor"' in main
    assert 'id="catalogo-paises"' in main


@pytest.mark.parametrize("cc", ("mx", "co"))
def test_mercados_de_control_conservan_su_catalogo_publico(cliente_web, cc):
    response = cliente_web.get(f"/{cc}/")
    assert response.status_code == 200
    main = response.text.split("<main", 1)[1].split("</main>", 1)[0]

    assert 'class="mercados-precios"' in main
    assert "Explorar precios de obra" in main


def test_landing_de_espana_sigue_vendiendo_cotizat_y_el_software(cliente_web):
    response = cliente_web.get("/es/")
    assert response.status_code == 200
    assert "<title>CotizaT: software de presupuestos de obra y reformas para España" in response.text
    assert "Software de presupuestos de obra y reformas para España" in response.text
    assert "/acceso" in response.text
