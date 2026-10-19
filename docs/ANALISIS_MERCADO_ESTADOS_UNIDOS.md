# Análisis de mercado: CotizaT en Estados Unidos

> Argumentación previa a cualquier código. Lo que hay hoy, lo que Estados
> Unidos exige y ningún otro mercado nuestro —lo imperial en cantidades y
> no solo en precios, y un impuesto que no es nacional ni siquiera estatal
> en sus efectos—, y decisiones pendientes. Revisión del repositorio y
> fuentes consultadas el **19-10-2026**.

## 1. Respuesta corta

Estados Unidos **no es cuarto mercado más de la serie IE → AU → CA: es el
único que obliga a tocar la aplicación, no solo los datos**. Los tres
mercados anteriores eran métricos y con un IVA/GST nacional: bastaba una
matriz de precios investigada (Fase 0) y, en Irlanda, un motor fiscal
adicional (Fase 1). Aquí hay tres piezas distintas:

1. **La matriz de precios USD** no presenta ningún problema nuevo: el
   importador ya convierte precios imperiales a la unidad del recurso
   (con tests), la moneda USD = la base del catálogo venezolano, y el
   método IE/AU/CA (salario oficial + «employer cost», materiales de
   comercio, alquileres) se aplica tal cual con datos del BLS.
2. **Las cantidades imperiales NO existen en el producto**. Hoy un
   contratista de Texas ve y escribe m², m³ y litros en el editor, en el
   detalle y en el PDF: el conversor imperial solo actúa al importar
   precios de referencia en el panel. La landing pública afirma lo
   contrario («quantities and prices convert between square feet and
   square metres»), es decir, **la página promete algo que el producto
   no hace** — el mismo problema que tuvo el RCT en la landing de
   Irlanda antes de la Fase 1. Hay que construir la capa de
   visualización/entrada imperial o corregir el texto; no hay tercera
   opción honesta.
3. **El impuesto no se resuelve con un selector de estado a secas**. El
   tipo varía por estado, condado y ciudad (~11.000–13.000
   jurisdicciones), pero además —y esto es lo decisivo— **en la mayoría
   de los estados el contratista no cobra «sales tax» al cliente en
   absoluto**: paga el impuesto al comprar los materiales y la mano de
   obra sobre inmueble no se grava. Un `%` sobre el total estilo IVA
   (lo que hoy hace `impuesto_pct`) es lo correcto solo en un puñado de
   estados con «gross receipts» (Hawái, Nuevo México, Washington,
   Arizona al 65 %). El diseño correcto es **estado de la obra + modo de
   base imponible + tipo editable**, siguiendo el patrón de los motores
   CIS y RCT.

Recomendación: **Fase 0 (matriz USD) primero** — es independiente de las
otras dos piezas y cierra el hueco de precios —, **Fase 1 (cantidades
imperiales en la interfaz)** y **Fase 2 (motor fiscal por estado)**,
corrigiendo la afirmación de la landing de inmediato si la Fase 1 no va
a ser inmediata.

## 2. Dónde estamos hoy en Estados Unidos (auditoría del repositorio, 2026-10-19)

### Lo que ya existe y sirve

| Pieza | Estado | Dónde |
| --- | --- | --- |
| Registro del país (USD, EIN, `sistema_unidades="imperial"`, único imperial de los 23) | ✅ | `app/paises.py` |
| «Sales tax» marcada regional: la landing no afirma un tipo nacional | ✅ | `IMPUESTO_REGIONAL = {"US", "CA"}` en `app/paises.py` |
| Conversión de **precios** imperiales en la importación (ft²→m², gal US→l, yd³→m³, lb→kg…; precio **y rango**; guarda la unidad original) | ✅ con tests (`test_el_importador_convierte_una_matriz_imperial`) | `app/services/unidades_precio.py`, `app/services/importador_precios_mercado.py` |
| `MONEDA_PAIS["US"] = "USD"` en el importador; `TASAS_CORTE["US"] = 1.0` (la base del catálogo ya es USD, así que el factor de familia será precio US ÷ base VE directamente) | ✅ | `importador_precios_mercado.py` |
| Reparto coste materiales/mano de obra en `calcular_totales` (hoy para el CIS) | ✅ reutilizable para el modo «solo materiales» | `app/services/calculations.py` |
| `retencion_pct` («retainage»), `codigo_postal` y `direccion_obra` en el presupuesto | ✅ | `app/models.py` |
| Textos SEO US que describen el impuesto como local y configurable por presupuesto | ✅ (la parte fiscal; la parte de unidades no) | `app/seo_mercados_en.py` |

