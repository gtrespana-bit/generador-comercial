# Matriz de aceptación: los pasos que solo puedes hacer tú

Guía operativa para cerrar en `https://cotizat-generador.vercel.app` los puntos
de la matriz que no pueden automatizarse: **6, 7, 8, 9, 11, 12, 13 (parte
manual) y 14**. Los puntos 1–5 ya están superados y el 10 lo cubre CI.

Duración estimada: **45–60 minutos**. Usa solo datos ficticios.

---

## Antes de empezar: lo que necesitas a mano

1. **Dos correos reales y distintos**, ambos accesibles ahora mismo.
   - Usuario A: el que ya usaste para crear la Organización A.
   - Usuario B: uno nuevo, que todavía no existe en CotizaT.
   - Truco si te falta uno: Gmail acepta `tucorreo+b@gmail.com` como dirección
     distinta y entrega en la misma bandeja.
2. **Dos navegadores, o uno normal y otro en ventana privada.** No sirve usar
   pestañas del mismo navegador: la sesión es una cookie compartida y al entrar
   como B saldrías de A. Sugerencia: Chrome para A, Chrome en incógnito para B.
3. Un bloc de notas para pegar el enlace de invitación.

> **Aviso sobre el envío de emails.** El SMTP por defecto de Supabase limita a
> **~2-4 correos por hora**. Registrar al Usuario B y confirmar su email consume
> parte de esa cuota, y si además pruebas recuperaciones de contraseña puedes
> quedarte sin envíos a mitad del recorrido. Si un email no llega, casi siempre
> es el límite y no un fallo de CotizaT: espera una hora o configura un SMTP
> propio. **No desactives «Confirm email» para esquivarlo**: es el ajuste que
> destapó el fallo de registro corregido en `d4aa7f1`.

> **Aviso importante sobre el punto 6.** CotizaT envía el correo de invitación
> automáticamente cuando `RESEND_API_KEY` y `COTIZAT_EMAIL_FROM` están
> configuradas (ver `docs/EMAILS_INVITACION.md`). Si el correo no está
> configurado o el envío falla, la pantalla muestra el enlace **una sola vez**
> y no lo vuelve a enseñar. En ese caso, cópialo en el bloc de notas antes de
> navegar a otra página; si lo pierdes, revoca la invitación y crea otra.

---

## Punto 6 — Invitar al Usuario B y que acepte una sola vez

### 6.1 (Usuario A) Crear la invitación

1. En el navegador de **A**, entra en `https://cotizat-generador.vercel.app/equipo`.
2. En **"Invitar a una persona"**, escribe el email de B.
3. En **Rol**, elige **"Solo lectura"**. Es importante que sea este rol: el
   punto 7 comprueba precisamente que `lectura` no puede escribir.
4. Pulsa el botón de invitar.
5. Aparece un recuadro **"Enlace generado"** con un campo de texto.
   **Copia ese enlace ahora** y pégalo en tu bloc de notas.

✅ **Correcto si:** ves el mensaje "Invitación creada para «email de B»" y el
enlace tiene la forma `https://cotizat-generador.vercel.app/invitaciones/<token largo>`.

❌ **Si falla:** un error tipo "Escribe un email válido" o "Ese email ya
pertenece al equipo" significa que B ya está dentro; anótalo y sigue.

### 6.2 (Usuario B) Registrarse y verificar el email

1. En el **segundo navegador**, abre `https://cotizat-generador.vercel.app/acceso`.
2. Regístrate con el email de B y una contraseña nueva.
3. Ve al buzón de B, abre el correo de confirmación de Supabase y pulsa el
   enlace de verificación.

> Esto no es opcional. CotizaT rechaza la invitación con "Confirma tu email
> antes de aceptar la invitación" si B no ha verificado su correo.

### 6.3 (Usuario B) Aceptar la invitación

1. Con la sesión de B iniciada, pega en ese navegador el enlace del paso 6.1.
2. Pulsa el botón de aceptar.

✅ **Correcto si:** te lleva a `/organizaciones` con el mensaje
**"Invitación aceptada. Ya puedes entrar a la organización."** y ves
"Constructora A" (o el nombre que le pusieras) en la lista.

### 6.4 Comprobar que el enlace es de un solo uso

1. **Vuelve a pegar el mismo enlace** en el navegador de B y pulsa aceptar otra vez.

✅ **Correcto si:** responde **"La invitación no es válida o ya caducó."**
Esto es el corazón del punto 6: el token se consume al usarse.

❌ **Si te deja aceptar dos veces:** es un fallo grave de seguridad. Detente y
avísame.

---

## Punto 7 — El rol `lectura` consulta pero no escribe

