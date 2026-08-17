# Propuesta de reorganización del catálogo de partidas

**Referencia de navegación:** Generador de Precios de CYPE, ámbito Rehabilitación  
**Propuesta propia:** estructura numérica, terminología venezolana y datos originales de CotizaT  
**Fecha:** 16/08/2026
**Estado:** aprobada; fases 0 y 1 implantadas el 16/08/2026

> **Implantado:** las 540 partidas ya usan `CC.SS.AA.NNN`, están mapeadas en
> 18 capítulos, 172 subcapítulos y 147 apartados con contenido. La base de
> datos, el actualizador versionado y el árbol de tres niveles ya están
> operativos. La siguiente fase es ampliar primero hasta unas 800 partidas.

---

## 1. Recomendación ejecutiva

Sí conviene reorganizar el catálogo. El problema no es solo visual: la clasificación actual se queda en dos niveles y mezcla varios criterios de organización. A veces el primer nivel representa una fase de obra, otras veces un material, un acabado o una especialidad. Eso obliga a recordar en qué lugar decidimos guardar cada cosa.

Mi recomendación es adoptar el **patrón de navegación de CYPE**, sin copiar su base de datos:

```text
01 Capítulo principal
└── 01.03 Subcapítulo
    └── 01.03.02 Apartado
        └── 01.03.02.010 Partida
```

Es decir: **tres niveles de clasificación y, debajo, las partidas**. Todos los niveles visibles usarán números, no letras.

Propongo además:

1. Reordenar las 540 partidas existentes sin perder ninguna.
2. Pasar de los 20 capítulos actuales a **18 capítulos principales más coherentes con el proceso constructivo**.
3. Incorporar un tercer nivel real, llamado **apartado**.
4. Mostrar siempre código, ruta y número de partidas en el árbol.
5. Ampliar primero el catálogo a unas **800 partidas útiles** y, en rondas posteriores, a un objetivo de **1.150–1.250 partidas**.
6. No crear cientos de duplicados por color, marca o acabado: esas variaciones deben seguir resolviéndose con productos/opciones.
7. Mantener código anterior, trazabilidad y vínculos de presupuestos durante la migración.

La idea no es «hacer una copia de CYPE con números». La idea es aprovechar lo que funciona de su sistema —capítulo, subcapítulo, apartado, partida y navegación progresiva— y construir una taxonomía propia para reforma y remodelación en Venezuela.

---

## 2. Diagnóstico del catálogo actual

### 2.1 Lo que ya está bien

El catálogo actual no es pequeño ni está vacío:

- **540 partidas** originales.
- **20 capítulos**.
- **121 subcapítulos**, todos con contenido.
- **311 recursos** en el cuadro de precios.
- Descompuestos, rendimientos, costes y precios vinculados.
- Códigos propios `CT-CC-SS-NNN`.
- Árbol lateral, buscador y arrastre al presupuesto ya operativos.

Por tanto, no recomiendo desechar lo existente. Hay una base valiosa que debe reclasificarse y ampliarse.

### 2.2 Dónde está el desorden

#### A. Solo hay dos niveles reales

La fuente de datos solo conoce:

```text
capítulo > subcapítulo > partida
```

La aplicación también persiste únicamente `categoría` y `subcategoría`. No existe todavía un apartado terciario. Al crecer el catálogo, algunos subcapítulos terminan siendo demasiado generales y otros excesivamente específicos.

#### B. El criterio cambia según el capítulo

Ejemplos:

- «Paredes y tabiquería» está separado de «Frisos y revestimientos de pared».
- «Pisos y pavimentos», «Cielos rasos» y «Pintura y acabados» son capítulos principales independientes.
- Las instalaciones están separadas en sanitarias, eléctricas y mecánicas.
- En demoliciones, en cambio, todo se agrupa bajo un único capítulo y se divide por sistema constructivo.

Ninguno de esos criterios es incorrecto por sí solo. El problema es que **no se aplica el mismo criterio en todo el árbol**.

#### C. Hay capítulos descompensados

Distribución actual destacada:

| Capítulo actual | Partidas |
|---|---:|
| Demoliciones y desmontajes | 103 |
| Pisos y pavimentos | 45 |
| Estructuras | 38 |
| Paredes y tabiquería | 38 |
| Frisos y revestimientos de pared | 31 |
| Herrería, carpintería y vidrios | 29 |
| Trabajos preliminares | 28 |
| Fundaciones | 28 |
| Instalaciones sanitarias | 21 |
| Instalaciones eléctricas | 22 |
| Instalaciones mecánicas y especiales | 15 |
| Pintura y acabados | 15 |
| Cielos rasos | 14 |
| Gestión de residuos y limpieza | 8 |

El catálogo está muy desarrollado en demoliciones, pero todavía es corto en instalaciones, impermeabilización, techos, cielos rasos, pintura, equipamiento, control de calidad y rehabilitación energética.

#### D. Los números no ayudan a navegar

Los códigos están en las partidas, pero el usuario navega principalmente por nombres. El árbol debería enseñar también:

