# España: auditoría de mano de obra y coste empresa (2026)

> **Actualización posterior:** se han aplicado cuatro referencias operativas por punto medio. Véase [decisión y cálculo](ESPANA_REFERENCIA_OPERATIVA_2026.md); este documento conserva la fotografía y conclusiones anteriores.

**Revisión:** 2026-11-06. Véase también el [contraste provincial posterior](ESPANA_CONTRASTE_PROVINCIAL_2026.md), con aportaciones al plan y corrección de las tablas de Barcelona 2025/2026. **Estado:** 17 recursos de mano de obra en revisión; ninguno confirmado como referencia nacional. Las cifras de este documento son análisis, no precios nuevos para producción.

## Criterio acordado

La mano de obra debe reflejar lo que cuesta a la empresa el empleado, no su salario neto ni una tarifa que ya incluya el beneficio de un autónomo. El coste por unidad de obra se obtiene con el coste por **hora productiva** y el rendimiento correspondiente de cada oficio. El rendimiento también debe verificarse: un precio horario correcto no valida por sí solo una partida.

La estimación debe incluir salario bruto anual y retribuciones aplicables, cuotas empresariales, aportación empresarial al plan de pensiones cuando proceda, y costes asociados al personal (prevención, formación, seguros, gestión, transporte y otros) según los datos de la empresa. Hay que dejar constancia de dónde se imputa cada gasto: no incluir dos veces una herramienta ya presupuestada como recurso, ni volver a sumar como gasto general una cantidad que ya esté en el coste horario. Las retribuciones en especie que correspondan deben incluirse en las bases de cotización, pero la aportación al plan de pensiones no se suma dos veces al coste.

Las horas ordinarias de convenio ya reflejan vacaciones y festivos del calendario; **no se vuelven a descontar**. Del tiempo efectivo de convenio a las horas productivas pueden quedar bajas, formación o tiempos no imputables, según las circunstancias reales y sin duplicar exclusiones. El divisor productivo debe sustentarse en datos y ser compatible con el rendimiento usado en el APU, para no cargar dos veces la improductividad.

## Cotización empresarial: escenario de comparación

Las normas de 2026 permiten construir este escenario para una persona en Régimen General y contrato indefinido ordinario, **sin bonificaciones**. Las bases de contingencias comunes y profesionales pueden diferir y deben obtenerse de la nómina, respetando mínimos, máximos y otras reglas; no es correcto aplicar sin más el porcentaje al salario neto o suponer que el bruto anual siempre coincide con ambas bases.

| Concepto a cargo de la empresa | Tipo de referencia | Base |
|---|---:|---|
| Contingencias comunes | 23,60 % | Base de contingencias comunes |
| MEI 2026 | 0,75 % | Base de contingencias comunes |
| Desempleo, contrato indefinido | 5,50 % | Base de contingencias profesionales |
| FOGASA | 0,20 % | Base de contingencias profesionales |
| Formación profesional | 0,60 % | Base de contingencias profesionales |
| Accidentes de trabajo y enfermedad profesional | **6,70 % para el personal de oficios en instalaciones y reparaciones en edificios, obras y trabajos de construcción en general** | Base de contingencias profesionales; comprobar encuadramiento y actividad para cada caso |