### Lo que no existe (y la landing dice que sí)

- **Conversión de cantidades**: ningún factor imperial aparece fuera de
  `unidades_precio.py` (grep de `10.7639`, `3.2808`, `0.0929` en app y
  plantillas = vacío). Las 3.006 partidas se miden en m2 (1.278), ud
  (974), m (537), m3 (127), glb (53) y kg (36), y así las ve el usuario
  en todos los países. La FAQ pública responde «Yes» a «Does it handle
  imperial measurements?» y el bloque «Feet, inches and gallons» dice
  que «CotizaT converts the quantity and the price, not just the
  label». **Es falso para las cantidades.**
- **Estado en el modelo de datos**: ni `Presupuesto`, ni `Factura`, ni
  `Configuracion` guardan un estado. El impuesto de un presupuesto
  nuevo sale de `cfg.iva_default` (un % libre de la empresa) y se aplica
  sobre la base total. El bloque US de `PAISES` lleva `iva: 7.0` como
  marcador, y `IMPUESTO_REGIONAL` evita que se lea como tipo nacional,
  pero el *cálculo* sigue siendo «un % sobre todo».
- **Precios por región**: `PrecioRecursoMercado` es único por
  (recurso, país, organización): una matriz nacional + overrides de
  empresa, sin columna de región — igual que AU/CA. La dispersión
  interestatal (salarios ±30 %) debe vivir en `precio_min`/`precio_max`
  y en el override de empresa, no en matrices por estado (ver §5).
- **Trampa de carga SQL**: la ruta `docs/cargar_precios_*` inserta
  `precio` **tal cual**, sin conversión de unidades (la conversión vive
  solo en el importador del panel). Si la matriz US se publicara con
  unidades imperiales en `unidad_fuente` y se cargara por SQL, un
  precio $/yd³ quedaría guardado como $/m³. Consecuencia: **el
  generador US publicará la matriz ya convertida a la unidad del
  recurso** (como hizo Canadá investigando en ft/yd³ y convirtiendo en
  el generador), registrando el formato nativo investigado en
  observaciones. El conversor del importador queda como red de
  seguridad para ficheros del operador, no como parte del contrato de
  la matriz.

## 3. El sistema imperial: por qué «1 m² ≠ 1 ft²» tiene razón y en qué sentido

El ejemplo de la demolición merece descomponerse, porque hay una capa
donde la conversión es exacta y dos donde no lo es:

**Capa aritmética (exacta).** Un rendimiento de 0,35 h/m² y un precio de
10 $/m² convertidos dan 0,0325 h/ft² y 0,93 $/ft²: el importe de la
partida es idéntico. Las APU del catálogo (horas, kg, m³ por unidad de
partida) son relaciones físicas que ya reutilizamos en 23 mercados;
Estados Unidos no las invalida. Por eso **el almacenamiento debe seguir
siendo métrico** (un solo catálogo, un solo motor de cálculo, precisión
sin redondeos acumulados) y la conversión vivir en los bordes —entrada
y presentación—, como en finanzas se guarda la moneda menor y se
formatea al mostrar.

**Capa comercial (no equivalente, y aquí está el trabajo de la Fase 0).**
El mercado americano no vende «por m²»: vende láminas de 4×8 ft, hormigón
por yarda cúbica (con recargo por carga corta), sacos de 80 lb, pintura
por galón, madera por «board foot», techo por «square» (100 ft²),
alquiler por día/semana con tarifas 4 h. Un precio «por m² de
demolición» en EE. UU. además se estructura distinto (la demolición
interior se cotiza mucho a precio cerrado o por ft² según alcance, con
la gestión de escombros —«roll-off dumpster»— como línea propia). La
respuesta del método CotizaT ya está probada (Canadá): **se investiga el
precio en su formato nativo y se convierte a la unidad del recurso con
la fuente citada**; la equivalencia la construye el estudio, no una
regla de tres a la base venezolana.

**Capa de medición del usuario (el hueco real).** Un contratista de
Houston mide «250 sq ft de demolición de tabique» y «12 cubic yards de
hormigón». Si el campo le pide m², o convierte él (mal, un día sí y otro
no) o introduce 250 en un campo de m² y su presupuesto sale **10,76
veces** más grande sin que nada lo avise. Es el error silencioso más
grave posible en el producto, y es el que hay que eliminar: campo en
sq ft con precio $/sq ft, conversión al guardar, y el PDF en las
unidades que el cliente final entiende.

