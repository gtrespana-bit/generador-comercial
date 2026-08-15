# Punto exacto de continuación

Fecha de corte: **15/08/2026, noche (segunda parte de la sesión)** (America/Caracas).

Este documento retoma el trabajo sin depender del historial del chat. Describe
**dónde quedó exactamente** el trabajo y **qué sigue**, en ese orden. Léelo
junto con `docs/CONTINUIDAD_STAGING_SUPABASE.md` (estado de staging/matriz) y
`PLAN_DE_COMERCIALIZACION_Y_EVOLUCION_SAAS.md` (E1-052, E1-056 y siguientes).

---

## 1. Lo último hecho: rama `arena/01a00790-generador-comercial` (PR #22 abierto)

Trabajo de esta sesión sobre `main` (`8d89954`, merge del PR #20). Tres commits:

### 1a. E1-052 — presupuesto de muestra comercial + PDF de ejemplo `[x]` (commit `f9ce25b`)

- `app/services/presupuesto_muestra.py`: construye un presupuesto de remodelación
  completo (7 capítulos, ~20 partidas, resumen por capítulos, garantías y
  firmas) con **datos 100 % ficticios**: empresa «Construcciones El Samán, C.A.»
  con RIF marcador `J-00000000-0` y contacto en el dominio reservado
  `ejemplo.com`, cliente genérico «Familia Rodríguez» sin documento, e importes
  inventados. El propio PDF declara en «Información adicional» que todo es ficticio.
- `tools/generar_presupuesto_muestra.py`: regenera el PDF y lo escribe en
  `app/static/pdf/presupuesto-ejemplo.pdf` (archivo versionado, ~74 KB).
- Landing `/conocer`: enlaza el PDF de ejemplo (botón «Ver un presupuesto de
  ejemplo (PDF)» en el hero + enlace en la tarjeta «PDF que da confianza»).
- `tests/test_presupuesto_muestra.py` (5 pruebas): PDF válido sin datos reales,
  generador reproducible, landing enlaza/sirve el PDF como `application/pdf`.

Con esto E1-052 pasó a `[x]` y E1-056 (`[~]`) solo espera el vídeo (E1-051).

### 1b. Auth: registro del error real de GoTrue + docs de Redirect URLs (commit `6e175b9`)

- `app/auth.py`: en errores HTTP de GoTrue ahora se registra en el log del
  servidor el estado y el cuerpo (acotado a 300 chars) de la respuesta
  (`Supabase Auth <método> <path> -> HTTP <código>: <cuerpo>`), para poder
  distinguir `otp_expired` / `email no confirmado` / `invalid_credentials` sin
  filtrar nada al usuario (el mensaje visible **no** cambió).
- `docs/AUTENTICACION_SUPABASE.md` y `docs/DOMINIO_COTIZAT_ONLINE.md`:
  documentado que `/acceso` (destino de confirmación de registro) debe estar en
  las Redirect URLs de Supabase junto a `/restablecer-clave`.

### 1c. Test flaky de CI corregido (commit `2ea7adc`)

`tests/test_instalacion_sqlite.py::_zip_de_backup` usaba `writestr(nombre, datos)`,
que graba la hora actual en cada entrada del zip: dos llamadas en segundos
distintos producían bytes distintos y el SHA-256 recalculado por el test dejaba
de coincidir con el que el servidor calculó sobre el archivo subido. Se fijó la
marca de tiempo de las entradas (`ZipInfo(date_time=...)`) para que el zip sea
**determinista**. En CI falló `test_http_flujo_completo_analizar_y_confirmar`
por cruzar el límite de segundo; ahora es estable.

### Suite al cierre

- **289 passed, 5 skipped** (284 → 289).
- `compileall`, `tools/verificar_plantillas.py` (49 plantillas) y
  `git diff --check` en verde.
- Sin dependencias nuevas (no se tocó `requirements*.txt` ni `requirements.lock`).

**PR #22 abierto** desde esta rama hacia `main` (se cierra el PR y luego el
usuario correrá las pruebas).

---

## 2. Incidencia abierta de Auth (registro + recuperación de contraseña)

### Síntomas reportados por el usuario (15/08/2026, noche)

1. Registrar un email nuevo → al pinchar el enlace de confirmación, aterriza en
   `/acceso` y el login dice «usuario o contraseña erróneo».
