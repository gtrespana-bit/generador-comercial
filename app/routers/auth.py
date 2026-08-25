"""Rutas de identidad: acceso, registro, cuenta, organizaciones, equipo e invitaciones."""  # E4-001 — router por dominio

from fastapi import APIRouter

from . import common
from .common import *  # noqa: F401,F403  (re-exporta modelos, servicios y utilidades)
from ..analytics import encolar_evento_ga
from ..services import auditoria

router = APIRouter()

@router.get("/acceso", response_class=HTMLResponse)
def acceso(request: Request, next: str = ""):
    error = request.query_params.get("error", "")
    mensaje = request.query_params.get("msg", "")
    try:
        SupabaseAuthSettings.from_environment()
        configurado = True
    except AuthNotConfigured as exc:
        configurado = False
        error = error or str(exc)
    # Lista de países del selector de registro. Se sirve en lugar de
    # hardcodearlos en la plantilla: si mañana se añade un mercado nuevo
    # (Brasil, Estados Unidos, …) aparece solo, sin tocar HTML.
    from ..paises import lista_paises
    return TEMPLATES.TemplateResponse(
        request,
        "auth/access.html",
        {
            "error": error,
            "msg": mensaje,
            "auth_configured": configurado,
            "next": _next_seguro(next, "/inicio"),
            "paises": lista_paises(),
            "pais_preseleccionado": (
                str(request.query_params.get("pais", "") or "").strip().upper()
                or str(request.cookies.get("cotizat_pais", "") or "").strip().upper()
            ),
        },
    )


@router.get("/recuperar-acceso", response_class=HTMLResponse)
def recuperar_acceso_form(request: Request):
    return TEMPLATES.TemplateResponse(
        request,
        "auth/recover.html",
        {
            "error": request.query_params.get("error", ""),
            "msg": request.query_params.get("msg", ""),
        },
    )


@router.post("/recuperar-acceso")
async def solicitar_recuperacion(request: Request):
    form = await request.form()
    email = str(form.get("email") or "").strip()
    mensaje = "Si la cuenta existe, Supabase enviará un enlace para restablecer la contraseña."
    try:
        settings = SupabaseAuthSettings.from_environment()
        redirect_to = password_reset_redirect_url()
        await run_in_threadpool(
            common.SupabaseAuthClient(settings).request_password_reset,
            email,
            redirect_to,
        )
    except InvalidCredentials:
        # Respuesta deliberadamente indistinguible para no enumerar cuentas.
        pass
    except AuthError as exc:
        return _redirect("/recuperar-acceso", error=str(exc))
    return _redirect("/recuperar-acceso", msg=mensaje)


@router.get("/restablecer-clave", response_class=HTMLResponse)
def restablecer_clave_form(request: Request):
    return TEMPLATES.TemplateResponse(
        request,
        "auth/reset_password.html",
        {"error": request.query_params.get("error", ""), "recovery_token": ""},
    )


@router.post("/restablecer-clave")
async def restablecer_clave(request: Request):
    form = await request.form()
    token = str(form.get("recovery_token") or "").strip()
    password = str(form.get("password") or "")
    confirmation = str(form.get("password_confirmation") or "")
    if password != confirmation:
        return TEMPLATES.TemplateResponse(
            request,
            "auth/reset_password.html",
            {"error": "Las contraseñas no coinciden.", "recovery_token": token},
            status_code=400,
        )
    try:
        settings = SupabaseAuthSettings.from_environment()
        client = common.SupabaseAuthClient(settings)
        # Verifica primero que el token todavía identifica a un usuario.
        await run_in_threadpool(client.get_user, token)
        await run_in_threadpool(client.update_password, token, password)
    except AuthError:
        return TEMPLATES.TemplateResponse(
            request,
            "auth/reset_password.html",
            {
                "error": "El enlace no es válido o ha caducado. Solicita uno nuevo.",
                "recovery_token": "",
            },
            status_code=400,
        )
    response = RedirectResponse(
        "/acceso?msg=" + quote("Contraseña actualizada. Ya puedes iniciar sesión."),
        status_code=303,
    )
    clear_auth_cookies(response, settings.cookie_secure, request)
    return response


@router.post("/acceso")
async def iniciar_sesion(request: Request):
    form = await request.form()
    destino = _next_seguro(form.get("next"), "/inicio")
    try:
        settings = SupabaseAuthSettings.from_environment()
        tokens = await run_in_threadpool(
            common.SupabaseAuthClient(settings).sign_in,
            str(form.get("email") or ""),
            str(form.get("password") or ""),
        )
    except AuthError as exc:
        return _redirect(
            f"/acceso?next={quote(destino)}",
            error=str(exc),
        )
    response = RedirectResponse(destino, status_code=303)
    set_auth_cookies(response, tokens, settings.cookie_secure)
    encolar_evento_ga(response, "login")
    # E4-027: constancia del inicio de sesión (best-effort, jamás lo impide).
    email_sesion = getattr(getattr(tokens, "identity", None), "email", "") or str(
        form.get("email") or ""
    )
    auditoria.anotar_sesion("sesion.login", email=email_sesion, request=request)
    return response


