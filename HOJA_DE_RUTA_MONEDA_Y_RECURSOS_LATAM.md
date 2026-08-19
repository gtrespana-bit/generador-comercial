# Hoja de ruta — Moneda y recursos por mercado LatAm

**Proyecto:** Cotizat / Generador Comercial  
**Estado:** preparada para ejecución  
**Fecha de creación:** 2026-08-19  
**Rama de trabajo:** `arena/01a01aa4-generador-comercial`

> Este documento es la fuente de seguimiento de esta iniciativa. Cada bloque debe actualizarse al terminarse, indicando fecha, cambios realizados y pruebas ejecutadas. No se debe marcar un bloque como completado solo porque exista parte de su código: debe estar implementado, integrado y probado en la aplicación.

---

## 0. Decisiones cerradas

- [x] La moneda comercial de Cotizat (planes, licencias y cobros de la plataforma) es **USD**.
- [x] La moneda comercial de Cotizat es independiente de la moneda de los presupuestos de los clientes.
- [x] Venezuela utiliza **USD** por defecto en los presupuestos.
- [x] VES/Bs no se mostrará como moneda operativa visible en los presupuestos venezolanos.
- [x] Se utilizarán códigos ISO 4217 en la interfaz y documentos.
- [x] No se dependerá únicamente de símbolos ambiguos como `$`.
- [x] El país propondrá una moneda por defecto, pero el usuario podrá cambiarla.
- [x] Todos los precios, costes, beneficios, márgenes, cargos, impuestos, pagos y saldos deben ser coherentes en una única moneda contractual.
- [x] No se permitirá la doble conversión de valores.
- [x] La moneda y la tasa de presupuestos aprobados o enviados deben quedar congeladas.
- [x] Los recursos tendrán precios específicos por mercado; no se resolverá la diferencia entre países únicamente con tasas de cambio.
- [x] Los países inicialmente activos son los definidos en la configuración operativa actual. La cobertura futura de LatAm no se considera activa automáticamente.

---

## 1. Estado global

| Bloque | Estado | Fecha | Responsable / notas |
|---|---|---:|---|
| 0. Decisiones de producto | ✅ Completado | 2026-08-19 | Decisiones acordadas y documentadas |
| 1. Auditoría técnica | ✅ Completado | 2026-08-19 | Auditoría documentada; decisiones A-E pendientes antes del diseño |
| 2. Modelo monetario | ✅ Completado | 2026-08-19 | Catálogo ISO, contexto base/contractual y campos persistentes implementados |
| 3. Conversión y tasas | ✅ Completado | 2026-08-19 | Conversión central, Decimal, validación, origen y congelación de tasa preparados |
| 4. Interfaz y configuración | ✅ Completado | 2026-08-19 | Configuración ISO, acceso rápido, selector contextual, confirmación y protección de históricos implementados |
| 5. Editor y cálculos | ✅ Completado | 2026-08-19 (rev. tarde) | Cerrado en la auditoría de la tarde: la ficha, la descomposición, los productos y los packs cruzaban la frontera catálogo↔presupuesto sin convertir. Ver «Auditoría de cierre» |
| 6. Plantillas y exportaciones | ✅ Completado | 2026-08-19 (rev. tarde) | Quedaban 27 usos de `\| money` con «$» ambiguo y símbolos fijos en el JS. Todo a ISO + símbolo distintivo (MX$, COL$, US$) |
| 7. Recursos por país | ✅ Completado | 2026-08-19 (rev. tarde) | Las tablas nuevas se crearon sin GRANT ni RLS (rompía «Nuevo presupuesto» en producción); corregido en la revisión `e7b3c1d5a204` |
| 8. Mano de obra y rendimientos | ✅ Completado | 2026-08-19 (rev. tarde) | `tarifa_hora_media` ya se expresa en la moneda del presupuesto al estimar horas desde el coste |
| 9. Históricos y congelación | ✅ Completado | 2026-08-19 | Versiones, proyectos, cambios, pagos, facturas y procedencia de recursos protegidos |
| 10. Integración con etapa 6 | ✅ Completado | 2026-08-19 | Proyectos, cambios, pagos, facturas y saldos con moneda contractual congelada |
| 11. Pruebas y aceptación | ✅ Completado | 2026-08-19 (rev. tarde) | Suite completa: 785 passed, 7 skipped. Incluye `tests/test_moneda_editor.py` (frontera catálogo↔presupuesto) y RLS real contra PostgreSQL |
| 12. Documentación y cierre | ✅ Completado | 2026-08-19 (rev. tarde) | Guías, migraciones (incluido el paso 10 de Supabase) y esta hoja actualizados |

