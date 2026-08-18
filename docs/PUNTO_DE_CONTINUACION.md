# Punto exacto de continuación

Fecha de corte: **18/08/2026, checkout de planes + panel admin premium + gestión de organización, con PR #33 abierto** (America/Caracas).

Este documento retoma el trabajo sin depender del historial del chat. Describe
**dónde quedó exactamente** el trabajo y **qué sigue**, en ese orden. Léelo
junto con `basedatos_partidas/EMPEZAR_AQUI.md` (reglas y progreso del catálogo),
`basedatos_partidas/INVENTARIO.md` (cifras y contraste de precios) y
`PLAN_DE_COMERCIALIZACION_Y_EVOLUCION_SAAS.md` (§1.9 y §11).

---

## ✅ Cierre de sesión — checkout de planes + panel admin premium + gestión de organización (18/08/2026)

Rama fija de la sesión: `arena/01a012cd-generador-comercial`, basada en `main`
(`88d3859`, merge del PR #32). **PR #33 creado hacia `main`:**
https://github.com/gtrespana-bit/generador-comercial/pull/33 (confirmar con
`gh pr view 33`; si ya está fusionado, `main` contiene el código).

El bloque cierra tres frentes comerciales/operativos: **(1)** el cobro manual
del piloto con checkout real dentro de la app, **(2)** un panel de operador
premium y **(3)** la gestión de la organización visible y con permisos.

### 1. Checkout de planes con pago manual (E1-059, cobro manual)

Se descartó el `mailto:` como vía de compra (el cliente quiere *comprar ya*,
no enviar una solicitud). El flujo completo dentro de la app:

- **`GET /pago`** — planes anual (89 US$ / año) y mensual (9,99 US$ / mes),
  lado a lado en escritorio, con botones que llevan al checkout.
- **`GET /pago/comprar?plan=anual|mensual`** (requiere sesión y organización):
  elige método de pago (tarjetas), ve los **datos del titular para pagar**,
  completa los **campos de verificación del método** y adjunta el
  **comprobante** (imagen PNG/JPG/WEBP o PDF, máx 12 MB).
- **`POST /pago/comprar`** — valida, guarda el comprobante en storage privado
  (categoría `comprobantes`, añadida a `_ALLOWED_CATEGORIES` en `app/storage.py`),
  crea la compra `pendiente` y notifica por email a soporte con el comprobante
  adjunto (`enviar_compra_por_email` en `app/services/email.py`, plantillas
  `emails/compra.{html,txt}`).
- **`GET /pago/confirmacion?id=X`** — resumen y estado pendiente.

Métodos y datos (fijos, públicos por diseño) viven en **`app/datos_pago.py`**:

| Método | Datos para pagar |
|---|---|
| Pago móvil | Banco Provincial · 0412-6443099 · V-20794917 |
| Binance | ID 1090042241 |
| Kontigo | +58412-3215016 |
| USDT | TRC-20 · TPFa5x7jsUk4qw8Qfm1R1XXbPPCPRj8ZXy |

Los números de teléfono están declarados como excepción legítima en
`tools/auditar_datos_sensibles.py` (son canales públicos de cobro, no datos
privados). Los importes 89/9,99 mapean al plan en `PLAN_POR_IMPORTE`
(`app/services/panel_admin.py`) y a la duración de licencia `1a`/`1m`
(`app/services/licencias.py`).

**Modelo `CompraPlan`** (`app/models.py`, tabla `compras_plan`): tenant
(pertenece a la organización compradora) con `plan`, `metodo_pago`, `importe`,
`datos_verificacion` (JSON), `comprobante_*`, `estado`
(`pendiente|activa|rechazada`), `licencia_id` y auditoría de revisión.
**RLS**: INSERT tenant (el cliente crea su compra), SELECT tenant **o**
operador, UPDATE solo operador, sin DELETE (historial íntegro).

**Panel `/admin/compras`** (operador): ver comprobante (`GET
/admin/compras/{id}/comprobante`, lee del storage con la referencia guardada
porque el operador no tiene el tenant del comprador), activar (crea la
licencia del plan con `crear_licencia` origen `pago`) o rechazar.

### 2. Panel admin premium (`/admin`)

Sustituye la idea de paneles sueltos por un **hub único** (`/admin`):

- **KPIs**: clientes, con plan, sin plan, por vencer (15 días), compras por
  activar e ingresos.
- **Tabla "Clientes y planes"** ordenable por columna (cliente, plan, compra,
  caducidad, estado, ingresos) y filtrable por texto/email y estado
  (`app/static/js/admin-panel.js`, solo `classList`/`addEventListener`,
  cumple CSP; el filtro oculta filas con clase `oculta` en vez de `.style`).
- **Compras por activar** en línea: ver comprobante → activar / rechazar.
- **Concesión manual** de licencia (prueba/cortesía/compensación/pago) plegable.
- Datos: `resumen_admin()` en `app/services/panel_admin.py` (une
  organizaciones + licencias + compras + emails de membresías).
- Los enlaces antiguos `/admin/licencias`, `/admin/compras` y
  `/admin/operacion` siguen funcionando; el hub enlaza entre ellos.

### 3. Gestión de la organización (perfil de empresa)

- **Nombre de la organización** (el del menú lateral) editable en
  `/configuracion` (tarjeta "Tu organización"); al cambiar se regenera el slug
  con unicidad (`_slug_organizacion_unico` en `app/routers/configuracion.py`).
