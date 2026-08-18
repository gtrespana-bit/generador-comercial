# Panel de operador: licencias (E1-060)

> **Estado: EN PRODUCCIÓN y verificado el 16/08/2026** en `https://cotizat.online`.
> Los dos pasos de despliegue de la §1 están **completados** (migración
> `f4c1d8e37a95` aplicada y `COTIZAT_OPERADORES` configurada en Vercel). El
> titular entró al panel y confirmó que funciona. Por decisión del titular se
> mantiene **deliberadamente simple** por ahora (solo lo esencial); las mejoras
> de interfaz y las piezas que faltan quedan anotadas en la §4.

Fecha: **16/08/2026**. Registro interno para conceder acceso, renovarlo, regalar
un período de prueba o compensar una incidencia.

Ruta: **`/admin/licencias`**.

---

## 1. Antes de nada: dos pasos obligatorios de despliegue

> **Estado: completados el 16/08/2026** (ver §5). Se conservan aquí como
> registro de cómo se despliega el panel: **cualquier entorno nuevo** (preview,
> otra base de datos, un despliegue desde cero) tendrá que repetirlos.

Este bloque **incluye una migración de base de datos**. Sin aplicarla,
`/readyz` responderá 503 en producción, porque el código pasa a exigir el head
`f4c1d8e37a95` (antes `e1a4b7c9d2f0`) y la base todavía estaría en el anterior.

### Paso 1 — Aplicar la migración

Con la conexión administrativa (**nunca** la de runtime), como en migraciones
anteriores:

```bash
MIGRATION_DATABASE_URL='postgresql://administrador:…@host:5432/postgres?sslmode=require' \
  alembic upgrade head
```

**Alternativa sin terminal (la que se usó el 16/08/2026):** el script SQL listo
para pegar en **Supabase → SQL Editor → New query → Run**:
`docs/staging_upgrade_f4c1d8e37a95.sql`. Va en una transacción y lleva guarda
de versión: aborta sin tocar nada si la base no está en `e1a4b7c9d2f0`.

Comprobación: `/readyz` debe responder `"alembic": "head:f4c1d8e37a95"`.

### Paso 2 — Declararte operador

En **Vercel → Settings → Environment Variables** (Production):

```
COTIZAT_OPERADORES = tu-correo@ejemplo.com
```

Admite varios separados por comas. Guarda y **redespliega**.

> **Sin esta variable el panel queda cerrado para todo el mundo**, incluido tú.
> Es el valor seguro por omisión: un despliegue nuevo no nace con un
> administrador implícito.
>
> El correo debe ser **el mismo con el que inicias sesión** y estar
> **confirmado**. Si no lo está, no eres operador aunque figures en la lista.

---

## 2. Cómo está protegido (y por qué así)

El panel es **la única excepción al aislamiento multi-tenant** del producto. El
resto de la aplicación se apoya en la membresía de organización; aquí hace falta
mirar *por encima* de las organizaciones. Por eso lleva tres barreras
independientes:

| # | Barrera | Qué impide |
| --- | --- | --- |
| 1 | `COTIZAT_OPERADORES` (variable de entorno) | Que alguien se nombre operador escribiendo en la base |
| 2 | `get_operator_db` | Que una sesión de cliente alcance las rutas del panel |
| 3 | RLS `cotizat_licencia_*` | Que un fallo de código llegue a leer o escribir licencias |

### Por qué la lista está en el entorno y no en la base

Lo natural habría sido una columna `es_operador` en `usuarios`. Se descartó a
propósito: esa columna sería **escribible desde la propia aplicación**, así que
cualquier fallo de autorización se convertiría en una escalada a
superadministrador. Una variable de entorno solo se cambia en Vercel, fuera del
alcance del código en ejecución.

Consecuencia deliberada: **no hay ninguna pantalla para nombrar operadores**. Se
añaden en Vercel y se redespliega. Es incómodo a propósito.

Una prueba (`test_no_existe_ninguna_forma_de_nombrar_operadores_desde_la_aplicacion`)
falla si algún día aparece esa columna.

