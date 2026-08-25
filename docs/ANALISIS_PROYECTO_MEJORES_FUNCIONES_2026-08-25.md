# Análisis del proyecto, mejores funciones y ventajas — base para la landing

**Fecha:** 2026-08-25
**Producto:** CotizaT (Presupuestos y control comercial para construcción y remodelación)
**Objetivo:** tener una fotografía completa del proyecto, identificar qué hace único al producto, poner nombre a sus ventajas y usar esa información para que la landing home sea más llamativa y muestre lo mejor **a primera vista**.

---

## 0. Resumen ejecutivo

- CotizaT **no es "otro generador de presupuestos"**: es un flujo comercial completo que va del **catálogo descompuesto** al **PDF con versión, firma y resumen de cambios** pasando por **margen, beneficio y tiempo de obra**.
- Su verdadero activo (el que casi nadie tiene) es la **base de precios con análisis de precios unitarios (APU)** conectada en cascada: recursos → partidas → capítulos → presupuesto → PDF.
- La landing actual ya es sólida y habla de esto, pero prima el contenido "de fondo" y explica demasiado antes de mostrar el gancho. Para **mostrar las mejores funciones a primera vista** conviene:
  1. Subir a la primera pantalla las **4 funciones que cierran la venta** (Beneficio real, Base de precios lista, Plazo calculado, PDF profesional con cambios).
  2. Añadir justo debajo del hero una **franja de "superpoderes"** con cifras y prueba concreta (no descripciones largas).
  3. Bajar a la parte media las explicaciones largas (APU, comparativa, tour) que hoy compiten con el mensaje principal.

---

## 1. Qué es exactamente CotizaT

En una frase: **convierte tu catálogo y tus precios en presupuestos de obra claros, con costo real, beneficio visible, plazo estimado y un PDF profesional listo para enviar por WhatsApp o email.**

- **Para quién:** pequeñas constructoras, remodeladores y contratistas de 2 a 15 personas (Venezuela, Colombia, México, Ecuador, Perú y España, con foco latino).
- **Qué NO es:** no es un ERP de obra, no es un visor BIM, no emite facturas fiscales. Ese "no" también es una ventaja de enfoque: el cliente no paga por cosas que no usa.

---

## 2. Cómo se hizo el análisis

- Revisión de `README.md`, `docs/` (rutas de producto, comercialización, SEO, APU, planos, BC3, seguridad, licencias, operación) y de los análisis anteriores (`ANALISIS_PRODUCTO_Y_VIABILIDAD.md`, `HOJA_DE_RUTA_Y_ESTADO_DEL_PROYECTO.md`, `GUIA_IMPORTACION_EXCEL_Excel.md`).
- Inspección directa de los módulos clave que sostienen las funciones: `calculations.py` (márgenes), `apu.py` (APU), `tiempos.py` (horas/duración), `bc3.py` (FIEBDC-3), `planos.py` (medición de planos), `cambios_presupuesto.py` (versiones/comparación), `pdf*.py`, `excel_export.py`, `landing_ejemplo.py`, `seo.py`.
- Verificación de las cifras de catálogo a partir de `basedatos_partidas` (3.006 partidas + 392 recursos).

---

## 3. Mapa de capacidades (todo el producto en 7 bloques)

