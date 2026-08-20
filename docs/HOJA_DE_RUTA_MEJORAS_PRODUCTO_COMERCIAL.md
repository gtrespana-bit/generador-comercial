# Hoja de ruta — Mejora comercial y experiencia de producto

Fecha de creación: 2026-08-20  
Producto: CotizaT / Generador Comercial  
Objetivo: convertir CotizaT en una herramienta que guíe al contratista para **presupuestar mejor, evitar errores, proteger margen, vender más y controlar la obra**, sin saturar la interfaz.

---

## Principios de producto

Antes de añadir cualquier función, validar que cumple estos criterios:

- [ ] **Simplifica una decisión real** del usuario.
- [ ] **No añade ruido visual** a la pantalla principal.
- [ ] Puede estar en modo plegado, asistente o acción secundaria si es avanzado.
- [ ] Usa datos que CotizaT ya tiene siempre que sea posible.
- [ ] Evita duplicar pantallas o flujos.
- [ ] Tiene una salida clara: revisar, corregir, enviar, vender, cobrar o planificar.
- [ ] No muestra al cliente información interna como costes, margen o tiempos privados.

Regla general: **más funciones no significa mejor producto**. La prioridad es que el usuario sienta que CotizaT le facilita la vida.

---

# Estado actual reciente

## Ya realizado

- [x] Reposicionar la landing para comunicar que CotizaT no es solo un generador de presupuestos.
- [x] Mostrar desde la primera pantalla: margen, costes, tiempos, firma y cobros.
- [x] Corregir la composición de cuadrilla en la planificación de tiempos.
- [x] Hacer que jornada, cuadrillas y composición recalculen plazo y fecha fin.
- [x] Añadir asistente ligero de planificación de obra.
- [x] Añadir comparador automático de escenarios de cuadrilla.
- [x] Añadir detección de cuello de botella en planificación.
- [x] Añadir cronograma interno simple por capítulos.
- [x] Añadir calendario simple con sábados y colchón recomendado.
- [x] Añadir exportación/impresión del plan interno.
- [x] Añadir pruebas para la lógica de composición de cuadrilla.
- [x] Añadir asistente de revisión antes de enviar presupuestos.
- [x] Añadir salud del presupuesto con score visual.
- [x] Reordenar acciones del detalle con botón principal y menú de opciones.

Commits relacionados:

- `d33dbee` — Mejora landing y simulador de tiempos.
- `49c74af` — Añade asistente ligero de planificación de obra.

---

# Fase 1 — CotizaT evita errores antes de enviar

## Objetivo

Que el usuario sepa si un presupuesto está realmente listo antes de mandarlo al cliente.

Mensaje de producto:

> “CotizaT te avisa antes de enviar un presupuesto incompleto, con margen bajo o con datos críticos sin revisar.”

---

## 1.1 Asistente “Revisar antes de enviar”

### Estado

- [x] Realizado

### Descripción

Crear una tarjeta de revisión en el detalle del presupuesto y antes de enviar la propuesta.

Debe mostrar un estado tipo:

```txt
Tu presupuesto está listo al 86%

✓ Cliente asignado
✓ PDF con logo
✓ Margen total 32%
⚠ 3 partidas sin coste interno
⚠ 2 partidas sin tiempo estimado
⚠ Falta teléfono del cliente
```

### Checks recomendados

- [x] Cliente asignado.
- [x] Cliente con email o teléfono.
- [x] Presupuesto con al menos un capítulo y una partida activa.
- [x] Todas las partidas activas tienen precio.
- [x] Todas las partidas activas tienen cantidad mayor que cero.
- [x] Margen total calculable.
- [x] Margen total por encima del mínimo recomendado.
- [x] Partidas con margen bajo identificadas.
- [x] Partidas sin coste interno identificadas.
- [x] Partidas sin tiempo estimado identificadas.
- [x] PDF con logo o aviso si no hay logo.
- [x] Validez configurada.
- [x] Moneda y tasa coherentes.
- [x] IVA configurado.
- [ ] Productos opcionales/alternativos revisados.
- [x] Versión creada o actualizada antes de enviar.

### Acciones desde el asistente

- [x] Revisar partidas sin coste.
- [x] Revisar margen bajo.
- [x] Revisar tiempos.
- [x] Completar datos del cliente.
- [ ] Ver PDF.
- [x] Enviar de todos modos.

### Criterios de aceptación

- [ ] El usuario puede entender en menos de 10 segundos si el presupuesto está listo.
- [ ] El asistente no bloquea el trabajo: advierte y permite continuar.
- [ ] Los avisos llevan a la pantalla exacta donde corregir el problema.
- [ ] No muestra información interna al cliente.