- `09 Instalaciones`
- `09.03 Eléctricas`
- `09.03.04 Canalizaciones y cajas`
- `09.03.04.010 Canalización empotrada...`

Así el orden deja de depender del alfabeto y la ruta se entiende de un vistazo.

#### E. Crecer sin cambiar la estructura empeoraría el problema

Añadir otras 500 partidas al árbol actual aumentaría la cobertura, pero no la facilidad de uso. La reorganización debe hacerse **antes o al mismo tiempo que la ampliación**.

---

## 3. Qué tomar de CYPE y qué no tomar

### Sí tomar

- Navegación progresiva de **capítulo → subcapítulo → apartado → partida**.
- Separación de las grandes familias constructivas.
- Organización de demoliciones por el elemento que se elimina.
- Un capítulo común de instalaciones con especialidades debajo.
- Un capítulo común de revestimientos/acabados con sistemas debajo.
- Código visible que explique la posición de cada partida.
- Posibilidad de llegar a una partida navegando aunque no se recuerde su nombre.

### No tomar

- Sus letras de capítulo o códigos de partida.
- Sus descripciones, precios, rendimientos, recursos o descompuestos.
- Una reproducción literal de todos sus apartados, muchos de los cuales no son prioritarios para nuestro mercado.
- Terminología peninsular cuando el usuario venezolano espera otra palabra.
- Miles de combinaciones casi idénticas que dificulten más la búsqueda.

### Regla de propiedad del catálogo

La estructura será propia, numérica y adaptada. Los datos técnicos seguirán siendo originales de CotizaT. CYPE se usa como **referencia de experiencia de navegación**, no como fuente para clonar su banco de precios.

---

## 4. Nueva codificación numérica

### 4.1 Formato visible propuesto

```text
CC.SS.AA.NNN
```

| Segmento | Significado | Ejemplo |
|---|---|---|
| `CC` | capítulo principal | `09` Instalaciones |
| `SS` | subcapítulo | `09.03` Eléctricas |
| `AA` | apartado | `09.03.04` Canalizaciones y cajas |
| `NNN` | partida, en saltos de 10 | `09.03.04.010` Canalización empotrada |

Ejemplo completo:

```text
09 Instalaciones
└── 09.03 Eléctricas
    └── 09.03.04 Canalizaciones y cajas
        ├── 09.03.04.010 Canalización empotrada en pared
        ├── 09.03.04.020 Canalización superficial en tubería PVC
        └── 09.03.04.030 Caja de paso o derivación
```

### 4.2 Reglas de numeración

1. Todos los niveles visibles son numéricos.
2. Los capítulos, subcapítulos y apartados usan dos dígitos.
3. Las partidas usan tres dígitos y avanzan de diez en diez: `010`, `020`, `030`.
4. Se dejan huecos para insertar partidas futuras sin renumerar todo el catálogo.
5. Un código retirado no se reutiliza para otro concepto.
6. Reclasificar una partida no puede romper presupuestos antiguos.
7. La identidad técnica estable será el `id` de base de datos; el código expresa clasificación, no identidad histórica.
8. Durante la transición se conservará una tabla `código anterior → código nuevo`.

### 4.3 Prefijo de marca

Mi recomendación es que el usuario vea el código puramente numérico (`09.03.04.010`). Si en una exportación interesa marcar su origen, se puede presentar como `CT 09.03.04.010`, pero `CT` no formará parte de la jerarquía.

---

## 5. Propuesta de capítulos principales

La siguiente estructura conserva la lógica general de CYPE, pero usa orden, nombres y alcance propios.

| Código | Capítulo principal propuesto | Procedencia principal del catálogo actual | Objetivo orientativo |
|---:|---|---|---:|
| 01 | Actuaciones previas | Trabajos preliminares y provisionales | 40–50 |
| 02 | Demoliciones y desmontajes | Demoliciones y desmontajes | 120–140 |
| 03 | Acondicionamiento del terreno | Movimiento de tierras | 35–45 |
| 04 | Fundaciones | Fundaciones | 40–50 |
| 05 | Estructuras | Estructuras | 65–80 |
| 06 | Fachadas y particiones | Paredes, tabiquería y tratamientos de fachada | 70–85 |
| 07 | Carpintería, herrería, vidrios y protección solar | Herrería, carpintería y vidrios | 65–80 |
| 08 | Remates y ayudas | Conceptos hoy repartidos entre varios capítulos | 30–40 |
| 09 | Instalaciones | Sanitarias, eléctricas, mecánicas y especiales | 150–180 |
| 10 | Aislamientos e impermeabilizaciones | Impermeabilizaciones y aislamientos | 55–70 |
| 11 | Techos y cubiertas | Techos y cubiertas | 40–55 |
| 12 | Revestimientos y acabados | Frisos, pisos, cielos rasos y pintura | 170–210 |
| 13 | Equipamiento, mobiliario y señalización | Equipamiento y mobiliario fijo | 55–70 |
| 14 | Obras exteriores y urbanismo | Obras exteriores y urbanismo | 50–65 |
| 15 | Gestión de residuos y limpieza | Gestión de residuos y limpieza | 20–30 |
| 16 | Control de calidad y ensayos | Capítulo nuevo | 20–30 |
| 17 | Seguridad y salud en obra | Seguridad y salud | 25–35 |
| 18 | Rehabilitación energética | Capítulo nuevo | 25–40 |

