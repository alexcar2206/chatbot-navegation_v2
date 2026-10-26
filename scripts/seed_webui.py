#!/usr/bin/env python3
"""First-boot seed: download docs ZIP, create Knowledge Bases + workspace model via Open WebUI API."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import sys
import tempfile
import time
import zipfile
from pathlib import Path

import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [webui-seed] %(levelname)s %(message)s',
    datefmt='%H:%M:%S',
)
log = logging.getLogger('webui-seed')

PUBLIC_READ_GRANT = [{'principal_type': 'user', 'principal_id': '*', 'permission': 'read'}]

SYSTEM_PROMPT = """Eres un asistente de ayuda sobre declaraciones responsables, autorizaciones y normativa de navegación en embalses (Miño / PONARS).

Responde ÚNICAMENTE con información presente en el contexto documental recuperado de las bases de conocimiento.
Si la respuesta no está en esos documentos, responde exactamente: "No consta en la documentación disponible."
No inventes normas, plazos, requisitos, embalses ni procedimientos.
Cuando sea posible, indica de qué documento o apartado sale la información.
Responde en español, de forma clara y breve."""

SUGGESTION_PROMPTS = [
    {
        'title': ['Zonas de navegación', 'Anexo 3 / embalse'],
        'content': (
            '¿Qué zonas del Anexo 3 aplican en el embalse de Belesar '
            'y qué restricciones de navegación hay según la documentación?'
        ),
    },
    {
        'title': ['Declaración responsable', 'requisitos'],
        'content': (
            '¿Qué datos y documentos necesito para una declaración responsable '
            'de navegación en embalses de la demarcación Miño-Sil?'
        ),
    },
    {
        'title': ['Plazos', 'vigencia ≤ 1 año'],
        'content': (
            '¿Cuál es el plazo máximo de una declaración responsable para embalses '
            '(opción ≤ 1 año) según la documentación disponible?'
        ),
    },
    {
        'title': ['Matrícula CHMS', 'formato'],
        'content': (
            '¿Qué formato tiene la matrícula CHMS y cuándo se considera '
            'ya asignada según la documentación?'
        ),
    },
    {
        'title': ['Autorización', 'frente a declaración'],
        'content': (
            '¿Cuándo hace falta una autorización frente a una declaración responsable '
            'para navegar en un embalse de la demarcación Miño-Sil?'
        ),
    },
    {
        'title': ['Mapa / coordenadas', 'zona autorizada'],
        'content': (
            '¿Cómo puedo comprobar si unas coordenadas están dentro de una zona '
            'de navegación autorizada del Anexo 3?'
        ),
    },
]

DOC_SUFFIXES = {
    '.pdf',
    '.txt',
    '.md',
    '.docx',
    '.doc',
    '.csv',
    '.json',
    '.html',
    '.htm',
}


def env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {'1', 'true', 'yes', 'on'}


def session_with_token(token: str) -> requests.Session:
    s = requests.Session()
    s.headers.update({'Authorization': f'Bearer {token}'})
    return s


def wait_for_webui(base: str, timeout_s: int) -> None:
    log.info('Waiting for Open WebUI at %s (timeout %ss)...', base, timeout_s)
    deadline = time.time() + timeout_s
    last_err = None
    while time.time() < deadline:
        try:
            r = requests.get(f'{base}/api/config', timeout=10)
            if r.status_code == 200:
                log.info('Open WebUI API is reachable')
                return
            last_err = f'HTTP {r.status_code}'
        except requests.RequestException as e:
            last_err = str(e)
        time.sleep(5)
    raise RuntimeError(f'Open WebUI not ready after {timeout_s}s: {last_err}')


def signin(base: str, email: str, password: str) -> str:
    log.info('Signing in as %s', email)
    r = requests.post(
        f'{base}/api/v1/auths/signin',
        json={'email': email, 'password': password},
        timeout=60,
    )
    if r.status_code != 200:
        raise RuntimeError(f'Signin failed ({r.status_code}): {r.text[:500]}')
    data = r.json()
    token = data.get('token')
    if not token:
        raise RuntimeError(f'Signin response missing token: {data!r}')
    return token


def get_model(s: requests.Session, base: str, model_id: str) -> dict | None:
    r = s.get(f'{base}/api/v1/models/model', params={'id': model_id}, timeout=60)
    if r.status_code == 200:
        data = r.json()
        if data:
            return data
    return None


def model_exists(s: requests.Session, base: str, model_id: str) -> bool:
    return get_model(s, base, model_id) is not None


def download_zip(url: str, dest: Path, expected_sha256: str = '') -> None:
    """Download the ZIP; if ``expected_sha256`` is set, abort on mismatch."""
    log.info('Downloading docs ZIP: %s', url)
    digest = hashlib.sha256()
    with requests.get(url, stream=True, timeout=600) as r:
        r.raise_for_status()
        with dest.open('wb') as f:
            for chunk in r.iter_content(chunk_size=1024 * 256):
                if chunk:
                    f.write(chunk)
                    digest.update(chunk)
    log.info('Downloaded %s (%s bytes, sha256=%s)', dest, dest.stat().st_size, digest.hexdigest())
    if expected_sha256 and digest.hexdigest().lower() != expected_sha256.lower():
        raise RuntimeError(
            f'docs ZIP checksum mismatch: expected {expected_sha256}, got {digest.hexdigest()}'
        )


def extract_zip(zip_path: Path, out_dir: Path) -> Path:
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(out_dir)
    return out_dir


def docs_pack_ready(path: Path) -> bool:
    if not path.is_dir():
        return False
    try:
        return any(path.iterdir())
    except OSError:
        return False


def ensure_docs_pack(zip_url: str, dest: Path, force: bool = False, expected_sha256: str = '') -> Path:
    """Download/extract the docs ZIP into dest (shared volume) for RAG + geo GDB.

    The new pack is fully downloaded and extracted next to ``dest`` before the
    old one is touched, so a failed download never leaves the volume without docs.
    """
    if docs_pack_ready(dest) and not force:
        log.info('docs_pack already present at %s', dest)
        return dest

    dest.parent.mkdir(parents=True, exist_ok=True)
    # Same filesystem as dest so the final swap is a cheap rename.
    with tempfile.TemporaryDirectory(prefix='.docs-pack-', dir=dest.parent) as tmp:
        tmp_path = Path(tmp)
        zip_path = tmp_path / 'docs.zip'
        extract_dir = tmp_path / 'docs'
        extract_dir.mkdir()
        download_zip(zip_url, zip_path, expected_sha256=expected_sha256)
        extract_zip(zip_path, extract_dir)

        if dest.exists():
            log.info('Replacing docs_pack at %s', dest)
            old = tmp_path / 'previous'
            dest.rename(old)
        extract_dir.rename(dest)

    log.info('Persisted docs_pack at %s', dest)
    return dest


def iter_doc_files(folder: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(folder.rglob('*')):
        if path.is_file() and path.suffix.lower() in DOC_SUFFIXES:
            files.append(path)
    return files


def knowledge_groups(root: Path) -> list[tuple[str, list[Path]]]:
    """Return (knowledge_name, files) groups from extracted ZIP root."""
    dirs = sorted(
        [p for p in root.iterdir() if p.is_dir() and not p.name.startswith('__') and p.name != '__MACOSX']
    )
    root_files = [p for p in root.iterdir() if p.is_file() and p.suffix.lower() in DOC_SUFFIXES]

    # Peel a single wrapper directory when it mainly contains subfolders of docs
    if len(dirs) == 1 and not root_files:
        wrapper = dirs[0]
        subdirs = sorted(
            [p for p in wrapper.iterdir() if p.is_dir() and not p.name.startswith('__') and p.name != '__MACOSX']
        )
        if subdirs:
            root = wrapper
            dirs = subdirs
            root_files = [
                p for p in wrapper.iterdir() if p.is_file() and p.suffix.lower() in DOC_SUFFIXES
            ]

    groups: list[tuple[str, list[Path]]] = []
    if dirs:
        for d in dirs:
            files = iter_doc_files(d)
            if files:
                groups.append((d.name, files))
        if root_files:
            groups.append(('Documentación adicional', root_files))
    elif root_files:
        groups.append(('Documentación navegación', root_files))

    if not groups:
        raise RuntimeError(f'No document files found under {root}')
    return groups


def find_knowledge_by_name(s: requests.Session, base: str, name: str) -> dict | None:
    """Return an existing knowledge base with this exact name (paginated listing)."""
    page = 1
    seen = 0
    while True:
        r = s.get(f'{base}/api/v1/knowledge/', params={'page': page}, timeout=60)
        if r.status_code != 200:
            raise RuntimeError(f'knowledge list failed ({r.status_code}): {r.text[:500]}')
        data = r.json() or {}
        items = data.get('items') or []
        for item in items:
            if item.get('name') == name[:200]:
                return item
        seen += len(items)
        if not items or seen >= int(data.get('total') or 0):
            return None
        page += 1


def create_knowledge(s: requests.Session, base: str, name: str, description: str) -> dict:
    # Idempotent: a previous seed that failed half-way must not duplicate KBs.
    existing = find_knowledge_by_name(s, base, name)
    if existing and existing.get('id'):
        log.info('Reusing existing knowledge base: %s (%s)', name, existing['id'])
        return existing
    log.info('Creating knowledge base: %s', name)
    r = s.post(
        f'{base}/api/v1/knowledge/create',
        json={
            'name': name[:200],
            'description': description[:1000],
            'access_grants': PUBLIC_READ_GRANT,
        },
        timeout=120,
    )
    if r.status_code not in (200, 201):
        raise RuntimeError(f'knowledge/create failed ({r.status_code}): {r.text[:500]}')
    data = r.json()
    if not data or not data.get('id'):
        raise RuntimeError(f'knowledge/create returned unexpected body: {data!r}')
    return data


def knowledge_filenames(s: requests.Session, base: str, knowledge_id: str) -> set[str]:
    """Filenames already attached to a knowledge base (to resume a partial seed)."""
    names: set[str] = set()
    page = 1
    while True:
        r = s.get(
            f'{base}/api/v1/knowledge/{knowledge_id}/files',
            params={'page': page, 'limit': 200},
            timeout=60,
        )
        if r.status_code != 200:
            raise RuntimeError(f'knowledge files list failed ({r.status_code}): {r.text[:500]}')
        data = r.json() or {}
        items = data.get('items') or []
        names.update(item.get('filename') or (item.get('meta') or {}).get('name') or '' for item in items)
        if not items or len(names) >= int(data.get('total') or 0):
            return {n for n in names if n}
        page += 1


def upload_file_to_knowledge(
    s: requests.Session,
    base: str,
    knowledge_id: str,
    file_path: Path,
) -> None:
    log.info('  Uploading %s', file_path.name)
    metadata = json.dumps({'knowledge_id': knowledge_id})
    with file_path.open('rb') as fh:
        r = s.post(
            f'{base}/api/v1/files/',
            params={'process': 'true', 'process_in_background': 'false'},
            files={'file': (file_path.name, fh)},
            data={'metadata': metadata},
            timeout=600,
        )
    if r.status_code not in (200, 201):
        raise RuntimeError(f'file upload failed for {file_path.name} ({r.status_code}): {r.text[:500]}')


def wait_pending_clear(s: requests.Session, base: str, knowledge_id: str, timeout_s: int = 600) -> None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        r = s.get(f'{base}/api/v1/knowledge/{knowledge_id}/files/pending', timeout=60)
        if r.status_code != 200:
            log.warning('pending check HTTP %s: %s', r.status_code, r.text[:200])
            return
        payload = r.json()
        # API may return list or {items: [...]}
        if isinstance(payload, list):
            pending = payload
        elif isinstance(payload, dict):
            pending = payload.get('items') or payload.get('files') or []
        else:
            pending = []
        if not pending:
            log.info('No pending files for knowledge %s', knowledge_id)
            return
        log.info('Waiting for %s pending file(s)...', len(pending))
        time.sleep(5)
    log.warning('Timed out waiting for pending files on %s (continuing)', knowledge_id)


def create_model(
    s: requests.Session,
    base: str,
    model_id: str,
    base_model_id: str,
    name: str,
    knowledge_items: list[dict],
) -> None:
    log.info('Creating workspace model %s (base=%s)', model_id, base_model_id)
    body = {
        'id': model_id,
        'base_model_id': base_model_id,
        'name': name,
        'meta': {
            'description': 'Asistente RAG sobre declaraciones y normativa de navegación (seed automático).',
            'knowledge': knowledge_items,
            'suggestion_prompts': SUGGESTION_PROMPTS,
            'tags': [],
        },
        'params': {'system': SYSTEM_PROMPT},
        'access_grants': PUBLIC_READ_GRANT,
        'is_active': True,
    }
    r = s.post(f'{base}/api/v1/models/create', json=body, timeout=120)
    if r.status_code not in (200, 201):
        raise RuntimeError(f'models/create failed ({r.status_code}): {r.text[:800]}')
    log.info('Model created successfully')


def first_ollama_pull_model() -> str:
    """First model id from OLLAMA_PULL_MODELS (space- or comma-separated)."""
    raw = os.getenv('OLLAMA_PULL_MODELS', 'llama3.2:3b').strip()
    parts = [p.strip() for p in raw.replace(',', ' ').split() if p.strip()]
    return parts[0] if parts else 'llama3.2:3b'


def ensure_model(
    s: requests.Session,
    base: str,
    *,
    model_id: str,
    name: str,
    access_grants: list[dict],
    is_active: bool,
    description: str,
    hidden: bool = False,
) -> None:
    """Idempotent base-model override (base_model_id=null) for visibility / access grants.

    Use meta.hidden=True (with is_active=True) to hide from the chat selector without
    disabling the model — is_active=False removes it from the catalog and breaks
    workspace presets that use it as base_model_id.
    """
    if model_exists(s, base, model_id):
        log.info('Model %s already exists — skipping ensure', model_id)
        return

    log.info(
        'Ensuring base model override %s (is_active=%s, hidden=%s, public=%s)',
        model_id,
        is_active,
        hidden,
        bool(access_grants),
    )
    body = {
        'id': model_id,
        'base_model_id': None,
        'name': name,
        'meta': {
            'description': description,
            'suggestion_prompts': None,
            'tags': [],
            'hidden': hidden,
        },
        'params': {},
        'access_grants': access_grants,
        'is_active': is_active,
    }
    r = s.post(f'{base}/api/v1/models/create', json=body, timeout=120)
    if r.status_code not in (200, 201):
        raise RuntimeError(f'models/create ensure failed for {model_id} ({r.status_code}): {r.text[:800]}')
    log.info('Ensured model %s', model_id)


def ensure_base_models(
    s: requests.Session,
    base: str,
    *,
    base_model_id: str,
    ollama_model_id: str,
) -> None:
    """Register Groq base (public/hidden) and Ollama base (admin-only) for the assistant."""
    ensure_model(
        s,
        base,
        model_id=base_model_id,
        name=base_model_id,
        access_grants=PUBLIC_READ_GRANT,
        is_active=True,
        hidden=True,
        description='Public but hidden base for Asistente Navegación Miño (seed).',
    )
    if ollama_model_id != base_model_id:
        ensure_model(
            s,
            base,
            model_id=ollama_model_id,
            name=ollama_model_id,
            access_grants=[],
            is_active=True,
            description='Admin-only Ollama model for local testing (seed).',
        )


def _normalize_access_grants(grants: object) -> list[dict]:
    if not isinstance(grants, list) or not grants:
        return list(PUBLIC_READ_GRANT)
    out: list[dict] = []
    for g in grants:
        if not isinstance(g, dict):
            continue
        principal_type = g.get('principal_type')
        principal_id = g.get('principal_id')
        if not principal_type or principal_id is None:
            continue
        out.append(
            {
                'principal_type': principal_type,
                'principal_id': principal_id,
                'permission': g.get('permission') or 'read',
            }
        )
    return out or list(PUBLIC_READ_GRANT)


def sync_assistant_base_model(
    s: requests.Session,
    base: str,
    *,
    model_id: str,
    base_model_id: str,
    model_name: str,
) -> None:
    """Align workspace assistant base_model_id to SEED_BASE_MODEL_ID when it already exists."""
    existing = get_model(s, base, model_id)
    if not existing:
        log.info('Assistant %s not found — skip base sync', model_id)
        return

    current_base = existing.get('base_model_id')
    if current_base == base_model_id:
        log.info('Assistant %s already uses base %s', model_id, base_model_id)
        return

    log.info('Updating assistant %s base_model_id %s → %s', model_id, current_base, base_model_id)
    meta = existing.get('meta') or {}
    params = existing.get('params') or {}
    if not isinstance(meta, dict):
        meta = {}
    if not isinstance(params, dict):
        params = {}

    body = {
        'id': model_id,
        'base_model_id': base_model_id,
        'name': existing.get('name') or model_name,
        'meta': meta,
        'params': params,
        'access_grants': _normalize_access_grants(existing.get('access_grants')),
        'is_active': bool(existing.get('is_active', True)),
    }
    r = s.post(f'{base}/api/v1/models/model/update', json=body, timeout=120)
    if r.status_code != 200:
        raise RuntimeError(f'models/model/update failed ({r.status_code}): {r.text[:800]}')
    log.info('Assistant %s base synced to %s', model_id, base_model_id)


def write_marker(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f'seeded_at={time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}\n', encoding='utf-8')
    log.info('Wrote seed marker %s', path)




def regenerar_navegacion(s: requests.Session, base: str) -> None:
    """After docs_pack is on disk, rebuild geo_cache + DR plantilla (avoids lifespan race)."""
    for path, label in (
        ('/api/v1/mapa/regenerar', 'mapa geo'),
        ('/api/v1/declaracion/regenerar', 'declaracion plantilla'),
    ):
        try:
            r = s.post(f'{base}{path}', timeout=300)
            if r.status_code == 403:
                log.info('Skip %s regen (feature disabled): %s', label, r.text[:200])
                continue
            if r.status_code != 200:
                log.warning('%s regen HTTP %s: %s', label, r.status_code, r.text[:500])
                continue
            data = r.json() if r.content else {}
            log.info(
                '%s regen: ok=%s available=%s action=%s msg=%s',
                label,
                data.get('ok'),
                data.get('available'),
                data.get('action'),
                data.get('message'),
            )
        except requests.RequestException as e:
            log.warning('%s regen failed: %s', label, e)


def main() -> int:
    zip_url = os.getenv('SEED_DOCS_ZIP_URL', '').strip()
    if not zip_url:
        log.info('SEED_DOCS_ZIP_URL empty — skipping seed')
        return 0

    base = os.getenv('WEBUI_URL', 'http://open-webui:8080').rstrip('/')
    email = os.getenv('WEBUI_ADMIN_EMAIL', '').strip()
    password = os.getenv('WEBUI_ADMIN_PASSWORD', '').strip()
    model_id = os.getenv('SEED_MODEL_ID', 'asistente-navegacion-mino').strip()
    base_model_id = os.getenv('SEED_BASE_MODEL_ID', 'openai/gpt-oss-20b').strip()
    model_name = os.getenv('SEED_MODEL_NAME', 'Asistente Navegación Miño').strip()
    ollama_model_id = first_ollama_pull_model()
    marker = Path(os.getenv('SEED_MARKER_PATH', '/data/.seed_webui_complete'))
    docs_pack = Path(os.getenv('SEED_DOCS_PACK_PATH', '/data/docs_pack'))
    force = env_bool('SEED_FORCE', False)
    wait_timeout = int(os.getenv('SEED_WAIT_TIMEOUT', '900'))

    # Persist pack for map geo even when RAG seed was already completed.
    try:
        ensure_docs_pack(
            zip_url, docs_pack, force=force, expected_sha256=os.getenv('SEED_DOCS_ZIP_SHA256', '').strip()
        )
    except Exception as e:
        log.error('docs_pack persist failed: %s', e)
        return 1

    if not email or not password:
        log.error('WEBUI_ADMIN_EMAIL / WEBUI_ADMIN_PASSWORD required for seed')
        return 1

    wait_for_webui(base, wait_timeout)

    # Admin may be created slightly after API is up
    token = None
    for attempt in range(1, 31):
        try:
            token = signin(base, email, password)
            break
        except Exception as e:
            log.warning('Signin attempt %s failed: %s', attempt, e)
            time.sleep(5)
    if not token:
        log.error('Could not sign in as admin')
        return 1

    s = session_with_token(token)

    # New-chat prompt chips come from config.py defaults; the seed no longer
    # overwrites ui.prompt_suggestions, so admin customizations survive restarts.

    # Always regen after pack is ready (open-webui lifespan often ran before the ZIP extract).
    regenerar_navegacion(s, base)

    # Always keep Groq + Ollama bases registered and assistant base aligned to env.
    try:
        ensure_base_models(s, base, base_model_id=base_model_id, ollama_model_id=ollama_model_id)
        sync_assistant_base_model(
            s,
            base,
            model_id=model_id,
            base_model_id=base_model_id,
            model_name=model_name,
        )
    except Exception as e:
        log.error('Base model ensure/sync failed: %s', e)
        return 1

    if not force and marker.exists():
        log.info('Marker %s exists — RAG seed already done (docs_pack + regen + base sync done)', marker)
        return 0

    if not force and model_exists(s, base, model_id):
        log.info('Model %s already exists — skipping RAG seed (base sync done)', model_id)
        write_marker(marker)
        return 0

    if force and model_exists(s, base, model_id):
        log.info('SEED_FORCE set but model %s already exists — exiting 0 (use down -v to reset)', model_id)
        write_marker(marker)
        return 0

    try:
        groups = knowledge_groups(docs_pack)
    except Exception as e:
        log.error('docs_pack group failed: %s', e)
        return 1

    knowledge_items: list[dict] = []
    for name, files in groups:
        try:
            kb = create_knowledge(
                s,
                base,
                name=name,
                description=f'Documentación seed: {name}',
            )
        except Exception as e:
            log.error('Failed creating knowledge %s: %s', name, e)
            return 1
        kid = kb['id']
        try:
            already = knowledge_filenames(s, base, kid)
        except Exception as e:
            log.error('Could not list files of knowledge %s: %s', name, e)
            return 1
        for fp in files:
            if fp.name in already:
                log.info('  Skipping %s (already in knowledge base)', fp.name)
                continue
            try:
                upload_file_to_knowledge(s, base, kid, fp)
            except Exception as e:
                log.error('Upload failed: %s', e)
                return 1
        wait_pending_clear(s, base, kid)
        knowledge_items.append({'id': kid, 'name': kb.get('name') or name})

    try:
        create_model(s, base, model_id, base_model_id, model_name, knowledge_items)
    except Exception as e:
        log.error('Model create failed: %s', e)
        return 1

    write_marker(marker)
    log.info(
        'Seed complete: model=%s base=%s ollama=%s knowledge=%s docs_pack=%s',
        model_id,
        base_model_id,
        ollama_model_id,
        len(knowledge_items),
        docs_pack,
    )
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        log.exception('Unhandled seed error: %s', e)
        sys.exit(1)
