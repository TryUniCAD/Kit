from argparse import ArgumentParser
from hashlib import sha256
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from struct import unpack_from
import json


def digest(value):
    return sha256(value).hexdigest()


def main():
    parser = ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--bin-directory', type=Path, required=True)
    parser.add_argument('--record', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('output exists')
    source = args.record.read_bytes()
    record = json.loads(source)
    if record['schema'] != 'kit.sw2026.downstream-body-options.v1':
        raise ValueError('source record differs')
    dependency = record['pe_helper']
    helper = args.root / dependency['path']
    if digest(helper.read_bytes()) != dependency['sha256']:
        raise ValueError('PE helper differs')
    spec = spec_from_file_location('body_option_pe', helper)
    if spec is None or spec.loader is None:
        raise ValueError('PE helper cannot load')
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    image = module.PeImage(args.bin_directory / 'sldmodu.dll')
    original = record['modules'][0]
    if len(image.data) != original['bytes'] or image.sha256 != original['sha256']:
        raise ValueError('original model differs')
    exports = [row for row in image.exports() if row['name'] == record['setter']['export']]
    if len(exports) != 1 or exports[0]['address'] != record['setter']['entry'] or exports[0]['forwarder'] is not None:
        raise ValueError('setter export differs')
    directory_rva = image.u32(image.optional + 112)
    directory = image.offset(image.base + directory_rva)
    names = image.offset(image.base + image.u32(directory + 32))
    ordinals = image.offset(image.base + image.u32(directory + 36))
    matches = [index for index in range(image.u32(directory + 24)) if image.string(image.base + image.u32(names + 4 * index)) == record['setter']['export']]
    if len(matches) != 1 or image.u32(directory + 16) + image.u16(ordinals + 2 * matches[0]) != record['setter']['ordinal']:
        raise ValueError('setter ordinal differs')
    intervals = 0

    def check(pin):
        nonlocal intervals
        offset = pin['file_offset']
        raw = image.data[offset:offset + pin['bytes']]
        if len(raw) != pin['bytes'] or digest(raw) != pin['sha256']:
            raise ValueError('source interval differs: ' + pin['name'])
        if int(pin['end_exclusive'], 16) - int(pin['start'], 16) != pin['bytes']:
            raise ValueError('source interval size differs')
        if image.offset(int(pin['start'], 16)) != offset:
            raise ValueError('source interval mapping differs')
        intervals += 1

    for function in record['functions']:
        if not function['fragments']:
            raise ValueError('missing complete owner')
        for pin in function['fragments']:
            check(pin)
    for window in record['instruction_ranges']:
        check(window['pin'])
    for row in record['vocabulary']:
        check(row['pin'])
        position = row['pin']['file_offset']
        raw = image.data[position:position + row['pin']['bytes']]
        if raw.decode('utf-16-le') != row['text'] + '\0':
            raise ValueError('neighbor option vocabulary differs')
    for row in record['initializer_slots']:
        check(row['pin'])
        if image.u64(row['pin']['file_offset']) != int(row['target'], 16):
            raise ValueError('initializer slot differs')
    for row in record['imports']:
        if image.imports().get(int(row['iat'], 16)) != row['binding']:
            raise ValueError('import binding differs')
    section = record['loader_initial_state']['section']
    if image.data[section['header_offset']:section['header_offset'] + 8].rstrip(b'\0').decode('ascii') != section['name']:
        raise ValueError('section name differs')
    virtual, rva, rawsize, raw = unpack_from('<IIII', image.data, section['header_offset'] + 8)
    if [virtual, image.base + rva, rawsize, raw] != [section['virtual_size'], int(section['va'], 16), section['raw_bytes'], section['raw_file_offset']]:
        raise ValueError('section geometry differs')
    target = int(record['loader_initial_state']['word_va'], 16)
    relative = target - image.base - rva
    if not rawsize <= relative < virtual - 3:
        raise ValueError('option word is not wholly zero-fill')
    imports = []
    literal_modules = []
    for item in record['caller_inventory']['modules']:
        candidate = module.PeImage(args.bin_directory / item['module'])
        if len(candidate.data) != item['bytes'] or candidate.sha256 != item['sha256']:
            raise ValueError('caller original differs: ' + item['module'])
        normal = candidate.imports()
        if len(normal) != item['normal_import_entries']:
            raise ValueError('ordinary import count differs')
        for address, value in normal.items():
            if value['module'].lower() == 'sldmodu.dll' and value['name'] in [record['setter']['export'], '#' + str(record['setter']['ordinal'])]:
                imports.append(item['module'])
        rva, size = unpack_from('<II', candidate.data, candidate.optional + 112 + 13 * 8)
        count = 0
        if rva:
            position = candidate.offset(candidate.base + rva)
            while any(candidate.data[position:position + 32]):
                flags, name, hmod, iat, intab, bound, unload, clock = unpack_from('<IIIIIIII', candidate.data, position)
                owner = candidate.string(candidate.base + name if flags & 1 else name)
                thunk = candidate.offset(candidate.base + intab if flags & 1 else intab)
                index = 0
                while (value := candidate.u64(thunk + index * 8)):
                    label = '#' + str(value & 0xffff) if value >> 63 else candidate.string((candidate.base + value if flags & 1 else value) + 2)
                    if owner.lower() == 'sldmodu.dll' and label in [record['setter']['export'], '#' + str(record['setter']['ordinal'])]:
                        imports.append(item['module'])
                    index += 1
                position += 32
                count += 1
        if count != item['delay_descriptors']:
            raise ValueError('delayed descriptor count differs')
        if any(label.encode(encoding) in candidate.data for label in [record['setter']['export'], 's_setDownstreamIdOptions'] for encoding in ['ascii', 'utf-16-le']):
            literal_modules.append(item['module'])
    if imports != record['caller_inventory']['importing_modules']:
        raise ValueError('setter caller imports differ')
    if literal_modules != record['caller_inventory']['name_literal_modules']:
        raise ValueError('setter literal module set differs')
    result = {'schema': 'kit.sw2026.downstream-body-options-source-verification.v1', 'passed': True, 'record_sha256': digest(source), 'tool_sha256': digest(Path(__file__).read_bytes()), 'original_modules': len(record['caller_inventory']['modules']), 'complete_function_entries': len(record['functions']), 'source_intervals': intervals, 'initializer_slots_verified': len(record['initializer_slots']), 'vocabulary_items_verified': len(record['vocabulary']), 'imports_verified': len(record['imports']), 'setter_import_matches': len(imports), 'setter_literal_modules': literal_modules, 'option_word_wholly_in_zero_fill': True, 'derived_loader_initial_u32': 0, 'ordinary_post_startup_policy_qualified': False, 'source_verification_only': True, 'native_runs': 0, 'sdk_product_runs': 0, 'cad_inputs_read': 0, 'heldout_inputs_read': 0, 'vm_calls': 0, 'vendor_bytes_or_listings_published': False, 'full_native_admission_qualified': False}
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'passed': True, 'sha256': digest(args.output.read_bytes()), 'source_only': True}))


if __name__ == '__main__':
    main()