**Objetivo final razonable:** aproximadamente **1.150–1.250 partidas**. No recomiendo intentar llegar ahí en una sola carga.

### Por qué 18 capítulos y no mantener los 20 actuales

- Sanitarias, eléctricas y mecánicas pasan a ser subcapítulos de `09 Instalaciones`.
- Frisos, pisos, cielos rasos y pintura pasan a familias dentro de `12 Revestimientos y acabados`.
- Se crean capítulos que hoy faltan: `08 Remates y ayudas`, `16 Control de calidad y ensayos` y `18 Rehabilitación energética`.
- La ruta se vuelve predecible: primero se piensa en el sistema constructivo, después en la familia y por último en la solución concreta.

---

## 6. Árbol propuesto: nivel secundario

Este es el mapa inicial de subcapítulos. En la implantación se documentará cada apartado terciario en `clasificacion.json`.

### 01 Actuaciones previas

- `01.01` Desconexión y aislamiento de servicios existentes
- `01.02` Inspecciones, levantamientos, catas y diagnóstico
- `01.03` Protección de elementos existentes
- `01.04` Cerramientos, barreras de polvo y control de accesos
- `01.05` Andamios y medios de elevación
- `01.06` Apeos, apuntalamientos y estabilización provisional
- `01.07` Replanteos y control geométrico
- `01.08` Instalaciones provisionales y servicios de obra

### 02 Demoliciones y desmontajes

- `02.01` Fundaciones
- `02.02` Estructuras
- `02.03` Fachadas
- `02.04` Paredes y particiones
- `02.05` Carpintería, herrería, vidrios y protección solar
- `02.06` Remates y elementos auxiliares
- `02.07` Instalaciones
- `02.08` Aislamientos e impermeabilizaciones
- `02.09` Techos y cubiertas
- `02.10` Revestimientos, pisos y cielos rasos
- `02.11` Equipamiento y mobiliario fijo
- `02.12` Obras exteriores, firmes y pavimentos

### 03 Acondicionamiento del terreno

- `03.01` Limpieza, desbroce y retiro de capa vegetal
- `03.02` Excavaciones a cielo abierto
- `03.03` Zanjas, pozos y excavaciones localizadas
- `03.04` Rellenos, bases y compactación
- `03.05` Drenaje provisional, achique y estabilización
- `03.06` Carga y transporte de tierras

### 04 Fundaciones

- `04.01` Preparación y mejoramiento del terreno
- `04.02` Bases y zapatas
- `04.03` Vigas de riostra y vigas de fundación
- `04.04` Losas de fundación
- `04.05` Muros de contención
- `04.06` Pilotes y fundaciones profundas
- `04.07` Drenaje y protección de fundaciones
- `04.08` Reparación y refuerzo de fundaciones

### 05 Estructuras

- `05.01` Encofrados, cimbras y apeos de ejecución
- `05.02` Acero de refuerzo
- `05.03` Concreto estructural vaciado en sitio
- `05.04` Estructuras metálicas
- `05.05` Estructuras de madera
- `05.06` Losas y entrepisos
- `05.07` Escaleras y rampas estructurales
- `05.08` Anclajes, juntas y conexiones
- `05.09` Reparación y refuerzo estructural

### 06 Fachadas y particiones

- `06.01` Fachadas de bloque o ladrillo
- `06.02` Fachadas ligeras y revestidas
- `06.03` Particiones de bloque o ladrillo
- `06.04` Particiones de yeso laminado y sistemas secos
- `06.05` Particiones ligeras, móviles y acristaladas
- `06.06` Dinteles, frentes de losa y remates de vano
- `06.07` Fachadas ventiladas y sistemas de aislamiento exterior
- `06.08` Celosías, defensas y cerramientos especiales
- `06.09` Limpieza, restauración y tratamiento de fachadas

### 07 Carpintería, herrería, vidrios y protección solar

- `07.01` Puertas interiores
- `07.02` Puertas exteriores y de seguridad
- `07.03` Ventanas, balconeras y paños fijos
- `07.04` Portones, rejas y cierres metálicos
- `07.05` Barandas y pasamanos
- `07.06` Vidrios, espejos y cerramientos de vidrio
- `07.07` Mamparas de baño y divisiones acristaladas
- `07.08` Persianas, celosías, mosquiteros y protección solar
- `07.09` Herrajes, cerraduras y automatismos
- `07.10` Ajustes, reparación y restauración

### 08 Remates y ayudas

