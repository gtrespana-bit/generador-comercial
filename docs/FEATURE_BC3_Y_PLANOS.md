# Feature: Import BC3 y Medición automática sobre planos

Actualizado: 2026-08-23
Rama: arena/01a030f2-generador-comercial

## Resumen ejecutivo

Se implementan los dos puntos de mayor ROI para España sin cambiar de nicho:

1. **Import BC3 (FIEBDC-3)** - el reformista recibe el .bc3 del arquitecto y lo convierte en presupuesto CotizaT
2. **Planos con detección geométrica automática** - localiza estancias en PNG/JPG/WEBP, guarda sus áreas y permite corregirlas sin API externa ni coste por uso

Ambos mantienen el posicionamiento honesto: seguimos siendo software de reforma residencial/comercial, no de licitación pública completa.

## 1. Import BC3

### Qué hace
- Acepta `.bc3` en `/presupuestos/importar` y en el importador embebido del editor (`/presupuestos/nuevo`)
- Detecta encoding: UTF-8, Windows-1252, ISO-8859-1, CP850 (BCCA Andalucía viene en ANSI)
- Parsea registros: `~V`, `~K`, `~C`, `~D`, `~T`, `~M`
- Construye árbol capítulos (`#`) -> partidas a partir de `~D`
- Extrae mediciones `~M` con desglose: comentario \ uds \ long \ lat \ alt
- Calcula costes materiales/mano obra por tipo de concepto (1=mano obra, 3=materiales)
- Guarda .bc3 original en storage privado y manifiesto JSON para auditoría

### Límites
- MAX 10.000 conceptos, 5.000 partidas, 8 MB (protección contra volcar base completa BCCA 6.600 precios)
- Si BC3 es base completa, se limita a primeras 5.000 partidas con advertencia

### Estructura devuelta
```json
{
  "formato": "bc3",
  "capitulos_detectados": 2,
  "conceptos_detectados": 120,
  "filas": [
    {
      "codigo": "02.01",
      "capitulo": "REVESTIMIENTOS",
      "nombre": "Solado porcelánico 60x60",
      "descripcion": "Texto largo ~T",
      "unidad": "m2",
      "cantidad": 84.6,
      "precio": 38.5,
      "costes": {"materiales": 1.95, "mano_obra": 4.88},
      "mediciones": [{"concepto": "Cocina", "cantidad": 50}]
    }
  ]
}
```

### Flujo de código
- `app/services/bc3.py`: parser puro, sin dependencias externas
  - `es_formato_bc3()`: heurística rápida
  - `parse_bc3()`: registros -> conceptos, textos, descomposiciones, mediciones
  - `_construir_arbol_capitulos()`: BFS desde raíces ##/#
  - `analizar_bc3()`: convierte a filas CotizaT
  - `exportar_presupuesto_bc3()`: genera BC3 básico compatible con Presto/Arquímedes/Buildgets
- `app/routers/presupuestos.py`:
  - `_guardar_importacion_bc3()` y `_cargar_importacion_bc3()` (mismo patrón que CYPE)
  - `analizar_importacion_presupuesto()` ahora acepta `.bc3` y detecta BC3 en texto pegado
  - `_datos_bc3_desde_payload()` y `_anexar_filas_bc3()` para confirmar
  - `exportar_presupuesto()` con `?formato=bc3`

### Export BC3 (extra)
Aunque la recomendación inicial era solo import, se añade export básico para cerrar el ciclo:
- ~V, ~K, ~C capítulos y partidas, ~T descripción, ~D capítulo->partida y partida->recursos, ~M mediciones
- Encoding Windows-1252 (compatible Presto)
- Sin certificaciones ni residuos ~R (licitación pública completa queda fuera)

### Tests
- `tests/test_bc3.py`: 3 tests de formato, árbol y costes

### Coste
- 0€ licencia. FIEBDC es estándar abierto.
- Solo horas dev (40-60h export, 60-80h import) + mantenimiento encoding.

## 2. Planos con detección automática y ajuste manual

### Flujo principal
- Sube PNG, JPG o WEBP (12 MB máx., 20 planos por presupuesto).
- Tras la subida, el primer paso es **calibrar**: se marca una cota conocida y se escribe su medida real. El análisis de estancias va después, ya en metros.
- El servicio detecta espacios claros cerrados, crea un polígono editable por estancia y lo persiste inmediatamente como `PlanoMedicion` de tipo `area`.
- La lista, el lienzo y `GET /planos/{id}/datos` recuperan esas mismas geometrías después de recargar o volver otro día.
- «Repetir análisis» vuelve a procesar el archivo, pero deduplica los candidatos ya guardados mediante solapamiento de sus cajas; no crea copias en cada ejecución.
- El usuario calibra una distancia conocida para convertir píxeles a metros y m². Las mediciones existentes se recalculan en cascada.

