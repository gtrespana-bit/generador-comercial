# Auditoría del panel de administración

6 de noviembre de 2026 · rama `arena/3b3eccdd-generador-comercial`

Encargo: «el panel tiene problemas visuales, sobre todo de contraste, y la idea
era un super panel informativo, fácil de ver y bien organizado». Esto es el
diagnóstico medido y el plan. No se ha tocado ni una línea del panel todavía.

---

## Veredicto

El panel no tiene un problema de gusto: tiene **un modo oscuro a medio hacer que
se activa solo** y **una hoja de estilos sin sistema** (52 colores a mano, 45
tamaños de letra distintos, 70 KB de CSS dentro del HTML). Cualquier pantalla
nueva hereda ese desorden, y por eso el rediseño de #188/#189, que estaba bien
pensado, se ve mal.

Medido, no opinado: **41 pares texto/fondo por debajo de WCAG AA en modo oscuro**
y **4 en modo claro**. El peor caso es el número grande de las tarjetas de KPI,
que en modo oscuro se escribe a **1,23:1** sobre blanco: eso no es «bajo
contraste», es texto invisible.

Se arregla en cuatro tramos. El primero es CSS puro, sin lógica, y quita el
dolor de hoy.

---

## Cómo se midió (y cómo se vuelve a medir)

No hay navegador en este entorno, así que la medición se hace sobre el CSS real
que el panel sirve al navegador: `tools/auditar_contraste_panel.py` lee el bloque
`<style>` de `admin/base_admin.html` más los bloques `{% block extra_css %}` de
las 11 pantallas que aportan estilos, resuelve `var(--token)` para el modo claro
y el oscuro, y calcula el ratio WCAG 2.1 de cada par texto/fondo que el propio
CSS declara.

```bash
python tools/auditar_contraste_panel.py                     # informe legible
python tools/auditar_contraste_panel.py --json              # volcado para pruebas
python tools/auditar_contraste_panel.py --baseline docs/panel_contraste_baseline.json
```

La deuda actual está congelada en `docs/panel_contraste_baseline.json` y
`tests/test_contraste_panel.py` (5 pruebas, 2,3 s) impide que crezca. El baseline
solo puede encogerse: al arreglar un par hay que borrarlo, o la prueba avisa.

---

## Hallazgo 1 · Contraste: el modo oscuro está roto y se activa sin querer

`admin-kit.js:400` enciende `html.dark-mode` cuando el sistema operativo pide
tema oscuro (`prefers-color-scheme: dark`). El operador no elige: entra y el
panel se oscurece. A partir de ahí:

- la página se pinta con `--bg-body: #0b1120` y texto `--text-main: #e2e8f0`;
- pero **32 fondos están escritos a mano en claro** y no cambian con el tema;
- resultado: texto claro del tema oscuro sobre superficies claras fijas.

El caso que se ve primero, la pantalla «Hoy»:

| Regla | Color de texto | Fondo | Ratio |
|---|---|---|---|
| `.kpi-card` + `.kpi-value` | `--text-main` `#e2e8f0` | `#fff` escrito a mano | **1,23:1** |
| `.form-control`, `input[type=…]` | `--text-muted` `#94a3b8` | `#fff` | **1,23:1** |
| `.btn-secondary` | `--text-main` | `#fff` | **1,23:1** |
| `.panel-tab:hover` | `--text-main` | `#eaf1ec` | **1,07:1** |
| `th` (cabecera de tabla) | `--text-muted` | `#eef2f8` | **2,28:1** |
| `.badge-neutral` | `--text-muted` | `#eef3f0` | **2,28:1** |
| `.alert-danger` / `.badge-danger` | `#b91c1c` | `#2d1b1b` | **2,53:1** |
| `.badge-warning` | `#8a5b10` | `#2d230a` | **2,64:1** |

Los 41 pares completos están en el baseline. El mínimo AA es 4,5:1 para texto
normal y 3:1 para texto grande; **36 de los 41 no llegan ni a 3:1 y 10 no
llegan ni a 2:1**.