Fuentes: [Orden PJC/297/2026, artículos 4 y 33](https://www.boe.es/diario_boe/txt.php?id=BOE-A-2026-7296) y [Real Decreto-ley 3/2026, art. 3 y tarifa, cuadro II](https://www.boe.es/eli/es/rdl/2026/02/03/3/con). El 6,70 % no es el tipo universal de toda persona o empresa: depende de la actividad u ocupación aplicable. La suma **37,35 %** solo es aplicable en este escenario cuando ambas bases son iguales; no incluye pensión ni otros costes y no se puede asumir para otros contratos, bonificaciones o supuestos.

**Hallazgo:** el análisis antiguo de España usa un supuesto de 1,50 % de accidentes y una carga total de 32,15 %. Esa hipótesis no debe generalizarse a oficios de obra sujetos al 6,70 %. Tampoco permite concluir que todos los precios existentes estén mal: hay que reconstruir cada precio y sus bases.

## Ejemplo acotado: peón de Madrid, no valor nacional

El [convenio de Madrid, BOCM 31/12/2025, anexo VIII](https://www.bocm.es/boletin/CM_Orden_BOCM/2025/12/31/BOCM-20251231-1.PDF), publica 23.051,90 €/año para el peón suelto nivel XII y 25.103,23 €/año para oficial 1.ª nivel VIII. Son importes de tablas de Madrid, no costes empresariales ni valores nacionales. Para el peón, un **ejercicio aritmético incompleto**, no una nómina ni propuesta de precio, es:

- Salario anual de tabla: 23.051,90 €.
- **Hipótesis simplificada no verificada:** bases comunes y profesionales iguales a ese importe anual.
- Supuesto: contrato indefinido, sin bonificaciones, AT/EP 6,70 %. Cuotas empresariales hipotéticas: 23.051,90 × 37,35 % = 8.609,88 €.
- Resultado parcial: 31.661,78 €/año; dividido entre **1.736 horas de convenio**, 18,24 €/h. Este divisor no es una demostración de horas productivas reales.
- **Faltan** la aportación empresarial al plan de pensiones aplicable, sus efectos en bases si proceden, otros costes del empleado, complementos concretos y ajustes de productividad. No se conocen todos estos importes para una empresa real. Este ejemplo no es el coste total ni un suelo universal.

Nuestro `MO-AYU` usa 15 €/h como referencia nacional. La diferencia frente al ejemplo de Madrid **es una alerta, no una comparación equivalente ni motivo suficiente para sustituir el precio nacional**. Madrid es solo una zona y las bases efectivas, la categoría y el alcance de costes deben contrastarse.

El [BOE del convenio general](https://www.boe.es/diario_boe/txt.php?id=BOE-A-2025-25234) publica mínimos brutos nacionales por nivel, pero son remuneraciones, no el coste empresarial. También exige revisar las contribuciones sectoriales al plan de pensiones aplicables; su cálculo depende de las condiciones y tablas correspondientes.

## Revisión de los 17 recursos existentes

Los recursos de la matriz española están en EUR/h. La columna de uso cuenta descompuestos distintos del catálogo que referencian el código; no mide ventas ni importe monetario. Las cifras de la matriz **no se han confirmado** con esta ronda.

| Código | Oficio en catálogo | €/h matriz | Partidas que lo usan | Prioridad y pendiente |
|---|---|---:|---:|---|
| `MO-AYU` | Ayudante | 15 | 2922 | Reconstruir categoría peón/ayudante y costes completos por provincias. |
| `MO-OF1-ALB` | Albañil | 21 | 881 | Contrastar nivel, nómina y costes empresariales provinciales. |
| `MO-AYU-ESP` | Ayudante especializado | 18 | 409 | Precio derivado; verificar clasificación y costes propios. |
| `MO-OF1-ELE` | Electricista | 24 | 405 | Verificar convenio aplicable y complemento de especialidad. |
| `MO-OF1-MON` | Montador de prefabricados interiores | 21 | 319 | Derivado del oficial general; contrastar convenio y categoría. |
| `MO-OF1-PLO` | Fontanero | 23 | 218 | Confirmar convenio, categoría y costes de contratación. |
| `MO-OF1-CARPM` | Carpintero de madera estructural | 21 | 209 | Derivado; comprobar convenio y coste real. |
| `MO-OF1-PIN` | Pintor | 20 | 159 | Comprobar convenio aplicable y costes. |
| `MO-OF1-SOLD` | Soldador | 25 | 127 | Comprobar categoría, convenio y costes. |
| `MO-OF1-AC` | Refrigeración y climatización | 21 | 94 | Derivado; comprobar convenio y especialidad. |
| `MO-OF1-VIDR` | Vidriero | 21 | 92 | Derivado; comprobar convenio y especialidad. |
| `MO-OF1-PISO` | Solador | 22 | 63 | Comprobar categoría, convenio y costes. |
| `MO-OF1-ALI` | Alicatador | 22 | 53 | Comprobar categoría, convenio y costes. |
| `MO-OF1-CAB` | Armador de acero | 21 | 48 | Derivado; comprobar convenio de ferralla si aplica. |
| `MO-OF1-CARP` | Encofrador | 21 | 39 | Derivado; comprobar categoría y convenio. |
| `MO-OF1-JARD` | Jardinero | 21 | 24 | Derivado; comprobar convenio aplicable. |
| `MO-OF1` | Oficial general | 21 | 0 | Aunque no aparezca directamente en los descompuestos, revisar su uso como ancla de recursos derivados. |

El contraste de tipos generales se ha registrado para los 17; no se ha comprobado individualmente que el mismo convenio o tipo de accidentes se aplique a cada oficio. No se debe asignar de forma automática una tabla de construcción a electricistas, jardineros u otras especialidades sin verificar la actividad y el convenio.

## Herramienta de cálculo para la auditoría

`tools/coste_empresa_espana_auditoria.py` calcula por separado cuotas sobre ambas bases y añade pensión y otros costes introducidos por el operador. Requiere todos los datos, no obtiene salarios ni aplica cambios al catálogo. Su escenario es indefinido ordinario 2026 sin bonificaciones; no sustituye una nómina ni verifica automáticamente topes, encuadramiento o condiciones.

Ejemplo **exclusivamente aritmético e incompleto**, con pensión y otros costes puestos a cero para reproducir el ejercicio anterior:

```sh
python tools/coste_empresa_espana_auditoria.py \
  --salario-anual 23051.90 --base-comun-anual 23051.90 \
  --base-profesional-anual 23051.90 --pension-empresa 0 \
  --otros-costes 0 --horas-productivas 1736 --porcentaje-at-ep 6.7
```

Antes de adoptar cualquier cifra de coste total para CotizaT, hay que sustituir esas hipótesis por bases y gastos acreditados, verificar la imputación y representatividad territorial, y comprobar el impacto en partidas, márgenes y artefactos públicos. **No se ha actualizado la matriz, ni la base de datos, ni los precios de clientes.**