### Por qué `licencias` no es una tabla de tenant

Las tablas con `TenantMixin` llevan `organizacion_id` y se filtran
automáticamente por la organización activa. Una licencia *apunta* a una
organización pero **no le pertenece**: es información del titular del producto
sobre un cliente. Si heredara de `TenantMixin`, el filtro automático se la
mostraría al propio cliente — justo lo contrario de lo que hace falta.

En su lugar, la sesión de PostgreSQL lleva la marca `cotizat.es_operador`, que
solo se activa desde la identidad ya validada por Supabase. Para cualquier
sesión de cliente vale `off` y **la tabla se comporta como si estuviera vacía**.

### Qué NO puede hacer el panel

- **No da acceso a los datos de negocio de ningún cliente.** Muestra el nombre
  de la organización, el período y el cobro; nunca sus presupuestos, clientes o
  precios. Hay una prueba que lo verifica.
- **No borra licencias.** La migración ni siquiera concede `DELETE`: una
  licencia se cancela y la fila permanece, porque el historial es la única
  fuente de qué se cobró.

---

## 3. Uso

### Conceder o renovar

Elige organización, tipo, duración y —si es de pago— importe y referencia.

**Tipos disponibles:**

| Tipo | Para qué | Importe |
| --- | --- | --- |
| `pago` | Venta real | Obligatorio (> 0) |
| `prueba` | Período de evaluación | Siempre 0 |
| `cortesia` | Regalar tiempo (gesto comercial) | Siempre 0 |
| `compensacion` | Compensar una incidencia grave | Siempre 0 |

La distinción no es cosmética: **solo `pago` suma a los ingresos** del panel.
Mezclar cortesías con ventas inflaría la facturación al mirarla de un vistazo,
así que el sistema rechaza una cortesía con importe y un pago sin él.

**Duraciones**: 7 días, 1 mes, 3 meses, 6 meses o 1 año. Tope de seguridad de 3
años, para que un error de tecleo no conceda acceso casi indefinido.

### Renovar sin restar días

Si la organización **ya tiene una licencia vigente**, la nueva empieza el día
siguiente a su vencimiento en lugar de solaparse. Renovar a quien aún le quedan
días no se los quita ni se los duplica.

Ejemplo real: un cliente con un año pagado sufre una incidencia y se le regala
un mes. El mes de compensación se encola detrás del año; no se pierde nada.

### Cancelar

El enlace «cancelar» del historial marca la licencia como cancelada y añade a
las notas quién y cuándo, con el motivo si se indica. La fila no desaparece.

### Leer el estado

- **Activa** — con acceso.
- **Vence en N d** (ámbar) — quedan 15 días o menos: toca avisar al cliente.
- **Sin licencia** — la organización existe pero nunca se le concedió acceso.
  Son las filas que más conviene mirar.

Los estados se derivan de la fecha **al leer la página**, no por un proceso
nocturno: en Vercel no hay procesos en segundo plano, y una licencia «activa»
con la fecha pasada sería una mentira silenciosa.

---

## 4. Lo que este bloque todavía no hace

- ~~**No corta el acceso automáticamente.**~~ **Resuelto el 16/08/2026** (ver
  §6): con `COTIZAT_EXIGIR_LICENCIA=true` el acceso se suspende solo al
  vencer. El valor por omisión sigue siendo desactivado.
- ~~**No genera todavía el recibo en PDF.**~~ **Resuelto el 16/08/2026**:
  enlace «recibo PDF» en cada licencia de pago (ver §6).
- ~~**No envía avisos de vencimiento por correo.**~~ **Resuelto el
  16/08/2026**: botón «Enviar avisos de vencimiento» (ver §6).
- **La interfaz es deliberadamente simple** (decisión del titular, 16/08/2026):
  tabla + formulario, sin adornos. Funciona y cubre lo esencial, pero se
  mejorará más adelante (mejor agrupación por estado, filtros, acciones
  visibles sin redirigir, etc.).
- **No hay avisos programados por horario**: el despliegue es serverless; el
  botón del panel marca la cadencia semanal (ver `docs/PROCESO_PILOTOS.md`).

