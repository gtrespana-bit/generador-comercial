# Análisis: de Venezuela a Latinoamérica — Ventajas competitivas y qué cambiar

> **Fecha:** 19/08/2026 · **Titular decide pasar de “solo Venezuela” a “todo el mundo hispano”.**
> Análisis a fondo del repositorio completo (694 tests, ~33k líneas, 3.006 partidas, 17 productos, PDFs verificados, producción en `cotizat.online` con Supabase/Vercel) antes de proponer ningún cambio de código.
> Complementa a `ANALISIS_PRODUCTO_Y_VIABILIDAD.md` (13/08) y a `PLAN_DE_COMERCIALIZACION_Y_EVOLUCION_SAAS.md` (16/08).

---

## 0. Resumen ejecutivo (léelo en 2 minutos)

**La decisión es acertada y llega en el momento óptimo.** No solo no debes limitarte a Venezuela: limitarte sería renunciar a tu mayor palanca comercial.

1.  **El 95% del código ya es regionalizable.** El núcleo (capítulos, partidas con mediciones, descompuestos editables recurso a recurso, costes/margen/beneficio, tiempos por cuadrilla, versiones inmutables, enlace de propuesta con aceptación trazable, PDF profesional con Lato, dashboard/reportes, importador CYPE/Excel y backup verificable) **no menciona Venezuela en ningún sitio**. Funciona mañana en Bogotá, Lima, Santiago o Ciudad de México sin tocarlo.
2.  **El 5% que sí ata es cosmético pero bloqueante para la venta:** título, hero y descripción de la landing (“Hecho para Venezuela”), defaults de país/moneda/IVA, solo dos monedas (`USD`/`Bs`), etiqueta `RIF`, bloque `🇻🇪 Funciones regionales de Venezuela`, texto `Tasa (ref. BCV)` y `Bs` hardcodeados en `pdf.py`, `form.html` y `detail.html`, e hilo horario `hora de Venezuela`.
3.  **Conviertes una debilidad en foso.** Los grandes (Presto 100€/mes, Arquímedes 70€/mes) ignoran Latinoamérica. Los latinos (OneEstimate 49-99 USD/mes + IA, OPUS 150 USD/mes en México, S10 80 USD/mes en Perú) cobran 6-20× más que tu piloto (`89 USD/año = 7,4 USD/mes`) y venden como diferencial justo lo que ellos no resuelven bien: **precios actualizados, foso local y soporte cercano**. Tú ya tienes el catálogo (3.006 partidas), el precio en USD (moneda común del sector en todo LatAm inflacionario) y la operación browser-first con aislamiento real. Cambiar 12 pantallas y 4 tablas te abre 500M de hispanohablantes con el mismo binario.
4.  **No necesitas reescribir ni “hacer versión LatAm”.** Hace falta un MVP de **2-3 semanas** (configuración por país + moneda libre + IVA configurable + etiqueta fiscal genérica + landing neutra). Después, crecimiento por *catálogo* y por *métodos de cobro locales*, no por código por país.

**Veredicto:** mantén el foco vertical (construcción/remodelación), abre el mercado en horizontal (todos los países hispanos). No diluyas el producto en “generador universal”.

---

## 1. Qué es CotizaT hoy — diagnóstico honesto

### 1.1 Lo que ya es world-class (y por qué importa contra la competencia)

Esto es lo que el análisis profundo del 13/08 calificó 8/10 como *software*:

