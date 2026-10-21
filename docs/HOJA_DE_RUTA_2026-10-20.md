# Hoja de ruta tras el análisis completo (2026-10-20)

Origen: auditoría de estructura, rendimiento y SEO pedida por el titular el
20/10/2026, con mediciones sobre el código (queries por página, pesos,
similitud de contenido entre países, inventario real del sitemap). Este
documento ordena el trabajo aprobado. **El orden es la decisión importante**:
cada fase deja el terreno listo para la siguiente y ninguna obliga a rehacer
una anterior.

## Principios (no negociables: hay usuarios de pago dentro)

1. **Redes antes que cambios.** Primero se refuerza la capacidad de detectar
   un problema (tests contra PostgreSQL real, registro de errores), y solo
   después se tocan cosas con riesgo.
2. **PR pequeños y revertibles.** Nunca dos cambios con riesgo en el mismo
   despliegue. Cada merge se verifica antes de dar el siguiente paso:
   `/readyz` en verde + smoke manual del flujo tocado.
3. **Todo lo que toca dinero o acceso, detrás de un interruptor** (flag por
   variable de entorno), desplegado apagado y encendido después de verificar.
4. **Migraciones expand/contract:** primero se añade (compatible con el
   código viejo), se despliega, y lo obsoleto se retira en otra PR posterior.
   Así el orden exacto entre migrar y desplegar deja de ser crítico.
5. **Rollback ensayado:** revertir el merge o redesplegar el commit anterior
   en Vercel debe ser siempre posible en minutos. Nada de cambios de datos
   irreversibles sin respaldo previo verificado.
6. **Sin big-bang.** Lo que puede migrar por tandas (plantillas en inglés),
   migra por tandas conviviendo con lo viejo.

---

## Fase 0 — Redes de seguridad

*No toca lógica de negocio. Sin esta fase, todo lo demás es a ciegas.*

- **0.1 CI contra PostgreSQL real** *(punto 1 del análisis).* ✅ **HECHA
  (PR #137 + job pegado por el titular, verde desde la primera corrida,
  20/10/2026).** Job con servicio PostgreSQL 16: aplica las migraciones
  desde cero y corre la batería sensible (licencias, compras, soporte,
  aislamiento multi-tenant/RLS, `_check_seo`) con el login runtime sin
  bypass — `tests/test_postgresql_rls.py` + `tests/test_rls_postgres.py`.
  De paso se reparó que **la cadena Alembic no se reconstruía desde una
  base vacía** (3 de 55 revisiones) y un bug latente en
  `health._condicion_activo` (decidía por el motor global, no por la
  conexión). Ampliación progresiva: cada fase nueva con superficie PG
  añade su caso aquí (la 0.2 ya lo hizo).
- **0.2 Registro interno de errores** *(punto 2).* ✅ **HECHA (20/10/2026).**
  Tabla `errores_internos` con huella de deduplicación (conteo,
  primera/última vez, ruta saneada, **traza redactada**), alimentada por el
  middleware de captura existente **solo cuando ya hay un 500** (coste cero
  en el camino feliz, *best-effort* con sesión propia: si el registro
  falla —incluida la tabla sin migrar—, la respuesta no se rompe). En
  PostgreSQL la escritura entra por función SECURITY DEFINER y la lectura
  es solo del operador (RLS); el panel (Sistema › Estado) muestra la
  traza y permite marcar **resuelta** (una recurrencia se desmarca sola).
  Correo al buzón de avisos solo ante huella nueva o resucitada (tope
  5/hora) y parte diario de activas en el cron de mantenimiento, con poda
  a 90 días. Sin SDK de terceros; flag `COTIZAT_ERRORES_BD` (encendido).
  Detalle en `docs/MONITORIZACION_Y_DIAGNOSTICO.md` §4.
  - *Titular (pendiente):* monitor externo de disponibilidad (UptimeRobot
    o similar, gratuito) contra `/readyz` y la home: es lo único que avisa
    si cae Vercel entero.
