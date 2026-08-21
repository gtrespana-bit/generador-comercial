# Cobro y licencias (E1-059 / E1-060)

Fecha: **16/08/2026**. Documento de decisión: recoge la investigación.

> **Decisión adoptada (16/08/2026): cobro manual para el piloto** (opción B).
> La vía A (autónomo en España + Stripe) queda acordada como paso previo al
> cobro recurrente. E1-060 está implementado al completo: panel de operador,
> recibo PDF, corte automático con `COTIZAT_EXIGIR_LICENCIA` y avisos de
> vencimiento por correo (ver `docs/PANEL_DE_OPERADOR.md` §6 y
> `docs/PROCESO_PILOTOS.md`).
>
> **Actualización 20/08/2026.** Stripe Checkout está integrado (tarjeta, Apple
> Pay, Google Pay) junto al cobro manual. No sustituye Pago móvil ni cripto:
> Stripe no opera métodos locales en Venezuela, Colombia o Perú. Pasos de
> panel en `docs/STRIPE.md`.

> Aviso: esto no es asesoramiento fiscal ni legal. Antes de cobrar al primer
> cliente conviene una consulta con un asesor en España (y, si se factura desde
> Venezuela, también allí).

---

## 1. El condicionante que lo define todo

CotizaT se pensó para clientes en Latinoamérica, pero **el problema no es dónde
está el cliente, sino desde dónde se cobra**:

- **Stripe no opera en Venezuela.** No hay forma de darse de alta con una
  entidad venezolana.
- **Wise y Payoneer** imponen restricciones fuertes a residentes venezolanos
  (Wise directamente veta el país; Payoneer exige una cuenta bancaria no
  venezolana para retirar).
- **Paddle y Lemon Squeezy** (modelo *merchant of record*, que además resuelve
  los impuestos) exigen una entidad legal en un país soportado. Venezuela no lo
  es.

**Dato decisivo aportado por el titular (16/08/2026):** es de **nacionalidad
española y reside también en España**, trabajando temporalmente entre España y
Venezuela. Eso cambia el escenario por completo: la vía española está abierta.

---

## 2. Opciones reales

### Opción A — Autónomo en España + Stripe *(recomendada para cobrar en serio)*

Darse de alta como autónomo (**modelo 036** en Hacienda y **RETA** en Seguridad
Social, en ese orden) y usar Stripe con la entidad española.

**A favor**
- Stripe funciona con normalidad: cobro con tarjeta desde cualquier país,
  suscripciones, reintentos y cancelaciones ya resueltos.
- Factura española válida: desaparece la ambigüedad de «documento comercial no
  fiscal» para **la venta de CotizaT** (ojo: eso no cambia el alcance de los
  documentos que la app genera para los clientes, que siguen siendo no
  fiscales).
- Comisión baja: ~2,9 % + 0,30 € frente al ~5 % + 0,50 $ de un *merchant of
  record*.
- Da una razón social real para `COTIZAT_LEGAL_ENTITY` y para los términos.

**En contra**
- Cuota de autónomo (tarifa plana ~88 €/mes el primer año; después por tramos).
- Obligaciones trimestrales: IVA (modelo 303) e IRPF (modelo 130).
- Si se vende a **consumidores particulares de la UE** por encima de
  10.000 €/año, hay que aplicar el IVA del país del cliente y declarar por
  **ventanilla única OSS** (modelo 369). Con clientes latinoamericanos y/o
  empresas esto normalmente no aplica, pero conviene tenerlo presente.
- Requiere decidir la residencia fiscal con criterio: si se reside la mayor
  parte del año en Venezuela, la situación es mixta y **hay que consultarlo**.

### Opción B — Cobro manual *(recomendada para el piloto inmediato)*

Acordar el pago por transferencia, Zelle, Binance o Pago Móvil, y activar la
cuenta a mano.

**A favor**
- Cero integración, cero comisiones de pasarela, disponible hoy.
- Con 5–20 clientes de piloto es perfectamente operable.
- No bloquea nada: se puede empezar así y migrar a Stripe después.

