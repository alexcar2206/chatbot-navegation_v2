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

## Arranque

Hay dos stacks Docker. Usa **desarrollo** para el día a día (hot reload) y **producción / demo** para validar el despliegue real.

### Desarrollo (recomendado) — hot reload

Stack: [`docker-compose.dev.yaml`](docker-compose.dev.yaml) + [`Dockerfile.dev`](Dockerfile.dev) (Vite HMR en `:5173`, uvicorn `--reload` en `:8080`). **Sin Ollama por defecto** (chat vía Groq).

El asistente de workspace `asistente-navegacion-mino` usa por defecto **Groq** `openai/gpt-oss-20b` (`SEED_BASE_MODEL_ID`) con RAG reducido (`RAG_TOP_K=1`, `CHUNK_SIZE=400`) para caber mejor en el free tier (~8K TPM). El seed alinea la base del asistente a ese valor aunque el entorno ya estuviera seedado.

```bash
cp .env.dev.example .env.dev
# Rellenar WEBUI_SECRET_KEY y OPENAI_API_KEY en .env.dev
npm run dev:docker
# o: ./scripts/dev-up.sh
```

- UI: [http://localhost:5173](http://localhost:5173)
- API: [http://localhost:8080](http://localhost:8080)
- Parar: `npm run dev:docker:down` (o `./scripts/dev-down.sh`; añade `-v` / `-- -v` para borrar volúmenes de desarrollo).

Atajos npm / perfiles:

```bash
npm run dev:docker              # backend + frontend
npm run dev:docker:seed         # + seed (docs / knowledge)
npm run dev:docker:ollama       # + Ollama (pon ENABLE_OLLAMA_API=true en .env.dev)
npm run dev:docker:full         # seed + Ollama
npm run dev:docker:down         # parar todo el stack dev

# Primera vez / rebuild de Dockerfile.dev (args van a up; --profile ya va bien colocado)
npm run dev:docker:full -- --build
# equivalente: ./scripts/dev-up.sh --build --profile seed --profile ollama
```

**Si Groq responde 429 (TPM):** abre un chat nuevo, espera ~10 s y reintenta. `RAG_TOP_K=1` aplica al reiniciar el backend; un `CHUNK_SIZE` nuevo solo afecta tras reindex (`dev:docker:down -v` + seed).

**Probar el mismo asistente con Ollama local:** pon `ENABLE_OLLAMA_API=true` en `.env.dev`, arranca con `npm run dev:docker:ollama` (o `dev:docker:full`). Como **admin**, Workspace → Models → Asistente Navegación Miño → Base Model = `llama3.2:3b` (admin-only; no aparece a usuarios). Para volver a la nube, reasigna la base a `openai/gpt-oss-20b` (o re-ejecuta el seed).

**PC con poca RAM (p. ej. 8 GB / sin GPU):** no uses `--profile ollama`. Limita la memoria de WSL2 si hace falta (`%UserProfile%\.wslconfig` → `memory=5GB`). El primer `docker compose build` de `Dockerfile.dev` puede tardar; los cambios de código posteriores no requieren rebuild de la imagen de producción.

Tras un fallo del backend, comprueba `curl http://localhost:8080/health` antes de confiar en http://localhost:5173. Si ves “Servidor Requerido”, el frontend está bien pero la API no responde (mira `docker compose -f docker-compose.dev.yaml logs backend`).

Alternativa sin Docker: `backend/dev.sh` + `npm run dev` en el host (mismo hot reload).

### Producción / demo

Stack: [`docker-compose.yaml`](docker-compose.yaml) (imagen completa, `ollama`, `ollama-init`, `webui-seed`).

```bash
cp .env.example .env   # ajustar secretos si hace falta (API keys, etc.)
./scripts/prod-up.sh --build -d
# o: docker compose -f docker-compose.yaml up --build -d
```

- Interfaz: [http://localhost:3000](http://localhost:3000) (o el puerto de `OPEN_WEBUI_PORT`).
- El primer arranque puede tardar: `ollama-init` descarga modelos y `webui-seed` indexa documentación / prepara `docs_pack`. Al terminar el seed regenera **geo_cache** y la **plantilla DR**.
- Reset total: `docker compose -f docker-compose.yaml down -v`.

### Login admin (pruebas locales)

Valores por defecto de [`.env.example`](.env.example) / [`.env.dev.example`](.env.dev.example) (cámbialos si expones el servicio fuera de tu máquina):

- Email: `admin@chatnavegation.local`
- Contraseña: `chatnavegation123`
- Nombre: `Admin`

## Licencia

Este proyecto se basa en Open WebUI. Consulta [`LICENSE`](LICENSE) y [`LICENSE_HISTORY`](LICENSE_HISTORY) para los términos aplicables. El código añadido en este fork (mapa, declaración responsable, seed de documentación, configuración de dominio, etc.) forma parte de este repositorio bajo esos mismos términos salvo indicación contraria.
