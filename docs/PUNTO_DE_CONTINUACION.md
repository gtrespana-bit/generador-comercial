# Punto exacto de continuación

Fecha de corte: **16/08/2026, tarde (cierre de la cuarta parte de la sesión)** (America/Caracas).

Este documento retoma el trabajo sin depender del historial del chat. Describe
**dónde quedó exactamente** el trabajo y **qué sigue**, en ese orden. Léelo
junto con `docs/CONTINUIDAD_STAGING_SUPABASE.md` (estado de staging/matriz) y
`PLAN_DE_COMERCIALIZACION_Y_EVOLUCION_SAAS.md` (E1-052, E1-056 y siguientes).

---

## 0. Lo último hecho: rama `arena/01a007cf-generador-comercial` (E1-021 + E1-060)

El **PR #23 está fusionado** (merge `52d1a09`, título «E1-021 (datos sensibles)
+ fix de invitaciones sin cuenta previa»); la sección 1 queda como histórico.
Sobre ese merge, esta sesión cerró **E1-021 — repositorio privado y sin datos
reales sensibles**:

- `tools/auditar_datos_sensibles.py`: auditoría repetible de todo lo versionado
  (credenciales de Supabase/Resend/GitHub/AWS, JWT, PEM, cadenas de conexión con
  contraseña real, correos personales, teléfonos VE/ES, documentos fiscales,
  referencias del proyecto Supabase/Upstash y archivos que nunca deben
  versionarse). Distingue marcadores de valores reales, así que no genera ruido.
- **Repositorio confirmado privado** (`private: true`, 0 forks).
- **Historial completo auditado**: se recuperó el histórico (`--unshallow`) y se
  recorrieron los **653 blobs de los 101 commits**. **No hay ni hubo ninguna
  credencial real** → *no hace falta reescribir el histórico ni rotar claves*.
- **Tres datos reales corregidos en el árbol**: el correo personal del
  propietario en `HOJA_DE_RUTA_Y_ESTADO_DEL_PROYECTO.md` y dos apariciones de la
  referencia del proyecto Supabase en `docs/GUIA_STAGING_POR_CLICS.md`.
- `tests/test_datos_sensibles.py` (34 pruebas) deja la auditoría vigilada en CI.
- `docs/DATOS_SENSIBLES.md`: alcance, resultado y reglas de escritura.

Suite tras el bloque: **323 passed, 5 skipped**. `compileall`, plantillas
(49), lock (42 paquetes), simulación de Vercel RO y `git diff --check` en verde.

### Corrección de UX de invitaciones (16/08/2026)

Tras las pruebas E2E, el usuario confirmó que registro, confirmación, cambio de
contraseña e invitaciones **funcionan**, pero aceptar una invitación **sin tener
cuenta previa** obligaba a un rodeo: registrarse, confirmar el email, aterrizar
en «crea tu empresa» sin rastro de la invitación y **volver al correo a pulsar
el enlace por segunda vez**.

Causa: el enlace de confirmación de Supabase usa un `redirect_to` fijo
(`/acceso`) y pierde el `?next=/invitaciones/<token>/aceptar`; como el token solo
vivía en el email, la invitación era invisible dentro de la aplicación.

Corregido descubriendo la invitación **desde la sesión** (por email verificado),
no desde el token:

- `/organizaciones` lista las invitaciones pendientes con un botón de aceptar;
- `/invitaciones/pendientes/{id}/aceptar` es la vía sin token;
- `/organizaciones/nueva` redirige al panel si hay invitación pendiente y
  ninguna membresía;
- ambas vías comparten `_consumir_invitacion`, así que no pueden divergir en
  seguridad (sesión + email verificado + destinatario exacto).

Cubierto por `tests/test_invitacion_sin_cuenta.py` (5 pruebas HTTP) y 6 pruebas
nuevas en `tests/test_invitations.py`. Suite: **335 passed, 5 skipped**.

### Contenido comercial cerrado (16/08/2026)

- **E1-053 `[x]`** — `/legal/preguntas`: 17 preguntas en 5 bloques, enlazada
  desde la landing y el pie legal. Declara el acceso anticipado y repite que los
  documentos **no son facturas fiscales**; una prueba falla si algún día la FAQ
  llegara a prometer lo contrario.
- **E1-054 `[x]`** y **E1-055 `[x]`** — ya estaban cubiertos por
  `/legal/soporte` §2–§3 (incluido/excluido) y §5 (reporte con evidencia sin
  datos de clientes); ahora quedan protegidos por pruebas.

