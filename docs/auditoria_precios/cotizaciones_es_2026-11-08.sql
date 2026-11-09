-- CotizaT — cotizaciones reales de España, lote 1 (2026-11-08).
-- Generado por tools/aplicar_cotizaciones_espana.py desde
-- docs/auditoria_precios/espana_decision_cotizaciones_2026-11-08.csv y la matriz
-- basedatos_partidas/salida/precios_recursos_espana.csv.
--
-- ALCANCE: solo las referencias nacionales ES (sin organizacion_id) de los
-- 5 recursos cotizados. NO TOCA precios propios de empresas ni otros países.
-- MONEDA: EUR, precios sin IVA (la tabla guarda la moneda de cada mercado).

BEGIN;

-- MT-CIELO-PVC: cotizacion_directa · adopta 18.01 EUR (Leroy Merlin, lámina alveolar Renolam y panel alero de 10 mm (consulta 2026-11-08))
UPDATE public.precios_recursos_mercado
   SET precio = 18.01,
       precio_min = 16.74,
       precio_max = 18.01,
       moneda = 'EUR',
       confianza = 'referencia',
       incluye_iva = 'no',
       fuente = 'Leroy Merlin, lámina alveolar Renolam y panel alero de 10 mm (consulta 2026-11-08)',
       fecha_consulta = DATE '2026-11-08',
       observaciones = 'Cotización real contrastada el 2026-11-08 (cotizacion_directa). Banda medida: 16.74-18.01 EUR/m2, precio adoptado 18.01 EUR/m2 sin IVA. Dos láminas de PVC de techo: alveolar blanco brillo a 20,25 €/m² y panel rígido de 10 mm a 21,79 €/m² IVA incluido, que son 16,74 y 18,01 €/m² sin IVA. Se adopta la mayor por ser el panel de 10 mm, más próximo al cielo raso. Falta la perfilería de remate que la ficha del recurso incluye y que el catálogo valora aparte como MT-PERFIL-REMATE: por eso el precio se queda en el extremo alto de lo medido en lugar de bajar al alveolar.'
 WHERE codigo_recurso = 'MT-CIELO-PVC'
   AND pais_codigo = 'ES'
   AND organizacion_id IS NULL;
-- MT-PERSIANA-ALU: cotizacion_directa · adopta 56.19 EUR (Avosdim, persiana enrollable de aluminio aislado con cinta (consulta 2026-11-08))
UPDATE public.precios_recursos_mercado
   SET precio = 56.19,
       precio_min = 53.27,
       precio_max = 67.99,
       moneda = 'EUR',
       confianza = 'referencia',
       incluye_iva = 'no',
       fuente = 'Avosdim, persiana enrollable de aluminio aislado con cinta (consulta 2026-11-08)',
       fecha_consulta = DATE '2026-11-08',
       observaciones = 'Cotización real contrastada el 2026-11-08 (cotizacion_directa). Banda medida: 53.27-67.99 EUR/m2, precio adoptado 56.19 EUR/m2 sin IVA. Persianas manuales con cajón, guías y cinta: 97,90 € una unidad de 1,44 m² y 119,90 € una de 1,86 m², que dan 67,99 y 64,46 €/m² con IVA y 56,19 y 53,27 €/m² sin IVA. El alcance coincide con el recurso, que también incluye cajón y accionamiento. Se adopta 56,19 porque es la unidad pequeña, la que peor precio por metro tiene.'
 WHERE codigo_recurso = 'MT-PERSIANA-ALU'
   AND pais_codigo = 'ES'
   AND organizacion_id IS NULL;
-- MT-SOPORTE-AC: cotizacion_directa · adopta 10.98 EUR (Leroy Merlin, soportes STAG 50x45 y 50x50 (consulta 2026-11-08))
UPDATE public.precios_recursos_mercado
   SET precio = 10.98,
       precio_min = 7.68,
       precio_max = 10.98,
       moneda = 'EUR',
       confianza = 'referencia',
       incluye_iva = 'no',
       fuente = 'Leroy Merlin, soportes STAG 50x45 y 50x50 (consulta 2026-11-08)',
       fecha_consulta = DATE '2026-11-08',
       observaciones = 'Cotización real contrastada el 2026-11-08 (cotizacion_directa). Banda medida: 7.68-10.98 EUR/ud, precio adoptado 10.98 EUR/ud sin IVA. Dos escuadras galvanizadas de la misma familia y unidad: 9,29 € (50x45) y 13,29 € (50x50) IVA incluido, que son 7,68 y 10,98 € sin IVA. Se adopta la de 50x50 porque el recurso ampara equipos de mayor tamaño. Ninguna incluye tacos ni antivibratorios: el catálogo los valora aparte como MT-PERNO-ANCLA y MT-SOPORTE-ANTIVIB. Sustituye el valor derivado 18,23 y desmiente la horquilla declarada 15-60, que estaba por encima del mercado.'
 WHERE codigo_recurso = 'MT-SOPORTE-AC'
   AND pais_codigo = 'ES'
   AND organizacion_id IS NULL;
