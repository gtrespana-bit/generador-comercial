# Banco de preguntas y respuestas para Quora — 2026-11-09 (inglés primero)

Material operativo que acompaña a `docs/ESTRATEGIA_QUORA_2026-11-09.md`.

1. **§1 — 20 preguntas candidatas**: tipo (responder a un hilo existente /
   pregunta propia), idioma, mercado, URL de destino y ángulo de la respuesta.
2. **§2 — 6 respuestas listas para publicar** (3 en inglés, 3 en español), con
   las cifras reales de la biblioteca de precios del repo.
3. **§3 — 1 pregunta propia modelo** (en inglés) con su respuesta completa.
4. **§4 — Checklist de publicación** (10 puntos, 30 segundos).
5. **§5 — Plantilla de registro semanal.**

---

## 0. Tres convenciones antes de empezar

**Tipo.** `R` = responder a una pregunta que **ya existe** en Quora (siempre
preferencia). `P` = pregunta propia (solo si cumple las cinco condiciones de
§5 de la estrategia).

**Idioma y mercado.** El hilo manda: si el hilo está en inglés, la respuesta
es en inglés y el enlace apunta al mercado anglófono (`/en-us/…`, `/en-gb/…`,
`/en-au/…`, `/en-ie/…`); si está en español, al mercado hispano (`/mx/…`,
`/co/…`). **Nunca** se responde en un idioma a un hilo del otro, y nunca se
enlaza a un mercado distinto del que pregunta.

**Cifras.** Las cifras de este documento salen de la biblioteca de precios del
propio repositorio (`basedatos_partidas/salida/precios_recursos_*.csv` y los
artículos de `app/seo_articulos_mercados_en.py` / `app/seo_reino_unido.py`),
con su fuente y fecha. **Los precios envejecen**: antes de publicar hay que
comprobar que la fecha sigue siendo reciente y, si hace falta,actualizarlos.
Lo que no exista en la biblioteca va marcado así:

```
[[DATO: precio unitario real del catálogo del mercado]]
```

y se sustituye por el dato de `basedatos_partidas/` o por una fuente citada.
Si el dato no existe, la frase se escribe sin cifra ("va en el orden de…") o
no se publica. Una cifra inventada en un hilo público es el tipo de error que
un contratista detecta en dos minutos y no perdona.

---

## 1. Las 20 candidatas

Ordenadas por prioridad de filtro: primero las que tienen más probabilidad de
tener hilo con tráfico en Google, después las de intención de mercado.

### 1.1 Nivel A — inglés (prioridad, 60 % del tiempo)

| # | Pregunta (con palabras de cliente) | Tipo | Mercado | URL de destino | Ángulo de la respuesta |
| --- | --- | --- | --- | --- | --- |
| 1 | How much does it cost to remodel a bathroom? | R | US | `/en-us/guia/construction-labor-cost-per-hour` | Wage vs. employer cost por hora; por qué dos empresas del mismo pueblo cotizan 4.000 $ de diferencia |
| 2 | What hourly rate should I charge as a tradie? | R | AU | `/en-au/guia/tradie-hourly-rates-australia` | Award rate vs. employer cost; super, workers comp y las 1.600/1.980 horas |
| 3 | How do I handle CIS deductions on my construction invoices? | R | GB | `/en-gb/guia/cis-deduction-subcontractors` | 20 % / 30 % / gross, y que la base es la mano de obra, no la factura |
| 4 | When do I apply the VAT domestic reverse charge on construction? | R | GB | `/en-gb/guia/vat-domestic-reverse-charge-construction` | Desde el 01/03/2021, B2B reportado bajo CIS; la nota que debe ir en la factura |
| 5 | What should a construction estimate include so the client doesn't dispute the final invoice? | **P** | US | `/en-us/guia/construction-estimate-template` | Pregunta propia modelo (§3) |
| 6 | Do contractors charge sales tax on construction? | R | US | `/en-us/guia/sales-tax-on-construction-by-state` | Qué estados gravan la construcción y cómo se muestra en la cotización |
| 7 | What does a builder cost per hour in Ireland? | R | IE | `/en-ie/guia/builder-rates-ireland` | Salario SEO vs. coste de empresa; el día a 190 € frente a 260-315 € |
| 8 | Does a house quote in Ireland include VAT at 13.5 %? | R | IE | `/en-ie/guia/vat-on-construction-ireland` | La regla de los dos tercios y el RCT |
| 9 | Do I need to charge GST on building work in Australia? | R | AU | `/en-au/guia/gst-on-building-work-australia` | Umbral de registro y la retención del 47 % sin ABN |
| 10 | How do I build a rate per square metre for a job? | R | GB | `/en-gb/guia/unit-price-analysis-uk` | "Un precio por m² es una decisión, no un precio": materiales, mano de obra, maquinaria |
| 11 | What should a building quote include in Australia? | R | AU | `/en-au/guia/building-quote-template-australia` | ABN, licencia y GST en el documento |
| 12 | Is it worth using estimating software instead of Excel? | R | multi EN | `/en/prices-comparison` | Comparación honesta: cuándo Excel sigue ganando |

