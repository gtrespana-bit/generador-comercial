"""Generador del bloque formulaico de Revestimientos y acabados.

309 de las 401 descripciones del capítulo siguen el patrón

    <cabeza>. Incluye <lista de trabajos>. Medido por <unidad>.

La cola de medición es un conjunto cerrado de 72 formas y la lista de
trabajos repite un puñado de fragmentos («la preparación del soporte»,
«el rejuntado», «las dos manos»). Sólo la cabeza es siempre distinta,
y es la que nombra el trabajo, así que es lo único que se traduce a mano.

Las cadenas que no salen por aquí son las que llevan una frase
explicativa entre la cabeza y el «Incluye»: ésas se traducen aparte.
"""
import json
import pathlib
import re

RAIZ = pathlib.Path(__file__).resolve().parent.parent

# ── colas de medición ─────────────────────────────────────────────────────
MEDIDO = {
    "Medido por metro cuadrado pintado.": "Measured per square meter painted.",
    "Medido por metro cuadrado ejecutado.": "Measured per square meter completed.",
    "Medido por metro cuadrado revestido.": "Measured per square meter covered.",
    "Medido por metro cuadrado enchapado.": "Measured per square meter tiled.",
    "Medido por metro cuadrado tratado.": "Measured per square meter treated.",
    "Medido por metro cuadrado recubierto.": "Measured per square meter coated.",
    "Medido por metro cuadrado de trasdosado terminado.": "Measured per square meter of lining completed.",
    "Medido por metro cuadrado frisado.": "Measured per square meter plastered.",
    "Medido por metro cuadrado restaurado.": "Measured per square meter restored.",
    "Medido por metro cuadrado de forro terminado.": "Measured per square meter of lining completed.",
    "Medido por metro cuadrado colocado.": "Measured per square meter laid.",
    "Medido por metro cuadrado preparado.": "Measured per square meter prepared.",
    "Medido por metro cuadrado reparado.": "Measured per square meter repaired.",
    "Medido en superficie realmente ejecutada, descontando huecos mayores de 1 m².":
        "Measured by the area actually completed, deducting openings over 1 m².",
    "Medido por metro lineal colocado.": "Measured per meter laid.",
    "Medido por metro cuadrado limpiado.": "Measured per square meter cleaned.",
    "Medido por metro cuadrado barnizado.": "Measured per square meter varnished.",
    "Medido por metro lineal de peldaño.": "Measured per meter of tread.",
    "Medido por metro cuadrado repintado.": "Measured per square meter repainted.",
    "Medido por metro cuadrado nivelado.": "Measured per square meter leveled.",
    "Medido por metro cuadrado enlucido.": "Measured per square meter skim coated.",
    "Medido por metro cuadrado aplicado.": "Measured per square meter applied.",
    "Medido por metro cuadrado tratado y pintado.": "Measured per square meter treated and painted.",
    "Medido por metro cuadrado abrillantado.": "Measured per square meter polished.",
    "Medido por metro cuadrado regularizado.": "Measured per square meter made level.",
    "Medido por metro lineal reparado.": "Measured per meter repaired.",
    "Medido en superficie realmente ejecutada.": "Measured by the area actually completed.",
    "Medido por metro lineal de remate.": "Measured per meter of trim.",
    "Medido por metro lineal de borde.": "Measured per meter of edge.",
    "Medido por metro lineal pintado.": "Measured per meter painted.",
    "Medido por metro cuadrado lacado.": "Measured per square meter lacquered.",
    "Medido por metro cuadrado picado.": "Measured per square meter hacked off.",
    "Medido por metro cuadrado imprimado.": "Measured per square meter primed.",
    "Medido por metro cuadrado resanado.": "Measured per square meter patched.",
    "Medido por metro cuadrado rasqueteado.": "Measured per square meter scraped back.",
    "Medido por metro lineal de esquina reparada.": "Measured per meter of corner repaired.",
    "Medido por metro cuadrado saneado.": "Measured per square meter made good.",
    "Medido por metro cuadrado repellado.": "Measured per square meter stuccoed.",
    "Medido por metro lineal regularizado.": "Measured per meter made level.",
    "Medido en longitud realmente colocada.": "Measured by the length actually laid.",
    "Medido por metro cuadrado pulido.": "Measured per square meter polished.",
    "Medido por metro cuadrado aplacado.": "Measured per square meter clad.",
    "Medido por metro lineal de friso.": "Measured per meter of frieze.",
    "Medido por metro cuadrado estucado.": "Measured per square meter skim coated.",
    "Medido por metro cuadrado de mural.": "Measured per square meter of mural.",
    "Medido por unidad de peldaño colocada.": "Measured per tread laid.",
    "Medido por metro lineal de nariz.": "Measured per meter of nosing.",
    "Medido por metro lineal de peldaño revestido.": "Measured per meter of tread covered.",
    "Medido por metro lineal de junta.": "Measured per meter of joint.",
    "Medido por metro lineal de pasamanos.": "Measured per meter of handrail.",
    "Medido por metro lineal de cajón.": "Measured per meter of box.",
    "Medido por metro cuadrado de paramento regularizado.": "Measured per square meter of wall face made level.",
    "Medido por metro cuadrado de superficie tratada.": "Measured per square meter of surface treated.",
    "Medido por reparación ejecutada.": "Measured per repair carried out.",
    "Medido en longitud realmente ejecutada.": "Measured by the length actually completed.",
    "Medido por metro lineal de cenefa.": "Measured per meter of border.",
    "Medido por unidad de registro.": "Measured per access panel.",
    "Medido por metro lineal de cierre.": "Measured per meter of closure.",
    "Medido por metro lineal de mocheta pintada.": "Measured per meter of reveal painted.",
    "Medido por metro lineal de franja pintada.": "Measured per meter of band painted.",
    "Medido por metro cuadrado retocado.": "Measured per square meter touched up.",
    "Medido en superficie realmente tratada, midiendo ambas caras por separado.":
        "Measured by the area actually treated, measuring both faces separately.",
    "Medido por metro lineal de tubería pintada.": "Measured per meter of pipe painted.",
    "Medido por hoja de puerta pintada.": "Measured per door leaf painted.",
    "Medido en superficie realmente tratada, desarrollando todas las caras.":
        "Measured by the area actually treated, taking every face.",
    "Medido por metro cuadrado teñido.": "Measured per square meter stained.",
    "Medido por metro cuadrado demarcado.": "Measured per square meter marked out.",
    "Medido por metro cuadrado sellado.": "Measured per square meter sealed.",
    "Medido por metro lineal ejecutado.": "Measured per meter completed.",
    "Medido por metro cuadrado decapado.": "Measured per square meter stripped.",
    "Medido por metro lineal restaurado.": "Measured per meter restored.",
    "Medido por metro lineal de fisura sellada.": "Measured per meter of crack sealed.",
}

