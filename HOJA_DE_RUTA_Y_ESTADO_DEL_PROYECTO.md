# Hoja de ruta y estado del proyecto

Fecha de actualización: 2026-08-10  
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

- Incluir el resumen de tiempos en el PDF del presupuesto (página opcional).
- Plazo por capítulo con dependencias (diagrama de Gantt sencillo en la
  página de detalle).
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

Estado: **CORREGIDO** (requiere además un cambio de configuración en Supabase).

## Síntoma reportado

El email de recuperación llegaba correctamente, pero al pulsar el enlace el
navegador mostraba la pantalla de inicio de sesión en lugar de la de nueva
contraseña, con esta forma de URL:

```text
/acceso?next=/#access_token=...&expires_in=3600&type=recovery
```

## Causa raíz (configuración, no código)

La aplicación pide a Supabase `redirect_to=https://<origen>/restablecer-clave`.
Supabase **solo respeta ese parámetro si la URL exacta está en su lista de
Redirect URLs**. Si no está, no devuelve ningún error: la descarta en silencio
y usa el **Site URL** configurado.

La cadena completa del fallo:

1. Supabase descarta la `redirect_to` no autorizada y usa el Site URL (`/`).
2. `/` exige sesión, así que la app redirige a `/acceso?next=/`.
3. El navegador **re-adjunta el fragmento** `#access_token=...` en cada salto.
4. El fragmento **nunca viaja al servidor** (así funciona HTTP), por lo que
   ninguna ruta puede leerlo: el login lo ignora y el enlace parece roto,
   aunque el token sea perfectamente válido.

Se verificó decodificando el JWT del enlace: `type=recovery`, `amr.method=otp`,
vigencia de 1 hora y email correcto. El token era válido; solo aterrizó en la
página que no sabe leerlo.

## Solución de fondo (acción manual requerida)

En Supabase → Authentication → URL Configuration, añadir a **Redirect URLs**:

```text
https://cotizat-generador.vercel.app/restablecer-clave
```

Debe coincidir carácter a carácter, sin barra final.

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

- **`tests/test_recuperacion_redireccion.py`** (10 pruebas): ejercita el script
  con Node sobre un DOM mínimo. Cubre la URL real reportada, aterrizaje en la
  raíz, ausencia de bucle en la página correcta, login normal, `magiclink`,
  fragmento sin token, ancla corriente, enlace caducado, y que el token nunca
  salga del fragmento. Incluye una prueba que verifica que el script sigue
  cargado en ambas plantillas.
- **Suite completa**: 196 pruebas OK + 3 omitidas; 41 plantillas Jinja OK.
- **Manual**: script servido con `200 text/javascript` y admitido por la CSP
  (`script-src 'self'`), verificado contra la aplicación en ejecución.

## Documentación actualizada

`docs/GUIA_STAGING_POR_CLICS.md` (paso 6, con aviso destacado),
`docs/APROVISIONAMIENTO_STAGING.md` (paso F) y `docs/AUTENTICACION_SUPABASE.md`
(sección «Fallo observado: el enlace del email lleva al login»).
