#!/usr/bin/env python3
"""Read-only completeness check for this workflow's single-location product CSV."""
import argparse
import csv
import gzip
import json
import re
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path

ALIASES = {
    'handle': ['URL handle', 'Handle'],
    'title': ['Title'], 'description': ['Description', 'Body (HTML)'],
    'category': ['Product category', 'Product Category', 'Standardized Product Type'],
    'type': ['Type'], 'collection': ['Collection'],
    'sku': ['SKU', 'Variant SKU'], 'price': ['Price', 'Variant Price'],
    'tracker': ['Inventory tracker', 'Variant Inventory Tracker'],
    'quantity': ['Inventory quantity', 'Variant Inventory Qty'],
    'policy': ['Continue selling when out of stock', 'Variant Inventory Policy'],
    'fulfillment': ['Fulfillment service', 'Variant Fulfillment Service'],
    'image': ['Product image URL', 'Image Src', 'Image URL'],
    'option1': ['Option1 value', 'Option1 Value'],
    'option2': ['Option2 value', 'Option2 Value'],
    'option3': ['Option3 value', 'Option3 Value'],
}


def taxonomy_values(path):
    opener = gzip.open if path.suffix == '.gz' else open
    with opener(path, 'rt', encoding='utf-8-sig') as stream:
        data = json.load(stream)
    if not isinstance(data, dict):
        raise ValueError('Expected official categories JSON object')
    values = set()
    for vertical in data.get('verticals', []):
        for category in vertical.get('categories', []):
            if category.get('id') and category.get('full_name'):
                values.add(category['id'].rsplit('/', 1)[-1])
                values.add(category['full_name'])
    if not values:
        raise ValueError('No categories found in verticals[].categories[]')
    version = str(data.get('version', ''))
    if not version or 'unstable' in version.lower():
        raise ValueError('Use a versioned stable official taxonomy release')
    return values, version


def audit(csv_path, taxonomy_path, allow_untracked=False):
    allowed, version = taxonomy_values(taxonomy_path)
    with csv_path.open('r', encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        headers = reader.fieldnames or []
        if len(headers) != len(set(headers)):
            raise ValueError('Duplicate CSV headers')
        columns = {key: next((name for name in names if name in headers), None)
                   for key, names in ALIASES.items()}
        rows = list(reader)
    problems, groups = [], defaultdict(list)
    def issue(message, row=None, handle=None):
        problems.append({'message': message, **({'row': row} if row else {}),
                         **({'handle': handle} if handle else {})})
    for key in ALIASES:
        if key in {'option2', 'option3'}:
            continue
        if allow_untracked and key in {'tracker', 'quantity'}:
            continue
        if not columns[key]:
            issue('Missing supported column: ' + ALIASES[key][0])
    def value(row, key):
        return str(row.get(columns.get(key)) or '').strip() if columns.get(key) else ''
    current_handle = ''
    for index, row in enumerate(rows, 2):
        if None in row or any(v is None for v in row.values()):
            issue('Incorrect CSV field count', index)
        if not any(str(v or '').strip() for v in row.values() if not isinstance(v, list)):
            continue
        current_handle = value(row, 'handle')
        if not current_handle:
            issue('Every nonempty product, variant or image row needs its handle', index)
            continue
        groups[current_handle].append((index, row))
    variant_count = image_rows = untracked_count = 0
    for handle, members in groups.items():
        for key in ['title', 'description', 'category', 'type', 'collection']:
            items = {value(row, key) for _, row in members if value(row, key)}
            if not items:
                issue('Product has no ' + ALIASES[key][0], handle=handle)
            elif len(items) > 1:
                issue('Conflicting product-level ' + ALIASES[key][0], handle=handle)
            if key == 'category':
                for item in items:
                    if item not in allowed:
                        issue('Category is not a stable taxonomy short ID or full path: ' + item, handle=handle)
        if not any(value(row, 'image') for _, row in members):
            issue('Product has no image URL', handle=handle)
        seen_options = set()
        for line, row in members:
            is_variant = any(value(row, key) for key in ['title', 'sku', 'price', 'option1', 'option2', 'option3', 'tracker', 'quantity'])
            if not is_variant:
                if value(row, 'image'):
                    image_rows += 1
                else:
                    issue('Row has neither variant nor image data', line, handle)
                continue
            variant_count += 1
            options = tuple(value(row, key) for key in ['option1', 'option2', 'option3'])
            if options in seen_options:
                issue('Duplicate variant option combination', line, handle)
            seen_options.add(options)
            if not value(row, 'sku'):
                issue('Missing variant SKU', line, handle)
            try:
                price = Decimal(value(row, 'price'))
                if not price.is_finite() or price < 0:
                    raise InvalidOperation
            except InvalidOperation:
                issue('Invalid or missing variant price', line, handle)
            tracker = value(row, 'tracker')
            if not tracker and allow_untracked:
                untracked_count += 1
            else:
                if tracker != 'shopify':
                    issue('Expected Inventory tracker=shopify; no silent untracked fallback', line, handle)
                qty = value(row, 'quantity')
                if not re.fullmatch(r'[0-9]+', qty) or int(qty) <= 0:
                    issue('Available catalog needs explicit positive whole-number inventory', line, handle)
            if value(row, 'policy') != 'deny':
                issue('Expected deny for this available-stock workflow', line, handle)
            if not value(row, 'fulfillment'):
                issue('Missing fulfillment service', line, handle)
    if not groups:
        issue('No products found')
    result = {'passed': not problems, 'csv': str(csv_path.resolve()),
              'taxonomy_version': version, 'products': len(groups),
              'variants': variant_count, 'image_only_rows': image_rows,
              'untracked_exception_variants': untracked_count,
              'error_count': len(problems), 'errors': problems[:30],
              'errors_truncated': len(problems) > 30,
              'limits': 'Single-location completeness only. Does not verify source stock ownership, semantic classification, image access, promotion math or a live Shopify import.'}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv', type=Path)
    parser.add_argument('--taxonomy', type=Path, required=True, help='Official stable categories.en.json[.gz] downloaded to work directory')
    parser.add_argument('--report', type=Path)
    parser.add_argument('--allow-untracked', action='store_true', help='Only after the user explicitly requests untracked inventory')
    args = parser.parse_args()
    try:
        result = audit(args.csv, args.taxonomy, args.allow_untracked)
    except (ValueError, OSError, csv.Error, UnicodeError) as error:
        result = {'passed': False, 'error': str(error)}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
