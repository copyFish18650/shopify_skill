#!/usr/bin/env python3
"""Read-only CSV and configured storefront promotion audit; no prices are rewritten."""
import argparse
import csv
import hashlib
import html
import io
import json
import re
import unicodedata
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from pathlib import Path

try:
    from catalog_audit import ALIASES as CATALOG_ALIASES
except ImportError:
    CATALOG_ALIASES = {}

ALIASES = {
    'handle': ['URL handle', 'Handle'], 'title': ['Title'],
    'sku': ['SKU', 'Variant SKU'], 'price': ['Price', 'Variant Price'],
    'compare': ['Compare-at price', 'Compare At Price', 'Variant Compare At Price', 'Variant Compare-at Price'],
    'status': ['Status'], 'published': ['Published on online store', 'Published'],
    'image': ['Product image URL', 'Image Src', 'Image URL'],
    'option1': ['Option1 value', 'Option1 Value'],
    'option2': ['Option2 value', 'Option2 Value'],
    'option3': ['Option3 value', 'Option3 Value'],
    'tracker': ['Inventory tracker', 'Variant Inventory Tracker'],
    'quantity': ['Inventory quantity', 'Variant Inventory Qty'],
}
for _key in ALIASES:
    ALIASES[_key] = list(dict.fromkeys(ALIASES[_key] + CATALOG_ALIASES.get(_key, [])))

LIMITS = [
    'Checks promotion arithmetic and saved theme configuration only; it does not establish an authentic former retail price, MSRP, supplier cost, or lawful advertising basis.',
    'CSV status/publication is inherited per handle; omitted status/publication is treated as active/published for a stricter price check, not verified storefront publication.',
    'Every variant row of an active, published product is checked. Source availability, inventory ownership, Markets prices, currency conversion, discounts and backend imports are not verified.',
    'Money is audited with two-decimal USD-style precision; the CSV alone does not establish the shop currency.',
    'Theme support is header-group.json ordered, enabled announcement-bar sections with settings.text and a matching section schema/presets. Other announcement architectures require an explicit adapter.',
    'Saved configuration and schema checks do not prove Liquid/CSS visibility, browser behavior, actual import, checkout price, or live Shopify settings.',
]


def normalize(value):
    return re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFKC', str(value)).casefold())


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def validate_multiplier(value):
    try:
        result = Decimal(str(value))
    except InvalidOperation as error:
        raise ValueError('multiplier must be a decimal strictly between zero and one') from error
    if not result.is_finite() or not Decimal('0') < result < Decimal('1'):
        raise ValueError('multiplier must be a decimal strictly between zero and one')
    return result


def decimal_amount(value):
    text = str(value).strip()
    if not re.fullmatch(r'(?:\d+(?:\.\d*)?|\.\d+)', text):
        raise ValueError('must be a plain positive decimal amount')
    amount = Decimal(text)
    if not amount.is_finite() or amount <= 0:
        raise ValueError('must be finite and strictly positive')
    with localcontext() as context:
        context.prec = max(40, len(amount.as_tuple().digits) + 10)
        if amount.quantize(Decimal('.01'), rounding=ROUND_HALF_UP) != amount:
            raise ValueError('has precision beyond two monetary decimal places')
    return amount


def discounted(reference, multiplier):
    with localcontext() as context:
        context.prec = max(40, len(reference.as_tuple().digits) + len(multiplier.as_tuple().digits) + 10)
        return (reference * multiplier).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)


def issue_list():
    items = []
    def issue(code, message, **where):
        items.append({'code': code, 'message': message, **where})
    return items, issue