# ── fragmentos de la lista de trabajos ────────────────────────────────────
# Se prueban de más largo a más corto para que «las dos manos de barniz»
# no se quede en «las dos manos» por haber sustituido antes.
FRAGMENTOS = {
    "la preparación del soporte": "preparation of the substrate",
    "la preparación de la superficie": "preparation of the surface",
    "la preparación de la madera": "preparation of the wood",
    "la preparación del paramento": "preparation of the wall face",
    "la preparación": "the preparation",
    "la humectación del soporte": "wetting the substrate",
    "el tratamiento de juntas": "the joint treatment",
    "el sellado de juntas": "sealing the joints",
    "el sellado de la junta": "sealing the joint",
    "el remate de juntas": "finishing the joints",
    "el remate de encuentros": "finishing the junctions",
    "el remate perimetral": "the perimeter trim",
    "el remate de bordes": "finishing the edges",
    "el remate": "the finishing",
    "el rejuntado": "grouting",
    "la colocación del panel": "fixing the panel",
    "la colocación del tablero": "fixing the board",
    "la colocación de los paneles": "fixing the panels",
    "la colocación de las láminas": "fixing the sheets",
    "la colocación de la pieza": "placing the piece",
    "la colocación con cortes": "laying with cut pieces",
    "la colocación": "laying",
    "el atornillado de la placa": "screwing the board",
    "la reposición de la placa": "replacing the board",
    "la placa": "the board",
    "la estructura suspendida": "the suspended framework",
    "la estructura separada del muro": "the framework held off the wall",
    "la estructura": "the framework",
    "las dos manos de barniz": "the two coats of varnish",
    "las dos manos de acabado": "the two finishing coats",
    "las dos manos de esmalte": "the two coats of enamel",
    "las dos manos de pintura": "the two coats of paint",
    "las dos manos de laca": "the two coats of lacquer",
    "las dos manos": "the two coats",
    "el fondo": "the primer",
    "la imprimación": "the priming",
    "el afinado de las aristas": "finishing the arrises",
    "el afinado": "the finishing",
    "el lijado": "sanding",
    "el alisado": "smoothing",
    "el pulido": "polishing",
    "el abrillantado final": "the final buffing",
    "el acabado": "the finish",
    "la limpieza de la superficie": "cleaning the surface",
    "la limpieza de la zona": "cleaning the area",
    "la limpieza por franjas": "cleaning in strips",
    "la limpieza previa": "the previous cleaning",
    "la limpieza": "the cleaning",
    "limpieza": "cleaning",
    "la aplicación del mortero": "applying the mortar",
    "la aplicación del sellador": "applying the sealer",
    "la aplicación del hidrofugante": "applying the water repellent",
    "la aplicación del tratamiento": "applying the treatment",
    "la aplicación del fondo": "applying the primer",
    "la aplicación de la pasta": "applying the filler",
    "la aplicación": "the application",
    "las maestras": "the screeds",
    "el vaciado": "the casting",
    "la retirada del material suelto": "removing the loose material",
    "la protección del entorno": "protecting the surroundings",
    "el encolado": "the gluing",
    "el relleno": "the filling",
    "la nivelación": "the leveling",
    "el tratamiento": "the treatment",
    "el replanteo del patrón": "setting out the pattern",
    "el replanteo": "the field layout",
    "la fijación del perfil": "fixing the profile",
    "la fijación del panel": "fixing the panel",
    "la fijación del rodapié": "fixing the baseboard",
    "la fijación de los anclajes": "fixing the anchors",
    "la lana": "the wool",
    "el corte de la zona": "cutting out the area",
}


