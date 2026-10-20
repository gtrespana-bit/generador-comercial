# Paquetes SEO hispanos — implementación por lote

**Fecha:** 19/10/2026  
**Estado:** preparado en el repositorio; no acredita despliegue ni indexación.

## Alcance entregado

- 17 mercados posteriores a España, siguiendo el orden editorial de la estrategia.
- 46 recursos nuevos: 17 de mano de obra y 29 documentos/problemas técnicos locales.
- 54 recursos hispanos: tres por país. Las cinco guías históricas se mantienen en sus canónicas, con enlaces al corpus nuevo; sus antiguas rutas genéricas conservan el 301.
- España y los cinco mercados anglófonos conservan sus artículos y comportamiento.
- Registro común: canónicas, hreflang, Article, FAQ visible, sitemap y mapa del sitio.
- Landing y tres hubs de cada mercado enlazan sus tres recursos. Las nuevas piezas enlazan los hubs y otros recursos del mismo mercado. Los textos de landing/hubs añaden objeciones técnicas locales.
- Sin URLs de ciudad, cifras de búsqueda, testimonios ni funciones fiscales inventadas.

## Fuente y límites de los precios

**CO, PE, MX, EC, CL, AR, DO, PA, CR, GT, HN, SV, NI, UY, PY y BO:**
`basedatos_partidas/salida/precios_recursos_latam.csv`, el mismo artefacto que usa
`tools/importar_precios_mercado.py`. Se leen cinco oficios con su código, precio,
rango, fecha y naturaleza (referencia del modelo / derivado). No se usa la matriz
completa para rellenar huecos con respaldos regionales. Las cifras siguen el
modelo histórico de coste empresa documentado en la ronda 7; no son nuevas
observaciones de octubre ni liquidaciones laborales individuales. Que una tabla
esté en el código no prueba que esté importada en la base de producción.

**Venezuela:** `basedatos_partidas/datos/recursos.json`, moneda USD. Se muestran
solo tarifas internas del cuadro base, revisión declarada agosto de 2026, sin
inventar rango o calificarlas como coste empresa nacional validado. No se
publica una tasa de cambio de hoy.

- Fecha de consulta por fila visible; sin cambiar septiembre por octubre.
- Igual mínimo/máximo significa dispersión no documentada, no mercado sin variación.
- Importes horarios con dos decimales de cálculo y separadores del mercado, incluso si el documento final utiliza moneda sin decimales innecesarios.
- El ejemplo de producción de cuadrilla es explícitamente hipotético; no es un rendimiento local recomendado ni un precio final por m².
- Si faltan artefactos de precios se avisa; no se imprimen números de respaldo.
- Ningún nuevo artículo recibe HowTo automáticamente; documentos conceptuales y comparaciones no se declaran procedimientos normativos.

## Inventario canónico

### España (`/es/`)

- **Plantilla de presupuesto de reforma: qué debe llevar en España**  
  `/es/guia/plantilla-presupuesto-reforma-espana`
- **Precio por hora de la mano de obra de construcción en España (2026)**  
  `/es/guia/precio-hora-mano-obra-construccion-espana`
- **BC3 en presupuestos de reformas: importar, revisar y volver a exportar**  
  `/es/guia/bc3-presupuestos-reformas-espana`

### México (`/mx/`)

- **De la visita a la cotización en México (en pesos, con tu margen)**  
  `/mx/guia/cotizar-remodelacion-mexico`
- **Mano de obra de construcción en México: referencias 2026**  
  `/mx/guia/mano-obra-construccion-mexico`
- **Catálogo de conceptos y APU en México: del alcance al precio**  
  `/mx/guia/catalogo-conceptos-apu-mexico`

### Colombia (`/co/`)

- **Cómo armar un APU de pañete en Colombia (sin que el Excel se rompa)**  
  `/co/guia/apu-panete-colombia`
- **Mano de obra de construcción en Colombia: referencias 2026**  
  `/co/guia/mano-obra-construccion-colombia`
- **APU vs AIU en Colombia: qué calcula cada uno**  
  `/co/guia/apu-vs-aiu-colombia`

### Perú (`/pe/`)

- **Metrados y APU en Perú (en soles, con IGV aparte del comprobante)**  
  `/pe/guia/metrados-peru`
- **Mano de obra de construcción en Perú: referencias 2026**  
  `/pe/guia/mano-obra-construccion-peru`
- **APU de tarrajeo en Perú: metrado, recursos y rendimiento**  
  `/pe/guia/apu-tarrajeo-peru`

### Chile (`/cl/`)

- **Plantilla de presupuesto de construcción en Chile, en CLP**  
  `/cl/guia/plantilla-presupuesto-construccion-chile`
- **Mano de obra de construcción en Chile: referencias 2026**  
  `/cl/guia/mano-obra-construccion-chile`
- **APU de estuco en Chile: horas, pérdidas y precio en CLP**  
  `/cl/guia/apu-estuco-chile`

### Argentina (`/ar/`)

- **Actualizar un presupuesto de obra en Argentina sin perder el PDF enviado**  
  `/ar/guia/actualizar-presupuesto-obra-argentina`
