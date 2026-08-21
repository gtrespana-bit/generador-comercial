# Corrección — Clasificación por apartados y unificación de patrones (2026-08-21)

**Rama:** `arena/01a02516-generador-comercial` → merge a `main`  
**Autor:** Agent Arena  
**Issues:** 1) “Todas las partidas en Pisos, pavimentos y sus bases aparecen en un solo bloque aunque existen apartados 01 Bases, 03 Pisos cerámicos…” 2) “Enchapado vs Alicatado no siguen patrón y rompe el buscador en Colombia”

---

## 1. Problema 1 — Falta de desglose por apartado

### Síntoma
Catálogo con 3 niveles reales en `basedatos_partidas/datos/clasificacion.json`:

```
12 Revestimientos y acabados (capítulo)
 └─ 12.05 Pisos, pavimentos y sus bases (subcapítulo)
     ├─ 12.05.01 Bases, afirmados y nivelación (apartado) — 8 partidas
     ├─ 12.05.03 Pisos cerámicos y porcelanato — 8 partidas
     ├─ 12.05.04 Pisos de piedra, granito y terrazo — 7 partidas
     └─ ...
```

La página `/partidas` solo agrupaba por `categoria` (capítulo) y `subcategoria` (subcapítulo). Al entrar en **12.05** se veían 38 filas mezcladas sin encabezados de apartado.

El bug era **general**, no solo para `12.05`. Afecta a los 18 capítulos, 172 subcapítulos y ~380 apartados (ej. `02.10 Revestimientos, pisos y cielos rasos → 02.10.01/02/03`, `06.01 Fachadas de bloque → 06.01.01/02/03`, etc.).

### Solución — 4 ficheros, 260 líneas

**`app/routers/partidas.py`:**
- Nuevo query param `apartado` (`?categoria=12%20Revestimientos...&subcategoria=12.05...&apartado=12.05.01...`). `modo_directo` incluye `apartado`. Filtro `Partida.apartado == apartado`.
- Árbol lateral: de 2 a 3 niveles. `apartados_por_padre` (nivel 3), `conteo_apartados` y ` _por_sub` para apartados personalizados. Cada `subcapitulo` ahora lleva `apartados: [{apartado, codigo, nombre, total}]` ordenados por código.
- Traducción y conversión de moneda también para `apartado_display`.
- Expone `apartado_actual` a la plantilla.

**`app/templates/partidas/list.html`:**
- Sidebar: `apartado-list` anidado bajo cada `subcat-btn`, con `apartado-btn` activo y `?apartado=` en el href. Solo muestra apartados con `total>0` para no saturar.
- Vista directa (búsqueda o filtro): pasa de `capítulo → subcapítulo → tabla` a `capítulo → subcapítulo → apartado-section` colapsable; cada apartado tiene su tabla y badge.
- Vista navegación lazy: `subcat-body` sigue cargando vía `fetch`, pero el contenedor espera grupos de apartado.
- Paginación conserva `&apartado=`. Help text actualizado. Nuevo handler `partidas-toggle-apartado`.

**`app/static/js/partidas_rows.js`:**
- `agruparPorApartado()` ordena por código (`12.05.01` < `12.05.03`, `Sin apartado` al final). `render()` crea `apartado-section` con `apartado-head` + `apartado-body` + tabla propia. Si solo hay `Sin apartado`, renderiza tabla única sin encabezado redundante. Cumple CSP (sin `.style`, usa clase `subcat-placeholder`).

**`app/static/css/style.css`:**
- Estilos para `.apartado-list/.apartado-btn`, `.apartado-section/.apartado-head/.apartado-toggle/.apartado-count-badge`.

### Cómo probar
1. Abrir `/partidas` → verificar sidebar muestra 18 capítulos contraídos.
2. Expandir `12 Revestimientos y acabados → 12.05 Pisos...` → aparecen 6 apartados con conteos (8,8,7,7,7,9).
3. Clic en `12.05` → vista directa agrupa por apartado con encabezados `12.05.01 Bases...` etc.
4. Clic en `12.05.01` → solo 8 partidas de bases.
5. Expandir cualquier otro capítulo (ej. `02 Demoliciones → 02.10`) → mismo desglose.

Tests: `866 passed, 0 failed` (`verificar_plantillas` OK, `test_frontend_no_usa_sinks...` OK tras quitar `.style`).

---

## 2. Problema 2 — Patrón de nombres y buscador (Colombia: enchape vs alicatado)

### Síntoma
En `12.03.01 Cerámica y porcelanato en paredes` (18 partidas) había:

```
Alicatado de paramento interior...  (1, peninsular)
Enchapado de porcelanato...         (17, VE) / Enchape (CO)
```

Buscar `enchape` (CO) no encontraba `Alicatado` ni `Enchapado de porcelanato` porque `sinonimos_busqueda.json` tenía `enchapado: [alicatado, revestimiento de pared, chapado]` pero **no incluía `enchape`**, y `alicatado` no estaba en `glosario.json _prohibidos`. Visualmente dos nombres distintos para lo mismo.

