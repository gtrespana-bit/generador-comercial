# Investigación — defaults fiscales por estado (EE. UU.)

Fecha de corte: **2026-10-19**. Entregable de la Fase 2 de Estados Unidos
(motor fiscal por estado): la tabla de valores por defecto que usa
`app/services/fiscalidad_eeuu.py`. El contexto y las decisiones están en
`docs/ANALISIS_MERCADO_ESTADOS_UNIDOS.md` §4 y §9; esto es la evidencia
estado a estado.

## Qué se está fijando y con qué criterio

Para cada estado (+ DC) el motor necesita dos valores por defecto:

1. **Modo de base imponible** (`us_tax_base`): sobre qué se aplica el tipo
   cuando el contratista cobra al cliente.
   - `none` — no se cobra impuesto al cliente (el contratista es
     «consumidor final»: paga el impuesto al comprar los materiales y la
     mano de obra sobre inmuebles no se grava).
   - `materials` — se cobra sobre el precio de venta de los materiales.
   - `labor` — se cobra solo sobre la mano de obra/servicios.
   - `full` — se cobra sobre el precio completo (materiales + mano de obra).
   - `gross_receipts` — impuesto sobre ingresos brutos del contratista,
     con fracción de base configurable (Arizona grava el 65 %).
2. **Tipo de partida**: el tipo combinado estatal + local medio
   (ponderado por población) de **Tax Foundation, «State and Local Sales
   Tax Rates, Midyear 2026»** (1-jul-2026). Es un punto de partida
   editable: el tipo exacto depende del condado/ciudad de la obra y
   CotizaT no mantiene 11.000 jurisdicciones (fuera de alcance, §4 del
   análisis).

**Criterio del default**: el tratamiento de la obra típica de CotizaT —
una **reforma/mejora de un inmueble para su propietario**, con precio por
partidas. Donde el estado distingue por tipo de obra (mejora capital vs
reparación; residencial vs no residencial), el default es la rama
«mejora» y la nota dice cuándo cambiar el modo. El motor nunca decide
por el usuario: propone el default, imprime la nota y deja cambiar modo,
tipo y fracción en cada documento.

## Verificación

- **Verificado contra la guía oficial del estado** (o norma citada):
  AZ, CA, CO, CT, DC, HI, IA, KS, MS, NE, NM, NC, SD, TX, WA, WV, ID, FL.
- **Marco general** («en la mayoría de los estados el contratista es
  consumidor de los materiales y no recauda sobre la obra», Avalara /
  Wolters Kluwer, con la lista cerrada de excepciones): el resto. Las
  listas de excepciones de ambas fuentes coinciden (minoristas en
  AZ/HI/MS/NE/NM/WA y, en contratos itemizados, CO/DC/IN/TX; servicios
  gravados por defecto solo en HI/NM/SD/WV), así que todo estado fuera
  de esas listas y de los casos por tipo de obra (NY/NJ/CT/KS/IA/NC)
  queda `none` por la regla mayoritaria.

## La tabla (51)

Modo = default para reforma/mejora de inmueble. Tipo = combinado medio
Tax Foundation midyear 2026 (excepto SD, cuyo 2 % es el «contractor's
excise tax», no el tipo de ventas). «Nota» resume el aviso que ve el
usuario en el editor.

