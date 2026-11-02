# 41 cuentas, 4 de pago: medido en la base, no estimado (02/11/2026)

Dato del titular: **41 cuentas y 4 con plan de pago**. Esta versión sustituye
la anterior del mismo día: los números ya **no son los que reportó el dueño**
ni los que yo supuse; salen de consultar la base de producción
(`CotizaT-Generador`, `ca-central-1`, 02/11/2026), descontando las cuentas de
prueba del dueño.

Este documento sustituye el orden de prioridades de
`PLAN_USUARIOS_DE_PAGO_2026-11-02.md` (que queda como contexto del embudo y de
la atribución).

## 0. Cómo se contó (para que se pueda repetir)

- **Cuentas de prueba excluidas:** `gtrespana@gmail.com` y
  `lanzareformas@icloud.com`, más todas las empresas cuyo nombre empieza por
  `testing`, `remodelat` o `remodelt` (las creó el dueño, una por país, para
  probar). Son 11 empresas y 12 licencias de cortesía.
- **Qué es «cuenta»:** fila en `usuarios` con membresía activa en una empresa
  que no sea de prueba. **Qué es «pago»:** empresa con `licencias.origen =
  'pago'`. Una empresa pagadora con dos compras cuenta una vez.
- Al filtrar con cuidado, los dos números del titular cuadran exactos:
  **41 cuentas y 4 empresas pagadoras**. No había error de conteo; había error
  de interpretación de *qué* se estaba contando (ver §2.1).

## 1. El embudo real, paso a paso

| Paso | Empresas | % de las 41 | Se pierden |
|---|---|---|---|
| 1. Cuenta creada | **41** | 100 % | — |
| 2. Empezó a usar el producto (guardó partidas o usó la IA) | **40** | 97,6 % | −1 |
| 3. Creó un presupuesto **real** (no la demo) | **7** | 17,1 % | **−33** |
| 4. Envió ese presupuesto al cliente | **2** | 4,9 % | −5 |
| 5. Compró (licencia `pago`) | **4** | 9,8 % | −37 respecto al paso 1 |

El paso 5 no cuelga del 4: **solo 2 empresas enviaron un presupuesto y 4
pagaron**, y no son las mismas. Dos de las pagadoras (Sermant JR y MD
CONSTRUCTA) compraron sin haber enviado nunca un presupuesto al cliente.

**El embudo no se rompe donde parecía.** Entre «se registra» y «abre la
herramienta» no se pierde nadie: 40 de 41 guardaron partidas o lanzaron una
conversación con la IA. **Se rompe justo después: 7 de 41 llegaron a un
presupuesto real, y 33 nunca crearon uno.**

Y hay una sorpresa en el paso 5: **2 de las 4 que pagan nunca crearon un
presupuesto real** antes de pagar (Sermant JR y MD CONSTRUCTA no; PJP sí, y
RemodelaT es la cuenta del dueño). Es decir, hoy se paga por confianza en la
promesa del producto, no porque el producto haya demostrado entregar un
presupuesto terminado.

**Nota de conteo:** hay 45 empresas para 41 cuentas porque dos usuarios
crearon empresa dos o tres veces (`arquitectos` x3, `Dauria Matias` + `MD
CONSTRUCTA`). Se cuentan como activación, no como cuentas.

## 2. Correcciones a lo que yo mismo escribí antes

### 2.1 «Ingreso actual 356 USD/año» era falso

La versión anterior de este documento asumía que los 4 pagos eran anuales.
Las compras reales son **4 mensualidades de 9,99 USD** (tres por Stripe, una
por pago móvil). Ingreso mensual real: **39,96 USD**. Anualizado, si nadie se
da de baja: **479,52 USD**. Lo cobrado hasta hoy: **~130 USD**.

**LTV real: 9,99 × vida media.** Con 12 meses de vida supuesta, LTV = 119,88
USD (no 89). Con la regla 3:1, el **CAC máximo es 39,96 USD** (29,67 si el
cliente se fuera al anual). Eso sigue sin dar para pagar tráfico: 49 clics en
una semana no han traído ni una cuenta de esos mercados.

### 2.2 Las 4 altas diarias de septiembre no existen

Las 41 cuentas se reparten así: **1 en agosto, 19 en septiembre y 21 en
octubre** (1–31 oct). En los 7 días del informe de Search Console (25–31/10)
entraron **2 cuentas**, las dos últimas del mes. La media de octubre es de
0,7 altas/día y la de los últimos 7 días, 0,3; no hay 4 altas diarias. Ese
es el techo actual de todo el embudo.

