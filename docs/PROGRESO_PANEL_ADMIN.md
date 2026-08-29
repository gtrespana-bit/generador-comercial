# Panel profesional — estado exacto

**Fecha:** 2026-08-30 (última capa: Fase 5 · arquitectura del panel, §3bis)
**Rama de trabajo:** `arena/01a04f52-generador-comercial`
**Commit de partida:** `bc8a8ca` — "Fase 3/4 panel web: CMS, avisos, releases, flags, CRM, vistas, API keys y salud"
**Head Alembic esperado por runtime:** `d3e5f7a9c2b4` — la Fase 5 **no añade migración**: reorganiza pantallas, rutas y contexto; no toca el esquema

---

## 1. Resumen ejecutivo

| Área | Estado |
|---|---|
| Fase 1 (roles, auditoría, ⌘K, notificaciones, métricas) | ✅ Completa |
| Fase 2 (ficha cliente, cobros, renovaciones, automatizaciones núcleo, CSV) | ✅ Completa |
| Fase 3 (web como producto: CMS, SEO, avisos, releases, flags) | ✅ Completa |
| Fase 4 (CRM, vistas, API keys, salud de datos, informe) | 🟡 Núcleo implementado; 4–6 ítems pendientes |
| Fase 5 (arquitectura del panel: seis áreas, pestañas, filtros server-side, acciones en la lista) | ✅ Completa — ver §3bis |

- **Suite completa tras la Fase 5:** **1223 passed, 9 skipped** (`.venv/bin/python -m pytest -q -p no:randomly`, 284 s; 2 avisos preexistentes: `SAWarning` en `catalogo_propio` y `DeprecationWarning` de `TestClient` en `test_seo`).
- Desglose: 1154 de la capa anterior + 69 nuevas en `tests/test_panel_arquitectura.py`. Los cuatro archivos que probaban la navegación antigua (`test_licencias.py`, `test_licencias_acceso.py`, `test_operacion.py`, `test_panel_emails.py`) se reescribieron al contrato nuevo, no se relajaron.
- Sin cambios de esquema ni de permisos: `get_operator_db`, el RLS de operador y la CSP (`nonce`, sin atributos `on*`) quedan intactos; hay pruebas que lo siguen exigiendo (`tests/test_web_security.py`, `tests/test_panel_aislamiento*.py`).
- **SQL manual** `docs/staging_upgrade_d3e5f7a9c2b4.sql` → **ya fue ejecutado por el usuario en Supabase** (confirmado).
- **Cambios empujados** a la rama `arena/01a04bd3-generador-comercial`.

---

## 2. Cadena de migración y esquema actual

- Runtime espera: `EXPECTED_ALEMBIC_HEAD = "d3e5f7a9c2b4"` en `app/database.py`.
- Revisión nueva: `migrations/versions/d3e5f7a9c2b4_web_admin_crm_y_salud.py`
  - `down_revision = "c2d4e6f8a1b3"` (Fase 2).
- Tablas creadas (del **titular / operador**, no tenant):
  - `contenido_web` — borrador/publicado por clave.
  - `avisos_web` — banners/avisos con ventana de fechas.
  - `releases` — changelog.
  - `feature_flags` — interruptores de funcionalidad.
  - `vistas_guardadas` — filtros/columnas persistentes por módulo.
  - `crm_clientes` — estado comercial + próximo contacto por organización.
  - `api_keys_operador` — solo `clave_hash` SHA-256, nunca token plano.

### Seguridad del esquema
- `RLS`: `ENABLE + FORCE ROW LEVEL SECURITY` en todas las tablas nuevas.
- `contenido_web`, `avisos_web`, `releases`: SELECT público solo de `publicado/activo`; escrituras solo operador.
- `feature_flags`, `vistas_guardadas`, `crm_clientes`, `api_keys_operador`: solo operador.
- Ninguna tabla nueva tiene `DELETE`.
- Las API keys guardan **hash**; el token en claro se muestra una sola vez al crearse.

---

## 3. Lo implementado en Fases 1–4

### Fase 1 (✅)
- Roles de operador (`OperadorProducto`, `/admin/equipo`).
- Auditoría del admin (`EventoAdmin`, `/admin/auditoria`).
- Buscador global / ⌘K.
- Centro de notificaciones.
- Métricas financieras en dashboard (MRR/ARR, renovaciones, LTV, tasa de pago, ticket medio).