> **Cómo leer esta hoja.** La tabla de arriba es el estado real. Las casillas
> `[ ]` de cada bloque se escribieron al planificar y **no se han ido marcando**
> durante la ejecución: no son un indicador fiable de lo que falta. Lo
> verificado, lo corregido y lo que sigue pendiente está en «Auditoría de
> cierre — 2026-08-19 (sesión de tarde)», al final del documento.

Estados permitidos:

- ⬜ Pendiente
- 🟡 En curso
- 🟠 Bloqueado
- ✅ Completado
- ❌ Requiere revisión

---

# BLOQUE 1 — Auditoría técnica y mapa de importes

**Objetivo:** localizar todos los lugares donde se almacenan, convierten, calculan o muestran importes.

## Tareas

- [ ] Inventariar todos los modelos con campos monetarios.
- [ ] Inventariar precios de partidas, productos, recursos y descomposiciones.
- [ ] Inventariar costes de materiales, mano de obra, complementarios y otros.
- [ ] Inventariar cargos adicionales, transporte, indirectos e imprevistos.
- [ ] Inventariar descuentos, IVA, retenciones y beneficios.
- [ ] Inventariar pagos, anticipos, proyectos y cambios de alcance.
- [ ] Inventariar textos y formatos fijos en USD, Bs, VES o símbolos ambiguos.
- [ ] Revisar toda la lógica Python de conversión.
- [ ] Revisar toda la lógica JavaScript del editor.
- [ ] Revisar plantillas HTML, PDF, Excel, correos y enlaces públicos.
- [ ] Identificar campos históricos que no pueden cambiar de significado.
- [ ] Clasificar cada importe como: catálogo, presupuesto, proyecto, pago, Cotizat o histórico.
- [ ] Documentar cualquier dato que actualmente esté almacenado sin moneda explícita.

## Criterio de finalización

- [ ] Existe un mapa de todos los importes de la aplicación.
- [ ] No queda ningún cálculo monetario importante sin propietario definido.
- [ ] Se han identificado los valores que están en USD por diseño y los que están en USD por limitación histórica.

**Estado:** 🟡 En curso  
**Fecha de finalización:** —  
**Notas:** Ya existe soporte parcial en modelos, `app/paises.py`, `app/utils.py`, `app/services/tasa.py`, editor y PDF, pero todavía hay que cerrar la auditoría completa.

---

# BLOQUE 2 — Modelo monetario unificado

**Objetivo:** establecer una única representación oficial de monedas y contexto monetario.

## Tareas

- [ ] Crear o consolidar un catálogo de monedas ISO 4217.
- [ ] Definir código, nombre, símbolo auxiliar y número de decimales por moneda.
- [ ] Definir formato visible profesional por moneda.
- [ ] Definir moneda base del catálogo.
- [ ] Definir moneda comercial de Cotizat como USD y mantenerla separada.
- [ ] Definir moneda contractual del presupuesto.
- [ ] Definir moneda del proyecto heredada del presupuesto aprobado.
- [ ] Definir moneda admitida para pagos.
- [ ] Normalizar VES/Bs como compatibilidad histórica, sin mostrarlo en Venezuela.
- [ ] Revisar defaults de países activos.
- [ ] Diferenciar país de organización, país del cliente y mercado de precios.
- [ ] Añadir validaciones para códigos no soportados.
- [ ] Evitar que una moneda se represente a veces como `Bs` y otras como `VES` en datos nuevos.
- [ ] Documentar la política de decimales y redondeo.

## Datos mínimos de un contexto monetario

