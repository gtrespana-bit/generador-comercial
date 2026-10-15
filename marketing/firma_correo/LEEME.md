# Firma de correo de CotizaT

Firma profesional para los correos de **Ruben Romero · Fundador · CotizaT**,
lista para pegar en Gmail, Outlook o Apple Mail.

| Archivo | Qué es |
|---|---|
| `firma.html` | **La firma.** Ábrelo en el navegador, cópialo y pégalo en el editor de firmas de tu cliente de correo. |
| `firma.txt` | La misma firma en texto plano, para clientes que no muestran HTML. |
| `vista-previa.png` | Cómo se ve (recreación de la firma con la tipografía de respaldo del correo). |
| `generar_assets.py` | Regenera `vista-previa.png` (Pillow + las fuentes del proyecto). |

El logotipo se carga por URL desde el **icono oficial que la web ya publica**:

- `https://cotizat.online/static/icono-192.png` (el que usa la firma)
- `https://cotizat.online/static/icono-512.png` (pantallas retina, vía `srcset`)

Son los mismos archivos del favicon y del manifiesto PWA, así que llevan
publicados desde antes: la firma **no depende de desplegar nada nuevo** y el
logo se ve en cuanto se pega en el cliente de correo. Si algún día quieres un
logotipo distinto solo para la firma, publica el PNG en
`app/static/` y cambia esas dos URLs en `firma.html`.

## Instalación

### Gmail

1. Abre `firma.html` con doble clic (se abre en el navegador).
2. Selecciona toda la firma con el ratón (desde el logotipo hasta la última
   línea) y copia con `Ctrl+C`.
3. Gmail → ⚙ **Configuración** → **Ver todos los ajustes** → **General** →
   **Firma** → **Crear nueva** → escribe un nombre (p. ej. «Soporte») → pega con
   `Ctrl+V`.
4. Baja hasta el final y pulsa **Guardar cambios**.

> El logotipo se carga desde cotizat.online, así que aparece en la vista previa
> y en los correos. Si al pegar ves un hueco, comprueba que la URL
> `https://cotizat.online/static/icono-192.png` abre en el navegador: si abre,
> el hueco lo pone el editor (Gmail a veces tarda en refrescar), no la imagen.

### Outlook (web o escritorio)

- **Outlook web:** Configuración → Correo → Redactar y responder → Firma →
  pegar la firma copiada del navegador.
- **Outlook de escritorio:** Archivo → Opciones → Correo → Firmas → **Nueva** →
  pegar. Si el formato se desordena, guarda `firma.html` en
  `%appdata%\Microsoft\Signatures\` y selecciónalo desde «Firma».

### Apple Mail

Ajustes → Firmas → crea una firma, arrastra dentro del recuadro la firma
copiada del navegador y **desmarca** «Ajustar siempre a tipografía
predeterminada» para que se conserven los colores.

## Editar los datos

Es HTML normal: cambia el texto que está entre etiquetas.

| Qué | Dónde en `firma.html` |
|---|---|
| Nombre | `>Ruben Romero</div>` |
| Cargo | `>Fundador · CotizaT</div>` |
| Descriptor | `>Presupuestos y control comercial…</div>` |
| Correo | el texto y el `href="mailto:…"` |
| Web | el texto y el `href="https://cotizat.online…"` |
| Llamada a la acción | `> Prueba gratis 7 días, sin tarjeta` |

Si añades un teléfono, copia la línea de contacto y usa
`<a href="tel:+34…">…</a>` o `https://wa.me/34…?text=…` para WhatsApp.

## Detalles deliberados

- **Tablas y CSS en línea:** es lo único que Outlook (que maqueta con el motor
  de Word) y Gmail renderizan igual. Nada de flexbox, `float` ni hojas de
  estilo: el `<style>` suele eliminarse en Gmail y Apple Mail.
- **Sin imagen incrustada:** Outlook bloquea el base64 dentro del HTML, así que
  el logotipo se sirve desde el dominio —el icono oficial
  `/static/icono-192.png`, que ya está publicado por el favicon y el manifiesto
  PWA—. El texto alt «CotizaT» cubre el caso de que el cliente bloquee imágenes
  remotas (comportamiento por omisión en muchos, y en Gmail con remitentes
  desconocidos).
- **Sin tipografías externas:** solo la pila del sistema con respaldo Arial /
  Helvetica; si el equipo no tiene Inter, la firma se ve igual de bien.
- **`utm_source=firma_correo` en el enlace a la web:** permite ver en Analytics
  cuántas visitas llegan por la firma sin que el texto visible cambie. Quita el
  parámetro si no lo quieres.
- **Sin imágenes de redes sociales ni avisos de confidencialidad:** alargan la
  firma y no aportan; se pueden añadir si hacen falta.

## Regenerar los recursos

```bash
python3 -m venv .venv-firma
.venv-firma/bin/pip install pillow
.venv-firma/bin/python marketing/firma_correo/generar_assets.py
```

Si cambias un dato de `firma.html`, actualiza también `DATOS` en
`generar_assets.py` para que `vista-previa.png` siga contando lo mismo.
