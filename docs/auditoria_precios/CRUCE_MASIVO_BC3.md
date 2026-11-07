# Cruce masivo de recursos con bases BC3

## Objetivo y fuente

En lugar de buscar dos ofertas por cada recurso, cruzar los 388 recursos del catálogo contra los precios **simples** de bancos de precios completos; comparar después las referencias equivalentes de distintos territorios. La [Junta de Extremadura publica su base 2026 en BC3](https://www.juntaex.es/w/base-precios-construccion-2026), con actualización de la página de 11 de agosto de 2026. Su archivo enlazado es [BCEXTGREM_26_v1.bc3](https://www.juntaex.es/documents/77055/621768/BCEXTGREM_26_v1.bc3/8066c810-a694-eeed-c456-a64abca3cc2e?t=1782217730923). Es una referencia **de Extremadura**, no una estadística nacional.

## Ejecución

Descargar el BC3 oficial a una ubicación local y ejecutar:

```bash
python tools/cruzar_precios_bc3.py \
  --fuente 'Extremadura 2026|Extremadura|https://www.juntaex.es/w/base-precios-construccion-2026|/ruta/al/BCEXTGREM_26_v1.bc3' \
  --salida /tmp/candidatos_espana.csv
```

Se puede repetir `--fuente` para añadir bancos compatibles de otras zonas. El nombre, ámbito, URL y ruta son explícitos; el CSV de salida incluye SHA-256, código y fecha originales, descripción, unidad, precio, descripción larga, recursos y puntuación. Si no hay candidato queda una fila `sin_candidatos`. El archivo de origen puede ser grande: mantenerlo fuera del repositorio, salvo autorización y necesidad documentadas.

**Importante:** la clasificación por prefijos `P` material, `M` maquinaria y `O` mano de obra corresponde a la convención observada de Extremadura; no aplicar a otra base sin comprobar sus códigos. Se omiten precios por zona no desambiguados, unidades no reconocidas y conceptos con descomposición. No se convierten magnitudes, ni se resuelven las especificaciones con una puntuación textual.

El resultado es una **lista de candidatos sin validar**. Una coincidencia de palabras no acredita equivalencia de tamaño, composición, rendimiento ni condiciones. La alerta numérica es orientativa, no una garantía de equivalencia. Antes de aplicar un precio, revisar descripción y texto de la fuente y sus condiciones, incluidos IVA y transporte; en maquinaria comprobar operador, energía y amortización; en mano de obra comprobar que sea coste empresarial y sus cargas. Un único banco territorial no acredita una media nacional. Cuando haya dos fuentes territoriales comparables, emplear la media aritmética solicitada y registrar las dos fuentes y su ámbito. Si no son comparables, no promediarlas. Verificar las condiciones de uso y redistribución de cada banco antes de incorporar datos de forma masiva.

El cruce **no cambia** precios, estados, matriz, SQL ni producción. La revisión y aplicación explícitas se realizan después, con pruebas y registro de trazabilidad. Las pruebas del lector y del filtrado son `python -m pytest -q tests/test_cruzar_precios_bc3.py`.
