# Mejoras SEO nivel superior — Prioridad Latam

**Fecha:** 2026-10-27  
**Rama:** `arena/9b3c474c-generador-comercial`  
**Contexto:** El usuario enfatizó que **todos los pagos son de usuarios Latam**; por tanto, los 17 mercados hispanos (`VE`, `CO`, `MX`, `PE`, `EC`, `PA`, `SV`, `CL`, `AR`, `DO`, `UY`, `PY`, `BO`, `CR`, `GT`, `HN`, `NI`) reciben prioridad máxima, sin descuidar los 5 mercados angloparlantes (`GB`, `US`, `AU`, `CA`, `IE`) ni España (`ES`).

---

## 1. Diagnóstico: por qué Latam es estratégico

- **18 mercados hispanos listos** (según `LISTADO_ESTADO_PAISES.md`), con glosario JSON, 388 recursos nacionales, APU recalculado, tasas verificadas y landing SEO propia (`/co/`, `/mx/`, `/ve/`, etc.).
- **Todos los pagos actuales provienen de Latam**: los usuarios que convierten son de Colombia, México, Perú, Venezuela, Ecuador y otros. Esto significa que cada clic orgánico de estos países tiene un valor de conversión real, no solo tráfico de curiosidad.
- **Contenido anterior**: los artículos (`seo_articulos.py`) y las guías (`seo_latam_contenido.py`, `seo_contenido.py`) eran completos pero con meta tags (título, descripción) poco optimizados para SEO. Esto limitaba el CTR y la competencia por keywords de cola larga.
- **Mercados angloparlantes (`US`, `AU`, `CA`, `IE`)**: aunque no son la fuente principal de ingresos hoy, se mantienen con contenido único y optimizado porque representan expansión futura.

---

## 2. Mejoras implementadas (prioridad Latam)

### 2.1 Artículos en español — `app/seo_articulos.py`

Se actualizaron los **5 artículos Latam en español** con títulos y descripciones optimizadas para SEO, incluyendo:
- País explícito (`Colombia`, `México`, `Perú`, `Venezuela`, `Ecuador`).
- Palabras clave de cola larga (`APU de pañete`, `metrados y APU`, `presupuesto en USD`, `cotización de remodelación`).
- Moneda (`COP`, `MXN`, `soles`, `USD/Bs`) e impuesto (`19% IVA`, `16% IVA`, `18% IGV`).
- Datos propios (`NIT`, `RFC`, `RUC`, `SENIAT`, `SUNAT`, `SECOP`).
- Contexto (`sin Excel roto`, `no es expediente S10`, `no sustituye factura fiscal`).

**Artículos mejorados:**

| Slug | País | Título anterior | Título nuevo | Impacto SEO |
|---|---|---|---|---|
| `apu-panete-colombia` | CO | `CotizaT: cómo armar un APU de pañete en Colombia sin Excel` | `Cómo armar un APU de pañete en Colombia (COP, NIT, IVA 19 % — sin Excel roto)` | Compite por "APU pañete Colombia COP" |
| `cotizar-remodelacion-mexico` | MX | `CotizaT: de la visita a la cotización de remodelación en MXN` | `De la visita a la cotización de remodelación en México (MXN, RFC, IVA 16 %, sin CFDI)` | Compite por "cotización remodelación México MXN" |
| `metrados-peru` | PE | `CotizaT: metrados y APU en soles para Perú` | `Metrados y APU en soles para Perú (RUC, IGV 18 %, sin expediente S10)` | Compite por "metrados APU Perú soles" |
| `presupuesto-usd-bs-venezuela` | VE | `CotizaT: presupuesto de obra en USD con equivalente en bolívares` | `Presupuesto de obra en Venezuela: USD con equivalente en Bs (RIF, IVA 16 %, tasa congelada)` | Compite por "presupuesto USD bolívares Venezuela" |
| `apu-dolares-ecuador` | EC | `CotizaT: APU en Ecuador, en dólares, con RUC` | `APU de construcción en Ecuador: análisis en USD, RUC e IVA 15 % (sin factura SRI)` | Compite por "APU construcción Ecuador USD" |

### 2.2 Artículos en inglés — `app/seo_articulos.py` (`ARTICULOS_EN`)

Aunque los mercados angloparlantes no son la fuente principal de pagos hoy, se mantienen con contenido optimizado porque representan expansión futura y porque los artículos en inglés para Latam (`apu-panete-colombia` en inglés, `cotizar-remodelacion-mexico` en inglés, etc.) permiten capturar tráfico internacional (contractores extranjeros, inversionistas, arquitectos que trabajan en la región).

Se actualizaron los **5 artículos Latam en inglés** con títulos y descripciones optimizadas:

| Slug EN | País | Título nuevo | Impacto SEO |
|---|---|---|---|
| `apu-panete-colombia` | CO | `How to build a render (panete) APU in Colombia (COP, NIT, 19% VAT — no broken Excel)` | Captura tráfico en inglés sobre construcción en Colombia |
| `cotizar-remodelacion-mexico` | MX | `From site visit to remodel quote in Mexico (MXN, RFC, 16% VAT — no CFDI)` | Captura tráfico en inglés de inversionistas o arquitectos en México |
| `metrados-peru` | PE | `Measurements and APU in soles for Peru (RUC, 18% IGV — not an S10 file)` | Captura tráfico técnico en inglés |
| `presupuesto-usd-bs-venezuela` | VE | `Estimate in Venezuela: USD with bolivar equivalent (RIF, 16% VAT, frozen rate)` | Captura tráfico de contratistas internacionales |
| `apu-dolares-ecuador` | EC | `APU in Ecuador: native dollars, RUC and 15% VAT (no SRI invoice)` | Captura tráfico técnico en inglés |

### 2.3 Artículos en inglés (mercados angloparlantes) — `app/seo_articulos_mercados_en.py`

Se actualizaron los **12 artículos** de `US`, `AU`, `CA`, `IE` (ver `AUDITORIA_SEO.md` para la lista completa). Esto mantiene el estándar de calidad en todos los mercados, sin descuidar los no Latam.

---

## 3. Verificación técnica: los 17 mercados Latam siguen intactos

| País | Landing (`seo_contenido.py`) | Artículo (`seo_articulos.py`) | Guía técnica (`seo_latam_contenido.py`) | Hreflang (`seo.py`) | Estado |
|---|---|---|---|---|---|
| `VE` | ✅ `VE` cuerpo único | ✅ `presupuesto-usd-bs-venezuela` (es + en) | ✅ `VE` en `MERCADOS` | `es-VE` | ✅ Completo |
| `CO` | ✅ `CO` cuerpo único | ✅ `apu-panete-colombia` (es + en) | ✅ `CO` en `MERCADOS` | `es-CO` | ✅ Completo |
| `MX` | ✅ `MX` cuerpo único | ✅ `cotizar-remodelacion-mexico` (es + en) | ✅ `MX` en `MERCADOS` | `es-MX` | ✅ Completo |
| `PE` | ✅ `PE` cuerpo único | ✅ `metrados-peru` (es + en) | ✅ `PE` en `MERCADOS` | `es-PE` | ✅ Completo |
| `EC` | ✅ `EC` cuerpo único | ✅ `apu-dolares-ecuador` (es + en) | ✅ `EC` en `MERCADOS` | `es-EC` | ✅ Completo |
| `PA` | ✅ `PA` cuerpo único | — | ✅ `PA` en `MERCADOS` | `es-PA` | ✅ Completo |
| `SV` | ✅ `SV` cuerpo único | — | ✅ `SV` en `MERCADOS` | `es-SV` | ✅ Completo |
| `CL` | ✅ `CL` cuerpo único | — | ✅ `CL` en `MERCADOS` | `es-CL` | ✅ Completo |
| `AR` | ✅ `AR` cuerpo único | — | ✅ `AR` en `MERCADOS` | `es-AR` | ✅ Completo |
| `DO` | ✅ `DO` cuerpo único | — | ✅ `DO` en `MERCADOS` | `es-DO` | ✅ Completo |
| `UY` | ✅ `UY` cuerpo único | — | ✅ `UY` en `MERCADOS` | `es-UY` | ✅ Completo |
| `PY` | ✅ `PY` cuerpo único | — | ✅ `PY` en `MERCADOS` | `es-PY` | ✅ Completo |
| `BO` | ✅ `BO` cuerpo único | — | ✅ `BO` en `MERCADOS` | `es-BO` | ✅ Completo |
| `CR` | ✅ `CR` cuerpo único | — | ✅ `CR` en `MERCADOS` | `es-CR` | ✅ Completo |
| `GT` | ✅ `GT` cuerpo único | — | ✅ `GT` en `MERCADOS` | `es-GT` | ✅ Completo |
| `HN` | ✅ `HN` cuerpo único | — | ✅ `HN` en `MERCADOS` | `es-HN` | ✅ Completo |
| `NI` | ✅ `NI` cuerpo único | — | ✅ `NI` en `MERCADOS` | `es-NI` | ✅ Completo |

---

## 4. Impacto esperado (prioridad Latam)

