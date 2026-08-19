# Decisiones de producto — Moneda y recursos por país

**Estado:** acordado para la siguiente etapa de trabajo  
**Fecha:** 2026-08-19

## Alcance inicial

El producto se prepara para LatAm, pero la primera cobertura operativa se limita a los países actualmente activos en el producto. No se debe confundir la lista futura de países soportados con los mercados de lanzamiento.

## Moneda de Cotizat

La moneda comercial de Cotizat (planes, licencias y cobros de la plataforma) es **USD**. Esta moneda es independiente de la moneda de los presupuestos que genera cada cliente.

## Moneda de los presupuestos

- El país de la organización propone una moneda por defecto.
- El usuario puede cambiarla desde configuración y, cuando corresponda, desde el presupuesto.
- El presupuesto debe mostrar un único código ISO 4217 de forma consistente en toda la aplicación.
- Se utilizará el código ISO, no símbolos ambiguos como `$` sin contexto.
- Todos los precios, costes, beneficios, márgenes, cargos, descuentos, impuestos, retenciones, pagos, saldos, PDFs, Excel y enlaces públicos deben utilizar la misma moneda contractual del presupuesto.
- Nunca se debe convertir un valor ya convertido.
- La tasa utilizada por un presupuesto aprobado o enviado debe quedar congelada junto con su fecha y contexto monetario.

## Regla para Venezuela

Venezuela utilizará **USD** por defecto y no se mostrará VES/Bs en los presupuestos. VES/Bs puede conservarse únicamente como compatibilidad técnica de datos históricos si fuese necesario, pero no debe aparecer como moneda operativa ni como opción visible para los presupuestos venezolanos en esta fase.

## Países dolarizados

Los países cuya operación del producto sea en USD utilizarán USD directamente, sin una conversión ficticia a una moneda local. La configuración de país propone el valor, pero el usuario conserva la posibilidad de elegir otra moneda admitida si el producto lo permite.

## Moneda base y conversión

El catálogo regional puede conservar una moneda base interna para mantenimiento y actualización. La moneda base nunca debe confundirse con la moneda visible del presupuesto.

Cada presupuesto debe conservar, como mínimo:

- moneda contractual;
- moneda base de origen, si es distinta;
- tasa aplicada;
- fecha de la tasa;
- fuente o método de la tasa, cuando exista.

## Recursos y precios por país

Los recursos no deben ser globales únicamente por nombre. El mismo recurso puede tener precios muy distintos según el país:

- cemento;
- acero;
- arena y agregados;
- materiales acabados;
- transporte;
- mano de obra;
- equipos y alquileres;
- productos comerciales;
- rendimientos y costes asociados.

Por tanto, el catálogo debe separar:

1. **Identidad del recurso:** código, nombre, unidad, categoría y equivalencias.
2. **Precio por mercado:** país, moneda, precio, fecha de vigencia y fuente.
3. **Datos de mano de obra:** categoría, unidad, tarifa, productividad y país.
4. **Proveedor o fuente opcional:** para trazabilidad y actualización.
5. **Historial:** los cambios futuros no deben alterar presupuestos históricos.

El precio de una partida debe calcularse usando los recursos del mercado de la organización o del presupuesto, no usando automáticamente un precio regional genérico.

## Jerarquía recomendada de precios

1. Precio específico de la organización o empresa.
2. Precio específico del país/mercado.
3. Precio regional de respaldo.
4. Precio base USD únicamente si no existe otra referencia.

La aplicación debe informar cuando utiliza un precio de respaldo o desactualizado; no debe presentar como local un precio que en realidad es regional o genérico.

## Regla de cálculo

Todos los componentes de una partida deben estar en la misma moneda antes de calcular:

- coste directo;
- precio de venta;
- margen;
- beneficio;
- totales del presupuesto;
- cambios de alcance;
- total contratado;
- pagos y saldo.

La conversión monetaria y la localización de recursos son problemas relacionados, pero distintos:

- la conversión cambia la unidad monetaria;
- la localización cambia el valor económico real del recurso en cada mercado.

No se debe resolver la diferencia de precios de Colombia, Perú o México aplicando únicamente una tasa USD/moneda local.

## Comentario de diseño

La moneda debe poder cambiarse rápidamente desde la interfaz, pero cambiar la moneda de visualización no debe modificar silenciosamente la moneda contractual de presupuestos aprobados, proyectos o documentos enviados. Para estos documentos se debe crear una nueva versión o una conversión explícita con confirmación.

## Orden de trabajo acordado

1. Modelo monetario unificado.
2. Moneda visible en toda la aplicación y exportaciones.
3. Conversión única y sin doble aplicación.
4. Recursos y precios por país.
5. Recalculo de partidas, costes, beneficios y márgenes.
6. Congelación monetaria de presupuestos aprobados.
7. Integración segura con proyectos, cambios de alcance y pagos.
8. Pruebas de coherencia por país y moneda.