Suite: **342 passed, 5 skipped**.

### E1-059 — investigado, decisión del titular

Stripe **no opera en Venezuela**; Wise/Payoneer restringen a residentes
venezolanos y los *merchant of record* (Paddle, Lemon Squeezy) exigen entidad en
país soportado. **El titular es español y reside también en España**, así que la
vía limpia es **autónomo en España + Stripe** (036 + RETA), con cuota, IVA/IRPF
trimestrales y OSS solo si se superan 10.000 €/año a particulares de la UE.
Para el piloto inmediato basta el **cobro manual**. Análisis en
`docs/COBRO_Y_LICENCIAS.md`.

### E1-060 — diseñado, pendiente de construir

Decisión del titular: el registro de licencias va **dentro de la aplicación**.
Ojo, no es trivial: hoy **no existe** rol de superadministrador y todas las
tablas de negocio son *tenant* bajo RLS. Una licencia no pertenece a ninguna
organización, así que exige tabla **no-tenant** con RLS propia, rol de operador
por variable de entorno, panel `/admin/licencias`, recibo PDF y auditoría. Es
una excepción deliberada al aislamiento: debe abordarse como su propio bloque.

### E1-060 — panel de operador construido (16/08/2026)

`/admin/licencias`: ver, conceder, renovar, **regalar prueba/cortesía**,
compensar incidencias y cancelar con constancia. Resumen con organizaciones sin
licencia e ingresos (solo cuenta `origen='pago'`), y aviso ámbar a 15 días.

**Aislamiento resuelto de raíz**, que era el riesgo señalado:
`licencias` es tabla **no-tenant** con RLS propia (`cotizat_licencia_*`) que
exige `cotizat.es_operador`; la lista de operadores vive en
`COTIZAT_OPERADORES` (**variable de entorno, no columna**, para que no exista
escalada escribiendo en la base) y se exige email verificado. 18 pruebas en
`tests/test_licencias.py`. Suite: **362 passed, 5 skipped**.

### E1-060 — desplegado en producción y verificado (16/08/2026)

Los dos pasos obligatorios quedaron **completados** (detalle y evidencia en
`docs/PANEL_DE_OPERADOR.md` §5):

1. **Migración `f4c1d8e37a95` aplicada** en Supabase con el script
   `docs/staging_upgrade_f4c1d8e37a95.sql` (SQL Editor; guarda de versión +
   transacción). `/readyz` pasó a `"alembic": "head:f4c1d8e37a95"` con `ok: true`.
   El check RLS del propio script devolvió `true/true/true`.
2. **`COTIZAT_OPERADORES` añadida en Vercel** (Production) y **redeploy**.
   El titular entró a **https://cotizat.online/admin/licencias**, inició sesión
   con su correo verificado y **confirmó que el panel funciona**.

**Decisión del titular (16/08/2026):** el panel se queda **deliberadamente
simple** por ahora — solo lo esencial. La mejora de la interfaz queda anotada
como pendiente futuro, no como bloqueante.

Pendiente dentro de E1-060: recibo/contrato en PDF, corte automático de acceso
y avisos de vencimiento por correo (los tres esperan, sobre todo, a la decisión
de cobro de E1-059).

**Siguiente bloque: E1-059** (decisión de cobro del titular) y, con ella, el
recibo en PDF.

---

## 1. Histórico: rama `arena/01a00790-generador-comercial` (PR #22, fusionado)

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

> **Guía paso a paso: `docs/PENDIENTES_OPERATIVOS.md`** (dónde está cada ajuste
> en Supabase, GoDaddy y Vercel, con el DNS real ya comprobado).
>
> **Estado al 16/08/2026.** Ninguno bloquea el desarrollo, pero
> siguen abiertos y hay que recordarlos en cada sesión:
> 1. Añadir `https://cotizat.online/acceso` a las Redirect URLs de Supabase,
>    subir el rate limit de emails a ~30/hora y dejar el cooldown en 60 s.
> 2. ~~Pruebas E2E de Auth.~~ **Hechas el 15/08/2026**: registro, confirmación,
>    cambio de contraseña e invitaciones (con y sin cuenta previa) verificados.
>    De ahí salió la corrección de UX de invitaciones descrita arriba; conviene
>    repetir el caso «sin cuenta» tras desplegarla.
> 3. Crear `soporte@cotizat.online`. **Ojo**: GoDaddy retiró el reenvío
>    gratuito y el dominio raíz **no tiene MX**, así que hoy un correo a esa
>    dirección rebota. Alternativa gratuita (Forward Email / ImprovMX /
>    Cloudflare) en `docs/PENDIENTES_OPERATIVOS.md` §3.
> 4. Definir la razón social y añadir `COTIZAT_LEGAL_ENTITY` en Vercel
>    (Production) + redeploy.
> 5. **Vercel Hobby prohíbe el uso comercial** → pasar a Pro antes de cobrar al
>    primer cliente. **Aplazado por decisión del usuario** (16/08/2026):
>    sin cobros todavía, no corre prisa.

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

