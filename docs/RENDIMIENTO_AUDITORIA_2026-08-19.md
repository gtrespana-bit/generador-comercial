# Auditoría y corrección de rendimiento (2026-08-19)

> **Nota 20/08/2026:** `b9f4d8a2c6e1` sigue siendo la revisión de índices descrita aquí, pero ya no es el head del runtime. El head actual es `a4c8e2f7b1d6` (evidencia de precios por mercado).

## Síntoma reportado

- Click en **Partidas**: 30–40 s hasta cargar.
- Click en **Presupuestos** y el resto de páginas: varios segundos.
- Sensación general de «algo está roto» con una conexión buena.

## Diagnóstico (medido con el catálogo completo: 3.006 partidas)

El despliegue web (Vercel + Supabase PostgreSQL) paginaba, **en cada click**,
trabajo que solo debía ejecutarse una vez. Medición con 25 ms de latencia
simulada por consulta (típica de base remota) y la base sembrada con el
catálogo completo y 25 presupuestos con capítulos/partidas/mediciones:

| Página               | Antes (consultas) | Antes (tiempo) | Después (consultas) | Después (tiempo) |
|----------------------|------------------:|---------------:|--------------------:|-----------------:|
| `/partidas`          |        13 + **2 cargas completas del catálogo** | 0,5 s + transferencia | 11 | 0,33 s |
| `/presupuestos`      |               480 |        12,7 s |                   8 |           0,26 s |
| `/recursos`          |               793 |        21,5 s |                   7 |           0,25 s |
| `/inicio`            |               489 |        13,1 s |                  17 |           0,59 s |
| Ficha de presupuesto |                37 |         1,0 s |                  21 |           0,58 s |

Además, cada visita a `/partidas` **hidrataba 3.546 entidades `Partida` y
transportaba 7,4 MiB de `descomposicion_json`** (medido con contador de
cargas ORM). Tras la corrección: **0 entidades, 0 MiB**. Ese volumen, vía
TLS contra PostgreSQL remoto, son varios segundos por sí solo y explica los
30–40 s cuando se combinaba con el resto.

### Causas encontradas

1. **Auditoría del catálogo en cada página** (`asegurar_catalogo_propio`,
   llamada desde `/partidas`, `/recursos`, editor y ficha de presupuesto):
   cargaba el catálogo completo (filas con JSON de varios KiB) hasta tres
   veces por visita para decidir si había que migrar. Si la fila de
   `configuracion` faltaba o la versión quedaba atrasada, re-migraba las
   ~3.006 partidas **en cada click** (bucle sin fin).
2. **N+1 de precios de mercado**: `/recursos` resolvía el precio efectivo
   con 2 SELECT por recurso (~800 consultas); el editor de presupuestos
   además abría un SAVEPOINT por recurso (~1.200 viajes).
3. **N+1 de totales**: `p.total`, `p.subtotal`… recorren capítulos →
   partidas → mediciones con cargas perezosas; la lista de presupuestos y el
   panel los tocan por fila.
4. **Sincronización de recursos en cada visita** a `/recursos`: recorría
   todos los descompuestos del catálogo cargando entidades completas.
5. **Validación de sesión con viaje completo a Supabase Auth en cada
   petición** (`GET /auth/v1/user`), abriendo conexión nueva (DNS+TCP+TLS)
   cada vez porque se usaba `urlopen` sin reutilización.
6. **Sin índices** para claves foráneas (PostgreSQL no las crea solo) ni
   para los filtros del catálogo: capítulos→partidas, mediciones,
   partidas por organización/visibilidad/capítulo, presupuestos por
   estado/cliente, etc. Todo seq-scan bajo RLS.
7. El análisis de precios del panel (`analizar_catalogo_partidas`) cargaba
   el catálogo completo con todos sus JSON para calcular márgenes.

## Correcciones