### Fase 2 (✅)
- Ficha de cliente/empresa con resumen, miembros, facturas/pagos, historial licencias, notas internas, actividad.
- Centro de cobros mensual con CSV y reenvío individual de recibo.
- Panel de renovaciones con campaña de avisos.
- Automatizaciones núcleo visibles/ejecutables (avisos 15d, recordatorios 5/1d, mantenimiento, alertas sin plan).
- Filtros + exportación CSV. Vistas guardadas persistentes se completaron en Fase 4.
- **Fix aplicado a `admin_cobros_cliente`**: el SQL ya **no usa `facturas.total`** (no existe); calcula el total desde `factura_items` (subtotal × (1 − descuento) × (1 + impuesto)). Este fix fue aplicado por el usuario y no debe reintentarse con `f.total`.

### Fase 3 (✅)
- `/admin/web`: CMS de landing/SEO con guardar borrador, publicar y descartar.
- `/admin/avisos`: banners públicos con tipo/nivel/título/mensaje/ventana/activo.
- `/admin/releases`: changelog con publicar/ocultar y destacado.
- `/admin/flags`: feature flags.
- `/novedades`: página pública que muestra solo releases publicadas.
- `landing.html`: muestra el primer aviso activo y lee contenido gobernado desde la DB.
- Modelos/servicio:
  - `ContenidoWeb`, `AvisoWeb`, `ReleaseWeb`, `FeatureFlag` en `app/models.py`.
  - `app/services/web_admin.py` (gestión + lectura pública).
  - `app/services/web_publica.py`.

### Fase 4 (🟡 núcleo)
- `/admin/crm`: canal/CRM ligero (B4).
- `/admin/vistas`: gestión de vistas guardadas persistentes (A5 completo en almacén + pantalla).
- `/admin/salud-datos`: vista de salud de catálogo + resumen de configuración (D2, parcial).
- `/admin/api-keys`: creación/revocación de API keys de operador (A6, parcial: falta 2FA).
- Modelos/servicio: `CrmCliente`, `VistaGuardada`, `ApiKeyOperador`.

---

## 3bis. Fase 5 · arquitectura del panel (30/08/2026)

No añade funciones: cambia **dónde vive cada pantalla y desde dónde se actúa**.
El panel era una lista de ~17 rutas planas con siete tablas de las mismas
organizaciones; ahora son seis áreas con pestañas, filtros en el servidor y
acciones en la propia fila. Documento para el operador: `docs/PANEL_DE_OPERADOR.md` §11.

**Mapa único de verdad** — `app/panel_arquitectura.py`:

- `SECCIONES` (6): id, nombre, ruta, descripción, icono SVG, `atajo` de teclado
  y sus `Pestana` (cada una con `vista_modulo` si admite vistas guardadas).
- De ahí salen el menú lateral, la barra de pestañas, el migado de pan, los
  contadores de los badges, el `?tab=` válido de cada ruta (`pestanas_de_ruta`),
  la lista blanca de destinos de `volver` (`es_destino_panel`) y las
  redirecciones de las 16 rutas fusionadas (`RUTAS_ANTIGUAS` → 302 conservando
  la query). **Ninguna plantilla repite navegación ni título: se lee del mapa.**
- `VISTAS_EN_PANEL` conecta cada módulo de vistas guardadas con el área y la
  pestaña que lo muestra; `FICHA_PESTANAS` hace lo propio con las cinco
  pestañas de la ficha de cliente (independientes del área).

**Rutas** — `app/routers/admin_paginas.py` (nuevo): **11 GET** —siete pantallas
(`hoy`, `clientes`, `cliente_detalle`, `ingresos`, `web`, `sistema`, `analitica`)
y cuatro CSV (`clientes.csv`, `ingresos.csv?tab=`, y las históricas
`renovaciones.csv`/`cobros.csv`)—, más las redirecciones 302 de las 16 rutas
fusionadas, **registradas en bucle desde `RUTAS_ANTIGUAS`** (no son 16
funciones copiadas). `app/routers/admin.py` se queda solo con
acciones POST, la API de ⌘K/campana y los endpoints del cron, y perdió ~330
líneas de plantillas duplicadas. `contexto_sistema()` es compartido por las
acciones que vuelven a pintar Sistema (p. ej. crear una API key muestra el token
una sola vez).

**Contexto de lista** — `app/services/panel_contextos.py`: `url_panel`,
`filtrar_filas`, `ordenar_filas`, `chips`, `enlace_filtro`, `enlace_orden`
(devuelve un dict, nunca HTML), `vistas_en_barra`, `filtros_json`,
`contadores_panel` (dos consultas), `periodo_mes`, `vecinos_del_mes` y las
tablas de etiquetas (`ESTADOS_ACCESO`, `FILTROS_PLAN`, `TIPOS_COBRO`,
`RENOVACION_ESTADOS`, `ALCANCES_ROL`, `DESCRIPCIONES_CRM`, `NOTAS_CHEQUEOS`).
Contrato deliberate: **el router aporta datos crudos + `vistas`/`url_filtros`/
`dict_filtros`/`periodo`/`opciones_*`; cada parcial fija sus `vista_*`** para no
escribir dos veces el mismo bloque.

