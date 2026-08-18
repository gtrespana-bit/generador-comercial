# Integración continua (E1-038)

`ci.yml` de esta carpeta es la **definición versionada** del flujo de
integración continua. GitHub Actions solo ejecuta el archivo situado en
`.github/workflows/ci.yml`, así que ambos deben ser idénticos.

## Por qué está duplicado

El token de la aplicación que abre los cambios automáticos en este repositorio
no tiene el permiso `workflows`, necesario para crear o modificar archivos bajo
`.github/workflows/`. GitHub rechaza el push con:

```text
refusing to allow a GitHub App to create or update workflow
`.github/workflows/ci.yml` without `workflows` permission
```

Mantener aquí la definición permite versionarla, revisarla y protegerla con
pruebas aunque el archivo activo deba instalarse manualmente una sola vez.

## Activación (una sola vez)

Desde un clon local con permisos normales de escritura:

```bash
mkdir -p .github/workflows
cp docs/ci/ci.yml .github/workflows/ci.yml
git add .github/workflows/ci.yml
git commit -m "ci: activa el flujo de integración continua"
git push
```

También puede crearse desde la interfaz web de GitHub
(**Actions → New workflow → set up a workflow yourself**) pegando el contenido
de `docs/ci/ci.yml`.

A partir de ese momento cada pull request ejecuta el flujo automáticamente.

## Qué verifica

| Paso | Motivo |
|---|---|
| Instalación de `requirements.lock` | Probar siempre el mismo conjunto exacto de paquetes. |
| `tools/verificar_lock.py` | Evitar que Vercel y CI instalen versiones distintas. |
| `compileall` | Detectar errores de sintaxis en Python. |
| `tools/verificar_plantillas.py` | Parsear las 40 plantillas con el entorno Jinja real. |
| `node --check` | Detectar errores de sintaxis en los 20 archivos JavaScript. |
| `git diff --check` | Marcar conflictos y espacios sobrantes, solo en las líneas del cambio. |
| `tools/simular_vercel_rofs.py` | Reproducir el sistema de archivos de solo lectura de Vercel, que ya provocó incidencias de arranque. |
| `pytest -q` | Ejecutar la suite completa. |

## Mantenimiento

Al cambiar el flujo, edita `docs/ci/ci.yml` y copia el resultado sobre
`.github/workflows/ci.yml`. La prueba
`test_el_flujo_activo_coincide_con_la_definicion_versionada`
(`tests/test_integracion_continua.py`) vigila que ambas copias no se separen.

**Desfase esperado en PRs del bot:** como el token no puede tocar
`.github/workflows/ci.yml`, un PR que actualice `docs/ci/ci.yml` deja la copia
activa desfasada a propósito. La prueba lo detecta y, si el PR no tocó la copia
activa (idéntica a `origin/main`), lo reporta con `skip` (no rompe CI) con el
comando exacto para sincronizar. **Tras fusionar un PR que toque `docs/ci/ci.yml`,
el titular debe ejecutar:**

```bash
cp docs/ci/ci.yml .github/workflows/ci.yml
git add .github/workflows/ci.yml
git commit -m "ci: sincroniza la copia activa con docs/ci/ci.yml"
git push
```

o editar el archivo desde la interfaz web de GitHub y hacer commit. Hasta que
se sincronice, el flujo activo es el anterior (los pasos nuevos de
`docs/ci/ci.yml` no se ejecutan todavía).
