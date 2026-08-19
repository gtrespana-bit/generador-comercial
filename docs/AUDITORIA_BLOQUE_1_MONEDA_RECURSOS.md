# Auditoría Bloque 1 — Mapa técnico de moneda, importes y recursos

**Fecha:** 2026-08-19  
**Estado:** completada como auditoría; decisiones de diseño pendientes  
**Rama:** `arena/01a01aa4-generador-comercial`

## Resumen ejecutivo

El proyecto ya tiene una primera capa de moneda y conversión, pero está diseñada principalmente como una conversión de catálogo USD hacia moneda local. Todavía no existe un modelo de precios de recursos por mercado. Además, hay puntos donde la moneda se utiliza solo para formatear, puntos donde se convierte y puntos donde aparentemente se persiste el resultado convertido. Es necesario resolver esto antes de construir el modelo definitivo.

## 1. Fuentes actuales de moneda

### País y configuración de organización

- `app/paises.py`: defaults por país, incluyendo `moneda` y `moneda_local`.
- `app/models.py`, `Configuracion`:
  - `moneda_default`
  - `tasa_cambio`
  - `fecha_tasa`
  - `tarifa_hora_media`
- `app/routers/auth.py`: inicializa moneda y tasa según país.
- `app/routers/configuracion.py`: guarda moneda/tasa y permite consultar tasa automática.

### Presupuesto

`Presupuesto` contiene actualmente:

- `moneda`
- `tipo_cambio`
- `fecha_tipo_cambio`
- importes y porcentajes de cálculo

Esto permite conservar parcialmente el contexto de un presupuesto, pero no guarda todavía una moneda base explícita, fuente de tasa ni snapshot de precios de recursos.

### Versiones y enlaces

- `PresupuestoVersion` conserva `total`, pero no se observa en el modelo un contexto monetario completo separado.
- `EnlacePropuesta` tiene `total` y `moneda`.

### Proyectos y pagos

- `Pago` tiene `importe` y `moneda`.
- `Proyecto` y `CambioAlcance` almacenan importes derivados, pero el proyecto no parece tener un contexto monetario contractual propio independiente del presupuesto.
- `CambioAlcanceItem` tiene precio unitario, pero no contexto de moneda individual.

### Catálogo y recursos

- `Partida` tiene `precio_unitario` y costes internos.
- `Producto` tiene precio de venta y compra.
- `Recurso` tiene `precio`.
- No existe todavía una tabla/modelo de precio por país, vigencia, fuente o proveedor para un mismo recurso.

## 2. Motor actual de conversión

`app/services/tasa.py` define una conversión unidireccional conceptual:

```text
precio_local = precio_usd × tasa
```

También define tasas sugeridas y consulta `open.er-api.com`.

La función `factor_conversion_local()` y el índice del catálogo convierten precio y costes con el mismo factor, lo que evita algunas mezclas dentro de una misma carga del editor.

### Riesgos detectados

1. El servicio asume que el valor de origen es USD.
2. No existe una moneda de origen explícita en los modelos de catálogo, partidas, productos o recursos.
3. No existe una identidad de tasa con fuente y vigencia completa.
4. Se usa `float` en gran parte de los importes persistidos.
5. La tasa automática de una API genérica no equivale necesariamente a la tasa comercial u oficial del mercado.
6. La conversión actual no resuelve que el precio económico del recurso sea diferente en cada país.

## 3. Hallazgo crítico: posible conversión persistente del catálogo

En `app/routers/partidas.py`, alrededor de las líneas 241-252, hay lógica que convierte y asigna directamente a objetos `Partida`:

```python
_p.precio_unitario = tasa_convertir_precio(_p.precio_unitario or 0, _factor)
_p.coste_materiales = tasa_convertir_precio(_p.coste_materiales or 0, _factor)
_p.coste_mano_obra = tasa_convertir_precio(_p.coste_mano_obra or 0, _factor)
```

Esto es peligroso si esos objetos son registros del catálogo y la sesión se confirma, porque una visita o importación en moneda local podría transformar permanentemente el valor base. Si posteriormente se vuelve a aplicar la conversión, puede producirse:

```text
USD → COP → COP convertido de nuevo como si fuera USD
```

Este punto debe verificarse con una prueba de base de datos antes de modificar el modelo.

## 4. Hallazgo crítico: formateo no equivale a conversión

Hay pantallas que utilizan correctamente filtros como `money(p.moneda)`, pero eso solo es correcto si el número ya está en la moneda del presupuesto.

Ejemplos sensibles:

- `app/templates/budgets/detail.html`
- `app/templates/budgets/decomposition.html`
- `app/templates/budgets/version.html`
- `app/templates/partidas/*.html`

La vista de detalle contiene además formatos directos como:

```jinja
{{ part.precio_unitario | num }} {{ p.moneda | simbolo }}
```

Esto muestra el símbolo/código asociado, pero no hace conversión numérica.

## 5. Hallazgo crítico: salidas con formatos fijos o símbolos históricos

### PDF

`app/services/pdf.py` contiene lógica fija o histórica para:

- `$` y `Bs` en símbolos auxiliares.
- Referencias `BCV`.
- Equivalentes en VES.
- Textos `1 USD = ... Bs`.

