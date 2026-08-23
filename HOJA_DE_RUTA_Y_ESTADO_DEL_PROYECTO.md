# Hoja de ruta y estado del proyecto

Fecha de actualización: 2026-08-16
Proyecto: Generador de presupuestos para remodelación  
Estado: Fases 0 a 10 completadas

Este documento es la referencia principal para continuar el desarrollo en una sesión futura. Describe qué se decidió, qué se implementó, qué falta y cuál debe ser el siguiente paso.

---

# 1. Objetivo del producto

Construir un generador de presupuestos profesional para empresas de remodelación de viviendas, especialmente proyectos de gama media y alta, manteniendo tres características esenciales:

1. Crear un presupuesto rápido y sencillo.
2. Permitir funciones avanzadas solo cuando sean necesarias.
3. Generar documentos profesionales y útiles para la venta y ejecución de la obra.

El producto no debe convertirse en un formulario enorme. La experiencia principal debe seguir siendo:

```text
Seleccionar cliente
    ↓
Añadir capítulos
    ↓
Añadir partidas
    ↓
Revisar cantidades y precios
    ↓
Guardar
    ↓
Generar PDF
```

---

# 2. Decisiones de alcance

## 2.1 Funciones que sí se van a desarrollar

- Motor de cálculos económico.
- Costes internos y márgenes.
- Gastos indirectos e imprevistos.
- Alternativas de presupuesto.
- Partidas incluidas, opcionales y excluidas.
- Catálogo avanzado de partidas.
- Catálogo avanzado de productos.
- Autocompletado y recomendaciones.
- Importación profesional de Excel/CSV.
- Búsqueda global.
- Estados ampliados.
- Versiones de presupuestos.
- Conversión de presupuesto aprobado a proyecto.
- Cambios de alcance.
- Anticipos y pagos.
- Plantillas de PDF.
- Resumen ejecutivo y anexos.
- Ahorros y descuentos visibles.
- Dashboard avanzado.
- Reportes.
- Funciones específicas para Venezuela.

## 2.2 Funciones descartadas

Estas funciones no deben implementarse salvo que se cambie expresamente la decisión:

- Fórmulas geométricas automáticas.
- Largo × ancho.
- Cálculo automático de áreas.
- Cálculo automático de perímetros.
- Cálculo automático de volúmenes.
- Deducción automática de puertas y ventanas.
- Tipos de medición avanzados.

El sistema continuará usando:

- Cantidad directa.
- Mediciones manuales por zonas o conceptos.
- Suma automática de mediciones.
- Unidad editable.

## 2.3 Seguridad

La aplicación se considera actualmente local y no expuesta a la red. La seguridad, autenticación, usuarios y operación multiusuario quedan fuera del alcance actual salvo que se solicite expresamente lo contrario.

---

# 3. Estado actual por fases

## Fase 0 — Auditoría y diseño

Estado: **COMPLETADA**.

Documento técnico:

```text
docs/FASE_0_AUDITORIA_Y_DISENO.md
```

Se realizó:

- Inventario de modelos.
- Inventario de rutas.
- Revisión del constructor JavaScript.
- Revisión de plantillas.
- Revisión del PDF.
- Revisión de catálogos.
- Revisión de facturación.
- Diseño de nuevas entidades.
- Diseño del modo básico y avanzado.
- Criterios de aceptación.
- Orden técnico de implementación.

Commit asociado:

```text
c4c23e9 docs: define phase zero audit and product architecture
```

## Fase 1 — Motor económico y funciones avanzadas

Estado: **COMPLETADA**.

Archivo principal añadido:

```text
app/services/calculations.py
```

Se implementó:

- Motor centralizado de cálculos.
- Redondeo comercial a dos decimales.
- Subtotal.
- Base imponible.
- Descuento.
- IVA.
- Total.
- Coste interno.
- Margen estimado.
- Coste de materiales.
- Coste de mano de obra.
- Otros costes.
- Desperdicio.
- Gastos indirectos.
- Imprevistos.
- Transporte.
- Otros cargos.
- Modo básico sin funciones avanzadas.
- Modo avanzado configurable.

La configuración permite activar:

- Modo avanzado.
- Costes internos.
- Alternativas.
- Cargos adicionales.

Se actualizaron:

- Modelos SQLAlchemy.
- Migraciones SQLite.
- Constructor de presupuestos.
- Cálculos del navegador.
- Vista de detalle.
- PDF.
- Validaciones del servidor.
- Duplicación de presupuestos.

Commit principal:

```text
d183204 feat: add configurable advanced budget calculation engine
```

## Fase 2 — Alternativas y partidas opcionales

Estado: **COMPLETADA**.

Se implementó:

- Partida incluida.
- Partida opcional.
- Partida alternativa.
- Partida no incluida.
- Partida provisional.
- Partida sujeta a medición.
- Grupo de alternativas.
- Selección de alternativa.
- Validación para evitar dos alternativas activas dentro del mismo grupo.
- Totales separados de incluidos, opcionales y alternativas.
- Etiquetas en el PDF.
- Presentación de costes opcionales y alternativos.
- Selección automática en el editor para alternativas del mismo grupo.

Commit principal:

```text
544ecf4 feat: complete configurable alternatives and optional items
```

---

# 4. Funcionamiento actual del modo básico

El modo básico debe mantenerse como la experiencia principal.

El usuario ve:

- Cliente.
- Datos de obra.
- Capítulos.
- Nombre de partida.
- Cantidad.
- Unidad.
- Precio unitario.
- Importe.
- Descripción.
- Mediciones manuales.
- Producto opcional.
- Descuento.
- IVA.
- Condiciones.

No debe ver, salvo que se active desde Configuración:

- Costes internos.
- Margen.
- Alternativas.
- Opcionales.
- Gastos indirectos.
- Imprevistos.
- Cargos adicionales.

---

# 5. Funcionamiento actual del modo avanzado

Cuando se activa el modo avanzado, el presupuesto puede utilizar:

- Tipo de partida.
- Selección de partida.
- Grupo de alternativa.
- Costes internos.
- Desperdicio.
- Gastos adicionales.
- Margen estimado.

El modo avanzado se puede activar globalmente desde Configuración o por presupuesto cuando la capacidad está disponible.

Los presupuestos antiguos conservan su funcionamiento básico salvo que se editen y se activen expresamente las funciones avanzadas.

---

# 6. Modelo de datos actual relevante

## Cliente

```text
Cliente
- nombre
- RIF
- país
- teléfono
- email
- dirección
```

## Presupuesto

Incluye actualmente:

- Número.
- Año.
- Fecha.
- Título.
- Dirección de obra.
- Código postal.
- Validez.
- Moneda.
- Tasa de cambio.
- IVA.
- Descuento.
- Estado.
- Notas.
- Condiciones.
- Portada.
- Resumen.
- Firmas.
- Foto del proyecto.
- Firma del cliente.
- Activación del modo avanzado.
- Gastos indirectos.
- Imprevistos.
- Transporte.
- Otros cargos.

## Partida de presupuesto

Incluye:

- Nombre.
- Descripción.
- Unidad.
- Cantidad directa.
- Precio unitario.
- Mediciones manuales.
- Producto presupuestado.
- Tipo de partida.
- Selección.
- Grupo de alternativa.
- Coste de materiales.
- Coste de mano de obra.
- Otros costes.
- Desperdicio.
- Margen objetivo informativo.

## Catálogo de partidas

Actualmente incluye:

- Nombre.
- Descripción.
- Precio unitario.
- Unidad.
- Categoría.
- Contador de usos.

## Catálogo de productos

Actualmente incluye:

- Nombre.
- Descripción.
- Precio.
- Unidad.
- Categoría.
- Imagen.

## Facturas

Actualmente se generan desde presupuestos aprobados y copian una estructura simplificada. La mejora futura deberá convertirlas en documentos congelados vinculados a una versión concreta del presupuesto.

---

# 7. Pendientes de la Fase 2 que conviene revisar antes de continuar

Aunque la Fase 2 está implementada, antes de avanzar conviene hacer una prueba visual y funcional completa de:

1. Crear un presupuesto básico.
2. Crear un presupuesto avanzado.
3. Crear una partida opcional.
4. Crear dos alternativas del mismo grupo.
5. Seleccionar una alternativa.
6. Intentar seleccionar dos alternativas del mismo grupo.
7. Guardar y editar el presupuesto.
8. Duplicarlo.
9. Exportarlo a CSV.
10. Generar el PDF.
11. Comprobar el detalle de totales.
12. Cargar una plantilla.
13. Restaurar un presupuesto antiguo.

Si durante esa revisión aparecen problemas visuales, deben corregirse antes de comenzar la Fase 3.

---

# 8. Fase 3 — Catálogos y autocompletado

Estado: **COMPLETADA** (2026-08-06).

## Resultado implementado

Los datos avanzados viven en los catálogos y el constructor mantiene su flujo compacto. Las bases existentes se migran de forma aditiva al abrir la aplicación, sin requerir recrear la base de datos.

### Catálogo de partidas

Se añadieron como datos opcionales:

- Código interno y subcategoría.
- Coste de materiales, mano de obra y otros costes.
- Tiempo estimado, proveedor y rendimiento informativo.
- Desperdicio recomendado.
- Imagen y notas técnicas.
- Fecha de actualización de precio.
- Registro de uso y último uso.

La ficha principal conserva nombre, unidad, precio, categoría y descripción. El resto aparece bajo el desplegable **«Datos técnicos y de costes»**.

### Catálogo de productos

Se añadieron como datos opcionales:

- Marca, modelo, SKU y proveedor.
- Precio de compra y precio de venta (el precio unitario histórico se conserva como venta).
- Fecha automática de actualización de precio.
- Color, acabado, formato y tiempo de entrega.
- Variantes.
- Ficha técnica PDF validada.
- Foto principal y galería de imágenes.
- Registro de uso y último uso.

Se ampliaron los CSV de ambos catálogos y se puede aplicar un ajuste porcentual de precios de venta sin modificar presupuestos existentes.

### Autocompletado y recomendaciones

Se mejoró la base existente de `app/static/js/budget_form.js`, sin duplicar el constructor:

- Orden por uso reciente y frecuencia de uso.
- Coincidencia por palabras, tolerante a acentos, sobre nombre, descripción, categoría, códigos y datos de proveedor.
- Eliminación de sugerencias duplicadas.
- Carga de descripción, unidad, precio, categoría y costes recomendados de la partida cuando el modo avanzado está activo.
- Sugerencias de productos relacionadas con la categoría de la partida al enfocar el campo de producto.
- Datos comerciales en cada sugerencia de producto (marca, modelo, SKU, categoría y fecha del último precio).

## Principio de interfaz preservado

El creador básico sigue mostrando únicamente:

- Nombre.
- Unidad.
- Precio.
- Descripción.

Los datos de costes, producto, recomendaciones y alternativas continúan dentro de paneles opcionales o del modo avanzado.

---

# 9. Fase 4 — Importación y búsqueda global

Estado: **COMPLETADA** (2026-08-06).

## Importador CSV / Excel

Se creó el asistente accesible desde:

```text
Presupuestos → Importar CSV / Excel
```

El flujo implementado es:

1. Cargar un archivo `.csv` o `.xlsx`, o pegar filas desde Excel.
2. Indicar si la primera fila contiene encabezados.
3. Analizar y mostrar una vista previa de hasta 1.000 filas.
4. Detectar y permitir reasignar cada columna.
5. Validar en el servidor.
6. Revisar errores y advertencias.
7. Crear un presupuesto nuevo o añadir las partidas a uno existente.

Columnas soportadas:

- Capítulo.
- Partida.
- Descripción.
- Unidad.
- Cantidad.
- Precio unitario.
- Categoría.
- Tipo de partida opcional.

El lector acepta números con coma o punto decimal y entiende tipos como incluida, opcional, alternativa, no incluida, provisional y sujeta a medición.

Las advertencias cubren:

- Nombre de partida vacío (error bloqueante).
- Cantidad o precio vacío / inválido.
- Valores negativos (error bloqueante).
- Unidades no habituales.
- Filas duplicadas.
- Capítulos que aún no existen en el presupuesto destino (se crearán al confirmar).

La validación se repite en el servidor al confirmar: el navegador no puede saltarse las reglas ni crear líneas sin revisar.

Archivo técnico añadido:

```text
app/services/importer.py
```

Dependencia añadida:

```text
openpyxl>=3.1
```

## Búsqueda global

Se añadió la pantalla **Buscar** en el menú lateral:

```text
/buscar?q=texto
```

Agrupa y enlaza directamente a resultados de:

- Clientes.
- Presupuestos.
- Facturas.
- Partidas.
- Productos.
- Plantillas.
- Notas internas de presupuestos.

Busca también por números de documento, RIF, SKU, marca, modelo, proveedor, código interno y descripciones relevantes. Los proyectos se incorporarán a este mismo buscador cuando exista su entidad en la Fase 6.

---

# 10. Fase 5 — Estados y versiones

Estado: **COMPLETADA** (2026-08-07).

## Resultado implementado

- Estados ampliados: borrador, en revisión, enviado, cambios solicitados, reenviado, aprobado, aprobado parcialmente, en ejecución, finalizado, rechazado, vencido, cancelado y archivado.
- Instantáneas inmutables y numeradas de cada presupuesto, creadas manualmente o automáticamente al enviar, reenviar, aprobar, aprobar parcialmente, iniciar ejecución o finalizar.
- Vista de una versión congelada y comparación de dos versiones.
- Al editar un documento ya congelado se crea una nueva versión y se puede registrar el motivo.
- Las facturas quedan vinculadas a una versión aprobada concreta; si faltaba, se crea al facturar.
- La migración SQLite es aditiva y conserva las bases existentes.

## Estados propuestos

```text
Borrador
En revisión
Enviado
Cambios solicitados
Reenviado
Aprobado
Aprobado parcialmente
En ejecución
Finalizado
Rechazado
Vencido
Cancelado
Archivado
```

No es obligatorio activar todos. Deben poder configurarse o mantenerse ocultos si la empresa no los necesita.

## Versiones

Crear una entidad `presupuesto_versiones` con:

- Presupuesto asociado.
- Número de versión.
- Fecha.
- Motivo del cambio.
- Estado.
- Total.
- Snapshot del contenido.
- PDF congelado opcional.

Reglas:

- Editar un borrador puede seguir modificando el documento actual.
- Un presupuesto enviado o aprobado debe poder congelarse.
- Los cambios posteriores deben crear una nueva versión.
- Una factura debe indicar qué versión la originó.
- Debe poder compararse una versión con otra.

---

# 11. Fase 6 — Proyecto, cambios de alcance y pagos

Estado: **COMPLETADA** (2026-08-07).

## Resultado implementado

- Conversión directa de presupuestos aprobados o aprobados parcialmente a proyectos.
- El proyecto queda vinculado al presupuesto y a su versión aprobada, preservando el total contratado.
- Ficha de proyecto con fechas, estado, notas y resumen: contratado, cambios aprobados, total actual, pagado y saldo pendiente.
- Cambios de alcance numerados, con partidas agregadas o eliminadas, estado y diferencia calculada.
- Registro de pagos y anticipos por proyecto: fecha, importe, moneda, método, referencia, estado y notas.
- Navegación independiente de proyectos e integración desde el presupuesto aprobado.

## Conversión a proyecto

Desde un presupuesto aprobado:

```text
Convertir en proyecto
```

El proyecto debe conservar:

- Presupuesto aprobado.
- Versión aprobada.
- Capítulos.
- Partidas.
- Total contratado.
- Fechas.
- Estado.
- Pagos.
- Cambios.
- Notas.
- Fotografías.

## Cambios de alcance

Crear cambios numerados:

```text
Cambio Nº 001
Cambio Nº 002
Cambio Nº 003
```

Cada cambio tendrá:

- Descripción.
- Partidas añadidas.
- Partidas eliminadas.
- Diferencia de precio.
- Diferencia de tiempo si posteriormente se incorpora cronograma.
- Estado.
- Fecha.
- Aprobación.
- PDF del cambio.

Estados:

```text
Borrador
Enviado
Aprobado
Rechazado
Aplicado
```

## Pagos

Crear una entidad `pagos` con:

- Proyecto o presupuesto.
- Factura opcional.
- Fecha.
- Importe.
- Moneda.
- Método.
- Referencia.
- Estado.
- Comprobante.
- Notas.

Debe diferenciarse:

```text
Total contratado
Total facturado
Total pagado
Saldo pendiente
```

---

# 12. Fase 7 — PDF y presentación comercial

Estado: **COMPLETADA** (2026-08-07).

## Resultado implementado

- Selector por presupuesto de estilos: elegante, técnica, minimalista, corporativa, compacta y editorial.
- Se consolidaron las opciones comerciales existentes: portada, resumen ejecutivo, detalle, firmas, alternativas y opcionales.
- Bloque opcional de ahorro con precio original, descuento y precio final.
- Gestión de anexos PDF (fichas, planos y documentos), con índice opcional en el PDF principal.
- Las opciones son propias del documento y no recargan el modo básico.

## Plantillas visuales

Proponer varias opciones:

- Elegante.
- Técnica.
- Minimalista.
- Corporativa.
- Compacta.
- Editorial.

## Opciones configurables

- Portada.
- Resumen ejecutivo.
- Detalle completo.
- Mediciones.
- Productos.
- Alternativas.
- Opcionales.
- Firmas.
- Datos bancarios.
- Fotografías.
- Anexos.
- Ahorro y descuentos.

## Anexos

Permitir anexar:

- Fichas técnicas.
- Fotografías.
- Planos.
- Condiciones ampliadas.
- Cronograma cuando exista.
- Documentos de proveedores.

## Ahorro

Mostrar opcionalmente:

```text
Precio original
Descuento comercial
Ahorro obtenido
Precio final
```

El ahorro debe ser visible solo si el usuario lo activa desde Configuración o desde el documento.

---

# 13. Fase 8 — Dashboard y reportes

Estado: **COMPLETADA** (2026-08-07).

## Resultado implementado

- Dashboard ampliado con actividad mensual, enviados, tasa de aprobación, importe promedio, margen estimado y proyectos activos.
- Centro de reportes con período configurable y vistas de ventas, presupuestos por estado y proyectos/cobros.
- Exportación CSV de ventas, estados y situación financiera de proyectos.

## Dashboard

Añadir indicadores:

- Presupuestos del mes.
- Presupuestos enviados.
- Presupuestos aprobados.
- Presupuestos vencidos.
- Tasa de aprobación.
- Importe promedio.
- Importe aprobado.
- Descuentos concedidos.
- Margen estimado.
- Clientes activos.
- Productos más usados.
- Partidas más usadas.

## Reportes

Exportar a CSV y PDF:

- Ventas por período.
- Presupuestos por cliente.
- Presupuestos por estado.
- Productos utilizados.
- Partidas más utilizadas.
- Descuentos.
- Rentabilidad.
- Pagos pendientes.
- Cambios de alcance.
- Proyectos activos.

---

# 14. Fase 9 — Funciones específicas para Venezuela

Estado: **COMPLETADA, OPCIONAL Y CONFIGURABLE** (2026-08-07).

## Resultado implementado

- Activación global de capacidades regionales sin afectar el modo básico.
- Número de control, fecha de tasa, equivalente en bolívares, retenciones, operación exenta y cláusula cambiaria por documento.
- Datos bancarios y métodos de pago configurables en el PDF.
- La tasa y su fecha se almacenan en el presupuesto para preservar documentos históricos.

Estas funciones no deben aparecer en el creador si están desactivadas.

Opciones:

- Mostrar RIF.
- Mostrar número de control.
- Mostrar datos fiscales.
- Mostrar tasa de cambio.
- Mostrar fecha de tasa.
- Mostrar equivalente en Bs.
- Activar retenciones.
- Activar operaciones exentas.
- Activar cláusula de ajuste cambiario.
- Mostrar datos bancarios.
- Pago móvil.
- Transferencia.
- Zelle.
- USDT.
- Series de documentos.

La tasa debe quedar guardada en cada documento para que un PDF antiguo no cambie al actualizarse la tasa actual.

---

# 15. Orden recomendado para continuar

El orden correcto es:

```text
1. Revisar visualmente Fases 2, 3 y 4
2. Revisión integral, pruebas visuales y definición de una nueva hoja de ruta
```

No comenzar Fase 5 sin haber probado bien los tipos de partida y alternativas, porque las versiones deberán congelar exactamente esa información.

No comenzar Fase 7 sin definir antes qué información debe quedar congelada en una versión.

---

# 16. Criterios generales de aceptación

Cada fase debe cumplir:

- El modo básico no se vuelve más complicado.
- Las funciones avanzadas permanecen ocultas cuando están desactivadas.
- Los presupuestos antiguos siguen abriendo correctamente.
- Los totales se calculan igual en navegador, detalle, CSV y PDF.
- Las plantillas antiguas siguen cargando.
- Las alternativas no alteran el total hasta ser seleccionadas.
- Los opcionales aparecen separados del total incluido.
- Los cambios no modifican silenciosamente documentos congelados.
- Los PDFs antiguos conservan su información.
- Cada fase se prueba antes de pasar a la siguiente.
- Al terminar cada fase se crea un commit y se hace push.

---

# 17. Cómo continuar en una sesión futura

Antes de modificar código, leer este documento y revisar:

```text
docs/FASE_0_AUDITORIA_Y_DISENO.md
HOJA_DE_RUTA_Y_ESTADO_DEL_PROYECTO.md
```

Después:

1. Comprobar `git status`.
2. Revisar el último commit.
3. Revisar la fase marcada como pendiente más próxima.
4. No repetir funciones ya implementadas.
5. Mantener fuera las mediciones geométricas salvo nueva autorización.
6. Mantener el modo básico simple.
7. Probar la fase completa.
8. Crear commit descriptivo.
9. Hacer push a `arena/019fda4e-presupuestos`.

Siguiente fase prevista:

```text
Todas las fases de la hoja de ruta actual están completadas.
```


---

# 18. Revisión final de calidad (2026-08-07)

