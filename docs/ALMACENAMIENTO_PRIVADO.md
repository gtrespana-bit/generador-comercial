# Almacenamiento privado de CotizaT

## Estado y decisión

CotizaT ya no depende de rutas físicas para archivos nuevos. Los modelos
comerciales guardan referencias independientes del proveedor:

```text
storage://organizaciones/<organizacion_id>/<categoria>/<archivo>
```

El binario vive en un `StorageBackend`. PostgreSQL conserva únicamente clave,
organización, categoría, MIME, tamaño, SHA-256, nombre original y metadatos en
`archivos_almacenados`; nunca guarda el binario.

Backends disponibles:

- `LocalStorage`: desarrollo/compatibilidad. Los objetos nuevos viven en
  `private_storage/`, fuera de `/static`, y pasan por autorización.
- `SupabaseStorage`: destino web, para el bucket privado previsto
  `cotizat-private`.

La interfaz permite sustituir Supabase por Cloudflare R2 sin cambiar logos,
presupuestos, partidas o productos.

## Cobertura

La abstracción cubre logotipo, imágenes de productos y partidas, foto de
proyecto, firma del cliente, anexos PDF, fichas técnicas PDF y fuentes/manifiestos
CYPE.

Las rutas históricas `uploads/...` siguen legibles. En SQLite local se conserva
el montaje estático; en PostgreSQL se bloquea y las referencias pasan por
`/archivos-legado/...`, que comprueba que un registro de la organización activa
las use. Su migración futura requerirá inventario y checksums.

## Autorización y aislamiento

El navegador nunca recibe una URL pública de Supabase. Jinja y JavaScript
convierten una referencia en:

```text
/archivos/organizaciones/42/productos/archivo.png
```

El endpoint exige sesión y organización mediante `get_db`, valida el prefijo
tenant, consulta metadatos bajo el filtro ORM y solo entonces lee Storage. Las
respuestas usan caché privada, `nosniff`, CSP `sandbox` y política same-origin.
Los manifiestos JSON internos no se descargan.

Además, las claves rechazan rutas absolutas, barras invertidas, `..`, segmentos
vacíos y caracteres no permitidos. Un `CHECK` de base obliga a que la clave de
metadatos corresponda a `organizacion_id`. Las referencias ocultas enviadas por
el editor también se revalidan para impedir que un tenant inyecte una imagen de
otro en un PDF.

## Configuración

SQLite elige `local` por defecto; PostgreSQL elige `supabase`:

```dotenv
COTIZAT_STORAGE_BACKEND=supabase
SUPABASE_URL=https://<proyecto>.supabase.co
SUPABASE_STORAGE_BUCKET=cotizat-private
SUPABASE_SECRET_KEY=sb_secret_<valor-real>
```

`SUPABASE_SECRET_KEY` no sustituye a la publishable key de Auth. Es exclusiva
del servidor: no entra en Git, plantillas, JavaScript, logs ni variables
públicas. Las nuevas claves `sb_secret_` son opacas, no JWT, y se envían en
`apikey`, nunca como Bearer.

## Bucket: acción deliberadamente pendiente

El código **no crea el bucket al arrancar**. `create_private_bucket()` existe
para una acción administrativa explícita y fuerza `public: false`, 12 MB y una
lista MIME. En este bloque no se creó el bucket real ni política pública.

Para habilitar el entorno real:

1. aplicar Alembic hasta el head vigente `c93e7a4d20f1` (incluye `72e6f4d8a1c3`);
2. crear/verificar `cotizat-private` como privado;
3. configurar la secret key solo en backend;
4. probar subida, lectura, descarga, PDF y borrado con dos organizaciones;
5. confirmar que una clave de A devuelve 404 bajo B;
6. verificar que no exista acceso público.

El navegador no opera directamente contra Storage, por lo que no necesita
políticas de lectura para `anon`/`authenticated`. La secret key omite RLS de
Storage y hace que el proxy de aplicación sea la frontera de autorización.

## PDF y serverless

ReportLab necesita una ruta. Los objetos remotos se materializan en `/tmp` con
directorio `0700`, archivo `0600` y nombre derivado del SHA-256 de la clave.
Esto funciona en runtimes con filesystem de solo lectura salvo `/tmp`; la
persistencia continúa en Storage.

## Backup local y futura migración

Los backups SQLite incluyen `presupuestos.db`, `uploads/` histórico y
`private_storage/` nuevo. Backup/restore de archivos permanece desactivado en
PostgreSQL, donde debe existir estrategia administrada para base y objetos.

La migración histórica será reanudable: inventariar por organización, validar
MIME/tamaño, calcular checksum, subir bajo `organizaciones/<id>/...`, insertar
metadatos, actualizar referencias y comparar conteos antes de borrar locales.

## Validación y límites honestos

Las pruebas cubren claves/traversal, constraint tenant, aislamiento ORM, proxy,
metadatos sin binarios, backend local, REST Supabase simulado, bucket privado,
borrado compartido y materialización PDF. La prueba real contra Supabase
Storage sigue pendiente en un runner/despliegue con salida TLS al proyecto.

Este bloque no autoriza publicar CotizaT. CSRF por origen y cabeceras globales
ya están implementados, pero siguen pendientes CSP/XSS final, aplicar/probar el
rol PostgreSQL y las políticas RLS, pruebas reales de Auth/Storage y auditoría.

Referencias oficiales:

- https://supabase.com/docs/guides/getting-started/migrating-to-new-api-keys
- https://supabase.com/docs/guides/storage/security/access-control
- https://supabase.com/docs/reference/python/storage-from-upload