### Opciones

- **A. Solo matriz; la interfaz sigue métrica** y se corrige la landing.
  Honesto pero el producto US queda inutilizable en la práctica
  profesional. Solo defendible como estado transitorio corto.
- **B. Capa de presentación/entrada imperial** condicionada a
  `sistema_unidades == "imperial"` (hoy: solo US). Conversión de
  cantidad y precio unitario en editor, detalle y PDF (y exportaciones
  que muestren cantidades), con el almacenamiento métrico intacto.
  Hereda el conversor de `unidades_precio.py` (hace falta también el
  sentido inverso: de cantidad, no de precio). Esfuerzo medio —
  superficie: `budgets/form`, detalle, `app/services/pdf.py` (+ PDF
  interactivo), y revisión de Excel/BC3 — y es lo único que hace
  verdadera la promesa actual de la landing. **Recomendada.**
- **C. Catálogo imperial nativo** (fork de las 3.006 partidas en ft²,
  LF, CY…). Rompe la arquitectura de catálogo único × mercados y
  duplica el mantenimiento para siempre. **Descartada.**

Nota: no todas las unidades necesitan conversión: `ud` y `glb` (lump
sum) son universales; `h` igual. El mapa es m→ft (LF), m2→sq ft,
m3→cu yd, l→gal (US), kg→lb. Los rendimientos internos (h/m²) se
mostrarían como h/sq ft en vistas de coste si esas vistas se tocan;
decisión de detalle para la Fase 1.

## 4. El impuesto: un selector de estado es necesario, pero no basta

### Cómo se grava de verdad la construcción en EE. UU.

Tres marcos (Avalara, guías estatales de contratistas):

1. **Contratista como consumidor final (la mayoría de los estados**:
   California, Florida, Pensilvania, Wisconsin, Iowa, Kansas,
   Connecticut…). El contratista **paga el impuesto al comprar los
   materiales** y **no cobra «sales tax» al cliente**; la mano de obra
   que mejora un inmueble («real property» / «capital improvement») no
   se grava. En una propuesta CotizaT, lo correcto aquí es «sin línea
   de impuesto» (a lo sumo una leyenda «sales tax on materials included
   in prices»).
2. **Se cobra al cliente según tipo de obra/contrato**: Nueva York y
   Nueva Jersey (reparaciones sí, sobre materiales + mano de obra;
   «capital improvement» exento con certificado ST-124/ST-8), Texas
   (reforma **no residencial** gravada al completo; residencial y obra
   nueva, mano de obra exenta; y el tratamiento de los materiales
   cambia entre contrato «lump sum» y «separated»), Carolina del Norte
   (servicios de reparación/mantenimiento/instalación gravados),
   Colorado (en «time-and-materials» el contratista es minorista y
   recauda sobre los materiales con margen).
3. **Impuesto sobre ingresos brutos del contratista**: Arizona (TPT
   «prime contracting»: base = **65 % de los ingresos brutos**, tipo
   estatal 5,6 % + locales; el MRRA sin modificación queda fuera desde
   2015), Hawái (GET 4 % + recargo condal sobre todo, mano de obra
   incluida, + 0,5 % sobre materiales incorporados), Nuevo México (GRT
   sobre ingresos brutos), Washington («retail sales tax» sobre el
   precio del contrato al consumidor + B&O), Dakota del Sur («contractor's
   excise tax» del 2 %) y Virginia Occidental (servicios gravados salvo
   «capital improvement»).

Tipos 2026 (Tax Foundation, midyear 2026): combinación estatal + local
media ponderada **7,53 %**; máxima media Luisiana **10,13 %**, Tennessee
9,61 %, Washington 9,57 %; **sin impuesto estatal** Oregón, New
Hampshire, Montana y Delaware (Alaska sin estatal pero con locales).
El tipo aplicable es el del **lugar de la obra** («destination
sourcing» en la mayoría de los estados): el estado pertenece al
**presupuesto**, no solo a la empresa.

### Diseño propuesto (patrón CIS/RCT)

- **Estado de la obra** en `Presupuesto` (y `Factura`): selector de 50
  estados + DC, con **estado por defecto de la empresa** en
  `Configuracion` (la mayoría trabaja en un solo estado) editable por
  documento. Requiere migración Alembic + SQL de staging, como la del
  RCT.
