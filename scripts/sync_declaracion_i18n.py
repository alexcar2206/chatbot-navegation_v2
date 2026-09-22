#!/usr/bin/env python3
"""Sync Declaración UI i18n keys into every locale translation.json (idempotent).

Fills missing keys or empty-string values. Never overwrites non-empty values.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from declaracion_i18n_packs import DECLARACION_KEYS, get_translations

REPO = Path(__file__).resolve().parents[1]
LOCALES_DIR = REPO / 'src' / 'lib' / 'i18n' / 'locales'


def sync_file(path: Path, locale: str) -> int:
    raw = path.read_text(encoding='utf-8')
    data = json.loads(raw)
    pack = get_translations(locale)
    updated = 0
    for key in DECLARACION_KEYS:
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
    for path in sorted(LOCALES_DIR.glob('*/translation.json')):
        locale = path.parent.name
        n = sync_file(path, locale)
        files += 1
        if n:
            print(f'{locale}: updated {n} keys')
            total_updated += n
        else:
            print(f'{locale}: ok (no changes)')

    print(f'Done: {files} files, {total_updated} keys updated')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