**En contra**
- Sin recibo automático ni renovación automática: todo se lleva a mano.
- No escala más allá de unas pocas decenas de clientes.
- Cobrar de forma recurrente sin alta fiscal **no es sostenible**: en cuanto la
  actividad es habitual, hay que regularizarla.

### Opción C — Merchant of record (Paddle / Lemon Squeezy)

Solo viable **con la entidad española ya creada**. Cobra ~5 % + 0,50 $ pero se
encarga del IVA/OSS de todo el mundo.

Tiene sentido si la venta internacional a particulares crece y la carga fiscal
del OSS se vuelve pesada. **Hoy no compensa**: más caro y resuelve un problema
que todavía no existe.

### Recomendación

1. **Ahora, para el piloto**: opción B (manual). No frena el desarrollo.
2. **Antes de cobrar de forma recurrente**: opción A (autónomo en España +
   Stripe), que es la única que sostiene el cobro habitual con factura válida.
3. **Más adelante, si hace falta**: reevaluar la opción C.

---

## 3. E1-060 — Registro interno de licencias

**Decisión del titular (16/08/2026): debe vivir _dentro_ de la aplicación**, en
un panel de administración propio.

### Qué implica (y por qué no es trivial)

Hoy **no existe** ningún concepto de superadministrador: toda la autorización
de CotizaT se apoya en la **membresía de una organización**, y todas las tablas
de negocio son *tenant* (llevan `organizacion_id` y están protegidas por RLS).
Una licencia **no pertenece a ninguna organización**: es un dato del negocio del
titular *sobre* una organización. No encaja en el modelo actual, así que hay que
diseñarlo con cuidado:

1. **Tabla no-tenant** (p. ej. `licencias`), fuera de `TenantMixin`, con su
   propia política RLS: legible **solo** por el rol operador, nunca por el rol
   de aplicación de un cliente. Es el punto delicado: una licencia mal expuesta
   filtraría a un cliente cuánto paga otro.
2. **Rol de operador del producto**, distinto de los roles de organización, con
   una lista explícita de cuentas autorizadas por variable de entorno (no una
   columna que pueda modificarse desde la propia aplicación).
3. **Panel `/admin/licencias`**: alta, renovación, estado (activa, vencida,
   cancelada), importe, método de cobro y notas. Protegido igual que el resto:
   CSRF, CSP con nonce, sin datos en GET.
4. **Recibo en PDF** con los datos del cliente y el período pagado, reutilizando
   el generador existente (`app/services/pdf.py`).
5. **Auditoría**: quién creó o modificó cada licencia y cuándo.

### Riesgo principal a vigilar

El panel de operador es, por definición, **una excepción al aislamiento
multi-tenant** que el resto del sistema defiende. Debe:

- no permitir **leer datos de negocio** de ninguna organización (solo el hecho
  de la licencia: quién, cuánto, hasta cuándo);
- estar cubierto por pruebas que fallen si un usuario normal alcanza la ruta;
- quedar fuera del alcance de las políticas de tenant, sin debilitarlas.

Por eso conviene abordarlo **como su propio bloque**, no de pasada.

---

## 4. Estado y siguiente paso

| Pieza | Estado |
| --- | --- |
| E1-053 Preguntas frecuentes | ✅ `/legal/preguntas` |
| E1-054 Alcance del soporte | ✅ `/legal/soporte` §2–§3 |
| E1-055 Reporte de errores | ✅ `/legal/soporte` §5 |
| E1-059 Método de cobro | ✅ **decidido (16/08/2026): cobro manual para el piloto**; Stripe+autónomo antes del cobro recurrente |
| E1-060 Registro de licencias | ✅ panel `/admin/licencias` desplegado en producción el 16/08/2026; recibo PDF, corte automático y avisos de vencimiento implementados el 16/08/2026 noche (migración `b7c4a9e2d31f`) |
| E1-061 Activación manual de pilotos | ✅ proceso documentado en `docs/PROCESO_PILOTOS.md` (16/08/2026) |

