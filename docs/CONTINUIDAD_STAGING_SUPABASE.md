# Continuidad exacta: staging Vercel + Supabase

Fecha de corte: 13/08/2026 (America/Caracas).

Este documento permite continuar el trabajo desde una conversación nueva sin
depender del historial del chat. Debe leerse junto con
`PLAN_DE_COMERCIALIZACION_Y_EVOLUCION_SAAS.md`, especialmente las secciones 1.3
y 11.

## 1. Estado confirmado del repositorio

La Etapa 1 local browser-first incluye:

- PostgreSQL y migraciones Alembic sin DDL implícito al arrancar;
- organizaciones, usuarios, membresías y propiedad empresarial;
- aislamiento tenant automático en SQLAlchemy;
- Supabase Auth con cookies HttpOnly, recuperación e invitaciones de un solo uso;
- Storage privado abstraído, metadatos en PostgreSQL y proxy autorizado;
- rol grupal PostgreSQL `cotizat_app`, contexto transaccional y políticas RLS;
- CSRF same-origin, cabeceras defensivas y rate limiting local de Auth;
- CSP con nonce para scripts y estilos, sin `unsafe-inline`;
- ausencia automatizada de handlers HTML, atributos `style`, style API directa y
  sinks de fragmentos HTML;
- auditoría de protección de rutas y ausencia de mutaciones empresariales
  directas en endpoints GET;
- rol `lectura` bloqueado antes de efectos externos de Storage.

Última validación local antes de este documento:

```text
145 passed
```

También pasaron compilación Python, parseo Jinja, `node --check` y
`git diff --check`. `.env` y `presupuestos.db` no forman parte del repositorio.

### Preparación de staging añadida desde el sandbox (14/08/2026)

Sin contactar con Supabase/Vercel (el sandbox no tiene salida TLS a esos
servicios) y sin imprimir secretos, se dejó listo:

- `/healthz` (liveness) y `/readyz` (readiness) sin autenticación. `/readyz`
  verifica configuración de Auth/Storage/`COTIZAT_PUBLIC_URL`, conexión
  PostgreSQL, head de Alembic (`c93e7a4d20f1`) y que el login runtime sea
  miembro no privilegiado de `cotizat_app`; devuelve 503 con `errors` sin
  secretos si algo falta.
- `app/tools/ensure_bucket.py` para verificar o crear `cotizat-private`
  (`public=false`, 12 MB) desde un equipo con salida TLS.
- `docs/APROVISIONAMIENTO_STAGING.md` y `docs/GUIA_STAGING_POR_CLICS.md` con el
  orden A–F paso a paso (backup, migraciones, rol runtime idempotente, bucket,
  variables de Vercel y Auth), incluyendo el formato de usuario del pooler
  `rol.ref-proyecto` y el SQL ya compilado en `docs/staging_migration.sql` y
  `docs/staging_runtime_role.sql` para pegar en el SQL Editor sin terminal.
- Compatibilidad con claves legacy JWT (`anon`/`service_role` en formato
  `eyJ...`) además de las nuevas `sb_publishable_...`/`sb_secret_...`.

La suite local quedó en **157 passed** y siguen pasando compilación Python,
parseo Jinja con el entorno real, `node --check` y `git diff --check`.

Trabajo de esta sesión en la rama `arena/019ffdba-generador-comercial`
(pendiente de abrir PR contra `main`):

```text
3de8678 docs: fija URL de staging https://cotizat-generador.vercel.app
b08891a docs: registra estado real de staging (migracion, roles, bucket)
0120946 docs: aclara formato de usuario del pooler (rol.ref-proyecto)
8959f8a staging: evita ALTER ROLE con atributos reservados en SQL Editor
9cdca2a staging: guia por clics, SQL listo y compatibilidad con claves legacy JWT
33deb39 staging: endpoints de salud y guía de aprovisionamiento Vercel+Supabase
```

El PR de integración es:

```text
https://github.com/gtrespana-bit/generador-comercial/pull/1
```

Después de fusionarlo, una conversación nueva debe trabajar desde el `main`
resultante y no intentar reconstruir los cambios desde el chat.

## 2. Estado externo conocido y no confirmado todavía

Último estado real conocido de Supabase:

```text
Alembic remoto: 9bca2ad1f6e4
Alembic esperado por el código: c93e7a4d20f1
```

Las revisiones posteriores encadenan Storage privado, invitaciones y RLS. No se
debe afirmar que están aplicadas hasta comprobar `alembic current` contra el
proyecto real.

Pendientes externos:

1. ~~respaldo recuperable de Supabase~~: el plan Free no incluye backups
   automáticos; las migraciones aplicadas son aditivas y no borraron datos.
   El propietario puede exportar manualmente desde Table Editor si lo desea.
