# Perfil de Quora de Rubén — 2026-11-09 (ficha lista para copiar)

Todo lo que hace falta para rellenar el perfil de Quora, con el texto exacto de
cada campo, en inglés (para el nivel A: US, GB, AU, IE) y en español (nivel B:
MX, CO, CL, ES). Los datos están tomados del repositorio y de la cuenta de
GitHub, así que son verificables.

**La idea de fondo:** en Quora no compite el mejor redactor, compite quien
tiene datos propios. Rubén tiene algo que casi nadie tiene: **es el
constructor que mide la obra y además escribe el software con el que la
presupuesta**. Eso es la credencial, y tiene que estar en las dos primeras
frases de la bio y en la primera frase de cada respuesta.

---

## 1. Ficha de identidad (de dónde sale cada dato)

| Campo | Dato | Fuente |
| --- | --- | --- |
| Nombre | Rubén | El titular |
| Edad | 40 años | El titular |
| Idioma nativo | Español; inglés de trabajo (el producto está íntegramente traducido) | `docs/HOJA_DE_RUTA_MERCADOS_INGLESES.md` |
| Empresa 1 | **RemodelaT** — reformas y remodelación de viviendas en A Coruña y su área metropolitana (Arteixo, Oleiros, Culleredo, Cambre, Sada, Bergondo, Betanzos, Carral, Abegondo). Portfolio real de obras ejecutadas por el fundador | `gtrespana-bit/RemodelaT-Galicia` (README) |
| Empresa 2 | **CotizaT** — software de presupuestos y control comercial de obra | `app/branding.py`, `README.md` |
| Producto | CotizaT: capítulos y partidas, mediciones por zonas, catálogo de **3.008 partidas**, precios unitarios, PDF profesional, firma del cliente, envío por WhatsApp, catálogo de precios por mercado, importación de descompuestos CYPE (.xlsx) | `README.md`, `basedatos_partidas/salida/catalogo_partidas.csv` |
| Mercados | **23**: ES, VE, CO, MX, EC, PE, CL, AR, DO, UY, PY, BO, PA, CR, GT, HN, SV, NI, US, GB, AU, CA, IE | `app/paises.py` (`ORDEN_SELECTOR`) |
| Stack (solo si se menciona) | FastAPI, SQLAlchemy, PostgreSQL, Jinja2, ReportLab, openpyxl; desplegado en Vercel con Supabase | `requirements.txt`, `docs/DESPLIEGUE_VERCEL.md` |
| Precio | 89 US$/año (9,99 US$/mes) | `docs/HOJA_DE_RUTA_SEO.md` |
| Web | `cotizat.online` (y `cotizat.online/en-gb/…`, `/en-us/…`, `/mx/…`) | `app/seo.py` |
| Soporte | `soporte@cotizat.online` | `app/branding.py` |
| GitHub | `github.com/gtrespana-bit` — **42 repos públicos** | GitHub API |
| Señal de constructor | El propio repo de CotizaT y los sitios de RemodelaT: webs de reformas, catálogos, marketplaces de segunda mano (maquinaria, autocaravanas), inmobiliarias, clínicas y restaurantes | GitHub API |

**Lo que GitHub dice de ti y conviene no desperdiciar:** 42 proyectos públicos
en unos años —marketplaces de segunda mano, inmobiliarias, clínicas, comercios,
tiendas— casi todos construidos por ti. Eso es la prueba de que no eres "un
man who's learning software": llevas años construyendo productos digitales
para negocios reales. En el perfil eso se resume en una línea y se demuestra
en las credenciales, no en un párrafo de autobombo.

---

## 2. Nombre visible (Display name)

**EN:** `Rubén — Construction Estimator & Remodeling Contractor`
**ES:** `Rubén — Constructor y software de presupuestos de obra`

Variante más sobria, si el nombre con texto largo se ve raro en móvil:
`Rubén (CotizaT)` / `Rubén — Constructor de reformas`.

