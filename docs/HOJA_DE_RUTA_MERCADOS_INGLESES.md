# Hoja de ruta: inglés por mercado y apertura del Reino Unido

**Rama:** `arena/861f96bf-generador-comercial` · **71 commits** sobre `8a2ee18`
**Última verificación:** 18 de octubre de 2026 · suite **1744 pasan, 9 omitidos**

Este documento existe para poder retomar el trabajo sin tener que reconstruir
el contexto. Dice qué está terminado, qué queda, en qué orden conviene
abordarlo y qué decisiones **no** se deben revertir.

Todo lo que aparece aquí está comprobado en el repositorio. Cuando un dato es
una estimación o un juicio, se dice expresamente.

---

## 1. Estado de un vistazo

| Bloque | Estado | Commit |
|---|---|---|
| Adaptación al inglés de toda la aplicación | **Hecho** | `d6a08e6`, `8dccab5`, `548b3e6` |
| Análisis de mercado: Reino Unido | **Hecho** | `51bc39b` |
| Reino Unido · Fase 0 — matriz de precios en libras | **Hecho** | `0223004` |
| Recursos del catálogo en inglés de obra real | **Hecho** | `c6145b2` |
| Reino Unido · Fase 1 — CIS e inversión del sujeto pasivo | **Hecho** | `2c614cd` |
| Reino Unido · Fase 2 — divisa y vigencia de precios | **Hecho** | `7cdd1c2` |
| Carga de matrices desde el panel de operador | **Hecho** | `883b42a`, `508daaf` |
| **Cargar la matriz de Reino Unido en producción** | **Pendiente** | — es el bloqueo |
| Reino Unido · Fase 3 — SEO de cola larga | Pendiente | — |
| Irlanda, Australia, Canadá, Estados Unidos | Pendiente | cada uno necesita estudio de precios |

**Conclusión:** el producto está listo para Reino Unido **salvo una cosa**:
la matriz de precios de 388 recursos está generada y validada, pero **no está
cargada en la base de datos**. Sin ella, un presupuesto británico sale a
aproximadamente la mitad del coste real, y la mano de obra unas seis veces por
debajo. Es exactamente el escenario que se descartó desde el principio.

---

## 2. Qué está terminado

### 2.1 La adaptación al inglés

La base del catálogo está en **inglés de Estados Unidos** y la terminología de
cada mercado se aplica encima como variante (`app/services/variante_ingles.py`).
No hay un bloque compartido entre países: cada uno tiene su vocabulario, sus
impuestos y sus tarifas.

- **3.006 partidas** del catálogo traducidas. Medido con detector de acentos y
  `ñ` más una lista de términos de oficio: **0 restos de español**.
- Revisados al azar y corregidos: *kerb, worktop, splashback, tap, cooker hood,
  raised access floor, socket outlet, ironmongery*.
- Los **388 recursos** del descompuesto tienen su cadena en inglés
  (`basedatos_partidas/datos/recursos_en.json`), incorporada a la tabla de
  excepciones en tiempo de carga.
- Correos, PDF, rótulos y avisos en inglés.
- `tools/chequear_plantillas_en.py`: **92 pares · 0 problemas**.

### 2.2 La arquitectura por mercado

- **23 mercados**: 18 hispanos + 5 ingleses (AU, CA, GB, IE, US).
- URLs en minúsculas en la ruta (`/en-gb/`), BCP-47 en el `hreflang` (`en-GB`).
- La tabla de países es `PAISES` (no `MERCADOS`).
- El panel de administración (`admin/`) queda **en español, fuera de scope**.

### 2.3 Reino Unido

**Fase 0 — matriz de precios (`0223004`).**
388 recursos en libras, sobre la base de **coste empresa**, sin IVA.
167 precios investigados uno a uno y 221 derivados del factor de su familia.
El criterio de precios exactos —no convertidos por tipo de cambio— está
documentado en `docs/METODOLOGIA_PRECIOS_REFERENCIA_REINO_UNIDO.md` y
`docs/INVESTIGACION_PRECIOS_REINO_UNIDO.md`.

Mano de obra, coste empresa por hora facturable:

| Oficio | £/h | Oficio | £/h |
|---|---|---|---|
| Peón general | 18,71 | Fontanero / calefacción | 25,22 |
| Peón especialista | 19,50 | Soldador / montador | 25,67 |
| Paisajista | 20,85 | Electricista | 26,64 |
| Ferrallista | 22,74 | Albañil | 23,23 |
| Pintor | 22,99 | Carpintero / vidriero / montador | 23,64 |
| Solador / alicatador | 24,48 | | |

Recargo empresarial del **19,8 %** sobre **1.751,9 horas facturables/año**.

**Fase 1 — fiscalidad (`2c614cd`).**
Motor CIS e inversión del sujeto pasivo en
`app/services/fiscalidad_reino_unido.py`. Retención del **20 %** (registrado y
verificado), **30 %** (no registrado) o **0 %** (bruto), aplicada sobre la mano
de obra **descontando el coste de materiales**. Inversión del sujeto pasivo
cuando procede (VATA 1994 s. 55A), con la nota obligatoria en la factura.
Migración `k6c9f2d5b8a3`, que es el **head de Alembic actual**.

