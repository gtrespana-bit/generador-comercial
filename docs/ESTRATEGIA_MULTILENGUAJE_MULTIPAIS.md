# Estrategia multi-idioma y multi-país para CotizaT

**Fecha:** 2026-10-15
**Contexto:** CotizaT cubre 18 mercados hispanohablantes. Se plantea expandir a países con idiomas distintos (inglés, francés, alemán, rumano, etc.).

## 1. Respuesta corta

**Sí es muy complicado**, pero no por el selector de idioma: por la internacionalización completa (i18n) de un producto que hoy no tiene ninguna capa de traducción. El esfuerzo real no es "añadir un país", es **convertir CotizaT en un producto multilingüe**.

**No uses solo un selector de idioma sobre la misma URL.** Es la peor opción para SEO, compartibilidad y caché. Usa **URLs distintas y rastreables por locale** (idioma + país). Entre path y subdominio, para el estado actual del proyecto lo más sensato es **path-based con código de locale** (`/es-es/`, `/en-us/`, `/fr-fr/`, `/de-de/`, `/ro-ro/`), manteniendo un solo despliegue. Los subdominios tienen sentido cuando un mercado ya es grande y necesita entidad legal/infraestructura propia.

## 2. Por qué "selector de idioma sobre la misma URL" es mala idea

- Google indexa una sola URL por contenido; el idioma cambia en cliente y no se rastrea bien.
- Los enlaces compartidos (WhatsApp, email) abren siempre en el idioma por defecto.
- Caché/CDN y SSR se complican: la misma URL devuelve idiomas distintos según cookie/cabecera.
- Las métricas (analytics, Search Console) se mezclan.
- Los PDFs y emails generados en servidor necesitan saber el idioma del destinatario; si la URL no lo dice, hay que inferirlo de la sesión.

## 3. Opciones de arquitectura

### A. Path-based por locale (recomendado para empezar)

Ejemplo: `cotizat.com/es-es/`, `cotizat.com/es-mx/`, `cotizat.com/en-us/`, `cotizat.com/fr-fr/`, `cotizat.com/de-de/`, `cotizat.com/ro-ro/`.

Ventajas:
- Un solo despliegue, un solo dominio, cookies/sesión compartidas.
- SEO claro: hreflang por locale, sitemap por idioma.
- Encaja con el patrón actual (`/es/`, `/co/`): se migra de código de país a código de locale.
- Fácil de enrutar en FastAPI con un prefijo.

Costes:
- Migración de las rutas actuales (`/es/` → `/es-es/`, etc.) con redirects 301.
- Todos los enlaces internos y assets deben ser relativos al locale.

### B. Subdominios por mercado/idioma

Ejemplo: `es.cotizat.com`, `mx.cotizat.com`, `us.cotizat.com`, `fr.cotizat.com`.

Ventajas:
- Branding/región independiente, cookies por región, CDN regional, entidades legales separadas.
- Mejor para mercados grandes (Francia, Alemania, EE. UU.).

Costes:
- DNS wildcard, certificados, despliegues múltiples o routing por host.
- Sesión/auth compartida entre subdominios (cookies de dominio padre) o SSO.
- Más complejo de operar con el stack actual (un solo FastAPI).

### C. Dominios por país (ccTLD)

Ejemplo: `cotizat.es`, `cotizat.fr`, `cotizat.de`, `cotizat.ro`.

Máximo SEO local y confianza, pero máxima complejidad operativa y coste. Solo tiene sentido con equipos locales y facturación local.

**Recomendación:** empezar con **A (path-based)**. Si un mercado supera un umbral (por ejemplo, >1.000 clientes de pago o entidad legal propia), migrar ese mercado a subdominio/dominio propio.

## 4. Lo que de verdad es caro: la internacionalización

Hoy no existe i18n. Trabajo mínimo para soportar N idiomas:

1. **Extraer strings.** Todos los textos de `app/templates/`, `app/static/js/`, emails (`app/templates/emails/`), PDF (`app/services/pdf.py`, `pdf_interactivo.py`, `contrato.py`, `garantias.py`) y mensajes de error. Estimación: miles de strings.
2. **Sistema de traducción.** Jinja2 i18n extension + archivos `.po`/`.mo` o JSON por idioma, con fallback a español. Middleware que resuelve locale desde la URL, cookie o `Accept-Language`.
3. **Traducción profesional.** No vale traducción automática para un producto comercial; además el vocabulario de obra es específico (deviz, Devis, deviz, estimate, etc.).
4. **Catálogo y APU.** El catálogo base está en español venezolano. Para cada idioma hay que traducir nombres/descripciones de partidas o mantener glosarios VE→idioma (como hoy VE→ES). Para idiomas no latinos (árabe, chino, cirílico) el problema es mayor.
5. **PDF y fuentes.** ReportLab usa fuentes estándar (Latin-1). Rumano (ș, ț), francés/alemán (mayoría OK en Latin-1) y otros necesitan fuentes con cobertura Unicode (DejaVu, Noto) embebidas y subsetting. Hoy solo Lato/Inter están embebidas.
6. **Formatos.** Números, fechas, moneda y separadores decimales varían (1.234,56 vs 1,234.56). Hay que usar formateo por locale.
7. **Contenido SEO.** Cada locale necesita copy propio (no find-and-replace), hreflang, sitemap y JSON-LD con `inLanguage` y `areaServed`.
8. **Legal.** GDPR (UE), protección al consumidor, facturación electrónica por país (RO e-Factura, Francia e-invoicing 2026, etc.), contratos/garantías adaptados o desactivados.

## 5. Complejidad por idioma (estimación cualitativa)

| Idioma | Dificultad | Notas |
|---|---|---|
| Inglés | Media | Mercado enorme pero saturado; competencia fuerte (US/UK). Buena puerta para SaaS. |
| Francés | Alta | Mercado protegido, normas NF, facturación electrónica obligatoria progresiva. |
| Alemán | Alta | Exigencia de calidad/precisión, DIN, GDPR estricto. |
| Rumano | Alta | Mercado local con software barato y e-Factura obligatoria. |
| Otros latinos (portugués) | Media | Brasil/Portugal comparten dolor pero son mercados distintos. |

## 6. Plan recomendado (no hacer todo a la vez)

1. **Fase 0 — Validación (2–4 semanas).** Elegir UN solo nuevo idioma/mercado con cliente pagador real (recomendación: inglés, por tamaño y por ser el idioma puente). Validar precio y necesidad.
2. **Fase 1 — i18n mínimo (6–10 semanas).** Implementar sistema de traducción, extraer strings, traducir UI + PDF + emails al idioma elegido. Añadir locale en URL (`/en-.../`).
3. **Fase 2 — Datos de mercado (3–6 semanas).** Precios de referencia, moneda, IVA, ID fiscal, vocabulario de obra, SEO/landing.
4. **Fase 3 — Cumplimiento (variable).** Legal, facturación electrónica si aplica, GDPR.
5. **Fase 4 — Escalar.** Solo si la Fase 1–3 vendieron, repetir para el siguiente idioma reutilizando la infraestructura i18n.

**Regla:** no añadir un idioma nuevo hasta que el anterior tenga clientes de pago. La i18n es inversión fija; hay que amortizarla mercado por mercado.

## 7. Decisión de URL recomendada

- **Ahora:** migrar de `/es/`, `/co/`… a `/{locale}/` con código `lang-country` (`/es-es/`, `/es-mx/`, `/es-co/`…). Mantener redirects 301 desde las URLs antiguas.
- **Nuevos idiomas:** `/en-us/`, `/fr-fr/`, `/de-de/`, `/ro-ro/`, etc.
- **Subdominio** solo cuando un mercado supere el umbral de clientes/ingresos y necesite entidad legal propia.

## 8. Lo que NO se ha tocado en el repositorio

Este documento es solo análisis y estrategia. No se han modificado rutas, tests ni SEO. El selector sigue con los 18 países actuales.

## 8. Piloto implementado (2026-10-15)

- Ruta pública en inglés: `/en/` (redirección `/en` → `/en/`), con landing piloto en `app/templates/landing_en.html`.
- Cookie `cotizat_lang=en` al visitar el piloto.
- La UI completa sigue en español; este piloto valida demanda y copy antes de localizar el producto.
- Terminología: `basedatos_partidas/glosarios/EN.json` + `docs/GUIA_TRADUCCION_INGLES_CONSTRUCCION.md`.