- `08.01` Ayudas de albañilería para instalaciones
- `08.02` Rozas, perforaciones y pasos
- `08.03` Recibido de marcos, equipos y pequeños elementos
- `08.04` Sellados, juntas y encuentros
- `08.05` Alféizares, vierteaguas, pasamanos y coronaciones
- `08.06` Bancadas, soportes y bases de equipos
- `08.07` Forrados, cajones y tapajuntas
- `08.08` Perfiles decorativos, molduras y remates especiales
- `08.09` Sellado cortafuego de pasos de instalaciones

### 09 Instalaciones

- `09.01` Agua potable y agua caliente
- `09.02` Desagüe sanitario y aguas pluviales
- `09.03` Instalaciones eléctricas
- `09.04` Iluminación
- `09.05` Telecomunicaciones y datos
- `09.06` Audiovisuales, porteros e intercomunicación
- `09.07` Climatización y refrigeración
- `09.08` Ventilación y extracción
- `09.09` Gas combustible
- `09.10` Protección contra incendios
- `09.11` Seguridad, alarmas, CCTV y control de acceso
- `09.12` Domótica y automatización
- `09.13` Protección contra rayos y sobretensiones
- `09.14` Tanques, bombas e hidroneumáticos
- `09.15` Generación, respaldo y energía solar fotovoltaica
- `09.16` Transporte vertical y accesibilidad mecánica
- `09.17` Reparación, pruebas y puesta en marcha

### 10 Aislamientos e impermeabilizaciones

- `10.01` Aislamiento térmico
- `10.02` Aislamiento acústico y control de vibraciones
- `10.03` Impermeabilización de fundaciones y muros enterrados
- `10.04` Impermeabilización de techos y terrazas
- `10.05` Impermeabilización de baños, cocinas y áreas húmedas
- `10.06` Impermeabilización de tanques, piscinas y jardineras
- `10.07` Drenajes, geotextiles y capas separadoras
- `10.08` Sellado de juntas y estanqueidad
- `10.09` Tratamiento de filtraciones, humedad y capilaridad

### 11 Techos y cubiertas

- `11.01` Formación de pendientes y bases
- `11.02` Cubiertas planas transitables y no transitables
- `11.03` Cubiertas de teja
- `11.04` Cubiertas de lámina metálica
- `11.05` Cubiertas ligeras de policarbonato o materiales traslúcidos
- `11.06` Estructuras y soportes de techo
- `11.07` Claraboyas, lucernarios y accesos
- `11.08` Canales, bajantes, limahoyas y remates
- `11.09` Reparación y mantenimiento de cubiertas

### 12 Revestimientos y acabados

- `12.01` Preparación, reparación y regularización de soportes
- `12.02` Frisos, enlucidos y revestimientos de mortero
- `12.03` Enchapados de pared de piezas rígidas
- `12.04` Revestimientos decorativos y especiales de pared
- `12.05` Pisos, pavimentos y sus bases
- `12.06` Escaleras, rodapiés, juntas y remates de piso
- `12.07` Trasdosados y forros interiores
- `12.08` Cielos rasos continuos
- `12.09` Cielos rasos desmontables y ligeros
- `12.10` Pintura interior
- `12.11` Pintura exterior
- `12.12` Pintura y protección de madera y metal
- `12.13` Recubrimientos continuos, industriales y decorativos
- `12.14` Tratamientos de protección y restauración de acabados

### 13 Equipamiento, mobiliario y señalización

- `13.01` Mobiliario de cocina
- `13.02` Mesones, topes y salpicaderos
- `13.03` Mobiliario y equipamiento de baño
- `13.04` Closets, alacenas y almacenamiento fijo
- `13.05` Electrodomésticos y equipos integrados
- `13.06` Equipamiento accesible y ayudas técnicas
- `13.07` Señalización interior y exterior
- `13.08` Equipamiento comercial, oficina y áreas comunes
- `13.09` Equipamiento deportivo, recreativo y especial

### 14 Obras exteriores y urbanismo

- `14.01` Pavimentos exteriores
- `14.02` Aceras, brocales, rampas y escaleras exteriores
- `14.03` Drenaje exterior
- `14.04` Muros, cercas y cerramientos de parcela
- `14.05` Portones y accesos exteriores
- `14.06` Jardinería y tratamiento del terreno
- `14.07` Redes de riego
- `14.08` Redes exteriores de servicios
- `14.09` Iluminación exterior
- `14.10` Piscinas y áreas recreativas
- `14.11` Pérgolas, jardineras y mobiliario exterior

### 15 Gestión de residuos y limpieza

- `15.01` Clasificación y acopio de residuos
- `15.02` Bajada, carga y movimiento interno de escombros
- `15.03` Contenedores y medios de almacenamiento
- `15.04` Transporte y disposición autorizada
- `15.05` Residuos especiales o peligrosos
- `15.06` Limpieza durante la obra
- `15.07` Limpieza final y entrega

### 16 Control de calidad y ensayos