> Quora **no** admite dos perfiles distintos por idioma con cuentas
> separadas: es **una cuenta, dos versiones del perfil**, y el conmutador
> (Ajustes → Idiomas) cambia lo que ve el lector. Se rellenan las dos
> versiones: la bio y las credenciales de cada idioma.

---

## 3. Titular (Headline) — el texto que aparece bajo tu nombre

> Límite práctico: que quepa en una línea en móvil. Hay versión corta y larga.

**EN (corta, 57 caracteres):**
```
Construction estimator, renovation contractor, software builder
```

**EN (larga, más keywords):**
```
Construction estimating and unit rates | Renovation contractor | I build the software I quote with
```

**ES (corta):**
```
Constructor de reformas y autor de software de presupuestos de obra
```

**ES (larga):**
```
Presupuestos de obra y precios unitarios | Constructor de reformas | Creo el software con el que cito
```

---

## 4. Biografía (About) — tres versiones para elegir

### 4.1 EN · corta (2 frases) — recomendada para empezar

```
I run RemodelaT, a renovation company in A Coruña, Spain, and I build CotizaT,
the construction estimating software we use to price our own work. The numbers
I post are the ones we actually quote with — labour cost per billable hour,
award rates, CIS and VAT treatment — not figures pulled from a blog.
```

### 4.2 EN · media (la que mejor funciona: 4 frases)

```
I own RemodelaT, a home renovation company in A Coruña, Spain, and I also build
CotizaT, the construction estimating software we use to price our own jobs.
That means the numbers I put on this site are the ones our price library
carries: employer cost per billable hour rather than raw wages, award rates
loaded with super and workers' compensation, CIS deductions calculated on
labour rather than on the invoice.

I've also spent years building software for other businesses — marketplaces,
property portals, clinics and shops — so I write about estimating software the
way an estimator would, not the way a brochure would.

Ask me about cost, rates, quotes or what a client actually disputes.
```

### 4.3 EN · larga (si prefieres que el perfil sea una carta de presentación)

```
I run RemodelaT, a home renovation and remodeling company in A Coruña and its
metropolitan area, and I build CotizaT, the construction estimating software we
use to price our own work: budgets by chapters and line items, measurements by
room, unit prices, professional PDF quotes, client signature and change orders.

That combination is why I answer questions here. Most estimating advice online
quotes a number; the number is only half of it. A plumber is not a wage, it is
a wage plus FICA, unemployment insurance, workers' compensation and the hours
nobody can bill — and getting that wrong is the difference between a quote
that holds and a job that loses money. I keep a price library for 23 markets
(Spain, the UK, Ireland, the US, Australia, Canada and Latin America) with the
sources and dates on every figure, and I publish what is in it.

Before CotizaT I built marketplaces, property portals and business sites for
other people, so I am comfortable with software as well as with brickwork.

Questions on construction costs, labour rates, estimating software, quotes,
CIS, VAT, GST or sales tax are welcome — especially if you want the working
out, not just the answer.
```

### 4.4 ES · corta

```
Soy dueño de RemodelaT, una empresa de reformas y remodelación en A Coruña, y
creo CotizaT, el software de presupuestos con el que cotizamos nuestro propio
trabajo. Los números que publico son los con los que cotizamos de verdad.
```

### 4.5 ES · media (recomendada para el nivel B)

```
Dirijo RemodelaT, una empresa de reformas y remodelación de viviendas en A
Coruña y su área metropolitana, y desarrollo CotizaT, el software de
presupuestos de obra que usamos para cotizar nuestro propio trabajo: capítulos
y partidas, mediciones por zonas, precios unitarios, PDF profesional, firma del
cliente y control de cambios de alcance.

Por eso contesto aquí. Casi todos los artículos sobre presupuestar dan un
número, y el número es solo la mitad: un plomero no es un salario, es un
salario con las cargas, el seguro y las horas que no se facturan. Por eso
mantengo una biblioteca de precios para 23 mercados con la fuente y la fecha de
cada dato.

Antes de CotizaT construí marketplaces, inmobiliarias y webs para otros
negocios, así que me manejo tanto con la obra como con el software.
```