No es un fallo de un elemento suelto: es la consecuencia de tener dos fuentes de
verdad para el color (tokens que sí cambian de tema y hexadecimales que no). La
paleta oscura, por cierto, está completa: el problema no son los tokens.

**Modo claro: 4 fallos, y son de otro tipo.** El mapa de calor de analítica usa
texto oscuro sobre celdas oscuras (`.cel.c-null` 1,99:1, `.cel.c-0` 2,24:1,
`.cel.c-3` 3,41:1) y el `kbd` de la chuleta de atajos se queda en 4,17:1. Es
deuda localizada, no estructural.

---

## Hallazgo 2 · Tipografía: 45 escalones y la mitad del texto por debajo de 12,6 px

188 declaraciones de `font-size` con **45 valores distintos** entre 0,6 y 1,75 rem.
**88 de las 188 (47 %) están en 0,79 rem o menos**; el valor más repetido es
0,78 rem (12,5 px) y hay 14 declaraciones en 0,7-0,76 rem (11-12 px).

En un portátil a 125 % de escala o en una pantalla 1366×768, los metadatos, las
notas al pie de las tarjetas y las etiquetas de los ejes se leen a 9-11 px
efectivos. Eso, sumado a `font-weight: 800`/`900` por todas partes, produce la
sensación de «no puedo leer esto» incluso donde el contraste sí cumple.

No hay escala tipográfica: cada tarjeta eligió su tamaño.

---

## Hallazgo 3 · Arquitectura CSS: no hay hoja de estilos, hay 70 KB dentro del HTML

| Dato | Valor |
|---|---|
| CSS en `base_admin.html` (bloque `<style>`) | 1.197 líneas · 44 KB |
| CSS aportado por las pantallas (`extra_css`) | 436 líneas · 26 KB |
| Reglas CSS en el panel | 662 |
| Plantillas del panel | 41 · 6.885 líneas |
| Tamaños de fuente distintos | 45 |
| Colores hexadecimales distintos | 52 |
| Tokens de color declarados | 25 |
| Media queries | 10 (para 19 pestañas + 7 pestañas de ficha) |

Consecuencias medibles:

1. **No se cachea.** El CSS viaja dentro de cada respuesta HTML, con `nonce` de
   CSP. Son ~70 KB extra por pantalla que el navegador vuelve a descargar.
2. **Las pantallas redefinen el sistema.** `analitica.html` vuelve a declarar
   `.btn-primary` y `.btn-secondary`; el resultado es un botón secundario distinto
   según la pantalla.
3. **Dos tarjetas, dos verdades.** `.card` usa `var(--card-bg)` (correcto);
   `.kpi-card` usa `#fff` (el fallo del hallazgo 1). Ambas conviven en la misma
   pantalla.
4. **Sin componentes.** Hay `.card`, `.card-pie`, `.kpi-card`, `.kpi`,
   `.bloque-acc`, `.alerta-banda`, `.aviso-corto`, `.panel-tab`… cada uno con su
   propio juego de colores.

---

## Hallazgo 4 · Dos lenguajes visuales: la web pública y el panel no parecen el mismo producto

| | Web pública (`public.css`) | Panel (`base_admin.html`) |
|---|---|---|
| Acento | `#123f78` índigo | `#123b72` azul marino |
| Segundo acento | `#e5ae3c` dorado | `#c9f24d` lima |
| Fondo | `#f4f5f7` | `#f3f6fb` |
| Texto | `#1a1d23` | `#101828` |
| Radio base | 16 px | 14 px |
| Barra lateral | no aplica | `#061427` con activo lima |

El dorado no existe en el panel; el lima no existe en la web. La fuente (Inter)
sí es común, y ese es el único puente. Para un panel que quiere «parecer caro»,
esta es la incoherencia más visible a primera vista después del contraste.

---

## Hallazgo 5 · Densidad sin jerarquía