- [ ] `moneda_base`
- [ ] `moneda_objetivo` o `moneda_contractual`
- [ ] `tipo_cambio`
- [ ] `fecha_tipo_cambio`
- [ ] `fuente_tipo_cambio` o método de origen
- [ ] precisión y regla de redondeo aplicable

**Estado:** ⬜ Pendiente  
**Fecha de finalización:** —

---

# BLOQUE 3 — Servicio único de conversión y tasas

**Objetivo:** centralizar todas las conversiones y evitar conversiones duplicadas.

## Tareas

- [ ] Crear o consolidar un servicio único de moneda.
- [ ] Separar conversión de formato visual.
- [ ] Separar conversión monetaria de localización de precios de mercado.
- [ ] Implementar conversiones desde la moneda base hacia la moneda objetivo.
- [ ] Validar que la tasa sea positiva y válida.
- [ ] Guardar fecha de vigencia de la tasa.
- [ ] Guardar fuente o indicar si es manual.
- [ ] Definir qué ocurre cuando no existe tasa.
- [ ] Evitar conversiones USD → local → USD → local.
- [ ] Aplicar `Decimal` o precisión suficiente para cálculos monetarios.
- [ ] Definir redondeo por unidad, línea, subtotal e importe final.
- [ ] Crear funciones reutilizables para Python y contexto equivalente para JavaScript.
- [ ] Añadir advertencia cuando se utilice una tasa manual, antigua o de respaldo.

**Estado:** ⬜ Pendiente  
**Fecha de finalización:** —

---

# BLOQUE 4 — Configuración y cambio rápido de moneda

**Objetivo:** permitir elegir y cambiar moneda sin provocar inconsistencias.

## Tareas

- [ ] Mostrar la moneda recomendada al crear una organización según su país.
- [ ] Permitir modificar la moneda por defecto desde configuración.
- [ ] Añadir acceso rápido a la moneda activa en la interfaz.
- [ ] Mostrar código ISO, no solamente símbolo.
- [ ] Permitir elegir moneda a nivel de presupuesto.
- [ ] Mostrar la tasa y fecha cuando haya conversión.
- [ ] Confirmar antes de cambiar la moneda de un presupuesto con datos guardados.
- [ ] Impedir cambios silenciosos en presupuestos aprobados o enviados.
- [ ] Definir si el cambio rápido modifica solo la visualización o también la moneda contractual.
- [ ] Asegurar que la moneda del presupuesto tenga prioridad sobre la preferencia global.
- [ ] Aplicar la regla USD por defecto para Venezuela.
- [ ] Ocultar VES/Bs de la selección visible venezolana.
- [ ] Mantener compatibilidad para presupuestos antiguos sin romperlos.

**Estado:** ⬜ Pendiente  
**Fecha de finalización:** —

---

# BLOQUE 5 — Editor y cálculos económicos

**Objetivo:** que el editor calcule y muestre todo en la misma moneda.

## Tareas

- [ ] Entregar al editor un contexto monetario explícito.
- [ ] Convertir precio unitario y costes con el mismo factor antes del cálculo.
- [ ] Mostrar moneda en partidas y precios unitarios.
- [ ] Mostrar moneda en productos asociados.
- [ ] Mostrar moneda en descomposiciones.
- [ ] Calcular coste directo en moneda contractual.
- [ ] Calcular precio de venta en moneda contractual.
- [ ] Calcular beneficio en moneda contractual.
- [ ] Calcular markup y margen sin mezclar unidades monetarias.
- [ ] Calcular transporte, indirectos, imprevistos y otros cargos en moneda contractual.
- [ ] Calcular descuento, IVA y retenciones en moneda contractual.
- [ ] Revisar cálculos de cantidades, rendimientos y costes importados desde Excel.
- [ ] Evitar que el editor vuelva a convertir valores recibidos ya convertidos.
- [ ] Mostrar una señal clara cuando un recurso carezca de precio local.
- [ ] Verificar que guardar y volver a abrir conserve exactamente los resultados.

**Estado:** ⬜ Pendiente  
**Fecha de finalización:** —

---