def _lista(es: str) -> str | None:
    """Traduce «la preparación del soporte, la colocación y el rejuntado»."""
    partes = [p.strip() for p in re.split(r",\s*|\s+y\s+", es) if p.strip()]
    if not all(p in FRAGMENTOS for p in partes):
        return None
    if len(partes) == 1:
        return FRAGMENTOS[partes[0]]
    if len(partes) == 2:
        return f"{FRAGMENTOS[partes[0]]} and {FRAGMENTOS[partes[1]]}"
    return ", ".join(FRAGMENTOS[p] for p in partes[:-1]) + " and " + FRAGMENTOS[partes[-1]]


def despiezar(original: str) -> tuple[str, str, str] | None:
    """Separa cabeza, lista de trabajos y cola de medición."""
    m = re.match(r"^(?P<cab>[^.]+)\. Incluye (?P<lista>[^.]+)\. (?P<med>Medido [^.]+\.)$", original)
    if not m:
        return None
    return m.group("cab"), m.group("lista"), m.group("med")


if __name__ == "__main__":
    pend = json.loads((RAIZ / "tools/_pend_rev.json").read_text(encoding="utf-8"))
    cubiertas, sin_medido, sin_lista = [], [], []
    for s in pend:
        p = despiezar(s)
        if not p:
            continue
        _, lista, med = p
        if med not in MEDIDO:
            sin_medido.append(med)
        elif _lista(lista) is None:
            sin_lista.append(lista)
        else:
            cubiertas.append(s)
    print(f"patrón simple: {sum(1 for s in pend if despiezar(s))}")
    print(f"  con cola y lista conocidas: {len(cubiertas)}")
    print(f"  cola de medición desconocida: {len(set(sin_medido))}")
    for x in sorted(set(sin_medido)):
        print("     ", x)
    print(f"  lista desconocida: {len(sin_lista)}")


