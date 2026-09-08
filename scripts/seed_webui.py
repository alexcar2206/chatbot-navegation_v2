#!/usr/bin/env python3
"""First-boot seed: download docs ZIP, create Knowledge Bases + workspace model via Open WebUI API."""

from __future__ import annotations

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


def model_exists(s: requests.Session, base: str, model_id: str) -> bool:
    r = s.get(f'{base}/api/v1/models/model', params={'id': model_id}, timeout=60)
    if r.status_code == 200 and r.json():
        return True
    return False


def download_zip(url: str, dest: Path) -> None:
    log.info('Downloading docs ZIP: %s', url)
    with requests.get(url, stream=True, timeout=600) as r:
        r.raise_for_status()
        with dest.open('wb') as f:
            for chunk in r.iter_content(chunk_size=1024 * 256):
                if chunk:
                    f.write(chunk)
    log.info('Downloaded %s (%s bytes)', dest, dest.stat().st_size)


def extract_zip(zip_path: Path, out_dir: Path) -> Path:
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(out_dir)
    # If ZIP has a single top-level dir wrapping everything, peel one layer for convenience
    children = [p for p in out_dir.iterdir() if p.name not in {'.', '..'}]
    if len(children) == 1 and children[0].is_dir():
        # Keep as-is: that single dir may be the only KB folder OR a wrapper.
        # Prefer treating immediate children of out_dir as groups when multiple dirs exist.
        pass
    return out_dir


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


def create_knowledge(s: requests.Session, base: str, name: str, description: str) -> dict:
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
            'suggestion_prompts': None,
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


def write_marker(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f'seeded_at={time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}\n', encoding='utf-8')
    log.info('Wrote seed marker %s', path)


def main() -> int:
    zip_url = os.getenv('SEED_DOCS_ZIP_URL', '').strip()
    if not zip_url:
        log.info('SEED_DOCS_ZIP_URL empty — skipping seed')
        return 0

    base = os.getenv('WEBUI_URL', 'http://open-webui:8080').rstrip('/')
    email = os.getenv('WEBUI_ADMIN_EMAIL', '').strip()
    password = os.getenv('WEBUI_ADMIN_PASSWORD', '').strip()
    model_id = os.getenv('SEED_MODEL_ID', 'asistente-navegacion-mino').strip()
    base_model_id = os.getenv('SEED_BASE_MODEL_ID', 'llama3.2:3b').strip()
    model_name = os.getenv('SEED_MODEL_NAME', 'Asistente Navegación Miño').strip()
    marker = Path(os.getenv('SEED_MARKER_PATH', '/data/.seed_webui_complete'))
    force = env_bool('SEED_FORCE', False)
    wait_timeout = int(os.getenv('SEED_WAIT_TIMEOUT', '900'))

    if not email or not password:
        log.error('WEBUI_ADMIN_EMAIL / WEBUI_ADMIN_PASSWORD required for seed')
        return 1

    if not force and marker.exists():
        log.info('Marker %s exists — seed already done', marker)
        return 0

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

    if not force and model_exists(s, base, model_id):
        log.info('Model %s already exists — skipping seed', model_id)
        write_marker(marker)
        return 0

    if force and model_exists(s, base, model_id):
        log.info('SEED_FORCE set but model %s already exists — exiting 0 (use down -v to reset)', model_id)
        write_marker(marker)
        return 0

    with tempfile.TemporaryDirectory(prefix='webui-seed-') as tmp:
        tmp_path = Path(tmp)
        zip_path = tmp_path / 'docs.zip'
        extract_dir = tmp_path / 'docs'
        extract_dir.mkdir()
        try:
            download_zip(zip_url, zip_path)
        except Exception as e:
            log.error('ZIP download failed: %s', e)
            return 1
        try:
            extract_zip(zip_path, extract_dir)
            groups = knowledge_groups(extract_dir)
        except Exception as e:
            log.error('ZIP extract / group failed: %s', e)
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
            for fp in files:
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
    log.info('Seed complete: model=%s knowledge=%s', model_id, len(knowledge_items))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        log.exception('Unhandled seed error: %s', e)
        sys.exit(1)