- **Permisos**: solo `propietario` y `administrador` editan (`puede_gestionar`
  de `app/permisos.py`; en SQLite/escritorio el usuario local es el propietario
  implícito). `miembro` y `lectura` ven la página en **solo lectura**
  (`<fieldset disabled>`) y el POST se rechaza en el servidor.
- **Estado del plan visible para el cliente**:
  - Tarjeta **"Tu plan"** en `/configuracion`: plan, fecha de caducidad y días
    restantes (o enlace a `/pago` si no hay plan).
  - Píldora en el **menú lateral** (`base.html`): "✓ Plan mensual · 14 d" o
    "Sin plan · Ver planes". El resumen se calcula en `get_db` y se expone como
    `request.state.licencia_resumen`.
  - Como la sesión del cliente **no puede leer `licencias`** (RLS de operador),
    se creó la función **SECURITY DEFINER**
    `cotizat_security.organization_license_info(p_organization_id)` (migración
    `f9d4c2a7e5b3`) que solo devuelve la fila de la organización del propio
    claim de sesión (`context_organization_id`). Servicio:
    `resumen_licencia_cliente()` en `app/services/licencias.py`.
- Accesos añadidos: enlace **"Editar empresa"** en el menú lateral, botón
  **"Configurar empresa"** en `/cuenta` y en `/organizaciones` para la activa.

### 4. Landing (retoques de conversión)

- Las tarjetas de precios de la home ahora son **clickeables → `/pago`**.
- El **formulario de demo fue eliminado** (el titular no hace demostraciones):
  los botones "Solicitar demostración" pasaron a "Ver planes". El endpoint
  `POST /demo`, la función `enviar_solicitud_demo_por_email` y las plantillas
  `emails/demo.*` quedan **inactivos pero intactos** (reutilizables).

### Migraciones del bloque (2, ambas YA aplicadas en Supabase por el titular)

1. **`e5f2a8d31b6c`** — tabla `compras_plan` + RLS tenant/operador.
   Script: `docs/staging_upgrade_e5f2a8d31b6c.sql`.
2. **`f9d4c2a7e5b3`** — función `cotizat_security.organization_license_info`.
   Script: `docs/staging_upgrade_f9d4c2a7e5b3.sql`.

Head esperado por el runtime: **`f9d4c2a7e5b3`** (`EXPECTED_ALEMBIC_HEAD` en
`app/database.py`, comprobado por `tests/test_rls.py`).

### Estado y verificación

- **543 tests pasando, 6 omitidos**; 72 plantillas Jinja; `compileall`;
  `node --check`; lock de 42 paquetes; `git diff --check` limpio; auditoría de
  datos sensibles sin hallazgos.
- Smoke test end-to-end: `/pago` → `/pago/comprar` (método + comprobante) →
  confirmación, con almacenamiento local.
- Commits del bloque (en orden): `707f715` (checkout), `3949e2d` (panel admin
  premium), `3ad6d8a` (edición de organización), `80c11e2` (permisos + plan
  visible) y el commit documental del traspaso.

### Pendientes / candidatos siguientes

1. **Fusionar el PR #33 y desplegar `main`** (Vercel). Con las migraciones ya
   aplicadas, `/readyz` debe volver a 200 tras el despliegue.
2. **Ensayar el flujo de compra real en staging** con una organización de
   prueba: comprar → comprobante → email → activar desde `/admin` → el cliente
   ve "Tu plan" con fecha y días.
3. Decisión pendiente del titular: **recibo PDF de la compra** para el cliente
   (existe `recibo_licencia.py` para el panel; falta el equivalente para el
   cliente) y **corte automático** (`COTIZAT_EXIGIR_LICENCIA=true`) — ya está
   implementado el corte, falta la licencia de cortesía al titular y el switch
   en Vercel (ver `docs/PANEL_DE_OPERADOR.md` §6 y `docs/PROCESO_PILOTOS.md`).
4. Catálogo: objetivo amplio de **5.000 partidas** (brecha ~1.994) y cierre de
   los **~196 precios provisionales B2B** (requiere cotización del titular).
5. Decisión del titular sobre **revisar los rendimientos** de mano de obra del
   catálogo (comentó que algunos "están fatal"; no se tocaron).
6. Opcional: video/tour grabado (Loom) cuando el titular lo grabe.

---

## ✅ Cierre de sesión — catálogo 3.006 + landing comercial (17/08/2026)