1. ~~**Cerrar el PR #22** y correr las pruebas E2E de Auth.~~ **PR #23 fusionado
   el 16/08/2026** (merge `52d1a09`, incluye E1-021, el fix de invitaciones sin
   cuenta previa y el panel E1-060). Pruebas E2E de Auth **hechas el
   15/08/2026**: registro, confirmación, cambio de contraseña e invitaciones.
2. ~~**E1-021 — revisar que el repositorio no contenga datos reales
   sensibles.**~~ **Completado el 15/08/2026** (ver sección 0 y
   `docs/DATOS_SENSIBLES.md`).
3. ~~**E1-060 — panel de operador.**~~ **Desplegado y verificado el 16/08/2026**
   en `https://cotizat.online/admin/licencias` (sección 0 y
   `docs/PANEL_DE_OPERADOR.md`). Queda **E1-059 — decisión de cobro del
   titular** (análisis en `docs/COBRO_Y_LICENCIAS.md`) y con ella el recibo en
   PDF, el corte automático de acceso y los avisos de vencimiento.
4. **E1-051 — vídeo de demostración de 5 minutos** (operativo del usuario; la
   landing lo enlazará donde corresponda).
5. Iterar diseño/contenido de landing y legales (v1 aceptada con mejoras
   pendientes declaradas por el usuario). El panel de operador se quedó
   deliberadamente simple por ahora; su mejora de interfaz es otro pendiente
   futuro, no bloqueante.

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

**Dónde quedó todo (16/08/2026, tarde, cierre de la cuarta parte).**

- **PR #23 fusionado** (merge `52d1a09`): E1-021 (datos sensibles), fix de
  invitaciones sin cuenta previa y **E1-060 — panel de operador**
  (`/admin/licencias`) construido y probado (362 passed, 5 skipped).
- **E1-060 DESPLEGADO EN PRODUCCIÓN y verificado el 16/08/2026**:
  1. Migración `f4c1d8e37a95` aplicada en Supabase con el script
     `docs/staging_upgrade_f4c1d8e37a95.sql` (SQL Editor). `/readyz` responde
     `"alembic": "head:f4c1d8e37a95"` con `ok: true`.
  2. `COTIZAT_OPERADORES` añadida en Vercel (Production) + redeploy.
  3. El titular entró a `https://cotizat.online/admin/licencias` y confirmó
     que funciona. Por decisión suya, el panel se queda deliberadamente simple
     por ahora; la mejora de interfaz es pendiente futuro.
- **Pendiente dentro de E1-060:** recibo en PDF, corte automático de acceso y
  avisos de vencimiento (esperan a E1-059).
- Suite al cierre de código: **362 passed, 5 skipped**. Rama de esta sesión:
  `arena/01a00825-generador-comercial` (commits de docs `.env.example` +
  script SQL de la migración, ya en GitHub).

**Incidencia de Auth (registro + recuperación) — resuelta en operativo:**
- SMTP personalizado de Supabase con Resend creado por el titular.
- Pendientes operativos suyos aún abiertos: añadir
  `https://cotizat.online/acceso` a las Redirect URLs de Supabase, subir el
  rate limit por hora (~30) y dejar el cooldown en 60 s; crear la redirección
  `soporte@cotizat.online` en GoDaddy; definir la razón social y añadir
  `COTIZAT_LEGAL_ENTITY` en Vercel; Vercel Hobby → Pro antes de cobrar.

**Aparcado por decisión mía:** los puntos 13-manual y 14 de la matriz, hasta que
el desarrollo esté cerrado.

**Siguiente bloque:** **E1-059 — decisión de cobro del titular** (análisis en
`docs/COBRO_Y_LICENCIAS.md`) y, con ella, el recibo en PDF, el corte automático
de acceso y los avisos de vencimiento. E1-021 y el panel E1-060 ya están
cerrados/desplegados. El vídeo (E1-051) queda a mi cargo.

---