- **Mano de obra de construcción en Argentina: referencias 2026**  
  `/ar/guia/mano-obra-construccion-argentina`
- **APU de revoque en Argentina con precios fechados en ARS**  
  `/ar/guia/apu-revoque-argentina`

### Venezuela (`/ve/`)

- **Presupuesto en USD y bolívares: la tasa se congela, el PDF no se mueve**  
  `/ve/guia/presupuesto-usd-bs-venezuela`
- **Mano de obra de construcción en Venezuela: referencias 2026**  
  `/ve/guia/mano-obra-construccion-venezuela`
- **APU de friso en Venezuela: recursos en USD y revisión en Bs**  
  `/ve/guia/apu-friso-venezuela`

### Ecuador (`/ec/`)

- **APU en Ecuador: dólares nativos, RUC e IVA 15 %**  
  `/ec/guia/apu-dolares-ecuador`
- **Mano de obra de construcción en Ecuador: referencias 2026**  
  `/ec/guia/mano-obra-construccion-ecuador`
- **APU de enlucido en Ecuador: consumos y cuadrilla en USD**  
  `/ec/guia/apu-enlucido-ecuador`

### República Dominicana (`/do/`)

- **Cubicación para presupuesto en República Dominicana**  
  `/do/guia/cubicacion-presupuesto-republica-dominicana`
- **Mano de obra de construcción en República Dominicana: referencias 2026**  
  `/do/guia/mano-obra-construccion-republica-dominicana`
- **Plantilla de presupuesto en pesos dominicanos: alcance e ITBIS**  
  `/do/guia/plantilla-presupuesto-dop-itbis`

### Panamá (`/pa/`)

- **Plantilla de presupuesto de construcción en Panamá, en USD**  
  `/pa/guia/plantilla-presupuesto-construccion-panama`
- **Mano de obra de construcción en Panamá: referencias 2026**  
  `/pa/guia/mano-obra-construccion-panama`
- **APU de repello en Panamá: precio USD y revisión de cuadrilla**  
  `/pa/guia/apu-repello-panama`

### Costa Rica (`/cr/`)

- **Plantilla de presupuesto de construcción en Costa Rica, en colones**  
  `/cr/guia/plantilla-presupuesto-construccion-costa-rica`
- **Mano de obra de construcción en Costa Rica: referencias 2026**  
  `/cr/guia/mano-obra-construccion-costa-rica`
- **APU de repello en colones: método para Costa Rica**  
  `/cr/guia/apu-repello-colones-costa-rica`

### Guatemala (`/gt/`)

- **Plantilla de presupuesto de construcción en Guatemala, en quetzales**  
  `/gt/guia/plantilla-presupuesto-construccion-guatemala`
- **Mano de obra de construcción en Guatemala: referencias 2026**  
  `/gt/guia/mano-obra-construccion-guatemala`
- **APU de repello y block en Guatemala: dos partidas en GTQ**  
  `/gt/guia/apu-repello-block-guatemala`

### Honduras (`/hn/`)

- **Plantilla de presupuesto de construcción en Honduras, en lempiras**  
  `/hn/guia/plantilla-presupuesto-construccion-honduras`
- **Mano de obra de construcción en Honduras: referencias 2026**  
  `/hn/guia/mano-obra-construccion-honduras`
- **APU de pared de bloque y repello en Honduras, en HNL**  
  `/hn/guia/apu-bloque-repello-honduras`

### El Salvador (`/sv/`)

- **Plantilla de presupuesto de construcción en El Salvador, en USD**  
  `/sv/guia/plantilla-presupuesto-construccion-el-salvador`
- **Mano de obra de construcción en El Salvador: referencias 2026**  
  `/sv/guia/mano-obra-construccion-el-salvador`
- **APU de repello en El Salvador: recursos locales en dólares**  
  `/sv/guia/apu-repello-el-salvador`

### Nicaragua (`/ni/`)

- **Plantilla de presupuesto de construcción en Nicaragua, en córdobas**  
  `/ni/guia/plantilla-presupuesto-construccion-nicaragua`
- **Mano de obra de construcción en Nicaragua: referencias 2026**  
  `/ni/guia/mano-obra-construccion-nicaragua`
- **APU de repello en córdobas: método para Nicaragua**  
  `/ni/guia/apu-repello-cordobas-nicaragua`

### Uruguay (`/uy/`)

- **Plantilla de presupuesto de reforma en Uruguay, en UYU**  
  `/uy/guia/plantilla-presupuesto-reforma-uruguay`
- **Mano de obra de construcción en Uruguay: referencias 2026**  
  `/uy/guia/mano-obra-construccion-uruguay`
- **APU de revoque en Uruguay: recursos en pesos uruguayos**  
  `/uy/guia/apu-revoque-uruguay`

### Paraguay (`/py/`)

- **Presupuesto de obra en guaraníes sin decimales innecesarios**  
  `/py/guia/presupuesto-guaranies-sin-decimales-paraguay`