El registro interno hacía falta se cobrase como se cobrase; con la decisión de
cobro manual tomada, las tres piezas que esperaban (recibo, corte y avisos)
quedaron construidas en la misma sesión.

**Actualización 18/08/2026.** El titular ensayó el circuito completo en staging
(compra con comprobante → activación desde `/admin/compras` → plan visible) y lo
dio por bueno. Se cerró después el lado del comprador, que era lo único
realmente «manual» que quedaba: al activar la compra el cliente **recibe un
correo** con la fecha de vencimiento y el **recibo PDF adjunto**, y puede
volver a descargarlo cuando quiera desde `/configuracion`
(`GET /pago/recibo/{compra_id}.pdf`, migración `c7f1a3b9d425`). Detalles en
`docs/PANEL_DE_OPERADOR.md` §7. Sigue sin haber renovación automática: eso llega
con Stripe.

**Corte automático (18/08/2026).** Con el circuito de compra ya probado, el
interruptor `COTIZAT_EXIGIR_LICENCIA` pasa a ser accionable. Antes de tocarlo
hubo que resolver una contradicción del diseño: el corte protegía *todas* las
rutas de la organización, incluidas las de compra, así que una organización
vencida recibía 403 al intentar pagar. La suspensión era una trampa sin salida y
cada renovación habría acabado en soporte.

La solución es una segunda puerta, `get_db_renovacion` (`app/database.py`), que
hace exactamente lo mismo que `get_db` —sesión, membresía, organización activa,
RLS de tenant— **menos** comprobar la vigencia de la licencia. La usan solo las
cuatro rutas de `app/routers/pagos.py` que hacen falta para renovar; ninguna de
ellas expone datos de negocio (presupuestos, clientes, catálogo). El resto del
producto sigue detrás de `get_db`. La pantalla «Acceso suspendido» ofrece ahora
el botón «Renovar mi plan».

Que esas rutas —y solo esas— usen la puerta sin corte no se deja a la memoria:
`tests/test_licencias_acceso.py` lo comprueba recorriendo el árbol de rutas de
la aplicación, de modo que añadir mañana una ruta de compra bajo `get_db`, o
colar la puerta sin corte en una ruta que no sea de pago, rompe la suite.

**Recordatorio automático (18/08/2026, noche).** El aviso de vencimiento dejó
de depender de un botón manual: un cron de Vercel (`vercel.json` → `crons`,
ruta `/api/cron/recordatorios-vencimiento` protegida con `CRON_SECRET`) envía
un recordatorio premium a 5 y 1 día antes de vencer, una única vez por hito y
licencia, con CTA al checkout `/pago` y `Reply-To` a soporte. **Operativo
desde el 19/08/2026**: PR #40 fusionado, `CRON_SECRET` configurada en
Production, job verificado en Settings → Cron Jobs; la primera ejecución
automática es el 19/08 a las 13:00 UTC. Detalle en
`docs/PENDIENTES_OPERATIVOS.md` §9.

---

## 5. Prueba gratuita de 7 días (18/08/2026)

El corte automático no se podía encender tal cual: con `COTIZAT_EXIGIR_LICENCIA`
activo, **toda organización recién registrada nacía suspendida**. Quien se
apuntara vería la pantalla de «Acceso suspendido» antes de haber visto el
producto. La prueba gratuita es el prerrequisito que cierra ese hueco.

### 5.1 Qué recibe el cliente

Al crear su **primera organización** se le concede automáticamente una licencia
de `origen='prueba'`, importe 0 y **7 días** de acceso completo
(`COTIZAT_DIAS_PRUEBA`, tope duro de 90 días aplicado también dentro de la base
de datos). No pide tarjeta ni datos de pago. Al terminar, cae en el circuito de
compra normal, que ya existía.

Las pruebas **no generan recibo**: `app/services/recibo_licencia.py` exige
`origen='pago'` e importe mayor que cero. No hay nada que justificar
fiscalmente cuando no ha habido cobro.

### 5.2 El abuso que hay que impedir

La objeción evidente a cualquier prueba gratuita es el **reciclaje de cuentas**:
registrarse una y otra vez para no pagar nunca. Las defensas, por orden de
importancia:

