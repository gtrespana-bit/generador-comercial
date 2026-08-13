# Análisis a fondo del proyecto, opinión honesta de viabilidad comercial y hoja de ideas

> Documento de análisis independiente sobre el estado real del repositorio, escrito tras leer el
> código, ejecutar la aplicación, pasar la batería de tests y revisar visualmente el PDF que genera.
> Fecha: 13 de agosto de 2026.

---

## 0. Qué se hizo para poder opinar (y no hablar de oídas)

No es una opinión leyendo el README. Esto es lo que se comprobó de verdad:

| Verificación | Resultado |
|---|---|
| Inventario de código | 105 archivos versionados, ~33.900 líneas entre Python, JS, HTML y CSS |
| Instalación limpia de dependencias en venv nuevo | OK, sin conflictos |
| Suite de tests (`pytest tests/`) | **58 pasados, 0 fallos**, 3,3 s |
| Arranque de la app (`uvicorn`) | Levanta sin errores |
| 13 rutas principales vía HTTP | **Todas 200** |
| Generación de PDF real (`/presupuestos/1/pdf`) | 200, 4 páginas, 68 KB |
| Inspección **visual** del PDF generado (render a PNG) | Revisado página a página |
| Inspección visual del PDF real de obra (`P-2026-003 La Rusticana`, 15 págs.) | Revisado |
| Búsqueda de capa de seguridad (`auth`, `login`, `session`, `password`, `csrf`, `cors`) | **Cero coincidencias en todo el proyecto** |
| Contenido real de la BD | 59 partidas de catálogo, 8 recetas de estancia, 4 presupuestos, 11 items |

---

## 1. Qué es esto realmente, en una frase

No es "un generador de presupuestos". Es un **ERP vertical de bolsillo para una empresa de
reformas**: presupuestación con mediciones y descompuestos al estilo CYPE, catálogos propios,
versionado, contratos, garantías, facturas, proyectos con cambios de alcance y pagos, estimación
de tiempos, dashboard con analítica de márgenes y un motor de PDF comercial. Todo ello funcionando
**offline, sin depender de un solo servicio externo**, y empaquetable como aplicación de escritorio
para Windows.

Ese alcance está muy por encima de lo que la mayoría de la gente imagina cuando dice "hice un
generador de presupuestos". Ese es el dato central de todo este análisis.

---

## 2. Arquitectura y estado técnico

### 2.1 Stack

```
FastAPI + Jinja2 (SSR)  ·  SQLAlchemy 2.0 + SQLite  ·  ReportLab (PDF)
openpyxl (Excel)  ·  Pillow  ·  JS vanilla modular (sin framework, sin build)
PyInstaller + Inno Setup + pywebview (WebView2) → .exe instalable en Windows
```

Elección **acertada** para el objetivo: cero build step, cero node_modules en producción, se
empaqueta en un ejecutable y funciona sin internet. Es la decisión correcta para el mercado
venezolano, donde la conectividad no se da por supuesta.

### 2.2 Mapa del código

| Módulo | Líneas | Nota |
|---|---:|---|
| `app/main.py` | 5.073 | **112 rutas en un solo archivo** — el principal problema estructural |
| `app/models.py` | 1.670 | ~28 modelos + `migrar()` aditiva idempotente |
| `app/services/pdf.py` | 1.381 | Motor de PDF, 6 estilos + anexos |
| `app/services/pdf_interactivo.py` | 852 | PDF con formulario/aceptación |
| `app/services/importer.py` | 812 | Importación CYPE/Excel/CSV |
| `app/services/excel_export.py` | 763 | Exportación |
| `app/services/tiempos.py` | 598 | Estimación de plazos en 3 niveles |
| `app/services/recursos.py` | 351 | Descompuestos |
| `app/services/garantias.py` | 288 | Anexo de garantías por familia |
| `app/services/calculations.py` | 259 | **Motor de cálculo único** |
| `app/services/contrato.py` | 167 | Contrato en PDF |
| `app/services/versions.py` | 89 | Versionado inmutable |
| `app/static/js/editor/partida.js` | 2.645 | Editor de partidas |
| `app/static/css/style.css` | 3.215 | 16 media queries → responsive real |

