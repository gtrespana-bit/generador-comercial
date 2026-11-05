# Monitorización y diagnóstico de la operación web (E3-024)

Fecha: **16/08/2026** · Suite: **453 passed, 6 skipped** · Sin migración nueva
(el head al cerrar ese bloque era `a3d7e9c1b5f2`; este bloque no cambió esquema).

> Estado actual: el head es `d6e2f9c4b8a1`; ver
> `docs/PUNTO_DE_CONTINUACION.md`. Esta página conserva el histórico de E3-024.

Con este bloque queda completo el **cierre funcional y operativo de la Etapa 3**
(E3-016 a E3-024). El operador puede ahora ver de un vistazo si el despliegue
está sano y qué errores no capturados están ocurriendo, sin exponer datos de
ningún cliente.

---

## 1. Qué hay y dónde

| Pieza | Ruta / archivo | Acceso |
|---|---|---|
| Liveness (proceso vivo, sin tocar dependencias) | `GET /healthz` | público (ya existía) |
| Readiness (configuración + dependencias + head de Alembic + rol runtime) | `GET /readyz` | público (ya existía) |
| **Panel de operación** | `GET /admin/operacion` | **solo operador** (`COTIZAT_OPERADORES`) |
| Registro de errores no capturados | `app/services/operacion.py` | proceso |
| Middleware de captura | `RegistroErroresMiddleware` (en `main.py`) | transparente |

El panel de licencias (`/admin/licencias`) enlaza con el de operación.

## 2. Panel de operación (`/admin/operacion`)

Tres bloques, todos sin datos de tenant:

1. **Estado del despliegue** — los mismos chequeos de `/readyz`, presentados
   con su estado (ok / error / no aplica). Un 503 de readiness se ve aquí como
   «CON ERRORES» con el detalle de cada chequeo.
2. **Hechos operativos** — backend (`sqlite`/`postgresql`), modo efímero
   (serverless sin escritura en disco), head de Alembic esperado, backend de
   almacenamiento, contador de frecuencia, exigencia de licencias, tiempo del
   proceso activo, errores registrados y operadores configurados.
3. **Errores recientes no capturados** — tabla con última vez, método y ruta,
   tipo, mensaje y ocurrencias, agregados por ruta + tipo + mensaje.

## 3. Registro de errores: qué captura y qué no

- **Captura:** cada excepción que escapa de las rutas (las que hoy terminan
  en un 500 genérico). El middleware la registra y la **relanza intacta**: la
  semántica HTTP no cambia y el 500 lo sigue produciendo el servidor.
- **Privacidad:** la ruta se registra **sin query string** (ahí viajan los
  tokens) y los segmentos con forma de token se sustituyen por `<token>`;
  los mensajes se sanean para no filtrar credenciales (igual que `/readyz`).
- **Acotado:** 200 entradas agregadas como máximo; un fallo en bucle no agota
  la memoria, solo incrementa `ocurrencias`.
- **No captura:** excepciones ya manejadas por la aplicación (errores de
  negocio que devuelven su página con aviso), que son flujo normal.

## 4. Limitación declarada (resuelta el 20/10/2026, Fase 0.2)

El registro original vivía **en la memoria del proceso** y se perdía al
reiniciar; en serverless cada instancia guardaba el suyo. Esa limitación
quedó cerrada con un **sumidero propio** (sin SDK de terceros, para no
pagar coste por petición ni exportar trazas fuera):

- Cada huella (método + ruta saneada + tipo + mensaje) se persiste en la
  tabla `errores_internos` mediante `app/services/errores_internos.py`,
  *best-effort*: solo cuando ya hay un 500, en su propia sesión y sin que
  un fallo del registro pueda romper la respuesta. En PostgreSQL la
  escritura entra por la función SECURITY DEFINER
  `cotizat_security.registrar_error_interno` (el llamante puede no tener
  sesión) y la lectura es solo del operador (RLS).
- La fila guarda la **traza** de la última ocurrencia (redactada: las
  credenciales embebidas en URLs se sustituyen antes de guardarla),
  además de ocurrencias y primera/última vez. El panel (Sistema › Estado)
  lee de la base, muestra la traza bajo demanda y permite marcar la
  huella como **resuelta**; si el fallo reaparece, la marca se limpia
  sola y vuelve a contar como nueva.
