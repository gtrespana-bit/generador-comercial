# Inventario del trabajo — base de datos de partidas

Estado a 16/08/2026. Todo vive en `basedatos_partidas/`, carpeta **externa e
independiente** del código de la aplicación. No se ha modificado ni un archivo
del proyecto.

## Cifras

| | |
|---|---:|
| Partidas | **120** |
| Hojas de descompuesto `.xlsx` | 120 |
| Partidas con producto de elección del cliente | 8 |
| Recursos en el cuadro de precios | **78** |
| — mano de obra / materiales / maquinaria | 10 / 42 / 12 |
| — precios confirmados / provisionales | 10 / 54 |
| Clasificación | 18 capítulos · 74 subcapítulos · 41 grupos |
| — capítulos con partidas / vacíos | 6 / 12 |
| Moneda | USD (Venezuela) |

**Validación**: las 120 partidas pasan `es_formato_cype_xlsx` y `analizar_cype_xlsx`
del proyecto. El catálogo masivo se detecta con **8 campos, 0 errores, 0 advertencias**.

---

## Los 3 archivos que se editan a mano

| Archivo | Qué es |
|---|---|
| `datos/recursos.json` | **Cuadro de precios.** Fuente única de verdad. 50 recursos con código, unidad, descripción, precio y estado. |
| `datos/clasificacion.json` | **Taxonomía.** Los 18 capítulos con sus subcapítulos y grupos. Define el árbol de la barra lateral. |
| `datos/descompuestos/*.json` | **Una partida por archivo.** Título, descripción, margen y lista de recursos con su rendimiento. |

`datos/partidas.csv` **no se edita**: lo regenera el generador.

## Los 3 programas

| Programa | Qué hace |
|---|---|
| `descompuestos.py` | Motor principal. Resuelve recursos, valida la jerarquía, calcula la cascada de costes, escribe las hojas `.xlsx`, el maestro y el árbol. Comprueba cada archivo contra el lector del proyecto. |
| `construir.py` | Genera el catálogo masivo (`.csv`, `.xlsx`, `.json`) y lo valida con el importador real. |
| `precios.py` | `exportar` / `aplicar`. Actualización de precios en bloque, ordenada por impacto, con copia de seguridad. |

## Lo que se sube a la aplicación

| Archivo | Destino |
|---|---|
| `salida/descompuestos/*.xlsx` | Una a una, con descomposición y rendimientos completos |
| `salida/catalogo_partidas.xlsx` | Carga masiva del catálogo (Partidas → Importar) |
| `salida/arbol_catalogo.json` | Futuro: árbol de la barra lateral |
| `salida/precios_para_revisar.csv` | Plantilla para recoger precios de proveedor |

---

## Capítulo D · Demoliciones — **CERRADO**

98 partidas en 13 subcapítulos y 42 grupos.

| Sub | Nombre | Part. | Grupos |
|---|---|---:|---|
| DD | Cimentaciones | 3 | DDS zapatas · DDM vigas y muros · DDL losas |
| DE | Estructuras | 6 | DEC concreto (4) · DEA metálica · DEM madera |
| DF | Fachadas | 4 | DFF muros · DFL ligeros · DFD defensas (2) |
| DP | Particiones | 5 | DPT tabiquería (5) |
| DL | Carpintería y vidrios | 6 | DLP puertas (2) · DLV ventanas · DLC rejas · DLA closets · DLG vidrios |
| DH | Remates | 3 | DHR alféizares, dinteles y pasamanos |
| DI | Instalaciones | 8 | DIS aparatos (3) · DIF agua · DIE eléctrica (2) · DIC clima · DII iluminación |
| DN | Aislamientos e impermeabilizaciones | 3 | DNI impermeabilizaciones (2) · DNA aislamientos |
| DQ | Cubiertas | 6 | DQI inclinadas (3) · DQP planas · DQC canales (2) |
| DR | Revestimientos y trasdosados | 42 | DRS (16) · DRC (5) · DRF (5) · DRT (5) · DRR (3) · DRD (3) · DRE (3) · DRQ (2) |
| DS | Equipamiento | 4 | DSC cocinas (2) · DSB baños · DSM mobiliario fijo |
| DU | Urbanización de la parcela | 4 | DUC cerramientos (2) · DUJ jardinería · DUI instalaciones |
| DM | Firmes y pavimentos exteriores | 4 | DMP pavimentos (3) · DMB brocales |

## Otros capítulos en curso

| Cap | Partidas | Estado |
|---|---:|---|
| F · Fachadas y particiones | 2 | FFB bloque · FBY yeso laminado |
| I · Instalaciones | 7 | IFT · IFA · IFL · IST · ISA · IEC · IEM |
| R · Revestimientos | 10 | RSA · RSG (2) · RSD · RAG · RPF · RII · RIM · RIP · RTY |
| S · Equipamiento | 2 | SBA inodoro y lavamanos |
| G · Gestión de residuos | 1 | GTR retiro de escombro |

## Cadena de generación

```
datos/recursos.json ─┐
datos/clasificacion.json ─┼─► descompuestos.py ─► salida/descompuestos/*.xlsx
datos/descompuestos/*.json ─┘                  ├─► datos/partidas.csv
                                               └─► salida/arbol_catalogo.json
                                                        │
                              datos/partidas.csv ──► construir.py ─► salida/catalogo_partidas.*
```

Orden de ejecución:

```bash
python3 basedatos_partidas/descompuestos.py
python3 basedatos_partidas/construir.py
```

---

## Documentos de apoyo

| Archivo | Contenido |
|---|---|
| `README.md` | Manual completo: formatos, campos, cadena de generación |
| `COMPARATIVA_NUESTRAS_VS_CYPE.md` | Calibración de nuestros rendimientos contra CYPE |
| `COMPARATIVA_SOLADO_PORCELANICO.md` | Misma partida en Andalucía, Extremadura y CYPE |
| `ENLACES_BASES_DE_PRECIOS.md` | Enlaces a las bases públicas españolas |

---

## Lo que falta

1. **40 precios de material provisionales.** Es lo más urgente: en Venezuela el
   material pesa mucho más que la mano de obra. Empezar por los 10 de más impacto
   que lista `precios.py exportar`.
2. **14 capítulos vacíos**: carpintería, cielos rasos, sanitarios, cubiertas,
   impermeabilizaciones, gestión de residuos, seguridad y salud…
3. **Barra lateral**: el `arbol_catalogo.json` ya está, falta el front.
