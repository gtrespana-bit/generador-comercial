# Análisis de mercado: CotizaT en el Reino Unido

**Fecha:** 2026-10-18
**Contexto:** CotizaT cubre 23 mercados: 18 hispanohablantes (España + 17 LatAm) y 5 anglófonos (US, GB, AU, CA, IE). La traducción del catálogo al inglés está terminada (3.006 partidas, 6.008 cadenas) y el registro británico está resuelto. Antes de invertir en más trabajo de producto (conversiones de unidades, precios, cumplimiento) se analiza si el mercado lo justifica y en qué orden. **Reino Unido es el primero.**
**Alcance:** este documento solo analiza Reino Unido. US, AU, CA e IE tendrán su propio análisis.

---

## 1. Respuesta corta

**Sí, el Reino Unido merece inversión, y es además el mercado anglófono correcto para empezar — pero no por ser el más fácil, sino por ser el que más se reutiliza.** Es el más caro de ganar de los cinco y el más competitivo; lo que inclina la balanza es que su trabajo pesado no se tira:

- El motor fiscal que exige (CIS) es estructuralmente el mismo que Irlanda necesita (RCT, 0 %/20 %/35 % frente a 0 %/20 %/30 %). Se construye una vez y sirve para dos mercados.
- El vocabulario de obra británico ya es la base compartida de GB, IE y AU (177 entradas en `_VOCABULARIO_GB`). Reino Unido es quien lo estrena, pero el coste ya está pagado.
- El sistema métrico del Reino Unido es el de IE, AU y CA. No hay que construir nada.

**Pero hay una condición previa que decide todo y que hoy no se cumple: no tenemos ni un solo precio británico.** El catálogo tiene precios base en USD que el producto convierte por tipo de cambio. En el Reino Unido eso produce cifras incorrectas, no imprecisas: una partida de 15,70 USD/m² se convierte en ~12,40 £/m² cuando el mercado británico paga 40–70 £/m² por un alicatado y 15–25 £/m² por un enlucido. **Un presupuesto británico construido por conversión de divisa hunde el margen del usuario y destruye la confianza el primer día.**

Recomendación: **entrar, pero por la puerta del cumplimiento y no por la de los precios.** Secuencia propuesta en el §7.

---

## 2. Dónde estamos hoy en el Reino Unido (auditoría del repositorio, 2026-10-18)

Lo que **ya está hecho y verificado**:

| Pieza | Estado | Dónde |
|---|---|---|
| Entrada de mercado `GB` | ✅ completa | `app/paises.py` |
| Catálogo traducido | ✅ 3.006 partidas / 6.008 cadenas | `basedatos_partidas/glosarios/EN.excepciones.json` |
| Vocabulario británico de obra | ✅ 177 entradas + 40 ortográficas, 0 duplicados | `app/services/variante_ingles.py` |
| Rótulos de PDF por mercado | ✅ 51 puntos `_rot()` → QUOTE, QUOTE No., QUOTE TOTAL | `app/services/pdf.py` |
| Mensajes de interfaz por mercado | ✅ 295 pares, `mensaje(texto, idioma, mercado)` | `app/i18n.py`, `app/locales/mensajes_en.json` |
| Emails en inglés | ✅ 12 plantillas `_en`, base sensible al idioma | `app/templates/emails/` |
| Plantillas | ✅ todas con variante `_en` (raíz y 15 subcarpetas) | `app/templates/` |
| Landing y SEO de cabecera | ✅ ruta `/gb/` y bloque GB propio | `app/routers/publico.py`, `app/seo_en.py` |

Datos del mercado británico ya correctos en `PAISES["GB"]`: GBP, símbolo £, IVA 20 %, «VAT registration number» (placeholder `GB123456789`), formato `DD/MM/YYYY`, separador de miles coma y decimal punto, locale `en-GB`, ejemplo «London» / «Ltd» / `+44 20 7946 0000`.

Lo que **falta** y condiciona la entrada:

| Hueco | Gravedad | Detalle |
|---|---|---|
| **Precios de referencia británicos** | 🔴 bloqueante | `MONEDA_PAIS` en `app/services/importador_precios_mercado.py` cubre 18 mercados hispanos. **Ni GB ni ningún mercado anglófono.** |
| **Tasa de cambio GBP** | 🔴 bloqueante (aunque insuficiente) | `TASAS_SUGERIDAS` en `app/services/tasa.py` no tiene `GBP`. |
| **CIS (Construction Industry Scheme)** | 🔴 bloqueante para subcontratistas | No existe. El producto no separa mano de obra de materiales en la factura, que es el requisito número uno del CIS. |
| **VAT Domestic Reverse Charge** | 🔴 bloqueante para subcontratistas | No existe. Ver §3.3. |
| **Corpus SEO de larga cola** | 🟠 alto | `app/seo_contenido.py` (1.298 líneas) está claveado **solo** por países hispanos (VE, CO, MX, PE, EC, PA, SV, CL, AR, DO, UY, PY…). `app/seo_articulos.py` (649 líneas): **cero** contenido inglés. Tenemos landing y `seo_en.py`, pero no la máquina de artículos que genera captación orgánica en los mercados hispanos. |
| **Biblioteca de rendimientos y tasas** | 🟠 alto | La mediana del catálogo es 15,70 USD/m², 10,44 USD/m, 19,15 USD/ud. Sin rendimientos británicos (m²/hora por oficio) no hay forma de reconstruir precios. |
| **Alineación NRM2 / SMM7** | 🟡 medio | El catálogo no referencia norma británica de medición. Ver §3.4. |

---

## 3. Datos de mercado

### 3.1 Tamaño y estructura

| Concepto | Reino Unido (2026) |
|---|---|
| Producción del sector | ~142.000 M£ de VAB (2024), ~6 % del PIB |
| Empleo | ~2,07 M de personas (2025, −0,9 % interanual) |
| **Empresas de construcción** | **885.485 — el mayor sector del Reino Unido por número de empresas (~15,6–16 % del total)** |
| Perfil | **99,1 % pymes**; **78,1 % sin ningún empleado** (autónomos) |
| Empresas con IVA/PAYE | ~370.770 (ONS 2024) |
| Tendencia | **~122.000 empresas perdidas desde 2020**; la previsión de producción para 2026 es **contractiva (~−2,5 %)** |
| Detalle de la contracción | vivienda privada −7 %, reforma y mantenimiento −8 %; infraestructura +3,2 % |

**Lectura:** el volumen de empresas es enorme y el perfil dominante (autónomo sin empleados) encaja exactamente con un SaaS de presupuestos de 20–50 £/mes. Pero **el censo de empresas está cayendo y la reforma —nuestro núcleo— es lo que más cae (−8 %)**. Es un mercado grande que se está encogiendo en el segmento donde somos fuertes. Eso no descarta la entrada; sí obliga a no financiarla con optimismo de crecimiento.

### 3.2 Competencia local (precios verificados 2026, £/mes salvo indicación)

| Herramienta | Precio | Posición |
|---|---|---|
| Powered Now | 19–40 £/usuario | Autónomos. **CIS + IVA integrados**, certificados, funciona sin conexión |
| PriceBuilder | 25–45 £ | Móvil, presupuestos en obra |
| QuoteSmith / QuoteBuild | 19–39 £ | Presupuestos ilimitados, control de margen |
| Tradify | 34–44 £/usuario | Gestión de trabajos con presupuestación ligera |
| BuildPartner | 24–122 £ | Tarifas británicas por región |
| Fergus | 35 £ | Costeo de obra en tiempo real |
| PriceAJob | 10–35,95 £ | Nube, precios de material británicos |
| PriceNailer | 29 £ | IA que lee planos |
| The Proper Tool | 29 £ | Ampliaciones y buhardillas, IA, 31 categorías británicas |
| RenoCalc | 4,99 £/presupuesto o 19,99–399,99 £ | IA desde plano, 12 oficios, genera método y contrato |
| EasyEstimate | gratis / 39,99 £ | **Más de 60.000 precios vivos de proveedor** |
| Buildxact | 89–349 £ | Australiana, planes británicos, despiece desde plano, Xero |
| EstimatorXpress (HBXL) | 899–1.299 £/año (~75–100 £/mes) | La más británica: datos profundos, NRM, 6.000+ materiales |
| simPRO | 400 £+ | Equipos de 20+ |
| Causeway / esti-mate | 1.515–2.400 £+ | QS tradicional, escritorio Windows |

**Lectura:** el mercado está **maduro, poblado y barato en la entrada**. Hay al menos quince competidores serios, varios nacidos en el Reino Unido, y la franja 19–45 £/mes está ocupada por herramientas que **ya hacen CIS**. Nuestra ventaja real (catálogo de 3.006 partidas con descompuestos y PDF profesional) no la tiene nadie en esa franja de precio — pero solo si los precios son británicos.

