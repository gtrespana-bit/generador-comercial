# EMPEZAR AQUÍ — estado del trabajo y siguiente paso

> Documento de traspaso. Si abres una ventana de chat nueva, lee esto primero
> y no vuelvas a levantar lo que ya está decidido.
>
> Última actualización: 16/08/2026, tras implantar la taxonomía numérica v2.

---

# 1. Qué es esto en una frase

Una base de datos de partidas de construcción **propia al 100 %**, para
**reforma y remodelación residencial en Venezuela**, en **USD**, que se importa
sin errores en CotizaT y que ya se usa desde una barra lateral en el editor de
presupuestos.

---

# 2. Estado a día de hoy

| | |
|---|---:|
| Partidas | **3.006** |
| Capítulos · subcapítulos · apartados con partidas | **18 · 172 · 256** |
| Recursos en el cuadro de precios | 392 |
| Validación con el importador real | **0 errores · 0 advertencias** |
| Tests del proyecto | **515 pasando · 6 omitidos** |

---

# 3. Reglas que NO hay que volver a discutir

1. **Terminología venezolana, siempre.** Concreto (no hormigón), friso (no
   enfoscado), cielo raso (no falso techo), piso (no solado), mesón (no
   encimera), **afirmado** (no contrapiso ni recrecido), plomero, granito
   vaciado en sitio. Está vigilado por `terminologia.py auditar`.
2. **CYPE no se toca.** Es un producto comercial vivo. Se rechazó extraerla por
   el derecho *sui generis* (art. 133 TRLPI) y por riesgo de competencia
   desleal si se copiara su codificación. Codificación propia visible
   `CC.SS.AA.NNN`; el antiguo `CT-CC-SS-NNN` solo queda como alias histórico.
3. **Mano de obra: no se baja.** Oficial 5,50 USD/h, ayudante especializado
   4,00, ayudante 3,50. Es una decisión de negocio del cliente: paga por encima
   del mercado por principio. Con esas tarifas al trabajador le llega el 16,5 %
   del precio de venta, frente al 6,5 % con tarifa de mercado.
4. **Alquiler de equipos: fuera de alcance.** Los 43 recursos de maquinaria se
   quedan como están por decisión expresa del cliente.
5. **El producto que elige el cliente no va dentro de la partida.** Cerámica,
   sanitarios, grifería, papel tapiz: se declaran en el bloque
   `producto_cliente` con su consumo, y se facturan aparte. 69 partidas lo usan.
6. **Sólo se atan al cemento las mezclas de obra.** Cuatro: pega 1:4, friso
   1:5, afirmado 1:6, estructural 1:3. El pego en saco, el premezclado y el
   autonivelante tienen precio propio e independiente.
7. **Modo de trabajo:** capítulo a capítulo y grupo a grupo, cerrando cada uno
   completo. Nada de saltar de un lado a otro. Cuando el cliente dice «hazlo
   todo de una», es ejecución masiva sin pedir confirmación.

---

# 4. Dónde está cada cosa

```
basedatos_partidas/
├── EMPEZAR_AQUI.md              ← este archivo
├── README.md                    manual completo (formatos, precios, terminología)
├── INVENTARIO.md                cifras y tabla de capítulos
├── USO_EN_LA_APLICACION.md      carga masiva, propagación de precios, barra lateral
├── datos/
│   ├── recursos.json            FUENTE ÚNICA DE PRECIOS
│   ├── clasificacion.json       18 capítulos · 172 subcapítulos · 147 apartados
│   ├── glosario.json            vocabulario venezolano
│   ├── contraste_mercado_2026-08.json   evidencia de precios con fuente
│   ├── mapa_migracion_v2.json   540 equivalencias de código v1 → v2
│   └── descompuestos/*.json     3.006 partidas, una por archivo
├── salida/                      540 .xlsx + catálogo + árbol (se regenera)
├── descompuestos.py construir.py    motor
├── precio.py                    cambiar UN precio (uso diario)
├── precios.py                   revisión en bloque
├── contraste.py                 volcar una ronda de contraste de mercado
├── terminologia.py              vocabulario
├── cobertura.py  equidad.py     informes
```

En la aplicación se tocó: `app/services/importer.py`, `app/main.py`,
`app/security.py`, `app/templates/budgets/form.html`,
`app/static/js/editor/arbol_catalogo.js` (nuevo), `.../editor/catalogo.js`,
`app/static/css/style.css`.

---

