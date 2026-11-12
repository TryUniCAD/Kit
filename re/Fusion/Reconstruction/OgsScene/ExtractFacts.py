import hashlib
import json
import runpy
import struct
from pathlib import Path

BASE = Path(__file__).resolve().parent
API = runpy.run_path(str(BASE / 'InspectSerializers.py'))
APP = API['APP']
FACTS = [
    ('Libraries/libOGSGraphics.dylib', 'WideString', 'OGS::Serialization::write(Ns::IWriteStreamBase*, wchar_t const*&)', ['0xfa1c4', '0xfa1f8'], 'u32 UTF-16 code-unit count followed by UTF-16LE units; no terminator'),
    ('Libraries/libOGSGraphics.dylib', 'DirectProperty', 'OGS::Serialization::GeneralSerializer::SetProperty', ['0xc9eb0', '0xc9ed4', '0xcc41c', '0xcc458'], 'When context write stream exists, property name is omitted and known typed value is written directly'),
    ('Libraries/libOGSGraphics.dylib', 'PrimitiveDispatch', 'OGS::Serialization::GeneralSerializer::StreamArray', ['0xcbbdc', '0x37142c'], 'Native metadata type dispatch: 7 bool, 9 byte, 12 i32, 13 u32, 16 f32, 17 f64; vector types multiply element count'),
    ('Libraries/libOGSGraphics.dylib', 'MatrixAndBox', 'OGS::Serialization::GeneralSerializer::Serialize', ['0xc9400', '0xc96b8', '0xc99a4'], 'SBox3 writes six f64; Box3 six f32; ADevMatrix writes sixteen f32 starting at native matrix+8'),
    ('Libraries/libOGSGraphics.dylib', 'SharedObject', 'OGS::Serialization::Serializer::Serialize', ['0xede70', '0x375364', '0x375370'], 'InterfaceID identifies serializer; serializers flagged unique write an object identity string produced by %p; already-seen identity suppresses body'),
    ('Libraries/libOGSGraphics.dylib', 'World', 'OGS::Serialization::WorldSerializer::Serialize', ['0x100ccc', '0x100d30', '0x10109c', '0x10122c'], 'InterfaceID, RevisionId:u32, PublishMode:i32, serialized children, WorldSerializerEndMark string; nested ARenderList adds Accelerate:bool, root IWorld dispatch does not'),
    ('Libraries/Neutron/NsScene10.dylib', 'RootVersions', 'Ns::Scene::SerializationData::Serialize', ['0x2b77c4', '0x2b7820', '0x2b7868', '0x2b7888', '0x2b78c4', '0x2b78e8'], 'First group writes Size:u32, (InterfaceID:utf16,Version:u32)*Size, EnvironmentVersion:utf16 from IEnvironment::ActiveEnvironmentID'),
    ('Libraries/Neutron/NsScene10.dylib', 'GroupOverride', 'OGS::Serialization::FusionGroupNodeSerializer::Serialize', ['0xadd98', '0xadee8', '0xadf28', '0xae2cc', '0xae38c'], 'Fusion replaces generic group framing, writes root versions once, conditional transforms/style/world, then quick NodeDataType branch'),
    ('Libraries/Neutron/NsScene10.dylib', 'QuickNode', 'OGS::Serialization::NodeDataSerializer::SerializeQ', ['0xa8904', '0x1c5fc4', '0x1c6000', '0x1c6140'], 'Quick base writes NodeType and AttributeType without class/handle; NodeData suffix includes numeric segment/entity links and typed presentation flags'),
    ('Libraries/Neutron/NsScene10.dylib', 'SimpleMeshOverride', 'Ns::Serialization::OgsSimpleMeshSerializer::Serialize', ['0x163a90', '0x163b18', '0x163b50', '0x163c2c', '0x163c5c', '0x163c94', '0x163e70'], 'Fusion custom mesh omits generic RenderGeom VertexFormat link; writes Modelbox, PrimitiveType, inline vertex buffer, optional index serializer, Planarity'),
    ('Libraries/libOGSGraphics.dylib', 'VertexRange', 'OGS::Serialization::MeshStreamSerializer::Serialize(OGS::Devices::AVertexBuffer', ['0xd5350', '0xd541c', '0xd5424', '0xd5444', '0xd54d0', '0xd5508'], 'Three i32: stream number, byte offset, byte length; separate stream_mesh_%03d receives exactly byte length bytes'),
    ('Libraries/libOGSGraphics.dylib', 'IndexRange', 'OGS::Serialization::MeshStreamSerializer::Serialize(OGS::Devices::AIndexBuffer', ['0xd580c', '0xd58d4', '0xd58dc', '0xd58e4', '0xd5908'], 'Four i32: stream number, byte offset, byte length, index stride equals 2; last flag selects u16 versus u32 indices'),
    ('Libraries/libOGSGraphics.dylib', 'VertexFields', 'OGS::Serialization::VertexFormatSerializer::Serialize', ['0xfeacc', '0xfebf0', '0xfec50', '0xfec74', '0xfecf8'], 'Field count followed by six i32 per native VertexField, member offsets +0x10 through +0x24'),
    ('Libraries/libOGSDevices.dylib', 'VertexFieldConstructor', 'OGS::Devices::VertexField::VertexField(OGS::Devices::EVertexFieldUsage', ['0x15ec90', '0x15ecb0', '0x15ecbc', '0x15ecc4'], 'Member order: type enum, usage enum, offset, stream index, usage index, instance control; stream initially bool(instance control>0), usage index=(usage>>8)&15'),
    ('Libraries/libOGSDevices.dylib', 'StreamAndUsage', 'OGS::Devices::VertexFormat::', ['0x15f3e0', '0x1602fc', '0x161ddc', '0x161c4c', '0x161d54', '0x161040'], 'StreamCount and ToSingle/ToMultiStream prove +0x1c stream index; IndexOf(usage,index) proves +0x20 usage index; Offset(usage) returns +0x18'),
    ('Libraries/libOGSDeviceMetal.dylib', 'VertexMeaning', 'OGS::Devices::VertexDescriptorMetal::OGSVertexFormatToMetal', ['0x33124', '0x332d8', '0x332f4', '0x33304', '0x33394', '0x333b0'], 'Native Metal adapter converts type enum to MTL format; offset multiplied by four; stream member becomes bufferIndex; instance control>0 selects PerInstance, otherwise PerVertex; Metal step rate fixed 1'),
]