Se realizó una revisión transversal de las fases 0 a 9:

- Validación de sintaxis de los módulos Python principales con `py_compile`.
- Arranque de aplicación y revisión HTTP de Inicio, presupuestos, editor, detalle, proyectos, reportes, configuración y consulta de versiones.
- Generación real de un PDF de presupuesto.
- Prueba de transición a aprobado, creación de versión congelada y conversión del presupuesto a proyecto.
- Revisión de migraciones SQLite aditivas para versiones, proyectos, pagos, anexos y campos regionales.
- Se corrigió la validación defensiva de la fecha de tasa de cambio al crear presupuestos.

El árbol de trabajo queda limpio y las fases 0 a 9 están listas para uso y revisión visual en una instalación con datos reales.

---

# 19. Fase 10 — Descomposición de costes editable en el generador (2026-08-07)

Estado: **COMPLETADA**.

## Problema que resuelve

El generador permitía crear/editar partidas, pero el «rendimiento», el
«precio por hora» o el «precio por kg» de cada recurso solo podían tocarse en
la página técnica de una partida CYPE ya importada. Las partidas nuevas o
del catálogo usaban campos de coste planos (un único número por categoría)
que no se podían desglosar ni ajustar recurso a recurso.

## Resultado implementado

Toda partida del generador dispone ahora de una sección **«Descomposición de
costes (recursos)»** dentro de su panel expandible, con filas ordenadas tipo
tabla (como la captura de referencia):

```text
Categoría | Código | Und. | Descripción | Rendimiento | Precio unit. | Importe | ✕
Mano de obra | MO001 | h | Oficial solador | 0,537 | 24,41 | 13,11 | ✕
Materiales   | MT002 | kg | Mortero cola  | 8,5   | 0,23  | 1,96  | ✕
```

- **Modificable**: rendimiento, precio unitario (por hora, por kg, por m³…),
  categoría de coste (mano de obra, materiales, directos complementarios,
  otros), código, unidad y descripción. Fila de porcentaje (unidad «%») con
  precio derivado de solo lectura, igual que en CYPE.
- **Con lógica**: el importe de cada fila se recalcula en vivo
  (Rendimiento × Precio unitario); los subtotales por categoría, la base de
  los % complementarios y el **coste directo por unidad** se muestran en un
  resumen bajo la tabla y alimentan beneficio/margen y totales al instante.
- **Ordenada**: mismas reglas de redondeo y de cascada que el formato CYPE;
  las filas de subtotal/total se muestran derivadas y las de passthrough de
  matrices importadas permanecen ocultas pero se conservan completas.
- **Automática**: las partidas del catálogo que traen costes recomendados
  crean sus filas editables al insertarse; las partidas antiguas con costes
  planos se convierten en filas (con botón «🧮 Crear filas desde los costes
  actuales»); una partida en blanco empieza sin filas y se van agregando
  con «+ Agregar recurso».
- **CYPE preservado**: al editar rendimientos/precios de una partida
  importada de CYPE, la matriz original (celdas, fórmulas, rangos, .xlsx) se
  conserva y se sincroniza; los costes se recalculan con las reglas del
  formato original. El archivo sigue descargable desde la partida.

## Detalles técnicos

- `DescomposicionPartida.origen` (nuevo): `cype` (matriz importada) o
  `manual` (creada/editada en el generador). Migración aditiva + backfill de
  las existentes según tuvieran `archivo_origen`.
- `DescomposicionFila.categoria` (nueva): categoría explícita de coste; la
  derivación grupo/código se usa solo como respaldo. Respetada también en la
  página técnica (`/descomposicion`) y en `recalcular_descompuesto_cype`.
- El formulario del generador serializa cada fila con campos paralelos
  `d_*` (tipo, grupo, categoría, código, unidad, descripción, rendimiento,
  precio, número de fila, celdas JSON y fórmulas JSON) y el servidor
  reconstruye la descomposición en cada guardado con `_construir_descomposicion_desde_form`,
  recalculando la cascada (importes, subtotales, % y coste directo) y
  sincronizando la matriz (`_sincronizar_celdas_descompuesto`).
- Las descomposiciones manuales aplican el desperdicio de la partida sobre
  el coste directo; las CYPE conservan el coste directo autoritativo del
  archivo (comportamiento previo intacto).
- Borradores locales, plantillas, duplicado de partidas/capítulos y
  duplicado de presupuestos conservan las filas (como array o como objeto
  con `origen` + `filas`).
- Página técnica y detalle distinguen «🧮 Descomposición de costes» (manual)
  de «📐 Descompuesto CYPE» (matriz importada).

## Pruebas realizadas

- jsdom: render de partidas manuales y CYPE, filas visibles/ocultas,
  edición en vivo, filas %, subtotales, coste directo, agregar/eliminar
  filas, serialización `d_*`, autosave, restauración de borrador (forma
  array) y duplicado de partida.
- Servidor: creación y edición de presupuesto con descomposición manual
  (incluida fila %), importación CYPE real (RBE010) y edición de sus
  recursos vía formulario, sincronización de celdas de la matriz, PDF,
  detalle y página técnica.
- Migración: base antigua sin `origen`/`categoria` migra y marca las
  descomposiciones con archivo como `cype`.

## Complementos (misma sesión)

- **Botón «⇧ Importar desde Excel» en el tab Partidas**: abre el asistente
  de importación en **modo catálogo** (`/presupuestos/importar?destino=catalogo`).
  Las partidas detectadas (CYPE o tabulares) se guardan en el Catálogo de
  Partidas con código interno, unidad, descripción y costes por categoría;
  las tabulares se agrupan por el capítulo del archivo. No crea ni modifica
  presupuestos. Los duplicados por nombre se omiten con aviso.
- Las partidas CYPE importadas a un presupuesto conservan ahora también su
  **código y costes** en la entrada de catálogo automática.
- **Error «Falta el componente para leer archivos Excel (.xlsx)»**: era una
  instalación sin `openpyxl` (los lanzadores no lo comprobaban). Se añadió
  `openpyxl` a la comprobación de dependencias de INICIAR.bat/.sh/.command y
  CREAR_INSTALADOR.bat, y el mensaje de error ahora indica cómo resolverlo
  (reabrir con el lanzador o `pip install openpyxl`).

---

# 20. Fase 11 — Estimación de tiempos de obra (2026-08-10)

## Resultado implementado

Aprovechando que las partidas ya están muy bien especificadas (descompuestos
CYPE con rendimientos por hora, tiempos estimados en el catálogo y costes de
mano de obra), se añadió el cálculo del **tiempo estimado de ejecución de la
obra** en tres niveles:

1. **Indicador básico en el creador** (`budgets/form.html` + `editor/tiempos.js`):
   fila «⏱ Tiempo estimado de obra» en la tarjeta de totales y chip en la
   barra sticky. Se recalcula en vivo con cada cambio: «≈ 104,4 h · 13,0 días».
   Si hay partidas sin datos, avisa y enlaza al detalle (cuando el
   presupuesto ya está guardado).

2. **Página de detalle completa** (`GET /presupuestos/<id>/tiempos` →
   `budgets/tiempos.html`): tarjetas resumen (horas totales, días laborables
   con selector de cuadrillas en paralelo, semanas, cobertura de datos),
   barra de participación por capítulo, tabla por partida con **fuente de
   cada estimación** y desplegable con las **filas de rendimiento** que
   aportan las horas (recurso, unidad, rendimiento y horas por unidad).

3. **Página del descompuesto** (`budgets/decomposition.html`): nueva tarjeta
   «⏱ Tiempo por unidad» que muestra las horas que ocupan los recursos del
   descompuesto por unidad de partida y las horas totales para la cantidad
   medida.

## Motor de cálculo (`app/services/tiempos.py`)

Fuentes de horas por partida, en orden de prioridad:

1. **Descompuesto** (medido): filas de recurso con unidad de tiempo
   (`h`, `hr`, `hora`… → ×1; `día`, `jornada`… → ×horas de jornada). Las
   filas de mano de obra suman «horas de mano de obra»; el resto de filas con
   unidad de tiempo (maquinaria, equipos) se informa aparte como «horas de
   equipos». Las filas `%` y las de materiales (kg, m³…) no cuentan tiempo.
2. **Catálogo** (medido): si la partida no tiene descompuesto con horas pero
   viene del catálogo y este tiene `tiempo_estimado_horas`, se usa ese valor
   como horas por unidad.
3. **Por coste** (estimado, configurable): horas ≈ `coste_mano_obra` ÷
   `tarifa_hora_media`. Se marca como «💰 Por coste» y se puede desactivar
   en Configuración.

Solo suman las partidas activas (excluidas y alternativas/opcionales no
seleccionadas quedan fuera, igual que en el motor económico). Totales: horas,
días laborables (÷ jornada configurable, por defecto 8 h), semanas (÷5) y
cobertura (partidas con datos / partidas activas).

## Configuración nueva (`Configuracion`)

- `horas_jornada` (float, 8): horas por jornada laboral.
- `tarifa_hora_media` (float, 8): moneda/h para la estimación por coste.
- `estimar_tiempo_por_coste` (bool, True): permite la estimación por coste.

Se guardan desde `settings.html` (nuevo bloque «⏱ Estimación de tiempos de
obra») y migran automáticamente (lista de columnas de `configuracion`).

## Pruebas

- `tests/test_tiempos.py`: factor de unidades, descompuesto → horas por
  unidad (incluye filas % y no temporales), categoría explícita, prioridad de
  fuentes (descompuesto > catálogo > coste > sin datos), partidas no activas
  excluidas, desglose por capítulo y resumen de fuentes.
- Suite completa: 32 pruebas OK (incluye compilación de todas las plantillas
  y rutas).
- Manual: presupuesto P-2026-002 con los cuatro casos (descompuesto con
  rendimientos, catálogo con tiempo estimado, solo coste de mano de obra y
  sin datos) → 104,4 h ≈ 13 días, cobertura 75 %, y página de detalle con los
  cuatro tipos de insignia.

## Pendientes / ideas siguientes

- **Resumen de tiempos en el PDF — DECIDIDO (19/08/2026): NO para el cliente.**
  La estimación de tiempos **ya existe en la app** (Fase 11: horas por
  partida, días con cuadrillas, semanas, cobertura — creador y página
  `/presupuestos/<id>/tiempos`). Es información interna con ventaja comercial:
  el PDF que ve el cliente final **nunca** lleva horas ni plazos calculados
  (evita reclamaciones tipo «el papel dice 5 h y se hizo en 2»). Si algún día
  se quisiera imprimir, sería una **versión imprimible interna para la
  empresa**, nunca el PDF del cliente.
- ~~Plazo por capítulo con dependencias (diagrama de Gantt)~~ — **descartado
  (19/08/2026)**: la estimación de tiempos existente ya cubre la planificación
  interna (desglose por capítulo, días con cuadrillas, semanas); la idea de
  barras encadenadas no aportaba nada nuevo.
- Guardar una estimación «congelada» en cada versión del presupuesto.

---

# 21. Fase 12 — Recetas de Estancias (Packs de Reforma por Estancia / Armado de Capítulos con 1 Clic - `Alt+R`) (2026-08-11)