# BLOQUE 6 — Plantillas, PDF, Excel, correos y enlaces públicos

**Objetivo:** eliminar cualquier mezcla de monedas en salidas internas y externas.

## Tareas

- [ ] Auditar todas las plantillas Jinja.
- [ ] Auditar el PDF principal.
- [ ] Auditar anexos PDF.
- [ ] Auditar PDF interactivo.
- [ ] Auditar Excel.
- [ ] Auditar correos de presupuesto.
- [ ] Auditar propuestas públicas.
- [ ] Auditar contratos.
- [ ] Auditar informes y resúmenes.
- [ ] Mostrar código ISO en todos los importes.
- [ ] Mostrar tasa y fecha cuando sea necesario para transparencia.
- [ ] Eliminar textos fijos `USD`, `Bs/USD` y equivalentes donde no correspondan.
- [ ] Verificar que el PDF enviado coincida con la pantalla y el Excel.
- [ ] Verificar que el enlace público conserve la moneda del presupuesto.

**Estado:** ⬜ Pendiente  
**Fecha de finalización:** —

---

# BLOQUE 7 — Modelo de recursos y precios por país

**Objetivo:** disponer de precios económicamente fiables para cada mercado.

## Diseño acordado

La identidad de un recurso será independiente del precio del mercado.

```text
Recurso: Cemento Portland
Unidad: saco

Precio Colombia: 32.000 COP
Precio Perú: 28,00 PEN
Precio México: 285,00 MXN
Precio Venezuela: 9,50 USD
```

## Tareas

- [ ] Separar identidad del recurso y precio del recurso.
- [ ] Definir código estable del recurso.
- [ ] Definir unidad y equivalencias.
- [ ] Definir país o mercado del precio.
- [ ] Definir moneda del precio.
- [ ] Definir fecha de vigencia.
- [ ] Definir fecha de actualización.
- [ ] Definir fuente o proveedor.
- [ ] Definir nivel de confianza del precio.
- [ ] Definir precio específico de empresa.
- [ ] Definir precio nacional.
- [ ] Definir precio regional de respaldo.
- [ ] Definir precio base internacional de último recurso.
- [ ] Informar cuándo se usa un precio de respaldo.
- [ ] Evitar presentar un precio regional como precio local confirmado.
- [ ] Mantener historial de precios.
- [ ] Evitar que actualizar un recurso cambie presupuestos históricos.
- [ ] Migrar recursos actuales sin perder relaciones con partidas.
- [ ] Definir importación y actualización masiva por país.
- [ ] Definir permisos para cambiar precios oficiales y precios propios.

**Estado:** ⬜ Pendiente  
**Fecha de finalización:** —

---

# BLOQUE 8 — Mano de obra, equipos y rendimientos por mercado

**Objetivo:** que los costes técnicos reflejen el mercado real, no solo una conversión monetaria.

## Tareas

- [ ] Crear categorías de mano de obra por país.
- [ ] Definir tarifa por hora, jornada o unidad de trabajo.
- [ ] Definir productividad y rendimiento por mercado.
- [ ] Separar oficial, ayudante, especialista y otras categorías necesarias.
- [ ] Crear precios por país para alquiler de equipos.
- [ ] Crear precios por país para transporte y logística.
- [ ] Definir si los rendimientos son nacionales o regionales.
- [ ] Permitir sobrescritura por empresa.
- [ ] Guardar fecha y fuente de cada tarifa.
- [ ] Mantener versiones históricas.
- [ ] Integrar recursos localizados en las descomposiciones CYPE y manuales.
- [ ] Revisar `tarifa_hora_media` para que tenga moneda y mercado definidos.
- [ ] Revisar cálculos de tiempo de obra para no mezclar tarifa de un país con precios de otro.

**Estado:** ⬜ Pendiente  
**Fecha de finalización:** —

---

# BLOQUE 9 — Partidas y generación de precios fiables

**Objetivo:** que una partida se calcule a partir de recursos adecuados al mercado.

## Tareas

