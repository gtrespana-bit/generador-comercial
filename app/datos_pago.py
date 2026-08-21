"""Planes publicados y datos de pago manual (canales del titular).

Estos datos son deliberadamente públicos: se muestran en la página de pago a
cualquier cliente. Son los canales por los que el titular cobra el piloto
(E1-059: cobro manual). Cuando cambien, se actualizan aquí y se despliega;
no viven en la base de datos a propósito (un solo lugar de verdad, sin
migraciones por un número de teléfono nuevo).

Los planes mapean a la duración de licencia que concede ``crear_licencia``
(``app/services/licencias.py``): anual -> ``1a``, mensual -> ``1m``.
"""
from __future__ import annotations

#: Planes ofrecidos: importe en USD y duración de licencia al activar.
PLANES: dict[str, dict] = {
    "anual": {
        "nombre": "Plan anual",
        "importe": 89.0,
        "precio_antes": 109.0,
        "duracion_licencia": "1a",
        "etiqueta": "MÁS AHORRO",
        "ventajas": (
            "Todas las funciones incluidas",
            "Configuración asistida de tu empresa y catálogo",
            "Soporte directo por email",
            "Actualizaciones incluidas",
        ),
    },
    "mensual": {
        "nombre": "Plan mensual",
        "importe": 9.99,
        "precio_antes": 12.99,
        "duracion_licencia": "1m",
        "etiqueta": "SIN PERMANENCIA",
        "ventajas": (
            "Todas las funciones incluidas",
            "Sin permanencia: cancela cuando quieras",
            "Soporte directo por email",
        ),
    },
}

#: Clave del cobro automático con Stripe Checkout (tarjeta / Apple Pay /
#: Google Pay). No vive en ``METODOS_PAGO`` porque no pide comprobante ni
#: datos de verificación: Stripe confirma el pago por webhook.
METODO_STRIPE = "stripe"

STRIPE_FICHA: dict = {
    "nombre": "Tarjeta (Stripe)",
    "icono": "💳",
    "descripcion": (
        "Pago inmediato con tarjeta Visa, Mastercard, American Express, "
        "Apple Pay o Google Pay. La licencia se activa al confirmar el cobro."
    ),
    "datos": (),
    "verificacion": (),
}

#: Métodos de pago: qué se muestra al cliente y qué debe declarar al comprar.
#: ``datos`` son los datos públicos del titular para pagarle; ``verificacion``
#: son los campos que el comprador debe completar para rastrear su pago.
METODOS_PAGO: dict[str, dict] = {
    "pago_movil": {
        "nombre": "Pago móvil",
        "icono": "📱",
        "descripcion": (
            "Transferencia desde cualquier banco venezolano usando solo el "
            "número de teléfono. Rápido y sin comisiones."
        ),
        "datos": (
            ("Banco", "Banco Provincial"),
            ("Teléfono", "0412-6443099"),
            ("Titular (cédula/RIF)", "V-20794917"),
        ),
        "verificacion": (
            ("banco_origen", "Banco desde el que pagaste", "text", ""),
            ("numero_operacion", "Número de operación del pago móvil", "text", ""),
            ("fecha_pago", "Fecha del pago", "date", ""),
            ("nombre_titular", "Nombre de la persona que realizó el pago", "text", ""),
        ),
    },
    "binance": {
        "nombre": "Binance",
        "icono": "₿",
        "descripcion": (
            "Transferencia de criptomonedas vía ID de Binance. "
            "Aceptamos USDT (BEP-20 / TRC-20)."
        ),
        "datos": (
            ("ID de Binance", "1090042241"),
        ),
        "verificacion": (
            ("binance_id_origen", "Tu ID de Binance", "text", ""),
            ("hash_transaccion", "Hash o ID de la transferencia", "text", ""),
            ("fecha_pago", "Fecha del pago", "date", ""),
            ("nombre_titular", "Nombre de la persona que realizó el pago", "text", ""),
        ),
    },
    "kontigo": {
        "nombre": "Kontigo",
        "icono": "💳",
        "descripcion": (
            "Billetera digital venezolana. Recarga y paga desde la "
            "aplicación Kontigo al instante."
        ),
        "datos": (
            ("Teléfono / ID de Kontigo", "+58412-3215016"),
        ),
        "verificacion": (
            ("telefono_origen", "Tu teléfono o ID de Kontigo", "text", ""),
            ("numero_operacion", "Número de operación", "text", ""),
            ("fecha_pago", "Fecha del pago", "date", ""),
            ("nombre_titular", "Nombre de la persona que realizó el pago", "text", ""),
        ),
    },
    "usdt": {
        "nombre": "USDT (TRC-20)",
        "icono": "🪙",
        "descripcion": (
            "Transferencia directa de USDT a nuestra wallet en la red TRC-20 "
            "de Tron."
        ),
        "datos": (
            ("Red", "TRC-20 (Tron)"),
            ("Dirección de wallet", "TPFa5x7jsUk4qw8Qfm1R1XXbPPCPRj8ZXy"),
        ),
        "verificacion": (
            ("wallet_origen", "Tu dirección de wallet de origen", "text", ""),
            ("hash_transaccion", "TXID o hash de la transacción", "text", ""),
            ("fecha_pago", "Fecha del pago", "date", ""),
            ("nombre_titular", "Nombre de la persona que realizó el pago", "text", ""),
        ),
    },
}

#: Estados posibles de una compra registrada.
ESTADOS_COMPRA = ("pendiente", "activa", "rechazada")

#: Cookie que recuerda el plan que la persona quería comprar antes de tener
#: que crear su cuenta y su organización. Es la que permite retomar la compra
#: en el panel después del alta, en vez de perder la intención en el camino
#: (registro → confirmación de email → alta de empresa → onboarding).
PLAN_PENDIENTE_COOKIE = "cotizat_plan_pendiente"


def plan_info(plan: str) -> dict:
    """Devuelve la ficha de un plan o lanza KeyError si no existe."""
    return PLANES[plan]


def metodo_info(metodo: str) -> dict:
    """Devuelve la ficha de un método o lanza KeyError si no existe."""
    if metodo == METODO_STRIPE:
        return STRIPE_FICHA
    return METODOS_PAGO[metodo]


def metodo_conocido(metodo: str) -> bool:
    """True si el método es un cobro manual publicado o Stripe."""
    return metodo == METODO_STRIPE or metodo in METODOS_PAGO