Rama fija de la sesión: `arena/01a0108b-generador-comercial`, basada en `main`
(`e58a94d`, merge del PR #31). El bloque cierra dos frentes: **(1)** ampliar el
catálogo propio hasta superar el mínimo de 3.000 partidas y **(2)** convertir
la página de inicio en una landing comercial pública y premium.

### 1. Catálogo propio: 540 → 3.006 partidas

- **3.006 partidas**, 18 capítulos, 172 subcapítulos y 256 apartados con
  partidas. **0 subcapítulos sin cobertura** (`planificar_cobertura.py`).
- Ampliación por capítulos con generadores reproducibles en `tools/`:
  capítulos 01–10 y 12 hasta el mínimo; luego 11/13/14 y 15/16/17/18.
- Contraste de precios contra el mercado venezolano (rondas 3, 4 y 5:
  eléctrico, plomería/gas/climatización, soldadura/pinturas/seguridad/agregados).
  Corrección de doble conteo (equipo fuera de `recursos`, queda en
  `producto_cliente`) y de terminología (losa, friso, rodapié…).
- ~196 precios provisionales restantes documentados en
  `basedatos_partidas/INVENTARIO.md` (~148 consumibles de bajo valor +
  ~48 especialidades B2B que requieren cotización de proveedor).
- Refactor previo del bloque: E4-001 (routers por dominio), E4-003 (config por
  entorno), E4-016/E4-017 (inventario de aislamiento y auditoría de archivos);
  árbol de partidas con carga bajo demanda (`/partidas`).
- `CATALOGO_VERSION = 3` en `app/services/catalogo_propio.py` (incorpora las
  partidas nuevas a instalaciones existentes).

### 2. Landing pública (la home ya no es el login)

- `/` es la landing pública; `/inicio` es el panel. Login/registro/onboarding
  redirigen a `/inicio`. Alias `/conocer`.
- Landing premium: **hero dividido** (mensaje + maqueta de presupuesto PDF con
  badges de margen/tiempo); **«Así se ve»** con un *presupuesto real de
  remodelación de baño* (partidas, precios y rendimientos reales del catálogo,
  beneficio por partida/capítulo/total, horas por rol y productos con imagen);
  **«El plus que marca la diferencia»** (margen +35 % y tiempo de obra);
  **tour animado** de 4 pantallas (`app/static/js/landing-tour.js`, solo
  `classList` + `addEventListener`); imágenes de producto en `app/static/img/`.
- Sin mención a CYPE en contenido visible. Cifras del catálogo dinámicas
  (`cifras_catalogo()` en `app/routers/common.py`, global Jinja `catalogo`).
- CSP estricta cumplida: sin `innerHTML`, sin estilos inline, sin handlers
  inline.

### Estado y qué sigue

- Suite: **516 passed, 6 skipped**. `git diff --check` limpio.
- PR **#32** desde `arena/01a0108b-generador-comercial` hacia `main`
  (confirmar con `gh pr view 32`).

Pendientes (sin orden de prioridad):

1. Objetivo amplio de **5.000 partidas** (brecha ~1.994; seguir produciendo
   familias reales por capítulo).
2. Cerrar los **~196 precios provisionales** B2B (requiere cotización del
   titular; no se puede cerrar por web).
3. **Formulario de demo real** en la landing (capturar lead) en vez de `mailto:`.
4. Decisión del titular sobre **revisar los rendimientos** de mano de obra del
   catálogo (comentó que algunos «están fatal»; no se tocaron en este bloque).
5. Opcional: añadir el video/tour grabado (Loom) cuando el titular lo grabe.

---

## ✅ Cierre de sesión — catálogo extenso (16/08/2026)

Rama fija de la sesión: `arena/01a00d6f-generador-comercial`, basada en
`main` (`96d82c1`). El bloque deja terminadas y documentadas estas fases:

1. **Taxonomía numérica v2:** 540 partidas reclasificadas en 18 capítulos,
   172 subcapítulos y 147 apartados; código visible `CC.SS.AA.NNN` y alias
   histórico conservado.
2. **Escalabilidad:** índice ligero, ficha bajo demanda, caché, árbol progresivo,
   búsqueda híbrida y gestión paginada; benchmark reproducible con 5.000
   partidas.
3. **Personalización por organización:** ocultar/restaurar oficiales, eliminar
   personalizadas y recibir altas oficiales incrementales sin reactivar ocultas.
4. **Plan de expansión:** matriz exacta 3.000/5.000 para 172 familias y
   diccionario de sinónimos con 146 grupos y 661 términos en los 18 capítulos.

Migraciones `f8a1b2c3d4e5` y `d6e2f9c4b8a1`: **ejecutadas en Supabase por el
titular**. Head actual esperado por el runtime: **`d6e2f9c4b8a1`**.

Validación de cierre: **483 tests superados y 6 omitidos**, 63 plantillas,
compilación Python, JavaScript, lock de 42 dependencias, auditoría de datos
sensibles, terminología venezolana y benchmark de 5.000 partidas.

**PR #31 abierto hacia `main`:**
https://github.com/gtrespana-bit/generador-comercial/pull/31

Checks del PR verificados en verde tras el último push: **CI, Vercel y Vercel
Preview Comments aprobados**. El PR queda listo para revisión y fusión.

Documentos principales:

- `docs/ESTRATEGIA_CATALOGO_EXTENSO.md`
- `docs/FASE_1_CATALOGO_ESCALABLE.md`
- `docs/FASE_2_VISIBILIDAD_CATALOGO.md`
- `docs/FASE_3_MATRIZ_COBERTURA_Y_SINONIMOS.md`
- `basedatos_partidas/salida/RESUMEN_COBERTURA.md`

**Siguiente trabajo:** producción de familias completas, empezando por
`09 Instalaciones` y luego `12 Revestimientos y acabados`. No requiere rediseñar
la taxonomía ni la infraestructura de catálogo.

---

## ✅ 0. Migración de visibilidad aplicada en Supabase (16/08/2026)

El titular confirmó la ejecución de
`docs/staging_upgrade_d6e2f9c4b8a1.sql`. La base queda en el head
**`d6e2f9c4b8a1`**, que coincide con el exigido por el runtime. La migración
añade identidad estable, marca oficial, visibilidad por organización y versión
de alta a `partidas`; no oculta ni elimina datos durante su ejecución.

---

## ✅ 0a. Taxonomía v2 aplicada en Supabase (16/08/2026)

El titular confirmó la ejecución en Supabase de
`docs/staging_upgrade_f8a1b2c3d4e5.sql`. La base queda en el head
**`f8a1b2c3d4e5`**, sobre `a3d7e9c1b5f2`. Fue el head intermedio anterior a
`d6e2f9c4b8a1`.

La migración añade el árbol de categorías, el vínculo de cada partida a su
apartado, el código anterior y `version_catalogo`. No modifica presupuestos ni
precios. **Las secciones posteriores conservan el histórico del corte anterior y
por eso nombran `a3d7e9c1b5f2` como head.**

---

## ⚠️ 0bis. Recuperación de sesión del 16/08/2026 (léase antes que el resto)

La rama `arena/01a00b99-generador-comercial` se recuperó en una sesión nueva a
partir de un parche de exportación. Estado real verificado en esta sesión:

- **Base:** commit `17e1172` («Add files via upload»), única rama
  `arena/01a00b99-generador-comercial`. No se cambió de rama.
- **Parche aplicado completo con `git apply --index`** (formato `diff --git`,
  sin cabeceras `From`), excluyendo únicamente los artefactos de `handoff/`:
  sus binarios venían como `Binary files differ` sin datos recuperables y la
  carpeta debía eliminarse de todas formas. Todo lo demás (32 rutas de código,
  plantillas, pruebas, docs y migración) aplicó limpio, sin conflictos.
- **Eliminados:** el `.patch` de recuperación de la raíz (estaba trackeado en
  el commit base, por eso figura como borrado) y toda carpeta `handoff/`. No
  queda ningún `.patch` ni `handoff` en el árbol.
- **Estado git actual:** los cambios recuperados están **staged pero SIN
  commit** (33 rutas: 32 de contenido + el borrado del `.patch`). El head de
  la rama sigue siendo `17e1172`; no existen los commits `435a690`, `85e590c`
  ni `33fdf10` en este repositorio, solo su contenido aplicado. Sin PR abierto
  y sin push, por instrucción expresa.
- **Siguiente paso recomendado:** revisar `git status` y, con autorización,
  commitear el estado recuperado en esta misma rama antes de seguir trabajando.

Verificación ejecutada en esta sesión (todo en verde):

- Suite completa: **409 passed, 6 skipped** (las 6 son pruebas PostgreSQL
  omitidas por no existir URL administrativa de pruebas).
- Plantillas Jinja: **59 correctas**. `compileall`: OK. JavaScript
  (`node --check`): OK. `tools/verificar_lock.py`: **42 paquetes coherentes**.
  `git diff --check`: OK. `tools/simular_vercel_rofs.py`: importación correcta.

Estado funcional confirmado: **E3-016 a E3-019 completados** (envío por email,
enlace público revocable, aceptación/rechazo trazable, notificación y estado
controlado). La migración `c2f6e8a1d934` está en
`migrations/versions/c2f6e8a1d934_public_proposal_links.py`; al cierre de esta
sesión **ya fue aplicada y verificada en Supabase** — ver §0ter, que deja sin
efecto el párrafo original de esta sección.

---

## ✅ 0ter. Migraciones del bloque aplicadas en Supabase (16/08/2026)

El titular ejecutó en Supabase SQL Editor los scripts del bloque y **verificó
los dos resultados** esperados:

- **`c2f6e8a1d934` (propuestas):** la tabla `public.enlaces_propuesta` tiene
  exactamente las 4 políticas previstas:

  | polname | polcmd | using_expr | check_expr |
  |---|---|---|---|
  | `cotizat_proposal_insert_tenant` | INSERT | — | `tenant_access(organizacion_id, true)` |
  | `cotizat_proposal_select_public` | SELECT | `token_hash = NULLIF(current_setting('cotizat.proposal_token_hash', true), '')` AND `revoked_at IS NULL` AND `expires_at > clock_timestamp()` | — |
  | `cotizat_proposal_select_tenant` | SELECT | `tenant_access(organizacion_id, false)` | — |
  | `cotizat_proposal_update_tenant` | UPDATE | `tenant_access(organizacion_id, true)` | `tenant_access(organizacion_id, true)` |

- **`a3d7e9c1b5f2` (baja):** la función `cotizat_security.baja_organizacion`
  existe con `security_definer = true` y propietario `postgres` (el usuario
  que aplica la migración), tal como declara el script. ✅ La guarda de
  versión del script exige `c2f6e8a1d934` antes, así que la cadena está
  completa: `b7c4a9e2d31f → c2f6e8a1d934 → a3d7e9c1b5f2`.

**Consecuencia operativa esperada:** hasta que el código de esta rama (que
exige el head `a3d7e9c1b5f2`) se despliegue en el entorno migrado, su
`/readyz` responderá **503** porque la base va por delante del código. No es
un fallo: es la comprobación de head funcionando como está diseñada. Tras el
despliegue, `/readyz` debe volver a 200.

---

## 🚀 0quater. Cierre de bloque con PR del titular (16/08/2026)

**PR #27 creado y ABIERTO** — https://github.com/gtrespana-bit/generador-comercial/pull/27
desde `arena/01a00b99-generador-comercial` hacia `main`, con los 8 commits del
bloque. **Al volver, confirmar el estado** (abierto / fusionado) con:

```bash
gh pr list --head arena/01a00b99-generador-comercial --state all
# o directamente:
gh pr view 27 --json state,statusCheckRollup
```

Commits que contiene el PR (en orden):

1. `9fd5afa` — recuperación de E3-016 a E3-019 (envío, enlaces, respuesta,
   notificación) desde el parche de recuperación.
2. `bd684e1` — E3-020/E3-021: respaldo web verificable y restauración en dos
   pasos.
3. `a0d2711` — E3-022/E3-023: exportación portátil y baja con borrado
   verificado.
4. `7ddb7de` — E3-024: panel `/admin/operacion` y registro de errores.
5. `2bf6d19` — documentación de las migraciones aplicadas en Supabase.
6. `d3eb2a7` — Etapa 4 (primer bloque): autorización centralizada
   (`app/permisos.py`) y logs estructurados (`app/logs.py`).
7. `2de721a` — documentación del traspaso de sesión (este §0quater y §7).
8. `2a0d56d` y el commit de cierre documental posterior — traspaso definitivo
   para el PR #27 con su número y enlace registrados.

Estado verificado de la rama en el momento del PR:

- Suite: **465 passed, 6 skipped**; 63 plantillas; `compileall`; JavaScript;
  lock (42 paquetes); `git diff --check`; simulación de Vercel read-only.
- Migraciones `c2f6e8a1d934` y `a3d7e9c1b5f2` **ya aplicadas y verificadas en
  Supabase** (§0ter): no hay que volver a aplicarlas. Al desplegar este
  código, `/readyz` del entorno migrado vuelve a 200 (hasta entonces, 503
  esperado).
- Sin secretos en el repositorio (la auditoría `tools/auditar_datos_sensibles.py`
  sigue activa en CI).
- **CI:** al crear el PR, el workflow `CI` se ejecuta automáticamente sobre
  él (el disparador `pull_request` hacia `main`; la copia del workflow vive en
  `docs/ci/ci.yml`). Fusionar solo cuando termine en verde.

### Qué hacer justo después del PR (árbol de decisión para la sesión nueva)

**A. Si el PR sigue abierto (o falló CI):**

1. Mirar los checks en GitHub: `gh pr view 27 --json statusCheckRollup`.
2. Si algo falla, corregirlo en esta misma rama (la sesión continúa en
   `arena/01a00b99-generador-comercial`) y empujar; el check se re-ejecuta.
3. No empezar E4-001 con el PR roto: primera prioridad, PR en verde.

**B. Si el PR fue fusionado (escenario normal):**

1. `main` ya contiene todo el trabajo (los 7 commits). Si el HEAD local de la
   sesión nueva aparece retrocedido: `git fetch origin
   arena/01a00b99-generador-comercial && git reset --mixed FETCH_HEAD`
   (o partir de `main` directamente, según cómo abra la sesión nueva).
2. **Desplegar** el código de `main`/rama (Vercel, Production): con las
   migraciones ya aplicadas (§0ter), `/readyz` debe volver a **200**. Si
   respondiera 503, revisar `checks` de `/readyz` antes de nada.
3. **Ensayar en staging el flujo real** con una organización de prueba:
   respaldo → restauración → exportación → `/admin/operacion` (no ejecutar la
   baja sobre datos reales; usar solo la organización de prueba).
4. **Continuar el desarrollo** por la tarea planificada: **E4-001 — dividir
   `app/main.py` en routers por dominio** (detalle en §5, punto 10).

### Recordatorio de entorno para la sesión nueva

- Recrear el entorno: `python -m venv .venv && .venv/bin/pip install -r
  requirements.lock` (el `.venv` no persiste entre sesiones).
- Los secretos (Supabase, Resend, Upstash) nunca se piden ni se tocan desde
  el código; todo lo que depende de ellos es del titular (§6, reglas).

---

## 0. Lo último hecho: PR #25 fusionado en `main`

**Decisión de negocio adoptada en esta sesión (titular, 16/08/2026):**

- **E1-059 → cobro manual para el piloto** (transferencia / Zelle / Binance /
  Pago Móvil, activación a mano). La vía «en serio» queda acordada: autónomo
  en España (036 + RETA) + Stripe cuando haya cobro recurrente. Análisis en
  `docs/COBRO_Y_LICENCIAS.md`.

Con esa decisión se cerraron **E1-060 por completo** y **E1-061**:

1. **Recibo PDF** por licencia de pago (`app/services/recibo_licencia.py`):
   número estable `CT-000NNN`, período inclusive, método/referencia del cobro;
   pie declara **comercial sin validez fiscal** mientras no haya razón social.
   Enlace «recibo PDF» en el panel; cortesías y pruebas no tienen recibo.
2. **Corte automático de acceso**: con `COTIZAT_EXIGIR_LICENCIA=true`
   (**apagado por omisión**), una organización sin licencia vigente recibe la
   pantalla «Acceso suspendido» (`app/templates/licencia_suspendida.html`) en
   cualquier ruta de negocio; los datos no se tocan y vuelven al renovar. En
   PostgreSQL el corte pregunta a `cotizat_security.organization_has_license`
   (SECURITY DEFINER guardada por claim de organización). Escritorio jamás
   exige licencia.
3. **Avisos de vencimiento por correo** (botón del panel, Resend): escribe a
   propietario/administrador activos vía
   `cotizat_security.organization_admin_emails` (guardada por marca de
   operador), anota el envío en la propia licencia y no repite el mismo día.
4. **Bug latente corregido**: la política `cotizat_org_select` solo devolvía
   las organizaciones con membresía propia, así que en producción el panel era
   **ciego a las organizaciones de clientes**. La migración `b7c4a9e2d31f`
   añade la vía de operador a esa política (sin tocar datos de negocio).
5. **E1-061 documentado** en `docs/PROCESO_PILOTOS.md` — guion completo:
   demostración → registro → cobro manual → licencia + recibo → seguimiento
   semanal con avisos → suspensión automática → reactivación. Su §0 lista los
   requisitos previos en el ORDEN correcto.

Migración nueva: **`b7c4a9e2d31f`** (head exigido por `/readyz`; script para
Supabase en `docs/staging_upgrade_b7c4a9e2d31f.sql`, con guarda de versión).
29 pruebas nuevas en `tests/test_licencias_acceso.py`. Suite:
**391 passed, 5 skipped**. `compileall`, plantillas (53), lock (42 paquetes),
simulación de Vercel RO y `git diff --check` en verde. El PR #25 fue
fusionado el 16/08/2026; CI de `main` terminó en verde. Después del despliegue,
el titular confirmó que las licencias funcionan.

La validación externa de usabilidad también quedó cerrada el 16/08/2026:
varias personas probaron el producto, profesionales del ámbito de la
construcción no necesitaron ayuda y varios presupuestos genéricos de baño se
terminaron en aproximadamente 10 minutos. No se localizaron errores. Las
personas sin conocimientos de construcción tardaron más de 20 minutos, dato
coherente con el nicho profesional definido y no un fallo del recorrido.

### Decisiones de alcance posteriores del titular (16/08/2026)

1. **Etapa 1 se considera completada.**
2. Las partidas actuales son **propias, de ejemplo y solo para pruebas**. Se
   eliminarán cuando se carguen las partidas reales revisadas; catálogo y
   partidas comerciales quedan fuera del trabajo actual.
3. La **validación comercial pagada se aplaza hasta el final**. El titular no
   entregará a clientes un generador que todavía considere incompleto. No se
   abrirán pilotos durante los siguientes bloques técnicos.
4. La etapa activa pasa a ser el **cierre funcional y operativo web**. El
   siguiente bloque recomendado completa entrega y aceptación del presupuesto.

### Trabajo acumulado en la rama actual (sin PR por decisión del titular)

- **E3-016:** envío del presupuesto por email con PDF adjunto y congelado.
- **E3-017:** enlace público seguro, temporal y revocable a una propuesta.
- **E3-018:** aceptación/rechazo único y trazable de la versión exacta.
- **E3-019:** aviso inmediato a administradores y cambio de estado solo para la
  última versión, con constancia y reintento si falla Resend.
- Head nuevo de la rama: **`c2f6e8a1d934`**. Producción continúa correctamente
  en `b7c4a9e2d31f`; no aplicar `docs/staging_upgrade_c2f6e8a1d934.sql` ni
  desplegar el código hasta terminar el bloque y recibir autorización expresa.
- Suite: **409 passed, 6 skipped**; 59 plantillas, `compileall`, JavaScript,
  lock y `git diff --check` en verde.

### Pasos operativos pendientes DEL BLOQUE DE LICENCIAS (histórico)

1. ~~Fusionar el PR #25 y desplegar `main`.~~ **Hecho el 16/08/2026**; CI en
   verde y funcionalidad de licencias confirmada por el titular.
2. ~~Aplicar `docs/staging_upgrade_b7c4a9e2d31f.sql` en Supabase~~ **Hecho el
   16/08/2026 (noche)**: funciones creadas con propietario `postgres` y
   `security_definer=true` (verificado en `pg_proc`).
3. **Conceder licencia de cortesía a la propia organización del titular**
   desde el panel (nota «uso del titular»). Hacerlo ANTES del paso 4.
4. Cuando empiece el piloto de pago: `COTIZAT_EXIGIR_LICENCIA=true` en Vercel
   (Production) + redeploy. El panel deja de mostrar el aviso ámbar.
   Verificación previa sin tocar producción (SQL Editor):
   `BEGIN; SELECT set_config('cotizat.organization_id', '<id>', true); SELECT cotizat_security.organization_has_license(<id>); ROLLBACK;`
   → FALSE sin licencia, TRUE tras concederla. La matriz completa de qué puede
   hacer cada estado está en `docs/PANEL_DE_OPERADOR.md` §6.
5. Verificación en producción del fix de visibilidad: con un **segundo correo
   de cliente** registrado (organización sin membresía del titular), comprobar
   que ahora SÍ aparece en `/admin/licencias`.

---

## 1. Histórico de la sesión anterior (rama `arena/01a00825`, PR #24 fusionado)

- PR #23 (merge `52d1a09`): E1-021 (auditoría de datos sensibles — repos privado
  y sin credenciales), fix de invitaciones sin cuenta previa (descubiertas por
  email verificado desde `/organizaciones`), y E1-060 primera parte.
