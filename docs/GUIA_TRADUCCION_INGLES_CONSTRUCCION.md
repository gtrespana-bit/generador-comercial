# Guía de traducción al inglés (construcción) — CotizaT

**Fecha:** 2026-10-15
**Glosario base:** `basedatos_partidas/glosarios/EN.json`

## 1. Variante de inglés

- **Por defecto: inglés de EE. UU. (US)**, por tamaño de mercado.
- Cuando un término difiere en Reino Unido (UK), se anota en el motivo del glosario y se prefiere la forma US en la UI; la variante UK se documenta para futuras localizaciones (`en-GB`).
- Evitar mezclar ortografías (color/colour, labor/labour). Usar US de forma consistente.

## 2. Reglas de no-literalidad

- No traducir palabra por palabra si el oficio usa otro término. Ejemplos:
  - "friso" → "render" (no "frieze").
  - "cielo raso" → "suspended ceiling" (no "raw sky").
  - "cabilla" → "rebar" (no "little cable").
  - "partida" → "line item" (no "departure").
  - "presupuesto" → "estimate" en contexto de obra (no "budget" salvo sentido general).
- Mantener siglas técnicas cuando son estándar en inglés: CMU, PPE, PDF, VAT.
- Mantener unidades métricas (m², m³, ml) aunque el mercado US use pies; la conversión de unidades es una fase posterior.

## 3. Términos clave acordados

| Español (VE) | Inglés (US) | Nota |
|---|---|---|
| concreto | concrete | |
| friso / pañete / repello | render | UK: render; US: plaster finish |
| cielo raso | suspended ceiling | UK: suspended ceiling; US: drop ceiling |
| rodapié / zócalo | baseboard | UK: skirting board |
| plomero | plumber | |
| cabilla | rebar | |
| losa | slab | |
| vaciado de concreto | concrete pour | |
| mezcladora de concreto | concrete mixer | |
| bloque de concreto | concrete masonry unit (CMU) | |
| porcelanato | porcelain tile | |
| enchapado / alicatado | tiling | |
| pintura de caucho | elastomeric paint | |
| contrapiso | screed | |
| encofrado | formwork | |
| pladur | drywall | |
| tabique | partition | |
| albañil | bricklayer | |
| maestro de obra | site foreman | |
| presupuesto | estimate | En sentido general: budget |
| cotización | quote | |
| partida | line item | |
| capítulo | section | |
| descompuesto / APU | cost breakdown / unit price analysis | |
| rendimiento | productivity | |
| mano de obra | labor | |
| margen | margin | |
| IVA | VAT | US: sales tax |
| garantía | warranty | |
| remodelación | remodeling | UK: renovation |
| reforma | renovation | |
| cambio de alcance | change order | |
| cuadrilla | crew | |

## 4. Capítulos del catálogo (títulos del árbol)

Los 445 títulos (capítulos, subcapítulos y apartados) se tradujeron a
mano en `tools/lotes/lote_76_titulos_del_arbol.py` (20/10/2026); viven
como excepciones y ganan siempre a la máquina de reglas. Antes salían
palabra por palabra: «Works priors», «Conditioning of the ground»,
«protection plot» por protección solar, con residuos sin traducir
(«salud», «urbanismo», «firmes»). `tests/test_titulos_arbol_en.py`
impide que vuelvan.

Referencia de los capítulos de nivel 1 (base US; `variante_ingles`
localiza GB/IE/AU/CA):

| Español | Inglés |
|---|---|
| 01 Actuaciones previas | Preliminary work |
| 02 Demoliciones y desmontajes | Demolition and dismantling |
| 03 Acondicionamiento del terreno | Earthwork and site preparation |
| 04 Fundaciones | Foundations |
| 05 Estructuras | Structures |
| 06 Fachadas y particiones | Facades and partitions |
| 07 Carpintería, herrería, vidrios y protección solar | Carpentry, metalwork, glazing and solar shading |
| 08 Remates y ayudas | Trim work and builder's work |
| 09 Instalaciones | Building services (MEP) |
| 10 Aislamientos e impermeabilizaciones | Insulation and waterproofing |
| 11 Techos y cubiertas | Roofs and roofing |
| 12 Revestimientos y acabados | Coatings and finishes |
| 13 Equipamiento, mobiliario y señalización | Equipment, furniture and signage |
| 14 Obras exteriores y urbanismo | Exterior and site works |
| 15 Gestión de residuos y limpieza | Waste management and cleaning |
| 16 Control de calidad y ensayos | Quality control and testing |
| 17 Seguridad y salud en obra | Construction health and safety |
| 18 Rehabilitación energética | Energy retrofit |

Léxico fijo del árbol: remate = *trim* (en cubierta, *flashing*),
ayudas de albañilería = *builder's work*, protección solar = *solar
shading*, respaldo eléctrico = *backup*, pasos de instalaciones =
*penetrations*, aislamiento de servicios = *isolation* (el térmico sigue
siendo *insulation*).

## 5. Próximos pasos técnicos

1. Introducir i18n real (Jinja2 + archivos de idioma) para UI y PDF.
2. Añadir ruta `/en/` con landing en inglés (copy propio, no traducción literal).
3. Añadir fuentes con cobertura Unicode para PDF (DejaVu/Noto) si se soportan acentos/otros scripts.
4. Definir mercado objetivo (US/UK) y moneda (USD/GBP) antes de precios de referencia.
5. Crear tests equivalentes a `tests/test_espana.py` para inglés.
