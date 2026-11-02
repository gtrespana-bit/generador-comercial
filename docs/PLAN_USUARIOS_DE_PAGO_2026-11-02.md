# Plan centrado en usuarios de pago (02/11/2026)

Los datos de Search Console dicen qué páginas reciben impresiones. No dicen
nada sobre lo único que importa al negocio: **cuántos de esos visitantes
registran una cuenta y cuántos acaban pagando**. Este documento fija ese
criterio y ordena el trabajo por su efecto sobre el ingreso, no sobre el
tráfico.

## 1. El embudo, con lo que hoy se sabe

Del panel (`/admin/analitica` → «Embudo de conversión») y de la telemetría de
servidor:

```
Cuentas registradas → Empresas creadas → Crearon presupuesto → Enviaron presupuesto → Pagaron
```

Los cinco pasos existen y se cuentan. Lo que **faltaba** es la pregunta que
decide dónde trabajar: *¿qué página trajo a los que pagan?*

Ejemplo con los datos del 02/11: el catálogo de precios genera el **76 % de
las impresiones** (787 fichas, 3 559 impresiones, 21 clics) y las 46
consultas comerciales —«programa de presupuestos», «APU»— dan **121
impresiones y 0 clics**. Sin atribución, «más partidas» y «una página de
producto» parecen igual de urgentes. Con atribución, se ve cuál convierte.

## 2. La atribución ya está implementada

`app/services/atribucion.py` + el `?origen=` de los CTA + el panel.

- Cada CTA de las páginas de precios apunta a
  `/acceso?origen=precios_ficha&pais=ES`.
- `/acceso` lo valida contra un **catálogo cerrado** y lo pone en un campo
  oculto del formulario.
- El alta lo guarda en `eventos_producto` (`cuenta.registrada`) como
  `origen_seccion`: `precios_ficha`, `precios_hub`, `precios_indice`,
  `comparador`, `mano_obra`, `calculadora`, `guia`, `landing_pais`, `planes`,
  `como_funciona`, `portada`.
- El panel lo pinta en **«Qué página trae los registros»**.

**No se usa cookie, y es a propósito**: las páginas públicas se sirven desde
el CDN de Vercel y una respuesta con `Set-Cookie` deja de cachearse (con
`Vary: Cookie`, Vercel no cachea nada). Meter la atribución por cookie
costaría el caché de las 787 fichas que traen el 76 % de las impresiones. El
parámetro en la URL no cuesta nada porque el HTML es idéntico para todos.

Qué **no** se guarda, a propósito: la URL, la IP, el referer ni un
identificador de visitante. Mercado + sección, y solo en el momento del alta.

## 3. Lo que hay que medir en 3 semanas (y decide el siguiente paso)

| Dato | Dónde | Qué decide |
|---|---|---|
| Registros por sección de origen | Panel → «Qué página trae los registros» | Si el catálogo no registra a nadie, dejar de producir partidas y hacer producto |
| Registros → empresa creada | Panel → Embudo | Si la fricción está en el alta o después |
| Empresa → presupuesto creado | Panel → Embudo | Si el producto se entiende en los primeros 7 días de prueba |
| Presupuesto → enviado | Panel → Embudo | Si el valor se percibe (PDF/WhatsApp) |
| Enviado → pagado | Panel → Embudo | Si el precio y el momento de cobro son correctos |
| Cobros declarados vs. activados | Panel → Ingresos | Si el pago manual pierde clientes por el camino |

La prueba es de **7 días** (`COTIZAT_DIAS_PRUEBA`, por defecto 7) sin tarjeta.
Es corta para un producto de presupuestos: el usuario lo abre, mira el
catálogo y lo deja «para la semana que viene». Candidata a subir a 14 días
**solo si** los datos muestran que el abandono ocurre entre el día 1 y el 7.

## 4. Prioridades, ordenadas por ingreso esperado

Todo lo demás (más partidas, más mercados, más guías) va **después** de esto.

### 1. La página que vende, no la que informa

Las 46 consultas con intención de compra tienen 0 clics en posiciones 44–87.
No aparece nadie buscando un programa de presupuestos. Hace falta una página
de producto real (no una landing de catálogo) para «programa de presupuestos
de obra» y «APU»: qué hace, para quién es, cuánto cuesta, prueba de 7 días y
un ejemplo de PDF.

### 2. Que quien llega a una partida tenga algo que hacer

Una ficha dice «Portón corredizo: 490,78 EUR/ud en España». El visitante
puede: irse, o **meter ESA partida en un presupuesto de prueba** y ver el
producto funcionando en 30 segundos. Hoy solo hay un botón «Crear mi
presupuesto» que lleva a un alta. Candidato claro: cantidad + «probar con esta
partida», sin registro, y el registro al guardar o descargar el PDF.

### 3. Activar en los primeros 7 días

El embudo ya lo mide. Lo que hay que vigilar: cuántas empresas crean un
presupuesto **el primer día**. Si no lo hacen, la prueba se gasta mirando el
catálogo. Palanca: un presupuesto de ejemplo ya creado en el alta (con las
partidas del país elegido) para que la primera pantalla no sea un formulario
vacío.

### 4. Quitar fricción del pago manual

El flujo es: elige plan → paga por transferencia/cripto → adjunta comprobante
→ se revisa en 48 h. Cada paso pierde gente. Medible en el embudo de cobro
(`pago.checkout_iniciado` → `pago.compra_registrada` → `licencia.activada`).

### 5. Y solo después, SEO de catálogo

Los títulos de hub con precio y el enlazado de fichas (plan del
`DIAGNOSTICO_GSC_REAL_2026-11-02.md`) siguen siendo buenos: cuestan poco y
mantienen las impresiones. Pero no son la palanca de ingreso: con posición 10
y 0 clics en un hub, el problema es que la página no vende, no que falte un
dato.

## 5. Lo que no se hace

- No se compran reseñas ni se inventan `aggregateRating` para limpiar el aviso
  de Search Console.
- No se añaden mercados ni decenas de miles de URL: el catálogo ya es el 76 %
  de las impresiones y aporta 21 clics.
- No se optimiza por «más visitas»: se optimiza por registros y por cobros.
  Una página con 20 visitas y 2 suscripciones vale más que 3 000 visitas de
  «precio de la losa» que se van sin registrarse.
