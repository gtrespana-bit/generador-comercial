# Panel profesional — estado exacto

**Fecha:** 2026-08-29
**Rama de trabajo:** `arena/01a04bd3-generador-comercial`
**Commit actual:** `2a9ef6e` — "Fase 3/4 panel web: CMS, avisos, releases, flags, CRM, vistas, API keys y salud"
**Head Alembic esperado por runtime:** `d3e5f7a9c2b4`

---

## 1. Resumen ejecutivo

| Área | Estado |
|---|---|
| Fase 1 (roles, auditoría, ⌘K, notificaciones, métricas) | ✅ Completa |
| Fase 2 (ficha cliente, cobros, renovaciones, automatizaciones núcleo, CSV) | ✅ Completa |
| Fase 3 (web como producto: CMS, SEO, avisos, releases, flags) | ✅ Completa |
| Fase 4 (CRM, vistas, API keys, salud de datos, informe) | 🟡 Núcleo implementado; 4–6 ítems pendientes |

- **Suite completa:** 1153 passed, 9 skipped, 2 warnings (la última ejecución completa).
- **Adicional después de la ejecución completa:** test `/novedades` añadido en `tests/test_panel_pro_fase34.py`; también pasa.
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

## 4. Qué queda pendiente (ordenado por prioridad)

1. **Vistas guardadas conectadas a las páginas** (A5 real)
   - Ya existe `vistas_guardadas` + `/admin/vistas`.
   - Falta que Clientes, Cobros, Renovaciones, Compras y Automatizaciones puedan **guardar/cargar** su filtro/columnas actuales desde la propia página.

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
| `app/routers/admin.py` | Rutas `/admin/web`, `/admin/avisos`, `/admin/releases`, `/admin/flags`, `/admin/crm`, `/admin/vistas`, `/admin/salud-datos`, `/admin/api-keys`. |
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
