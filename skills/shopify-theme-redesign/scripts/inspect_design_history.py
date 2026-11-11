#!/usr/bin/env python3
"""Find local Shopify design records and preview images; does not judge similarity."""

import argparse
import json
from pathlib import Path

from theme_audit import parse_json


def inspect_history(root, limit=3, exclude=None):
    root = Path(root).resolve()
    if not root.is_dir():
        raise ValueError('history root must be an existing directory')
    if limit < 1:
        raise ValueError('limit must be positive')
    exclude = Path(exclude).resolve() if exclude else None
    records = []
    for folder in root.iterdir():
        if not folder.is_dir() or folder == exclude:
            continue
        brief = next((folder / name for name in ('design-direction.json', 'design.json') if (folder / name).is_file()), None)
        index = folder / 'theme/templates/index.json'
        if brief is None and not index.is_file():
            continue
        record = {'directory': str(folder), 'brief_path': str(brief) if brief else None}
        source = brief if brief else index
        record['_modified'] = source.stat().st_mtime
        try:
            record['design_record'] = parse_json(brief.read_text(encoding='utf-8-sig'), True) if brief else None
            if index.is_file():
                data = parse_json(index.read_text(encoding='utf-8-sig'), True)
                if not isinstance(data, dict) or not isinstance(data.get('sections'), dict) or not isinstance(data.get('order'), list):
                    raise ValueError('homepage record must contain sections and order')
                record['homepage_section_types'] = [data['sections'][key].get('type') for key in data.get('order', []) if not data['sections'][key].get('disabled')]
        except (OSError, ValueError, KeyError, TypeError) as error:
            record['read_error'] = str(error)
        names = ('desktop-first-screen.png', 'desktop-hero.png', 'desktop-home.png', 'mobile-first-screen.png', 'mobile-hero.png', 'desktop-empty-categories.png', 'desktop-footer.png')
        record['screenshots'] = [str(folder / 'preview' / name) for name in names if (folder / 'preview' / name).is_file()]
        records.append(record)
    records.sort(key=lambda record: (-record['_modified'], record['directory']))
    records = records[:limit]
    for record in records:
        del record['_modified']
    return {'root': str(root), 'records': records, 'scope': 'Read-only discovery. Inspect the actual screenshots and make a design judgment; no visual review or similarity score is performed.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('--limit', type=int, default=3)
    parser.add_argument('--exclude', type=Path)
    args = parser.parse_args()
    try:
        result = inspect_history(args.root, args.limit, args.exclude)
    except (OSError, ValueError) as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
