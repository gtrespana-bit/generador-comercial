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

- [ ] Pendiente

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

- [ ] Cliente asignado.
- [ ] Cliente con email o teléfono.
- [ ] Presupuesto con al menos un capítulo y una partida activa.
- [ ] Todas las partidas activas tienen precio.
- [ ] Todas las partidas activas tienen cantidad mayor que cero.
- [ ] Margen total calculable.
- [ ] Margen total por encima del mínimo recomendado.
- [ ] Partidas con margen bajo identificadas.
- [ ] Partidas sin coste interno identificadas.
- [ ] Partidas sin tiempo estimado identificadas.
- [ ] PDF con logo o aviso si no hay logo.
- [ ] Validez configurada.
- [ ] Moneda y tasa coherentes.
- [ ] IVA configurado.
- [ ] Productos opcionales/alternativos revisados.
- [ ] Versión creada o actualizada antes de enviar.

### Acciones desde el asistente

- [ ] Revisar partidas sin coste.
- [ ] Revisar margen bajo.
- [ ] Revisar tiempos.
- [ ] Completar datos del cliente.
- [ ] Ver PDF.
- [ ] Enviar de todos modos.

### Criterios de aceptación

- [ ] El usuario puede entender en menos de 10 segundos si el presupuesto está listo.
- [ ] El asistente no bloquea el trabajo: advierte y permite continuar.
- [ ] Los avisos llevan a la pantalla exacta donde corregir el problema.
- [ ] No muestra información interna al cliente.

---

## 1.2 Salud del presupuesto

### Estado

- [ ] Pendiente

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

- [ ] Porcentaje de preparación.
- [ ] Nivel visual: verde, ámbar, rojo.
- [ ] Lista breve de principales problemas.
- [ ] Enlaces directos para corregir.

### Criterios de aceptación

- [ ] La puntuación se entiende sin explicación técnica.
- [ ] No ocupa demasiado espacio en el detalle del presupuesto.
- [ ] Puede integrarse dentro del asistente “Revisar antes de enviar”.

---

## 1.3 Botón principal único “Enviar propuesta”

### Estado

- [ ] Pendiente

### Descripción

Reducir dispersión de acciones en el detalle del presupuesto.

En lugar de mostrar muchas acciones con la misma importancia, estructurar así:

Acción principal:

- [ ] Enviar propuesta.

Acciones secundarias:

- [ ] Editar.
- [ ] Descargar PDF.
- [ ] Planificación de obra.

Menú “Más”:

- [ ] Versiones.
- [ ] Duplicar.
- [ ] Crear proyecto.
- [ ] Anexos.
- [ ] Eliminar.

### Criterios de aceptación

- [ ] La acción principal es obvia.
- [ ] Las acciones avanzadas siguen disponibles.
- [ ] La pantalla se siente menos cargada.

---

# Fase 2 — CotizaT ayuda a vender más

## Objetivo

Ayudar al contratista a aumentar el ticket medio y cerrar más propuestas.

Mensaje de producto:

> “No mandes una sola opción: presenta alternativas claras para que el cliente elija y compre mejor.”

---

## 2.1 Opciones Básico / Estándar / Premium

### Estado

- [ ] Pendiente

### Descripción

Permitir presentar variantes comerciales del mismo presupuesto.

Ejemplo:

| Opción | Total | Descripción |
|---|---:|---|
| Básico | 4.200 US$ | Acabado estándar |
| Estándar | 5.100 US$ | Mejor porcelanato + grifería |
| Premium | 6.300 US$ | Alta gama + extras |

### Enfoque recomendado

No crear un editor complejo desde el inicio. Empezar con una versión simple:

- [ ] Duplicar presupuesto como opción.
- [ ] Etiquetar opción: Básico, Estándar, Premium o personalizada.
- [ ] Comparar total, margen y diferencia.
- [ ] Mostrar en propuesta pública de forma clara.

### Criterios de aceptación