**Plantillas** — `app/templates/admin/`: ocho pantallas (`dashboard`,
`clientes`, `cliente_detalle`, `ingresos`, `web`, `sistema`, `analitica` +
`base_admin`) y veinte parciales en `partes/`, incluidos con
`"admin/partes/<área>_" + pestana + ".html"`. Se borraron las 16 plantillas
huérfanas. El `<style>` del base envuelve el bloque `extra_css` de los hijos
(los hijos meten CSS crudo, no `<style>`), y `extra_js` es un bloque suelto: el
hijo escribe el `<script nonce src>` completo. Toda clase usada tiene que existir
en `base_admin.html`, que es el único CSS del panel.

**JavaScript** — un solo script global, `app/static/js/admin-kit.js`: ⌘K,
campana, `/` (abre el buscador), `g`+letra (lee `data-atajo` del nav, que viene
del mapa), `data-confirmar` (portado desde `admin-panel.js`, borrado) y
`data-hint`. `admin-correos.js` cubre el destino de prueba de la pestaña de
correos. Sin `innerHTML`, sin `.style.` y sin atributos `on*` (CSP con `nonce`).

**Funciones que estaban huérfanas y ahora se ven/editan desde la lista**:
editar avisos (`POST /admin/avisos/{id}/editar`) y versiones
(`POST /admin/releases/{id}/editar`) —nuevos servicios `actualizar_release` y
`borrar_crm` en `app/services/web_admin.py`—; quitar el estado comercial desde
la propia pestaña; flags y API keys en Sistema › Accesos; vistas guardadas en la
barra de cada lista. Los enlaces que fabricaban `panel_busqueda.py` y
`panel_notificaciones.py` se reescribieron a las rutas nuevas (apuntaban a
páginas fusionadas o a parámetros que nadie leía).

**Auditoría** — `app/services/audit_admin.py` añade `RESULTADOS_AUDITORIA`, la
acción `web.release_editada` y el filtro `resultado` (ver solo lo que falló);
`ACCIONES_LECIBLES` es el mapa acción → etiqueta y una prueba en
`tests/test_panel_arquitectura.py` recorre los routers exigiendo que toda
`accion="…"` emitida tenga etiqueta.

**Pruebas** — `tests/test_panel_arquitectura.py` (69): mapa y límites del menú,
los 16 302 con sus parámetros, render de las 16 pestañas y de las 5 de la ficha,
filtros/orden/vistas/CSV server-side, acciones que vuelven a su pestaña y
auditan, `volver` validado contra redirecciones abiertas, token de API key
legible una sola vez y revocable, etiquetas de auditoría completas y que ningún
enlace generado por los servicios cae en una pantalla muerta. Se reescribieron
además los contratos obsoletos de `tests/test_licencias.py`,
`tests/test_licencias_acceso.py`, `tests/test_operacion.py` y
`tests/test_panel_emails.py` (el hub ya no es la tabla de clientes; `/admin/operacion`
y `/admin/emails` son redirecciones).

---

## 4. Qué queda pendiente (ordenado por prioridad)

1. **Vistas guardadas conectadas a las páginas** (A5 real) — ✅ **cerrado el 30/08/2026**
   - Ya existe `vistas_guardadas`; `/admin/vistas` desapareció como página.
   - Cada lista que admite vistas (Clientes › directorio, Ingresos › cobros,
     compras, renovaciones y contratos, Sistema › automatizaciones) las muestra
     como chips en su propia barra, con «guardar la vista actual» y «borrar»
     ahí mismo; `?vista=ID` reconstruye los filtros en el servidor.
   - Queda pendiente, si algún día hace falta: guardar **columnas** (la tabla
     `vistas_guardadas` ya tiene la columna `columnas`; la barra solo persiste
     filtros).

2. **Reenvío masivo de facturas** (B2)
   - Solo hay reenvío individual.
   - Requiere: función `SECURITY DEFINER` para leer facturas del tenant sin exponer contenido, pantalla de selección y cola de envío.

3. **Reglas visuales completas de automatizaciones** (B5)
   - Núcleo de ejecución y vista actual existentes.
   - Faltan: programación adicional, historial de ejecuciones, estados por regla, confirmaciones de impacto.