- **0.3 Migraciones automáticas** *(punto 3).* ❌ **DESCARTADA por decisión
  del titular (20/10/2026).** Prefiere aplicar las migraciones a mano en el
  SQL Editor de Supabase para llevar él mismo el control de cuáles se han
  aplicado y cuáles no. El flujo manual queda como norma: cada migración
  trae su `docs/staging_upgrade_<rev>.sql` transaccional con guarda de
  versión (CI lo exige), las migraciones son aditivas (expand/contract,
  principio 4) para que la ventana código↔esquema sea inocua, y `/readyz`
  muestra el head real frente al esperado. No re-proponer la automatización
  salvo que el titular cambie de criterio.
- **0.4 CI en dos velocidades** *(punto 10, primera parte).* "Humo"
  (<2 min) en cada push de rama y suite completa en PR a `main`. Sin tocar
  ningún test todavía: es solo organización del workflow.

**Hecho cuando:** un error forzado en una preview aparece en el panel y llega
por correo; el job PG detecta a propósito un INSERT con RETURNING (se
comprueba rompiéndolo en una rama desechable). *(La 0.3 salió de esta
definición al descartarse; con 0.1, 0.2 y 0.4 la fase queda cerrada.)*

## Fase 1 — Rendimiento y peso del despliegue

*Antes que el SEO nuevo: las URLs que vengan deben nacer cacheadas y leyendo
la fuente de datos definitiva.*

- **1.1 Región de las funciones = región de Supabase** *(punto 5).* ✅ HECHA
  (2026-10-20). El proyecto Supabase está en **ca-central-1** (Montreal) y
  las funciones corrían por defecto en `iad1` (Washington, D.C.):
  `vercel.json` fija ahora `yul1`, la pareja exacta de ca-central-1, para
  que las 4–18 consultas secuenciales por página de panel dejen de pagar
  el viaje entre regiones. La base de datos **se queda en Canadá**
  (decisión de 2026-10-20): moverla sería una migración de proyecto
  completa (datos, Auth y Storage) con parada y riesgo para usuarios de
  pago, y el coste dominante era el tramo función↔BD, no usuario→función;
  la costa este norteamericana es además el punto medio razonable entre
  España y LatAm. Solo se replanteará si el tráfico muestra un dominio
  claro de una sola zona. Guarda en `tests/test_vercel_cron_config.py`.
- **1.2 Caché CDN de las páginas públicas sin sesión** *(punto 5).* ✅ HECHA
  (2026-10-20). Landing, homes de país, temas, guías, legal, sitemap y robots
  con `s-maxage=300` + `stale-while-revalidate`/`stale-if-error` de un día.
  Como Vercel considera no-cacheable cualquier `Vary: Cookie`, el idioma de
  la superficie pública sale solo de la URL (prefijo `/en`); la cookie sigue
  mandando fuera (panel, `/soporte`, `/pago`). `app/cache_publico.py` pone
  la lista blanca de rutas y un middleware fail-open con guardas estrictas
  (GET 200, sin query, sin cookies de sesión, sin `Set-Cookie` en la
  respuesta); las cookies de preferencia solo se fijan si cambian el valor.
  Excepciones a propósito: `/pago` (varía por cookie de país y `?msg=`) y
  `/soporte` (formulario con idioma por cookie).
- **1.3 Artefactos mínimos de runtime** *(punto 7).* ✅ HECHA (2026-10-20).
  De `basedatos_partidas/` (62 MB en el repo) solo viaja a Vercel lo que la
  app lee en caliente (~27 MB): `.vercelignore` deja fuera salidas de
  generación, auditorías, matrices (el panel las carga por subida), scripts
  y también `tests/`, `docs/` y `tools/`. Los contadores de la landing se
  leen de `datos/cifras_catalogo.json`, precalculado por
  `tools/generar_cifras_catalogo.py`. Verificado por simulación local (con
  todo lo excluido fuera, la app arranca y 290 tests de los lectores pasan)
  porque la CI clona el repo completo y no caza una sobre-exclusión.