- PR #24 (merge `4e7eeeb`): docs `.env.example` + script SQL de la migración
  `f4c1d8e37a95` (panel de operador `/admin/licencias`: ver, conceder,
  renovar, regalar prueba/cortesía, compensar, cancelar con constancia;
  tabla no-tenant con RLS de operador; operadores en `COTIZAT_OPERADORES`).
- E1-060 primera parte **desplegado y verificado en producción** (16/08/2026,
  tarde): migración aplicada, `COTIZAT_OPERADORES` en Vercel, panel confirmado
  por el titular. **Decisión suya:** el panel se queda deliberadamente simple;
  la mejora de interfaz es pendiente futuro, no bloqueante.
- Contenido comercial cerrado: E1-053 (`/legal/preguntas`), E1-054 y E1-055
  (`/legal/soporte`), E1-052 (PDF de presupuesto de muestra en `/conocer`).
- Suite al cierre de esa sesión: 362 passed, 5 skipped.

## 2. Incidencia de Auth (registro + recuperación) — cerrada

Resuelta en operativo el 15-16/08/2026: SMTP personalizado con Resend, Redirect
URLs de Supabase completadas (`/acceso` añadido, **confirmado por el titular en
la sesión del 16/08 noche**) y rate limit de emails a 30/hora (**también
confirmado**). El log `Supabase Auth <método> <path> -> HTTP <código>` queda en
el servidor por si algo volviera a fallar (Vercel → Logs).

