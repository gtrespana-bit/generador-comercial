# Estrategia SEO país por país — CotizaT

**Fecha:** 19 de octubre de 2026  
**Dominio canónico:** `https://cotizat.online`  
**Mercados:** 23 (18 hispanohablantes + 5 anglófonos)  
**Decisión:** dejar de tratar «país» como una sustitución de nombre y construir un silo editorial completo por mercado.

## 1. Respuesta corta

Sí: para mejorar el SEO de forma sustancial hay que trabajar **un país cada vez**. Una landing con moneda, impuesto y vocabulario local es necesaria, pero no basta. Para que Google y una empresa local perciban autoridad, cada mercado necesita:

1. **Una propuesta comercial propia**, no una traducción de la portada.
2. **Tres o cuatro clusters de búsqueda**, cada uno con una URL y una intención distintas.
3. **Datos de primera mano del producto**: precios nacionales, coste de mano de obra, fiscalidad que de verdad soporta la aplicación, unidades y documentos.
4. **Pruebas locales**: ejemplo de presupuesto, captura/PDF, cliente, caso o testimonio del país.
5. **Enlaces locales**: gremios, proveedores, directorios, medios técnicos y colaboradores de ese mercado.
6. **Medición separada**: impresiones, clics, registros, primer presupuesto y pagos por país.

No se deben publicar de golpe 54 artículos obtenidos cambiando moneda y gentilicio. Eso crea contenido programático débil. El método correcto es cerrar un país, medirlo y pasar al siguiente.

## 2. Auditoría real del sitio

### Lo que ya está bien

- Una canónica por mercado: `/es/`, `/mx/`, `/co/`, `/en-gb/`, etc.
- `hreflang` con locale real (`es-ES`, `es-MX`, `en-GB`, `en-US`).
- Landing, tres hubs (`software-presupuestos`, `apu`, `remodelacion`), sitemap, robots, Open Graph y JSON-LD.
- Moneda, identificación fiscal, impuesto, formato numérico y vocabulario del producto por país.
- Matrices nacionales de precios y documentación de fuentes.
- Reino Unido tiene cuatro guías; EE. UU., Irlanda, Australia y Canadá tienen tres cada uno.

### El hueco principal

La cobertura editorial es desigual:

| Grupo | Estado antes de esta ronda |
|---|---|
| Reino Unido | 4 artículos de mercado |
| EE. UU., Irlanda, Australia y Canadá | 3 artículos por mercado |
| Venezuela, Colombia, México, Ecuador y Perú | 1 artículo por mercado |
| España | 0 artículos de mercado |
| Otros 12 mercados hispanos | 0 artículos de mercado |

Además, los cinco artículos hispanos existentes vivían en `/guia/...`, fuera del país. Eso debilitaba la arquitectura: una guía colombiana estaba enlazada desde Colombia, pero su URL no pertenecía al silo `/co/`.

### Qué se ha implantado en esta ronda

España es el primer país hispano trabajado a fondo:

- `/es/guia/plantilla-presupuesto-reforma-espana`
- `/es/guia/precio-hora-mano-obra-construccion-espana`
- `/es/guia/bc3-presupuestos-reformas-espana`

Las tres páginas tienen contenido propio (más de 800 palabras útiles cada una), title, H1, description, FAQ visible, Article schema, tablas y enlaces hacia los hubs españoles. La tabla de mano de obra lee la misma matriz nacional de 388 recursos que usa el producto; no copia cifras a mano.

También se ha corregido la arquitectura para todos los artículos hispanos:

- La canónica de `apu-panete-colombia` pasa a `/co/guia/apu-panete-colombia`.
- La canónica mexicana pasa a `/mx/guia/...`; lo mismo para VE, PE y EC.
- Las URLs antiguas `/guia/...` responden **301** a la nueva canónica.
- Un artículo español bajo `/mx/guia/...` responde 404, no 200 con canonical cruzada.
- Sitemap, migas, `inLanguage`, `hreflang`, mapa del sitio, landing y hubs usan la URL de país.
- `HowTo` solo se publica cuando el texto es realmente un procedimiento.

## 3. Qué significa «terminar un país»

Un mercado pasa de **abierto** a **SEO completo v1** cuando cumple esta lista:

### Investigación

