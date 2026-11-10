# KHC Auto Import — el negocio de importación de coches — 2026-11-09

Análisis del repo `gtrespana-bit/KHC-Auto-Import` (83 MB, el más grande del
portafolio): qué es el negocio, cómo está construido, qué números lo
sostienen, qué se puede decir en público y qué no.

---

## 1. Qué es

**KHC Auto Import** es el negocio de **compra, importación y venta de
vehículos seleccionados en A Coruña y Galicia**: stock nacional y unidades
importadas de toda Europa (Alemania, Francia, Bélgica, Países Bajos, Italia,
Suiza, Austria, Luxemburgo y Portugal), **siempre con garantía mínima de 12
meses por escrito**.

No es una web de anuncios: es una empresa montada como sistema. Un único
despliegue en Vercel sirve **dos aplicaciones** separadas por dominio:

| Aplicación | Quién la usa | Dominio | Tecnología |
| --- | --- | --- | --- |
| **Web pública** | Clientes | `khcimport.autos` | Next.js (App Router), render en servidor |
| **ERP de gestión** | Uso interno diario | `app.khcimport.autos` | React 19 + Vite + Tailwind v4, compilado a `/erp/` |
| **Base de datos** | Ambas | — | Supabase (Postgres + Storage, región UE) con RLS y roles |

El `middleware` reparte por dominio: en el del ERP traduce las rutas a
`/erp/…` (el usuario nunca ve el prefijo) y en el de la web deja el ERP
inaccesible. Un solo proyecto, dos dominios, una base de datos.

**Posicionamiento de la web** (documentado en `docs/14`): la web **no dice
"somos importadores"**. Dice que venden vehículos seleccionados —nacionales e
importados—, que compran donde está la unidad correcta (no solo en Alemania) y
que **todas las ventas salen con garantía mínima de 12 meses por escrito**.

### El negocio real, verificado en producción (10/11/2026)

No es un plan ni una idea: es una **empresa en marcha, de mi propiedad, con
capital propio y con stock publicado**. Estas comprobaciones se han hecho
contra los sistemas reales, no contra el repositorio:

| Comprobación | Dónde | Resultado verificado |
| --- | --- | --- |
| Web pública viva | `khcimport.autos` | **11 vehículos en stock publicado**, con fotos, precio, año, kilometraje, combustible, cambio y país de origen |
| ERP vivo | `app.khcimport.autos` | Login activo, datos alojados en la Unión Europea |
| Despliegue | Vercel, proyecto `khc-import` | Producción en `READY`, rama `main`, cron diario de mantenimiento a las 06:00 |
| Base de datos | Supabase (UE) | Postgres 17 + Storage, RLS y roles owner/manager/sales/accountant |
| Capital propio | Plan de negocio v7 | **41.500 € de caja del negocio** tras costes de arranque, sin financiación externa |
| Local | Análisis de nave | **Nave de 465 m² en O Milladoiro** (Ames, A Coruña), 1.200 €/mes |

**El stock publicado hoy son 11 vehículos, todos importados**: Volvo XC40
(18.500 €), Mercedes-Benz Clase C Estate (23.990 €), Renault Talisman (15.990 €),
Fiat 500X (13.990 €), VW Golf (18.700 €), BMW Serie 3 Touring (17.250 €),
Audi A3 (15.990 €), BMW Serie 1 (12.475 €), VW Golf GTI (18.500 €), Honda
Civic Type R EP3 (25.900 €) y VW Golf GTI Performance (24.850 €). Todos con
etiqueta C y garantía de 12 meses. La web lo dice y es exacto: **la mayor
parte de los coches se venden por encargo**.