---

## 5. Credenciales (lo que se ve bajo cada respuesta)

 Quora muestra las credenciales al lado de cada respuesta. Son el "sello de
garantía". Recomendación: **4 como máximo**, dos de ellas con fecha y una
con prueba verificable.

| # | Tipo | Texto EN | Texto ES |
| --- | --- | --- | --- |
| 1 | Trabajo | `Founder — CotizaT (2026–present) · Construction estimating software for 23 markets` | `Fundador — CotizaT (2026–actual) · Software de presupuestos de obra para 23 mercados` |
| 2 | Trabajo | `Owner — RemodelaT · Home renovation and remodeling, A Coruña, Spain` | `Propietario — RemodelaT · Reformas y remodelación de viviendas, A Coruña` |
| 3 | Competencias | `Construction estimating · Unit rates · Labour cost · Quoting · APU` | `Presupuestos de obra · Precios unitarios · Coste de mano de obra · APU` |
| 4 | Organización | `Member — 42 public repositories, from marketplaces to a full estimating platform` | `42 repositorios públicos: marketplaces, inmobiliarias y una plataforma completa de presupuestos` |

> En RemodelaT **no se pone año de fundación ni «años de experiencia»**: su propia web lo prohíbe ("empresa nueva; sin «años de experiencia» ni año de fundación"). Se aplica la misma regla aquí. De CotizaT sí se pone 2026, porque el proyecto está documentado desde esa fecha.

**El campo de URL del perfil (website):**

```
https://cotizat.online/en-us/?utm_source=quora&utm_medium=profile&utm_campaign=perfil
```

> Si el lector es de España, `/en-gb/`; si es de México, `/mx/`. Quora solo
> admite **una** URL en el perfil: se pone la de arriba y se cambia si el
> peso de las respuestas se desplaza a otro mercado. En la versión española del
> perfil, la URL es `https://cotizat.online/es/?utm_source=quora&utm_medium=profile&utm_campaign=perfil`.

**Ubicación:** la ciudad donde de verdad attendes a un cliente. Si es A Coruña,
`A Coruña, Spain`; si sigues operando desde Venezuela, `Caracas, Venezuela` y
se añade en la bio "also operating from Spain". Quora la usa para resultados
locales, así que no se pone un sitio que no sea el real.

---

## 6. Foto de perfil

- **Una persona, luz natural, fondo liso, del pecho para arriba.** Nada de
  logotipo, nada de collage de obras, nada de foto con el logo de fondo.
- La razón no es estética: en una respuesta, el lector ve "Rubén · Founder,
  CotizaT" y decide en un segundo si es una persona o un anuncio. Un avatar de
  logotipo hace que el perfil huela a promoción antes de leer la primera
  frase, y Quora penaliza ese perfil.
- No hace falta foto de obra: eso va en el Business Profile de CotizaT.

---

## 7. Temas a seguir (Topics)

Quora usa los temas para categorizar al autor y para mostrarte hilos
parecidos. Seguir 8-12 es suficiente; más, es ruido.

**EN (nivel A):**
`Construction` · `Home Improvement` · `Home Renovation` · `Remodeling` ·
`Architecture` · `Civil Engineering` · `Construction Management` ·
`Real Estate` · `Property Management` · `Building codes and permits` ·
`Small Business` · `Entrepreneurship`

**ES (nivel B):**
`Construcción` · `Reformas y rehabilitaciones` · `Remodelación` ·
`Arquitectura` · `Ingeniería civil` · `Bienes raíces` ·
`Construcción y vivienda` · `Pequeñas empresas` · `Emprendimiento`

> Se comprueba en Quora antes de seguir: el nombre exacto del tema varía
> (`Home Improvement` existe; `Remodeling` suele ir dentro de `Home
> Improvement`). Se siguen los que devuelvan hilos con respuestas reales.

