#!/usr/bin/env python3
"""Create a Shopify product CSV with one reference-based sale adjustment.

Only the Price/Compare-at columns change. This is an offline transformation,
not an import, exchange-rate conversion, or claim about a store's price history.
"""
import argparse
import csv
import hashlib
import io
import json
import os
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from pathlib import Path


SCHEMAS = (
    ('Price', 'Compare-at price'),
    ('Variant Price', 'Variant Compare At Price'),
)


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def amount(value, label, row_number):
    try:
        parsed = Decimal(value.strip())
    except InvalidOperation:
        raise ValueError('row %d: %s must be a plain numeric amount' % (row_number, label))
    if not parsed.is_finite() or parsed < 0:
        raise ValueError('row %d: %s must be finite and nonnegative' % (row_number, label))
    return parsed


def transform(source, multiplier, minor_units=2):
    """Validate all records before returning new bytes and an audit summary."""
    multiplier = Decimal(str(multiplier))
    if not multiplier.is_finite() or not Decimal('0') < multiplier < Decimal('1'):
        raise ValueError('multiplier must be strictly between 0 and 1')
    if not isinstance(minor_units, int) or not 0 <= minor_units <= 6:
        raise ValueError('minor-units must be an integer from 0 to 6')
    bom = source.startswith(b'\xef\xbb\xbf')
    text = source.decode('utf-8-sig')
    rows = list(csv.reader(io.StringIO(text, newline=''), strict=True))
    if not rows or not rows[0]:
        raise ValueError('CSV header is missing')
    header = rows[0]
    if len(header) != len(set(header)):
        raise ValueError('CSV has duplicate header names')
    present = [pair for pair in SCHEMAS if pair[0] in header or pair[1] in header]
    if len(present) != 1 or not all(name in header for name in present[0]):
        raise ValueError('CSV must contain exactly one supported Price/Compare-at header pair; no columns are added')
    price_name, reference_name = present[0]
    price_index, reference_index = header.index(price_name), header.index(reference_name)
    target_columns = {price_index, reference_index}
    updated = [list(header)]
    unit = Decimal(1).scaleb(-minor_units)
    counts = {'variant_rows': 0, 'existing_compare_at_basis_rows': 0,
              'original_price_basis_rows': 0, 'blank_price_rows': 0, 'zero_price_rows': 0}
    for row_number, row in enumerate(rows[1:], start=2):
        if len(row) != len(header):
            raise ValueError('row %d: field count differs from the header' % row_number)
        result = list(row)
        price_text, compare_text = row[price_index].strip(), row[reference_index].strip()
        if not price_text:
            if compare_text:
                raise ValueError('row %d: blank Price must also have blank Compare-at price' % row_number)
            counts['blank_price_rows'] += 1
            updated.append(result)
            continue
        old_price = amount(price_text, price_name, row_number)
        old_compare = amount(compare_text, reference_name, row_number) if compare_text else None
        reference = old_compare if old_compare is not None and old_compare > old_price else old_price
        with localcontext() as context:
            context.prec = max(40, len(reference.as_tuple().digits) + abs(reference.as_tuple().exponent) + minor_units + 10)
            if reference.quantize(unit, rounding=ROUND_HALF_UP) != reference:
                raise ValueError('row %d: reference has more precision than --minor-units; original value is not rounded silently' % row_number)
            sale = (reference * multiplier).quantize(unit, rounding=ROUND_HALF_UP)
        if reference > 0 and sale >= reference:
            raise ValueError('row %d: rounding produces no price reduction at this currency precision' % row_number)
        result[price_index] = format(sale, '.%df' % minor_units)
        result[reference_index] = format(reference, '.%df' % minor_units) if reference else ''
        counts['variant_rows'] += 1
        counts['existing_compare_at_basis_rows' if old_compare is not None and old_compare > old_price else 'original_price_basis_rows'] += 1
        if reference == 0:
            counts['zero_price_rows'] += 1
        updated.append(result)
    if not counts['variant_rows']:
        raise ValueError('CSV contains no priced variant rows')
    output = io.StringIO(newline='')
    writer = csv.writer(output, lineterminator='\r\n' if '\r\n' in text else '\n')
    writer.writerows(updated)
    encoded = output.getvalue().encode('utf-8-sig' if bom else 'utf-8')
    roundtrip = list(csv.reader(io.StringIO(encoded.decode('utf-8-sig'), newline=''), strict=True))
    if roundtrip != updated or len(roundtrip) != len(rows):
        raise ValueError('CSV export round-trip differs from validated values')
    if any(a != b for before, after in zip(rows, roundtrip)
           for i, (a, b) in enumerate(zip(before, after)) if i not in target_columns):
        raise ValueError('A non-price field changed during export')
    return encoded, {
        'passed': True, 'rows': len(rows) - 1, 'columns': len(header), **counts,
        'multiplier': str(multiplier), 'minor_units': minor_units,
        'price_column': price_name, 'compare_at_column': reference_name,
        'utf8_bom_preserved': bom, 'non_price_fields_unchanged': True,
        'source_sha256': digest(source), 'output_sha256': digest(encoded),
        'live_shopify_import': False,
    }


def reprice_file(source_path, output_path, multiplier, minor_units=2):
    source_path = Path(source_path).resolve()
    output_path = Path(output_path).resolve()
    if source_path == output_path or output_path.exists():
        raise ValueError('output must be a new file and must not replace the source')
    source = source_path.read_bytes()
    payload, report = transform(source, multiplier, minor_units)
    # Validation and export reconciliation finish before any output is opened.
    if digest(source_path.read_bytes()) != report['source_sha256']:
        raise ValueError('source changed while it was being validated')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with output_path.open('xb') as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError:
        raise ValueError('output appeared during validation; it was not replaced')
    if digest(output_path.read_bytes()) != report['output_sha256']:
        raise ValueError('saved CSV bytes differ from the validated export')
    report.update({'input': str(source_path), 'output': str(output_path)})
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--multiplier', required=True, help='Explicit sale/reference multiplier from this site promotion plan, e.g. 0.85 for 15%% off')
    parser.add_argument('--minor-units', default=2, type=int, help='Currency decimal places; default 2, no conversion')
    args = parser.parse_args()
    try:
        result = reprice_file(args.input, args.output, Decimal(args.multiplier), args.minor_units)
    except (ValueError, OSError, UnicodeError, csv.Error, InvalidOperation) as exc:
        print(json.dumps({'passed': False, 'error': str(exc)}, ensure_ascii=True))
        return 1
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
