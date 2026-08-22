# Apertura del mercado España — 2026-08-22

España es el primer mercado de CotizaT fuera de LatAm. Esta nota resume qué
se implantó, cómo se comporta y qué paso operativo queda (carga de precios en
Supabase).

## Qué incluye la versión España

1. **País y fiscalidad** (`app/paises.py`)
   - `ES` en el catálogo de países y en `ORDEN_SELECTOR`: bandera, EUR,
     IVA 21 %, NIF, vocabulario de obra peninsular
     («hormigón, pladur, falso techo, alicatado, fontanero») y ejemplos de
     formulario (B12345678, +34 600 000 000, S.L., Madrid).
   - Selector de país de la landing, alta de cuenta
     (`app/templates/auth/access.html`) y alta de organización
     (`organization_new.html`) ofrecen España.

2. **Partidas adaptadas a España** (terminología, igual que CO/MX/EC/PE)
   - Glosario VE→ES: `basedatos_partidas/glosarios/ES.json` (~130 entradas:
     concreto→hormigón, friso→enfoscado, cielo raso→falso techo,
     mesón→encimera, plomero→fontanero, cabilla→redondo, tanquilla→arqueta,
     losa→forjado, vaciado→hormigonado, enchapado→alicatado,
     porcelanato→porcelánico, pintura de caucho→pintura plástica…).
   - La traducción es al vuelo (`app/services/traduccion.py`, con
     «españa»→«ES» en el mapa de nombres): el catálogo base no se duplica;
     `/partidas`, el editor, los recursos y los PDF muestran la forma
     peninsular cuando la organización es española.

3. **Precios adaptados a España** (EUR)
   - Matriz nacional: `basedatos_partidas/salida/precios_recursos_espana.csv`
     — 388 recursos × 1 país: 64 referencias observadas (mano de obra de
     convenio/mercado 2026, cemento, acero, pladur, adhesivos, pinturas,
     áridos, hormigón premezclado, maquinaria…) y 324 derivadas de la
     canasta investigada. Todo en EUR con rango, fuente, fecha y confianza.
   - Investigación: `docs/INVESTIGACION_PRECIOS_ESPANA.md`.
   - Metodología: `docs/METODOLOGIA_PRECIOS_REFERENCIA_ESPANA.md`
     (misma jerarquía que LatAm: override de organización → referencia
     nacional → respaldo USD).
   - Tasa de corte 1 USD = 0,8564 EUR (xe.com/BCE, 21-22/08/2026), también
     verificada en `app/services/tasa.py` (`TASAS_SUGERIDAS["EUR"]`) para que
     el wizard y la landing pre-rellenen la tasa EUR.

4. **Landing y SEO**
   - Rutas `/es` y `/es/` (`app/routers/publico.py`), copy propio en
     `app/seo.py` (`_LANDING["ES"]`) y cuerpo propio en
     `app/seo_contenido.py` (`CUERPO_PAIS["ES"]`): no es un find-and-replace.
   - hreflang `es-ES`, sitemap con `/es/`, JSON-LD con `es-ES` y España en
     `areaServed`.
   - El ejemplo de la landing se muestra en EUR con la tasa verificada y con
     la terminología traducida (enfoscado, no friso).

5. **Importador** (`app/services/importador_precios_mercado.py`)
   - `MONEDA_PAIS["ES"] = "EUR"`: las matrices ES se validan e importan con
     su moneda correcta.

## Paso operativo pendiente (producción)

Pegar en Supabase SQL Editor el archivo
`docs/cargar_precios_referencia_espana_2026-08-22.sql` (generado por
`tools/generar_sql_precios_espana.py`). El script es idempotente, está en una
transacción con verificaciones y **solo** reemplaza referencias nacionales
ES; no toca overrides de empresas ni referencias de otros países. Después,
comprobar con la consulta final del script (debe devolver 388).

Regeneración si cambian los datos:

```bash
python3 tools/generar_matriz_precios_espana.py   # CSV
python3 tools/generar_sql_precios_espana.py      # SQL
```

## Pruebas

`tests/test_espana.py` (30 pruebas): país/selector, defaults EUR-IVA-NIF,
traducción VE→ES (palabras, frases, plurales, protección de términos ya
peninsulares), tasa EUR, wizard de bienvenida español, `/configuracion` y
`/partidas/api/filas` en EUR, landing `/es/` (canonical, hreflang, ejemplo en
EUR, IVA 21 %, Madrid), y validación de la matriz y del SQL de carga.

Suite completa: 975 passed, 9 skipped (2026-08-22).