**Fase 2 — divisa y vigencia (`7cdd1c2`).**
Los 23 mercados tienen moneda y tasa verificada; sin conversión posible la
plataforma lo dice en vez de inventar un `1.0`. Unidades imperiales solo para
Estados Unidos, convirtiendo el precio **y el rango**. Vigencia de precios con
estados *vigente / por revisar / obsoleta / caducada / sin fecha*.

### 2.4 Carga de matrices desde el panel (`883b42a`)

Nueva pestaña **Sistema › Matrices de precios**:

- Estado de los 23 mercados: referencias cargadas, moneda, sistema de unidades,
  última consulta y cuántas están por revisar.
- Carga en dos pasos: **validar** (no escribe) y **cargar** (solo escribe si la
  validación salió limpia).
- Solo **superadmin**: cambia lo que pagan todos los clientes del país.

Detalles de diseño que conviene no perder:

- El importador resuelve los recursos por **código y en todas las
  organizaciones** (modo `nacional`). Una referencia nacional sirve a todos los
  inquilinos, así que no puede buscarse solo en la organización que sube el
  fichero.
- Las políticas RLS de `precios_recursos_mercado` **solo permiten escribir
  referencias nacionales a una sesión con rol de operador**. Por eso el panel
  no es una comodidad: es la única vía que la arquitectura deja abierta. La
  herramienta de línea de comandos no puede activar ese rol.
- «Reemplazar» **desactiva** en vez de borrar. `resolver_precio` filtra por
  `activo`, así que el efecto es el mismo, pero el histórico se conserva y la
  operación se puede deshacer.

---

## 3. Qué queda pendiente

### 3.1 Antes de poder usar nada: desplegar

La matriz se carga **desde el panel de producción**, así que primero hay que
llevar el código a `main` y desplegar.

Orden:

1. Abrir la PR de `arena/861f96bf-generador-comercial` → `main`.
2. Hacer merge.
3. Desplegar.
4. **No hace falta ninguna migración nueva**: la tabla ya existe y las políticas
   RLS son las que había. El head de Alembic sigue siendo `k6c9f2d5b8a3`.

### 3.2 Bloqueo: cargar la matriz de Reino Unido

**Reino Unido no debe abrirse a clientes reales antes de este paso.**

Fichero: `basedatos_partidas/salida/precios_recursos_reino_unido.csv`
388 filas · país `GB` · moneda `GBP` · separador `;` · `fecha_consulta`
completa en las 388 filas (2026-10-18) · 167 `referencia` + 221 `derivado`.

Verificado con el validador real: **388 filas, 0 errores**.

Pasos:

1. Panel → **Sistema** → **Matrices de precios**.
2. Subir el CSV y pulsar **«Validar sin escribir»**.
3. Debe decir: *388 filas · 388 nuevas · 0 errores*. Si dice otra cosa, **no
   escribir** y revisar el motivo en pantalla.
4. Pulsar **«Escribir 388 referencias»**.

Comprobación después de cargar: abrir un presupuesto con país Reino Unido y
confirmar que la mano de obra ronda las cifras de la tabla de arriba, no la
mitad.

**Magnitud del error si se abre sin cargar** (388 recursos comparables,
1 USD = 0,7502 GBP): mediana **1,84×** por debajo del coste real; rango entre
0,53× y 17,14×.

| Recurso | Base USD | Convertido | Real GB |
|---|---|---|---|
| Oficial 1ª (solador) | 5,50 | £4,13 | **£24,48** |
| Peón | 3,50 | £2,63 | **£18,71** |
| Arena | 22,00 | £16,50 | **£54,00** |

### 3.3 Tres defectos de inglés localizados

Encontrados revisando las 3.006 cadenas en inglés. Están identificados con su
código, así que son de arreglo directo:

| Código | Nombre | dice ahora | debe decir |
|---|---|---|---|
| `09.10.01.090` | Instalación de pulsador de alarma | *pull station* | **call point** |
| `09.17.02.020` | Reparación de punto eléctrico | *electrical outlet* | **socket outlet** |
| `02.07.08.050` | Desmontaje de cocina empotrada | *built-in hob* | **built-in cooker** |

Los dos primeros son vocabulario de Estados Unidos colándose en el mercado
británico. El tercero es un error de significado: su propia descripción dice
«cocina **o estufa** empotrada», así que *hob* (solo la placa) se queda corto.

Nota: el catálogo ya usa *socket outlet* correctamente en otras partidas; hay
44 apariciones de «outlet» y solo esta es incorrecta.

### 3.4 Deuda técnica menor

- `app/services/landing_ejemplo.py:321` hace
  `tasa_sugerida(moneda) or 1.0`. Una moneda sin tasa se presenta como si
  una unidad valiera un dólar. Debería avisar en vez de inventar.
- Las tasas se verificaron de una en una para **GBP, AUD y CAD**. Las demás
  siguen con las que había; conviene repasarlas antes de abrir cada mercado.

### 3.5 Fase 3: SEO de cola larga en Reino Unido