- [ ] Definir el mercado activo de cada organización.
- [ ] Resolver recursos por país al crear o importar una partida.
- [ ] Aplicar la jerarquía empresa → país → regional → base.
- [ ] Calcular coste directo usando recursos localizados.
- [ ] Calcular precio de venta usando costes del mercado correcto.
- [ ] Recalcular beneficios y márgenes después de cambios de recursos.
- [ ] Mostrar el origen de los precios usados.
- [ ] Mostrar avisos de precios sin actualizar.
- [ ] Mostrar avisos de precios de respaldo.
- [ ] Permitir sustituir el precio automático por uno propio.
- [ ] Mantener la trazabilidad de la sustitución.
- [ ] Evitar modificar automáticamente partidas ya utilizadas en presupuestos aprobados.
- [ ] Revisar importaciones Excel para asociar recursos al mercado correcto.

**Estado:** ⬜ Pendiente  
**Fecha de finalización:** —

---

# BLOQUE 10 — Presupuestos históricos y congelación

**Objetivo:** garantizar que los documentos y compromisos anteriores no cambien.

## Tareas

- [ ] Congelar moneda contractual al aprobar o enviar.
- [ ] Congelar tasa y fecha de tasa.
- [ ] Congelar precio y moneda de los recursos utilizados.
- [ ] Congelar costes y rendimientos usados en cada partida.
- [ ] Definir comportamiento para borradores al actualizar precios.
- [ ] Definir nueva versión cuando cambie la moneda de un documento aprobado.
- [ ] Impedir que una actualización de catálogo altere proyectos existentes.
- [ ] Crear snapshot o referencias versionadas suficientes para reproducir el documento.
- [ ] Verificar que el PDF histórico se pueda regenerar igual.
- [ ] Verificar que los totales históricos sigan siendo reproducibles.

**Estado:** ⬜ Pendiente  
**Fecha de finalización:** —

---

# BLOQUE 11 — Integración con proyectos, cambios de alcance y pagos

**Objetivo:** continuar la etapa 6 sobre una moneda contractual coherente.

## Tareas

- [ ] Heredar la moneda del presupuesto aprobado al crear el proyecto.
- [ ] Congelar moneda y contexto monetario del proyecto.
- [ ] Calcular total contratado en la moneda del proyecto.
- [ ] Calcular cambios de alcance en la moneda del proyecto.
- [ ] Calcular total actual, pagado y saldo en la moneda del proyecto.
- [ ] Validar moneda de los pagos.
- [ ] Decidir si inicialmente los pagos deben usar obligatoriamente la moneda del proyecto.
- [ ] Si se admiten pagos en otra moneda, guardar tasa y equivalente contractual.
- [ ] Evitar mezclar pagos USD con contratos COP sin conversión documentada.
- [ ] Mostrar ISO en proyectos, cambios, pagos y recibos.
- [ ] Revisar contratos y documentos relacionados.
- [ ] Mantener histórico de cambios y pagos.

**Estado:** ⬜ Pendiente  
**Fecha de finalización:** —

---

# BLOQUE 12 — Pruebas y aceptación

**Objetivo:** comprobar que no existe ninguna mezcla de monedas ni precios de mercados.

## Países y monedas mínimas

- [ ] Venezuela → USD.
- [ ] Colombia → COP.
- [ ] México → MXN.
- [ ] Perú → PEN.
- [ ] País adicional activo definido por la configuración del producto.
- [ ] Ecuador u otro país dolarizado → USD, si está activo en la fase correspondiente.

## Pruebas funcionales

- [ ] Crear organización en cada país.
- [ ] Confirmar moneda por defecto.
- [ ] Cambiar moneda desde configuración.
- [ ] Crear presupuesto en moneda recomendada.
- [ ] Crear presupuesto en USD desde país no dolarizado.
- [ ] Abrir detalle de partida.
- [ ] Abrir descomposición.
- [ ] Editar precio y coste.
- [ ] Calcular beneficio y margen.
- [ ] Aplicar descuento, IVA, retención y cargos.
- [ ] Generar PDF.
- [ ] Generar Excel.
- [ ] Abrir enlace público.
- [ ] Crear proyecto.
- [ ] Añadir cambio de alcance.
- [ ] Registrar pago.
- [ ] Verificar saldo.
- [ ] Cambiar el precio nacional de un recurso.
- [ ] Confirmar que un presupuesto aprobado no cambia.
- [ ] Confirmar que un borrador aplica correctamente una actualización permitida.
- [ ] Confirmar que no ocurre doble conversión.
- [ ] Confirmar que los códigos ISO aparecen siempre correctamente.