**Hecho cuando:** la home y una guía responden con cabecera de caché
compartida y el segundo hit no toca la función; `/readyz` sigue en verde con
el paquete reducido; el panel se nota igual o más rápido (misma región).

## Fase 2 — Precios con pipeline (antes del SEO programático) ✅

*Publicar miles de URLs apoyadas en precios que caducan en silencio sería
construir sobre arena (punto 12).*

Cadencia fijada por el titular: **mensual** (umbral de alarma, 40 días).

- ✅ `precios_actualizados` en `/readyz`: antigüedad por país desde
  `MAX(fecha_actualizacion)` de las referencias nacionales (sin migración
  de esquema); alarma blanda `REVISAR` sin tumbar `ok`.
- ✅ Fecha de consulta derivada de los datos en las guías con tablas
  (España, LatAm y Venezuela vía `app/fechas_texto.py`): nada de fechas
  escritas a fuego — al actualizar `fecha_consulta` en la matriz, la guía
  publica el mes nuevo sola.
- ✅ Proceso único documentado en `docs/ACTUALIZACION_PRECIOS.md`:
  fuente → validar (`verificar_matriz_importable.py`) → cargar → verificar
  CSV↔BD → `/readyz` en «hoy». `tools/verificar_matrices_bd.py` verifica
  ya las 7 matrices en una pasada, con la conversión imperial de EE. UU.
  replicada (prueba de fuego local: 8536 precios, 22 países, sin
  diferencias).

**Hecho cuando:** actualizar precios es ejecutar un comando documentado y
ver el check pasar a «hoy». ✔

## Fase 3 — i18n: mecanismo único (antes de crear superficies nuevas) ✅

*Hay 94 plantillas `*_en.html` (40% del total): cada pantalla cuesta el
doble (punto 8). No se migra todo ahora: se instala el mecanismo para que
nada nuevo nazca duplicado.*

El mecanismo ya existía (`app/i18n.py`, catálogos `app/locales/*.json`,
filtro `t()` y un resolvedor que cae a la plantilla base si no hay
gemela): la fase lo estrena de verdad en plantillas completas.

- ✅ **Piloto:** `auth/forbidden.html`, `baja_completada.html` y
  `licencia_suspendida.html` sirven ES/EN desde una sola plantilla
  (textos trasladados desde sus gemelas al catálogo, sin re-traducir).
  Paridad cubierta por `tests/test_i18n_plantillas.py` (render en
  ambos idiomas, cobertura de claves, sin fuga de claves).
- ✅ **Regla activa y vigilada:** toda plantilla nueva (fases 4 y 5)
  nace única con `t()`; un test trinquete congela las 91 gemelas
  restantes — la lista solo puede encoger. La migración del resto,
  por tandas en PRs que ya toquen esas pantallas (fase 6), sin
  proyecto dedicado.
- **Frontera:** esto es solo la interfaz. Las traducciones del
  catálogo (`basedatos_partidas/datos/recursos_en.json` y compañía,
  hechas una a una) no se tocan.
- **Orden aprendido:** las pantallas que extienden `base.html` migran
  después de la propia base (su gemela extiende `base_en.html`;
  migrarlas antes daría contenido en un idioma dentro del marco del
  otro).

**Hecho cuando:** las pantallas piloto sirven ES/EN desde una sola plantilla
y la suite de idiomas lo cubre. ✔

## Fase 4 — Stripe completo

*Dinero: máximo cuidado, todo con interruptor y convivencia de mundos
(punto 6).*

- **4.1** *Titular:* crear Product/Prices (mensual y anual) en el dashboard
  de Stripe y pasar los IDs como variables de entorno. Sin tocar código.