### 2.3 El dato de «último acceso» no sirve para medir abandono

`usuarios.ultimo_acceso_at` se sella con freno de 5 minutos en el único punto
por el que pasan las peticiones autenticadas. Pero en la base solo **5 de las
41** tienen marca, mientras que **40 sí guardaron partidas o conversaciones**.
Conclusión: el campo se escribe desde hace poco y no puede usarse para decidir
«cuántas siguen entrando». Para eso está `eventos_producto`
(`actividad.diaria`, `sesion.activa`), que tiene 23 y 7 latidos de 8 y 2
empresas respectivamente.

### 2.4 La atribución por página todavía no tiene datos

`eventos_producto` guarda `cuenta.registrada` desde el 30/08, pero la clave
`origen` solo aparece en **4 eventos del 15–20/10**, y esos 4 son de
`licencia.activada` (plan y método), no de página de origen. Es decir: el
mecanismo `?origen=` que se desplegó hoy **nunca se ha ejercitado**. El
`detalle` de las 58 altas solo lleva `{"pais": "XX"}`.

## 3. De dónde vienen y qué usan (lo que sí dice la base)

**Altas por país** (41 cuentas, las de prueba fuera):

| País | Cuentas | Pagan |
|---|---|---|
| ES | **13** | 0 |
| NI | 4 | 0 |
| MX | 4 | 0 |
| PY | 4 | 0 |
| CL | 3 | 0 |
| EC | 3 | 1 |
| PE | 2 | 0 |
| CR / DO | 2 | 2 |
| AR, BO, HN, PA, US, UY | 6 | 0 |

**Los mercados donde el producto *se usa* no son los que pagan, y los que
pagan no son mercados de Search Console.** España es el 32 % de las cuentas y
**cero pagos**. Los cuatro pagos son de Ecuador (PJP), Costa Rica (Sermant JR)
y República Dominicana (MD CONSTRUCTA) más la cuenta del dueño: **ninguno de
los tres mercados que pagan aparece en el informe de GSC**. Y el país que más
tráfico y más cuentas aporta (España: 1.098 impresiones, 13 cuentas) no ha
comprado ni una licencia.

Eso no se lee todavía como «el mercado español no paga»: con 4 pagos, la
diferencia no es distinguible del azar. Lo que sí es un hecho es que **el
catálogo SEO y los clientes que pagan son dos poblaciones distintas**, y por
tanto optimizar el catálogo no es el camino para conseguir pagos.

**Uso real por empresa** (señal de que el producto funciona cuando se usa):

| Empresa | Presupuestos (reales + demo) | Partidas | Conversaciones IA | Paga |
|---|---|---|---|---|
| PJP (EC) | 7 (6 + 1) | **727** | 15 | Sí |
| MD CONSTRUCTA (DO) | 6 (6 + 0) | 72 | 10 | Sí |
| iges soluciones (ES) | 6 (5 + 1) | 24 | — | No |
| Sermant JR (CR) | 1 (0 + 1) | 0 | 5 | Sí |
| ARCADIA JRC (ES) | 3 (2 + 1) | 49 | 1 | No |
| IBAU-PY (PY) | 3 (2 + 1) | 41 | — | No |

Es decir: **quien de verdad echa mano de la herramienta la usa en serio**
(727 partidas en un solo cliente, 15 conversaciones con la IA). El problema no
es que el producto no sirva: es que **33 de las 41 personas nunca llegaron a
crear un presupuesto real**, y de las 36 demos que se abrieron, **ninguna**
se convirtió en presupuesto real.

## 4. Lo que el dato descarta

- **No es un problema de tráfico.** Las 41 cuentas no salen de los 49 clics
  del informe de Search Console: el catálogo entero hace 21 clics en una
  semana. Optimizar el SEO de fichas no va a mover el embudo en el corto plazo.
- **No es un problema de producto en uso.** Quien lo usa, lo usa en serio.
- **No es que la prueba sea demasiado corta.** Las 41 la empezaron y **33
  nunca llegaron a un presupuesto real**. El problema está en las primeras 48
  horas, no en el día 7: alargarla a 14 días no arregla a quien abandonó en la
  primera sesión.
- **No es que falte catálogo ni precio bajo.** 787 fichas, 1.045 apartados con
  rango de precio y 21 clics en una semana: el catálogo no es el cuello de
  botella del pago.

## 5. Orden nuevo del trabajo