@router.post("/registro")
async def registrar_cuenta(request: Request):
    form = await request.form()
    destino = _next_seguro(form.get("next"), "/organizaciones/nueva")
    password = str(form.get("password") or "")
    password_confirmation = str(form.get("password_confirmation") or "")
    if password != password_confirmation:
        return _redirect("/acceso", error="Las contraseñas no coinciden.")
    # E4-038: sin la aceptación explícita no hay cuenta. El checkbox es
    # obligatorio en el formulario; aquí se vuelve a exigir porque el HTML
    # «required» solo protege al navegador, no a quien llame la ruta a mano.
    if not str(form.get("acepto_terminos") or "").strip():
        return _redirect(
            "/acceso",
            error=(
                "Debes aceptar los términos del servicio y la política de "
                "privacidad para crear tu cuenta."
            ),
        )
    email_registro = str(form.get("email") or "")
    if es_desechable(email_registro):
        # Un buzón que se autodestruye en diez minutos no identifica a nadie:
        # permite generar identidades nuevas sin coste y vaciar de sentido el
        # «una prueba por persona». Se corta aquí, antes de crear la cuenta.
        # A diferencia del mensaje genérico de más abajo, este sí es explícito
        # porque no revela nada: no dice si el correo existe, solo que ese
        # proveedor no sirve.
        return _redirect(
            "/acceso",
            error=(
                "Ese proveedor de correo temporal no está admitido. "
                "Regístrate con un correo permanente, personal o de empresa."
            ),
        )
    try:
        settings = SupabaseAuthSettings.from_environment()
        result = await run_in_threadpool(
            common.SupabaseAuthClient(settings).sign_up,
            str(form.get("email") or ""),
            password,
            str(form.get("nombre") or ""),
            public_app_url("/acceso"),
        )
    except AuthError as exc:
        return _redirect("/acceso", error=str(exc))
    _registrar_consentimiento_de_registro(
        request,
        email=str(form.get("email") or ""),
        nombre=str(form.get("nombre") or ""),
    )
    # País elegido en el registro: fija cookie para que la creación de la
    # organización nazca ya configurada (moneda/IVA/ID fiscal/tasa).
    pais_reg = str(form.get("pais") or "").strip().upper()
    from ..paises import PAISES
    if pais_reg not in PAISES:
        # fallback a cookie previa o VE
        pais_reg = str(request.cookies.get("cotizat_pais", "") or "").strip().upper()
        if pais_reg not in PAISES:
            pais_reg = "VE"
    # Helper para fijar cookie de país en cualquier redirect de registro
    def _resp_con_pais(resp):
        try:
            resp.set_cookie("cotizat_pais", pais_reg, max_age=365*24*3600, path="/", samesite="lax", httponly=False)
        except Exception:
            pass
        return resp

    if result.tokens is None:
        # Mensaje único tanto para el alta nueva como para el email ya
        # registrado: GoTrue oculta a propósito cuál de los dos casos es, y
        # diferenciarlos aquí permitiría enumerar qué emails tienen cuenta.
        resp = _redirect(
            "/acceso",
            msg=(
                "Revisa tu email y abre el enlace de confirmación para activar la "
                "cuenta. Si ya tenías una cuenta con ese email, inicia sesión con "
                "tu contraseña o usa «Olvidé mi contraseña»."
            ),
        )
        return _resp_con_pais(resp)
    response = RedirectResponse(destino, status_code=303)
    set_auth_cookies(response, result.tokens, settings.cookie_secure)
    encolar_evento_ga(response, "sign_up")
    return _resp_con_pais(response)


def _registrar_consentimiento_de_registro(request: Request, *, email: str, nombre: str):
    """Registra la aceptación de términos del alta (E4-038), sin romperla.

    Se abre una sesión anónima a propósito: en el momento del registro no hay
    tokens (el correo se confirma después), y el registro de consentimiento no
    puede depender de la autenticación. Es best-effort: si la base no
    responde, la cuenta se crea igualmente y la marca se rellena en /cuenta.
    """
    try:
        from ..database import SessionLocal
        from ..legal import TERMINOS_VERSION
        from ..services.consentimiento import registrar_consentimiento
        from ..services.prueba_gratuita import hash_ip

        ip = request.client.host if request.client else ""
        with SessionLocal() as db:
            registrar_consentimiento(
                db,
                email=email,
                nombre=nombre,
                version=TERMINOS_VERSION,
                ip_hash=hash_ip(ip),
            )
    except Exception:
        log.exception("No se pudo registrar el consentimiento del alta.")


@router.post("/salir")
async def cerrar_sesion(request: Request):
    """Cierra la sesión local y revoca el refresh token en Supabase.

    Borrar las cookies basta para el navegador, pero el refresh token seguiría
    siendo válido en GoTrue. La revocación es best-effort: si Supabase no
    responde, la sesión local se cierra igualmente y nunca se deja al usuario
    dentro por un fallo del proveedor.
    """
    response = RedirectResponse("/acceso", status_code=303)
    secure = True
    # Identidad ANTES de revocar (después el token ya no vale). Best-effort:
    # sin identidad, el cierre se anota sin correo o no se anota.
    email_sesion = ""
    try:
        from ..auth import identity_for_request

        email_sesion = identity_for_request(request).email or ""
    except Exception:
        pass
    try:
        settings = SupabaseAuthSettings.from_environment()
        secure = settings.cookie_secure
        access_token = request.cookies.get(ACCESS_COOKIE, "")
        if access_token:
            await run_in_threadpool(
                common.SupabaseAuthClient(settings).sign_out, access_token
            )
    except AuthNotConfigured:
        pass
    except AuthError:
        log.info("No se pudo revocar la sesión en Supabase; se cierra localmente.")
    clear_auth_cookies(response, secure, request)
    if email_sesion:
        auditoria.anotar_sesion("sesion.logout", email=email_sesion, request=request)
    return response


# ---------------------------------------------------------------------------
# Panel de la cuenta (perfil, contraseña y sesión)
# ---------------------------------------------------------------------------