### Cómo funciona el detector
`app/services/planos.py` implementa visión geométrica determinista con Pillow y biblioteca estándar:
1. reduce temporalmente la imagen a un máximo de 1100 px;
2. calcula umbral adaptativo Otsu sobre escala de grises;
3. **borra cotas y números** (dígitos, ticks y líneas de acotación) para que no se lean como tabiques;
4. reconoce muros horizontales, verticales y **diagonales**, y solo puentea huecos de puerta entre tramos con entidad;
5. segmenta por componentes conectados los espacios claros que no tocan el borde;
6. filtra ruido por área, dimensiones, proporción y ocupación;
7. simplifica el polígono y alinea ángulos casi ortogonales, conservando las diagonales reales.

El proceso no envía planos ni datos a terceros, no usa un modelo generativo y no tiene coste por página. Es una detección de geometría, no una interpretación semántica: las etiquetas iniciales son `Estancia N`. El usuario hace clic en el recinto, escribe el nombre y se guarda.

### Ajuste manual y conservación
- Línea (m), área (m²), perímetro (m) y conteo (ud) siguen disponibles como alternativa y para corregir detecciones.
- Una medición válida se **autoguarda**: el primer guardado usa `POST` y cada punto, etiqueta o color posterior usa `PUT` sobre el mismo registro.
- Los primeros puntos todavía incompletos se conservan como borrador en `localStorage`; al recargar se recuperan.
- Cambiar de herramienta finaliza primero un trazo válido. Un borrador incompleto no se descarta sin confirmación.
- El doble clic ignora puntos consecutivos prácticamente idénticos, cierra área/perímetro y confirma el guardado.
- «Editar geometría» carga una medición persistida en el lienzo; sus cambios recalculan valor y unidad en el servidor.
- Mínimos validados también en servidor: 2 puntos para línea, 3 para área/perímetro/volumen y 1 para conteo.
- Aplicar una medición a partida crea la `Medicion` correspondiente en el presupuesto.

### Formatos y límites
- PNG/JPG/WEBP: medibles y analizables directamente.
- PDF: se convierte a PNG si PyMuPDF está instalado. Sin ese extra, el PDF se conserva y se puede descargar, pero la interfaz pide una versión PNG/JPG para analizar y medir con fiabilidad.
- Máximo de 30 candidatos por análisis y 500 mediciones por plano.
- El algoritmo favorece plantas con paredes contrastadas y principalmente horizontales/verticales. Planos borrosos, perspectivas, muros diagonales o recintos realmente abiertos pueden requerir corrección manual.

### Modelos y endpoints
- `PlanoObra`: presupuesto, archivo privado, dimensiones y calibración.
- `PlanoMedicion`: tipo, etiqueta, valor, unidad, geometría JSON, partida destino y color.
- No ha sido necesaria una migración nueva: las detecciones reutilizan el modelo persistente existente.
- `POST /planos/{id}/detectar`: analiza, deduplica y guarda candidatos.
- `POST /planos/{id}/mediciones`: crea el primer estado válido de un trazo.
- `PUT /planos/{id}/mediciones/{mid}`: actualiza geometría y recalcula el valor.
- `GET /planos/{id}/datos`: devuelve plano y todas las mediciones persistidas.
- Se mantienen calibración, aplicación a partida, renombrado, borrado y exportaciones CSV/DXF/PNG/PDF.

### Tests
`tests/test_planos.py` cubre 17 escenarios, entre ellos detección con huecos de puerta, análisis HTTP, deduplicación, persistencia tras recarga, creación/actualización geométrica, rechazo de polígonos incompletos y exportaciones.

### Coste
- 0 € recurrente: Pillow ya forma parte de las dependencias y no se llama a ninguna API de visión.
- PyMuPDF continúa siendo opcional para convertir PDFs a imagen.

## SEO / Copy

Actualizado `app/seo_contenido.py` ES:
- Antes: "CotizaT no exporta BC3 ni lee planos..."
- Ahora: "CotizaT importa BC3 de arquitectos y bases como BCCA... También detecta estancias y guarda mediciones editables sobre planos, sin enviar el archivo a una API externa... Si trabajas licitación pública que exige exportar BC3 con certificaciones y residuos, aún no es tu software; si haces reforma que recibe BC3 del arquitecto, el flujo es el que ya usas."

Mantiene honestidad y convierte mejor.

## Por dónde empezar (recomendación implementada)

1. BC3 import (ya hecho): permite al reformista decir "sí, traé el BC3 del arquitecto"
2. Planos con detección geométrica, autoguardado y ajuste manual (ya hecho): diferenciador sin coste por página.
3. Próximo: validar el detector con planos reales variados y, si hay demanda, mejorar export BC3 con descomposición completa y luego certificaciones.

## Checklist operación

