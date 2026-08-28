"""Vista previa local del panel de analítica (``/admin/analitica``).

Arranca la aplicación real con una base SQLite en memoria sembrada con datos
de ejemplo y sustituye la puerta de operador, para poder recorrer el panel
en el navegador sin Supabase: ``python tools/vista_previa_analitica.py``.

Solo para desarrollo y demostración; no forma parte del despliegue.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

# Base aislada para la preview (mismo mecanismo que la suite).
_TMP = Path(tempfile.mkdtemp(prefix="cotizat-analitica-"))
os.environ["COTIZAT_DB"] = str(_TMP / "preview.db")
os.environ.pop("DATABASE_URL", None)
os.environ.setdefault("COTIZAT_OPERADORES", "titular@cotizat.online")

from fastapi import Request  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.database import Base, get_operator_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import (  # noqa: E402
    EventoProducto,
    Licencia,
    Membresia,
    Organizacion,
    Usuario,
)

HOY = date.today()


def sembrar(Session) -> int:
    """Tres empresas con historias distintas: activa, en riesgo yTrial muerta."""
    empresas = [
        ("Constructora Bermúdez", 210, "activo"),      # usa el producto a diario
        ("Remodelaciones Andes", 45, "riesgo"),        # paga pero dormida
        ("Obras Palacio", 12, "nueva"),                # recién creada
        ("Inversions Ríos", 160, "muerta"),           # vieja, sin licencia
    ]
    engine_orgs = []
    with Session() as db:
        usuarios = []
        for i, (nombre, _dias, _perfil) in enumerate(empresas):
            dias = _dias
            org = Organizacion(
                nombre=nombre,
                slug=f"org-{i}",
                created_at=datetime.utcnow() - timedelta(days=dias),
            )
            usuario = Usuario(
                auth_user_id=f"00000000-0000-4000-8000-{i:012d}",
                email=f"usuario{i}@example.com",
                nombre=nombre.split()[0],
                created_at=datetime.utcnow() - timedelta(days=dias),
            )
            db.add_all([org, usuario])
            db.flush()
            db.add(Membresia(organizacion_id=org.id, usuario_id=usuario.id, rol="propietario"))
            engine_orgs.append((org, usuario, dias, _perfil))
            usuarios.append(usuario)
        db.commit()

        for org, usuario, dias, perfil in engine_orgs:
            alta = datetime.utcnow() - timedelta(days=dias)
            eventos = [("organizacion.creada", alta, {"pais": "ES" if org.id % 2 else "VE"})]
            if perfil in ("activo", "riesgo"):
                # Pagó y activó.
                db.add(Licencia(
                    organizacion_id=org.id, estado="activa", origen="pago",
                    inicio=HOY - timedelta(days=dias - 1),
                    vence=HOY + timedelta(days=365 - dias if perfil == "activo" else 20),
                    importe=89.0,
                ))
                eventos.append(("licencia.activada", alta + timedelta(hours=1),
                                {"plan": "anual", "origen": "stripe"}))
                eventos.append(("pago.checkout_iniciado", alta + timedelta(hours=1),
                                {"plan": "anual"}))
                eventos.append(("pago.compra_registrada", alta + timedelta(hours=2),
                                {"plan": "anual", "metodo": "stripe"}))
            if perfil == "nueva":
                db.add(Licencia(
                    organizacion_id=org.id, estado="activa", origen="prueba",
                    inicio=HOY - timedelta(days=dias), vence=HOY + timedelta(days=7),
                    importe=0.0,
                ))
            # Ciclo de valor: presupuesto, envío, aprobación, PDF, importación.
            if perfil in ("activo", "riesgo", "nueva"):
                cuantos = 6 if perfil == "activo" else (2 if perfil == "nueva" else 3)
                for n in range(cuantos):
                    base = alta + timedelta(days=2 + n * 6)
                    if base > datetime.utcnow():
                        break
                    eventos.append(("presupuesto.creado", base,
                                    {"primero": n == 0, "partidas": 4 + n}))
                    eventos.append(("presupuesto.pdf_descargado", base + timedelta(hours=1), {}))
                    if n % 2 == 0:
                        eventos.append(("presupuesto.enviado_email", base + timedelta(hours=2), {}))
                    if n % 3 == 1:
                        eventos.append(("presupuesto.aprobado", base + timedelta(hours=3), {}))
                    if n % 4 == 2:
                        eventos.append(("importacion.confirmada", base + timedelta(hours=4),
                                        {"formato": "cype_descompuesto", "filas": 12}))
                    if n % 5 == 3:
                        eventos.append(("equipo.invitacion_enviada", base + timedelta(hours=5), {}))
            # Latidos: activa cada 2-3 días; riesgo murió hace 45; nueva a diario.
            if perfil == "activo":
                dias_latido = range(0, dias, 2)
            elif perfil == "riesgo":
                dias_latido = range(45, dias, 3)
            elif perfil == "nueva":
                dias_latido = range(0, dias + 1)
            else:
                dias_latido = range(60, dias, 7)
            for d in dias_latido:
                momento = datetime.utcnow() - timedelta(days=int(d))
                if momento >= alta:
                    eventos.append(("actividad.diaria", momento, {}))
            for accion, creado, detalle in eventos:
                db.add(EventoProducto(
                    organizacion_id=org.id, accion=accion,
                    actor_email=usuario.email,
                    detalle=json.dumps(detalle), created_at=creado,
                ))
        # Registros globales recientes (países mixtos).
        for i, pais in enumerate(["ES", "ES", "VE", "MX", "ES", "CO", "VE", "ES"]):
            db.add(EventoProducto(
                organizacion_id=None, actor_email=f"registro{i}@example.com",
                accion="cuenta.registrada", detalle=json.dumps({"pais": pais}),
                created_at=datetime.utcnow() - timedelta(days=i * 3 + 1),
            ))
        db.commit()
        return engine_orgs[0][1].id


def main() -> None:
    import uvicorn

    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    usuario_id = sembrar(Session)

    def _db_operador(request: Request):
        db = Session()
        db.info["usuario_id"] = usuario_id
        db.info["auth_email"] = "titular@cotizat.online"
        db.info["es_operador"] = True
        request.state.operador_preview = True
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_operator_db] = _db_operador
    print("Panel de analítica en http://localhost:8000/admin/analitica")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")


if __name__ == "__main__":
    main()