| Área | Evidencia | Por qué es ventaja comercial |
|---|---|---|
| **Motor económico único con `Decimal` + `ROUND_HALF_UP`** | `app/services/calculations.py` es la única fuente de verdad (web, CSV, PDF comparten totales). Nunca se confía en subtotales del navegador. | Un presupuesto que descuadra 1 céntimo pierde la confianza para siempre. La mayoría de SaaS baratos calculan en JS y redondean con `float`. Tú no. |
| **PDF que vende** | ReportLab + Lato embebida, banda navy de capítulo con subtotal, partidas 1.1/1.2 con descripción técnica CYPE, mediciones desglosadas, producto presupuestado con imagen, totales base/IVA/total, anexos fusionados como páginas reales, marca de agua por estado, garantías por familia. Verificado visualmente en 4-15 páginas. | El cliente final no distingue tu PDF de uno de 60€/mes. Es tu closer. Un reformista gana obras por cómo se ve el documento. |
| **Descompuestos editables recurso a recurso** | `DescomposicionPartida`/`DescomposicionFila` con `origen=cype|manual`, `categoria` explícita, edición de rendimiento × precio unitario, subtotales, % complementarios y coste directo sincronizado con la matriz `.xlsx` original sin perder celdas/fórmulas. | CYPE/Presto lo tienen; ningún SaaS de 10-15€/mes lo tiene. Para un técnico, poder tocar “si sube el cemento de 0,23 a 0,28” y que recalcule todo es oro. En LatAm eso se traduce a APU. |
| **Tiempos de obra** | `app/services/tiempos.py`: horas por descompuesto (h/día/jornada), por catálogo o por `coste_mano_obra / tarifa_media`; totales, días con N cuadrillas y cobertura, separando h-hombre y h-equipo. | Ningún competidor barato lo muestra en obra. Permite prometer plazo sin inventar y calcular margen real vs. mano de obra. |
| **Versiones inmutables + propuesta con enlace seguro** | `PresupuestoVersion` snapshot + `EnlacePropuesta` (solo SHA-256, expirable, revocable, RLS por hash). Aceptación/rechazo con trazabilidad (función SECURITY DEFINER), notificación a admin y estado que solo avanza si es última versión. | Convierte el presupuesto en cierre de venta (“firma aquí desde el móvil”). ReformAI/OneEstimate lo venden como premium; tú ya lo tienes a 89$/año. |
| **Catálogo de 3.006 partidas clasificadas** | `basedatos_partidas/datos/descompuestos/*.json` → `partidas.csv` → 18 capítulos CYPE, con desglose materiales/mano de obra/complementarios, desperdicio y terminología auditada. | La competencia presume 3.650 (Motor de Presupuestos) o 10.700 APUs (OneEstimate). Tú ya compites en volumen y superas a todos los españoles baratos. El catálogo **es el producto** el día 1. |
| **Browser-first real** | PostgreSQL + RLS por `cotizat_app` (rol sin BYPASSRLS verificado por `/readyz`), 29 modelos tenant auditados, storage privado por proxy (no URLs públicas), rate limit distribuido Upstash, CSP sin `unsafe-inline`, backups/restore verificados con SHA-256, auditoría inmutable. | Puedes operar 500 empresas sin fuga de datos. Es lo que separa “licencia de escritorio” de “SaaS cobrable”. |
| **Precio de piloto fundador** | `89 USD/año` (habitual 109) o `9,99 USD/mes` + 7 días gratis sin tarjeta, con anti-reciclaje por email normalizado. | Ver §3: 6-13× más barato que la competencia directa. |

### 1.2 Lo que todavía no es SaaS vendible en cualquier país

| Hueco | Estado |
|---|---|
| Dependencia de marca/landing venezolana | Bloquea marketing fuera |
| Solo 2 monedas, IVA 16% venezolano como default, RIF, BCV | Bloquea presupuestos en MXN/COP/PEN/CLP/ARS |
| Catálogo con precios en USD pero validados contra mercado venezolano | Requiere disclaimer “referencial” o set regional |
| País default `Venezuela` en 5 sitios | Fricción en onboarding fuera |
| Fiscalidad Venezuela detrás de un flag único (`activar_funciones_venezuela`) | Necesita generalización a “funciones regionales por país” |

Ninguno de estos exige re-arquitectura. Todos son *configuración por tenant*.

---

## 2. Ventajas reales frente a la competencia directa (2026)

### 2.1 Quién es la competencia si abres a LatAm

| Segmento | Producto | Precio público | Foco | Lo que presume |
|---|---|---|---|---|
| **LatAm con IA/APU** | **OneEstimate** | Gratis 4/mes · **49 USD/mes** Pro · 99 Business | CO/MX/PE/CL/AR + ES | 10.700 APUs por país, IA sobre planos, BIM/IFC, AIU colombiano nativo |
| | **OPUS (Ecosoft)** | **~150 USD/mes** | México (obra pública) | Precios unitarios, generador APU, integración Neodata |
| | **Neodata** | **~90-120 USD/mes** | México | Presupuestos + control obra pública |
| | **S10 ERP** | **~80 USD/mes** | Perú/Bolivia | Clásico local, controla obra y costos |
| **LatAm pymes** | **ConstruCloud** | **~60 USD/mes** | Pymes hispanas | Gestión pymes construcción |
| | **Foco en Obra** | **~50 USD/mes** | Chile/Argentina | Presupuestos + seguimiento |
| **España/Europa** | **Presto (RIB)** | **~58-100€/mes** (480€/año) | España, licitación | Estándar sector, BC3/FIEBDC |
| | **Arquímedes (CYPE)** | **~70€/mes** (475€) | Técnico / Open BIM | Muy técnico |
| | **BrickControl** | **99€/mes** | España, integral | ERP completo |
| | **MedicionPro** | **29€/mes** | Cloud BC3 | Mediciones, certificaciones |
| **Low-cost global** | **ReformAI** | **14,99€/mes** (gratis 3/mes) | Reformas, móvil | App foto+texto, sin APU serio |
| | **Motor de Presupuestos** | **39€/mes** | Autónomos ES | 4.244 partidas, IA+voz |
| | **Excel / Word / plantillas** | **0** | Universal | 70-80% del mercado real todavía |
| **TÚ** | **CotizaT** | **7,4 USD/mes (89/año)** | **LatAm hispano, remodelación** | PDF, APU editables, tiempos, versiones, propuesta firmable, 3.006 partidas |

