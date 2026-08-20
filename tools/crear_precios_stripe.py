"""Crea (o localiza) los precios recurrentes de Stripe para CotizaT.

Crea un Producto «CotizaT» con dos Prices recurrentes en USD —anual 89,00 y
mensual 9,99— y devuelve sus ``price_...`` para pegar en el despliegue:

    STRIPE_PRICE_ANUAL=price_...
    STRIPE_PRICE_MENSUAL=price_...

Es idempotente: identifica cada precio por su ``lookup_key``, así que se puede
volver a ejecutar sin duplicar nada.

Uso (con la clave secreta en el entorno):

    STRIPE_SECRET_KEY=sk_test_... python tools/crear_precios_stripe.py
"""
from __future__ import annotations

import os
import sys


PRODUCTO = "CotizaT"
PLANES = [
    {
        "lookup_key": "cotizat_anual",
        "nombre": "Plan anual",
        "precio_usd": 89.00,
        "intervalo": "year",
    },
    {
        "lookup_key": "cotizat_mensual",
        "nombre": "Plan mensual",
        "precio_usd": 9.99,
        "intervalo": "month",
    },
]


def main() -> int:
    clave = str(os.environ.get("STRIPE_SECRET_KEY", "") or "").strip()
    if not clave:
        print("Falta STRIPE_SECRET_KEY en el entorno.", file=sys.stderr)
        return 1

    import stripe

    stripe.api_key = clave

    # Producto único (busca por nombre, crea si no existe).
    productos = stripe.Product.search(query=f"name:'{PRODUCTO}'")
    if productos.data:
        producto_id = productos.data[0]["id"]
    else:
        producto_id = stripe.Product.create(name=PRODUCTO).id
    print(f"Producto: {producto_id}")

    for plan in PLANES:
        existentes = stripe.Price.list(lookup_keys=[plan["lookup_key"]], active=True)
        if existentes.data:
            precio_id = existentes.data[0]["id"]
        else:
            precio_id = stripe.Price.create(
                product=producto_id,
                currency="usd",
                unit_amount=int(round(plan["precio_usd"] * 100)),
                recurring={"interval": plan["intervalo"]},
                lookup_key=plan["lookup_key"],
            ).id
        print(
            f"{plan['nombre']:>12}  {plan['precio_usd']:>7.2f} US$/{plan['intervalo']}  "
            f"{precio_id}  (lookup_key={plan['lookup_key']})"
        )

    print("\nCopia en el despliegue (Vercel → Settings → Environment Variables):")
    for plan in PLANES:
        existentes = stripe.Price.list(lookup_keys=[plan["lookup_key"]], active=True)
        variable = {
            "cotizat_anual": "STRIPE_PRICE_ANUAL",
            "cotizat_mensual": "STRIPE_PRICE_MENSUAL",
        }[plan["lookup_key"]]
        print(f"{variable}={existentes.data[0]['id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
