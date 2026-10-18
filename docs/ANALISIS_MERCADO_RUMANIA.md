# Análisis de viabilidad: adaptación de CotizaT al mercado de Rumanía

**Fecha:** 2026-10-15
**Contexto:** CotizaT cubre hoy 18 mercados, todos hispanohablantes (17 LatAm + España). La solicitud es abrir Rumanía.

## 1. Respuesta corta

**No es viable tratar Rumanía como "un país más" del selector.** Sería el primer mercado no hispanohablante y el primero fuera del bloque cultural en el que se basa todo el producto (vocabulario, catálogo, traducción runtime, SEO, documentación). Añadirlo como si fuera España (glosario VE→RO + precios en RON) dejaría la interfaz, los PDF, los emails y la ayuda en español, lo que no es un producto para el mercado rumano.

Si existe un cliente concreto que lo pague, la vía realista es un **proyecto de localización completo** (i18n + datos de mercado + cumplimiento legal), no una entrada en `app/paises.py`. Estimación: **3–6 meses de trabajo de un desarrollador + un traductor nativo de construcción**, más un presupuesto de investigación de precios y cumplimiento fiscal.

## 2. Por qué Rumanía no encaja en el patrón actual

El patrón de "apertura de país" que se usó para España y LatAm asume:

- La UI, los PDF, los emails y la ayuda ya están en el idioma del mercado (español).
- Solo cambian términos de obra (concreto→hormigón, friso→enfoscado) vía `app/services/traduccion.py` y glosarios JSON.
- Solo cambian moneda, IVA, ID fiscal y precios de referencia.

Rumanía rompe las tres premisas:

1. **Idioma.** No hay capa de internacionalización: `app/templates/base.html` fija `<html lang="es">`, todos los templates, JS, mensajes de error, emails y PDF están en español. No existe framework i18n (gettext/Babel). Habría que introducirlo o duplicar templates.
2. **Terminología de obra.** El glosario VE→ES traduce entre variantes del español. Un glosario VE→RO traduciría "concreto" a "beton", pero el resto de la interfaz seguiría en español. El resultado sería un producto híbrido inutilizable para un constructor rumano.
3. **Marco legal y fiscal.** Rumanía es miembro de la UE con e-facturación obligatoria (RO e-Factura / ANAF, B2B desde 2024, B2C desde 2025), SAF-T y IVA estándar del 21 % (reducida 11 %). CotizaT genera documentos comerciales, no facturas fiscales; en Rumanía el PDF no es el documento legal. Habría que integrar emisión RO_CIUS o dejar claro que el usuario factura por su cuenta (como se hace en España con el CFDI/SEPA, pero aquí el mercado espera e-Factura).

## 3. Datos de mercado relevantes (verificados 2026-10-15)

| Concepto | Rumanía |
|---|---|
| Moneda | RON (leu rumano), ~5,0 RON/EUR |
| IVA estándar | 21 % (desde 01/08/2025); reducida 11 % |
| ID fiscal | CUI/CIF; prefijo RO para IVA intracomunitario |
| Autoridad fiscal | ANAF |
| Capital / mercado principal | Bucarest |
| Idioma | Rumano |
| E-facturación | Obligatoria (RO e-Factura, ANAF) |
| Construcción | Normas HG 907/2016 (devize, F1–F6, DG/DO) |
| Salario mínimo construcción | ~4.582 RON/mes |

## 4. Competencia local

El mercado rumano ya tiene software consolidado y barato para el mismo perfil (meseriași y pequeñas empresas): Deviz Rapid, eDevize, Windoc Deviz, Deviz 360, deviz.ro. Ofrecen devize conformes a HG 907/2016, bases de datos de normas, exportación a Excel, firma digital y envío por WhatsApp. CotizaT no tendría ventaja de features frente a ellos; su ventaja (offline, PDF profesional, catálogo propio) es replicable y ya está cubierta. Entrar sin localización completa sería competir en desventaja.

## 5. Plan de adaptación si se decide seguir adelante

### Fase 0 — Validación comercial (2–4 semanas, antes de código)

- Confirmar cliente pagador y precio objetivo (licencia o suscripción).
- Definir si el producto se vende como "presupuesto comercial" (sin e-Factura) o si se integra ANAF.
- Decidir si la marca CotizaT se traduce o se mantiene.

### Fase 1 — Internacionalización (i18n) (4–8 semanas)

- Introducir sistema de traducciones (Jinja2 + JS) con archivos de idioma `es` y `ro`.
- Extraer todos los strings de templates, JS, emails, PDF y mensajes de error.
- Traducir la interfaz completa al rumano con un traductor nativo del sector construcción.
- Cambiar `<html lang>` dinámico y metadatos SEO por idioma.

### Fase 2 — Datos de país Rumanía (2–4 semanas)

- Añadir entrada `RO` en `app/paises.py` (RON, IVA 21 %, CUI/CIF, vocabulario rumano de obra, ejemplos Bucarest).
- Crear glosario `basedatos_partidas/glosarios/RO.json` (VE→RO) para catálogo base.
- Investigar y generar matriz de precios en RON (`tools/generar_matriz_precios_*.py` + SQL de carga).
- Añadir tasa de referencia RON en `app/services/tasa.py`.
- Actualizar `app/services/importador_precios_mercado.py` (`MONEDA_PAIS["RO"] = "RON"`).

### Fase 3 — SEO y landing (1–2 semanas)

- Ruta `/ro/` y `/ro/` en `app/routers/publico.py`.
- Copy propio en `app/seo.py` y `app/seo_contenido.py` (no find-and-replace).
- hreflang `ro-RO`, sitemap, JSON-LD con Rumanía en `areaServed`.

### Fase 4 — Cumplimiento legal (variable)

- Evaluar integración RO e-Factura (ANAF) si se quiere facturar desde la app.
- GDPR: política de privacidad, cookies, DPA, alojamiento UE.
- Adaptar garantías y contratos al derecho rumano (o desactivarlos).

### Fase 5 — Tests y cierre (1–2 semanas)

- Suite `tests/test_rumania.py` equivalente a `tests/test_espana.py`.
- Actualizar `tests/test_pais_selector.py` (19 países) y `LISTADO_ESTADO_PAISES.md`.
- Auditoría `auditar_lanzamiento.py --strict`.

## 6. Coste aproximado y riesgo

- Esfuerzo total estimado: **3–6 meses** de un desarrollador a tiempo parcial + traductor + investigación de precios.
- Riesgo principal: competencia local ya establecida y barata; sin i18n real el producto no se vende.
- Riesgo secundario: obligaciones de e-Factura y GDPR si se promete "facturación".

## 7. Recomendación

**No abrir Rumanía ahora.** CotizaT tiene un foso claro en español (Venezuela, España y LatAm) y el trabajo de localización completo no se justifica sin un cliente pagador validado. Si la solicitud viene de un cliente concreto:

1. Ofrecer primero una **licencia en español** con soporte (si el cliente es bilingüe o trabaja con clientes hispanos).
2. Si insiste en rumano, presupuestar la Fase 0–2 como proyecto a medida con pago por hitos, no como feature del roadmap estándar.
3. Revaluar cuando exista una segunda solicitud rumana (señal de mercado real).

## 8. Lo que NO se ha tocado en el repositorio

Este documento es solo análisis. No se han modificado `app/paises.py`, glosarios, tests ni SEO. El selector sigue con los 18 países actuales.