### Auditoría 3.006 partidas
- `terminologia.py auditar` → `Sin términos peninsulares` (pero `alicatado` no estaba listado) + matizados `pavimento×59`, `zócalo×37`.
- `variantes_consulta("enchape") = [['enchape']]` sin expansión.
- Primeras palabras por apartado mostraron outliers: `Alicatado` (1), `Zócalo` (2), `Revestimiento` (2), `Colocación de piso` (2), `Salpicadero` (1), `Alfombra` (1).

### Solución — 9 renombres + sinónimos + normalizador de BD

**JSON fuente (VE base):**
- `12.03.01.010.json` `Alicatado → Enchapado` (título y descripción)
- `12.03.01.130.json` `Revestimiento de frente de bañera... → Enchapado de frente de bañera con pieza cerámica, en capa fina.`
- `12.03.01.160.json` `Revestimiento de columna... → Enchapado de columna...`
- `12.03.01.070.json` `Zócalo cerámico de pared. → Rodapié cerámico de pared.` (VE `rodapié`, CO `guardaescoba`)
- `12.03.02.040.json` `Zócalo de piedra natural. → Rodapié de piedra natural.`
- `12.05.03.010.json` `Colocación de piso cerámico... → Piso cerámico...`
- `12.05.03.020.json` `Colocación de piso de porcelanato... → Piso de porcelanato...`
- `12.03.01.110.json` `Salpicadero de cocina... → Enchapado de salpicadero de cocina...` (unificado a petición)
- `12.05.06.040.json` `Alfombra o moqueta. → Piso de alfombra o moqueta, encolado o tensado.`
- `datos/recursos.json` `MO-OF1-ALI` `Oficial alicatador. → enchapador.`

**Diccionarios:**
- `datos/sinonimos_busqueda.json` grupo `enchapado` añade `enchape` → `["alicatado","revestimiento de pared","chapado","enchape"]`; grupo `piso` añade `alfombra, moqueta` → `["suelo","pavimento","solado","revestimiento de piso","alfombra","moqueta"]`
- `datos/glosario.json` nuevo cambio `alicatado → enchapado` y `_prohibidos: alicatado`

**Migración de BD existente:**
- `app/services/catalogo_propio.py` añade `_RENOMBRADOS_PATRON` (9 entradas) y `_normalizar_nombres_patron(db)` idempotente, llamado en cada `asegurar_catalogo_propio()` antes de la lógica de versionado. Actualiza `Partida.nombre/descripcion` y `Recurso.descripcion` donde `nombre == viejo` y hace `commit` solo si hay cambios. Log: `Normalizados X nombres...`.

**Patrón impuesto:**
> `<Enchapado de> + <material> + <ubicación> + <, en capa fina>` para todo paño de pared cerámico. Ej. `Enchapado de paramento interior con pieza cerámica o porcelanato, en capa fina.` (VE) → `Enchape de ...` (CO vía `glosarios/CO.json: enchapado→enchape`).  
> `<Piso de> + <material> + <, en capa fina>` para todo piso. Buscar `enchape`, `enchapado`, `alicatado`, `chapado` → mismo set; `piso`, `suelo`, `solado`, `alfombra` → mismo set.

**Verificación:**
```
$ python3 basedatos_partidas/terminologia.py auditar
Sin términos peninsulares.
$ python -c "from app.services.busqueda_catalogo import variantes_consulta; print(variantes_consulta('enchape'))"
[['enchape','enchapado','alicatado','revestimiento de pared','chapado']]
```

Detalles completos en `ANALISIS_PATRONES_PARTIDAS.md` (3.006 partidas, 256 apartados con partidas, 17/18 vs 1, etc.).

---

## 3. Qué queda pendiente (intencionalmente)

* `Cenefa o listelo decorativo en enchapado.` y `Perfil de remate... en enchapado.` ya contienen `en enchapado`, son encontrables por `enchape` vía alias, se dejaron con nombre propio por ser accesorios.
* `Zócalo` restante (33 ocurrencias matizadas) son usos correctos (base de cúpula, junta sísmica) — se mantienen como aviso, no error.
* No se bumpió `CATALOGO_VERSION` (3) porque el normalizador de nombres ya corrige instalaciones existentes sin migración pesada. Próxima feature que toque títulos puede subir a 4.

---

## 4. Commits en esta rama

1. `98ff7ca fix(partidas): organizar por apartado dentro de subcapitulo` — 4 ficheros, 260 líneas
2. `455786a fix(patron): unificar nombres Enchapado/Alicatado y Piso/Colocación para buscador` — 12 ficheros (7 JSON + sinonimos + glosario + recursos + normalizador + doc)
3. `5224756 fix(patron): unificar Salpicadero y Alfombra al patrón Enchapado/Piso` — 4 ficheros

Todos con `pytest 867 passed, 7 skipped` y `verificar_plantillas 86 OK`.

**Merge a `main` listo.** Después del merge esta sesión `arena/01a02516-*` queda sin acceso por diseño de Arena.