def _render_cuenta(
    request: Request,
    db: Session,
    *,
    msg: str = "",
    error: str = "",
    status_code: int = 200,
):
    """Pinta el panel con el perfil local y las membresías del usuario.

    ``get_authenticated_db`` no resuelve organización activa (el panel debe
    abrirse incluso sin haber elegido empresa), así que la selección se deduce
    aquí de la cookie y se contrasta con las membresías reales: una cookie
    manipulada nunca marca como activa una empresa ajena.
    """
    usuario = db.get(Usuario, db.info["usuario_id"])
    membresias = membresias_activas(db, usuario.id)
    cookie = request.cookies.get(ORGANIZATION_COOKIE, "").strip()
    try:
        seleccionada = int(cookie) if cookie else None
    except ValueError:
        seleccionada = None
    if seleccionada not in {m.organizacion_id for m in membresias}:
        seleccionada = membresias[0].organizacion_id if len(membresias) == 1 else None
    return TEMPLATES.TemplateResponse(
        request,
        "auth/account.html",
        {
            "usuario": usuario,
            "membresias": membresias,
            "organizacion_activa_id": seleccionada,
            "email_verificado": bool(usuario.email_verificado_at),
            "consentimiento_version": usuario.acepto_terminos_version or "",
            "consentimiento_at": usuario.acepto_terminos_at,
            "msg": msg,
            "error": error,
        },
        status_code=status_code,
    )


@router.get("/cuenta", response_class=HTMLResponse)
def ver_cuenta(request: Request, db: Session = Depends(get_authenticated_db)):
    if common.DATABASE_IS_SQLITE:
        return _redirect("/configuracion")
    return _render_cuenta(
        request,
        db,
        msg=request.query_params.get("msg", ""),
        error=request.query_params.get("error", ""),
    )


@router.post("/cuenta/consentimiento")
def aceptar_terminos_cuenta(
    request: Request,
    db: Session = Depends(get_authenticated_db),
):
    """Registra la aceptación de términos desde el panel de cuenta (E4-038).

    Es el camino para las cuentas creadas antes de existir el registro (la
    marca no quedó anotada en su alta) y la vía natural si algún día cambia la
    versión de los términos: aceptar la nueva versión asienta una fila nueva
    sin tocar las anteriores.
    """
    if common.DATABASE_IS_SQLITE:
        return _redirect("/configuracion")
    from ..legal import TERMINOS_VERSION
    from ..services.consentimiento import (
        aplicar_consentimiento_a_usuario,
        registrar_consentimiento,
    )

    usuario = db.get(Usuario, db.info["usuario_id"])
    ip = request.client.host if request.client else ""
    from ..services.prueba_gratuita import hash_ip

    registrar_consentimiento(
        db,
        email=usuario.email,
        nombre=usuario.nombre,
        version=TERMINOS_VERSION,
        ip_hash=hash_ip(ip),
    )
    aplicar_consentimiento_a_usuario(db, usuario)
    db.commit()
    return _redirect("/cuenta", msg="Gracias. Quedó registrada tu aceptación de los términos y la política de privacidad.")


@router.post("/cuenta/perfil")
async def actualizar_perfil_cuenta(
    request: Request,
    db: Session = Depends(get_authenticated_db),
):
    """Guarda el nombre visible en el perfil local y en Supabase.

    El email no se edita aquí: cambiarlo exige reverificación en Supabase y
    rehacer el vínculo con `usuarios.auth_user_id`, lo que rompería membresías
    e invitaciones pendientes emitidas contra el email anterior.
    """
    if common.DATABASE_IS_SQLITE:
        return _redirect("/configuracion")
    form = await request.form()
    nombre = str(form.get("nombre") or "").strip()[:200]
    if len(nombre) < 2:
        return _render_cuenta(
            request, db, error="Escribe un nombre de al menos 2 caracteres.",
            status_code=400,
        )
    usuario = db.get(Usuario, db.info["usuario_id"])
    usuario.nombre = nombre
    db.commit()
    try:
        settings = SupabaseAuthSettings.from_environment()
        access_token = request.cookies.get(ACCESS_COOKIE, "")
        if access_token:
            await run_in_threadpool(
                common.SupabaseAuthClient(settings).update_profile, access_token, nombre
            )
    except AuthError:
        # El perfil local ya quedó guardado: no se revierte por un fallo del
        # metadato remoto, que solo alimenta el nombre mostrado.
        log.info("No se pudo sincronizar el nombre con Supabase.")
    return _redirect("/cuenta", msg="Perfil actualizado.")


@router.post("/cuenta/clave")
async def cambiar_clave_cuenta(
    request: Request,
    db: Session = Depends(get_authenticated_db),
):
    """Cambia la contraseña exigiendo la actual y cierra la sesión."""
    if common.DATABASE_IS_SQLITE:
        return _redirect("/configuracion")
    form = await request.form()
    actual = str(form.get("password_actual") or "")
    nueva = str(form.get("password") or "")
    confirmacion = str(form.get("password_confirmation") or "")
    if nueva != confirmacion:
        return _render_cuenta(
            request, db, error="Las contraseñas nuevas no coinciden.", status_code=400
        )
    usuario = db.get(Usuario, db.info["usuario_id"])
    try:
        settings = SupabaseAuthSettings.from_environment()
        access_token = request.cookies.get(ACCESS_COOKIE, "")
        await run_in_threadpool(
            common.SupabaseAuthClient(settings).change_password,
            access_token,
            usuario.email,
            actual,
            nueva,
        )
    except InvalidCredentials as exc:
        return _render_cuenta(request, db, error=str(exc), status_code=400)
    except AuthError as exc:
        return _render_cuenta(request, db, error=str(exc), status_code=503)
    # Cambiar la contraseña invalida las sesiones anteriores: se fuerza un
    # inicio de sesión nuevo en lugar de conservar cookies ya obsoletas.
    auditoria.anotar_sesion(
        "cuenta.clave_cambiada", email=usuario.email, request=request
    )
    response = RedirectResponse(
        "/acceso?msg=" + quote("Contraseña actualizada. Inicia sesión de nuevo."),
        status_code=303,
    )
    clear_auth_cookies(response, settings.cookie_secure, request)
    return response


