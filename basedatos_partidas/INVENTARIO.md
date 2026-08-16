# Inventario del trabajo — base de datos de partidas

Estado a 16/08/2026. Todo vive en `basedatos_partidas/`, carpeta **externa e
independiente** del código de la aplicación. No se ha modificado ni un archivo
del proyecto.

## Cifras

| | |
|---|---:|
| Partidas | **27** |
| Hojas de descompuesto `.xlsx` | 27 |
| Partidas con producto de elección del cliente | 8 |
| Recursos en el cuadro de precios | **64** |
| — mano de obra / materiales / maquinaria | 10 / 42 / 12 |
| — precios confirmados / provisionales | 10 / 54 |
| Clasificación | 18 capítulos · 74 subcapítulos · 41 grupos |
| — capítulos con partidas / vacíos | 6 / 12 |
| Moneda | USD (Venezuela) |

**Validación**: las 27 partidas pasan `es_formato_cype_xlsx` y `analizar_cype_xlsx`
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

## Las 14 partidas

### D · Demoliciones
| Código | Ud | Partida | Horas | Coste | Venta |
|---|---|---|---:|---:|---:|
| DRS010 | m² | Demolición de pavimento cerámico y capa de agarre | 0,530 | 3,55 | 4,62 |

### F · Fachadas y particiones
| Código | Ud | Partida | Horas | Coste | Venta |
|---|---|---|---:|---:|---:|
| FBY010 | m² | Tabique autoportante PYL 15+70+15, doble placa | 0,700 | 40,31 | 52,40 |

### I · Instalaciones
| Código | Ud | Partida | Horas | Coste | Venta |
|---|---|---|---:|---:|---:|
| IFT010 | m | Tubería de agua PPR 20 mm empotrada, con roza y resane | 0,460 | 5,73 | 7,45 |
| IST010 | m | Tubería de desagüe PVC sanitario 4" | 0,410 | 8,49 | 11,04 |
| IEC010 | m | Canalización conduit 20 mm + conductor 12 AWG | 0,340 | 6,44 | 8,37 |
| IEM010 ⊕ | ud | Punto de interruptor o tomacorriente | 0,330 | 6,71 | 8,72 |

### R · Revestimientos y trasdosados
| Código | Ud | Partida | Horas | Coste | Venta |
|---|---|---|---:|---:|---:|
| RSA010 | m² | Recrecido autonivelante 5 mm | 0,300 | 6,17 | 8,02 |
| RSG010 ⊕ | m² | Pavimento cerámico/porcelanato formato estándar | 0,600 | 7,05 | 9,17 |
| RSG020 ⊕ | m² | Pavimento porcelanato gran formato | 0,900 | 9,62 | 12,51 |
| RSD010 ⊕ | m | Rodapié cerámico o porcelanato | 0,165 | 1,30 | 1,69 |
| RAG010 ⊕ | m² | Alicatado de paramento interior | 0,780 | 8,36 | 10,87 |
| RIP010 | m² | Preparación de paramento para pintura | 0,220 | 2,17 | 2,82 |
| RII010 ⊕ | m² | Pintura de caucho mate, dos manos | 0,255 | 2,66 | 3,46 |
| RIM010 | m² | Esmalte sintético sobre carpintería | 0,420 | 4,02 | 5,23 |

⊕ = no incluye el material de acabado que elige el cliente.
Venta = coste directo × 1,30.

---

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