Estado: **COMPLETADA**.

## Problema que resuelve

Cotizar una estancia de remodelación de gama alta (un baño principal de lujo,
una cocina integral con isla, o una renovación de suelos de 100 m²) exigía al
comercial o técnico insertar manualmente entre 10 y 12 partidas una por una,
buscando en el catálogo y ajustando cantidades y precios en el constructor.
Esto tomaba de 30 a 45 minutos por habitación y creaba el riesgo de olvidar
partidas críticas (impermeabilizaciones, pases de fontanería, juntas epóxicas).

## Resultado implementado

- **Modelo `RecetaEstancia` en base de datos**: guarda plantillas de capítulos
  completos con un multiplicador o coeficiente proporcional respecto a la medida
  base de la estancia (`m²` o `und`). Migración SQLite aditiva e idempotente.
- **6 Presets de Reforma de Lujo precargados** en `app/seeds.py` (y restaurables
  con el botón «⚡ Restaurar Presets» de `/recetas`):
  1. *Baño Principal de Lujo* (8.0 m² - 12 partidas: demolición, impermeabilización, piso porcelánico, revestimiento mural, cielo raso hidrófugo, plomería, iluminación LED, sanitario suspendido, mueble cuarzo, griferías empotradas y mampara de cristal).
  2. *Cocina Integral de Lujo con Isla* (15.0 m² - 8 partidas: demolición, regularización, solado porcelánico gran formato, backsplash piedra sinterizada, circuitos fuerza, plomería lavaplatos/hielo, iluminación arquitectónica, tope de cuarzo/Neolith).
  3. *Reforma Integral de Suelos y Pisos de Lujo* (100.0 m² - 5 partidas: levantado, pasta autonivelante, solado gran formato/laminado AC5, fragüe epóxico, rodapié lacado).
  4. *Dormitorio Principal Suite con Vestidor* (24.0 m² - 6 partidas: alisado, pintura satinada premium, cielo raso luz indirecta, piso laminado con base acústica, tomacorrientes USB-C, vestidor modular lacado).
  5. *Sala / Comedor de Alta Gama con Luz Indirecta* (40.0 m² - 5 partidas: cielo raso arquitectónico candileja, alisado muros, pintura satinada, solado porcelánico, iluminación escenográfica LED dimmable).
  6. *Instalación Eléctrica e Iluminación Residencial Completa* (120.0 m² - 5 partidas: tablero 24 circuitos, cableado libre halógenos, tomacorrientes polarizados, downlights LED y tiras LED).
- **Gestión visual en `/recetas`**: catálogo organizado por categorías (Baños,
  Cocinas, Suelos, Habitaciones, Electricidad, Otros) donde se pueden crear
  nuevos packs, editar sus partidas y coeficientes, duplicarlos o eliminarlos.
- **Integración con el Constructor (`Alt+R` / botón «⚡ Pack de Estancia»)**:
  - Al presionar **`Alt+R`** (o el botón sticky/toolbar), se abre un modal de
    inserción instantánea.
  - Seleccionas el Pack e introduces la medida real de tu estancia (ej. `12 m²`).
  - Una tabla de vista previa calcula en vivo las cantidades proporcionales
    (`Coeficiente × Medida`) para los materiales/revestimientos y mantiene fijas
    las cantidades de piezas sanitarias o muebles (`tipo_calculo == 'fijo'`).
  - Al hacer clic en «⚡ Insertar en Presupuesto» (o presionar `Enter`), se
    inserta el capítulo completo y todas sus partidas en 1 segundo, renumera y
    recalcula los totales del presupuesto automáticamente.
- **Guardar cualquier Capítulo como Pack («💾 Guardar pack»)**:
  - En la barra de acciones de cada cabecera de capítulo en el constructor
    (junto a `+ Partida` y `⧉`), se añadió el botón **«💾 Guardar pack»**.
  - Permite guardar cualquier capítulo armado en el editor como una nueva
    `RecetaEstancia` en el catálogo de packs, calculando automáticamente los
    coeficientes proporcionales para reutilizarlo en presupuestos futuros.
- **Búsqueda Global (`/buscar`)**: las recetas se indizan por nombre,
  descripción y categoría, con acceso directo a su edición desde el buscador.

## Pruebas realizadas

- **`tests/test_recetas.py`**: cobertura de rutas web (`/recetas`), APIs JSON
  (`/recetas/api/list`, `/recetas/api/{id}`), creación por POST, guardado
  desde capítulo vía API, cálculo proporcional y fijo, duplicación, búsqueda
  global y restauración de presets iniciales.
- **Suite completa**: 48 pruebas OK (`.venv/bin/pytest -o pythonpath=.`).

---

# 22. Fase 13 — Panel de cuenta, contraseña y cierre de sesión (2026-08-14)

Estado: **COMPLETADA** (pendiente de validación real contra Supabase).

## Problema que resuelve

Tras iniciar sesión no existía ningún lugar donde la persona usuaria pudiera
ver o modificar sus propios datos. El único rastro de la sesión era un bloque
pequeño al final de la barra lateral con el email y un enlace de salida, y la
contraseña solo podía cambiarse saliendo de la aplicación y pidiendo un email
de recuperación. Faltaba lo más básico de cualquier SaaS: un panel de cuenta.

## Resultado implementado

- **Nueva página `/cuenta`** (`auth/account.html`), integrada en el layout de
  la aplicación (`base.html`) en lugar de ser una pantalla suelta como
  `/equipo` u `/organizaciones`. Contiene cuatro bloques: datos personales,
  cambio de contraseña, organizaciones y sesión.
- **Perfil editable** (`POST /cuenta/perfil`): actualiza `usuarios.nombre` y
  sincroniza `user_metadata.name` en Supabase. El email se muestra pero no se
  edita, con su estado de verificación.
- **Cambio de contraseña** (`POST /cuenta/clave`): exige la contraseña actual,
  **reautentica** contra GoTrue con `grant_type=password` y solo entonces
  llama a `PUT /auth/v1/user`. Al terminar cierra la sesión y obliga a entrar
  de nuevo. Incluida en el rate limiter local (10 intentos / 5 min por IP).
- **Organizaciones**: tabla con las membresías activas, el rol de cada una y
  la empresa seleccionada marcada como «Activa», con acceso directo para
  cambiar de empresa o crear otra.
- **Cierre de sesión mejorado** (`POST /salir`): además de borrar las cookies,
  revoca el refresh token en Supabase (`POST /auth/v1/logout`). Es
  *best-effort*: si Supabase no responde, la sesión local se cierra igual.
- **Barra lateral**: el bloque de sesión pasa a mostrar avatar con la inicial,
  nombre y los enlaces «Mi cuenta» / «Cerrar sesión», y se añade «Mi cuenta»
  en la sección Sistema de la navegación.

## Detalles técnicos y riesgos cubiertos

- **Sesión robada no basta para cambiar la contraseña.** GoTrue acepta
  `PUT /auth/v1/user` solo con el access token; la reautenticación previa con
  la contraseña actual cierra ese vector de secuestro de cuenta.
- **El cierre de sesión ya no puede revertirse solo.** `clear_auth_cookies`
  recibe ahora la petición y descarta cualquier renovación pendiente: sin eso,
  `RefreshedAuthCookieMiddleware` reescribía las cookies justo después de
  borrarlas cuando el access token se había renovado en la misma petición.
- **La organización activa no se cree por cookie.** `/cuenta` usa
  `get_authenticated_db` (no exige empresa elegida), así que la cookie se
  contrasta contra las membresías reales antes de marcar ninguna como activa.
- **El email no se edita** porque es la clave del vínculo con `auth.users` y
  el destinatario de las invitaciones pendientes; cambiarlo exige un flujo de
  reverificación que no está implementado.

## Pruebas realizadas

- **`tests/test_cuenta.py`** (10 pruebas): render del panel, actualización de
  perfil local + metadato remoto, rechazo de nombre vacío y de cambio de
  email, cambio de contraseña con reautenticación y borrado de cookies,
  contraseña actual incorrecta sin llegar a actualizar, validación de
  confirmación/longitud antes de contactar Supabase, revocación en `/salir`,
  cierre de sesión aunque Supabase falle, descarte de la renovación pendiente
  y cobertura de rate limiting en rutas con contraseña.
- **Suite completa**: 186 pruebas OK + 3 omitidas; 41 plantillas Jinja
  parseadas correctamente.
- **Manual**: panel revisado en el navegador con dos organizaciones,
  comprobando el marcado de la activa y que una cookie de organización ajena
  no marca ninguna.

## Pendientes / ideas siguientes

- Cambio de email con reverificación y transición del vínculo `auth_user_id`.
- Listado de sesiones activas por dispositivo con revocación individual.
- Eliminación de cuenta y salida voluntaria de una organización.
- Validación end-to-end real contra Supabase (sigue bloqueada en el sandbox).

---

# 23. Corrección — El enlace de recuperación aterrizaba en el login (2026-08-14)

Estado: **CORREGIDO** (bug de código; no requiere cambios de configuración).

## Síntoma reportado

El email de recuperación llegaba correctamente, pero al pulsar el enlace el
navegador mostraba la pantalla de inicio de sesión en lugar de la de nueva
contraseña, con esta forma de URL:

```text
/acceso?next=/#access_token=...&expires_in=3600&type=recovery
```

## Causa raíz real (bug propio) — corrige el diagnóstico inicial

**Primer diagnóstico, equivocado:** se atribuyó a que la Redirect URL no
estaba autorizada en Supabase. El usuario confirmó que **ya lo estaba desde
antes**, lo que obligó a revisar el código y descartó esa hipótesis.

**Causa verificada:** la aplicación enviaba `redirect_to` dentro del **cuerpo
JSON** de `POST /auth/v1/recover`. GoTrue no lo lee ahí. Su struct
`RecoverParams` (`internal/api/recover.go`) solo declara:

```go
type RecoverParams struct {
    Email               string `json:"email"`
    CodeChallenge       string `json:"code_challenge"`
    CodeChallengeMethod string `json:"code_challenge_method"`
}
```

No existe campo `redirect_to`, así que el valor se descartaba **en silencio**
—sin error ni aviso— y GoTrue caía al **Site URL**. El cliente oficial
`auth-js` lo envía como **parámetro de query** (`src/lib/fetch.ts`:
`qs['redirect_to'] = options.redirectTo`), no en el cuerpo.

Corrección aplicada en `app/auth.py`:

```text
POST /auth/v1/recover?redirect_to=https%3A%2F%2F<origen>%2Frestablecer-clave
body: {"email": "..."}
```

**Mismo bug latente en el registro:** `SignupParams` (`internal/api/signup.go`)
tampoco declara `redirect_to`, de modo que el email de confirmación también
habría caído al Site URL. Corregido igual y `/registro` pasa ahora
`public_app_url("/acceso")`.