### 3.3 Marco fiscal: lo que el Reino Unido exige y ningún otro mercado nuestro exige

**CIS — Construction Industry Scheme (HMRC).** Retención sobre la **mano de obra únicamente**, excluyendo materiales y excluyendo el IVA:

| Situación del subcontratista | Retención |
|---|---|
| Gross payment status (verificado) | **0 %** |
| Registrado y verificado | **20 %** |
| No registrado o no verificado | **30 %** |

- Tipos sin cambios desde 2007.
- Obligación del contratista: verificar al subcontratista con HMRC antes de pagar.
- Declaración mensual **CIS300**: presentación el día 19, pago el 22. **Las declaraciones nulas vuelven a ser obligatorias desde abril de 2026.**
- **Las facturas deben separar mano de obra de materiales.** Sin esa separación no hay CIS posible.
- Desde el **6 de abril de 2026**, los pagos de administraciones locales quedan exentos de CIS.

**VAT Domestic Reverse Charge (VATA 1994 s. 55A, desde el 1 de marzo de 2021).** Se aplica cuando se cumplen a la vez: ambas partes están registradas en IVA **y** el suministro entra en el ámbito del CIS **y** el tipo es general (20 %) o reducido (5 %) **y** el cliente no es un usuario final que lo haya notificado por escrito. Entonces:

- La factura del subcontratista se emite **sin IVA** (neta).
- Debe llevar una referencia obligatoria: «Reverse charge: VAT Act 1994 Section 55A applies» / «S55A VATA 94 applies» / «Customer to pay the VAT to HMRC».
- Debe indicar el importe o el tipo del IVA.
- El cliente declara y paga ese IVA a HMRC.

**No** se aplica a: usuarios finales, obra nueva residencial (tipo cero), suministro solo de materiales, ni alquiler de andamios sin operador. El umbral de registro en IVA es 90.000 £ (2026/27). Si el usuario final no notifica por escrito, la inversión del sujeto pasivo se aplica por defecto.

**Consecuencia para CotizaT:** el PDF británico necesita **dos bloques que hoy no existen** —una línea de retención CIS sobre la mano de obra, y una declaración de inversión del sujeto pasivo con la referencia legal— y el modelo de datos necesita desglosar mano de obra de materiales en cada partida. Nada de esto existe en el producto hoy.

### 3.4 Medición: métrico, y esto resuelve la conversión de unidades

**El Reino Unido es métrico y no necesita ninguna conversión de unidades.** El programa de metricación se inició en 1965 y cerró con los Reglamentos de Edificación de 1972. La madera pasó el 1 de abril de 1970, el cobre en 1971–72, y el ladrillo métrico (215 × 102,5 × 65 mm) en enero de 1970. La Ley de Pesas y Medidas de 1985 lo consolidó: los materiales de construcción británicos **deben** venderse en métrico; el imperial solo es legal en señales de tráfico, cerveza de barril y metales preciosos. En 2022 el Gobierno consultó revertirlo y recibió un **99 % de rechazo**.

Matices que importan al catálogo, porque el oficio habla imperial aunque el comercio venda métrico:

| Material | Cómo se pide en el Reino Unido | Conversión real |
|---|---|---|
| Madera | «un 4×2 de 3 metros» — **sección imperial nominal, longitud métrica** | 4×2 = 47 × 100 mm (aserrado regularizado) o 38 × 89 mm (CLS) |
| Tableros | todos dicen «8×4» | 2440 × 1220 mm, espesor en mm |
| Ladrillo | métrico | 215 × 102,5 × 65 mm desde 1970 |
| Tubería de cobre | mm | desde 1971–72 |
| Planos y Reglamentos | mm exclusivamente | — |

**Consecuencia directa sobre el trabajo aplazado:** la tarea que habíamos llamado «conversiones de unidades» es, en realidad, **«conversión al imperial para Estados Unidos»**. Cuatro de los cinco mercados anglófonos (GB, IE, AU, CA) son métricos y comparten la base actual. El problema es mucho más pequeño de lo que parecía y **no debe financiarse antes de los precios ni del CIS**.

---

## 4. Norma de medición británica (NRM)

- **NRM1** — estimación de coste y planificación de coste por elementos (RIBA 0–3).
- **NRM2** — medición detallada para obra de edificación; **sustituyó a SMM7**: publicada en abril de 2012, operativa el 1 de enero de 2013, reemplazo formal el 1 de julio de 2013. Reeditada como práctica profesional de RICS en octubre de 2022.
- **NRM3** — mantenimiento y coste de ciclo de vida (RIBA 6–7).

