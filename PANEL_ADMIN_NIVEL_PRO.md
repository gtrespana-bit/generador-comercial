# Panel de administración — plan para llevarlo a nivel profesional

**Fecha:** 2026-08-29
**Estado:** ✅ Fases 1–2 completas y ✅ Fase 3 completada; Fase 4 en curso con CRM, vistas guardadas, salud de datos y API keys — suite verde (1153 pruebas, 9 skipped). Pendientes detallados en la sección 3.
**Ámbito:** `app/routers/admin.py`, `app/services/panel_admin.py`, `app/templates/admin/*`, `app/services/analitica.py`, `app/services/mantenimiento.py`
**Objetivo:** que `/admin` deje de ser un panel de **lectura/gestión de licencias** y pase a ser el **centro de control de todo el negocio**: cobros, clientes, web, producto, seguridad y operaciones.

---

## 0. Lo que ya tienes (y que no se puede perder)

El panel actual es sólido para la fase en la que está. No hay que reconstruirlo, hay que **completarlo**:

| Módulo | Qué hace | Valor |
|---|---|---|
| `/admin` | Dashboard con clientes, planes, caducidades, LTV, compras pendientes | Vista operativa diaria |
| `/admin/licencias` | Conceder/renovar/cancelar, recibo PDF, avisos de vencimiento | Gestión de acceso |
| `/admin/compras` | Revisar comprobantes, activar/rechazar compras | Cierre de cobros manuales |
| `/admin/analitica` | KPI, embudo, activos, cohortes, churn, uso de funciones, países | Datos de producto |
| `/admin/emails` | Enviar cualquier correo de prueba a un buzón real | QA de comunicaciones |
| `/admin/operacion` | Diagnóstico de despliegue (`/readyz` + errores) | Salud técnica |
| Respaldo/restauración | Copia completa + verificación diaria en cron | Continuidad |
| Auditoría/actividad | Registro por organización de `quién hizo qué` | Trazabilidad por cliente |
| Telemetría | EventoProducto, latidos, embudo, churn | Métricas propias |

**Por qué aún no "se siente" súper profesional:**

1. Es un panel de **operador único** (lista de correos en `COTIZAT_OPERADORES`), sin roles ni equipo.
2. **No hay auditoría de las acciones del propio admin**: quién concedió, revocó, activó, cambió un plan. Eso es estándar en cualquier SaaS.
3. No hay **ficha profunda del cliente**: solo ves la fila expandida con licencias; no ves uso, presupuestos, enlaces enviados, facturas, pagos, notas.
4. No hay **buscador global/command palette** (⌘K) ni vistas guardadas/filtros compartidos.
5. No hay **centro de notificaciones/alertas** del negocio (renovaciones, churn, compras, errores de email/Stripe/backup).
6. La **web pública** (landing, SEO, artículos, FAQ, precios por país, testimonios) está en código/archivos, no administrable desde el panel.
7. No hay **automatizaciones visibles** (renovación, reactivación, digest de reporte, cron jobs) más allá de los 2 cron de Vercel.
8. El dashboard muestra **acumulados**, no negocio en movimiento: falta MRR/ARR, renovaciones del mes, tasa de pago, LTV por cohorte, alertas.

---

## 1. Principio rector

> Un panel profesional no sirve para **ver** el negocio; sirve para **operarlo y decidir**.

Cada módulo nuevo debe responder una de estas preguntas:

- ¿Qué está pasando ahora? (alertas, pendientes, riesgo)
- ¿Quién es el cliente y qué me debe? (ficha, cobros, saldos)
- ¿Qué hago con ese cliente? (conceder, recordar, escalar, enviar, suspender)
- ¿Cómo está la web y el producto? (SEO, contenidos, métricas, salud)
- ¿Lo que hago queda documentado? (roles, auditoría, acciones reversibles)

---

## 2. Mapa de módulos propuestos

### A) Fundaciones del "super panel" (base para todo lo demás)