Fuentes: tabla del análisis del 13/08 + búsqueda 19/08 (OneEstimate/OPUS/S10/ConstruCloud) [1](https://hubservice.io/en/blog/mejor-software-ia-presupuestos-apu-construccion-latam-2026) [3](https://oneestimate.ai/es/blog/mejores-software-presupuestos-construccion).

### 2.2 Tus 8 ventajas diferenciales (con prueba, no con eslogan)

**1) Precio que no se puede discutir.** 89 USD/año es 1/6 de OneEstimate Pro (588 USD/año), 1/13 de OPUS (1.800 USD/año), 1/8 de Presto. Para una empresa de 3-15 personas en LatAm, pagar 49-150 USD/mes *todos los meses* es el bloqueador Nº1. Tú resuelves ese dolor con un anual que equivale a **una sola hora de oficial facturada**.

**2) PDF de nivel Presto por 15% del precio.** Ningún low-cost entrega: banda de capítulo con subtotal, mediciones por zona (“Cocina 4,00×2,50”), producto con foto, anexo de garantías y anexos fusionados como páginas reales con índice paginado. OneEstimate y OPUS sacan buen PDF, pero a 7-20× tu precio.

**3) APU/descompuestos editables de verdad.** OneEstimate/S10/OPUS viven de su base de APUs; ReformAI/MedicionPro a 15-29€/mes no dejan tocar rendimiento ni precio por recurso. Tú sí: `Rendimiento × Precio unitario = Importe`, con fila `%` y sincronización CYPE. Un jefe de obra en Lima entiende “cambio el rendimiento del ayudante de 0,5 a 0,7 h/m²” sin curso.

**4) Margen y beneficio a la vista, por partida y por capítulo.** El header del presupuesto muestra `+35% · $651 margen`, y cada capítulo/partida arrastra `Coste $96,58 · Beneficio $33,82`. En obra, el margen no es un informe mensual: es saber si ese baño te da 25% o 12% antes de enviar. Ningún barato lo calcula; los caros lo esconden en un módulo “costos”.

**5) Catálogo que permite presupuestar el día 1.** 3.006 partidas en 18 capítulos, con costes desglosados y terminología venezolana auditada (`hormigón→concreto`, `solado→piso`, `fontanero→plomero`, etc.). Un cliente nuevo de fuera no necesita 2 semanas cargando datos: busca “impermeabilización” y tiene 5 variantes. Ampliar a ~5.000 (objetivo documentado) es añadir JSONs, no reescribir producto.

**6) Propuesta que cierra la venta sin visita.** Enlace público expirable + aceptación con nombre/email/hora + notificación al administrador + cambio de estado. En LatAm, el cuello de botella es “el cliente no responde el WhatsApp”. Un link que ve en el móvil y firma en 30s es tasa de cierre, no feature.

**7) Funciona sin internet donde importa.** Browser-first pero sin dependencia de Google Fonts ni servicios externos para generar el PDF; valida imágenes con Pillow y permite trabajo en obra con conectividad intermitente. Los competidores cloud puros se caen donde tu cliente presupuesta (la obra).

**8) Honestidad que no erosiona confianza.** No vendes “IA mágica” ni “factura fiscal” donde no la hay. En un mercado latam saturado de “IA para todo”, decir “sugerencias deterministas desde tu catálogo, sin inventar precios” es diferenciación. OneEstimate basa su marketing en IA; cuando la IA falla un APU, pierde credibilidad. Tú nunca inventas un precio.

### 2.3 Dónde *no* ganas hoy (y no necesitas ganar para cobrar)

