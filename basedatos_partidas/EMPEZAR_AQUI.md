# EMPEZAR AQUÍ — estado del trabajo y siguiente paso

> Documento de traspaso. Si abres una ventana de chat nueva, lee esto primero
> y no vuelvas a levantar lo que ya está decidido.
>
> Última actualización: 16/08/2026, justo antes del pull request.

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
| Partidas | **540** |
| Capítulos · subcapítulos | 20 · 121 (todos con contenido) |
| Recursos en el cuadro de precios | 311 |
| Coste directo del catálogo | 15.733,15 USD |
| **Peso económico con precio cerrado** | **79,6 %** |
| Validación con el importador real | **0 errores · 0 advertencias** |
| Tests del proyecto | **391 pasando** |

Desglose del cuadro de precios:

| Estado | Recursos | Peso | % |
|---|---:|---:|---:|
| `confirmado` (mano de obra, dato del cliente) | 17 | 3.180,69 | 20,2 % |
| `verificado-mercado` (contrastado con VE) | 113 | 9.214,75 | 58,6 % |
| `derivado` (morteros, salen del cemento) | 4 | 127,36 | 0,8 % |
| `provisional` | 177 | 3.210,35 | 20,4 % |

---

# 3. Reglas que NO hay que volver a discutir

1. **Terminología venezolana, siempre.** Concreto (no hormigón), friso (no
   enfoscado), cielo raso (no falso techo), piso (no solado), mesón (no
   encimera), **afirmado** (no contrapiso ni recrecido), plomero, granito
   vaciado en sitio. Está vigilado por `terminologia.py auditar`.
2. **CYPE no se toca.** Es un producto comercial vivo. Se rechazó extraerla por
   el derecho *sui generis* (art. 133 TRLPI) y por riesgo de competencia
   desleal si se copiara su codificación. Codificación propia `CT-CC-SS-NNN`.
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
│   ├── clasificacion.json       20 capítulos · 121 subcapítulos
│   ├── glosario.json            vocabulario venezolano
│   ├── contraste_mercado_2026-08.json   evidencia de precios con fuente
│   └── descompuestos/*.json     540 partidas, una por archivo
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

# 6. SIGUIENTE PASO — por dónde empezar

## 6.1 Prioridad 1: cerrar los 134 precios de material provisionales

Son 2.213 USD, el 14,1 % del coste directo. Ya no son los de más peso: la
segunda ronda cerró los grandes. Lo que queda son piezas de proveedor
especializado, cada una con poco peso individual.

Los diez de más impacto:

| Recurso | Ud | Hoy | Peso |
|---|---|---:|---:|
| `MT-TABIQUE-MOVIL` | m² | 135,00 | 139,05 |
| `MT-CASETA-BIEN` | ud | 120,00 | 120,00 |
| `MT-ACC-BOMBA` | ud | 28,00 | 84,00 |
| `MT-TRAMPA-GRASA` | ud | 78,00 | 78,00 |
| `MT-REGUL-GAS` | ud | 24,00 | 72,00 |
| `MT-CONTENEDOR` | ud | 65,00 | 65,00 |
| `MT-HERRAJE-MAD` | ud | 5,50 | 58,02 |
| `MT-BANDA-REF` | m | 2,80 | 55,44 |
| `MT-ARNES` | ud | 55,00 | 55,00 |
| `MT-BARRA-TIERRA` | ud | 18,00 | 54,00 |

**Cómo hacerlo.** Crear `datos/contraste_mercado_2026-XX.json` con el mismo
formato que el de agosto (precio adoptado, rango observado, conversión,
fuente) y volcarlo con `python3 basedatos_partidas/contraste.py aplicar`.
Fuentes que funcionaron: **EPA en línea** (`ve.epaenlinea.com`, precios en USD,
se rastrea con `fetch_page`) y **MercadoLibre Venezuela** (los listados por
familia dan 30-40 precios de una búsqueda).

> Ojo: desde bash **no hay salida a Internet**. Solo funcionan las herramientas
> `fetch_page` y `web_search`.

**El que más falta hace:** `MT-PERFIL-ALUM` (aluminio, hoy 9,50 USD/kg). Es el
de mayor dispersión de todo el cuadro: al detal sale entre 12 y 17 USD/kg. Se
cierra con una lista de precios de un extrusor o un taller de aluminio.

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
  quedó preparada: cada partida lleva `ambito` y `codigo_covenin` vacío, y
  `clasificacion.json` declara `_ambitos_previstos`.
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
