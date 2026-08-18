# Datos sensibles en el repositorio (E1-021)

Fecha de la revisión: **15/08/2026**.

E1-021 tiene dos mitades: **mantener el repositorio privado** (operativo) y
**revisar que no contenga datos reales sensibles** (contenido). Este documento
cierra ambas y describe cómo se mantiene cerrado.

---

## 1. Repositorio privado — verificado

```console
$ gh api repos/gtrespana-bit/generador-comercial --jq '{private,visibility,forks:.forks_count}'
{"private": true, "visibility": "private", "forks": 0}
```

Sin forks, la visibilidad privada no ha filtrado copias. **No cambiar a público**
sin repetir antes la auditoría de la sección 3.

> Aviso: en GitHub, hacer público un repositorio **no borra** su historial. Todo
> lo que se confirmó alguna vez queda visible. Por eso la auditoría cubre el
> histórico completo y no solo el árbol de trabajo.

---

## 2. Qué se considera «dato sensible» aquí

| Categoría | Ejemplos | Por qué importa |
| --- | --- | --- |
| Credenciales | `sb_secret_…`, `sb_publishable_…`, `re_…` (Resend), JWT, tokens de GitHub/AWS/Upstash, claves PEM | Acceso directo a la base, al correo del dominio o al repositorio |
| Cadenas de conexión | `postgresql://usuario:contraseña@host` | Contiene la credencial y el host reales |
| Datos personales | Correos de Gmail/Outlook/etc., teléfonos VE/ES, RIF/NIF | Identifican a personas reales; además son datos protegidos |
| Infraestructura propia | Referencia del proyecto Supabase, subdominio de Upstash | No son secretos, pero señalan la instalación real a quien quiera atacarla |
| Archivos que nunca se versionan | `.env`, `*.db`, volcados, `backups/`, `app/static/uploads/`, `.vercel/` | Contienen datos de trabajo reales |

Los **derechos y la procedencia del catálogo** (partidas, descompuestos CYPE y
capturas) son **E1-022**, no E1-021, y están **cerrados** desde el 19/08/2026
con auditoría de evidencia (ver §6).

---

## 3. Auditoría realizada

### 3.1 Árbol de trabajo — 214 archivos versionados

Herramienta: `tools/auditar_datos_sensibles.py`.

```console
$ python tools/auditar_datos_sensibles.py
Sin hallazgos: 214 archivos versionados revisados (E1-021).
```

**Tres hallazgos reales, ya corregidos:**

1. `HOJA_DE_RUTA_Y_ESTADO_DEL_PROYECTO.md` publicaba el **correo personal del
   propietario** dentro de la captura HTTP de una prueba de recuperación de
   contraseña → sustituido por `persona@example.com`, con una nota que indica
   que el correo real se reemplazó.
2. y 3. `docs/GUIA_STAGING_POR_CLICS.md` incluía dos veces la **referencia real
   del proyecto Supabase** en el ejemplo de cadena de conexión del pooler →
   sustituida por `<ref-de-tu-proyecto>`. La guía se entiende igual y deja de
   señalar la instalación concreta.

Ninguno era una credencial: no hay nada que rotar por estos tres.

### 3.2 Historial completo — 101 commits, 653 blobs

El repositorio llegó *shallow* a la sesión; se recuperó el histórico completo
(`git fetch --unshallow`) y se recorrieron **todos** los blobs de **todas** las
ramas buscando los patrones de credencial de la sección 2.

Resultado: **ninguna credencial real, en ningún commit**. Todas las
coincidencias son marcadores o valores de laboratorio, por ejemplo:

```text
re_clave-de-prueba-no-real          sb_secret_no_debe_usarse
sb_secret_prueba-no-real            postgres://user:secret@db.example
postgresql://cotizat_runtime:REEMPLAZAR@localhost
```

Tampoco existe, ni existió, ningún blob con ruta `.env`, `*.db`, `*.pem` o
similar.

**Conclusión: no hace falta reescribir el histórico (`filter-repo`) ni rotar
ninguna clave por causa del repositorio.** Las claves siguen viviendo solo en
Supabase, Vercel, Resend y Upstash.

---

## 4. Cómo se mantiene cerrado

`tests/test_datos_sensibles.py` (34 pruebas) se ejecuta con la suite, y CI
ejecuta la suite en cada pull request. Comprueba tres cosas:

1. **El repositorio está limpio** ahora mismo (auditoría completa + ausencia de
   archivos prohibidos + `.gitignore` sigue cubriendo lo esencial).
2. **Cada regla detecta de verdad**, con un ejemplo sintético por categoría. Una
   regla rota da confianza falsa, que es peor que no tenerla.
3. **Los marcadores legítimos no producen ruido** (`REEMPLAZAR`,
   `persona@example.com`, `+58 412 000 0000`, `J-00000000-0`, `tu-proyecto`…).
   Un auditor que grita en falso acaba ignorado.

Ejecución manual:

```console
python tools/auditar_datos_sensibles.py          # informe legible
python tools/auditar_datos_sensibles.py --json   # salida para máquinas
```

Devuelve estado `1` si encuentra algo.

### Si la auditoría marca algo

1. **Si es un dato real** → sustitúyelo por un marcador o un dominio reservado
   (`example.com`, `ejemplo.com`, `.test`, `.invalid`). Si era una credencial
   **rótala en el proveedor**: quitarla del código no la invalida, y el
   historial la conserva.
2. **Si es un falso positivo** → añádelo a `EXCEPCIONES` en
   `tools/auditar_datos_sensibles.py` con el motivo escrito. Se exceptúa la
   coincidencia concreta (ruta + regla + texto), nunca la regla entera.

