from pathlib import Path
import argparse
import codecs
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
import importlib.util
import json
import math
import os
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--factory', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    request = json.load(sys.stdin)
    sys.path.insert(0, str(args.root / 'src'))
    spec = importlib.util.spec_from_file_location('bounds_circle_input', args.factory)
    factory = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(factory)
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.base.WritePolicy import GetDocumentCaps
    from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
    from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.MakePartTarget import MakePartTarget
    from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectRectDims import ProjectRectDims
    from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
    from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
    from interchange.Enums.EnumGeometry import GeometryKind
    from interchange.geometry.Models.GeometryCurves import LineGeometry
    from interchange.geometry.Models.Sketch import SketchEntity
    from interchange.geometry.Models.VectorPlane import PlaneVector
    for encoding in ('utf-16-le', 'utf-16-be', 'cp1252'):
        codecs.lookup(encoding)
    document = factory.make_document(request['spec'])
    if request['kind'] == 'rectangle':
        points = request['vertices_mm']
        entities = tuple(SketchEntity(f'edge/{index}', GeometryKind.KLine,
            LineGeometry(PlaneVector(*point), PlaneVector(*points[(index+1) % len(points)])))
            for index, point in enumerate(points))
        sketch = replace(document.sketches[0], entities=entities, parameter_ids=(), constraints=(),
            closed_profile_entity_ids=(tuple(value.id for value in entities),))
        document = replace(document, sketches=(sketch,), parameters=(document.parameters[0],))
    document.AssertValid()
    GetDocumentCaps(document)
    active = [True]
    attempts = []

    def guard(event, values):
        if active[0] and event in ('open', 'subprocess.Popen', 'os.system', 'os.posix_spawn', 'socket.connect'):
            attempts.append(event)
            raise RuntimeError('bounds composition attempted external I/O or runtime execution')

    sys.addaudithook(guard)
    candidate = PrepareNative(document, BytesIO(), request['spec']['written_at'],
        WriteOptions(values={'final_destination': request['spec']['native_destination']}))
    original_hash = sha256(candidate.BytesValue).hexdigest()
    mutation = request.get('mutation')
    if mutation == 'top':
        candidate = replace(candidate, PlanValue=replace(candidate.PlanValue, AxisValue='y', PlaneName='Top Plane'))
    elif mutation == 'reverse':
        candidate = replace(candidate, PlanValue=replace(candidate.PlanValue, EndValue=replace(candidate.PlanValue.EndValue, IsReversed=True)))
    elif mutation == 'mid_plane':
        candidate = replace(candidate, PlanValue=replace(candidate.PlanValue, EndValue=replace(candidate.PlanValue.EndValue, ModeValue='mid_plane')))
    elif mutation == 'two_directions':
        candidate = replace(candidate, PlanValue=replace(candidate.PlanValue, EndValue=replace(candidate.PlanValue.EndValue, ModeValue='two_directions', SecondDepth=.0041)))
    elif mutation == 'stale_radius':
        candidate = replace(candidate, PlanValue=replace(candidate.PlanValue, CircleValue=replace(candidate.PlanValue.CircleValue, RadiusValue=candidate.PlanValue.CircleValue.RadiusValue+.001)))
    elif mutation == 'foreign_profile':
        candidate.ProfileValue.ProfileValue.FieldsValue['owner'] = ArchiveNode(RuntimeClass('moPart_c', 1), {})
    elif mutation == 'foreign_support':
        candidate.ProfileValue.ReferenceValue.FieldsValue['f58'].FieldsValue['owner'] = ArchiveNode(RuntimeClass('moPart_c', 1), {})
    elif mutation == 'stale_depth':
        candidate.BossValue.DimensionsValue[0].ParameterValue.FieldsValue['f58'] += .0023
    elif mutation == 'draft':
        candidate.BossValue.DimensionsValue[2].ParameterValue.FieldsValue['f58'] = .0179
    elif mutation == 'inactive_reverse':
        candidate.BossValue.DimensionsValue[1].ParameterValue.FieldsValue['f58'] += .0031
    elif mutation == 'foreign_dimension':
        candidate.BossValue.DimensionsValue[0].DimensionValue.FieldsValue['f28'] = candidate.BossValue.DimensionsValue[1].ParameterValue
    elif mutation == 'external_parameter':
        candidate.BossValue.DimensionsValue[0].ParameterValue.FieldsValue['f48'] = ArchiveNode(RuntimeClass('moLengthParameter_c', 1), {})
    elif mutation == 'extra_arc':
        sketch = candidate.ProfileValue.GeometryValue.SketchValue.FieldsValue
        sketch['arcs'] = (*sketch['arcs'], sketch['arcs'][0])
    elif mutation == 'foreign_arc_row':
        sketch = candidate.ProfileValue.GeometryValue.SketchValue.FieldsValue
        sketch['arcs'] = ({'flags':0, 'arc':dict(candidate.ProfileValue.GeometryValue.ArcValue.FieldsValue)},)
    elif mutation == 'cut_owner':
        candidate = replace(candidate, CutValue=candidate.BossValue)
    refused = None
    target = None
    try:
        target = MakePartTarget(candidate)
    except (TypeError, ValueError) as error:
        refused = {'type': type(error).__name__, 'message': str(error)}
    if request['expected_refusal']:
        assert refused is not None
    else:
        assert target is not None and refused is None
    projection_refusal = None
    if request['kind'] == 'circle' and mutation is None:
        try:
            ProjectRectDims(document)
        except (TypeError, ValueError) as error:
            projection_refusal = str(error)
        assert projection_refusal is not None
    active[0] = False
    assert not attempts
    result = {'passed': True, 'pid': os.getpid(), 'name': request['spec']['name'],
        'kind': request['kind'], 'mutation': mutation, 'refusal': refused,
        'part_sha256': original_hash, 'part_bytes': len(candidate.BytesValue),
        'streams_sha256': {name:sha256(value).hexdigest() for name,value in candidate.StreamsValue.items()},
        'public_rectangle_child_projection_refused': projection_refusal,
        'runtime_file_open_attempts': len(attempts), 'native_processes':0, 'hidden_inputs_read':0,
        'bounds':None, 'target_aliases':None}
    if target is not None:
        result['bounds'] = dict(target.BoundsValue)
        result['target_aliases'] = {'root':target.RootValue is candidate.SystemValue.RootValue,
            'configuration':target.CurrentConfig is candidate.CurrentConfig,
            'header':target.HeaderValue is candidate.HeaderValue,
            'config_graph':target.ConfigValue is candidate.ConfigValue,
            'resolved_graph':target.ResolvedValue is candidate.ResolvedValue,
            'streams':target.StreamsValue is candidate.StreamsValue,
            'bytes':target.BytesValue is candidate.BytesValue}
        assert all(result['target_aliases'].values())
        if request['kind'] == 'circle':
            cx, cy = (value*.001 for value in request['spec']['center_mm'])
            radius, depth = request['spec']['radius_mm']*.001, request['spec']['depth_mm']*.001
            low, high = (cx-radius,cy-radius,0.),(cx+radius,cy+radius,depth)
            center = tuple((a+z)*.5 for a,z in zip(low,high))
            sphere = math.sqrt(2*radius*radius+depth*depth*.25)
            expected = (*center,*high,*low,sphere)
            assert all(math.isclose(target.BoundsValue[f'b{i}'],value,rel_tol=2e-15,abs_tol=1e-18) for i,value in enumerate(expected))
    assert not args.output.exists()
    args.output.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'passed':True,'sha256':sha256(args.output.read_bytes()).hexdigest()}))


if __name__ == '__main__':
    main()