| Módulo | Qué hace | Esfuerzo | Impacto |
|---|---|---|---|
| **A1. Roles de operador** ✅ | Sustituir la lista plana `COTIZAT_OPERADORES` por tabla `operadores` con rol (`superadmin`, `admin`, `soporte`, `analista`) + acceso activo. | Media | 🔥🔥🔥 |
| **A2. Auditoría del admin** ✅ | Registrar en `eventos_auditoria`/tabla propia `admin_accion`: quién, cuándo, qué, a quién, IP hash, resultado. | Media | 🔥🔥🔥 |
| **A3. Buscador global / ⌘K** ✅ | Buscar clientes, emails, licencias, compras, facturas, artículos y acciones; atajos de teclado. | Media | 🔥🔥🔥 |
| **A4. Centro de notificaciones** ✅ | Campana con pendientes: renovaciones ≤15d, compras por activar, errores de Stripe/Resend, backups, riesgo churn, ventas del mes. | Media | 🔥🔥🔥 |
| **A5. Vista guardadas y CSV** ✅ (CSV + filtros) | Filtros por estado/plan/país/importe/fecha y exportación de la vista actual a CSV en Clientes, Cobros y Renovaciones. Vistas guardadas persistentes como módulo propio quedan para Fase 4. | Baja | 🔥🔥 |

### B) Negocio y clientes (donde está el retorno)

| Módulo | Qué hace | Esfuerzo | Impacto |
|---|---|---|---|
| **B1. Ficha de cliente/ficha empresa** ✅ | `/admin/clientes/{id}` con **Resumen** (plan, uso, último acceso), **Miembros**, **Facturas/pagos**, **Historial licencias**, **Notas internas**, **Actividad**. | Alta | 🔥🔥🔥 |
| **B2. Centro de cobros** ✅ | `/admin/cobros` mensual con licencias, compras, facturas y pagos; exportación CSV. Reenvío de recibo desde la ficha/historial. | Alta | 🔥🔥🔥 |
| **B3. Panel de renovaciones** ✅ | `/admin/renovaciones` mensual: qué vence, importe, estado del aviso y acceso a la ficha. | Media | 🔥🔥🔥 |
| **B4. Canal/CRM ligero** | Estado comercial del cliente (lead, prueba, activo, en riesgo, inactivo), notas, onboarding, próximo contacto. | Media | 🔥🔥 |
| **B5. Automatizaciones** ✅ (núcleo) | `/admin/automatizaciones`: reglas visibles y ejecutables (recordatorios 5/1d, avisos 15d, mantenimiento) más alertas de clientes sin plan. Las reglas visuales completas siguen en Fase 4. | Alta | 🔥🔥🔥 |
| **B6. Métricas financieras** ✅ | MRR/ARR, renovaciones del mes, tasa de pago por origen, LTV por cohorte, ticket medio, ingresos por país/plan. | Media | 🔥🔥🔥 |

### C) Web pública y contenido

| Módulo | Qué hace | Esfuerzo | Impacto |
|---|---|---|---|
| **C1. CMS de landing** | Editar hero, beneficios, números, CTAs y secciones desde el panel (con publicar/descartar). | Alta | 🔥🔥🔥 |
| **C2. SEO operational** | Gestionar meta title/description, H1, URLs por país, artículos, `sitemap`, `robots`, alt de imágenes, fecha de actualización. | Media | 🔥🔥🔥 |
| **C3. Contenido por país** | Precio, moneda, IVA, ID fiscal, vocabulario, FAQ, testimonios, casos, comparativas por `ES/VE/CO/MX/PE/EC…`. | Media | 🔥🔥🔥 |
| **C4. Avisos y banners** | Mantenimiento programado, aviso legal, anuncio de versión, panel de "estado del servicio". | Baja | 🔥🔥 |
| **C5. Releases / changelog** | Notas de versión visibles a clientes, enlace a guía rápida, release destacado. | Baja | 🔥🔥 |

### D) Producto, datos y operación

