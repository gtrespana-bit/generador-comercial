# CotizaT

**Presupuestos y control comercial para construcción y remodelación.**

CotizaT convierte tu catálogo y tus precios en presupuestos de obra claros,
editables y listos para presentar. Está orientado inicialmente a pequeñas
empresas de construcción y remodelación en Venezuela: trabaja en USD o
bolívares, organiza capítulos, partidas, mediciones, productos y cambios de
alcance, y genera documentos PDF profesionales.

> CotizaT funciona de forma local. Sus sugerencias se basan en coincidencias
> deterministas sobre el catálogo del usuario; no se presentan como
> inteligencia artificial ni requieren enviar los datos a un servicio externo.

## Cómo se estructura un presupuesto

```
Presupuesto (P-2026-001)
├── Proyecto / obra: título, dirección de la obra, código postal
├── Cliente: nombre, RIF, país
└── Capítulo (p. ej. MUROS Y PARTICIONES) — banda navy + subtotal propio
    └── Partida: título + descripción técnica larga
        ├── Cantidad = suma de mediciones (o cantidad directa)
        ├── Mediciones: desglose por zonas (Cocina 10.00 m2, Salón 2.50 m2…)
        └── Producto presupuestado (opcional): nombre, precio e imagen
```

El PDF se cierra con el bloque **BASE IMPONIBLE / I.V.A. / PRESUPUESTO
TOTAL** sobre fondo azul-grisáceo con faja azul y numeración de páginas
«n/N».

## Funcionalidades

- **Clientes**: alta, edición y búsqueda (nombre, RIF/C.I., país, teléfono,
  email, dirección).
- **Presupuestos por capítulos**:
  - Constructor visual: capítulos ilimitados, partidas con descripción
    técnica, mediciones desglosadas y producto presupuestado con imagen.
    Las partidas se **colapsan solas al terminar** de editarlas y también
    puedes plegarlas/desplegarlas cuando quieras con el botón ▾/▴ o con un
    clic en cualquier zona no editable de la fila. Las filas alternan tono
    para distinguirse mejor.
  - **Atajos de teclado (escritura rápida, "hands-free")**: `Enter` dentro de
    una partida avanza nombre → cantidad → precio (sin crear partidas nuevas);
    `Alt+P` añade partida, `Alt+C` añade capítulo, `Ctrl/⌘+K` (o `/`) enfoca el
    buscador del catálogo, `Ctrl/⌘+Z` deshace cambios estructurales y
    `Ctrl/⌘+Enter` guarda.
  - **Funciones "pro" del constructor**:
    - Arrastrar y soltar para reordenar partidas.
    - Duplicar partida y duplicar capítulo.
    - Pegar partidas desde Excel (copiar y pegar TSV).
    - Deshacer estructural (`Ctrl/⌘+Z`) y autosave local (borrador recuperable).
    - Numeración automática de partidas `1.1, 1.2 …` (en pantalla y en el PDF).
    - Guardar y cargar **plantillas de presupuesto** (`/plantillas`).
    - Vista previa del PDF en vivo desde el editor.
  - **Modo oscuro**: botón 🌙/☀️ en el sidebar (se recuerda la preferencia).
  - Catálogo de partidas reutilizables (se insertan con un clic). Las
    partidas nuevas que escribes al armar un presupuesto **se guardan
    solas en el catálogo** (con su categoría) para reutilizarlas a futuro.
  - **Productos** (pestaña independiente de las partidas): catálogo de
    materiales con precio y foto. Al crear un presupuesto puedes elegir un
    producto de la pestaña **Productos** para cada partida, o escribir uno
    nuevo: también se guarda automáticamente en el catálogo de productos.
  - Cada producto puede llevar **foto con vista previa** y se puede
    eliminar la foto antes de guardar.
  - Totales en vivo por capítulo y generales (base, descuento, IVA, total).
  - Numeración automática por año: `P-2026-001`, `P-2026-002`, …
  - Moneda **USD** o **Bs**, tasa de cambio de referencia BCV.
  - Estados: borrador, enviado, aprobado, rechazado, vencido.
  - Historial con filtros por cliente, estado y rango de fechas.
  - **Exportación a PDF profesional:** fuente
    **Lato** embebida, caja de empresa con faja navy, logo, banda de
    capítulos, mediciones, «Producto presupuestado», bloque de totales e
    «Información adicional». El PDF incluye **marca de agua** con el
    estado cuando es BORRADOR, RECHAZADO o VENCIDO.
  - **Firma digital del cliente**: dibuja la firma en el formulario
    (ratón o dedo) y se inserta en el bloque de firmas del PDF.
  - **Enviar por WhatsApp**: botón que abre wa.me con el mensaje del
    presupuesto ya redactado (cliente, número, total, validez).
  - **Importación de descompuestos CYPE (.xlsx)**: detecta cada partida,
    grupo, recurso, subtotal y total de coste; conserva todas las filas,
    columnas, fórmulas, celdas combinadas y el Excel original descargable.
    Las columnas se localizan dinámicamente por sus encabezados, así que
    admite los distintos layouts del exportador (8 columnas tipo `DPT020` o
    10 columnas con separadores tipo `RBE010`) sin perder ninguna fila ni
    columna. Clasifica los gastos en **materiales, mano de obra, directos
    complementarios y otros**, tanto si la partida lleva materiales como si
    solo lleva mano de obra. El coste directo de CYPE alimenta el cálculo
    interno por partida sin duplicar subtotales, y puedes revisar la matriz
    completa desde el detalle del presupuesto.
  - **Edición de costes del descompuesto**: en la vista del descompuesto
    puedes editar el **rendimiento** y el **precio unitario** de cada
    recurso (p. ej. si sube la hora del trabajador o el precio del cemento).
    Cada recurso cuesta Rendimiento × Precio unitario por unidad de partida,
    y al guardar se recalcula toda la cascada con las mismas reglas de las
    fórmulas del Excel: importes, subtotales, directos complementarios (%)
    y coste directo, reflejándose en los gastos de la partida y en el
    presupuesto. Opcionalmente se puede actualizar también el precio de
    venta de la partida al nuevo coste directo.
  - **Exportar a CSV/Excel**: historial (respetando filtros), detalle de
    un presupuesto, y catálogos de partidas y productos.
  - Vista previa del PDF en el navegador (👁 Ver PDF).
