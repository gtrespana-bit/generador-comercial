# Análisis de patrones de nombres — Catálogo de Partidas (3.006 partidas)

**Fecha:** 2026-08-21  
**Solicitado por:** revisión de Colombia — `Revestimientos pared / Enchape` vs `Alicatado`

## Resumen ejecutivo

> Si busco **“enchape”** deberían salir **todos** los enchapes. Hoy salía `Enchape de porcelanato en gran formato` pero no `Alicatado en paramento interior`, aunque es la **misma partida** (revestimiento cerámico en pared en capa fina). El buscador ya expande sinónimos, pero el patrón visual también debe ser único.

**Causa raíz:** 1 partida en `12.03.01 Cerámica y porcelanato en paredes` usaba término peninsular **Alicatado**, mientras las otras 17 del mismo apartado usan **Enchapado** (VE) / **Enchape** (CO). El diccionario de sinónimos `sinonimos_busqueda.json` no incluía `enchape` como alias de `enchapado`, así que `enchape` no encontraba `enchapado` ni `alicatado`.

**Fix aplicado:** 7 renombres + 1 sinónimo + 1 recurso + normalizador en BD para instalaciones existentes.

---

## 1. Inventario por niveles

| Nivel | Ej. Colombia | Total |
|-------|--------------|-------|
| Capítulo | `12 Revestimientos y acabados` | 18 |
| Subcapítulo | `12.05 Pisos, pavimentos y sus bases` | 172 |
| Apartado | `12.05.01 Bases, afirmados y nivelación` | ~380 |
| Partida | `12.03.01.010 Enchapado de paramento interior...` | 3.006 |

La página `/partidas` ya fue corregida en el commit anterior para agrupar **capítulo → subcapítulo → apartado**. Es general, no solo para 12.05.

## 2. Caso reportado — detalle

**Ubicación:** `12.03.01 Cerámica y porcelanato en paredes` (18 partidas)

```
12.03.01.010  Alicatado de paramento interior con pieza cerámica...  ⚠️ OUTLIER (1)
12.03.01.020  Enchapado de porcelanato de gran formato en pared.    ✓
12.03.01.030  Enchapado cerámico en fachada...                      ✓
12.03.01.040  Cenefa o listelo decorativo en enchapado.             (accesorio)
12.03.01.050  Perfil de remate...                                   (accesorio)
12.03.01.060  Enchapado de zona de ducha...                         ✓
12.03.01.070  Zócalo cerámico de pared.                              ⚠️ → Rodapié
...
12.03.01.130  Revestimiento de frente de bañera...                  ⚠️ → Enchapado
12.03.01.160  Revestimiento de columna...                            ⚠️ → Enchapado
```

**Por qué no se encontraban:**

* `sinonimos_busqueda.json` grupo `enchapado: [alicatado, revestimiento de pared, chapado]` → buscar `alicatado` encuentra `enchapado`, pero buscar `enchape` (CO) no expandía a nada → `%enchape%` no matchea `%enchapado%`.
* `glosarios/CO.json` traduce `enchapado → enchape`, pero el título seguía siendo `Alicatado`, que no tiene traducción → queda huérfano en CO.
* Visualmente el usuario ve dos nombres distintos para lo mismo.

## 3. Otros patrones detectados (no bloqueantes, pero unificados)

| Apartado | Antes (inconsistente) | Ahora (patrón) | Motivo |
|----------|----------------------|----------------|--------|
| 12.03.01 | `Zócalo cerámico de pared.` | `Rodapié cerámico de pared.` | `zócalo` es matizado: en VE `rodapié` es la moldura del piso; `zócalo` es base de cúpula. CO `guardaescoba`. |
| 12.03.02 | `Zócalo de piedra natural.` | `Rodapié de piedra natural.` | mismo |
| 12.03.01 | `Revestimiento de frente de bañera...` | `Enchapado de frente de bañera...` | `Revestimiento` genérico no es encontrable por `enchape` (alias es `revestimiento de pared`, no `revestimiento` solo) |
| 12.03.01 | `Revestimiento de columna...` | `Enchapado de columna...` | mismo |
| 12.05.03 | `Colocación de piso cerámico...` (2) | `Piso cerámico...` | verbo redundante, otros 6 del mismo apartado ya usan `Piso...` |
| Recursos | `Oficial de 1ª alicatador.` | `Oficial de 1ª enchapador.` | oficio |