- **4.2** Checkout con Price IDs detrás de flag. El webhook acepta en
  paralelo las suscripciones actuales (creadas con `price_data`) y las
  nuevas: **los clientes que ya pagan no notan nada** ni se les toca la
  suscripción.
- **4.3** Customer Portal desde «Mi plan»: actualizar tarjeta (hoy imposible:
  es la fuente de churn silencioso cuando una tarjeta caduca), facturas de
  Stripe y cancelación. La cancelación por API ya existente se mantiene para
  las suscripciones heredadas hasta que el portal las cubra a todas.
- **4.4** *Solo si el gestor del titular lo confirma:* factura formal (hoy se
  emite recibo propio). Es una decisión de negocio/fiscal, no técnica.

**Hecho cuando:** un alta nueva paga contra el Price de catálogo, el portal
permite cambiar la tarjeta de una suscripción de prueba en modo test, y las
renovaciones heredadas siguen activando licencias igual que hoy.

## Fase 5 — SEO programático sobre el catálogo

*La palanca de crecimiento (punto 4), deliberadamente después de 1, 2 y 3.*

- **5.1 Piloto:** un país (MX) y un nivel (subcapítulos/partidas con precio
  real del país y descompuesto resumido), enlazado desde las guías
  existentes. Hoy el sitemap son 195 URLs (76 guías, 75 temas × país con
  69–84% de texto compartido) frente a 8.536 referencias de precio en
  22 países sin ninguna URL.
- **Guardia anti-contenido-fino:** no se publica combinación sin dato
  diferencial del país (precio real, no plantilla con el nombre cambiado).
  Canonical, breadcrumbs y schema desde el primer día; sitemap por secciones
  si el volumen lo pide.
- **5.2** Extensión por países/niveles **según indexación real en Search
  Console tras 2–4 semanas del piloto**, no por intuición.

**Hecho cuando (piloto):** las URLs nuevas aparecen indexadas en GSC y el
tráfico orgánico a esas rutas es medible; la extensión se decide con esos
datos.

## Fase 6 — Velocidad de desarrollo (continua, sin fecha de cierre)

- **Paralelizar la suite** (`pytest-xdist`) aislando la BD por worker
  *(punto 10, segunda parte).* Hoy: 12–16 min por CI. Se hace cuando la
  fase 0 ya da señal fiable, para distinguir un fallo real de uno de
  concurrencia.
- **Migración de plantillas `_en` por tandas** (continuación de la fase 3).
- **Monolitos** *(punto 9)*: sin proyecto dedicado. `routers/presupuestos.py`
  (4.543 líneas), `models.py` (4.120) y `seo.py` (2.432) se parten por
  dominio **cuando una funcionalidad los abra por otro motivo**; hacerlo
  como obra aislada es exactamente el cambio que no se nota y sí puede
  romper.

## Lo que NO entra (decidido)

- **Correo (ex punto 11):** `soporte@cotizat.online` es un buzón activo y
  atendido; no hay nada que arreglar. Queda a criterio del titular retirar
  `COTIZAT_AVISOS_EMAIL` para que los avisos internos vayan también directos
  a ese buzón.
- **Reescribir el frontend o migrar de stack:** el SSR actual es el activo
  SEO; no se toca.
- **Micro-optimizaciones** sin medición que las pida.

## Tareas que solo puede hacer el titular (con guía nuestra)

1. Monitor externo de `/readyz` (fase 0.2).
2. Confirmar la región de Supabase (fase 1.1).
3. Comprobar plan y copias (backups/PITR) de Supabase: la base de datos es
   el negocio de los clientes; la ventana de recuperación debe ser una
   decisión consciente, no un default.
4. Crear los Prices en Stripe (fase 4.1) y validar la factura formal con su
   gestor (4.4).
5. Enviar/confirmar el sitemap `https://cotizat.online/sitemap.xml` en
   Search Console y Bing (pendiente anterior; la fase 5.1 se mide desde ahí).
