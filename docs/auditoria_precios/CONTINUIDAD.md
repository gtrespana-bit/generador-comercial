# Punto de continuidad: auditoría de precios por país

**Corte:** 6 de noviembre de 2026, fecha local de la sesión (America/Caracas).
**Rama:** `arena/6a7ec8e3-generador-comercial`.
**PR abierto:** [#210 — calculadora pública](https://github.com/gtrespana-bit/generador-comercial/pull/210). Los avances de esta auditoría se guardan también en esa rama y PR; no significa que hayan sido fusionados o desplegados.

## Qué pide el usuario

- Auditar los precios país por país, empezando por **España**, con referencia nacional operativa. Quiere terminar la auditoría y ver avances efectivos; rechazó un ritmo de búsqueda manual de uno en uno.
- Buscar un **método escalable por lotes** y realizarlo autónomamente: el usuario no quiere descargar, aportar archivos ni realizar gestiones.
- La mano de obra debe representar el coste de la empresa, no solo el salario. El usuario autorizó expresamente usar la media aritmética de dos referencias provinciales comparables como punto operativo (por ejemplo, 16 y 17 → 16,50).
- No inventar datos ni presentar una referencia operativa de dos fuentes como media estadística de toda España o como coste real garantizado. No confirmar recursos heterogéneos o insuficientemente sustentados. Distinguir coste empresarial de gastos generales y beneficio, y contemplar rendimientos para obtener coste por unidad de obra.

La calculadora del PR es una demostración de **una partida**, no presupuestos completos gratuitos. No implementar recuperación ni transferencia del cálculo después de registrarse o iniciar sesión: el usuario descartó expresamente esa complejidad. Las horas-persona no son duración de obra sin datos de cuadrilla.

## Estado exacto del corte

Inventario: **388 recursos**, de los que **13** están `confirmado_referencia`, **30** `en_revision` y **345** `pendiente`. El estado describe la auditoría, no que se conozca o garantice el coste de todas las empresas. Dentro de los 30 en revisión, 15 tienen precio provisional revisado y 15 aún no. En total se han actualizado precios de **19 materiales y 9 referencias de mano de obra**. La lista y el estado por recurso están en [`espana_2026-11-06.csv`](espana_2026-11-06.csv).

- Las cuatro referencias laborales contrastadas son `MO-AYU` 20,39 €/h, `MO-AYU-ESP` 20,59 €/h y `MO-OF1` / `MO-OF1-ALB` 23,18 €/h. Los otros cinco oficios tienen 23,18 €/h como hipótesis condicionada al convenio de construcción y permanecen en revisión. El modelo incluye retribución de tabla, aportación al plan y cargas estimadas, pero no todos los costes reales ni horas improductivas; detalle y fuentes en [`ESPANA_REFERENCIA_OPERATIVA_2026.md`](ESPANA_REFERENCIA_OPERATIVA_2026.md).
- Los materiales están documentados en [`ESPANA_MATERIALES_2026.md`](ESPANA_MATERIALES_2026.md), con las 38 ofertas y sus condiciones en [`espana_materiales_ofertas_2026.csv`](espana_materiales_ofertas_2026.csv). Son medias de dos ofertas puntuales sin IVA deducible ni transporte, no cotizaciones garantizadas ni una muestra estadística nacional. Algunos precios siguen en revisión por equivalencia o disponibilidad.
- La matriz local `basedatos_partidas/salida/precios_recursos_espana.csv` y el índice público local `basedatos_partidas/datos/precios_publicos/ES.json` reflejan estas referencias. El inventario conserva la fotografía inicial y los campos revisados por separado. No confundir el estado antiguo `confirmado` del catálogo base, que corresponde a otro flujo, con la auditoría española.
- Se ha generado `docs/cargar_precios_referencia_espana_2026-11-06.sql` para 388 filas, **sin ejecutarlo**. La instantánea anterior de cuatro referencias laborales está en [`cargar_precios_espana_mano_obra_2026-11-06.sql`](cargar_precios_espana_mano_obra_2026-11-06.sql). No se ha desplegado ni cambiado la base de datos de producción ni los precios propios de clientes.
- El último control ejecutado pasó **106 pruebas** de las suites de BC3, materiales, coste empresarial, calculadora, España y precios públicos. `tools/verificar_matriz_importable.py ES` informó de **388 filas importables y 0 errores**: esto solo valida compatibilidad de importación, no confirma que los 388 precios sean correctos. `git diff --check` no encontró errores.

## Tarea pendiente prioritaria: cruce real por lotes

Se ha creado `tools/cruzar_precios_bc3.py`, documentado en [`CRUCE_MASIVO_BC3.md`](CRUCE_MASIVO_BC3.md), con pruebas en `tests/test_cruzar_precios_bc3.py`. Lee BC3 locales, propone candidatos con fuente, ámbito, hash, unidad y alertas, y **no aplica precios**. Solo se ha probado con BC3 sintéticos: **no se ha ejecutado un cruce real completo**.

La [Junta de Extremadura publica una base oficial BC3 2026](https://www.juntaex.es/w/base-precios-construccion-2026); el [archivo BC3](https://www.juntaex.es/documents/77055/621768/BCEXTGREM_26_v1.bc3/8066c810-a694-eeed-c456-a64abca3cc2e?t=1782217730923) se pudo consultar por fragmentos con la herramienta de lectura web, pero no se consiguió descargar íntegro al workspace por las restricciones de acceso de la sesión. La lectura web produjo 2339 fragmentos con problemas de caracteres; no reconstruir ni afirmar un archivo completo a partir de unos pocos. No se encontró un espejo íntegro en GitHub en las búsquedas hechas. Una base de Extremadura es regional, no una media nacional.

**Siguiente trabajo:** obtener autónomamente bancos completos y utilizables de dos o más zonas, respetando sus condiciones de uso; ejecutar el cruce de verdad; validar equivalencias, unidades, IVA, transporte y alcance antes de aplicar medias; ampliar pruebas, actualizar inventario, matriz y fuentes. La clasificación por prefijos de la herramienta corresponde a Extremadura y debe comprobarse antes de usar otra base. Si la infraestructura sigue impidiendo obtener los datos, dejar constancia precisa del bloqueo y no pedir al usuario que los descargue. Una puntuación textual no confirma equivalencia ni costes reales.

Para reproducir los controles actuales, con dependencias instaladas:

```bash
python -m pytest -q tests/test_cruzar_precios_bc3.py tests/test_materiales_espana_auditoria.py tests/test_coste_empresa_espana_auditoria.py tests/test_calculadora.py tests/test_espana.py tests/test_precios_publicos.py
python tools/verificar_matriz_importable.py ES
git diff --check
```

El entorno de esta sesión usó `.venv/bin/python`. Para regeneración existen `tools/generar_matriz_precios_espana.py`, `tools/generar_sql_precios_espana.py` y el generador de precios públicos. No ejecutar SQL ni desplegar silenciosamente: informar del alcance y conservar la trazabilidad de cada corte.
