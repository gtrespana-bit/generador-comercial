# Respaldo y restauración web por organización (E3-020 / E3-021)

Fecha: **16/08/2026** · Suite: **423 passed, 6 skipped** · Sin migración nueva
(el head de Alembic al cerrar este bloque era `c2f6e8a1d934`; el bloque
siguiente lo llevó a `a3d7e9c1b5f2`, aplicada y verificada en Supabase).

Este documento describe la copia de seguridad **web** completa y verificable de
una organización y su restauración controlada. Sustituye —para la versión
web— la limitación histórica de «backups administrados sin descarga»: ahora el
propietario puede descargar un paquete íntegro y restaurarlo él mismo, sin
intervención del operador.

---

## 1. Qué es la copia

Un único `.zip` con formato declarado **`cotizat-backup` v1**, generado por
`app/services/respaldo.py`:

| Entrada | Contenido |
|---|---|
| `manifest.json` | formato, versión, organización origen (nombre/slug), conteos por tabla, lista de archivos con SHA-256/tamaño/referencias originales, **omisiones declaradas con su motivo** y avisos |
| `datos/*.json` | todas las tablas de negocio de la organización, con el id original (`_id`) de cada fila para rehacer las relaciones |
| `archivos/<sha256>` | bytes de cada archivo referenciado, guardados bajo su huella (una sola vez por contenido, aunque lo referencien diez campos) |
| `LEEME_RESTAURACION.txt` | explicación legible de qué contiene y cómo restaurarlo |

**Verificable:** cada archivo viaja bajo su SHA-256; la restauración comprueba
todas las huellas y los conteos **antes** de escribir una sola fila.

## 2. Qué viaja (completo)

Clientes, catálogo (categorías, partidas, productos, recursos), plantillas y
recetas, presupuestos con capítulos, partidas, mediciones, descomposiciones
CYPE y sus filas, opciones de producto, notas de seguimiento, anexos, borradores,
versiones congeladas, proyectos con cambios de alcance y pagos, facturas con
sus capítulos e ítems, **los ajustes comerciales de la configuración** (IVA,
moneda, validez, opciones del PDF…) y **todos los archivos referenciados**
desde cualquier campo (fotos de proyecto, PDFs congelados, logos de partidas,
fichas técnicas, Excel de origen, anexos…), deduplicados por SHA-256.

Las membresías viajan como pares `(correo, rol)`.

## 3. Qué NO viaja (decisión deliberada, declarada en el manifest)

| Omisión | Motivo |
|---|---|
| Cuentas de usuario / contraseñas | viven en Supabase Auth; la restauración aplica las membresías solo si la cuenta sigue existiendo |
| Licencias | las gestiona el operador; restaurarlas desde una copia podría alterar el acceso |
| Enlaces públicos de propuesta | el secreto solo existe como SHA-256 y no se puede reconstruir; **las respuestas históricas viajan como notas de seguimiento** para conservar la trazabilidad |
| Invitaciones pendientes | se regeneran desde Configuración → Equipo |
| Datos de demostración (`es_demo`) | un servidor restaurado no debe heredar contenido ficticio |
| Identidad de la empresa destino (nombre, RIF, logo, contacto) | se conserva la del destino; los ajustes comerciales sí se restauran |

## 4. Cómo se restaura (reglas)

Rutas: `GET /configuracion/respaldo`, `GET .../descargar`,
`POST .../restaurar` (analizar), `POST .../restaurar/confirmar`. Solo
**propietario/administrador**.

1. **Dos pasos con el MISMO archivo**: el paso 1 analiza y verifica sin
   escribir nada; el paso 2 exige volver a subir exactamente el mismo archivo
   (SHA-256 del paquete) más una casilla de confirmación. Compatible con
   serverless: el servidor no guarda el archivo entre peticiones (se
   streamea a `/tmp` con límite de **300 MB**).
2. **Fusión idempotente**: nada existente se borra ni se sobrescribe. Las
   filas se deduplican por claves naturales (presupuestos y facturas por
   `numero`, catálogo por `nombre`, clientes por `nombre+rif`, hijos por su
   padre + orden + nombre…): lo que coincide se **reutiliza**, lo que falta se
   **crea**. Restaurar dos veces no duplica nada; restaurar tras una pérdida
   parcial solo repone lo perdido.
3. **Archivos reescritos solo en filas nuevas**: las referencias de archivo de
   las filas creadas apuntan a objetos del almacenamiento privado del destino;
   si el objeto con la misma huella ya existe, se reutiliza su clave. Los
   objetos huérfanos creados antes de un fallo se retiran (best-effort).
4. **Rechazos duros**: manifest ausente/inválido, formato o versión
   desconocidos, conteos que no coinciden, huella alterada, rutas con
   `..`, entradas no esperadas, archivo > 300 MB. Nada se escribe.

La escritura usa la sesión ORM autenticada: tenencia, rol (`lectura`
bloqueado) y RLS se aplican igual que en cualquier escritura de la app. La
transacción la compromete la ruta; ante error, `rollback`.

## 5. Operación y verificación

- **Sin migración nueva**: el bloque no cambia el esquema. `EXPECTED_ALEMBIC_HEAD`
  continuaba en `c2f6e8a1d934`; **no aplicar nada en Supabase** por este
  bloque. (Histórico: el titular aplicó después `c2f6e8a1d934` y
  `a3d7e9c1b5f2` el 16/08/2026 — ver §0ter del punto de continuación.)
- En producción los archivos viajan por el proxy autorizado hacia el bucket
  privado (`storage://organizaciones/{org}/…`); la restauración usa el mismo
  camino que una subida normal (`save_object`).
- Pruebas: `tests/test_respaldo_restauracion.py` (14 pruebas): formato e
  integridad del paquete, deduplicación por SHA-256, restauración completa tras
  pérdida, idempotencia, pérdida parcial, rechazos (huella alterada, conteos,
  versión, zip-slip), flujo HTTP de dos pasos con el mismo archivo, roles y
  omisiones honestas (licencias, enlaces, cuentas inexistentes).
- Verificación del bloque: suite completa **423 passed, 6 skipped**, 60
  plantillas, `compileall`, JavaScript, lock (42 paquetes) y
  `git diff --check` en verde; simulación de Vercel read-only correcta.

## 6. Pendientes deliberados del bloque (no son olvidos)

- **Exportación y baja por organización** (E3-022 / E3-023): **completadas el
  16/08/2026** sobre este mismo paquete — ver
  `docs/EXPORTACION_Y_BAJA_ORGANIZACION.md`.
- La descarga SQLite histórica (`/configuracion/backup`) sigue intacta para el
  escritorio; el nuevo respaldo funciona en **ambos** backends.