def audit_csv(path, multiplier):
    path = Path(path)
    payload = path.read_bytes()
    reader = csv.DictReader(io.StringIO(payload.decode('utf-8-sig'), newline=''), strict=True)
    headers = reader.fieldnames or []
    errors, issue = issue_list()
    normalized_headers = defaultdict(list)
    for name in headers:
        normalized_headers[normalize(name)].append(name)
    if not headers:
        issue('missing_headers', 'CSV header is missing')
    for key, matches in normalized_headers.items():
        if len(matches) > 1:
            issue('duplicate_headers', 'Duplicate CSV headers after case/spacing normalization', headers=matches)
    columns = {}
    for key, aliases in ALIASES.items():
        candidates = list(dict.fromkeys(name for alias in aliases for name in normalized_headers.get(normalize(alias), [])))
        columns[key] = candidates[0] if candidates else None
        if len(candidates) > 1:
            issue('ambiguous_columns', 'Multiple columns match the same supported field', field=key, headers=candidates)
    for key in ['handle', 'price', 'compare']:
        if not columns.get(key):
            issue('missing_column', 'Missing supported column: ' + ALIASES[key][0], field=key)
    rows = list(reader)
    groups = defaultdict(list)
    def value(row, key):
        return str(row.get(columns.get(key)) or '').strip() if columns.get(key) else ''
    for line, row in enumerate(rows, 2):
        if None in row or any(item is None for item in row.values()):
            issue('row_width', 'CSV row field count differs from its header', row=line)
        if not any(str(item or '').strip() for item in row.values() if not isinstance(item, list)):
            continue
        handle = value(row, 'handle')
        if not handle:
            issue('missing_handle', 'A nonempty CSV record needs its product handle', row=line)
            continue
        groups[handle].append((line, row))

    totals = Counter(products=len(groups), checked_products=0, excluded_products=0, variant_rows=0,
                     checked_variants=0, excluded_variants=0, image_only_rows=0, metadata_only_rows=0)
    excluded_reasons = Counter()
    excluded = []
    assumptions = []
    if not columns.get('status'):
        assumptions.append('Status column absent; price checking assumes active.')
    if not columns.get('published'):
        assumptions.append('Published column absent; price checking assumes published.')
    for handle, records in groups.items():
        statuses = {value(row, 'status').casefold() for _, row in records if value(row, 'status')}
        publications = set()
        for line, row in records:
            text = value(row, 'published').casefold()
            if text in {'true', 'yes', '1'}:
                publications.add(True)
            elif text in {'false', 'no', '0'}:
                publications.add(False)
            elif text:
                issue('invalid_publication', 'Unrecognized Published value', handle=handle, row=line, value=text)
        if len(statuses) > 1:
            issue('conflicting_status', 'Conflicting product-level Status values for this handle', handle=handle, values=sorted(statuses))
        if len(publications) > 1:
            issue('conflicting_publication', 'Conflicting product-level Published values for this handle', handle=handle)
        invalid_statuses = statuses - {'active', 'archived', 'draft'}
        if invalid_statuses:
            issue('invalid_status', 'Unrecognized Shopify Status', handle=handle, values=sorted(invalid_statuses))
        reasons = sorted(statuses & {'archived', 'draft'})
        if False in publications:
            reasons.append('unpublished')
        excluded_product = bool(reasons)
        product_variants = 0
        if excluded_product:
            totals['excluded_products'] += 1
            excluded_reasons.update(reasons)
        else:
            totals['checked_products'] += 1
        for line, row in records:
            # A title/image on a continuation row alone is not a variant. A metadata-only
            # active product still fails below if it has no actual auditable variant.
            is_variant = any(value(row, key) for key in ['sku', 'price', 'compare', 'option1', 'option2', 'option3', 'tracker', 'quantity'])
            if not is_variant:
                totals['image_only_rows' if value(row, 'image') else 'metadata_only_rows'] += 1
                continue
            totals['variant_rows'] += 1
            product_variants += 1
            if excluded_product:
                totals['excluded_variants'] += 1
                continue
            totals['checked_variants'] += 1
            location = {'handle': handle, 'row': line}
            if value(row, 'sku'):
                location['sku'] = value(row, 'sku')
            amounts = {}
            for key in ['price', 'compare']:
                try:
                    amounts[key] = decimal_amount(value(row, key))
                except (ValueError, InvalidOperation) as error:
                    issue('invalid_' + key, ALIASES[key][0] + ' ' + str(error), **location)
            if len(amounts) != 2:
                continue
            sale, reference = amounts['price'], amounts['compare']
            if reference <= sale:
                issue('compare_not_above_sale', 'Compare-at must be strictly greater than Price', **location,
                      price=str(sale), compare_at=str(reference))
            expected = discounted(reference, multiplier)
            if sale != expected:
                issue('incorrect_multiplier', 'Price does not equal Compare-at × multiplier with ROUND_HALF_UP cents',
                      **location, price=str(sale), compare_at=str(reference), expected_price=str(expected))
        if excluded_product:
            excluded.append({'handle': handle, 'reasons': reasons, 'variant_rows': product_variants})
        elif not product_variants:
            issue('product_without_variants', 'Active/published product has no auditable variant row', handle=handle)
    if not groups:
        issue('no_products', 'CSV has no product records')
    if not totals['checked_variants']:
        issue('no_eligible_variants', 'No active/published variant rows were available to validate')
    unchanged = digest(path.read_bytes()) == digest(payload)
    if not unchanged:
        issue('input_changed', 'CSV changed externally while the audit was running; retry on a stable file')
    return {'passed': not errors, 'csv': str(path.resolve()), 'sha256': digest(payload),
            'input_unchanged': unchanged, 'columns': columns, 'counts': dict(totals),
            'excluded_product_reasons': dict(excluded_reasons), 'excluded_products': excluded,
            'assumptions': assumptions, 'error_count': len(errors), 'errors': errors[:100],
            'errors_truncated': len(errors) > 100}


