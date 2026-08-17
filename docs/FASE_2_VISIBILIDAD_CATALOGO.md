# Fase 2 — Visibilidad y actualización incremental del catálogo

**Estado de código:** completada el 16/08/2026
**Estado de Supabase:** migración pendiente de ejecutar

## Objetivo

Permitir que cada organización adapte el catálogo general sin perder la
capacidad de recibir ampliaciones oficiales:

- una partida oficial se puede ocultar y restaurar;
- una partida creada por la organización se puede eliminar definitivamente;
- ocultar no rompe presupuestos ni borra imágenes/descompuestos;
- una actualización no vuelve a mostrar partidas ocultas;
- las partidas oficiales nuevas se incorporan automáticamente;
- los presupuestos históricos no cambian.

## Identidad estable

Cada partida oficial incorpora:

| Campo | Función |
|---|---|
| `catalogo_uid` | Identidad estable, independiente de código y clasificación. |
| `es_oficial` | Distingue contenido CotizaT de contenido de la organización. |
| `oculta` | Preferencia privada de visibilidad de la organización. |
| `version_alta_catalogo` | Versión en la que apareció por primera vez. |
| `version_catalogo` | Última versión oficial aplicada a esa copia. |

`catalogo_uid` es único dentro de la organización. Las partidas particulares
mantienen el valor `NULL` y no se confunden con las oficiales.

Para las 540 partidas actuales, el UID estable procede de su código histórico
`CT-CC-SS-NNN`. Las partidas futuras deberán declarar un UID que nunca cambie,
aunque sean reclasificadas.

## Ocultar frente a eliminar

La acción «eliminar» decide según el origen:

### Partida oficial

- se guarda `oculta=true`;
- desaparece del árbol, Spotlight, búsqueda, generador y exportación normal;
- conserva el mismo id, precio, recursos, imagen y vínculos históricos;
- aparece en `Partidas → Ocultas`;
- se puede restaurar individualmente o en lote.

### Partida personalizada

- se elimina físicamente como hasta ahora;
- antes se anulan únicamente sus vínculos de procedencia con líneas de
  presupuesto;
- la línea histórica y su precio permanecen en el presupuesto.

## Actualización incremental

Al aplicar una versión nueva:

1. se localiza cada partida por `catalogo_uid`;
2. se actualizan código y ruta sin tocar precios locales ni descompuestos
   editados;
3. se conserva `oculta` sin forzarla a falso;
4. se crean solo partidas cuyo `version_alta_catalogo` sea posterior a la
   versión que ya tenía la organización;
5. las partidas eliminadas físicamente antes de esta fase no reaparecen;
6. reintentar la misma versión es idempotente y no duplica registros.

Las 540 partidas v2 se consideran de alta en versión 2. Esto evita que un
futuro salto a v3 interprete erróneamente las partidas históricas como nuevas.

## Interfaz

`/partidas` incorpora:

- contador y acceso a `Ocultas`;
- confirmación explícita «ocultar» para oficiales;
- eliminación definitiva solo para personalizadas;
- vista paginada de ocultas;
- restauración individual;
- selección y restauración en lote;
- preservación de filtros y paginación dentro de la vista.

Las consultas que alimentan el editor y las búsquedas filtran siempre
`oculta=false`. La ficha individual sigue disponible para documentos históricos
que conserven el vínculo.

## Migración

Nuevo head Alembic:

```text
d6e2f9c4b8a1
```

Antes de desplegar en Supabase se debe ejecutar:

```text
docs/staging_upgrade_d6e2f9c4b8a1.sql
```

La migración solo añade columnas, restricción e índices. No oculta ni elimina
partidas durante su ejecución. La aplicación rellena los UID oficiales de forma
idempotente al abrir el catálogo o el editor.

## Validación

- Si se oculta una oficial, el registro y el vínculo del presupuesto sobreviven.
- La partida desaparece del índice del editor y de la búsqueda remota.
- La vista de ocultas permite restaurarla.
- La actualización conserva una partida oculta.
- Una partida simulada de v3 se incorpora una sola vez.
- Una personalizada continúa eliminándose físicamente.
- La migración completa fue probada desde una SQLite vacía hasta el nuevo head.

La siguiente etapa del orden de ejecución es construir la matriz de cobertura y
sinónimos de los 18 capítulos para iniciar la expansión masiva por familias.