**1. Una prueba por identidad de correo, para siempre.** Es la defensa real. Se
registra el correo **normalizado** en `pruebas_concedidas`, con restricción
única. Normalizar significa neutralizar los alias que el proveedor trata como
la misma cuenta: se quitan los puntos en Gmail/Googlemail, se recorta
`+etiqueta` en la decena de proveedores que la soportan, y `googlemail.com` se
unifica con `gmail.com`. Así `fulano.detal+uno@gmail.com` y `fulanodetal@gmail.com` son
la misma identidad y solo obtienen una prueba entre las dos.

La marca **sobrevive al borrado de la organización** (la clave foránea es
`ON DELETE SET NULL`): borrar la cuenta y volver a registrarse no devuelve la
prueba, porque la prueba se consumió igual.

**2. Dominios desechables bloqueados en el registro.** Los proveedores de correo
de usar y tirar no pueden ni registrarse — decisión del titular, más estricta
que dejarlos entrar sin prueba. La lista vive en
`app/services/identidad_registro.py`.

**3. La licencia es de la ORGANIZACIÓN, nunca del usuario.** Quien quiera una
segunda organización paga un plan para ella. Si la licencia fuera por usuario,
uno solo podría pagar una vez y montar diez organizaciones con diez personas
dentro. Por eso una segunda organización **no** trae otra prueba: la marca es
por identidad de correo y ya está gastada.

**4. IP del alta, hasheada y solo informativa.** Se guarda un hash con sal
(`COTIZAT_HASH_SALT`, con reserva en `SUPABASE_SECRET_KEY`) para que el panel
pueda **señalar** patrones de registros repetidos. Nunca bloquea a nadie de
forma automática: una IP compartida es lo normal en oficinas y operadores
móviles, y bloquear por ella castigaría a clientes legítimos.

### 5.3 Por qué la concesión vive dentro de la base de datos

Quien se registra es un cliente, y la RLS de `f4c1d8e37a95` reserva toda
escritura sobre `licencias` a sesiones de operador. La prueba se concede con
`cotizat_security.grant_trial_license(...)`, una función `SECURITY DEFINER`
(migración `a3d9c1e75b28`).

Está construida asumiendo que la llamará un hostil:

- Solo concede a la organización del claim de la sesión, así que nadie regala
  licencias a organizaciones ajenas.
- Solo crea licencias de `origen='prueba'` e importe 0: aunque se la llame con
  parámetros manipulados, **no puede fabricar un año de acceso de pago**.
- No concede si la organización ya tuvo *cualquier* licencia.
- Fija `search_path`, sin lo cual un esquema malicioso secuestraría la función.

Y hace **las dos escrituras a la vez** —la marca de identidad y la licencia—
porque separarlas dejaría dos formas de romperse: una caída entre ambas
produciría o una prueba repetible indefinidamente, o un cliente marcado y sin
sus días. La marca se inserta primero con `ON CONFLICT DO NOTHING`; si no
devuelve fila, no hay licencia. Así la carrera entre dos altas simultáneas del
mismo correo **se resuelve en la base, no en Python**.

Detalle de implementación que costó encontrar: las tablas llevan
`FORCE ROW LEVEL SECURITY`, que se aplica **también al propietario**, así que
`SECURITY DEFINER` por sí solo no bastaba. La función eleva
`cotizat.es_operador` de forma local a la transacción y **lo restaura en las
cuatro salidas**, incluida la de excepción: la sesión del cliente nunca hereda
la marca. La elevación cubre además el `SELECT` de comprobación, no solo los
`INSERT` — dejarla después habría hecho que la lectura de `licencias` no
devolviera filas y se concediera prueba a quien ya la tuvo, que es un fallo
*abierto*.

En SQLite (escritorio y pruebas) no hay RLS ni funciones de seguridad: la
aplicación escribe directamente y la restricción única sigue protegiendo.

### 5.4 Qué se comprueba

