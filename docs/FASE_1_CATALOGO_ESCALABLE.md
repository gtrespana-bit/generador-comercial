# Fase 1 — Catálogo preparado para 5.000 partidas

**Estado:** completada el 16/08/2026
**Objetivo:** que el volumen del catálogo no degrade la apertura, navegación,
búsqueda ni inserción de partidas.

## Problema de partida

El editor enviaba al navegador, para cada partida:

- descripción técnica completa;
- cuatro grupos de costes;
- notas, proveedor, tiempos e imagen;
- toda la descomposición JSON.

Además, la plantilla generaba una segunda lista HTML con las mismas partidas y
el árbol creaba todas las hojas en el DOM al arrancar. Con 540 partidas, la
página de un presupuesto superaba 3,3 MB sin comprimir. La extrapolación a
5.000 partidas no era aceptable.

La pantalla de gestión `/partidas` también renderizaba el catálogo entero de
una sola vez.

## Solución implantada

### 1. Índice ligero inicial

El presupuesto recibe únicamente:

- id, nombre, precio y unidad;
- capítulo, subcapítulo y apartado;
- código actual, código anterior y código de clasificación;
- usos y fecha de último uso;
- un tesauro compacto de búsqueda.

No viajan descripciones completas, costes, notas ni descompuestos. También se
eliminó la lista HTML duplicada que existía detrás del buscador.

### 2. Ficha completa bajo demanda

Nuevo endpoint autenticado:

```text
GET /partidas/{id}/ficha
```

La ficha se solicita solo cuando el usuario:

- mantiene el cursor para abrir el preview;
- inserta la partida;
- necesita sus costes o su descomposición.

El navegador conserva una caché por id y comparte las peticiones en curso: una
misma ficha no se descarga dos veces durante la sesión.

### 3. Árbol progresivo

Al abrir el editor se crean únicamente las ramas de capítulo, subcapítulo y
apartado. Las hojas de partida se construyen al abrir el apartado. Una búsqueda
solo renderiza las hojas coincidentes.

El botón «Abrir» despliega capítulos y subcapítulos, pero no fuerza la creación
de las 5.000 hojas.

### 4. Búsqueda híbrida

El índice incluye un tesauro normalizado y compacto para resultados
instantáneos. Además, la búsqueda consulta bajo demanda:

```text
GET /partidas/api/buscar?q=...&limite=...
```

El servidor busca también en la descripción completa, proveedor, ruta y códigos.
El árbol y Spotlight fusionan los resultados locales y remotos sin duplicados.

Cuando ambos niveles devuelven cero resultados se registra una única métrica de
la consulta mediante:

```text
POST /partidas/api/busqueda-sin-resultados
```

Esto permite detectar familias faltantes antes de depender de una queja del
cliente.

### 5. Inserción y generador asíncronos

Arrastrar, hacer doble clic, pulsar `Enter`, usar Spotlight o generar un
borrador esperan la ficha completa antes de crear la línea. Por tanto, la línea
conserva descripción, costes, tiempos y descomposición aunque el índice inicial
sea ligero.

### 6. Gestión paginada

`/partidas` presenta 100 partidas por página y mantiene búsqueda global en el
servidor. Las operaciones sobre la página siguen funcionando, mientras las
exportaciones continúan incluyendo el catálogo completo.

## Prueba sintética de 5.000 partidas

El comando reproducible `.venv/bin/python tools/benchmark_catalogo_escalable.py`
levanta una SQLite temporal con 5.000 partidas, cada una con descripción y
descomposición. Resultado en `TestClient`, sin caché de navegador:

| Pantalla | Resultado |
|---|---:|
| Apertura del editor | **1,245 s** |
| HTML del editor sin comprimir | **3.479.606 bytes** |
| Registros del índice | **5.000** |
| Apertura de `/partidas` | **0,110 s** |
| HTML de gestión | **519.405 bytes** |
| Filas renderizadas en gestión | **100** |

La respuesta real viaja además bajo `GZipMiddleware`, por lo que el tamaño de
transferencia es inferior al HTML sin comprimir medido en la prueba.

Con las 540 partidas actuales, el HTML del editor bajó de aproximadamente 3,33
MB a menos de 1 MB en la regresión automatizada.

## Validación

- 477 tests superados y 6 omitidos por requerir PostgreSQL administrativo.
- JavaScript validado con `node --check`.
- 63 plantillas Jinja parseadas.
- 42 dependencias directas coherentes con el lock.
- Auditoría de datos sensibles: sin hallazgos.
- Pruebas nuevas verifican índice ligero, ficha bajo demanda, búsqueda en
  descripción y paginación de 100 filas.

## Siguiente fase

Implantar ocultación/restauración de partidas oficiales por organización y
actualización incremental: una partida ocultada no debe reaparecer, mientras
las nuevas partidas oficiales sí deben incorporarse automáticamente.