2. ~~`alembic upgrade head` con URL administrativa~~: aplicado el 13/08/2026
   pegando `docs/staging_migration.sql` en el SQL Editor de Supabase.
   `SELECT version_num FROM alembic_version` devuelve `c93e7a4d20f1`.
3. ~~login `cotizat_runtime` limitado y miembro de `cotizat_app`~~: creado.
   Verificado `rolsuper=false`, `rolbypassrls=false`, `rolinherit=true` y
   `pg_has_role(..., 'cotizat_app', 'member') = true`.
4. ~~bucket privado `cotizat-private`~~: creado en Supabase Storage
   (`public=false`, límite 12 MB).
5. proyecto de staging HTTPS en Vercel: **repositorio importado y primer
   deploy realizado, pero con errores pendientes de diagnosticar**. El
   propietario confirmó que subió el proyecto a Vercel y reportó errores, pero
   no se ha compartido aún el Build Log/Runtime Log ni la respuesta de
   `/healthz`/`/readyz`. La URL de staging elegida es
   `https://cotizat-generador.vercel.app`.
6. Site URL y Redirect URL reales en Supabase Auth: **el propietario confirmó
   que añadió las URLs en Supabase**. Deben ser exactamente:
   - Site URL: `https://cotizat-generador.vercel.app`
   - Redirect URL: `https://cotizat-generador.vercel.app/restablecer-clave`
   En Vercel, `COTIZAT_PUBLIC_URL` también debe valer
   `https://cotizat-generador.vercel.app` (sin barra final); el propietario
   confirmó que la variable está creada. **Falta confirmar que se hizo un
   redeploy después de crear la variable y que `/readyz` responde 200.**
7. pruebas con dos emails y dos organizaciones: pendiente.
8. validación de CSP/interacciones en navegador real: pendiente.
9. rate limiting distribuido antes de escalar a múltiples instancias: pendiente.

Notas del aprovisionamiento real (2026-08-13):

- El pooler de Supabase usa el formato de usuario `rol.ref-proyecto`
  (p. ej. `cotizat_runtime.ivsuiyfljcajrijgwisg`), no solo `cotizat_runtime`.
- El `ALTER ROLE ... NOSUPERUSER ... NOBYPASSRLS` que Alembic emite de forma
  incondicional falla en el SQL Editor de Supabase cloud (el rol ejecutor no
  es superuser) con `permission denied to alter role`. `staging_migration.sql`
  y `staging_runtime_role.sql` ya crean el rol condicionalmente sin ese ALTER.
- La cadena `DATABASE_URL` para Vercel debe usar `cotizat_runtime.<ref>` y
  terminar en `?sslmode=require`. Si la contraseña lleva símbolos, debe
  percent-codificarse (o usar una de solo letras/números).

El sandbox de Arena cortó TLS al intentar acceder a Supabase y al descargar
Chromium para Playwright. No repetir esos intentos como si fueran una validación
real: ejecutar las comprobaciones desde Vercel o un equipo con salida TLS.

## 3. Orden obligatorio del siguiente bloque

> Punto exacto al 13/08/2026: Pasos A–D completados. Paso E (Vercel) con el
> proyecto importado, variables y URL configuradas, pero errores sin
> diagnosticar todavía. Paso F (Auth) hecho por el propietario en Supabase.
> **Lo siguiente en la nueva conversación es diagnosticar por qué Vercel da
> errores**, empezando por pedir el contenido de `/readyz` (o el Build/Runtime
> Log) del deployment en `https://cotizat-generador.vercel.app`.

### Paso A — Integrar y respaldar

- ✅ PR #1 fusionado.
- ⚠️ El plan Free no incluye backups automáticos; las migraciones aplicadas son
  aditivas. Se puede exportar manualmente desde Table Editor si se desea.

### Paso B — Aplicar migraciones

- ✅ Aplicado pegando `docs/staging_migration.sql` en el SQL Editor.
- `SELECT version_num FROM alembic_version` devuelve `c93e7a4d20f1`.
- Se descubrió y corrigió que el `ALTER ROLE` incondicional de Alembic falla en
  el SQL Editor de Supabase cloud (`permission denied to alter role`); el SQL
  del repositorio ya crea el rol condicionalmente.

### Paso C — Crear el login runtime

- ✅ `cotizat_runtime` creado con `docs/staging_runtime_role.sql`.
- Verificado: `rolsuper=false`, `rolbypassrls=false`, `rolinherit=true`,
  miembro de `cotizat_app=true`.
- Referencia del proyecto en el pooler: `ivsuiyfljcajrijgwisg`, host
  `aws-0-ca-central-1.pooler.supabase.com`, puerto `5432`.

