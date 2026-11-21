from argparse import ArgumentParser
from hashlib import sha256
from json import dumps
from pathlib import Path
from runpy import run_path
from struct import unpack_from


def imports(image):
    rva, size = unpack_from('<II', image.data, image.optional + 120)
    start = image.offset(rva, size)
    result = {}
    for off in range(start, start + size, 20):
        lookup, _, _, name_rva, first = unpack_from('<IIIII', image.data, off)
        if not any((lookup, name_rva, first)):
            break
        module = image.text(name_rva)
        count = 0
        while True:
            value = unpack_from('<Q', image.data, image.offset((lookup or first) + 8 * count, 8))[0]
            if not value:
                break
            symbol = '#' + str(value & 0xffff) if value >> 63 else image.text(value + 2)
            result[image.base + first + count * 8] = {'module': module, 'symbol': symbol}
            count += 1
    return result


def main():
    parser = ArgumentParser()
    parser.add_argument('--image-helper', type=Path, required=True)
    parser.add_argument('--model', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    image = run_path(str(args.image_helper))['Image'](args.model)
    if sha256(image.data).hexdigest() != '569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e':
        raise ValueError('model module differs from pinned SP05.2')
    vtable = 0x4cff1620
    col = unpack_from('<Q', image.at(vtable - 8, 8))[0]
    descriptor = image.base + unpack_from('<I', image.at(col + 12, 4))[0]
    name = image.text(descriptor + 16 - image.base)
    if name != '.?AVmoAtom_c@@':
        raise ValueError('constructor vtable does not belong to moAtom_c')
    slots = {hex(offset): hex(unpack_from('<Q', image.at(vtable + offset, 8))[0])
             for offset in (0x28, 0x88, 0x3a8)}
    if slots['0x88'] != '0x4c03e5c0' or slots['0x3a8'] != '0x4bcf10e0':
        raise ValueError('ordinary atom name slots differ')
    selected = ((0x4b293560, 0x4b293567, 'setNameDerived'),
                (0x4c03e5c0, 0x4c03e5d7, 'moNode::name'),
                (0x4bcede70, 0x4bcee024, 'moAtom constructor inspected window'),
                (0x4bcf2ed0, 0x4bcf2f7e, 'getAtomFromName inspected window'),
                (0x4bcfb360, 0x4bcfb63b, 'setBody inspected window'),
                (0x4bcfb7a0, 0x4bcfba91, 'setBody name helper inspected window'),
                (0x4bcf1286, 0x4bcf12c5, 'atom name calculator authored-name branch'))
    windows = [{'name': label, 'start': hex(first), 'end_exclusive': hex(last),
                'file_offset': image.offset(first - image.base, last - first),
                'sha256': sha256(image.at(first, last - first)).hexdigest()}
               for first, last, label in selected]
    imports_by_slot = imports(image)
    result = {'schema': 'kit.sw2026.atom-name-native-pins.v1',
              'module': args.model.name, 'sha256': sha256(image.data).hexdigest(),
              'bytes': len(image.data), 'image_base': hex(image.base),
              'helper_sha256': sha256(args.image_helper.read_bytes()).hexdigest(),
              'tool_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
              'vtable': hex(vtable), 'rtti': name, 'slots': slots,
              'windows': windows,
              'imports': {hex(slot): imports_by_slot[slot] for slot in
                          (0x4cd39ec0, 0x4cd39ec8, 0x4cd386d8, 0x4cd34ec0, 0x4cd34e40)},
              'static_only': True, 'runtime_execution_observed': False}
    with args.output.open('x', encoding='utf-8', newline='\n') as output:
        output.write(dumps(result, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    main()