---

## 8. Perfil de negocio (Business Profile) de CotizaT

Quora lo exige para contenido que menciona productos, y además da una página
propia con impresiones y clics. Es la parte "corporativa" de la estrategia.

| Campo | Valor |
| --- | --- |
| Nombre | `CotizaT` |
| Categoría | `Software` / `Business` (la que exista en el formulario) |
| Web | `https://cotizat.online` |
| Descripción corta (EN) | `Construction estimating software for contractors: budgets by chapters and line items, unit prices, measurements by room, professional PDF quotes with client signature, and a price library for 23 markets in local currency and local tax terms.` |
| Descripción corta (ES) | `Software de presupuestos de obra para constructores: capítulos y partidas, precios unitarios, mediciones por zonas, PDF profesional con firma del cliente y biblioteca de precios para 23 mercados en moneda e impuestos locales.` |
| Descripción larga (EN) | `CotizaT turns a catalogue and a set of prices into a clear, editable quote a client can sign. Chapters and line items, measurements broken down by room, unit prices with their source and date, change orders, a professional PDF with the totals block, and a catalogue you reuse job to job. It speaks USD, EUR, GBP, MXN, COP, PEN, CLP, ARS, AUD and CAD, with the local VAT, GST, sales tax or RCT treatment and the local fiscal identifiers, and it is priced in dollars. Built by a renovation contractor who wanted the software we actually quote with.` |
| Logo | El logo de CotizaT en PNG con fondo transparente (`marketing/` en el repo) |

---

## 9. La voz de Rubén (5 reglas para las respuestas)

Estas reglas son las que hacen que una respuesta sobreviva en Quora. Están
desarrolladas en `docs/ESTRATEGIA_QUORA_2026-11-09.md` §4.3; aquí van en forma
de lista de bolsillo.

1. **Primero la respuesta, después el matiz.** La primera frase contesta a la
   pregunta en una línea. Si se empieza con "es una pregunta interesante…",
   el hilo pasa al siguiente.
2. **Un dato propio por respuesta.** Un número de la biblioteca de precios, un
   cálculo, un error que se cometió. Un dato con **fuente y fecha**: si no la
   tiene, no se publica.
3. **Nada de plantilla.** La misma estructura con otras palabras en cada hilo.
   Quora detecta el texto repetido y lo tira.
4. **El enlace va en el medio**, uno solo, con texto descriptivo, y solo en
   1 de cada 3-5 respuestas. Si la respuesta pierde su valor sin el clic, es
   publicidad y se va.
5. **Cerrar con la afiliación, sin pedir nada.** Una frase que diga que eres
   el autor del software, y ninguna petición de votos.

**Frase de afiliación (variantes, una por mercado/idioma):**

| Idioma | Frase |
| --- | --- |
| EN | `To be clear: I build CotizaT, the estimating software we use for these quotes, which is why the link above goes to our own guide.` |
| EN (corta) | `Full transparency: I build CotizaT, the software behind that guide.` |
| ES | `Para que quede claro: trabajo en CotizaT, que desarrolla el software donde hacemos estos presupuestos, y por eso el enlace de arriba va a nuestra guía.` |
| ES (corta) | `Sin rodeos: soy el autor de CotizaT, el software que hay detrás de esa guía.` |

**Tu gancho personal, en una frase (para abrir cuando toque):**

- EN: `I run a renovation company, so these are the numbers we actually quote with — not the ones I found online.`
- ES: `Dirijo una empresa de reformas, así que estos son los números con los que cotizamos de verdad, no los que encontré por internet.`

---

## 10. La primera respuesta (qué publicar primero)

No publiques un perfil y te calles: **la primera respuesta decide si el
perfil se mueve o se queda en cero**. Propuesta para empezar:

