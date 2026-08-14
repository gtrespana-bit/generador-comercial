# Staging sin terminal: guía por clics (Supabase Free + Vercel)

Si no tienes terminal o no quieres usar `pg_dump`/Alembic, esta guía hace el
mismo trabajo desde el navegador. Es la versión “manual” de
[`APROVISIONAMIENTO_STAGING.md`](APROVISIONAMIENTO_STAGING.md). No necesitas
instalar nada.

## Lo que el plan Free de Supabase sí y no te da

- **No** hay backups automáticos en el plan Free. Por eso las migraciones de
  CotizaT son **aditivas** (solo crean tablas, columnas, funciones y
  políticas; no borran tus datos). Aun así, antes de migrar, ve a
  **Table Editor** y anota/exporta lo que tengas si quieres una red de
  seguridad.
- **Sí** puedes ejecutar SQL en **SQL Editor** (lo usamos para las
  migraciones y el rol runtime).
- **Sí** tienes Storage para crear el bucket privado.

---

## Paso 1 — Aplicar las migraciones en Supabase (SQL)

1. Abre tu proyecto en Supabase.
2. En el menú izquierdo, pulsa **SQL Editor** → **New query**.
3. Abre el archivo `docs/staging_migration.sql` que viene en el repositorio,
   copia **todo su contenido** y pégalo en el editor.
4. Pulsa **Run** (o `Ctrl/Cmd + Enter`).
   - Verás “Success. No rows returned” o resultados de los SELECT.
   - El archivo va dentro de una transacción (`BEGIN; … COMMIT;`): si algo
     falla, no se aplica a medias.
5. Comprueba que quedó en la versión correcta: en una nueva consulta pega y
   ejecuta:

   ```sql
   SELECT version_num FROM alembic_version;
   ```

   Tiene que devolver **exactamente**:

   ```text
   c93e7a4d20f1
   ```

Eso es todo el “Alembic upgrade head”; no necesitas instalar Alembic.

---

## Paso 2 — Crear el login de la aplicación (`cotizat_runtime`)

Este es el usuario que usará Vercel para conectarse a la base de datos. Tiene
permisos limitados y no se salta el aislamiento (RLS).

1. Sigue en **SQL Editor** → **New query**.
2. Abre `docs/staging_runtime_role.sql`.
3. **Antes de ejecutarlo**, cambia `CAMBIA_ESTA_CONTRASEÑA_LARGA` por una
   contraseña larga y aleatoria que inventes ahora mismo.
   - No uses tu contraseña de Supabase ni la de tu correo.
   - No me la envíes ni la guardes en el repositorio. La pondrás luego en
     Vercel como variable de entorno.
4. Pulsa **Run**.
5. Al final del archivo están los dos SELECT de verificación. Ejecútalos y
   confirma:
   - `rolsuper = false`, `rolbypassrls = false`, `rolinherit = true`.
   - `miembro_cotizat_app = true`.

---

## Paso 3 — Crear el bucket privado `cotizat-private`

Aquí se guardan logos, imágenes, anexos y fichas técnicas. **Debe ser
privado**: el proxy de CotizaT es quien autoriza las descargas.

1. En Supabase, menú izquierdo → **Storage**.
2. Pulsa **New bucket** (o “Create bucket”).
3. Rellena:
   - **Name**: `cotizat-private`
   - **Public bucket**: **desmarcado** (OFF)
   - **File size limit**: activa el límite y pon `12` MB
   - **Allowed MIME types** (si aparece): deja el predeterminado o añade
     `image/png`, `image/jpeg`, `image/webp`, `image/gif`, `application/pdf`
4. Pulsa **Save**.
5. No añadas ninguna “policy” que dé acceso público a `anon` o
   `authenticated`. La aplicación usa su clave secreta en el backend.

---

## Paso 4 — Reunir los datos que pondrás en Vercel

En Supabase:

1. **Project URL**: menú izquierdo → **Project Settings** → **Data API** (o
   **API**). Copia el valor de **Project URL** (algo como
   `https://abcd1234.supabase.co`). Esa es tu `SUPABASE_URL`.
2. **Clave publicable (`anon`)**: en esa misma pantalla, en **Project API
   keys**, copia la clave etiquetada como **anon public**.
   - En proyectos nuevos se llama `sb_publishable_...`; en proyectos antiguos
     es un texto largo que empieza por `eyJ...`. Ambas valen.
   - Esta es `SUPABASE_PUBLISHABLE_KEY`.
3. **Clave secreta del servidor**: copia la clave **service_role** (o
   `sb_secret_...`).
   - Es secreta: solo va en Vercel (backend), nunca en el navegador ni en el
     chat.
   - Esta es `SUPABASE_SECRET_KEY`.