- [ ] Exportar de Search Console todas las consultas e impresiones del subdirectorio.
- [ ] Revisar manualmente las primeras 10 SERP de 20 consultas; registrar tipo de resultado, competencia y formato.
- [ ] Entrevistar al menos a 3 profesionales del país o analizar 10 presupuestos reales anonimizados.
- [ ] Validar el vocabulario con el producto y con documentos locales; no con un diccionario general.
- [ ] No inventar volumen de búsqueda. Si no hay Keyword Planner/Ahrefs/Semrush, priorizar por intención y GSC.

### Producto y prueba

- [ ] Moneda, impuesto e ID fiscal correctos.
- [ ] Matriz nacional de precios cargada y fechada.
- [ ] Ejemplo PDF local, con términos y formato numérico del país.
- [ ] La página no promete factura electrónica, cálculo fiscal o función que el producto no hace.
- [ ] Una tabla o dato original que otro blog no tenga: mano de obra, materiales, tratamiento fiscal soportado o metodología.

### Contenido

- [ ] Landing de país con posicionamiento y objeciones locales.
- [ ] Tres hubs de intención con cuerpo local, no find-and-replace.
- [ ] Tres artículos iniciales: documento/plantilla, precios/mano de obra, problema técnico o fiscal local.
- [ ] Cada artículo responde una intención; ninguna pareja compite por la misma consulta principal.
- [ ] Enlazado país → hubs → artículos → producto, y artículos entre sí solo cuando es útil.

### Autoridad y distribución

- [ ] Un colaborador, asociación, proveedor, medio o directorio local enlaza o menciona el recurso.
- [ ] Una pieza visual local: vídeo, captura, PDF o tabla compartible.
- [ ] Perfil y testimonios del país si existen; nunca inventados.
- [ ] Revisión de exactitud por una persona del mercado en temas fiscales o laborales.

### Medición

- [ ] Dashboard filtrado por subdirectorio y `pais_codigo`.
- [ ] Indexación de todas las canónicas, sin «duplicada» ni «página con redirección» en sitemap.
- [ ] Eventos: visita orgánica → CTA → registro → primer presupuesto → pago.
- [ ] Fecha de revisión de contenido y responsable.

## 4. Orden recomendado, sin dispersarse

El orden no es solo población. Combina ajuste del producto, datos ya disponibles, intención comercial y trabajo pendiente.

| Orden | Mercado | Motivo |
|---:|---|---|
| 1 | **España** | Mercado prioritario, matriz EUR, BC3 y vocabulario propio. Paquete v1 implantado en esta ronda. |
| 2 | **México** | Mayor escala hispana y uso natural de «cotización»; ya existe una guía de remodelación. |
| 3 | **Colombia** | Ajuste muy fuerte con APU; oportunidad clara para diferenciar APU privado de AIU público. |
| 4 | **Perú** | «Metrados» crea un cluster propio que no compite con México o Colombia. |
| 5 | **Chile** | Mercado listo en CLP, vocabulario y precios; aún no tiene un solo artículo. |
| 6 | **Argentina** | Dolor fuerte de actualización de precios y versiones; requiere especial cuidado con fechas. |
| 7 | **Venezuela** | Producto muy adaptado a USD/Bs y tasa congelada; ya tiene una guía. |
| 8 | **Ecuador** | USD nativo, RUC y APU; ya tiene una guía y buen encaje con precios locales. |
| 9 | **República Dominicana** | «Cubicación», DOP e ITBIS permiten diferenciar el corpus. |
| 10 | **Panamá** | USD, ITBMS y referencias de convenio/mercado; intención comercial clara. |
| 11 | **Costa Rica** | CRC, NITE y terminología propia; evitar prometer trámites CFIA que el producto no hace. |
| 12 | **Guatemala** | GTQ, NIT, FEL como exclusión clara y precios nacionales. |
| 13 | **Honduras** | HNL, RTN, ISV y costes de mano de obra investigados. |
| 14 | **El Salvador** | USD, NIT, IVA y precios locales; diferenciarlo de Panamá/Ecuador aunque compartan moneda. |
| 15 | **Nicaragua** | NIO, RUC y precios nacionales; corpus aún inexistente. |
| 16 | **Uruguay** | UYU y RUT; los temas BPS/obra requieren revisión especializada antes de publicar. |
| 17 | **Paraguay** | PYG sin decimales es una diferencia real y útil; menor señal esperada. |
| 18 | **Bolivia** | BOB y cómputos métricos; validar vocabulario y búsquedas antes de ampliar. |

