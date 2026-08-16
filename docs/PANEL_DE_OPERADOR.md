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

- **No corta el acceso automáticamente.** Hoy el registro es informativo: nadie
  se queda fuera de la aplicación por no tener licencia. Aplicar el corte es una
  decisión de negocio con consecuencias (dejar a un cliente fuera por un error
  de registro), así que se deja para cuando exista el cobro real (E1-059).
- **No genera todavía el recibo en PDF.** El registro ya guarda todo lo
  necesario (importe, método, referencia, período); falta el documento.
- **No envía avisos de vencimiento por correo.** El panel los marca en ámbar.
- **La interfaz es deliberadamente simple** (decisión del titular, 16/08/2026):
  tabla + formulario, sin adornos. Funciona y cubre lo esencial, pero se
  mejorará más adelante (mejor agrupación por estado, filtros, acciones
  visibles sin redirigir, etc.).

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
