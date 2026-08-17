# Identidad visual, usabilidad y rendimiento del frontend (pasada 2026-08)

Fecha: **16/08/2026** · Suite: **470 passed, 6 skipped** · Sin migración nueva
(el head al cerrar ese bloque era `a3d7e9c1b5f2`; este bloque no cambió esquema).

> Estado actual: el head es `d6e2f9c4b8a1`. El rendimiento del catálogo fue
> ampliado después para 5.000 partidas; ver `docs/FASE_1_CATALOGO_ESCALABLE.md`.

Esta pasada resuelve los fallos de CI que bloqueaban el despliegue de Vercel,
unifica la identidad visual de toda la superficie (pública y autenticada) y
ataca el rendimiento del frontend —sobre todo la página de Partidas, que con
540 partidas llegaba a los ~5 MB de HTML— sin cambiar el modelo de datos ni el
comportamiento de negocio.

---

## 1. Qué se hizo y por qué

| Bloque | Archivos clave | Impacto |
|---|---|---|
| **CI en verde** | `templates/index.html`, `js/editor/spotlight.js`, `js/editor/arbol_catalogo.js`, `js/editor/totales.js` | Tres regresiones de seguridad/marca que hacían fallar `pytest` en GitHub Actions y bloqueaban el merge. |
| **Identidad unificada** | `css/public.css` (nuevo), `css/style.css`, `css/csp.css`, 14 plantillas públicas/auth | El producto tenía tres identidades compitiendo (logo/PDF en azul marino, shell en índigo, login/landing en verde). Todo queda en **azul marino + oro** (la marca real). |
| **Rendimiento de red** | `main.py` (gzip, caché), `security.py` (CSP) | Partidas pasa de ~5,3 MB a ~240 KB por gzip. Estáticos con caché de CDN e inmutable por versión. |
| **Rendimiento de la página de Partidas** | `templates/partidas/list.html`, `js/partidas_descomp.js` (nuevo), `css/style.css` | Categorías colapsadas, descomposición bajo demanda y revelación progresiva. |
| **Fuentes self-hosted** | `css/fonts.css` (nuevo), `fonts/Inter-*.woff2` (nuevos) | Adiós a Google Fonts; la tipografía carga del mismo origen. |

---

## 2. Correción de CI (3 tests en rojo)

1. `test_inicio_renderiza_marca_y_propuesta_honesta` — el botón del dashboard
   decía «Sugerir»; ahora «Sugerir desde catálogo».
2. `test_frontend_no_usa_sinks_html_de_inyeccion` — se eliminaron los
   `innerHTML` y los accesos directos a `.style` de tres módulos nuevos,
   reescribiéndolos con `createElement`/`textContent` y `CotizatStyles.set`.
3. `test_acciones_declarativas_tienen_handler_registrado` — se registró la
   acción declarativa `open-spotlight` que usaba el buscador sin handler.

## 3. Identidad visual unificada (azul marino + oro)

La aplicación tenía **tres identidades en paralelo**: el logo y el PDF en azul
marino, el onboarding en marino+oro, el shell en índigo (`#6366f1`, copia de
Linear/Notion) y login/landing/legales en un verde bosque viejo con CSS
duplicado por página. Se consolidó todo sobre la marca real:

- Nuevo `public.css` compartido para login, registro, recuperación,
  invitaciones, landing, legales, propuesta pública, organizaciones y equipo.
- Migración de tokens de `style.css` y `csp.css` de índigo a marino+oro.
- Logomarca real (documento + check dorado) en barra lateral y superficies
  públicas, en lugar del icono genérico de tres rayas.
- Login a pantalla partida; landing y propuesta pública rediseñadas.

## 4. Rendimiento de red

- **Compresión gzip** (`GZipMiddleware`): HTML/CSS/JS/JSON. Excluye PDF y
  Office, que ya están comprimidos.
- **Caché de estáticos**: los navegadores revalidan por ETag
  (`max-age=0, must-revalidate`); la CDN de Vercel cachea hasta un año
  (`s-maxage` + `stale-while-revalidate`).
- **Assets inmutables por versión** (filtro `asset` + `?v=<commit>`): cambiar
  un CSS/JS en un despliegue cambia su URL; el navegador deja de revalidar.
- **Lazy-loading** de imágenes en listas (`loading="lazy" decoding="async"`).

## 5. Página de Partidas

- **Categorías colapsadas por defecto**: solo cabeceras con contador. Al
  pulsar una categoría/subcategoría (o buscar) se expande lo necesario.
- **Descomposición bajo demanda**: las ~540 tablas de recursos ya no se emiten
  en el HTML; se piden vía `GET /partidas/{id}/descomposicion` al desplegar,
  con skeleton de carga y construcción de DOM segura.
- **Revelación progresiva**: secciones >80 partidas muestran un primer tramo
  con «Mostrar N más»; sin límite al buscar.
- **Dashboard en una pasada**: una sola lectura del histórico en lugar de ~10
  consultas completas a `presupuestos`.

## 6. Fuentes self-hosted

Inter se sirve desde `/static/fonts` (`.woff2` + `OFL-Inter.txt`), obtenida de
`github.com/rsms/inter`. La CSP dejó de autorizar `fonts.googleapis.com` /
`fonts.gstatic.com`.

## 7. Errores corregidos durante la pasada

- **Cuelgue del filtro**: la primera pasada de filtrado hacía un `insertRule`
  por nodo (miles) y un `getComputedStyle` por fila; se corrigió en
  `csp_styles.js` y `partidas/list.html`.
- **Anidamiento de secciones (causa raíz del filtrado roto)**: el template de
  Partidas abría `<section class="cat-section">` por categoría pero **nunca lo
  cerraba** (no existía ningún `</section>` desde el origen). El navegador
  anidaba todas las categorías, dejando la ventana en blanco al filtrar. Se
  añadió el cierre que faltaba.

---

**Criterio de aceptación**: `pytest -q` en verde (470 passed, 6 skipped) y
`python tools/verificar_plantillas.py` sin errores.