Los accesorios `Cenefa`, `Perfil`, `Salpicadero` se mantienen con su nombre propio (no son el paño de campo).

## 4. Patrón impuesto

**Regla:** `<Enchapado de> + <material> + <ubicación> + <, en capa fina/junta mínima>` para todo paño de pared con cerámica/porcelanato.  
**Ejemplos canónicos (VE base → CO translation):**

* VE: `Enchapado de paramento interior con pieza cerámica o porcelanato, en capa fina.` → CO: `Enchape de paramento interior con pieza cerámica o porcelanato, en capa fina.`
* VE: `Enchapado de porcelanato de gran formato en pared.` → CO: `Enchape de porcelanato...`
* VE: `Piso cerámico o porcelanato de formato estándar, en capa fina.` (igual en CO, `piso` es `piso` en ambos)

Buscar `enchape`, `enchapado`, `alicatado`, `chapado` o `revestimiento de pared` ahora devuelve el mismo set (sinónimos bidireccionales, `capitulos: ["12"]`).

## 5. Cambios técnicos

**Ficheros JSON fuente (VE):**
* `datos/descompuestos/12.03.01.010.json` — título/descripción `Alicatado → Enchapado`
* `12.03.01.130.json`, `12.03.01.160.json` — `Revestimiento → Enchapado`
* `12.03.01.070.json`, `12.03.02.040.json` — `Zócalo → Rodapié`
* `12.05.03.010.json`, `12.05.03.020.json` — `Colocación de piso → Piso`
* `datos/recursos.json` — `MO-OF1-ALI` `Oficial alicatador → enchapador.`

**Diccionarios:**
* `datos/sinonimos_busqueda.json` grupo `enchapado` añade `"enchape"` → `["alicatado","revestimiento de pared","chapado","enchape"]`
* `datos/glosario.json` — nuevo cambio `alicatado → enchapado` y `_prohibidos: alicatado`

**Migración en BD (instalaciones existentes):**
* `app/services/catalogo_propio.py` — `_RENOMBRADOS_PATRON` + `_normalizar_nombres_patron(db)` llamado en cada `asegurar_catalogo_propio()` (idempotente, solo UPDATE donde `nombre == viejo`). También corrige descripción y recurso. Log: `Normalizados X nombres de patrón...`

**Verificación:**
```
$ python3 basedatos_partidas/terminologia.py auditar
Sin términos peninsulares.
$ variantes_consulta("enchape")
[['enchape','enchapado','alicatado','revestimiento de pared','chapado']]
# en CO, buscar "enchape" ahora encuentra los 18 de 12.03.01
```

## 6. Cómo queda el buscador

* **VE** escribe `enchape` o `enchapado` → encuentra los 18 de 12.03.01 (incluido el antiguo alicatado)
* **CO** escribe `enchape` → encuentra los mismos 18 (porque VE `Enchapado` se traduce a `Enchape` al vuelo + sinónimo)
* **Cualquier país** `piso`, `suelo`, `solado`, `pavimento` → mismo set (grupo `piso`)
* `friso`, `pañete`, `revoque`, `repello` → mismo set (grupo `friso`)

El patrón visual + el diccionario hacen que el buscador sea rápido sin tener que recordar si era `alicatado` o `enchape`.

---

**Próximos pasos opcionales (no aplicados para no sobre-normalizar):** Unificar `Salpicadero de cocina` → `Enchapado de salpicadero...` y `Cenefa/Perfil` si se quiere que también sean encontrables por `enchape`. Se dejó como está porque son accesorios con nombre propio.
