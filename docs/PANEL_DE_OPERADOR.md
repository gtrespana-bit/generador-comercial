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
| Usuario suspendido | ✅ Solo: iniciar/cerrar sesión, `/organizaciones` (cambiar de organización), aceptar invitaciones y páginas legales | Nada de datos: ni presupuestos, clientes, catálogo, PDFs ni descargas |

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