| Bloque | Capacidades | Valor para el usuario |
|---|---|---|
| **1. Base de precios** | Catálogo de 3.006 partidas descompuestas, 392 recursos, 331 materiales, 17 oficios, 44 equipos, 16.127 líneas de APU | No empiezas de cero, llegas con precios del mercado |
| **2. APU y costes** | Descomposición en recursos (rendimiento × precio), costes directos complementarios, edición de rendimiento/precio, recálculo en cascada | Sabes de dónde sale cada precio y puedes corregirlo sin romper nada |
| **3. Presupuesto** | Capítulos ilimitados, partidas, mediciones, productos, packs de estancia, autosave, deshacer, Excel/TSV, plantillas, numeración | Es rápido armar y mantener el presupuesto |
| **4. Comercial** | Beneficio/margen por partida–capítulo–total, alertas de margen bajo, tiempo de obra (horas por rol + duración), planificación de cuadrilla | Deja de cotizar a ciegas: ves cuánto ganas y cuánto tardas |
| **5. Entrada de datos** | Importar Excel propio, **Excel .xlsx**, **BC3 (FIEBDC-3)**, medición sobre planos (líneas/áreas/perímetros/conteos), exportar DXF/CSV/PNG, anexos al PDF | Aprovecha lo que ya existe en la empresa (planos, Excel, Excel) |
| **6. Entrega** | PDF con logo, condiciones, garantías, firmas, marca de agua, **versiones inmutables**, enlace privado (caducidad, revocación, firma), WhatsApp, email, **resumen de cambios** al reenviar | Tú envías como ya lo haces, pero con trazabilidad profesional |
| **7. Operación** | Clientes, historial con filtros, estados, vencimiento automático, ajuste de precios por %, cobros (documentos DC, saldos), reportes/CSV, copia de seguridad/restauración, multiorganización, licencias/facturación | El presupuesto se convierte en negocio, no queda en un PDF suelto |

---

## 4. Ranking de las mejores funciones (Top 10, por impacto comercial)

### 🔟 1. Base de precios con APU incluida (la joya de la corona)
- **Qué es:** 3.006 partidas + 392 recursos + **16.127 líneas de descomposición** editables (rendimiento × precio), organizadas en 18 capítulos y 172 subcapítulos.
- **Por qué es la mejor:** un productor de presupuesto normal empieza con una lista plana o con lo que recuerde. Aquí el usuario **llega con una base de precios profesional**, en USD o moneda local, con vocabulario del país.
- **Prueba en la landing:** `{{ catalogo().lineas_precio_txt }} líneas de precio` y `{{ catalogo().lineas_descomp_txt }} líneas de APU`.

### 🔟 2. APU en cascada (cambia un recurso y se recalcula todo)
- **Qué es:** cada partida guarda materiales, mano de obra y equipo. Si sube el cemento o la hora del oficial, **todas** las partidas que usan ese recurso se recalculan solas (recurso → partida → capítulo → presupuesto → PDF).
- **Por qué es Top 2:** es lo que **ninguna plantilla de Excel hace sin romperse**. Es el argumento más fuerte contra "yo ya tengo mi Excel".

### 🔟 3. Beneficio y margen reales en vivo
- **Qué es:** coste interno por partida + comparación con precio de venta → **beneficio**, **margen %**, por partida, capítulo, productos y total. Con alertas de margen bajo.
- **Por qué es Top 3:** el contratista que cotiza con Excel **no sabe cuánto gana** en cada obra. Verlo en vivo al añadir una partida cambia la decisión de precio.

### 🔟 4. Tiempo de obra con tu cuadrilla
- **Qué es:** horas-hombre por rol (oficial, ayudante, capataz), **duración estimada de la obra**, simulación de planificación y asignación manual de horas.
- **Por qué es Top 4:** permite **prometer plazos que se pueden cumplir**, lo cual es una promesa de venta muy potente para remodeladores.

### 🔟 5. Importación de descompuestos Excel + BC3 (FIEBDC-3)
- **Qué es:** importa descompuestos de **descompuestos Excel (.xlsx)** sin perder filas ni fórmulas, y **.bc3 (FIEBDC-3)** (UTF-8/Windows-1252/ISO/CP850). Exporta BC3 básico.
- **Por qué es Top 5:** baja la barrera de entrada para quien ya trabaja con bases de precios. Convierte "otro software" en "el que ya entiende mis archivos".

### 🔟 6. Medición sobre planos
- **Qué es:** sube PNG/JPG/WEBP/PDF, calibra la escala y mide **líneas (m), áreas (m²), perímetros y conteos**. Snap ortogonal, snap a vértices, zoom, paneo, atajos. La cantidad se aplica a la partida; exporta DXF/CSV/PNG y anexa al PDF.
- **Por qué es Top 6:** elimina el "copiar medidas a mano del plano al Excel" y **deja trazabilidad en el PDF** (imagen + mediciones + tabla).