Por qué el síntoma despistaba: al caer al Site URL (`/`), que exige sesión, la
app rebotaba a `/acceso`, y el navegador re-adjuntaba el fragmento en cada
salto. El fragmento **nunca viaja al servidor**, así que ninguna ruta podía
leer el token. El resultado es idéntico al de una Redirect URL sin autorizar,
que fue justo la pista falsa. Lección: ante este síntoma, verificar primero el
**formato de la petición** antes que la configuración remota.

Se decodificó el JWT del enlace para descartar un token inválido:
`type=recovery`, `amr.method=otp`, vigencia de 1 hora y email correcto. El
token siempre fue válido; solo aterrizaba donde nadie lo leía.

## Verificación

Captura HTTP real contra un servidor local que suplanta a GoTrue, comprobando
la petición exacta que sale (el correo real de la prueba se sustituyó aquí por
uno de ejemplo, E1-021):

```text
POST /auth/v1/recover?redirect_to=https%3A%2F%2Fcotizat-generador.vercel.app%2Frestablecer-clave
body: {"email": "persona@example.com"}
```

## Red de seguridad implementada en la aplicación

- **`app/static/js/recovery_redirect.js`**: se carga en `auth/access.html` y en
  `base.html` (los dos destinos a los que Supabase puede desviar). Si detecta
  `type=recovery` con `access_token` en el fragmento, reenvía a
  `/restablecer-clave` conservándolo íntegro. Si el enlace llega caducado
  (`error`/`error_code` sin token), desvía a `/recuperar-acceso` con un mensaje
  claro en vez de dejar a la persona mirando el login.
  - El token **permanece siempre en el fragmento**: no se copia a la query,
    donde acabaría en logs de servidor o en la cabecera `Referer`.
  - No actúa si ya se está en `/restablecer-clave` (no puede crear bucles), ni
    con anclas normales de la aplicación, ni con `type=magiclink`.
- **`/readyz`** publica ahora `recovery_redirect_url_esperada` con la URL exacta
  que debe autorizarse en Supabase, para diagnosticar esto de un vistazo. Es
  informativo y no hace fallar el readiness: la lista vive en Supabase y no
  puede consultarse sin credenciales de administración.

## Pruebas realizadas

- **`tests/test_auth.py`**: dos pruebas nuevas fijan el formato de la petición
  (`redirect_to` en la query y **ausente** del cuerpo) para `/auth/v1/recover`
  y `/auth/v1/signup`. Son las que habrían detectado este fallo.
- **`tests/test_recuperacion_redireccion.py`** (10 pruebas): ejercita el script
  con Node sobre un DOM mínimo. Cubre la URL real reportada, aterrizaje en la
  raíz, ausencia de bucle en la página correcta, login normal, `magiclink`,
  fragmento sin token, ancla corriente, enlace caducado, y que el token nunca
  salga del fragmento. Incluye una prueba que verifica que el script sigue
  cargado en ambas plantillas.
- **Suite completa**: 198 pruebas OK + 3 omitidas; 41 plantillas Jinja OK.
- **Manual**: script servido con `200 text/javascript` y admitido por la CSP
  (`script-src 'self'`), verificado contra la aplicación en ejecución.

## Documentación actualizada

`docs/GUIA_STAGING_POR_CLICS.md` (paso 6, con aviso destacado),
`docs/APROVISIONAMIENTO_STAGING.md` (paso F) y `docs/AUTENTICACION_SUPABASE.md`
(sección «Fallo observado: el enlace del email lleva al login»).

## Verificación end-to-end en staging (14/08/2026)

El propietario confirmó el ciclo completo en
`https://cotizat-generador.vercel.app`: el email de recuperación llega, el
enlace abre `/restablecer-clave`, la contraseña se cambia y el inicio de
sesión con la contraseña nueva funciona. Con esto:

- la corrección de `redirect_to` queda validada contra GoTrue real, no solo
  contra el servidor que lo suplantaba en las pruebas;
- el **punto 3 de la matriz de aceptación** (`docs/CONTINUIDAD_STAGING_SUPABASE.md`,
  Sección 4) queda superado;
- la validación end-to-end de Auth contra Supabase, listada como pendiente en
  la Fase 13, deja de estar bloqueada para los flujos de contraseña.

---

# 24. Siguiente bloque — Punto 4 de la matriz: Storage privado en despliegue real

Estado: **PENDIENTE** (es el trabajo inmediato).

## Por qué es lo siguiente

Auth ya está probado en HTTPS real de punta a punta. La pieza equivalente que
**nunca se ha ejercitado contra el servicio real** es `SupabaseStorage`: todas
sus pruebas usan una simulación REST. Es el último subsistema con riesgo de
sorpresa en despliegue, y el resto de la matriz (PDF con imágenes, aislamiento
entre organizaciones) depende de que funcione.

## Qué hay que comprobar, en este orden

1. **Punto 4 — subida y lectura.** Con el Usuario A en la Organización A:
   logo de empresa, imagen de producto, imagen de partida, anexo PDF y ficha
   técnica PDF. Cada archivo debe verse luego a través de
   `/archivos/organizaciones/<id>/...` y nunca mediante una URL pública de
   Supabase.
2. **Punto 5 — PDF.** Generar y descargar el PDF de un presupuesto que use esas
   imágenes. Aquí se ejercita `materialize_reference()` sobre `/tmp`, que es el
   camino específico del filesystem de solo lectura de Vercel.
3. **Punto 10 — aislamiento.** Con el Usuario B en la Organización B, pedir una
   clave de objeto de A. Debe responder **404**, no 403 ni el archivo.
4. **Punto 13 — bucket privado.** Pedir el objeto directamente a la URL pública
   de Supabase Storage. Debe negar el acceso.

## Señales de fallo a vigilar

- Error al subir con `SUPABASE_SECRET_KEY` enviada como `Bearer` en lugar de
  `apikey` (el código ya usa `apikey`; confirmarlo en el log si falla).
- Rechazo por tamaño: el bucket está limitado a 12 MB y con lista MIME.
- PDF sin imágenes: indicaría que `/tmp` no se pobló o que la referencia no se
  materializó.
- Un 200 en el punto 10 significa fuga entre organizaciones: es bloqueante y no
  debe corregirse relajando el filtro ORM ni las políticas RLS.

## Después del punto 4

Puntos 6 a 9 (invitación al Usuario B, aceptación de un solo uso con email
verificado, rol `lectura` comprobado, ascenso a `miembro` y Organización B con
nombres homónimos sin fuga de datos), el punto 11 (cookies HttpOnly/Secure y
`document.cookie` vacío) y el punto 12 (consola sin violaciones CSP) quedan
**superados en staging el 14/08/2026**. Resta el punto 14 (arranque rechazado
con un rol `BYPASSRLS`; opcional, lógica cubierta en CI). Cerrada la matriz, el
siguiente bloque de infraestructura es el rate limiting distribuido
(Redis/Upstash), obligatorio antes de escalar a varias instancias o abrir el
registro.

---

# 25. Anexos incorporados al PDF del presupuesto (14/08/2026)

Estado: **COMPLETADO**.

## El problema

Marcar «Incluir anexos» solo imprimía una lista de nombres al final del
presupuesto. El cliente leía «Anexo 1 · Planos de distribución» y no recibía
ningún plano: los archivos se quedaban en la aplicación, accesibles únicamente
para usuarios con sesión iniciada. Un cliente sin cuenta no tenía forma de
verlos.

Se descartó la alternativa de imprimir un hipervínculo al proxy
`/archivos/...`: el destinatario típico de un presupuesto no tiene cuenta en
CotizaT, así que el enlace le habría devuelto un 404.

## Qué hace ahora

Los anexos se **fusionan como páginas reales** del PDF del presupuesto. Un
único archivo contiene el presupuesto y todos sus documentos de apoyo, y el
índice explica cómo se entregan y dónde encontrarlos:

> Los anexos que se relacionan a continuación forman parte de este presupuesto
> y se entregan dentro de este mismo archivo: están añadidos como páginas
> adicionales al final del documento, en el orden indicado y conservando su
> formato y su numeración originales.
>
> • Anexo 1 · Planos de distribución — 3 páginas, desde la página 2 de este archivo.
> • Anexo 2 · Ficha técnica del porcelanato — 1 página, desde la página 5 de este archivo.

El número de página anunciado es el real: el documento se genera, se mide y se
regenera con la paginación definitiva. El pie «n/N» cuenta también las páginas
de los anexos, de modo que el total coincide con el archivo entregado.

## Tope de tamaño (límite de Vercel)

Una función de Vercel no puede devolver más de **4,5 MB** en el cuerpo de la
respuesta; superarlo produce `413 FUNCTION_PAYLOAD_TOO_LARGE` y no hay opción
de configuración que lo cambie. Como `/presupuestos/{id}/pdf` envía el binario
completo, `app/services/pdf_anexos.py` mantiene el resultado por debajo de
`LIMITE_TOTAL_BYTES` (4 MB, con `LIMITE_DURO_BYTES` = 4,4 MB como red de
seguridad). Los anexos que no caben **no se incorporan** y el índice lo dice
con claridad («se entrega como archivo independiente para no superar el tamaño
máximo de este PDF») en lugar de producir un error que el usuario no sabría
interpretar.

Si en el futuro se quiere levantar ese tope, el patrón correcto es subir el PDF
combinado al almacenamiento y devolver una redirección a una URL firmada, en
vez de enviar el binario por la función.

## Degradación y seguridad

- Un anexo borrado del almacenamiento, cifrado o ilegible **no rompe la
  descarga**: se omite y el índice lo anuncia como entrega aparte.
- De los anexos solo se copian las páginas. Se descartan los widgets de
  formulario y las anotaciones con JavaScript, para que un PDF subido no pueda
  inyectar comportamiento en el documento comercial ni interferir con el
  formulario del PDF interactivo (`app/services/pdf_interactivo.py`), que se
  conserva intacto tras la fusión.

## Cambios

- `app/services/pdf_anexos.py` (nuevo): lectura, planificación por tamaño,
  texto del índice, fusión y saneado.
- `app/services/pdf.py`: `generar_pdf()` orquesta medición y fusión;
  `_documento_presupuesto()` construye el documento base; `_CanvasNumerado`
  acepta `paginas_extra` para el pie «n/N».
- `requirements.txt` + `requirements.lock`: `pypdf==6.16.1`.
- `presupuestos.spec`: `pypdf` y `app.services.pdf_anexos` en el empaquetado.
- Textos de interfaz en `budgets/detail.html` y `budgets/form.html`.
- `tests/test_pdf_anexos.py` (nuevo, 10 pruebas), incluido un recorrido HTTP
  completo: subir el anexo, marcar la casilla y descargar el PDF fusionado.

Suite: **208 passed, 3 skipped**.

# 26. Aislamiento entre organizaciones y bucket privado, verificados en CI (14/08/2026)

**Estado: COMPLETADO** (salvo una comprobación manual que depende del proyecto
Supabase real, no del código).

## El problema

Los puntos 10 y 13 de la matriz de aceptación —"una clave de objeto de la
Organización A devuelve 404 bajo la Organización B" y "el bucket no entrega
objetos sin pasar por CotizaT"— eran comprobaciones manuales sobre staging.
Son exactamente las dos que no conviene dejar en manos de la memoria: bastaba
con que alguien tocara el proxy `/archivos/{object_key}`, el filtro por tenant
o el aprovisionamiento del bucket y olvidara repetirlas para que una fuga entre
empresas llegara a producción sin que nada avisara.