| # | Archivo | Cambio |
|---|---------|--------|
| 1 | `app/services/catalogo_propio.py` | Camino rápido de la auditoría con 2 consultas de metadatos (`count` + fila de configuración). La migración única (cuando toca) lee solo columnas de identidad, parchea los JSON por bloques de ids y escribe con UPDATE executemany. La marca `configuracion.version_catalogo` se crea ya con la versión aplicada (cierra el bucle infinito). |
| 2 | `app/auth.py` | Identidad cacheada por token (TTL `COTIZAT_AUTH_CACHE_TTL`, 180 s por omisión; nunca más del 90 % de la vida del JWT) y conexión **keep-alive** por hilo para GoTrue, con reintento único si la conexión murió. |
| 3 | `app/models.py` | `sincronizar_usuario_auth` no repite el SELECT por email cuando el perfil ya coincide (una consulta menos por petición). |
| 4 | `app/services/precios_mercado.py` | `resolver_precios_lote` / `resolver_precios_para_presupuesto_lote`: UNA consulta para todos los recursos, misma jerarquía organización → nacional → base. |
| 5 | `app/routers/presupuestos.py` | Lista y ficha cargan cliente + grafo económico con `joinedload`/`selectinload` (consultas fijas en vez de N+1); el editor resuelve los precios de mercado en lote. |
| 6 | `app/routers/inicio.py` + `app/services/analisis.py` | Panel y reportes con carga temprana del grafo y análisis de márgenes leyendo solo las columnas necesarias. |
| 7 | `app/routers/recursos.py` + `app/services/recursos.py` + `app/routers/common.py` | Precios en lote; la sincronización al **abrir** la página respeta un intervalo mínimo por organización (`COTIZAT_SYNC_RECURSOS_TTL`, 600 s; los guardados siempre fuerzan) y sus barridos leen solo las columnas que usan. |
| 8 | `app/models.py` + `migrations/versions/b9f4d8a2c6e1_rendimiento_indices_calientes.py` | 22 índices: partidas (organización+oculta / capítulo+subcapítulo / versión), presupuestos (organización+estado, cliente) y todas las FK calientes del grafo (capítulos, items, mediciones, productos, versiones, anexos, notas, facturas, cambios, pagos). Los crea Alembic en PostgreSQL, `create_all` en instalaciones nuevas y `models.migrar` en SQLite existente. |

Esta auditoría introdujo el head `b9f4d8a2c6e1`; desde el 20/08/2026 el runtime exige `a4c8e2f7b1d6`, que cuelga de él.

## Despliegue

1. Fusionar el PR → Vercel despliega el código solo. **Todas las correcciones
   de código (consultas, cachés, N+1, keep-alive) funcionan desde ese
   momento sin tocar la base de datos.** Las instalaciones de escritorio
   (SQLite) tampoco requieren nada: crean sus índices solas al arrancar.
2. **Paso manual único para la base web (Supabase)**: aplicar la migración de
   índices `b9f4d8a2c6e1`. Copia y pega
   `docs/staging_upgrade_b9f4d8a2c6e1.sql` en el SQL Editor de Supabase y
   ejecútalo (trae guarda de versión previa y es idempotente). Alternativa
   por terminal:
   `MIGRATION_DATABASE_URL=postgresql://administrador:…@host:5432/cotizat alembic upgrade head`.
3. Aplicar después `docs/staging_upgrade_a4c8e2f7b1d6.sql` y verificar `GET /readyz → {"ok": true, "alembic": "head:a4c8e2f7b1d6"}`.

Si el paso 2 se retrasa, la aplicación sigue funcionando y ya es mucho más
rápida por el código, pero `/readyz` responde 503 (la guarda de head funciona
así a propósito) y la base continúa sin índices.

## Pruebas

- `tests/test_rendimiento.py` (nuevo): la auditoría del catálogo no hidrata
  partidas en estado normal, el bucle de versión atrasada se repara una vez,
  el lote de precios coincide con la resolución individual, el cliente GoTrue
  reutiliza conexión y la identidad se cachea (y con TTL 0 no).
- Suite completa: 794 pruebas en verde.