- [ ] El usuario puede crear tres opciones sin rehacer todo desde cero.
- [ ] El cliente final ve las opciones sin ver costes internos ni margen.
- [ ] CotizaT muestra diferencia de precio y qué incluye cada opción.

---

## 2.2 Propuesta pública más vendedora

### Estado

- [ ] Pendiente

### Descripción

Mejorar la página pública que ve el cliente para que ayude a cerrar la venta.

### Elementos recomendados

- [ ] Resumen superior claro: obra, total, validez y empresa.
- [ ] Bloque “Qué incluye”.
- [ ] Bloque de productos opcionales/alternativos si existen.
- [ ] Botón principal: Aceptar propuesta.
- [ ] Acción secundaria: Solicitar cambios.
- [ ] Acción secundaria: Rechazar.
- [ ] Firma en pantalla.
- [ ] PDF descargable.
- [ ] Mensaje de confianza: versión, fecha, validez.

### Información que NO debe mostrarse

- [ ] Coste interno.
- [ ] Margen.
- [ ] Beneficio.
- [ ] Cuello de botella.
- [ ] Horas internas por oficio.

### Criterios de aceptación

- [ ] El cliente entiende qué acepta.
- [ ] La firma es fácil desde móvil.
- [ ] Si hay opciones, puede elegir sin confusión.

---

## 2.3 Plantillas de mensajes WhatsApp/email

### Estado

- [ ] Pendiente

### Descripción

Crear plantillas reutilizables para comunicación comercial.

### Plantillas iniciales

- [ ] Enviar presupuesto.
- [ ] Recordatorio amable.
- [ ] Presupuesto por vencer.
- [ ] Propuesta aceptada.
- [ ] Solicitud de datos faltantes.
- [ ] Envío de documento de cobro.
- [ ] Confirmación de inicio de obra.

### Variables útiles

- [ ] Nombre del cliente.
- [ ] Número de presupuesto.
- [ ] Título de obra.
- [ ] Total.
- [ ] Fecha de validez.
- [ ] Enlace público.
- [ ] Empresa.

### Criterios de aceptación

- [ ] El usuario puede enviar un mensaje profesional sin redactar desde cero.
- [ ] Las plantillas son editables.
- [ ] El mensaje generado es breve y natural.

---

# Fase 3 — CotizaT protege durante la obra

## Objetivo

Evitar pérdidas por cambios de alcance, pagos olvidados o acuerdos no documentados.

Mensaje de producto:

> “Cuando el cliente pide cambios, CotizaT los calcula, los documenta y los deja firmados.”

---

## 3.1 Cambios de alcance firmables

### Estado

- [ ] Pendiente

### Descripción

Convertir los cambios de proyecto en mini-propuestas aprobables por el cliente.

### Flujo recomendado

- [ ] Crear cambio de alcance desde proyecto.
- [ ] Añadir partidas nuevas, modificadas o eliminadas.
- [ ] Calcular diferencia económica.
- [ ] Calcular diferencia de plazo.
- [ ] Mostrar impacto en margen interno.
- [ ] Generar propuesta de cambio.
- [ ] Enviar enlace al cliente.
- [ ] Cliente acepta/firma el cambio.
- [ ] El proyecto actualiza total contratado y saldo.

### Criterios de aceptación

- [ ] El cambio de alcance no altera el presupuesto original aprobado.
- [ ] Cada cambio tiene versión, fecha y estado.
- [ ] El cliente puede firmar desde móvil.
- [ ] El contratista ve impacto en dinero y tiempo.

---

## 3.2 Plan de pagos desde el presupuesto

### Estado

- [ ] Pendiente

### Descripción

Permitir definir un plan de cobro antes o después de aprobar el presupuesto.

Ejemplo:

| Hito | % | Importe |
|---|---:|---:|
| Anticipo | 50% | 2.500 US$ |
| Avance de obra | 30% | 1.500 US$ |
| Entrega | 20% | 1.000 US$ |

