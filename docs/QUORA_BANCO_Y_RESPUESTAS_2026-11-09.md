# Banco de preguntas y respuestas para Quora — 2026-11-09

Material operativo que acompaña a `docs/ESTRATEGIA_QUORA_2026-11-09.md`.

Contenido de este archivo:

1. **§1 — 20 preguntas candidatas**, con tipo (responder a un hilo existente /
   pregunta propia), mercado, URL de destino y el ángulo de la respuesta.
2. **§2 — 3 respuestas listas para publicar** (texto completo, solo hay que
   sustituir los datos marcados y verificar el enlace).
3. **§3 — 1 pregunta propia modelo** con su respuesta completa (la versión
   legítima de "preguntar y publicitar").
4. **§4 — Checklist de publicación** (10 puntos, 30 segundos).
5. **§5 — Plantilla de registro semanal.**

---

## 0. Dos convenciones antes de empezar

**Tipo.** `R` = responder a una pregunta que **ya existe** en Quora (siempre
preferencia). `P` = pregunta propia (solo si cumple las cinco condiciones de
§5 de la estrategia).

**Cifras.** Ninguna respuesta se publica con un número inventado. Los huecos
se marcan así:

```
[[DATO: precio unitario real del catálogo para chapter demo en VE]]
```

y se sustituyen por el dato que exista en el catálogo del mercado
(`basedatos_partidas/`, `app/services/precios_publicos.py`) o por una fuente
citada. Si el dato no existe, la frase se escribe sin cifra ("va en el orden
de…") o no se publica. Una cifra inventada en un hilo público es el tipo de
error que un contratista detecta en dos minutos y no perdona.

---

## 1. Las 20 candidatas

Ordenadas por prioridad de filtro: primero las que tienen más probabilidad de
tener hilo con tráfico en Google, después las de intención de mercado.

| # | Pregunta (con palabras de cliente) | Tipo | Mercado | URL de destino | Ángulo de la respuesta |
| --- | --- | --- | --- | --- | --- |
| 1 | ¿Cuánto cuesta remodelar un baño en Venezuela? | R | VE | `/ve/guia/presupuesto-usd-bs-venezuela` | Rango por m² + qué partidas mueven el precio (demolición vs. directazo) |
| 2 | ¿Cuánto cuesta un pañete por metro cuadrado en Colombia? | R | CO | `/co/guia/apu-panete-colombia` | Cálculo del APU paso a paso, no solo el precio final |
| 3 | ¿Vale la pena un software de presupuestos o sigo con Excel? | R | multi | `/precios-comparados` | Comparación honesta: qué sigue siendo mejor en Excel |
| 4 | ¿Cómo hago un presupuesto de obra en Perú? | R | PE | `/pe/guia/metrados-peru` | Metrados + APU + IGV separado del comprobante |
| 5 | ¿Cuánto cobra un maestro de obra por metro cuadrado en México? | R | MX | `/mx/guia/cotizar-remodelacion-mexico` | Precio de mercado vs. precio de venta: el margen va en la cotización |
| 6 | ¿Cómo se cotiza en dólares en Ecuador? | R | EC | `/ec/guia/apu-dolares-ecuador` | Dólares nativos + RUC + IVA 15 % |
| 7 | ¿Qué es un análisis de precios unitarios (APU)? | R | genérico | `/guia/analisis-precios-unitarios` | Explicar el método con un ejemplo numérico simple |
| 8 | ¿Cómo presento un presupuesto para que el cliente no lo rechace? | R | genérico | `/guia/presupuesto-de-obra` | Estructura del documento: capítulos, mediciones, totales, validez |
| 9 | ¿Cuánto margen de ganancia se pone a una obra? | R | multi | `/precios-comparados` | Rangos por tipo de obra y por tamaño de empresa |
| 10 | ¿Cómo cotizo una obra en billones cuando cambia la tasa cada día? | R | VE | `/ve/guia/presupuesto-usd-bs-venezuela` | Tasa congelada en el presupuesto y fecha de vencimiento |
| 11 | ¿Conviene dar anticipo a una obra? ¿Cuánto? | R | multi | `/como-funciona` | Porcentajes habituales y cómo quedan por escrito en el PDF |
| 12 | ¿Cómo mido las cantidades de una obra sin metrar a ojo? | R | genérico | `/pe/guia/metrados-peru` (o `/calculadora`) | Sistema de mediciones por zonas y sumas automáticas |
| 13 | ¿Por qué mi Excel de presupuestos se rompe cuando meto muchas partidas? | R | genérico | `/guia/analisis-precios-unitarios` | Causas reales: referencias cruzadas, filas variables, copiado |
| 14 | ¿Qué incluye el precio unitario de un item? | R | genérico | `/guia/analisis-precios-unitarios` | Material + mano de obra + maquinaria + gastos + utilidad |
| 15 | ¿Se puede cotizar una obra sin visitar el sitio? | R | multi | `/como-funciona` | Qué sí y qué no; qué datos pedir por foto para cotizar a distancia |
| 16 | ¿Qué es mejor: un presupuesto en spreadsheet o uno con capítulos? | R | multi | `/guia/presupuesto-de-obra` | Cuándo cada formato gana (obra grande vs. reforma) |
| 17 | ¿Cuánto cobra un maestro de obra por hora en Venezuela? | R | VE | `/ve/guia/presupuesto-usd-bs-venezuela` | Tarifa por hora + carga social; el clásico error de olvidar la carga |
| 18 | ¿Cómo calculo el consumo de materiales en un presupuesto? | R | genérico | `/calculadora` | Rendimientos por m² y desperdicio por partida |
| 19 | ¿Vale la pena pedirle al cliente un 50 % de anticipo? | R | multi | `/como-funciona` | Cómo se documenta y qué se hace si no se paga |
| 20 | ¿Cuánto cuesta una obra por metro cuadrado en Venezuela? | **P** | VE | `/ve/guia/presupuesto-usd-bs-venezuela` | Pregunta propia modelo (§3): rango real por tipo de obra |

**Cómo se usa la tabla.** Las 19 primeras son candidatas a **hilo existente**:
antes de escribir, se busca el texto en Google. Si el hilo de Quora aparece en
el top 5, se responde; si no aparece y el hilo tiene menos de 1.000 visitas,
se pasa a la siguiente. La nº 20 es la única pregunta propia, y va la última
a propósito: primero se responde, luego se pregunta.

---

## 2. Tres respuestas listas para publicar

### 2.1 Respuesta A — para el hilo «¿Cuánto cuesta remodelar un baño en Venezuela?»

> **Texto para pegar (sin el bloque de código):**
>
> Si te dan un precio cerrado sin haber visto el sitio, ese precio es una
> estimación, no un presupuesto. En Venezuela hay además una variable que no
> existe en otros países: la tasa se mueve entre que mides y entre que cobran.
>
> El orden de magnitud, para un baño completo de unos 4-5 m², con acabados
> medios (piso, revestimiento, pintura, muebles existentes que se reutilizan y
> una lámpara), es de [[DATO: rango VE de baño completo en USD por m²]]
> en dólares, con la mano de obra puesta por fuera y los materiales por
> dentro. Ese número cambia mucho según dos cosas:
>
> **1. Si hay que tocar la instalación o no.** Un baño "de directazo" (piso,
> revestimiento, pintura) es una obra de acabados. Un baño con cambio de
> tuberías, demolición del piso y nueva impermeabilización multiplica el
> presupuesto, y no por el material sino por la demolición y el tiempo de
> obra: ese suele ser el 60-70 % del costo cuando hay que romper.
>
> **2. El desorden de la tasa.** Si el presupuesto se firma en bolívares y el
> pago cae tres semanas después, ese presupuesto ya no vale lo mismo. La
> forma sana de trabajar esto es cotizar en dólares y congelar la tasa de
> referencia del día de la cotización, con fecha de vencimiento explícita.
> En nuestra guía de presupuesto en USD y bolívares está el procedimiento
> paso a paso ([guía de presupuesto USD/Bs para Venezuela](https://cotizat.online/ve/guia/presupuesto-usd-bs-venezuela?utm_source=quora&utm_medium=referral&utm_campaign=comunidad&utm_content=remodelacion-bano-ve)).
>
> Un último detalle que casi nadie pone por escrito y que luego genera
> discusiones: **qué queda incluido y qué no**. Retiro de la demolición, retiro de
> escombros, compra de materiales en tienda versus precios de maestro,
> pintura de dos manos, cambio de instalación eléctrica. Si eso no está
> escrito en el documento, cualquier diferencia de 15-20 % entre lo que dijo
> el maestro y lo que dice el presupuesto es un problema de palabras, no de
> números.
>
> Para que quede claro: trabajo en CotizaT, que desarrolla el software donde
> hacemos estos presupuestos, y por eso el enlace de arriba va a nuestra
> guía.

**Preparación antes de publicar:** sustituir el `[[DATO: …]]` por el rango real
del catálogo VE (capítulo de demo y baños) o por un rango citado de fuentes
públicas del mercado; comprobar que la URL responde 200; verificar que el
texto del enlace es el que se ve.

---

### 2.2 Respuesta B — para el hilo «¿Cuánto cuesta un pañete por metro cuadrado en Colombia?»

> Un pañete no tiene un precio: tiene un **precio unitario que depende de la
> altura, del material y de quién lo aplica**. Por eso el número que circula
> de boca en boca ("un pañete está como a X") es el menos útil de todos.
>
> El cálculo real es un APU, y son cuatro sumandos:
>
> 1. **Material.** Cemento o mortero, arena, agua y, si es pañete con aditivo
>    o hidrófugo, el aditivo. El consumo típico está entre 0,35 y 0,45 kg de
>    mezcla seca por m² según el espesor; con 1 cm de espesor, ese es el orden
>    de magnitud que se repite en obra.
> 2. **Mano de obra.** Depende de si el maestro trabaja solo o con ayudante, y
>    de si el precio que se pacta es por m² o por día. Este es el ítem que más
>    se olvida cuando se arma el presupuesto "a ojo".
> 3. **Maquinaria y herramientas.** Mixer, nivel, andamio, transporte.
> 4. **Gastos indirectos y utilidad.** Bodega, administración, transporte y
>   utilidad. Ahí es donde se decide el margen real de la obra, no en el
>    precio del material.
>
> Un ejemplo para que se vea el orden de magnitud (no es una cotización):
> para 20 m² de pañete a 1 cm, con mezcla estándar, el material pesa del orden
> de [[DATO: kg de mezcla por m² y precio del saco en CO]] y la mano de obra
> de [[DATO: precio de maestro por m² en CO]]; el total no baja de
> [[DATO: total APU pañete por m² en CO]] por m² en pesos colombianos.
>
> El detalle que hace que el APU no se rompa al tres meses es guardar
> **las unidades y la fuente de cada insumo** (no solo el precio), y que las
> fórmulas sean referencias y no valores pegados: así, cuando el cemento sube
> 8 %, se actualiza el APU y no el presupuesto entero. Está desarrollado paso a
> paso, con las fórmulas, en nuestra [guía de APU de pañete en
> Colombia](https://cotizat.online/co/guia/apu-panete-colombia?utm_source=quora&utm_medium=referral&utm_campaign=comunidad&utm_content=apu-panete-co).
>
> Si el pañete es exterior o va sobre mampostería nueva, cambia el punto de
> partida: hay que hablar de mortero de pega o de pañete de fachada, no del
> mismo producto.
>
> Para que quede claro: trabajo en CotizaT, que desarrolla el software donde
> hacemos estos presupuestos, y por eso el enlace de arriba va a nuestra guía.

**Preparación antes de publicar:** sustituir los tres `[[DATO: …]]` por el
precio real del saco de mezcla en Colombia y por el precio de mano de obra
vigente en el mercado objetivo; si son datos propios del catálogo, mantener el
"no es una cotización".

---

### 2.3 Respuesta C — para el hilo «¿Vale la pena un software de presupuestos o sigo con Excel?»

> Depende del tamaño de la obra y de la cantidad de presupuestos al mes. No es
> una respuesta publicitaria, así que va con las dos partes.
>
> **Excel sigue siendo mejor que cualquier software cuando:**
>
> - Haces dos o tres presupuestos al mes, todos de un mismo tipo de obra.
> - No necesitas dar el presupuesto al cliente en un formato presentable (lo
>   entregas en PDF hecho a mano o con una plantilla que ya tienes).
> - No hay cambios de alcance: la obra se resuelve en un viaje y se cobra.
>
> En ese caso, un software no te ahorra tiempo: te cuesta.
>
> **Un software empieza a pagar cuando aparece una de estas cosas:**
>
> - **El catálogo se repite.** Si las mismas 60 partidas aparecen en cada obra,
>   estás reescribiendo el mismo precio unitario cada vez. Ahí el valor está
>   en el catálogo, no en el editor.
> - **Hay capítulos y subcapítulos.** Una obra de 15 capítulos con 200 partidas
>   en Excel termina en una hoja con celdas combinadas, referencias rotas y
>   subtotales que alguien corrige a mano antes de enviarlo.
> - **Cambian los alcances durante la obra.** Cuando hay adiciones y faltantes,
>   lo que importa es poder emitir un presupuesto ajustado con los mismos datos
>   base, no rehacer el archivo desde cero.
> - **Hay que entregar un documento presentable** con capítulos, mediciones,
>   IVA y total, y que el cliente lo pueda leer sin que el autor explique nada.
> - **La cotización va en una moneda que se mueve** y hace falta congelar la
>   tasa de referencia con fecha.
>
> Un matiz importante: el software no sustituye al criterio de presupuesto. La
> estructura del presupuesto (capítulos, precios unitarios, mediciones) es la
> misma de siempre; lo que cambia es que el catálogo se reutiliza, los
> subtotales se calculan solos y el documento sale con la firma del cliente y
> el total al pie. En nuestra [comparativa de precios](https://cotizat.online/precios-comparados?utm_source=quora&utm_medium=referral&utm_campaign=comunidad&utm_content=excel-vs-software)
> está el detalle de qué incluye cada opción.
>
> Mi resumen: si haces una obra al mes, Excel. Si haces obras con capítulos y
> entregas presupuesto tras presupuesto, el ahorro de horas aparece en la
> tercera.
>
> Para que quede claro: trabajo en CotizaT, que desarrolla el software donde
> hacemos estos presupuestos, y por eso el enlace de arriba va a nuestra
> comparativa.

**Preparación antes de publicar:** comprobar que `/precios-comparados` responde
200 y que la tabla de la comparativa sigue al día (si no, actualizarla antes de
publicar la respuesta).

---

## 3. Pregunta propia modelo + su respuesta

Esta es la versión legítima de "preguntar y publicitar": **la pregunta es
real, la respuesta resuelve, la marca aparece una vez y el enlace va en medio**.

### 3.1 La pregunta (texto exacto)

> **¿Cuánto cuesta una obra por metro cuadrado en Venezuela?**

Requisitos que cumple: la formulan los clientes con esas palabras; no
contiene marca ni nombres de competidores; tiene intención de mercado (VE);
y la respuesta puede apoyarse en datos reales del catálogo.

### 3.2 La respuesta completa

> La respuesta corta es "depende de qué obra", y la larga es la que sigue.
> Cualquier cifra sin esas cuatro variables — tipo de obra, terminación, ciudad
> y qué incluye el precio — es un número de pasillo.
>
> **1. Por tipo de obra (orden de magnitud, en dólares por m²):**
>
> - Obra nueva, terminación básica: [[DATO: rango VE obra nueva básica USD/m²]]
> - Obra nueva, terminación media: [[DATO: rango VE obra nueva media USD/m²]]
> - Remodelación de vivienda: [[DATO: rango VE remodelación USD/m²]]
> - Remodelación de local comercial: [[DATO: rango VE local comercial USD/m²]]
> - Obra con localización premium (pisos especiales, carpintería a medida,
>   exteriores cuidada): [[DATO: rango VE premium USD/m²]]
>
> **2. Qué mueve el precio dentro de cada rango:**
>
> - **La terminación**, sobre todo el flooring y la pintura: cambiar el tipo de
>   piso puede mover la obra entre un 15 % y un 25 %.
> - **La estructura**: si hay que demoler, hacer muro de carga o modificar
>   instalaciones, el costo estructural domina todo lo demás.
> - **La altura y los acabados**: en una vivienda de 3 pisos, la mano de obra
>   de acabados sube por andamio y por traslados.
> - **La ciudad**: no por el mismo trabajo, sino por el precio del material y
>   del maestro, que no es el mismo en Maracaibo que en Caracas.
>
> **3. Qué se incluye en el precio (esto es lo que más se olvida):**
>
> Un precio "por m²" puede incluir o no: material, mano de obra, indirectos
> (bodega, administración, transporte), utilidad, alquiler de equipos, limpieza
> final y retiro de escombros. Un precio que no dice si incluye materiales no
> se puede comparar con otro. Cuando comparen dos presupuestos, lo primero
> que hay que preguntar es eso, no el número final.
>
> **4. El detalle local: la tasa.**
>
> Cotizar en bolívares y cobrar semanas después obliga a hablar de una tasa
> de referencia con fecha de congelación. La guía completa del procedimiento,
> con la tasa, los pasos y cómo presentarlo para que el cliente lo entienda,
> está en [presupuesto en USD y bolívares para
> Venezuela](https://cotizat.online/ve/guia/presupuesto-usd-bs-venezuela?utm_source=quora&utm_medium=referral&utm_campaign=comunidad&utm_content=cuanto-cuesta-m2-ve).
>
> Si la respuesta debe quedar en una línea: en Venezuela, una obra nueva de
> terminación media anda por el orden de [[DATO: media ponderada USD/m²]] por
> m², y una remodelación de vivienda se queda unos [[DATO: media
> remodelación USD/m²]] por m²; la tercera parte de ese número es
> terminación, la cuarta estructura y el resto es margen.
>
> Para que quede claro: trabajo en CotizaT, que desarrolla el software donde
> hacemos estos presupuestos, y por eso el enlace de arriba va a nuestra guía.

**Preparación antes de publicar:** sustituir **todos** los `[[DATO: …]]` por
cifras del catálogo VE o por rangos de fuentes públicas citadas. Si al final
quedan huecos, la respuesta **no se publica**: una respuesta con huecos es
peor que no tener respuesta, porque se nota.

### 3.3 Qué hacer con el hilo después

- Responder a los comentarios con datos y sin defender el producto a ultranza.
- Actualizar la respuesta si cambia el catálogo (añadir fecha de revisión).
- No pedir votos. Los upvotes se ganan respondiendo bien a otras preguntas.
- Publicar **una** versión (en español). No clonar en cinco idiomas.

---

## 4. Checklist de publicación (30 segundos)

- [ ] ¿Es una pregunta **real** (la haría un cliente) y **sin marca**?
- [ ] ¿La respuesta **se entiende entera** sin hacer clic?
- [ ] ¿Hay **un solo enlace**, y **no está en la primera ni en la última frase**?
- [ ] ¿El texto del enlace **describe** el destino (no "haz clic aquí")?
- [ ] ¿El destino es una URL **indexable** del **mercado** del lector?
- [ ] ¿Lleva **UTM** (`utm_source=quora&utm_medium=referral&utm_campaign=comunidad&utm_content=…`)?
- [ ] ¿He **sustituido todos** los `[[DATO: …]]` por cifras reales o fuentes citadas?
- [ ] ¿He **declarado la afiliación** ("trabajo en CotizaT…")?
- [ ] ¿He **respondido a la pregunta concreta**, sin convertir la respuesta en un anuncio de lo que vendo?
- [ ] ¿Es **texto propio**, no copiado del artículo del sitio (el hilo es la
      versión social, el artículo es la canónica)?

Si falla uno, no se publica.

---

## 5. Plantilla de registro semanal

Una fila por respuesta publicada. Es una tabla (Google Sheets o similar); no
hace falta más.

| fecha | url_hilo | mercado | tipo | url_destino | vistas_7d | vistas_30d | upvotes | clics | registros | notas |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-11-16 | https://quora.com/... | VE | R | /ve/guia/presupuesto-usd-bs-venezuela | | | | | | |
| | | | | | | | | | | |

Columnas derivadas: `vistas_30d / semanas` = ritmo. Si una respuesta sigue
subiendo a los 90 días, se **actualiza** (añadir un dato nuevo), no se
sustituye.

**Revisión mensual (15 minutos):**

1. ¿Cuáles dos respuestas trajeron más clics? → se actualizan.
2. ¿Alguna fue colapsada o eliminada? → se anota el motivo y se corrige el
   patrón, no la respuesta aislada.
3. ¿Los clics van a URLs indexables? (comprobar con `app.seo.es_indexable`)
4. ¿Cuántos registros trae el canal en total? (GA4 → Adquisición → Referrals →
   quora.com, y el panel de altas)

---

## 6. Documentos relacionados

- `docs/ESTRATEGIA_QUORA_2026-11-09.md` — la estrategia, el porqué y el piloto
  de 90 días.
- `docs/HOJA_DE_RUTA_SEO.md` — contenidos por país y ritmo general.
- `app/seo.py` — `es_indexable()`: la función que decide si una URL puede
  enlazarse desde fuera.
