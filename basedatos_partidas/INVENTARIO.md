# Inventario del trabajo — base de datos de partidas

Estado a 16/08/2026. Todo vive en `basedatos_partidas/`, carpeta **externa e
independiente** del código de la aplicación. No se ha modificado ni un archivo
del proyecto.

## Cifras

| | |
|---|---:|
| Partidas | **540** |
| Hojas de descompuesto `.xlsx` | 540 |
| Partidas con producto de elección del cliente | 69 |
| Recursos en el cuadro de precios | **311** |
| — mano de obra / materiales / maquinaria | 10 / 42 / 12 |
| — precios confirmados / provisionales | 10 / 54 |
| Clasificación | 20 capítulos · 121 subcapítulos |
| — capítulos con partidas / vacíos | **20 / 0** |
| Moneda | USD (Venezuela) |

**Validación**: las 540 partidas pasan `es_formato_cype_xlsx` y `analizar_cype_xlsx`
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

## Los 20 capítulos — CATÁLOGO CERRADO

| Cap | Nombre | Sub. | Partidas |
|---|---|---:|---:|
| 01 | Trabajos preliminares y provisionales | 5 | 24 |
| 02 | Demoliciones y desmontajes | 17 | 98 |
| 03 | Movimiento de tierras | 4 | 22 |
| 04 | Fundaciones | 5 | 25 |
| 05 | Estructuras | 6 | 35 |
| 06 | Paredes y tabiquería | 5 | 25 |
| 07 | Frisos y revestimientos de pared | 5 | 25 |
| 08 | Pisos y pavimentos | 8 | 39 |
| 09 | Cielos rasos | 5 | 11 |
| 10 | Impermeabilizaciones y aislamientos | 4 | 12 |
| 11 | Techos y cubiertas | 5 | 14 |
| 12 | Instalaciones sanitarias | 7 | 16 |
| 13 | Instalaciones eléctricas | 6 | 17 |
| 14 | Instalaciones mecánicas y especiales | 4 | 13 |
| 15 | Herrería, carpintería y vidrios | 7 | 24 |
| 16 | Pintura y acabados | 5 | 11 |
| 17 | Equipamiento y mobiliario fijo | 5 | 13 |
| 18 | Obras exteriores y urbanismo | 5 | 15 |
| 19 | Gestión de residuos y limpieza | 3 | 6 |
| 20 | Seguridad y salud en obra | 4 | 9 |
| | **TOTAL** | **121** | **540** |

Cobertura: **115/115 subcapítulos con contenido**.

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