- **Modo de base imponible** (`us_tax_base`): `none` (no se cobra al
  cliente — marco 1, con leyenda en PDF), `materials` (solo materiales
  — usa el reparto que `calcular_totales` ya calcula para el CIS, con
  el matiz de aplicar sobre precio de venta de materiales, no coste),
  `full` (materiales + mano de obra), y casos tipo Arizona/Hawái/Nuevo
  México/Washington cubiertos por `full` con **fracción de base**
  configurable (65 % en AZ) — o como modo propio `gross_receipts` si se
  prefiere explícito.
- **Tabla de defaults por estado investigada** (datos, no código
  fiscal): modo por defecto + tipo combinado medio de Tax Foundation
  como punto de partida **editable** (el tipo exacto depende del
  condado/ciudad; no vamos a integrar un servicio tipo Avalara ni
  mantener 11.000 jurisdicciones — fuera de alcance explícito, igual
  que la landing ya dice que «CotizaT does not decide your sales tax»).
- Servicio `app/services/fiscalidad_eeuu.py` simétrico a
  `fiscalidad_reino_unido.py`/`fiscalidad_irlanda.py`: bloque en
  `budgets/form(_en)`, filas en PDF/PDF en línea, leyendas («Sales tax
  (TX, 8.25 %) on materials only»).

Lo que NO debe hacerse: un selector que solo cambie el `%` aplicado al
total (opción «barata»): en ~35 estados eso **cobra al cliente un
impuesto que no existe** y en otros lo calcula sobre la base
equivocada. Sería peor que el campo libre actual, porque llevaría la
etiqueta del estado y parecería correcto.

## 5. Precios: la Fase 0 es la parte fácil (y ya está allanada)

- **«Employer cost»**: BLS OEWS mayo 2025 (publicado 15-05-2026)
  publica medianas nacionales por ocupación: «construction laborers»
  22,66 $/h, carpinteros 29,12, «cement masons» 27,41, electricistas
  30,38, fontaneros 30,67, albañiles de ladrillo/bloque 29,87
  (medias ~10–13 % por encima). Cargas 2026: FICA patronal 7,65 %
  (Seguridad Social 6,2 % hasta base **184.500 $** — no vincula a
  salarios de oficio — + Medicare 1,45 %), FUTA 0,6 % neto sobre los
  primeros 7.000 $ (42 $/año), SUTA estatal (nuevo empleador de
  construcción a menudo alto; Pensilvania 2026: 10,5924 % sobre su base)
  y **«workers' compensation» por clase de riesgo** — la partida que
  más varía entre oficios (cubierta ≠ electricidad) y la que el estudio
  deberá tomar de tarifas NCCI/estatales por código de clase.
- **Sin ancla territorial única**: la dispersión interestatal/metro es
  ±30 % (carpintero: Laredo TX −31 % vs mediana US; metros costeras muy
  por encima). Como en Reino Unido (ONS con Londres en el rango) y
  Canadá (Ontario nacional con BC/Alberta en el rango): **mediana
  nacional BLS como referencia y rango ancho** (−15 %/+35 % orientativo
  a fijar con los percentiles OEWS por estado), documentado. Matrices
  por estado quedan fuera (388×50 referencias inmantenibles y el
  esquema no tiene región).
- **Materiales**: Home Depot/Lowe's (precios sin impuesto — en EE. UU.
  el estante es «ex-tax» por convención, igual que en Canadá), hormigón
  preparado $/yd³ de productores (NRMCA como contexto), alquileres con
  tarifas publicadas (United Rentals publica precios de catálogo por
  día/semana — el equivalente americano de las tarifas HSS/Speedy —
  aunque el precio real se negocia; a documentar como en IE).
- **Formato de matriz**: la de siempre (388 filas, `;`, 16 columnas),
  publicada en la **unidad del recurso** (conversión en el generador —
  ver la trampa SQL en §2 — con el formato nativo investigado en
  observaciones: «lámina 4×8 ft», «$/yd³ → $/m³»). `moneda=USD`,
  `incluye_iva=no` (precios de estante/profesionales sin «sales tax»,
  que además es coherente con el marco 1: el impuesto de materiales lo
  soporta el contratista y **no** forma parte del precio de referencia;
  si se quisiera coste «con impuesto pagado», sería decisión explícita
  del estudio, no por defecto).

## 6. Fases propuestas