> **Cuándo NO usar `EXCEPCIONES`.** Si te encuentras añadiendo excepciones a
> puñados, la lista deja de documentar rarezas y empieza a vaciar la regla.
> Ocurrió el 18/08/2026: los ejemplos de la prueba gratuita generaron **42
> hallazgos** de «correo-personal». La salida correcta no fue exceptuarlos uno
> a uno, sino **arreglar los datos** (nombres de fantasía) y enseñarle al
> auditor el concepto general —el mismo `_es_marcador` que ya aplicaba a
> credenciales, teléfonos y RIF—, con tests que fijan las dos direcciones: lo
> que debe seguir detectándose y lo que no debe dar ruido. Una excepción es
> para un caso irrepetible con nombre y apellido; un patrón que se repite pide
> una regla.

### Ojo: el auditor solo ve lo que Git ya rastrea

`archivos_versionados()` usa `git ls-files`, así que **un archivo nuevo no se
audita hasta que se commitea**. La consecuencia práctica muerde: la suite puede
estar en verde antes de commitear y romperse justo después, con el commit ya
subido. Pasó con `fbc3c26`. **Tras commitear archivos nuevos, vuelve a correr
la suite completa** antes de dar el trabajo por cerrado.

---

## 5. Reglas para escribir documentación y pruebas

- Correos de ejemplo: `persona@example.com`, `duena@example.com`,
  `no-responder@cotizat.test`. **Nunca** una dirección de Gmail u otro proveedor
  de consumo, ni siquiera la propia.
  - **Única excepción, y es estrecha:** cuando el dominio real *es* el hecho
    que se documenta. La normalización de identidad (los puntos que Gmail
    ignora, el `+etiqueta` de Outlook) solo es cierta en esos proveedores, y un
    ejemplo con `example.com` no demostraría nada. En ese caso —y solo en ese—
    se admite el dominio real **con un nombre de fantasía en la parte local**:
    `fulano`, `mengana`, `zutano`… Quien identifica a una persona es la parte
    local, no el dominio. `fulano.detal@gmail.com` no es de nadie; en cambio
    un nombre y un apellido corrientes sobre ese mismo dominio pueden ser una
    persona real, y el auditor los marca.
    La lista de nombres admitidos es cerrada (`NOMBRES_DE_FANTASIA`) y el
    nombre debe **abrir** la parte local: si va precedido de cualquier otra
    cosa (del estilo «no-soy-» seguido de `fulano`), se sigue marcando.
- Teléfonos: abonado a ceros (`+58 412 000 0000`).
- Documentos fiscales: `J-00000000-0`.
- Proyectos y hosts: `https://tu-proyecto.supabase.co`,
  `<ref-de-tu-proyecto>`, `https://tu-base.upstash.io`.
- Secretos en documentación: siempre `REEMPLAZAR…`, nunca un valor con forma
  de clave verdadera.
- Capturas de pantalla: recórtalas antes de subirlas si muestran correos,
  nombres de clientes o importes reales.

---

## 6. Pendiente relacionado (no bloquea E1-021)

- **E1-022 — auditar la procedencia y los derechos del catálogo de partidas.** ✅
  **CERRADO (19/08/2026) con auditoría de evidencia.** Resultado: el catálogo es
  **100 % de autoría propia**; los archivos de ejemplo (`DPT020.xlsx`,
  `RBA010.xlsx`, `RBE030.xlsx`, `BENEFICIO.png` y la captura de la raíz) **no
  aportan contenido al producto** y no suponen riesgo de derechos.

  Evidencia de la auditoría (fecha 19/08/2026, sobre `main` en `c24c2cc`):

  - El catálogo en producción vive en `basedatos_partidas/datos/`:
    **3.006 partidas descompuestas** (`descompuestos/*.json` + `partidas.csv`)
    y el cuadro de recursos (`recursos.json`). La app carga **solo** de ahí
    (`app/services/catalogo_propio.py`); los `.xlsx` jamás se cargan en runtime.
  - **0 coincidencias** (exactas y parciales, ventanas de 60 caracteres) entre
    los textos de los 3 `.xlsx` y los títulos/descripciones del catálogo, ni en
    `partidas.csv` ni en `recursos.json`.
  - Los códigos `RBA010`/`RBE030` de CYPE **no existen** en el catálogo. Los
    `DPT0xx` aparecen solo como `codigo_anterior` (historial interno propio,
    migrado el 16/08/2026 a codificación `CT-…`; `mapa_migracion.json` es
    interno, no se publica — ver `basedatos_partidas/README.md`,
    «Codificación propia»).
  - `recursos.json` no contiene frases distintivas CYPE (p. ej. `UNE-EN 998`,
    `GP CSIII`); las 2 partidas del catálogo que mencionan «mortero de cal»
    (12.02.01.100, 12.14.03.080) son textos propios genéricos.
  - Los `.xlsx` solo se usan como **formato de importación**: documentación
    (`GUIA_IMPORTACION_EXCEL_CYPE.md`), parser de archivos subidos por el
    usuario (`app/services/importer.py`) y fixtures de pruebas
    (`tests/test_app.py`). `BENEFICIO.png` y la captura de la raíz son
    archivos sueltos sin ninguna referencia en código ni plantillas.

  Conclusión: nada de ese material de terceros llega al producto. Si en el
  futuro se importara un banco de precios externo (p. ej. BCCA), ese contenido
  quedaría en la organización que lo suba y nunca en el catálogo propio.