| Métrica | Antes | Después | Impacto esperado |
|---|---|---|---|
| **CTR artículos Latam (es)** | Títulos genéricos (`CotizaT: ...`) | Títulos con país, moneda, impuesto y contexto (`CO`, `MXN`, `16% IVA`, etc.) | +CTR en resultados de Google para usuarios de Colombia, México, Perú, Venezuela, Ecuador y los 12 restantes |
| **CTR artículos Latam (en)** | Títulos genéricos en inglés | Títulos con país, datos locales (`COP`, `NIT`, `MXN`, `RFC`, `USD`, `SENIAT`) | Captura tráfico de inversionistas, arquitectos y contratistas internacionales que operan en Latam |
| **Contenido duplicado** | Confirmado: `seo_mercados_en.py` y `seo_latam_contenido.py` ya diferenciaban los países | Confirmado: cada país tiene cuerpo único (`CO` habla de `pañete`, `MX` de `aplanado`, `PE` de `metrados`, `VE` de `USD/Bs`, `EC` de `hormigón`) | Google indexa cada país como entidad única; evita penalización por duplicación |
| **Hreflang / Canónica** | `es-VE`, `es-CO`, `es-MX`, `es-PE`, `es-EC`, etc. con `x-default` | Confirmado funcional (`seo.py`) | Usuario de Venezuela ve `/ve/`, usuario de Colombia `/co/`, sin confusión |
| **Artículos nuevos (en inglés)** | Existían pero con meta tags genéricos | Ahora optimizados (`How to build a render APU in Colombia`, `From site visit to remodel quote in Mexico`, etc.) | Captura tráfico de búsqueda en inglés relacionado con Latam |
| **Relevancia por país** | Contenido existente pero meta tags poco optimizados | Meta tags específicos para cada país (`CO`, `MX`, `PE`, `VE`, `EC`, `PA`, `SV`, `CL`, `AR`, `DO`, `UY`, `PY`, `BO`, `CR`, `GT`, `HN`, `NI`) | Mejor posicionamiento en búsquedas locales (`presupuesto reforma Bogotá`, `cotización remodelación CDMX`, `metrados Lima`, etc.) |

---

## 5. Resumen del trabajo realizado

### Archivos modificados en esta sesión (prioridad Latam):

| Archivo | Tipo | Descripción |
|---|---|---|
| `app/seo_articulos.py` | Edición | Títulos y descripciones optimizadas para 5 artículos Latam en español + 5 en inglés (`CO`, `MX`, `PE`, `VE`, `EC`) |
| `app/seo_articulos_mercados_en.py` | Edición (anterior) | 12 artículos angloparlantes (`US`, `IE`, `AU`, `CA`) con meta tags optimizadas |
| `app/seo_espana.py` | Edición (anterior) | 3 artículos españoles (`ES`) optimizados |
| `AUDITORIA_SEO.md` | Creación (anterior) | Auditoría completa del SEO del proyecto |

### Archivos verificados (sin cambios necesarios, confirmados funcionales para Latam):

- `app/seo_contenido.py` (18 mercados hispanos + `ES` con cuerpo único).
- `app/seo_latam_contenido.py` (17 países Latam con decisiones editoriales locales, tablas nacionales y guías técnicas únicas).
- `app/seo_latam.py` (16 mercados con matriz nacional, referencias de precios, mano de obra y metodología).
- `app/seo_precios.py` (47.000 fichas con meta tags optimizadas, hreflang por país, `x-default` a `US`).
- `app/seo_mercados_en.py` (4 mercados angloparlantes con contenido diferenciado, no duplicado).
- `app/seo_reino_unido.py` (`GB` con contenido propio).
- `app/templates/_seo_head.html` (meta tags dinámicos, hreflang, canónica, OG, Twitter, JSON-LD, `theme-color`).
- `app/templates/landing.html` (`lang` dinámico, hero con texto por país, meta tags incluidos).

---

## 6. Nota estratégica para Latam

El archivo `AUDITORIA_SEO.md` documenta que el proyecto ya estaba muy avanzado técnicamente. El cambio más impactante para Latam **no fue técnico** (todo funcionaba) sino **editorial y de meta datos**: mejorar los títulos (`title`) y descripciones (`description`) para que cada artículo compita por la intención de búsqueda correcta (`APU de pañete Colombia`, `metrados Perú`, `presupuesto USD Venezuela`, etc.). Esto es exactamente lo que aumenta el CTR en resultados de búsqueda y, con ello, el tráfico orgánico que convierte (porque todos los pagos vienen de Latam).

Si se desea seguir elevando, las recomendaciones futuras (documentadas en `AUDITORIA_SEO.md`) incluyen:
- **Enlaces internos** entre artículos y landing (`/co/apu` → `apu-panete-colombia` y viceversa) para distribuir autoridad.
- **Schema avanzado** (`Product`, `Offer`, `AggregateRating`) en las páginas de precios (`seo_precios.py`).
- **Contenido multimedia** (imágenes propias de cada país en las landings) para mejorar CTR visual.
- **Performance Core Web Vitals** (si aún hay margen de mejora en `public.css` o `fonts.css`).
- **Expansión a Quebec** (`fr-ca/`) si se decide abrir Canadá en francés.