-- MT-TRAMPA-GRASA: cotizacion_directa · adopta 169 EUR (Bomdesa, separador de grasas ECO 72 l, y Eurosur, separador de 55 l (consulta 2026-11-08))
UPDATE public.precios_recursos_mercado
   SET precio = 169,
       precio_min = 169,
       precio_max = 439.32,
       moneda = 'EUR',
       confianza = 'referencia',
       incluye_iva = 'no',
       fuente = 'Bomdesa, separador de grasas ECO 72 l, y Eurosur, separador de 55 l (consulta 2026-11-08)',
       fecha_consulta = DATE '2026-11-08',
       observaciones = 'Cotización real contrastada el 2026-11-08 (cotizacion_directa). Banda medida: 169.00-439.32 EUR/ud, precio adoptado 169.00 EUR/ud sin IVA. La horquilla declarada 60-150 €/ud queda desmentida por el mercado: el separador de grasas prefabricado más barato localizado, ECO UNE-EN 1825 de 72 l con tapa, cuesta 204,49 € con IVA, es decir 169,00 € sin IVA, y el modelo de 55 l bajo fregadero sube a 531,58 €. Se adopta el mínimo real. El recurso no declara capacidad, así que si la partida exige un separador de cocina de mayor caudal este precio se queda corto.'
 WHERE codigo_recurso = 'MT-TRAMPA-GRASA'
   AND pais_codigo = 'ES'
   AND organizacion_id IS NULL;
-- MT-VIDRIO-TEMP: banco_y_minorista · adopta 77.47 EUR (CYPE LVT010 (mt21vtt010e) y Plakglass, vidrio templado de 10 mm (consulta 2026-11-08))
UPDATE public.precios_recursos_mercado
   SET precio = 77.47,
       precio_min = 59.13,
       precio_max = 125.95,
       moneda = 'EUR',
       confianza = 'referencia',
       incluye_iva = 'no',
       fuente = 'CYPE LVT010 (mt21vtt010e) y Plakglass, vidrio templado de 10 mm (consulta 2026-11-08)',
       fecha_consulta = DATE '2026-11-08',
       observaciones = 'Cotización real contrastada el 2026-11-08 (banco_y_minorista). Banda medida: 59.13-125.95 EUR/m2, precio adoptado 77.47 EUR/m2 sin IVA. Se conserva el precio de la matriz porque las dos evidencias lo acotan por abajo y por arriba: el banco CYPE da 59,13 €/m² de material de 10 mm con canteado pero sin taladros, y la cristalería minorista da 125,95 €/m² sin IVA con mecanizado a medida. El recurso incluye perforaciones, que el banco no valora, de modo que el precio de la matriz cae entre ambos y no se sustituye: lo que cambia es la evidencia, que pasa de «sin ficha de banco» a dos fuentes reales que enmarcan el valor.'
 WHERE codigo_recurso = 'MT-VIDRIO-TEMP'
   AND pais_codigo = 'ES'
   AND organizacion_id IS NULL;

-- Comprobación: debe devolver 5 filas con la banda coherente.
SELECT codigo_recurso, precio, precio_min, precio_max, moneda, confianza,
       incluye_iva, fecha_consulta
  FROM public.precios_recursos_mercado
 WHERE codigo_recurso IN ('MT-CIELO-PVC', 'MT-PERSIANA-ALU', 'MT-SOPORTE-AC', 'MT-TRAMPA-GRASA', 'MT-VIDRIO-TEMP')
   AND pais_codigo = 'ES'
   AND organizacion_id IS NULL
 ORDER BY codigo_recurso;

COMMIT;
