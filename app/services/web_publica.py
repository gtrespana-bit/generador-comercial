"""Lectura pública del contenido web gobernado desde el panel (Fase 3).

Nuña sesión de navegador (sin ``cotizat.es_operador``) lee únicamente lo que
PostgreSQL permite vía RLS: contenido publicado, avisos activos y releases
publicadas. En SQLite las rutas públicas también limitan a esos estados para
que el comportamiento sea portable y las pruebas no dependan de un motor.

Nunca se abre una sesión de organización ni se desactiva el aislamiento.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from ..models import AvisoWeb, ContenidoWeb, ReleaseWeb


def contenido_publico(db: Session, clave: str) -> dict | None:
    fila = db.query(ContenidoWeb).filter(ContenidoWeb.clave == clave).one_or_none()
    if fila is None or not fila.publicado:
        return None
    try:
        import json

        datos = json.loads(fila.publicado)
    except (TypeError, ValueError):
        return None
    return datos if isinstance(datos, dict) else None


def avisos_publicos(db: Session, hoy: date | None = None) -> list[AvisoWeb]:
    hoy = hoy or date.today()
    return db.query(AvisoWeb).filter(
        AvisoWeb.activo.is_(True),
        (AvisoWeb.inicio.is_(None) | (AvisoWeb.inicio <= hoy)),
        (AvisoWeb.fin.is_(None) | (AvisoWeb.fin >= hoy)),
    ).order_by(AvisoWeb.created_at.desc(), AvisoWeb.id.desc()).all()


def releases_publicas(db: Session) -> list[ReleaseWeb]:
    return db.query(ReleaseWeb).filter(
        ReleaseWeb.publicado.is_(True)
    ).order_by(ReleaseWeb.fecha.desc(), ReleaseWeb.id.desc()).all()


def contexto_web_publico(db: Session) -> dict:
    """Contexto compacto (claves conocidas + avisos + releases)."""
    claves = (
        "landing.hero",
        "landing.outcomes",
        "seo.software-presupuestos",
        "seo.apu",
        "seo.remodelacion",
    )
    contenido = {}
    for clave in claves:
        dato = contenido_publico(db, clave)
        if dato is not None:
            contenido[clave] = dato
    return {
        "contenido": contenido,
        "avisos": avisos_publicos(db),
        "releases": releases_publicas(db),
    }
