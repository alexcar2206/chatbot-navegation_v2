# Chatbot Navegación (Miño-Sil)

Fork de [Open WebUI](https://github.com/open-webui/open-webui) orientado a la navegación en la demarcación **Miño-Sil**: asistente self-hosted (chat + RAG) con documentación del dominio y herramientas propias.

## Qué es

Aplicación web para consultar normativa y zonas de navegación mediante un chatbot con recuperación de documentos (RAG), desplegable en local con Docker Compose.

## Base Open WebUI (resumen)

Este proyecto hereda la plataforma Open WebUI. Entre lo relevante:

- Chat con modelos locales (**Ollama**) o APIs compatibles con OpenAI
- Knowledge Bases y RAG sobre documentos
- Usuarios, roles y panel de administración
- Interfaz multilingüe (i18n)

Detalle completo de Open WebUI: [docs.openwebui.com](https://docs.openwebui.com/).

## Añadidos de este fork

- **Seed automático** (`webui-seed` en Docker Compose): descarga el ZIP de documentación (`SEED_DOCS_ZIP_URL`), crea Knowledge Bases, el modelo de workspace y deja el pack en `docs_pack` (`SEED_DOCS_PACK_PATH`).
- **Mapa** en `/mapa` (entrada en el sidebar): consulta zonas del Anexo 3 por nombre, clic en el mapa, coordenadas (EPSG:4326) o geolocalización. Requiere `ENABLE_MAPA=true` y la capa geo generada desde el GDB del pack (`REGENERAR_GEO_ON_START`). La UI del mapa está traducida en todos los locales; los mensajes de zona del backend pueden seguir en español; los **nombres de embalses no se traducen**.
- **Declaración responsable** en `/declaracion` (sidebar bajo Mapa): wizard MVP que genera el DOCX oficial. Flag `ENABLE_DECLARACION=true`. Tras el seed (`Seed complete`), `webui-seed` regenera geo_cache y la plantilla Jinja automáticamente (evita el race del primer arranque). Desde el mapa, si el embalse está en la lista MVP, puedes enviarlo al formulario.
  - **Borradores**: se guardan en el navegador (`localStorage`), aislados por usuario. No van al servidor ni se sincronizan entre dispositivos; al cambiar de cuenta en el mismo PC cada uno ve solo los suyos.
  - **Regenerar plantilla / geo**: `POST /api/v1/declaracion/regenerar` y `POST /api/v1/mapa/regenerar` requieren **admin** (el seed usa el token de administrador).
  - **Alcance MVP**: declarante sin representante, una embarcación, embalses de la lista (opción A) con plazo máximo de 1 año, seguro genérico y firma. No incluye representante, varias embarcaciones, ríos, régimen NRP de hasta 6 años ni variantes de seguro. El wizard muestra este aviso; revisa siempre el DOCX antes de presentarlo.

Variables de entorno: ver [`.env.example`](.env.example).

### Probar la API de declaración (curl)

Con el servicio en marcha, un usuario autenticado y la plantilla disponible:

```bash
# Sustituir TOKEN por un JWT / API key válido
curl -s -H "Authorization: Bearer TOKEN" http://localhost:3000/api/v1/declaracion/status
curl -s -H "Authorization: Bearer TOKEN" http://localhost:3000/api/v1/declaracion/schema | head
# Generar DOCX (body JSON con {"datos": { ... campos MVP ... }})
curl -s -X POST -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" \
  -d @payload_dr.json -o Declaracion.docx \
  http://localhost:3000/api/v1/declaracion/generar
```

`/generar` admite cualquier usuario verificado con la feature activa. Para forzar rebuild de plantilla o geo_cache hace falta un token **admin** en los endpoints `/regenerar`.

El ZIP de documentación alimenta: RAG (knowledge), **mapa** (GDB → geo_cache) y **declaración** (DOCX editable → plantilla).

## Arranque (Docker Compose)

El camino recomendado es el [`docker-compose.yaml`](docker-compose.yaml) de este repo (servicios `open-webui`, `ollama`, `ollama-init`, `webui-seed`).

```bash
cp .env.example .env   # ajustar secretos si hace falta (API keys, etc.)
docker compose build --no-cache
docker compose up -d
```

- Interfaz: [http://localhost:3000](http://localhost:3000) (o el puerto de `OPEN_WEBUI_PORT`).
- **Login admin (pruebas locales)** — valores por defecto de [`.env.example`](.env.example) (cámbialos si expones el servicio fuera de tu máquina):
  - Email: `admin@chatnavegation.local`
  - Contraseña: `chatnavegation123`
  - Nombre: `Admin`
- El primer arranque puede tardar: `ollama-init` descarga modelos y `webui-seed` indexa documentación / prepara `docs_pack` (usa esas mismas credenciales admin). Al terminar el seed regenera **geo_cache** y la **plantilla DR** (no hace falta reiniciar `open-webui` a mano).
- Reset total (borra volúmenes de datos y modelos locales): `docker compose down -v`.

## Licencia

Este proyecto se basa en Open WebUI. Consulta [`LICENSE`](LICENSE) y [`LICENSE_HISTORY`](LICENSE_HISTORY) para los términos aplicables. El código añadido en este fork (mapa, declaración responsable, seed de documentación, configuración de dominio, etc.) forma parte de este repositorio bajo esos mismos términos salvo indicación contraria.