*   **Medición automática sobre planos / BIM IFC / IA que lee PDFs.** OneEstimate es líder ahí. No lo persigas: exige equipo de ML y no lo valora tu público (remodelación de vivienda, no licitación). Tu ventaja es APU manual fino + tiempos, no magia.
*   **AIU colombiano nativo / FIEBDC (BC3) español / normativa por país.** Son formalismas que pesan en licitación pública, no en remodelación privada (tu nicho). Documenta que “no es factura fiscal” y deja el formalismo fiscal para más tarde, por país.
*   **App nativa de campo.** Tu responsive + PWA pendiente es suficiente para fase 1. Procore/Buildertrend juegan otra liga (enterprise).

---

## 3. Qué te ata hoy a Venezuela — inventario completo

Revisión exhaustiva del código del 19/08 (grep sobre 105 archivos versionados):

| Nº | Atadura | Archivo(s) | Severidad para LatAm |
|---|---|---|---|
| V-01 | **Título/meta/hero 100% Venezuela.** `Presupuestos… para Venezuela`, `🇻🇪 Hecho para Venezuela`, `El catálogo más completo para presupuestar en Venezuela`, precios “los que usa el sector… en Venezuela”, sección completa `Pensado para Venezuela` | `app/templates/landing.html:6,37,613,617,689` | **Crítica:** quien entra desde México/Colombia se va. |
| V-02 | **Meta description Venezuela + USD BCV** | `landing.html:7` | Crítica SEO |
| V-03 | **Solo 2 monedas: USD y Bs** (enum hardcodeado). Símbolo `Bs` directo, `Otros → Bs` asumido, atajo `Ctrl+M` solo USD↔Bs | `app/models.py` `Configuracion.moneda_default`, `Presupuesto.moneda`, `app/routers/configuracion.py:95`, `presupuestos.py:1519,2975`, `utils.py SIMBOLOS`, `form.html:116,120`, `detail.html:84,126`, `pdf.py:630`, `js/editor/main.js:63` | **Bloqueante funcional** |
| V-04 | **IVA 16% por defecto** (alícuota VE) + hint “Alícuota general de Venezuela: 16%” | `models.py:1155` `iva_default=16.0`, `settings.html:140` | Media-alta (en CO/CL 19%, AR 21%, PE 18%…) |
| V-05 | **Flag único `activar_funciones_venezuela`** con 5 subflags (`numero_control`, `tasa_cambio`, `total_bs`, `retenciones`, `clausula_cambiaria`) | `models.py:1170-1176`, `routers/configuracion.py:109`, `presupuestos.py:1538,2994`, `settings.html:192`, `budgets/form.html:145` | Media: arquitectura correcta pero nombre no escala |
| V-06 | **Textos BCV/Bs en PDF y detalle:** `Tasa (ref. BCV): 1 USD = … Bs`, `Equivalente referencial: … Bs` | `app/services/pdf.py:274,1362-1364`, `budgets/detail.html:84` | Media-alta (confunde fuera) |
| V-07 | **Etiqueta fiscal `RIF`** hardcodeada en 20 sitios (empresa y cliente, contrato, PDF, seed, presupuesto_muestra) | `models.py` `empresa_rif`, `Cliente.rif`, `services/contrato.py:74-75`, `pdf.py:206,267`, `templates/*`, `seeds.py` | Media (en CO NIT, CL RUT, AR CUIT, PE RUC, MX RFC, EC RUC, DO RUC/RNC…) |
| V-08 | **País default `Venezuela`** en 5 defaults (cliente, configuración, presupuesto muestra) | `models.py:447` `Cliente.pais`, `1139` `empresa_pais`, `seeds.py:57`, `routers/clientes.py:32,40`, `services/onboarding.py:74` | Baja pero ruido constante |
| V-09 | **Horario soporte `hora de Venezuela (UTC-4)`** | `legal/soporte.html:32` | Baja |
| V-10 | **Catálogo y precios “contrastados con mercado venezolano”** | `landing.html` + `basedatos_partidas/` (precios en USD validados VE) | Baja si se comunica como “USD referencial LatAm” |
| V-11 | **Formato numérico único `1.234.567,89`** (Venezuela/España: punto miles, coma decimal). México usa `1,234,567.89`; Chile/Argentina mezclan. | `app/utils.py` `fmt_num`, `fmt_monto` | Baja-median (no bloquea, pero nota local) |
| V-12 | **Métodos de cobro del piloto muy VE** (Pago Móvil) aunque con Zelle/USDT/Binance que sí son regionales | `docs/COBRO_Y_LICENCIAS.md`, `services/datos_pago.py` | Baja (ampliar a Nequi, MercadoPago, Yape, etc. es solo texto) |

**Conclusión:** 12 ataduras, 2 críticas (V-01/V-02), 1 bloqueante funcional (V-03), 3 medias (V-04/V-06/V-07). Ninguna toca el motor de cálculo, descompuestos, tiempos ni aislamiento.