### Paso D — Crear Storage privado

- ✅ Bucket `cotizat-private` creado (`public=false`, 12 MB).

### Paso E — Crear staging Vercel

- ✅ Proyecto importado a Vercel.
- ✅ URL: `https://cotizat-generador.vercel.app` (sin barra final en
  `COTIZAT_PUBLIC_URL`).
- ✅ Variables configuradas por el propietario: `DATABASE_URL` (con
  `cotizat_runtime.ivsuiyfljcajrijgwisg`), `COTIZAT_REQUIRE_RLS_ROLE=true`,
  `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `COTIZAT_STORAGE_BACKEND=supabase`,
  `SUPABASE_STORAGE_BUCKET=cotizat-private`, `SUPABASE_SECRET_KEY`,
  `COTIZAT_COOKIE_SECURE=true`, `COTIZAT_TRUST_PROXY=true`,
  `COTIZAT_PUBLIC_URL`.
- ⚠️ **Errores reportados, aún sin diagnosticar.** No se ha compartido el log.
- Pendiente de verificar: redeploy tras la variable y respuesta de
  `/healthz` (200) y `/readyz` (200 con `ok:true`).

Regla invariable:

- nunca configurar `MIGRATION_DATABASE_URL` en runtime;
- nunca usar una conexión `postgres`/administrativa como `DATABASE_URL`;
- nunca poner `service_role`/`sb_secret_` en variables públicas del frontend;
- nunca fijar `COTIZAT_REQUIRE_RLS_ROLE=false` como solución de despliegue.

### Paso F — Configurar Auth

- ✅ El propietario añadió en Supabase:
  - Site URL: `https://cotizat-generador.vercel.app`
  - Redirect URL: `https://cotizat-generador.vercel.app/restablecer-clave`
- Verificar que funcionan recuperación de contraseña e invitaciones durante la
  matriz real (correos de Supabase).

## 4. Matriz de aceptación real

No declarar staging validado hasta completar con dos correos verificados:

1. usuario A se registra, verifica email e inicia/cierra sesión;
2. A crea organización A y completa onboarding limpio o demo;
3. recuperación de contraseña llega y solo redirige al origen fijo;
4. A sube logo, producto/partida con imagen, anexo y ficha PDF;
5. A crea un presupuesto y genera/descarga PDF;
6. A invita a B y B acepta una sola vez con email coincidente y verificado;
7. B con rol `lectura` puede consultar/descargar pero no crear, editar, borrar ni
   provocar efectos de Storage;
8. al cambiar B a `miembro`, puede escribir en la organización autorizada;
9. crear organización B con nombres/números homónimos no mezcla datos con A;
10. una URL/clave de objeto de A solicitada bajo B devuelve 404;
11. cookies Auth son Secure/HttpOnly y las escrituras cross-site devuelven 403;
12. DevTools no muestra violaciones CSP ni fallos de interacción/estilos;
13. el bucket no entrega objetos sin pasar por CotizaT;
14. el arranque falla si se sustituye temporalmente `DATABASE_URL` por un rol con
    `BYPASSRLS` o fuera de `cotizat_app` (probar sin exponer credenciales).

Usar solo datos ficticios durante esta matriz.

## 5. Qué hacer después de la matriz

Si staging pasa:

1. añadir Redis/Upstash para rate limiting distribuido antes de múltiples
   instancias o exposición pública;
2. automatizar smoke tests HTTPS de Auth/rutas/CSP donde sea viable;
3. diseñar y probar importación explícita de instalaciones SQLite y objetos;
4. continuar E1-012 a E1-014 (usabilidad y medición del recorrido web);
5. preparar beta privada controlada, no lanzamiento abierto.

Si staging falla, corregir primero infraestructura o regresión observada; no
relajar CSRF, CSP, RLS, bucket privado ni la exigencia del rol limitado para
hacer que arranque.

## 6. Mensaje sugerido para iniciar una conversación nueva

Copiar este texto, sin añadir secretos:

> Continúa el proyecto CotizaT desde el `main` que incorpora el PR #1. Lee
> `docs/CONTINUIDAD_STAGING_SUPABASE.md` y
> `PLAN_DE_COMERCIALIZACION_Y_EVOLUCION_SAAS.md`, secciones 1.3 y 11. No repitas
> trabajo ya completado. El siguiente objetivo es preparar y validar staging
> Vercel + Supabase siguiendo el orden del documento. Antes de cambiar código,
> verifica el estado real de Alembic, el rol runtime, el bucket y las variables
> sin imprimir secretos. Mantén como pendientes explícitos Redis/Upstash,
> importación SQLite y validación real con dos organizaciones.