| Pantalla | Líneas | Tarjetas | Contenido |
|---|---|---|---|
| Hoy (`dashboard`) | 628 | 29 | 3 bloques de alertas + KPIs + ingresos + vencimientos + ventas + churn + soporte + altas + atajos + auditoría |
| Analítica | 754 | 44 | 11 gráficos + embudo + cohortes + mapas de calor + tablas |
| Sistema | 54 (solo pestañas) | — | 8 pestañas servidas por `partes/` |

Dos problemas distintos:

- **Todo pesa lo mismo.** La misma tarjeta blanca, el mismo borde, el mismo
  tamaño de título para «Requiere tu atención ahora» que para «Últimas
  acciones del panel». El operador no tiene un orden de lectura; tiene 29 bloques.
- **Nada dice qué hacer.** «Hoy» se llama «lo que necesita una decisión antes de
  que cierre el día», pero la decisión es una tarjeta más entre 29, y las
  acciones (conceder, activar, responder) están dentro de cada bloque.

Lo que **sí** está bien y hay que proteger: la arquitectura de información está
resuelta en una única fuente (`app/panel_arquitectura.py`: 6 áreas, 19 pestañas,
7 pestañas de ficha, rol por pestaña, atajos y breadcrumbs derivados), hay
`skip link`, `aria-current`, `focus-visible`, atajos de teclado, buscador global
(`/admin/buscar`), notificaciones y chuleta. El esqueleto es de panel caro; la
piel es la que no.

---

## Plan propuesto

| Tramo | Qué | Riesgo | Cómo se verifica | Tamaño |
|---|---|---|---|---|
| **A. Rescate de contraste** | Las 32 superficies fijas pasan a tokens; paleta oscura completa; suelo tipográfico (nada por debajo de 0,86 rem salvo metadatos justificados); **el modo oscuro deja de activarse solo** (queda el botón) | Bajo: solo CSS, sin lógica ni consultas | Auditoría 41→0 y 4→0, suite completa, revisión visual con `?cb=` | 2-3 h |
| **B. Sistema de diseño** | `app/static/css/admin.css` cacheable; escala tipográfica de 7 pasos, espaciado 4/8/12/16/24/32, un solo componente por patrón (tarjeta, KPI, tabla, badge, pestaña, formulario); estados claro/oscuro/hover/focus en un sitio | Medio: toca 41 plantillas | La auditoría sigue en 0; el baseline se vacía; ninguna plantilla gana `style=` nuevos; suite | ~1 día |
| **C. Reorganización «super panel»** | Hoy en 3 bandas (decisiones → dinero → salud) con 6 tarjetas visibles y «ver todo»; Analítica en 4 pestañas (adquisición, producto, retención, ingresos) en vez de 44 tarjetas; tablas con columnas priorizadas; estados vacíos con acción; KPIs con delta y sparkline | Medio-alto: criterio de producto | Revisión tuya pantalla por pantalla; prueba de humo por pantalla; ninguna consulta nueva pesada | 2-3 días |
| **D. Pulido** | Modo oscuro de verdad (no solo tokens), responsive real (hoy 10 media queries), esqueletos de carga, exportar/imprimir, gráficos con contraste AA, micro-interacciones | Medio | Auditoría con navegador además de la estática | ~2 días |

Orden recomendado: **A hoy** (quita el dolor y deja la puerta puesta), **B
después** (sin sistema, C multiplica el desorden), y **C solo con tu revisión**.

---

## Anexo · deuda medida hoy

```text
reglas CSS analizadas ........ 660
tokens de color (claro) ...... 25
colores literales distintos .. 52
superficies claras fijas ..... 32
modo claro ................... 4 pares bajo AA
modo oscuro .................. 41 pares bajo AA   (36 por debajo de 3:1, 10 por debajo de 2:1)
```

Peores superficies en modo oscuro (contraste de los tokens de texto sobre ellas):

| Superficie | `--text-main` | `--text-muted` | `--brand-color` |
|---|---|---|---|
| `#fff` (24 reglas) | 1,23 | 2,56 | 2,96 |
| `#eef2f8` | 1,10 | 2,28 | 2,63 |
| `#eef3f0` | 1,10 | 2,28 | 2,64 |
| `#eaf1ec` | 1,07 | 2,23 | 2,58 |
| `#fbfdfb` (13 reglas) | 1,21 | 2,51 | 2,90 |
| `#f4f7f5` | 1,14 | 2,38 | 2,74 |