Los cinco mercados anglófonos ya tienen un paquete v1. Se mantienen y amplían según datos; no deben quitar capacidad al siguiente país hispano.

## 5. Plan editorial específico de cada país

Los títulos son **hipótesis de intención**, no una orden para publicarlos sin SERP/GSC. Cada fila incluye diferencias que el texto debe demostrar.

### España (`/es/`) — v1 implantada

**Posicionamiento:** reformistas y pequeñas constructoras que necesitan presupuesto comercial en EUR, catálogo español y entrada/salida BC3.

1. **Plantilla de presupuesto de reforma en España** — documento, capítulos, mediciones, opciones, IVA, condiciones y versiones.
2. **Precio por hora de mano de obra en España (2026)** — coste empresa frente a tarifa; tabla desde la matriz EUR.
3. **BC3 en presupuestos de reformas** — importación, revisión, localización de precios y exportación FIEBDC-3.

**Prueba que falta fuera del código:** PDF español descargable y un caso real de empresa de reformas.  
**No prometer:** factura AEAT/VeriFactu ni que el tipo reducido de IVA se decide automáticamente.

### México (`/mx/`) — siguiente recomendado

**Lenguaje:** cotización, aplanado, plafón, zoclo, banqueta, MXN, RFC, IVA 16 %.  
**Ya existe:** guía de la visita a la cotización de remodelación.

Siguientes clusters:

1. **Precio de mano de obra de construcción en México 2026** — jornal, coste empresa y rendimiento; separar CDMX/Monterrey/Guadalajara solo si la fuente lo permite.
2. **Catálogo de conceptos y análisis de precios unitarios** — qué es concepto, insumo, rendimiento y precio; sin presentarse como Neodata.
3. **Presupuesto de remodelación de baño en México** — alcance y omisiones, no un precio nacional ficticio por m².

**Activo enlazable:** tabla de recursos MXN con fuente y rango.  
**No prometer:** CFDI, PAC, licitación o lectura automática de planos.

### Colombia (`/co/`)

**Lenguaje:** APU, pañete, andén, sardinel, guardaescoba, COP, NIT, IVA 19 %.  
**Ya existe:** APU de pañete.

Siguientes clusters:

1. **APU vs AIU en Colombia** — explicar que el APU descompone partidas y que CotizaT no calcula AIU de contrato estatal.
2. **Coste de mano de obra de construcción en Colombia 2026** — coste empresa y rendimiento en COP.
3. **Plantilla de cotización para remodelación en Colombia** — obra privada, cambios y PDF para WhatsApp.

**Activo enlazable:** calculadora/tabla APU de pañete con recursos editables.  
**No prometer:** SECOP, interventoría, pliegos ni factura DIAN.

### Perú (`/pe/`)

**Lenguaje:** metrados, tarrajeo, vereda, gasfitero, PEN/S/, RUC, IGV 18 %.  
**Ya existe:** guía de metrados y APU.

Siguientes clusters:

1. **Cómo pasar de metrados a presupuesto** — zonas, partidas, cantidades y APU.
2. **Precio de mano de obra de construcción en Perú 2026** — coste empresa en soles y rangos.
3. **APU de tarrajeo en Perú** — recursos, rendimiento y diferencia entre coste y venta.

**Activo enlazable:** ejemplo de metrado → APU → PDF.  
**No prometer:** expediente S10, obra pública ni comprobante SUNAT.

### Chile (`/cl/`)

**Lenguaje:** hormigón, estuco, cielo falso, guardapolvo, gasfíter, CLP, RUT, IVA 19 %.

Primer paquete:

1. **Plantilla de presupuesto de construcción en Chile** — formato en CLP y alcance de obra privada.
2. **Precio de mano de obra de construcción en Chile 2026** — coste empresa, no sueldo líquido ni tarifa final.
3. **APU de estuco en Chile** — recursos, rendimiento, pérdidas y margen.

**Activo enlazable:** tabla CLP sin decimales innecesarios y ejemplo local.  
**No prometer:** facturación SII, estados de pago normativos o funciones de licitación.

### Argentina (`/ar/`)

**Lenguaje:** hormigón, revoque, cielorraso, zócalo, ARS, CUIT, IVA 21 %.

Primer paquete:

1. **Cómo actualizar un presupuesto de obra sin cambiar el PDF enviado** — fecha de precios, versiones y vigencia.
2. **Coste de mano de obra de construcción en Argentina 2026** — siempre con fecha de corte visible.
3. **APU de revoque en pesos argentinos** — recursos y rendimientos; no una lista eterna de precios.

**Activo enlazable:** histórico de fecha/rango, no solo cifra central.  
**Riesgo:** inflación. Todo dato monetario necesita fecha, fuente, caducidad y revisión más frecuente.

### Venezuela (`/ve/`)

**Lenguaje:** concreto, friso, cielo raso, rodapié, USD/Bs, RIF, IVA 16 %.  
**Ya existe:** presupuesto USD/Bs con tasa congelada.

Siguientes clusters:

1. **APU de friso en Venezuela** — materiales, cuadrilla, rendimiento y coste en USD/Bs.
2. **Coste de mano de obra de construcción en Venezuela 2026** — fecha, zona y moneda de referencia explícitas.
3. **Plantilla de presupuesto de remodelación en dólares y bolívares** — vigencia y versiones.

**Activo enlazable:** ejemplo del mismo presupuesto en USD/Bs con tasa congelada.  
**Riesgo:** no publicar una «tasa de hoy» que quede obsoleta; explicar metodología y fecha.

### Ecuador (`/ec/`)

**Lenguaje:** hormigón, enlucido, tumbado, barredera, gasfitero, USD, RUC, IVA 15 %.  
**Ya existe:** APU en dólares.

Siguientes clusters:

1. **Precio de mano de obra de construcción en Ecuador 2026**.
2. **APU de enlucido en Ecuador** — vocabulario y recursos locales.
3. **Plantilla de presupuesto de obra en Ecuador** — USD nativo, RUC e IVA configurable.

**Activo enlazable:** tabla en USD sin conversión artificial.  
**No prometer:** factura electrónica SRI.

### República Dominicana (`/do/`)

**Lenguaje:** cubicación, hormigón, pañete, plafón, DOP, RNC, ITBIS 18 %.

Primer paquete:

1. **Cómo hacer una cubicación para presupuesto en República Dominicana**.
2. **Precio de mano de obra de construcción en RD 2026**.
3. **Plantilla de presupuesto en pesos dominicanos con ITBIS**.

**Activo enlazable:** ejemplo cubicación → partidas → PDF.  
**Revisión necesaria:** uso exacto de «cubicación» por segmento y tratamiento de ITBIS antes de un artículo fiscal.

### Uruguay (`/uy/`)

**Lenguaje:** hormigón, revoque, cielorraso, sanitario, UYU, RUT, IVA 22 %.

Primer paquete:

1. **Plantilla de presupuesto de reforma en Uruguay**.
2. **Coste de mano de obra de construcción en Uruguay 2026**.
3. **APU de revoque en pesos uruguayos**.

**Activo enlazable:** tabla UYU con coste empresa y rango.  
**No publicar aún:** una guía normativa de BPS de construcción hasta tener función en producto y revisión profesional.

### Paraguay (`/py/`)

**Lenguaje:** hormigón, revoque, cielorraso, PYG/guaraníes, RUC, IVA 10 %.

Primer paquete:

1. **Presupuesto de obra en guaraníes sin decimales**.
2. **Precio de mano de obra de construcción en Paraguay 2026**.
3. **APU de revoque en Paraguay**.

**Activo enlazable:** PDF que demuestre formato PYG sin céntimos y separadores correctos.  
**No prometer:** factura SIFEN/SET.

### Bolivia (`/bo/`)

**Lenguaje:** cómputos métricos, hormigón, revoque, cielo falso, BOB, NIT, IVA 13 %.

Primer paquete:

1. **De cómputos métricos a presupuesto de obra en Bolivia**.
2. **Precio de mano de obra de construcción en Bolivia 2026**.
3. **APU de revoque en bolivianos**.

**Activo enlazable:** ejemplo de cómputo y descompuesto en BOB.  
**Validar primero:** vocabulario con profesionales de La Paz, Santa Cruz y Cochabamba; no crear páginas de ciudad todavía.

### Panamá (`/pa/`)

**Lenguaje:** concreto, repello, cielo raso, USD/PAB, RUC, ITBMS 7 %.

Primer paquete:

1. **Plantilla de presupuesto de construcción en Panamá**.
2. **Precio de mano de obra de construcción en Panamá 2026** — distinguir mínimo/convenio/coste empresa.
3. **APU de repello en Panamá**.