- Una huella nueva —o resucitada tras estar resuelta— dispara un correo
  al buzón de avisos (tope anti-tormenta: 5 por hora y proceso). El cron
  diario de mantenimiento envía el parte de huellas activas en las
  últimas 24 h (silencio si no hay ninguna) y poda las resueltas sin
  actividad en 90 días.
- Interruptor: `COTIZAT_ERRORES_BD=false` vuelve al comportamiento
  histórico (solo buffer en memoria). Si la tabla aún no existe (ventana
  entre el despliegue y la migración), la persistencia se omite en
  silencio y el panel cae al buffer declarándolo en la nota.

Lo que sigue sin cubrir este sumidero, a propósito: la caída total de la
plataforma (Vercel o la BD fuera) no genera fila ni correo — eso lo vigila
el monitor externo de `/readyz`— y los errores «controlados» que la
aplicación ya traduce a páginas con aviso no son 500 y no entran aquí.

## 5. Verificación

- Pruebas nuevas: `tests/test_operacion.py` (12): agregación y límite del
  registro, saneamiento de tokens y credenciales, middleware que captura y
  relanza (500 intacto), diagnóstico con salud y hechos, panel solo para el
  operador y enlace desde licencias.
- Suite completa: **453 passed, 6 skipped**; 63 plantillas, `compileall`,
  JavaScript, lock (42 paquetes) y `git diff --check` en verde; simulación de
  Vercel read-only correcta. `/healthz` y `/readyz` sin cambios de
  comportamiento.

## 6. Alertas y vigilancia proactiva (E4-023, 19/08/2026)

Hasta ahora la detección de caídas era **reactiva** (alguien entra y ve que
falla). Con E4-023 hay dos capas:

### 6a. Verificación diaria con correo (código, ya operativo)

El mismo cron `/api/cron/mantenimiento` (02:00 UTC) ejecuta los chequeos de
`/readyz` (`app/services/mantenimiento.py` → `ejecutar_verificacion_diaria`).
Si algo falla, envía a **todos los operadores** (`COTIZAT_OPERADORES`) el
correo interno `emails/alerta_operador.{html,txt}` con los errores y el estado
de cada chequeo (sin exponer secretos: el readiness ya los sanea). Es un
correo **interno**: no aparece en el panel «Correos» (`/admin/emails`).

- Si está en verde no escribe a nadie y el resumen del cron lo refleja.
- Sin operadores configurados, no hay a quién escribir (y el resumen lo dice).
- Pruebas en `tests/test_mantenimiento_cron.py`.

### 6b. Vigilante externo de disponibilidad (panel del titular, pendiente)

La verificación diaria solo ve el estado **una vez al día**. Para enterarte de
una caída en minutos, el vigilante externo pide `GET https://cotizat.online/healthz`
(liveness, sin dependencias) cada 1–5 minutos y alerta por email/WhatsApp si
no responde `200`:

1. Crea una cuenta en un monitor de disponibilidad (p. ej. UptimeRobot,
   plan gratuito: 50 monitores a 5 min).
2. Añade un monitor HTTP(S) con URL `https://cotizat.online/healthz`,
   intervalo 5 min, alertas a tu buzón (y a `soporte@cotizat.online` si
   quieres un segundo canal).
3. Marca como **esperado** el 503 de `/readyz` solo si quieres vigilarlo
   también (el 503 es correcto cuando el despliegue no debe recibir tráfico);
   para disponibilidad pura, vigila `/healthz` (siempre 200 si el proceso
   vive).
4. Guarda las credenciales del monitor fuera del repositorio; no añadas el
   monitor como secreto de la app.

## 7. Estado del cierre de Etapa 3

Código completo en la rama (E3-016 a E3-024) y **migraciones `c2f6e8a1d934` y
`a3d7e9c1b5f2` aplicadas y verificadas en Supabase el 16/08/2026** (ver
`docs/PUNTO_DE_CONTINUACION.md` §0ter). Pendiente: desplegar el código de la
rama (hasta entonces `/readyz` del entorno migrado responde 503, esperado) y
ensayar el flujo real en staging. Después, según la puerta de salida del plan:
endurecimiento técnico de la Etapa 4 o el bloque funcional que el titular
decida. Validación comercial y catálogo real siguen aplazados (D-017).

## 8. `StringDataRightTruncation`: texto más largo que su columna (3/11/2026)