## 3. Pendientes operativos del usuario (sin código)

> Guía paso a paso: `docs/PENDIENTES_OPERATIVOS.md`. Ninguno bloquea el
> desarrollo. **Estado actualizado al 16/08/2026 (noche):**

1. ~~Redirect URL `/acceso` + rate limit ~30/hora + cooldown 60 s.~~ **Hecho**,
   confirmado por el titular el 16/08.
2. Crear `soporte@cotizat.online`. **Aplazado por decisión del titular: lo
   creará cuando haga falta de verdad** (los avisos de vencimiento ya
   instruyen escribir a esa dirección; conviene tenerlo antes del piloto).
3. Razón social → `COTIZAT_LEGAL_ENTITY` en Vercel. **Aplazado**: se hará
   cuando estemos a punto de lanzar (el recibo y los legales muestran el
   marcador honesto mientras tanto, a propósito).
4. Vercel Hobby prohíbe uso comercial → **Pro (20 $/mes)** antes de cobrar al
   primer cliente. **Aplazado**: sin cobros todavía, no corre prisa.
5. ~~Repetir la prueba E2E «invitación sin cuenta previa» en producción.~~
   **Hecha el 16/08/2026 (noche)**: funciona.

## 4. Aparcado por decisión del usuario

**Puntos 13-manual y 14 de la matriz de aceptación** — no pedirlos hasta que el
desarrollo esté cerrado (guía en `docs/MATRIZ_PASOS_MANUALES.md`). Landing y
legales: v1 aceptada con mejoras pendientes declaradas; iteración pendiente, no
bloqueante. Interfaz mejorada del panel de operador: pendiente futuro.

