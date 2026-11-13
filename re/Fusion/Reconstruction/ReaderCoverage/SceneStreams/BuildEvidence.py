import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

NATIVE = {
    'binary': 'Autodesk Fusion.app/Contents/Libraries/Neutron/NsScene10.dylib',
    'arm64_sha256': 'd33789c8c20033f1c7673ff9b1dcf87f1ef7cf9c43c7245d75c8a65a83bc8c82',
    'method': 'otool -tV disassembly, nm symbol map and wide-string decoding, read only',
    'functions': {
        'LODGeometryNodeSerializer::SerializeForBody': '0xb4180',
        'LODGeometryNodeSerializer::DeSerializeForBody': '0xb4ac8',
        'Ns::Scene::GetDisplayItemSerializer': '0x2bb0a0',
        'EnhancedMeshEdgeSerializer::SerializeQ': '0xaaeb8',
        'EnhancedMeshEdgeSerializer::DeSerializeQ': '0xaaf8c',
        'EnhancedMeshFacetSerializer::SerializeQ': '0xaaa44',
        'EnhancedMeshFacetSerializer::DeSerializeQ': '0xaabd4',
        'MeshSerializer::Serialize(DisplayItemFacet*)': '0xb58b8',
        'MeshSerializer::SerializeEnhancedMeshEdge': '0xb5db0',
        'MeshSerializer::DeSerializeEnhancedMeshEdge': '0xb6868',
        'FusionGroupNodeSerializer::SerializeBrepBody': '0xaefac',
        'BillBoardAttributeSerializer::DeSerialize': '0x52e14',
    },
    'wide_strings': {
        '0x3b8064': 'NodeDataType', '0x3b8098': 'HasLODs', '0x3b8150': 'DisplayItemType',
        '0x3b8190': 'DisplayType', '0x3b81c0': 'RenderGeom', '0x3b80f4': 'WorldBox',
        '0x3b8118': 'UseClosestLOD', '0x3b84c0': 'Props', '0x3b84d8': 'Fusion_mesh_%03d',
        '0x3b6cd4': 'EdgeNum', '0x3b6d14': 'Props', '0x3a8cf0': 'Style', '0x3a8d08': 'Anchor',
        '0x3a8d24': 'Axis', '0x3a8d38': 'Compensation', '0x3a8d6c': 'FlipVisibility',
    },
    'display_item_serializers': {
        '1': 'DisplayItemSerializer', '2': 'DisplayItemEdgeSerializer', '3': 'DisplayItemFacetSerializer',
        '4': 'EnhancedMeshEdgeSerializer', '6': 'OgsEnhancedEdgeSerializer -> EnhancedMeshEdgeSerializer',
        '7': 'OgsEnhancedFaceSerializer -> EnhancedMeshFacetSerializer', 'other': 'none',
    },
}

LAYOUT = {
    'body_lod': [
        'NodeData payload',
        'HasLODs u32: zero or one bit (1 << level, 0x800 for level 11)',
        'when HasLODs != 0 and render geometry exists: DisplayItemType u32',
        'DisplayItemType 0: RenderGeom link (flag, class text, object)',
        'DisplayItemType 6: OgsEnhancedEdge Props u32[4]',
        'DisplayItemType 7: OgsEnhancedFace Props u32[6], EdgeNum u32, Props u32[EdgeNum]',
        'WorldBox f64[6]',
        'UseClosestLOD u8',
    ],
    'enhanced_edge_props': ['stream index', 'byte offset', 'position float count (3 per vertex)', 'normal float count (equals position count)'],
    'enhanced_edge_stream': 'per vertex f32 px py pz nx ny nz at Fusion_mesh_%03d[offset]',
    'enhanced_face_props': ['stream index', 'byte offset', 'position float count', 'normal float count', 'texture float count (2 per vertex, rounded even)', 'index count'],
    'enhanced_face_stream': 'per vertex f32 px py pz nx ny nz u v, then u32 triangle indices, at Fusion_mesh_%03d[offset]',
    'enhanced_face_edges': 'EdgeNum then one u32 per edge: the body-local serialization ordinal of an earlier OgsEnhancedEdge in the same body map',
    'stream_advance': 'MeshSerializer adds the written bytes to the offset and moves to the next stream index with offset 0 after the limit',
    'stream_family': 'Fusion_mesh_NNN is written only by MeshSerializer and is distinct from stream_mesh_NNN used by OgsSimpleMesh buffers',
    'object_identity': 'GroupNode and other graphics object ids are %p text: 0x-prefixed lowercase on macOS saves, 16 uppercase hex digits on Windows saves',
    'billboard_v1': 'BillBoardAttribute serializer version 1 carries Style, Anchor, Axis, Compensation; version 2 adds FlipVisibility u32',
}


def lines(name):
    return [json.loads(line) for line in (Path(sys.argv[2]) / name).read_text().splitlines() if line.strip()]


if __name__ == '__main__':
    acceptance = json.loads(Path(sys.argv[1]).read_text())
    evidence = {
        'status': 'captured',
        'native': NATIVE,
        'layout': LAYOUT,
        'saved_observation': {
            'grouped.f3d first enhanced edge': 'type 6 Props (0, 0, 180, 180), 60 vertices, 1440 bytes',
            'grouped.f3d first enhanced face': 'type 7 Props (0, 2880, 177, 177, 118, 171), EdgeNum 1, edges (0)',
            'grouped.f3d Fusion_mesh_000': 'last face ends at 32464 + 102 * 32 + 300 * 4 = 36928 bytes, the full member',
        },
        'acceptance': acceptance,
        'census': {'baseline': {'pass': 903, 'read': 169}, 'branch': {'pass': 912, 'read': 160}, 'regressions': 0, 'new_differing_members': 0},
        'bundles': {
            'examples/.f3z/example1.f3z': 'Fusion-saved outer archive: deflate members with save timestamps',
            're/Fusion/LocalOracle/Bundles/kit_production_example1.f3z': 'Kit-made outer archive: stored members, 1980 timestamps, reordered; every inner document is byte-identical to the Fusion-saved bundle',
        },
        'remaining': {
            'class_gaps_example1': lines('gaps-example1.jsonl'),
            'class_gaps_example2': lines('gaps-example2.jsonl'),
            'scene_gaps': {
                'example1 member 0': 'FProteinEffectAttribute: EffectAttribute base plus AssetReference text, not modelled',
                'example1 member 1': 'OverrideTransformAttribute: TransformAttribute plus a linked object, not modelled',
                'example1 member 2': 'globals lack GraphicsBlobFeatures and carry F360InstanceNode version 0',
                'example1 member 4': 'Fusion_mesh_000 world references 64048 of 128096 bytes, the tail is unreferenced mesh data',
                'example1 member 7': 'stream_mesh_000 references 35460 of 91620 bytes and Fusion_mesh_000 57680 of 706104 bytes',
            },
        },
    }
    (HERE / 'SceneStreams.json').write_text(json.dumps(evidence, indent=1, default=str) + '\n')
