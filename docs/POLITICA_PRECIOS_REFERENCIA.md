# Política de precios de referencia de Cotizat

## Propósito

Cotizat es un generador de ayuda para presupuestar. Sus precios nacionales no son promesas de precio exacto ni sustituyen la cotización del proveedor de la empresa.

## Presentación obligatoria

Todo precio nacional de referencia debe conservar:

- rango observado;
- valor de referencia sugerido;
- país y moneda;
- unidad y presentación;
- fecha de consulta;
- fuente;
- nivel de confianza;
- si incluye IVA;
- si incluye transporte;
- aviso de verificación.

## Mensaje visible recomendado

```text
Precio nacional de referencia: 28.000 COP/saco
Rango observado: 23.500–44.900 COP
Verifica este valor con tu proveedor, ciudad y volumen de compra.
```

## Jerarquía de uso

1. Precio personalizado de la empresa.
2. Precio nacional de referencia.
3. Precio base o regional de respaldo, siempre identificado.
4. Precio pendiente, cuando no existe una referencia razonable.

## Niveles

- `confirmado`: contrastado con fuente primaria o varias fuentes fiables.
- `referencia`: rango de mercado razonable, útil para iniciar un presupuesto.
- `provisional`: una fuente débil, extrapolación o dato con presentación pendiente de confirmar.
- `derivado`: calculado desde otros recursos.
- `pendiente`: no debe entrar silenciosamente en un cálculo.

## Responsabilidad del usuario

La empresa debe poder modificar el precio según:

- proveedor;
- ciudad;
- marca;
- calidad;
- volumen;
- transporte;
- negociación;
- disponibilidad;
- fecha.

Al guardar un valor personalizado se debe conservar el precio nacional como referencia original y registrar que el nuevo valor pertenece a la organización.

## No se debe afirmar

Nunca mostrar:

```text
Este material costará exactamente X.
```

Debe mostrarse:

```text
Precio orientativo de referencia.
Verifica con tu proveedor.
```
