"""Planes publicados y datos de pago manual (canales del titular).

Estos datos son deliberadamente públicos: se muestran en la página de pago a
cualquier cliente. Son los canales por los que el titular cobra el piloto
(E1-059: cobro manual). Cuando cambien, se actualizan aquí y se despliega;
no viven en la base de datos a propósito (un solo lugar de verdad, sin
migraciones por un número de teléfono nuevo).

Los planes mapean a la duración de licencia que concede ``crear_licencia``
(``app/services/licencias.py``): anual -> ``1a``, mensual -> ``1m``.

Además de los canales manuales del piloto, existe el método ``stripe``
(cobro con tarjeta vía Stripe Checkout). Qué métodos se muestran en el
checkout depende del país del comprador (``METODOS_POR_PAIS``): Venezuela
mantiene los canales manuales y añade la tarjeta al final; el resto abre con
Stripe y deja la cripto manual como respaldo.
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
    #: Pago con tarjeta procesado por Stripe Checkout. No pide comprobante ni
    #: datos de verificación: el cliente sale a la página de pago de Stripe y
    #: la activación llega sola por webhook. Marca ``online`` para que el
    #: checkout muestre el botón «Pagar con tarjeta» en vez del formulario de
    #: comprobante.
    "stripe": {
        "nombre": "Tarjeta (Stripe)",
        "icono": "💳",
        "descripcion": (
            "Pago con tarjeta de crédito o débito internacional, procesado de "
            "forma segura por Stripe. Tu plan se activa automáticamente al "
            "confirmar el pago."
        ),
        "online": True,
        "datos": (),
        "verificacion": (),
    },
}

#: Qué métodos se muestran por país en el checkout. Venezuela conserva los
#: canales manuales del piloto y añade la tarjeta al final (para quien tenga
#: tarjeta internacional); el resto de mercados abre con Stripe y deja la
#: cripto manual como respaldo. ``*`` es el genérico para países sin ficha.
METODOS_POR_PAIS: dict[str, tuple[str, ...]] = {
    "VE": ("pago_movil", "binance", "kontigo", "usdt", "stripe"),
    "CO": ("stripe", "binance", "usdt"),
    "MX": ("stripe", "binance", "usdt"),
    "EC": ("stripe", "binance", "usdt"),
    "PE": ("stripe", "binance", "usdt"),
    "*": ("stripe", "usdt"),
}

#: Estados posibles de una compra registrada. ``cancelada`` es el estado de una
#: suscripción de Stripe dada de baja (``customer.subscription.deleted``).
ESTADOS_COMPRA = ("pendiente", "activa", "rechazada", "cancelada")

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
    return METODOS_PAGO[metodo]


def metodos_para_pais(codigo: str | None) -> dict[str, dict]:
    """Devuelve los métodos de pago del país, en el orden en que se muestran.

    Venezuela conserva los canales manuales y añade la tarjeta; los demás
    mercados abren con Stripe y dejan la cripto como respaldo. Un código
    desconocido o vacío cae en el genérico ``*`` (tarjeta + USDT), que es lo
    seguro para clientes de fuera de Venezuela.
    """
    codigo = str(codigo or "").strip().upper()
    claves = METODOS_POR_PAIS.get(codigo, METODOS_POR_PAIS["*"])
    return {clave: METODOS_PAGO[clave] for clave in claves if clave in METODOS_PAGO}


def es_metodo_online(metodo: str) -> bool:
    """True si el método se cobra en línea (Stripe) y no exige comprobante."""
    try:
        return bool(metodo_info(metodo).get("online"))
    except KeyError:
        return False