**Activo enlazable:** tabla de recursos en USD con referencias panameñas, no precios ecuatorianos reutilizados.  
**No prometer:** factura DGI ni cumplimiento de convenio automático.

### Costa Rica (`/cr/`)

**Lenguaje:** concreto, repello, cielo raso, rodapié, fontanero, CRC/colones, NITE, IVA 13 %.

Primer paquete:

1. **Plantilla de presupuesto de construcción en Costa Rica**.
2. **Precio de mano de obra de construcción en Costa Rica 2026**.
3. **APU de repello en colones**.

**Activo enlazable:** tabla CRC con formato `1.234,56`.  
**No prometer:** trámite CFIA, APC o factura Hacienda.

### Guatemala (`/gt/`)

**Lenguaje:** concreto, repello, cielo falso, block, flipón, GTQ/quetzales, NIT, IVA 12 %.

Primer paquete:

1. **Plantilla de presupuesto de construcción en Guatemala**.
2. **Precio de mano de obra de construcción en Guatemala 2026**.
3. **APU de repello y block en quetzales**.

**Activo enlazable:** canasta EPA/Cemaco/Construfácil/INE documentada en la investigación.  
**No prometer:** factura FEL.

### Honduras (`/hn/`)

**Lenguaje:** concreto, repello, cielo falso, bloque, HNL/lempiras, RTN, ISV 15 %.

Primer paquete:

1. **Plantilla de presupuesto de construcción en Honduras**.
2. **Precio de mano de obra de construcción en Honduras 2026**.
3. **APU de pared de bloque o repello en lempiras**.

**Activo enlazable:** tabla de jornal y coste empresa con rango.  
**No prometer:** factura SAR ni un precio nacional exacto sin variación regional.

### El Salvador (`/sv/`)

**Lenguaje:** concreto, repello, cielo falso, USD, NIT, IVA 13 %.

Primer paquete:

1. **Plantilla de presupuesto de construcción en El Salvador**.
2. **Precio de mano de obra de construcción en El Salvador 2026**.
3. **APU de repello en dólares**.

**Activo enlazable:** referencias CASALCO y precios USD con fecha.  
**Diferenciación:** no reciclar Ecuador o Panamá por compartir USD; jornal, IVA, ID y fuentes son salvadoreños.

### Nicaragua (`/ni/`)

**Lenguaje:** concreto, repello, cielo raso, Gypsum, NIO/córdobas, RUC, IVA 15 %.

Primer paquete:

1. **Plantilla de presupuesto de construcción en Nicaragua**.
2. **Precio de mano de obra de construcción en Nicaragua 2026**.
3. **APU de repello en córdobas**.

**Activo enlazable:** tabla NIO basada en SINSA/MITRAB y rangos.  
**No prometer:** factura DGI.

## 6. Mercados anglófonos: mantener por país, no agruparlos como «English»

### Estados Unidos (`/en-us/`)

**Ya publicado:** estimate template, sales tax en 51 jurisdicciones, labor cost/h.  
**Siguiente solo con GSC:** `change order template`, `allowance vs estimate`, o páginas estatales únicamente para estados con impresiones y producto/fiscalidad suficientes. No generar 50 páginas cambiando el nombre del estado.

### Reino Unido (`/en-gb/`)

**Ya publicado:** quote template, CIS, domestic reverse charge, unit price analysis.  
**Siguiente:** day rates, schedule of works, snagging list, how to price a job. Mantener spelling británico y no mezclar GST/RCT.

### Australia (`/en-au/`)

**Ya publicado:** building quote, GST, tradie rates.  
**Siguiente:** prime cost vs provisional sum, progress claims, variations. Las licencias son estatales: no afirmar una regla nacional.

### Canadá (`/en-ca/`)

**Ya publicado:** estimate template, GST/HST por provincia, labour rates.  
**Siguiente:** holdback por provincia o estimate vs quote. Solo abrir páginas provinciales cuando GSC muestre demanda y el producto represente esa diferencia.

### Irlanda (`/en-ie/`)

**Ya publicado:** quote template, VAT/two-thirds rule, builder rates.  
**Siguiente:** RCT para subcontratistas, payment claims, scope of works. No mezclar CIS británico con RCT irlandés.

## 7. Sprint de seis semanas para cada país

### Semana 1 — investigación, no redacción