Nada de esto bloquea el uso: el panel ya sirve para lo que se pidió — ver,
gestionar, regalar meses y dejar constancia.

---

## 5. Verificación en producción (16/08/2026)

Secuencia completa aplicada y verificada:

1. **Migración aplicada** con el script `docs/staging_upgrade_f4c1d8e37a95.sql`
   (Supabase → SQL Editor). La consulta final del script devolvió:
   `relrowsecurity = true, relforcerowsecurity = true, cotizat_app_puede_leer = true`.
2. **`/readyz` en https://cotizat.online/readyz** pasó de
   `"alembic": "inesperado:e1a4b7c9d2f0"` (ok: false) a:
   ```json
   {"ok": true, "checks": {"alembic": "head:f4c1d8e37a95",
    "rol_runtime": "superuser=False, bypassrls=False, inherit=True, cotizat_app=True", ...}, "errors": []}
   ```
3. **`COTIZAT_OPERADORES`** configurada en Vercel (Production) con el correo del
   titular y **redeploy** (las variables solo se leen al arrancar).
4. **Acceso real**: el titular entró a `https://cotizat.online/admin/licencias`,
   inició sesión con su correo verificado y confirmó que el panel funciona.

> Si en el futuro un entorno nuevo rechaza el acceso aunque la variable esté
> puesta, revisar en este orden: (1) ¿se redesplegó después de guardar la
> variable? (2) ¿el correo de la sesión está confirmado en Supabase Auth?
> (3) ¿coincide exactamente la dirección? La lista se normaliza en minúsculas,
> pero la pertenencia exige el mismo correo de la sesión.

---

## 6. Segunda parte (16/08/2026, noche): recibo, corte y avisos

Con E1-059 decidida (**cobro manual para el piloto**) se construyeron las tres
piezas que faltaban. Migración `b7c4a9e2d31f`
(`docs/staging_upgrade_b7c4a9e2d31f.sql` para aplicarla en Supabase).

### Recibo PDF por licencia de pago

- Enlace «recibo PDF» en el historial de cada licencia `origen='pago'` con
  importe. Número estable `CT-000NNN` (derivado del id), período con ambos
  días inclusive, método y referencia del cobro.
- El pie declara que es un **documento comercial sin validez fiscal ni
  tributaria**: mientras no exista razón social registrada
  (`COTIZAT_LEGAL_ENTITY`), el emisor muestra el marcador honesto, igual que
  las páginas legales.
- Una cortesía o prueba **no tiene recibo** (el panel devuelve el motivo):
  documentar como cobro algo regalado falsearía el registro.

### Corte automático de acceso

- Interruptor del despliegue: `COTIZAT_EXIGIR_LICENCIA=true`. **Por omisión,
  desactivado** — actualizar el código nunca cierra un despliegue solo.
- Con él activo, una organización sin licencia vigente no pasa de la puerta
  común de las rutas de negocio (`get_db`): recibe la pantalla «Acceso
  suspendido», que le dice que sus datos siguen guardados y cómo reactivar.
  Los datos no se tocan; al renovar, todo vuelve.
- En PostgreSQL el corte no consulta `licencias` directamente (la sesión del
  cliente no puede leerla por RLS de operador): pregunta a
  `cotizat_security.organization_has_license(id)`, función SECURITY DEFINER
  que solo devuelve un booleano y solo sobre la organización del claim de la
  propia sesión. En escritorio (SQLite) el corte **no aplica nunca**.
- El panel muestra un aviso ámbar mientras el interruptor esté apagado, y
  `/readyz` publica `"licencias": "exigida" | "no-exigida"`.
- Antes de activarlo en producción: aplicar la migración, conceder la
  cortesía a la propia organización del titular y entonces fijar la variable
  (orden completo en `docs/PROCESO_PILOTOS.md` §0).

#### Qué puede hacer cada estado con el corte activo

