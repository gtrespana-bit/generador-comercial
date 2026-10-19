# Investigación de precios de referencia — Irlanda (2026-10-19)

Estudio de precios de la Fase 0 del mercado irlandés, equivalente al realizado para España
(2026-08-25) y el Reino Unido (2026-10-18). Genera la matriz nacional
`basedatos_partidas/salida/precios_recursos_irlanda.csv` (388 recursos, EUR sin IVA) con
`tools/generar_matriz_precios_irlanda.py` y el modelo laboral
`tools/coste_empresa_irlanda.py`. La metodología está en
`docs/METODOLOGIA_PRECIOS_REFERENCIA_IRLANDA.md`.

**Fecha de corte: 19 de octubre de 2026.** Tipo de corte: **1 USD = 0,8886 EUR** (EUR/USD
1,1253, tipo de referencia del BCE del 16/10/2026). Todos los precios de este documento y de la
matriz son **sin IVA**.

## 1. La advertencia que ordena todo lo demás

Dos errores habrían sido fáciles y los dos se han evitado:

1. **Convertir la base por tipo de cambio.** Los precios base de
   `basedatos_partidas/datos/recursos.json` son USD con ámbito **Venezuela** (un oficial a
   5,50 USD/h). Multiplicar por 0,8886 EUR daría un oficial irlandés a 4,89 €/h: un 85 % por
   debajo de su coste real. La matriz se construye desde precios irlandeses observados; la base
   solo aporta la *forma* de la canasta a través de los factores por familia (§5).

2. **Copiar el Reino Unido en euros.** Irlanda comparte idioma, formatos (bloque de 440×215,
   hoja de yeso de 8×4 pies, enchufes BS 1363) y buena parte de la cadena de suministro con GB,
   así que la tentación era reutilizar la matriz británica convirtiendo libras a euros. Pero sus
   precios no coinciden (la placa de yeso cuesta un 70 % más que en GB; la piedra triturada, la
   mitad), su marco laboral es otro (SEO con categorías propias, PRSI, CWPS), su IVA de
   materiales es dual (13,5 %/23 %), tiene un gravamen específico sobre el hormigón (DCPL) y su
   peón cuesta más que el oficial español. GB ≠ IE, también en precios.

Irlanda publica **menos precios** que el Reino Unido: los grandes hormigoneros (Roadstone,
Kilsaran, Irish Cement) trabajan «bajo presupuesto», Chadwicks no muestra precio sin cuenta y
Sika/SIG venden por cotización. La canasta se ha construido con quien sí publica: Hanly
Quarries (hormigón y áridos sueltos), TJ O'Mahony, McMahons, Brooks, Goodwins y M.D. O'Shea
(precio con y sin IVA), Screwfix Irlanda (solo con IVA: la cifra neta divide por 1,23 y queda
declarado en cada ancla), Mr Hire y Laois Hire (alquiler sin IVA) y las fuentes oficiales (WRC,
Revenue, CSO, BCE).

## 2. Criterio de mano de obra: coste empresa, no tarifa de autónomo

El mismo criterio de España y el Reino Unido: el recurso de mano de obra es el **coste empresa
por hora facturable**, porque el catálogo ya aplica un 35 % de margen sobre el coste directo.
La tarifa que un autónomo irlandés cobra al cliente (50-80 €/h el electricista, 50-100 €/h el
fontanero, jornales de 300-550 €/día) produciría margen sobre margen.

### 2.1 El mapa salarial: un SEO en pie y dos anulados

La singularidad irlandesa es que **no hay una sola escala**. Hubo tres órdenes sectoriales
(SEO); dos cayeron en los tribunales y sus escalas pactadas sobreviven como referencia de
mercado:

| Sector | Estado | Escala adoptada | Oficial tipo |
|---|---|---|---|
| Construcción general | **SEO en vigor** (WRC) | Mínimos legales desde 01/08/2026 | Craftsperson 23,74 €/h |
| Eléctrico | SEO anulado (2020/2022) | Escala pactada AECI/Connect, 16/02/2026 (+3,4 %) | 3.er año: 27,60 €/h |
| Mecánico (fontanería/HVAC) | SEO anulado (2023) | Escala Connect desde 01/05/2026 (+3,2 %) | 3.er año: 29,12 €/h |

