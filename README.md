# Chatbot Navegación Miño-Sil

Aplicación web para la **Confederación Hidrográfica del Miño-Sil**: asistente self-hosted (chat + RAG) para consultar normativa y zonas de navegación, con mapa y generación de declaración responsable.

Basado en [Open WebUI](https://github.com/open-webui/open-webui) (fork adaptado). Despliegue local con Docker Compose; sin CI/CD de release upstream.

## Qué incluye

- Chat con modelos locales (**Ollama**) o APIs compatibles con OpenAI
- Knowledge Bases y RAG sobre documentación del dominio
- Usuarios, roles, notas, workspace (modelos / knowledge / prompts) y analytics de administración
- **Mapa** (`/mapa`): zonas del Anexo 3 (clic, nombre, coordenadas o geolocalización)
- **Declaración responsable** (`/declaracion`): wizard MVP que genera el DOCX oficial
- Identidad visual **Río Miño** + cabecera institucional MITECO
- Idiomas: **es-ES**, **gl-ES**, **en-US**, **pt-PT**

## Seed y documentación

El servicio `webui-seed` (Docker Compose) descarga el ZIP de documentación (`SEED_DOCS_ZIP_URL`), crea Knowledge Bases, el modelo de workspace y deja el pack en `docs_pack`. El ZIP alimenta RAG, **mapa** (GDB → geo_cache) y **declaración** (DOCX editable → plantilla).

Flags principales: `ENABLE_MAPA=true`, `ENABLE_DECLARACION=true`. Tras el seed se regeneran geo_cache y la plantilla DR.

Funcionalidades desactivadas por defecto en este fork (canales, calendario, automatizaciones, plugins/tools, comunidad, etc.): ver [`.env.example`](.env.example).

### Probar la API de declaración (curl)

```bash
# Sustituir TOKEN por un JWT / API key válido
curl -s -H "Authorization: Bearer TOKEN" http://localhost:3000/api/v1/declaracion/status
curl -s -H "Authorization: Bearer TOKEN" http://localhost:3000/api/v1/declaracion/schema | head
curl -s -X POST -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" \
  -d @backend/open_webui/test/navegacion/fixtures/payload_dr.json -o Declaracion.docx \
  http://localhost:3000/api/v1/declaracion/generar
```

`/generar` admite cualquier usuario verificado con la feature activa. `/regenerar` (plantilla o geo) requiere **admin**.

## Arranque

### Desarrollo (recomendado) — hot reload

```bash
cp .env.dev.example .env.dev
# Rellenar WEBUI_SECRET_KEY y OPENAI_API_KEY en .env.dev
npm run dev:docker
```

- UI: http://localhost:5173
- API: http://localhost:8080
- Parar: `npm run dev:docker:down` (añade `-v` para borrar volúmenes)

Atajos: `dev:docker:seed`, `dev:docker:ollama`, `dev:docker:full`.

### Producción / demo

```bash
cp .env.example .env
./scripts/prod-up.sh --build -d
```

- Interfaz: http://localhost:3000 (o `OPEN_WEBUI_PORT`)
- Reset total: `docker compose -f docker-compose.yaml down -v`

### Login admin (pruebas locales)

Valores por defecto de `.env.example` / `.env.dev.example` (cámbialos fuera de local):

- Email: `admin@chatnavegation.local`
- Contraseña: `chatnavegation123`
- Nombre: `Admin`

## Identidad institucional

Logos tipográficos de respaldo en [`static/static/institucional/`](static/static/institucional/). Sustituye `cabecera-ministerio.svg` / `footer-gobierno.svg` (o añade PNG oficiales) según el manual de imagen de la AGE / MITECO.

## Licencia

Consulta [`LICENSE`](LICENSE) y [`LICENSE_HISTORY`](LICENSE_HISTORY). El código añadido en este fork (mapa, declaración, seed, marca CHMS, etc.) forma parte de este repositorio bajo esos términos salvo indicación contraria.