- `16.01` Ensayos de concreto, acero y mampostería
- `16.02` Inspección de soldaduras, anclajes y estructura
- `16.03` Pruebas de impermeabilización y estanqueidad
- `16.04` Pruebas de instalaciones sanitarias
- `16.05` Pruebas eléctricas y de puesta a tierra
- `16.06` Pruebas de climatización, ventilación y balanceo
- `16.07` Termografía, humedad y diagnóstico no destructivo
- `16.08` Puesta en marcha, protocolos y documentación final

### 17 Seguridad y salud en obra

- `17.01` Protecciones colectivas
- `17.02` Equipos de protección individual
- `17.03` Señalización, delimitación y control de accesos
- `17.04` Seguridad en trabajos en altura
- `17.05` Seguridad en excavaciones y espacios confinados
- `17.06` Protección contra incendios durante la obra
- `17.07` Instalaciones de higiene y bienestar
- `17.08` Gestión, formación y documentación preventiva

### 18 Rehabilitación energética

- `18.01` Diagnóstico y evaluación energética
- `18.02` Mejora térmica de fachadas
- `18.03` Mejora térmica de techos y cubiertas
- `18.04` Mejora térmica de pisos y entrepisos
- `18.05` Sustitución y mejora de ventanas y vidrios
- `18.06` Protección solar y control de ganancias térmicas
- `18.07` Mejora de climatización y ventilación
- `18.08` Iluminación eficiente y control
- `18.09` Incorporación de energías renovables

---

## 7. Ejemplos del tercer nivel

El tercer nivel es el cambio más importante. No basta con renombrar los capítulos actuales.

### 7.1 Ejemplo: instalaciones eléctricas

```text
09 Instalaciones
└── 09.03 Instalaciones eléctricas
    ├── 09.03.01 Acometidas y medición
    ├── 09.03.02 Puesta a tierra
    ├── 09.03.03 Tableros y protecciones
    ├── 09.03.04 Canalizaciones y cajas
    ├── 09.03.05 Conductores y cableado
    ├── 09.03.06 Circuitos y puntos eléctricos
    ├── 09.03.07 Interruptores y tomacorrientes
    └── 09.03.08 Reparaciones y adecuaciones
```

Ejemplo de partida:

```text
09.03.07.020 Tomacorriente doble con puesta a tierra, empotrado.
```

### 7.2 Ejemplo: pisos

```text
12 Revestimientos y acabados
└── 12.05 Pisos, pavimentos y sus bases
    ├── 12.05.01 Bases, recrecidos y afirmados
    ├── 12.05.02 Nivelación y preparación
    ├── 12.05.03 Cerámica y porcelanato
    ├── 12.05.04 Piedra, granito y terrazo
    ├── 12.05.05 Madera y laminados
    ├── 12.05.06 Vinílicos, caucho y flexibles
    ├── 12.05.07 Concreto, microcemento y continuos
    ├── 12.05.08 Pisos técnicos
    └── 12.05.09 Reparación de pisos existentes
```

Ejemplo de partida:

```text
12.05.03.010 Piso de porcelanato colocado con adhesivo, producto no incluido.
```

### 7.3 Ejemplo: demolición de instalaciones

```text
02 Demoliciones y desmontajes
└── 02.07 Instalaciones
    ├── 02.07.01 Agua potable
    ├── 02.07.02 Desagües
    ├── 02.07.03 Eléctricas
    ├── 02.07.04 Iluminación
    ├── 02.07.05 Climatización y ventilación
    ├── 02.07.06 Gas
    ├── 02.07.07 Telecomunicaciones y seguridad
    └── 02.07.08 Tanques, bombas y equipos
```

### 7.4 Ejemplo: impermeabilización

```text
10 Aislamientos e impermeabilizaciones
└── 10.04 Impermeabilización de techos y terrazas
    ├── 10.04.01 Preparación e imprimación
    ├── 10.04.02 Manto asfáltico
    ├── 10.04.03 Membranas líquidas
    ├── 10.04.04 Membranas sintéticas
    ├── 10.04.05 Puntos singulares y desagües
    ├── 10.04.06 Protección de la impermeabilización
    └── 10.04.07 Reparación localizada de filtraciones
```

---

## 8. Mapa general de migración de capítulos actuales

| Actual | Destino principal |
|---|---|
| 01 Trabajos preliminares y provisionales | 01 Actuaciones previas; una parte a 17 Seguridad |
| 02 Demoliciones y desmontajes | 02 Demoliciones y desmontajes |
| 03 Movimiento de tierras | 03 Acondicionamiento del terreno |
| 04 Fundaciones | 04 Fundaciones |
| 05 Estructuras | 05 Estructuras |
| 06 Paredes y tabiquería | 06 Fachadas y particiones |
| 07 Frisos y revestimientos de pared | 12 Revestimientos y acabados |
| 08 Pisos y pavimentos | 12 Revestimientos y acabados |
| 09 Cielos rasos | 12 Revestimientos y acabados |
| 10 Impermeabilizaciones y aislamientos | 10 Aislamientos e impermeabilizaciones |
| 11 Techos y cubiertas | 11 Techos y cubiertas |
| 12 Instalaciones sanitarias | 09 Instalaciones |
| 13 Instalaciones eléctricas | 09 Instalaciones |
| 14 Instalaciones mecánicas y especiales | 09 Instalaciones |
| 15 Herrería, carpintería y vidrios | 07 Carpintería, herrería, vidrios y protección solar |
| 16 Pintura y acabados | 12 Revestimientos y acabados |
| 17 Equipamiento y mobiliario fijo | 13 Equipamiento, mobiliario y señalización |
| 18 Obras exteriores y urbanismo | 14 Obras exteriores y urbanismo |
| 19 Gestión de residuos y limpieza | 15 Gestión de residuos y limpieza |
| 20 Seguridad y salud | 17 Seguridad y salud en obra |