---

## 1.2 Salud del presupuesto

### Estado

- [x] Realizado

### Descripción

Mostrar una puntuación simple del presupuesto:

- Listo.
- Revisar.
- Riesgo.

Ejemplo:

```txt
Salud del presupuesto: 78% · Revisar antes de enviar
```

### Componentes

- [x] Porcentaje de preparación.
- [x] Nivel visual: verde, ámbar, rojo.
- [x] Lista breve de principales problemas.
- [x] Enlaces directos para corregir.

### Criterios de aceptación

- [ ] La puntuación se entiende sin explicación técnica.
- [ ] No ocupa demasiado espacio en el detalle del presupuesto.
- [ ] Puede integrarse dentro del asistente “Revisar antes de enviar”.

---

## 1.3 Botón principal único “Enviar propuesta”

### Estado

- [x] Realizado

### Descripción

Reducir dispersión de acciones en el detalle del presupuesto.

En lugar de mostrar muchas acciones con la misma importancia, estructurar así:

Acción principal:

- [x] Enviar propuesta.

Acciones secundarias:

- [x] Editar.
- [x] Descargar PDF.
- [x] Planificación de obra.

Menú “Más”:

- [x] Versiones.
- [x] Duplicar.
- [x] Crear proyecto.
- [x] Anexos.
- [x] Eliminar.

### Criterios de aceptación

- [ ] La acción principal es obvia.
- [ ] Las acciones avanzadas siguen disponibles.
- [ ] La pantalla se siente menos cargada.

---

# Fase 2 — Reenvíos y cambios simples sin saturar

## Objetivo

Mantener el flujo real del contratista: envía PDF, el cliente llama o escribe,
pide cambios y el contratista reenvía una versión corregida. CotizaT solo debe
ayudar a que ese reenvío sea claro, rápido y profesional.

Mensaje de producto:

> “Cuando modificas un presupuesto ya enviado, CotizaT te ayuda a explicar qué cambió y reenviar el PDF sin confusión.”

## Alcance deliberadamente reducido

No se implementarán por ahora:

- [ ] Flujo complejo de selección online para el cliente.
- [ ] Opciones Básico / Estándar / Premium como módulo completo.
- [ ] CRM avanzado de seguimiento.
- [ ] Automatizaciones de recordatorios.
- [ ] Gantt o planificación compleja orientada al cliente.
- [ ] Plantillas generales de mensajes que añadan ruido.

Principio: **si una función no ahorra tiempo claro al contratista, no entra**.

---

## 2.1 Detección simple de modificaciones en presupuestos reenviados

### Estado

- [x] Realizado

### Descripción

Cuando un presupuesto ya fue enviado, publicado o tiene versión congelada, y el usuario lo edita, CotizaT debe facilitar ver qué cambió respecto a la versión anterior.

No busca “explicarle al contratista su negocio”; solo evitar confusiones al reenviar.

### Debe detectar

- [x] Total anterior vs total nuevo.
- [x] Partidas añadidas.
- [x] Partidas eliminadas.
- [x] Partidas con cantidad modificada.
- [x] Partidas con precio modificado.
- [x] Capítulos añadidos o eliminados.

### No debe mostrar por defecto

- [ ] Análisis complejo de margen.
- [ ] Impactos excesivamente detallados.
- [ ] Gráficas.
- [ ] Flujo online para el cliente.

### Criterios de aceptación

- [ ] En menos de 10 segundos el usuario entiende qué cambió.
- [ ] La comparación aparece solo cuando tiene sentido: presupuesto ya enviado/versionado.
- [ ] La vista es compacta y plegable.
- [ ] No interrumpe el guardado ni el envío.

---

## 2.2 Resumen de cambios para copiar y reenviar

### Estado

- [x] Realizado

### Descripción

Generar un texto corto listo para copiar en WhatsApp/email cuando el contratista reenvía una versión modificada.

Ejemplo:

```txt
Hola, Juan. Te envío el presupuesto actualizado P-2026-009.

Total anterior: 3.248,00 USD
Nuevo total: 2.980,00 USD
Diferencia: -268,00 USD

Cambios principales:
- Se eliminó mampara de ducha.
- Se cambió porcelanato premium por estándar.
- Se añadió pintura de techo.

Adjunto el PDF actualizado.
```

### Criterios de aceptación

- [x] El texto es breve y natural.
- [x] Se puede copiar con un botón.
- [x] Se puede editar antes de copiar/enviar.
- [x] No incluye costes internos, margen ni información sensible.
- [ ] Si no hay cambios detectables, no muestra nada innecesario.

