# Hoja de ruta: inglés por mercado y apertura del Reino Unido

**Rama:** `arena/76b3d95f-generador-comercial` sobre `main` (`cbb5e99`, que ya
incluye el trabajo inglés fusionado en la PR #124 y la PR #128)
**Última verificación:** 19 de octubre de 2026 · suite **1933 pasan, 9 omitidos**

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
| Lectura RLS de operador sobre `recursos` | **Hecho y desplegado** | `l7d0e3f6a9c4` (`/readyz` = head) |
| Cargar la matriz de Reino Unido en producción | **Hecho** | 18-10-2026, SQL Editor |
| Reino Unido · Fase 3 — SEO de cola larga | **Hecho** | esta rama (`docs/SEO_REINO_UNIDO.md`) |
| Irlanda · Fase 0 — estudio de precios y matriz EUR | **Hecho** | esta rama (`docs/INVESTIGACION_PRECIOS_IRLANDA.md`) |
| Irlanda · Fase 1 — RCT e inversión del sujeto pasivo | **Hecho** | esta rama (`app/services/fiscalidad_irlanda.py`) |
| Irlanda · carga de la matriz y migración en producción | **Hecho** | ejecutados el 19-10-2026 (migración `m8e1f4a7b2c5` + `docs/cargar_precios_referencia_irlanda_2026-10-19.sql`) |
| Australia · Fase 0 — estudio de precios y matriz AUD | **Hecho** | esta rama (`docs/INVESTIGACION_PRECIOS_AUSTRALIA.md`) |
| Australia · carga de la matriz en producción | **Hecho** | ejecutado el 19-10-2026 (`docs/cargar_precios_referencia_australia_2026-10-19.sql`) |
| Canadá · Fase 0 — estudio de precios y matriz CAD | **Hecho** | esta rama (`docs/INVESTIGACION_PRECIOS_CANADA.md`) |
| Canadá · carga de la matriz en producción | **Hecho** | ejecutado el 19-10-2026 (`docs/cargar_precios_referencia_canada_2026-10-19.sql`) |
| Estados Unidos | Pendiente | necesita estudio de precios (y es imperial) |

**Conclusión:** Reino Unido está **abierto y completo** en producto, datos y
SEO. La matriz de 388 recursos está cargada, la migración `l7d0e3f6a9c4` está
desplegada (`/readyz` la confirma) y el mercado tiene landing, tres hubs y
cuatro artículos con URL propia (`docs/SEO_REINO_UNIDO.md`).

Lo que queda ya no es un bloqueo técnico: Irlanda tiene su estudio de precios,
su Fase 1 fiscal (RCT) hecha, la migración `m8e1f4a7b2c5` aplicada y su
matriz cargada en producción (19-10-2026); Australia y Canadá tienen su
estudio de precios hecho y su matriz cargada (19-10-2026), a falta solo de
su Fase 1 fiscal, y solo Estados Unidos —el imperial— necesita aún su
estudio de precios antes de abrirse. Lo único de Reino Unido que sigue pendiente es
**conseguir enlaces entrantes y medir** en Search Console: el contenido está,
la autoridad de dominio se construye fuera del código.

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
Migración `k6c9f2d5b8a3`; el head de Alembic pasó después a `l7d0e3f6a9c4` (§2.5) y hoy es `m8e1f4a7b2c5` (RCT irlandés, §3.6).

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

### 2.5 El fallo de producción del 2026-10-18 y su arreglo (`l7d0e3f6a9c4`)

El primer intento de cargar la matriz británica desde el panel de producción
devolvió **388 errores «recurso no encontrado»**, uno por fila. La causa:

- El importador resuelve cada fila contra `public.recursos` por código
  (`resolver_recursos` en modo `nacional`).
- `recursos` es tabla *tenant* con RLS desde `c93e7a4d20f1`: la política
  `cotizat_tenant_select` exige `cotizat.organization_id` con valor **y**
  membresía activa en esa organización.
- La sesión del panel (`get_operator_db`) autentica al operador y marca
  `cotizat.es_operador=on`, pero **no activa ninguna organización**: el
  `SELECT` sobre `recursos` devuelve cero filas.
- `sin_filtro_organizacion` solo levanta el filtro **ORM** de la aplicación;
  el RLS de PostgreSQL se aplica por debajo.
- Las políticas de `precios_recursos_mercado` (`e7b3c1d5a204`) sí contemplan
  al operador (puede escribir la referencia nacional), pero nadie añadió la
  excepción de **lectura** sobre `recursos`, que es lo que el importador
  necesita para resolver los códigos.

Por qué no se detectó antes:

- Con **SQLite** (escritorio y toda la suite de tests) no hay RLS: el panel se
  probó verde.
- `tools/verificar_matriz_importable.py` valida contra una **sesión simulada**
  que levanta el catálogo de `recursos.json`, no contra la base real: su
  «388 filas · 0 errores» nunca ejerció el RLS.
- España y LatAm se cargaron por **SQL en el SQL Editor de Supabase** (rol
  administrativo, que ignora el RLS), no por el panel.

El arreglo, en esta rama:

- Migración **`l7d0e3f6a9c4`** — política adicional
  `cotizat_operador_select_recursos` (solo `SELECT`, solo para la marca
  `cotizat.es_operador`). Las políticas permisivas se combinan con OR: la
  visibilidad de cada organización sobre sus recursos no cambia y el operador
  no puede escribir en el catálogo de nadie.
- `docs/staging_upgrade_l7d0e3f6a9c4.sql` — aplicación manual en el SQL
  Editor (producción no ejecuta Alembic sola).
- El importador ahora **explica la causa** cuando la sesión no ve ningún
  recurso, en vez de repetir «recurso no encontrado» cientos de veces.
- Tests: cadena de heads actualizada (los cuatro ficheros del ritual),
  políticas de la migración y diagnóstico del importador.

El head de Alembic pasa a ser **`l7d0e3f6a9c4`**.

---

## 3. Qué queda pendiente

### 3.1 Despliegue y esquema: hecho

La base de producción está en **`l7d0e3f6a9c4`**, que es el head que exige el
código, y `/readyz` responde `ok: true` (comprobado el 18-10-2026). Las dos
migraciones que bloqueaban el panel están aplicadas:

- `k6c9f2d5b8a3` — columnas de fiscalidad británica (`iva_tratamiento`,
  `cis_tipo`, `coste_materiales`).
- `l7d0e3f6a9c4` — política `cotizat_operador_select_recursos`, que es lo que
  deja al panel de operador **ver** el catálogo para resolver los códigos.

**Lo que hay que recordar si vuelve a pasar.** Vercel no mira `/readyz` al
desplegar: si el código exige una revisión que la base no tiene, la app
responde 500 en `/inicio` y el despliegue sigue diciendo «Listo». El orden
correcto es aplicar el SQL de la migración **antes o en el mismo momento** del
merge, y comprobar `/readyz` después. Los scripts de
`docs/staging_upgrade_<rev>.sql` abortan solos si la versión no es la
esperada, así que no hay riesgo de aplicarlos dos veces.

### 3.2 Carga de la matriz de Reino Unido: hecha

La matriz está cargada en producción (18-10-2026). Fichero de origen:
`basedatos_partidas/salida/precios_recursos_reino_unido.csv`, 388 filas,
país `GB`, moneda `GBP`, 167 `referencia` + 221 `derivado`, validada con el
importador real: **388 filas, 0 errores**.

Queda como referencia para las próximas matrices, porque las dos vías siguen
abiertas y son idempotentes:

- **Panel de operador** → *Sistema › Matrices de precios* → validar sin
  escribir y luego escribir. Solo funciona con la migración `l7d0e3f6a9c4`
  desplegada.
- **SQL Editor de Supabase** con el rol administrativo, pegando
  `docs/cargar_precios_referencia_reino_unido_2026-10-18.sql`. La verificación
  final del script debe devolver **388**.

Qué se habría perdido sin cargarla (388 recursos comparables,
1 USD = 0,7502 GBP): mediana **1,84×** por debajo del coste real, con un rango
entre 0,53× y 17,14×.

| Recurso | Base USD | Convertido | Real GB |
|---|---|---|---|
| Oficial 1ª (solador) | 5,50 | £4,13 | **£24,48** |
| Peón | 3,50 | £2,63 | **£18,71** |
| Arena | 22,00 | £16,50 | **£54,00** |

### 3.3 Los tres defectos de inglés: cerrados

Los tres siguen corregidos en `app/services/variante_ingles.py` y hay una
prueba que impide que vuelvan (`tests/test_catalogo_recursos_gb.py`):

| Código | Nombre | decía | dice |
|---|---|---|---|
| `09.10.01.090` | Instalación de pulsador de alarma | *pull station* | **call point** |
| `09.17.02.020` | Reparación de punto eléctrico | *electrical outlet* | **socket outlet** |
| `02.07.08.050` | Desmontaje de cocina empotrada | *built-in hob* | **built-in cooker** |

Comprobado ejecutando el traductor real con mercado `GB`: los tres devuelven
el término británico.

### 3.4 Deuda técnica menor

- `app/services/landing_ejemplo.py:321` hace
  `tasa_sugerida(moneda) or 1.0`. El `1.0` ya no se muestra (justo debajo hay
  una guarda que cae a USD en vez de inventar la conversión), pero queda como
  código muerto que conviene limpiar.
- Las tasas se verificaron de una en una para **GBP, AUD, CAD y USD**. El
  **euro quedó reverificado el 19-10-2026** al fixing del BCE del 16/10
  (EUR/USD 1,1253 → 0,8886), la misma tasa de corte de la matriz irlandesa.
- El resto de monedas del selector siguen con las tasas de agosto.

### 3.5 Fase 3 — SEO de cola larga: hecha

Reino Unido ya tiene contenido propio de mercado, no plantilla:

| URL | Qué cubre |
|---|---|
| `/en-gb/` | Landing con cuerpo largo británico (CIS, IVA, vocabulario, APU) |
| `/en-gb/software-presupuestos` | Hub con bloques de preliminares, Excel y CIS/IVA |
| `/en-gb/apu` | Hub con coste empresa, residuos y plant |
| `/en-gb/remodelacion` | Hub con strip-out, making good y snagging |
| `/en-gb/guia/construction-quote-template-uk` | Qué lleva una *quotation* británica |
| `/en-gb/guia/cis-deduction-subcontractors` | Las tres retenciones CIS |
| `/en-gb/guia/vat-domestic-reverse-charge-construction` | Inversión del sujeto pasivo |
| `/en-gb/guia/unit-price-analysis-uk` | Análisis de precios unitarios en libras |

Además se corrigieron los defectos técnicos que hacían que ese contenido no
puntuara: sitemap sin redirecciones, hreflang `en` a una URL que responde 200,
`inLanguage` con locale, hubs ingleses que pintaban el cuerpo en español y
`X-Robots-Tag` calculado sobre la ruta reescrita. El detalle está en
`docs/SEO_REINO_UNIDO.md`.

**Lo que queda de SEO no es código:** enlaces entrantes (directorios de
oficio, FMB, TrustMark, prensa del sector) y medición en Search Console. Sin
autoridad de dominio, ocho páginas bien escritas siguen sin tráfico.

### 3.6 Los otros cuatro mercados

Cada uno necesita **su propio estudio de precios**, tal como se decidió: no se
abre un mercado sin él.

| Mercado | Unidades | Moneda | Situación |
|---|---|---|---|
| **Irlanda** | métrico | EUR | **Estudio, Fase 1 (RCT), migración y carga hechos (19-10-2026)**; queda el SEO de cola larga |
| **Australia** | métrico | AUD | **Estudio hecho y matriz cargada (19-10-2026)**; falta la Fase 1 fiscal (ABN/TPAR) |
| **Canadá** | métrico | CAD | **Estudio hecho y matriz cargada (19-10-2026)**; falta la Fase 1 fiscal (GST/HST, T5018) |
| **Estados Unidos** | **imperial** | USD | Conversión de unidades hecha; falta estudio de precios |

Estados Unidos es el que más trabajo lleva: es el único imperial, así que las
cotizaciones llegan en libras, galones, pies y yardas mientras el catálogo
cuenta en kilos, litros y metros.

**Presencia web (hecho, 2026-10-18).** Los cuatro tienen ya landing con
contenido de mercado —no plantilla con el país cambiado—, FAQ de su
fiscalidad y su sitio en la portada: accesos directos en el hero, bloque
propio en la tabla de los 23 mercados y mención explícita en el copy genérico.
Detalle en `docs/SEO_MERCADOS_INGLESES.md`. Lo que sigue faltando es el
estudio de precios, y sin él no se abren a clientes.

| Mercado | Landing | Cuerpo de mercado | FAQ propia | Matriz de precios |
|---|---|---|---|---|
| Reino Unido | `/en-gb/` | Sí (+ 4 artículos) | Sí | **Cargada** |
| Estados Unidos | `/en-us/` | Sí | Sí | Pendiente |
| Australia | `/en-au/` | Sí | Sí | **Cargada** (19-10-2026) |
| Canadá | `/en-ca/` | Sí | Sí | **Cargada** (19-10-2026) |
| Irlanda | `/en-ie/` | Sí | Sí | **Cargada** (19-10-2026) |

**Irlanda · Fase 1 fiscal — RCT (hecho, 19-10-2026).** Motor propio en
`app/services/fiscalidad_irlanda.py`, espejo del británico pero con la base
contraria: el RCT retiene el 0/20/35 % que fija Revenue sobre **el importe
íntegro sin IVA, materiales incluidos** («overall contract rule»), mientras
que el CIS solo retiene sobre la mano de obra. Inversión del sujeto pasivo
(s. 16(3) VATCA 2010) con la leyenda literal de Revenue y aviso de la regla
de los dos tercios (s. 16(5)): con IVA normal al 13,5 %, si los materiales
superan dos tercios del importe, todo tributa al 23 % — se avisa, no se
cambia el tipo por la espalda. Columna `rct_tipo` en presupuestos y facturas
(migración `m8e1f4a7b2c5`, head vigente), bloque 🇮🇪 en el editor y filas en
detalle y PDF; la retención se hereda al convertir a factura y al duplicar.
La landing irlandesa describía el RCT «sobre el elemento de mano de obra» —
la regla británica — y se ha corregido el texto a la vez que se hacía el
motor. De paso se reparó una regresión de la Fase 1 británica: el decorador
de la ruta de la descomposición de partida quedó pegado a
`_fiscalidad_gb_desde_form` y la pantalla llevaba sin registrarse desde
entonces.

---

## 4. Orden recomendado

1. **Publicar esta rama** (PR → merge → desplegar) y comprobar en producción
   `/readyz` (`m8e1f4a7b2c5`) y `/sitemap.xml` (cuatro URLs `/en-gb/guia/...`,
   ninguna `/gb/` ni `/en/`).
2. **Search Console**: reenviar el sitemap e inspeccionar `/en-gb/` y un
   artículo para confirmar «Página indexable». Empezar a medir impresiones.
3. **Enlaces entrantes** para Reino Unido: directorios de oficio, FMB,
   TrustMark y prensa del sector. Es lo único que separa el contenido de las
   primeras posiciones.
4. **Irlanda**: estudio de precios, Fase 1 fiscal (RCT), migración
   `m8e1f4a7b2c5` y carga de la matriz **hechos** (19-10-2026; SQL ejecutados
   en Supabase). Queda el SEO de cola larga, como en Reino Unido.
5. **Australia** (Fase 0 hecha y matriz cargada el 19-10-2026): Fase 1 fiscal
   — retención del 47 % por falta de ABN, *taxable payments annual report*
   (TPAR) y GST al 10 %. **Canadá** (Fase 0 hecha y matriz cargada el
   19-10-2026): Fase 1 fiscal — GST/HST por provincia y declaración T5018
   de pagos a subcontratistas.
6. **Estados Unidos** al final: imperial y el que más exige.

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
| SEO de Reino Unido | `app/seo_reino_unido.py`, `docs/SEO_REINO_UNIDO.md`, `tests/test_seo_reino_unido.py` |
| Presencia de los mercados ingleses | `app/seo_mercados_en.py`, `docs/SEO_MERCADOS_INGLESES.md`, `tests/test_presencia_mercados_angloparlantes.py` |

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
| Tests | 1872 pasan, 9 omitidos (34 de SEO británico + 34 de presencia de mercados) |
| Head de Alembic | `m8e1f4a7b2c5` |
| Recargo empresarial británico | 19,8 % sobre 1.751,9 h facturables |
| Tasa adoptada | 1 USD = 0,7502 GBP |