---

## Resultado del tramo A (mismo día)

Ejecutado sobre `arena/3b3eccdd-generador-comercial`. Solo CSS y una función de
JavaScript: ninguna consulta, ninguna ruta, ningún servicio.

| Métrica | Antes | Después |
|---|---|---|
| Pares por debajo de AA · modo oscuro | 41 | **0** |
| Pares por debajo de AA · modo claro | 4 | **0** |
| Superficies de fondo escritas a mano | 32 | **0** |
| Colores literales (fuera de la paleta) | 52 | **1** (`#241a02`, tinta del contador sobre el lima) |
| Tamaños de letra distintos | 45 | **9** (escala `--t-2xs`…`--t-4xl`) |
| Declaraciones por debajo de 12,5 px | 88 | **0** |
| Tokens de color declarados | 25 | **71** |
| Modo oscuro automático | sí (`prefers-color-scheme`) | **no**: solo con el botón |

Qué se hizo, en orden:

1. **Paleta completa.** Cada superficie, borde y color de estado tiene token en
   claro y en oscuro: `--surface-2`, `--surface-3`, `--surface-hover`,
   `--border-suave`, `--topbar-bg`; y por familia semántica `--danger-bg`,
   `--danger-borde`, `--danger-texto`, `--danger-solid` (igual para `success`,
   `warn` y `blue`). El texto sobre un fondo de marca ya no es blanco sobre el
   azul claro del modo oscuro: los botones usan `--brand-solid`.
2. **Los 52 hexadecimales sueltos pasaron a tokens** en las 12 plantillas que
   servían CSS. El único que queda es deliberado.
3. **Mapa de calor de analítica** rehecho en la rampa navy del panel (antes eran
   seis verdes con texto oscuro sobre fondo oscuro: 1,99:1). Ahora cada nivel
   declara su par fondo/texto y cumple AA en los dos temas.
4. **Escala tipográfica de nueve pasos** sustituyendo 45 tamaños. El suelo sube
   de 9,6 px a 12,5 px: 106 declaraciones que estaban por debajo.
5. **El modo oscuro ya no se activa solo.** Se queda en claro salvo que el
   operador lo pida; la preferencia sigue guardándose en `localStorage`.
6. **`kbd` de la chuleta** de atajos: fondo propio (`--surface-3`) en vez del
   color de borde, que dejaba el texto a 4,17:1.

La puerta queda cerrada: `tests/test_contraste_panel.py` (7 pruebas) exige cero
violaciones, cero superficies fijas, un solo color literal, nueve tamaños de
letra, ningún token roto o inexistente y ningún token de texto sin versión
oscura. Durante el propio tramo esa puerta detectó dos fallos reales: tokens que
se apuntaban a sí mismos (`--topbar-bg: var(--topbar-bg)`) y un token que el
parser no veía por un comentario con dos puntos.

Suite completa: **3368 passed, 13 skipped en 214 s**.

---

## Resultado del tramo B (mismo día)

Objetivo: que la piel del panel deje de viajar dentro de cada respuesta y que
exista un solo sitio donde tocar un componente.

| Métrica | Antes | Después |
|---|---|---|
| CSS dentro del HTML del panel | ~44 KB en cada respuesta | **0** |
| Hojas de estilo del panel | 0 (todo inline) | **1**: `app/static/css/admin.css` |
| Caché del CSS | ninguna | `max-age=31536000, immutable` con `?v=<sha>` |
| CSS propio de pantalla | 426 líneas sueltas en 11 plantillas | mismo CSS, prefijado `.panel-<área>` en la hoja |
| Declaraciones de espaciado en escala | 0 | **128** (pasos `--e-1`…`--e-8`) |
| Plantillas del panel con `<style>` | 12 | **0** |
| Tokens del panel | 71 | **78** (7 de espaciado) |

Qué se hizo:

1. **Extracción completa.** Las 1.294 líneas del `<style>` de `base_admin.html`
   más las 426 de las 11 pantallas pasan a `admin.css` (78,5 KB; 14,5 KB
   comprimido). `base_admin.html` enlaza con `{{ 'css/admin.css' | asset }}`, la
   misma ruta que ya usaban `public.css` y `style.css`, así que hereda la
   política de caché del proyecto: inmutable para una versión concreta.
2. **Aislamiento por área.** Ahora que todas las pantallas comparten hoja, el
   CSS de una podría alcanzar a otra. Para que no: `<body class="panel-{{ seccion_activa }}">`
   y cada bloque de pantalla se prefija con su área (`.panel-hoy`,
   `.panel-clientes`, `.panel-ingresos`, `.panel-web`, `.panel-analitica`,
   `.panel-sistema`). El comportamiento visible es exactamente el de antes,
   porque un selector prefijado gana a la regla base igual que antes ganaba por
   orden.
3. **Escala de espaciado** (`--e-1` 4 px … `--e-8` 32 px) aplicada a las 128
   declaraciones cuyo valor ya coincidía con un paso. No mueve nada: convierte
   el 16 en `var(--e-4)`. Los valores fuera de escala (9, 13, 14, 18 px) quedan
   a la vista como deuda del siguiente tramo.
4. **Se retira el hook `{% block extra_css %}`.** Una pantalla nueva ya no
   inyecta estilos: los añade a la hoja. Lo vigila una prueba.

Puertas nuevas (además de las 7 del tramo A):

- `test_la_piel_del_panel_vive_en_una_hoja_cacheable`: la hoja existe, el panel
  la enlaza con `asset()` y el `<body>` lleva su clase de área.
- `test_ninguna_plantilla_del_panel_vuelve_a_incrustar_estilos`: ninguna
  plantilla del panel contiene `<style>` ni `extra_css`.
- `test_las_paginas_del_panel_cargan_su_hoja_y_marcan_el_area` (humo, con sesión
  real): el HTML servido enlaza `admin.css?v=…`, marca `panel-hoy` y no lleva
  estilos incrustados.

Validación: `admin.css` parsea sin errores (0 de 637 reglas de primer nivel),
llaves equilibradas, contraste 0/0 en ambos modos, **3371 pruebas en verde**.

---

## Resultado del tramo C (mismo día)

Objetivo: que el panel se pueda **leer**. Con el contraste arreglado (tramo A)
y un solo sitio donde tocar cada componente (tramo B), faltaba lo que más se
nota: la información estaba toda, pero no tenía jerarquía.

### «Hoy»: de 29 tarjetas planas a 3 bandas

La pantalla de entrada apilaba 29 tarjetas del mismo peso. La misma alerta se
pintaba dos veces (banda de alertas arriba y tarjeta de pendientes más abajo) y
cuatro de los nueve KPIs eran contadores de trabajo que ya estaban, otra vez,
en las tarjetas de detalle.

| | Antes | Ahora |
|---|---|---|
| Bloques de primer nivel | 4 contenedores sueltos, 29 tarjetas | **3 bandas** numeradas |
| Veces que se pinta una alerta | 2 | **1** |
| KPIs | 9 (4 eran contadores de trabajo) | **5**, todos de dinero y cartera |
| Números repetidos en dos sitios | 4 | **0** |

- **Banda 1 · Requiere tu acción ahora.** Una sola lista de lo accionable, con
  su punto de severidad y dos botones (el hecho concreto y la lista completa).
  Deja fuera lo que ya tiene tabla propia en la banda 2, para no repetirlo.
- **Banda 2 · Lo que espera hoy.** Las cuatro colas del día: clientes por
  vencer, buzón de soporte, riesgo de baja y altas. Cada tarjeta lleva su
  contador en la cabecera, y ese contador **es un enlace a la lista que cuenta**
  (la invariante sigue vigilada por
  `test_los_kpis_del_panel_llevan_a_la_misma_lista_que_cuentan`).