- [x] Parser BC3 puro
- [x] Integración importador tabular + CYPE + BC3
- [x] Export BC3 básico
- [x] Modelos planos + RLS
- [x] Servicios planos
- [x] Router planos
- [x] Template canvas interactivo
- [x] Migración Alembic
- [x] Tests BC3 y planos
- [x] Botón BC3 en detalle presupuesto y botón Planos
- [x] Copy SEO actualizado
- [ ] Probar con BC3 real BCCA2023_V02.zip (descargar y probar en local)
- [ ] Instalar PyMuPDF en producción si se quieren PDFs directos

## Cómo probar

```bash
# BC3
python -m pytest tests/test_bc3.py -v
# Crear sample.bc3 y subir en /presupuestos/importar

# Planos
python -m pytest tests/test_planos.py -v
# Ir a /presupuestos/{id}/planos → marcar una cota → aplicar escala → analizar estancias → clic y nombrar
```

---

## Actualización 2026-08-23: visor global + opciones premium

### Visibilidad
- `GET /planos`: galería global de todos los planos de la organización, agrupados por presupuesto, con miniaturas, estadísticas y enlaces profundos `?plano=<id>`.
- Entrada «Planos» en el sidebar, en la cabecera de Presupuestos, acción por fila, botón en la barra del editor y enlace desde el área de medición.

### Área de medición (premium)
- **Snap ortogonal**: fijo con casilla o manteniendo Mayús; restringe el siguiente punto a horizontal/vertical del anterior.
- **Snap a vértices**: magnetismo a puntos de mediciones guardadas (umbral 8 px de pantalla, independiente del zoom), con anillo indicador.
- **Línea elástica**: previsualización en vivo del siguiente segmento y del cierre del polígono.
- **Paneo**: botón central del ratón siempre, o herramienta ✋ Mover.
- **Atajos**: L/A/P/C/E/M cambian herramienta, Ctrl+Z deshace punto, Esc cancela.
- **Pantalla completa** del lienzo (⛶⛶) y **descarga PNG** del plano con las mediciones dibujadas.
- Barra de estado con coordenadas del cursor (m o px), zoom y medición en curso.
- Renombrado de mediciones (✏️), totales por unidad, mostrar/ocultar mediciones.

### Exportaciones
- **CSV** (`/presupuestos/{id}/planos/exportar?formato=csv`): todas las mediciones del presupuesto, `;` + BOM para Excel ES.
- **DXF** (`/planos/{id}/exportar?formato=dxf`): ASCII R12 solo ENTITIES, coordenadas en metros (Y invertida, origen abajo-izquierda), capa por tipo (`MED_LINEAL_M`, `MED_AREA_M`, …) y etiquetas como TEXT. Abre en AutoCAD/LibreCAD/BricsCAD.
- **PNG**: descarga del lienzo con mediciones (client-side).
- **PDF**: con «Incluir anexos» activo, `pdf_planos` genera un anexo en memoria (imagen del plano + mediciones superpuestas + tabla) que entra por el circuito estándar de `pdf_anexos` (índice, tope 4 MB, degradación elegante).

### Fix crítico incluido
- `_ALLOWED_CATEGORIES` de `app/storage.py` no incluía `planos`: toda subida fallaba con «No se pudo guardar el plano». Corregido y cubierto con test de subida real.

### Tests
- La cobertura original de 13 pruebas (geometría, visor, deep-link, CSV, DXF, renombrado y anexo PDF) se amplía a 22: detector sin tratar cotas como muros, ángulos diagonales, métricas de estancia, calibración previa al análisis y altura libre.

---

## Actualización 2026-08-23: calibrar primero, cotas ≠ tabiques

Feedback de uso: el detector era peor que no tener nada. Confundía números de cota con muros, no respetaba ángulos y la recalibración estaba escondida. El flujo queda así:

1. **Recalibrar plano** (paso 1, visible y obligatorio en la práctica). Dos clics sobre una medida ya acotada + valor real + altura libre (2,50 m). Toda cantidad posterior sale de esa escala.
2. **Detectar estancias**. Ya no se lanza al subir. Ignora dígitos, ticks y líneas de cota; reconoce tabiques también a 45°/135°; solo puentea huecos de puerta entre tramos con entidad.
3. **Clic en la estancia**. Se selecciona, se escribe el nombre y se guarda solo. En el panel aparecen automáticamente:
   - m² de suelo (área del polígono);
   - perímetro cerrado;
   - m² de paredes = perímetro × altura libre.

Límites honestos: no lee el nombre impreso en el plano ni resta huecos de puertas/ventanas. Un recinto abierto o un plano borroso sigue pidiendo ajuste manual.

Código: `app/services/planos.py` (`_borrar_anotaciones_cotas`, `_pintar_run_direccion`, `_ortogonalizar_poligono`, `metricas_estancia`), `POST /planos/{id}/altura`, `PlanoObra.altura_libre_m`.