`tests/test_prueba_gratuita.py` (50 casos) cubre la normalización de correos, la
detección de desechables, la concesión, el rechazo de la segunda prueba, la
atomicidad y —como no hay PostgreSQL en el entorno de pruebas— un bloque de
invariantes sobre el texto del SQL: `search_path` fijado, guarda de
organización, imposibilidad de crear licencias de pago, duración acotada,
`ON CONFLICT`, restauración en las cuatro salidas y orden elevación → lectura.

### 5.5 Puesta en producción

1. ✅ **Hecho.** Aplicar `docs/staging_upgrade_a3d9c1e75b28.sql` con el rol
   administrativo de Supabase (**no** con `cotizat_app`: el rol que lo ejecuta
   queda como propietario de la función y es el privilegio con el que corre).
   El fichero está generado desde la propia migración con
   `alembic upgrade --sql`, trae guarda de versión previa y una prueba de humo
   al final. *(Aplicado por el titular el 18/08/2026, sin incidencias.)*
2. ⏳ Comprobar que `/readyz` responde con `"alembic": "head:a3d9c1e75b28"`.
3. ✅ **Hecha.** Licencia de cortesía a la organización del titular.
4. ⏳ Solo entonces, `COTIZAT_EXIGIR_LICENCIA=true` en Vercel (Production) y
   redeploy. Verificar `"licencias": "exigida"` en `/readyz`.

El orden importa: encender el interruptor antes del paso 1 dejaría suspendida a
toda organización nueva, que es justo lo que la prueba viene a evitar.

**Matiz sobre el paso 3, para no repetir un error de razonamiento:** la
cortesía **no** es un prerrequisito del paso 4. El panel `/admin/*` cuelga de
`get_operator_db`, que no comprueba licencia, así que el operador entra aunque
su propia organización esté suspendida y siempre puede concederse una licencia
desde dentro. Lo único bloqueante de verdad era la migración.

**Condición añadida tras el anuncio público (§5.6):** el paso 4 exige además
que el **PR #38 esté fusionado y desplegado**. El anuncio y la concesión de la
prueba viajan en ese PR; encender el corte antes dejaría suspendida a cada
organización recién registrada, porque todavía no habría prueba que la cubra.

**Cómo revertir:** `COTIZAT_EXIGIR_LICENCIA=false` y redeploy. El interruptor
solo decide si se comprueba la vigencia; no borra ni altera ninguna licencia.

### 5.6 El anuncio público de la prueba (18/08/2026)

Una prueba que no se anuncia no cumple ninguna función comercial: durante unos
días los 7 días existieron en el registro sin que ninguna página los
mencionara, así que nadie llegaba a pedirlos.

**Dónde se anuncia.** En los cuatro puntos donde alguien decide: la landing
(`/` y `/conocer`, once condicionales distintos), la página de pago y la de
acceso.
El CTA principal del hero pasó a apuntar a **`/acceso`**, que es donde está el
registro real; las tarjetas de plan siguen yendo a `/pago`.

**Cómo se apaga.** Todo cuelga de dos globales de Jinja declaradas en
`app/routers/common.py` que son **funciones, no valores**
(`dias_de_prueba` y `hay_prueba_gratuita`). Jinja cachea la plantilla
compilada, no su resultado, así que se evalúan en cada render: poner
`COTIZAT_DIAS_PRUEBA=0` retira el anuncio de las cuatro páginas y la landing
revierte a «Ver planes», **sin redesplegar ni tocar plantillas**. Lo fija
`test_apagar_la_prueba_retira_el_anuncio`, que recorre las cuatro páginas con
la prueba apagada; existe porque el día que se retire la oferta lo que no puede
pasar es que la web siga prometiéndola.

**Excepción deliberada.** En `/pago` el bloque se omite si llega un `msg`:
quien viene rebotado ya agotó la prueba y volver a ofrecérsela sería una burla.

**Textos que comprometen al producto** y deben seguir siendo ciertos: no se
pide tarjeta, no hay cobro automático, y al terminar la prueba la cuenta deja
de generar presupuestos nuevos **sin borrar nada**. Si alguna de las tres deja
de cumplirse, hay que cambiar la web el mismo día.
