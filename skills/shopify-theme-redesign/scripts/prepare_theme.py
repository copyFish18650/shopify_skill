#!/usr/bin/env python3
"""Copy the independently authored native base into a new local theme directory."""

import argparse
import hashlib
import json
import re
import shutil
import tempfile
import zipfile
from html import escape
from pathlib import Path, PurePosixPath

from theme_audit import ROOTS, inspect_theme
from apply_native_retail import apply_native_retail
from apply_storefront_depth import apply_storefront_depth
from apply_native_service_pages import apply_native_service_pages


def seed_policy_defaults(stage, profile, operator_name=None, operator_address=None):
    """Seed this skill's new native copies only; never edit a merchant checkout or policy record."""
    normalized_name = ' '.join((operator_name or '').split())
    normalized_address = '\n'.join(line.strip() for line in (operator_address or '').splitlines() if line.strip())
    address_value = normalized_address or '#待填入'
    operator_html = escape(normalized_name) if normalized_name else '<strong>#待填入</strong>'
    documents = {kind: body.replace('[[operator_name]]', operator_html) for kind, body in profile['documents'].items()}

    def read(relative):
        return json.loads((stage / relative).read_text(encoding='utf-8'))

    def save(relative, value):
        (stage / relative).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    def load_section(name):
        path = stage / 'sections' / (name + '.liquid')
        source = path.read_text(encoding='utf-8')
        match = re.search(r'{%-?\s*schema\s*-?%}(.*?){%-?\s*endschema\s*-?%}', source, re.S)
        if match is None:
            raise ValueError('missing section schema: ' + name)
        return path, source, match, json.loads(match.group(1))

    def save_section(parts, schema):
        path, source, match, _ = parts
        path.write_text(source[:match.start(1)] + '\n' + json.dumps(schema, ensure_ascii=False, indent=2) + '\n' + source[match.end(1):], encoding='utf-8')

    def apply_document(block):
        if block.get('type') != 'information':
            return
        values = block['settings']
        kind = values['kind']
        values['body'] = documents[kind]
        if kind == 'size':
            values['title'] = 'Size & Product Guide'

    group = read('sections/footer-group.json')
    footer = next(record for record in group['sections'].values() if record['type'] == 'footer')
    applied = []
    for block in footer['blocks'].values():
        apply_document(block)
        if block['type'] == 'information':
            applied.append(block['settings']['kind'])
    if set(applied) != set(documents) or len(applied) != len(documents):
        raise ValueError('native Footer does not match the confirmed policy document set')
    footer['settings']['size_help'] = documents['size']
    footer['settings']['operator_address'] = address_value
    save('sections/footer-group.json', group)
    parts = load_section('footer')
    schema = parts[3]
    address_field = next((field for field in schema['settings'] if field.get('id') == 'operator_address'), None)
    if address_field is None:
        address_field = {'type': 'textarea', 'id': 'operator_address', 'label': 'Contact address',
                         'info': 'Use this store operator\'s document address. Shared by the footer and bundled Contact Information / Legal Notice; not automatically a return destination.'}
        schema['settings'].append(address_field)
    address_field['default'] = address_value
    for field in schema['settings']:
        if field.get('id') == 'size_help':
            field['default'] = documents['size']
    information = next(block for block in schema['blocks'] if block['type'] == 'information')
    for field in information['settings']:
        if field.get('id') == 'body':
            field['default'] = documents['about']
        elif field.get('id') == 'title':
            field['default'] = 'About Us'
        elif field.get('id') == 'kind':
            for option in field['options']:
                if option['value'] == 'size':
                    option['label'] = 'Size & Product Guide'
    for preset in schema['presets']:
        preset.setdefault('settings', {})['operator_address'] = address_value
        for block in preset.get('blocks', []):
            apply_document(block)
        if 'size_help' in preset.get('settings', {}):
            preset['settings']['size_help'] = documents['size']
    # Render the address from one editable setting, rather than duplicate static
    # addresses across richtext bodies that would diverge after an editor change.
    path, source, match, original_schema = parts
    caption = '<div class="footer-caption rte">{{ section.settings.caption }}</div>'
    public_address = '''{% if section.settings.operator_address != blank %}<div class="footer-address"><p class="footer-address__label">{{ 'footer.address' | t }}</p><address>{{ section.settings.operator_address | escape | newline_to_br }}</address></div>{% endif %}'''
    body = '{{ block.settings.body }}'
    document_address = '''{% if block.settings.kind == 'contact_information' or block.settings.kind == 'legal' %}{% if section.settings.operator_address != blank %}<div class="information-address"><h3>{{ 'footer.address' | t }}</h3><address>{{ section.settings.operator_address | escape | newline_to_br }}</address></div>{% endif %}{% endif %}'''
    if caption not in source or body not in source:
        raise ValueError('native Footer address insertion points are missing')
    source = source.replace(caption, caption + '\n' + public_address, 1)
    source = source.replace(body, body + document_address, 1)
    match = re.search(r'{%-?\s*schema\s*-?%}(.*?){%-?\s*endschema\s*-?%}', source, re.S)
    save_section((path, source, match, original_schema), schema)
    locale = read('locales/en.default.json')
    locale['footer']['address'] = 'Contact address'
    save('locales/en.default.json', locale)
    stylesheet = stage / 'assets/theme.css'
    with stylesheet.open('a', encoding='utf-8') as handle:
        handle.write('\n.footer-address{margin-top:22px;max-width:100%;font-size:12px;overflow-wrap:anywhere}.footer-address__label{font-weight:600;margin-bottom:7px}.footer-address address,.information-address address{font-style:normal;line-height:1.8}.information-address{margin-top:24px;overflow-wrap:anywhere}\n')

    answers = {
        'q1': '<p>Your shipping confirmation email contains tracking details after dispatch. Carrier tracking can take 24 to 48 hours to update. Contact support with your order reference if you need help.</p>',
        'q2': '<p>Processing takes 1 to 3 business days. Transit is estimated at 7 to 15 business days after dispatch, with an estimated total of 8 to 18 business days. Weekends and holidays are excluded. Standard shipping is free within the United States; estimates are not guaranteed arrival dates.</p>',
        'q3': '<p>You may request cancellation of unfulfilled items within 15 minutes of placing your order. For an address or other change, contact support promptly; availability depends on order status. See Return &amp; Refund Policy for the full terms.</p>',
        'q4': '<p>Keep the item and packaging, take photographs when possible, and contact support with your order reference and a description. We cover reasonable return shipping for verified damaged, defective, or incorrect items. Contact us before mailing anything.</p>',
        'q6': '<p>Please use our on-site contact form. Support hours are Monday to Friday, 9:00 AM to 6:00 PM MST (UTC-7). We aim to reply within 24 hours on business days.</p>',
    }
    index = read('templates/index.json')
    faq = next(record for record in index['sections'].values() if record['type'] == 'faq')
    for key, answer in answers.items():
        faq['blocks'][key]['settings']['answer'] = answer
    save('templates/index.json', index)
    parts = load_section('faq')
    schema = parts[3]
    for preset in schema['presets']:
        preset['blocks'] = [faq['blocks'][key] for key in faq['block_order']]
    save_section(parts, schema)
    return {'profile_id': profile['profile_id'], 'document_count': len(applied), 'operator_name_provided': bool(normalized_name), 'operator_address_provided': bool(normalized_address), 'public_address_setting': 'footer.operator_address', 'public_contact_method': 'native_contact_form', 'backend_changed': False}