**La nave, decidida el 12/10/2026.** 465 m² en el polígono de O Milladoiro
(Ames), a 1.200 €/mes, sustituyendo la de San Marcos porque triplica la
superficie por solo 100 €/mes más: 8 metros de altura libre, patio de maniobra
de 100 m² para camiones, entreplanta de 60 m² con 4 despachos, zona de
exposición interior de 200 m² para 8-10 coches, zona de detallado de 80 m²,
taller técnico de 60 m² con corriente trifásica y sistema BIES. **Reforma de
Fase 1 presupuestada en 5.115,47 €, gastos fijos de 2.098,69 €/mes y 7.604,94 €
el día 1.** La decisión que dejó el plan cerrado fue empezar **sin financiación
y con la reforma aplazada**, para no comprometer la caja de circulante.

**El equipamiento de recepción ya está comprado, con precios reales y
enlace:** scanner bidireccional LAUNCH CRP919E/X BT (368,40 €), medidor de
espesor de pintura GOYOJO GMT-CTG-2 (50,39 €), arrancador de litio 12 V
(57,39 €), pack de 10 informes de historial carVertical (145,08 € con IVA),
tapamatrículas, carpetas y llaveros con la marca, kit de detallado y
tratamiento nano cerámico. **CAPEX del día 0: 822,90 €**, cerrado y con
comprobante.

**Los números del plan están cerrados y son reproducibles** (`datos_nave_milladoiro.py`
es la fuente única de datos): alquiler 1.200 €/mes, fianza de 2.400 € (dos
mensualidades, LAU art. 36.1), gastos fijos de 2.098,69 €/mes con internet
(50 €/mes), fondo de tres meses de 6.296,07 € y **reforma de Fase 1 de
5.115,47 € con IVA**: suelo epoxi 400 m² (905 €), pintura (479 €), iluminación
LED (1.230 €), señalización y cartelería (496,36 €), mobiliario de oficina
(800 €), seguridad (414,99 €) y limpieza, extintores y herramientas (790,12 €).
**La reforma la hace él mismo con su propia mano de obra.** Siete líneas se
aplazan al mes 2 para no comprometer el fondo. **Caja al cerrar el día 1:
6.346,48 €**, es decir, 50,41 € por encima del fondo, con dos coches ya
comprados. A 36 meses el plan proyecta 12 coches y 141.830,56 €, con sueldo
propio desde el mes 6. Hay además un **escalón intermedio (1.5)**: autónomo con
REBU y alta VIES sin local físico por 284,14 €/mes, y un **dossier de aval** con
el plan de viabilidad financiera para el landlord.

**El ciclo real de caja:** entre 28 y 40 días por coche inmovilizado. 36-40
días si baja en camión portacoches (1.000 € + AXA 50,97 €); 28-32 días si
baja rodando, que devuelve el dinero 8 días antes.

**El escandallo a céntimo de las tres unidades del piloto** (lo presenta el
plan como simulación del caso realista, no como ventas ya cerradas):

| Unidad | Compra en Alemania | Coste puesto en A Coruña | Precio de venta | Beneficio neto |
| --- | --- | --- | --- | --- |
| Ford Focus ST 2.3 EcoBoost 280 CV | 17.900 € | 20.710,73 € | 24.490 € | +2.733,42 € |
| VW Golf 7.5 GTI Performance 245 CV DSG | 19.400 € | 22.212,00 € | 26.290 € | +2.970,62 € |
| Porsche Cayenne E-Hybrid / Audi Q7 TFSIe | 29.500 € | 31.339,50 € | 36.900 € | +3.985,80 € |

El coste puesto incluye compra, logística, homologación, ITV de Galicia, IVTM,
DGT, placas, Modelo 576, taller, filtros, anuncios y detallado.

---

## 2. Las dos fases

### Fase 1 — Prueba de concepto (validación con 3 vehículos)

Operar **como particular**: compra a nombre propio en Europa, matriculación en
la DGT de A Coruña, venta a compradores finales en Galicia. En esta fase se
opera **sin local**, enseñando los vehículos con cita previa en A Coruña: el
alquiler se aplaza hasta que la rotación lo justifique, no antes.

- **Tributación limpia:** ganancia patrimonial declarada en el IRPF anual
  (base imponible del ahorro) y liquidación previa de los impuestos obligatorios
  (Modelo 576 de la AEAT, IVTM del Concello de A Coruña, ITV de importación).