**Qué se vio.** El panel de errores registró un 500 en `POST
/presupuestos/nuevo` con
`psycopg.errors.StringDataRightTruncation: value too long for type character
varying(200)`. El `INSERT` que fallaba era el de `partidas`: el primer nombre
del lote (`Retirar juntas de piso en terraza de coralina`) era correcto, pero
otra línea del mismo presupuesto llevaba **el texto completo de las condiciones
de pago** (~400 caracteres) en el campo «nombre de la partida».

**Por qué tumba el guardado entero.** Los nombres viajan a dos columnas de
ancho distinto: `presupuesto_items.nombre` (`VARCHAR(250)`) y, por el guardado
automático del catálogo, `partidas.nombre` (`VARCHAR(200)`). PostgreSQL no
recorta: aborta la sentencia y el `flush` completo falla, así que el usuario
**pierde el presupuesto** y ve un 500. SQLite ignora el ancho declarado, de ahí
que la suite no lo detectara: el fallo solo existía en producción.

**Qué se hizo.** Una red única en `Session` (`before_flush`) recorta cualquier
texto a la anchura declarada en su columna antes de enviar la sentencia
(`app/services/limites_columnas.py`). Se recorta, no se rechaza: el presupuesto
se guarda con el nombre abreviado en vez de perderse. Cada recorte deja un
`WARNING` en los logs con el campo y la longitud original (nunca el texto), y
`_guardar_en_catalogos` recorta además **antes** de deduplicar para no chocar
contra `uq_partida_organizacion_nombre` cuando dos nombres largos solo difieren
a partir del carácter 201. En el editor, los campos de nombre llevan `maxlength`
para que el usuario vea el mismo tope que aplica el servidor.

**Diagnóstico rápido.** Si vuelve a aparecer un `DataError` de este tipo, la
columna culpable está en el mensaje (`character varying(N)`) y el campo, en el
primer parámetro del `INSERT` cuya longitud se pasa de `N`. El `WARNING
cotizat.limites_columnas` de los minutos previos dice qué cliente está usando
un campo corto para guardar un texto largo.

**Sobre el acceso del usuario afectado.** En el mismo caso se planteó por qué
una organización «sin cuenta activa» había podido guardar. El corte por
licencia (`COTIZAT_EXIGIR_LICENCIA`) comprueba
`estado = 'activa' AND inicio <= CURRENT_DATE AND vence >= CURRENT_DATE`, y
`vence` es un día **inclusivo** evaluado en UTC. La petición entró a las 23:55
UTC del 3/11: si la licencia (o la prueba de 7 días) vencía ese mismo día,
seguía vigente y el corte actuó a las 00:00 UTC del 4/11, que es cuando el
panel pasó a mostrarla como «Vencida». No hubo acceso indebido. Para
verificarlo:

```sql
SELECT id, estado, origen, inicio, vence, CURRENT_DATE AS hoy_utc,
       (estado = 'activa' AND inicio <= CURRENT_DATE AND vence >= CURRENT_DATE)
         AS daba_acceso_hoy
FROM public.licencias
WHERE organizacion_id = 43
ORDER BY inicio DESC, id DESC;
```

Se compara con la fecha/hora del error (`errores_internos.ultima_vez`) y no con
la de la consulta: un día de diferencia cambia la respuesta. El estado del
interruptor se ve en `/readyz` (`"licencias": "exigida"`).

## 9. `ECHECKOUTTIMEOUT`: la cola del pooler y la búsqueda de 11 s (5/11/2026)

**Qué se vio.** Dos 500 seguidos en el panel y en el buzón del titular, con el
misma organización (43) y el mismo mensaje:

```
(psycopg.errors.InternalError) ECHECKOUTTIMEOUT: checkout timeout
(server_id: ...) after 60000ms in Transaction mode
```

Uno en `GET /partidas/api/buscar` y otro en `POST /presupuestos/98/borrador`,
lanzados con **9 ms de diferencia**: las dos peticiones de la misma pestaña
cayeron a la vez. El mensaje del pooler aparecía en el `set_config` de
`app/database.py`, que es donde el listener `after_begin` reinstala los claims
de RLS: era el primer `execute` de la transacción, no la causa.

**Qué no era.** El tamaño del pool. En Vercel el motor ya usa `NullPool`
(`VERCEL` está definido), de modo que cada petición abre y cierra su propia
conexión y el reparto lo hace el pooler. El culpable era el **tiempo** de una
consulta, no el número de conexiones.

