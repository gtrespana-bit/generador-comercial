# Marketing de CotizaT — Facebook

Piezas listas para Meta: la **página de Facebook** del proyecto y los
**flyers** para publicaciones/anuncios, ambos con mensaje inequívoco de
producto: **CotizaT es software — un generador de presupuestos con gestión
comercial** que usa la propia empresa de construcción o remodelación.

---

## 1 · Página de Facebook

| Elemento | Valor | Archivo |
|---|---|---|
| Nombre | `CotizaT · Presupuestos` | — |
| Foto de perfil | Ícono oficial de la app (512×512 PNG, mín. FB: 320) | `cotizat-perfil-facebook-512x512.png` |
| Portada | 1640×624 PNG · contenido en zona segura central (FB superpone la foto de perfil abajo a la izquierda y recorta laterales en móvil) | `cotizat-portada-facebook-1640x624.png` |

**Nombre de usuario (@):** probar primero `@CotizaT`; si está ocupado:
`@cotizat.online` o `@CotizaTApp`. Conviene usar el mismo alias en
Instagram para el contenido cruzado.

**Descripción (255 caracteres máx., 232 usados):**

> Generador de presupuestos y gestión comercial para empresas de construcción y remodelación. Precios de mercado de tu país, tu moneda, tu IVA y tu ID fiscal. Beneficio y horas-hombre a la vista. PDF profesional y WhatsApp. 18 países.

**Categorías:** páginas de Facebook admiten hasta 3. Usar
**Software** (principal), **Empresa de software** y **Servicio para
empresas**. NO elegir «Empresa de construcción»: confundiría el producto
(la herramienta la usan esas empresas; nosotros no ejecutamos obras).

**Campos clave:** web `https://cotizat.online` · botón «Más información»
→ `https://cotizat.online` · correo `soporte@cotizat.online`.

**Información adicional (campo «Acerca de» largo):**

> CotizaT es la herramienta con la que tu empresa genera y gestiona sus
> presupuestos de obra: catálogo propio de partidas y productos, plantillas,
> mediciones por zonas y PDF profesional con tu logo y la firma digital del
> cliente, listo para enviar por WhatsApp.
>
> Está hecho para tu país: incluye precios de mercado locales verificados
> (388 recursos por país), trabaja en tu moneda entre 17 divisas con tasa de
> referencia, aplica tu IVA y muestra tu identificador fiscal en cada
> documento. Además calcula tu beneficio real (coste vs venta, margen por
> partida) y las horas-hombre de la obra (oficial y ayudante, con duración
> estimada).
>
> Funciones profesionales: APU con rendimientos editables, importación de
> CYPE (.xlsx) y BC3, medición sobre planos con exportación DXF, asistente
> de revisión, cambios de alcance y documentos de cobro.
>
> Disponible para 18 países de Latinoamérica y España. Empieza en
> cotizat.online.

---

## 2 · Flyers publicitarios

| Archivo | Tamaño | Uso |
|---|---|---|
| `cotizat-flyer-facebook-1080x1080.png` | 1080 × 1080 (1:1) | Feed universal (Facebook e Instagram). Se muestra completo en móvil y escritorio. |
| `cotizat-flyer-facebook-1080x1350.png` | 1080 × 1350 (4:5) | Feed móvil (recomendado): ocupa más pantalla → mayor impacto. |

Ambos cumplen especificaciones de Meta: PNG, ≥1080 px, <30 MB y texto por
debajo del 20 % de la imagen.

## Estructura del mensaje (qué es el producto, sin ambigüedad)

1. **Etiqueta** `GENERADOR DE PRESUPUESTOS` — categoría del producto a la primera vista.
2. **Titular** «Genera y gestiona **tus presupuestos**» — la empresa los
   genera ella misma con la herramienta.
3. **Subtítulo** «de obra, en tu moneda y con tu normativa».
4. **6 ventajas** (datos reales del producto):
   - Genera presupuestos en minutos — catálogo propio, plantillas y PDF profesional
   - Gestiona y controla cada venta — estados, cambios de alcance, cobros y WhatsApp
   - Precios de mercado de tu país — 388 recursos verificados, con fuente y fecha
   - Tu moneda y tu normativa local — 17 monedas · IVA e ID fiscal propios
   - Beneficio y horas a la vista — margen por partida · horas-hombre de la obra
   - APU, CYPE, BC3 y planos — edita rendimientos · mide m² · exporta DXF
5. **Tarjeta flotante** con el ejemplo oficial de la app:
   +651,47 US$ de beneficio (+35 %) · 98 h-hombre · ≈ 6 días.
   El rótulo «EJEMPLO DESDE LA PROPIA APP» refuerza que es captura del producto.
6. **CTA** `cotizat.online`.

Cobertura internacional real: VE, CO, MX, PE, EC, PA, SV, CL, AR, DO, UY,
PY, BO, CR, GT, HN, NI y ES — cada país con glosario local (friso »
pañete/aplanado), IVA propio (16 %, 19 %, 21 %, 7 %, 10 %…) e
identificador fiscal local (RIF, NIT, RFC, RUC, CUIT, RNC, RUT, RTN, NIF)
en los documentos.

## Configuración sugerida del anuncio

- **Destino:** `https://cotizat.online` · **Botón CTA:** «Más información»
- **Texto principal:**

  > La herramienta con la que tu empresa genera y gestiona sus presupuestos de obra 🛠️
  > ✅ Catálogo propio, plantillas y PDF profesional con tu logo
  > ✅ Control total: estados, cambios de alcance y cobros por WhatsApp
  > ✅ Precios de mercado de tu país, ya cargados (18 países)
  > ✅ Tu moneda, tu IVA y tu identificador fiscal
  > ✅ Beneficio real y horas de trabajo siempre a la vista
  >
  > Software para construcción y remodelación. Pruébalo en cotizat.online

- **Título:** `Generador de presupuestos para construcción`
- **Descripción:** `Genera y gestiona presupuestos de obra con los precios, moneda y normativa de tu país.`
- **Segmentación:** una campaña por país o grupo de países; intereses en
  construcción, remodelación, ferretería, arquitectura. Público:
  dueños/encargados de empresas de construcción y remodelación (la imagen
  ya filtra al comprador correcto).

## Regenerar los flyers

Montaje reproducible con Pillow sobre los recursos de marca del repo:

```bash
python3 -m venv .venv-flyer
.venv-flyer/bin/pip install pillow
.venv-flyer/bin/python marketing/generar_flyer.py
```

Copys (`LABEL_TXT`, `SUB_TXT`, `ADV_STANDALONE`) y disposición
(`CFG_STANDALONE_11`, `CFG_STANDALONE_45`) al inicio de cada sección de
`generar_flyer.py`. Nota: la fuente Lato del proyecto no trae los glifos
`₡` ni `→`; usa `CRC`, `»` u otros equivalentes.