FACTS.extend([('Libraries/libOGSGraphics.dylib', 'RootWorldDispatch', 'OGS::Serialization::PersistentObjectManager::SaveWorld(IDataDriver*)', ['0xe12e4', '0xe1390', '0xe139c'], 'Root requests IWorld serializer, so ARenderList root omits derived Accelerate; nested ARenderList uses derived serializer'), ('Libraries/Neutron/NsScene10.dylib', 'EntityByteOrder', 'Ns::Scene::NodeDataSerializer::SerializeQ', ['0x1c60dc', '0x1c6120', '0x3a8890', '0x3a88c0'], 'EntityID constructed as eight explicitly shifted bytes, big-endian numeric order; not ordinary little-endian uint64 primitive'), ('Libraries/Neutron/NsScene10.dylib', 'EntityPredicates', 'Ns::Scene::NodeData::hasEntity / hasAppendixEntity', ['0x1bc790', '0x1bc7a0'], 'Entity status1 and2 carry segment/entity identity;0 omits it'), ('Libraries/Neutron/NsScene10.dylib', 'EmptyAttributeKinds', 'Ns::Serialization::ANodeDataSerializer::SerializeQ', ['0xa89c8', '0xa8abc'], 'Empty ordinary kind0 and empty extended kind1 omit attribute-set payload; populated2/3 select ordinary/extended'), ('Libraries/Neutron/NsScene10.dylib', 'QuickNodeSelectors', 'GetNodeDataSerializer / F360InstanceNodeSerilizer', ['0x2bae40', '0x1060fc', '0x106c4c'], 'Selectors2/3/5/6/7 share NodeData quick payload;4 adds IsXRef, conditional ACTEntityID bytes, InstanceIDu32'), ('Libraries/Neutron/NsScene10.dylib', 'BrepWorld', 'FusionGroupNodeSerializer::SerializeBrepBody', ['0xaefac', '0xaeaf8', '0xb4180'], 'ValidBody flag, edge quickgroup and LOD vector, face quickgroup and LOD vector, optional double-precision modelbox'), ('Libraries/Neutron/NsScene10.dylib', 'SketchWorld', 'FusionGroupNodeSerializer::SerializeSketch', ['0xae634', '0xb4180'], 'Optional faces BRep world, signed LOD and regular node counts, LOD nodes, regular nodes and nonculling nodes'), ('Libraries/Neutron/NsScene10.dylib', 'TextureMappingCache', 'TextureMappingCache::SerializeCache / SerializeCacheData', ['0x5ec34', '0x5f47c', '0x4bf630', '0x4bf658'], 'Layered flag, primary cache, optional secondary cache; each modei32,axis3d,box6d,baked16d,mapping16d;mode4 adds cylinder-cap booleans,mode6 adds wood-origin and board-face-axis3d')])