| Fase | Contenido | Tipo | Notas |
| --- | --- | --- | --- |
| **0 — Matriz USD** | `tools/coste_empresa_eeuu.py` (OEWS + FICA/FUTA/SUTA/workers' comp), generador, 388 filas, verificador, tests, SQL de carga, docs (investigación + metodología) | Solo datos | Clon del pipeline IE/AU/CA; sin código de app ni migración. Cierra el hueco de precios. |
| **0.1 — Corrección SEO** | La landing/FAQ deja de afirmar conversión de cantidades hasta que la Fase 1 la haga cierta | Textos | Inmediata si la Fase 1 no es inmediata. Sin esto, la página miente hoy. |
| **1 — Cantidades imperiales** ✅ *hecha (19-10-2026, ver §9)* | Capa de conversión en editor/detalle/PDF(s) según `sistema_unidades`; conversor de cantidades (ambos sentidos); tests | Código | Sin migración (derivado del mercado). Hace usable el producto US. |
| **2 — Fiscalidad por estado** | `fiscalidad_eeuu.py`, campos `estado_codigo`/`us_tax_base` (+ default empresa), tabla de defaults por estado, bloque de formulario, PDF, migración + staging SQL, tests | Código + migración | Patrón CIS/RCT. Investigación de los 51 defaults apoyada en guías estatales/Avalara. |

Fuera de alcance en las tres: tipos exactos por ZIP/condado (servicio
externo), certificados ST-124/ST-8 como documentos, «prevailing wage»
(Davis-Bacon) y matrices por estado.

## 7. Recomendación

1. Ejecutar la **Fase 0** ahora (este PR), con la **corrección SEO
   0.1** en el mismo commit o el siguiente.
2. Decidir la **Fase 1** como siguiente bloque de producto: sin ella,
   la matriz USD alimenta presupuestos que un contratista americano no
   puede redactar sin convertir a mano — el mercado seguiría «con
   precios» pero no usable.
3. La **Fase 2** después de la 1, con su investigación de defaults por
   estado como entregable revisable antes de código (como se hizo con
   RCT/CIS).

Decisiones que se someten al usuario: alcance imperial (A/B/C de §3),
diseño fiscal (§4: motor por estado vs selector-% vs statu quo),
ubicación del estado (presupuesto con/sin default de empresa) y orden
de ejecución (§6).

## 8. Lo que NO se ha tocado en el repositorio

Este análisis es solo este documento: no se ha modificado código,
precios, `PAISES["US"]` (sigue `iva: 7.0` neutralizado por
`IMPUESTO_REGIONAL`), plantillas ni la landing (su afirmación sobre
cantidades sigue vigente hasta que se apruebe corregirla). Ninguna
migración nueva.

## 9. Decisiones adoptadas (19-10-2026)

- **Unidades**: opción B de §3 — capa de presentación/entrada imperial
  (cantidades y precios unitarios en la interfaz y el PDF;
  almacenamiento y cálculo métricos). Descartados el statu quo métrico
  y el catálogo imperial nativo.
- **Impuesto**: motor por estado de §4 — estado de la obra + modo de
  base imponible con defaults investigados por estado y tipo editable.
  Descartado el selector que solo precarga un %.
- **Ubicación del estado**: valor por defecto de la empresa
  (`Configuracion`) heredado y editable en cada presupuesto/factura.
- **Orden**: Fase 0 (matriz USD) primero, con la corrección SEO 0.1;
  después Fase 1 (cantidades imperiales) y Fase 2 (fiscalidad por
  estado), en bloques separados dentro de este PR.

**Ejecución (19-10-2026):** la Fase 0 está hecha el mismo día —
`tools/coste_empresa_eeuu.py` (medianas OEWS + FICA/FUTA/SUTA +
workers' comp por clase), `tools/generar_matriz_precios_eeuu.py`, 388
precios USD (52 investigados; factores 1,841 materiales / 2,174
maquinaria), verificador 388/388, SQL de carga generado (pendiente de
ejecutar: fila 19 de `docs/PENDIENTES_OPERATIVOS.md`), 8 tests y los
documentos de investigación y metodología. La matriz se publica en la
unidad métrica del recurso, como recomienda §2 (trampa de la ruta
SQL). La corrección SEO 0.1 también está aplicada: la landing y la
FAQ ya no afirman conversión de cantidades («Prices yes, quantities
not yet»). Pendiente de construir entonces: Fase 1 (cantidades
imperiales) y Fase 2 (motor fiscal por estado).

**Fase 1 ejecutada (19-10-2026):** la capa de cantidades imperiales
está construida el mismo día. Diseño adoptado —**la unidad es la
marca**—: el editor muestra y acepta la unidad de pantalla (`sq ft`,
`ft`, `cu yd`, `gal`, `lb`) como texto libre, con la cantidad
multiplicada por el factor y el precio dividido por él (el importe de
cada línea no cambia); al guardar, el servidor normaliza a métrico
guiándose por la propia cadena de unidad, sin banderas en el
formulario, el borrador del autoguardado ni los packs. El JS del
editor no cambia su lógica (solo la lista de unidades ofrecidas).
Núcleo en `app/services/unidades_precio.py`
(`unidad_mostrada/cantidad_mostrada/precio_mostrado/
rendimiento_mostrado`, `normalizar_partida_a_metrico`,
`ficha_catalogo_a_mostrada`, `receta_a_mostrada/
normalizar_pack_a_metrico`, `es_imperial_config` con la misma puerta
de país que GB/IE). Superficies cubiertas: datos iniciales del editor
y su guardado (crear/editar), índice diferido, hojas del árbol,
buscador y ficha (incl. precios de mercado), «actualizar precio» y
«guardar en catálogo» desde el editor, packs/recetas (coeficientes
reescalados), plantillas, selector de mediciones de plano,
importaciones (un Excel en sq ft no deja el catálogo ni el
presupuesto en imperial; CYPE/BC3 son métricos por formato), detalle
de presupuesto y de factura, versiones, PDF estático **e interactivo**
(la tabla del JavaScript se construye ya en pies: el P.U. se cotiza a
céntimos por sq ft y el documento multiplica exacto consigo mismo),
CSV/Excel del documento y el ejemplo de la landing. Reglas finas: el
precio de cada recurso del APU no se convierte (sigue en $/kg, $/h):
convierte el rendimiento, que es por unidad de partida; las horas por
unidad se mueven igual; la fila «%» no trata su rendimiento como
cantidad pero sí su precio-base; las etiquetas de producto solo
acompañan si eran la unidad de la partida. **Límites deliberados**:
el CRUD de Partidas/Productos/Recursos y la página de descompuesto
siguen en métrico (superficies internas del operador, como el
interior del APU); el BC3 exportado queda en métrico (FIEBDC es un
estándar entre herramientas métricas); los cambios de alcance no
tienen unidad (nada que convertir: cantidad × precio tal cual se
escriben); el copiloto/IA y el pegado de Excel en el navegador
generan líneas rotuladas en métrico que se guardan correctamente y se
enseñan convertidas al reabrir. La afirmación SEO de cantidades
queda restaurada (ahora es cierta). 19 tests nuevos
(`tests/test_unidades_imperiales.py`); suite **1974 passed, 9
skipped**. Pendiente: Fase 2 (motor fiscal por estado).

## Fuentes (consultadas el 19-10-2026)

- Avalara, «Sales tax requirements for construction contractors»
  (marcos estatales; Hawái GET 4 %/0,5 %; Dakota del Sur 2 %; Colorado
  T&M) — avalara.com
- Guías estatales de contratistas: Texas Comptroller (94-116,
  residencial/no residencial), NY (capital improvement ST-124), NJ
  (ST-8), Kansas (KS-1525), Wisconsin (Pub. 207), Connecticut
  (IP 2018(2)), Iowa Contractors Guide — marco «contratista consumidor»
- Arizona DOR, Contracting FAQs y A.R.S. § 42-5075 (TPT «prime
  contracting», base 65 %, MRRA)
- Tax Foundation, «State and Local Sales Tax Rates, Midyear 2026»
  (media combinada 7,53 %; Luisiana 10,13 %; tipos por estado)
- BLS OEWS mayo 2025 (publicado 15-05-2026): medianas nacionales por
  ocupación de construcción; BLS Occupational Outlook Handbook
- SSA/IRS 2026: base salarial Seguridad Social 184.500 $, FICA 7,65 %
  patronal, FUTA 0,6 % neto sobre 7.000 $ (Pub. 15)
- Repositorio: `app/paises.py`, `app/services/unidades_precio.py`,
  `importador_precios_mercado.py`, `calculations.py`, `app/models.py`,
  `app/seo_mercados_en.py`, `tools/generar_sql_precios_pais.py`,
  `basedatos_partidas/datos/partidas.csv`