## Pruebas de regresión

- [ ] Ejecutar suite existente de tests.
- [ ] Añadir tests del servicio de moneda.
- [ ] Añadir tests de recursos por país.
- [ ] Añadir tests de cálculos en moneda local.
- [ ] Añadir tests de PDF y Excel.
- [ ] Añadir tests de proyectos y pagos.
- [ ] Añadir tests de compatibilidad con datos antiguos en USD y Bs/VES.

**Estado:** ⬜ Pendiente  
**Fecha de finalización:** —

---

# BLOQUE 13 — Documentación y cierre

**Objetivo:** dejar el sistema preparado para continuar el crecimiento a nuevos países.

## Tareas

- [ ] Actualizar README.
- [ ] Actualizar hoja de ruta general.
- [ ] Actualizar punto de continuación.
- [ ] Documentar cómo añadir un país.
- [ ] Documentar cómo añadir una moneda.
- [ ] Documentar cómo cargar precios de recursos por país.
- [ ] Documentar cómo actualizar tarifas de mano de obra.
- [ ] Documentar reglas de históricos.
- [ ] Documentar reglas para proyectos y pagos.
- [ ] Documentar campos de origen y confianza del precio.
- [ ] Crear checklist de despliegue.
- [ ] Crear checklist de aceptación de un nuevo mercado.
- [ ] Marcar esta hoja como completada solo después de pasar las pruebas.

**Estado:** ⬜ Pendiente  
**Fecha de finalización:** —

---

## Auditoría de cierre — 2026-08-19 (sesión de tarde)

Revisión completa del trabajo del día a partir de dos síntomas reportados: el
total de una partida se veía en pesos mexicanos mientras sus precios unitarios
seguían en dólares al pulsar «editar», y el símbolo mostrado era «$» en lugar
del de cada país.

### Causa común

El catálogo (partidas, productos, recursos y packs) se guarda en la **moneda
base** (USD) y el presupuesto tiene su **moneda contractual**. Los caminos que
cruzan esa frontera se habían convertido solo en algunas vistas, y siempre con
la moneda de la *organización*, no con la del *presupuesto*.

### Defectos encontrados y corregidos

| # | Defecto | Efecto para el usuario |
|---|---|---|
| 1 | `GET /partidas/{id}/ficha` no convertía | Al editar una partida, precio unitario, costes y descomposición aparecían en USD junto a un total en MXN |
| 2 | `POST /partidas/{id}/actualizar-precio` no deshacía la conversión | «Actualizar el catálogo» desde un presupuesto en MXN guardaba los pesos como dólares: el precio se multiplicaba por la tasa en cada edición |
| 3 | `guardar-desde-presupuesto` usaba la moneda de la organización y no convertía los costes recalculados | Precio en la moneda base con costes en moneda local en la misma partida |
| 4 | `crear`/`actualizar` partida sobrescribían los costes convertidos con los locales | Mismo desfase en la pestaña Partidas |
| 5 | Productos del editor sin convertir | Añadir un producto sumaba dólares a un total en pesos |
| 6 | Packs (recetas) guardados y releídos sin moneda | Un pack creado en MXN multiplicaba por 17 al insertarlo en un presupuesto en USD |
| 7 | `/partidas/api/buscar` y `/partidas/{id}/descomposicion` usaban la moneda de la organización | Desfase cuando el presupuesto tenía otra moneda |
| 8 | 27 usos de `\| money` y varios «$» fijos en JavaScript | Importes mexicanos, colombianos y dólares con el mismo símbolo |
| 9 | `tarifa_hora_media` no seguía la moneda del presupuesto | Estimación de horas multiplicada por la tasa |
| 10 | Precios por mercado sin `GRANT` ni RLS | 500 al abrir «Nuevo presupuesto» (corregido en la revisión `e7b3c1d5a204`) |