# ── cabezas del bloque cubierto ───────────────────────────────────────────
CABEZAS = {
 "Regularización de paramento interior con mortero de nivelación para corregir desniveles previo al acabado":
  "Leveling of an interior substrate with leveling mortar to correct unevenness prior to the finish",
 "Picado y limpieza de paramento deteriorado con eliminación del revestimiento suelto previo a la reparación":
  "Hacking off and cleaning of a deteriorated substrate, removing the loose covering prior to repair",
 "Aplicación de imprimación selladora o fondo fijador sobre paramento poroso previo a la pintura":
  "Application of a sealing primer or stabilizing primer to a porous substrate prior to painting",
 "Nivelación puntual de paramento con pasta de nivelación para alisar zonas irregulares previo al acabado":
  "Localized leveling of a substrate with leveling compound to smooth irregular areas prior to the finish",
 "Tratamiento antihumedad de paramento previo a la pintura, con aplicación de producto bloqueador de humedad":
  "Damp proofing treatment of a substrate prior to painting, with the application of a damp blocking product",
 "Preparación de soporte de madera para pintura, con lijado, limpieza y aplicación de fondo tapaporos":
  "Preparation of a wood substrate for painting, with sanding, cleaning and the application of a sanding sealer",
 "Preparación de soporte de yeso o enlucido con aplicación de sellador previo a la pintura":
  "Preparation of a plaster or skim coated substrate with the application of a sealer prior to painting",
 "Limpieza de paramento interior con agua a presión para eliminar suciedad y restos antes del acabado":
  "Cleaning of an interior substrate with pressurized water to remove dirt and debris before the finish",
 "Rasqueteado y retirada del friso o revestimiento existente deteriorado, dejando el soporte limpio para el nuevo acabado":
  "Scraping back and removal of the existing deteriorated stucco or covering, leaving the substrate clean for the new finish",
 "Preparación de soporte para la aplicación de microcemento, con regularización, imprimación y malla en juntas":
  "Preparation of the substrate for the application of microcement, with leveling, priming and mesh at the joints",
 "Eliminación de restos de adhesivo y pintura vieja en paramento, con decapante o raspado, previo al nuevo acabado":
  "Removal of adhesive residue and old paint from a substrate, with paint stripper or scraping, prior to the new finish",
 "Tratamiento de manchas de óxido en paramento de concreto, con limpieza y aplicación de producto pasivante":
  "Treatment of rust stains on a concrete substrate, with cleaning and the application of a passivating product",
 "Preparación de soporte metálico para pintura, con limpieza, lijado y aplicación de fondo anticorrosivo":
  "Preparation of a metal substrate for painting, with cleaning, sanding and the application of an anticorrosion primer",
 "Aplicación de friso de mortero sobre paramento de bloque de concreto, con maestras y afinado, de 1,5 cm de espesor":
  "Application of mortar stucco to a concrete block substrate, with screeds and finishing, 1.5 cm thick",
 "Repello de paramento exterior con mortero y acabado liso, listo para pintar":
  "Stucco base coat on an exterior substrate with mortar and a smooth finish, ready to paint",
 "Aplicación de friso de mortero en techo, con maestras y afinado":
  "Application of mortar stucco to a ceiling, with screeds and finishing",
 "Friso de nivelación de columnas y vigas de concreto para regularizar su superficie previo al acabado":
  "Leveling stucco on concrete columns and beams to make their surface even prior to the finish",
 "Aplicación de friso de mortero en zonas estrechas, mochetas y remates de vanos":
  "Application of mortar stucco in narrow areas, reveals and the finishing of openings",
 "Aplicación de friso de mortero sobre muro de piedra, regularizando la superficie previo al acabado":
  "Application of mortar stucco over a stone wall, making the surface even prior to the finish",
 "Enlucido de yeso sobre paramento de bloque, con maestras y acabado fino":
  "Gypsum skim coat over a block substrate, with screeds and a fine finish",
 "Enlucido de yeso sobre muro de ladrillo, con maestras y acabado fino":
  "Gypsum skim coat over a brick wall, with screeds and a fine finish",
 "Enchapado de paramento con pieza cerámica o porcelanato de junta mínima, en capa fina":
  "Tiling of a substrate with ceramic or porcelain tile with a minimal joint, in a thin bed",
 "Enchapado de paramento con pieza cerámica colocada en espiga, en capa fina":
  "Tiling of a substrate with ceramic tile laid in a herringbone pattern, in a thin bed",
 "Enchapado de paramento con pieza de formato largo (tipo metro o lamosa), en capa fina":
  "Tiling of a substrate with large format tile, in a thin bed",
 "Enchapado del frente de bañera con pieza cerámica o porcelanato, dejando registro de acceso":
  "Tiling of the bath front with ceramic or porcelain tile, leaving an access panel",
 "Enchapado de columna con pieza cerámica o porcelanato, en capa fina":
  "Tiling of a column with ceramic or porcelain tile, in a thin bed",
 "Enchapado de paramento con gres porcelánico técnico de gran resistencia, en capa fina":
  "Tiling of a substrate with high strength technical porcelain stoneware, in a thin bed",
 "Enchapado de paramento con pieza de piedra natural a junta seca, sin junta visible":
  "Cladding of a substrate with natural stone with a tight joint and no visible joint",
 "Enchapado de fachada con pieza de piedra natural fijada con anclaje mecánico puntual":
  "Cladding of a facade with natural stone fixed with local mechanical anchors",
 "Enchapado de mocheta o zócalo con pieza de mármol, en capa fina":
  "Tiling of a reveal or base with marble, in a thin bed",
 "Revestimiento de paramento con láminas o paneles de corcho, con su adhesivo y remates":
  "Covering of a substrate with cork sheets or panels, with their adhesive and trim",
 "Revestimiento de paramento con pieza de piedra decorativa ligera, en capa fina":
  "Covering of a substrate with lightweight decorative stone, in a thin bed",
 "Revestimiento de paramento con paneles 3D decorativos, con su adhesivo y remates":
  "Covering of a substrate with decorative 3D panels, with their adhesive and trim",
 "Revestimiento de paramento con lámina acrílica o policarbonato decorativo, con perfil de fijación":
  "Covering of a substrate with decorative acrylic or polycarbonate sheet, with a fixing profile",
 "Aplacado de paramento con lámina o panel metálico decorativo, con fijación mecánica":
  "Cladding of a substrate with decorative metal sheet or panel, with mechanical fixing",
 "Revestimiento de paramento con ladrillo visto decorativo (ladrillo caravista o plaqueta)":
  "Covering of a substrate with decorative facing brick (facing brick or brick slips)",
 "Revestimiento de paramento con paneles de madera acabados con laca, con su bastidor":
  "Covering of a substrate with lacquer finished wood panels, with their batten framework",
 "Revestimiento de paramento con fibra natural tejida (sisal, yute o bambú), con adhesivo y remates":
  "Covering of a substrate with woven natural fiber (sisal, jute or bamboo), with adhesive and trim",
 "Revestimiento de paramento con paneles o listones de bambú, con bastidor de fijación":
  "Covering of a substrate with bamboo panels or battens, with the fixing framework",
 "Revestimiento de paramento con tablero OSB decorativo, con bastidor y acabado":
  "Covering of a substrate with decorative OSB board, with the framework and the finish",
 "Revestimiento de paramento con gres porcelánico imitación madera, en capa fina":
  "Covering of a substrate with wood effect porcelain stoneware, in a thin bed",
 "Revestimiento de paramento con panel de metal expandido o malla decorativa, con fijación mecánica":
  "Covering of a substrate with expanded metal or decorative mesh panel, with mechanical fixing",
 "Revestimiento de paramento con plancha de melamina, con bastidor y remates":
  "Covering of a substrate with melamine sheet, with the framework and the trim",
 "Revestimiento de paramento con panel perforado acústico decorativo, con bastidor":
  "Covering of a substrate with decorative perforated acoustic panel, with the framework",
 "Afirmado de concreto aligerado con anime de poliestireno como relleno, para nivelación de pisos":
  "Lightweight concrete fill with polystyrene EPS as filler, for leveling floors",
 "Colocación de piso cerámico con guarda o cenefa perimetral de pieza decorativa, en capa fina":
  "Laying of a ceramic tile floor with a perimeter border of decorative tile, in a thin bed",
 "Colocación de piso de porcelanato rectificado de junta mínima, en capa fina":
  "Laying of a rectified porcelain tile floor with a minimal joint, in a thin bed",
 "Colocación de piso de mármol en placa de gran formato, en capa fina":
  "Laying of a marble floor in large format slabs, in a thin bed",
 "Colocación de piso de piedra natural a junta mínima, en capa fina":
  "Laying of a natural stone floor with a minimal joint, in a thin bed",
 "Colocación de piso de parquet encolado en espiga, sobre afirmado nivelado":
  "Laying of a glued parquet floor in a herringbone pattern, over a leveled fill",
 "Colocación de piso de bambú encolado sobre afirmado nivelado":
  "Laying of a glued bamboo floor over a leveled fill",
 "Colocación de piso de linóleo encolado sobre soporte nivelado":
  "Laying of a glued linoleum floor over a leveled substrate",
 "Colocación de rodapié de PVC, con su adhesivo y remates":
  "Fixing of a PVC baseboard, with its adhesive and trim",
 "Colocación de rodapié de piedra natural, con adhesivo y rejuntado":
  "Fixing of a natural stone baseboard, with adhesive and grouting",
 "Colocación de rodapié de aluminio, con fijación mecánica o adhesiva":
  "Fixing of an aluminum baseboard, with mechanical or adhesive fixing",
 "Colocación de rodapié de madera lacada, con fijación mecánica o adhesiva":
  "Fixing of a lacquered wood baseboard, with mechanical or adhesive fixing",
 "Colocación de rodapié de porcelanato rectificado, con adhesivo y junta mínima":
  "Fixing of a rectified porcelain baseboard, with adhesive and a minimal joint",
 "Revestimiento de peldaño de escalera con huella y contrahuella de granito o piedra prefabricada":
  "Covering of a stair tread with a granite or precast stone tread and riser",
 "Revestimiento del descansillo de escalera con pieza cerámica o porcelanato":
  "Covering of a stair landing with ceramic or porcelain tile",
 "Revestimiento de escalera completa (huellas, contrahuellas y remates) con porcelanato, en capa fina":
  "Covering of a complete stair (treads, risers and trim) with porcelain tile, in a thin bed",
 "Revestimiento de peldaño con pieza de piedra natural recuperada o laja, en capa fina":
  "Covering of a tread with reclaimed natural stone or flagstone, in a thin bed",
 "Revestimiento de rellano de escalera con pieza de piedra natural, en capa fina":
  "Covering of a stair landing with natural stone, in a thin bed",
 "Suministro y montaje de trasdosado autoportante de placa de yeso laminado de alta dureza de 12,5 mm, para paramentos sometidos a impacto y zonas de tránsito como pasillos y áreas comunes":
  "Supply and installation of a self-supporting lining of 12.5 mm high hardness gypsum board, for substrates subject to impact and circulation areas such as corridors and common areas",
 "Forro de placa de yeso laminado sobre estructura metálica para medianería, sin contacto directo con el muro vecino":
  "Lining of gypsum board on a metal framework for a party wall, without direct contact with the adjoining wall",
 "Forro de placa de cemento reforzada con fibra sobre estructura, para paramentos exteriores o expuestos":
  "Lining of fiber cement board on a framework, for exterior or exposed substrates",
 "Forro de placa de cemento reforzada con fibra en fachada, sobre estructura, como cerramiento ligero":
  "Lining of fiber cement board on a facade, on a framework, as a lightweight enclosure",
 "Reparación puntual de forro de placa de cemento dañado, con sustitución de la zona y sellado de juntas":
  "Localized repair of a damaged cement board lining, replacing the area and sealing the joints",
 "Cielo raso continuo de placa de yeso laminado de alta dureza, para zonas de tránsito y áreas comunes":
  "Continuous ceiling of high hardness gypsum board, for circulation areas and common areas",
 "Cielo raso continuo de placa de cemento reforzada con fibra para baños y áreas húmedas":
  "Continuous ceiling of fiber cement board for bathrooms and wet areas",
 "Reparación de cielo raso de yeso laminado dañado, con sustitución de la zona afectada y tratamiento de juntas":
  "Repair of a damaged gypsum board ceiling, replacing the affected area and treating the joints",
 "Cielo raso continuo de placa de yeso a doble altura, con estructura y placa en dos niveles":
  "Continuous gypsum board ceiling at double height, with the framework and the board on two levels",
 "Cielo raso continuo de placa de yeso laminado en foso de escalera, con estructura y placa":
  "Continuous gypsum board ceiling in a stairwell, with the framework and the board",
 "Cielo raso desmontable de fibra mineral con perfilería oculta, en retícula de 60x60":
  "Demountable mineral fiber ceiling with a concealed grid, on a 60x60 grid",
 "Cielo raso desmontable de lámina de aluminio lineal, con perfilería de suspensión":
  "Demountable linear aluminum strip ceiling, with the suspension system",
 "Cielo raso desmontable de fibra mineral de alta absorción acústica, con perfilería":
  "Demountable mineral fiber ceiling with high acoustic absorption, with the grid system",
 "Cielo raso de láminas de PVC para local comercial o área de servicio, con perfilería":
  "PVC sheet ceiling for commercial premises or service areas, with the grid system",
 "Cielo raso de paneles acústicos de madera, con estructura de fijación y remate":
  "Wood acoustic panel ceiling, with the fixing framework and the trim",
 "Cielo raso de tablero decorativo de madera sobre rastreles, con acabado":
  "Decorative wood board ceiling on battens, with the finish",
 "Colocación de perfil de cierre entre cielos rasos de distinta cota, como transición":
  "Fixing of a closure profile between ceilings at different levels, as a transition",
 "Aplicación de pintura intumescente ignífuga sobre estructura o paramento interior, con las capas necesarias para el grado de resistencia requerido":
  "Application of intumescent fire resistant paint to a structure or interior substrate, with the coats needed for the required fire resistance rating",
 "Aplicación de pintura acrílica lavable en paramentos de cocina, con dos manos":
  "Application of washable latex paint to kitchen walls, with two coats",
 "Aplicación de esmalte sobre estructura metálica interior, con fondo anticorrosivo y dos manos":
  "Application of enamel paint to an interior metal structure, with an anticorrosion primer and two coats",
 "Aplicación de pintura de caucho en techo con rodillo extensible, con dos manos":
  "Application of elastomeric paint to a ceiling with an extension roller, with two coats",
 "Aplicación de pintura satinada lavable en locales de alta humedad, con fondo antihumedad y dos manos":
  "Application of washable satin paint in high humidity premises, with a damp proof primer and two coats",
 "Aplicación de pintura de caucho o epóxica en sótano o garaje interior, con dos manos":
  "Application of elastomeric or epoxy paint in a basement or interior garage, with two coats",
 "Aplicación de pintura sobre concreto visto o superficie mineral exterior, con fondo sellador y dos manos":
  "Application of paint to exposed concrete or an exterior mineral surface, with a sealing primer and two coats",
 "Aplicación de hidrofugante previo y dos manos de pintura exterior en fachadas expuestas a lluvia":
  "Application of a water repellent first and two coats of exterior paint on facades exposed to rain",
 "Aplicación de pintura exterior en zócalo de fachada, con dos manos":
  "Application of exterior paint to the base of a facade, with two coats",
 "Aplicación de pintura exterior en cubierta o techo de superficie inclinada, con dos manos":
  "Application of exterior paint to a roof or a sloping ceiling surface, with two coats",
 "Aplicación de pintura exterior con acabado mate sobre fachada, con dos manos":
  "Application of flat exterior paint to a facade, with two coats",
 "Aplicación de hidrofugante a base de siloxano sobre fachada, permeable al vapor":
  "Application of a siloxane based water repellent to a facade, vapor permeable",
 "Aplicación de pintura exterior sobre muro de contención, con dos manos":
  "Application of exterior paint to a retaining wall, with two coats",
 "Aplicación de esmalte sobre portón o puerta metálica exterior, con fondo anticorrosivo y dos manos":
  "Application of enamel paint to an exterior metal gate or door, with an anticorrosion primer and two coats",
 "Aplicación de esmalte al agua sobre carpintería interior de madera, con fondo y dos manos":
  "Application of water based enamel paint to interior wood joinery, with a primer and two coats",
 "Aplicación de esmalte sintético sobre carpintería metálica exterior, con fondo anticorrosivo y dos manos":
  "Application of synthetic enamel paint to exterior metal joinery, with an anticorrosion primer and two coats",
 "Aplicación de esmalte sintético sobre carpintería de madera exterior, con fondo y dos manos":
  "Application of synthetic enamel paint to exterior wood joinery, with a primer and two coats",
 "Pintura de mueble de cocina con laca, con preparación y dos manos":
  "Painting of kitchen cabinets with lacquer, with the preparation and two coats",
 "Aplicación de esmalte sobre closet o mueble de madera, con fondo y dos manos":
  "Application of enamel paint to a closet or wood cabinet, with a primer and two coats",
 "Aplicación de esmalte o laca sobre persiana de madera, con fondo y dos manos":
  "Application of enamel paint or lacquer to a wooden roller shutter, with a primer and two coats",
 "Aplicación de esmalte sobre pasamanos o baranda metálica, con fondo anticorrosivo y dos manos":
  "Application of enamel paint to a metal handrail or guardrail, with an anticorrosion primer and two coats",
 "Aplicación de esmalte sobre puerta metálica, con fondo anticorrosivo y dos manos":
  "Application of enamel paint to a metal door, with an anticorrosion primer and two coats",
 "Aplicación de laca sobre carpintería interior de madera, con fondo y dos manos":
  "Application of lacquer to interior wood joinery, with a primer and two coats",
 "Barnizado de barandas y pasamanos de madera, con lijado y dos manos de barniz":
  "Varnishing of wood guardrails and handrails, with sanding and two coats of varnish",
 "Barnizado de puerta de madera interior, con lijado y dos manos de barniz":
  "Varnishing of an interior wood door, with sanding and two coats of varnish",
 "Aplicación de barniz protector sobre madera estructural interior, con dos manos":
  "Application of protective varnish to interior structural wood, with two coats",
 "Barnizado de mueble de madera exterior, con lijado y dos manos de barniz marino":
  "Varnishing of exterior wood furniture, with sanding and two coats of marine varnish",
 "Aplicación de laca sobre puertas de interior, con fondo y dos manos":
  "Application of lacquer to interior doors, with a primer and two coats",
 "Sellado de piso de concreto con sellador acrílico o de poliuretano, para protección y realce":
  "Sealing of a concrete floor with an acrylic or polyurethane sealer, for protection and enhancement",
 "Aplicación de recubrimiento epóxico en paramento de cocina industrial, resistente a grasas y limpieza":
  "Application of an epoxy coating to a commercial kitchen substrate, resistant to grease and cleaning",
 "Tratamiento de madera carcomida con consolidante e insecticida, previo a la restauración":
  "Treatment of wood damaged by wood-boring insects with a consolidant and an insecticide, prior to restoration",
 "Limpieza de paramento de ladrillo visto, con cepillado y lavado para eliminar suciedad y eflorescencias":
  "Cleaning of an exposed brick substrate, with brushing and washing to remove dirt and efflorescence",
 "Aplicación de hidrofugante sobre fachada de piedra natural o ladrillo visto, para repeler el agua sin impedir la transpiración":
  "Application of a water repellent to a natural stone or exposed brick facade, to repel water without stopping it from breathing",
 "Aplicación de hidrofugante sobre cubierta de teja, para repeler el agua y evitar la absorción":
  "Application of a water repellent to a tiled roof, to repel water and prevent absorption",
 "Aplicación de hidrofugante sobre paramento de concreto exterior, para repeler el agua":
  "Application of a water repellent to an exterior concrete substrate, to repel water",
}


def generar() -> dict[str, str]:
    pend = json.loads((RAIZ / "tools/_pend_rev.json").read_text(encoding="utf-8"))
    lote = {}
    for s in pend:
        p = despiezar(s)
        if not p or p[0] not in CABEZAS:
            continue
        lista = _lista(p[1])
        if lista is None or p[2] not in MEDIDO:
            continue
        lote[s] = f"{CABEZAS[p[0]]}. Includes {lista}. {MEDIDO[p[2]]}"
    return lote


if __name__ == "__main__":
    lote = generar()
    (RAIZ / "tools/_gen_rev.json").write_text(
        json.dumps(lote, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"generadas: {len(lote)} de 114")
    for k, v in list(lote.items())[:4]:
        print("  ES:", k[:90]); print("  EN:", v[:150]); print()