### 1.2 Nivel B — español (40 % del tiempo)

| # | Pregunta (con palabras de cliente) | Tipo | Mercado | URL de destino | Ángulo de la respuesta |
| --- | --- | --- | --- | --- | --- |
| 13 | ¿Cuánto cuesta remodelar un baño en México? | R | MX | `/mx/guia/cotizar-remodelacion-mexico` | De la visita a la cotización: qué se mide y qué se escribe |
| 14 | ¿Cómo armo un APU de pañete en Colombia? | R | CO | `/co/guia/apu-panete-colombia` | Material + oficial y ayudante + rendimiento; el oficial de 1ª a 19.937 COP/h de coste de empresa |
| 15 | ¿Cómo metrado una obra en Perú? | R | PE | `/pe/guia/metrados-peru` | Medir por zonas y IGV aparte del comprobante |
| 16 | ¿Conviene cotizar en dólares o en soles en Ecuador? | R | EC | `/ec/guia/apu-dolares-ecuador` | Dólares nativos, RUC e IVA 15 % |
| 17 | ¿Qué es un análisis de precios unitarios? | R | genérico | `/guia/analisis-precios-unitarios` | El método con un ejemplo numérico simple |
| 18 | ¿Cómo hago un presupuesto de obra que el cliente no rechace? | R | genérico | `/guia/presupuesto-de-obra` | Estructura del documento: capítulos, mediciones, totales, validez |
| 19 | ¿Cuánto margen de ganancia se pone a una obra? | R | multi | `/precios-comparados` | Rangos por tipo de obra y por tamaño de empresa |
| 20 | ¿Cómo cotizo una obra en México con IVA y anticipo? | R | MX | `/mx/guia/cotizar-remodelacion-mexico` | Qué se cobra por adelantado y cómo queda por escrito |

**Cómo se usa la tabla.** Las 19 primeras son candidatas a **hilo existente**:
antes de escribir, se busca el texto en Google. Si el hilo de Quora aparece en
el top 5, se responde; si no aparece y el hilo tiene menos de 1.000 visitas,
se pasa a la siguiente. La nº 5 es la única pregunta propia, y va la última a
propósito: primero se responde, luego se pregunta.

---

## 2. Seis respuestas listas para publicar

### 2.1 Respuesta A (EN · US) — para el hilo «How much does it cost to remodel a bathroom?»

