from argparse import ArgumentParser
from hashlib import sha256
from json import dumps
from pathlib import Path
import sys


def main():
    parser = ArgumentParser()
    parser.add_argument('--binaries', type=Path, required=True)
    parser.add_argument('--pe-helper', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if sha256(args.pe_helper.read_bytes()).hexdigest() != 'ffa6f015b152d2aa0ce869afc94665e5f01f5089d23298fa19681ff2ac7dc7b9':
        raise ValueError('original independently authored PE helper differs')
    sys.path.insert(0, str(args.pe_helper.parent))
    from PinNativeNames import Image
    image = Image(args.binaries / 'sldmodu.dll')
    if sha256(image.data).hexdigest() != '569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e':
        raise ValueError('pinned SP05.2 model module differs')
    ranges = (
        ('atom_constructor', 0x4bcede70, 0x4bcee024),
        ('atom_serializer', 0x4bcefbb0, 0x4bcf02e1),
        ('feature_id_reconcile', 0x4bcf98c0, 0x4bcf9b15),
        ('set_name_derived', 0x4b293560, 0x4b293567),
        ('set_display_mode', 0x4b292070, 0x4b292077),
        ('new_atom', 0x4bcf0ca0, 0x4bcf0d27),
        ('output_count', 0x4b706160, 0x4b706181),
        ('set_one_output', 0x4b717940, 0x4b7179a2),
        ('set_multiple_outputs', 0x4b717470, 0x4b717930),
        ('replace_and_destroy_body', 0x4bcf9cf0, 0x4bcf9d92),
        ('id_counter_boundary_only', 0x4bcf9230, 0x4bcf923c),
        ('folded_owner_setter', 0x4b2c6d10, 0x4b2c6d18),
        ('manager_load_window', 0x4bcefa03, 0x4bcefb7d),
        ('feature_load_id_repair_window', 0x4bb23a90, 0x4bb23c20))
    result = {'schema': 'kit.sw2026.named-body-cold-reuse-pins.v2',
        'module_sha256': sha256(image.data).hexdigest(), 'image_base': hex(image.base),
        'pe_helper_sha256': sha256(args.pe_helper.read_bytes()).hexdigest(),
        'ranges': [{'owner': name, 'start': hex(start), 'end_exclusive': hex(end),
            'file_offset': image.offset(start - image.base, end - start),
            'bytes': end - start, 'sha256': sha256(image.at(start, end - start)).hexdigest()}
            for name, start, end in ranges]}
    with args.output.open('x', encoding='utf-8', newline='\n') as output:
        output.write(dumps(result, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    main()
