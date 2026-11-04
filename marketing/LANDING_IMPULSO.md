# Landing «Impulso» — diagnóstico, decisiones y medición

**Fecha:** 3 de noviembre de 2026  
**Objetivo:** más registros y más retención/activación, no solo más clics.  
**Estado:** variante nueva sirviéndose por defecto en `/` y en las landings de país en español; el diseño anterior sigue accesible en `/?diseno=clasico` para comparar. Los mercados en inglés conservan `landing_en.html` hasta tener traducción propia de la variante.

---

## 1. Diagnóstico del landing anterior

`app/templates/landing.html` era una página muy completa, pero pensada para acumular contenido SEO, no para decidir en cinco segundos:

- El primer viewport pedía leer barra de país, navegación, kicker largo, badge, H1 SEO, subtítulo, ocho mercados, dos CTA, microcopy, cuatro tarjetas y tres bullets antes de encontrar una imagen del producto.
- No había una **promesa de primer valor** explícita: el visitante no sabía qué tendría en su primer presupuesto ni cuánto tardaría en verlo.
- La CTA principal competía con otra CTA de PDF, enlaces de navegación y chips de mercados; no existía una acción dominante y repetida.
- El copy describía funciones, no la consecuencia de negocio: «tiempo perdido», «margen invisible», «precio que no se puede defender».
- El alta real pedía nombre, país, email, contraseña, confirmación y términos, y después volvía a pedir país y razón social. La landing prometía valor, pero el primer paso del producto era una pantalla de configuración.
- No había prueba social verificada. Se descartó fabricar testimonios, logos o contadores: además de no ser honesto, la norma de la FTC sobre reseñas falsas lo prohíbe.
- No había instrumentación que distinguiera clic en CTA, inicio de alta, alta completada y primer PDF exportado. Sin eso, «más conversión» no se puede atribuir a un cambio concreto.

---

## 2. Qué se ha construido

### Archivos nuevos

| Archivo | Papel |
| --- | --- |
| `app/templates/landing_impulso.html` | Nueva portada: hero de resultado, mapa completo de capacidades, calculadora de coste de oportunidad, tour real del producto, activación en 3 pasos, precios y cierre. |
| `app/templates/_landing_impulso.css` | Sistema visual propio, inline con nonce, sin fuentes externas. El hero se pinta con CSS crítico; `public.css` sigue diferida. |
| `app/static/js/landing_impulso.js` | Microcompromisos, calculadora con datos del visitante, CTA persistente y eventos de profundidad. Sin inserción de marcado ni estilos en línea. |
| `tests/test_landing_impulso.py` | Contratos de la variante, atribución y noindex del duplicado A/B. |
| `marketing/landing-impulso-preview.html` | Captura autocontenida para ver el diseño sin servidor. |

### Cambios en el producto

- `app/routers/publico.py`: `_plantilla_portada()` decide la variante; `?diseno=clasico` mantiene la anterior.
- `app/routers/common.py`: la variante clásica devuelve `noindex, follow` para no canibalizar la canónica.
- `app/services/atribucion.py`: nueva sección `landing_impulso`, catálogo cerrado de variantes (`impulso`, `clasica`) e intenciones (`tiempo`, `margen`, `cierre`).
- `app/routers/auth.py` y `auth/access*.html`: el CTA llega con `alta=1`, país preseleccionado, variante e intención; el formulario conserva esos valores en campos ocultos y enfoca el alta.
- `app/templates/landing_impulso.html`: todos los CTA llevan `data-ga-event` y el mismo `data-lp2-cta` para que el copy cambie con la intención elegida.

---

## 3. Técnicas aplicadas y por qué