### 🔟 7. PDF profesional + versiones inmutables
- **Qué es:** fuente Lato embebida, logo, banda de capítulos, mediciones, "Producto presupuestado", bloque de totales, **firma digital del cliente**, marca de agua según estado, **versión inmutable por envío**.
- **Por qué es Top 7:** es el **producto que el cliente final ve y firma**. Un PDF impecable es la mejor publicidad de una constructora.

### 🔟 8. Vender con opciones y packs de estancia
- **Qué es:** productos **incluido / opcional / alternativa** con foto, y packs (baño, cocina, dormitorio) que insertan el capítulo entero escalado a los m² reales.
- **Por qué es Top 8:** transforma la "lista de precios" en **una propuesta comercial** donde el cliente elige, no renuncia. Ayuda a subir el ticket medio.

### 🔟 9. Cambios claros al reenviar
- **Qué es:** comparador de snapshots que detecta qué cambió, **resumen de cambios** para copiar/reenviar, botón "reenviar versión actualizada".
- **Por qué es Top 9:** el flujo real de obra: "cliente llama, pide cambios". Este es el momento donde se pierde el control en Excel; aquí se mantiene.

### 🔟 10. Del presupuesto al cobro + datos sin rehenes
- **Qué es:** documentos de cobro (DC), control de saldos, reportes/CSV, **copia de seguridad completa** y restauración.
- **Por qué es Top 10:** cierra el ciclo comercial y **da confianza** ("tu data no queda secuestrada").

---

## 5. Ventajas competitivas reales

### 5.1 Contra Excel / plantillas
- No hay que mantener fórmulas frágiles ni caché de versiones por correo.
- **Catálogo compartido:** los precios no viven en la cabeza de una persona.
- **APU y recálculo en cascada** (el cambio de un recurso ya no es un "buscar y reemplazar").
- **Tiempo de obra** automático.
- **Control de versiones y cambios** (qué se envió, qué cambió).

### 5.2 Contra generadores típicos (que solo suman líneas)
- Bajan hasta el **coste** (no solo el precio).
- Mostrar **margen y beneficio** en vivo.
- **Base de precios incluida** (no 50 partidas de muestra).
- **Import de Excel/BC3** y **medición en planos** (los típicos no lo tienen).
- **Productos con opciones y packs** (propuesta comercial, no lista plana).

### 5.3 Contra ERP / BIM de obra
- CotizaT **no obliga a aprender una plataforma**: se vive en PDF, WhatsApp y email.
- Entrada rápida, instalación sencilla, sin curva de un ERP.
- Enfoque en el **flujo comercial** (cotizar-ganar-enviar-cobrar), no en la gestión completa de obra.

### 5.4 Ventajas de negocio (no funcionales)
- **Sin permanencia y prueba de 7 días sin tarjeta** → baja fricción.
- **Datos exportables** (Excel, PDF, copia completa) → genera confianza.
- **Landing + SEO multi-país** → llega a mercados por intención de búsqueda.
- **Honestidad posicionada** ("no es IA", "no es factura fiscal") → es un diferencial frente a herramientas que sobrevenden.

---

## 6. La relación "best functions ↔ landing"

| Mejor función | Cómo debe aparecer en la landing |
|---|---|
| Base de precios + APU | Cifra grande arriba: "3.392 líneas de precio / 16.127 líneas APU" |
| Beneficio y margen real | "Sabes cuánto ganas por partida" (no "presupuesta" genérico) |
| Tiempo de obra | "Promete plazos que puedes cumplir: 98 h → ~6 días" |
| PDF + cambios | "PDF con tu logo + qué cambió al reenviar" |
| Excel / BC3 / planos | "Importa lo que ya tienes: Excel, BC3, planos" (una sola línea) |
| Packs y opciones | "Vende con opciones, no con renuncias" |
| Datos sin rehenes | "Exporta todo cuando quieras" (mini-barra de confianza) |

---

