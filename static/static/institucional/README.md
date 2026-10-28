# Logos institucionales

La app carga estos dos SVG desde `/static/institucional/`:

- `cabecera-ministerio.svg`: cabecera del Ministerio para la Transición Ecológica y el Reto Demográfico. Se muestra en la banda blanca del login (`src/routes/auth/+page.svelte`) y en la portada del chat (`src/lib/components/chat/Placeholder.svelte`).
- `footer-gobierno.svg`: marca del Gobierno de España para el pie del sidebar (`src/lib/components/layout/Sidebar.svelte`). Se pinta en blanco vía CSS (`brightness-0 invert`).

Los SVG actuales son marcas tipográficas provisionales, sin escudo. Para usar los logos oficiales, sustituye el contenido de los ficheros manteniendo el mismo nombre y la extensión `.svg`.

`backend/open_webui/static/institucional/` guarda una copia espejo. Solo hace falta cuando el backend se sirve sin el build del frontend; en Docker el backend copia `static/` del build al arrancar. Si cambias un logo, actualiza las dos copias.

Si en algún momento se usan PNG en lugar de SVG, cambia las rutas en los tres componentes citados arriba.
