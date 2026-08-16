"""E4-002 / E4-009 — autorización centralizada por rol de membresía.

La matriz de capacidades vive en `app/permisos.py` como única fuente de
verdad; estas pruebas la fijan y además escanean el código para que ningún
check de rol vuelva a escribirse inline (las rutas deben usar los
predicados), salvo la guardia de bajo nivel de `app.models` que es defensa en
profundidad y no depende de este módulo.
"""
from pathlib import Path

import pytest

from app.models import PermisoOrganizacionError
from app.permisos import (
    ROLES_ESCRITURA,
    ROLES_GESTION,
    ROLES_VALIDOS,
    ROL_PROPIETARIO,
    es_lectura,
    es_propietario,
    exigir_escritura,
    exigir_gestion,
    exigir_propietario,
    puede_escribir,
    puede_gestionar,
    rol_actual,
)


class _Sesion:
    def __init__(self, rol):
        self.info = {"rol_membresia": rol}


# ---------------------------------------------------------------------------
# La matriz de capacidades (fuente única de verdad)
# ---------------------------------------------------------------------------

def test_conjuntos_de_roles_son_los_declarados():
    assert ROLES_VALIDOS == ("lectura", "miembro", "administrador", "propietario")
    assert ROLES_ESCRITURA == frozenset({"miembro", "administrador", "propietario"})
    assert ROLES_GESTION == frozenset({"administrador", "propietario"})
    assert ROL_PROPIETARIO == "propietario"


def test_matriz_lectura_y_escritura():
    for rol in ROLES_VALIDOS:
        db = _Sesion(rol)
        assert es_lectura(db) == (rol == "lectura"), rol
        assert puede_escribir(db) == (rol != "lectura"), rol
        assert puede_gestionar(db) == (rol in {"administrador", "propietario"}), rol
        assert es_propietario(db) == (rol == "propietario"), rol


def test_sin_contexto_de_rol_nada_queda_permitido():
    db = _Sesion(None)
    assert rol_actual(db) == ""
    assert not puede_escribir(db)
    assert not puede_gestionar(db)
    assert not es_propietario(db)
    assert not es_lectura(db)


# ---------------------------------------------------------------------------
# Versiones que lanzan excepción
# ---------------------------------------------------------------------------

def test_exigir_escritura_lanza_para_lectura_y_pasa_para_el_resto():
    with pytest.raises(PermisoOrganizacionError, match="solo lectura"):
        exigir_escritura(_Sesion("lectura"))
    for rol in ("miembro", "administrador", "propietario"):
        exigir_escritura(_Sesion(rol))  # no lanza


def test_exigir_gestion_solo_admite_propietario_y_administrador():
    for rol in ("lectura", "miembro"):
        with pytest.raises(PermisoOrganizacionError):
            exigir_gestion(_Sesion(rol))
    exigir_gestion(_Sesion("administrador"))
    exigir_gestion(_Sesion("propietario"))


def test_exigir_propietario_y_mensajes_personalizados():
    with pytest.raises(PermisoOrganizacionError, match="mensaje concreto"):
        exigir_gestion(_Sesion("miembro"), mensaje="mensaje concreto")
    with pytest.raises(PermisoOrganizacionError, match="solo la dueña"):
        exigir_propietario(_Sesion("administrador"), mensaje="solo la dueña")
    exigir_propietario(_Sesion("propietario"))


# ---------------------------------------------------------------------------
# Regresión estática: no deben reaparecer checks de rol escritos a mano
# ---------------------------------------------------------------------------

def test_las_rutas_no_reinventan_checks_de_rol_inline():
    """Cualquier comprobación de rol en main.py debe pasar por app/permisos.

    Se permiten las lecturas (pasar el rol a las plantillas) y la asignación
    a variables, pero no comparaciones de conjuntos escritas a mano.
    """
    fuentes = Path("app")
    patrones_prohibidos = (
        'rol_membresia") == "lectura"',
        'rol_membresia") != "propietario"',
        'rol_membresia") not in {',
        'rol_membresia") in {',
        'rol_membresia"] == "lectura"',
        'rol_membresia"] in {',
    )
    hallazgos = []
    for ruta in sorted(fuentes.rglob("*.py")):
        if "__pycache__" in ruta.parts:
            continue
        texto = ruta.read_text(encoding="utf-8")
        for patron in patrones_prohibidos:
            if patron in texto:
                hallazgos.append(f"{ruta}: {patron}")
    # La guardia de bajo nivel de SQLAlchemy vive en models.py y no depende
    # de permisos (defensa en profundidad); es la única excepción legítima.
    hallazgos = [h for h in hallazgos if not h.startswith("app/models.py")]
    assert hallazgos == []