### Funciones

- [ ] Plantillas de plan de pagos.
- [ ] Cálculo automático por porcentaje.
- [ ] Edición manual de importes.
- [ ] Generar documento de cobro desde un hito.
- [ ] Marcar hito cobrado/parcial/pendiente.

### Criterios de aceptación

- [ ] El usuario entiende cuánto cobrar y cuándo.
- [ ] Los cobros se conectan con proyecto y saldo.
- [ ] No se presenta como factura fiscal.

---

## 3.3 Estado financiero del proyecto

### Estado

- [ ] Pendiente

### Descripción

Crear un resumen claro del dinero del proyecto.

Ejemplo:

```txt
Contrato aprobado: 5.200 US$
Cambios aprobados: +430 US$
Total contratado: 5.630 US$
Cobrado: 3.000 US$
Pendiente: 2.630 US$
Margen estimado: 31%
```

### Criterios de aceptación

- [ ] El usuario ve saldo pendiente en segundos.
- [ ] Los cambios de alcance impactan el total contratado.
- [ ] Los documentos de cobro impactan el cobrado/pendiente.

---

# Fase 4 — CotizaT mantiene sano el negocio

## Objetivo

Ayudar al usuario a mantener catálogo, precios, márgenes y reportes en buen estado.

Mensaje de producto:

> “Tu catálogo es tu activo. CotizaT te ayuda a mantenerlo actualizado y rentable.”

---

## 4.1 Salud del catálogo

### Estado

- [ ] Pendiente

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

- [ ] Revisar margen bajo.
- [ ] Revisar sin coste.
- [ ] Revisar sin tiempo.
- [ ] Actualizar precios.
- [ ] Sincronizar recursos.

### Criterios de aceptación

- [ ] El usuario entiende si puede presupuestar con confianza.
- [ ] Los avisos son accionables.
- [ ] No obliga a revisar todo de golpe.

---

## 4.2 Actualización guiada de precios

### Estado

- [ ] Pendiente

### Descripción

Mejorar los ajustes por porcentaje para que sean más seguros.

### Funciones

- [ ] Simular antes de aplicar.
- [ ] Ajustar por capítulo.
- [ ] Ajustar por tipo de recurso: material, mano de obra, equipo.
- [ ] Ver impacto promedio.
- [ ] Guardar histórico de ajustes.
- [ ] Permitir deshacer último ajuste.

### Criterios de aceptación

- [ ] El usuario sabe qué cambiará antes de confirmar.
- [ ] El ajuste no se siente peligroso.
- [ ] Queda registro de cuándo y por qué se cambió.

---

## 4.3 Impacto de recursos vinculados

### Estado

- [ ] Pendiente

### Descripción

Desde un recurso, mostrar en qué partidas aparece y cómo impacta un cambio de precio.

Ejemplo:

```txt
Cemento gris aparece en 18 partidas.
Si sube de 8 a 10 US$, estas partidas cambiarán así…
```

### Criterios de aceptación

- [ ] El usuario entiende el efecto en cascada.
- [ ] Puede actualizar un recurso con confianza.
- [ ] Ve partidas afectadas antes de confirmar.

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

- [ ] Asistente “Revisar antes de enviar”.
- [ ] Salud del presupuesto.
- [ ] Reordenar acciones principales en detalle del presupuesto.

## Sprint 2

- [ ] Plantillas de mensajes WhatsApp/email.
- [ ] Propuesta pública más vendedora.
- [ ] Seguimiento de propuesta vista/aceptada/rechazada.

## Sprint 3

- [ ] Opciones Básico / Estándar / Premium.
- [ ] Comparativa visible para el cliente.
- [ ] Selección de opcionales/alternativas en propuesta pública.

## Sprint 4

- [ ] Cambios de alcance firmables.
- [ ] Estado financiero del proyecto.
- [ ] Plan de pagos desde presupuesto/proyecto.

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
