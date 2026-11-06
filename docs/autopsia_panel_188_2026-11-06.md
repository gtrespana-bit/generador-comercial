# Autopsia del apagón del panel (PR #188 / #189)

**Fecha:** 06/11/2026
**Alcance:** por qué el despliegue de #188 dejó la web entera inaccesible, y qué
hay que arreglar para poder recuperar ese trabajo sin repetirlo.

## Resumen en una línea

Un **`NameError` de una sola línea** en el nivel de módulo impedía importar
`app.panel_arquitectura`, y con él `app.main`: la aplicación no arrancaba, así
que **todas** las rutas devolvían 500 —no solo el panel—. Ese mismo `NameError`
rompía `tests/conftest.py`, de modo que **la suite completa no llegaba a
ejecutarse** y el defecto era invisible en CI.

## Cómo se recuperó el código

`main` quedó retrocedido a `f6ecb4a` (merge de #187). Los commits de #188 y
#189 siguen vivos en GitHub aunque sus merges no estén en la historia de `main`:

```bash
git fetch origin refs/pull/188/head:refs/tmp/pr188 refs/pull/189/head:refs/tmp/pr189
git worktree add --detach /tmp/autopsia188 refs/tmp/pr188
```

| ref | commit | contenido |
|---|---|---|
| `refs/tmp/pr188` | `d78af0b5` | 4 commits: dashboard de alertas · RBAC real por roles · timeline de cliente · productividad del operador (+1368 líneas, 14 ficheros) |
| `refs/tmp/pr189` | `df269250` | fix del `NameError lic_por_org` en `resumen_financiero` (+5 líneas) |

#189 **no es opcional**: sin él, `resumen_financiero` revienta y con él
`/admin`, `/admin/licencias`, `/admin/cobros` y `/admin/analitica`.

## Causa del apagón (confirmada)

`app/panel_arquitectura.py:78`, en el código de #188:

```python
ROLES_TODOS = ROLES_OPERADOR     # ROLES_OPERADOR nunca se importa
```

Cadena exacta de la caída:

```
import app.main
  app/main.py:55            from .routers import (...)
    app/routers/admin.py:10 from ..panel_arquitectura import es_destino_panel
      app/panel_arquitectura.py:78  ROLES_TODOS = ROLES_OPERADOR
NameError: name 'ROLES_OPERADOR' is not defined
```

Y el efecto dominó en las pruebas:

```
ImportError while loading conftest '/tmp/autopsia188/tests/conftest.py'
tests/conftest.py:62: from app.main import app
E   NameError: name 'ROLES_OPERADOR' is not defined
```

**Por eso "revertir" no arreglaba nada**: el commit con el que se intentó volver
a #187 (`8ea5068e`) estaba **vacío**, no revertía ni un fichero.

Con una sola línea añadida (`from .models import ROLES_OPERADOR`) la aplicación
arranca y los 162 módulos de `app/` importan (162 passed).

## Qué queda cuando el `NameError` se corrige

Con el import + el fix de #189, sobre el árbol de #188: **23 fallos**, que se
clasifican en cuatro grupos. La distinción importa porque solo el grupo D es
trabajo real del rediseño.

### A. Consecuencia del apagón — 1 línea

El `NameError` de arriba. Es todo lo que hacía falta para tumbar la web.

### B. Falta #189 — 5 líneas

`NameError: name 'lic_por_org' is not defined` en `resumen_financiero`:
afecta a `/admin`, `/admin/licencias`, `/admin/avisos`, `/admin/analitica`,
`/admin/cobros`. Ya está escrito en `df269250`; hay que llevarlo junto a #188.

### C. Pisotón con el `main` actual — se cura rebasando, no parcheando

Son cosas que #190–#192 ya arreglaron **después** de #188, y que existen en el
árbol de #188 porque nació de #187:

| síntoma en el árbol de #188 | dónde se arregló ya |
|---|---|
| `TypeError: do_max() got an unexpected keyword argument 'list'` (`app/templates/admin/analitica.html:454`) | #190 (`.note-sub`, `max(...)`/`[0]`) |
| `test_web_security`: `style=` inline en `admin/analitica.html` | #190 |
| cabeza Alembic `v2d7f1a6b9c3` vs. `x9m2k4p8v1n6`; `visitas_pagina` sin GRANT; `VisitaPagina` sin excepción de tenancy | #190/#191 |
| `DATOS_EFIMEROS` en `test_arranque_en_sistema_de_solo_lectura[sqlite]` | posterior |

**Conclusión:** el trabajo de #188 **no se puede reaplicar como diff ni como
cherry-pick a ciegas**; hay que **rebasarlo sobre `main`**. Si se fusionara el
árbol antiguo, volveríamos a romper `analitica.html`, la cadena de migraciones y
la política CSP.

### D. Defectos reales de #188 (los que hay que decidir, no solo arreglar)

1. **RBAC nuevo vs. llamadas antiguas.** `_rol_permite(None, …)` devuelve
   `False` por diseño («sesión no operadora, nunca se permite»), pero varias
   pruebas y llamadas internas siguen invocando `nav_panel()`,
   `pestanas_de()` y `pestana_valida()` **sin rol**:
   - `nav_panel()` → `[]` → sidebar vacío (`test_el_panel_tiene_seis_entradas_como_maximo`).
   - `pestana_valida("clientes", …)` → `''` (`test_las_pestanas_de_la_ficha_no_dependen_del_area`).
   - Y el caso peligroso: `''` acaba en un nombre de plantilla
     → `TemplateNotFound: 'admin/partes/ficha_.html'`. Es un **500 real**
     si alguna vista llega sin rol.
   Los call sites de producción sí pasan `rol=rol_operador`
   (`panel_contextos.py:334`, `admin_paginas.py:334,801,823,…`), así que hoy no
   rompe; el arreglo correcto es que el **valor por omisión sea explícito**
   (o `None` = todos, coherente con el resto) y que las pruebas digan el rol.
2. **Auditoría sin etiqueta:** `admin.vista_favorita` se emite
   (`app/routers/admin.py:1600`) pero no está en `ACCIONES_LECIBLES`
   (`app/services/audit_admin.py:30`) → no se puede filtrar y se lee un código
   suelto. Una línea.
3. **`KeyError: 'clientes'`** en la pantalla de listas (`tests/test_panel_listas.py:228`).
4. **`IndexError: list index out of range`** en los contadores del menú
   (`tests/test_panel_arquitectura.py:955`).
5. **Clasificación de actividad:** una empresa que solo inicia sesión se
   etiqueta `'semana'` donde la prueba espera `'hoy'`
   (`tests/test_panel_analitica.py:324`). Métrica falsa, no caída.
6. **Regresión funcional del dashboard:** `'Clientes por vencer'` ya no aparece
   en `/admin` (`tests/test_licencias.py:605`) — el rediseño de la agenda se
   llevó por delante el bloque de vencimientos.
7. **RBAC demasiado estricto en tests de licencias** (5 ×
   `GestionEquipoError: Se requiere el rol admin, superadmin`): hay que decidir
   si soporte y analista deben poder conceder pruebas/activar compras. Es una
   **decisión de producto**, no un bug: si el RBAC es el correcto, se actualizan
   las pruebas; si no, se ajusta la matriz de permisos.

## Lo que hay que hacer antes de reintentar la restauración

1. **Red de seguridad** (el hueco que permitió esto): una prueba que arranque
   `app.main` en un subproceso limpio y pida `/healthz`, y un humo que recorra
   **todas** las páginas del panel con sesión de operador y datos sembrados
   exigiendo `< 500`. `tests/test_importacion_modulos.py` ya cubre el caso de
   este apagón (162 módulos), pero solo si la suite puede arrancar.
2. **Rebasar #188 sobre `main`** (no reaplicar el diff), resolviendo los
   conflictos por grupos: C se descarta (lo de `main` manda), D se arregla.
3. **Reordenar la migración:** `x9m2k4p8v1n6` debe colgar de
   `w3m9k2p8v1n4`, no de `v2d7f1a6b9c3`, y `EXPECTED_ALEMBIC_HEAD` pasa a
   `x9m2k4p8v1n6` solo cuando la migración esté aplicada en producción.
4. **Entregar en tramos pequeños** (un PR por punto del rediseño) con preview
   revisada, en lugar de 1368 líneas de golpe.

## Cómo reproducir esta autopsia

```bash
git fetch origin refs/pull/188/head:refs/tmp/pr188 refs/pull/189/head:refs/tmp/pr189
git worktree add --detach /tmp/autopsia188 refs/tmp/pr188
cd /tmp/autopsia188

.venv/bin/python -c "import app.main"   # NameError: ROLES_OPERADOR
.venv/bin/python -m pytest -q           # la suite no colecciona siquiera

# añade `from .models import ROLES_OPERADOR` en app/panel_arquitectura.py y:
.venv/bin/python -c "import app.main"   # IMPORT OK
.venv/bin/python -m pytest -q           # 3314 passed, 35 failed, 14 skipped

# aplica también el fix de #189:
git cherry-pick df269250
.venv/bin/python -m pytest -q \
    tests/test_avisos_y_soporte.py tests/test_compras_plan.py \
    tests/test_licencias.py tests/test_licencias_acceso.py \
    tests/test_panel_actividad_y_accesos.py tests/test_panel_analitica.py \
    tests/test_panel_arquitectura.py tests/test_panel_listas.py \
    tests/test_panel_pro_fase1.py       # 233 passed, 23 failed → grupos C y D
```