- **Objetivos de validación:** conocer al céntimo los costes reales de
  importación; medir los tiempos reales de rotación; saber qué segmentos,
  motorizaciones y etiquetas ambientales tienen más salida; y optimizar el
  embudo local (Coches.net, Wallapop, Milanuncios, contactos de confianza).

### Fase 2 — Escalamiento profesional (empresa y local)

- **Alta en el IAE** (Comercio al por menor de vehículos) como autónomo o S.L.
- **Régimen REBU:** IVA únicamente sobre el margen, no sobre el importe total.
- **Showroom ya decidido:** nave de **465 m² en O Milladoiro (Ames, A Coruña)**,
  1.200 €/mes, 8 m de altura libre, 100 m² de patio de maniobra, 200 m² de
  exposición interior para 8-10 coches, taller de 60 m² y entreplanta de 60 m²
  con 4 despachos. Reforma de Fase 1 presupuestada en **5.115,47 €** y gastos
  fijos de **2.098,69 €/mes**, con la reforma aplazada para no tocar la caja de
  circulante.
- **Financiación propia:** decisión del 12/10/2026 de empezar **sin
  financiación**, con capital propio y la caja del negocio en 41.500 € tras
  costes de arranque.
- **Garantía comercial** respaldada por pólizas de garantía mecánica
  profesional (GarantiPLUS, Atlántica) sobre la garantía legal del RDL 1/2007.

**Criterios de activación de Fase 2 (marcados como cumplidos en el repo):**

| Criterio | Estado |
| --- | --- |
| 3 vehículos vendidos con éxito, con rotación objetivo < 35 días/unidad | ✅ |
| Beneficio neto medio > **2.000 €/unidad** tras gastos e IRPF | ✅ |
| Cartera consolidada: transportista habitual, ingeniero de fichas reducidas, taller de revisión, centro de detallado | ✅ |
| Capital circulante de **45.000–65.000 €** para mantener 3-5 unidades simultáneas | ✅ |

---

## 3. El ERP: 15 módulos hechos para el día a día

| Módulo | Qué hace |
|---|---|
| **Cuadro de mando** | Caja, capital en stock, beneficio neto, impuestos pendientes, avisos operativos y cobros/pagos a 90 días |
| **Flota y stock** | Cada vehículo con su coste real, estado en un flujo de 10 pasos, documentación y margen neto; vista tabla y tablero |
| **Catálogo** | **1.104 variantes de 37 marcas** con fiabilidad de motor, precio de compra (DE) y venta (ES), **con el origen de cada cifra declarado**, y rotación |
| **Simulador de importación** | Coste total desglosado, impuestos exactos, precio sugerido, punto de equilibrio y análisis de sensibilidad |
| **Clientes y ventas** | CRM con fases, embudo, presupuestos y tareas con vencimiento |
| **Contabilidad** | Cobros y pagos de vehículo y de estructura, resultados por meses, tesorería y rentabilidad por marca, modelo y segmento |
| **Impuestos** | Calendario fiscal generado con los datos reales (576, 06, 620, 303, 349, 390, 130, 202, 200, 100, IVTM, RETA) con control de presentación |
| **Facturación** | Numeración correlativa, desglose según régimen (REBU / general / particular), mención legal obligatoria, imprimible en PDF |
| **Anuncios** | Generador de textos listos para Wallapop, Milanuncios y Coches.net con los datos reales de la ficha y control del límite de caracteres |
| **Documentación** | 15 documentos por vehículo (8 obligatorios) y expediente imprimible |
| **Fotos** | Galería por vehículo en IndexedDB (redimensionada a 1.600 px), foto principal y orden, visible en la flota y reutilizable en el anuncio |
| **Informes** | Cuenta de resultados, valoración de stock, carga fiscal y evolución mensual, imprimibles en PDF |
| **Publicación web** | Botón **Publicar en la web** por ficha: contenido comercial, fotos sin EXIF y con la matrícula tapada, vista previa y aviso de desincronización si cambia precio o km |
| **Contactos web** | Bandeja de los formularios de la web (llamada, WhatsApp, correo, alta en el CRM y seguimiento) |
| **Ajustes** | Empresa, régimen fiscal, tarifas editables del ejercicio, respaldo de datos y **fuentes de cada cifra** |

