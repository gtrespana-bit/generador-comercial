# Los cinco mercados de habla inglesa en la web pública

**Fecha:** 18 de octubre de 2026
**Ámbito:** presencia de GB, US, AU, IE y CA en landings, hubs, sitemap y navegación.

---

## 1. El problema

El producto sirve **23 mercados**, cinco de ellos anglófonos con moneda,
fiscalidad y terminología propias. La web pública, en cambio, se comportaba
como si solo existieran España y Latinoamérica:

| Dónde | Qué pasaba |
|---|---|
| Hero de la portada | `paises[:6]` → España, Venezuela, Colombia, México, Ecuador, Perú. **Ningún mercado inglés.** |
| Tabla de mercados | Los mismos seis. Los otros 17 se resumían en «+ 17 países» sin enlace. |
| Portada genérica (ES) | Título, H1, `sub`, `kicker`, cuerpo y FAQ hablaban solo de «España y Latinoamérica». |
| `/en-us/` (puerta de entrada en inglés) | El hero abría con España, Venezuela, Colombia, México, Ecuador y Perú. **Ni Estados Unidos.** |
| Landings `/en-au/`, `/en-ie/`, `/en-ca/` | La misma página que `/en-us/` con el nombre, la moneda y el impuesto cambiados. Para Google, duplicados. |

Un mercado que no aparece en la portada no existe para el visitante ni para
el rastreador, por muy buena que sea su landing.

## 2. Qué se ha cambiado

### 2.1 Orden de presentación (no de validación)

`ORDEN_SELECTOR` sigue intacto —es el orden de validación, del selector y de
las pruebas—. Para pintar la web hay dos listas nuevas en `app/paises.py`:

- `MERCADOS_DESTACADOS_ES` → ES, MX, US, GB, CO, IE, AU, CA
- `MERCADOS_DESTACADOS_EN` → US, GB, IE, AU, CA, ES, MX, CO

`mercados_destacados(idioma, actual)` devuelve ocho accesos directos y coloca
**primero el mercado de la página**: en `/en-gb/`, Reino Unido abre la lista;
en `/co/`, Colombia.

`mercados_por_bloque(idioma)` devuelve los **23** mercados en dos bloques con
rótulo propio:

- «España y Latinoamérica» (18)
- «Mercados de habla inglesa (precios en GBP, USD, AUD, CAD y EUR)» (5)

En una página en inglés el orden se invierte: primero *English-speaking
markets*.

### 2.2 Portada

- El hero ya no usa `paises[:6]`: pinta los ocho accesos que decide el
  servidor.
- La tabla de mercados lista **los 23**, cada uno con enlace a su landing
  (`/mx/`, `/en-gb/`, `/en-us/`…), con el mismo peso visual para el bloque
  anglófono. Se acabó el «+ 17 países» sin salida.
- La copy genérica nombra los mercados ingleses en el título, el H1, el
  `sub`, el `kicker` y el cuerpo, y el FAQ responde a la pregunta directa
  «¿CotizaT sirve también para Reino Unido o Estados Unidos?».
- La barra de país ya no dice «(España · LatAm)» sino que incluye Reino
  Unido, Estados Unidos y Australia.

### 2.3 Cada mercado anglófono, con su propio texto

`app/seo_mercados_en.py` (nuevo) añade cuerpo y FAQ de mercado a US, AU, CA e
IE; GB sigue en `app/seo_reino_unido.py`. Ninguna de las cinco landings es ya
la misma página con el nombre cambiado:

| Mercado | Lo que la hace suya |
|---|---|
| **GB** | CIS 20/30/0 sobre mano de obra, IVA 20/5/0, inversión del sujeto pasivo, *skirting/worktop/plasterboard*, 388 recursos en GBP |
| **US** | *estimate* vs *proposal* vs *bid*, sales tax por estado y condado, imperial (pies, galones), divisiones CSI MasterFormat, retainage y lien waivers |
| **AU** | quote/estimate/variation, GST 10 %, tax invoice con ABN, PC sum y provisional sum, progress claims, licencia por estado (QBCC, VBA, NSW Fair Trading) |
| **CA** | GST 5 % y HST 13 %/15 % según provincia, holdback provincial, progress draws, CCDC y change orders, métrico |
| **IE** | VAT 13,5 % en servicios frente a 23 % en materiales y la regla de los dos tercios, RCT 0/20/35 %, bills of quantities, snag list |

Cada una suma además **dos preguntas de FAQ propias** (sales tax, GST/HST,
RCT, prime cost) y conserva el schema `FAQPage` visible en la página.

### 2.4 Detalles técnicos que se arreglaron de paso

- **Meta descriptions cortadas.** `_aplicar_prueba` recortaba el texto ya
  unido a la coletilla de la prueba y el snippet acababa en «7 días gratis,
  sin…». Ahora recorta la base y añade la coletilla completa; ninguna ficha
  pasa de 160 caracteres ni termina en puntos suspensivos.
- **Hubs ingleses**: ya pedían la ficha en el idioma de la petición (ver
  `docs/SEO_REINO_UNIDO.md`), así que las páginas de mercado no mezclan
  idiomas.
- **Sitemap y enlaces coinciden**: las cinco URLs `/en-xx/` están en la
  portada, en el mapa del sitio y en `sitemap.xml`.

## 3. Cómo comprobarlo

```bash
.venv/bin/python -m pytest tests/test_presencia_mercados_angloparlantes.py -q
```

34 pruebas que fijan: los cinco mercados en los accesos directos, la tabla
con 23 enlaces, los dos rótulos de bloque, el orden anglófono en páginas en
inglés, títulos y descripciones distintos por mercado, y que cada landing
explica su propia fiscalidad.

En producción, con el servidor en marcha:

- `/` → hero con ES, MX, US, GB, CO, IE, AU, CA y tabla de 23 mercados.
- `/en-gb/` → hero encabezado por Reino Unido y bloque anglófono primero.
- `/en-us/`, `/en-au/`, `/en-ca/`, `/en-ie/` → cuerpo propio de cada uno.

## 4. Lo que sigue pendiente (y no se disimula)

- **Precios.** Solo Reino Unido tiene matriz cargada (388 recursos). US, AU,
  CA e IE tienen catálogo, moneda, impuesto y terminología, pero **no**
  estudio de precios propio: por eso su texto explica cómo se presupuesta y
  no publica cifras de mercado. Cuando cada uno tenga su matriz, las cifras
  entran en su landing y en su hub.
- **Irlanda** necesita además reverificar la tasa EUR (sigue en 25-08-2026).
- **Enlaces entrantes y medición.** Igual que en Reino Unido: el contenido
  está, la autoridad de dominio se construye fuera del código.