@router.get("/organizaciones", response_class=HTMLResponse)
def listar_organizaciones_web(
    request: Request,
    db: Session = Depends(get_authenticated_db),
):
    if common.DATABASE_IS_SQLITE:
        return _redirect("/inicio")
    usuario = db.get(Usuario, db.info["usuario_id"])
    membresias = membresias_activas(db, usuario.id)
    cookie = request.cookies.get(ORGANIZATION_COOKIE, "").strip()
    try:
        seleccionada = int(cookie) if cookie else None
    except ValueError:
        seleccionada = None
    if seleccionada not in {m.organizacion_id for m in membresias}:
        seleccionada = membresias[0].organizacion_id if len(membresias) == 1 else None
    return TEMPLATES.TemplateResponse(
        request,
        "auth/organizations.html",
        {
            "usuario": usuario,
            "membresias": membresias,
            "organizacion_activa_id": seleccionada,
            # Sin esto, quien se registra desde una invitación no encuentra
            # ninguna forma de aceptarla dentro de la aplicación.
            "invitaciones": invitaciones_pendientes_para(db, usuario=usuario),
            "error": request.query_params.get("error", ""),
            "msg": request.query_params.get("msg", ""),
        },
        headers={"Cache-Control": "no-store"},
    )


@router.post("/invitaciones/pendientes/{invitacion_id}/aceptar")
def aceptar_invitacion_pendiente_web(
    invitacion_id: int,
    request: Request,
    db: Session = Depends(get_authenticated_db),
):
    """Acepta una invitación ya visible en el panel, sin volver al email.

    El enlace del correo sigue funcionando igual; esta ruta cubre el caso en
    que la persona ya está dentro (típicamente recién registrada y confirmada),
    donde exigir que rebusque el email era un paso muerto.
    """
    if common.DATABASE_IS_SQLITE:
        return _redirect("/inicio")
    usuario = db.get(Usuario, db.info["usuario_id"])
    identidad = request.state.supabase_identity
    try:
        membresia = aceptar_invitacion_pendiente(
            db,
            invitacion_id=invitacion_id,
            usuario=usuario,
            email_verificado=identidad.email_verified,
        )
        organizacion_id = membresia.organizacion_id
        db.commit()
    except GestionEquipoError as exc:
        db.rollback()
        return _redirect("/organizaciones", error=str(exc))
    except Exception:
        db.rollback()
        log.error(
            "Error aceptando la invitación pendiente:\n%s", traceback.format_exc()
        )
        raise
    response = _redirect(
        "/organizaciones", msg="Invitación aceptada. Ya puedes entrar a la organización."
    )
    _set_organization_cookie(response, organizacion_id)
    return response


@router.get("/organizaciones/nueva", response_class=HTMLResponse)
def nueva_organizacion_web(
    request: Request,
    db: Session = Depends(get_authenticated_db),
):
    if common.DATABASE_IS_SQLITE:
        return _redirect("/inicio")
    usuario = db.get(Usuario, db.info["usuario_id"])
    pendientes = invitaciones_pendientes_para(db, usuario=usuario)
    # Quien llega aquí por el destino por omisión del registro puede tener una
    # invitación esperando: crear una empresa propia casi nunca es lo que
    # quiere, así que se le ofrece la opción correcta antes de escribir nada.
    if pendientes and not membresias_activas(db, usuario.id):
        return _redirect("/organizaciones")
    # Lista de países disponibles para el selector. Viene de la fuente única
    # (``app.paises.PAISES``) y ya está ordenada por el ORDEN_SELECTOR
    # actualizado: 17 países (Latinoamérica + España) en lugar de los 6 que
    # se listaban a mano. Si mañana se añade otro mercado, aparece solo.
    from ..paises import lista_paises
    return TEMPLATES.TemplateResponse(
        request,
        "auth/organization_new.html",
        {
            "usuario": usuario,
            "paises": lista_paises(),
            # País preseleccionado: cookie del registro o query param
            # ``?pais=XX`` (legacy). Si no, no preseleccionamos nada para
            # que el usuario elija consciente, no por defecto.
            "pais_preseleccionado": (
                str(request.query_params.get("pais", "") or "").strip().upper()
                or str(request.cookies.get("cotizat_pais", "") or "").strip().upper()
            ),
            "error": request.query_params.get("error", ""),
        },
    )


