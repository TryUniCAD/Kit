from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
import json


def digest(value):
    return sha256(value).hexdigest()


def main():
    parser = ArgumentParser()
    parser.add_argument('--bin-directory', type=Path, required=True)
    parser.add_argument('--record', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('output exists')
    source = args.record.read_bytes()
    record = json.loads(source)
    if record.get('schema') != 'kit.sw2026.downstream-local-owner-context.v1':
        raise ValueError('source record differs')
    images = {}
    for row in record['modules']:
        raw = (args.bin_directory / row['name']).read_bytes()
        if len(raw) != row['bytes'] or digest(raw) != row['sha256']:
            raise ValueError('original module differs: ' + row['name'])
        images[row['name']] = raw
    count = 0

    def check(module, pin):
        nonlocal count
        if pin['name'] == 'entry_sample':
            raise ValueError('incomplete source entry')
        raw = images[module][pin['file_offset']:pin['file_offset'] + pin['bytes']]
        if len(raw) != pin['bytes'] or digest(raw) != pin['sha256']:
            raise ValueError('source interval differs: ' + pin['name'])
        if int(pin['end_exclusive'], 16) - int(pin['start'], 16) != pin['bytes']:
            raise ValueError('source interval size differs: ' + pin['name'])
        count += 1

    for row in record['functions']:
        if not row['fragments']:
            raise ValueError('function lacks source range')
        for pin in row['fragments']:
            check(row['module'], pin)
    for row in record['instruction_ranges']:
        check(row['module'], row['pin'])
    for row in record['virtual_slots']:
        check(row['module'], row['pin'])
        start = row['pin']['file_offset']
        actual = int.from_bytes(images[row['module']][start:start + 8], 'little')
        if actual != int(row['target'], 16):
            raise ValueError('virtual owner differs: ' + row['name'])
    result = {
        'schema': 'kit.sw2026.downstream-local-owner-source-verification.v1',
        'passed': True,
        'record_sha256': digest(source),
        'tool_sha256': digest(Path(__file__).read_bytes()),
        'original_modules': len(images),
        'complete_function_entries': len(record['functions']),
        'source_intervals': count,
        'virtual_slots_verified': len(record['virtual_slots']),
        'imports_bound_by_original_module_hash': len(record['imports']),
        'source_verification_only': True,
        'native_runs': 0,
        'sdk_product_runs': 0,
        'cad_inputs_read': 0,
        'heldout_inputs_read': 0,
        'vendor_bytes_or_listings_published': False,
        'full_native_admission_qualified': False,
    }
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'passed': True, 'sha256': digest(args.output.read_bytes()), 'source_only': True}))


if __name__ == '__main__':
    main()