| Situación | ¿Trabaja? | Comentario |
| --- | --- | --- |
| Licencia vigente (inicio ≤ hoy ≤ vence) | ✅ Todo | El día de `vence` cuenta como día de acceso |
| Sin licencia / vencida / cancelada | ❌ Suspendida | Ve «Acceso suspendido» en cualquier ruta de negocio |
| Licencia encadenada que empieza mañana | ❌ Hoy | Se activa sola al llegar `inicio` |
| Panel de operador | ✅ Siempre | No depende de ninguna organización |
| Usuario suspendido | ✅ Solo: iniciar/cerrar sesión, `/organizaciones` (cambiar de organización), aceptar invitaciones, páginas legales **y el circuito de compra** | Nada de datos: ni presupuestos, clientes, catálogo, PDFs ni descargas |

Notas de diseño del corte:

- Es **por organización**, no por usuario: crear una organización nueva no
  sirve para escapar (la nueva también carece de licencia).
- Un registro nuevo sin piloto acordado ve la suspensión desde el minuto uno:
  el período de prueba lo concede el titular (7 días desde el panel) según el
  proceso de `docs/PROCESO_PILOTOS.md`.
- El corte se evalúa en cada petición: una licencia que venció anoche suspende
  en el siguiente clic.
- Verificación sin tocar producción (Supabase → SQL Editor):
  `BEGIN; SELECT set_config('cotizat.organization_id', '<id>', true); SELECT cotizat_security.organization_has_license(<id>); ROLLBACK;`

### Avisos de vencimiento por correo

- Botón «Enviar avisos de vencimiento» (visible solo cuando alguna licencia
  vence en 15 días o menos). Escribe a los **administradores activos** de cada
  organización por Resend; en PostgreSQL los correos salen de
  `cotizat_security.organization_admin_emails(id)`, SECURITY DEFINER guardada
  por la marca de operador (una sesión de cliente obtiene cero filas).
- Cada envío queda anotado en la propia licencia («[fecha] Aviso de
  vencimiento enviado a …») y no se repite el mismo día aunque se pulse dos
  veces. Un fallo del proveedor se reporta y **no** se anota: puede
  reintentarse en el momento.
- Sin `RESEND_API_KEY`/`COTIZAT_EMAIL_FROM` el panel lo explica en vez de
  fallar en silencio.

### Corrección de visibilidad del panel (bug latente)

La política `cotizat_org_select` de la revisión `c93e7a4d20f1` solo devolvía
las organizaciones donde el usuario tiene membresía, así que en producción el
panel era **ciego a las organizaciones de clientes** (solo veía las del
propio titular, lo que disimulaba el fallo). La nueva política mantiene la vía
de membresía intacta y añade la de la marca de operador — el panel lista
nombres para administrar licencias; los datos de negocio siguen aislados.

### Pruebas

29 pruebas nuevas en `tests/test_licencias_acceso.py` (interruptor, corte en
el camino real de `get_db`, pantalla de suspensión, recibo –válido, numerado
y solo de pago–, avisos –destinatarios, constancia, deduplicación, fallos– y
guardas de las funciones SQL). Suite completa: **391 passed, 5 skipped**.

---

## 7. Post-venta al cliente (18/08/2026): aviso de activación y recibo propio

Tras verificar en staging el flujo de compra con cobro manual, se cerró lo que
faltaba **del lado del comprador**. Migración: **`c7f1a3b9d425`**
(`docs/staging_upgrade_c7f1a3b9d425.sql`).

### Al activar una compra, el cliente recibe un correo

`POST /admin/compras/{id}/activar` envía ahora un aviso a la dirección que
registró la compra: plan, importe, método de cobro, **fecha de inicio y de
vencimiento** (`dd/mm/aaaa`, también en el asunto) y el **recibo PDF adjunto**.
Plantillas `app/templates/emails/plan_activado.html` / `.txt`.

El envío es **best-effort y nunca revierte la activación**: si Resend falla o no
hay credenciales, la licencia queda activa igualmente y el panel muestra el
motivo, para que el operador pueda avisar por otra vía.

### El cliente puede descargar su recibo

