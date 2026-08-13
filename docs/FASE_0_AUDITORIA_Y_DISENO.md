# Fase 0 — Auditoría técnica y diseño de evolución

Fecha: 2026-08-06  
Proyecto: Generador de presupuestos  
Alcance: funcionamiento, experiencia de uso y modelo de negocio. No se incluyen seguridad, usuarios ni exposición de red.

## 1. Decisiones de alcance confirmadas

### Se mantienen fuera

- Fórmulas geométricas automáticas (largo × ancho, áreas, perímetros y volúmenes).
- Tipos de medición avanzados.

El creador seguirá trabajando con cantidad directa y mediciones manuales por zona. Esto es deliberado para preservar la sencillez.

### Se desarrollarán

- Motor económico y de cálculos.
- Versiones de presupuestos.
- Alternativas configurables.
- Partidas incluidas, opcionales y excluidas.
- Catálogos mejorados.
- Autocompletado y recomendaciones.
- Importación profesional desde Excel/CSV.
- Búsqueda global.
- Estados ampliados.
- Conversión a proyecto.
- Cambios de alcance.
- Anticipos y pagos.
- Plantillas y PDF avanzado.
- Dashboard y reportes.
- Funciones venezolanas opcionales y configurables.

## 2. Inventario actual

### Modelos existentes

- `Cliente`: datos del cliente.
- `Presupuesto`: documento principal, moneda, IVA, descuento, validez, estado, notas, condiciones y opciones del PDF.
- `Capitulo`: agrupación ordenada de partidas.
- `PresupuestoItem`: partida con cantidad directa, precio, descripción y producto.
- `Medicion`: desglose manual por concepto/zona.
- `Configuracion`: datos empresariales, defaults y opciones visuales.
- `Plantilla`: estructura JSON de capítulos y partidas.
- `Partida`: catálogo reutilizable de trabajos.
- `Producto`: catálogo reutilizable de materiales.
- `NotaSeguimiento`: notas internas.
- `Factura`, `FacturaCapitulo`, `FacturaItem`: copia simplificada de un presupuesto aprobado.

### Funciones existentes confirmadas

- Constructor dinámico de capítulos y partidas.
- Mediciones manuales por zona.
- Cálculo de cantidad total desde mediciones.
- Catálogo de partidas y productos.
- Autosave local.
- Deshacer estructural.
- Duplicar partida y capítulo.
- Drag & drop.
- Pegado TSV desde Excel.
- Plantillas JSON.
- Vista previa y PDF.
- Estados básicos.
- Vencimiento automático.
- Exportación CSV.
- Facturación simple.
- Notas internas.
- Backup y restauración.

### Comprobación pendiente en la siguiente iteración

El autocompletado, recomendaciones y selección de productos ya tienen una base en `budget_form.js`; antes de crear otra solución se debe probar el flujo completo y documentar qué falta exactamente. La decisión es mejorar lo existente, no duplicarlo.

## 3. Hallazgos funcionales que afectan al diseño

### 3.1 El presupuesto actual mezcla tres conceptos

En `PresupuestoItem` conviven:

- Precio unitario de venta.
- Producto presupuestado.
- Cantidad/mediciones.

Para las siguientes fases conviene separar conceptualmente:

```text
Partida de trabajo
  ├── mediciones
  ├── componentes/materiales
  ├── coste interno
  └── precio de venta
```

La pantalla básica no tiene que mostrar todos esos niveles; el modelo sí debe soportarlos.

### 3.2 La factura actual es una instantánea reducida

Al convertir a factura se copia la cantidad total, pero no se conservan mediciones, productos ni anexos. Para una futura facturación esto debe quedar como una instantánea congelada de líneas, mientras que el presupuesto podrá seguir evolucionando por versiones.

### 3.3 Las opciones del PDF ya tienen precedentes de configuración

Portada, resumen y firmas ya se activan desde Configuración. Las nuevas opciones deben seguir el mismo patrón:

- Default global.
- Override por documento.
- Ocultas si la función está desactivada.

### 3.4 El JSON de plantillas es válido para una primera versión

Para plantillas simples se puede conservar el JSON. Cuando se añadan alternativas, opcionales, costes y productos avanzados, habrá que versionar el formato:

```json
{
  "schema_version": 2,
  "chapters": []
}
```

Nunca se debe asumir que todas las plantillas antiguas tienen los campos nuevos.

## 4. Diseño funcional propuesto

## 4.1 Modos de uso

### Modo básico — predeterminado

Visible en el creador:

- Nombre.
- Cantidad.
- Unidad.
- Precio unitario.
- Importe.
- Descripción opcional.
- Mediciones manuales opcionales.

### Modo avanzado — activable

Solo aparece si se activa en Configuración o desde el presupuesto:

- Tipo de partida.
- Alternativas.
- Productos avanzados.
- Coste interno.
- Margen.
- Desperdicio.
- Gastos adicionales.
- Campos venezolanos.

Principio de interfaz: activar una capacidad no debe convertir todas las partidas existentes en formularios enormes. Se mostrará mediante secciones plegables y solo por partida cuando sea necesario.

## 4.2 Tipos de partida

Se propone un campo estable y sencillo:

```text
included       Incluida
optional       Opcional
alternative    Alternativa
excluded       No incluida
provisional    Provisional
measurement   Sujeta a medición
```

Una partida incluida participa en el total base. Una opcional o alternativa solo participa cuando se selecciona. Una excluida nunca participa en el total, pero puede aparecer en el PDF si está configurado.

## 4.3 Alternativas

