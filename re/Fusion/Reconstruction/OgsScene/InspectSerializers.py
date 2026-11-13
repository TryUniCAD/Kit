import hashlib
import json
import re
import runpy
import struct
from pathlib import Path

BASE = Path(__file__).resolve().parent
API = runpy.run_path(str(BASE.parent / 'ReadBinaryMembers.py'))
APP = Path('~/Library/Application Support/Autodesk/webdeploy/production/b43a07003c01dd54425db484d23b1c5e6248a21d/Autodesk Fusion.app/Contents').expanduser()
TARGETS = {
    'Libraries/libOGSGraphics.dylib': ('Serializer::Serialize', 'WorldSerializer::Serialize', 'ARenderListSerializer::Serialize', 'GroupNodeSerializer::Serialize', 'RenderNodeSerializer::Serialize', 'GeometryNodeSerializer::Serialize', 'SimpleMeshSerializer::Serialize', 'VertexFormatSerializer::Serialize', 'AIndexBufferSerializer::Serialize', 'AVertexBufferSerializer::Serialize', 'MeshStreamSerializer::', 'GeneralSerializer::StreamArray', 'GeneralSerializer::SerializeLink', 'GeneralSerializer::WriteInterfaceID', 'GeneralSerializer::Serialize('),
    'Libraries/Neutron/NsScene10.dylib': ('FusionGroupNodeSerializer::Serialize', 'FusionGroupNodeSerializer::DeSerialize', 'NodeDataSerializer::Serialize', 'AttributeSetSerializer::Serialize', 'AttributeSetExSerializer::Serialize', 'AttributeSerializer::Serialize', 'VisibilityAttributeSerializer::Serialize', 'SelectabilityAttributeSerializer::Serialize', 'DepthPriorityAttributeSerializer::Serialize', 'TransformAttributeSerializer::Serialize', 'PixelScaleAttributeSerializer::Serialize', 'FOccludedEffectAttributeSerializer::Serialize', 'BillBoardAttributeSerializer::Serialize', 'FLineStyleAttributeSerializer::Serialize', 'GraphicsBlobFeatures', 'WorldCallback::On', 'FTextNodeSerializer::Serialize', 'FatPointMeshSerializer::Serialize', 'Serializer::Serialize', 'SerializationData::Serialize', 'Serilizer::Serialize', '::SerializeCache'),
}


def wide(binary, address):
    if not isinstance(address, int):
        return None
    raw = binary.read(address, 2048)
    if raw is None:
        return None
    values = []
    for start in range(0, len(raw), 4):
        value = struct.unpack_from('<I', raw, start)[0]
        if not value:
            return ''.join(values) if values else None
        if not 32 <= value < 127:
            return None
        values.append(chr(value))
    return None


def inspect(binary, name):
    address, symbol = binary.named[name]
    registers = {}
    result = []
    for offset, (operation, args, annotation) in binary.instructions(symbol).items():
        def reg(value):
            return 'x' + value[1:] if re.fullmatch(r'w\d+', value) else value
        def get(value):
            if value.startswith('#'):
                try:return int(value[1:], 0)
                except ValueError:return None
            return registers.get(reg(value))
        if operation == 'adrp' and annotation.startswith('0x'):
            registers[reg(args[0])] = int(annotation, 16)
        elif operation == 'adr' and args[1].startswith('#'):
            registers[reg(args[0])] = offset + int(args[1][1:], 0)
        elif operation == 'mov':
            registers[reg(args[0])] = get(args[1])
        elif operation in ('add', 'sub') and len(args) == 3:
            first, second = get(args[1]), get(args[2])
            registers[reg(args[0])] = first + (second if operation == 'add' else -second) if isinstance(first, int) and isinstance(second, int) else None
        elif operation == 'bl' or operation == 'b' and args[0].startswith('__Z'):
            target = args[0]
            if target.startswith('__Z'):
                target = API['demangle'](target)
            elif 'symbol stub for:' in annotation:
                target = API['demangle'](annotation.split('symbol stub for: ', 1)[1])
            if any(word in target for word in ('Serialize', 'serialize', 'Stream', 'Property', 'Version', 'Save', 'write(', 'read(')):
                result.append({'address': hex(offset), 'callee': target, 'literalArguments': {str(index): {'address': hex(registers['x' + str(index)]), 'text': wide(binary, registers.get('x' + str(index)))} for index in range(6) if wide(binary, registers.get('x' + str(index)))}, 'integerArguments': {str(index): registers['x' + str(index)] for index in range(6) if isinstance(registers.get('x' + str(index)), int) and 0 <= registers['x' + str(index)] < 128}})
            registers = {name: value for name, value in registers.items() if name.startswith('x') and name[1:].isdigit() and int(name[1:]) >= 19}
        elif operation == 'blr':
            registers = {name: value for name, value in registers.items() if name.startswith('x') and name[1:].isdigit() and int(name[1:]) >= 19}
        elif args and operation.startswith(('ldr', 'ldur', 'ldar')):
            registers.pop(reg(args[0]), None)
    return {'name': name, 'address': hex(address), 'events': result}


def main():
    report = {'scope': 'Static call-site extraction only; branch paths are not executed and events are possible calls, not a complete linear wire schema', 'architecture': 'arm64', 'addressBasis': 'Unslid Mach-O virtual address', 'images': []}
    for relative, patterns in TARGETS.items():
        binary = API['Binary'](APP / relative)
        names = [name for name in binary.named if any(pattern in name for pattern in patterns) and 'cold' not in name and 'thunk' not in name]
        methods = [inspect(binary, name) for name in names]
        report['images'].append({'path': relative, 'sha256': binary.sha256, 'methods': methods})
    (BASE / 'SerializerCalls.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'images': len(report['images']), 'methods': sum(len(row['methods']) for row in report['images'])}))


if __name__ == '__main__':
    main()