| Est. | Estado | Modo | Tipo % | Nota |
|---|---|---|---:|---|
| AL | Alabama | none | 9.46 | — |
| AK | Alaska | none | 0.00 | Sin impuesto estatal; algunos municipios gravan (media local 1,82 %) |
| AZ | Arizona | none | 8.54 | Reforma sin modificación = MRRA (impuesto en los materiales, sin línea en factura). «Modification» = TPT prime contracting sobre el 65 % → `gross_receipts` |
| AR | Arkansas | none | 9.48 | — |
| CA | California | none | 9.03 | Los «fixtures» suministrados e instalados sí son venta minorista (CDTFA Pub. 9) |
| CO | Colorado | none | 7.89 | «Time-and-materials»: minorista → `materials` sobre el precio con margen (FYI Sales 6) |
| CT | Connecticut | none | 6.35 | Vivienda ocupada por el propietario y obra nueva exentas; servicios a inmuebles comerciales/industriales existentes, gravados (IP 2018(2)) |
| DE | Delaware | none | 0.00 | Sin impuesto sobre ventas |
| DC | District of Columbia | none | 6.00 | El contratista es consumidor de los materiales (DCMR 9-438.5/.18); ventas de material itemizado (§438.3) pueden ser minoristas |
| FL | Florida | none | 6.98 | — (GT-800067: consumidor final en lump-sum y en T&M) |
| GA | Georgia | none | 7.56 | — |
| HI | Hawaii | gross_receipts | 4.50 | GET sobre todo el contrato (4 % + recargo condal 0,5 % en Oahu); materiales incorporados al 0,5 % mayorista — el motor usa un solo tipo |
| ID | Idaho | none | 6.03 | Consumidor de todo lo que usa (guía Idaho Tax Commission) |
| IL | Illinois | none | 8.98 | — |
| IN | Indiana | none | 7.00 | «Time-and-materials» → `materials` |
| IA | Iowa | none | 6.94 | La mano de obra de reforma está exenta aunque el servicio esté enumerado; reparaciones sueltas → `full` (Iowa Contractors Guide) |
| KS | Kansas | none | 8.71 | Mano de obra residencial y «original construction» exentas; reforma **comercial** → `labor` (materiales gravados en la compra) (KS-1525) |
| KY | Kentucky | none | 6.00 | — |
| LA | Luisiana | none | 10.13 | — |
| ME | Maine | none | 5.50 | — |
| MD | Maryland | none | 6.00 | — |
| MA | Massachusetts | none | 6.25 | — |
| MI | Michigan | none | 6.00 | — |
| MN | Minnesota | none | 8.14 | — |
| MS | Mississippi | none | 7.06 | Residencial: materiales al 7 % en la compra. No residencial > 10.000 $: «contractor's tax» 3,5 % sobre el precio completo → `gross_receipts` con tipo 3,5 (MS DOR) |
| MO | Missouri | none | 8.44 | — |
| MT | Montana | none | 0.00 | Sin impuesto sobre ventas |
| NE | Nebraska | none | 6.98 | Default = contratista «Option 1» (consumidor); Options 2/3 (minorista) → `materials` (Reg. 1-017) |
| NV | Nevada | none | 8.24 | — |
| NH | New Hampshire | none | 0.00 | Sin impuesto sobre ventas |
| NJ | New Jersey | none | 6.60 | «Exempt capital improvement» sin impuesto (certificado ST-8); reparaciones/mantenimiento → `full` |
| NM | New Mexico | gross_receipts | 7.68 | GRT sobre los ingresos de construcción; el tipo depende del lugar de la obra |
| NY | New York | none | 8.54 | «Capital improvement» sin impuesto (ST-124) y materiales gravados en la compra; reparación/mantenimiento → `full` |
| NC | North Carolina | none | 7.10 | «Real property contract» (reforma) sin impuesto; servicios RMI → `full` |
| ND | North Dakota | none | 7.09 | — |
| OH | Ohio | none | 7.29 | Lo que sigue siendo bien mueble tras instalarse (p. ej. moqueta) es venta minorista (OAC 5703-9-14) |
| OK | Oklahoma | none | 9.06 | — |
| OR | Oregon | none | 0.00 | Sin impuesto sobre ventas |
| PA | Pennsylvania | none | 6.34 | — |
| RI | Rhode Island | none | 7.00 | — |
| SC | South Carolina | none | 7.49 | — |
| SD | South Dakota | gross_receipts | 2.00 | «Contractor's excise tax» 2 % sobre el precio completo; los servicios de construcción están exentos del impuesto de ventas y los materiales pagan en la compra |
| TN | Tennessee | none | 9.61 | — |
| TX | Texas | none | 8.20 | Mano de obra residencial exenta y materiales como consumidor en «lump sum»; no residencial → `full`; contrato «separated» → `materials` (Pub. 94-116) |
| UT | Utah | none | 7.42 | — |
| VT | Vermont | none | 6.43 | — |
| VA | Virginia | none | 5.77 | — |
| WA | Washington | full | 9.57 | Construcción «retailing» para el consumidor: «retail sales tax» sobre el precio completo (el B&O es aparte y no se muestra) |
| WV | West Virginia | none | 6.60 | La mejora capital es «contracting» no gravado; otros servicios al inmueble → `full` (TSD-310) |
| WI | Wisconsin | none | 5.72 | — |
| WY | Wyoming | none | 5.39 | — |