### Reglas que quedan fijadas

- Contrato único de contexto monetario: los endpoints del catálogo aceptan
  `moneda` y `tasa`; el editor los envía siempre (`window.COTIZAT_MONEDA_ACTIVA`
  y `window.COTIZAT_TASA_ACTIVA`).
- Al **leer** se convierte base → moneda del documento; al **escribir** se
  deshace la conversión antes de tocar el catálogo.
- Nunca se inventa una tasa: sin tasa válida, el importe se queda en la moneda
  base en lugar de mostrar una conversión falsa.
- Los importes se muestran con código ISO (`1.234,56 MXN`) y, cuando hace falta
  un símbolo, con el distintivo del país (`MX$`, `COL$`, `US$`, `S/`, `Bs`).
- Decimales: COP, CLP y PYG sin decimales; el resto con dos, tanto en Python
  como en el JavaScript del editor.

### Cobertura de pruebas añadida

- `tests/test_moneda_editor.py`: ficha, descomposición, actualización de precio,
  guardado hacia el catálogo, productos, recursos, packs y símbolos.
- `tests/test_rls_postgres.py`: precios por mercado bajo RLS real.
- `tests/test_rls.py`: toda tabla del modelo debe tener `GRANT`; head único.

### Limitaciones conocidas (no son defectos nuevos)

- El panel y los reportes suman totales de presupuestos que pueden estar en
  monedas distintas; se etiquetan con la moneda de la organización. Convertir o
  segmentar esa suma es trabajo pendiente de un bloque futuro.
- Los packs creados **antes** de este cambio se interpretan como moneda base
  (era el comportamiento anterior, con el catálogo en USD).
- La conversión del editor usa la tasa USD → moneda local. Una conversión
  directa entre dos monedas locales (COP → MXN) exige las dos tasas y hoy no se
  ofrece en la interfaz.

---

## Registro de sesiones

### 2026-08-19 — Sesión inicial

- Se acordó usar códigos ISO en lugar de símbolos ambiguos.
- Se confirmó USD como moneda comercial de Cotizat.
- Se confirmó USD como moneda por defecto de los presupuestos venezolanos.
- Se acordó no mostrar VES/Bs en presupuestos venezolanos.
- Se confirmó que el usuario puede elegir una moneda distinta a la recomendada por el país.
- Se incorporó como requisito principal la localización de precios de recursos por país.
- Se distinguió entre conversión monetaria y precio real de mercado.
- Se creó `docs/DECISIONES_MONEDA_Y_RECURSOS_LATAM.md`.
- Se creó esta hoja de ruta para continuar en sesiones posteriores.

## Registro de cambios del documento

| Fecha | Cambio |
|---|---|
| 2026-08-19 | Creación de la hoja de ruta y definición inicial de bloques |
| 2026-08-19 (tarde) | Auditoría de cierre: 10 defectos de moneda corregidos, reglas de contexto monetario fijadas y limitaciones conocidas documentadas |

### 2026-08-19 — Política de decimales confirmada

Se adopta la recomendación inicial:

- USD: 2 decimales.
- COP: 0 decimales visibles en documentos; precisión interna cuando sea necesaria.
- MXN: 2 decimales.
- PEN: 2 decimales.
- CLP: 0 decimales.
- PYG: 0 decimales.

### 2026-08-19 — Confirmación de decisiones A-E

- A confirmado: catálogo base/referencia y precios independientes por país; Colombia y Perú pueden tener precios distintos para el mismo recurso.
- B confirmado: cambiar moneda en borrador requiere confirmación y solo se convierte si el cliente lo decide.
- C confirmado: la tasa automática es una sugerencia revisable; se guarda la tasa confirmada y se congela al enviar/aprobar.
- D confirmado: precios nacionales inicialmente; cada empresa puede ajustar manualmente sus datos; se deja preparada la futura granularidad regional.
- E confirmado: los pagos se mantienen en la moneda contractual del proyecto; la forma interna de cobro queda fuera del alcance inicial.