Las alternativas deben agruparse, no ser partidas sueltas sin relación:

```text
Grupo: Acabado de piso de sala
  - Opción estándar
  - Opción premium
  - Opción lujo
```

El grupo tendrá una selección activa. En modo básico no se muestra esta estructura.

## 4.4 Totales

El motor deberá distinguir:

```text
subtotal_incluido
subtotal_opcional
subtotal_alternativas
costes_adicionales
subtotal_bruto
descuento
base_imponible
impuesto
total
```

Además, internamente:

```text
coste_materiales
coste_mano_obra
coste_otros
coste_interno
margen
```

La presentación dependerá de la configuración del documento y del PDF.

## 5. Diseño de datos por fases

No se recomienda introducir todas las tablas nuevas de una vez. Se propone esta secuencia.

### Migración A — motor económico

Añadir campos opcionales a la línea de presupuesto:

- `tipo_partida`.
- `coste_materiales`.
- `coste_mano_obra`.
- `coste_otros`.
- `desperdicio_pct`.
- `margen_pct`.
- `mostrar_en_pdf`.
- `grupo_alternativa`.
- `alternativa_seleccionada`.

Los valores por defecto deben preservar exactamente el comportamiento actual.

### Migración B — versiones

Nuevos conceptos recomendados:

```text
presupuesto_versiones
- id
- presupuesto_id
- numero_version
- fecha
- motivo
- estado
- datos_snapshot
- pdf_snapshot opcional
- total
- created_at
```

El presupuesto actual puede seguir siendo el documento editable, mientras que cada versión enviada/aprobada queda congelada.

### Migración C — proyecto y cambios

```text
proyectos
- id
- presupuesto_id
- nombre
- estado
- fecha_inicio
- fecha_estimada_fin
- fecha_fin
- notas

cambios_alcance
- id
- proyecto_id
- numero
- descripcion
- estado
- diferencia_total
- fecha

cambio_alcance_items
- id
- cambio_id
- tipo
- nombre
- cantidad
- precio
- importe
```

### Migración D — pagos

```text
pagos
- id
- presupuesto_id o proyecto_id
- factura_id opcional
- fecha
- importe
- moneda
- metodo
- referencia
- estado
- comprobante
- notas
```

### Migración E — configuración regional

Campos opcionales de configuración:

- `mostrar_datos_fiscales`.
- `mostrar_numero_control`.
- `mostrar_tasa_cambio`.
- `mostrar_total_bs`.
- `mostrar_datos_bancarios`.
- `mostrar_retenciones`.
- `mostrar_clausula_cambiaria`.
- `metodos_pago_configurados`.

No deben aparecer en el creador si están desactivados.

## 6. Orden técnico de implementación

### Fase 1 — Motor

1. Extraer las reglas de cálculo a un servicio aislado.
2. Definir una única función de totales.
3. Cubrir cantidad directa y mediciones manuales.
4. Añadir coste interno opcional.
5. Añadir costes adicionales.
6. Añadir alternativas y opcionales.
7. Actualizar pantalla, detalle, CSV y PDF.

### Fase 2 — Catálogos

1. Ampliar catálogo de partidas.
2. Ampliar catálogo de productos.
3. Mejorar autocompletado existente.
4. Añadir actualización de precios.
5. Añadir importación/exportación de catálogos.

### Fase 3 — Versiones y estados

1. Diseñar transición de estados.
2. Crear snapshots.
3. Añadir comparación.
4. Congelar PDF de versiones relevantes.
5. Integrar versiones con facturas.

### Fase 4 — Excel y búsqueda

1. Separar parser de Excel del JavaScript principal.
2. Añadir vista previa y validaciones.
3. Añadir búsqueda global.
4. Incorporar filtros y navegación contextual.

### Fase 5 — Proyecto, cambios y pagos

1. Conversión de aprobado a proyecto.
2. Cambios de alcance.
3. Pagos y anticipos.
4. Resumen financiero del proyecto.

### Fase 6 — Presentación y reportes

1. Plantillas visuales.
2. Resumen ejecutivo.
3. Anexos.
4. Descuentos y ahorro.
5. Dashboard.
6. Reportes.
7. Configuración venezolana opcional.

## 7. Criterios de aceptación

La evolución será correcta si:

- Un usuario nuevo puede crear un presupuesto sin activar funciones avanzadas.
- Activar una función desde Configuración no altera presupuestos antiguos de forma inesperada.
- Los totales básicos actuales siguen dando el mismo resultado.
- Una partida opcional no afecta el total hasta ser seleccionada.
- Una alternativa solo afecta el total cuando se selecciona.
- El PDF básico sigue siendo corto y claro.
- El PDF avanzado añade información sin romper la maquetación.
- Un presupuesto enviado puede congelarse como versión.
- Una factura conserva exactamente la versión aprobada que la originó.
- Un cambio de alcance no modifica silenciosamente el presupuesto original.
- Un pago no modifica el total contratado, solo el saldo pendiente.
- Las plantillas antiguas continúan cargando correctamente.
- Las funciones venezolanas pueden permanecer completamente ocultas.

## 8. Próximo paso después de Fase 0

La primera implementación debe ser la extracción del motor de cálculos y la definición del contrato de datos para una línea de presupuesto. No se debe comenzar todavía por nuevas pantallas ni por el rediseño del PDF.

El orden recomendado es:

```text
reglas de cálculo → modelo compatible → pruebas → interfaz básica → PDF → funciones avanzadas
```

Esto permite añadir capacidades sin convertir el creador en un formulario complejo.