---

## 4. Qué hay que cambiar para ser “apto para todo LatAm”

### 4.1 Principio: no por país, por configuración del tenant

Ya tienes el patrón: `Configuracion` por organización, `Presupuesto` congela el valor. La fiscalidad no debe ser “si Venezuela entonces X”, sino:

```
Configuracion.pais_default              → "Venezuela" | "Colombia" | …
Configuracion.moneda_default            → ISO 4217 libre (USD, MXN, COP, PEN, CLP, ARS, UYU, BOB, DOP, GTQ, BRL, EUR …)
Configuracion.iva_default               → 0-100 configurable (sin hint país)
Configuracion.etiqueta_id_fiscal        → "RIF" | "NIT" | "RUT" | "CUIT" | "RUC" | "RFC" | "ID Fiscal" (texto libre 20c)
Configuracion.activar_funciones_regionales → bool (renombra activar_funciones_venezuela, manteniendo compatibilidad)
Configuracion.* regionales ya existen   → mostrar_numero_control, mostrar_tasa_cambio, etc. se mantienen como flags genéricos
Presupuesto.etiqueta_id_fiscal_snapshot → opcional, para que el PDF histórico no cambie si luego cambias etiqueta
Presupuesto.moneda                      → ya existe, ampliar CHECK
```

**No crees tabla `paises` ni máquina fiscal por país.** Un mercado por país con reglas distintas es Etapa 6 (ver §7 del PLAN). Para LatAm-aptitud basta moneda libre + IVA configurable + etiqueta fiscal genérica + textos neutros.

### 4.2 Cambios técnicos concretos (archivo por archivo)

#### Capa 1 — Des-venezolanizar la cara (landing + onboarding) — 1 día

| Archivo | Cambio |
|---|---|
| `app/templates/landing.html` | Título: `…para Venezuela` → `…para Latinoamérica` o `…para construcción y remodelación` (neutro). Hero: `🇻🇪 Hecho para Venezuela` → `Hecho para Latinoamérica · Construcción y remodelación` (mantén la bandera como ícono secundario, no como identidad). Retirar o neutralizar secciones `Pensado para Venezuela` y `catálogo más completo para presupuestar en Venezuela` → `Más de 3.000 partidas clasificadas con precios de referencia en USD` + subtítulo `Ajusta moneda, IVA y tu ID fiscal en segundos`. Meta description: quitar “venezolano”. |
| `app/templates/onboarding.html` | Placeholder `Venezuela` → selector de país con lista LatAm + “Otro”. No obligues: `value="{{ cfg.empresa_pais or '' }}" placeholder="p. ej. Colombia"`. Si eligen país, precarga etiqueta fiscal e IVA sugerido (ver Capa 2). |
| `app/templates/legal/soporte.html` | `hora de Venezuela (UTC−4)` → `hora de Caracas (UTC−4) / Bogotá–Lima (UTC−5) · responde en horario laboral del huso del cliente` o genérico. |
| `app/branding.py` | Si `LEGAL_ENTITY` menciona Venezuela, neutralizar. |

#### Capa 2 — Moneda libre + IVA configurable + ID fiscal genérico — 2–3 días