Sin empezar. `app/seo_articulos.py` y `app/seo_contenido.py` no mencionan
ningún código de mercado: hoy el SEO inglés es genérico, no por país.

### 3.6 Los otros cuatro mercados

Cada uno necesita **su propio estudio de precios**, tal como se decidió: no se
abre un mercado sin él.

| Mercado | Unidades | Moneda | Situación |
|---|---|---|---|
| **Irlanda** | métrico | EUR | Conducto listo; falta estudio de precios |
| **Australia** | métrico | AUD | Conducto listo; falta estudio de precios |
| **Canadá** | métrico | CAD | Conducto listo; falta estudio de precios |
| **Estados Unidos** | **imperial** | USD | Conversión de unidades hecha; falta estudio de precios |

Estados Unidos es el que más trabajo lleva: es el único imperial, así que las
cotizaciones llegan en libras, galones, pies y yardas mientras el catálogo
cuenta en kilos, litros y metros.

---

## 4. Orden recomendado

1. **PR → merge → desplegar.** Sin esto no se puede usar nada.
2. **Cargar la matriz del Reino Unido** y verificar un presupuesto de punta a
   punta. Es lo único entre el código actual y un Reino Unido utilizable.
3. **Los tres defectos de inglés.** Son tres cadenas; mejor dejarlas cerradas
   antes de que haya clientes delante.
4. **Fase 3 de SEO** para Reino Unido, ya con el mercado funcionando.
5. **Irlanda**: es el siguiente más barato (métrico, y comparte el euro y
   buena parte del vocabulario británico). Australia y Canadá después.
6. **Estados Unidos** al final: imperial, y es el mercado que más exige.

---

## 5. Decisiones que no se deben revertir

Son criterios del proyecto, no detalles de implementación:

- **No traducciones literales.** Los oficios y las soluciones constructivas
  tienen nombres distintos en cada país. *«Si va a ser algo mediocre mejor no
  hacerlo.»*
- **Reino Unido y Estados Unidos nunca comparten bloque.** Cada país tiene su
  terminología, sus impuestos y sus tarifas.
- **Documentos distintos por país, sin compartir código**: lo que cambia es el
  resultado, no la plantilla. Una sola plantilla alimentada por datos de
  mercado.
- **Precios exactos, nunca convertidos.** Convertir la base en dólares del
  catálogo está descartado: da 15,70 USD/m² → ~£12,40/m² frente a las £40–70/m²
  reales del mercado británico.
- **Estudio de precios antes de abrir un mercado.**
- **Sin apaños ni parches**: lo que se haga, en cada mercado.
- La tabla de países se llama **`PAISES`**.
- `admin/` queda en español.

---

## 6. Cómo continuar

Arrancar el entorno (el `.venv` no sobrevive entre sesiones):

```bash
python3 -m venv .venv && .venv/bin/pip install -q -r requirements.txt
```

Comandos de control que conviene pasar antes de cualquier cambio:

```bash
.venv/bin/python -m pytest -q                    # suite completa (~5 min)
.venv/bin/python tools/chequear_plantillas_en.py # pares de plantillas EN
.venv/bin/python tools/verificar_matriz_importable.py GB   # matriz británica
.venv/bin/python tools/verificar_matriz_importable.py ES   # matriz española
```

Ficheros que concentran el trabajo:

| Qué | Dónde |
|---|---|
| Generación de matrices de precios | `tools/generar_matriz_precios_reino_unido.py` |
| Metodología e investigación de precios | `docs/METODOLOGIA_PRECIOS_REFERENCIA_REINO_UNIDO.md`, `docs/INVESTIGACION_PRECIOS_REINO_UNIDO.md` |
| Análisis de mercado | `docs/ANALISIS_MERCADO_REINO_UNIDO.md` |
| Fiscalidad británica | `app/services/fiscalidad_reino_unido.py` |
| Importador y validación | `app/services/importador_precios_mercado.py` |
| Variantes de inglés por mercado | `app/services/variante_ingles.py` |
| Divisa y vigencia | `app/services/tasa.py`, `app/services/vigencia_precios.py` |
| Carga desde el panel | `app/routers/admin.py`, `app/routers/admin_paginas.py` |

**Al añadir una migración**, se rompen cinco tests a la vez: hay que actualizar
los cuatro parches de la cadena de heads, añadir `docs/staging_upgrade_<rev>.sql`
y subir `EXPECTED_ALEMBIC_HEAD` en `app/database.py`.

---

## 7. Números verificados

| Magnitud | Valor |
|---|---|
| Partidas del catálogo | 3.006 |
| Recursos del descompuesto | 388 |
| Mercados | 23 (18 hispanos + 5 ingleses) |
| Referencias de la matriz británica | 388 (167 investigadas + 221 derivadas) |
| Resto de español en el catálogo inglés | 0 |
| Pares de plantillas EN sin problemas | 92 / 92 |
| Tests | 1744 pasan, 9 omitidos |
| Head de Alembic | `k6c9f2d5b8a3` |
| Recargo empresarial británico | 19,8 % sobre 1.751,9 h facturables |
| Tasa adoptada | 1 USD = 0,7502 GBP |
