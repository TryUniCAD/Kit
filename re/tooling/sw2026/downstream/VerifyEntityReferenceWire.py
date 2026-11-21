from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
from struct import unpack_from
import json


def digest(value):
    return sha256(value).hexdigest()


def main():
    parser = ArgumentParser()
    parser.add_argument('--bin-directory', type=Path, required=True)
    parser.add_argument('--record', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--checkout', type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('output exists')
    wire = args.record.read_bytes()
    record = json.loads(wire)
    if record.get('schema') != 'kit.sw2026.downstream-entity-reference-wire-source.v1':
        raise ValueError('source record identity differs')
    images = {}
    for row in record['modules']:
        raw = (args.bin_directory / row['name']).read_bytes()
        if len(raw) != row['bytes'] or digest(raw) != row['sha256']:
            raise ValueError('original module differs ' + row['name'])
        images[row['name']] = raw
    count = 0

    def check(module, pin):
        nonlocal count
        data = images[module][pin['file_offset']:pin['file_offset'] + pin['bytes']]
        if len(data) != pin['bytes'] or digest(data) != pin['sha256']:
            raise ValueError('source interval differs ' + pin['name'])
        if int(pin['end_exclusive'], 16) - int(pin['start'], 16) != pin['bytes']:
            raise ValueError('source interval size differs ' + pin['name'])
        count += 1

    for row in record['functions']:
        for pin in row['fragments']:
            if pin['name'] == 'entry_sample':
                raise ValueError('incomplete entry sample is not a function bound')
            check(row['module'], pin)
    for row in record['runtime_classes']:
        check(row['module'], row['descriptor_pin'])
        check(row['module'], row['serialize_slot_pin'])
        pointer = unpack_from('<Q', images[row['module']], row['serialize_slot_pin']['file_offset'])[0]
        if pointer != int(row['serialize_target'], 16):
            raise ValueError('Serialize target differs ' + row['class'])
    for row in record['auxiliary_classes']:
        check(row['module'], row['descriptor_pin'])
        if row['class'] != row['observed_name']:
            raise ValueError('auxiliary descriptor identity differs')
    shared_count = 0
    if args.checkout is not None:
        for row in record['materialized_reuse']['files']:
            raw = (args.checkout / row['path']).read_bytes()
            if len(raw) != row['bytes'] or digest(raw) != row['sha256']:
                raise ValueError('materialized source differs ' + row['path'])
            shared_count += 1
    result = {
        'schema': 'kit.sw2026.downstream-entity-reference-source-verification.v1',
        'passed': True,
        'record_sha256': digest(wire),
        'tool_sha256': digest(Path(__file__).read_bytes()),
        'verified_modules': len(images),
        'complete_function_entries': len(record['functions']),
        'source_intervals_verified': count,
        'runtime_descriptors': len(record['runtime_classes']),
        'serialize_cells': len(record['runtime_classes']),
        'auxiliary_descriptors': len(record['auxiliary_classes']),
        'typed_imports_source_bound_by_module_hash': len(record['imports']),
        'materialized_sources_verified': shared_count,
        'source_pin_verification_only': True,
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