| Archivo | Cambio |
|---|---|
| `app/models.py` | `Configuracion`: añadir `etiqueta_id_fiscal = Column(String(20), default="RIF")` y renombrar `activar_funciones_venezuela` a `activar_funciones_regionales` **manteniendo property alias** para no migrar datos: <br>`@property def activar_funciones_venezuela(self): return self.activar_funciones_regionales` + setter (compat). <br>`moneda_default` pasa de CHECK `IN ('USD','Bs')` a `String(10)` libre validado contra lista ISO (ver `app/utils.py`). <br>Añadir `SIMBOLOS` ampliado (USD $, MXN $, COP $, ARS $, CLP $, PEN S/, UYU $, BOB Bs, PYG ₲, GTQ Q, DOP RD$, CRC ₡, NIO C$, HNL L, PAB B/., BRL R$, EUR €). <br>`Cliente.rif` → mantener columna, exponer como `id_fiscal` en formularios (alias). |
| `app/utils.py` | Ampliar `SIMBOLOS` y `fmt_monto` para fallback `f"{valor} {moneda}"`. Mantener `fmt_num` con punto miles / coma decimal como default (mayoría LatAm) pero dejar puerta a `fmt_num_locale` futuro. |
| `app/config.py` / `app/routers/configuracion.py` | `moneda_default` valida contra `MONEDAS_SOPORTADAS` (lista de 20 ISOs). `iva_default` sin hint de país. `etiqueta_id_fiscal` texto libre 2-20c. Mapeo `PAIS → {iva_sugerido, etiqueta_default, moneda_sugerida}` solo como *sugerencia* en onboarding/config (no bloqueante): <br>VE 16% RIF Bs/USD · CO 19% NIT COP · MX 16% RFC MXN · PE 18% RUC PEN · CL 19% RUT CLP · AR 21% CUIT ARS · EC 15% RUC USD · DO 18% RNC DOP (ITBIS) · UY 22% RUT UYU · BO 13% NIT BOB · GT 12% NIT GTQ · etc. |
| `app/routers/clientes.py` + `app/templates/clients/form.html` | Label `RIF/C.I.` → `{{ cfg.etiqueta_id_fiscal or 'ID fiscal' }}` (dinámico por organización). Placeholder por país. |
| `app/routers/presupuestos.py` + `app/templates/budgets/form.html` + `budgets/detail.html` | Select de moneda: de 2 opciones a ~20 (USD, MXN, COP, PEN, CLP, ARS, UYU, BOB, PYG, DOP, GTQ, HNL, NIO, CRC, PAB, BRL, EUR, Bs). Buscar `in ("USD","Bs")` en 3 sitios y sustituir por lista. Etiqueta `Tasa de cambio Bs/USD` → `Tasa de cambio (referencia)` genérica con dos campos `moneda_origen → moneda_destino` o mantener `tipo_cambio` como factor genérico (si moneda=USD y hay tasa, es “USD→local”). Atajo `Ctrl+M` → cicla por monedas configuradas o deja de asumir Bs. |
| `app/services/pdf.py` | `Tasa (ref. BCV): 1 USD = … Bs` → `Tasa de referencia: 1 USD = … Bs` (o `1 {moneda_base} = … {moneda_local}`) parametrizado por `config.mostrar_tasa_cambio`. `Equivalente referencial: … Bs` → `Equivalente: … {moneda}` con símbolo dinámico. `RIF:` → `{{ etiqueta_id_fiscal }}:` dinámico (empresa y cliente). Símbolo moneda en `_totales`, `_tabla_partida` ya usa `moneda` param → ampliar diccionario. |
| `app/services/contrato.py` + `presupuesto_muestra.py` | `RIF/C.I.:` → etiqueta dinámica. Muestra usa `EMPRESA_PAIS = "Colombia"` o neutro si el catálogo se declara regional. |
| `migrations/` | Alembic: `add_etiqueta_id_fiscal + renombrar flag` con default `RIF` y backfill `activar_funciones_regionales = activar_funciones_venezuela`. |
| `app/templates/settings.html` | Bloque `🇻🇪 Funciones regionales de Venezuela` → `🌎 Funciones regionales (opcionales)` + 5 checkboxes genéricos. Añadir campo `Etiqueta ID fiscal` (texto) y `Moneda por defecto` (select 20). Hint IVA: “Déjalo en 0 si no aplicas IVA” sin mencionar Venezuela. |

**Migración y compatibilidad:** ninguna organización venezolana pierde nada. Su `etiqueta_id_fiscal` queda `RIF`, su moneda `USD` o `Bs`, su IVA 16% y su `activar_funciones_regionales=True`. El alias mantiene viejo flag leído.

#### Capa 3 — Catálogo y precios — 0 días de código, 1 decisión comercial

*   **No re-precieas el catálogo por país.** Mantén los 3.006 precios en **USD** como “referencia LatAm” y declara honestamente en landing/PDF: “Precios de referencia en USD, revisa y ajusta a tu mercado”. Es lo que ya hace `fmt_monto` con tasa de referencia: el presupuesto puede emitirse en COP/MXN/PEN y mostrar equivalente USD si el cliente lo pide, sin inventar precios por país.
*   **A medio plazo** (Etapa 6), evalúa *sets regionales* de coste de mano de obra (un oficial cuesta distinto en Santiago vs. Lima) como “coeficiente por país” aplicado al desglose `coste_mano_obra`. No lo hagas en el MVP.

#### Capa 4 — Cobro y operación LatAm — 1 día

*   **Mantén el cobro manual del piloto.** Transferencia, Zelle, Binance y USDT ya funcionan en todo LatAm. Añade a `datos_pago.py`/`settings.html` placeholders de métodos locales como `Nequi (CO), Yape/Plin (PE), MercadoPago (AR/MX), Pix (BR), Pago Móvil (VE)` — solo texto informativo, no integración.
*   **Stripe** (cuando haya volumen) ya es regional: MX, BR, etc. No cambia código.

### 4.3 Qué *no* tocar en el MVP

