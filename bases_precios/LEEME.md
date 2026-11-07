# Bases de precios descargadas

Aquí van los bancos oficiales que **no** se versionan (decenas de MB y licencia
de la fuente). El contenido está ignorado por git salvo este archivo.

## Base de Precios de la Construcción de Extremadura 2026

- Página oficial: <https://www.juntaex.es/w/base-precios-construccion-2026>
- Documento: «Base de precios de la construcción de Extremadura 2026 en formato bc3»
- Enlace directo comprobado (7/11/2026):
  <https://www.juntaex.es/documents/77055/621768/BCEXTGREM_26_v1.bc3/8066c810-a694-eeed-c456-a64abca3cc2e?t=1782217730923>
- Nombre esperado del archivo: `BCEXTGREM_26_v1.bc3`
- Descarga guiada (valida FIEBDC-3, calcula sha256 y puede cruzar el catálogo):

```bash
python3 tools/descargar_banco_bc3.py --cruzar
```

El resto de archivos de esta carpeta (`*.bc3`, `*.csv`, `*.zip`, `*.pdf`) no se
suben al repositorio.