### 2.3 Lo que está genuinamente bien hecho (y no es habitual verlo)

1. **Motor de cálculo único con `Decimal` y `ROUND_HALF_UP`.**
   `calculations.py` es la única fuente de verdad para web, CSV y PDF. Esto es exactamente lo que
   la mayoría de proyectos amateurs hace mal: calculan en el JavaScript, otra vez en el template y
   otra vez en el PDF, y acaban con tres totales distintos por redondeo en coma flotante. Aquí no.
   Un software de presupuestos que descuadra un céntimo pierde la confianza del cliente para
   siempre; esto lo tienes blindado.

2. **La tabla es la fuente de verdad, no el navegador.**
   En `_descomposicion_catalogo` está escrito literalmente: *"nunca se confía en subtotales
   enviados por el navegador"*. Recalcula todo en servidor. Es criterio de ingeniero, no de
   tutorial.

3. **Migraciones aditivas idempotentes.**
   `migrar(engine)` añade columnas con `ALTER TABLE ... ADD COLUMN` y reconstruye tablas cuando el
   esquema cambió de verdad, envolviendo partidas antiguas en un "CAPÍTULO GENERAL". Es decir:
   **un usuario que actualice de versión no pierde sus datos.** Sin esto no se puede vender nada
   que se actualice.

4. **Validación real de archivos subidos.**
   Las imágenes se abren con Pillow y se verifican (no se confía en la extensión), los PDF se
   validan por firma `%PDF-`, hay límite de 12 MB, y los nombres se regeneran con UUID para que
   dos presupuestos no se pisen las fotos. La restauración de backups tiene **protección contra
   zip-slip** (`..`, rutas absolutas, `commonpath`). Eso es seguridad de nivel profesional.

5. **Backup automático semanal en zip + restauración desde la UI**, con copia de lo anterior antes
   de sobrescribir. El usuario típico de este software no hace copias de seguridad jamás; que la
   app las haga sola es una función que evita un desastre.

6. **Un middleware propio para un bug real de Starlette** (decodificación de formularios
   urlencoded en Latin-1). Alguien detectó por qué se rompían las tildes y lo arregló en la capa
   correcta, en vez de parchear cada campo.

7. **Honestidad de producto.** Esto merece mención aparte. En `analisis.py`, `garantias.py`,
   `contrato.py` y `generador.js` está documentado que estos módulos **sustituyeron a botones
   falsos** de "IA", "Smart" y "Blockchain" que solo lanzaban un `alert()` con texto fijo. Hoy:
   - "Autogenerar con IA" = matcher determinista por palabras clave sobre **tu propio catálogo**.
   - "Optimizar precios" = compara precio de venta contra coste interno real, avisa si el margen
     baja del 15 % o si el precio lleva más de 180 días sin revisar.
   - Contrato = PDF real generado con ReportLab.

   Alguien se sentó a borrar su propio humo y reemplazarlo por cálculo real. Eso dice más sobre la
   viabilidad del producto que cualquier lista de features.

### 2.4 Lo que está mal o es deuda técnica

| Problema | Gravedad | Por qué importa |
|---|---|---|
| `main.py` de 5.073 líneas con 112 rutas | Alta | Cada cambio es un riesgo. Imposible que entre un segundo desarrollador. Añadir auth aquí es doloroso. |
| **Cero autenticación, cero usuarios, cero roles** | Crítica para SaaS | Ver §4 |
| `run.py` sirve en `0.0.0.0:8000` sin protección | Alta | Cualquiera en la misma WiFi (una obra, un coworking) entra y edita/borra todo. Sin login, sin registro de quién hizo qué. |
| Sin CSRF ni CORS | Media-alta en LAN | Una web maliciosa abierta en el mismo PC puede hacer POST a `localhost:8000/presupuestos/1/eliminar`. |
| `base.html` carga la fuente Inter desde Google Fonts | Media | **Rompe la coherencia visual sin internet** — justo el escenario que el resto del producto cuida. Además filtra la IP de tus clientes a Google. Las Lato ya están embebidas: haz lo mismo con Inter. |
| Datos de RemodelaT hardcodeados en `models.py` (nombre, teléfono `04227997043`, email, web, dirección) | Alta para vender | El primer cliente que instale ve **tu** teléfono como configuración por defecto. |
| 67 `except Exception` en el código, 17 de ellos con `pass` | Media | Los fallos se tragan en silencio. Cuando un cliente diga "no me guardó la foto", no habrá ni un log que lo explique. |
| Sin `LICENSE` | Media | Legalmente el código no tiene términos. Si vas a vender licencias, necesitas EULA. |
| Sin CI (GitHub Actions) | Media | Tienes 58 tests excelentes que nadie ejecuta automáticamente al hacer merge. |
| Historia git de 1 commit | Baja | Sin trazabilidad. Cosmético, pero se nota al abrir el repo. |
| Sin envío por email (SMTP) | Alta comercial | Solo WhatsApp y descarga manual del PDF. Es la carencia funcional #1. |
| Solo 3 productos y 0 recursos sembrados frente a 59 partidas | Media | El catálogo de productos y recursos está prácticamente vacío para un cliente nuevo. |