> **Texto para pegar:**
>
> The number everyone quotes is the wrong number. A bathroom remodel is priced
> on **hours of labour**, and most people price those hours with a wage when
> they should be pricing them with an employer cost.
>
> Take the US median wages from the 2026 BLS and load them with everything the
> contractor actually pays: FICA 7.65 %, federal unemployment (0.6 % net on the
> first $7,000), state unemployment, workers' compensation, paid time away from
> the tools, and the non-billable hours every crew has. That is what our price
> library carries:
>
> | Trade | Median wage | Employer cost per billable hour |
> | --- | --- | --- |
> | Plumber | $30.67/h | $40.21/h |
> | Electrician | $30.38/h | $39.76/h |
> | Brick / block mason | $29.87/h | $39.78/h |
>
> So a plumber quoted at the wage is under-priced by roughly a third before a
> single line of overhead is added — tools, insurance, supervision, the gaps
> between jobs, and profit. And workers' compensation is the swing item: cheap
> for a painter, expensive for a roofer or a demolition crew, which is why the
> same bathroom can legitimately move by $4,000 between two contractors in the
> same town. One of them is estimating with wages and finding the difference at
> the end of the job.
>
> Two things worth writing on the quote so the client is not surprised later:
> whether the number includes permits and inspection, and what happens to the
> price if the wall turns out to be plaster rather than drywall. That second
> one is where bathroom budgets actually die.
>
> The full breakdown of how the hour is loaded — and what a $4,000 gap between
> two quotes in the same street actually consists of — is in our guide to
> [construction labor cost per hour](https://cotizat.online/en-us/guia/construction-labor-cost-per-hour?utm_source=quora&utm_medium=referral&utm_campaign=comunidad&utm_content=us-labour-cost).
>
> To be clear: I build CotizaT, the estimating software we use for these
> quotes, which is why the link above goes to our own guide.

**Preparación antes de publicar:** comprobar que las cifras de la tabla siguen
vigentes (BLS y la fecha de nuestra biblioteca), que la URL responde 200 y que
el texto del enlace es el que se ve.

---

### 2.2 Respuesta B (EN · AU) — para el hilo «What hourly rate should I charge as a tradie?»

> **Text to paste:**
>
> There are two numbers, and most quotes get confused because they mix them.
>
> **The award rate is the floor, not the price.** Australian construction pay
> is set by award — the Building and Construction General On-site Award
> (MA000020), the Electrical Award (MA000025), the Plumbing Award (MA000036).
> The ordinary hourly rate is what the award says; it is the minimum a
> tradesperson costs you *before* superannuation, portable long service leave,
> workers' compensation, and the hours nobody can bill.
>
> **The employer cost is what you price with.** Take the award rate and load it
> with the 12 % superannuation guarantee, workers' compensation, annual and
> personal leave, public holidays and RDOs, then divide by the hours you can
> actually bill. Our price library carries it like this:
>
> | Trade | Award ordinary rate | Employer cost per billable hour |
> | --- | --- | --- |
> | Fit-out carpenter / carpenter and joiner (CW3 + tool allowance) | A$32.30/h | A$49.59/h |
>
> The gap between the two columns is the whole argument. A year holds roughly
> 1,600 billable hours against about 1,980 paid ones — the missing 380 are
> annual leave, public holidays, RDOs, wet days and the time between jobs. That
> is why a business that quotes from the raw award of A$31-32 lands in trouble
> on its third job, and why a quote built from an employer cost of A$48-50 does
> not look mysterious next to the market rate.
>
> And to be precise about the arithmetic: **employer cost is cost, not price.**
> Your charge-out rate adds vehicle, tools, insurance, supervision and profit
> on top, and then GST goes on the client's document.
>
> If you want the whole rate table — every trade, the award reference and the
> loaded cost — it is in our guide to [tradie hourly rates in
> Australia](https://cotizat.online/en-au/guia/tradie-hourly-rates-australia?utm_source=quora&utm_medium=referral&utm_campaign=comunidad&utm_content=au-tradie-rates).
>
> To be clear: I build CotizaT, the estimating software we use for these
> quotes, which is why the link above goes to our own guide.

**Preparación antes de publicar:** comprobar que la award rate y el 12 % de
super siguen vigentes (la Superannuation Guarantee cambia cada 1 de julio) y que
la tabla de la biblioteca está al día.

---

### 2.3 Respuesta C (EN · GB) — para el hilo «How do I handle CIS deductions on my construction invoices?»

> **Text to paste:**
>
> Two mistakes cause most of the trouble, and both are about the **base** of
> the deduction.
>
> **First: CIS is a percentage of the labour, not of the invoice.** A £4,000
> invoice made up of £1,200 of tiles and £2,800 of labour is not deducted on
> £4,000 — the deduction is calculated on the labour element. Get the base
> wrong and it quietly eats your margin on every single job, because nobody
> checks it until the year-end accounts.
>
> **Second: there are three rates, not two.** A subcontractor registered with
> HMRC for CIS suffers a 20 % deduction. A subcontractor who is not registered,
> or who cannot be verified, suffers 30 %. And a subcontractor can be paid
> **gross** — no deduction at all — if their status allows it. The same tiler
> can be at 20 % for one contractor and gross for another; the only
> difference is their registration, which is exactly why the status needs to
> travel with the quote rather than live in someone's head.
>
> Two practical points for the quote itself:
>
> - **Put the status in writing.** Under CIS a contractor needs your UTR and
>   your verification status, because that is what decides whether they deduct
>   20 %, 30 % or nothing. If your subcontractor quote does not state it, the
>   contractor is guessing.
> - **VAT is a separate trap.** Since 1 March 2021 most construction services
>   supplied business to business and reported under CIS carry the domestic
>   reverse charge: the supplier does not charge VAT and the customer accounts
>   for it. Apply it to the wrong job, or forget the note on the invoice, and
>   the problem surfaces months later.
>
> The rates, the calculation and the wording that goes on the quote are in our
> guide to [CIS deductions for
> subcontractors](https://cotizat.online/en-gb/guia/cis-deduction-subcontractors?utm_source=quora&utm_medium=referral&utm_campaign=comunidad&utm_content=gb-cis).
>
> To be clear: I build CotizaT, the estimating software we use for these
> quotes, which is why the link above goes to our own guide.

**Preparación antes de publicar:** verificar que los tres regímenes (20 %, 30 %
y pago bruto) y la fecha del 01/03/2021 siguen vigentes en HMRC; comprobar que
la URL responde 200.

---

### 2.4 Respuesta D (ES · CO) — para el hilo «¿Cómo armo un APU de pañete en Colombia?»

> **Texto para pegar:**
>
> Un APU de pañete son cuatro sumandos y tres decisiones. Las decisiones
> importan más que los números: es donde se gana o se pierde el margen de la
> obra.
>
> **1. Material.** Cemento o mortero, arena, agua y, si el pañete va con
> aditivo o hidrófugo, el aditivo. El consumo típico está en el orden de
> 0,35-0,45 kg de mezcla seca por m² según el espesor; con 1 cm, ese es el
> orden de magnitud que se repite en obra. El precio del saco se guarda con
> su unidad y su fuente, no solo con su valor.
>
> **2. Mano de obra, y aquí está la primera decisión.** En nuestra biblioteca
> de precios, un oficial de 1ª en Colombia cuesta **19.937 COP por hora de
> coste de empresa** (rango 16.312-23.562 COP, con corte del 08/09/2026) y un
> ayudante especializado, 16.539 COP/h. Son **costes de empresa**, no salarios:
> ya incluyen ARL, pensión y prestaciones, por eso no se vuelven a sumar en el
> APU. Si el APU se arma con el jornal y luego se le "carga" la carga social
> otra vez, el presupuesto queda inflado; si se arma solo con el jornal, la
> obra pierde plata.
>
> **3. Maquinaria y herramientas.** Mixer, nivel, andamio, transporte. Casi
> siempre es una partida pequeña, pero es la que nadie escribe.
>
> **4. Gastos indirectos y utilidad.** Bodega, administración, transporte,
> utilidad. **Aquí está la segunda decisión: el margen de la obra se decide
> aquí, no en el precio del material.** Un maestro que pone 15 % de margen
> sobre el material y 8 % sobre la mano de obra se está equivocando de
> sitio.
>
> Y la tercera decisión es de forma: **las fórmulas tienen que ser
> referencias, no valores pegados.** Si el cemento sube un 8 %, se actualiza
> el APU y no el presupuesto entero. Es la diferencia entre un archivo que
> aguanta tres meses y uno que se rompe el día que cambia un precio.
>
> El método completo, con las fórmulas y los errores que más se repiten, está
> en nuestra [guía de APU de pañete en
> Colombia](https://cotizat.online/co/guia/apu-panete-colombia?utm_source=quora&utm_medium=referral&utm_campaign=comunidad&utm_content=co-apu-panete).
>
> Para que quede claro: trabajo en CotizaT, que desarrolla el software donde
> hacemos estos presupuestos, y por eso el enlace de arriba va a nuestra guía.

**Preparación antes de publicar:** actualizar las cifras de mano de obra a la
fecha de publicación (la biblioteca se corta el 08/09/2026) y mantener la
frase "costo de empresa" para no inducir a error.

---

### 2.5 Respuesta E (ES) — para el hilo «¿Conocen algún software de construcción para reducir costos?»

**Idioma del hilo:** español. **Enlace:** uno solo, la guía de APU (indexable,
con CTA de prueba dentro). **Afiliación:** declarada en la misma frase en la
que se nombra la herramienta.

Texto exacto para copiar y pegar:

```
Sí, existe, pero te voy a decir lo que no te cuentan esas páginas: el software no abarata la obra por sí solo. Lo que abarata es dejar de decidir a ojo. El programa es solo la forma barata de tener lo que en una hoja de cálculo se te rompe: precios con su fecha, mediciones que cuadran y cambios de alcance por escrito.

El primer salto que yo haría no es el takeoff ni el 3D, es el precio unitario. Cada partida de tu presupuesto debería salir de un análisis de precios unitarios: materiales, rendimiento, horas y el precio con su fecha y su fuente. Ahí es donde se te va el dinero sin que te enteres. El mismo recurso con el precio del año pasado, o el mismo oficial más caro que hace dos años, y el presupuesto sigue viéndose igual en el papel.

Herramientas en las que merece la pena mirar:

- Medición y takeoff: Bluebeam Revu, Autodesk Takeoff, PlanSwift, CostX, On-Screen Takeoff.
- Presupuesto y control de obra: Buildertrend, eTakeoff y las hojas de cálculo de toda la vida, que no van a morir.
- Gestión de obra y cambios: Procore, Buildertrend, OpenProject, Fieldwire. Aquí es donde se recupera el dinero: el cambio de alcance queda registrado por escrito y el presupuesto se ajusta con la evidencia, no con una discusión.

Y para que conste, que es justo lo que Quora pide declarar: yo trabajo con obra todos los días y participo en el desarrollo de CotizaT, una herramienta para esto. Si te interesa el método más que la marca, escribí una guía sobre cómo montar un APU sin que se te rompa en cuanto cambias un precio:
https://cotizat.online/guia/analisis-precios-unitarios?utm_source=quora&utm_medium=referral&utm_campaign=comunidad&utm_content=es-precios

Un consejo antes de que pagues nada: mete en la prueba una obra que ya tengas cerrada y compara el importe que te devuelve con lo que de verdad te costó. Si se parece, la herramienta te sirve; si se va lejos del real, ningún programa te va a salvar.

Si me dices el país y qué tipo de obra haces (residencial, reforma, obra pública), te digo por dónde empezaría y qué parte del presupuesto suele escaparse.
```

**Por qué así:**

| Regla | Cómo se cumple |
| --- | --- |
| El hilo manda | Pregunta en español, respuesta en español, enlace a página en español |
| Un solo enlace | La guía de APU; lleva dentro el CTA de prueba y el nombre de la marca |
| Enlace en contexto | Va en el sixth párrafo, ni al principio ni al final |
| Afiliación declarada | «participo en el desarrollo de CotizaT», en la misma frase que nombra la herramienta |
| Nada de producto en la primera frase | La primera frase es una respuesta sobre software, no un anuncio |
| Cifras sin inventar | Ninguna cifra: solo criterio y nombres reales de herramientas |
| Cierre con pregunta | Invita a decir país y tipo de obra; baja el tono de la respuesta y suma hilo |
| Sin repetirse | Si contesta, se agradece el detalle y no se pega lo mismo en otros hilos |

**Si preguntan en comentarios:**

- *«¿Es gratis?»* → hay 7 días de prueba sin tarjeta; el software es de pago.
- *«¿Sirve para obra pública?»* → para la obra privada; el APU de contrato
  estatal es otro sistema y no lo cubre.
- *«¿En qué países?»* → 23 mercados con moneda e impuesto propios.
- *«¿Puedes adaptar mi Excel?»* → sí, importan descompuestos .xlsx conservando
  fórmulas y celdas combinadas, y se pega TSV o se importa .bc3 (FIEBDC-3).

---

### 2.6 Respuesta F (ES) — para el hilo «¿Cuándo debería una empresa reemplazar Excel por una aplicación web empresarial?»

**Hilo genérico de gestión**, con audiencia amplia de dueños de negocio, técnicos y gerentes. La estrategia: responder de verdad al corte entre hoja y aplicación web, y meter **CotizaT como caso propio real** (declarando autoría) para que cualquier profesional de obra, reformas, arquitectura o instalaciones que lea el hilo vea qué resuelve exactamente, mientras el resto entiende el ejemplo sin sentir que le están vendiendo humo. **Un solo enlace**, en la mitad de la respuesta, con su UTM.

Texto exacto para copiar y pegar (sin cortes de línea a mitad de párrafo para pegar directo en el editor de Quora):

```
La respuesta corta: cuando la hoja deja de ser una calculadora y pasa a ser la memoria compartida de la empresa. Ese es el corte real, y tiene mucho menos que ver con el tamaño del equipo de lo que parece.

Mientras el Excel lo usa una sola persona para analizar números o simular escenarios, es imbatible: rápido, flexible y prácticamente gratis. El problema empieza el día en que la operación diaria depende de ese archivo. Las señales suelen ser siempre las mismas:

- Varias personas tocan el mismo documento y nadie sabe quién cambió una celda, cuándo ni por qué.
- El archivo "bueno" vive en el correo o en el escritorio de alguien ("presupuesto_final_v3_definitivo_este_si.xlsx").
- Quien entra solo a cargar un dato ve también costes internos, márgenes o datos de clientes que no debería tocar.
- Cambias una tarifa o un precio base y tienes que perseguir veinte pestañas rezando para no haber roto una fórmula de subtotal.
- Si la persona que armó la plantilla enferma o se va de vacaciones, nadie se atreve a tocarla.
- A fin de mes toca cuadrar a mano tres versiones distintas de la misma realidad.

Te pongo mi propio caso —y aclaro de frente que la herramienta es mía—: yo vengo de la construcción y terminé creando CotizaT precisamente porque el Excel se nos rompía presupuestando obra. Cambiaba el precio de un material o la hora del oficial y había que actualizar hojas una por una; un cliente pedía quitar dos partidas, reescribías encima, se descuadraba una suma y acababas enviando un PDF con el margen comido. Al pasarlo a aplicación web conectas tu catálogo de partidas con tus precios unitarios, actualizas un coste una sola vez sin alterar los presupuestos ya entregados, el sistema te avisa si dejas una partida a cero o el margen bajo mínimos y sacas el PDF con tu logo listo para mandar por WhatsApp guardando cada versión. Aquí dejé escrito cómo estructuramos ese paso para no depender de una hoja frágil:
https://cotizat.online/guia/presupuesto-de-obra?utm_source=quora&utm_medium=referral&utm_campaign=comunidad&utm_content=es-excel-app

Ahora bien, igual de importante es saber cuándo NO salir de Excel. Si el proceso lo lleva una sola persona, cabe en una tabla limpia y un error se detecta en dos minutos, pagar o desarrollar una aplicación web es comprarte un problema nuevo. Cambiar de herramienta cuando el proceso sigue desordenado solo convierte un caos barato en un caos con cuota anual.

Cuando sí toca dar el salto, tres cosas que se aprenden viendo migraciones reales:

1. No migres toda la empresa de golpe. Elige un solo cuello de botella —presupuestos, inventario, partes de trabajo, cobros—, resuelve ese y deja el resto en hojas hasta que duela de verdad.
2. Exige que la aplicación hable con lo que ya tienes: que importe tus .xlsx o CSV sin obligarte a picar todo de cero, y que exporte el PDF o el archivo limpio que tu cliente necesita leer. Si el primer mes se va en transcribir histórico, en la tercera semana el equipo vuelve al Excel a escondidas.
3. Haz la cuenta que de verdad manda: cuánto te cuesta un solo error frente a lo que cuesta un año de herramienta. En presupuestos, en compras o en facturación, una sola fila mal sumada suele pagar varios años de licencia.

¿Qué proceso es el que hoy te tiene dudando entre estirar más el Excel o jubilarlo? Si cuentas un poco de qué va tu empresa, es fácil decirte si ya te compensa migrar o si basta con ordenar la hoja.
```

**Por qué funciona para atraer clientes a CotizaT sin que Quora la colapse:**

| Regla | Cómo se cumple |
| --- | --- |
| Responde primero a la pregunta | Abre con criterio claro y seis señales concretas que cualquier empresa reconoce |
| Publicidad natural, de primera mano | Cuenta el dolor real de presupuestar obra en Excel y menciona qué hace CotizaT en la práctica (catálogo conectado, versiones congeladas, avisos de margen, PDF + WhatsApp) |
| Afiliación declarada sin sonar robótico | «aclaro de frente que la herramienta es mía» — cumple la política de Quora sin repetir la frase plantilla de otras respuestas |
| Un solo enlace, en mitad del texto | Apunta a `/guia/presupuesto-de-obra` (indexable, cuyo título en Quora despliega *«CotizaT: cómo hacer un presupuesto de obra paso a paso»* y lleva dentro el alta de 7 días gratis) |
| Credibilidad humana | Incluye cuándo **no** dejar Excel; eso desactiva el rechazo al spam y multiplica votos positivos |
| Español neutro (España + LatAm) | Usa *tú* sin localismos cerrados, válido para México, Colombia, Chile y España |

**Si preguntan en comentarios:**

- *«¿Cuánto cuesta?»* → tiene 7 días de prueba gratis sin tarjeta y después plan anual de 89 USD/año.
- *«¿Sirve para cualquier empresa?»* → CotizaT está enfocada en presupuestos de construcción, reformas e instalaciones; para otros sectores, el criterio de los seis puntos es exactamente el mismo.
- *«¿Cuánto tarda pasar mis hojas?»* → importa catálogos y matrices en `.xlsx`, TSV pegado directo desde Excel o `.bc3`, así que no hay que picar partidas desde cero.
- *«¿Y si somos una empresa pequeña de tres o cuatro personas?»* → si varias personas tocan presupuestos o precios a la vez, o si un descuadre en una partida se come el beneficio del trabajo, ya compensa; si todo lo cotiza una sola persona con cuatro líneas fijas, Excel todavía cumple.

---

## 3. Pregunta propia modelo + su respuesta

Esta es la versión legítima de "preguntar y publicitar": **la pregunta es
real, la respuesta resuelve, la marca aparece una vez y el enlace va en medio**.

### 3.1 La pregunta (texto exacto)

> **What should a construction estimate include so the client doesn't dispute the
> final invoice?**

Requisitos que cumple: la formulan los clientes con esas palabras; no contiene
marca ni nombres de competidores; tiene intención de mercado (US); y la
respuesta puede apoyarse en datos reales.

### 3.2 La respuesta completa

> Most of the disputes I see are not about money. They are about **scope that
> nobody wrote down**. The invoice says $18,400 and the client expected
> $14,000, and both numbers are reasonable, because different work is included
> in each. Here is what an estimate has to carry to survive that conversation.
>
> **1. The scope, item by item, with quantities.** Not "bathroom
> renovation — $8,500", but the lines: remove and dispose of the existing
> floor, install waterproofing to the shower area, replace the plasterboard,
> fit three fixtures, tile X m² at Y. The client can only dispute a number
> they can see. A lump sum is an invitation to argue about what it contained.
>
> **2. What is explicitly excluded.** This is the part everyone omits and
> everybody misses. If the estimate does not say "does not include painting,
> electrical upgrades, disposal of the old units", then on the day the client
> expects those to be inside the number. Exclusions are not distrust: they are
> the difference between a fixed price and a slow-motion negotiation.
>
> **3. The unit prices behind the totals.** If the estimate says $18,400 and
> the client wants to know why, "labour, materials, 18 % overhead and 10 %
> margin" is an answer. A single total is not, and a client who cannot see the
> build-up assumes the worst.
>
> **4. The labour assumption, in writing.** This is where the two quotes in
> the same street end up $4,000 apart. One contractor priced the plumber at
> the median wage — $30.67/h — and the other priced the employer cost per
> billable hour — $40.21/h — after FICA, unemployment insurance, workers'
> compensation and the hours nobody can bill. Both quotes are honest; only
> one of them survives the job.
>
> **5. The commercial terms.** Deposit and how it is applied, stage payments,
> when the price is fixed until, what invalidates it (the wall turns out to be
> plaster, not drywall), how long the price is valid, and what happens on
> cancellation. All of it fits in a page.
>
> **6. The signature.** A signed estimate is not a formality: it is the
> evidence of what was agreed and when. Ours carries the client's signature
> block for that reason.
>
> **7. The revisions.** Any change after the estimate is accepted is a
> variation, with its own price and its own date — not a silent edit to the
> original document. A client who knows the rule in advance does not feel
> ambushed by it later.
>
> The template we use, with the commercial terms and the revision clause
> written out, is in our guide to [what a construction estimate must
> include](https://cotizat.online/en-us/guia/construction-estimate-template?utm_source=quora&utm_medium=referral&utm_campaign=comunidad&utm_content=us-estimate-template).
>
> To be clear: I build CotizaT, the estimating software we use for these
> quotes, which is why the link above goes to our own guide.

**Preparación antes de publicar:** comprobar que las cifras del punto 4 siguen
vigentes y que el artículo de destino (`/en-us/guia/construction-estimate-template`)
cubre realmente los siete puntos; si no los cubre, el hilo sirve para
detectar esa carencia.

### 3.3 Qué hacer con el hilo después

- Responder a los comentarios con datos y sin defender el producto a ultranza.
- Actualizar la respuesta si cambia la biblioteca de precios (añadir fecha de
  revisión).
- No pedir votos. Los upvotes se ganan respondiendo bien a otras preguntas.
- Publicar **una** versión (en inglés). No clonar en cinco idiomas.

---

## 4. Checklist de publicación (30 segundos)

- [ ] ¿Es una pregunta **real** (la haría un cliente) y **sin marca**?
- [ ] ¿La respuesta **se entiende entera** sin hacer clic?
- [ ] ¿Está escrita **en el idioma del hilo**?
- [ ] ¿El enlace apunta al **mercado del lector** (`/en-us/…`, `/mx/…`)?
- [ ] ¿Hay **un solo enlace**, y **no está en la primera ni en la última frase**?
- [ ] ¿El texto del enlace **describe** el destino (no "click here")?
- [ ] ¿El destino es una URL **indexable** (comprobar con `app.seo.es_indexable`)?
- [ ] ¿Lleva **UTM** (`utm_source=quora&utm_medium=referral&utm_campaign=comunidad&utm_content=…`)?
- [ ] ¿He **actualizado las cifras** a la fecha de publicación?
- [ ] ¿He **declarado la afiliación** ("I build CotizaT…")?

Si falla uno, no se publica.

---

## 5. Plantilla de registro semanal

Una fila por respuesta publicada. Es una tabla (Google Sheets o similar); no
hace falta más.

| fecha | url_hilo | idioma | mercado | url_destino | vistas_7d | vistas_30d | upvotes | clics | registros | notas |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-11-16 | https://quora.com/... | EN | US | /en-us/guia/construction-labor-cost-per-hour | | | | | | |
| | | | | | | | | | | |

Columnas derivadas: `vistas_30d / semanas` = ritmo. Si una respuesta sigue
subiendo a los 90 días, se **actualiza** (añadir un dato nuevo), no se
sustituye.

**Revisión mensual (15 minutos):**

1. ¿Cuáles dos respuestas trajeron más clics? → se actualizan.
2. ¿Alguna fue colapsada o eliminada? → se anota el motivo y se corrige el
   patrón, no la respuesta aislada.
3. ¿Los clics van a URLs indexables? (comprobar con `app.seo.es_indexable`)
4. ¿Cuántos registros trae el canal en total, y **cuáles por mercado**? (GA4
   → Adquisición → Referrals → quora.com, y el panel de altas)

---

## 6. Documentos relacionados

- `docs/ESTRATEGIA_QUORA_2026-11-09.md` — la estrategia, el porqué, el orden de
  mercados y el piloto de 90 días.
- `docs/PERFIL_QUORA_RUBEN_2026-11-09.md` — ficha del perfil (bio, credenciales,
  Business Profile, temas) y las frases de afiliación.
- `docs/HOJA_DE_RUTA_SEO.md` — contenidos por país y ritmo general.
- `app/seo.py` — `es_indexable()`: la función que decide si una URL puede
  enlazarse desde fuera.
- `basedatos_partidas/salida/precios_recursos_*.csv` — de dónde salen las
  cifras de estas respuestas.