| Técnica | Aplicación concreta | Guardrail ético / técnico |
| --- | --- | --- |
| **Comprensión en 5 segundos** | H1 de resultado «Deja de adivinar. Cobra con margen.», subtítulo con el resultado completo y una demo del presupuesto con total, beneficio, plazo y catálogo en el primer viewport. | La frase SEO sigue dentro del H1, pero en un nivel visual secundario; no se pierde título, descripción, canónica ni JSON-LD. |
| **Una acción dominante, repetida** | CTA verde lima en hero, calculadora, activación, tour, precios, cierre, navegación y barra fija al hacer scroll. En móvil ocupa todo el ancho. | El enlace al PDF de ejemplo queda como acción secundaria de bajo compromiso, no como CTA rival. |
| **Copy en primera persona y orientado a resultado** | «Quiero mi primer presupuesto hoy», «Quiero saber mi margen real», «Sí, quiero empezar ahora». 2–5 palabras en la mayoría de casos, siempre con verbo. | No se usa urgencia falsa, cuentas atrás ni «plazas limitadas». |
| **Microcompromiso / autosegmentación** | Tres chips: «Dejar de perder tardes», «Saber mi margen real», «Cerrar más presupuestos». Cambian el texto del CTA y añaden `intencion` a su URL. | Tres opciones, no un menú de 20; el valor por defecto es explícito y se puede ignorar. |
| **Valor antes del registro** | PDF real, catálogo público de precios/APU y calculadora local que usa solo los números que escribe el visitante. | La calculadora no envía datos, no inventa ahorros ni promete un porcentaje de mejora. |
| **Progreso dotado / time-to-value** | «Paso 1 de 3 ya listo: catálogo de tu país», barra al 33 % y meta concreta: primer PDF con margen y logo. | El paso completado es real: el catálogo se sirve con la cuenta. No se regalan sellos ficticios. |
| **Reducción de fricción** | `alta=1` enfoca el formulario de creación; `pais=XX` llega desde la landing; se difiere la calificación; se mide variante e intención con campos ocultos. | No se eliminan contraseña, confirmación ni aceptación de términos: siguen siendo requisitos reales del backend. |
| **Prueba honesta junto a cada decisión** | Cifras del catálogo, 23 mercados, ejemplo aritmético real, precio tachado con precio habitual, «sin tarjeta», «sin permanencia», «no facturas fiscales», exportación de datos. | Sin testimonios, logos de clientes, contadores de usuarios ni indicadores sociales inventados. |
| **Elección reducida** | Un CTA principal; una secundaria; un selector de país; tres intenciones. El mapa de capacidades se muestra como recorrido de 8 eslabones, no como lista interminable. | El detalle completo sigue disponible para quien quiera profundizar. |
| **Retención desde la sesión 1** | La página explica el primer valor antes del alta y lo conecta con el onboarding: catálogo precargado → primer cliente/obra → PDF con logo. | No se promete IA: el asistente del producto es determinista. |
| **Velocidad y móvil** | CSS crítico inline, `public.css` diferida, `content-visibility`, sin webfonts, sin imágenes de fondo en el hero, `loading="lazy"`, `decoding="async"`, JSON-LD tras `</main>`. | Se mantienen los contratos de LCP/CLS, CSP sin atributos de evento, nonces y safe-area móvil. |
| **Medición de embudo completo** | `cta_hero`, `cta_final`, `cta_sticky`, `landing_intencion`, `landing_calculo_tiempo`, `landing_scroll`, además de `sign_up` del servidor. | GA4 solo se carga con ID válido; los eventos del servidor no dependen del navegador. |

---

## 4. Copy principal

> **Deja de adivinar. Cobra con margen.**  
> Tu próximo presupuesto puede salir con coste real, margen, plazo y PDF listo para enviar. No una suma de líneas: una decisión de negocio que tu cliente entiende a la primera.

CTA: **«Quiero mi primer presupuesto hoy»**.  
Microcopy: **`N días gratis · sin tarjeta · sin cobro automático`**, generado desde `hay_prueba_gratuita()` / `dias_de_prueba()`. Si la prueba se apaga, la landing retira toda mención y pasa a llevar a `/pago` sin dejar de tener CTA.

---

## 5. Plan de medición y A/B

### Embudo a instrumentar de extremo a extremo