---

## 3. El PDF: el activo comercial más fuerte del producto

Lo revisé visualmente, no solo comprobé que devolviera 200. **Es el mejor argumento de venta que
tienes**, muy por encima de la interfaz.

Lo que produce el documento:

- Cabecera con logo, bloque de empresa (email, teléfono, web, dirección), título **PRESUPUESTO**,
  datos de obra y ficha de cliente (nombre, RIF, país, validez, nº de presupuesto).
- Capítulos con banda azul oscuro y **subtotal del capítulo alineado a la derecha**.
- Partidas numeradas jerárquicamente (1.1, 1.2, 2.1…) con **descripción técnica larga de calidad
  CYPE** ("Acometida enterrada para abastecimiento de agua potable de tubo de polietileno PE 100,
  de 32 mm de diámetro exterior, PN=10 atm y 2 mm de espesor…"), columnas Cantidad / Precio /
  Importe.
- **Líneas de medición desglosadas** ("Cocina Aprox (4,00 x 2,50)", "Muro Habitación Principal").
  Esto es lo que separa un presupuesto profesional de una lista de precios.
- Bloque "Producto presupuestado" con precio unitario y descripción del material.
- Marca de agua diagonal **BORRADOR**, paginación "1/15".
- Página de totales: Base imponible / IVA (16 %) / **PRESUPUESTO TOTAL** destacado, más
  "Información adicional" y "Condiciones del presupuesto".
- Anexo **GARANTÍAS DE LA OBRA** con tarjetas por familia: Estructuras/tabiques 5 años, Pisos y
  revestimientos 5 años, Carpintería de madera 3 años, Plomería 5 años, Pintura 2 años, cada una
  con alcance y exclusiones.

**Veredicto:** un cliente final recibe esto y no le queda ninguna duda de que está tratando con una
empresa seria. Es indistinguible de la salida de un software de 60 €/mes. El PDF real de la obra
"La Rusticana" (15 páginas) lo confirma en un caso de uso auténtico, no de demo.

---

## 4. Opinión honesta: ¿es esto vendible? ¿puedes cobrar mensualidad?

Voy a ser directo, incluyendo lo que no te va a gustar.

### 4.1 La respuesta corta

**Sí, es vendible. Y no, hoy no puedes cobrar una mensualidad.**

Esas dos afirmaciones no se contradicen. Son dos negocios distintos y estás listo para uno, no
para el otro.

### 4.2 Por qué "las personas que lo probaron dicen que pagarían" no es todavía una validación

Esto es lo más importante del documento. Hay una distancia enorme entre *"esto está buenísimo, yo
pagaría por esto"* y una tarjeta cobrada. Casi todo el mundo que te dice lo primero **no hace lo
segundo**, y no por mentir: en el momento de decirlo no está calculando su presupuesto real, está
siendo amable con alguien que le enseñó algo que hizo con esfuerzo.

La prueba honesta es una sola: **pídeles dinero.** Hoy, sin haber construido nada más. Diles
"cuesta X, te lo instalo esta semana". Si tres de ellos pagan, tienes un producto. Si los tres
dicen "déjame pensarlo", tienes un cumplido.

Hazlo antes de escribir una línea más de código. Es la información más valiosa que puedes
conseguir y te cuesta cero.

### 4.3 Contra qué compites (datos reales de mercado)

El mercado hispanohablante de software de presupuestos de obra está bastante poblado, y los
precios están públicos:

| Producto | Precio | Perfil |
|---|---|---|
| Presto (RIB) | ~480 €/año, o desde ~58 €/mes | Estándar en España, constructoras y licitación pública [8](https://tienda.seystic.com/producto/presto-presupuestos-mediciones/) [9](https://www.stelorder.com/blog/mejores-programas-presupuestos-de-obra/) |
| Arquímedes (CYPE) | desde ~475 € / ~70 €/mes | Técnico, Open BIM [2](https://oneestimate.ai/es/blog/mejores-software-presupuestos-construccion) |
| BrickControl | 99 €/mes | Gestión integral de obra [3](https://medicionpro.com/blog/mejor-software-gestion-obras-espana) |
| Planhopper | desde ~456 €/año | ERP de construcción para pymes [6](https://medicionpro.com/blog/alternativas-presto) |
| STIMAT | 60–75 €/mes | Clásico de reformas [5](https://reformai.app/articulos/guias/presupuesto-reforma-inteligencia-artificial) |
| Motor de Presupuestos | 39 €/mes (autónomos) | IA + voz, catálogo de 4.244 partidas [1](https://motordepresupuestos.com/) |
| MedicionPro | 29 €/mes | Cloud, BC3, certificaciones [3](https://medicionpro.com/blog/mejor-software-gestion-obras-espana) |
| ReformAI | 14,99 €/mes, plan gratis 3/mes | App móvil nativa, foto + texto [4](https://reformai.app/articulos/branded/reformai-vs-presto-comparativa) |

Dos lecturas de esta tabla:

**La buena:** funcionalmente **ya compites**. Mediciones desglosadas, descompuestos, certificable,
contratos, facturación, control de costes, versiones, PDF profesional — tienes cosas que MedicionPro
cobra a 29 €/mes y que ReformAI a 14,99 €/mes no tiene. Tu producto no es inferior en features.

**La mala:** todos esos son **cloud, multiusuario, con app móvil y con pasarela de pago**. Tú eres
un ejecutable de escritorio monousuario. En el eje "software", empatas o ganas. En el eje
"producto vendible por suscripción", ellos van dos años por delante.

### 4.4 Tu ventaja real (y no es la que crees)

No es el PDF ni el catálogo. Es esto: **nadie de esa lista sirve a Venezuela.**

Tienes funciones que ninguno de esos productos españoles tiene ni tendrá jamás:

- Número de control fiscal, retenciones de IVA/ISLR, operaciones exentas.
- Tasa de cambio con fecha, total en Bs y **cláusula cambiaria** en el presupuesto.
- Vocabulario adaptado (concreto, plomería, tomacorrientes, cielo raso, zoclo, mesón, fragüe…).
  Esa lista de traducciones en `seeds.py` es conocimiento de dominio que no se improvisa.
- **Funciona sin internet.** En un país con cortes eléctricos y conectividad irregular, un
  ejecutable local que nunca te deja tirado en una visita a obra no es una limitación técnica: es
  una característica que el cliente entiende y valora.

Ese es el foso. Un reformista de Valencia (Carabobo) no puede usar MedicionPro para emitir con
número de control y cláusula cambiaria. Tú eres el único que resuelve su problema exacto.

### 4.5 Escenario A — Licencia de escritorio: **VENDIBLE YA**

Estás a **2–3 semanas de trabajo** de poder cobrar.

Lo que falta, mínimo viable:

1. Quitar los datos de RemodelaT de los defaults y poner un **asistente de primer arranque**
   (nombre de empresa, RIF, logo, moneda, IVA) — medio día.
2. **Activación por clave de licencia** ligada al equipo (hash de máquina + firma). No hace falta
   nada sofisticado; el objetivo no es frenar a un cracker, es que el cliente honesto entienda que
   compró algo — 2–3 días.
3. Un `LICENSE` / EULA — medio día.
4. Envío por email (SMTP) — 1–2 días.
5. Manual en PDF y un vídeo de 5 minutos — 2 días.

**Precio sugerido para Venezuela:** 120–200 USD de licencia perpetua con un año de actualizaciones,
y 40–60 USD/año de renovación opcional. Con 20 licencias vendidas cubres varios meses de tu tiempo.
Es dinero real y validación real.

Este camino tiene un techo bajo (no escala, cada venta es artesanal) pero es **el que debes hacer
primero**, porque te da clientes de pago con los que aprender antes de invertir meses en el otro.

### 4.6 Escenario B — SaaS con mensualidad: **2–4 meses de trabajo, no menos**

Lo que hoy hace imposible cobrar una suscripción:

| Bloqueante | Estado actual |
|---|---|
| Autenticación | **No existe** (0 coincidencias de `login`/`session`/`password` en todo el código) |
| Usuarios y roles | No existen |
| Multi-tenant (aislamiento entre empresas) | No existe. Una BD SQLite = una empresa |
| Base de datos concurrente | SQLite. No aguanta 50 empresas escribiendo a la vez |
| CSRF / CORS | No existen |
| Auditoría (quién cambió qué) | No existe |
| Pasarela de pago recurrente | No existe |
| Recuperación de contraseña / email transaccional | No existe |
| Hosting, dominio, backups en la nube, monitorización | No existe |
| Onboarding y periodo de prueba | No existe |

Ninguno es imposible. Es que **son diez**, y el primero (auth) obliga a tocar 112 rutas repartidas
en un archivo de 5.000 líneas. Por eso la refactorización de `main.py` en routers deja de ser
"limpieza" y pasa a ser **prerrequisito de negocio**.

Sé honesto contigo mismo con la aritmética del SaaS: a 15 USD/mes necesitas ~70 clientes pagando
para llegar a 1.000 USD/mes, y con soporte por WhatsApp incluido. En Venezuela conseguir 70
empresas de reformas que paguen en dólares todos los meses es alcanzable, pero es **un trabajo
comercial de un año**, no un efecto secundario de tener buen software.

### 4.7 Riesgo que nadie te va a decir

Sigues llamando **"Autogenerar con IA"** a un matcher por palabras clave (`index.html:12`,
`form.html:648`). Internamente lo documentaste con honestidad. De cara al cliente sigue siendo un
reclamo que no se sostiene: el primer cliente técnico que lo pruebe con una frase que tu catálogo
no cubre verá que no hay ninguna IA, y eso contamina la credibilidad de todo lo demás —
que sí es real y sí es bueno.

**Recomendación:** renómbralo a **"Autogenerar desde tu catálogo"** o "Generador rápido". Pierdes
una palabra de marketing y ganas algo que vale mucho más: que todo lo que prometes sea cierto. Si
más adelante quieres IA de verdad, añádela como función opcional que requiere conexión, y entonces
sí llámala IA.

### 4.8 Veredicto final

> **Como software: 8/10.** Maduro, bien pensado, con decisiones de ingeniería correctas donde
> importa, y con un PDF de nivel comercial indiscutible. Está muy por encima de un proyecto
> personal.
>
> **Como producto vendible hoy: 5/10.** Le falta todo lo que rodea al software: identidad de marca
> propia (no RemodelaT), licenciamiento, onboarding, email, soporte y una forma de cobrar.
>
> **Como negocio SaaS hoy: 2/10.** No por calidad, sino porque le faltan los cimientos de
> multiusuario que un SaaS exige.
>
> **Camino recomendado:** cobra por licencia de escritorio en 3 semanas, consigue 10–20 clientes
> reales que paguen, aprende de ellos durante 3 meses, y **solo entonces** decide si construyes el
> SaaS. Que la mensualidad la financien clientes, no tu fe.

---

## 5. Ideas: qué añadir, en orden de retorno

### Bloque 0 — Antes de vender nada (2–3 semanas)

| # | Idea | Esfuerzo | Por qué |
|---|---|---|---|
| 1 | **Asistente de primer arranque** + borrar datos de RemodelaT de los defaults | 0,5 d | Hoy tu cliente ve tu teléfono. Bloqueante absoluto. |
| 2 | **Envío por email (SMTP)** del presupuesto en PDF con plantilla | 1–2 d | Carencia funcional #1. WhatsApp no sirve para clientes corporativos. |
| 3 | **Activación por clave de licencia** | 2–3 d | Sin esto no hay venta, hay regalo. |
| 4 | **Embeber la fuente Inter** como ya haces con Lato | 1 h | Elimina la única dependencia de internet que queda. |
| 5 | **LICENSE + EULA** | 0,5 d | Legal. |
| 6 | **Manual PDF + vídeo de 5 min** | 2 d | Reduce el soporte a la mitad desde el día 1. |
| 7 | **GitHub Actions** ejecutando los 58 tests en cada push | 2 h | Ya tienes los tests; solo falta que corran solos. |

### Bloque 1 — Lo que hará que te paguen más (1–2 meses)

| # | Idea | Por qué vende |
|---|---|---|
| 8 | **Aceptación online del presupuesto**: enlace único → el cliente ve el PDF, firma en el móvil y queda aceptado, con notificación al instante | Es *la* función que la competencia usa como gancho. Convierte el presupuesto en un cierre de venta. Ya tienes firma digital y PDF interactivo: falta el enlace público. |
| 9 | **Catálogo de partidas real y grande para Venezuela** (300–500 partidas con precios de referencia actualizables) | Hoy siembras 59 partidas, 3 productos y 0 recursos. La competencia presume de 3.650–4.244. **El catálogo es el producto**: es lo que hace que el cliente pueda presupuestar el primer día en lugar de pasar dos semanas cargando datos. Esta es, con diferencia, la idea de mayor retorno de toda la lista. |
| 10 | **Actualización de precios por lote con índice** (inflación, tasa BCV) con un clic y con histórico | En Venezuela los precios se mueven cada semana. Que la app reajuste todo el catálogo con un porcentaje o con la tasa del día es dolor puro resuelto. Ya tienes `/partidas/ajustar` y `/recursos/bulk-ajustar`: falta el histórico y la automatización. |
| 11 | **Modo obra en el móvil**: la web ya es responsive (16 media queries) — falta un PWA instalable con caché offline para tomar medidas en sitio | Todos tus competidores venden "desde el móvil en la visita". Estás a poco de tenerlo. |
| 12 | **Comparador visual de versiones** ya existe: añade **"qué cambió y cuánto cuesta el cambio"** enviable al cliente | Los cambios de alcance son donde las reformas pierden dinero. |
| 13 | **Certificaciones de obra** (avance mensual %, certificación parcial y acumulada → factura) | Es lo que separa "presupuestador" de "gestor de obra" y justifica una mensualidad. Tienes proyectos, pagos y facturas: falta el eslabón. |
| 14 | **Rentabilidad real por obra**: coste presupuestado vs. coste incurrido (facturas de proveedor, jornales) | Convierte la herramienta en algo que se usa **todos los días**, no solo al presupuestar. La retención de un SaaS depende de esto. |
| 15 | **Plantillas de presupuesto por tipo de obra** ampliando los 6 packs de estancia a "reforma integral de apartamento", "local comercial", "obra nueva unifamiliar" | Multiplica la utilidad de lo que ya construiste en la Fase 12. |

### Bloque 2 — Preparar el SaaS (2–4 meses, solo si el Bloque 0 vendió)

| # | Idea |
|---|---|
| 16 | **Trocear `main.py`** en `routers/` por dominio (presupuestos, catálogos, proyectos, facturas, config). Prerrequisito de todo lo demás. |
| 17 | **Auth + usuarios + roles** (admin / presupuestador / solo lectura) con sesiones seguras y CSRF. |
| 18 | **Multi-tenant**: `empresa_id` en todos los modelos + filtrado obligatorio a nivel de sesión de BD (no confiar en que cada query lo recuerde). |
| 19 | **PostgreSQL** como backend alternativo manteniendo SQLite para la versión escritorio. |
| 20 | **Log de auditoría**: quién cambió qué precio y cuándo. En una empresa con varios presupuestadores esto se vuelve obligatorio. |
| 21 | **Pasarela de pago** + prueba de 14 días + facturación de la propia suscripción. |
| 22 | **Sustituir los 17 `except: pass` por logging real** y añadir una página de diagnóstico. Cuando tengas 50 clientes, esto es la diferencia entre resolver una incidencia en 10 minutos o en 3 días. |
| 23 | **Telemetría mínima anónima y opt-in** (qué funciones se usan). Sin esto vas a construir a ciegas. |

### Bloque 3 — Diferenciación a futuro

| # | Idea |
|---|---|
| 24 | **IA de verdad, bien etiquetada y opcional**: convertir una descripción libre o unas notas de voz en partidas, usando tu catálogo como restricción para que nunca invente precios. Como función online opcional, con el modo offline intacto. |
| 25 | **OCR de facturas de proveedor** para alimentar el coste real de la obra. |
| 26 | **Portal del cliente**: el propietario entra y ve avance, fotos, pagos y cambios aprobados. Es un argumento de venta gigante para el reformista frente a su cliente final. |
| 27 | **Importación/exportación BC3 (FIEBDC-3)** si algún día miras a España. Es el pasaporte del sector allí. |
| 28 | **Marketplace de catálogos**: vender/compartir catálogos por especialidad (plomería, electricidad, carpintería). Ingreso recurrente sin desarrollo continuo. |

---

## 6. Los cinco puntos que resumen todo

1. **El software es bueno de verdad.** 12 fases completadas, 58 tests en verde, motor de cálculo con
   `Decimal`, migraciones que no pierden datos, validación de ficheros con criterio de seguridad. No
   es un prototipo.
2. **El PDF es tu mejor vendedor.** Verificado visualmente: mediciones desglosadas, capítulos con
   subtotales, anexo de garantías. Nivel comercial pleno.
3. **Tu foso es Venezuela, no las features.** Número de control, retenciones, tasa BCV, cláusula
   cambiaria, vocabulario local y funcionamiento offline. Ninguno de los grandes te va a disputar
   ese terreno.
4. **Hoy puedes vender licencias, no suscripciones.** Faltan auth, multi-tenant, pago y email. La
   licencia de escritorio está a 2–3 semanas; el SaaS a 2–4 meses.
5. **Antes de programar más, cobra.** Pídeles el dinero a esas personas que dijeron que pagarían.
   Su respuesta vale más que cualquier análisis, incluido este.

---

## 7. Detalles concretos para arreglar esta semana

```
app/models.py:1057-1061   → datos de RemodelaT como defaults de configuración
app/templates/base.html   → <link> a Google Fonts (Inter): embeberla como Lato
app/templates/index.html:12         → "Autogenerar con IA"  → "Autogenerar desde tu catálogo"
app/templates/budgets/form.html:648 → ídem
run.py                    → 0.0.0.0:8000 sin protección; usar 127.0.0.1 por defecto
(raíz)                    → falta LICENSE
app/main.py               → 17 bloques `except Exception: pass` sin logging
```

---

---

## 8. ¿Nicho de construcción o abrir a más mercados?

**Recomendación: quedarte en construcción y remodelación. Profundizar, no ensanchar.**
Pero "no ensanchar" no significa "no crecer": hay tres formas de crecer y solo una es mala.

### 8.1 El argumento decisivo: mide cuánto de tu código NO es generalizable

| Módulo | Líneas | ¿Sirve fuera de construcción? |
|---|---:|---|
| `seeds.py` (catálogo + vocabulario VE) | 991 | **No** |
| `importer.py` (descompuestos CYPE) | 812 | **No** |
| `tiempos.py` (rendimientos por m², ml, ud, jornada) | 598 | **No** |
| `recursos.py` + `DescomposicionPartida/Fila` | 351 | **No** |
| `garantias.py` (13 familias de obra con plazos 2/3/5 años) | 288 | **No** |
| Modelo `Medicion` (largo × ancho × alto) | — | **No** |
| `RecetaEstancia` (packs de cocina, baño, salón) | — | **No** |
| `Proyecto` / `CambioAlcance` / `Pago` | — | **No** |

**Más de 3.000 líneas — el corazón del producto — solo tienen sentido en obra.**

Eso es la respuesta entera. Lo que hace que tu PDF impresione (mediciones desglosadas, capítulos
con subtotal, garantías por familia, descompuestos) es **exactamente lo que no se puede
generalizar**. Si haces la herramienta genérica, tienes que esconder o desactivar todo eso, y lo
que queda es un generador de facturas más — compitiendo con Holded, Alegra, STEL Order o Zoho, que
tienen equipos de 50 personas y años de ventaja. Pasarías de ser el mejor en un sitio pequeño a ser
el peor en un sitio enorme.

### 8.2 Las tres direcciones de crecimiento, ordenadas por retorno

**① Profundidad — mismo cliente, más de su trabajo. (Empieza aquí)**
Certificaciones de avance, rentabilidad real por obra, portal del cliente, compras a proveedores.
Cero riesgo de mercado: ya sabes quién es el cliente y ya te compró. Cada función nueva sube el
precio que puedes cobrar y baja la probabilidad de que se vaya. **Es lo que justifica una
mensualidad**, porque convierte la app en algo que se abre todos los días y no solo al presupuestar.

**② Gremios adyacentes — misma obra, otra especialidad. (Casi gratis)**
Electricistas, plomeros, instaladores de aire acondicionado, carpinteros, herreros,
impermeabilizadores, pintores. **No requieren cambiar el software: requieren un catálogo semilla
distinto.** Tu propia BD ya lo insinúa — de 59 partidas tienes 9 de Electricidad, 7 de Baños,
4 de Plomería, 2 de Pintura, 2 de Carpintería.

Un instalador de aire acondicionado necesita mediciones, partidas, descompuestos, garantía por
familia y un PDF serio: **es tu producto tal cual, con otras 80 partidas sembradas**. Multiplicas
mercado sin multiplicar código. Es la expansión más barata que existe y deberías hacerla en cuanto
tengas los primeros clientes.

**③ Otros países de LatAm — mismo dolor, otra fiscalidad. (El crecimiento de verdad)**
Y aquí está lo bueno: **ya construiste la arquitectura para esto sin darte cuenta.** El bloque
fiscal venezolano está detrás de un flag (`activar_funciones_venezuela`), `Cliente` tiene campo
`pais`, y la configuración de IVA, retenciones, moneda y tasa de cambio es editable. Es decir: ya
tienes el patrón de "módulo por país", solo hay un módulo escrito.

Colombia, Ecuador, Perú, Panamá, República Dominicana, Bolivia y Argentina comparten tu dolor
exacto: economía dolarizada o con inflación, precios que se mueven, vocabulario propio, y ninguna
herramienta local decente. Coste por país: reglas fiscales + vocabulario + precios de referencia.
Semanas, no meses. **Este es el eje que puede llevarte de 20 clientes a 500.**

**④ Multisector genérico (dentistas, imprentas, eventos, agencias). No lo hagas.**
Tirarías tu foso a la basura para entrar en el mercado más saturado y peor pagado del software de
gestión.

### 8.3 El matiz que evita el error contrario

Si mañana un fotógrafo, un carpintero de muebles o un organizador de eventos te dice "esto me
sirve, ¿me lo vendes?" — **véndeselo**. La herramienta ya funciona para cualquiera que cobre por
capítulos y partidas; que apague las mediciones y listo.

La regla es: **acepta al cliente, no construyas el mercado.** Cobrar una licencia a alguien de otro
sector cuesta cero. Añadir funciones para su sector cuesta tu producto entero.

### 8.4 Y una consecuencia práctica: la marca

Si el plan a dos años es LatAm, la marca no puede ser ni "RemodelaT" (es tu constructora, no tu
software) ni algo atado a Venezuela. Necesita un nombre propio, neutro y regional. Es una decisión
de 200 USD hoy y de miles mañana, y conviene tomarla **antes** de vender la primera licencia y
mandar a imprimir el manual.

### 8.5 Resumen

> **No amplíes a más sectores. Amplía a más gremios y a más países dentro del mismo sector.**
>
> Secuencia recomendada:
> - **Meses 0–3** — vende licencias a reformistas en Venezuela. Profundidad (§5 Bloque 1).
> - **Meses 3–6** — catálogos semilla por gremio (electricidad, plomería, A/C, carpintería). Mismo
>   software, cuatro mercados.
> - **Meses 6–12** — segundo país. Empieza por uno dolarizado (Ecuador o Panamá): tu módulo de
>   moneda ya está resuelto y te ahorras la mitad del trabajo fiscal.
> - **Nunca** — el generador de presupuestos universal.

---

*Análisis realizado sobre el commit `74d4822` de la rama `arena/019ff8ba-presupuestos`.*