def prepare_theme(category, output, operator_name=None, operator_address=None, category_labels=None, announcement_text='Explore the collection', promotion_ready=False):
    category = category.strip()
    if not category:
        raise ValueError('category must not be empty')
    output = output.resolve()
    if output.exists():
        raise ValueError('output already exists; choose a new working directory')
    assets = Path(__file__).resolve().parents[1] / 'assets'
    archive_path = assets / 'native-base.zip'
    metadata = json.loads((assets / 'native-base.json').read_text(encoding='utf-8'))
    policy_profile = json.loads((assets / 'merchant-policy-defaults.json').read_text(encoding='utf-8'))
    digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    if digest != metadata['sha256']:
        raise ValueError('native base checksum does not match its provenance record')

    with zipfile.ZipFile(archive_path) as archive:
        if archive.testzip() is not None:
            raise ValueError('native base ZIP CRC check failed')
        for member in archive.infolist():
            name = member.filename
            path = PurePosixPath(name)
            if (path.is_absolute() or '..' in path.parts or '\\' in name or ':' in name
                    or not path.parts or path.parts[0] not in ROOTS):
                raise ValueError('invalid native base archive path: ' + name)
        if {PurePosixPath(name).parts[0] for name in archive.namelist()} != set(ROOTS):
            raise ValueError('native base does not have the eight required theme roots')

        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='shopify-prepare-') as temporary:
            stage = Path(temporary) / 'theme'
            archive.extractall(stage)
            policy_result = seed_policy_defaults(stage, policy_profile, operator_name, operator_address)
            retail_result = apply_native_retail(stage, category_labels)
            storefront_result = apply_storefront_depth(stage)
            service_result = apply_native_service_pages(stage, announcement_text,
                output.parent.name if output.name == 'theme' else output.name,
                archive_path.name, digest, promotion_ready)
            report, _, _ = inspect_theme(stage)
            if not report['static_passed']:
                raise ValueError('native base audit failed: ' + '; '.join(report['errors']))
            shutil.copytree(stage, output)

    retail_result['theme_dir'] = str(output)
    storefront_result['theme_dir'] = str(output)
    service_result['manifest'] = str(output / 'assets/service-pages-manifest.json')

    return {
        'theme_dir': str(output),
        'category': category,
        'source': metadata['source'],
        'base_sha256': digest,
        'policy_defaults': policy_result,
        'native_retail': retail_result,
        'storefront_depth': storefront_result,
        'native_service_pages': service_result,
        'ready_for_delivery': False,
        'remaining': [
            'Retain the confirmed operating rules. Use only this task\'s individual operator name and document address. Keep footer and bundled contact/legal documents on the shared operator_address setting. Missing current-task identity/address stays pending; never fall back to a prior store. Do not publish account email, credentials or identity numbers. Keep the native contact form and verify its receiving configuration before claiming live delivery. Complete unresolved necessary privacy/legal details and check native-policy overrides.',
            'Adapt category copy, guides, policy terminology, locale strings, schema presets and saved JSON without resetting the confirmed operating rules.',
            'After final Footer category/body/address edits, run apply_native_service_pages.py THEME --refresh-manifest-only. This refreshes local Page drafts without overwriting custom presentation or creating backend Pages. Keep ordinary existing Page/Policy URLs; missing Pages remain pending rather than opening dialogs or guessed URLs.',
            'The sale banner starts disabled unless --promotion-ready was provided after actual CSV repricing verification. Finalize with apply_native_service_pages.py THEME --refresh-manifest-only --promotion-ready --announcement-text "CURRENT AUTHORIZED COPY" only when current prices support the campaign. CSV prices must be reduced once; Liquid/checkout must not apply this percentage again.',
            'Replace all baseline hero/carousel/lifestyle/category/editorial images and their responsive/mobile/default/preset variants. Register source identities and audit the whole batch plus accessible history with audit_site_diversity.py. Renaming, recropping, recoloring or recompressing a reused source is not a new cross-site image.',
            'Preserve source image proportions during resizing and use real image dimensions and srcset descriptors. Inspect each selected photo in its actual desktop/tablet/mobile frame: do not force narrow portraits into wide cover boxes or apply one top-biased focal point to all images. Keep important product/person details visible; adapt the local frame or choose a suitable source, retaining editable focal points and mobile images where needed.',
            'Follow the requested mode before adapting the scaffold: premium stores prioritize the user-approved mature premium baseline, or Cozyster when no particular prior baseline is identified. Retain approximately 85% of mature layout/component relationships and adapt approximately 15% locally; this is design direction, not a pixel score. Basic stores use EstateKid unless overridden. All modes implement full pages/cards/product detail/mobile. Preserve native data/forms and valid Footer dependencies.',
            'Read site-diversity.md: all modes retain product and image uniqueness. Premium stores may reuse mature navigation, cards, product-detail layout and merchandising rhythm; document retained components and local adaptations rather than forcing structural novelty. Basic and autonomous modes continue substantive composition differences. Record coverage honestly; visual reference does not itself authorize catalog scraping.',
            'Retain visible empty catalog slots and automatic collection/Type replacement after import, including desktop header and mobile category shortcuts. Populate planned category labels for the current category; these remain non-links until actual data exists. Preserve existing native menu destinations.',
            'Choose coherent interactions using the local CSS knowledge reference and real product media. Premium stores retain mature interaction patterns with small content-driven adjustments; other modes follow their own design variation requirements. Functional assets alone do not establish visual fidelity. Verify mouse, keyboard, touch, reduced motion and native form states.',
            'Pair surface/foreground and button/label colors. Follow color-and-surface.md for measured text, price, placeholder, control and state contrast in the actual browser, including opacity inheritance, overlays and photo crops. Do not reintroduce faded reference prices, unreadable helper text or light panels with inherited white text. Inspect desktop and mobile; static schema and Theme Check do not certify readability.',
            'Design collection, product, search, cart and content/service pages as part of this storefront. Use real non-empty filter fixtures and verify query preservation; the supplied page styles and optional editorial section are functional resources, not a required visual composition.',
            'Run current static, official and available preview checks, then create a uniquely named delivery ZIP.',
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--category', required=True)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--operator-name', help='Current task individual operator name for public policy text; never an account email or identifier')
    parser.add_argument('--operator-address', help='Current task operator document address for the public footer/contact information; newline-separated text, never identity numbers or credentials')
    parser.add_argument('--category-label', action='append', default=[], help='Planned category label in an empty store; repeat for each label. Actual store collections/types replace these labels after import.')
    parser.add_argument('--announcement-text', default='Explore the collection', help='Explicit campaign copy from this site promotion plan; neutral until prices and discount are verified')
    parser.add_argument('--promotion-ready', action='store_true', help='Enable the saved sale banner after actual current CSV prices have been verified; otherwise the sale announcement starts disabled')
    args = parser.parse_args()
    try:
        result = prepare_theme(args.category, args.output, args.operator_name, args.operator_address, args.category_label, args.announcement_text, args.promotion_ready)
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