def main():
    images = {}
    for relative, *_ in FACTS:
        if relative not in images:
            binary = API['API']['Binary'](APP / relative)
            images[relative] = binary
    result = {'applicationVersion': '2706.1.17', 'architecture': 'arm64', 'addressBasis': 'Unslid Mach-O virtual address', 'images': [{'path': path, 'sha256': binary.sha256} for path, binary in images.items()], 'facts': [{'image': image, 'name': name, 'symbol': symbol, 'addresses': addresses, 'meaning': meaning} for image, name, symbol, addresses, meaning in FACTS]}
    devices = images['Libraries/libOGSDevices.dylib']
    metal = images['Libraries/libOGSDeviceMetal.dylib']
    result['vertexTypes'] = {'sizesTableAddress': '0x4553e0', 'sizes': list(struct.unpack('<24I', devices.read(0x4553e0, 96))), 'metalFormatTableAddress': '0x43bb8', 'metalFormatsForNative1Through3': list(struct.unpack('<3Q', metal.read(0x43bb8, 24))), 'native0MetalDefault': 28, 'qualifiedTypes': {'1': 'f32x2', '2': 'f32x3'}, 'usageNames': {str(value): {'literalAddress': hex(address), 'text': API['wide'](devices, address)} for value, address in ((0, 0x454ff0), (1, 0x455014), (2, 0x455128))}}
    header = Path('/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/System/Library/Frameworks/Metal.framework/Headers/MTLVertexDescriptor.h')
    result['metalEnumSource'] = {'path': str(header), 'sha256': hashlib.sha256(header.read_bytes()).hexdigest(), 'enumValues': {'Float': 28, 'Float2': 29, 'Float3': 30, 'Float4': 31, 'PerVertex': 1, 'PerInstance': 2}}
    result['limits'] = ['Instance control complete portable integer semantics beyond the tested zero profile unresolved; Metal uses only its sign', 'Native property names are not persisted; static call extraction includes branches and cannot itself establish linear layout', 'Only the two documented profiles are completely qualified; other native callbacks remain unsupported. Native complete-document acceptance is recorded separately in LocalOracle/NativeDocuments']
    (BASE / 'BinaryFacts.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'images': len(images), 'facts': len(FACTS), 'vertexTypeMap': result['vertexTypes']['metalFormatsForNative1Through3']}))


if __name__ == '__main__':
    main()