- **Mano de obra de construcción en Paraguay: referencias 2026**  
  `/py/guia/mano-obra-construccion-paraguay`
- **APU de revoque en Paraguay: consumos y cálculo en PYG**  
  `/py/guia/apu-revoque-paraguay`

### Bolivia (`/bo/`)

- **De cómputos métricos a presupuesto de obra en Bolivia**  
  `/bo/guia/computos-metricos-presupuesto-bolivia`
- **Mano de obra de construcción en Bolivia: referencias 2026**  
  `/bo/guia/mano-obra-construccion-bolivia`
- **APU de revoque en bolivianos: del cómputo al coste**  
  `/bo/guia/apu-revoque-bolivianos-bolivia`

## Pendientes que no se dan por hechos

> Actualizado el 20/10/2026 (`docs/SEO_VERIFICACION_PRODUCCION_2026-10-20.md`).

| Trabajo | Estado |
|---|---|
| Código y contenido inicial de los 18 silos hispanos | Fusionado en el PR #133 |
| Despliegue de las nuevas páginas | **Confirmado el 20/10**: despliegue *Production* de `48a372cc` y contenido real servido; auditoría local del mismo código 195/195 |
| Canónica/hreflang/robots con cabeceras en el dominio | Certificadas en código; queda correr `tools/auditar_seo_produccion.py` contra el dominio (y corregir antes el host `www`) |
| Dominio preferido apex vs `www` | **Conflicto confirmado**: el borde sirve `www` y todo lo demás declara el apex; pendiente invertir en Vercel Domains |
| Confirmación de matrices cargadas en producción | Artefactos dentro de la función, confirmados; filas en BD: `tools/verificar_matrices_bd.py` listo y `/readyz` publica el conteo; falta ejecutarlo contra Supabase |
| GSC, SERP y validación de intención/competencia | Pendiente; no hay datos de estas fuentes en esta sesión |
| Comprobación y actualización local de las referencias históricas | Pendiente |
| Revisión de profesionales locales | Pendiente, especialmente fiscal/laboral |
| PDF real de ejemplo por país y comprobación de formato | Pendiente; no se ofrece una descarga inexistente |
| Casos, testimonios, colaboradores y enlaces locales | Pendiente; no se inventan |
| Dashboard de adquisición/activación/ingresos e indexación | Pendiente de conectar datos y medir |
| Validación automatizada final | 519 comprobaciones validadas en SEO, idiomas, mercados y precios; detalle más abajo |

No se declara ningún país nuevo «SEO completo v1». La petición de rapidez se
aplica a la implementación, no a fingir investigación o distribución. No abrir
páginas de estados, provincias o ciudades hasta disponer de evidencia y soporte
de producto. Los clusters adicionales de México (baño), Colombia (plantilla),
Perú (ampliación de metrados), Venezuela (plantilla) y Ecuador (plantilla) quedan
para validación de demanda; no se crean URLs que dupliquen la guía histórica.

## Implementación mantenible

- `app/seo_latam_contenido.py`: decisiones y párrafos específicos por mercado, sin cifras fiscales/precios duplicados.
- `app/seo_latam.py`: lectura de fuentes, tablas, ejemplo aritmético, estructura de revisión y enlaces de silo.
- `app/seo_articulos.py`: integración con los registros existentes y enlaces de vuelta desde las guías históricas.
- `app/seo_contenido.py`: contexto local en landing y hubs existentes.
- `tests/test_seo_latam.py`: cobertura conjunta de países, canónicas, idiomas, enlaces, schema, datos y ausencia de artefactos.

## Resultado de la validación final

Se ejecutó un único lote de regresión funcional, no pruebas parciales durante la redacción:

```sh
.venv/bin/python -m pytest -q tests/test_seo*.py tests/test_idioma.py tests/test_mercados.py tests/test_coste_empresa_mano_obra.py tests/test_precios_catalogo_moneda.py tests/test_precios_divisa.py tests/test_precios_mercado.py
```

Resultado inicial: **455 passed, 64 failed**. Los fallos estaban en el aislamiento
de la cookie del cliente compartido de las pruebas nuevas: comprobar `/en-us/`
fijaba el idioma inglés antes de solicitar la ruta histórica española y para
los casos siguientes. Se limpian cookies entre casos y se comprueba la URL
inglesa al final del caso; no se cambió el middleware de producción para
acomodar el test.

Se repitieron exclusivamente los casos fallidos, sin rehacer el lote completo:

```sh
.venv/bin/python -m pytest -q --lf
# 64 passed in 33.48s
```

Balance: **519 comprobaciones validadas**, sin fallos pendientes en este lote.
Incluye las 46 rutas nuevas, canonical/locale/FAQ/Article, rechazo de país e
idioma incorrectos, redirecciones, enlaces de silo, sitemap/mapa del sitio,
igualdad de precios con CSV/JSON, marcas de datos derivados y falta de fuentes.
No se ha ejecutado la suite completa del repositorio ni se ha validado el sitio
en producción. Las dependencias se instalaron en `.venv` sin modificar los
archivos de requisitos del proyecto.