| Módulo | Qué hace | Esfuerzo | Impacto |
|---|---|---|---|
| **D1. Catálogo por país** | Ver estado de cobertura por país, actualizar precios/recursos, marcar versiones, sincronización con `basedatos_partidas`. | Media | 🔥🔥 |
| **D2. Salud de datos** | Auditoría de precios anómalos, duplicados, recetas huérfanas, catálogos incompletos, partidas con coste 0. | Media | 🔥🔥 |
| **D3. Feature flags** | Activar/desactivar funciones por despliegue: onboarding, planos, IA, cotizaciones, pruebas piloto. | Media | 🔥🔥 |
| **D4. Operaciones y logs** | Estado de Stripe/Resend/Supabase/Storage, colas de email, resultados de cron, purga de backups. | Media | 🔥🔥 |
| **D5. Migraciones/data imports** | Importar/exportar catálogo, organizaciones, licencias, artículos SEO; verificar resultado. | Alta | 🔥🔥 |

---

## 3. Orden recomendado (roadmap por fases)

### Fase 1 — "Súper usable" (1–2 semanas, alto retorno) ✅ completada

1. **A1: Roles de operador** (tabla + formulario + acceso activo/suspensión).
2. **A2: Auditoría del admin** (registro de cada acción del panel).
3. **A3: Buscador global / ⌘K**.
4. **A4: Centro de notificaciones**.
5. **B6: Métricas financieras** en el dashboard (MRR/ARR, renovación del mes, tasa pago, LTV por cohorte).

**Qué ganas:** el admin se vuelve *operable*, no solo informativo; cada acción queda rastreada y el dashboard cuenta la historia del negocio.

### Fase 2 — "Gestión del cliente" (2–4 semanas) ✅ completada (núcleo)

6. **B1: Ficha de cliente/empresa** ✅.
7. **B2: Centro de cobros** (facturas, pagos, Stripe, reenviar) ✅ núcleo.
8. **B3: Panel de renovaciones** con campaña de avisos ✅.
9. **B5: Automatizaciones** ✅ reglas visibles/ejecutables (recordatorios, avisos, mantenimiento).
10. **A5: Vista guardadas + CSV** ✅ CSV y filtros; vistas guardadas persistentes en Fase 4.

**Qué ganas:** pasas de "gestionar licencias" a "gestionar relaciones comerciales".

### Fase 3 — "La web como producto" ✅ implementada

11. **C1: CMS de landing** ✅ (`/admin/web`, borrador/publicar/descartar).
12. **C2: SEO operational** ✅ (claves de contenido para landing/SEO; `/novedades`).
13. **C3: Contenido por país** ✅ base (las claves de contenido admiten campos por país; la capa pública las lee por `?pais=`/subdirectorio).
14. **C5: Releases / changelog** ✅ (`/admin/releases` + `/novedades` público).
15. **D3: Feature flags** ✅ (`/admin/flags`) + **C4: Avisos/banners** ✅ (`/admin/avisos`).

**Qué ganas:** dejas de pedir a un desarrollador cada cambio de texto/página y la web se gobierna desde el panel.

### Fase 4 — "Escala y confianza" (en curso)

16. **B4: CRM/lead ligero** ✅ (`/admin/crm`).
19. **A6: Integraciones/API keys + doble factor de operadores** ✅ API keys con hash SHA-256 (`/admin/api-keys`); 2FA de operadores pendiente.
17. **D1–D2: Catálogo + salud de datos** 🟡 página `/admin/salud-datos` (vista operacional; agregados cruzados por organización vía funciones SECURITY DEFINER pendientes).
- **A5: Vistas guardadas persistentes** ✅ (`/admin/vistas` + tabla `vistas_guardadas`).
- **B2: Reenvío masivo de facturas** ⏳ pendiente (necesita función SECURITY DEFINER + cola de correo).
- **B5: Reglas visuales completas de automatizaciones** ⏳ pendiente (el núcleo de ejecución y la vista actual siguen; faltan triggers/ajustes UI completos).
- **D4: Operaciones avanzadas / informe ejecutivo (PDF/CSV)** ⏳ pendiente.