No se debe migrar únicamente por el capítulo actual. Cada partida se revisará individualmente, porque algunos conceptos de remates, ayudas, protección, control o eficiencia energética cambiarán a capítulos nuevos.

---

## 9. Plan para ampliar el número de partidas

## 9.1 Principio: ampliar cobertura, no inflar el catálogo

Una partida nueva debe cubrir una diferencia real en al menos uno de estos aspectos:

- sistema constructivo;
- material relevante;
- método de ejecución;
- unidad de medición;
- rendimiento o equipo necesario;
- condición del soporte;
- interior/exterior;
- reparación/sustitución/obra nueva dentro de la reforma;
- prestación técnica que cambie de forma importante el coste.

No se creará una partida distinta solo por:

- color;
- marca;
- modelo comercial;
- diseño estético;
- una diferencia de producto que ya puede resolver el bloque de producto del cliente.

Esto es esencial: si para «piso porcelánico» creamos 40 partidas por marca, formato y color, el catálogo vuelve a ser difícil de usar. Debe existir una familia técnica clara y las opciones comerciales deben vivir en productos.

## 9.2 Primera ampliación: de 540 a unas 800 partidas

Prioridad alta, porque son trabajos frecuentes de reforma y hoy tienen poca profundidad:

### Instalaciones: aproximadamente +90

- Tuberías por material y rango de diámetro.
- Agua fría, caliente, retornos, colectores y válvulas.
- Desagües, ventilaciones, sifones, bajantes y pluviales.
- Puntos sanitarios completos y reparaciones localizadas.
- Canalizaciones, cajas, cableado por sección, circuitos y mecanismos.
- Tableros, protecciones, puesta a tierra y sobretensiones.
- Iluminación interior, exterior, emergencia y control.
- Datos, Wi‑Fi, intercomunicación, CCTV y control de acceso.
- Minisplit, conductos, rejillas, extracción y drenaje de condensados.
- Detección/extinción de incendios.
- Bombas, tanques, hidroneumáticos, respaldo e inversores.

### Revestimientos y acabados: aproximadamente +65

- Preparaciones y reparaciones de soporte.
- Más soluciones de friso, pasta, yeso y mortero.
- Enchapados por soporte, ubicación y método de colocación.
- Pisos exteriores, antideslizantes, técnicos y continuos.
- Juntas, perfiles, rodapiés, peldaños y reparaciones.
- Cielos rasos por sistema y condición de instalación.
- Pinturas específicas para humedad, alto tránsito, metal y madera.

### Carpintería, herrería y vidrios: aproximadamente +30

- Puertas por material y tipo de apertura.
- Marcos, premarcos, herrajes y cerraduras.
- Ventanas por apertura, material y prestación.
- Mosquiteros, celosías y protección solar.
- Vidrio laminado, templado, de seguridad y espejos.
- Reparación, sellado y ajuste de carpinterías existentes.

### Impermeabilización y techos: aproximadamente +30

- Preparación, imprimación y tratamiento de puntos singulares.
- Sistemas asfálticos, líquidos y sintéticos.
- Baños, terrazas, tanques, jardineras y muros enterrados.
- Canales, limahoyas, remates, claraboyas y reparaciones.

### Equipamiento y exteriores: aproximadamente +25

- Cocina, baño, almacenamiento y accesibilidad.
- Pavimentos, drenajes, riego, cercas e iluminación exterior.

### Remates, ayudas y control: aproximadamente +20

- Rozas, perforaciones, recibidos, bancadas y sellados.
- Pruebas de presión, estanqueidad, puesta a tierra y funcionamiento.

## 9.3 Segunda ampliación: de 800 a unas 1.050 partidas

- Estructuras y refuerzos especializados.
- Fachadas ventiladas, ligeras y sistemas de aislamiento exterior.
- Gamas completas de cubiertas y encuentros.
- Equipamiento comercial, oficinas y áreas comunes.
- Protección contra incendios más completa.
- Domótica, energía solar y respaldo eléctrico.
- Urbanismo, piscinas y paisajismo.
- Control de calidad y puesta en marcha.

## 9.4 Tercera ampliación: objetivo de 1.150–1.250

