from pathlib import Path
from hashlib import sha256
from struct import unpack_from
import argparse
import importlib.util
import json


def digest(value):
    return sha256(value).hexdigest()


def delayed_import(image, address):
    rva, size = unpack_from('<II', image.data, image.optional + 112 + 13 * 8)
    start = image.offset(image.base + rva)
    matches = []
    for cursor in range(start, start + size, 32):
        values = unpack_from('<8I', image.data, cursor)
        if not any(values):
            break
        flags, module, _, table, names, _, _, _ = values
        convert = lambda value: image.base + value if flags & 1 else value
        base = convert(table)
        if address < base or (address - base) % 8:
            continue
        index = (address - base) // 8
        entry = image.offset(convert(names))
        count = 0
        while image.u64(entry + 8 * count):
            count += 1
        if index >= count:
            continue
        item = image.u64(entry + 8 * index)
        name = '#' + str(item & 0xffff) if item >> 63 else image.string(convert(item) + 2)
        matches.append({'module': image.string(convert(module)), 'name': name, 'slot_index': index})
    if len(matches) != 1:
        raise ValueError('exact native delayed import is not unique')
    return matches[0]


def main():
    parser = argparse.ArgumentParser()
    for name in ('root', 'bin', 'record', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--record-sha256', required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    if args.bin.resolve().is_relative_to(root) or args.output.resolve().is_relative_to(root) or args.output.exists():
        raise ValueError('use licensed modules and an unused output outside the checkout')
    raw = args.record.read_bytes()
    if digest(raw) != args.record_sha256:
        raise ValueError('source record differs')
    record = json.loads(raw)
    dependencies = []
    for row in record['dependencies']:
        raw = (root / row['path']).read_bytes()
        if len(raw) != row['bytes'] or digest(raw) != row['sha256']:
            raise ValueError('source dependency differs: ' + row['path'])
        dependencies.append(row['path'])
    spec = importlib.util.spec_from_file_location('DownstreamOriginalPe', root / 're/tooling/sw2026/materials/MaterialPe.py')
    if spec is None or spec.loader is None:
        raise RuntimeError('native metadata reader unavailable')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    images = {}
    for row in record['modules']:
        image = module.PeImage(args.bin / row['name'])
        if image.sha256 != row['sha256'] or image.base != int(row['base'], 16) or len(image.data) != row['bytes']:
            raise ValueError('licensed module identity differs: ' + row['name'])
        images[row['name']] = image
    checked = []
    for function in record['functions']:
        image = images[function['module']]
        for row in function['fragments']:
            actual = image.pin(row['name'], int(row['start'], 16), int(row['end_exclusive'], 16))
            if actual != row:
                raise ValueError('original native range differs: ' + function['analyst_role'])
            checked.append({'module': function['module'], 'role': function['analyst_role'], 'start': row['start'], 'sha256': row['sha256']})
    for row in record['literals']:
        image = images[row['module']]
        start = int(row['start'], 16)
        end = int(row['end_exclusive'], 16)
        actual = image.pin(row['name'], start, end)
        if actual != {key: value for key, value in row.items() if key not in ('module', 'utf16_text')}:
            raise ValueError('native schema literal differs')
        offset = image.offset(start)
        if image.data[offset:offset + end - start - 2].decode('utf-16-le') != row['utf16_text']:
            raise ValueError('native schema literal decoding differs')
    for row in record['exports']:
        matches = [value for value in images[row['module']].exports() if value['name'] == row['name']]
        if matches != [{key: value for key, value in row.items() if key != 'module'}]:
            raise ValueError('exact native export differs')
    for row in record['imports']:
        actual = images[row['image']].imports().get(int(row['iat'], 16))
        if actual != {key: value for key, value in row.items() if key not in ('image', 'iat')}:
            raise ValueError('exact native import differs')
    row = record['delay_import']
    actual = delayed_import(images[row['image']], int(row['iat'], 16))
    if actual != {key: row[key] for key in ('module', 'name', 'slot_index')}:
        raise ValueError('native kernel edge enumeration import differs')
    result = {'schema': 'kit.sw2026.drawing-downstream-source-verification.v1', 'passed': True,
              'source_record_sha256': args.record_sha256, 'modules': record['modules'], 'verified_ranges': checked,
              'verified_literals': len(record['literals']), 'verified_exports': len(record['exports']),
              'verified_imports': len(record['imports']), 'verified_delayed_import': actual,
              'source_dependencies_verified': dependencies, 'native_runs': 0, 'cad_payload_reads': 0,
              'writer_output_count': 0, 'heldout_credit': 0, 'vendor_code_emitted': False}
    output = (json.dumps(result, sort_keys=True, indent=2) + '\n').encode()
    with args.output.open('xb') as stream:
        stream.write(output)
    print(json.dumps({'passed': True, 'sha256': digest(output), 'ranges': len(checked)}))


if __name__ == '__main__':
    main()