@router.post("/organizaciones/nueva")
async def crear_organizacion_web(
    request: Request,
    db: Session = Depends(get_authenticated_db),
):
    if common.DATABASE_IS_SQLITE:
        return _redirect("/inicio")
    form = await request.form()
    nombre = str(form.get("nombre") or "").strip()[:200]
    if len(nombre) < 2:
        return _redirect(
            "/organizaciones/nueva",
            error="Escribe un nombre válido para la empresa.",
        )
    slug_base = _slug_organizacion(nombre)
    # RLS no debe revelar slugs de otras empresas para buscar un sufijo. Un
    # sufijo aleatorio mantiene la unicidad sin ampliar la lectura global.
    slug = f"{slug_base[:107]}-{uuid.uuid4().hex[:12]}"
    usuario = db.get(Usuario, db.info["usuario_id"])
    # El alta reserva el id desde ``organizaciones_id_seq`` para insertar sin
    # ``RETURNING``: la política ``cotizat_org_select`` exige una membresía que
    # todavía no existe y haría fallar la lectura implícita del INSERT.
    organizacion = crear_organizacion_con_propietario(
        db,
        nombre=nombre,
        slug=slug,
        usuario_id=usuario.id,
    )
    establecer_contexto_organizacion(db, organizacion.id)

    # Prueba gratuita: sin esto, con la exigencia de licencia activada la
    # organización nacería suspendida en el mismo segundo del alta y el cliente
    # tendría que pagar antes de ver nada. Se concede aquí, con el contexto de
    # organización ya establecido, porque la función SECURITY DEFINER que
    # escribe la licencia comprueba precisamente ese claim.
    #
    # `conceder_prueba` no lanza excepciones a propósito: si algo falla, la
    # organización se crea igual y la persona aterriza en la pantalla de
    # planes. Perder la prueba se recupera; perder el alta, no.
    resultado_prueba = conceder_prueba(
        db,
        organizacion_id=organizacion.id,
        email=str(db.info.get("auth_email") or getattr(usuario, "email", "")),
        ip=ip_de_request(request),
        es_sqlite=common.DATABASE_IS_SQLITE,
    )

    # La configuración se añade *después* de conceder la prueba: `conceder_prueba`
    # trabaja dentro de un SAVEPOINT y, si la identidad ya gastó su prueba, hace
    # rollback hasta él. Con la Configuracion pendiente en la sesión, el autoflush
    # la metería dentro de ese punto y el rollback se la llevaría por delante,
    # dejando la organización sin configuración.
    # País -> defaults (moneda/IVA/ID fiscal/tasa) para que nazca configurada
    pais_org = str(form.get("pais") or "").strip().upper()
    from ..paises import PAISES, PAIS_GENERICO
    from ..services.tasa import tasa_sugerida
    if pais_org not in PAISES:
        pais_org = str(request.cookies.get("cotizat_pais", "") or "").strip().upper()
        if pais_org not in PAISES:
            pais_org = "VE"
    _pais_data = PAISES.get(pais_org, PAIS_GENERICO)
    _cfg_init = Configuracion(
        organizacion_id=organizacion.id,
        empresa_pais=_pais_data["nombre"],
        moneda_default=_pais_data["moneda"],
        iva_default=float(_pais_data["iva"]),
        etiqueta_id_fiscal=_pais_data["id_fiscal"],
        tasa_cambio=tasa_sugerida(_pais_data["moneda"]) if _pais_data["moneda"] not in ("USD", "PAB") else 1.0,
        fecha_tasa=date.today() if _pais_data["moneda"] not in ("USD", "PAB") else None,
    )
    db.add(_cfg_init)
    db.commit()

    # Sin prueba, la persona va a la pantalla de planes: negarla nunca puede
    # impedir pagar. Con prueba, entra directa a la bienvenida.
    destino = "/bienvenida" if resultado_prueba.concedida else "/pago"
    response = RedirectResponse(
        f"{destino}?msg={quote(resultado_prueba.mensaje)}", status_code=303
    )
    _set_organization_cookie(response, organizacion.id)
    return response


@router.post("/organizaciones/{organizacion_id}/seleccionar")
def seleccionar_organizacion_web(
    organizacion_id: int,
    db: Session = Depends(get_authenticated_db),
):
    if common.DATABASE_IS_SQLITE:
        return _redirect("/inicio")
    usuario_id = db.info["usuario_id"]
    membresia = (
        db.query(Membresia)
        .join(Organizacion, Organizacion.id == Membresia.organizacion_id)
        .filter(
            Membresia.usuario_id == usuario_id,
            Membresia.organizacion_id == organizacion_id,
            Membresia.activa.is_(True),
            Organizacion.activa.is_(True),
        )
        .first()
    )
    if membresia is None:
        raise OrganizationAccessDenied(
            "No tienes acceso a la organización seleccionada."
        )
    response = RedirectResponse("/inicio", status_code=303)
    _set_organization_cookie(response, organizacion_id)
    return response


def _render_equipo(
    request: Request,
    db: Session,
    *,
    invitation_link: str = "",
    msg: str = "",
    status_code: int = 200,
):
    organizacion_id = db.info["organizacion_id"]
    actor_rol = db.info["rol_membresia"]
    exigir_gestor(actor_rol)
    membresias = (
        db.query(Membresia)
        .join(Usuario, Usuario.id == Membresia.usuario_id)
        .filter(Membresia.organizacion_id == organizacion_id)
        .order_by(Membresia.activa.desc(), Usuario.email, Membresia.id)
        .all()
    )
    invitaciones = (
        db.query(InvitacionOrganizacion)
        .filter(
            InvitacionOrganizacion.organizacion_id == organizacion_id,
            InvitacionOrganizacion.accepted_at.is_(None),
            InvitacionOrganizacion.revoked_at.is_(None),
        )
        .order_by(InvitacionOrganizacion.created_at.desc())
        .all()
    )
    return TEMPLATES.TemplateResponse(
        request,
        "auth/team.html",
        {
            "membresias": membresias,
            "invitaciones": invitaciones,
            "actor_rol": actor_rol,
            "ahora": datetime.utcnow(),
            "invitation_link": invitation_link,
            "msg": msg or request.query_params.get("msg", ""),
            "error": request.query_params.get("error", ""),
        },
        status_code=status_code,
        headers={"Cache-Control": "no-store"},
    )


@router.get("/equipo", response_class=HTMLResponse)
def gestionar_equipo_web(request: Request, db: Session = Depends(get_db)):
    if common.DATABASE_IS_SQLITE:
        return _redirect("/inicio")
    return _render_equipo(request, db)