1. `landing_view` con `variante`, `mercado`, `intencion`.
2. `cta_click` por posición (`hero`, `nav`, `calculadora`, `activacion`, `tour`, `precios`, `final`, `sticky`).
3. `signup_start`: `/acceso?origen=landing_impulso&alta=1&variante=impulso`.
4. `signup_complete`: evento de servidor `sign_up` + `cuenta.registrada` con `origen_seccion`, `variante_landing`, `intencion_landing` y país.
5. `organization_created`, `first_budget_created`, `first_pdf_exported`.
6. Retención D1 / D7 / D30 y tiempo hasta el primer PDF.

### Protocolo

- **Una hipótesis por experimento.** Primera: «un hero de resultado + CTA única + valor antes del alta aumenta `signup_complete` sin reducir `first_pdf_exported`».
- Comparar `impulso` frente a `clasico` con tráfico simultáneo; la clásica está `noindex` para no contaminar SEO.
- Esperar **300–400 conversiones por variante** y al menos **dos ciclos semanales completos** antes de decidir; evitar parar en cuanto sube el CTR.
- Métrica primaria: altas completadas por visita. Métricas de guarda: altas que crean organización, primer presupuesto, primer PDF, D7, rebote móvil, LCP/INP/CLS y quejas de soporte.
- Si sube el clic pero baja la activación, el cambio no se acepta: el objetivo es registro **y** retención.
- Siguientes tests aislados: texto del CTA, orden de los tres chips, presencia de la calculadora y momento de aparición de la barra fija.

---

## 6. Contratos que se conservan

- `/` y `/xx/` mantienen título/H1/FAQ/cuerpo SEO por país, canónica, hreflang, `og:image`, 6 JSON-LD tras `</main>` y enlaces al catálogo de precios.
- 23 mercados en el selector y en la tabla; los cinco anglófonos entre los accesos directos.
- `class="plan destacado" href="/pago"`, `class="plan" href="/pago"`, precios 89/109 y 9,99/12,99, `mailto:`, legales, «Ver planes», «no facturas fiscales» y ausencia de «demostración».
- Prueba gratuita gobernada por `COTIZAT_DIAS_PRUEBA`: 14 días sigue diciendo 14; con `0` desaparece «gratis» y la CTA lleva a planes.
- CSP sin `on*=`, sin `style=`, con nonces y scripts diferidos; CSS crítico inline y `public.css` con `media="print"`.
- Selector de país, tour, cookies públicas, cambio de idioma y footer compartidos intactos.
- Suite completa de tests en verde.

---

## 7. Lecturas de referencia

Se consultaron fuentes primarias y synthesis de CRO/onboarding, sin trasladar porcentajes de terceros como promesas del producto:

- NN/g — onboarding, progressive disclosure, indicadores de progreso, personalización: https://www.nngroup.com/articles/onboarding-tutorials/ y https://www.nngroup.com/articles/usability-heuristics-complex-applications/
- FTC — norma final sobre reseñas y testimonios falsos (16 CFR Part 465): https://www.ftc.gov/legal-library/browse/rules/nonadvertising-consumer-reviews-testimonials-rule
- Google / Core Web Vitals — umbrales LCP, INP y CLS: https://web.dev/articles/vitals
- Baymard Institute — fricción en formularios: https://baymard.com/blog
- Unbounce / ContentVerve — copy de CTA en primera persona: https://unbounce.com/conversion-rate-optimization/cta-buttons/
- Userpilot / Appcues — time-to-value y activación en SaaS: https://userpilot.com/blog/time-to-value/ y https://www.appcues.com/blog/user-onboarding
- Nunes & Drèze — endowed progress effect: https://www.researchgate.net/publication/227426469_The_Endowed_Progress_Effect_How_Artificial_Advancement_Increases_Effort
- Iyengar & Lepper — sobrecarga de elección: https://www.researchgate.net/publication/232441910_When_Choice_is_Demotivating_Can_One_Desire_Too_Much_of_a_Good_Thing

> Nota: las cifras de conversión de estudios externos son direccionales y dependen del contexto. No se han usado para escribir promesas en la landing; las únicas cifras visibles son las del catálogo, los mercados, los precios y la duración real de la prueba.