Esto no puede seguir siendo la lógica general de LatAm. Venezuela debe poder funcionar en USD sin mostrar VES/Bs, y un presupuesto COP/MXN/PEN debe mostrar su código ISO.

### PDF interactivo

`app/services/pdf_interactivo.py` conserva un mapa de símbolos limitado a USD/Bs.

### Excel

`app/services/excel_export.py` define:

```python
_CURRENCY_FMT = '#,##0.00 "USD"'
```

Aunque algunas hojas incluyen una celda `Moneda`, el formato de varias cifras puede continuar mostrando USD. También aparece el texto histórico `Tasa de cambio (Bs/USD)`.

Este es un riesgo directo de inconsistencia entre pantalla, PDF y Excel.

## 6. Hallazgo: datos financieros de dominios distintos

Hay varios importes en USD que son correctos por pertenecer a Cotizat y no a los presupuestos:

- licencias;
- compras de planes;
- pagos de la plataforma;
- recibos de licencia;
- panel administrativo.

No deben convertirse con la moneda del país de la organización del cliente. Deben permanecer en USD como moneda comercial de Cotizat.

También existen compras y recursos internos con `moneda="USD"` por defecto. Debe decidirse si esos registros pertenecen al dominio comercial de Cotizat o al dominio de costes del presupuesto.

## 7. Mapa de cálculo

El cálculo principal está en `app/services/calculations.py` y utiliza importes numéricos del presupuesto/partida:

- importe de partida;
- costes de obra;
- productos;
- descuentos;
- costes adicionales;
- impuesto;
- total;
- coste interno;
- margen y beneficio.

El motor mantiene coherencia aritmética si todos los campos recibidos están en la misma unidad monetaria, pero no verifica todavía que todos tengan moneda compatible.

El editor JavaScript también recalcula precios, costes y márgenes, especialmente en:

- `app/static/js/editor/main.js`
- `app/static/js/editor/partida.js`
- `app/static/js/editor/totales.js`

Necesitará un contexto monetario explícito y una regla de origen para no convertir dos veces.

## 8. Mapa de importación/exportación

- `app/services/importer.py` elimina `$` y `Bs` durante la lectura de números.
- Las importaciones no parecen tener todavía un contrato uniforme para declarar moneda de origen.
- Los Excel de catálogo, partidas, productos y recursos deben declarar moneda y mercado o pedirlos durante la importación.
- La exportación debe escribir el código ISO de cada conjunto de importes y aplicar un formato dinámico.

## 9. Recursos: conclusión de la auditoría

El modelo actual `Recurso(precio)` no es suficiente para precios por mercado. Se necesita separar:

```text
Recurso
  identidad común: código, nombre, unidad, categoría

PrecioRecurso
  recurso_id
  país/mercado
  moneda
  precio
  fecha_vigencia
  fecha_actualización
  fuente
  proveedor opcional
  nivel de confianza
  organización opcional
```

La misma separación deberá estudiarse para:

- mano de obra;
- equipos;
- transporte;
- productos comerciales;
- rendimientos si varían por mercado.

La jerarquía propuesta para resolver un precio es:

1. organización;
2. país/mercado;
3. regional;
4. base de respaldo;
5. aviso de dato no local.

## 10. Decisiones confirmadas para el Bloque 2

Estas decisiones fueron confirmadas por el usuario el 2026-08-19:

### Decisión A — Moneda de almacenamiento y precios por mercado

- El catálogo común puede conservar USD como referencia/base técnica.
- Cada país tendrá precios independientes.
- Un precio actualizado en Colombia no modifica el precio de Perú, México ni Venezuela.
- Ejemplo válido:

```text
Cemento — Colombia: 32.000 COP/saco
Cemento — Perú: 28,00 PEN/saco
```

- La moneda del precio debe ser explícita.
- El modelo debe permitir actualizar un mercado sin alterar otro.

### Decisión B — Cambio de moneda en borrador

- La aplicación pedirá confirmación.
- Solo convertirá los valores si el cliente confirma.
- No se hará una conversión silenciosa.
- Para documentos enviados o aprobados se aplicará la política de congelación/versionado definida en la hoja de ruta.

### Decisión C — Tasa de cambio

- La tasa automática será una sugerencia.
- El usuario podrá revisarla y confirmarla.
- El presupuesto guardará la tasa confirmada.
- Al enviarse o aprobarse, la tasa quedará congelada.

### Decisión D — Granularidad inicial

- Los precios se gestionarán inicialmente a nivel nacional.
- La estructura debe permitir una futura ampliación regional.
- Cada empresa podrá modificar manualmente los datos para reflejar una cifra exacta de su zona o proveedor.

### Decisión E — Moneda de pagos

- Los pagos de un proyecto se mantendrán en la moneda contractual del proyecto.
- La forma real en que la empresa cobre internamente queda fuera del alcance inicial.
- El proyecto venezolano utilizará USD, conforme a la decisión específica de Venezuela, aunque la regla general sea mantener la moneda contractual definida por el presupuesto.

## Conclusión

El Bloque 1 confirma que la iniciativa es viable, pero también confirma que no conviene empezar por cambios visuales aislados. Primero hay que resolver el origen de los importes, el riesgo de conversión persistente del catálogo y el modelo de precios por mercado.