## Qué se hizo

`tests/test_aislamiento_almacenamiento.py` (6 pruebas) traslada ambos puntos a
la suite:

- **Punto 10, recorrido HTTP real.** Dos organizaciones con su propio usuario y
  su propia membresía. La Organización A sube un anexo; la petición se hace con
  el cliente HTTP contra la URL que genera `file_url`, no llamando a la función
  del endpoint. Con A activa se recibe 200 y el contenido; con B activa, la
  misma URL exacta devuelve 404 y el cuerpo no contiene el archivo.
- **Punto 10, manipulación de la clave.** Cinco intentos de alcanzar el objeto
  de A desde B: identificador reescrito, `..` en la ruta, `..` codificado como
  `%2f`, identificador con cero a la izquierda y `?download=1`. Todos 404.
- **Punto 10, capa de datos.** El metadato de A tampoco aparece al consultar
  `ArchivoAlmacenado` con B activa: el 404 no depende solo del proxy.
- **Punto 13.** El bucket se aprovisiona `public=false`; `ensure_bucket` falla
  si encuentra un bucket público; `SupabaseStorage` no expone `public_url` ni
  `signed_url`; `file_url` siempre devuelve una ruta `/archivos/...` sin
  `supabase.co`; y ninguna plantilla ni JavaScript de `app/` contiene
  `supabase.co/storage` ni `/object/public/`.

## Verificación de que las pruebas sirven

Escritas de una vez, pasaron a la primera, que es justo cuando conviene
desconfiar. Se comprobó rompiendo la protección a propósito:

1. Anulando solo el prefijo de tenant en `validate_tenant_object_key`: siguen en
   verde, porque el filtro ORM por organización todavía tapa la fuga.
2. Anulando solo el filtro ORM del proxy: siguen en verde, porque la validación
   de la clave la bloquea antes.
3. Anulando **las dos** capas a la vez: las pruebas fallan con `200 != 404`.

Es decir, el aislamiento tiene defensa en profundidad —hacen falta dos fallos
simultáneos para que haya fuga— y las pruebas detectan ese escenario. Los tres
archivos se restauraron después (`git diff` limpio antes de commitear).

## Lo que sigue siendo manual

Confirmar en el navegador que la URL pública del objeto en el proyecto Supabase
real responde acceso denegado. Depende de la configuración del bucket, no del
repositorio, así que ninguna prueba puede sustituirla.

## Resultado

Suite completa: **214 passed, 3 skipped** (antes 208). Matriz de aceptación:
puntos 1–5 superados en staging, 10 y 13 cubiertos en CI; los siguientes (6–9)
requieren un segundo correo real.

# 27. Registro reparado: GoTrue no siempre anida el usuario (14/08/2026)

## El problema

El registro, ya confirmado como superado en la matriz (punto 1), empezó a fallar
**siempre** en staging con «Supabase no pudo crear la cuenta». No era una clave
caducada ni configuración perdida, sino un **bug propio** que permanecía latente.

`POST /auth/v1/signup` responde **HTTP 200 con tres formas distintas**
(`internal/api/signup.go`), y solo una anida el usuario bajo la clave `user`:

| Situación | Respuesta | Forma |
| --- | --- | --- |
| Autoconfirm activo | `sendJSON(w, 200, token)` | `{access_token, refresh_token, user:{...}}` |
| Confirmación por email, alta nueva | `sendJSON(w, 200, user)` | usuario **en la raíz** |
| Email ya registrado sin confirmar | `sendJSON(w, 200, sanitizedUser)` | raíz, `identities: []` |

`sign_up` leía siempre `payload["user"]`. Mientras el proyecto estuvo en
autoconfirm funcionaba; al activar «Confirm email», las dos últimas respuestas
—correctas— se convirtieron en `InvalidCredentials` y el registro falló al 100%.

## Qué se hizo

Se acepta el usuario en la raíz cuando no viene envuelto y el error queda
reservado para respuestas sin identidad utilizable. El caso «email ya
registrado» se detecta por `identities: []` (el usuario obfuscado de GoTrue) y
se expone como `SignupResult.ya_registrado`.

**La bandera no altera el mensaje mostrado.** Diferenciar el aviso convertiría
el formulario en un enumerador de emails con cuenta, justo lo que GoTrue evita.
`/registro` responde siempre lo mismo: confirma tu email y, si ya tenías cuenta,
inicia sesión o usa «Olvidé mi contraseña».

## Verificación de que las pruebas sirven

Cuatro pruebas nuevas en `tests/test_auth.py` cubren las tres formas más el
cuerpo sin identidad. Al revertir la corrección, dos fallan con el mensaje
textual reportado (`InvalidCredentials: Supabase no pudo crear la cuenta.`).

## Lo que sigue siendo manual

Los puntos 6 a 9, 11 y 12 quedaron superados el 14/08/2026 (invitación al
Usuario B, aceptación con email verificado, rol `lectura` comprobado, ascenso a
`miembro`, Organización B homónima sin fuga de datos, cookies HttpOnly/Secure y
consola sin violaciones CSP). Restan el punto 13 (parte manual) y el 14, con la
guía `docs/MATRIZ_PASOS_MANUALES.md`.

## Resultado

Suite completa: **218 passed, 3 skipped** (antes 214). Commit `d4aa7f1`.

# 28. El límite de intentos de acceso no limitaba nada en Vercel (14/08/2026)

## El problema

`AuthRateLimitMiddleware` guardaba los intentos en un `dict` del proceso. En un
servidor único eso funciona. En Vercel **no**: cada invocación puede ejecutarse
en un proceso nuevo, así que el diccionario arranca vacío una y otra vez.

El resultado es peor que un límite laxo: es un límite inexistente disfrazado de
protección. Los «10 intentos cada 5 minutos» de `/acceso` solo se aplicaban
entre peticiones que casualmente cayeran en la misma instancia caliente. Quien
probara contraseñas no necesitaba ni saltárselo. La documentación lo daba por
sabido («no sustituye un límite distribuido»), pero seguía figurando como
pendiente de infraestructura mientras staging ya estaba en línea.

## Qué se hizo

`app/ratelimit.py` separa la decisión («¿permito este intento?») de dónde se
guarda la cuenta, detrás de `hit(identidad, límite, ventana) -> Decision`:

| Backend | Cuándo | Comparte estado |
| --- | --- | --- |
| `MemoryRateLimit` | Escritorio, desarrollo, respaldo ante fallos | No |
| `UpstashRateLimit` | Con las dos variables `UPSTASH_REDIS_REST_*` | Sí |

Decisiones que merecen justificarse:

- **API REST en vez de cliente Redis.** Una función serverless no conserva
  sockets entre invocaciones, así que la conexión persistente no aporta; usar
  `urllib` evita además sumar una dependencia al runtime, y con ella un pin en
  `requirements.txt` y una regeneración del lock. Mismo patrón que `app/auth.py`
  y `app/storage.py`.
- **Ventana fija por tramo** (`now // ventana` en la clave) y no deslizante: la
  clave caduca sola sin tareas de limpieza, renovar el TTL es idempotente y todo
  cabe en un solo viaje (`INCR` + `EXPIRE` en un pipeline, timeout 3 s). Se
  pierde precisión en la frontera entre tramos; a cambio no hacen falta sorted
  sets ni scripts Lua. La imprecisión es acotada y conocida.
- **Degradación al contador local si Upstash falla.** Fallar abierto sería
  quitar el límite justo cuando el servicio está en apuros; fallar cerrado
  dejaría a todos los usuarios fuera por una caída ajena. Se vuelve a la
  protección que ya existía.
- **La IP no viaja en claro** a un tercero: la clave es
  `cotizat:rl:<sha256("ruta|ip")[:32]>:<índice>`, determinista entre instancias
  —lo único que el contador necesita— pero no reconstruible.
- **Una configuración incompleta no impide arrancar**: se registra un aviso y se
  degrada. Quien avisa es `/readyz`, con `checks.rate_limit`. Solo
  `COTIZAT_REQUIRE_DISTRIBUTED_RATELIMIT=true` convierte «memoria» en error, y
  ni siquiera entonces bajo SQLite, donde un contador por proceso es lo correcto.

## Verificación de que las pruebas sirven

18 pruebas en `tests/test_ratelimit_distribuido.py`, contra un servidor HTTP real
que implementa `INCR`/`EXPIRE` —no un doble en memoria—, para ejercitar de verdad
el pipeline, las cabeceras y el parseo.

La prueba central reproduce el fallo original: reparte cuatro intentos entre
**dos aplicaciones distintas**, cada una con su propio middleware, como dos
invocaciones serverless. Con el límite en 3, el cuarto debe rechazarse aunque
llegue a la instancia que solo ha visto uno. Junto a ella,
`test_el_contador_en_memoria_no_habria_detectado_el_abuso` corre el mismo
escenario con `MemoryRateLimit` y comprueba que el abuso **pasa**: si algún día
esa prueba empieza a fallar, la anterior habrá dejado de demostrar algo.

El resto cubre el límite exacto, el aislamiento por IP y por ruta, que la IP no
aparezca en el tráfico saliente, que se fije `EXPIRE`, el `Bearer`, el único
round-trip, la degradación con el servicio devolviendo 500 y con el puerto
muerto (sin propagar excepción al login), el rechazo de URL no https y de token
vacío, y los cuatro estados de `/readyz`.

## Lo que sigue siendo manual

Activarlo en staging: crear la base en Upstash y añadir a Vercel
`UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN` y
`COTIZAT_REQUIRE_DISTRIBUTED_RATELIMIT=true`. Hasta entonces `/readyz` seguirá
publicando `rate_limit: memoria`, que en Vercel significa sin límite efectivo.
Los pasos 13-manual y 14 de la matriz continúan aparcados por decisión del
usuario hasta el final del desarrollo.

## Resultado

Suite completa: **250 passed, 5 skipped** (antes 228).

---

# 29. Panel de operador y licencias — E1-060 (2026-08-16)

Estado: **COMPLETADO y DESPLEGADO en producción**.

## Qué es

Registro interno de licencias del producto: el titular puede conceder acceso,
renovarlo, regalar un período de prueba o compensar una incidencia. Es la única
excepción deliberada al aislamiento multi-tenant: una licencia *apunta* a una
organización pero **no le pertenece** (es información del negocio del titular
sobre un cliente).

## Qué se construyó

- **Ruta `/admin/licencias`** (panel) + `POST /admin/licencias` (conceder/
  renovar) + `POST /admin/licencias/{id}/cancelar`.
- **Tabla `licencias` no-tenant** con estados `activa`/`vencida`/`cancelada`,
  orígenes `pago`/`prueba`/`cortesia`/`compensacion`, encadenamiento de
  renovaciones (la nueva empieza al día siguiente del vencimiento), y tope de
  seguridad de 3 años.
- **Solo `origen='pago'` suma a los ingresos** del panel: una cortesía con
  importe o un pago sin él se rechazan.
