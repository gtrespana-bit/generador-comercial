> **Actualización posterior:** también se han revisado diecinueve materiales. Véase [contraste de materiales](ESPANA_MATERIALES_2026.md).

# España: primeras referencias operativas de mano de obra (2026)

**Actualización: 2026-11-06.** Por decisión del usuario se adopta como referencia española un **punto medio simple** entre los escenarios de Madrid y Barcelona. Se utilizan los datos 2026 documentados en [contraste provincial](ESPANA_CONTRASTE_PROVINCIAL_2026.md). Este es un criterio práctico, no un promedio estadístico de España ni un coste real garantizado de una empresa concreta.

## Precios actualizados

| Recurso | Precio anterior €/h | Madrid €/h | Barcelona €/h | Referencia nueva €/h |
|---|---:|---:|---:|---:|
| `MO-AYU` — ayudante genérico (aproximado por peón ordinario) | 15,00 | 18,65 | 22,14 | **20,39** |
| `MO-AYU-ESP` — ayudante especializado (peón especialista) | 18,00 | 18,67 | 22,52 | **20,59** |
| `MO-OF1-ALB` — oficial albañil | 21,00 | 20,31 | 26,05 | **23,18** |
| `MO-OF1` — oficial general, misma aproximación | 21,00 | 20,31 | 26,05 | **23,18** |

### Extensión condicionada a otros oficios de obra

Se aplica provisionalmente **23,18 €/h** a `MO-OF1-MON` (montador), `MO-OF1-CARPM` (carpintería estructural), `MO-OF1-PISO` (solador), `MO-OF1-ALI` (alicatador) y `MO-OF1-CAB` (ferrallista), bajo el supuesto explícito de oficial de primera de oficio al que resulta aplicable el convenio de construcción, con el mismo escenario de cotización. El [convenio general de construcción](https://www.boe.es/diario_boe/txt.php?id=BOE-A-2023-19903) contempla actividades como carpintería de armar, solados y ferralla; esto **no demuestra** que cada empresa u oficio individual esté sujeto a dicho convenio. La [aclaración oficial](https://www.boe.es/diario_boe/txt.php?id=BOE-A-2026-10312) indica que los CNAE listados son estadísticos y no deciden por sí solos el convenio aplicable. Pueden corresponder otros convenios, como metal, además de otros tipos de AT/EP o complementos. Estos cinco recursos **siguen en revisión**, no son costes empresariales completos ni confirmados.

El punto medio se calcula con valores provinciales **sin redondear** y solo se redondea al céntimo al final. Los extremos se redondean al céntimo por separado: por ello el promedio de los valores ya redondeados puede diferir en un céntimo. El rango mínimo/máximo de cada fila en la matriz son estos dos escenarios, no un intervalo nacional garantizado.

## Cálculo reproducible y alcance del coste

Para cada provincia y categoría:

```text
base aproximada = retribución de tabla anual + aportación empresarial anual al plan
coste anual estimado = retribución + pensión
                     + base aproximada × 37,35 % cuotas empresariales
                     + base aproximada × 0,35 % Fundación Laboral de la Construcción
coste horario de convenio = coste anual estimado / jornada anual de convenio
referencia operativa = (coste Madrid + coste Barcelona) / 2
```

- Datos de salario y pensión: tablas provinciales de 2026 en [`espana_mano_obra_provincias_2026.csv`](espana_mano_obra_provincias_2026.csv). Se compara peón suelto/ordinario con el ayudante genérico; la clasificación exacta de la empresa puede ser otra. Oficial general se aproxima con el oficial de construcción, no con otros convenios.
- Cuotas: escenario de contrato indefinido ordinario sin bonificaciones, con contingencias comunes 23,60 %, MEI 0,75 %, desempleo 5,50 %, FOGASA 0,20 %, formación 0,60 % y AT/EP 6,70 % para la ocupación indicada en la tarifa. Fuentes: [Orden PJC/297/2026](https://www.boe.es/buscar/act.php?id=BOE-A-2026-7296) y [Real Decreto-ley 3/2026](https://www.boe.es/buscar/act.php?id=BOE-A-2026-2548). La [Fundación Laboral](https://www.fundacionlaboral.org/cuotas) publica una cuota del 0,35 % en 2026 para empresas incluidas en el convenio.
- **Aproximación explícita:** se usa la suma de retribución y pensión como proxy uniforme de las bases, sin bonificaciones ni deducciones. No sustituye el cálculo mensual de bases, topes, exclusiones o reducciones aplicables. La tabla puede incluir conceptos extrasalariales sujetos a reglas específicas. El cálculo evita tratar la aportación al plan como salario adicional y sumarla dos veces.
- El divisor es **1.736 horas de jornada de convenio**, no horas productivas medidas. No se descuentan de nuevo vacaciones. Las horas improductivas, absentismo y rendimientos se deben analizar con el APU para evitar duplicaciones.
- Incluye retribución de tabla, pensión y cuotas modeladas; **no incluye todos los costes empresariales** como prevención, formación adicional, seguro, estructura y otros gastos específicos no cuantificados. Deben imputarse una sola vez donde corresponda, no inventarse ni incorporarse de nuevo si ya están en el presupuesto. Tampoco incluye beneficio ni IVA.
- Las tablas 2026 de Barcelona son provisionales. Se usa una muestra intencionada de dos provincias a partes iguales; no es representativa estadísticamente ni garantiza el coste en cada zona.

Ejemplo `MO-AYU`, Madrid: (23.051,90 + 456,40) × (1 + 0,3735 + 0,0035) / 1.736 = **18,65 €/h**. El cálculo íntegro se ejecuta al generar la matriz mediante `tools/generar_matriz_precios_espana.py` y lee los importes trazados en el CSV provincial.

## Estado y publicación

Estos cuatro códigos se marcan **confirmado_referencia** en el registro: significa que se han aplicado y comprobado las fuentes y el método de punto medio acordado, **no que se haya verificado el coste efectivo de todas las empresas ni toda España**. Se mantienen como `derivado` en la matriz por ser estimaciones calculadas. Los cinco oficios adicionales descritos arriba permanecen en revisión pese a actualizarse su precio provisional. La actualización del archivo no altera automáticamente los precios propios de clientes ni la base de datos desplegada; se genera un SQL para la carga de referencias nacionales si corresponde.