Diferencias que afectan a un catálogo: NRM2 tiene **41 secciones de obra frente a las 22 de SMM7**, elimina buena parte de las reglas de «se considera incluido» (lo que no se describe no está incluido), mide espesores de muro en mm reales en vez de «medio ladrillo» / «un ladrillo», y mide la excavación por profundidad real en tramos de 250 mm.

**Advertencia importante:** RICS ha reconocido que **la adopción real de NRM2 es limitada**. En la práctica, las consultoras que preparan mediciones para contratista principal siguen usando SMM7, mientras que los contratistas que preparan paquetes de oficio usan NRM2 adaptado a su medida. **No basta con declarar «cumple NRM2»**: cualquier afirmación en ese sentido sería falsa hoy y lo más prudente es no hacerla.

---

## 5. Lo que hay que construir

### Fase 0 — Decisión de precios (2–3 semanas, antes de código de producto)

Es el único trabajo que puede tumbar el proyecto, así que va primero y es acotado.

1. Definir la **biblioteca de tasas británica**: rendimientos por oficio (m²/hora, m/hora, ud/hora) y costes de oficial, oficial de primera y peón.
2. Referencias de contraste públicas y de mercado: CIJC Working Rule Agreement (mínimo **13,18 £/hora** para peón general desde el 20 de julio de 2026; tasa de oficio **16,40 £/hora**), salario mínimo legal 12,71 £/hora (21+), y las tarifas de mercado por oficio:

| Oficio | Tarifa/día (mercado 2026) | Londres y sureste |
|---|---|---|
| Peón | 120–180 £ | 130–200 £ |
| Yesero / enlucidor | 180–250 £ | 200–320 £ |
| Electricista | 200–350 £ | 250–380 £ |
| Fontanero | 200–300 £ | 250–380 £ |
| Albañil | 180–280 £ | 230–350 £ |

3. Reconstruir **una muestra representativa** del catálogo (unas 200–300 partidas bien repartidas por capítulos) con esas tasas, y comparar contra dos fuentes de contraste británicas.
4. **Puerta de decisión:** si la desviación respecto al mercado británico es asumible, se financia el resto. Si no, el Reino Unido se queda en espera y los recursos van a otro mercado anglófono.

### Fase 1 — Cumplimiento británico (3–4 semanas)

Es lo primero de producto, deliberadamente, por su reutilización.

1. **CIS**: campo de estado del subcontratista en el cliente (0 %/20 %/30 %), desglose obligatorio mano de obra / materiales por partida, línea de retención sobre la mano de obra en el PDF, y bloque de resumen CIS.
2. **Domestic Reverse Charge**: condición por cliente (usuario final sí/no, con notificación escrita), emisión de factura neta de IVA, y la leyenda obligatoria «Reverse charge: VAT Act 1994 Section 55A applies» con el importe del IVA.
3. Ampliar el modelo de datos para sostener ambos: hoy el producto no separa mano de obra de materiales en el documento, y eso es un cambio estructural, no un rótulo.
4. Tests propios (`tests/test_reino_unido.py`) incluyendo los casos en que **no** aplica DRC: usuario final, obra nueva residencial, solo materiales, andamio sin operador.

### Fase 2 — Precios y divisa (4–6 semanas, condicionada a la Fase 0)

1. Matriz de precios británica sobre la biblioteca de tasas de la Fase 0.
2. `MONEDA_PAIS["GB"] = "GBP"` en `app/services/importador_precios_mercado.py` (hoy solo hay 18 mercados hispanos).
3. `TASAS_SUGERIDAS["GBP"]` en `app/services/tasa.py`, con su fecha y su fuente, como las demás.
4. Implantar el **mecanismo de precios por mercado** si aún no existe: los precios británicos no pueden salir de convertir los USD del catálogo, tienen que ser una tabla propia.

### Fase 3 — SEO de larga cola (2–3 semanas)

1. Contenido británico en `app/seo_contenido.py` y `app/seo_articulos.py`, que hoy no tienen **ni una línea** en inglés. No es find-and-replace: los temas, las palabras clave y las objeciones son distintas (CIS, inversión del sujeto pasivo, NRM, «quote» frente a «estimate»).
2. hreflang `en-GB`, sitemap y JSON-LD con Reino Unido en `areaServed`.
3. Actualizar `LISTADO_ESTADO_PAISES.md` y los tests del selector.