def promotion_text(text):
    """Find explicit discount claims, not arbitrary percent numerals in JSON."""
    plain = html.unescape(re.sub(r'<[^>]*>', ' ', unicodedata.normalize('NFKC', str(text))))
    plain = ' '.join(plain.split()).casefold()
    number = r'(\d+(?:\.\d+)?)\s*(?:%|percent)'
    patterns = [number + r'\s*(?:off\b|less\b|discount\b|savings\b)',
                r'\b(?:save|saving)\s+(?:up\s+to\s+)?' + number,
                r'\b(?:discount|savings)\s*(?:of|by|:)?\s*' + number]
    rates = set()
    for pattern in patterns:
        rates.update(Decimal(match.group(1)) for match in re.finditer(pattern, plain))
    return plain, rates


def check_discount_text(text, discount, issue, location):
    if not isinstance(text, str) or not text.strip():
        issue('missing_announcement_text', 'Announcement text is absent or not a literal string', **location)
        return False
    plain, rates = promotion_text(text)
    if rates and rates != {discount}:
        issue('wrong_announcement_rate', 'Discount wording conflicts with the requested price multiplier',
              **location, detected_percent=[str(rate) for rate in sorted(rates)], expected_percent=str(discount))
        return False
    if discount not in rates:
        return False
    if re.search(r'\b(?:up\s+to|at\s+least)\s+\d+(?:\.\d+)?\s*(?:%|percent)', plain):
        issue('qualified_announcement_rate', 'Announcement must describe the exact verified discount, not an up-to/minimum offer', **location)
        return False
    if re.search(r'\b(?:no|not|without)\s+(?:a\s+)?\d+(?:\.\d+)?\s*(?:%|percent)', plain):
        issue('negated_announcement_rate', 'A negated discount is not an enabled promotion claim', **location)
        return False
    return True


def audit_theme(theme, multiplier):
    theme = Path(theme)
    discount = (Decimal(1) - multiplier) * 100
    errors, issue = issue_list()
    group_path = theme / 'sections/header-group.json'
    group = json.loads(group_path.read_text('utf-8-sig'))
    sections = group.get('sections', {})
    order = group.get('order', [])
    if not isinstance(sections, dict) or not isinstance(order, list):
        raise ValueError('header-group.json must have sections object and order array')
    if len(order) != len(set(order)):
        issue('duplicate_header_order', 'Header group order contains duplicate section IDs')
    enabled, disabled, unsupported, schema_records = [], [], [], []
    valid_saved = 0
    audited_types = set()
    for section_id in order:
        record = sections.get(section_id)
        if not isinstance(record, dict):
            issue('missing_ordered_section', 'Header order references a missing section', section_id=section_id)
            continue
        section_type = record.get('type', '')
        if record.get('disabled', False) is True:
            if section_type == 'announcement-bar':
                disabled.append(section_id)
            continue
        if section_type != 'announcement-bar':
            if re.search(r'announce|promo|banner', str(section_type), re.I):
                unsupported.append({'section_id': section_id, 'type': section_type})
            continue
        location = {'section_id': section_id, 'type': section_type}
        text = record.get('settings', {}).get('text')
        valid = check_discount_text(text, discount, issue, {**location, 'source': 'saved settings.text'})
        enabled.append({**location, 'text': text, 'matches_requested_discount': valid})
        valid_saved += int(valid)
        if section_type in audited_types:
            continue
        audited_types.add(section_type)
        section_path = theme / 'sections' / (section_type + '.liquid')
        source = section_path.read_text('utf-8-sig')
        match = re.search(r'{%-?\s*schema\s*-?%}(.*?){%-?\s*endschema\s*-?%}', source, re.S)
        if not match:
            issue('missing_section_schema', 'Enabled announcement section has no schema', path=str(section_path))
            continue
        schema = json.loads(match.group(1))
        field = next((setting for setting in schema.get('settings', []) if setting.get('id') == 'text'), None)
        default_text = field.get('default') if field else None
        default_valid = check_discount_text(default_text, discount, issue, {'source': 'schema text default', 'path': str(section_path)})
        if not default_valid:
            issue('invalid_schema_default', 'Re-added announcement must retain the requested discount in its text default', path=str(section_path))
        presets = schema.get('presets', [])
        if not presets:
            issue('missing_announcement_presets', 'No announcement presets exist to validate the re-add path', path=str(section_path))
        preset_records = []
        for index, preset in enumerate(presets):
            settings = preset.get('settings', {})
            inherited = 'text' not in settings
            effective = default_text if inherited else settings.get('text')
            preset_valid = check_discount_text(effective, discount, issue, {'source': 'preset text', 'preset_index': index, 'path': str(section_path)})
            if not preset_valid:
                issue('invalid_preset_text', 'Announcement preset falls back to missing, generic or incompatible promotional text', preset_index=index, path=str(section_path))
            preset_records.append({'index': index, 'name': preset.get('name'), 'text': effective,
                                   'inherits_schema_default': inherited, 'matches_requested_discount': preset_valid})
        schema_records.append({'type': section_type, 'path': str(section_path), 'default_text': default_text,
                               'default_matches_requested_discount': default_valid, 'presets': preset_records})
    if not valid_saved:
        issue('no_enabled_matching_announcement', 'No ordered, enabled announcement-bar saved settings.text states the requested discount', expected_percent=str(discount))
    # Product/quick-view locale notes and saved inner-page text must agree too.
    # A banner-only audit missed a stale "Save 30%" product note in an earlier base.
    configured_claims = []
    def inspect_strings(value, file_path, pointer=''):
        if isinstance(value, dict):
            for key, child in value.items():
                inspect_strings(child, file_path, pointer + '/' + str(key))
        elif isinstance(value, list):
            for index, child in enumerate(value):
                inspect_strings(child, file_path, pointer + '/' + str(index))
        elif isinstance(value, str):
            _, rates = promotion_text(value)
            if rates:
                configured_claims.append({'path': str(file_path), 'key': pointer,
                                          'detected_percent': [str(r) for r in sorted(rates)]})
                if rates != {discount}:
                    issue('wrong_storefront_rate', 'Configured storefront discount text conflicts with this site multiplier',
                          path=str(file_path), key=pointer, detected_percent=[str(r) for r in sorted(rates)], expected_percent=str(discount))
    for folder in ['config', 'locales', 'templates', 'sections']:
        for file_path in sorted((theme / folder).rglob('*.json')):
            inspect_strings(json.loads(file_path.read_text('utf-8-sig')), file_path)
    for file_path in sorted((theme / 'sections').glob('*.liquid')):
        source = file_path.read_text('utf-8-sig')
        match = re.search(r'{%-?\s*schema\s*-?%}(.*?){%-?\s*endschema\s*-?%}', source, re.S)
        if match:
            inspect_strings(json.loads(match.group(1)), file_path)
    return {'passed': not errors, 'theme': str(theme.resolve()), 'expected_discount_percent': str(discount),
            'enabled_announcements': enabled, 'disabled_announcement_ids': disabled,
            'unsupported_announcement_types': unsupported, 'schemas': schema_records, 'configured_promotion_claims': configured_claims,
            'error_count': len(errors), 'errors': errors, 'configuration_only': True}