2. Recuperar contraseña → llega el email, pero al cambiar la clave dice «El
   enlace no es válido o ha caducado».
3. Luego, al pedir recuperación, salió «Supabase Auth no pudo completar la
   solicitud».

### Diagnóstico (dos causas independientes)

1. **Falta la Redirect URL `/acceso`.** El registro usa
   `redirect_to = https://cotizat.online/acceso` (en `registrar_cuenta`), pero
   en Supabase solo estaba añadida `https://cotizat.online/restablecer-clave`.
   GoTrue valida por **coincidencia exacta** (sin barra final ni `www`): si la
   URL no está en la lista, la descarta y el enlace cae al Site URL, dejando el
   email **sin confirmar** → el login devuelve «Email, contraseña o sesión no
   válidos» (la app enmascara todos los 4xx con ese mensaje).

2. **Límite del SMTP por defecto de Supabase (~2-4 correos/hora).** Al agotarse,
   GoTrue devuelve un estado no-4xx (429/5xx) y la app muestra «Supabase Auth no
   pudo completar la solicitud» (mensaje reservado para errores no 4xx).

### Acciones operativas YA realizadas por el usuario (Supabase dashboard)

- **Creó el SMTP personalizado** conectado a **Resend**:
  - Host `smtp.resend.com`, puerto `465` (SSL/TLS), usuario `resend`,
    contraseña = API key `re_...` de Resend, remitente `no-responder@cotizat.online`.
- Con esto se elimina el límite de ~2-4/hora del SMTP por defecto.

### Acciones pendientes del usuario (antes o durante las pruebas)

1. **Añadir la Redirect URL que falta** en Authentication → URL Configuration:
   - `https://cotizat.online/acceso` (confirmación de registro)
   - `https://cotizat.online/restablecer-clave` (recuperación)
   - Site URL = `https://cotizat.online`.
2. **Subir el rate limit por hora** de emails (dejarlo en ~30/hora) y mantener
   el cooldown entre emails en **60 s**.
3. Tras el merge del PR #22: reproducir el fallo y leer en **Vercel → Logs** la
   línea `Supabase Auth <método> <path> -> HTTP <código>: <cuerpo>` (el commit
   `6e175b9` la añade) para confirmar la causa exacta si algo sigue fallando.

---

## 3. Pendientes operativos del usuario (sin código)

1. **Pruebas E2E** (el usuario las hará **después del PR #22**): registro +
   confirmación de email, recuperación de contraseña, e invitación real en
   `/equipo` → correo desde `no-responder@cotizat.online` → aceptar y comprobar
   que se consume.
2. **Crear el buzón/redirección `soporte@cotizat.online`** en GoDaddy (apunta a
   su correo real). La landing y los legales ya lo publican.
   - Aclaración dejada por escrito: `no-responder@cotizat.online` **no** necesita
     buzón (Resend lo firma y envía); `soporte@` sí necesita destino real.
3. **Definir la razón social** → añadir `COTIZAT_LEGAL_ENTITY` en Vercel
   (Production) y redeploy.
4. **Vercel Hobby prohíbe uso comercial** → pasar a **Pro (20 $/mes)** antes de
   cobrar al primer cliente.

---

## 4. Aparcado por decisión del usuario

**Puntos 13-manual y 14 de la matriz de aceptación** — no pedirlos hasta que el
desarrollo esté cerrado (guía en `docs/MATRIZ_PASOS_MANUALES.md`).

---

## 5. Qué es lo siguiente

En orden recomendado:

1. **Cerrar el PR #22** y **correr las pruebas E2E** de Auth (registro +
   confirmación, recuperación, invitación en `/equipo`) — a cargo del usuario.
2. **E1-021 — revisar que el repositorio no contenga datos reales sensibles.**
3. **E1-059/E1-060 — método de cobro + recibo/contrato firmable y registro
   interno de licencias** (cierra E1-057 y el criterio «guía, oferta, contrato
   y soporte»).
4. **E1-051 — vídeo de demostración de 5 minutos** (operativo del usuario; la
   landing lo enlazará donde corresponda).
5. Iterar diseño/contenido de landing y legales (v1 aceptada con mejoras
   pendientes declaradas por el usuario).