- **Banda 3 · Cómo va el mes.** MRR, ingresos, ventas, clientes de pago y
  clientes sin plan, con la serie de seis meses y las últimas ventas. Esto se
  consulta; no se trabaja aquí.

### «Analítica»: de 44 tarjetas a 4 pestañas

Era una sola página de 632 líneas con 44 tarjetas: presencia en vivo, KPIs,
tabla de empresas, explorador de eventos, tres series, embudo, cohortes, uso de
funciones, países, orígenes, horas y churn. Todo verdad, todo junto.

Ahora son cuatro pestañas **resueltas en el servidor** (cada una con su URL,
enlazable desde el buscador o un aviso, y sin depender de JavaScript), todas
sobre la misma consulta: cambiar de pestaña no cambia el número, cambia qué
parte se mira. La ventana de días elegida viaja con la pestaña.

| Pestaña | Qué responde |
|---|---|
| **Resumen** | ¿Quién está dentro ahora y cuánto avanza el embudo? |
| **Producto** | ¿Qué se usa, qué se corrige al guardar y a qué hora se trabaja? |
| **Clientes** | ¿Quién paga, cuánto usa y quién está a punto de irse? |
| **Web** | ¿Qué pasa en la capa pública y de dónde llegan los registros? |

Ninguna métrica se perdió: el reparto está comprobado en
`test_el_operador_ve_el_panel_completo`, que recorre las cuatro pestañas y exige
ver cada bloque que antes estaba en la página única.

### Un componente por patrón

- **KPI único.** «Hoy» tenía su propio KPI (`kpi-valor`, `kpi-titulo`,
  `kpi-meta`, `kpi-comparativa`) distinto del que usan las otras 15 pantallas
  (`kpi-value`, `kpi-label`). Se borró el de Hoy: ahora todas comparten el
  mismo componente y la tendencia es una pieza opcional (`.kpi-tendencia`).
- **Banda** como patrón nuevo y único (`.banda`, `.banda-cab`, `.banda-num`,
  `.banda-rejilla`), en la hoja base para que la reutilicen las demás pantallas.
- **Fuera el patrón viejo de banda de alertas**: ~40 reglas que ya no usaba
  nadie (`.alerta-banda*`, `.alerta-item*`, `.alerta-punto*`).
- La hoja baja de 1.734 a **1.688 líneas** y de 659 a **634 reglas** aunque el
  panel gana tres patrones nuevos.

### Puertas nuevas

- `test_hoy_se_lee_en_tres_bandas`: tres bandas, en orden, una sola lista de
  pendientes, cero contadores de trabajo repetidos como KPI.
- `test_las_cuatro_pestanas_de_analitica_se_navegan_por_url`: las cuatro
  pestañas, con su URL y con la ventana de días conservada.
- `test_el_operador_ve_el_panel_completo` (reescrita): recorre las cuatro
  pestañas y exige ver todo lo que había en la página única.
- `test_todas_las_pestanas_del_panel_responden` (humo): ya recorría
  `?tab=` de todas las áreas, así que una pestaña nueva sin plantilla falla.

Validación: **3373 pruebas en verde**, 249 plantillas parseadas, contraste
**0 violaciones** en claro y en oscuro.

---

## Resultado del tramo D (mismo día)

Objetivo: cerrar lo que no se ve en una captura — el modo oscuro a medias, el
móvil, la señal al navegar y el contraste de los elementos que no son texto.

### El hallazgo: la auditoría del modo oscuro estaba ciega

Al empezar el tramo, el auditor seguía informando «0 violaciones en oscuro».
Era mentira. `paleta()` buscaba el texto `html.dark-mode` y lo encontraba
**primero dentro de un comentario** del encabezado de `admin.css` (la propia
documentación de la hoja dice «su versión en `html.dark-mode`»), así que
devolvía el bloque `:root` siguiente: desde el tramo B, el modo oscuro se
medía con la **paleta clara**.

- Arreglado: los comentarios se quitan antes de buscar y un selector se compara
  como conjunto (`html.dark-mode, body.dark-mode`), no como texto exacto.