- **Aislamiento de raíz** (el riesgo del diseño): RLS propia
  (`cotizat_licencia_*`) que exige la marca `cotizat.es_operador`; la lista de
  operadores vive en la variable de entorno **`COTIZAT_OPERADORES`** (no en una
  columna, para que no exista escalada escribiendo en la base) y se exige
  **email verificado**.
- Pruebas: `tests/test_licencias.py` (18) + auditoría en
  `tests/test_web_security.py`. Suite: **362 passed, 5 skipped**.

## Despliegue en producción (16/08/2026)

1. **Migración `f4c1d8e37a95`** aplicada en Supabase con el script
   `docs/staging_upgrade_f4c1d8e37a95.sql` (SQL Editor → New query → Run).
   Verificación RLS del propio script: `true/true/true`.
2. **`COTIZAT_OPERADORES`** añadida en Vercel (Production) + **redeploy**.
3. `/readyz` real: `"alembic": "head:f4c1d8e37a95"` con `ok: true`.
4. **Verificado por el titular** en `https://cotizat.online/admin/licencias`.

Guía de uso y protección: `docs/PANEL_DE_OPERADOR.md`.

## Pendiente dentro de E1-060 (no bloqueante)

- Recibo en PDF (espera a la decisión de cobro **E1-059**).
- ~~Corte automático de acceso al vencer~~ → implementado y **listo para
  encenderse** (18/08/2026): ver la actualización al final de este documento.
- Avisos de vencimiento por correo (hoy el panel marca el ámbar a 15 días).
- **Mejora de la interfaz**: por decisión del titular (16/08/2026) el panel se
  queda deliberadamente simple por ahora; se mejorará más adelante.

## Actualización 18/08/2026 — compra real verificada en staging y post-venta al cliente

**Ensayo del flujo de compra real en staging: SUPERADO.** El titular
recorrió en staging el flujo de compra real con cobro manual (E1-059 sobre la
base de E1-060): `/pago` → checkout con método de pago y comprobante adjunto →
compra `pendiente` → **activación desde `/admin/compras`** → el cliente ve «Tu
plan» con fecha de vencimiento y días restantes. El cobro manual queda validado
de extremo a extremo.

El ensayo dejó dos huecos de post-venta, ya resueltos en este bloque:

1. **Aviso de activación por email al comprador.** `POST /admin/compras/{id}/activar`
   envía ahora `enviar_activacion_plan_por_email(...)` (plantillas
   `app/templates/emails/plan_activado.html` / `.txt`) con plan, importe, método
   de cobro, **inicio y vencimiento en `dd/mm/aaaa`** (también en el asunto) y el
   **recibo PDF adjunto**. El envío es best-effort: si Resend falla, la licencia
   sigue activa y el operador ve el error en el panel.
2. **Recibo PDF descargable por el cliente.** Nueva ruta
   `GET /pago/recibo/{compra_id}.pdf` (attachment, `Cache-Control: no-store`) y
   enlace «Descargar recibo (PDF)» en la tarjeta «Tu plan» de `/configuracion`.
   Como `licencias` solo es legible por sesiones de operador (RLS
   `f4c1d8e37a95`), la migración **`c7f1a3b9d425`** copia el período concedido a
   `compras_plan` (`licencia_inicio` / `licencia_vence`, con backfill) y la ruta
   del cliente reutiliza el mismo generador de `app/services/recibo_licencia.py`.

Con esto se cierra el punto «Recibo en PDF» que E1-060 dejaba pendiente a la
espera de E1-059. Suite: **568 passed, 6 skipped**.

**Operativo:** `docs/staging_upgrade_c7f1a3b9d425.sql` **aplicado en Supabase**
el 18/08/2026; `/readyz` vuelve a 200.


## Actualización 18/08/2026 (tarde) — el corte por licencia, listo para encenderse

Aplicada ya la migración `c7f1a3b9d425`, se abordó el último pendiente del
bloque de cobro: activar `COTIZAT_EXIGIR_LICENCIA=true`.

**El fallo que había que corregir antes.** El corte se aplica en `get_db`, la
puerta común de todas las rutas de organización, y las rutas de compra colgaban
de ella. Con la licencia vencida, `/pago/comprar` (GET y POST), la confirmación
y el recibo devolvían **403 «Acceso suspendido»**: la organización suspendida
leía en pantalla que podía renovar y, al intentarlo, chocaba con la misma
pared. La suspensión era una trampa sin salida y toda renovación habría acabado
en soporte, a mano — justo lo que el circuito de compra vino a evitar.

**La corrección.** Nueva dependencia **`get_db_renovacion`** en
`app/database.py`: idéntica a `get_db` (sesión, membresía, organización activa,
RLS de tenant) pero **sin** comprobar la vigencia. La usan **solo** las cuatro
rutas de compra de `app/routers/pagos.py`, que no exponen ningún dato de
negocio; el resto del producto sigue cortándose igual. La pantalla «Acceso
suspendido» gana el botón **«Renovar mi plan»**.

**Cómo queda protegido.** Cuatro regresiones en `tests/test_licencias_acceso.py`:
la organización suspendida llega al checkout y registra la compra, el resto de
rutas siguen cortadas, y un test estructural recorre el árbol de rutas exigiendo
que **exactamente** las rutas de compra usen la puerta sin corte — ni una de
más ni una de menos. Se verificó que el test muerde: revirtiendo `pagos.py` a
`get_db`, la suite falla.

Suite: **573 passed, 6 skipped** *(cifra de esa tarde; el total vigente está en
la última sección del documento)*.

**Pendiente operativo (en este orden).** 1) Conceder licencia de **cortesía** a
la organización del titular desde `/admin/licencias` — si no, al encender el
interruptor el titular se corta a sí mismo. 2) Fijar
`COTIZAT_EXIGIR_LICENCIA=true` en Vercel y redesplegar. 3) Comprobar
`"licencias": "exigida"` en `/readyz`. Detalle en `docs/PANEL_DE_OPERADOR.md`
§8 y `docs/PROCESO_PILOTOS.md` §0.

> **Corrección posterior (18/08/2026, noche).** El paso 1 **no** era un
> prerrequisito: el panel `/admin/*` cuelga de `get_operator_db`, que no
> comprueba licencia, así que el operador entra aunque su propia organización
> esté suspendida y puede concederse la cortesía en cualquier momento. Sin
> riesgo de quedarse fuera. Lo verdaderamente bloqueante era la migración —y
> ahora, además, que el **PR #38 esté desplegado** antes de encender el corte.


## Actualización 18/08/2026 (noche) — la prueba gratuita se anuncia; PR #38 listo para fusionar

Cierre del bloque de cobro y licencias. **PR #38**, 6 commits, cabeza
`b73b56d`, sobre `main` en `00cfec0`. Suite: **642 passed, 6 skipped**.

**Lo que faltaba y era puramente comercial.** La prueba de 7 días funcionaba en
el registro desde la mañana, pero **ninguna página la mencionaba**. Nadie
llegaba a pedirla, y encima toda la landing empujaba a `/pago`, que es el
destino equivocado para quien viene a probar gratis. Ahora se anuncia en los
cuatro puntos donde alguien decide —landing (`/` y `/conocer`), `/pago` y
`/acceso`— y el CTA del hero apunta a `/acceso`, donde está el registro real.

**La decisión técnica que importa.** El anuncio cuelga de dos globales de Jinja
(`dias_de_prueba`, `hay_prueba_gratuita`) que son **funciones, no valores**:
Jinja cachea la plantilla compilada, no su resultado, así que se evalúan en
cada render. Apagar `COTIZAT_DIAS_PRUEBA` retira el anuncio de las cuatro
páginas y la landing revierte a «Ver planes» **sin redesplegar**. Un test lo
recorre con la prueba apagada, porque el día que se retire la oferta lo que no
puede pasar es que la web siga prometiéndola. En `/pago` el bloque se omite si
llega un aviso: quien viene rebotado ya agotó la prueba.

**Un fallo de proceso que conviene recordar.** El commit anterior (`fbc3c26`)
se subió con la suite en rojo: 42 hallazgos de la auditoría E1-021 por ejemplos
de correo verosímiles. La causa es que **el auditor solo revisa archivos ya
versionados**, así que no vio los ejemplos hasta que estuvieron commiteados. Se
arregló sin vaciar la regla —nombres de fantasía y una exención estrecha sobre
la parte local, no 42 excepciones— y la lección quedó escrita en
`docs/DATOS_SENSIBLES.md` §4. De paso apareció una doctest que mentía:
**`pytest` no ejecuta doctests en este proyecto**, así que los `>>>` son
documentación que nadie verifica; queda sin decidir si añadir
`--doctest-modules`.

**Pendiente operativo, en este orden.** 1) Fusionar el PR #38 y esperar al
despliegue. 2) Comprobar `"alembic": "head:a3d9c1e75b28"` en `/readyz`. 3)
`COTIZAT_EXIGIR_LICENCIA=true` en Vercel (Production). 4) **Redeploy**. 5)
Verificar `"licencias": "exigida"`. La migración y la licencia de cortesía
**ya están hechas**. El orden importa: encender el corte antes de desplegar
este PR dejaría suspendida a toda organización recién registrada, porque la
prueba que las cubre viaja aquí. Para revertir, `false` y redeploy: el
interruptor no altera ningún dato. Detalle en `docs/PUNTO_DE_CONTINUACION.md`
(sección «EMPEZAR AQUÍ») y `docs/COBRO_Y_LICENCIAS.md` §5.5-5.6.

## Actualización 18/08/2026 (noche) — el cron de Vercel se diagnostica y se dota de verificación

**PR #39 fusionado en `main`** (`455f3fc`, 18/08/2026) con los recordatorios
automáticos, la identidad «CotizaT · Presupuestos» y el panel «Correos». El
corte por licencia sigue activo en producción.

**El problema reportado:** el cron no aparecía en el panel de Vercel (Cron
Jobs). Se verificó a fondo que el lado del repositorio estaba correcto:
`vercel.json` es válido para el preset FastAPI actual de Vercel (entrada
`app/main.py`, `maxDuration: 60`, `crons` con
`/api/cron/recordatorios-vencimiento` a `0 13 * * *`, compatible con Hobby), la
ruta existe y responde GET (401 sin `CRON_SECRET`, 200 con él, nunca 404), y el
barrido con RLS de operador funciona (`get_cron_db` + `set_config
cotizat.es_operador`). Conclusión: **Vercel solo materializa los crones en
despliegues de producción** (un Preview nunca los muestra) y el `CRON_SECRET`
seguía pendiente de añadir en el proyecto.

**Qué cambió en el repositorio (rama `arena/01a016b5-generador-comercial`,
commit `f4e2fbe`):**

- `/readyz` publica `cron_secret` (`configurado`/`no-configurado`) y `cron`
  (ruta declarada en `vercel.json` vs. rutas registradas), sin exponer el
  secreto. Permite distinguir «el cron no se creó» de «el cron falla».
- Constante `CRON_RECORDATORIOS_PATH` en `app/routers/admin.py` (única fuente
  de verdad de la ruta).