---

## 2.3 Aviso discreto al editar presupuesto ya enviado

### Estado

- [x] Realizado

### Descripción

Si el usuario entra a editar un presupuesto que ya fue enviado, aprobado, publicado con enlace o tiene versiones, mostrar un aviso pequeño:

```txt
Este presupuesto ya fue enviado o tiene versiones guardadas.
Si lo modificas, podrás ver un resumen de cambios para reenviarlo con claridad.
```

### Criterios de aceptación

- [ ] No bloquea la edición.
- [ ] No asusta al usuario.
- [ ] Ayuda a recordar que el presupuesto ya fue compartido.

---

## 2.4 Botón “Reenviar versión actualizada”

### Estado

- [x] Realizado

### Descripción

En el detalle del presupuesto, si hay diferencias frente a la última versión enviada, mostrar una acción simple:

- [x] Ver cambios.
- [x] Descargar PDF actualizado.
- [x] Copiar resumen para WhatsApp/email.

No crear un flujo nuevo complejo. Solo agrupar las tres acciones más útiles.

### Criterios de aceptación

- [ ] El usuario puede reenviar una versión modificada en menos de un minuto.
- [ ] La acción no aparece si no hay versiones/cambios.
- [ ] No obliga a usar propuesta online.

---

# Fase 3 — Pulido del editor y velocidad de uso

## Objetivo

Hacer que crear y modificar presupuestos sea más rápido, más limpio y con menos posibilidad de error. No se añaden módulos grandes: se ordena mejor lo que ya existe.

Mensaje de producto:

> “CotizaT mantiene toda la potencia, pero el editor debe sentirse rápido y sencillo.”

---

## 3.1 Vista simple por defecto y detalles plegados

### Estado

- [x] Realizado

### Descripción

El editor ya trabaja con fila compacta y ficha expandible. Se refuerza este enfoque para que la fila principal sea la vista de trabajo diaria y los detalles queden bajo edición/ficha.

### Incluido

- [x] Fila compacta con nombre, cantidad, unidad, precio, importe, beneficio y menú.
- [x] Ficha completa accesible desde editar/expandir.
- [x] Acciones secundarias dentro del menú de la partida.
- [x] Mantener costes, producto, descompuesto y mediciones sin mostrarlos todos a la vez.

---

## 3.2 Avisos suaves dentro del editor

### Estado

- [x] Realizado

### Descripción

Añadir chips discretos por partida para detectar problemas sin mostrar alertas grandes.

### Avisos incluidos

- [x] Partida sin nombre.
- [x] Cantidad cero.
- [x] Precio cero.
- [x] Sin coste interno.
- [x] Pérdida: coste mayor que precio.
- [x] Margen bajo.

### Criterios de aceptación

- [x] Los avisos son visuales y pequeños.
- [x] No bloquean la edición.
- [x] Se recalculan mientras se trabaja.

---

## 3.3 Estado vacío útil del editor

### Estado

- [x] Realizado

### Descripción

Cuando aún no hay partidas, mostrar un punto de partida claro.

### Acciones disponibles

- [x] Añadir partida.
- [x] Buscar catálogo.
- [x] Insertar pack.
- [x] Pegar Excel.

### Criterios de aceptación

- [x] El usuario no ve un lienzo vacío sin saber qué hacer.
- [x] Las acciones llevan a flujos existentes, sin añadir complejidad nueva.

---

## 3.4 Guardado y autoguardado más claro

### Estado

- [x] Validado con lo existente

### Descripción

Se mantiene el sistema actual de estado de guardado/autoguardado porque ya cubre la necesidad sin añadir ruido.

### Existente

- [x] Indicador de autoguardado.
- [x] Guardado de borrador.
- [x] Botón de guardar principal.
- [x] Recuperación de borrador local/servidor.

---

## 3.5 Acciones rápidas sin saturar

### Estado

- [x] Validado con lo existente

### Descripción

Se mantiene la lógica actual: acciones frecuentes visibles en cabecera y acciones de partida dentro del menú.

### Existente

- [x] Añadir partida.
- [x] Duplicar partida.
- [x] Eliminar partida.
- [x] Duplicar capítulo.
- [x] Insertar pack.
- [x] Pegar desde Excel.
- [x] Vista previa PDF.
- [x] Buscador de catálogo.

---

# Fase 4 — CotizaT mantiene sano el negocio

## Objetivo

Ayudar al usuario a mantener catálogo, precios, márgenes y reportes en buen estado.

Mensaje de producto:

