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

Variables de entorno: ver [`.env.example`](.env.example).

## Arranque (Docker Compose)

El camino recomendado es el [`docker-compose.yaml`](docker-compose.yaml) de este repo (servicios `open-webui`, `ollama`, `ollama-init`, `webui-seed`).

```bash
cp .env.example .env   # rellenar WEBUI_ADMIN_PASSWORD (y API keys si aplica)
docker compose build --no-cache
docker compose up -d
```

- Interfaz: [http://localhost:3000](http://localhost:3000) (o el puerto de `OPEN_WEBUI_PORT`).
- El primer arranque puede tardar: `ollama-init` descarga modelos y `webui-seed` indexa documentación / prepara `docs_pack` para el mapa.
- Reset total (borra volúmenes de datos y modelos locales): `docker compose down -v`.

## Licencia

Este proyecto se basa en Open WebUI. Consulta [`LICENSE`](LICENSE) y [`LICENSE_HISTORY`](LICENSE_HISTORY) para los términos aplicables. El código añadido en este fork (mapa, seed de documentación, configuración de dominio, etc.) forma parte de este repositorio bajo esos mismos términos salvo indicación contraria.
