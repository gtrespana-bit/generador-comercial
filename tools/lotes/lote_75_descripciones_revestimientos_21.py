# -*- coding: utf-8 -*-
"""Descripciones — Revestimientos y acabados (21 y último): restauración
y mantenimiento. Cierra el capítulo.

Vocabulario aplicado:

· «Decapado» es stripping y el «decapante» es stripper; la pintura
  «reblandecida» es the softened paint.
· El «aclarado» es rinsing, y hay que hacerlo «sin dañar la piedra»,
  without damaging the stone.
· «Reintegración de faltantes» es reinstatement of the missing sections,
  la expresión de oficio para reponer lo que falta.
· «Paño» de papel tapiz es length, no bay: el bay es el de la pintura.
· «Abrir la fisura» antes de sellarla es opening up of the crack, porque
  una fisura cerrada no admite sellador.
· «Cristalizado» es crystallizing y «abrillantado» es buffing: dos
  operaciones distintas y en este orden.
· «Granito vaciado en sitio» es terrazzo, como en todo el capítulo.
· «Enlucido» es skim coat y el «afinado» final es finishing.
· «Masilla» en madera es wood filler, y «resane de golpes» es filling
  the knocks.
"""

LOTE = {
    "Decapado químico de capas de pintura existentes en paramento o carpintería, previo a un nuevo acabado. Incluye la aplicación del decapante, el retiro de la pintura reblandecida y la limpieza de la superficie. Medido por metro cuadrado decapado.":
        "Chemical stripping of existing paint layers on a substrate or carpentry, prior to a new finish. Includes applying the stripper, the removal of the softened paint and the cleaning of the surface. Measured per square meter stripped.",

    "Limpieza química de paramento de piedra natural para eliminar manchas, eflorescencias y contaminación. Incluye la aplicación del producto, el cepillado y el aclarado sin dañar la piedra. Medido por metro cuadrado limpiado.":
        "Chemical cleaning of a natural stone substrate to remove stains, efflorescence and pollution. Includes applying the product, the brushing and the rinsing without damaging the stone. Measured per square meter cleaned.",

    "Restauración de molduras decorativas de yeso, con reintegración de faltantes y acabado. Incluye la reposición de las molduras y el acabado. Medido por metro lineal restaurado.":
        "Restoration of decorative gypsum moldings, with the reinstatement of the missing sections and the finish. Includes the replacement of the moldings and the finish. Measured per meter restored.",

    "Reintegración de juntas de piso o enchapado de mármol, con limpieza y rejuntado con mortero adecuado. Incluye el vaciado de juntas y el rejuntado. Medido por metro cuadrado restaurado.":
        "Reinstatement of the joints of a marble floor or cladding, with cleaning and re-grouting with the appropriate mortar. Includes the raking out of the joints and the re-grouting. Measured per square meter restored.",

    "Restauración puntual de papel tapiz, con reposición de paños dañados y remate de juntas. Incluye la retirada del paño dañado y la reposición. Medido por metro cuadrado restaurado.":
        "Localized restoration of wallpaper, with the replacement of damaged lengths and finishing the joints. Includes the removal of the damaged length and the replacement. Measured per square meter restored.",

    "Aplicación de sellador hidrofugante y antimanchas sobre piso o enchapado de piedra natural. Incluye la limpieza previa y la aplicación del sellador protector. Medido por metro cuadrado tratado.":
        "Application of a water repellent and anti-stain sealer on a natural stone floor or cladding. Includes the previous cleaning and the application of the protective sealer. Measured per square meter treated.",

    "Sellado de fisuras en fachada con sellador elástico de poliuretano, previo al acabado. Incluye la apertura y limpieza de la fisura y la aplicación del sellador. Medido por metro lineal de fisura sellada.":
        "Sealing of cracks in a facade with an elastic polyurethane sealant, prior to the finish. Includes the opening up and cleaning of the crack and the application of the sealant. Measured per meter of crack sealed.",

    "Tratamiento fungicida de paramento afectado por moho o algas, con limpieza y aplicación del producto. Incluye la limpieza de la zona y la aplicación del fungicida para evitar la reaparición. Medido por metro cuadrado tratado.":
        "Fungicidal treatment of a substrate affected by mold or algae, with cleaning and application of the product. Includes the cleaning of the area and the application of the fungicide to prevent it from reappearing. Measured per square meter treated.",

    "Aplicación de protector anti-graffiti sobre fachada pintada. Incluye la limpieza previa y la aplicación del protector. Medido por metro cuadrado tratado.":
        "Application of an anti-graffiti protector on a painted facade. Includes the previous cleaning and the application of the protector. Measured per square meter treated.",

    "Restauración de carpintería de madera con decapado del acabado anterior, lijado y barnizado nuevo. Incluye el decapado, el lijado, el fondo y las dos manos de barniz. Medido por metro cuadrado restaurado.":
        "Restoration of wood carpentry with stripping of the previous finish, sanding and new varnishing. Includes the stripping, the sanding, the primer and the two coats of varnish. Measured per square meter restored.",

    "Cristalizado y abrillantado de piso de piedra natural o granito, para recuperar el brillo y la protección superficial. Incluye el pulido mecánico con abrasivos y el abrillantado final. Medido por metro cuadrado abrillantado.":
        "Crystallizing and buffing of a natural stone or granite floor, to recover the shine and the surface protection. Includes the mechanical polishing with abrasives and the final buffing. Measured per square meter polished.",

    "Reintegración de faltantes y pulido de piso de granito vaciado en sitio, para recuperar su acabado. Incluye el resane de las zonas dañadas y el pulido y abrillantado del conjunto. Medido por metro cuadrado restaurado.":
        "Reinstatement of missing sections and polishing of a terrazzo floor poured on site, to recover its finish. Includes the patching of the damaged areas and the polishing and buffing of the whole. Measured per square meter restored.",

    "Restauración de carpintería de madera con relleno de masilla, lijado y acabado. Incluye el resane de golpes, el lijado y el acabado. Medido por metro cuadrado restaurado.":
        "Restoration of wood carpentry with filling with wood filler, sanding and finishing. Includes the filling of the knocks, the sanding and the finish. Measured per square meter restored.",

    "Abrillantado de piso de mármol con pulido mecánico y cristalizado. Incluye el pulido, el cristalizado y el abrillantado final. Medido por metro cuadrado abrillantado.":
        "Buffing of a marble floor with mechanical polishing and crystallizing. Includes the polishing, the crystallizing and the final buffing. Measured per square meter polished.",

    "Restauración de piso de madera con lijado, resane de juntas y barnizado. Incluye el lijado, el resane y las dos manos de barniz. Medido por metro cuadrado restaurado.":
        "Restoration of a wood floor with sanding, filling of the joints and varnishing. Includes the sanding, the filling and the two coats of varnish. Measured per square meter restored.",

    "Limpieza y abrillantado de piso de granito, con pulido mecánico y protección. Incluye la limpieza, el pulido y el abrillantado. Medido por metro cuadrado abrillantado.":
        "Cleaning and buffing of a granite floor, with mechanical polishing and protection. Includes the cleaning, the polishing and the buffing. Measured per square meter polished.",

    "Restauración de enlucido de mortero de cal, con reintegración de las zonas dañadas y acabado. Incluye la reposición del mortero y el afinado. Medido por metro cuadrado restaurado.":
        "Restoration of a lime mortar skim coat, with the reinstatement of the damaged areas and the finish. Includes the replacement of the mortar and the finishing. Measured per square meter restored.",
}