- **Documentos de cobro no fiscales**: desde un presupuesto **aprobado** se
  genera un documento comercial (`DC-2026-001`) con su propio PDF e historial.
  La interfaz y el PDF aclaran que no sustituye una factura fiscal.
- **Notas de seguimiento**: apuntes internos por presupuesto (llamadas,
  cambios, acuerdos) que no aparecen en el PDF.
- **Vencimiento automático**: los presupuestos enviados cuya validez
  expiró pasan solos a «vencido»; el inicio avisa de los que vencen en
  los próximos 7 días.
- **Ajuste de precios del catálogo por %** (subir/bajar todo de golpe,
  ideal con inflación) y **partidas más usadas primero** (contador de uso).
- **Paginación** del historial (25 por página) e **índices** en la base de
  datos para que todo siga rápido con miles de registros.
- **Configuración**: nombre comercial, razón social, RIF, teléfono, email,
  país, ciudad, web, dirección, **logotipo propio** (con **control de tamaño en el PDF**),
  color de marca y valores por defecto (moneda, IVA, validez, notas,
  condiciones). Una instalación nueva usa datos empresariales neutros; cada
  empresa debe completar su propia información antes de emitir documentos.
  - Los **valores por defecto del PDF** marcados (portada, resumen de
    capítulos, firmas) se aplican al guardar **tanto a los presupuestos
    nuevos como a los ya existentes**; si una casilla queda sin marcar,
    sólo afecta a los nuevos.
- **Copia de seguridad**: en Configuración puedes **descargar una copia
  completa** (base de datos + imágenes en un solo .zip) y **restaurarla**
  en cualquier instalación o versión nueva. Antes de restaurar se guarda
  automáticamente una copia de lo actual en `backups/`. La ruta de la base
  de datos también se puede cambiar con la variable de entorno
  `COTIZAT_DB` para apuntar una instalación nueva al mismo archivo. El nombre
  histórico `PRESUPUESTOS_DB` continúa aceptándose por compatibilidad.