# 5. Órdenes que hay que conocer

```bash
# regenerar todo tras tocar datos
python3 basedatos_partidas/descompuestos.py && python3 basedatos_partidas/construir.py

# el cemento amaneció en 20 el saco: simula primero, aplica después
python3 basedatos_partidas/precio.py fijar MT-CEMENTO 20 --por-saco 42.5
python3 basedatos_partidas/precio.py fijar MT-CEMENTO 20 --por-saco 42.5 --aplicar

# ver qué depende de un recurso antes de tocarlo
python3 basedatos_partidas/precio.py ver MT-CEMENTO

# vocabulario
python3 basedatos_partidas/terminologia.py auditar

# avance
python3 basedatos_partidas/cobertura.py
python3 basedatos_partidas/equidad.py
```

Para levantar la aplicación con el catálogo cargado:

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
DATABASE_URL=sqlite:////tmp/cotizat_demo.db \
COTIZAT_FRAME_ANCESTORS="https://*.e2b.app 'self'" \
  .venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

`COTIZAT_FRAME_ANCESTORS` solo hace falta para verlo embebido en una vista
previa. Sin esa variable el comportamiento es el de producción:
`frame-ancestors 'none'`.

---

# 6. SIGUIENTE PASO — catálogo general extenso

La reorganización ya está implantada. Por decisión del titular, 800 y 1.500
son solo hitos internos: el mínimo general será de unas **3.000 partidas base**
y el objetivo amplio de **4.000–5.000**. La carga progresiva, ficha bajo
demanda, búsqueda híbrida y paginación ya están implantadas y probadas con
5.000 partidas. La ocultación/restauración por organización y las altas
incrementales también están implantadas. La matriz de 3.000/5.000 partidas y
el diccionario de sinónimos de 146 grupos ya cubren los 18 capítulos. El siguiente paso es
producir familias completas, comenzando por `09 Instalaciones`.

> **Progreso 17/08/2026:**
> - **Capítulo 12 Revestimientos y acabados** completo hasta el mínimo (401/400).
> - **Capítulo 07 Carpintería, herrería, vidrios y protección solar** completo
>   hasta el mínimo (180/180).
> - **Capítulo 10 Aislamientos e impermeabilizaciones** completo hasta el
>   mínimo (150/150).
> - **Capítulo 02 Demoliciones y desmontajes** completo hasta el mínimo (265/260).
> - **Capítulo 06 Fachadas y particiones** completo hasta el mínimo (180/180).
> - **Capítulo 01 Actuaciones previas** completo hasta el mínimo (100/100).
> - **Capítulo 03 Acondicionamiento del terreno** completo hasta el mínimo (80/80).
> - **Capítulo 04 Fundaciones** completo hasta el mínimo (100/100).
> - **Capítulo 05 Estructuras** completo hasta el mínimo (170/170).
> - **Capítulo 08 Remates y ayudas** completo hasta el mínimo (120/120).
> - **Capítulo 09 Instalaciones** completo hasta el mínimo (540/540).
> - **Capítulo 11 Techos y cubiertas** completo hasta el mínimo (130/130).
> - **Capítulo 13 Equipamiento, mobiliario y señalización** completo (140/140).
> - **Capítulo 14 Obras exteriores y urbanismo** completo hasta el mínimo (160/160).
> - **Capítulo 15 Gestión de residuos y limpieza** completo (50/50).
> - **Capítulo 16 Control de calidad y ensayos** completo (80/80).
> - **Capítulo 17 Seguridad y salud en obra** completo (60/60).
> - **Capítulo 18 Rehabilitación energética** completo (100/100).
> **Objetivo mínimo de 3.000 partidas alcanzado** (3.006, 0 errores, 0 advertencias).

La producción cerrará familias completas en este orden: `09 Instalaciones`,
`12 Revestimientos y acabados`, `07 Carpintería, herrería y vidrios`, `10/11
Impermeabilizaciones y techos`, y finalmente `08/16/18 Remates, control y
rehabilitación energética`. Los precios y recursos nuevos deben contrastarse
al mismo tiempo; no se añaden partidas con descompuestos de relleno.

## 6.1 Auditoría y cobertura referencial de lanzamiento

La auditoría integral del 20/08/2026 sustituyó las cifras anteriores, que se
habían quedado obsoletas con la ampliación a 3.006 partidas:

- las 3.006 partidas tienen mano de obra, oficio y rendimiento explícitos;
- CO/PE/MX/EC tienen 388/388 referencias nacionales cada uno;
- 73 precios proceden de observaciones directas y 1.479 son referencias
  derivadas de las canastas investigadas, siempre identificadas como tales;
- Venezuela conserva sus 388 precios base USD con nivel de confianza visible;
- 218 grupos (875 partidas) comparten APU y quedan identificados para revisión
  técnica progresiva; una coincidencia no es automáticamente un error.

La referencia es nacional, no por ciudad, y no pretende adivinar el precio
exacto de una tienda. Conserva rango, fecha, fuente y confianza según
`docs/METODOLOGIA_PRECIOS_REFERENCIA_LATAM.md`.

Informe y detalle exhaustivo:

- `docs/AUDITORIA_CATALOGO_PRELANZAMIENTO_2026-08-20.md`;
- `salida/auditoria_partidas.csv` (una fila por cada partida).

Antes de publicar debe pasar:

```bash
python3 basedatos_partidas/auditar_lanzamiento.py --strict
```

Las nuevas rondas de investigación actualizan las anclas y regeneran las
referencias derivadas. Nunca se oculta su origen ni se presentan como una
cotización exacta.

## 6.2 Prioridad 2: mirar la barra lateral con el ojo puesto

La barra lateral funciona y está verificada por respuesta HTTP, pero **no se ha
visto en un navegador real**. Queda por comprobar con la vista puesta:

- que la proporción de la rejilla (320 px de panel) no ahogue el presupuesto;
- que arrastrar desde el árbol no choque con el reordenado interno de
  capítulos, que usa el mismo `dragstart`;
- el comportamiento en pantalla estrecha (por debajo de 1100 px el panel pasa
  arriba, con 340 px de alto).

## 6.3 Prioridad 3 (pendiente de decisión del cliente)

- **Ámbito obra nueva.** No iniciado. Requiere el texto de **COVENIN 2000-2** y
  su **Suplemento N.º 1 de 1999**, que el cliente no tiene. La codificación
  cada partida conserva `ambito=reforma`; obra nueva tendrá una clasificación
  independiente cuando se disponga de la norma.
- **Alquiler de equipos.** 43 recursos, 997 USD. Congelado por decisión del
  cliente; solo se retoma si él lo pide.

---

# 7. Cosas que ya se probaron y NO hay que repetir

- **Descargar bases de precios españolas.** Andalucía y Extremadura no se
  pudieron bajar (sin red en bash), Madrid exige certificado digital español y
  Galicia exige registro. Está documentado en `ENLACES_BASES_DE_PRECIOS.md`.
- **Reutilizar la codificación de CYPE.** Descartado por riesgo legal. Además
  se comprobó que había colisiones reales: nuestro antiguo `DPT020` era un
  tabique de drywall y el `DPT020` de CYPE es una demolición.
- **Buscar «afirmado» en fuentes venezolanas.** No fue concluyente; lo que
  aparece es «afinado de piso». Se usa «afirmado» porque es la palabra del
  cliente. Cambiarlo es una orden: editar `datos/glosario.json` y ejecutar
  `terminologia.py aplicar`.
- **Aplicar «zócalo → rodapié» y «cazoleta → tragante» a ciegas.** Se comprobó
  que las 18 apariciones de zócalo y las de cazoleta eran todas correctas. Están
  en `_matizados` del glosario para que avisen sin marcar error.

---

# 8. Trampas conocidas del repositorio

- **El CI comprueba espacios finales** con `git diff --check`. El módulo `csv`
  de Python termina las líneas en `\r\n` por defecto y git lo marca como
  espacio final. Los tres escritores de CSV llevan ya `lineterminator="\n"`;
  si se añade otro, hay que ponérselo también. El BOM (`utf-8-sig`) sí se
  conserva: es lo que hace que Excel abra bien las tildes.
- **Renombrar el código de un recurso**: hay códigos que son prefijo de otros
  (`MO-OF1-SOL` solador vive dentro de `MO-OF1-SOLD` soldador). `terminologia.py`
  ya lo hace con límites de palabra; no sustituir códigos con un replace a secas.
- **La sesión puede perder el HEAD local** y volver al punto de partida aunque
  la rama remota esté completa. Antes de commitear, comprobar
  `git rev-parse HEAD` contra `git rev-parse origin/<rama>`; si no coinciden y
  el remoto va por delante, recuperar con `git reset --soft <tip remoto>`, que
  conserva el árbol de trabajo.