Resultado: 46 `none`, 1 `full` (WA), 3 `gross_receipts` (HI, NM, SD),
0 `materials`/`labor` por defecto — esos dos modos son el destino de las
notas (CO/IN/TX/NE itemizado → `materials`; KS comercial → `labor`).

## Decisiones que conviene dejar escritas

- **Arizona por defecto es `none`, no el 65 %**: desde 2015 la reforma
  de vivienda típica es MRRA (el impuesto va en los materiales y la
  factura no lleva línea de impuesto, según AZ DOR). El TPT «prime
  contracting» al 65 % queda a un cambio de modo, con la fracción ya
  precargada (0,65) en los datos del estado.
- **Dakota del Sur usa 2,00 y no el 6,11 combinado**: lo que se cobra
  sobre el contrato es el «excise» del 2 %; el impuesto de ventas cae
  sobre los materiales en la compra.
- **Alaska usa 0,00** aunque Tax Foundation promedia 1,82 % local:
  no hay tipo estatal y sugerir la media local inventaría un impuesto
  en municipios que no lo tienen. La nota avisa.
- **El tipo combinado es media ponderada por población**: sirve de
  punto de partida, no de tipo legal. La ayuda del editor lo dice
  («starting point — set the exact rate for the job address»).
- **La estimación de materiales** en los modos `materials`/`labor` usa
  el reparto de costes del propio presupuesto (coste de materiales ÷
  coste de obra, aplicado a la parte de obra de la base, con los
  productos vendidos contando como materiales). Es la aproximación
  documentada en `fiscalidad_eeuu.py`, gemela de la del CIS británico
  pero sobre precio de venta, no sobre coste.

## Fuentes (consultadas el 19-10-2026)

- Tax Foundation, «State and Local Sales Tax Rates, Midyear 2026»
  (tabla de 51 jurisdicciones: estatal, local medio, combinado).
- Avalara, «Sales tax requirements for construction contractors»
  (actualizado oct-2026): servicios gravados por defecto solo en
  HI/NM/SD/WV; ejemplos CT/HI/ID/NE/NM/SD/WV/FL/CA/CO/TX/OH/WA.
- Wolters Kluwer, «Understanding Sales Tax Rules for the Construction
  Industry»: listas de estados minoristas (lump-sum: AZ/HI/MS/NE/NM;
  itemizado: + CO/DC/IN/TX) y regla mayoritaria de consumidor.
- Guías oficiales: Kansas Pub. KS-1525 (rev. 30-07-2025); Iowa
  Contractors Guide (revenue.iowa.gov); Mississippi DOR, «Guide for
  Construction Contractors» (contractor's tax 3,5 %, no residencial
  > 10.000 $); Arizona DOR, «MRRA Contracting» y «Contracting FAQs»
  (base 65 % prime contracting; MRRA fuera); DC DCMR Title 9 §438;
  Connecticut DRS IP 2018(2); Texas Comptroller Pub. 94-116;
  California CDTFA Pub. 9.
