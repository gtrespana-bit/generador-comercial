# Uso en la aplicación: cargar el catálogo, cambiar precios y presupuestar

Este documento cubre las dos preguntas prácticas:

1. **Volatilidad**: cambio el precio del cemento y quiero que se actualicen
   todas las partidas.
2. **Uso diario**: cómo se meten estas 540 partidas en un presupuesto sin
   volverse loco.

---

# 1. Los dos niveles de propagación

Hay dos sitios donde vive el precio, y conviene tenerlo claro porque se usan en
momentos distintos.

| | Nivel A — el generador | Nivel B — la aplicación |
|---|---|---|
| Dónde | `basedatos_partidas/datos/recursos.json` | Pestaña **Recursos** de CotizaT |
| Quién lo toca | Tú, con `precio.py` | Tú, desde el navegador |
| Cuándo | Revisión de fondo, morteros, nuevas partidas | Día a día, en caliente |
| Alcance | Regenera las 540 hojas y el catálogo | Recalcula lo que ya está cargado |
| Ventaja | Recursos compuestos, simulación previa | Inmediato, sin regenerar ni reimportar |

**En el día a día se usa el nivel B.** El nivel A es la fuente de verdad y se
usa cuando hay que rehacer o ampliar el catálogo.

---

# 2. Cargar las 540 partidas en la aplicación

La aplicación acepta **varios `.xlsx` de descompuesto a la vez** (el importador
lo permite expresamente cuando todos son de ese formato).

1. Ir a **Partidas → Importar** (o `/presupuestos/importar?destino=catalogo`).
2. Seleccionar los archivos de `basedatos_partidas/salida/descompuestos/`.
   Se pueden marcar todos de golpe. Si el navegador se atraganta, van en
   tandas por capítulo (`CT-06-*`, `CT-07-*`…): el orden da igual.
3. Confirmar con destino **catálogo**.

Cada partida entra con su **descomposición completa**, no solo con el precio:
código, unidad, rendimiento y precio de cada recurso. Eso es lo que hace
posible el paso siguiente.

Al terminar, la aplicación **crea sola el cuadro de recursos** leyendo las
descomposiciones: aparecen los ~306 recursos con sus códigos `MT-…`, `MO-…`,
`MQ-…` repartidos en las pestañas de materiales, mano de obra y equipos. No hay
que importarlos aparte.

> **Comprobado de extremo a extremo.** Se importaron los 540 archivos contra una
> base limpia: 540 partidas creadas, 0 omitidas, 306 recursos generados
> automáticamente.

---

# 3. Cambiar un precio y que se propague (nivel B)

1. **Recursos** → buscar «cemento» → abrir `MT-CEMENTO`.
2. Cambiar el precio y guardar.
3. La aplicación recorre todas las partidas del catálogo y todas las
   descomposiciones de los presupuestos, sustituye el precio, recalcula los
   importes y vuelve a sumar los costes directos.

> **Comprobado.** Con el cemento al doble (0,225 → 0,4706 USD/kg, o sea el saco
> de 42,5 kg de 9,55 a 20 USD), la aplicación recalculó **67 partidas** de una
> sola vez. El tabique de bloque de 10 pasó de 12,39 a 13,19 USD/m² y el friso
> maestreado de 6,45 a 8,38 USD/m².

## La trampa que había y que ya está corregida

La primera vez que se probó esto, cambiar el cemento movió **10 partidas de
540**. El motivo: el mortero de pega y el de friso eran recursos opacos con
precio congelado, así que las 89 partidas que llevan cemento *dentro de un
mortero* no se enteraban.

Se corrigió convirtiendo los morteros en **recursos compuestos** y abriéndolos
en sus componentes dentro de la hoja de descompuesto. Ahora en el tabique de
bloque se ve:

```
MT-BLQ-10      ud   Bloque de concreto hueco de 10x20x40 cm          12,80
MT-CEMENTO     kg   Cemento Portland gris tipo I. Para mortero…       3,23
MT-ARENA       m3   Arena lavada de río. Para mortero de pega     0,009975
MT-AGUA-OBRA   m3   Agua para amasado. Para mortero de pega         0,0019
```

De paso se arregló un error de densidad: el mortero estaba valorado dividiendo
el coste del m³ entre 1.000 kg cuando pesa unos 2.100 kg/m³. Al pasar la unidad
a m³ el problema desaparece.

## Qué no se propaga, y está bien

El **concreto premezclado** no depende del saco de cemento: se compra hecho y lo
tarifa la planta. Tiene su propio recurso y se actualiza aparte. Igual que los
morteros industriales en saco (pego, autonivelante, grout).

---

# 4. Rutina recomendada con la volatilidad

**Semanal, o cuando se dispare algo:**

```bash
# simular antes de tocar
python3 basedatos_partidas/precio.py fijar MT-CEMENTO 20 --por-saco 42.5
```

Si el impacto convence, hay dos caminos:

- **Rápido**: cambiar solo ese precio en la pestaña Recursos de la aplicación.
  Instantáneo, sin reimportar. Es lo normal.
- **De fondo**: aplicarlo también en el generador con `--aplicar`, para que la
  fuente de verdad no se quede atrás. Conviene hacerlo aunque sea en bloque una
  vez al mes.

**Regla:** si el precio que cambia es el de un componente de mortero (cemento,
arena, agua), en la aplicación hay que cambiar **ese** componente, no el
mortero: el mortero ya no existe como línea.

---

# 5. Cómo se usan hoy las partidas en un presupuesto

Lo que ya funciona en el editor de presupuestos:

- **Buscador de catálogo** en la barra de herramientas: se escribe y filtra;
  al pulsar, la partida entra en el capítulo activo con su descomposición.
- **Atajos**: `Ctrl`/`⌘`+`K` buscar, `Alt`+`P` partida, `Alt`+`C` capítulo.
- **Arrastrar y soltar** para reordenar capítulos y partidas dentro del
  presupuesto, con línea guía de inserción.
- **Pack de Estancia** (`Alt`+`R`): inserta habitaciones enteras escaladas.
- Importar Excel y pegar filas desde Excel sin salir de la pantalla.

## Lo que falta para la idea de la barra lateral

La idea era: *una barra lateral con la base de datos completa y sus
subcategorías, y poder buscar y arrastrar hasta el presupuesto*.

Hoy el catálogo aparece como una **lista plana desplegable dentro del
buscador**. Con 540 partidas eso deja de servir: no hay forma de recorrer
«Capítulo 07 → Frisos → los seis frisos que hay» sin acordarse del nombre
exacto.

Falta, en concreto:

1. **Panel lateral fijo** con el árbol de 20 capítulos → 121 subcapítulos →
   540 partidas, plegable por rama. El árbol ya está generado en
   `salida/arbol_catalogo.json` con contadores por rama, precio, unidad, horas
   y marca de producto de cliente.
2. **Buscador dentro del árbol** que filtre manteniendo el contexto (que se
   vea de qué capítulo cuelga cada resultado).
3. **Arrastrar desde el árbol hasta un capítulo del presupuesto.** La
   infraestructura de arrastre ya existe (`static/js/editor/dragdrop.js`), pero
   hoy solo reordena lo que ya está dentro; hay que admitir un origen externo.
4. **Doble clic o Enter** como alternativa al arrastre, porque en portátil sin
   ratón arrastrar es incómodo.

Esto sí toca código de la aplicación (`app/templates/budgets/form.html`,
`app/static/js/editor/`) y un endpoint que sirva el árbol.