- Con la medición real, el oscuro aporta **63 tokens propios** (antes: 0).
- La buena noticia: los colores del CSS ya eran correctos. **0 violaciones en
  ambos modos** con la paleta buena. Lo que faltaba era todo lo demás.
- `test_el_modo_oscuro_se_mide_con_su_propia_paleta` impide que la medición
  vuelva a quedarse ciega en silencio.

### Modo oscuro de verdad

Los tokens estaban, pero el navegador no sabía en qué tema estaba:

| Antes | Ahora |
|---|---|
| Calendario de un campo de fecha en blanco | `color-scheme: dark` por tema |
| Desplegables, casillas y scrollbars claros | `accent-color` + `scrollbar-color` con tokens |
| Selección de texto azul del sistema | `::selection` con el navy y `--on-brand` |
| Borde de campo a 1,29:1 (invisible) | `--borde-control` a **3,26:1** (WCAG 1.4.11) |
| Anillo de foco navy sobre panel oscuro | `--anillo-brand`, con versión oscura |

### Responsive

- **19 rejillas** usaban `minmax(420px, 1fr)`: 42 px más anchas que un móvil de
  360, y por tanto scroll horizontal. Ahora `minmax(min(420px, 100%), 1fr)`, que
  encoge en vez de desbordar. Una prueba prohíbe volver al mínimo fijo.
- **`@media (max-width: 480px)`**: menos relleno, KPIs en dos columnas legibles,
  y botones de **40 px** de alto (con 26 px no se pulsa con el pulgar).

### Señal al navegar (en vez de esqueletos)

El panel se renderiza en el servidor: no llegan datos después del HTML, así que
un esqueleto de tarjetas grises prometería algo que no va a pasar. Lo que sí
faltaba es saber que el clic contó: **barra de progreso de 3 px** arriba, con
`aria-busy` en la región principal mientras se navega. Sin estilos en línea y
respetando `prefers-reduced-motion`.

### Elementos no textuales (WCAG 1.4.11)

El auditor ahora mide también lo que un ojo cansado no ve fallar: bordes de
control, anillo de foco y series de gráfico, con mínimo 3:1.

- Encontró una barra de gráfico al 85 % de opacidad que se quedaba en **2,95:1**.
  La opacidad se va; el énfasis pasa al `:hover`.
- Resultado: 6 mediciones × 2 modos, **todas por encima de 3:1** (la más justa,
  3,01:1; la del anillo de foco, 11,09:1 en claro y 7,79:1 en oscuro).

### Cifras

| | Tramo C | Tramo D |
|---|---|---|
| Tokens (claro / oscuro) | 85 / 0 medidos | **86 / 63** |
| Reglas | 634 | 658 |
| Violaciones de texto (claro / oscuro) | 0 / 0 (ciego) | **0 / 0 (real)** |
| Elementos no textuales | sin medir | **12 mediciones, 0 fallos** |
| Pruebas | 3373 | **3382** |

Tramo D cerrado. Lo que queda para más adelante, ya fuera del plan acordado:
pantalla de carga por sección (requiere datos por `fetch`), impresión de fichas
y pruebas en navegador real.

---

## Tramo E · Honestidad y velocidad (mismo día)

Con los cuatro tramos del plan cerrados, el siguiente escalón no era visual:
era **lo que el panel dice y cómo responde**. Tres huecos medidos en el código
—no supuestos— y arreglados en un solo tramo.

### E1 · La hora que ve el operador

La empresa opera desde Caracas (UTC−4) y todo lo guardado es UTC
(`DateTime` con `datetime.utcnow` en `app/models.py`, correcto para almacenar y
para ordenar). El problema estaba al pintar: **13 plantillas imprimían el
instante en crudo**, así que una venta de las 20:30 aparecía como las 00:30
**del día siguiente**. No es un detalle de formato: es un dato falso en la
pantalla que se usa para decidir.

Ahora la conversión vive en un solo sitio, `app/tiempo.py`:

- Zona configurable con `COTIZAT_ZONA_HORARIA` (por omisión `America/Caracas`).
  Si el nombre está mal escrito se cae a UTC y el panel sigue funcionando: una
  variable de entorno no puede tumbar el arranque.