Escala del Construction SEO desde el 1 de agosto de 2026 (Workplace Relations Commission),
semana de 39 h:

| Categoría | €/h | A quién cubre |
|---|---|---|
| Craftsperson | 23,74 | Albañiles, carpinteros, pintores, yeseros, alicatadores, vidrieros… |
| Category A | 23,03 | *Steel fixers*, andamistas avanzados, operadores de grúa/planta pesada, *banksmen* |
| Category B | 21,37 | *General operatives* con más de 2 años en la industria |
| New Entrant | 17,28 | Solo los 2 primeros años de incorporación |

Las escalas AECI (eléctrica) y Connect (mecánica) son por antigüedad tras el aprendizaje; se
adopta el **3.er año** como oficial tipo (AECI: 27,06 → 28,48 €/h del año 1 al 11; Connect:
28,51 → 30,01 €/h del año 1 al 10). Los extremos quedan dentro del rango de la matriz.

Decisiones de correspondencia con los 17 recursos del catálogo:

- **Cabillero = Category A (23,03), no craft.** El SEO clasifica expresamente a los *steel
  fixers* en la categoría A. Es el caso contrario al de otros mercados, donde el armador es
  oficial pleno, y se respeta el dato irlandés.
- **Peón = Category B (21,37), no New Entrant.** La tarifa de 17,28 €/h es un grado temporal de
  dos años; aplicarla a todas las horas de peón presupuestadas infringiría el SEO y
  infravaloraría la obra. Consecuencia nada intuitiva pero real: **el peón irlandés cuesta más
  que el oficial español** (29,60 frente a 21,00 €/h de coste empresa).
- **Soldador y climatización = escala mecánica.** No figuran entre los *crafts* del SEO de
  construcción; el soldador de tubería/estructura y el técnico HVAC trabajan bajo la referencia
  Connect del sector mecánico.
- **Jardinero = Category B asimilado.** El paisajismo queda fuera del SEO de construcción.

Contraste con la realidad de mercado: la CSO (*Earnings and Labour Costs*, 2.º trimestre de
2026) sitúa las ganancias medias de la construcción en **29,88 €/h** — por encima de todas las
tarifas base anteriores, porque incluyen horas extra (pagadas a ×1,5/×2 según el SEO),
plus de desplazamiento y los oficios mejor pagados. Confirma que el SEO es un suelo, no la
media; por eso el rango de la matriz sube un 20 % (§2.3), pero el precio central se ancla en la
escala verificable euro a euro, igual que en GB se ancló en la mediana ONS con suelo CIJC.

### 2.2 De salario a coste empresa