> “Tu catálogo es tu activo. CotizaT te ayuda a mantenerlo actualizado y rentable.”

---

## 4.1 Salud del catálogo

### Estado

- [x] Realizado

### Descripción

Panel simple para saber si el catálogo está listo para presupuestar.

Ejemplo:

```txt
Salud del catálogo: 74%

✓ 320 partidas con precio
✓ 280 con coste interno
⚠ 40 sin tiempo estimado
⚠ 25 con margen bajo
⚠ 18 sin revisar hace más de 90 días
```

### Acciones

- [x] Revisar margen bajo.
- [x] Revisar sin coste.
- [x] Revisar sin tiempo.
- [x] Actualizar precios.
- [ ] Sincronizar recursos.

### Criterios de aceptación

- [ ] El usuario entiende si puede presupuestar con confianza.
- [ ] Los avisos son accionables.
- [ ] No obliga a revisar todo de golpe.

---

## 4.2 Actualización guiada de precios

### Estado

- [x] Realizado

### Descripción

Mejorar los ajustes por porcentaje para que sean más seguros.

### Funciones

- [x] Simular antes de aplicar.
- [ ] Ajustar por capítulo.
- [ ] Ajustar por tipo de recurso: material, mano de obra, equipo.
- [x] Ver impacto promedio.
- [ ] Guardar histórico de ajustes.
- [ ] Permitir deshacer último ajuste.

### Criterios de aceptación

- [x] El usuario sabe qué cambiará antes de confirmar.
- [x] El ajuste no se siente peligroso.
- [ ] Queda registro de cuándo y por qué se cambió.

---

## 4.3 Impacto de recursos vinculados

### Estado

- [x] Realizado

### Descripción

Desde un recurso, mostrar en qué partidas aparece y cómo impacta un cambio de precio.

Ejemplo:

```txt
Cemento gris aparece en 18 partidas.
Si sube de 8 a 10 US$, estas partidas cambiarán así…
```

### Criterios de aceptación

- [x] El usuario entiende el efecto en cascada.
- [x] Puede actualizar un recurso con confianza.
- [x] Ve partidas afectadas antes de confirmar.

---

# Fase 5 — Dashboard y seguimiento comercial

## Objetivo

Que el usuario abra CotizaT y sepa qué requiere atención hoy.

Mensaje de producto:

> “CotizaT no solo guarda tus presupuestos: te dice qué debes revisar, perseguir o cobrar.”

---

## 5.1 Panel “Qué requiere atención”

### Estado

- [ ] Pendiente

### Descripción

Añadir una sección en dashboard con prioridades.

Ejemplo:

```txt
Hoy deberías revisar:

1. 2 presupuestos vencen esta semana
2. 3 propuestas enviadas no han sido respondidas
3. 4 partidas tienen margen bajo
4. 1 proyecto tiene saldo pendiente
```

### Criterios de aceptación

- [ ] Máximo 5 avisos.
- [ ] Cada aviso tiene acción directa.
- [ ] El dashboard no se vuelve pesado.

---

## 5.2 Seguimiento de propuesta enviada

### Estado

- [ ] Pendiente

### Descripción

Registrar eventos de propuesta pública.

### Eventos sugeridos

- [ ] Enlace creado.
- [ ] Enlace enviado.
- [ ] Propuesta vista.
- [ ] PDF descargado.
- [ ] Aceptada.
- [ ] Rechazada.
- [ ] Vencida.
- [ ] Recordatorio enviado.

### Criterios de aceptación

- [ ] El usuario sabe si el cliente vio la propuesta.
- [ ] Se puede filtrar por propuestas pendientes de seguimiento.
- [ ] No depende de leer WhatsApp.

---

## 5.3 Recordatorios automáticos

### Estado

- [ ] Pendiente

### Descripción

Crear recordatorios simples y configurables.

### Casos iniciales

- [ ] Presupuesto enviado sin respuesta en X días.
- [ ] Presupuesto próximo a vencer.
- [ ] Saldo pendiente.
- [ ] Documento de cobro pendiente.

### Criterios de aceptación

- [ ] El usuario puede activar/desactivar recordatorios.
- [ ] Los mensajes usan plantillas editables.
- [ ] No genera spam ni múltiples avisos repetidos.

---

# Mejoras transversales de interfaz

## Modo simple / modo avanzado en el editor

### Estado

- [ ] Pendiente

### Descripción

El editor debe ser potente sin parecer complejo.

Modo simple visible por defecto:

- [ ] Cliente.
- [ ] Título.
- [ ] Capítulos.
- [ ] Partidas.
- [ ] Cantidad.
- [ ] Precio.
- [ ] Total.

