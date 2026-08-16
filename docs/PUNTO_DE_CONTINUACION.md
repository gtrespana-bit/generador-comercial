# Punto exacto de continuación

Fecha de corte: **16/08/2026, noche (Etapa 1 cerrada; validación comercial aplazada)** (America/Caracas).

Este documento retoma el trabajo sin depender del historial del chat. Describe
**dónde quedó exactamente** el trabajo y **qué sigue**, en ese orden. Léelo
junto con `docs/CONTINUIDAD_STAGING_SUPABASE.md` (estado de staging/matriz) y
`PLAN_DE_COMERCIALIZACION_Y_EVOLUCION_SAAS.md` (§1.9 y §11).

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
`migrations/versions/c2f6e8a1d934_public_proposal_links.py` y **sigue sin
aplicar** (no aplicar ni tocar Supabase hasta autorización de despliegue).

---

## ✅ 0ter. Migraciones del bloque aplicadas en Supabase (16/08/2026)

El titular ejecutó en Supabase SQL Editor los scripts del bloque y **verificó
los dos resultados** esperados:

- **`c2f6e8a1d934` (propuestas):** la tabla `public.enlaces_propuesta` tiene
  exactamente las 4 políticas previstas — `cotizat_proposal_insert_tenant`
  (INSERT con `tenant_access(organizacion_id, true)`),
  `cotizat_proposal_select_tenant` (SELECT por tenant),
  `cotizat_proposal_select_public` (SELECT solo por hash del token + vigente +
  no revocada) y `cotizat_proposal_update_tenant` (UPDATE por tenant). ✅
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

## 6. Reglas invariables (no negociables)

- **no abrir ni pedir fusionar un PR durante un bloque de trabajo activo**: al
  fusionarlo, el titular debe cerrar el chat y se pierde el acceso de esta
  sesión a la rama; los PR solo se crean cuando sean absolutamente necesarios,
  al terminar un bloque funcional completo y con autorización expresa del
  titular;
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
`docs/PUNTO_DE_CONTINUACION.md` y luego `docs/CONTINUIDAD_STAGING_SUPABASE.md`.
No repitas trabajo ya hecho y no me pidas secretos.

**Dónde quedó todo (16/08/2026, noche).**

- **E1-059 decidida: cobro manual para el piloto** (Stripe+autónomo en España
  queda para el cobro recurrente).
- **E1-060 cerrado del todo** (rama `arena/01a00837-generador-comercial`):
  recibo PDF de licencias de pago, **corte automático de acceso** con
  `COTIZAT_EXIGIR_LICENCIA` (apagado por omisión), **avisos de vencimiento**
  por correo desde el panel, y corrección del bug que dejaba al panel ciego a
  organizaciones de clientes. Migración nueva `b7c4a9e2d31f` con script
  `docs/staging_upgrade_b7c4a9e2d31f.sql`. Suite: **391 passed, 5 skipped**.
- **E1-061 documentado** en `docs/PROCESO_PILOTOS.md` (guion de pilotos).
- **PR #25 fusionado**, migración aplicada y licencias funcionando según la
  verificación del titular.
- **Usabilidad superada (E1-012/013/014):** profesionales de construcción sin
  ayuda, varios presupuestos de baño en ≈10 minutos y sin errores observados.
- **Etapa 1 completada.** Las partidas actuales son propias y se mantienen
  solo como ejemplos de prueba; el catálogo real se cargará al final.
- **Validación comercial aplazada por decisión del titular:** no habrá pilotos
  hasta que el producto se considere completo.
- Incidencia de Auth cerrada (Redirect URLs y rate limits confirmados).

**E3-016 a E3-024 completados localmente:** envío por email, enlace público
revocable, respuesta trazable, notificación y estado controlado, respaldo
web completo y verificable con restauración en dos pasos, exportación
portátil, baja con borrado verificado y monitorización y diagnóstico del
operador. **Cierre funcional y operativo de la Etapa 3 completo en la rama.**
Suite verificada: **453 passed, 6 skipped**. **Las migraciones `c2f6e8a1d934`
y `a3d7e9c1b5f2` están aplicadas y verificadas en Supabase el 16/08/2026**
(ver §0ter). Queda desplegar el código de la rama (hasta entonces `/readyz`
del entorno migrado responde 503, esperado) y ensayar el flujo real. Siguiente
según la puerta de salida: endurecimiento técnico de la Etapa 4. No abrir PR.
No retomar catálogo ni pilotos salvo nueva decisión expresa.

**Nota de la sesión de recuperación (16/08/2026):** todo lo anterior se
recuperó desde un parche en la rama `arena/01a00b99-generador-comercial`
(sección «0bis» de este documento) y quedó commiteado y empujado como
`9fd5afa`. Los commits del bloque de respaldo se añaden sobre esa base en la
misma rama.

---