@router.post("/equipo/invitaciones", response_class=HTMLResponse)
async def crear_invitacion_web(request: Request, db: Session = Depends(get_db)):
    if common.DATABASE_IS_SQLITE:
        return _redirect("/inicio")
    form = await request.form()
    try:
        # Valida primero el origen fijo para no persistir una invitación cuyo
        # enlace no pueda construirse de forma segura.
        public_app_url("/")
        invitacion, token = crear_invitacion(
            db,
            organizacion_id=db.info["organizacion_id"],
            actor_usuario_id=db.info["usuario_id"],
            email=str(form.get("email") or ""),
            rol=str(form.get("rol") or ""),
        )
        invitation_link = public_app_url(f"/invitaciones/{token}")
        db.commit()
    except (GestionEquipoError, AuthNotConfigured) as exc:
        db.rollback()
        return _redirect("/equipo", error=str(exc))
    auditoria.registrar_evento(
        db,
        "equipo.invitacion_enviada",
        entidad="invitacion",
        entidad_id=invitacion.id,
        detalle={"email": invitacion.email, "rol": invitacion.rol},
    )

    # La invitación ya está guardada: el correo es un canal de entrega, no la
    # fuente de verdad. Si no hay correo configurado o el proveedor falla, se
    # degrada al comportamiento de siempre: mostrar el enlace una vez en
    # pantalla para copiarlo.
    email_enviado = False
    try:
        organizacion = db.get(Organizacion, db.info["organizacion_id"])
        invitador = db.get(Usuario, db.info["usuario_id"])
        enviar_invitacion_por_email(
            email=invitacion.email,
            enlace=invitation_link,
            organizacion_nombre=organizacion.nombre if organizacion else "",
            invitador_nombre=invitador.nombre if invitador else "",
            invitador_email=invitador.email if invitador else "",
            rol=invitacion.rol,
            caduca_el=invitacion.expires_at,
        )
        email_enviado = True
    except (EmailNotConfigured, EmailSendError) as exc:
        log.info(
            "Invitación para %s sin correo (%s); se muestra el enlace en pantalla.",
            invitacion.email,
            type(exc).__name__,
        )
    if email_enviado:
        return _render_equipo(
            request,
            db,
            msg=(
                f"Invitación enviada a {invitacion.email}. "
                "Revisará su bandeja de entrada para aceptarla."
            ),
        )
    return _render_equipo(
        request,
        db,
        invitation_link=invitation_link,
        msg=(
            f"Invitación creada para {invitacion.email}. No se pudo enviar el "
            "correo: copia el enlace y compártelo por un canal seguro."
        ),
    )


@router.post("/equipo/invitaciones/{invitacion_id}/revocar")
def revocar_invitacion_web(
    invitacion_id: int,
    db: Session = Depends(get_db),
):
    if common.DATABASE_IS_SQLITE:
        return _redirect("/inicio")
    invitacion = (
        db.query(InvitacionOrganizacion)
        .filter(
            InvitacionOrganizacion.id == invitacion_id,
            InvitacionOrganizacion.organizacion_id == db.info["organizacion_id"],
        )
        .first()
    )
    if invitacion is None:
        return _redirect("/equipo", error="La invitación no existe.")
    try:
        revocar_invitacion(
            db,
            invitacion=invitacion,
            organizacion_id=db.info["organizacion_id"],
            actor_usuario_id=db.info["usuario_id"],
        )
        db.commit()
    except GestionEquipoError as exc:
        db.rollback()
        return _redirect("/equipo", error=str(exc))
    auditoria.registrar_evento(
        db,
        "equipo.invitacion_revocada",
        entidad="invitacion",
        entidad_id=invitacion.id,
        detalle={"email": invitacion.email},
    )
    return _redirect("/equipo", msg="Invitación revocada.")