Modo avanzado plegado:

- [ ] Costes internos.
- [ ] Descompuesto/APU.
- [ ] Tiempos.
- [ ] Producto asociado.
- [ ] Alternativa/opcional.
- [ ] Mediciones detalladas.
- [ ] Notas internas.

### Criterios de aceptación

- [ ] Un usuario nuevo puede crear un presupuesto sin entender todas las funciones.
- [ ] Un usuario avanzado no pierde potencia.
- [ ] El editor no se siente sobrecargado.

---

## Estados vacíos más útiles

### Estado

- [ ] Pendiente

### Descripción

Mejorar pantallas vacías para guiar al usuario.

Ejemplo:

```txt
Aún no tienes presupuestos.
Crea uno desde cero, usa una plantilla o inserta un pack de estancia.
```

### Páginas a revisar

- [ ] Presupuestos.
- [ ] Clientes.
- [ ] Productos.
- [ ] Partidas.
- [ ] Recursos.
- [ ] Packs.
- [ ] Proyectos.
- [ ] Cobros.
- [ ] Reportes.

---

## Lenguaje más orientado a negocio

### Estado

- [ ] Pendiente

### Cambios sugeridos

- [ ] “Optimizar precios” → “Revisar margen y precios”.
- [ ] “Recursos” → “Costes y recursos”.
- [ ] “Versiones” → “Historial de propuestas”.
- [ ] “Facturas” / “Documentos de cobro” → “Cobros y saldos”.
- [ ] “Tiempos” → “Planificación de obra”.
- [ ] “Descomposición” → “Costes/APU”.

---

# Funciones que NO se recomiendan por ahora

Para evitar sobrecargar el producto:

- [ ] No implementar Gantt complejo tipo MS Project.
- [ ] No implementar chat interno complejo.
- [ ] No implementar inventario completo de almacén.
- [ ] No implementar contabilidad fiscal completa.
- [ ] No vender “IA” como promesa principal.

Si se implementan en el futuro, deben entrar como módulos opcionales y no contaminar el flujo principal.

---

# Orden recomendado de ejecución

## Sprint 1

- [x] Asistente “Revisar antes de enviar”.
- [x] Salud del presupuesto.
- [x] Reordenar acciones principales en detalle del presupuesto.

## Sprint 2

- [x] Detección simple de cambios frente a la última versión enviada.
- [x] Resumen de cambios para copiar y reenviar por WhatsApp/email.
- [x] Aviso discreto al editar un presupuesto ya enviado.
- [x] Botón “Reenviar versión actualizada”.

## Sprint 3

- [x] Reforzar vista simple por defecto en el editor.
- [x] Añadir avisos suaves por partida.
- [x] Añadir estado vacío útil en el editor.
- [x] Validar guardado/autoguardado existente.
- [x] Validar acciones rápidas sin saturar.

## Sprint 4

- [x] Salud del catálogo.
- [x] Actualización guiada de precios.
- [x] Impacto de recursos vinculados.

## Sprint 5

- [ ] Salud del catálogo.
- [ ] Actualización guiada de precios.
- [ ] Impacto de recursos vinculados.

## Sprint 6

- [ ] Dashboard “Qué requiere atención”.
- [ ] Recordatorios automáticos.
- [ ] Reportes de rentabilidad y embudo comercial.

---

# Métricas de éxito

Medir si las mejoras realmente ayudan:

- [ ] Tiempo medio para crear primer presupuesto.
- [ ] % de presupuestos enviados con margen calculado.
- [ ] % de presupuestos enviados sin avisos críticos.
- [ ] Tasa de aceptación de propuestas.
- [ ] Tiempo medio desde envío hasta aceptación.
- [ ] % de proyectos con cambios de alcance documentados.
- [ ] % de cobros pendientes visibles en dashboard.
- [ ] Uso de plantillas de mensajes.
- [ ] Uso de opciones Básico/Estándar/Premium.

---

# Próxima acción recomendada

Empezar por:

## Asistente “Revisar antes de enviar”

Motivo:

- Reutiliza datos ya existentes.
- No sobrecarga la interfaz.
- Da valor inmediato.
- Refuerza el mensaje comercial de CotizaT.
- Reduce errores antes de enviar propuestas.

Primer entregable mínimo:

- [ ] Tarjeta en detalle del presupuesto.
- [ ] Lista de checks críticos.
- [ ] Estado general: Listo / Revisar / Riesgo.
- [ ] Botones para corregir.
- [ ] Integración con flujo de envío.