Extras: roles `owner` / `manager` / `sales` / `accountant` con seguridad por
filas (RLS); **modo local con IndexedDB** cuando no hay credenciales (con
respaldo JSON exportable); PWA instalable y sin conexión; financiación al
comprador con sistema francés, entrada, plazo y comisión de intermediación
registrada como ingreso; botones de WhatsApp y email con el mensaje de
seguimiento ya escrito.

---

## 4. El activo más defendible: el motor de precios con fuentes

Los precios **no son una fórmula inventada**. Cada horquilla declara su
origen en la ficha y la interfaz lo muestra.

| Origen del precio | Qué significa | Cobertura |
| --- | --- | --- |
| **Ajustado a anuncios** | Regresión sobre anuncios reales, por año, motor, combustible y km | 78 compra · 76 venta |
| **Contrastado con anuncios** | Cuantiles de anuncios de esa motorización | 20 compra · 15 venta |
| **Anuncios de la generación** | Extrapolación ajustando por potencia | 29 compra · 14 venta |
| **Estimación del modelo** | Curva de depreciación recalibrada contra lo verificado | 876 compra · 898 venta |

- **Evidencia:** 474 observaciones con fuente, URL, año, km, motor y precio,
  capturadas el **24/09/2026** en Mobile.de, AutoScout24.de, coches.net,
  Autocasión, Coches.com, Autohero, HR Motor, AutoUncle, Spoticar,
  autoanzeigen.de, Wallapop, Milanuncios y Ocasionplus.
- **Modelo ajustado:** mínimos cuadrados sobre
  `ln(precio) = β_grupo + α·(año−2019) + γ·(km/1000)`, con grupo =
  marca + modelo + generación + combustible + franja de potencia (25 CV).
  Si un grupo tiene pocos anuncios se sube un nivel (generación → modelo) para
  no ajustar ruido. **Calidad actual: R² 0,892 en compra y 0,892 en venta**,
  dispersión σ ≈ 8,8-9,1 %.
- **Sin extrapolaciones a ciegas:** fuera del rango observado (años 2014-2025,
  13.700-229.000 km) no se aplica la regresión.
- **Auditoría reproducible:** `npm run prices:check` reproduce los **474
  anuncios uno por uno** con su año, motor y km (error mediano 5,5 %; 9 de cada
  10 por debajo del 16 %) y **aborta** si una horquilla es incoherente, si un
  motor de más potencia se tasa por debajo, si un anuncio cae fuera de años o
  combustible de su generación, o si una ficha curada contradice el catálogo.
- **Limitación declarada:** el modelo usa un único PVP por generación, así que
  en generaciones con motores muy distintos (Corolla gasolina vs. híbrido) y
  sin anuncios propios puede equivocarse en torno a un 25 %. Por eso esas
  fichas van marcadas como «estimación del modelo» y no como dato verificado.
- **Cero extrapolaciones en los límites:** fuera de rango se usa el modelo
  calibrado, nunca la regresión.
- **Calibración:** donde no hay anuncios, el modelo no usa nivel de precios
  propio: se multiplica por el factor que lo alinea con lo verificado
  (compra ×1,165, venta ×1,035) y, en venta, por la corrección del
  diferencial ES/DE de ese modelo.

**Scrapers propios en el repo:** `data/autoscout-es`, `data/autoscout`,
`data/milanuncios`, `data/mobilede` (con `progress.jsonl` y `report.txt`) y un
workflow de GitHub Actions para Milanuncios, cuya web bloquea con captcha pero
expone una API de búsqueda pública.

---

## 5. El motor fiscal: tarifas de 2026, no orientativas