**Qué era.** `_aplicar_busqueda_catalogo` traducía cada palabra escrita a
`8 campos × N variantes` comparaciones `ILIKE` **sueltas**. Con sinónimos, una
búsqueda de seis palabras generaba **más de 250 condiciones**: la consulta que
falló en producción tiene exactamente 250 marcadores `$n`. Cada una obliga a
rehacer la concatenación de ocho columnas (una de ellas TOAST) por fila, y el
catálogo real tiene 15.000 partidas. Medido en la base de producción con
`EXPLAIN (ANALYZE)`:

| Forma de la condición | Tiempo |
| --- | --- |
| 250 condiciones `ILIKE` sueltas (la que falló) | **7.028 ms** |
| 48 condiciones `ILIKE` sueltas | 441 ms |
| Texto concatenado + una `~*` por palabra | **23–49 ms** |

Y `pg_stat_statements` lo confirma en tráfico real: esa consulta acumulaba
**95 ejecuciones con 11,1 s de media** (17 minutos de base de datos para una
sola forma de consulta). El editor la dispara en cada pausa del tecleo (rebote
de 140 ms), así que las peticiones se apilaban más rápido de lo que se
vaciaban, el pooler en modo Transaction se quedó sin huecos y, pasados 60 s de
cola, empezó a rechazar a todos. De ahí que el fallo fuera «siempre el mismo
usuario»: era el que estaba escribiendo en el buscador.

**Qué se hizo.**

1. **Una condición por palabra.** `common._texto_buscable_catalogo` concatena
   los campos una vez y `_condicion_de_un_grupo` compone **una expresión
   regular** con las variantes (`~* '(cable|conductor|cableado)'`). Misma
   semántica —la palabra puede estar en cualquier campo—, dos órdenes de
   magnitud menos de trabajo. En SQLite se mantiene el `OR` de `ILIKE`, que no
   tiene `REGEXP`. La descripción entra recortada a 600 caracteres.
2. **Tope de variantes** (`VARIANTES_MAXIMAS_POR_GRUPO = 12`): un grupo de
   sinónimos grande ya no puede volver a inflar la consulta.
3. **Un fallo de infraestructura no es un bug de producto.** `operacion.
   error_de_infraestructura` reconoce el `ECHECKOUTTIMEOUT`, el `TimeoutError`
   del pool y los «too many connections». Con eso: la respuesta es **503 con
   `Retry-After`** en lugar de un 500 (el middleware de registro ocupa la capa
   exterior, la única desde la que todavía se puede responder), **no se manda
   correo** —el fallo se sigue viendo en el panel con su traza— y el buscador
   del editor respeta el `Retry-After` en vez de reintentar con cada tecla.
4. **Un fallo de base no se disfraza de licencia vencida.** `licencias.
   organizacion_tiene_acceso` devolvía `False` ante cualquier excepción; con el
   pooler caído eso significaba «tu plan venció». Ahora un fallo de
   infraestructura se propaga (acaba en el 503) y solo los fallos de permisos o
   de esquema mantienen el criterio fail-closed.
5. **Una transacción por petición.** El latido diario y la presencia hacían cada
   uno su `commit`; cada commit cerraba la transacción y la lectura siguiente
   abría otra con sus seis `set_config`. Ahora se confirman juntos en la puerta
   de `get_db` (`_anotar_telemetria`). En una petición de solo lectura: de tres
   transacciones a una.
6. **Tope de espera propio**, `COTIZAT_DB_POOL_TIMEOUT` (10 s por omisión, `0`
   lo desactiva; no aplica con `NullPool`). Menor que los 60 s del pooler a
   propósito: mejor un 503 rápido que un minuto de pantalla colgada.

**Sobre el acceso de esta organización.** La organización 43 **no** tiene la
prueba caducada como acceso: su prueba venció el 17/10/2026 y el 20/10 compró
el plan mensual (`id 54`, `origen = 'pago'`, `vence 18/11/2026`).
`cotizat_security.organization_has_license(43)` devuelve `true`. Es decir, el
usuario tenía derecho a estar dentro y, además, estaba pagando. Lo que fallaba
era el producto bajo su uso normal, no un acceso indebido.

**Cómo se vigila ahora.** `/readyz` y el panel de operación siguen mostrando el
estado de la base. Un 503 de saturación deja fila en `errores_internos` (sin
correo) y el cliente recibe `Retry-After: 3`. Si el panel vuelve a llenarse de
`ECHECKOUTTIMEOUT`, la consulta culpable está en `pg_stat_statements`:

```sql
SELECT calls, round(mean_exec_time) AS media_ms, left(query, 120)
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;
```
