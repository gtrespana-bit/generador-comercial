# Punto exacto de continuación

Fecha de corte: **18/08/2026, PR #38 listo para fusionar (prueba gratuita anunciada al público); el titular activa `COTIZAT_EXIGIR_LICENCIA` justo después del merge** (America/Caracas).

Este documento retoma el trabajo sin depender del historial del chat. Describe
**dónde quedó exactamente** el trabajo y **qué sigue**, en ese orden. Léelo
junto con `basedatos_partidas/EMPEZAR_AQUI.md` (reglas y progreso del catálogo),
`basedatos_partidas/INVENTARIO.md` (cifras y contraste de precios) y
`PLAN_DE_COMERCIALIZACION_Y_EVOLUCION_SAAS.md` (§1.9 y §11).

> **Si acabas de abrir una ventana nueva, lee solo la sección siguiente.**
> Está escrita para eso: dice en qué estado exacto queda el repositorio, qué va
> a hacer el titular por su cuenta, y qué trabajo toca después.

---

## ✅ Cierre de sesión — Recordatorio de vencimiento automático (cron) + identidad (18/08/2026, noche)

Rama fija de la sesión: `arena/01a0165a-generador-comercial`, basada en `main`
(merge del PR #38). Con el corte por licencia ya encendido en producción, este
bloque cierra el hueco que faltaba en el circuito de cobro y ajusta la
identidad pública.

### 1. Recordatorio de vencimiento por email (automático, premium)

Antes, el aviso de vencimiento solo salía cuando el **operador pulsaba un
botón** en `/admin/licencias`. Ahora hay un **recordatorio automático** que el
programador de Vercel dispara una vez al día, en **dos hitos exactos**: 5 días
antes (previsión) y 1 día antes (última llamada). Cada hito se envía **una
única vez por licencia** (renovar crea licencia nueva y el conteo vuelve a
empezar).

- **Correo premium** (`app/templates/emails/recordatorio_vencimiento.{html,txt}`):
  cabecera de marca en verde con gradiente, cuenta atrás grande, tabla con
  organización/plan/válido-hasta, CTA **«Renovar mi plan»** (o **«Elegir un
  plan»** si es prueba) que enlaza al checkout `/pago` —ya no un `mailto:`—,
  caja de tranquilidad («tus datos no se borran»), `Reply-To` a soporte y pie
  con la identidad. Sigue la paleta de CotizaT (`#0b5b38`, `#eef7f2`,
  `#f3f7f5`).
- **Envío** (`app/services/email.py` → `enviar_recordatorio_vencimiento`),
  **barrido** (`app/services/licencias.py` → `enviar_recordatorios_vencimiento`,
  `RECORDATORIOS_DIAS=(5,1)`, marca en `licencias.notas` por hito).
- **Cron**: `vercel.json` → `crons` (`/api/cron/recordatorios-vencimiento`,
  diario a las 13:00 UTC). La ruta (`app/routers/admin.py`) verifica
  `Authorization: Bearer $CRON_SECRET` en tiempo constante y usa la nueva
  dependencia `get_cron_db` (`app/database.py`), que marca la sesión como
  operador del sistema **sin** Supabase Auth —la puerta de seguridad es el
  secreto, no una sesión.
- Suite: **651 passed, 6 skipped** (9 pruebas nuevas en
  `tests/test_recordatorios_vencimiento.py`).

### 2. Identidad pública: «CotizaT · Presupuestos» sin identificador

Decisión del titular: no publicar la razón social real por ahora. `app/branding.py`
muestra **«CotizaT · Presupuestos»** (marca operativa, **sin** número de
identificación) como `LEGAL_ENTITY` por omisión; `COTIZAT_LEGAL_ENTITY` sigue
siendo el override para cuando exista una entidad registrada. Los pies de la
landing, `/pago` y el checkout ahora renderizan `© 2026 {{ titular_legal }}`
para no duplicar «CotizaT».

### 3. `soporte@cotizat.online` (Zoho) — resuelto, sin código

El titular creó el buzón en Zoho y **recibe correos**. La app ya apuntaba a esa
dirección (`SUPPORT_EMAIL` en `app/branding.py`), así que **no hay que tocar
nada**: el envío sigue por Resend y el buzón solo recibe. El recordatorio deja
`Reply-To: soporte@cotizat.online`, así que las respuestas caen en Zoho.

### Pendientes / candidatos siguientes

1. **El titular configura el cron en Vercel**: añadir `CRON_SECRET` (fuerte,
   `openssl rand -base64 32`) en *Settings → Environment Variables* (Production)
   y redesplegar. Sin `CRON_SECRET` la ruta responde 401 y Vercel no autentica
   la llamada. Detalle en `docs/PENDIENTES_OPERATIVOS.md` §9.
2. Vercel **Hobby → Pro** antes del primer cobro (sigue aplazado por el titular).
3. Vigilar el primer alta real con el corte encendido (pendiente de otra sesión).
4. `COTIZAT_LEGAL_ENTITY` cuando exista razón social registrada (la empresa
   española del titular está inactiva ~2 años y no se registrará una nueva por
   ahora; se reutilizará esa cuando el proyecto lo justifique).

---

## 🟢 EMPEZAR AQUÍ — Estado al cierre del 18/08/2026

### En una frase

Todo el bloque de cobro, licencias, panel de operador y prueba gratuita está
**terminado y en verde** en la rama `arena/01a015a7-generador-comercial`
(**PR #38**, 6 commits, cabeza `b73b56d`); falta **fusionarlo** y, acto
seguido, el titular **enciende el corte por licencia en producción**.

### Estado del repositorio

| Dato | Valor |
| --- | --- |
| Rama de trabajo | `arena/01a015a7-generador-comercial` (sincronizada con `origin`) |
| PR | **#38**, abierto, 6 commits, 47 archivos |
| Último commit | `b73b56d` — anuncio público de la prueba gratuita |
| Base | `main` en `00cfec0` |
| Suite | **642 passed, 6 skipped** (~80 s con `.venv/bin/pytest -q`) |
| Auditoría E1-021 | Sin hallazgos, 6416 archivos (`.venv/bin/python tools/auditar_datos_sensibles.py`) |
| Cabeza Alembic | `a3d9c1e75b28` (**ya aplicada en Supabase**) |

### Qué se hizo en esta última sesión

**1. La prueba gratuita ya se anuncia al público** (era el encargo). Los 7 días
existían en el registro pero no se mencionaban en ninguna página, así que nadie
llegaba a pedirlos: comercialmente no cumplían ninguna función. Ahora aparecen
en los cuatro puntos donde alguien decide —landing (`/` y `/conocer`), `/pago`
y `/acceso`— y el CTA principal del hero apunta a **`/acceso`**, que es donde
vive el registro real; las tarjetas de plan siguen yendo a `/pago`. Detalle
completo en la sección «Cierre de sesión» de más abajo y en
`docs/COBRO_Y_LICENCIAS.md` §5.6.

**2. Se arregló la suite, que estaba en rojo sin que se supiera.** El commit
anterior (`fbc3c26`) se subió con 42 fallos de la auditoría de datos sensibles.
Explicación y lección en «Errores y lecciones» al final de esta sección.

### ⚠️ Lo que el titular hace por su cuenta, sin esperar a nadie

En cuanto el PR #38 esté fusionado y desplegado, el titular ejecuta esto. **Ya
están hechos** los pasos previos (migración aplicada en Supabase y licencia de
cortesía concedida a su organización), así que solo queda el interruptor:

1. **Fusionar el PR #38** y esperar a que Vercel termine el despliegue.
2. Comprobar `/readyz`: debe verse `"alembic": "head:a3d9c1e75b28"`.
3. Vercel → *Settings* → *Environment Variables*, scope **Production**:
   `COTIZAT_EXIGIR_LICENCIA=true`.
4. **Redeploy** (una variable de entorno no se aplica sola al despliegue vivo).
5. Verificar en `/readyz` que aparece `"licencias": "exigida"`.

Valores que cuentan como verdadero: `1`, `true`, `on`, `si`, `sí`.

> **El orden importa y esta es la razón.** El corte deja sin acceso a toda
> organización sin licencia vigente. Encender el interruptor **antes** de que
> el PR esté desplegado dejaría suspendida a toda organización recién
> registrada, porque la prueba gratuita que las cubre viaja en este PR. Con el
> PR fuera, cada alta nueva nace con 7 días y el corte solo muerde a quien
> ya agotó su prueba sin pagar, que es exactamente lo que se busca.

**Cómo revertir si algo sale mal:** poner `COTIZAT_EXIGIR_LICENCIA=false` y
redesplegar. El interruptor no borra ni modifica datos; solo decide si se
comprueba la vigencia. Nada de lo concedido se pierde.

**Si el titular se corta a sí mismo por error:** el panel `/admin/*` cuelga de
`get_operator_db`, que **no** comprueba licencia. El panel sigue accesible
aunque la organización propia esté suspendida, así que siempre se puede entrar
a concederse una licencia. No hay forma de quedarse fuera del todo.

### Lo siguiente en el producto (nada de esto está empezado)

Por orden de valor, según lo hablado:

1. **Ver el panel de operador con datos realistas.** Está construido y probado,
   pero nunca se ha mirado con un volumen de clientes que se parezca al real.
   Es donde antes aparecerá un problema de diseño de los que cuestan tiempo
   cada día.
2. **Vigilar el primer alta real con el corte encendido.** El circuito completo
   —registro → prueba de 7 días → aviso de vencimiento → pago → renovación—
   nunca se ha recorrido de punta a punta con un cliente de verdad.
3. **Decidir qué pasa al vencer la prueba sin pagar.** Hoy la organización
   simplemente deja de generar presupuestos nuevos y conserva sus datos, que es
   lo que promete la web. No hay aviso por correo antes del vencimiento: quien
   se despiste se encuentra el corte de golpe. Un recordatorio a los 5 días es
   probablemente lo más rentable que queda por hacer en todo el circuito.

### Errores y lecciones de esta sesión (importa para no repetirlos)

**El auditor de datos sensibles solo mira archivos ya versionados en Git.**
Corolario incómodo: los archivos nuevos **no se auditan hasta que se
commitean**, así que la suite puede estar verde antes de commitear y romperse
justo después. Eso pasó con `fbc3c26`, que se subió con 42 hallazgos de
«correo-personal» por ejemplos de correo verosímiles sobre dominios de
consumo (nombre y apellido reales sobre `gmail.com`). **Después de
commitear archivos nuevos, volver a correr la suite completa.**

**Cómo se arregló, y por qué no con excepciones.** La salida fácil era añadir
42 entradas a `EXCEPCIONES` en `tools/auditar_datos_sensibles.py`, que es
exactamente lo que convierte una regla en teatro. El razonamiento correcto:
en estos ejemplos el **dominio** es parte del hecho técnico —los puntos que
Gmail ignora y el `+etiqueta` de Outlook no se pueden demostrar con
`example.com`— pero quien identifica a una persona es la **parte local**. Así
que los ejemplos pasaron a nombres de fantasía (`fulano`, `mengana`) y el
auditor aprendió el mismo concepto de marcador que ya aplicaba a credenciales,
teléfonos y RIF. La exención es estrecha a propósito: lista cerrada, anclada al
principio de la parte local, comprobada solo sobre ella, más el caso degenerado
sin usuario (`+etiqueta@`, `.@`) que ningún proveedor admite como buzón.
Un nombre verosímil sobre un dominio de consumo se sigue marcando aunque lleve
subdirección, y un nombre de fantasía precedido de cualquier otra cosa —del
estilo «no-soy-» seguido de `fulano`— tampoco cuela, porque la comprobación
exige que el nombre **abra** la parte local. Hay tests que lo fijan en ambas
direcciones.

Pequeña anécdota que confirma que la regla muerde: el primer borrador de este
mismo documento citaba una de esas direcciones como ejemplo, y **la auditoría
lo rechazó**. Por eso aquí se describen en palabras en lugar de escribirlas.

**Hay una doctest que mentía y la suite no lo vio.** Al renombrar quedó
`normalizar_email("Juan.Perez+cotizat@GMail.com")` documentando el resultado
`'fulanodetal@gmail.com'`, que es falso. Se corrigió, pero **`pytest` no
ejecuta doctests en este proyecto**: los `>>>` de
`app/services/identidad_registro.py` son documentación que nadie verifica.
Se detectó a mano con `.venv/bin/python -m doctest`. Queda **pendiente y sin
decidir** si añadir `--doctest-modules` a `pytest.ini`.

**Verificar antes de afirmar.** Varias veces en esta sesión di por bloqueante o
por pendiente algo que no lo era (el caso más claro: sostuve que la licencia de
cortesía debía concederse *antes* de activar el interruptor, y es falso, porque
`get_operator_db` no comprueba licencia). Comprobar el estado real con `grep`,
`git log` o una petición HTTP antes de dar algo por hecho.

---

## ✅ Cierre de sesión — La prueba gratuita se anuncia al público (18/08/2026, noche)

Misma rama (`arena/01a015a7-generador-comercial`) y mismo **PR #38**. Commits
`16063ec` y `b73b56d`.

### Por qué era lo siguiente

Lo planteó el titular sin rodeos: la prueba existía en el registro pero **no se
mencionaba en ninguna página pública**, así que nadie llegaba a pedirla. Una
prueba que el público no ve no cumple ninguna función comercial. Además, toda
la landing empujaba a `/pago`, que es el destino equivocado para quien viene a
probar gratis.

### Qué se hizo

**Dos globales de Jinja** en `app/routers/common.py`, dentro de
`TEMPLATES.env.globals.update(...)`:

```python
dias_de_prueba=dias_de_prueba,          # -> int, lee COTIZAT_DIAS_PRUEBA
hay_prueba_gratuita=prueba_activada,    # -> bool
```

Se pasan como **funciones, no como valores**, igual que `catalogo=cifras_catalogo`.
Esa decisión es la que hace que todo lo demás funcione: Jinja cachea la
plantilla compilada, no su resultado, así que una global que es función se
evalúa **en cada render**. Consecuencia práctica: apagar `COTIZAT_DIAS_PRUEBA`
retira el anuncio de todas las páginas **sin redesplegar ni tocar plantillas**,
y los tests solo necesitan `monkeypatch.setenv(...)` sin invalidar caché.

El patrón en plantillas es siempre el mismo:

```jinja
{% if hay_prueba_gratuita() %}… {{ dias_de_prueba() }} días gratis …{% else %}Ver planes{% endif %}
```

**Dónde aparece** (4 páginas; 11 condicionales en la landing, 1 en cada una de
las otras dos):

| Archivo | Qué se añadió |
| --- | --- |
| `app/templates/landing.html` | meta description, barra de navegación, píldora `hero-prueba`, CTA del hero a `/acceso` + letra pequeña, bloque `prueba-destacada` en `#precios`, un `<li>` en cada tarjeta de plan, `nota-honesta` reescrita, paso 1 de «de cero a presupuesto», CTA de cierre |
| `app/templates/pago.html` | bloque `pago-prueba` tras el hero |
| `app/templates/auth/access.html` | línea `auth-prueba` en el formulario de registro |
| `app/static/css/public.css` | `.hero-prueba`, `.hero-letra-pequena`, `.prueba-destacada`, `.pago-page .pago-prueba`, `.auth-split-forms .auth-prueba` |

**Dos detalles con intención**, que conviene no deshacer sin pensarlo:

- En `/pago` la condición es `hay_prueba_gratuita() and not msg`. Quien llega
  con un aviso **ya agotó la prueba**; volver a ofrecérsela sería una burla.
- El anuncio usa el **verde** del sistema (`--green-soft`, `#047857`, `#065f46`)
  y no el azul `--accent` de las CTA de pago, para que lo gratuito se distinga
  de un solo vistazo de lo que cuesta dinero.

### Textos que comprometen al producto

Están publicados y **deben seguir siendo ciertos**; si algún día dejan de
serlo, hay que cambiar la web el mismo día:

- «N días gratis · sin tarjeta de crédito»
- «Acceso completo durante N días. No pedimos tarjeta y no se cobra nada
  automáticamente.»
- «si no eliges un plan, tu cuenta simplemente deja de generar presupuestos
  nuevos y tus datos siguen ahí»

### Cómo queda vigilado

Seis tests nuevos en `tests/test_prueba_gratuita.py` (56 en el archivo, 642 en
la suite), sobre un helper `_paginas_publicas` que recorre `/`, `/conocer`,
`/pago` y `/acceso`.

El importante es **`test_apagar_la_prueba_retira_el_anuncio`**: con
`COTIZAT_DIAS_PRUEBA=0` exige que no quede rastro de «días gratis» —ni de
`d&iacute;as gratis`, por el escapado de Jinja— en ninguna de las cuatro
páginas. La razón de existir de ese test: el día que se retire la oferta, lo
que no puede pasar es que la web siga prometiéndola.

Se comprobó que **el test muerde**: forzando a `{% if True %}` la condición del
hero, falla; restaurándola, vuelve a verde. Además se verificó a mano
levantando el servidor con `COTIZAT_DIAS_PRUEBA=0`, donde las cuatro páginas
quedan limpias y la landing revierte a «Ver planes».

### Efecto secundario: la suite estaba en rojo y no se sabía

Detallado en «EMPEZAR AQUÍ → Errores y lecciones». Resumen: el auditor de datos
sensibles solo revisa archivos **ya versionados**, así que los ejemplos de
correo añadidos con la prueba gratuita no se auditaron hasta commitearlos, y
`fbc3c26` se subió con 42 hallazgos. Se corrigió en `16063ec` con nombres de
fantasía y una exención estrecha en el auditor, no con 42 excepciones.

---

## ✅ Cierre de sesión — Prueba gratuita de 7 días (18/08/2026)

Misma rama (`arena/01a015a7-generador-comercial`) y mismo **PR #38**.

### Por qué era lo siguiente

El interruptor `COTIZAT_EXIGIR_LICENCIA` no se podía encender: con el corte
activo, **toda organización recién registrada nacía suspendida**. La prueba
gratuita es el prerrequisito, no un extra comercial.

### Qué quedó hecho

Al crear la primera organización se concede sola una licencia de 7 días
(`origen='prueba'`, importe 0). Contra el reciclaje de cuentas: una prueba por
**identidad de correo normalizado** y para siempre (puntos y `+etiqueta`
neutralizados; la marca sobrevive al borrado de la organización), **dominios
desechables bloqueados en el registro**, licencia siempre **por organización**
—una segunda organización no trae otra prueba— e **IP del alta hasheada** que
solo señala patrones en el panel y jamás bloquea sola.

La concesión ocurre dentro de PostgreSQL
(`cotizat_security.grant_trial_license`, migración `a3d9c1e75b28`): marca e
licencia se insertan **a la vez**, y la carrera entre dos altas del mismo correo
la resuelve `ON CONFLICT DO NOTHING` en la base, no Python. El razonamiento
completo, incluido el asunto del `FORCE ROW LEVEL SECURITY`, está en
`docs/COBRO_Y_LICENCIAS.md` §5.

630 pruebas en verde, 50 de ellas nuevas en `tests/test_prueba_gratuita.py`.
(Cifra de aquel momento; al cierre de la sesión siguiente son **642**.)

### ⚠️ Lo que faltaba y en qué orden — **ya resuelto, se conserva por el razonamiento**

> **Estado real al 18/08/2026 por la noche:** los pasos 1 y 3 **están hechos**
> (el titular aplicó el SQL en Supabase sin incidencias y se concedió la
> licencia de cortesía). Quedan el 2 y el 4, que el titular ejecuta tras
> fusionar el PR #38 — ver «EMPEZAR AQUÍ» al principio de este documento.
>
> Una corrección respecto a lo que decía este apartado: el paso 3 **no** era
> un prerrequisito del 4. El panel `/admin/*` cuelga de `get_operator_db`, que
> no comprueba licencia, así que la cortesía puede concederse en cualquier
> momento. Lo único realmente bloqueante era la migración.

**El SQL de PostgreSQL solo está validado por lectura y en SQLite: no hay
PostgreSQL en el entorno de desarrollo.** La prueba de humo del final de
`docs/staging_upgrade_a3d9c1e75b28.sql` es el primer sitio donde se ejecuta de
verdad; conviene correrla dentro de una transacción con `ROLLBACK`, como está
escrita.

1. ✅ Aplicar `docs/staging_upgrade_a3d9c1e75b28.sql` en Supabase con el rol
   administrativo (**no** `cotizat_app`). *(Hecho por el titular, sin
   incidencias.)*
2. ⏳ Verificar la cabeza `a3d9c1e75b28` en `/readyz`.
3. ✅ Licencia de cortesía a la organización del titular. *(Hecha.)*
4. ⏳ `COTIZAT_EXIGIR_LICENCIA=true` en Vercel (Production) + redeploy, y
   comprobar `"licencias": "exigida"`.

Invertir el orden dejaría suspendida a toda organización nueva.

### Lo siguiente en el producto — **ya hecho, ver secciones posteriores**

El **panel de operador «premium»**: gestionar una organización (conceder,
renovar, retirar, ver pagos) **en dos clics desde el propio listado**, sin
recorrer la página ni buscar en desplegables. Con muchos clientes, una tarea
sencilla mal diseñada multiplica el coste operativo por 4-5.

---

## ✅ Cierre de sesión — El corte por licencia queda listo para encenderse (18/08/2026)

Rama fija de la sesión: `arena/01a015a7-generador-comercial`, basada en `main`
(`00cfec0`). Continúa el bloque siguiente (post-venta) en la misma rama y el
mismo **PR #38**.

### 0. Punto de partida

La migración `c7f1a3b9d425` **ya está aplicada en Supabase** (el titular
ejecutó `docs/staging_upgrade_c7f1a3b9d425.sql` con éxito), así que `/readyz`
deja de responder 503 por la guarda de `EXPECTED_ALEMBIC_HEAD`. Con eso, el
pendiente nº 3 del bloque anterior —activar `COTIZAT_EXIGIR_LICENCIA=true`—
pasó de «decisión de negocio» a trabajo de esta sesión.

### 1. El problema que había que resolver antes de encender el interruptor

Al revisar qué pasaría con el corte activo apareció un fallo de diseño serio:
**una organización vencida no podía renovar**. El corte se aplica en `get_db`,
la dependencia de la que cuelgan *todas* las rutas de organización — incluidas
las de compra. Con la licencia caducada, `/pago/comprar` (GET y POST),
`/pago/confirmacion` y `/pago/recibo/{id}.pdf` devolvían **403 «Acceso
suspendido»**.

Es decir: el cliente veía la pantalla de suspensión, que le invita a renovar, y
al intentar pagar se topaba con la misma pared. La suspensión era una trampa
sin salida y toda renovación habría tenido que pasar por soporte a mano,
justo lo contrario de lo que persigue el circuito de compra automático.

### 2. La corrección: una segunda puerta, `get_db_renovacion`

- Nueva dependencia **`get_db_renovacion`** en `app/database.py`: idéntica a
  `get_db` —autenticación, membresía, organización activa, RLS de tenant— pero
  **sin la comprobación de vigencia de la licencia**.
- La usan **solo** las cuatro rutas de `app/routers/pagos.py` necesarias para
  renovar. Ninguna expone datos de negocio: no dan acceso a presupuestos,
  clientes ni catálogo, solo al circuito de pago de la propia organización.
- `app/templates/licencia_suspendida.html`: botón **«Renovar mi plan»** que
  lleva a `/pago`, para que la salida sea visible y no haya que adivinarla.
- El resto del producto sigue detrás de `get_db` y se corta igual que antes.

### 3. Cómo queda vigilado (lo importante para el futuro)

El riesgo real no es el fallo de hoy sino su reaparición: alguien añade mañana
una ruta de compra colgada de `get_db` y la trampa vuelve, en silencio y solo
para clientes vencidos —el peor sitio donde descubrirlo—. Por eso el arreglo
va acompañado de cuatro regresiones en `tests/test_licencias_acceso.py`:

- Una organización suspendida **llega al checkout** y **puede registrar la
  compra** (no 403).
- El resto de rutas de organización **siguen cortadas** (no se ha abierto un
  agujero general).
- Un test estructural recorre el árbol de rutas de la aplicación y exige que
  **exactamente** las rutas de compra usen `get_db_renovacion` y ninguna otra:
  `test_las_rutas_de_compra_usan_la_puerta_sin_corte`.

Ese último test se verificó **a la inversa**: revirtiendo a mano las rutas de
`pagos.py` a `get_db`, la suite falla; restaurándolas, vuelve a verde. No es un
test que pase por vacío.

### 4. Detalle técnico útil para quien siga

- **Recorrido de rutas en tests.** FastAPI envuelve los routers incluidos, así
  que filtrar `app.routes` por `path` devuelve vacío. Hay que recursar por
  `getattr(ruta, "original_router", None).routes` y, en las hojas, leer
  `route.dependant.dependencies` → `{d.call}`.
- **Doble puerta en los tests.** Cualquier test que ejercite `/pago/*` debe
  sobrescribir **`get_db` y `get_db_renovacion`**; con solo `get_db` la petición
  cae a la base real y falla con `no such table`. En
  `tests/test_compras_plan.py` se centralizó en los helpers
  `_instalar_override(db, ids)` / `_retirar_override()`.

### Estado y verificación

- Suite completa: **573 passed, 6 skipped** (`.venv/bin/pytest -q`), 38 de ellos
  en `tests/test_compras_plan.py` y 33 en `tests/test_licencias_acceso.py`.
  `compileall` limpio. *(Cifra de aquel momento; el total vigente está en
  «EMPEZAR AQUÍ», al principio del documento.)*

### Pendientes / candidatos siguientes

1. **Conceder la licencia de cortesía a la organización del titular** desde
   `/admin/licencias` (tipo `cortesia`, duración larga, nota «uso del titular»).
   **Antes** de encender el interruptor: si no, el titular se corta a sí mismo.
   El panel de operador seguiría accesible, pero su organización no.
2. **Activar `COTIZAT_EXIGIR_LICENCIA=true`** en Vercel (Production) + redeploy.
   Comprobar en `/readyz` que aparece `"licencias": "exigida"`.
3. Ensayar en staging con una organización vencida de prueba: ver «Acceso
   suspendido», pulsar «Renovar mi plan», completar la compra y confirmar que
   el acceso vuelve al activarla desde `/admin/compras`.
4. Sigue sin haber **renovación automática** (Stripe + alta de autónomo): la
   renovación es compra manual + activación del operador.

---

## ✅ Cierre de sesión — Post-venta al cliente: aviso de activación + recibo PDF (18/08/2026)

Rama fija de la sesión: `arena/01a015a7-generador-comercial`, basada en `main`
(`00cfec0`).

### 0. Ensayo del flujo de compra real en staging: **SUPERADO**

(Es el «punto 1» del bloque anterior de esta serie de notas —pendiente nº 3 de
su lista—, no el punto 1 de `docs/MATRIZ_PASOS_MANUALES.md`, que es el
registro.)

El titular ejecutó en staging el **flujo de compra real con cobro manual**
(E1-059 / E1-060) de principio a fin y lo dio por bueno:

`/pago` → «Contratar» → checkout con método de pago y **comprobante adjunto**
→ compra en estado `pendiente` → aviso al operador → **activación desde
`/admin/compras`** → el cliente ve «Tu plan» con fecha de vencimiento y días
restantes.

Queda por tanto **cerrado** ese ensayo pendiente. Los
dos huecos que dejó (el comprador no recibía ningún aviso al
activarse su plan y no tenía forma de obtener un justificante) son justo lo que
resuelve este bloque.

### 1. Aviso de activación por email al comprador

- Nueva función `enviar_activacion_plan_por_email(...)` en
  `app/services/email.py`, con plantillas `app/templates/emails/plan_activado.html`
  y `.txt`: saludo, plan contratado, importe, método de cobro, **fecha de inicio
  y de vencimiento en `dd/mm/aaaa`** (también en el asunto) y, si existe, el
  **recibo en PDF como adjunto** (base64).
- `POST /admin/compras/{id}/activar` (`app/routers/admin.py`) llama al helper
  `_avisar_activacion_al_cliente(...)` justo después de activar. El envío es
  **best-effort**: si Resend falla, la activación no se revierte; el operador
  ve el aviso de error en el panel y la licencia sigue activa.
- Destinatario: el email que registró la compra (`creada_por_email`).

### 2. Recibo PDF descargable por el propio cliente

- Nueva ruta **`GET /pago/recibo/{compra_id}.pdf`** (`app/routers/pagos.py`):
  descarga como `attachment`, `Cache-Control: no-store`, nombre
  `recibo-CT-{id:06d}.pdf`. Solo sirve compras **de la organización activa** y
  en estado `activa` con importe > 0; en caso contrario, 404 / redirección con
  aviso.
- En `/configuracion`, la tarjeta **«Tu plan»** (`app/templates/settings.html`,
  estilos `.plan-recibo` en `style.css`) muestra el enlace **«Descargar recibo
  (PDF)»** de la última compra activada con importe, resuelta por
  `ultima_compra_con_recibo(...)` en `app/services/compras.py`.

**Restricción técnica que condiciona el diseño:** `licencias` tiene RLS que
solo responde a sesiones de **operador** (`cotizat.es_operador`, migración
`f4c1d8e37a95`), así que una ruta de cliente **no puede** leer la licencia. Por
eso el período concedido se **copia a `compras_plan`** (tabla tenant) al
activar, y la ruta del cliente construye un objeto `_LicenciaDeCompra`
(duck-typing) que reutiliza el mismo generador
`app/services/recibo_licencia.py` que usa el operador. El recibo del cliente y
el de `/admin/licencias/{id}/recibo.pdf` son idénticos.

### 3. Migración `c7f1a3b9d425` (⚠️ PENDIENTE de aplicar en Supabase)

- `migrations/versions/c7f1a3b9d425_compra_periodo_licencia.py`
  (`down_revision = d4e2f6a8b0c1`) añade `compras_plan.licencia_inicio` y
  `compras_plan.licencia_vence`, con **backfill** dual PostgreSQL/SQLite desde
  la licencia enlazada para que las compras ya activadas conserven su período.
- `app/database.py` → `EXPECTED_ALEMBIC_HEAD = "c7f1a3b9d425"`. Mientras no se
  aplique en Supabase, `/readyz` responderá **503** a propósito.
- Script para el titular: **`docs/staging_upgrade_c7f1a3b9d425.sql`** (verifica
  que el head previo sea `d4e2f6a8b0c1`, añade columnas, hace backfill y
  actualiza `alembic_version`, todo en una transacción).
- Verificado localmente: `alembic upgrade head` desde cero sobre SQLite llega a
  `c7f1a3b9d425` y crea ambas columnas; `downgrade -1` + `upgrade` también.

### Estado y verificación

- **568 tests pasando, 6 omitidos** (`.venv/bin/pytest -q`), de los cuales 37 en
  `tests/test_compras_plan.py`: el período copiado al activar, la ruta del
  recibo del cliente, el aislamiento entre organizaciones (una organización no
  alcanza el recibo de otra), la tarjeta del plan en `/configuracion`, el envío
  del aviso, el caso «Resend falla y la activación se mantiene» y dos
  comprobaciones del payload real de Resend (fechas, importe y adjunto base64
  decodificable).

### Pendientes / candidatos siguientes

1. ✅ **Hecho (18/08/2026):** `docs/staging_upgrade_c7f1a3b9d425.sql` aplicado
   en Supabase; `/readyz` vuelve a 200 con `"alembic": "head:c7f1a3b9d425"`.
2. Repetir en staging una compra completa para ver el **correo de activación**
   con su adjunto y el enlace de recibo en `/configuracion`.
3. ✅ **Resuelto en el bloque de arriba (18/08/2026):** el corte
   (`COTIZAT_EXIGIR_LICENCIA=true`) ya es seguro de encender — una organización
   suspendida puede renovar sola. Queda solo la licencia de cortesía al titular
   y el switch en Vercel (`docs/PANEL_DE_OPERADOR.md` §6).

---

## ✅ Cierre de sesión — Flujo de compra: retoma tras el alta + fix del comprobante (18/08/2026)

Rama fija de la sesión: `arena/01a01580-generador-comercial`, basada en `main`
(`19231e3`, merge del PR #36). **PR #37 creado hacia `main`** (confirmar con
`gh pr view 37`; si ya está fusionado, `main` contiene el código).

El bloque resuelve los dos problemas observados al ensayar el **punto 1** de la
matriz (flujo de compra real en staging, E1-059 cobro manual):

### 1. Bug: la compra siempre fallaba con «Adjunta el comprobante de pago para continuar»

**Causa raíz.** El checkout (`/pago/comprar`) renderiza un panel por método de
pago (Pago móvil, Binance, Kontigo, USDT) y los **cuatro campos de archivo
compartían `name="comprobante"`**. El navegador enviaba una parte por cada
método (tres vacías y una con el archivo real); el enlace del `UploadFile`
resultaba ambiguo y, salvo con el último método, el servidor recibía la parte
vacía y rechazaba la compra aunque se hubiera adjuntado el recibo. Lo mismo
afectaba a los campos de verificación con nombre repetido (`fecha_pago`,
`nombre_titular`, `hash_transaccion`, `numero_operacion`…).

**Corrección.**
- Cada método publica su archivo con nombre único (`comprobante_<clave>`) y
  `registrar_compra` lee solo el campo `comprobante_{metodo_pago}` del método
  elegido (via `request.form()`), no un parámetro `UploadFile` ambiguo.
- `app/static/js/pago-metodo.js` ahora **deshabilita** (`disabled`) los paneles
  no elegidos además de ocultarlos: un input `disabled` no se envía, así que el
  formulario manda únicamente los campos y el archivo del método activo.

### 2. Flujo: la intención de compra se perdía tras el registro

**Problema.** «Contratar plan» sin cuenta llevaba al login/registro; la
confirmación de email y el alta de la organización **perdían la intención de
compra**, y al entrar por primera vez no había forma clara de retomarla.

**Corrección (retoma de compra, cookie + avisos).**
- Nuevo enlace `Contratar → GET /pago/elegir?plan=…` (en `pago.html`) que
  guarda el plan elegido en la cookie **`cotizat_plan_pendiente`** (HttpOnly,
  7 días) **antes** de exigir sesión, de modo que sobrevive a registro +
  confirmación de email + alta de empresa.
- `GET /pago/comprar` y la confirmación siguen funcionando igual; al registrar
  la compra se limpia la cookie.
- **Panel `/inicio`**: si hay cookie de intención y la organización **no tiene
  licencia activa**, aparece el aviso «Retoma tu compra del Plan …» con botón
  **Continuar compra** (`/pago/comprar?plan=…`) y **Ahora no**
  (`POST /pago/descartar`, limpia la cookie). Render en `index.html` + estilos
  `.retomar-compra` en `style.css`.
- **`/bienvenida` (onboarding)**: aviso equivalente «Tienes una compra
  pendiente…» nada más crear la organización, para que la compra no quede
  olvidada durante la configuración inicial.

### Cambios

- `app/datos_pago.py`: constante `PLAN_PENDIENTE_COOKIE`.
- `app/routers/pagos.py`: `GET /pago/elegir`, `POST /pago/descartar`, lectura
  del comprobante por método y limpieza de la cookie al confirmar.
- `app/routers/inicio.py` y `app/routers/auth.py`: exponen la intención al
  dashboard y a la bienvenida.
- `app/templates/`: `pago.html`, `pago/comprar.html`, `index.html`,
  `onboarding.html`.
- `app/static/`: `pago-metodo.js` (deshabilitar paneles inactivos),
  `css/style.css` (`.retomar-compra`).
- `tests/test_compras_plan.py`: 7 regresiones nuevas (comprobante del método
  correcto aunque lleguen los demás vacíos, `/pago/elegir` guarda cookie,
  `/pago/descartar` la limpia, y los avisos en `/inicio` y `/bienvenida`).

### Estado y verificación

- Suite completa: **557 passed, 6 skipped**. `compileall`, `node --check`,
  72 plantillas Jinja, `verificar_lock`, auditoría de datos sensibles y
  `git diff --check` en verde. Sin migraciones nuevas (ningún cambio de esquema).

### Pendientes / candidatos siguientes

1. **Ensayar en staging el flujo completo** con una organización de prueba:
   elegir plan (sin sesión) → registrarse → confirmar email → crear empresa →
   ver el aviso de retoma → comprar con comprobante → activar desde `/admin` →
   el cliente ve «Tu plan» con fecha y días.
2. Decisión del titular: **recibo PDF de la compra para el cliente** (existe
   `recibo_licencia.py` para el operador; falta el equivalente de cliente) y
   **corte automático** (`COTIZAT_EXIGIR_LICENCIA=true`), pendientes de la
   sección anterior.
3. Si se quiere acortar el «largo y tedioso» del alta (registro → confirmación
   → organización completa) antes de pagar: es una decisión de producto mayor
   (capturar menos datos y completar la empresa después). No se tocó.
4. Catálogo a **5.000 partidas** y cierre de los **~196 precios provisionales
   B2B** (requieren cotización del titular).

---

## 🔧 Hotfix — `/inicio` devolvía 500 tras login (18/08/2026)

**Síntoma.** Tras el PR #33, todo login (incluso con credenciales correctas)
acababa con un `500` en `/inicio`. El log de Vercel mostraba:

```
sqlalchemy.exc.InternalError: (psycopg.errors.InFailedSqlTransaction)
  current transaction is aborted, commands ignored until end of transaction block
File "/var/task/app/routers/inicio.py", line 16, in inicio
    cfg = _config(db)
File "/var/task/app/routers/common.py", line 354, in _config
    cfg = db.query(Configuracion).first()
```

**Causa.** El bloque añadió `_resumen_licencia_para_request()` para alimentar
la píldora del menú lateral y la tarjeta "Tu plan" de Configuración
(`app/database.py`). La función envuelve la consulta al resumen en un
`try/except Exception` y devuelve un dict vacío si falla — pero la sesión
SQLAlchemy queda con la transacción abortada. En psycopg eso significa que
**toda consulta posterior** en la misma sesión falla con
`InFailedSqlTransaction` hasta un `ROLLBACK`. La primera consulta del handler
de `/inicio` (un SELECT trivial a `configuracion`) es la que explota, aunque
no tenga nada que ver con el resumen.

La rama PostgreSQL de `resumen_licencia_cliente` llama a
`cotizat_security.organization_license_info(:org)`, función SECURITY DEFINER
que internamente consulta `public.licencias` (tabla con `FORCE ROW LEVEL
SECURITY`). Si la función falla por permisos, RLS o claim ausente, el
`except` la silencia pero no libera la transacción rota. **SQLite local no
reproducía el bug** (cada sentencia abre su propia transacción), por eso los
tests no lo cazaron.

**Corrección** (commit único en este branch, **NO fusionado todavía**):

- `app/database.py` — `db.rollback()` dentro del `except` de
  `_resumen_licencia_para_request`, con un `try/except` interno por si la
  propia `rollback` falla (conexión ya cerrada).
- `tests/test_database_resilience.py` (nuevo) — 2 regresiones:
  1. `test_resumen_licencia_hace_rollback_si_la_consulta_falla`: comprueba
     que el helper llama a `db.rollback()` cuando la consulta interna lanza
     (este test **falla sin la corrección**, pasa con ella).
  2. `test_resumen_licencia_rollback_fallido_no_empeora_la_situacion`:
     cubre el caso patológico en que la propia `rollback` falla.

**Por qué el fix del cliente y no otro.** Se descartó relajar el `try/except`
porque ocultar el error original impedirá diagnosticar el fallo real de la
función en producción. Tampoco se modificó la migración `f9d4c2a7e5b3` (ya
aplicada en Supabase) ni `resumen_licencia_cliente` (un único llamador, ya
blindado por el helper). La causa última del fallo de la función SECURITY
DEFINER —probablemente una combinación de SECURITY DEFINER + RLS en
`licencias` que hace que la lectura interna devuelva 0 filas para el cliente
común, o un claim de organización ausente en alguna sesión— conviene
investigarla aparte. **Si la organización del cliente tiene una licencia
vigente y la píldora del menú lateral sigue mostrando "Sin plan", ahí está
el siguiente cabo suelto.**

**Verificación.** Suite completa: **545 passed, 6 skipped** (543 del PR #33
+ 2 regresiones nuevas). `git diff --check` limpio.

**Despliegue.** Tan pronto se fusione el PR (ver §0quater para el flujo),
Vercel debe redeployar `main` con el fix. `/readyz` debería seguir en 200.

---

## ✅ Cierre de sesión — checkout de planes + panel admin premium + gestión de organización (18/08/2026)

Rama fija de la sesión: `arena/01a012cd-generador-comercial`, basada en `main`
(`88d3859`, merge del PR #32). **PR #33 creado hacia `main`:**
https://github.com/gtrespana-bit/generador-comercial/pull/33 (confirmar con
`gh pr view 33`; si ya está fusionado, `main` contiene el código).

El bloque cierra tres frentes comerciales/operativos: **(1)** el cobro manual
del piloto con checkout real dentro de la app, **(2)** un panel de operador
premium y **(3)** la gestión de la organización visible y con permisos.

### 1. Checkout de planes con pago manual (E1-059, cobro manual)

Se descartó el `mailto:` como vía de compra (el cliente quiere *comprar ya*,
no enviar una solicitud). El flujo completo dentro de la app:

- **`GET /pago`** — planes anual (89 US$ / año) y mensual (9,99 US$ / mes),
  lado a lado en escritorio, con botones que llevan al checkout.
- **`GET /pago/comprar?plan=anual|mensual`** (requiere sesión y organización):
  elige método de pago (tarjetas), ve los **datos del titular para pagar**,
  completa los **campos de verificación del método** y adjunta el
  **comprobante** (imagen PNG/JPG/WEBP o PDF, máx 12 MB).
- **`POST /pago/comprar`** — valida, guarda el comprobante en storage privado
  (categoría `comprobantes`, añadida a `_ALLOWED_CATEGORIES` en `app/storage.py`),
  crea la compra `pendiente` y notifica por email a soporte con el comprobante
  adjunto (`enviar_compra_por_email` en `app/services/email.py`, plantillas
  `emails/compra.{html,txt}`).
- **`GET /pago/confirmacion?id=X`** — resumen y estado pendiente.

Métodos y datos (fijos, públicos por diseño) viven en **`app/datos_pago.py`**:

| Método | Datos para pagar |
|---|---|
| Pago móvil | Banco Provincial · 0412-6443099 · V-20794917 |
| Binance | ID 1090042241 |
| Kontigo | +58412-3215016 |
| USDT | TRC-20 · TPFa5x7jsUk4qw8Qfm1R1XXbPPCPRj8ZXy |

Los números de teléfono están declarados como excepción legítima en
`tools/auditar_datos_sensibles.py` (son canales públicos de cobro, no datos
privados). Los importes 89/9,99 mapean al plan en `PLAN_POR_IMPORTE`
(`app/services/panel_admin.py`) y a la duración de licencia `1a`/`1m`
(`app/services/licencias.py`).

**Modelo `CompraPlan`** (`app/models.py`, tabla `compras_plan`): tenant
(pertenece a la organización compradora) con `plan`, `metodo_pago`, `importe`,
`datos_verificacion` (JSON), `comprobante_*`, `estado`
(`pendiente|activa|rechazada`), `licencia_id` y auditoría de revisión.
**RLS**: INSERT tenant (el cliente crea su compra), SELECT tenant **o**
operador, UPDATE solo operador, sin DELETE (historial íntegro).

**Panel `/admin/compras`** (operador): ver comprobante (`GET
/admin/compras/{id}/comprobante`, lee del storage con la referencia guardada
porque el operador no tiene el tenant del comprador), activar (crea la
licencia del plan con `crear_licencia` origen `pago`) o rechazar.

### 2. Panel admin premium (`/admin`)

Sustituye la idea de paneles sueltos por un **hub único** (`/admin`):

- **KPIs**: clientes, con plan, sin plan, por vencer (15 días), compras por
  activar e ingresos.
- **Tabla "Clientes y planes"** ordenable por columna (cliente, plan, compra,
  caducidad, estado, ingresos) y filtrable por texto/email y estado
  (`app/static/js/admin-panel.js`, solo `classList`/`addEventListener`,
  cumple CSP; el filtro oculta filas con clase `oculta` en vez de `.style`).
- **Compras por activar** en línea: ver comprobante → activar / rechazar.
- **Concesión manual** de licencia (prueba/cortesía/compensación/pago) plegable.
- Datos: `resumen_admin()` en `app/services/panel_admin.py` (une
  organizaciones + licencias + compras + emails de membresías).
- Los enlaces antiguos `/admin/licencias`, `/admin/compras` y
  `/admin/operacion` siguen funcionando; el hub enlaza entre ellos.

### 3. Gestión de la organización (perfil de empresa)

- **Nombre de la organización** (el del menú lateral) editable en
  `/configuracion` (tarjeta "Tu organización"); al cambiar se regenera el slug
  con unicidad (`_slug_organizacion_unico` en `app/routers/configuracion.py`).
- **Permisos**: solo `propietario` y `administrador` editan (`puede_gestionar`
  de `app/permisos.py`; en SQLite/escritorio el usuario local es el propietario
  implícito). `miembro` y `lectura` ven la página en **solo lectura**
  (`<fieldset disabled>`) y el POST se rechaza en el servidor.
- **Estado del plan visible para el cliente**:
  - Tarjeta **"Tu plan"** en `/configuracion`: plan, fecha de caducidad y días
    restantes (o enlace a `/pago` si no hay plan).
  - Píldora en el **menú lateral** (`base.html`): "✓ Plan mensual · 14 d" o
    "Sin plan · Ver planes". El resumen se calcula en `get_db` y se expone como
    `request.state.licencia_resumen`.
  - Como la sesión del cliente **no puede leer `licencias`** (RLS de operador),
    se creó la función **SECURITY DEFINER**
    `cotizat_security.organization_license_info(p_organization_id)` (migración
    `f9d4c2a7e5b3`) que solo devuelve la fila de la organización del propio
    claim de sesión (`context_organization_id`). Servicio:
    `resumen_licencia_cliente()` en `app/services/licencias.py`.
- Accesos añadidos: enlace **"Editar empresa"** en el menú lateral, botón
  **"Configurar empresa"** en `/cuenta` y en `/organizaciones` para la activa.

### 4. Landing (retoques de conversión)

- Las tarjetas de precios de la home ahora son **clickeables → `/pago`**.
- El **formulario de demo fue eliminado** (el titular no hace demostraciones):
  los botones "Solicitar demostración" pasaron a "Ver planes". El endpoint
  `POST /demo`, la función `enviar_solicitud_demo_por_email` y las plantillas
  `emails/demo.*` quedan **inactivos pero intactos** (reutilizables).

### Migraciones del bloque (2, ambas YA aplicadas en Supabase por el titular)

1. **`e5f2a8d31b6c`** — tabla `compras_plan` + RLS tenant/operador.
   Script: `docs/staging_upgrade_e5f2a8d31b6c.sql`.
2. **`f9d4c2a7e5b3`** — función `cotizat_security.organization_license_info`.
   Script: `docs/staging_upgrade_f9d4c2a7e5b3.sql`.

Head esperado por el runtime: **`f9d4c2a7e5b3`** (`EXPECTED_ALEMBIC_HEAD` en
`app/database.py`, comprobado por `tests/test_rls.py`).

### Bloque posterior: la suma de licencias encadenadas (18/08/2026)

- **`a1b2c3d4e5f6`** — hotfix de tipos de `organization_license_info`.
- **`d4e2f6a8b0c1`** — el resumen del cliente muestra el **final de la cadena**
  de licencias: renovar con días por delante suma el tiempo (4 días + 1 mes →
  ~34 días, no 4). `organization_license_info` calcula el encadenado con una
  CTE recursiva; `app/services/licencias.py` y `panel_admin.py` hacen lo mismo
  en SQLite. **Aplicada en Supabase el 18/08/2026** con
  `docs/staging_upgrade_d4e2f6a8b0c1.sql` (confirmado por el titular).
  Head esperado por el runtime: **`d4e2f6a8b0c1`**.

### Estado y verificación

- **543 tests pasando, 6 omitidos**; 72 plantillas Jinja; `compileall`;
  `node --check`; lock de 42 paquetes; `git diff --check` limpio; auditoría de
  datos sensibles sin hallazgos.
- Smoke test end-to-end: `/pago` → `/pago/comprar` (método + comprobante) →
  confirmación, con almacenamiento local.
- Commits del bloque (en orden): `707f715` (checkout), `3949e2d` (panel admin
  premium), `3ad6d8a` (edición de organización), `80c11e2` (permisos + plan
  visible) y el commit documental del traspaso.

### Pendientes / candidatos siguientes

1. **Fusionar el PR #33 y desplegar `main`** (Vercel). Con las migraciones ya
   aplicadas, `/readyz` debe volver a 200 tras el despliegue.
2. **Fusionar el PR del hotfix de `/inicio`** (commit único en este mismo
   branch) — sin él, el login sigue roto en Vercel. Ver §Hotfix al inicio de
   este documento.
3. **Ensayar el flujo de compra real en staging** con una organización de
   prueba: comprar → comprobante → email → activar desde `/admin` → el cliente
   ve "Tu plan" con fecha y días.
4. Decisión pendiente del titular: **recibo PDF de la compra** para el cliente
   (existe `recibo_licencia.py` para el panel; falta el equivalente para el
   cliente) y **corte automático** (`COTIZAT_EXIGIR_LICENCIA=true`) — ya está
   implementado el corte, falta la licencia de cortesía al titular y el switch
   en Vercel (ver `docs/PANEL_DE_OPERADOR.md` §6 y `docs/PROCESO_PILOTOS.md`).
5. Catálogo: objetivo amplio de **5.000 partidas** (brecha ~1.994) y cierre de
   los **~196 precios provisionales B2B** (requiere cotización del titular).
6. Decisión del titular sobre **revisar los rendimientos** de mano de obra del
   catálogo (comentó que algunos "están fatal"; no se tocaron).
7. Opcional: video/tour grabado (Loom) cuando el titular lo grabe.

---

## ✅ Cierre de sesión — catálogo 3.006 + landing comercial (17/08/2026)

Rama fija de la sesión: `arena/01a0108b-generador-comercial`, basada en `main`
(`e58a94d`, merge del PR #31). El bloque cierra dos frentes: **(1)** ampliar el
catálogo propio hasta superar el mínimo de 3.000 partidas y **(2)** convertir
la página de inicio en una landing comercial pública y premium.

### 1. Catálogo propio: 540 → 3.006 partidas

- **3.006 partidas**, 18 capítulos, 172 subcapítulos y 256 apartados con
  partidas. **0 subcapítulos sin cobertura** (`planificar_cobertura.py`).
- Ampliación por capítulos con generadores reproducibles en `tools/`:
  capítulos 01–10 y 12 hasta el mínimo; luego 11/13/14 y 15/16/17/18.
- Contraste de precios contra el mercado venezolano (rondas 3, 4 y 5:
  eléctrico, plomería/gas/climatización, soldadura/pinturas/seguridad/agregados).
  Corrección de doble conteo (equipo fuera de `recursos`, queda en
  `producto_cliente`) y de terminología (losa, friso, rodapié…).
- ~196 precios provisionales restantes documentados en
  `basedatos_partidas/INVENTARIO.md` (~148 consumibles de bajo valor +
  ~48 especialidades B2B que requieren cotización de proveedor).
- Refactor previo del bloque: E4-001 (routers por dominio), E4-003 (config por
  entorno), E4-016/E4-017 (inventario de aislamiento y auditoría de archivos);
  árbol de partidas con carga bajo demanda (`/partidas`).
- `CATALOGO_VERSION = 3` en `app/services/catalogo_propio.py` (incorpora las
  partidas nuevas a instalaciones existentes).

### 2. Landing pública (la home ya no es el login)

- `/` es la landing pública; `/inicio` es el panel. Login/registro/onboarding
  redirigen a `/inicio`. Alias `/conocer`.
- Landing premium: **hero dividido** (mensaje + maqueta de presupuesto PDF con
  badges de margen/tiempo); **«Así se ve»** con un *presupuesto real de
  remodelación de baño* (partidas, precios y rendimientos reales del catálogo,
  beneficio por partida/capítulo/total, horas por rol y productos con imagen);
  **«El plus que marca la diferencia»** (margen +35 % y tiempo de obra);
  **tour animado** de 4 pantallas (`app/static/js/landing-tour.js`, solo
  `classList` + `addEventListener`); imágenes de producto en `app/static/img/`.
- Sin mención a CYPE en contenido visible. Cifras del catálogo dinámicas
  (`cifras_catalogo()` en `app/routers/common.py`, global Jinja `catalogo`).
- CSP estricta cumplida: sin `innerHTML`, sin estilos inline, sin handlers
  inline.

### Estado y qué sigue

- Suite: **516 passed, 6 skipped**. `git diff --check` limpio.
- PR **#32** desde `arena/01a0108b-generador-comercial` hacia `main`
  (confirmar con `gh pr view 32`).

Pendientes (sin orden de prioridad):

1. Objetivo amplio de **5.000 partidas** (brecha ~1.994; seguir produciendo
   familias reales por capítulo).
2. Cerrar los **~196 precios provisionales** B2B (requiere cotización del
   titular; no se puede cerrar por web).
3. **Formulario de demo real** en la landing (capturar lead) en vez de `mailto:`.
4. Decisión del titular sobre **revisar los rendimientos** de mano de obra del
   catálogo (comentó que algunos «están fatal»; no se tocaron en este bloque).
5. Opcional: añadir el video/tour grabado (Loom) cuando el titular lo grabe.

---

## ✅ Cierre de sesión — catálogo extenso (16/08/2026)

Rama fija de la sesión: `arena/01a00d6f-generador-comercial`, basada en
`main` (`96d82c1`). El bloque deja terminadas y documentadas estas fases:

1. **Taxonomía numérica v2:** 540 partidas reclasificadas en 18 capítulos,
   172 subcapítulos y 147 apartados; código visible `CC.SS.AA.NNN` y alias
   histórico conservado.
2. **Escalabilidad:** índice ligero, ficha bajo demanda, caché, árbol progresivo,
   búsqueda híbrida y gestión paginada; benchmark reproducible con 5.000
   partidas.
3. **Personalización por organización:** ocultar/restaurar oficiales, eliminar
   personalizadas y recibir altas oficiales incrementales sin reactivar ocultas.
4. **Plan de expansión:** matriz exacta 3.000/5.000 para 172 familias y
   diccionario de sinónimos con 146 grupos y 661 términos en los 18 capítulos.

Migraciones `f8a1b2c3d4e5` y `d6e2f9c4b8a1`: **ejecutadas en Supabase por el
titular**. Head actual esperado por el runtime: **`d6e2f9c4b8a1`**.

Validación de cierre: **483 tests superados y 6 omitidos**, 63 plantillas,
compilación Python, JavaScript, lock de 42 dependencias, auditoría de datos
sensibles, terminología venezolana y benchmark de 5.000 partidas.

**PR #31 abierto hacia `main`:**
https://github.com/gtrespana-bit/generador-comercial/pull/31

Checks del PR verificados en verde tras el último push: **CI, Vercel y Vercel
Preview Comments aprobados**. El PR queda listo para revisión y fusión.

Documentos principales:

- `docs/ESTRATEGIA_CATALOGO_EXTENSO.md`
- `docs/FASE_1_CATALOGO_ESCALABLE.md`
- `docs/FASE_2_VISIBILIDAD_CATALOGO.md`
- `docs/FASE_3_MATRIZ_COBERTURA_Y_SINONIMOS.md`
- `basedatos_partidas/salida/RESUMEN_COBERTURA.md`

**Siguiente trabajo:** producción de familias completas, empezando por
`09 Instalaciones` y luego `12 Revestimientos y acabados`. No requiere rediseñar
la taxonomía ni la infraestructura de catálogo.

---

## ✅ 0. Migración de visibilidad aplicada en Supabase (16/08/2026)

El titular confirmó la ejecución de
`docs/staging_upgrade_d6e2f9c4b8a1.sql`. La base queda en el head
**`d6e2f9c4b8a1`**, que coincide con el exigido por el runtime. La migración
añade identidad estable, marca oficial, visibilidad por organización y versión
de alta a `partidas`; no oculta ni elimina datos durante su ejecución.

---

## ✅ 0a. Taxonomía v2 aplicada en Supabase (16/08/2026)

El titular confirmó la ejecución en Supabase de
`docs/staging_upgrade_f8a1b2c3d4e5.sql`. La base queda en el head
**`f8a1b2c3d4e5`**, sobre `a3d7e9c1b5f2`. Fue el head intermedio anterior a
`d6e2f9c4b8a1`.

La migración añade el árbol de categorías, el vínculo de cada partida a su
apartado, el código anterior y `version_catalogo`. No modifica presupuestos ni
precios. **Las secciones posteriores conservan el histórico del corte anterior y
por eso nombran `a3d7e9c1b5f2` como head.**

---

## ⚠️ 0bis. Recuperación de sesión del 16/08/2026 (léase antes que el resto)

La rama `arena/01a00b99-generador-comercial` se recuperó en una sesión nueva a
partir de un parche de exportación. Estado real verificado en esta sesión:

- **Base:** commit `17e1172` («Add files via upload»), única rama
  `arena/01a00b99-generador-comercial`. No se cambió de rama.
- **Parche aplicado completo con `git apply --index`** (formato `diff --git`,
  sin cabeceras `From`), excluyendo únicamente los artefactos de `handoff/`:
  sus binarios venían como `Binary files differ` sin datos recuperables y la
  carpeta debía eliminarse de todas formas. Todo lo demás (32 rutas de código,
  plantillas, pruebas, docs y migración) aplicó limpio, sin conflictos.
- **Eliminados:** el `.patch` de recuperación de la raíz (estaba trackeado en
  el commit base, por eso figura como borrado) y toda carpeta `handoff/`. No
  queda ningún `.patch` ni `handoff` en el árbol.
- **Estado git actual:** los cambios recuperados están **staged pero SIN
  commit** (33 rutas: 32 de contenido + el borrado del `.patch`). El head de
  la rama sigue siendo `17e1172`; no existen los commits `435a690`, `85e590c`
  ni `33fdf10` en este repositorio, solo su contenido aplicado. Sin PR abierto
  y sin push, por instrucción expresa.
- **Siguiente paso recomendado:** revisar `git status` y, con autorización,
  commitear el estado recuperado en esta misma rama antes de seguir trabajando.

Verificación ejecutada en esta sesión (todo en verde):

- Suite completa: **409 passed, 6 skipped** (las 6 son pruebas PostgreSQL
  omitidas por no existir URL administrativa de pruebas).
- Plantillas Jinja: **59 correctas**. `compileall`: OK. JavaScript
  (`node --check`): OK. `tools/verificar_lock.py`: **42 paquetes coherentes**.
  `git diff --check`: OK. `tools/simular_vercel_rofs.py`: importación correcta.

Estado funcional confirmado: **E3-016 a E3-019 completados** (envío por email,
enlace público revocable, aceptación/rechazo trazable, notificación y estado
controlado). La migración `c2f6e8a1d934` está en
`migrations/versions/c2f6e8a1d934_public_proposal_links.py`; al cierre de esta
sesión **ya fue aplicada y verificada en Supabase** — ver §0ter, que deja sin
efecto el párrafo original de esta sección.

---

## ✅ 0ter. Migraciones del bloque aplicadas en Supabase (16/08/2026)

El titular ejecutó en Supabase SQL Editor los scripts del bloque y **verificó
los dos resultados** esperados:

- **`c2f6e8a1d934` (propuestas):** la tabla `public.enlaces_propuesta` tiene
  exactamente las 4 políticas previstas:

  | polname | polcmd | using_expr | check_expr |
  |---|---|---|---|
  | `cotizat_proposal_insert_tenant` | INSERT | — | `tenant_access(organizacion_id, true)` |
  | `cotizat_proposal_select_public` | SELECT | `token_hash = NULLIF(current_setting('cotizat.proposal_token_hash', true), '')` AND `revoked_at IS NULL` AND `expires_at > clock_timestamp()` | — |
  | `cotizat_proposal_select_tenant` | SELECT | `tenant_access(organizacion_id, false)` | — |
  | `cotizat_proposal_update_tenant` | UPDATE | `tenant_access(organizacion_id, true)` | `tenant_access(organizacion_id, true)` |

- **`a3d7e9c1b5f2` (baja):** la función `cotizat_security.baja_organizacion`
  existe con `security_definer = true` y propietario `postgres` (el usuario
  que aplica la migración), tal como declara el script. ✅ La guarda de
  versión del script exige `c2f6e8a1d934` antes, así que la cadena está
  completa: `b7c4a9e2d31f → c2f6e8a1d934 → a3d7e9c1b5f2`.

**Consecuencia operativa esperada:** hasta que el código de esta rama (que
exige el head `a3d7e9c1b5f2`) se despliegue en el entorno migrado, su
`/readyz` responderá **503** porque la base va por delante del código. No es
un fallo: es la comprobación de head funcionando como está diseñada. Tras el
despliegue, `/readyz` debe volver a 200.

---

## 🚀 0quater. Cierre de bloque con PR del titular (16/08/2026)

**PR #27 creado y ABIERTO** — https://github.com/gtrespana-bit/generador-comercial/pull/27
desde `arena/01a00b99-generador-comercial` hacia `main`, con los 8 commits del
bloque. **Al volver, confirmar el estado** (abierto / fusionado) con:

```bash
gh pr list --head arena/01a00b99-generador-comercial --state all
# o directamente:
gh pr view 27 --json state,statusCheckRollup
```

Commits que contiene el PR (en orden):

1. `9fd5afa` — recuperación de E3-016 a E3-019 (envío, enlaces, respuesta,
   notificación) desde el parche de recuperación.
2. `bd684e1` — E3-020/E3-021: respaldo web verificable y restauración en dos
   pasos.
3. `a0d2711` — E3-022/E3-023: exportación portátil y baja con borrado
   verificado.
4. `7ddb7de` — E3-024: panel `/admin/operacion` y registro de errores.
5. `2bf6d19` — documentación de las migraciones aplicadas en Supabase.
6. `d3eb2a7` — Etapa 4 (primer bloque): autorización centralizada
   (`app/permisos.py`) y logs estructurados (`app/logs.py`).
7. `2de721a` — documentación del traspaso de sesión (este §0quater y §7).
8. `2a0d56d` y el commit de cierre documental posterior — traspaso definitivo
   para el PR #27 con su número y enlace registrados.

Estado verificado de la rama en el momento del PR:

- Suite: **465 passed, 6 skipped**; 63 plantillas; `compileall`; JavaScript;
  lock (42 paquetes); `git diff --check`; simulación de Vercel read-only.
- Migraciones `c2f6e8a1d934` y `a3d7e9c1b5f2` **ya aplicadas y verificadas en
  Supabase** (§0ter): no hay que volver a aplicarlas. Al desplegar este
  código, `/readyz` del entorno migrado vuelve a 200 (hasta entonces, 503
  esperado).
- Sin secretos en el repositorio (la auditoría `tools/auditar_datos_sensibles.py`
  sigue activa en CI).
- **CI:** al crear el PR, el workflow `CI` se ejecuta automáticamente sobre
  él (el disparador `pull_request` hacia `main`; la copia del workflow vive en
  `docs/ci/ci.yml`). Fusionar solo cuando termine en verde.

### Qué hacer justo después del PR (árbol de decisión para la sesión nueva)

**A. Si el PR sigue abierto (o falló CI):**

1. Mirar los checks en GitHub: `gh pr view 27 --json statusCheckRollup`.
2. Si algo falla, corregirlo en esta misma rama (la sesión continúa en
   `arena/01a00b99-generador-comercial`) y empujar; el check se re-ejecuta.
3. No empezar E4-001 con el PR roto: primera prioridad, PR en verde.

**B. Si el PR fue fusionado (escenario normal):**

1. `main` ya contiene todo el trabajo (los 7 commits). Si el HEAD local de la
   sesión nueva aparece retrocedido: `git fetch origin
   arena/01a00b99-generador-comercial && git reset --mixed FETCH_HEAD`
   (o partir de `main` directamente, según cómo abra la sesión nueva).
2. **Desplegar** el código de `main`/rama (Vercel, Production): con las
   migraciones ya aplicadas (§0ter), `/readyz` debe volver a **200**. Si
   respondiera 503, revisar `checks` de `/readyz` antes de nada.
3. **Ensayar en staging el flujo real** con una organización de prueba:
   respaldo → restauración → exportación → `/admin/operacion` (no ejecutar la
   baja sobre datos reales; usar solo la organización de prueba).
4. **Continuar el desarrollo** por la tarea planificada: **E4-001 — dividir
   `app/main.py` en routers por dominio** (detalle en §5, punto 10).

### Recordatorio de entorno para la sesión nueva

- Recrear el entorno: `python -m venv .venv && .venv/bin/pip install -r
  requirements.lock` (el `.venv` no persiste entre sesiones).
- Los secretos (Supabase, Resend, Upstash) nunca se piden ni se tocan desde
  el código; todo lo que depende de ellos es del titular (§6, reglas).

---

## 0. Lo último hecho: PR #25 fusionado en `main`

**Decisión de negocio adoptada en esta sesión (titular, 16/08/2026):**

- **E1-059 → cobro manual para el piloto** (transferencia / Zelle / Binance /
  Pago Móvil, activación a mano). La vía «en serio» queda acordada: autónomo
  en España (036 + RETA) + Stripe cuando haya cobro recurrente. Análisis en
  `docs/COBRO_Y_LICENCIAS.md`.

Con esa decisión se cerraron **E1-060 por completo** y **E1-061**:

1. **Recibo PDF** por licencia de pago (`app/services/recibo_licencia.py`):
   número estable `CT-000NNN`, período inclusive, método/referencia del cobro;
   pie declara **comercial sin validez fiscal** mientras no haya razón social.
   Enlace «recibo PDF» en el panel; cortesías y pruebas no tienen recibo.
2. **Corte automático de acceso**: con `COTIZAT_EXIGIR_LICENCIA=true`
   (**apagado por omisión**), una organización sin licencia vigente recibe la
   pantalla «Acceso suspendido» (`app/templates/licencia_suspendida.html`) en
   cualquier ruta de negocio; los datos no se tocan y vuelven al renovar. En
   PostgreSQL el corte pregunta a `cotizat_security.organization_has_license`
   (SECURITY DEFINER guardada por claim de organización). Escritorio jamás
   exige licencia.
3. **Avisos de vencimiento por correo** (botón del panel, Resend): escribe a
   propietario/administrador activos vía
   `cotizat_security.organization_admin_emails` (guardada por marca de
   operador), anota el envío en la propia licencia y no repite el mismo día.
4. **Bug latente corregido**: la política `cotizat_org_select` solo devolvía
   las organizaciones con membresía propia, así que en producción el panel era
   **ciego a las organizaciones de clientes**. La migración `b7c4a9e2d31f`
   añade la vía de operador a esa política (sin tocar datos de negocio).
5. **E1-061 documentado** en `docs/PROCESO_PILOTOS.md` — guion completo:
   demostración → registro → cobro manual → licencia + recibo → seguimiento
   semanal con avisos → suspensión automática → reactivación. Su §0 lista los
   requisitos previos en el ORDEN correcto.

Migración nueva: **`b7c4a9e2d31f`** (head exigido por `/readyz`; script para
Supabase en `docs/staging_upgrade_b7c4a9e2d31f.sql`, con guarda de versión).
29 pruebas nuevas en `tests/test_licencias_acceso.py`. Suite:
**391 passed, 5 skipped**. `compileall`, plantillas (53), lock (42 paquetes),
simulación de Vercel RO y `git diff --check` en verde. El PR #25 fue
fusionado el 16/08/2026; CI de `main` terminó en verde. Después del despliegue,
el titular confirmó que las licencias funcionan.

La validación externa de usabilidad también quedó cerrada el 16/08/2026:
varias personas probaron el producto, profesionales del ámbito de la
construcción no necesitaron ayuda y varios presupuestos genéricos de baño se
terminaron en aproximadamente 10 minutos. No se localizaron errores. Las
personas sin conocimientos de construcción tardaron más de 20 minutos, dato
coherente con el nicho profesional definido y no un fallo del recorrido.

### Decisiones de alcance posteriores del titular (16/08/2026)

1. **Etapa 1 se considera completada.**
2. Las partidas actuales son **propias, de ejemplo y solo para pruebas**. Se
   eliminarán cuando se carguen las partidas reales revisadas; catálogo y
   partidas comerciales quedan fuera del trabajo actual.
3. La **validación comercial pagada se aplaza hasta el final**. El titular no
   entregará a clientes un generador que todavía considere incompleto. No se
   abrirán pilotos durante los siguientes bloques técnicos.
4. La etapa activa pasa a ser el **cierre funcional y operativo web**. El
   siguiente bloque recomendado completa entrega y aceptación del presupuesto.

### Trabajo acumulado en la rama actual (sin PR por decisión del titular)

- **E3-016:** envío del presupuesto por email con PDF adjunto y congelado.
- **E3-017:** enlace público seguro, temporal y revocable a una propuesta.
- **E3-018:** aceptación/rechazo único y trazable de la versión exacta.
- **E3-019:** aviso inmediato a administradores y cambio de estado solo para la
  última versión, con constancia y reintento si falla Resend.
- Head nuevo de la rama: **`c2f6e8a1d934`**. Producción continúa correctamente
  en `b7c4a9e2d31f`; no aplicar `docs/staging_upgrade_c2f6e8a1d934.sql` ni
  desplegar el código hasta terminar el bloque y recibir autorización expresa.
- Suite: **409 passed, 6 skipped**; 59 plantillas, `compileall`, JavaScript,
  lock y `git diff --check` en verde.

### Pasos operativos pendientes DEL BLOQUE DE LICENCIAS (histórico)

1. ~~Fusionar el PR #25 y desplegar `main`.~~ **Hecho el 16/08/2026**; CI en
   verde y funcionalidad de licencias confirmada por el titular.
2. ~~Aplicar `docs/staging_upgrade_b7c4a9e2d31f.sql` en Supabase~~ **Hecho el
   16/08/2026 (noche)**: funciones creadas con propietario `postgres` y
   `security_definer=true` (verificado en `pg_proc`).
3. **Conceder licencia de cortesía a la propia organización del titular**
   desde el panel (nota «uso del titular»). Hacerlo ANTES del paso 4.
4. Cuando empiece el piloto de pago: `COTIZAT_EXIGIR_LICENCIA=true` en Vercel
   (Production) + redeploy. El panel deja de mostrar el aviso ámbar.
   Verificación previa sin tocar producción (SQL Editor):
   `BEGIN; SELECT set_config('cotizat.organization_id', '<id>', true); SELECT cotizat_security.organization_has_license(<id>); ROLLBACK;`
   → FALSE sin licencia, TRUE tras concederla. La matriz completa de qué puede
   hacer cada estado está en `docs/PANEL_DE_OPERADOR.md` §6.
5. Verificación en producción del fix de visibilidad: con un **segundo correo
   de cliente** registrado (organización sin membresía del titular), comprobar
   que ahora SÍ aparece en `/admin/licencias`.

---

## 1. Histórico de la sesión anterior (rama `arena/01a00825`, PR #24 fusionado)

- PR #23 (merge `52d1a09`): E1-021 (auditoría de datos sensibles — repos privado
  y sin credenciales), fix de invitaciones sin cuenta previa (descubiertas por
  email verificado desde `/organizaciones`), y E1-060 primera parte.
- PR #24 (merge `4e7eeeb`): docs `.env.example` + script SQL de la migración
  `f4c1d8e37a95` (panel de operador `/admin/licencias`: ver, conceder,
  renovar, regalar prueba/cortesía, compensar, cancelar con constancia;
  tabla no-tenant con RLS de operador; operadores en `COTIZAT_OPERADORES`).
- E1-060 primera parte **desplegado y verificado en producción** (16/08/2026,
  tarde): migración aplicada, `COTIZAT_OPERADORES` en Vercel, panel confirmado
  por el titular. **Decisión suya:** el panel se queda deliberadamente simple;
  la mejora de interfaz es pendiente futuro, no bloqueante.
- Contenido comercial cerrado: E1-053 (`/legal/preguntas`), E1-054 y E1-055
  (`/legal/soporte`), E1-052 (PDF de presupuesto de muestra en `/conocer`).
- Suite al cierre de esa sesión: 362 passed, 5 skipped.

## 2. Incidencia de Auth (registro + recuperación) — cerrada

Resuelta en operativo el 15-16/08/2026: SMTP personalizado con Resend, Redirect
URLs de Supabase completadas (`/acceso` añadido, **confirmado por el titular en
la sesión del 16/08 noche**) y rate limit de emails a 30/hora (**también
confirmado**). El log `Supabase Auth <método> <path> -> HTTP <código>` queda en
el servidor por si algo volviera a fallar (Vercel → Logs).

## 3. Pendientes operativos del usuario (sin código)

> Guía paso a paso: `docs/PENDIENTES_OPERATIVOS.md`. Ninguno bloquea el
> desarrollo. **Estado actualizado al 16/08/2026 (noche):**

1. ~~Redirect URL `/acceso` + rate limit ~30/hora + cooldown 60 s.~~ **Hecho**,
   confirmado por el titular el 16/08.
2. Crear `soporte@cotizat.online`. **Aplazado por decisión del titular: lo
   creará cuando haga falta de verdad** (los avisos de vencimiento ya
   instruyen escribir a esa dirección; conviene tenerlo antes del piloto).
3. Razón social → `COTIZAT_LEGAL_ENTITY` en Vercel. **Aplazado**: se hará
   cuando estemos a punto de lanzar (el recibo y los legales muestran el
   marcador honesto mientras tanto, a propósito).
4. Vercel Hobby prohíbe uso comercial → **Pro (20 $/mes)** antes de cobrar al
   primer cliente. **Aplazado**: sin cobros todavía, no corre prisa.
5. ~~Repetir la prueba E2E «invitación sin cuenta previa» en producción.~~
   **Hecha el 16/08/2026 (noche)**: funciona.

## 4. Aparcado por decisión del usuario

**Puntos 13-manual y 14 de la matriz de aceptación** — no pedirlos hasta que el
desarrollo esté cerrado (guía en `docs/MATRIZ_PASOS_MANUALES.md`). Landing y
legales: v1 aceptada con mejoras pendientes declaradas; iteración pendiente, no
bloqueante. Interfaz mejorada del panel de operador: pendiente futuro.

## 5. Qué es lo siguiente

1. ~~**E3-016 — Envío por email del presupuesto.**~~ **Completado en la rama
   de trabajo el 16/08/2026**: formulario precargado, PDF adjunto por Resend,
   `Reply-To`, estado solo tras confirmación, versión inmutable, PDF exacto
   privado y constancia interna. Suite: 397 passed, 5 skipped.
2. ~~**E3-017 — Enlace público seguro y revocable.**~~ **Completado en la
   rama el 16/08/2026**: versión/PDF congelados, secreto solo en SHA-256,
   caducidad, revocación, página pública mínima y RLS por hash. Migración
   `c2f6e8a1d934` **aplicada y verificada por el titular en Supabase el
   16/08/2026** (las 4 políticas de `enlaces_propuesta` coinciden con el
   script). Suite: 403 passed, 6 skipped.
3. ~~**E3-018 — Aceptación o rechazo trazable.**~~ **Completado en la rama el
   16/08/2026**: una respuesta por enlace, versión exacta, identidad declarada,
   comentario y fecha/hora; función PostgreSQL limitada. Suite: 405 passed,
   6 skipped.
4. ~~**E3-019 — Notificación y estado controlado.**~~ **Completado localmente
   el 16/08/2026**: aviso a propietarios/administradores, cambio solo si es la
   última versión y reintento sin perder la respuesta. Suite: 409 passed,
   6 skipped.
5. ~~**E3-020 — Copia de seguridad web completa y verificable.**~~
   **Completado en la rama el 16/08/2026**: paquete `cotizat-backup` v1
   descargable por propietario/administrador en ambos backends, con manifest,
   omisiones declaradas y cada archivo bajo su SHA-256.
6. ~~**E3-021 — Restauración controlada en dos pasos.**~~ **Completado en la
   rama el 16/08/2026**: re-subida del MISMO archivo (SHA-256) + confirmación
   explícita, verificación íntegra antes de escribir, fusión idempotente sin
   borrar ni duplicar, archivos re-escritos al almacén privado con
   reutilización por huella y trazabilidad de propuestas conservada como
   notas. Sin migración nueva. Suite del bloque: **423 passed, 6 skipped**
   (14 pruebas nuevas en `tests/test_respaldo_restauracion.py`).
7. ~~**E3-022 — Exportación portátil.**~~ **Completado en la rama el
   16/08/2026**: `cotizat-export` v1 con CSV por tabla, archivos con nombre
   original y respaldo verificable embebido; solo propietario/administrador.
8. ~~**E3-023 — Baja con borrado verificado.**~~ **Completado en la rama el
   16/08/2026**: solo el propietario, nombre exacto escrito + casilla,
   archivos borrados antes de la base, borrado transaccional completo y
   aislado por organización; función `cotizat_security.baja_organizacion` en
   PostgreSQL. Migración **`a3d7e9c1b5f2`** (head exigido) **aplicada y
   verificada por el titular en Supabase el 16/08/2026** (`baja_organizacion`
   SECURITY DEFINER con propietario `postgres`). Suite del bloque:
   **441 passed, 6 skipped**
   (18 pruebas nuevas). Detalles en
   `docs/EXPORTACION_Y_BAJA_ORGANIZACION.md` y
   `docs/RESPALDO_Y_RESTAURACION_WEB.md`.
9. ~~**E3-024 — Monitorización y diagnóstico.**~~ **Completado en la rama el
   16/08/2026**: panel `/admin/operacion` solo para operador con los chequeos
   de `/readyz`, hechos operativos y registro acotado en memoria de errores no
   capturados (sin query strings ni tokens); middleware que captura y relanza
   sin cambiar la semántica HTTP. Sin migración nueva. Suite del bloque:
   **453 passed, 6 skipped** (12 pruebas nuevas en `tests/test_operacion.py`).
   Detalle en `docs/MONITORIZACION_Y_DIAGNOSTICO.md`.

**Con E3-024 queda completo el cierre funcional y operativo de la Etapa 3**
(E3-016 a E3-024) en la rama, y **las dos migraciones del bloque están
aplicadas y verificadas en Supabase** (ver §0ter). Siguiente según la puerta
de salida del plan: **desplegar el código de la rama** (hasta entonces
`/readyz` responderá 503 en el entorno migrado porque la base va por delante
del código), ensayar el flujo real en staging, y después el **endurecimiento
técnico de la Etapa 4**. Catálogo comercial y validación pagada permanecen
aplazados hasta que el titular declare completo el producto.

10. ~~**Etapa 4, primer bloque — autorización centralizada y logs
    estructurados.**~~ **Completado en la rama el 16/08/2026**:
    `app/permisos.py` (E4-002/E4-009) concentra los conjuntos de roles y sus
    predicados; los checks inline de las rutas migraron a los predicados y
    una prueba estática impide su regreso; `app/logs.py` (E4-022) añade modo
    JSON opt-in (`COTIZAT_LOG_JSON`) con redacción de credenciales en
    mensajes y trazas. Suite: **465 passed, 6 skipped** (12 pruebas nuevas en
    `tests/test_permisos.py` y `tests/test_logs.py`). Siguiente de la Etapa
    4: **E4-001 — dividir `app/main.py` en routers por dominio** (el plan
    marca la sección 4.1 como el trabajo estructural pendiente más grande).

## 6. Reglas invariables (no negociables)

- **no abrir ni pedir fusionar un PR durante un bloque de trabajo activo**: al
  fusionarlo, el titular debe cerrar el chat y se pierde el acceso de esta
  sesión a la rama; los PR solo se crean cuando sean absolutamente necesarios,
  al terminar un bloque funcional completo y con autorización expresa del
  titular. (Cumplido en esta sesión: el PR del bloque fue creado por el
  titular al cierre — ver §0quater — y la regla sigue rigiendo para el
  siguiente bloque.)
- nunca configurar `MIGRATION_DATABASE_URL` en runtime;
- nunca usar una conexión `postgres`/administrativa como `DATABASE_URL`;
- nunca poner `service_role`/`sb_secret_` en variables públicas del frontend;
- nunca fijar `COTIZAT_REQUIRE_RLS_ROLE=false` como solución de despliegue;
- no activar `COTIZAT_EXIGIR_LICENCIA=true` sin haber concedido antes la
  licencia de cortesía a la organización del titular;
- si staging falla, corregir el problema observado **sin relajar** CSRF, CSP,
  RLS, bucket privado ni la exigencia del rol limitado;
- usar solo datos ficticios en las pruebas de la matriz;
- toda dependencia nueva exige pin `==` en `requirements.txt` más
  `python tools/generar_lock.py`, o falla `tests/test_dependencias_bloqueadas.py`.

Nota operativa: el token de la app que abre cambios automáticos carece del
permiso `workflows`; `docs/ci/ci.yml` existe como copia y el workflow se instaló
manualmente.

Nota de entorno: el `.venv` no persiste entre sesiones (recrearlo es normal) y
el HEAD local puede aparecer retrocedido al inicio de una sesión nueva; si los
archivos están intactos, basta `git fetch origin <rama>` + `git reset --mixed
FETCH_HEAD` para realinear sin perder nada.

## 7. Mensaje para iniciar la conversación nueva

Copiar tal cual, sin añadir secretos ni tokens:

---

Continúa el proyecto CotizaT. Antes de proponer nada, lee
`docs/PUNTO_DE_CONTINUACION.md` (sección «Cierre de sesión — checkout de
planes + panel admin premium + gestión de organización» primero) y
`basedatos_partidas/EMPEZAR_AQUI.md`. No repitas trabajo ya hecho y no me
pidas secretos.

**Dónde quedó todo (18/08/2026, cierre con PR del titular).**

- Rama `arena/01a012cd-generador-comercial`, basada en `main` (`88d3859`,
  merge del PR #32). **PR #33 creado hacia `main`:**
  https://github.com/gtrespana-bit/generador-comercial/pull/33 (confirmar
  estado con `gh pr view 33`; si ya está fusionado, `main` contiene el código).
- Contenido del bloque: **checkout de planes con pago manual** (`/pago`,
  `/pago/comprar` con método + comprobante, `/pago/confirmacion`; Pago móvil,
  Binance, Kontigo, USDT en `app/datos_pago.py`), **panel admin premium**
  (`/admin` con KPIs, tabla ordenable/filtrable de clientes y planes,
  activación de compras), **gestión de organización** (nombre editable, solo
  propietario/admin editan, tarjeta "Tu plan" y píldora en el menú lateral con
  fecha de caducidad y días restantes) y **landing sin demo** con tarjetas de
  precio clickeables.
- Migraciones **`e5f2a8d31b6c`** (compras_plan) y **`f9d4c2a7e5b3`**
  (organization_license_info) **ya aplicadas en Supabase** por el titular.
  Head esperado: `f9d4c2a7e5b3`.
- Suite: **543 passed, 6 skipped**; 72 plantillas; `git diff --check` limpio.
- Al empezar: realinea si el HEAD aparece retrocedido
  (`git fetch origin arena/01a012cd-generador-comercial && git reset --hard
  FETCH_HEAD`) y recrea `.venv` (`python3 -m venv .venv && .venv/bin/pip
  install -q -r requirements-dev.txt`).
- Siguientes candidatos: fusionar/desplegar el PR #33 y ensayar el flujo de
  compra en staging; **recibo PDF de la compra para el cliente** y activar
  `COTIZAT_EXIGIR_LICENCIA` cuando toque; catálogo a **5.000 partidas**;
  cerrar **~196 precios provisionales B2B** (requiere cotización); decisión
  sobre **rendimientos** del catálogo.
- No repetir: el checkout, el panel admin, la edición de organización y la
  tarjeta de plan ya están hechos; **no volver a poner formulario de demo** en
  la landing; no inventar precios ni rendimientos; no nombrar a CYPE en
  contenido visible.

---