| Concepto | Valor 2026 |
| --- | --- |
| Tasa 1.1 DGT | 99,77 € |
| ITV Galicia | 43,76 € / 52,30 € (IVA incluido) |
| Ficha técnica | 80,29 € |
| IEDMT por tramos de CO₂ | 0 % / 4,75 % / 9,75 % / 14,75 % |
| ITP Galicia (Mod. 620, ATRIGA) | 8 % |
| IVTM A Coruña (Ordenanza Fiscal nº 52) | 19,50 / 62,62 / 132,19 / 179,20 / 224,00 €, con bonificación del 60 % para bajas emisiones |
| IVA | 21 % (REBU: 21 % sobre el margen) |
| IRPF base del ahorro | 19-30 % |
| IS 2026 | 25 % / 23 % ERD / 19 % + 21 % microempresa |

**Lo que no se ha podido verificar contra fuente oficial** (cuotas exactas de
autónomos por tramo, escala autonómica gallega del IRPF, bonificación del ITP para
eléctricos) está **marcado como estimación dentro de la propia aplicación** y
listado en *Ajustes → Fuentes y verificación*. Esa Transparency es la misma
política que aplica CotizaT: cada cifra con su fuente y su fecha.

---

## 6. La estrategia de mercado: no se compra por moda

La matriz de modelos ganadores y prohibidos se apoya en cuatro factores
**gallegos**, no en cuatro factores

1. **Orografía accidentada** → motores con buen par (diésel 2.0, híbridos con
   empuje inmediato); los gasolina atmosféricos pequeños sufren y se deprecian.
2. **Clima atlántico** (humedad y lluvia) → tracción total (AWD-i, 4Motion,
   xDrive, 4MATIC, 4x4) y carrocerías familiares/aventura (wagon, SUV, combi).
3. **Restricciones ZBE** (A Coruña y Vigo) → demanda creciente de **Etiqueta
   ECO** (híbridos Toyota, microhíbridos Hyundai/Kia MHEV 48V, GLP).
4. **Cultura del ocio y del trabajo rural/costero** → furgonetas mixtas combi
   (surf, playa, ciclismo, obras) y 4x4 para el interior rural.

### 6.1 El ranking medido con 56.969 anuncios reales

Generado por `scripts/opportunities.mjs` sobre **56.969 anuncios**
(46.397 de Alemania, 10.572 de España), todos llevados al mismo año y km, con
beneficio neto en REBU **después de** transporte, ITV, impuesto de
matriculación según CO₂, DGT, gestoría, preparación, garantía e IVA del margen.

| Veredicto | Grupo | Compra DE (empresa) | Beneficio empresa | ES sobre DE | Fiabilidad |
| --- | --- | --- | --- | --- | --- |
| 🟢 Muy rentable | Porsche Macan (95B) Gasolina ~252 CV · 2018 · 98k | 28.513 € | **7.391 €** (23 %) | +22 % | ✅ alta (47 anuncios) |
| 🟢 Muy rentable | Mercedes-Benz CLA (C118) Diésel ~150 CV · 2022 · 95k | 19.340 € | **6.157 €** (28 %) | +28 % | ✅ alta (127) |
| 🟢 Muy rentable | Audi Q5 (FY) Diésel ~204 CV · 2023 · 71k | 29.538 € | **4.986 €** (15 %) | +17 % | ⚠️ media |
| 🟢 Muy rentable | Mercedes-Benz Clase E (W213) Diésel ~194 CV · 2018 · 146k | 19.344 € | **4.429 €** (21 %) | +19 % | ✅ alta (114) |
| 🟢 Muy rentable | VW Golf (VIII) Diésel ~150 CV · 2022 · 88k | 17.154 € | **3.898 €** (20 %) | +23 % | ✅ alta (118) |
| 🟢 Muy rentable | BMW Serie 1 (F20 LCI) Diésel ~116 CV · 2018 · 135k | 8.480 € | **3.194 €** (31 %) | +44 % | ✅ alta (36) |

