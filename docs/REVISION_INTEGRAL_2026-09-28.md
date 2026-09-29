# Revisión integral de CotizaT — 28/09/2026

## Resultado ejecutivo

La revisión local quedó **verde en las comprobaciones automatizadas disponibles**: la suite terminó con **1268 pruebas aprobadas, 9 omitidas y 0 fallidas**, sin avisos de SQLAlchemy ni deprecaciones. También se corrigió un caso de identidad obsoleta al recrear la configuración durante la migración del catálogo.

Esto no equivale a certificar que no exista ningún defecto posible ni que el despliegue remoto esté listo: no se dispuso de conexión a Supabase/Vercel ni de un navegador gráfico instalado. Se indican al final las comprobaciones que requieren esos entornos.

## Cobertura y resultados

- **Suite completa:** `1268 passed, 9 skipped` (434 s). Los 9 skips son las pruebas de RLS que requieren `COTIZAT_TEST_ADMIN_DATABASE_URL`; no se conectó a una base real.
- **Python:** `compileall` de `app`, `tools`, `run.py` y `desktop.py`, correcto.
- **Plantillas:** 127 plantillas Jinja parseadas con el entorno real, correcto.
- **JavaScript:** `node --check` en todos los archivos de `app/static/js`, correcto.
- **CSS:** las 4 hojas del proyecto parsean sin errores; además, pasan las pruebas de la capa móvil incluidas en la suite.
- **Dependencias:** los 68 paquetes directos concuerdan con `requirements.lock`; `pip-audit` no encontró vulnerabilidades conocidas.
- **Secretos:** 6765 archivos versionados revisados por el auditor del proyecto; el análisis comparado con el baseline no añadió hallazgos. El baseline versionado quedó intacto.
- **Vercel / solo lectura:** las simulaciones PostgreSQL y SQLite importan la aplicación correctamente.
- **Alembic:** el código declara un único head, `h1c4b7e9a3d2`.
- **Smoke test HTTP local:** 20 endpoints principales consultados; las páginas funcionales renderizaron correctamente. En 16 páginas renderizadas se comprobaron **167 referencias same-origin** de recursos, todas con respuesta 200, y no se detectaron IDs HTML duplicados. La única excepción fue `/readyz` (503 por configuración ausente, detallado abajo).
- **Salud local:** `/healthz` responde 200. `/readyz` devuelve 503 en esta ejecución local porque no se configuraron Supabase Auth ni `COTIZAT_PUBLIC_URL`; es un entorno efímero de prueba, no una comprobación del estado de producción.

## Correcciones hechas

1. **Recreación de `Configuracion` al migrar el catálogo.** Si la fila se borraba dentro de una sesión que conservaba una instancia ORM expirada, SQLite podía reutilizar su ID y SQLAlchemy emitía `SAWarning` al insertar la fila nueva. Ahora se expulsa la instancia obsoleta de forma acotada antes de recrear la configuración. Se añadió una regresión que exige que el camino termine sin `SAWarning`.
2. **Aviso deprecado en una prueba SEO.** Se cambió la configuración de la cookie en `TestClient` al almacén del cliente, en lugar de pasarla por petición.
3. **Documentación operativa desactualizada.** El README y las guías principales indicaban heads de Alembic antiguos y algunos SQL manuales podían interpretarse como instrucciones actuales. Se actualizaron los puntos de entrada para dejar claro que el código exige `h1c4b7e9a3d2`, que el head remoto es desconocido desde esta revisión y que hay que consultar la versión real antes de migrar. Las referencias históricas quedan identificadas como tales.

## Lo que no puede certificarse desde este entorno

- **RLS real/PostgreSQL:** las 9 pruebas específicas quedaron omitidas al faltar `COTIZAT_TEST_ADMIN_DATABASE_URL`. Deben ejecutarse en una base de staging aislada y con un rol runtime no privilegiado.
- **Servicios externos:** no se ejecutaron flujos reales de Supabase Auth/Storage, Stripe Checkout/webhook, envío por Resend, ni los crons de Vercel. Tampoco se inspeccionaron sus variables o la versión remota de `alembic_version`.
- **Inspección visual en navegador:** las pruebas móviles y el parseo CSS pasan, y los recursos locales no dan 404; aun así, no se pudo hacer una inspección de píxeles, consola JavaScript o CSP en Chrome/Safari porque no había un navegador instalado y la descarga de Chromium falló por un error TLS de red. El preview local queda disponible para una comprobación visual manual.

Antes de declarar el despliegue listo, sigue la matriz de aceptación de [`APROVISIONAMIENTO_STAGING.md`](APROVISIONAMIENTO_STAGING.md) y verifica allí el estado remoto. No apliques un `staging_upgrade_*.sql` si la precondición de versión no coincide exactamente.