Todo esto en el navegador de **B**, dentro de la Organización A.

### 7.1 Lo que B **sí** debe poder hacer

1. Abre la lista de presupuestos y entra en el que creó A.
2. Descarga su PDF.

✅ **Correcto si:** ve los datos y el PDF se descarga sin error.

### 7.2 Lo que B **no** debe poder hacer

Intenta estas tres cosas, una por una:

1. Crear un presupuesto nuevo.
2. Editar el presupuesto existente (cambia el título y guarda).
3. Subir un anexo o una imagen de producto.

✅ **Correcto si:** las tres fallan con una pantalla de acceso denegado y el
mensaje **"Tu rol es de solo lectura y no permite modificar datos."**

❌ **Si alguna operación se guarda:** anota exactamente cuál y detente.

> Ojo: puede que el botón ni siquiera aparezca en pantalla. Eso también es
> correcto, pero es una defensa más débil. Si quieres afinar, prueba a navegar
> directo a `https://cotizat-generador.vercel.app/presupuestos/nuevo`: debe
> denegar igualmente.

### 7.3 B no puede ver el equipo

1. Con B, entra en `https://cotizat-generador.vercel.app/equipo`.

✅ **Correcto si:** deniega con **"Tu rol no permite administrar el equipo."**

---

## Punto 8 — Ascender a B a `miembro`

1. En el navegador de **A**, vuelve a `/equipo`.
2. Localiza la ficha de B. En su desplegable de rol, cambia **"Solo lectura"**
   por **"Miembro"** y guarda.
3. ✅ Debe aparecer **"Membresía actualizada."**
4. En el navegador de **B**, recarga y **crea un presupuesto** con cualquier
   dato ficticio.

✅ **Correcto si:** ahora sí lo guarda sin error.

> Si B tenía la pantalla abierta, que recargue: el rol se lee en cada petición,
> pero la página vieja puede tener botones ocultos.

---

## Punto 9 — Organización B con nombres homónimos (la prueba clave)

El objetivo es demostrar que dos empresas pueden usar **los mismos nombres y
números** sin mezclarse. Por eso hay que repetir los nombres a propósito.

1. Con **B**, ve a `https://cotizat-generador.vercel.app/organizaciones/nueva`.
2. Crea una organización llamada **exactamente igual** que la de A
   ("Constructora A", o el nombre que usaste).
3. Al crearla, quedas dentro de la organización nueva.
4. Crea un cliente con **el mismo nombre** que uno que ya exista en la
   Organización A.
5. Crea un presupuesto y fíjate en el número que le asigna.

✅ **Correcto si:**
- El presupuesto de la Organización B empieza otra vez en **`P-2026-001`**
  (la numeración es independiente por empresa, no continúa la de A).
- En la lista de clientes de B **solo** aparece el cliente que acabas de crear,
  no los de A.
- En la lista de presupuestos de B **solo** está el suyo.

6. **La comprobación inversa, que es la importante:** en `/organizaciones`,
   vuelve a seleccionar la Organización A y confirma que **sus** datos siguen
   intactos y que no aparece nada de la Organización B.

❌ **Si ves un cliente o presupuesto cruzado entre organizaciones**, detente
inmediatamente y avísame con la captura: es un fallo de aislamiento.

---

## Punto 11 — Cookies y CSRF

### 11.1 Cookies (en cualquiera de los dos navegadores, con sesión iniciada)

1. Pulsa **F12** para abrir DevTools.
2. Ve a **Application** (Chrome) o **Almacenamiento** (Firefox) →
   **Cookies** → `https://cotizat-generador.vercel.app`.
3. Busca estas tres cookies y mira sus columnas:

| Cookie | HttpOnly | Secure | SameSite |
|---|---|---|---|
| `cotizat_access_token` | ✔ | ✔ | Lax |
| `cotizat_refresh_token` | ✔ | ✔ | Lax |
| `cotizat_organization_id` | ✔ | ✔ | Lax |

✅ **Correcto si:** las tres tienen marcadas HttpOnly y Secure. Que sean
HttpOnly significa que un script no puede leer tu sesión.

4. Comprobación extra de 5 segundos: en la pestaña **Console**, escribe
   `document.cookie` y pulsa Enter.

✅ **Correcto si:** la respuesta **no** contiene `cotizat_access_token`.

### 11.2 Cierre de sesión

1. Cierra sesión desde el menú de la cuenta.
2. Vuelve a mirar las cookies.

✅ **Correcto si:** las tres han desaparecido.

---

## Punto 12 — Consola sin errores

Recorre, con DevTools abierto en la pestaña **Console**, estas pantallas:

1. Panel de inicio.
2. Lista y ficha de un presupuesto.
3. El creador de presupuestos (añade un capítulo y una partida).
4. `/cuenta` y `/equipo`.

✅ **Correcto si:** no aparece ningún mensaje en rojo que diga
**"Refused to ... because it violates the following Content Security Policy
directive"**, y todo funciona: los botones responden, los estilos se ven bien y
los desplegables abren.

> Los avisos amarillos de terceros o de deprecación no cuentan. Lo que buscamos
> son violaciones de CSP y funciones rotas.

Si ves una violación de CSP, cópiame el mensaje completo: indica exactamente qué
recurso se bloqueó.

---

## Punto 13 — Que el bucket no entregue archivos por su cuenta

Esta es la única parte del punto 13 que no puede cubrir CI, porque depende de la
configuración de tu proyecto Supabase, no del código.

### 13.1 Confirmar que el bucket es privado

1. Entra en tu proyecto de Supabase → **Storage**.
2. En la lista de buckets, mira `cotizat-private`.

✅ **Correcto si:** **no** tiene la etiqueta "Public". Si aparece como público,
detente: eso expondría todos los archivos de todos tus clientes.

### 13.2 La prueba real: pedir el archivo por la puerta de atrás

1. Sigue en **Storage** y navega hasta cualquier archivo que subiste
   (por ejemplo dentro de `organizaciones/1/anexos/`).
2. Fíjate en la ruta completa del archivo, algo como
   `organizaciones/1/anexos/planos-abc123.pdf`.
3. Construye esta URL a mano, sustituyendo `<proyecto>` por el subdominio de tu
   proyecto Supabase y la ruta por la del paso anterior:

   ```text
   https://<proyecto>.supabase.co/storage/v1/object/public/cotizat-private/organizaciones/1/anexos/planos-abc123.pdf
   ```

4. Pégala en una **ventana privada** (importante: sin tu sesión de Supabase) y
   ábrela.

✅ **Correcto si:** el navegador muestra un JSON de error parecido a
`{"statusCode":"404","error":"Bucket not found"}` o un mensaje de acceso
denegado. **No debe descargarse ni mostrarse el PDF.**

❌ **Si el archivo se abre:** el bucket está sirviendo contenido público.
Detente y avísame: es el bloqueante más serio de la lista.

### 13.3 Contraste (opcional pero recomendable)

Con la sesión de A iniciada en CotizaT, abre el mismo archivo desde la ficha del
presupuesto. Debe descargarse con normalidad. Esto demuestra lo que queremos:
el archivo **solo** se entrega pasando por CotizaT, que comprueba quién eres.

---

## Punto 14 — El arranque falla con un rol que se salta el aislamiento

Comprueba que CotizaT se niega a arrancar si alguien pone una conexión con
privilegios de más. **Es la única prueba que toca variables de producción**, así
que hazla con cuidado y al final.

1. Copia el valor actual de `DATABASE_URL` en Vercel a tu bloc de notas.
   Lo vas a restaurar en tres minutos.
2. En Vercel → tu proyecto → **Settings** → **Environment Variables**.
3. Edita **temporalmente** `DATABASE_URL` y pon la cadena de conexión del
   usuario `postgres` de Supabase (el administrador, el que aparece en
   **Project Settings → Database → Connection string**).
4. Vuelve a desplegar (**Deployments** → el último → **Redeploy**).
5. Cuando termine, abre `https://cotizat-generador.vercel.app/readyz`.

✅ **Correcto si:** responde **503** y el JSON menciona que `DATABASE_URL` debe
usar un login no privilegiado miembro de `cotizat_app`, sin SUPERUSER ni
BYPASSRLS. La aplicación se niega a servir datos: eso es exactamente lo que
queremos.

❌ **Si responde 200:** la protección no está activa. Revisa que
`COTIZAT_REQUIRE_RLS_ROLE` **no** esté puesta a `false`.

6. **Restaura `DATABASE_URL`** a su valor original (el de `cotizat_runtime`) y
   vuelve a desplegar.
7. Confirma que `https://cotizat-generador.vercel.app/readyz` vuelve a
   responder **200**.

> No dejes el paso 6 para más tarde: mientras tanto la aplicación está caída.
> Y no me envíes ninguna de esas cadenas de conexión: llevan contraseña.

---

## Cuando termines

Dime el resultado de cada punto. Con un "6 ✅, 7 ✅, 8 ✅, 9 ✅, 11 ✅, 12 ✅,
13 ✅, 14 ✅" me vale; si algo falla, cuéntame **qué punto**, **qué esperabas**
y **qué pasó**, con captura si es visual.

Con la matriz completa, el siguiente paso es fusionar el PR #11 y quitar del
README el aviso de "todavía no debe publicarse".