- `tests/test_vercel_cron_config.py`: guardas CI — cada ruta de `vercel.json`
  debe existir como GET en la app, ser alcanzable (nunca 404) y su horario ser
  válido para Hobby.
- Docs: `docs/DESPLIEGUE_VERCEL.md` (sección «Trabajo programado») y
  `docs/PENDIENTES_OPERATIVOS.md` §9 (checklist «Si el cron no aparece»).
- Suite: **662 passed, 6 skipped**.

**Pendiente del titular (del lado de Vercel, sin código):** 1) Fusionar este
PR y comprobar que el deployment *Production* es el nuevo. 2) Añadir
`CRON_SECRET` (Production) — `openssl rand -base64 32`. 3) **Redeploy**. 4)
Verificar `/readyz` → `"cron_secret": "configurado"` y la ruta
`...:registrada`; 5) confirmar en Settings → Cron Jobs que aparece
`recordatorios-vencimiento` (13:00 UTC, ±59 min en Hobby). Checklist completa
en `docs/PENDIENTES_OPERATIVOS.md` §9 y en el «Cierre de sesión» de
`docs/PUNTO_DE_CONTINUACION.md`.

## Actualización 19/08/2026 — cron operativo en Vercel y emails de Supabase con identidad

**Cierre del ciclo del cron.** El PR #40 se fusionó en `main` (`c24c2cc`,
18/08/2026 21:31 UTC) y se desplegó en producción. El titular añadió
`CRON_SECRET` en Vercel (Production), hizo el redeploy y **confirmó el job en
Settings → Cron Jobs**: `/api/cron/recordatorios-vencimiento`, `0 13 * * *`
(13:00 UTC). `/readyz` en producción devuelve
`"cron_secret": "configurado"` y
`"cron": "/api/cron/recordatorios-vencimiento:registrada"`, y la ruta responde
401 sin el secreto (nunca 404). El diagnóstico que motivó el PR #40 quedó
confirmado: el código estaba bien; el cron solo faltaba materializar
(despliegue de producción + `CRON_SECRET`).

**Emails de Supabase Auth con el diseño de CotizaT.** Las plantillas de
**Confirm signup**, **Reset password** y **Password changed** se prepararon en
`docs/supabase_templates/` (con la guía `docs/SUPABASE_EMAIL_TEMPLATES.md`) y
el titular las pegó en Supabase → Authentication → Email Templates. Los
correos del ciclo de vida de Auth ya no usan la plantilla genérica de
Supabase: siguen la identidad verde del resto de correos, conservando los
placeholders (`{{ .ConfirmationURL }}`, etc.).

**Pendiente de verificación:** la primera ejecución automática del cron
(19/08, 13:00 UTC, ±59 min en Hobby) y sus logs en Observability.

Suite: **662 passed, 6 skipped** (verificada el 19/08/2026).

## Actualización 19/08/2026 (tarde) — E1-022 cerrado y decisiones de producto

**E1-022 — auditoría de procedencia del catálogo: CERRADA con evidencia.**
El titular confirma que **todas las partidas del catálogo son de autoría
propia** y que los archivos de ejemplo (`DPT020/RBA010/RBE030.xlsx`,
`BENEFICIO.png`, captura) «no sirven para nada» hoy. La auditoría lo verificó
empíricamente: el catálogo son **3.006 partidas** en
`basedatos_partidas/datos/` (la app carga solo de ahí), con **0 coincidencias**
exactas y parciales (ventanas de 60 caracteres) contra los textos de los 3
`.xlsx`; los códigos `RBA010`/`RBE030` no existen en el catálogo y los `DPT0xx`
son solo historial interno (`codigo_anterior`, migrado a códigos propios
`CT-…`). Los `.xlsx` se usan únicamente como formato de importación (guía,
parser de subidas del usuario y fixtures de pruebas). Detalle completo en
`docs/DATOS_SENSIBLES.md` §6 y nota en `basedatos_partidas/README.md`.

**Decisión de producto — los tiempos nunca van al PDF del cliente.** La
estimación de tiempos de obra **ya está implementada** (Fase 11: horas por
partida, días con cuadrillas, semanas y cobertura, en el creador y en la
página `/presupuestos/<id>/tiempos`). Es información interna con ventaja
comercial: el cliente ve el presupuesto **sin** desglose de horas ni plazos
calculados. La idea de un «Gantt por capítulo» (barras de duración
encadenadas) quedó **descartada**: la estimación existente ya cubre la
planificación interna. Detalle en la sección «Pendientes / ideas siguientes»
de la Fase 11.

**Decisión de proceso — día final único de solo tests.** Toda la validación
de tipo prueba pendiente (matriz de aceptación manual, cruces con dos correos
y dos organizaciones, primer alta real con el corte encendido, auditoría
externa del bucket, invitación sin cuenta previa, recordatorio real) se
agrupa en **una sola jornada final de pruebas** cuando el desarrollo esté
cerrado. No se hacen por etapas: hacerlas ahora y repetirlas al cierre sería
trabajo doble.

## Actualización 19/08/2026 (noche) — Etapa 4: E4-030, E4-021 y E4-023 completados

Bloque de operación de la Etapa 4 terminado:

- **E4-030 — Escaneo de dependencias y secretos en CI.** `pip-audit` sobre
  `requirements.lock` y `detect-secrets` con baseline versionado
  `.secrets.baseline` como pasos de `docs/ci/ci.yml` (protegidos por
  `tests/test_integracion_continua.py`); herramientas fijadas en
  `requirements-dev.txt` y lock regenerado (66 paquetes).
- **E4-021 — Respaldo automático por organización.** Nuevo cron
  `/api/cron/mantenimiento` (02:00 UTC) en `app/services/mantenimiento.py`:
  reutiliza el paquete verificable de E3-020, lo guarda en el bucket privado
  (`organizaciones/<id>/respaldo_automatico/…`) con retención configurable y
  sin registro en `ArchivoAlmacenado` (evita crecimiento autorreferencial);
  las organizaciones que superan `COTIZAT_RESPALDO_MAX_MB` se reportan
  omitidas, no rompen el barrido. Storage gana `list()` y `put(max_size=…)`;
  el bucket admite `application/zip` en buckets nuevos.
- **E4-023 — Verificación diaria con alerta.** El mismo cron ejecuta los
  chequeos de `/readyz` y, si fallan, envía a los operadores
  (`COTIZAT_OPERADORES`) el correo interno `alerta_operador` con errores y
  estado de chequeos (sin secretos). El vigilante externo de disponibilidad
  (UptimeRobot) y los backups de Supabase Pro quedan como pasos de panel en
  `docs/PENDIENTES_OPERATIVOS.md` §11.

Suite: **672 passed, 6 skipped** (10 pruebas nuevas en
`tests/test_mantenimiento_cron.py`).

## Actualización 19/08/2026 (noche, 2ª) — Bloque 100 % recomendado: E4-038, E4-032, E4-043 (procedimiento)

Triaje de lo que quedaba de la Etapa 4: se separó lo **100 % recomendado
antes de lanzar** de lo que puede esperar a la beta, y se ejecutó el primer
bloque:

- **E4-038 — Consentimiento de términos registrado.** Checkbox obligatorio en
  el registro; tabla `consentimientos` con RLS de operador y unicidad
  (email, versión); funciones SECURITY DEFINER `record_consent` y
  `obtener_consentimiento` (mismo patrón blindado que la prueba gratuita);
  marca `usuarios.acepto_terminos_*` visible en `/cuenta`, con aceptación
  explícita para cuentas anteriores; versión única en `app/legal.py` (1.1)
  mostrada en la página de términos. Migración `b6d9e4c2a8f1` +
  `docs/staging_upgrade_b6d9e4c2a8f1.sql` (a aplicar en Supabase al fusionar).
- **E4-032 — Plan de respuesta a incidentes.** `docs/PLAN_DE_RESPUESTA_A_INCIDENTES.md`
  (severidades S1–S4, runbooks, contactos, «qué no hacer»).
- **E4-043 — Simulacro de caída y recuperación (procedimiento).**
  `docs/SIMULACRO_CAIDA_Y_RECUPERACION.md`; la ejecución queda para el titular
  antes del día final de tests (D-019).

Suite: **694 passed, 7 skipped** (23 pruebas nuevas en
`tests/test_consentimiento.py` y ajustes de cadena de cabezas). Cabeza
Alembic: `b6d9e4c2a8f1`.

## Actualización 23/08/2026 — Planos: visor global, medición premium y exportaciones (PR #83)

La función de planos del 22/08 estaba operativa pero era prácticamente
invisible (solo un botón en la ficha del presupuesto) y, sin saberlo,
**rota**: la categoría `planos` faltaba en `_ALLOWED_CATEGORIES` de
`app/storage.py`, así que toda subida fallaba con «No se pudo guardar el
plano». PR #83 corrige ambas cosas y sube la función a primera clase.

### Qué se construyó

- **Visor global `/planos`**: galería de todos los planos de la
  organización agrupados por presupuesto, con miniaturas, estadísticas
  (calibrados, mediciones) y enlaces profundos `?plano=<id>`. Entrada
  «Planos» en el sidebar, en la cabecera de Presupuestos, acción por fila
  y botón en la barra del editor.
- **Medición premium** en el área de trabajo: snap ortogonal (casilla o
  Mayús), snap a vértices con anillo indicador, línea elástica con
  previsualización del cierre, paneo (botón central o ✋ Mover), zoom con
  rueda centrado en el cursor, ⛶ Ajustar/pantalla completa, descarga PNG
  del lienzo, atajos L/A/P/C/E/M + Ctrl+Z + Esc, renombrado de
  mediciones, totales por unidad y mostrar/ocultar trazos.
- **Exportaciones**: CSV de todas las mediciones del presupuesto (`;` +
  BOM, Excel ES); **DXF ASCII R12** por plano en metros con Y invertida,
  capa por tipo y etiquetas TEXT (AutoCAD/LibreCAD/BricsCAD); PNG
  client-side; y **anexo «Planos y mediciones» en el PDF** del presupuesto
  con «Incluir anexos» activo (`app/services/pdf_planos.py`: imagen +
  mediciones superpuestas + tabla, integrado en el circuito estándar de
  `pdf_anexos` con índice, tope de 4 MB y degradación elegante).
- **Fix UI**: el menú «Más opciones» de la ficha del presupuesto quedaba
  **tapado por el Resumen** — la animación `fadeInUp` de `.page-head`
  crea un contexto de apilamiento que atrapaba el z-index del desplegable;
  `.page-head` ahora tiene capa propia (`z-index: 30`).

### Fix crítico

- `_ALLOWED_CATEGORIES` ahora incluye `planos`; cubierto con un test que
  sube un PNG real por `crear_plano` (antes de este fix, imposible).

### Documentación y pruebas

- `docs/FEATURE_BC3_Y_PLANOS.md` ampliado con la actualización premium;
  README con las secciones de BC3 y planos.
- `tests/test_planos.py`: 13 pruebas (geometría, visor, deep-link, CSV,
  DXF, renombrado, anexo PDF, subida real).
- Suite completa: **992 passed, 9 skipped**. Sin migraciones nuevas.
