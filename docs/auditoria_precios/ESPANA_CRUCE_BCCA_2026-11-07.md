# Cruce real del catálogo español con BCCA

Se cruzaron los **388** recursos de CotizaT con una copia íntegra del archivo `basicos.json` de [CERP Tech, banco abierto de ítems](https://github.com/cerptech/cerp-items-data), versión 0.7.0 y commit `1e27f53db7debd948bb132b3b9d2cadd69144a13`. Su licencia declara: **«Información obtenida del Portal de la Junta de Andalucía»** y atribuye su estructura, curación y pipeline a CERP Tech. La fuente de precios indicada en los registros es BCCA, edición **enero 2024**, ámbito **Andalucía**. El catálogo fue generado en noviembre de 2026, pero **eso no actualiza los precios**: muchos registros identifican precios de 2021 y 2022. Es una copia derivada de un tercero, no el BC3 original descargado de la Junta; los detalles y exactitud de cada elemento deben contrastarse.

- Archivo `basicos.json`: SHA-256 `b690c51034825f0435cfd6769dfc4e01bd51f80c5f8033123c6d4e1e918a3179`, igual al manifest `index.json` del bundle.
- Contiene 6.131 elementos; el filtro conservador acepta **5.656** elementos de materiales, maquinaria o mano de obra, con una sola tarifa positiva en euros, origen BCCA/Andalucía y unidad reconocida. Excluye auxiliares, otros, descomposiciones, tarifas múltiples y unidades no reconocidas; no realiza conversiones automáticas.
- **359** recursos tienen al menos una coincidencia textual y de unidad; **29** no. El archivo [de candidatos](espana_candidatos_bcca_2026-11-07.csv) contiene **1.637** propuestas, hasta cinco por recurso. Son sugerencias, no 359 equivalencias comprobadas.
- En cada fila se conserva el código, descripción, precio, edición y fecha de precio que declara el dataset; no se han aplicado precios ni cambiado estados automáticamente. Su similitud textual puede dar falsos positivos graves. Ejemplo: el primer candidato del perno de anclaje es un taco químico, no necesariamente equivalente; el de pasta de juntas no incluye cinta; el andamio incluye montaje. La coincidencia de números es orientativa, no una verificación dimensional.
- La fuente atribuye a BCCA registros con códigos de formatos heterogéneos; no se ha comprobado todo el conjunto contra la publicación oficial. Dos referencias puntuales (`FB00600` 0,79 y `FP01800` 1,17) aparecen también en el [cuadro oficial de 2023](https://www.juntadeandalucia.es/sites/default/files/inline-files/2023/07/BCCA2023_CUADRO%20DE%20PRECIOS%20BASICOS.pdf). Esto no valida las demás.

## Reproducción

```sh
curl -fL 'https://codeload.github.com/cerptech/cerp-items-data/tar.gz/1e27f53db7debd948bb132b3b9d2cadd69144a13' -o /tmp/cerp.tar.gz
mkdir -p /tmp/cerp && tar -xzf /tmp/cerp.tar.gz -C /tmp/cerp
sha256sum /tmp/cerp/cerp-items-data-1e27f53db7debd948bb132b3b9d2cadd69144a13/basicos.json
python tools/cruzar_precios_cerp.py /tmp/cerp/cerp-items-data-1e27f53db7debd948bb132b3b9d2cadd69144a13/basicos.json --salida /tmp/candidatos.csv
```

El archivo fuente íntegro no se incorpora al repositorio. La lista resultante es una tabla de revisión, no una orden de carga. Falta cotejar equivalencia, condiciones fiscales y de suministro y una fuente actual comparable antes de actualizar precios; en maquinaria y mano de obra también alcance de operario, energía y coste empresarial. No promediar con 2026 como si las fechas fueran simultáneas. Después contrastar rendimientos, no solo precios unitarios.