- Soluciones menos frecuentes o de mayor especialización.
- Rehabilitación energética.
- Accesibilidad avanzada.
- Reparación de patologías.
- Sistemas industriales, acústicos, de seguridad y especiales.

Cada ronda deberá mantener el mismo nivel de calidad actual: descripción propia, unidad, recursos, rendimientos, costes, precio, criterio de medición y terminología venezolana.

---

## 10. Cambios necesarios en la aplicación

La reorganización no se resolvía solo editando `clasificacion.json`: exigía cambiar modelo e interfaz. Ese soporte de tres niveles quedó implantado en la fase 1.

### 10.1 Modelo de datos recomendado

En lugar de añadir otra pareja de campos de texto, recomiendo convertir `CategoriaPartida` en un árbol real:

```text
CategoriaPartida
- id
- parent_id         -> otra CategoriaPartida
- codigo_segmento   -> 01, 02, 03...
- codigo_completo   -> 09.03.04
- nombre
- nivel             -> 1, 2 o 3
- orden
- ambito            -> reforma
- activa
- organizacion_id

Partida
- categoria_id      -> apartado de nivel 3
- codigo_partida    -> 010, 020...
- codigo_completo   -> 09.03.04.010
- codigo_legacy     -> CT-13-01-010 durante la transición
```

Ventajas:

- Permite tres niveles hoy y más niveles en el futuro sin volver a alterar la tabla.
- Evita repetir nombres de capítulo en las 1.200 partidas.
- Mantiene un orden explícito.
- Permite categorías vacías preparadas para crecimiento.
- Hace posible mover una rama completa.
- Reduce errores de escritura en categoría/subcategoría.

Durante una versión de transición se pueden conservar los campos de texto actuales para compatibilidad y retirarlos después.

### 10.2 Actualización versionada del catálogo

El sembrado actual es de una sola vez y reconoce las partidas por nombre. Para una reorganización grande hace falta:

- `version_catalogo`, por ejemplo `2`;
- actualización por identidad estable, no por nombre;
- `upsert` de las partidas oficiales;
- respeto absoluto a partidas creadas por el usuario;
- informe de altas, cambios, retiradas y conflictos;
- posibilidad de desactivar una partida sin borrarla;
- tabla de equivalencias de códigos.

Las partidas particulares del usuario pueden conservar su ruta. Si no tienen clasificación compatible, se ubicarán temporalmente en:

```text
99 Partidas personalizadas
└── 99.01 Sin clasificar
    └── 99.01.01 General
```

No se debe sobrescribir el contenido creado por una organización.

### 10.3 Nuevo árbol lateral

El árbol debería mostrar:

```text
▸ 09 Instalaciones                                      164
  ▸ 09.03 Eléctricas                                     42
    ▸ 09.03.04 Canalizaciones y cajas                    11
      09.03.04.010 Canalización empotrada...       8,40 $/m
```

Comportamiento propuesto:

- Tres ramas plegables antes de las partidas.
- Orden siempre numérico.
- Contador en cada rama.
- Ruta completa en el preview.
- Al buscar, abrir solo ramas con coincidencias.
- Buscar por código, nombre, descripción, sinónimos y toda la ruta.
- Resaltar las palabras encontradas.
- Mantener doble clic, `Enter` y arrastrar.
- Recordar ramas abiertas por usuario.
- Añadir accesos «Recientes» y «Más usadas» sin alterar la clasificación.
- Mostrar favoritos como una vista, no como una categoría duplicada.

### 10.4 Rendimiento

Con 1.200 partidas no conviene pintar todo el árbol expandido en el DOM desde el inicio. Se recomienda:

- enviar un índice compacto;
- renderizar hijos al abrir una rama;
- cargar o pintar fichas completas solo cuando sean necesarias;
- conservar búsqueda instantánea con un índice normalizado;
- no duplicar las partidas en varios lugares del árbol.

### 10.5 Editor del catálogo

La ficha de partida cambiaría de dos textos libres a selectores encadenados:

1. Capítulo.
2. Subcapítulo.
3. Apartado.
4. Número de partida sugerido.

El código completo se calcula automáticamente. Un administrador todavía podrá mover una partida, pero el sistema controlará colisiones y conservará el código anterior.

---

## 11. Migración sin romper presupuestos

### Principio fundamental

Los presupuestos existentes son documentos históricos. No deben cambiar de nombre, precio, código o clasificación porque se actualice el catálogo.

### Secuencia propuesta

1. Crear la estructura nueva sin borrar la actual.
2. Cargar los 18 capítulos, subcapítulos y apartados.
3. Preparar un mapa explícito para las 540 partidas existentes.
4. Asignar cada partida a un apartado nuevo.
5. Generar su código visible nuevo y guardar el código anterior.
6. Mantener el mismo `Partida.id` siempre que la partida ya exista en la organización.
7. No modificar las copias que ya viven dentro de presupuestos.
8. Ejecutar controles de duplicados, huérfanos y colisiones.
9. Publicar la nueva interfaz tras completar la migración.
10. Mantener una versión de compatibilidad para importaciones/exportaciones antiguas.