### Fuera de alcance

- **NRM/SMM7 como característica declarada.** No se anuncia conformidad con una norma cuya adopción real es parcial y que nuestro catálogo no aplica.
- **Integración con HMRC** (presentación de CIS300). Se calcula y se documenta; no se envía.
- **Facturación electrónica británica.** CotizaT genera documentos comerciales, no facturas fiscales; se mantiene el criterio actual.

---

## 6. Coste y riesgo

| Riesgo | Gravedad | Mitigación |
|---|---|---|
| **Precios irreales** | 🔴 crítico | Fase 0 como puerta de decisión antes de escribir producto |
| **Censo de empresas a la baja** (−122.000 desde 2020) y **reforma −8 %** | 🟠 alto | No financiar con previsión de crecimiento; el segmento infraestructura (+3,2 %) es el que crece |
| **Competencia abundante y barata** | 🟠 alto | Diferenciarse por catálogo + descompuestos + PDF, no por precio |
| **La franja 19–45 £ ya hace CIS** | 🟠 alto | El CIS deja de ser ventaja: es el precio de entrada, hay que tenerlo el primer día |
| **Reforma y mantenimiento es nuestro núcleo y es lo que más cae** | 🟡 medio | vigilar si el mix británico se desplaza a obra nueva |
| Cumplimiento fiscal cambia (CIS nulas desde abril 2026, exención de administraciones locales desde el 6 de abril de 2026) | 🟡 medio | Reglas en datos, no en código, con fecha de vigencia |

Esfuerzo estimado: **Fase 0, 2–3 semanas; Fase 1, 3–4; Fase 2, 4–6; Fase 3, 2–3.** Total a producto completo: **11–16 semanas**, más la investigación de precios. Es, con diferencia, la apertura de mercado anglófono más cara de las cinco.

---

## 7. Recomendación

**Ir al Reino Unido, en este orden y con una condición.**

1. **Condición: la Fase 0 decide.** No se escribe una línea de producto hasta tener la biblioteca de tasas británica y una muestra de 200–300 partidas reconstruidas y contrastadas. Si el número no sale, el mercado se aplaza y los recursos se van a otro sitio. Es la única pregunta que puede invalidar el proyecto y es la más barata de responder.
2. **Empezar por el CIS, no por los precios.** Es contraintuitivo pero es lo correcto: el CIS es el trabajo más reutilizable de todo el análisis. Irlanda tiene RCT con la misma estructura de tres tramos (0 %/20 %/35 %) y lo heredará casi entero. Los precios británicos, en cambio, no sirven para ningún otro mercado. Además, siete competidores de la franja de entrada ya hacen CIS: no es una ventaja, es el billete de entrada, y sin él no se puede vender a nadie que subcontrate.
3. **Descartar la conversión de unidades como proyecto.** El Reino Unido es métrico. Solo Estados Unidos necesita imperial, y eso es un trabajo contenido y posterior. El análisis de mercado acaba de encoger una tarea que parecía grande.
4. **No reclamar conformidad con NRM2.** RICS reconoce que su adopción es limitada y SMM7 sigue vivo en la práctica. Declarar lo contrario sería falso y detectable por cualquier QS británico.
5. **Financiar con cautela, no con optimismo.** 885.485 empresas y 99,1 % pymes es un volumen enorme, pero el censo cae y la reforma cae un 8 %. El mercado es grande y se está encogiendo justo en el segmento donde somos fuertes.
6. **Revaluar al terminar la Fase 1.** Con el CIS construido, Irlanda pasa a ser marginalmente barata: es el momento de abrirla, no antes.

**Orden propuesto para los cinco mercados anglófonos, sujeto a los análisis siguientes:**
**GB → IE → AU → CA → US.** Reino Unido primero por reutilización (el CIS arrastra a Irlanda, el vocabulario británico ya cubre GB/IE/AU, el métrico cubre IE/AU/CA). Estados Unidos al final: es el único que necesita imperial,impuesto sobre ventas por estado y vocabulario propio, y por tanto el que menos hereda del trabajo hecho.

---

## 8. Lo que NO se ha tocado en el repositorio

Este documento es solo análisis. No se han modificado `app/paises.py`, `app/services/tasa.py`, `app/services/importador_precios_mercado.py`, `app/seo_contenido.py`, `app/seo_articulos.py`, los glosarios, los descompuestos ni los tests. No se ha creado ningún dato de precio británico. El selector sigue con los 23 mercados actuales.
