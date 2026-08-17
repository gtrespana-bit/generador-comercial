# Exportación y baja por organización (E3-022 / E3-023)

Fecha: **16/08/2026** · Suite: **441 passed, 6 skipped** · Migración nueva:
**`a3d7e9c1b5f2`** (función de baja, solo PostgreSQL). **Aplicada y verificada
en Supabase el 16/08/2026**: `baja_organizacion` con `security_definer = true`
y propietario `postgres`, según la verificación del titular.

> Estado actual: la cadena continuó hasta `d6e2f9c4b8a1`; ver
> `docs/PUNTO_DE_CONTINUACION.md`. La migración aquí descrita sigue aplicada.

Este bloque cierra la portabilidad del dato y el ciclo de salida de una
organización: llevarse los datos en un formato abierto (E3-022) y darse de
baja con borrado verificado (E3-023). Se apoya en el respaldo verificable de
E3-020/021 (`docs/RESPALDO_Y_RESTAURACION_WEB.md`).

---

## 1. Exportación portátil (E3-022)

Ruta: `GET /configuracion/exportacion/descargar` (propietario/administrador).
Un `.zip` formato **`cotizat-export` v1** con:

| Entrada | Contenido |
|---|---|
| `cotizat-respaldo.zip` | el paquete verificable de E3-020 completo, restaurable en cualquier CotizaT (Configuración → Respaldo) |
| `csv/` | una hoja CSV por tabla (UTF-8 con BOM, abre directo en Excel/LibreOffice); encabezados derivados del modelo incluso cuando la tabla viene vacía |
| `archivos_con_nombre/` | los archivos con su nombre original, prefijado con 12 caracteres de su SHA-256 para evitar colisiones |
| `manifest_exportacion.json` | formato, versión, conteos, omisiones y avisos |
| `LEEME_EXPORTACION.txt` | instrucciones en lenguaje claro |

Las mismas omisiones honestas del respaldo: no viajan cuentas, licencias,
invitaciones, enlaces públicos ni datos de demostración. Límite: 350 MB.
Funciona igual en PostgreSQL y SQLite.

## 2. Baja de la organización (E3-023)

Rutas: `GET /configuracion/baja` y `POST /configuracion/baja/confirmar`.
**Solo el propietario.** La pantalla muestra primero qué se borraría y ofrece
la exportación antes de confirmar.

Guardias (defensa en profundidad: ruta + servicio + función PostgreSQL):

1. Rol de propietario exigido en ruta y en servicio.
2. **Nombre exacto de la organización escrito a mano** + casilla explícita de
   irreversibilidad. Sin coincidencia exacta no se borra nada.
3. En PostgreSQL, la función `cotizat_security.baja_organizacion(id)`
   (SECURITY DEFINER) exige además el claim `cotizat.organization_id` de la
   sesión y que `cotizat_security.membership_role(id)` devuelva `propietario`.

Orden del borrado, para no dejar residuos ni huérfanos:

1. **Archivos primero**: se recogen las claves de `archivos_almacenados` y se
   eliminan del almacenamiento privado ANTES de tocar la base. Si un objeto
   falla, la baja se aborta entera y no se borra nada (reintentar es seguro).
2. **Datos y organización en una transacción**: tablas de negocio en orden
   hijo → padre, invitaciones, configuración, licencias, membresías y la
   propia organización. En SQLite por ORM (con el filtro de tenant activo);
   en PostgreSQL por la función SECURITY DEFINER.

Lo que NO se borra (declarado, no olvidado):

- **La cuenta de acceso (Supabase Auth):** queda sin organizaciones y puede
  crear una nueva; el borrado de identidades de Auth es ajeno a la app.
- **La contabilidad externa del operador:** la licencia desaparece de la base
  (no hay contrato sin organización), pero el operador conserva sus registros
  propios.

Sin período de gracia por diseño: la baja es inmediata y verificada. Tras el
borrado la ruta responde directamente (sin redirect, para no consultar una
organización que ya no existe) y retira la cookie `cotizat_organization_id`.

## 3. Despliegue

- **Migración nueva `a3d7e9c1b5f2`** (solo PostgreSQL): crea la función de
  baja, la reasigna al usuario que aplica la migración, revoca PUBLIC y
  concede solo a `cotizat_app`. En SQLite no aplica (baja por ORM).
- Script para Supabase: **`docs/staging_upgrade_a3d7e9c1b5f2.sql`** con guarda
  de versión (`c2f6e8a1d934` → `a3d7e9c1b5f2`).
- `EXPECTED_ALEMBIC_HEAD` ya apunta a `a3d7e9c1b5f2`; **no aplicar en Supabase
  hasta la autorización de despliegue** del bloque (regla vigente del
  proyecto). Producción continúa en `c2f6e8a1d934` mientras tanto; el head
  exigido solo se comprueba en PostgreSQL.

## 4. Verificación del bloque

- Pruebas nuevas: `tests/test_exportacion.py` (6) y
  `tests/test_baja_organizacion.py` (12): contenido del paquete, CSVs con
  BOM y conteos, nombres de archivo, roles, rechazos sin efectos, borrado
  completo con aislamiento entre organizaciones, fallo de almacenamiento sin
  borrado parcial, cookie post-baja y definición SQL de la función.
- Suite completa: **441 passed, 6 skipped**; 62 plantillas, `compileall`,
  JavaScript, lock (42 paquetes) y `git diff --check` en verde; simulación de
  Vercel read-only correcta.

## 5. Siguiente (E3-024)

Monitorización y diagnóstico de la operación web (salud, errores y métricas
honestas). El catálogo comercial y la validación pagada siguen aplazados por
decisión del titular (D-017).
