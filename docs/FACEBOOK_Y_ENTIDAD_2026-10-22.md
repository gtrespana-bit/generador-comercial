# Facebook y la entidad «CotizaT»

Qué estaba asociado, qué se ha hecho en el código y qué queda en tu cuenta.

---

## Respuesta corta

**No, no estaba asociado.** El sitio no mencionaba la página de Facebook en
ninguna parte: ni un enlace en el pie, ni `sameAs` en el JSON-LD de
organización, ni la etiqueta de verificación de dominio de Meta. Para Google,
«CotizaT» de Facebook y cotizat.online eran dos cosas distintas con el mismo
nombre.

Y hay dos «asociaciones» diferentes, que se hacen en sitios diferentes:

| | Qué es | Quién puede hacerlo |
|---|---|---|
| **A. Entidad para buscadores** | Decirle a Google que la página de Facebook y el sitio son la misma marca | **Hecho en código** (esta ronda) |
| **B. Dominio verificado en Meta** | Decirle a Meta que cotizat.online es tuyo | **Solo tú**, en Business Manager |
| **C. Página ↔ dominio en Meta** | Que la página de CotizaT pueda usar el dominio para anuncios, píxel y vista previa de enlaces | **Solo tú**, tras hacer B |

Yo no puedo entrar en tu Facebook: no tengo tu sesión ni debo pedirte la
contraseña. Lo que sí puedo hacer —y he hecho— es dejar el sitio preparado
para las tres, y una de ellas la completa un token que pegas tú.

---

## A. Lo que ya está hecho en el código

### 1. `sameAs` en el JSON-LD de organización

Ahora todas las páginas declaran el perfil:

```json
{
  "@type": "Organization",
  "name": "CotizaT",
  "url": "https://cotizat.online/",
  "sameAs": ["https://www.facebook.com/profile.php?id=61593422986397"]
}
```

Es la señal que Google usa para unir cuentas con la marca. Aparece en las 234
URL del sitemap y en las 47 000 fichas del catálogo, en español y en inglés.

### 2. Enlace en el pie con `rel="me"`

En la columna de marca del pie, en las dos versiones (`_footer_publico.html`
y `_footer_publico_en.html`), con `rel="me noopener"` y `target="_blank"`.
`rel="me"` es la otra forma de declarar «esta cuenta es esta marca»; Google
usaba estos enlaces antes de generalizar `sameAs` y muchos validadores los
siguen leyendo.

### 3. Etiqueta de verificación de Meta, lista para recibir el token

`app/templates/_seo_head.html` emite:

```html
<meta name="facebook-domain-verification" content="…">
```

solo si existe la variable de entorno `COTIZAT_FACEBOOK_DOMAIN_VERIFICATION`.
No hay token escrito en el repositorio y, mientras no lo haya, la etiqueta no
aparece: el sitio no anuncia una verificación que no existe.

**Cómo se usa**: Meta te da ese token al añadir el dominio (paso B). Lo pegas
en Vercel → *Settings → Environment Variables* → `COTIZAT_FACEBOOK_DOMAIN_VERIFICATION`,
redeploy, y la etiqueta sale en todas las páginas. No hace falta que me lo
envíes: es un valor público que cualquiera puede leer en el HTML.

### 4. Una sola lista de perfiles

`app/social.py` es la fuente única: el `sameAs`, el pie y la verificación salen
de ahí. Cuando añadas Instagram, YouTube o LinkedIn, se añaden a `PERFILES` y
aparecen en los tres sitios a la vez.

---

## B y C. Los pasos que solo puedes dar tú

**B. Verificar el dominio en Meta** (5 minutos, gratis):

1. [business.facebook.com](https://business.facebook.com) → **Configuración
   del negocio** → **Seguridad de la marca** → **Dominios**.
2. **Añadir** → `cotizat.online`.
3. Elige **Meta-etiqueta**. Te dará un token como
   `abc123…`. Pégalo en Vercel como `COTIZAT_FACEBOOK_DOMAIN_VERIFICATION` y
   redespliega.
4. Vuelve a Meta y pulsa **Verificar**. Tarda segundos.

**C. Asociar la página al dominio**: en **Configuración del negocio** →
**Cuentas** → **Páginas**, la página de CotizaT debe estar dentro del mismo
portfolio (Business Manager) que el dominio. Con los dos en el mismo portfolio
quedan asociados; en la ficha del dominio verás la página como «activo
asociado».

> Nota: si la página está hoy creada en un perfil personal y no en un
> portfolio, hay que **añadirla al portfolio** (Páginas → Añadir → Reclamar o
> solicitar acceso). Es el único camino; Meta no permite asociar un dominio a
> una página que vive fuera del portfolio.

---

## ¿Mejora algo? Con honestidad

**Sí, pero no como factor de posicionamiento.**

- **Lo que sí**: consolida la entidad. Cuando alguien busca «CotizaT», Google
  tiene una sola entidad que unir (sitio + página + correo + logo) en vez de
  dos candidatas con el mismo nombre. Eso ayuda al panel de marca, a que las
  redes sociales salgan enlazadas en el resultado y a que un perfil homónimo
  no se quede el nombre.
- **Lo que sí, en Meta**: el dominio verificado desbloquea lo que Meta exige
  tener verificado para anuncios y píxel (si algún día los usas) y evita que
  la vista previa de cotizat.online aparezca como «dominio no verificado».
- **Lo que no**: enlaces sociales no suben posiciones. Un `sameAs` no cambia
  el ranking de «software de presupuestos Colombia». Para eso sigue mandando
  lo que ya está en marcha (catálogo, comparador, hubs, enlazado interno).
- **Y lo que empeora si se hace mal**: no publiques el perfil en el pie si la
  página está vacía o sin publicaciones. Un perfil abandonado enlazado desde
  el sitio resta más confianza de la que aporta. Si aún no tiene contenido,
  publícalo primero y luego añade el enlace (basta con vaciar `PERFILES` en
  `app/social.py` y el sitio deja de enlazarlo sin tocar plantillas).

---

## Pruebas

`tests/test_entidad_social.py` (20): el `sameAs` en todas las plantillas que
emiten la organización, el `rel="me"` del pie en los dos idiomas, la etiqueta
de verificación con y sin token, y que la lista de perfiles tenga una sola
fuente.

Suite completa: **2 874 pasan, 13 omitidas** (5:37).
