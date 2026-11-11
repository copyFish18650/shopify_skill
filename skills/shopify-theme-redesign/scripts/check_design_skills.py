#!/usr/bin/env python3
"""Read-only check of the three design-skill packages required before theme work."""

import argparse
import json
import hashlib
import re
from pathlib import Path
from urllib.parse import unquote


REQUIRED = {
    'design-taste-frontend': (
        'scripts/draw.mjs',
        'scripts/inspect.mjs',
        'references/critique.md',
    ),
    'design': ('references/visual-direction.md',),
    'web-design-engineer': ('references/design-calibration.md',),
}


def inspect_package(skills_dir, name, required_resources):
    root = (skills_dir / name).resolve()
    entry = root / 'SKILL.md'
    result = {'name': name, 'path': str(entry), 'ready': False, 'errors': []}
    if not entry.is_file():
        result['status'] = 'missing'
        result['errors'].append('SKILL.md is missing')
        return result
    try:
        text = entry.read_text(encoding='utf-8-sig')
    except (OSError, UnicodeError) as exc:
        result['status'] = 'unreadable'
        result['errors'].append(str(exc))
        return result
    frontmatter = re.match(r'\A---\s*\r?\n(.*?)\r?\n---(?:\s*\r?\n|\Z)', text, re.S)
    declared = None
    if frontmatter:
        match = re.search(r'^name:\s*([^\r\n]+)', frontmatter.group(1), re.M)
        if match:
            declared = match.group(1).strip().strip('\'"')
    if declared != name:
        result['errors'].append('Expected entry name %r, found %r' % (name, declared))
    if not frontmatter or not text[frontmatter.end():].strip():
        result['errors'].append('The entry has no usable instruction body')
    resources = set(required_resources)
    for target in re.findall(r'(?<!!)\[[^\]\n]*\]\(([^)\n]+)\)', text):
        target = unquote(target.strip().strip('<>').split('#', 1)[0])
        if target.startswith(('references/', 'scripts/', 'assets/')):
            resources.add(target)
    for relative in sorted(resources):
        resource = (root / relative).resolve()
        try:
            resource.relative_to(root)
        except ValueError:
            result['errors'].append('Resource path leaves the skill package: ' + relative)
            continue
        if not resource.is_file() or resource.stat().st_size == 0:
            result['errors'].append('Missing or empty bundled resource: ' + relative)
    result['resources_checked'] = len(resources)
    result['ready'] = not result['errors']
    result['status'] = 'ready' if result['ready'] else 'incomplete'
    return result


def verify_bundle(skills_dir):
    manifest_path = skills_dir / 'manifest.json'
    report = {'path': str(manifest_path), 'ready': False, 'errors': [], 'files_verified': 0}
    try:
        manifest = json.loads(manifest_path.read_text(encoding='utf-8-sig'))
    except (OSError, UnicodeError, ValueError) as exc:
        report['errors'].append('Cannot read the bundled-source manifest: ' + str(exc))
        return report
    modules = manifest.get('modules')
    if manifest.get('schema_version') != 1 or not isinstance(modules, list):
        report['errors'].append('Unsupported bundled-source manifest')
        return report
    if sorted(item.get('name', '') for item in modules) != sorted(REQUIRED):
        report['errors'].append('Manifest must contain exactly the three required modules')
        return report
    for module in modules:
        root = (skills_dir / module['name']).resolve()
        files = module.get('files')
        if not isinstance(files, dict) or 'SKILL.md' not in files or 'LICENSE.upstream.txt' not in files:
            report['errors'].append('Missing entry/license digest for ' + module['name'])
            continue
        for relative, expected in files.items():
            resource = (root / relative).resolve()
            try:
                resource.relative_to(root)
            except ValueError:
                report['errors'].append('Manifest resource leaves its package: ' + relative)
                continue
            try:
                actual = hashlib.sha256(resource.read_bytes()).hexdigest()
            except OSError as exc:
                report['errors'].append(module['name'] + '/' + relative + ': ' + str(exc))
                continue
            if actual != expected:
                report['errors'].append('Bundled file differs from recorded snapshot: ' + module['name'] + '/' + relative)
            else:
                report['files_verified'] += 1
    report['ready'] = not report['errors']
    return report


def inspect_design_skills(skills_dir):
    skills_dir = Path(skills_dir).expanduser().resolve()
    packages = [inspect_package(skills_dir, name, resources)
                for name, resources in REQUIRED.items()]
    bundle = verify_bundle(skills_dir)
    return {
        'ready': bundle['ready'] and all(package['ready'] for package in packages),
        'skills_dir': str(skills_dir),
        'bundle': bundle,
        'skills': packages,
        'limits': 'Bundled file integrity, entry names and resource checks only. Read the relevant rules before code; this does not verify their application, browser tools, visual quality or a cryptographic source signature.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    bundled = Path(__file__).resolve().parents[1] / 'assets' / 'design-skills'
    parser.add_argument('--skills-dir', type=Path, default=bundled,
                        help='A complete bundled design-skills directory; defaults to resources inside this Shopify skill')
    args = parser.parse_args()
    report = inspect_design_skills(args.skills_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['ready'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