---

## 4. Detalle de la primera fase (spec corta)

### 4.1 Roles de operador
- Tabla `operadores_producto`: `user_id`, `email`, `rol` (`superadmin`, `admin`, `soporte`, `analista`), `activo`, `created_at`, `updated_at`.
- `get_operator_db` mantiene la comprobación con `COTIZAT_OPERADORES` **como fallback**, pero ahora cede a la base de datos.
- Página `/admin/equipo`: listar, invitar, cambiar rol, suspender. Solo `superadmin` gestiona roles.
- En PostgreSQL: `es_operador` en RLS sigue igual; el rol solo afecta a **qué páginas** puedes ver.

### 4.2 Auditoría del admin
- Nuevo modelo `EventoAdmin` (o campo `destinatario` en auditoría): `operador_email`, `accion`, `entidad`, `entidad_id`, `detalle`, `ip_hash`, `resultado`, `created_at`.
- Registrar: conceit/renovar/suspender licencia, activar/rechazar compra, avisos enviados, cambios de rol, contenido publicado.
- Página `/admin/auditoria` con filtros por actor, fecha, acción, cliente.

### 4.3 Buscador global / ⌘K
- API JSON `/admin/buscar?q=` que busca organizaciones, emails, licencias, compras, facturas, artículos SEO.
- JS en `base_admin.html`: overlay al pulsar `⌘K`/`Ctrl+K`, lista de resultados, `Enter` abre la página.
- Sin dependencias externas (vanilla JS, CSP-friendly).

### 4.4 Centro de notificaciones
- En la topbar, campana con contador.
- Fuentes: licencias por vencer, compras pendientes, pagos Stripe fallidos, errores de email, backup sin OK, churn, facturas vencidas, artículos sin publicar.
- Cada notificación enlaza a la página de detalle.

### 4.5 Métricas financieras
- Añadir al dashboard: **MRR, ARR, ingresos del mes, renovaciones del mes, ticket medio, tasa pago→licencia, LTV medio por cohorte**.
- Serie de 6/12 meses (mini-gráfico SVG, sin librería).

---

## 5. Restricciones técnicas a respetar

1. **RLS de operador vs. datos de tenant.** El operador hoy no puede leer `presupuestos`/`clientes` de una organización (RLS tenant). Para la ficha de cliente, la opción recomendada es:
   - **Agregados vía función `SECURITY DEFINER`** en `cotizat_security` (métricas de uso, nº de presupuestos, estados, sin exponer contenido).
   - O añadir política `SELECT` RLS explícita "solo operador" si quieres ver detalle real; **nunca** desactivar aislamiento.
2. **Nunca exponer datos de negocio de un cliente en un panel que comparta el operador sin rol**.
3. Los **cron de Vercel** siguen en `vercel.json`; las automatizaciones nuevas deben tener su propia ruta con `CRON_SECRET`.
4. Todo lo nuevo debe quedar **indexado** y verificable con tests (el repo ya tiene buen hábito de tests).
5. Los cambios de contenido web deben tener **publicar/descartar**, nunca editar en producción directamente.

---

## 6. Resumen de datos "una línea por estación"

| Fase | Módulos | Resultado |
|---|---|---|
| 1 | Roles, auditoría, ⌘K, notificaciones, finanzas | Panel usable y auditable |
| 2 | Ficha cliente, cobros, renovaciones, automatizaciones | Panel que gestiona el negocio |
| 3 | CMS, SEO, país, changelog, feature flags | La web se gobierna desde el panel |
| 4 | CRM, catálogo, salud datos, APIs, 2FA, informes | Panel de escala y confianza |

---

## 7. Siguiente paso sugerido

Empezar por **Fase 1** (roles + auditoría + ⌘K + notificaciones + métricas financieras). Es la que produce mayor salto de percepción y prepara todas las fases posteriores: roles permiten dar acceso a soporte/analista, auditoría da confianza, ⌘K da rapidez, notificaciones convierten el panel en proactivo y las métricas financieras en un dashboard de negocio real.