- **Primer inicio**: una instalación nueva solicita los datos mínimos de la
  empresa y permite elegir entre **ejemplo guiado** e **instalación limpia**.
  El ejemplo carga un catálogo base, productos, packs, un cliente y un
  presupuesto ficticios, identificados como demostración y con precios que
  deben revisarse. La opción limpia no añade catálogos ni documentos. El
  dashboard guía hasta la primera descarga de un PDF real.

## Requisitos

- Python 3.10 o superior ([python.org/downloads](https://www.python.org/downloads/) — en Windows marca **“Add Python to PATH”** durante la instalación). Solo se instala una vez.

## Abrir la aplicación (sin tocar código)

Haz **doble clic** en el lanzador de tu sistema:

| Sistema | Archivo |
| --- | --- |
| Windows | `INICIAR.bat` |
| macOS | `INICIAR.command` |
| Linux | `INICIAR.sh` |

- La **primera vez** prepara todo solo (1-2 minutos); las siguientes abre al instante.
- El navegador se abre automáticamente en **http://localhost:8000**.
- Para cerrar la app, simplemente **cierra la ventana negra** que aparece (o `Ctrl+C` en Linux/macOS).
- Consejo: crea un acceso directo del lanzador en el escritorio o anclalo a la barra de tareas para tenerlo siempre a mano.

> En macOS, si al primer doble clic aparece un aviso de seguridad, haz clic
> derecho sobre `INICIAR.command` → **Abrir** → **Abrir** (solo es necesario
> la primera vez).

### Alternativa (para desarrolladores)

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Los datos se guardan en `presupuestos.db` (se crea automáticamente). Las
imágenes subidas (logo y productos) van a `app/static/uploads/` — ninguna de
las dos rutas se versiona en git. Para mover todos los datos a otra
instalación o versión usa la **copia de seguridad** de Configuración
(descargar .zip → restaurar en la nueva), o apunta la nueva instalación al
mismo archivo con `COTIZAT_DB` (`PRESUPUESTOS_DB` sigue aceptándose como alias).

## Estructura del proyecto

```
app/
├── main.py            # Rutas y lógica de la aplicación
├── database.py        # Conexión SQLite, inicialización y migraciones
├── models.py          # Cliente, Presupuesto, Capítulo, Item, Medición, Config
├── seeds.py           # Catálogos y datos ficticios del modo demostración
├── utils.py           # Formatos de moneda/cantidades/fecha (estilo venezolano)
├── services/
│   ├── onboarding.py  # Primer inicio y progreso hasta el primer PDF
│   └── pdf.py         # Motor del PDF estilo documento de referencia (ReportLab)
├── templates/         # Páginas HTML (Jinja2)
└── static/
    ├── css/           # Estilos de la aplicación
    ├── js/            # Constructor de capítulos del formulario
    ├── fonts/         # Familia Lato (licencia SIL OFL 1.1, ver OFL.txt)
    └── uploads/       # Logo e imágenes de producto (no versionado)
desktop.py             # Modo escritorio: ventana propia (pywebview)
run.py                 # Punto de entrada clásico (navegador)
presupuestos.spec      # Empaquetado con PyInstaller
instalador.iss         # Instalador de Windows (Inno Setup)
```

## Instalar como aplicación de Windows (ventana propia)

La aplicación se puede instalar **como un programa normal de Windows**:
icono propio, ventana propia (sin navegador y sin consola), acceso directo
en el escritorio y en el menú Inicio, y desinstalador.

### Opción A — Instalador con doble clic (recomendada)

1. En tu PC con Windows, ejecuta `CREAR_INSTALADOR.bat` (la primera vez
   instala PyInstaller e Inno Setup, ambos gratis).
2. El resultado es `instalador\Instalador_CotizaT.exe`.
3. Copia **solo ese archivo** a cualquier PC con Windows y ejecútalo: instala
   la app, sus accesos directos y el desinstalador.
4. Si ese PC no tiene Microsoft WebView2, el instalador lo detecta y lo
   descarga e instala **automáticamente y en silencio** antes de abrir la
   aplicación. El destinatario no tiene que buscar ni instalar programas
   secundarios; solo necesita conexión a internet durante esa primera
   instalación excepcional.

### Opción B — Carpeta portátil (sin instalador)

Ejecuta `EMPAQUETAR.bat` → `dist\CotizaT.exe` (un único archivo
autónomo). Copialo a cualquier PC y haz doble clic: se abre en su propia
ventana.

> **Para entregar a otras personas, usa siempre la Opción A.** Su instalador
> incluye el mecanismo que instala WebView2 automáticamente si hace falta. La
> Opción B es portátil y presupone que el equipo ya tiene WebView2. Si la ventana
> nativa no pudiera cargarse, la aplicación intenta abrirse en el navegador
> predeterminado y deja el diagnóstico en `logs\inicio.log`, dentro de la
> carpeta de datos activa.

### Si la aplicación no arranca (diagnóstico con inicio.log)

Cada intento de arranque escribe en `logs\inicio.log` dentro de la carpeta de
datos activa. En una instalación nueva es `%LOCALAPPDATA%\CotizaT`; si ya
existe una versión anterior con datos en `%LOCALAPPDATA%\Presupuestos`,
CotizaT sigue usando esa carpeta automáticamente. El cuadro de error muestra
las últimas líneas del registro.

1. **Busca la línea `=== Arranque de la aplicación de escritorio ===` con la
   fecha/hora en que lo intentaste.**
   - Si **no aparece**, el ejecutable ni siquiera llegó a empezar: suele ser
     el antivirus o SmartScreen bloqueándolo, o un `CotizaT.exe` antiguo.
     Desinstala, vuelve a instalar la versión actual y prueba de nuevo.
   - Si **aparece**, las líneas siguientes explican qué pasó.
2. **«El servidor local no respondió en N s»**: la aplicación tardó demasiado
   en prepararse. Es normal la primera vez en equipos lentos (el antivirus
   escanea el programa y se crea o migra la base de datos local).
   Vuelve a intentarlo. Si se repite, arranca la app con más margen:
   `set COTIZAT_ESPERA=300` y luego ejecuta `CotizaT.exe` desde esa
   misma ventana.
3. **«Causa: …»** o **«Error no controlado»**: esa línea es el error real
   (un módulo que falta, un archivo dañado, etc.); cópiala junto con las
   últimas líneas del registro para reportar el problema.
4. Si sospechas de una instalación corrupta, no borres la carpeta de datos.
   Primero descarga o copia un backup. Renombra temporalmente la carpeta activa
   y vuelve a abrir la app; CotizaT creará una instalación limpia y la carpeta
   renombrada quedará disponible para recuperación.

### Modo ventana propia en desarrollo

```bash
pip install -r requirements.txt   # incluye pywebview
python desktop.py                 # ventana propia (sin navegador)
python run.py                     # modo clásico (navegador)
```

> **Dónde viven tus datos:** una instalación nueva usa
> `%LOCALAPPDATA%\CotizaT\`. Si actualizas una versión anterior, se conserva
> `%LOCALAPPDATA%\Presupuestos\` cuando allí ya existen datos. La aplicación
> no mueve ni borra automáticamente la base, imágenes o backups. Antes de una
> actualización importante, crea una copia desde Configuración.

## Plan (siguientes pasos posibles)

- [x] Conversión de presupuesto aprobado a documento de cobro no fiscal
- [x] Copia / duplicado de presupuestos
- [x] Portada de presentación opcional con foto del proyecto
- [x] Firma del cliente digitalizada
- [x] Empaquetado como aplicación de escritorio (.exe) — `EMPAQUETAR.bat`
- [x] Instalador de Windows con ventana propia — `CREAR_INSTALADOR.bat` + `instalador.iss`
- [ ] Envío por email (SMTP) desde la aplicación
- [ ] Multi-empresa / usuarios

## Notas

- Las fuentes **Lato** (`app/static/fonts/`) se distribuyen bajo la licencia
  SIL Open Font License 1.1 (incluida en `OFL.txt`).
- Formato de PDF generado con diseño limpio y estructurado en capítulos y partidas.