## 5. Qué es lo siguiente

1. ~~**E3-016 — Envío por email del presupuesto.**~~ **Completado en la rama
   de trabajo el 16/08/2026**: formulario precargado, PDF adjunto por Resend,
   `Reply-To`, estado solo tras confirmación, versión inmutable, PDF exacto
   privado y constancia interna. Suite: 397 passed, 5 skipped.
2. ~~**E3-017 — Enlace público seguro y revocable.**~~ **Completado en la
   rama el 16/08/2026**: versión/PDF congelados, secreto solo en SHA-256,
   caducidad, revocación, página pública mínima y RLS por hash. Migración
   `c2f6e8a1d934` **aplicada y verificada por el titular en Supabase el
   16/08/2026** (las 4 políticas de `enlaces_propuesta` coinciden con el
   script). Suite: 403 passed, 6 skipped.
3. ~~**E3-018 — Aceptación o rechazo trazable.**~~ **Completado en la rama el
   16/08/2026**: una respuesta por enlace, versión exacta, identidad declarada,
   comentario y fecha/hora; función PostgreSQL limitada. Suite: 405 passed,
   6 skipped.
4. ~~**E3-019 — Notificación y estado controlado.**~~ **Completado localmente
   el 16/08/2026**: aviso a propietarios/administradores, cambio solo si es la
   última versión y reintento sin perder la respuesta. Suite: 409 passed,
   6 skipped.