@router.post("/equipo/membresias/{membresia_id}")
async def actualizar_membresia_web(
    membresia_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    if common.DATABASE_IS_SQLITE:
        return _redirect("/inicio")
    membresia = (
        db.query(Membresia)
        .filter(
            Membresia.id == membresia_id,
            Membresia.organizacion_id == db.info["organizacion_id"],
        )
        .with_for_update()
        .first()
    )
    if membresia is None:
        return _redirect("/equipo", error="La membresía no existe.")
    form = await request.form()
    rol_anterior = str(membresia.rol or "")
    activa_anterior = bool(membresia.activa)
    try:
        actualizar_membresia(
            db,
            membresia=membresia,
            organizacion_id=db.info["organizacion_id"],
            actor_usuario_id=db.info["usuario_id"],
            rol=str(form.get("rol") or ""),
            activa=str(form.get("activa") or "") == "1",
        )
        db.commit()
    except GestionEquipoError as exc:
        db.rollback()
        return _redirect("/equipo", error=str(exc))
    # E4-027: rastro de la gestión del equipo (después del commit).
    email_miembro = str(getattr(membresia.usuario, "email", "") or "")
    if str(membresia.rol or "") != rol_anterior:
        auditoria.registrar_evento(
            db,
            "equipo.rol_cambiado",
            entidad="membresia",
            entidad_id=membresia.id,
            detalle={
                "email": email_miembro,
                "de": rol_anterior,
                "a": str(membresia.rol or ""),
            },
        )
    if activa_anterior and not bool(membresia.activa):
        auditoria.registrar_evento(
            db,
            "equipo.miembro_desactivado",
            entidad="membresia",
            entidad_id=membresia.id,
            detalle={"email": email_miembro},
        )
    return _redirect("/equipo", msg="Membresía actualizada.")


def _render_invitacion(
    request: Request,
    token: str,
    *,
    error: str = "",
    status_code: int = 200,
    autenticado: bool = False,
    auto_aceptar: bool = False,
):
    return TEMPLATES.TemplateResponse(
        request,
        "auth/invitation.html",
        {
            "token": token,
            "error": error,
            "autenticado": autenticado,
            "auto_aceptar": auto_aceptar,
        },
        status_code=status_code,
        headers={"Cache-Control": "no-store", "Referrer-Policy": "strict-origin-when-cross-origin"},
    )


@router.get("/invitaciones/{token}", response_class=HTMLResponse)
def ver_invitacion_web(request: Request, token: str):
    # La vista pública no consulta la base ni confirma si el token existe.
    token_seguro = token if re.fullmatch(r"[A-Za-z0-9_-]{32,200}", token) else ""
    autenticado = bool(request.cookies.get(ACCESS_COOKIE))
    return _render_invitacion(request, token_seguro, autenticado=autenticado)


@router.get("/invitaciones/{token}/aceptar", response_class=HTMLResponse)
def ver_invitacion_aceptar_web(request: Request, token: str):
    """Página de aceptación servida por GET.

    Después de iniciar sesión, la redirección ``?next=...`` siempre llega por
    GET, así que esta ruta debe existir: sin ella el navegador recibía un
    405 Method Not Allowed porque la única ruta registrada era el POST.
    Si hay sesión, la página autoenvía el POST de aceptación (un clic menos
    tras el login); la validación y el consumo del token los hace el POST,
    protegido por CSRF, así que no se relaja ninguna seguridad.
    """
    # La vista pública no consulta la base ni confirma si el token existe.
    token_seguro = token if re.fullmatch(r"[A-Za-z0-9_-]{32,200}", token) else ""
    autenticado = bool(request.cookies.get(ACCESS_COOKIE))
    return _render_invitacion(
        request,
        token_seguro,
        autenticado=autenticado,
        auto_aceptar=autenticado,
    )


@router.post("/invitaciones/{token}/aceptar")
def aceptar_invitacion_web(
    token: str,
    request: Request,
    db: Session = Depends(get_authenticated_db),
):
    if common.DATABASE_IS_SQLITE:
        return _redirect("/inicio")
    usuario = db.get(Usuario, db.info["usuario_id"])
    identidad = request.state.supabase_identity
    try:
        membresia = aceptar_invitacion(
            db,
            token=token,
            usuario=usuario,
            email_verificado=identidad.email_verified,
        )
        organizacion_id = membresia.organizacion_id
        db.commit()
    except GestionEquipoError as exc:
        db.rollback()
        return _render_invitacion(
            request,
            token,
            error=str(exc),
            status_code=400,
            autenticado=True,
        )
    except Exception:
        # Un fallo de base/RLS no debe morir como un 500 mudo: la traza queda
        # en el log del despliegue para diagnosticarlo (regresión del 500 al
        # aceptar invitaciones por la política SELECT sobre la fila nueva).
        db.rollback()
        log.error("Error aceptando la invitación:\n%s", traceback.format_exc())
        raise
    response = _redirect(
        "/organizaciones", msg="Invitación aceptada. Ya puedes entrar a la organización."
    )
    _set_organization_cookie(response, organizacion_id)
    return response


# ---------------------------------------------------------------------------
# Primer inicio
# ---------------------------------------------------------------------------

@router.get("/bienvenida", response_class=HTMLResponse)
def bienvenida(request: Request, db: Session = Depends(get_db)):
    cfg = _config(db)
    if cfg.onboarding_completado:
        return _redirect("/inicio")
    # Si la persona venía a comprar un plan antes de crear su cuenta/empresa,
    # se le recuerda que retomará la compra al terminar esta configuración.
    compra_pendiente_ficha = None
    from ..datos_pago import PLANES, PLAN_PENDIENTE_COOKIE, plan_info

    plan_recordado = request.cookies.get(PLAN_PENDIENTE_COOKIE, "").strip()
    if plan_recordado in PLANES:
        resumen = getattr(request.state, "licencia_resumen", None) or {}
        if not resumen.get("activo"):
            compra_pendiente_ficha = plan_info(plan_recordado)
    from ..paises import PAIS_GENERICO, lista_paises
    from ..services.tasa import TASAS_SUGERIDAS, obtener_tasa_api
    from ..services.monedas import MONEDAS, MONEDAS_VISIBLE, definicion as _def_moneda

    # Tasas pre-cargadas (TASAS_SUGERIDAS) + intento de traer la tasa real del
    # día desde open.er-api.com para las monedas que aún no tienen tasa
    # verificada. Si la API no responde, se devuelven sólo las verificadas y
    # la UI muestra el botón «Tasa de hoy» para consultarla bajo demanda.
    tasas_dia = dict(TASAS_SUGERIDAS)
    for _m in MONEDAS_VISIBLE:
        if tasas_dia.get(_m) in (None,) and _m not in ("USD", "PAB"):
            try:
                _tasa_api, _ = obtener_tasa_api(_m, timeout=2)
                if _tasa_api:
                    tasas_dia[_m] = round(float(_tasa_api), 4)
            except Exception:
                pass

    # Lista de monedas para el selector: la visible completa + VES (legacy)
    # para que un país con moneda VES (Venezuela) la vea sin perder la opción.
    # El orden refleja la familiaridad del usuario hispanohablante: primero
    # USD/EUR (referencia global), luego el resto de LatAm y al final VES.
    _monedas_orden = [
        "USD", "EUR", "COP", "MXN", "PEN", "CLP", "ARS",
        "UYU", "PYG", "BOB", "DOP", "PAB", "CRC", "GTQ",
        "HNL", "NIO", "BRL", "VES",
    ]
    _monedas_info = []
    for _m in _monedas_orden:
        if _m in MONEDAS:
            d = _def_moneda(_m)
            _monedas_info.append({
                "codigo": d.codigo,
                "nombre": d.nombre,
                "simbolo": d.simbolo_auxiliar,
            })

    return TEMPLATES.TemplateResponse(
        request,
        "onboarding.html",
        {
            "cfg": cfg,
            "error": request.query_params.get("error", ""),
            # Confirmación de la prueba gratuita recién concedida. Se recorta
            # porque viene de la query y acaba pintándose en la página.
            "msg": request.query_params.get("msg", "")[:300],
            "compra_pendiente_ficha": compra_pendiente_ficha,
            # Una sola fuente de verdad para el auto-config por país: los JS
            # del wizard leen estos datos, no valores duplicados a mano.
            "paises": lista_paises(),
            "pais_generico": PAIS_GENERICO,
            "monedas": _monedas_info,
            "tasas": tasas_dia,
        },
    )


@router.post("/bienvenida")
async def finalizar_bienvenida(request: Request, db: Session = Depends(get_db)):
    cfg = _config(db)
    if cfg.onboarding_completado:
        return _redirect("/inicio")
    if not cfg.onboarding_iniciado_at:
        cfg.onboarding_iniciado_at = datetime.utcnow()
        db.commit()
    form = await request.form()
    datos = {
        "empresa_nombre": form.get("empresa_nombre", ""),
        "empresa_legal": form.get("empresa_legal", ""),
        "empresa_rif": form.get("empresa_rif", ""),
        "empresa_pais": form.get("empresa_pais", "Venezuela"),
        "empresa_ciudad": form.get("empresa_ciudad", ""),
        "empresa_direccion": form.get("empresa_direccion", ""),
        "empresa_telefono": form.get("empresa_telefono", ""),
        "empresa_email": form.get("empresa_email", ""),
        "moneda_default": form.get("moneda_default", "USD"),
        "iva_default": _f(form.get("iva_default"), 16.0),
        "etiqueta_id_fiscal": form.get("etiqueta_id_fiscal", "RIF"),
        "tasa_cambio": form.get("tasa_cambio", ""),
        "fecha_tasa": form.get("fecha_tasa", ""),
    }
    try:
        cfg = completar_onboarding(db, datos, str(form.get("modo_inicio", "")))
    except ErrorOnboarding as exc:
        return _redirect("/bienvenida", error=str(exc))

    logo = form.get("logo")
    if isinstance(logo, UploadFileStarlette) and logo.filename:
        ruta = await _guardar_imagen(logo, "logo", db)
        if ruta:
            cfg.logo = ruta
            db.commit()
    return _redirect("/inicio", msg="Tu espacio de trabajo está listo. Completa la guía para crear tu primer PDF.")


@router.post("/recorrido/catalogo-revisado")
def marcar_catalogo_revisado(db: Session = Depends(get_db)):
    cfg = _config(db)
    if not cfg.onboarding_catalogo_revisado:
        cfg.onboarding_catalogo_revisado = True
        db.commit()
    return _redirect("/partidas")


@router.post("/recorrido/omitir")
def omitir_guia_inicio(request: Request, db: Session = Depends(get_db)):
    """Oculta la «Guía de inicio» del panel sin dar el recorrido por completo.

    Pensado para quien ya conoce la app o crea otra organización y no
    necesita que le recuerden los cinco pasos. La decisión se guarda por
    organización (la columna vive en ``Configuracion``), de modo que cada
    espacio de trabajo conserva su propia preferencia.

    Cuando el cliente pide JSON (el botón del panel la envía por AJAX) se
    responde un ``{ok: true}`` ligero sin recargar el panel: la página de
    inicio es la más pesada de la app y no debe renderizarse por completo
    para una acción que solo oculta una tarjeta. El resto de clientes sigue
    recibiendo el redireccionado clásico a ``/inicio``.

    Hotfix b1c2d3e4f5a6: si la columna aún no existe en Postgres (deploy sin
    ``alembic upgrade head``) no se deja la página 500. Se intenta un
    ``ALTER ... IF NOT EXISTS`` best-effort y, si no hay permisos,
    simplemente se ignora (la guía seguirá visible pero la app abre).
    """
    cfg = _config(db)
    if not getattr(cfg, "recorrido_inicial_oculto", False):
        try:
            cfg.recorrido_inicial_oculto = True
            db.commit()
        except Exception as exc:
            try:
                db.rollback()
            except Exception:
                pass
            # best-effort DDL por si la columna falta
            try:
                from sqlalchemy import text as _text

                db.execute(_text("ALTER TABLE configuracion ADD COLUMN IF NOT EXISTS recorrido_inicial_oculto BOOLEAN DEFAULT false"))
                db.commit()
                # reintenta el set
                cfg.recorrido_inicial_oculto = True
                db.commit()
            except Exception:
                try:
                    db.rollback()
                except Exception:
                    pass
                log.warning("omitir_guia_inicio: no se pudo persistir preferencia (columna faltante sin permisos DDL): %s", exc)
                # No se propaga: la acción es ocultar una tarjeta, no crítica
                # Se deja el flag en memoria para que la tarjeta desaparezca al menos en esta request
                try:
                    cfg.__dict__["recorrido_inicial_oculto"] = True
                except Exception:
                    pass
    if _respuesta_auth_json(request):
        return JSONResponse({"ok": True})
    return _redirect("/inicio")