| Concepto | Valor 2026 | Fuente |
|---|---|---|
| Jornada | 39 h/semana × 52 = 2.028 h contratadas | SEO / escalas AECI y Connect |
| Vacaciones | 21 días (20 estatutarios + 1 de industria) en periodos cerrados (*builders' holidays*) | OWTA 1997; calendario CIF/Connect |
| Festivos públicos | 10 días | OWTA 1997 |
| Bajas | 5 días/año | Derecho estatutario de enfermedad vigente en 2026 |
| **Horas facturables** | **1.747,2 h/año** | 2.028 − 241,8 − 39,0 |
| PRSI empresa (clase A) | **11,40 %** desde 01/10/2026, sin techo | DSP/PwC; la tasa reducida (9,15 %) exige ≤552 €/semana y ningún oficio baja de 833 €/semana |
| CWPS empresa | **36,43 €/semana** desde 03/08/2026 (32,89 pensión + 1,17 muerte en servicio + 2,37 enfermedad) | CWPS / SEO |
| Gastos fijos | 1.550 €/año (seguro 250, EPI/herramienta 400, formación Safe Pass/CSCS 180, nóminas 120, previsión de *redundancy* 600) | Estimación documentada en el modelo |

Sobre la previsión de despido: la *redundancy* estatutaria irlandesa devenga 2 semanas por año
de servicio con tope de 600 €/semana. Se provisiona 1 semana al tope por año — el mismo
criterio amortizado de ES y GB — porque no todo el personal la llega a cobrar.

Ejemplo completo (oficial *craftsperson*):

```
Salario            23,74 €/h × 2.028 h           = 48.144,72 €
PRSI empresa       11,40 %                       =  5.488,50 €
CWPS               36,43 € × 52 semanas          =  1.894,36 €
Gastos fijos                                     =  1.550,00 €
                                              ───────────────
Coste anual                                      = 57.077,58 €
Coste por hora facturable  57.077,58 / 1.747,2   =     32,67 €
Recargo sobre salario                            =     18,6 %
```

El recargo (17-19 % según oficio) queda en la misma banda que GB (19,8 %): coherencia, no
coincidencia — ambos modelos cargan cotización, pensión y vacaciones sobre horas facturables.

### 2.3 Resultado

| Recurso | Oficio irlandés | Salario €/h | Coste empresa €/h |
|---|---|---:|---:|
| MO-OF1 | General builder (craftsperson) | 23,74 | **32,67** |
| MO-OF1-PISO | Floor layer | 23,74 | 32,67 |
| MO-OF1-ALI | Wall and floor tiler | 23,74 | 32,67 |
| MO-OF1-ALB | Bricklayer | 23,74 | 32,67 |
| MO-OF1-MON | Fit-out installer (joiner) | 23,74 | 32,67 |
| MO-OF1-PIN | Painter and decorator | 23,74 | 32,67 |
| MO-OF1-CARP | Formwork carpenter | 23,74 | 32,67 |
| MO-OF1-CARPM | Carpenter and joiner | 23,74 | 32,67 |
| MO-OF1-VIDR | Glazier | 23,74 | 32,67 |
| MO-AYU-ESP | Skilled general operative (Cat. A) | 23,03 | **31,75** |
| MO-OF1-CAB | Steel fixer (Cat. A) | 23,03 | **31,75** |
| MO-AYU | General operative (Cat. B) | 21,37 | **29,60** |
| MO-OF1-JARD | Landscape operative (asimilado) | 21,37 | 29,60 |
| MO-OF1-ELE | Electrician (AECI 3.er año) | 27,60 | **37,66** |
| MO-OF1-PLO | Plumber (Connect 3.er año) | 29,12 | **39,62** |
| MO-OF1-SOLD | Welder / pipefitter-welder | 29,12 | 39,62 |
| MO-OF1-AC | HVAC engineer | 29,12 | 39,62 |

La estructura es **mucho más plana** que en España: entre peón y oficial craft solo hay un
10 % (en ES, un 40 %). No es un error: es la tabla del SEO, y comprimirla «para que parezca
normal» sería inventarse Irlanda.

**Verificación de venta.** Con el 35 % de margen del catálogo, el precio de venta implícito es
44,10 €/h el oficial (353 €/día), 50,84 el electricista y 53,49 el fontanero — dentro o por
debajo de lo que el mercado cobra por esos oficios en obra continuada, y por debajo del
*call-out* de autónomo. El peón sale a 39,96 €/h (320 €/día), por encima del precio de
agencia; es la misma tensión ya documentada en GB y se acepta por la misma razón: el APU
anualiza vacaciones y cargas sobre las horas facturables de una plantilla propia, que es lo
que cuesta tener al peón todo el año, no alquilarlo por días.

**Rango publicado: −3 % / +20 %.** A diferencia de GB (−10 %/+20 %), el mínimo no puede bajar
más: la base es el mínimo legal o pactado nacional. El +20 % cubre Dublín y las pagas sobre el
SEO habituales en obra grande (la CSO da 29,88 €/h de ganancia media sectorial, un 26 % sobre
el craft base, con horas extra dentro).

## 3. Maquinaria

Fuente principal: lista pública de **Mr Hire** (día/semana sin IVA), contrastada con Laois Hire
(semanal sin IVA: excavadora de 1,5 t 290 €/semana, de 5 t 470, de 13 t 770; dumper de 9 t 500;
telescópica de 18 m 690) y la guía 2026 de DCM Hire. La tarifa de día se divide entre 8 h, como
en GB. Precios sin comb
...[truncated 10381 chars]