4. **Salud de datos en producción (D2 real)**
   - La página funciona, pero en PostgreSQL el operador no puede leer `partidas` de clientes por RLS.
   - Se necesitan funciones agregadas `SECURITY DEFINER` que devuelvan **métricas** (no contenido) por organización.

5. **Operaciones avanzadas + informe ejecutivo** (D4 / informe)
   - Estado de Stripe/Resend/Supabase/Storage, colas, resultado de cron/purga.
   - Informe mensual PDF/CSV: ingresos, clientes, conversión, churn, salud.

6. **2FA de operadores** (A6)
   - API keys listas; falta doble factor para operadores.

---

## 5. Archivos clave de esta iteración

| Archivo | Qué es |
|---|---|
| `migrations/versions/d3e5f7a9c2b4_web_admin_crm_y_salud.py` | Migración Fase 3/4 (nuevo head). |
| `docs/staging_upgrade_d3e5f7a9c2b4.sql` | SQL idempotente para Supabase, ya ejecutado. |
| `app/database.py` | `EXPECTED_ALEMBIC_HEAD = d3e5f7a9c2b4`. |
| `app/models.py` | Modelos `ContenidoWeb`, `AvisoWeb`, `ReleaseWeb`, `FeatureFlag`, `VistaGuardada`, `CrmCliente`, `ApiKeyOperador`. |
| `app/services/web_admin.py` | Servicios de CMS, avisos, releases, flags, CRM, vistas, API keys. |
| `app/services/web_publica.py` | Lectura pública (solo publicado/activo). |
| `app/panel_arquitectura.py` | **Mapa del panel**: secciones, pestañas, iconos, atajos, rutas antiguas → pestaña, destinos válidos de `volver`. |
| `app/routers/admin_paginas.py` | Las 11 GET del panel (7 pantallas + 4 CSV) y las 16 redirecciones 302. |
| `app/services/panel_contextos.py` | Filtros, orden, vistas y contadores compartidos por las listas del panel. |
| `app/routers/admin.py` | **Solo acciones**: `/admin/web`, `/admin/avisos`, `/admin/releases`, `/admin/flags`, `/admin/crm`, `/admin/vistas`, `/admin/api-keys`, ⌘K, campana y crons. |
| `app/static/js/admin-kit.js` | Único script global del panel: ⌘K, campana, `/`, `g`+letra, `data-confirmar`. |
| `tests/test_panel_arquitectura.py` | Contrato de la Fase 5 (69 pruebas). |
| `app/routers/publico.py` | `/novedades` + lectura de contenido web en landing. |
| `app/templates/admin/*.html` | Pantallas nuevas del panel. |
| `app/templates/novedades.html` | Changelog público. |
| `tests/test_panel_pro_fase34.py` | Pruebas de servicios y rutas Fase 3/4. |
| `PANEL_ADMIN_NIVEL_PRO.md` | Roadmap actualizado con estados por fase. |

---

## 6. Cómo verificar

### Suite local
```bash
.venv/bin/python -m pytest -q
```

### Verificación de head
```bash
grep -n "EXPECTED_ALEMBIC_HEAD" app/database.py
```

### Generar SQL Postgres de la migración (revisión)
```bash
DATABASE_URL='postgresql+psycopg://u:p@localhost/db' \
  .venv/bin/python -m alembic upgrade c2d4e6f8a1b3:d3e5f7a9c2b4 --sql
```

### En Supabase
- SQL aplicado: `docs/staging_upgrade_d3e5f7a9c2b4.sql`.
- Esperado en `public.alembic_version`: `d3e5f7a9c2b4`.
- Los tests `test_database_config.py::test_head_actual_tiene_sql_de_aplicacion_manual_en_supabase` validan que este archivo exista y marque la revisión.

---

## 7. Notas / límites conocidos

- **No se ha verificado con un PostgreSQL Supabase real en esta sesión**: el SQL manual sí fue ejecutado por el usuario, pero no ejecutamos una prueba de integración `test_rls_postgres.py` contra ese entorno aquí. La suite `test_rls_postgres.py` existe y se salta sin `DATABASE_URL` de Postgres.
- **La parte de RLS está probada por análisis de SQL y por tests unitarios**, no por una base Postgres real en CI local.
- **Salud de datos (`/admin/salud-datos`)** en PostgreSQL mostrará datos limitados/cero mientras no haya funciones `SECURITY DEFINER` por organización; es el ítem 4 pendiente.
- **No se ha abierto el multi-tenant**: el operador nunca lee contenido de presupuestos de clientes; el CRM/vistas/API keys son estado del titular sobre organizaciones.