### Controles obligatorios

- 540 de 540 partidas actuales mapeadas.
- Cero partidas oficiales en «Sin clasificar».
- Cero códigos nuevos duplicados.
- Cero vínculos rotos entre líneas de presupuesto y catálogo.
- Cero partidas del usuario sobrescritas.
- Precios y descompuestos idénticos antes y después de una reclasificación pura.
- Exportaciones antiguas todavía identificables mediante `codigo_legacy`.

---

## 12. Fases de ejecución recomendadas

### Fase 0 — Diseño cerrado del árbol

- Aprobar los 18 capítulos principales.
- Cerrar todos los subcapítulos.
- Definir apartados terciarios.
- Aprobar reglas de numeración y glosario.
- Construir el mapa de las 540 partidas.

**Entregable:** taxonomía v2 y mapa completo de migración, sin tocar producción.

### Fase 1 — Soporte técnico de tres niveles

- Migraciones de base de datos.
- Árbol jerárquico.
- Selectores encadenados en la ficha.
- Búsqueda por ruta y código.
- Actualizador versionado del catálogo.
- Pruebas de compatibilidad y aislamiento por organización.

**Entregable:** las mismas 540 partidas, ya ordenadas y fáciles de navegar.

### Fase 2 — Primera ampliación prioritaria

- Crear unas 260 partidas nuevas.
- Priorizar instalaciones, acabados, carpintería e impermeabilización.
- Completar recursos y precios de mercado.

**Entregable:** alrededor de 800 partidas.

### Fase 3 — Cobertura profesional

- Añadir unas 250 partidas.
- Completar estructura, fachadas, equipamiento, exteriores y sistemas especiales.

**Entregable:** alrededor de 1.050 partidas.

### Fase 4 — Cobertura avanzada

- Añadir 100–200 partidas especializadas según uso real y búsquedas sin resultado.

**Entregable:** catálogo estable de aproximadamente 1.150–1.250 partidas.

---

## 13. Criterios para saber si la reorganización funciona

La propuesta se considerará correcta si:

1. Una partida común se encuentra navegando en un máximo de tres aperturas de rama.
2. Una búsqueda por término común devuelve resultados relevantes con su ruta completa.
3. El usuario no necesita recordar si algo estaba en «Pisos», «Revestimientos» o «Acabados».
4. Todas las partidas oficiales tienen capítulo, subcapítulo y apartado.
5. Ningún apartado contiene una lista inmanejable; al superar aproximadamente 20–25 partidas debe revisarse si necesita división.
6. No existen categorías distintas para simples sinónimos.
7. No se crean duplicados por marca, color o modelo.
8. Las partidas más usadas siguen accesibles por recientes/favoritos, independientemente del árbol.
9. La ampliación no rompe presupuestos ni personalizaciones existentes.
10. El catálogo se puede actualizar por versión en organizaciones ya creadas.

Métricas que conviene registrar después de publicar:

- búsquedas sin resultado;
- consultas reformuladas varias veces;
- partidas creadas manualmente porque no se encontró una oficial;
- ramas más visitadas;
- tiempo desde abrir el árbol hasta añadir una partida;
- partidas oficiales nunca utilizadas;
- sinónimos escritos por los usuarios.

Esos datos decidirán mejor la tercera ronda de ampliación que intentar adivinar todas las especialidades desde el principio.

---

## 14. Alternativas descartadas

### Mantener los 20 capítulos y solo añadir un tercer nivel

Es la opción más barata, pero conserva la separación inconsistente entre instalaciones y acabados. Mejoraría el árbol, pero no resolvería del todo la dificultad para encontrar conceptos.

### Copiar literalmente la estructura y los códigos de CYPE

No lo recomiendo. No está adaptada por completo a Venezuela, incorpora familias de baja prioridad para nuestro mercado y haría que el catálogo perdiera identidad propia. Además, los datos y códigos de terceros no deben ser nuestra fuente.

### Añadir de inmediato 600 partidas sin reorganizar

Aumentaría la sensación de caos. La cobertura tiene que crecer sobre la taxonomía nueva.

### Crear una partida por cada producto comercial

Haría el árbol inmanejable y duplicaría la función del catálogo de productos. La partida debe describir el trabajo; el producto define marca, modelo, formato, color y precio de suministro elegido.

---

## 15. Decisión que propongo aprobar

Aprobar como dirección de trabajo:

- **18 capítulos principales** del apartado 5.
- **Tres niveles de clasificación** antes de la partida.
- Código visible `CC.SS.AA.NNN`, totalmente numérico.
- Migración de las 540 partidas existentes antes de ampliar.
- Primera meta de **800 partidas** y objetivo posterior de **1.150–1.250**.
- Estructura inspirada en la navegación de CYPE, pero taxonomía, terminología, códigos y datos propios.
- Actualización versionada y no destructiva para organizaciones existentes.

Esta opción ataca primero el problema señalado —encontrar las cosas— y permite ampliar el catálogo sin volver a desordenarlo.