## 7. Diagnóstico de la landing actual

**Lo que ya está muy bien:**
- El hero tiene un **mockup del panel/PDF** que comunica el producto en sí.
- Se usan **cifras reales** del catálogo (`lineas_precio_txt`, `lineas_descomp_txt`) y el **ejemplo es por país** (moneda, IVA, vocabulario).
- El SEO (`/`, `/co/`, `/mx/`, temas APU/remodelación) es profesional y no duplica contenido.
- El **banner de catálogo oscuro** y la **comparativa** son fuertes.

**Lo que se puede mejorar (y se ha hecho en esta iteración):**
1. **El mensaje de apertura es ancho, no afilado.** El hero enumera 4 funciones en tarjetas genéricas ("Beneficio real", "Planos y BC3", "Tiempo de obra", "PDF y reenvío"). Se ha cambiado por beneficios concretos con la **palanca** que los hace únicos: "APU → coste → margen", "base de precios ya lista", "plazo que puedes cumplir", "PDF + firma + cambios".
2. **Las mejores funciones no están "arriba"**: aparecen bien, pero en secciones medias. Se ha añadido **una franja de superpoderes justo después del hero** con 6 tarjetas + prueba cuantitativa, para que en el **primer scroll** el visitante ya vea el diferencial.
3. **Falta un ancla de confianza inmediata.** Se refuerzan los "check" del hero con los claims más difíciles de copiar (recálculo en cascada, Excel/BC3/planos).
4. **Ritmo visual plano en la parte alta.** Se añade un diseño más vivo (iconos en gradiente, tarjetas con acento, hover y micro-animaciones que respetan `prefers-reduced-motion`) sin tocar el LCP (el H1 se pinta con CSS crítico en línea, como antes).

---

## 8. Cambios implementados en la landing

1. **Hero afilado:** las 4 tarjetas `hero-outcomes` ahora dicen la **palanca real** (APU → coste → margen; base de precios ya lista; plazo calculado; PDF que cierra con firma, versión y WhatsApp).
2. **Franja "Nuestras mejores funciones" (`#superpoderes`)** justo tras el hero: 6 tarjetas con cifra de prueba y enlace a la sección de detalle.
   - Beneficio real por partida (margen en vivo).
   - Base de precios con APU (3.006 partidas + 392 recursos).
   - Tiempo de obra con tu cuadrilla (horas por rol y duración).
   - Importa Excel y BC3 + mide en planos.
   - Productos con opciones y packs de estancia.
   - PDF con logo, versiones y resumen de cambios.
3. **Ancho de confianza en el hero:** el bloque `hero-points` ahora ancla los tres claims más fuertes (recálculo en cascada, import Excel/BC3/planos, línea de precios).
4. **Estilo más llamativo sin romper rendimiento:** gradiente acento/oro en iconos, borde de acento en tarjetas, hover con elevación y micro-animación CSS solo en la franja nueva (fuera del primer viewport).

---

## 9. Próximos pasos recomendados (orden de retorno)

1. **Medir el primer scroll** con un test A/B del hero: versión nueva (palanca) vs. actual (enumeración). Lo importante es el clic en "Empezar mis X días gratis" y la visita al PDF de ejemplo.
2. **Poner la franja de superpoderes en la home por defecto y añadirla a `/como-funciona`** como "resumen de un minuto".
3. **Reutilizar los mismos 6 titulares** en los anuncios/Meta/Instagram para mantener coherencia.
4. **Añadir 2–3 testimonios reales de pilotos** (lo que más falta es prueba humana; cifras del catálogo ya se tienen).
5. **Crear un GIF/maqueta animada** del "cambio de un recurso que recalcula todo", porque es la función más difícil de explicar y la más impresionante de ver.

---

## 10. Conclusión

El producto tiene **funciones de verdadero valor** y varias son difíciles de copiar (APU + base de precios + tiempo de obra + versiones + import Excel/BC3/planos). La landing ahora **las muestra arriba, con número y con la palanca**, y deja el detalle para las secciones de profundidad. Ese es el equilibrio: **persuadir en el primer momento y argumentar en el resto de la página.**

