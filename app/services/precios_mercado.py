

def resolver_precio_para_presupuesto(db: Session, recurso_id: int, pais_codigo: str,
                                     organizacion_id: int | None, moneda_presupuesto: str,
                                     tasa_mercado_a_usd: float | None = None,
                                     tasa_usd_presupuesto: float | None = None) -> dict:
    """Devuelve precio efectivo listo para una nueva descomposición.

    El precio de mercado se mantiene intacto y se entrega además convertido a
    la moneda contractual del presupuesto. Si falta una tasa, no inventa una
    conversión: devuelve ``requiere_tasa``.
    """
    from .monedas import convertir
    res = resolver_precio(db, recurso_id, pais_codigo, organizacion_id)
    if res.precio is None:
        return {"precio": None, "moneda": None, "origen": res.origen, "confianza": res.confianza, "aviso": res.aviso, "requiere_tasa": False}
    origen = res.moneda or "USD"
    destino = str(moneda_presupuesto or "USD").upper()
    try:
        convertido = convertir(res.precio, origen, destino,
                               tasa_usd_destino=tasa_usd_presupuesto,
                               tasa_usd_origen=tasa_mercado_a_usd)
        return {"precio": float(convertido), "moneda": destino, "origen": res.origen, "confianza": res.confianza, "aviso": res.aviso, "requiere_tasa": False}
    except ValueError:
        return {"precio": res.precio, "moneda": origen, "origen": res.origen, "confianza": res.confianza, "aviso": "Falta tasa para convertir el precio al presupuesto", "requiere_tasa": True}
