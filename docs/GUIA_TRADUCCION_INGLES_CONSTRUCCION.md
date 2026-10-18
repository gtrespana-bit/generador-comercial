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

## 4. Próximos pasos técnicos

1. Introducir i18n real (Jinja2 + archivos de idioma) para UI y PDF.
2. Añadir ruta `/en/` con landing en inglés (copy propio, no traducción literal).
3. Añadir fuentes con cobertura Unicode para PDF (DejaVu/Noto) si se soportan acentos/otros scripts.
4. Definir mercado objetivo (US/UK) y moneda (USD/GBP) antes de precios de referencia.
5. Crear tests equivalentes a `tests/test_espana.py` para inglés.