Los escenarios que calcula el ERP son cuatro: **empresa** (compra en el 10 %
más barato de Alemania con 5 % de descuento negociado, venta al precio
mediano español), **realista** (25 % más barato), **medio** (mediana contra
mediana) y **prudente** (compra barata y venta en el 25 % más barato de
España, para vender rápido). La **fiabilidad** se exige con un mínimo de 15
anuncios en Milanuncios y Wallapop; por debajo de 8 no se muestra beneficio.

---

## 7. La web pública

- Catálogo de vehículos, fichas con galería, cómo trabajamos, **página de
  garantía**, búsqueda por encargo, compra de vehículos usados y captación.
- **Procedencia visible:** cada ficha declara si es nacional o importada (y de
  qué país), con filtro y datos estructurados `countryOfOrigin` para Google.
  Si una ficha no trae país, la web **no afirma** que sea importada.
- **Frontera de datos real:** la web no lee la tabla de vehículos; lee
  `publications`, con solo los campos publicados (sin costes, márgenes, VIN ni
  matrícula) y las fotos de un bucket público.
- **Sin credenciales de Supabase**, la web arranca en **modo demostración**
  (datos de ejemplo y `noindex`), ideal para trabajar el diseño.
- Sistema visual centralizado: tinta, marfil y dorado champán, titulares en
  serif, filetes finos.

---

## 8. Los 17 documentos de negocio

En `docs/`: guía práctica de importación en A Coruña (matrículas provisionales,
ITV, DGT), fiscalidad y legalidad particular vs. empresa, estudio de mercado y
modelos top en Galicia, modelos de contratos y plantillas (compraventa, recibos
de reserva, cláusulas de vicios ocultos), roadmap de Fase 2, guía de motores
(fiabilidad y rotación, con lista negra: PureTech, BlueHDi, 1.2 TCe, EcoBoost
pre-2020, N47, Ingenium), matriz de modelos ganadores vs. prohibidos, manual de
uso del ERP, base de datos y usuarios, **oportunidades medidas**, captura de
precios y ranking, web pública y publicación, despliegue y captación, identidad
web y posicionamiento, manual de la web pública, y **auditoría fiscal de
importación por tres vías**.

**Calidad técnica:** 74 aserciones (`npm run check`) sobre el motor fiscal,
económico, de facturación, plantillas y web; `npm run catalog:stats` para la
integridad del catálogo; `npm run smoke` monta 39 vistas con 3 escenarios de
datos; cron diario a las 06:00 contra `/api/keepalive` para que el proyecto
gratuito no se pause.

---

## 9. Cuestiones abiertas (las que el propio repo admite)

1. **El diferencial España/Alemania no está medido con precisión.** Comparando
   anuncios sueltos sale paridad, pero esas parejas no tienen el mismo motor ni
   acabado. En las 142 fichas con anuncios propios el catálogo da una venta
   ~18 % por encima de la compra; en las 861 estimadas, ~30 %. Se intentó
   corregir con la primera cifra y el 94 % del catálogo pasaba a dar pérdidas,
   así que **ninguna corrección global se aplica**. Consecuencia práctica: el
   beneficio de las fichas con anuncios (mediana ≈ 150 € en REBU) es el que se
   apoya en precios reales; el de las estimadas (mediana ≈ 1.470 €) puede estar
   sobrevalorado.
2. **El margen depende del kilometraje más que del modelo.** Dos de los
   «ganadores» de la matriz dan pérdidas al kilometraje de referencia.
3. **El régimen de particular tiene techo.** Tres vehículos es una prueba; para
   un volumen sostenido hace falta la Fase 2 (IAE, REBU, showroom, 45-65 k€ de
   circulante), y eso tiene un coste y un calendario.
4. **Las tarifas no verificadas están marcadas como estimación**, lo cual es
   correcto, pero significa que hay que comprobarlas antes de declarar.
5. **El repo se lee mejor que el negocio:** el sistema está más adelantado que
   la operación. El valor de este proyecto es la infraestructura de decisión;
   el negocio se activa cuando hay stock y capital.

---