- Exportar GSC y agrupar consultas por intención.
- Revisar SERP: producto, plantilla, precios, pregunta fiscal/técnica.
- Hablar con profesionales y reunir documentos reales.
- Elegir solo tres URLs y redactar un brief de cada una: consulta principal, secundarias, promesa, prueba, CTA y páginas que enlaza.

### Semana 2 — producto y fuente de verdad

- Verificar que la matriz nacional está en producción.
- Generar un presupuesto de ejemplo y comprobar moneda, separadores, impuesto, ID y vocabulario.
- Extraer tablas desde código/CSV/servicio cuando sea posible; evitar cifras duplicadas en copy.
- Corregir cualquier promesa que la aplicación no cumpla antes de publicar.

### Semana 3 — publicar el paquete completo

- Actualizar landing y hubs con conclusiones del mercado.
- Publicar tres artículos dentro del silo `/{cc}/guia/` o `/en-{cc}/guia/`.
- Añadir canonical, locale, Article/HowTo cuando corresponda y sitemap.
- Enlazar landing ↔ hubs ↔ artículos, sin granjas de enlaces a otros países.

### Semana 4 — prueba y distribución local

- PDF o plantilla descargable.
- Vídeo de 3–5 minutos con el mercado en título y ejemplo.
- Contacto con 20 sitios locales realmente relacionados; no comprar paquetes de enlaces.
- Conseguir revisión o mención de un profesional local.

### Semanas 5–6 — observar y corregir

- Indexación, consultas reales, CTR y posición.
- Reescribir title/description si hay impresiones sin clics.
- Ampliar secciones que Google ya relaciona con consultas; no abrir diez URLs nuevas.
- Decidir: iterar, crear una cuarta pieza o congelar y pasar al siguiente país.

## 8. Cuadro de mando por país

Medir por subdirectorio y por mercado del registro:

| Nivel | Métrica | Señal útil |
|---|---|---|
| Técnico | URLs canónicas indexadas / enviadas | Debe tender a 100 %, sin duplicadas ni redirecciones en sitemap |
| Visibilidad | Consultas no de marca con impresiones | Crecimiento de variedad, no solo una keyword |
| Ranking | Consultas en top 3 / 10 / 20 | Separadas por país e intención |
| Snippet | CTR por URL y posición | Detecta title/description débiles |
| Negocio | CTA por sesión orgánica | El artículo debe mover al producto |
| Activación | Registros que crean primer presupuesto | Más valioso que el registro solo |
| Ingreso | Pagos y MRR/ARR atribuidos al país | Decide dónde seguir invirtiendo |
| Calidad | Bajas rápidas, soporte y promesas incumplidas | Un ranking que atrae al usuario equivocado es negativo |

No mezclar todos los países en una media. Diez registros de Colombia y ninguno que crea un APU señalan un problema distinto de tres registros españoles que importan BC3 y pagan.

## 9. Reglas que no se deben romper

1. **Una URL, una intención, un país.**
2. **Un artículo de país vive dentro del subdirectorio del país.**
3. **No hacer páginas de ciudades sin prueba, demanda y diferencia real.**
4. **No traducir fiscalidad:** CIS ≠ RCT, GST ≠ IVA, CFDI ≠ presupuesto.
5. **No clavar precios sin fecha, rango y metodología.**
6. **No publicar legislación sin revisión y sin reflejo honesto en el producto.**
7. **No crear páginas masivas para llenar el sitemap.** Tres recursos excelentes superan treinta páginas intercambiables.
8. **No medir solo tráfico.** El objetivo es un presupuesto creado y un cliente pagador del país.
9. **No cambiar una URL indexada sin 301.**
10. **No abrir el siguiente mercado hasta que el paquete del actual esté publicado, distribuido y medido.**

## 10. Próximo paso concreto

1. Desplegar el paquete de España y reenviar `sitemap.xml` en Search Console.
2. Inspeccionar las tres URLs `/es/guia/...` y verificar canonical `es-ES` sin `noindex`.
3. Crear el PDF español de ejemplo y conseguir revisión de un reformista real.
4. Iniciar el sprint de **México**, empezando por GSC/SERP y la tabla de coste de mano de obra; no redactar las tres piezas hasta validar las consultas.
5. Revisar España a los 28 y 56 días. Si una de las tres páginas recibe impresiones, mejorar esa antes de añadir una cuarta.