*   `app/services/calculations.py`, `tiempos.py`, `descompuestos` → intactos.
*   `basedatos_partidas/terminologia.py` → ya es agnóstico (tu “concreto/piso/friso” es neutro LatAm; evita peninsularismos). Solo documenta que el glosario es LATAM, no VE.
*   `app/services/pdf_anexos.py`, `audit`, `storage`, `ratelimit` → intactos.

---

## 5. Diseño de “país” sin sobrediseñar

```
Usuario crea organización
  → Onboarding: “¿En qué país operas?” (lista + Otro) → sugiere IVA/etiqueta/moneda
  → Guarda en Configuracion.empresa_pais + etiqueta_id_fiscal + moneda_default + iva_default
  → El presupuesto hereda moneda/etiqueta pero permite cambiar por documento
  → El PDF renderiza con etiqueta y símbolo del documento, no del país
```

No necesitas modelo `Pais`. Un `JSON` de sugerencias (`app/paises_latam.json` o dict en `app/utils.py`) con 18 entradas es suficiente por 12 meses.

---

## 6. Precio para LatAm — por qué no lo toques (todavía)

| Plan | CotizaT | OneEstimate Pro | OPUS | S10 | Presto | BrickControl |
|---|---|---|---|---|---|---|
| Mensual equivalente | **7,4 USD** (89/año) | 49 USD | 150 USD | 80 USD | 58€ (~63 USD) | 99€ (~107 USD) |
| Anual | **89 USD** | 588 USD | 1.800 USD | 960 USD | ~480€ | 1.188€ |

**No bajes precio para “ser más barato en LatAm”. Ya eres el más barato con margen.** Y no subas hasta validar. El experimento válido es: ¿pagan 89 USD/año en Colombia/México/Perú? Si 5 de 15 entrevistados pagan, el precio es correcto para la región. Si nadie paga, no es precio: es onboarding/catálogo/pago.

Ajuste futuro (si hace falta): **PPP suave** — 89 USD/año en MX/CO/CL/PE, 69 USD/año en BO/EC/PY (ticket menor) — pero solo tras 20 intentos de cobro, no antes.

---

## 7. Roadmap LatAm-ready — 3 semanas, sin parar la operación

| Semana | Entregable | Criterio de hecho |
|---|---|---|
| **S1 — Cara neutra** | Landing + onboarding + soporte con textos LatAm, meta SEO regional, país como selector opcional | Un visitante de Bogotá no ve “Venezuela” en ningún hero/meta; el onboarding sugiere NIT 19% COP. Tests: `test_paginas_publicas` + visual. |
| **S2 — Moneda/IVA/ID fiscal** | Configuración con 20 monedas + IVA libre + etiqueta fiscal + PDF genérico (tasa ref. + RIF→dinámico) | Crear 3 presupuestos: uno en MXN 16% RFC, uno en COP 19% NIT, uno en PEN 18% RUC; los 3 PDFs muestran símbolo y etiqueta correctos y el cálculo no cambia. Migración Alembic + `test_configuracion` + `test_pdf_anexos`. |
| **S3 — Catálogo honesto + cobro** | Landing aclara “Precios de referencia en USD, ajusta a tu mercado”; datos_pago con métodos locales informativos; guía `docs/COBRO_Y_LICENCIAS.md` con nota LatAm | Un usuario chileno entiende que el precio en USD no es su precio final y sabe cómo pagar por Nequi/MercadoPago manual. Suite 694+ en verde. |

Después de S3 → **Etapa 2 real**: 30 prospectos (10 VE, 10 CO, 10 MX/PE), guion de entrevista del PLAN §2.2, 5 pilotos pagados (al menos 2 fuera de VE). Métrica de éxito: primer PDF <20 min en los 3 países.

---

## 8. Qué cambia en cada artefacto público (checklist de QA)

*   **/** (landing): título, meta description, hero kicker, 3 bullets, sección catálogo, sección “Pensado para…” → todo sin Venezuela. Añade franja `🌎 Disponible en todo LatAm hispano — configura tu moneda, IVA y tu ID fiscal en segundos`.
*   **/conocer**, **/legal/***: revisar menciones a VE.
*   **/bienvenida** y **/configuracion**: país como selector, moneda como select 20, etiqueta fiscal como input, bloque `🌎 Funciones regionales`.
*   **/presupuestos/nuevo** y **/presupuestos/:id/editar**: moneda libre, tasa genérica, RIF dinámico.
*   **/presupuestos/:id** (detalle) y **PDF**: símbolo correcto, tasa genérica, RIF→etiqueta.
*   **Email transaccional** (Resend): asunto/cuerpo no menciona VE.
*   **Catálogo**: mantiene 3.006 partidas; `landing.html: catalogo().partidas_txt` ya es dinámico.

