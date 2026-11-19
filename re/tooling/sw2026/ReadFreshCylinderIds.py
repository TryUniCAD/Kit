from pathlib import Path
import argparse
from collections import Counter
from hashlib import sha256
import json
import math
import os
import re
import sys


def execute(args, request):
    source = Path(request['path'])
    assert sha256(source.read_bytes()).hexdigest() == request['sha256']
    sys.path.insert(0, str(args.root / 'src'))
    import convert
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Container.Parasolid import EncodeBrep, DecodeBrep, EncodePartition
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
    from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt
    from interchange.brep.Surfaces.BrepSurfaces import CylinderSurface, PlaneSurface
    spec = request['spec']
    mode = request['mode']
    document = convert.open_document(source) if mode == 'default' else convert.open_document(source, include_brep=False, include_tessellation=False)
    document.AssertValid()
    assert len(document.bodies) == len(document.sketches) == 1
    assert sum(str(feature.kind) == 'extrusion' for feature in document.feature_timeline) == 1
    assert len(document.parameters) == 2 and document.configurations[0].name == 'Default'
    archive = SldprtArchive.from_bytes(source.read_bytes())
    link = ReadNativeLink(archive, 0)
    boss, = (node for node in link.ResolvedValue.RootsValue if node and node.ClassValue.NameValue == 'moExtrusion_c')
    assert len(document.feature_timeline) == len(link.ResolvedValue.RootsValue)
    header_epoch = DatumTime(link.ConfigValue.HeaderValue, FieldInt(boss.FieldsValue, 'f08'))
    result = {'schema': 'kit.sw2026.fresh-cylinder-public-read.v1', 'passed': True, 'case': spec['case'], 'pid': os.getpid(),
        'mode': mode, 'role': request['role'], 'source_sha256': request['sha256'],
        'document_sha256': sha256(document.to_json(indent=None).encode()).hexdigest(),
        'ordered_feature_timeline': [{'id': value.id, 'name': value.name, 'kind': str(value.kind)} for value in document.feature_timeline],
        'parameter_values': [{'id': v.id, 'name': v.name, 'value': v.value.value, 'unit': v.value.unit, 'owner': v.owner_id} for v in document.parameters],
        'extrusion_id': FieldInt(boss.FieldsValue, 'f08'), 'actual_header_feature_epoch': header_epoch,
        'has_native_partition': any('Partition' in name for name in archive.streams),
        'brep_present': document.brep is not None, 'generic_encode': None,
        'native_concentric_identity_proved': False, 'native_acceptance_measured': False,
    }
    assert not result['has_native_partition']
    if mode == 'metadata':
        assert document.brep is None
    else:
        brep = document.brep
        assert brep is not None and not brep.validate(frozenset(body.id for body in document.bodies))
        cylinders = tuple(value for value in brep.surfaces if isinstance(value, CylinderSurface))
        planes = tuple(value for value in brep.surfaces if isinstance(value, PlaneSurface))
        assert len(brep.bodies) == 1 and len(brep.faces) == 3 and len(cylinders) == 1 and len(planes) == 2
        cylinder, = cylinders
        side, = (face for face in brep.faces if face.surface_id == cylinder.id)
        radius, depth = spec['radius_mm'], spec['depth_mm']
        expected_volume = math.pi * radius * radius * depth
        expected_area = 2 * math.pi * radius * (depth + radius)
        topology = document.bodies[0].topology
        assert topology.valid and math.isclose(topology.volume, expected_volume, rel_tol=1e-12)
        assert math.isclose(topology.surface_area, expected_area, rel_tol=1e-12)
        assert math.isclose(cylinder.radius, radius, rel_tol=1e-12)
        assert any(value.code == 'sldprt.brep_reconstructed' for value in document.diagnostics)
        vector = lambda value: [value.x, value.y, value.z]
        result['geometry'] = {'faces': len(brep.faces), 'edges': len(brep.edges), 'vertices': len(brep.vertices),
            'body_id': brep.bodies[0].id, 'side_face_id': side.id, 'side_surface_id': cylinder.id,
            'radius_mm': cylinder.radius, 'origin_mm': vector(cylinder.origin), 'axis': vector(cylinder.axis),
            'volume_mm3': topology.volume, 'area_mm2': topology.surface_area,
            'expected_volume_mm3': expected_volume, 'expected_area_mm2': expected_area,
            'method': 'typed_parametric_circular_boss', 'native_kernel_identity': False,
            'identity_status_basis': 'absent partition plus the existing ReadCircPlan constructor native_kernel_identity=False rule',
            'body_attribute_names': sorted(brep.bodies[0].attributes), 'side_attribute_names': sorted(side.attributes)}
        calls = Counter()
        forbidden = []
        active = [True]

        def guard(event, values):
            if active[0] and event in ('open', 'subprocess.Popen', 'os.system', 'os.posix_spawn', 'socket.connect'):
                forbidden.append(event)
                raise RuntimeError('generic analytic encoding must remain source-only')

        def profile(frame, event, arg):
            if event == 'call' and frame.f_code.co_filename.endswith('/Geometry/Parasolid.py'):
                calls[frame.f_code.co_name] += 1

        sys.addaudithook(guard)
        sys.setprofile(profile)
        try:
            payload = EncodeBrep(brep, partition=True)
            partition = EncodePartition(payload)
            decoded = DecodeBrep(payload)
            assert decoded is not None and not decoded.validate()
            assert len(decoded.faces) == len(brep.faces) and len(decoded.bodies) == len(brep.bodies)
        finally:
            sys.setprofile(None)
            active[0] = False
        assert not forbidden
        assert all(calls[name] == 0 for name in ('EncodeBlankApi', 'EncodeBlankPart', 'WriteSolidAttrs', 'WriteBodySuffix'))
        assert not any(name in payload for name in (b'FACE_ID_2001', b'ATOM_ID_2001'))
        args.output.mkdir(parents=True, exist_ok=False)
        (args.output / 'AnalyticOnly.x_b').write_bytes(payload)
        (args.output / 'AnalyticOnly.Partition').write_bytes(partition)
        result['generic_encode'] = {'passed': True, 'payload_sha256': sha256(payload).hexdigest(),
            'payload_bytes': len(payload), 'partition_sha256': sha256(partition).hexdigest(), 'partition_bytes': len(partition),
            'schema': re.search(rb'SCH_[0-9A-Z_]+', payload[:8192]).group().decode(),
            'counts_preserved': True, 'cad_runtime': False, 'attached_to_native_document': False,
            'saved_face_and_atom_attributes_present': False, 'runtime_file_io_attempts': len(forbidden),
            'calls': {name: calls[name] for name in ('EncodeBrepModel', 'EncodeBrepBody', 'EmitVendorMut', 'EncodePartData', 'EncodeBlankApi', 'EncodeBlankPart', 'WriteSolidAttrs', 'WriteBodySuffix')},
            'decoded_body_attribute_names': sorted(decoded.bodies[0].attributes),
            'decoded_face_attribute_names': [sorted(value.attributes) for value in decoded.faces]}
    args.output.mkdir(parents=True, exist_ok=True)
    path = args.output / 'Record.json'
    path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({'passed': True, 'record': str(path), 'sha256': sha256(path.read_bytes()).hexdigest()}))


if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('--root', type=Path, required=True)
        parser.add_argument('--output', type=Path, required=True)
        args = parser.parse_args()
        execute(args, json.load(sys.stdin))
    except Exception as error:
        print(json.dumps({'passed': False, 'error_type': type(error).__name__, 'error': str(error)}))
        raise