### A. Ahora: el primer presupuesto, no el SEO

1. **El alta crea un presupuesto real ya cargado** con partidas del país
   elegido, no una demo aparte. La base dice que las demos no se convierten:
   de las 36 demos, 0 llegaron a un presupuesto real. El primer pantallazo
   tras el alta debe ser «tu presupuesto», con partidas y un botón para
   generar el PDF.
2. **Medir el paso 4 desde hoy.** `presupuesto.creado` solo tiene **3 eventos**
   en toda la historia; el paso que importa (¿creó su primer presupuesto real?)
   no se registra. Sin ese evento no se puede saber si la corrección funciona.
3. **El techo real es de 0,3–0,7 altas/día.** Un objetivo de 1.000 USD/mes
   son ~100 suscriptores mensuales (o 11 anuales a 89 USD). Con 4 clientes
   pagando, eso es multiplicar por 25 lo que hay: primero hay que multiplicar
   las altas, y hoy vienen de canales que GSC no ve.

### B. Después: el cobro, con los números corregidos

- **Precio y LTV:** 9,99/mes da LTV 119,88 USD a 12 meses. El anual de 89 USD
  baja el LTV a 89 y sigue sin justificar CAC de pago. Antes de tocar precio,
  hay que entender por qué el producto se percibe como de 10 USD/mes.
- **El pago manual funciona pero desordena:** la licencia de Sermant JR tiene
  **dos compras activas solapadas** (una «anual» mal deducida y otra mensual
  correcta, ambas `activa`). Un cliente pagando dos veces no es un caso de
  éxito: es un error de facturación.
- **Stripe ya cobra de verdad.** Las tres compras de clientes son `cs_live_`
  y las tres tienen `sub_` (PJP, Sermant JR y MD CONSTRUCTA). La cuarta
  (pago móvil, RemodelaT) no es de un cliente: es la cuenta del dueño.
- **Pero el webhook no las activa solo.** Las de PJP y Sermant JR las activó
  el dueño a mano (`revisado_por_email = gtrespana@gmail.com`); solo la de MD
  CONSTRUCTA la activó `stripe@cotizat.local`. Con 3 compras es anécdota; con
  30 sería el negocio parado cada vez que falle un webhook.

### C. Y solo si sobra capacidad: el SEO de catálogo

Los títulos de hub ya llevan el rango de precio (ver §7). **No** se produce
más catálogo: 787 fichas dan 21 clics y el catálogo ya es el 76 % de las
impresiones. Con este LTV no hay margen para pagar tráfico.

## 6. Lo que hay que arreglar antes de volver a mirar el embudo

| Problema encontrado | Efecto | Prioridad |
|---|---|---|
| El paso 4 no emite evento | El panel no puede decir cuántas crearon su primer presupuesto | Alta |
| `ultimo_acceso_at` casi vacío | «Usuarios activos» del panel subestima | Media |
| Dos licencias activas solapadas en Sermant JR | Cobro duplicado, y el panel lo cuenta como 2 | Media |
| `origen` no aparece en ninguna alta | No se puede atribuir ni el 1 % de las 41 | Media (ya desplegado, falta que lleguen altas) |
| Solo 1 de las 3 compras de cliente la activó el webhook | PJP y Sermant JR las activó el dueño a mano (`revisado_por_email = gtrespana@gmail.com`); solo MD CONSTRUCTA la activó `stripe@cotizat.local`. Si el webhook falla en silencio, el cliente paga y se queda sin servicio | **Alta** |
| 5 registros sin cuenta (3 emails, 24/09–02/10) | Altas que no completaron el onboarding y no aparecen en `usuarios` | Baja |

## 7. Lo aplicado hoy (código ya en la rama)

| Cambio | Por qué |
|---|---|
| El `<title>` de los hubs de apartado lleva el rango real | `/en-ie/prices/lifts-and-platform-lifts`: 63 impresiones, posición 10,2, **cero clics**. Ahora: «Lifts and platform lifts: 750.02 EUR–1,991.17 EUR in Ireland». 1 045 apartados con rango real |
| La prueba gratis aparece junto al CTA de las fichas y hubs | El 90 % de las cuentas no paga y el CTA no decía que existiera la prueba |
| `tools/analizar_embudo.py` | Convierte cuentas/pagos/visitas en conversión, LTV y CAC permitido |
| Atribución del alta (`?origen=`) | Responde «¿las que pagan vinieron del catálogo o de la portada?». Ya desplegado; aún sin datos |
