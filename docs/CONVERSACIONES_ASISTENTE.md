# Conversaciones del asistente y panel de análisis

Actualización: **8 de septiembre de 2026** · revisión Alembic:
`g7c8d9e0f1a2`.

## Qué se guarda

Cada uso de `/api/ia/chat` crea o reutiliza una conversación tenant y registra:

- la pregunta y la respuesta, con el rol y el orden cronológico;
- una instantánea del correo cuando la sesión web está identificada;
- la página desde la que se abrió el asistente, el título de la primera duda y
  las fechas de creación/último turno;
- una clave opaca de conversación (`public_id`) y una clave de idempotencia por
  turno (`turn_id`).

El borrador del presupuesto no se copia en el registro: el asistente puede
usarlo para contestar, pero solo se persiste la conversación y la página de
origen. La escritura del mensaje de usuario ocurre antes de iniciar un
streaming. Si el navegador corta el stream, se conserva la respuesta recibida
marcada como incompleta.

## Dónde se consulta

En el despliegue web, un operador autenticado abre:

```text
/admin/analitica/chats
```

La pantalla está subordinada a **Analítica**, no crea una pestaña de navegación
nueva. Permite buscar en organización, usuario, título y contenido de mensajes;
filtrar por organización y fechas; paginar; abrir el detalle cronológico y
descargar el conjunto activo en JSON desde **Exportar activas**.

Todas las lecturas del panel pasan por `get_operator_db`, quedan registradas en
`eventos_admin` y usan la política RLS de operador. Una sesión de cliente no
puede convertir el filtro ORM en una lectura global. El detalle tiene una
acción de borrado permanente para tramitar una solicitud de eliminación; la
acción también se audita.

## Retención y derechos

La retención es de **365 días desde el último turno**. El cron diario de
`/api/cron/mantenimiento` llama a `purgar_conversaciones_expiradas`; el panel
oculta una conversación vencida aunque el barrido todavía no haya terminado.
La purga global solo acepta una sesión marcada por `get_cron_db` (en SQLite se
puede ejercer de forma controlada en pruebas); una sesión tenant nunca obtiene
ese bypass.

Las conversaciones no forman parte del backup/restauración de negocio
(`cotizat-backup`): el texto libre tiene una retención y un tratamiento de
privacidad diferentes. La exportación separada del panel produce
`cotizat-conversaciones_YYYYMMDD_HHMM.json`, con los mensajes activos y la
fecha de retención. El borrado desde el detalle no se recupera al restaurar un
backup de negocio.

La política pública está en `/legal/privacidad` y declara el uso para prestar y
mejorar el producto, el acceso restringido de operadores, el proveedor
opcional Groq, la retención, el no uso para entrenamiento y el canal para pedir
acceso, exportación o eliminación.

## Migración web

La revisión nueva cuelga de `f6d1a9c3e8b2` y crea:

- `public.conversaciones_ia`;
- `public.mensajes_ia`;
- índices de organización, fecha, expiración y orden;
- RLS `cotizat_app`: tenant para clientes y operador para el panel/purga;
- permisos mínimos y actualización de `baja_organizacion` para borrar los
  mensajes antes de la organización.

Antes de desplegar el código, con el rol administrativo de migraciones:

```bash
export MIGRATION_DATABASE_URL='postgresql://<admin>@<host>:5432/cotizat?sslmode=require'
alembic current
alembic upgrade head
alembic current                  # g7c8d9e0f1a2
unset MIGRATION_DATABASE_URL
```

No se debe usar el login `cotizat_runtime` para ejecutar Alembic ni poner la
URL administrativa en Vercel. Si se aplica desde Supabase SQL Editor, usar
`docs/staging_upgrade_g7c8d9e0f1a2.sql`; el script aborta si la versión previa
no es exactamente `f6d1a9c3e8b2`.

Comprobaciones posteriores:

```sql
SELECT version_num FROM public.alembic_version;
SELECT relrowsecurity, relforcerowsecurity
FROM pg_class
WHERE oid IN ('public.conversaciones_ia'::regclass,
              'public.mensajes_ia'::regclass);
```

El segundo resultado debe ser `true, true` para ambas tablas. Después del
deploy, abrir el panel con un operador y verificar una conversación de prueba,
un filtro por texto, la exportación JSON, el borrado y la respuesta de
`/readyz` con `head:g7c8d9e0f1a2`.

## SQLite local

No se ejecuta el script PostgreSQL en la aplicación de escritorio. `init_db`
crea las tablas mediante el esquema ORM y la copia SQLite normal las conserva.
El panel global de operador es una superficie web; el asistente local sí puede
registrar conversaciones en el tenant SQLite activo.
