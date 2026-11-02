# 41 cuentas, 4 de pago: qué dice eso y qué se hace (02/11/2026)

Dato del titular: **41 cuentas activadas y 4 con plan de pago**. Este número
cambia el diagnóstico y desactiva parte del plan anterior. Este documento
sustituye el orden de prioridades de `PLAN_USUARIOS_DE_PAGO_2026-11-02.md`
(que queda como contexto del embudo y de la atribución).

## 1. La aritmética, sin adornos

| | Valor |
|---|---|
| Cuentas activadas | 41 |
| Con plan de pago | 4 |
| **Conversión cuenta → pago** | **9,8 %** |
| LTV (89 USD/año, 12 meses de vida) | 89 USD |
| CAC máximo con regla 3:1 | **30 USD por cliente** |
| Ingreso actual, si los 4 son anuales | **356 USD/año** |

Para 1 000 USD/mes hacen falta ~134 suscripciones anuales, o sea **multiplicar
por 33** el número de clientes de pago.

## 2. Lo que este dato descarta

- **No es un problema de producto.** Un SaaS de oficio con 9,8 % de conversión
  no está roto: 4 personas encontraron suficiente valor para pagar sin que
  nadie les llamara.
- **No es (solo) un problema de tráfico.** 49 clics en 7 días no explican 41
  cuentas. Las cuentas vienen de algo que Search Console no ve (WhatsApp,
  contactos directos, redes, pruebas concedidas). Duplicar el tráfico de
  Google duplicaría, como mucho, una parte pequeña de las altas.

## 3. Lo que este dato señala

**El agujero está entre «se registra» y «paga»: 37 cuentas.** Y dentro de ese
agujero hay tres causas posibles, con remedios opuestos:

| Causa | Cómo se reconoce | Remedio | Coste |
|---|---|---|---|
| No llega a usar el producto | No creó ni un presupuesto en la prueba | Presupuesto de ejemplo en el alta + onboarding al primer PDF | Días |
| Lo usa y no ve el valor | Creó presupuesto, no lo envió, no volvió | Mejorar el momento «PDF/WhatsApp» y el correo de la prueba | Días |
| Le ve el valor y no paga | Envió presupuestos y se acabó la prueba | Precio, momento del cobro y fricción del pago manual | Días |

**Ninguna de las tres se arregla con SEO.** Ese es el punto que cambia el
plan: de las tres palancas de costo decreciente —contenido (meses), producto
(días), monetización (horas)— el SEO es **la más cara y la más lenta**, y con
89 USD de LTV no hay margen para pagar tráfico.

## 4. Orden nuevo del trabajo

### A. Ahora (esta semana): cerrar el agujero de activación

1. **Saber en qué paso se caen las 37.** El panel ya tiene el embudo y ahora
   también «Qué página trae los registros». Falta el corte por paso: de las
   41, cuántas crearon presupuesto y cuántas lo enviaron.
2. **El alta crea un presupuesto de ejemplo** con partidas del país elegido.
   La primera pantalla deja de ser un formulario vacío y el usuario ve el
   producto funcionando en 30 segundos. Es la palanca más directa sobre «no
   llegó a usarlo».
3. **La prueba de 7 días es corta** para un producto que se usa «cuando sale
   la obra». Candidata a 14 días **solo si** los datos muestran que se cae
   entre el día 1 y el 7. Decidir con el punto A.1, no por intuición.

### B. Después (2 semanas): el precio

- **Anual primero.** A 89 USD/año el anual es el plan que paga; el mensual
  (9,99) da 120 USD/año si sobrevive 12 meses, pero la mayoría no dura.
- **Dejar de cobrar en el peor momento.** Hoy la prueba es sin tarjeta y el
  cobro llega con el servicio ya parado. Alternativa a probar con las 37:
  pedir tarjeta al final de la prueba con el primer mes al 50 %.
- **Quitar fricción al pago manual.** Hoy: transferencia/cripto → comprobante
  → revisión en 48 h. Cada paso pierde gente y el que se quedó sin servicio
  un viernes no vuelve. Medible en `pago.checkout_iniciado →
  pago.compra_registrada → licencia.activada`.

### C. Y solo si sobra capacidad: el SEO de catálogo

Los títulos de hub ya llevan el rango de precio (hecho hoy, ver §5) porque
costaba una línea. **No** se produce más catálogo: 787 fichas dan 21 clics y
el catálogo ya es el 76 % de las impresiones. Con 30 USD de CAC máximo, el
contenido tiene que ser casi gratis (lo es: ya está el catálogo) y apuntar a
quien busca «programa», no a quien busca «precio de la losa».

## 5. Lo aplicado hoy

| Cambio | Por qué |
|---|---|
| El `<title>` de los hubs de apartado lleva el rango real | `/en-ie/prices/lifts-and-platform-lifts`: 63 impresiones, posición 10,2, **cero clics**. Ahora: «Lifts and platform lifts: 750.02 EUR–1,991.17 EUR in Ireland». 1 045 apartados con rango real, así que hay masa para medir |
| La prueba gratis aparece junto al CTA de las fichas y hubs | El 90 % de las cuentas no paga: lo que decide es que la prueba **se empiece**, y el CTA no decía que existiera |
| `tools/analizar_embudo.py` | Convierte cuentas/pagos/visitas en conversión, LTV y CAC permitido, y lista las cuatro preguntas que hay que responder antes de elegir palanca |
| Atribución del alta (`?origen=`) | Responde «¿las 4 que pagan vinieron del catálogo o de la portada?». Sin eso, se optimiza lo que no importa |

## 6. Los cuatro números que hay que sacar del panel

De `/admin/analitica`, con ventana de 90 días:

1. **Cuántas de las 41 crearon al menos un presupuesto.** (Embudo, paso 3.)
2. **Cuántas lo enviaron.** (Paso 4.)
3. **Cuántas siguen entrando después de acabar la prueba.** (Actividad y
   cohortes.)
4. **Qué sección de origen traen las 4 que pagan.** (Tarjeta «Qué página trae
   los registros»; las anteriores a hoy saldrán «sin atribuir».)

Con esos cuatro se elige entre A.1, A.2 o B, y se deja de adivinar.