- **Hilo en inglés (nivel A):** *"What should a construction estimate include
  so the client doesn't dispute the final invoice?"* — respuesta ya redactada
  en `docs/QUORA_BANCO_Y_RESPUESTAS_2026-11-09.md` §3.2.
- **Hilo en español (nivel B):** *"¿Cómo armo un APU de pañete en Colombia?"* —
  respuesta ya redactada en el mismo documento §2.4.

En ambas, el enlace va al final del cuerpo y la frase de afiliación cierra.

**Antes de publicar el perfil**, comprueba con Google que el hilo que vas a
contestar sale en el top 5 con su texto literal. Si no sale, elige otro: el
perfil sin tráfico se queda en cero visitas y no da información útil.

---

## 11. Qué NO poner (con el porqué)

| No pongas | Por qué |
| --- | --- |
| "Experto en 23 países" | No has dirigido obras en 23 países; has desarrollado un software que las cotiza. Es distinto y se nota. |
| "Más de X años de experiencia" (sin fuente) | La web de RemodelaT Coruña lo prohíbe explícitamente ("sin «años de experiencia» ni año de fundación"). Si no hay fecha verificable, no va. |
| Testimonios de clientes o cifras de obras inventadas | Prohibido también en la web de RemodelaT ("no inventar datos de obras ni cifras"). Además es riesgo legal. |
| Logotipo como foto de perfil | Huele a anuncio; el perfil pierde alcance. |
| Una biografía de 800 palabras | Nadie la lee. Tres frases y un enlace. |
| La lista de 42 repos como logro en la bio | Va en la credencial, no en el párrafo. |
| "Contact me for a quote" | Quora es para responder, no para vender. Un perfil que pide trabajo pierde respuestas. |
| Enlace a una URL con `noindex` | Cada respuesta debe apuntar a una página indexable del mercado del lector (ver `app.seo.es_indexable`). |

---

## 12. Checklist de alta (25-30 minutos)

1. [ ] Crear la cuenta con el **correo de trabajo** que quieres que aparezca
       (si puede ser con dominio propio, mejor que un Gmail personal).
2. [ ] Ajustes → **Languages**: activar English y Español, con English como
       idioma por defecto (el nivel A manda).
3. [ ] Nombre visible, titular y **biografía en las dos versiones** (§2, §3, §4).
4. [ ] Foto: persona, no logotipo (§6).
5. [ ] URL del perfil con UTM (§5).
6. [ ] Credenciales: las cuatro de la tabla (§5).
7. [ ] Temas: 8-12 (§7).
8. [ ] **Business Profile de CotizaT** con logo y descripción (§8).
9. [ ] Publicar la **primera respuesta** (§10) y comprobar a las 48 h que no
       ha sido colapsada ni eliminada.
10. [ ] Publicar la segunda y la tercera en hilos distintos, con textos
        distintos, en 48 h.
11. [ ] Registrar todo en la hoja de `docs/QUORA_BANCO_Y_RESPUESTAS_2026-11-09.md` §5.

---

## 13. De dónde sale cada dato

- GitHub (42 repos, fechas, descripción): `https://github.com/gtrespana-bit`
- RemodelaT Coruña (marca, zona, monedas, portfolio, "no inventar"):
  `gtrespana-bit/RemodelaT-Galicia` → `README.md`, `src/data/*`
- CotizaT (producto, catálogo de 3.008 partidas, 23 mercados, stack, precio,
  correo de soporte): `README.md`, `app/branding.py`, `app/paises.py`,
  `requirements.txt`, `basedatos_partidas/salida/catalogo_partidas.csv`,
  `docs/HOJA_DE_RUTA_SEO.md`
- Plan del canal: `docs/ESTRATEGIA_QUORA_2026-11-09.md` y
  `docs/QUORA_BANCO_Y_RESPUESTAS_2026-11-09.md`
- Perfil de negocio de Quora (obligatorio para mencionar el producto):
  `https://business.quora.com/resources/writing-on-quora-as-a-business`
