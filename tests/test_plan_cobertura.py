"""Matriz de cobertura y diccionario de sinónimos del catálogo extenso."""
from pathlib import Path

from app.services.busqueda_catalogo import (
    alias_para_texto,
    estadisticas_diccionario,
    variantes_consulta,
)
from basedatos_partidas.planificar_cobertura import construir


def test_matriz_cubre_los_18_capitulos_y_suma_objetivos():
    matriz = construir()
    fuentes = list(Path("basedatos_partidas/datos/descompuestos").glob("*.json"))
    assert matriz["partidas_actuales"] == len(fuentes)
    assert matriz["objetivo_minimo"] == 3000
    assert matriz["objetivo_amplio"] == 5000
    assert len(matriz["capitulos"]) == 18
    subcapitulos = [
        sub for capitulo in matriz["capitulos"]
        for sub in capitulo["subcapitulos"]
    ]
    assert len(subcapitulos) == 172
    assert sum(s["objetivo_minimo"] for s in subcapitulos) == 3000
    assert sum(s["objetivo_amplio"] for s in subcapitulos) == 5000
    assert all(s["operaciones_requeridas"] for s in subcapitulos)
    assert all(s["variaciones_requeridas"] for s in subcapitulos)
    # Todos los subcapítulos tienen cobertura: el mínimo de 3.000 partidas se
    # alcanzó y ya no queda ningún subcapítulo vacío.
    assert not any(s["estado"] == "sin_cobertura" for s in subcapitulos)


def test_diccionario_es_bidireccional_y_cubre_todos_los_capitulos():
    estadisticas = estadisticas_diccionario()
    assert estadisticas["capitulos_cubiertos"] == 18
    assert estadisticas["grupos"] >= 140
    assert estadisticas["terminos"] >= 650

    assert "hormigon" in alias_para_texto("Concreto armado", "05")
    assert "concreto" in alias_para_texto("Hormigón armado", "05")
    assert "tomacorriente" in alias_para_texto("Enchufe doble", "09")
    assert "cielo" in alias_para_texto("Falso techo registrable", "12")


def test_variantes_de_consulta_expanden_vocabulario_de_oficio():
    grupos = variantes_consulta("enchufe")
    assert grupos and "tomacorriente" in grupos[0]
    grupos = variantes_consulta("contrapiso")
    assert grupos and "afirmado" in grupos[0]
    grupos = variantes_consulta("fontaneria")
    assert grupos and "plomeria" in grupos[0]