def audit(csv_paths, theme, multiplier):
    multiplier = validate_multiplier(multiplier)
    results = []
    for path in csv_paths:
        try:
            results.append(audit_csv(Path(path), multiplier))
        except (OSError, UnicodeError, ValueError, csv.Error, InvalidOperation) as error:
            results.append({'passed': False, 'csv': str(Path(path).resolve()), 'error_count': 1,
                            'errors': [{'code': 'csv_read_error', 'message': str(error)}]})
    try:
        theme_result = audit_theme(Path(theme), multiplier)
    except (OSError, UnicodeError, ValueError, TypeError, AttributeError) as error:
        theme_result = {'passed': False, 'theme': str(Path(theme).resolve()), 'error_count': 1,
                        'errors': [{'code': 'theme_read_error', 'message': str(error)}]}
    return {'passed': bool(results) and all(result['passed'] for result in results) and theme_result['passed'],
            'multiplier': str(multiplier), 'discount_percent': str((1 - multiplier) * 100),
            'rounding': 'Decimal ROUND_HALF_UP, two monetary decimal places',
            'csv_files': results, 'theme': theme_result, 'limits': LIMITS}


def is_within(path, root):
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--csv', type=Path, action='append', required=True, help='Repeat for every actual delivered catalog CSV')
    parser.add_argument('--theme', type=Path, required=True)
    parser.add_argument('--report', type=Path, help='Optional external JSON report; never overwrites CSV/theme files')
    parser.add_argument('--multiplier', required=True, help='Explicit sale/reference multiplier for this site, e.g. 0.85 for 15%% off; read the saved promotion plan')
    args = parser.parse_args()
    try:
        multiplier = validate_multiplier(args.multiplier)
        if args.report:
            report = args.report.resolve()
            if report in {path.resolve() for path in args.csv} or report.suffix.casefold() in {'.csv', '.py'} or is_within(report, args.theme.resolve()):
                raise ValueError('--report must be an external report path, not a CSV, Python script or a file inside the audited theme')
        result = audit(args.csv, args.theme, multiplier)
    except (ValueError, OSError) as error:
        result = {'passed': False, 'error': str(error), 'limits': LIMITS}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
