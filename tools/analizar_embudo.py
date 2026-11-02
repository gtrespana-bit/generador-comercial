"""Qué se puede medir con el embudo, con los números del titular.

Contexto (02/11/2026): 41 cuentas activadas y 4 con plan de pago. El dato
cambia el diagnóstico entero:

- **9,8 % de activación → pago** no es un mal producto. Es un producto con
  un problema concreto de activación y de precio percibido.
- El tráfico no es la restricción principal: 49 clics en 7 días no explican
  41 cuentas (las cuentas no vienen todas de Google; hay que verlas
  atribuidas por sección).

De ahí la regla de esta herramienta: **medir el embudo, no el tráfico**. Si
se mira solo el SEO, se optimiza la parte que no decide el ingreso.
"""
from __future__ import annotations

import argparse
import math
import sys

#: Precio de los planes publicados (`app/datos_pago.py`): mensual y anual.
#: Se repiten aquí a propósito para que la herramienta funcione sin la base y
#: sin dependencias; si cambian los precios, cambian aquí y se nota.
PRECIO_MENSUAL = 9.99
PRECIO_ANUAL = 89.0


def ltv(anual: float, mensual: float, meses_activo: float) -> dict:
    """Valor de un cliente en su vida útil, con dos supuestos explícitos."""
    return {
        "anual": anual * max(meses_activo / 12, 0),
        "mensual": mensual * max(meses_activo, 0),
        "nota": (
            "Vida útil asumida; cámbiala con --meses. Un SaaS de oficio sin "
            "datos de retención suele vivir entre 8 y 14 meses. Usar 12 es "
            "prudente, no optimista."
        ),
    }


def cac_permitido(ltv_anual: float, margen: float = 3.0) -> float:
    """Cuánto se puede gastar en conseguir un cliente y seguir siendo rentable.

    Regla sana para un negocio pequeño: el CAC no debe pasar de un tercio del
    LTV. No es una ley, es una vara para decidir si vale la pena pagar por
    tráfico.
    """
    return ltv_anual / margen


def embudo(cuentas: int, pagos: int, visitas: int | None = None) -> dict:
    """Los números del embudo y la conversión de cada salto."""
    if cuentas <= 0:
        return {}
    datos = {
        "cuentas": cuentas,
        "pagos": pagos,
        "conversion_cuenta_pago": 100 * pagos / cuentas,
        "sin_pagar": cuentas - pagos,
    }
    if visitas and visitas > 0:
        datos["visitas"] = visitas
        datos["visita_cuenta"] = 100 * cuentas / visitas
        datos["visita_pago"] = 100 * pagos / visitas
    # Para duplicar los clientes hay dos caminos: duplicar visitas o doblar
    # la conversión. Se calcula qué hace falta en cada uno.
    datos["visitas_para_doblar"] = (
        math.ceil(visitas * 2) if visitas else None
    )
    datos["conversion_para_doblar"] = 2 * datos["conversion_cuenta_pago"]
    return datos


def informe(cuentas: int, pagos: int, visitas: int | None, meses: float) -> str:
    e = embudo(cuentas, pagos, visitas)
    if not e:
        return "Sin cuentas no hay embudo que medir."
    valor = ltv(PRECIO_ANUAL, PRECIO_MENSUAL, meses)
    cac = cac_permitido(valor["anual"])
    lineas = ["# Embudo real", ""]
    lineas.append(f"- Cuentas activadas: **{e['cuentas']}**")
    lineas.append(f"- Con plan de pago: **{e['pagos']}**")
    lineas.append(
        f"- Conversión cuenta → pago: **{e['conversion_cuenta_pago']:.1f} %** "
        f"({e['sin_pagar']} cuentas sin pagar)"
    )
    if e.get("visita_cuenta"):
        lineas.append(
            f"- Visita → cuenta: **{e['visita_cuenta']:.2f} %** "
            f"({e['visitas']} clics/semana) · Visita → pago: "
            f"**{e['visita_pago']:.2f} %**"
        )
    lineas.append("")
    lineas.append("## Qué cuesta cada cliente")
    lineas.append("")
    lineas.append(
        f"- LTV anual asumiendo {meses:.0f} meses de vida: "
        f"**{valor['anual']:.0f} USD** (mensual: {valor['mensual']:.0f} USD)"
    )
    lineas.append(
        f"- CAC máximo con regla 3:1: **{cac:.0f} USD** por cliente de pago"
    )
    lineas.append("")
    lineas.append("## Los dos caminos para duplicar clientes")
    lineas.append("")
    if e.get("visitas_para_doblar"):
        lineas.append(
            f"- **Doblar el tráfico**: pasar de {e['visitas']} a "
            f"~{e['visitas_para_doblar']} clics/semana. Con la posición media "
            "actual eso significa multiplicar por cuatro la superficie que "
            "rankea: semanas de trabajo."
        )
    lineas.append(
        f"- **Doblar la conversión**: pasar de "
        f"{e['conversion_cuenta_pago']:.1f} % a "
        f"{e['conversion_para_doblar']:.1f} %. Cuesta menos: las 37 cuentas "
        "que ya se registran existen, lo que falta es lo que pasa después."
    )
    lineas.append("")
    lineas.append("## Qué hace falta mirar antes de elegir")
    lineas.append("")
    lineas.append(
        "1. De las 37 sin pago, **cuántas llegaron a crear un presupuesto**. "
        "Si la mayoría no llegó, el problema es la activación, no el precio."
    )
    lineas.append(
        "2. **Cuándo se cayeron**: día 1 (no entendió), día 3–5 (no le vio "
        "valor) o al acabar la prueba (le vio valor y no quiso pagar)."
    )
    lineas.append(
        "3. **Cuántas volvieron después de la prueba**. Si vuelven a mirar sin "
        "pagar, el producto sirve y el precio/fricción es el freno."
    )
    lineas.append(
        "4. **De qué sección vinieron las 4 que pagan**. Si vienen de la "
        "portada y no del catálogo, producir más catálogo no es el camino."
    )
    return "\n".join(lineas)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--cuentas", type=int, required=True)
    parser.add_argument("--pagos", type=int, required=True)
    parser.add_argument(
        "--visitas", type=int, default=None,
        help="clics desde Google en el periodo comparable (GSC)",
    )
    parser.add_argument(
        "--meses", type=float, default=12.0,
        help="meses de vida útil asumidos para el LTV (por omisión 12)",
    )
    args = parser.parse_args(argv)
    print(informe(args.cuentas, args.pagos, args.visitas, args.meses))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