- Ruta del cliente: **`GET /pago/recibo/{compra_id}.pdf`** (attachment,
  `Cache-Control: no-store`). Solo sirve compras **de su propia organización**,
  en estado `activa` y con importe > 0.
- Enlace «Descargar recibo (PDF)» en la tarjeta **«Tu plan»** de
  `/configuracion`, para la última compra activada con importe.
- Es **el mismo documento** que genera el enlace del operador
  (`/admin/licencias/{id}/recibo.pdf`): mismo número `CT-000NNN`, mismo período
  y el mismo pie de «documento comercial sin validez fiscal».

**Por qué hizo falta una migración.** `licencias` está protegida por RLS de
operador (`f4c1d8e37a95`): una sesión de cliente no puede leerla ni para su
propia organización. En vez de abrir esa puerta, la activación **copia el
período concedido a `compras_plan`** (`licencia_inicio` / `licencia_vence`,
tabla tenant), y la ruta del cliente arma con esos datos el objeto que espera el
generador de recibos. El aislamiento del registro de licencias queda intacto.

---

## 8. El corte no encierra al cliente (18/08/2026)

Al preparar el encendido de `COTIZAT_EXIGIR_LICENCIA` se encontró un fallo que
habría estropeado el circuito de cobro: **una organización vencida no podía
renovar**. El corte vive en `get_db`, la puerta común de todas las rutas de
organización, y las rutas de compra colgaban de ella; con la licencia caducada,
`/pago/comprar`, la confirmación y el recibo devolvían 403. El cliente leía en
la pantalla de suspensión que podía renovar y, al intentarlo, chocaba con la
misma pared.

### Cómo se resolvió

- **`get_db_renovacion`** (`app/database.py`): misma autenticación, membresía,
  organización activa y RLS de tenant que `get_db`, **sin** comprobar la
  vigencia de la licencia.
- La usan **solo** las cuatro rutas de compra de `app/routers/pagos.py`. No
  abren nada más: por ahí no se llega a presupuestos, clientes ni catálogo.
- La pantalla «Acceso suspendido» gana el botón **«Renovar mi plan»**.

Resultado operativo: un cliente vencido se renueva **solo** —compra con su
comprobante, el operador la activa desde `/admin/compras`, el acceso vuelve al
instante y le llega el correo con su recibo—. Sin esto, cada renovación habría
acabado en el buzón de soporte.

### Por qué no se romperá otra vez

`tests/test_licencias_acceso.py` recorre el árbol de rutas de la aplicación y
exige que **exactamente** las rutas de compra usen la puerta sin corte: ni una
de más (sería un agujero) ni una de menos (volvería la trampa). Se comprobó que
el test muerde de verdad revirtiendo las rutas a `get_db` y viendo fallar la
suite.

### Orden para encender el interruptor

1. Conceder **licencia de cortesía** a la organización del titular
   (`/admin/licencias`, tipo `cortesia`, duración larga). Sin esto, el titular
   se corta a sí mismo — el panel de operador seguiría accesible, su
   organización no.
2. `COTIZAT_EXIGIR_LICENCIA=true` en Vercel (Production) + redeploy.
3. Verificar en `/readyz` que aparece `"licencias": "exigida"`.

---

## 9. Gestionar un cliente en dos clics (18/08/2026)

El panel ya mostraba todo lo necesario, pero **actuar** costaba demasiado. Para
conceder o retirar acceso había que bajar hasta el formulario del final,
localizar la organización en un desplegable, rellenar cinco campos y enviar.
Con un cliente da igual; con cincuenta, cada gestión trivial se convierte en
cuatro o cinco gestos y en el riesgo real de operar sobre la fila equivocada:
el desplegable no sabe en qué cliente estabas mirando.

Ahora la unidad de trabajo es **la fila del cliente**.

### Cómo se usa

1. **Clic en la fila** del cliente (o `Enter` si se navega con el teclado).
   Debajo se despliega su ficha, con la fila resaltada y el chevron girado.
2. **Clic en la acción**. Y ya está.

La ficha tiene cuatro bloques:

| Bloque | Para qué |
| --- | --- |
| **Conceder / Renovar** | Cuatro botones de un solo clic: pago 1 año, pago 1 mes, prueba 7 días, cortesía 1 mes. El importe lo pone el plan publicado; no se teclea. |
| **Caso especial** | El formulario completo de siempre (tipo, duración, importe atípico, método, referencia, nota) para lo que se sale de lo normal. |
| **Suspender acceso** | Corta el acceso del cliente. Solo aparece si hay algo vigente que cortar. Pide confirmación. |
| **Historial** | Sus licencias con estado, recibo PDF de las de pago y cancelación individual. |

El título del primer bloque cambia según el caso: dice **Renovar** y recuerda
la fecha de fin cuando el cliente ya tiene acceso, porque una renovación se
encadena al final del período vigente y no resta días.

### Suspender actúa sobre la cadena, no sobre una licencia

Cancelar una licencia suelta **no** corta el acceso: al encadenarse las
renovaciones, una organización puede tener varias activas y seguir dentro por
la siguiente. Ese es el fallo silencioso peligroso: el operador cree haber
suspendido y el cliente sigue trabajando.

Por eso `suspender_organizacion` (`app/services/licencias.py`) cancela **todas**
las licencias activas que cubren hoy o empiezan después, y el mensaje dice
cuántas fueron. Si no había ninguna vigente, avisa en vez de callar.

Suspender **no borra datos**: se puede volver a conceder acceso en cualquier
momento, y el propio cliente puede renovarse solo (§8).

### Detalles de implementación

- Rutas nuevas: `POST /admin/organizaciones/{id}/conceder` y
  `POST /admin/organizaciones/{id}/suspender`. La organización viaja **en la
  URL**, que es lo que elimina el desplegable y el error de fila.
- El campo `volver` decide a qué panel se regresa, contra una **lista blanca**
  (`_DESTINOS_PANEL` en `app/routers/admin.py`). Un `volver` externo se ignora
  y cae a `/admin`: un parámetro de retorno sin filtrar es una redirección
  abierta.
- El despliegue de la ficha vive en `app/static/js/admin-panel.js`, sin
  `innerHTML` ni estilos en línea (la CSP del proyecto usa `nonce`). Las
  acciones son formularios POST normales: **sin JavaScript el panel sigue
  siendo operativo**, solo que las fichas aparecen desplegadas.
- Al ordenar o filtrar la tabla, cada ficha se mueve pegada a su fila; nunca
  puede quedar bajo el cliente equivocado.

### Pruebas

En `tests/test_licencias.py`, siete pruebas nuevas: que cada fila trae su ficha
enlazada por `aria-controls`, que conceder no exige elegir organización ni
teclear el importe, que una prueba no cobra, que suspender corta la cadena
entera, que suspender sin acceso vigente avisa, que las rutas rápidas son solo
de operador y que `volver` no admite destinos externos.

---

## 10. El operador nunca se queda fuera (nota del 18/08/2026)

Vale la pena dejarlo escrito porque durante un tiempo se creyó lo contrario, y
el error condicionaba el orden de la puesta en producción.

Las rutas `/admin/*` cuelgan de **`get_operator_db`** (`app/database.py`), que
comprueba que quien entra sea operador pero **no comprueba licencia**. Por eso:

- Encender `COTIZAT_EXIGIR_LICENCIA=true` **no** deja al titular sin panel,
  aunque su propia organización esté suspendida.
- La licencia de cortesía a la organización propia puede concederse **antes o
  después** de activar el corte, indistintamente: siempre se puede entrar al
  panel y concedérsela.
- Lo que sí queda cortado sin licencia propia es el **uso normal del producto**
  en la organización del titular —presupuestos, clientes, catálogo—, porque eso
  cuelga de `get_db`, que sí comprueba vigencia.

En resumen: no existe forma de quedarse encerrado fuera del sistema por
encender el interruptor. El único orden que sí es obligatorio es tener aplicada
la migración y **desplegado el PR #38** antes de activarlo, porque la prueba
gratuita que cubre a las organizaciones nuevas viaja en ese PR.