5. ~~**E3-020 — Copia de seguridad web completa y verificable.**~~
   **Completado en la rama el 16/08/2026**: paquete `cotizat-backup` v1
   descargable por propietario/administrador en ambos backends, con manifest,
   omisiones declaradas y cada archivo bajo su SHA-256.
6. ~~**E3-021 — Restauración controlada en dos pasos.**~~ **Completado en la
   rama el 16/08/2026**: re-subida del MISMO archivo (SHA-256) + confirmación
   explícita, verificación íntegra antes de escribir, fusión idempotente sin
   borrar ni duplicar, archivos re-escritos al almacén privado con
   reutilización por huella y trazabilidad de propuestas conservada como
   notas. Sin migración nueva. Suite del bloque: **423 passed, 6 skipped**
   (14 pruebas nuevas en `tests/test_respaldo_restauracion.py`).
7. ~~**E3-022 — Exportación portátil.**~~ **Completado en la rama el
   16/08/2026**: `cotizat-export` v1 con CSV por tabla, archivos con nombre
   original y respaldo verificable embebido; solo propietario/administrador.
8. ~~**E3-023 — Baja con borrado verificado.**~~ **Completado en la rama el
   16/08/2026**: solo el propietario, nombre exacto escrito + casilla,
   archivos borrados antes de la base, borrado transaccional completo y
   aislado por organización; función `cotizat_security.baja_organizacion` en
   PostgreSQL. Migración **`a3d7e9c1b5f2`** (head exigido) **aplicada y
   verificada por el titular en Supabase el 16/08/2026** (`baja_organizacion`
   SECURITY DEFINER con propietario `postgres`). Suite del bloque:
   **441 passed, 6 skipped**
   (18 pruebas nuevas). Detalles en
   `docs/EXPORTACION_Y_BAJA_ORGANIZACION.md` y
   `docs/RESPALDO_Y_RESTAURACION_WEB.md`.
