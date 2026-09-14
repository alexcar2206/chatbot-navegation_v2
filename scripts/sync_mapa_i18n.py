#!/usr/bin/env python3
"""Sync Mapa UI i18n keys into every locale translation.json (idempotent).

Fills missing keys or empty-string values with real translations from
mapa_i18n_packs.py. Never overwrites non-empty existing values.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from mapa_i18n_packs import MAPA_KEYS, get_translations

REPO = Path(__file__).resolve().parents[1]
LOCALES_DIR = REPO / 'src' / 'lib' / 'i18n' / 'locales'


def sync_file(path: Path, locale: str) -> int:
    raw = path.read_text(encoding='utf-8')
    data = json.loads(raw)
    pack = get_translations(locale)
    updated = 0
    for key in MAPA_KEYS:
        current = data.get(key, None)
        if current is not None and current != '':
            continue
        value = pack.get(key) or key
        if not value:
            value = key
        data[key] = value
        updated += 1

    if updated:
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent='\t') + '\n',
            encoding='utf-8',
        )
    return updated


def main() -> int:
    if not LOCALES_DIR.is_dir():
        print(f'Locales dir not found: {LOCALES_DIR}', file=sys.stderr)
        return 1

    total_updated = 0
    files = 0
    empty_remaining = []
    for path in sorted(LOCALES_DIR.glob('*/translation.json')):
        locale = path.parent.name
        n = sync_file(path, locale)
        files += 1
        if n:
            print(f'{locale}: updated {n} keys')
            total_updated += n
        else:
            print(f'{locale}: ok (no changes)')

        data = json.loads(path.read_text(encoding='utf-8'))
        for key in MAPA_KEYS:
            if data.get(key, '') == '':
                empty_remaining.append((locale, key))

    print(f'Done: {files} files, {total_updated} keys updated')
    if empty_remaining:
        print('ERROR: empty values remain:', file=sys.stderr)
        for locale, key in empty_remaining[:20]:
            print(f'  {locale}: {key!r}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