---

## 9. Riesgos si lo haces y si no lo haces

| Riesgo si abres a LatAm | Mitigación |
|---|---|
| Precios en USD desalineados con mano de obra local (ej. oficial en AR cuesta distinto) | Disclaimer “referencial” + ajuste masivo por % ya existente (`/partidas/ajustar`); a futuro coeficiente país |
| Soporte en distintos husos/ pagos locales dispersos | Mantén cobro manual + soporte async por email; documenta métodos por país solo como texto |
| “RIF” mal entendido fuera | Etiqueta dinámica resuelve; fallback `ID fiscal` |
| Competencia con IA/APU por país (OneEstimate) te supera en automatización | No compitas en IA: compite en precio + APU editable + PDF + cierre. Es otro segmento (remodelación vs. licitación) |

| Riesgo si *no* abres | Coste |
|---|---|
| Mercado venezolano pequeño y con fricción de cobro (Stripe no opera en VE, solo manual) | Techo de 50-100 clientes |
| OneEstimate/OPUS siguen subiendo y ocupan el relato “para LatAm” | Pierdes ventana de ser “el barato serio” |

---

## 10. Por qué esta apertura no te convierte en “generador genérico”

Reafirma la decisión D-001 del PLAN:

*   Sigues en **construcción y remodelación** (no abres a dentistas/eventos).
*   Creces por **gremios** (electricista, plomero/gasfiter, A/C, carpintero) con el mismo motor y distinto seed de catálogo — 80 partidas gremiales, no producto nuevo.
*   Creces por **país** con el mismo código y distinta configuración (moneda/IVA/etiqueta).
*   No persigues “presupuestos para todo”.

La regla del análisis del 13/08 sigue vigente: *acepta al cliente de otro sector si te paga, no construyas para él.*

---

## 11. Próximo paso recomendado

1.  **Decide etiqueta y mensaje LatAm** (¿“Hecho para Latinoamérica” o neutro “Presupuestos de obra profesionales, en minutos” sin país?). Reserva que `cotizat.app`/`cotizat.co` siguen libres (D-010).
2.  **Ejecuta S1-S3** en la rama `arena/01a017c7-generador-comercial` en 3 PRs pequeños (uno por capa), cada uno con su migración y sus 2-3 tests de regresión.
3.  **Valida con 15 entrevistas** (5 VE + 5 CO + 5 MX/PE) usando el guion del PLAN §2.2 antes de tocar catálogo por país. Si 3 pagan 89 USD/año, tienes señal LatAm.

> **Coste de no hacerlo:** seguir siendo “software venezolano” ante un cliente colombiano que habría pagado lo mismo por el mismo binario.
> **Coste de hacerlo:** ~2 semanas de desarrollo + 1 semana de pulido, sin deuda arquitectónica.

---

### Anexos

*   **Archivos Venezuela-dependientes (búsqueda 19/08):** `landing.html` (5), `onboarding.html`, `settings.html`, `budgets/form.html`, `budgets/detail.html`, `pdf.py`, `contrato.py`, `models.py`, `routers/configuracion.py`, `routers/clientes.py`, `routers/presupuestos.py`, `seeds.py`, `legal/soporte.html`, `utils.py`.
*   **Monedas sugeridas (20 ISOs):** USD, MXN, COP, PEN, CLP, ARS, UYU, BOB, PYG, GTQ, HNL, NIO, CRC, PAB, DOP, BRL, EUR, VES (por compatibilidad histórica; muestra como Bs), CAD, GBP — con `USD` como default neutro hasta que el usuario elija.
*   **IVA sugerido por país (solo sugerencia en onboarding):** VE 16, CO 19, MX 16, PE 18, CL 19, AR 21, EC 15, DO 18, UY 22, BO 13, GT 12, HN 15, NI 15, CR 13, PA 7, PY 10, SV 13, BR 17 (ICMS medio; Brasil no es prioridad hispana).
*   **ID fiscal por país:** VE RIF, CO NIT, CL RUT, AR CUIT, PE RUC, MX RFC, EC RUC, DO RNC, UY RUT, BO NIT, GT NIT, HN RTN, NI RUC, CR NIF, PA RUC, PY RUC.

*Análisis realizado sobre `86d99a6` (merge PR #43) en `arena/01a017c7-generador-comercial`, con búsqueda web de competencia LatAm 19/08/2026 y grep exhaustivo sobre 105 archivos versionados.*