9. ~~**E3-024 — Monitorización y diagnóstico.**~~ **Completado en la rama el
   16/08/2026**: panel `/admin/operacion` solo para operador con los chequeos
   de `/readyz`, hechos operativos y registro acotado en memoria de errores no
   capturados (sin query strings ni tokens); middleware que captura y relanza
   sin cambiar la semántica HTTP. Sin migración nueva. Suite del bloque:
   **453 passed, 6 skipped** (12 pruebas nuevas en `tests/test_operacion.py`).
   Detalle en `docs/MONITORIZACION_Y_DIAGNOSTICO.md`.

**Con E3-024 queda completo el cierre funcional y operativo de la Etapa 3**
(E3-016 a E3-024) en la rama, y **las dos migraciones del bloque están
aplicadas y verificadas en Supabase** (ver §0ter). Siguiente según la puerta
de salida del plan: **desplegar el código de la rama** (hasta entonces
`/readyz` responderá 503 en el entorno migrado porque la base va por delante
del código), ensayar el flujo real en staging, y después el **endurecimiento
técnico de la Etapa 4**. Catálogo comercial y validación pagada permanecen
aplazados hasta que el titular declare completo el producto.

10. ~~**Etapa 4, primer bloque — autorización centralizada y logs
    estructurados.**~~ **Completado en la rama el 16/08/2026**:
    `app/permisos.py` (E4-002/E4-009) concentra los conjuntos de roles y sus
    predicados; los checks inline de las rutas migraron a los predicados y
    una prueba estática impide su regreso; `app/logs.py` (E4-022) añade modo
    JSON opt-in (`COTIZAT_LOG_JSON`) con redacción de credenciales en
    mensajes y trazas. Suite: **465 passed, 6 skipped** (12 pruebas nuevas en
    `tests/test_permisos.py` y `tests/test_logs.py`). Siguiente de la Etapa
    4: **E4-001 — dividir `app/main.py` en routers por dominio** (el plan
    marca la sección 4.1 como el trabajo estructural pendiente más grande).

## 6. Reglas invariables (no negociables)

- **no abrir ni pedir fusionar un PR durante un bloque de trabajo activo**: al
  fusionarlo, el titular debe cerrar el chat y se pierde el acceso de esta
  sesión a la rama; los PR solo se crean cuando sean absolutamente necesarios,
  al terminar un bloque funcional completo y con autorización expresa del
  titular. (Cumplido en esta sesión: el PR del bloque fue creado por el
  titular al cierre — ver §0quater — y la regla sigue rigiendo para el
  siguiente bloque.)
- nunca configurar `MIGRATION_DATABASE_URL` en runtime;
- nunca usar una conexión `postgres`/administrativa como `DATABASE_URL`;
- nunca poner `service_role`/`sb_secret_` en variables públicas del frontend;
- nunca fijar `COTIZAT_REQUIRE_RLS_ROLE=false` como solución de despliegue;
- no activar `COTIZAT_EXIGIR_LICENCIA=true` sin haber concedido antes la
  licencia de cortesía a la organización del titular;
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

## 7. Mensaje para iniciar la conversación nueva

Copiar tal cual, sin añadir secretos ni tokens:

---

Continúa el proyecto CotizaT. Antes de proponer nada, lee
`docs/PUNTO_DE_CONTINUACION.md` (sección «Cierre de sesión — checkout de
planes + panel admin premium + gestión de organización» primero) y
`basedatos_partidas/EMPEZAR_AQUI.md`. No repitas trabajo ya hecho y no me
pidas secretos.

**Dónde quedó todo (18/08/2026, cierre con PR del titular).**

- Rama `arena/01a012cd-generador-comercial`, basada en `main` (`88d3859`,
  merge del PR #32). **PR #33 creado hacia `main`:**
  https://github.com/gtrespana-bit/generador-comercial/pull/33 (confirmar
  estado con `gh pr view 33`; si ya está fusionado, `main` contiene el código).
- Contenido del bloque: **checkout de planes con pago manual** (`/pago`,
  `/pago/comprar` con método + comprobante, `/pago/confirmacion`; Pago móvil,
  Binance, Kontigo, USDT en `app/datos_pago.py`), **panel admin premium**
  (`/admin` con KPIs, tabla ordenable/filtrable de clientes y planes,
  activación de compras), **gestión de organización** (nombre editable, solo
  propietario/admin editan, tarjeta "Tu plan" y píldora en el menú lateral con
  fecha de caducidad y días restantes) y **landing sin demo** con tarjetas de
  precio clickeables.
- Migraciones **`e5f2a8d31b6c`** (compras_plan) y **`f9d4c2a7e5b3`**
  (organization_license_info) **ya aplicadas en Supabase** por el titular.
  Head esperado: `f9d4c2a7e5b3`.
- Suite: **543 passed, 6 skipped**; 72 plantillas; `git diff --check` limpio.
- Al empezar: realinea si el HEAD aparece retrocedido
  (`git fetch origin arena/01a012cd-generador-comercial && git reset --hard
  FETCH_HEAD`) y recrea `.venv` (`python3 -m venv .venv && .venv/bin/pip
  install -q -r requirements-dev.txt`).
- Siguientes candidatos: fusionar/desplegar el PR #33 y ensayar el flujo de
  compra en staging; **recibo PDF de la compra para el cliente** y activar
  `COTIZAT_EXIGIR_LICENCIA` cuando toque; catálogo a **5.000 partidas**;
  cerrar **~196 precios provisionales B2B** (requiere cotización); decisión
  sobre **rendimientos** del catálogo.
- No repetir: el checkout, el panel admin, la edición de organización y la
  tarjeta de plan ya están hechos; **no volver a poner formulario de demo** en
  la landing; no inventar precios ni rendimientos; no nombrar a CYPE en
  contenido visible.

---