---

## 6. Reglas invariables (no negociables)

- nunca configurar `MIGRATION_DATABASE_URL` en runtime;
- nunca usar una conexión `postgres`/administrativa como `DATABASE_URL`;
- nunca poner `service_role`/`sb_secret_` en variables públicas del frontend;
- nunca fijar `COTIZAT_REQUIRE_RLS_ROLE=false` como solución de despliegue;
- si staging falla, corregir el problema observado **sin relajar** CSRF, CSP,
  RLS, bucket privado ni la exigencia del rol limitado;
- usar solo datos ficticios en las pruebas de la matriz;
- toda dependencia nueva exige pin `==` en `requirements.txt` más
  `python tools/generar_lock.py`, o falla `tests/test_dependencias_bloqueadas.py`.

Nota operativa: el token de la app que abre cambios automáticos carece del
permiso `workflows`; `docs/ci/ci.yml` existe como copia y el workflow se instaló
manualmente.

Nota de entorno: el `.venv` no persiste entre sesiones (recrearlo es normal) y
el HEAD local puede aparecer retrocedido al inicio de una sesión nueva; si los
archivos están intactos, basta `git fetch origin <rama>` + `git reset --mixed
FETCH_HEAD` para realinear sin perder nada.

---

## 7. Mensaje para iniciar la conversación nueva

Copiar tal cual, sin añadir secretos ni tokens:

---

Continúa el proyecto CotizaT. Antes de proponer nada, lee
`docs/PUNTO_DE_CONTINUACION.md` y luego `docs/CONTINUIDAD_STAGING_SUPABASE.md`.
No repitas trabajo ya hecho y no me pidas secretos.

**Dónde quedó todo (15/08/2026, noche, cierre de la segunda parte).**

- **Rama `arena/01a00790-generador-comercial`, PR #22 abierto** hacia `main`,
  con tres commits sobre el merge del PR #20:
  1. **E1-052 `[x]`** — presupuesto de muestra comercial sin datos reales
     (`app/services/presupuesto_muestra.py` + `tools/generar_presupuesto_muestra.py`
     → `app/static/pdf/presupuesto-ejemplo.pdf`), enlazado desde la landing
     `/conocer` y cubierto por `tests/test_presupuesto_muestra.py`.
  2. **Auth** — `app/auth.py` ahora registra en el log el error real de GoTrue
     (`Supabase Auth ... -> HTTP ...`); docs de Redirect URLs actualizadas.
  3. **Fix de CI** — zip de backup determinista en
     `tests/test_instalacion_sqlite.py` (el test SHA-256 era flaky en CI).
- Suite al cierre: **289 passed, 5 skipped**.

**Incidencia de Auth (registro + recuperación) en curso:**
- Síntomas: confirmar email → login «usuario o contraseña erróneo»; recuperar
  clave → «el enlace no es válido o ha caducado»; luego «Supabase Auth no pudo
  completar la solicitud».
- Diagnóstico: faltaba la Redirect URL `/acceso` (solo estaba
  `/restablecer-clave`) + límite del SMTP por defecto de Supabase (~2-4/hora).
- **Ya creé el SMTP personalizado de Supabase con Resend** (smtp.resend.com:465,
  usuario resend, clave `re_...`, remitente `no-responder@cotizat.online`).
- Pendiente mío (operativo): añadir `https://cotizat.online/acceso` a las
  Redirect URLs de Supabase, subir el rate limit por hora (~30) y dejar el
  cooldown en 60 s.

**Mis pendientes operativos (recuérdamelos, no los bloquees):** correr las
pruebas E2E de Auth (registro+confirmación, recuperación, invitación en
`/equipo`) después del PR; crear la redirección `soporte@cotizat.online` en
GoDaddy; definir la razón social y añadir `COTIZAT_LEGAL_ENTITY` en Vercel.
Recordar: Vercel Hobby prohíbe uso comercial → pasar a Pro antes de cobrar.

**Aparcado por decisión mía:** los puntos 13-manual y 14 de la matriz, hasta que
el desarrollo esté cerrado.

**Siguiente bloque:** E1-021 (revisión de datos sensibles del repo), después
E1-059/E1-060 (cobro + recibo/contrato). El vídeo (E1-051) queda a mi cargo.

---
