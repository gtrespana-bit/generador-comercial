# Simulacro de caída y recuperación (E4-043)

> Procedimiento del titular para ensayar que los respaldos (E4-021/E3-020) se
> restauran de verdad. Un respaldo que nadie ha restaurado nunca es una
> esperanza, no un plan: el simulacro convierte la esperanza en procedimiento.
>
> Estado: **pendiente de ejecución — primera ejecución recomendada antes del
> día final de tests (D-019)**. Se agrupa con E4-021 (respaldo automático) y
> con `docs/PLAN_DE_RESPUESTA_A_INCIDENTES.md` (E4-032), que es el plan que
> este simulacro ensaya.

## 0. Qué se ensaya y qué no

Se ensaya: **bajar a producción de un incidente que destruye la base de datos
y comprobar que el respaldo automático permite reconstruir los datos de una
organización en un entorno de pruebas**, sin tocar la producción real.

No se ensaya (deliberadamente): restaurar sobre producción en vivo, borrar
datos reales, ni probar la infraestructura de Supabase Pro (backups de panel),
que se verifica por separado cuando se contrate.

## 1. Requisitos

- Un entorno de pruebas con PostgreSQL: el staging de Supabase o un
  PostgreSQL local (la receta de `tests/test_rls_postgres.py` crea uno
  desechable, o se usa `docs/GUIA_STAGING_POR_CLICS.md`).
- Un respaldo real: el zip generado por el cron de mantenimiento
  (`organizaciones/<id>/respaldo_automatico/…`) o, si el cron aún no ha
  corrido, uno manual desde `/configuracion/respaldo`.
- Una organización de pruebas en producción o en staging con datos
  reconocibles (2-3 presupuestos, un cliente, una configuración con logo).

## 2. Procedimiento (≈ 60-90 minutos la primera vez)

1. **Preparar el escenario (10 min).** Elegir una organización de pruebas y
   anotar: número de presupuestos, clientes, configuración. Descargar su
   último respaldo automático (o generarlo manualmente). Registrar el SHA-256
   del archivo.
2. **Verificar la integridad del respaldo (10 min).** En un entorno aislado,
   abrir el zip y comprobar: `manifest.json` presente y legible, conteos que
   coinciden con lo anotado, archivos de anexos presentes. Sin esto, no se
   sigue.
3. **Simular la pérdida (5 min).** En el entorno de pruebas (NUNCA en
   producción): borrar una parte reconocible de los datos de la organización
   (por ejemplo, una tabla de presupuestos o una configuración). Anotar qué
   se borró.
4. **Restaurar (20 min).** Con la sesión de la organización de pruebas:
   `/configuracion/restaurar` — paso 1 (analizar, debe reportar lo que falta)
   y paso 2 (mismo archivo + confirmación). Verificar: los datos borrados
   volvieron, los que no se borraron NO se duplicaron (idempotencia),
   los anexos/PDFs se ven.
5. **Repetir la restauración (10 min).** Restaurar el mismo archivo otra vez
   y comprobar que no duplica nada: es la garantía de que una restauración
   fallida o repetida no corrompe.
6. **Probar el flujo del incidente (10 min).** Seguir el runbook S1 del plan
   de incidentes hasta el paso 3 con el escenario real: ¿dónde se buscaría el
   respaldo? ¿quién tiene acceso? ¿cuánto tardó? Anotar todo lo que falte
   (accesos, permisos, documentación).
7. **Cerrar con acta (10 min).** Rellenar la tabla de resultados de abajo y
   guardar el acta en `docs/INCIDENTES.md` (o como `docs/SIMULACRO_<fecha>.md`).
   Si algo falló, el fallo es el resultado valioso del simulacro: se arregla y
   se vuelve a ensayar.

## 3. Criterios de éxito

| Comprobación | Resultado esperado |
| --- | --- |
| El zip del respaldo abre y su manifest es válido | ✅ |
| Los conteos del manifest coinciden con la realidad anotada | ✅ |
| Tras restaurar, los datos borrados vuelven | ✅ |
| Tras restaurar, los datos no borrados no se duplican | ✅ |
| Segunda restauración del mismo archivo: sin duplicados | ✅ |
| Los anexos/PDFs referenciados se sirven tras la restauración | ✅ |
| El tiempo total hasta «datos recuperados» se anota y es < 60 min | ✅ (objetivo) |
| Se identifican ≥ 1 mejora de proceso (acceso, doc, automatización) | ✅ |

## 4. Frecuencia

- **Primera ejecución**: antes del día final de tests (D-019), con datos de
  la organización de pruebas real.
- **Después**: cada vez que cambie algo relevante en el esquema (migración) o
  en el mecanismo de respaldo, y al menos una vez al año.
- **Tras un incidente real S1**: repetir el simulacro con la lección
  incorporada dentro del mes siguiente.

## 5. Relación con el resto

- E4-021 (respaldo automático): el simulacro usa su salida.
- E3-021 (restauración ensayada): la restauración ya tiene pruebas
  automáticas (`tests/test_respaldo_restauracion.py`); el simulacro es el
  ensayo manual de integración que las pruebas no cubren.
- E4-043 se marca completado cuando exista la primera acta con todos los
  criterios ✅.