- Filtros `|local` (instante → zona), `|local_fecha` (día) y `|utc` (el
  instante exacto, para el `title` del `<time>`), más el global
  `zona_horaria()` → «hora de Caracas (UTC−04:00)», que se ve en la cabecera
  de Hoy, en el pie del reloj de analítica y en la tarjeta de actividad por
  hora. Nadie tiene que adivinar en qué zona está leyendo.
- Las **fechas de calendario no se desplazan**: `vence` o `inicio` son días,
  no instantes. Un vencimiento no cambia de día por la zona del que mira.
- Las fronteras de periodo («hoy», «este mes») del panel usan el día del
  operador (`hoy_local()`), no el día UTC: a las 22:00 en Caracas sigue siendo
  hoy, y «ventas de hoy» no se vacía a media tarde.
- `Actividad por hora` cuenta en la zona del operador; «hora punta 02:00 UTC»
  era medianoche en Caracas y no servía para decidir nada.

Una prueba recorre todas las plantillas del panel y **falla si alguien vuelve a
escribir un `strftime` con hora sin pasar por `|local`**. Es el tipo de arreglo
que se pierde en la siguiente pantalla nueva si no queda cerrado.

### E2 · La página del 500

Un fallo no capturado devolvía el texto crudo de Starlette
(«Internal Server Error»): en inglés, sin salidas, sin decir a quién avisar y
sin nada que permitir cruzarlo con la tabla de errores internos. Para un panel
que se usa a diario, ese es el peor momento posible para no tener interfaz.

- `500.html` con estado **500 real** (nunca 200), `noindex`, salidas
  (reintentar la misma ruta, volver al inicio, escribir al soporte) y una
  **referencia de 10 caracteres** a la vista.
- La referencia se deriva de la **huella** del fallo —la misma que ya usa
  `errores_internos`—, así que el operador la pega en la tabla de errores y
  encuentra la traza exacta **sin añadir una columna ni una migración**.
- La página no depende de la sesión ni de la base: el 500 puede venir de ahí.
  Si hasta la plantilla falla, se responde texto plano con la referencia; nunca
  se convierte un 500 en otro 500.
- Nada del fallo viaja al navegador: ni la traza ni el mensaje interno. La
  cabecera `X-Referencia-Error` acompaña a la respuesta para soporte.
- Una API recibe JSON (`{"ok": false, "referencia": …}`), no HTML.

### E3 · Precarga al navegar

El panel se renderiza en el servidor: cada clic es una ida y vuelta completa.
Medido en frío, con base de datos incluida, son cientos de milisegundos por
pantalla. En vez de reescribir el panel como SPA, se le dice al navegador a
dónde va a ir antes de que haga clic.

- **Speculation Rules** (`prefetch`, `eagerness: "moderate"`) con una lista
  blanca que construye el servidor: las seis áreas y las pestañas del área
  activa. Al detener el puntero —o al tocar— el navegador ya está trayendo esa
  página y el clic se siente instantáneo.
- La lista **no lleva enlaces de acción**: pasar el ratón por encima de
  «conceder» o «salir» no prepara nada. Lo comprueba una prueba.
- `moderate` evita que abrir el panel dispare seis descargas; los navegadores
  que no entienden la regla la ignoran sin coste. Lleva `nonce` para pasar la
  CSP, y no hay JavaScript propio nuevo.

### Cifras

| | Tramo D | Tramo E |
|---|---|---|
| Fechas con hora sin zona | 13 plantillas | **0** (y una prueba lo vigila) |
| Página de error del panel | texto crudo de Starlette | **500 con referencia rastreable** |
| Precarga de navegación | ninguna | **áreas + pestañas, con lista blanca** |
| Pruebas | 3382 | **3406** |

Queda para el tramo F lo que ya estaba aprobado aparte: la **consola de
comandos en ⌘K** (ejecutar, no solo buscar) y el **movimiento del MRR**
(nuevo, expansión, contracción y baja del mes), que `resumen_financiero` hoy no
calcula.