## 10. Qué se puede decir en público (y qué no)

### 10.1 Se puede decir (verificable en un clic)

- Que es un negocio de **compra, importación y venta de vehículos seleccionados
  en A Coruña y Galicia**, con garantía mínima de 12 meses por escrito.
- Que compra en Europa **y también nacional**, según dónde esté la unidad
  correcta, y que no todo el stock es importado.
- Que el sistema de gestión es propio: web y ERP en un solo despliegue, con
  catálogo de 1.104 variantes, simulador de importación con impuestos
  verificados, CRM, facturación por régimen, calendario fiscal y publicación
  web en un clic.
- Que los precios se calculan sobre **anuncios reales** con la fuente declarada,
  con un modelo de regresión auditado (R² 0,89) y una auditoría que reproduce
  cada anuncio.
- Que hay una web pública y una app interna, y que la web solo publica
  contenido comercial: nunca costes, márgenes, VIN ni matrícula.
- La garantía de 12 meses, el sistema de referencias y las relaciones con
  talleres, transportistas e ingenierías.
- **Que hay stock real disponible ahora mismo**: 11 vehículos publicados en la
  web con fotos, precio, kilometraje y país de origen. Es comprobable en un
  clic y es el mejor argumento de venta que existe.
- **Que el negocio es físico y propio**: nave de 465 m² en O Milladoiro
  (Ames, A Coruña), con taller propio, zona de exposición y entreplanta de
  oficinas, y reforma hecha con mano de obra propia.
- **Que el capital es propio y el arranque está cerrado**: el equipamiento de
  revisión está comprado y el modelo financiero va al céntimo.

### 10.2 No se dice

| No se publica | Motivo |
| --- | --- |
| **Proveedores concretos y rutas de compra** | Es el activo más sensible: si un competidor sabe a quién compras y a qué precio, se acaban los 2.000 €/coche |
| **El % de margen por modelo y por compra** | El repo lo tiene marcado como dato interno; en la web solo aparece el resultado final |
| **Las tarifas exactas de cada compra** | La web pública no muestra costes ni márgenes, y esa frontera está en el esquema de datos |
| **Matrículas, VIN y fotos sin tapar** | El propio ERP las enmascara al publicar |
| **La discrepancia entre fichas verificadas y estimadas** | Es una limitación interna, no un argumento de venta |
| **Que la Fase 1 es "vender como particular"** | Es una decisión fiscal interna. En público: "operamos en el marco legal que corresponda en cada fase" |
| **Cifras de facturación o de unidades vendidas** | No hay dato público que las sostenga |
| **Los proveedores de garantía (GarantiPLUS, Atlántica)** | Se pueden mencionar como cobertura, pero no usarlo como referencia comercial sin acuerdo |
| **El desglose económico interno**: capital, fianza, desglose de la reforma, fondo, flujo diario y proyección a 36 meses | Son datos financieros de la empresa, no argumentos de venta. En público, la existencia del local y del capital propio |
| **El dossier de aval y el plan de viabilidad para el landlord** | Documento interno para el propietario, con cifras de la empresa. No es material público |
| **Datos personales de la socia, de la familia y del equipo** | La carpeta `plan-negocio/` incluye un estudio de carga familiar y despachos con nombres; nada de eso se publica |

### 10.3 El bloque de descripción listo para copiar

**ES — largo**

```
KHC Auto Import es mi negocio de compra, importación y venta de vehículos
seleccionados en A Coruña y Galicia. Compramos donde está la unidad correcta
—no solo en Alemania, sino también en el mercado nacional— y todas las
ventas salen con garantía mínima de 12 meses por escrito. Tengo stock real
disponible ahora mismo y una nave de 465 m² en O Milladoiro con taller
propio.

Detrás hay un sistema propio, no una hoja de cálculo: un ERP de gestión con
catálogo de más de mil variantes, simulador de importación con los impuestos
verificados del ejercicio, CRM, facturación por régimen, calendario fiscal y
publicación en la web en un clic; y una web pública que solo muestra contenido
comercial.

Los precios no son suposiciones. Se calculan sobre anuncios reales de
Anuncios de Alemania y España, con la fuente declarada en cada ficha, un
modelo de regresión auditado que reproduce anuncio por anuncio, y un ranking de
oportunidades sobre más de cincuenta mil anuncios que dice qué segmentos
rentabilizan y cuáles no.
```