---

## 11. Segunda iteración: España en primer plano + catálogo por país + look premium

**Por qué esta iteración**
- El mensaje anterior sonaba muy **LatAm-centrista** ("para Latinoamérica"), y España es un mercado grande y prioritario (EUR, NIF, IVA 21 %, pladur/fontanería, BC3).
- No se estaba comunicando la verdad del producto: **cada país tiene su propio catálogo de precios**, no es una lista genérica con una bandera. El selector de país no es cosmético: cambia precios, moneda, IVA, ID fiscal y vocabulario.

**Cambios clave (todo verificado en `/`, `/es/` y `/co/`)**

1. **España primero en el selector y en el copy.**
   - `ORDEN_SELECTOR` ahora empieza por `ES` y sigue con Latinoamérica; afecta a landing, `/pago`, `/bienvenida` y `/organizaciones/nueva`.
   - El SEO genérico cambió de "para Latinoamérica" a **"para España y Latinoamérica"**, con H1 "…para España y Latinoamérica" y sub que menciona EUR/NIF/IVA 21 % y LatAm.
   - El cuerpo SEO genérico añade un bloque **"Cada país, su propio catálogo de precios"** (España EUR/NIF 21 %, Colombia COP/NIT 19 %, México MXN/RFC 16 %, Venezuela USD/RIF 16 %) y otro **"España, primer mercado europeo"**.

2. **Catálogo por país, explícito.**
   - Barra superior nueva: **"Tu país, tu catálogo de precios"** + badge "✨ precios de tu mercado" + hint que ahora dice "Elige tu país para ver su catálogo de precios (España · LatAm)".
   - Hero: franja de **mercados** (España, Venezuela, Colombia, México, Ecuador, Perú + 12 más), cada uno con su moneda e IVA, linkeada a `/es/`, `/ve/`, etc.
   - Nueva sección premium **"Catálogo por país, no genérico"** con una matriz (España EUR/IVA 21/NIF → Venezuela USD/RIF → Colombia COP/NIT → México MXN/RFC → Ecuador USD → Perú PEN) y el mensaje de que el país se elige al entrar.
   - La franja "España en euros" sustituye al genérico "moneda local" y todo el JS del selector (título, meta, banner, franja, moneda, vocabulario) se actualizó para ser ES-first y hablar de catálogo por país.

3. **Look más premium.**
   - Barra de país: fondo navy profundo con radiales dorado/azul, texto con gradiente, select con sombra y badge oro.
   - Hero: fondos radiales más ricos, tarjetas de mercado glass con hover/elevación, tarjetas de "outcomes" con iconos en gradiente y sombra fina, mockup del panel con sombra más profunda.
   - Botones primarios con gradiente azul y **efecto brillo que recorre al hover**; secundarios glass con borde dorado.
   - Tarjetas (ventajas, tarjetas, APU, ventana del showcase) con sombras suaves y borde luminoso; kickers con tinte dorado; fila de la comparativa `CotizaT` sobre fondo dark premium.
   - Se mantiene el **CSS crítico inline** para el primer viewport, así que el LCP no se degrada: el look premium se activa donde corresponde sin redibujo del H1.

4. **Mensaje de honestidad claro en el catálogo por país.** Cada país tiene su catálogo **de referencia** (con sus precios, moneda, IVA, ID fiscal y vocabulario). La app además permite al usuario editar cualquier partida/recurso y congelar su tasa en cada presupuesto. No se promete una cotización de tienda exacta; se promete un punto de partida de su mercado, editable.

**Cómo debería leerse ahora la home**
> CotizaT es software de presupuestos de obra y reformas para **España y Latinoamérica**. Cada país tiene su catálogo de precios, su moneda, su IVA y su vocabulario: elige el tuyo y cotiza con precios de tu mercado. Además ves **beneficio y margen en vivo**, **tiempo de cuadrilla**, **importas Excel/BC3 y mides planos**, y cierras con un **PDF profesional con versiones, firma y WhatsApp**.