4. **Cadena de conexión para la app**: menú **Project Settings** → **Database**
   → **Connection string**. Usa la opción **URI** y:
   - Escoge el modo **Transaction** o **Session pooler** (puerto 6543/5432
     según te muestre; ambos valen, pero para Vercel serverless suele
     recomendarse el pooler **Transaction**).
   - El usuario que trae por defecto es `postgres.<ref>`; **cámbialo** por
     `cotizat_runtime.<ref>` (en el pooler de Supabase el formato es
     `rol.ref-del-proyecto`; si tu cadena es
     `postgres.ivsuiyfljcajrijgwisg`, deja `ivsuiyfljcajrijgwisg` y cambia
     solo `postgres` por `cotizat_runtime`).
   - Sustituye el marcador de contraseña por la que pusiste en el Paso 2.
   - Asegúrate de que termina en `?sslmode=require`.
   - Resultado esperado (ejemplo con el patrón del pooler):

     ```text
     postgresql://cotizat_runtime.ivsuiyfljcajrijgwisg:TU_CONTRASEÑA@aws-0-<region>.pooler.supabase.com:6543/postgres?sslmode=require
     ```

   - Esa cadena es tu `DATABASE_URL`.

Apunta estos 4 valores en un lugar seguro momentáneamente (los pegarás en
Vercel):

- `SUPABASE_URL`
- `SUPABASE_PUBLISHABLE_KEY`
- `SUPABASE_SECRET_KEY`
- `DATABASE_URL` (con `cotizat_runtime` y su contraseña)

---

## Paso 5 — Crear el proyecto en Vercel e importar el repo

1. Entra en [vercel.com](https://vercel.com) con tu cuenta.
2. **Add New… → Project**.
3. Importa el repositorio `generador-comercial` (conecta GitHub si te lo pide).
4. Antes de desplegar, expande **Environment Variables** (o hazlo luego en
   **Settings → Environment Variables**).
5. Añade estas variables (una por una), todas para el entorno **Production**,
   **Preview** y **Development** si quieres que también apliquen a los
   previews:

   | Clave | Valor |
   |---|---|
   | `DATABASE_URL` | la cadena del Paso 4 con `cotizat_runtime` |
   | `COTIZAT_REQUIRE_RLS_ROLE` | `true` |
   | `SUPABASE_URL` | la URL del proyecto |
   | `SUPABASE_PUBLISHABLE_KEY` | la clave `anon`/`sb_publishable_` |
   | `COTIZAT_STORAGE_BACKEND` | `supabase` |
   | `SUPABASE_STORAGE_BUCKET` | `cotizat-private` |
   | `SUPABASE_SECRET_KEY` | la clave `service_role`/`sb_secret_` |
   | `COTIZAT_COOKIE_SECURE` | `true` |
   | `COTIZAT_TRUST_PROXY` | `true` |
   | `COTIZAT_PUBLIC_URL` | (lo rellenamos en el siguiente paso) |

6. **No** añadas `MIGRATION_DATABASE_URL`. No pongas una URL de `postgres`
   administrador como `DATABASE_URL`.
7. Pulsa **Deploy**.

---

## Paso 6 — Fijar la URL pública y redirigir Auth

1. Cuando termine el primer despliegue, Vercel te da un dominio, por ejemplo
   `https://cotizat-generador.vercel.app`.
2. Vuelve a Vercel → tu proyecto → **Settings → Environment Variables**, crea
   o edita:
   - `COTIZAT_PUBLIC_URL` = `https://cotizat-generador.vercel.app`
     (sin barra al final).
3. En Supabase → **Authentication** → **URL Configuration**:
   - **Site URL**: `https://cotizat-generador.vercel.app`
   - **Redirect URLs**: añade
     `https://cotizat-generador.vercel.app/restablecer-clave`
4. En Vercel → pestaña **Deployments**, abre el menú del último deployment →
   **Redeploy** para que tome la variable nueva.

---

## Paso 7 — Probar que arrancó

Abre en el navegador:

```text
https://cotizat-generador.vercel.app/healthz
https://cotizat-generador.vercel.app/readyz
```

- `/healthz` debe devolver `200` con `{"ok": true, ...}`.
- `/readyz` debe devolver `200` con `"ok": true`. Si responde `503`, lee el
  array `errors`: te dice exactamente qué falta (migración, rol, Auth, bucket,
  URL pública).

Luego abre la raíz (`/`): debe llevarte a `/acceso` (pantalla de iniciar
sesión).

---

## Quiero que me informes del resultado

Pásame, sin ninguna contraseña:

1. El resultado de `SELECT version_num FROM alembic_version;`
   (debe ser `c93e7a4d20f1`).
2. Los resultados de los SELECT del rol runtime
   (`false, false, true` y `true`).
3. El código HTTP de `/healthz` y `/readyz` (200/200 idealmente).
4. Si `/readyz` da 503, pega su contenido `errors` (no incluye secretos).

Con eso te digo si se puede pasar a la matriz de aceptación con dos correos.