**ES — corto (para directorios, notas de prensa o firma)**

```
KHC Auto Import: mi negocio de importación y venta de vehículos seleccionados
en A Coruña y Galicia, con garantía mínima de 12 meses, stock real disponible
y nave propia con taller. Sistema de gestión propio, precios calculados
sobre anuncios reales y web pública sin excedentes.
```

**EN — largo**

```
KHC Auto Import is my own business: buying, importing and selling selected
vehicles in A Coruña and Galicia. We buy where the right car is —not only in
Germany, but also on the national market—and every sale carries a minimum
12-month warranty in writing. We have real stock available now and our own
465 m² workshop with a service bay in O Milladoiro.

Behind it is our own system, not a spreadsheet: an operations ERP with a
catalogue of more than a thousand variants, an import simulator with the
current year's verified tax rates, a CRM, invoicing by regime, a tax
calendar and one-click publishing to the public site; plus a public site that
shows commercial content only.

Prices are not assumptions. They are calculated from real listings in Germany
and Spain, with the source declared on every record, an audited regression
model that reproduces each listing one by one, and an opportunity ranking
built from more than fifty thousand listings that tells you which segments
pay and which do not.
```

**EN — corto**

```
KHC Auto Import is my own business: importing and selling selected cars in
A Coruña and Galicia, with a minimum 12-month warranty, real stock available
and our own workshop. In-house management system, prices calculated from real
listings, and a public site with no excess information.
```

---

## 11. Fuentes

- Repo `gtrespana-bit/KHC-Auto-Import`: `README.md`, `docs/01` a `docs/17`,
  `erp/src/data/catalog/marketEvidence.js`, `erp/src/data/catalog/priceModel.js`,
  `scripts/opportunities.mjs`, `data/autoscout*`, `data/milanuncios`,
  `data/mobilede`, `app/`, `erp/src/components/`.
- Plan de negocio (carpeta interna `plan-negocio/`): `README.md`,
  `01_PRESUPUESTO_ARRANQUE_Y_ASIGNACION_CAPITAL.md`,
  `02_ESCANDALLO_UNITARIO_Y_GASTOS_POR_COCHE.md`,
  `03_PLAN_FINANCIERO_PILOTO_Y_FLUJO_CAJA.md`, `ANALISIS_NAVE_SANTIAGO_MILLADOIRO.md`,
  `RESUMEN_CAMBIOS_NAVE.md`, `REFORMA_FASE1_COMPLETA.md`,
  `datos_nave_milladoiro.py`, `DOCUMENTOS LEGALES KHC IMPORT/`.
- **Verificado en producción el 10/11/2026**: web pública `khcimport.autos`
  (11 vehículos en stock publicado), ERP `app.khcimport.autos` (login activo),
  despliegue de Vercel en estado `READY` con cron diario, dominios
  `khcimport.autos`, `www`, `app` y `khc-import.vercel.app`.
- Descripción pública de Rubén: `docs/DESCRIPCION_PUBLICA_RUBEN_2026-11-09.md`.

> ⚠️ **Aviso de exposición (10/11/2026):** el repositorio `KHC-Auto-Import` es
> **público**, y la carpeta `plan-negocio/` —marcada como confidential, con el
> capital, la fianza, el desglose de la reforma, el dossier de aval y datos
> personales del equipo— está **leíble públicamente en GitHub**. El
> `.vercelignore` solo la excluye de los despliegues web; no protege el
> repositorio. Y aunque se borrara ahora, seguiría en el historial de Git.
> Antes de publicar nada sobre este negocio hay que mover esa carpeta a un
> repositorio privado (o a una rama privada) y rotar el historial.
