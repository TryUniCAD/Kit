from argparse import ArgumentParser
from base64 import b64decode, b64encode
import codecs
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from io import BytesIO
import json
from math import dist, isclose, pi, prod
from pathlib import Path, PureWindowsPath
from shutil import copyfile, copytree, ignore_patterns
import subprocess
import sys
from tarfile import open as open_tar
from tempfile import TemporaryDirectory


HERE = Path(__file__).resolve()
REPO = HERE.parents[4]
PACKET = Path('/Users/odin/Documents/UniCAD/Oracle121Takeover/MidPlaneStockSecondary02')
FREEZE = '61365d7aee925dcf5b75e6bb5b8e342bdc0a58d69be7a888e6745acf22a79c9e'
NATIVE = 'a77fd9262fb9d92e31cdfa18778c3a9d7dd7e8543802795956ead2a6a8d65892'
AT = 'cb78cb757cc142930125639810991def7d5d8255'
FILES = {
    'src/convert/adapters/solidworks/Archive/Construction/ThroughAll/MakeScopedThru.py': 'b0103c3e8a1cf2978269fdebcc828257ad07865091550f97b4289a23c91c91a4',
    'src/convert/adapters/solidworks/Core/TypedResolved/Cuts/CheckColdPocket.py': '2510773e5a0183d50e07209aa0e8ed57eadb8775d607fe32b626edf58d09ab07',
    'src/convert/adapters/solidworks/Core/TypedResolved/Geometry/CheckPrismEnd.py': 'b1e5a253efe323968c0d57b1066d67078176563de6cdb94b78c1092fab275d6b',
    'src/convert/adapters/solidworks/Core/TypedResolved/Geometry/ReadPrismPlan.py': '7422b644061f138f0d4105367ce7d67005c9f4b42d7539d734fb111c62523010',
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def wire(data):
    return (json.dumps(data, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


def digest(data):
    return sha256(data).hexdigest()


def checked(path, pin):
    require(path.is_file() and not path.is_symlink(), 'missing or redirected verification file: ' + path.name)
    data = path.read_bytes()
    require(digest(data) == pin, 'verification file digest differs: ' + path.name)
    return data


def build_document(recipe, selected):
    from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import PrincipalFrame
    from interchange.document.Models.DocumentModel import CadDocument
    from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
    from interchange.Enums.EnumGeometry import GeometryKind
    from interchange.Enums.EnumValues import ValueKind
    from interchange.Features.FeatureBody import DesignBody
    from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
    from interchange.Features.FeatureStep import FeatureStep
    from interchange.geometry.Models.GeometryCurves import CircleGeometry, LineGeometry
    from interchange.geometry.Models.Selection import SelectPathElem, Selection
    from interchange.geometry.Models.Sketch import ConstraintRef, Sketch, SketchEntity, SketchRelation
    from interchange.geometry.Models.SupportPlane import SupportPlane
    from interchange.geometry.Models.Transform import Transform
    from interchange.geometry.Models.VectorPlane import PlaneVector
    from interchange.geometry.Models.VectorSpace import SpaceVector
    from interchange.Records.RecordConfig import Configuration
    from interchange.Records.RecordParameter import Parameter, ParameterValue
    from interchange.Records.RecordSource import CadSource

    width, height, depth = recipe['stock_size_m']
    cx, cy = recipe['stock_center_m']
    points = tuple(PlaneVector(1000 * (cx + u * width / 2), 1000 * (cy + v * height / 2))
                   for u, v in ((-1, -1), (1, -1), (1, 1), (-1, 1)))
    edge_ids = tuple(f'line/{index}' for index in range(4))
    lines = tuple(SketchEntity(key, GeometryKind.KLine, LineGeometry(points[index], points[(index + 1) % 4]))
                  for index, key in enumerate(edge_ids))
    relations = tuple(SketchRelation('axis/' + key, 'horizontal' if index % 2 == 0 else 'vertical', (ConstraintRef(key),))
                      for index, key in enumerate(edge_ids))
    frame = PrincipalFrame(recipe['axis'])
    transform = Transform(*(SpaceVector(*row) for row in (frame.OriginValue, frame.AxisU, frame.AxisV, frame.NormalValue)))
    plane = SupportPlane('plane/stock', {'x': 'Right Plane', 'y': 'Top Plane', 'z': 'Front Plane'}[recipe['axis']], transform)
    stock = Sketch('sketch/stock', 'StockProfile', plane.id, lines, constraints=relations, closed_profile_entity_ids=(edge_ids,))
    circle = SketchEntity('circle/cut', GeometryKind.KCircle, CircleGeometry(
        PlaneVector(*(value * 1000 for value in recipe['circle_center_m'])), recipe['radius_m'] * 1000))
    profile = Sketch('sketch/cut', 'ThroughProfile', plane.id, (circle,), closed_profile_entity_ids=((circle.id,),))
    length = ParameterValue(depth * 1000, ValueKind.KLength, 'mm')
    boss = FeatureStep('feature/stock', 'StockBoss', FeatureKind.KExtrusion, 0, sketch_id=stock.id, parameter_ids=('parameter/stock',),
                       operation=BooleanOp.KCreate, definition=ExtrudeFeature(length, ExtrudeEnd.KMidPlane, symmetric=True))
    selection = Selection('selection/stock', 'StockBoss body', (SelectPathElem('feature', boss.id, 'body'),))
    cut = FeatureStep('feature/cut', 'ThroughFeature', FeatureKind.KExtrusion, 1, (boss.id,), profile.id,
                      operation=BooleanOp.KCutOperation, selection_ids=(selection.id,) if selected else (), definition=ExtrudeFeature(
                          end_condition=ExtrudeEnd.KThroughAll, reversed=recipe['direction'] != 'reverse',
                          second_end_condition=ExtrudeEnd.KThroughAll if recipe['direction'] == 'both' else None))
    return CadDocument(CadSource('kit-neutral', '<disclosed-stock-secondary-calibration>', '0' * 64),
                       (Configuration('configuration/default', 'Default', True),),
                       (Parameter('parameter/stock', 'D1', length, owner_id=boss.id),), (plane,), (stock, profile),
                       (selection,) if selected else (), (boss, cut), (DesignBody('body/cut', boss.name, cut.id),), metadata={'name': recipe['name']})


def measured_geometry(document, target):
    from interchange.brep.Curves.BrepCurves import CircleCurve

    body, = document.bodies
    brep, topology = document.brep, body.topology
    require(brep is not None and not brep.validate(frozenset((body.id,))) and not document.brep_payloads
            and topology.valid and topology.solid_count == target['body_count'] == 1,
            'strict reader did not produce its own closed single solid')
    low, high = (tuple(getattr(point, key) for key in 'xyz') for point in (topology.bounding_box.minimum, topology.bounding_box.maximum))
    outer = prod(b - a for a, b in zip(low, high, strict=True))
    first, second = (curve for curve in brep.curves if isinstance(curve, CircleCurve))
    rims = [tuple(getattr(curve.center, axis) for axis in 'xyz') for curve in (first, second)]
    cavity = pi * first.radius**2 * dist(*rims)
    center = [(outer * (low[index] + high[index]) / 2 - cavity * (rims[0][index] + rims[1][index]) / 2)
              / (outer - cavity) * 0.001 for index in range(3)]
    result = {'volume': topology.volume * 1e-9, 'area': topology.surface_area * 1e-6, 'com': center,
              'topology': [len(brep.faces), len(brep.edges), len(brep.vertices)]}
    require(result['topology'] == [8, 14, 10] and first.radius == second.radius
            and isclose(topology.volume, outer - cavity, rel_tol=1e-10)
            and all(isclose(result[key], target[key], rel_tol=1e-10) for key in ('volume', 'area'))
            and all(isclose(a, b, rel_tol=1e-10, abs_tol=1e-12) for a, b in zip(center, target['com'], strict=True)),
            'signed reconstructed geometry disagrees with independent disclosed prediction')
    return result


def worker(root, mode):
    request = json.load(sys.stdin)
    sys.path[:0] = [str(root / 'src'), str(HERE.parent)]
    from convert import open_document
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileKey
    from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
    from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat
    from convert.adapters.solidworks.Core.Preparation.ThroughAll.PrepareThroughPart import PrepareThroughPart
    from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
    from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
    from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadCutBodyLink import ReadCutBodyLink
    from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismParam import ReadPrismParam
    from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
    from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from interchange.Features.FeatureExtrude import ExtrudeEnd
    from SdkNativeRoundTrips import roundtrips

    for encoding in ('ascii', 'latin-1', 'utf-8', 'utf-8-sig', 'utf-16-le', 'utf-16-be'):
        codecs.lookup(encoding)
    for module in ('interchange.brep.Curves.BrepCurves', 'interchange.brep.Validation.BrepValidate',
                   'interchange.document.Behavior.DocumentIo', 'interchange.document.Models.DocumentProvenance',
                   'interchange.document.Validation.DocumentAssemblyValidate', 'interchange.document.Validation.DocumentFeatureValidate',
                   'interchange.document.Validation.DocumentReferenceValidate'):
        import_module(module)
    recipe = request['recipe']
    variants = {'front_forward': recipe}
    for key, axis, direction in (('top_reverse', 'y', 'reverse'), ('right_both', 'x', 'both')):
        name = 'StockSecondary' + key.replace('_', '').title()
        variants[key] = dict(recipe, axis=axis, direction=direction, name=name,
                             native_path=str(PureWindowsPath(recipe['native_path']).with_name(name + '.SLDPRT')))
    build_document(recipe, True)
    attempts = []

    def protect(event, args):
        if event in {'open', 'os.listdir', 'os.scandir', 'os.system', 'os.exec', 'os.fork', 'os.posix_spawn', 'os.startfile'} or event.startswith(('subprocess.', 'socket.', 'ctypes.', 'winreg.')):
            attempts.append(event)
            raise PermissionError('stock secondary SDK worker attempted external access: ' + event)

    sys.addaudithook(protect)

    def owners(link):
        roots = link.ResolvedValue.RootsValue
        features = {NativeNodeId(node): node for node in roots}
        return features, ReadExtrude(link, roots[-3], features), ReadExtrude(link, roots[-1], features, IsCut=True)

    def read(data):
        result = open_document(data, source_format='solidworks.sldprt', strict=True, include_tessellation=False)
        result.assert_valid()
        require(result.brep is not None and len(result.bodies) == 1 and not result.brep_payloads, 'strict cold SDK geometry missing')
        return result

    corpus, generated = {}, {}
    for key, values in variants.items():
        corpus[key], generated[key] = {}, {}
        for scope in ('all', 'selected'):
            sink = BytesIO()
            candidate = PrepareThroughPart(build_document(values, scope == 'selected'), sink, values['written_at'],
                                           WriteOptions(configuration='Default', values={'final_destination': values['native_path']}))
            data = candidate.BytesValue
            require(sink.getvalue() == b'', 'internal preparation wrote to its sink')
            archive = SldprtArchive.from_bytes(data)
            link, _, _, _, streams = roundtrips(archive, False)
            features, boss, cut = owners(link)
            null = mode == 'changed' and scope == 'selected'
            fields = boss.EndValue.FieldsValue
            require(len(streams) == 10 and ReadFileKey(link.ConfigValue.HeaderValue.FieldsValue['f38'])[1] == values['native_path']
                    and 'f20' in fields and (fields['f20'] is None) == null
                    and boss.ModeValue == ExtrudeEnd.KMidPlane and not boss.IsReversed and boss.SecondValue is None
                    and boss.RequireDepth().DepthValue.name == 'D1' and cut.ModeValue == ExtrudeEnd.KThroughAll and cut.DepthValue is None,
                    'generated actual end owner, dimensional role or locator differs')
            dims = {name: ReadPrismParam(fields[name], angular)[0].FieldsValue['f50']
                    for name, angular in (('f18', False), ('fc8', True), ('fd0', True))}
            document = read(data)
            body = document.metadata['solidworks.typed_resolved_semantics']['cut_body_dependency']
            require(body == ReadCutBodyLink(link, features, boss, cut)
                    and body['binding'] == ('cold_selected_stock_atom' if scope == 'selected' else 'cold_all_bodies_intersection'),
                    'normal strict reader stock association differs from actual typed owner')
            corpus[key][scope] = {'sha256': digest(data), 'bytes': len(data), 'streams': streams, 'active_and_draft_ids': dims,
                                  'explicit_null_f20': null, 'binding': body, 'strict_geometry': True}
            generated[key][scope] = data

    front = generated['front_forward']
    geometry = measured_geometry(read(front['selected']), request['prediction'])
    negatives = {}
    if mode == 'changed':
        present = b64decode(request['disclosed_present'], validate=True)
        _, old_stock, _ = owners(ReadNativeLink(SldprtArchive.from_bytes(present), 0))
        require(old_stock.EndValue.FieldsValue['f20'] is not None and old_stock.SecondValue is None,
                'disclosed old control lost its initialized inactive display')
        require(measured_geometry(read(present), request['prediction']) == geometry, 'old selected-stock control shape changed')

        def check_bad(label, data):
            archive = SldprtArchive.from_bytes(data)
            link = ReadNativeLink(archive, 0)
            end = link.ResolvedValue.RootsValue[-3].FieldsValue['f818'].FieldsValue
            if label == 'missing-f20':
                del end['f20']
            elif label == 'all-body-null':
                end['f20'] = None
            elif label == 'inactive-value':
                _, parameter, value = ReadPrismParam(end['f20'], False)
                parameter.FieldsValue['f58'] = value / 2
            elif label == 'nonzero-draft':
                _, parameter, _ = ReadPrismParam(end['fc8'], True)
                parameter.FieldsValue['f58'] = 0.25
            elif label == 'duplicate-draft-id':
                one, _, _ = ReadPrismParam(end['fc8'], True)
                two, _, _ = ReadPrismParam(end['fd0'], True)
                two.FieldsValue['f50'] = one.FieldsValue['f50']
            elif label == 'unassigned-draft-id':
                dimension, _, _ = ReadPrismParam(end['fd0'], True)
                dimension.FieldsValue['f50'] = -1
            elif label == 'foreign-stock-wrapper':
                link.ResolvedValue.RootsValue[-1].FieldsValue['f548']['items'][0]['o'].FieldsValue['f108'] += 1
            elif label == 'active-second-end':
                end.update(f08=0, f0c=0)
            else:
                key, value = {'no-primary': ('f18', None), 'no-draft': ('fd0', None), 'reversed-stock': ('f8c', 1)}[label]
                end[key] = value
            try:
                ReadCutBodyLink(link, *owners(link))
            except ValueError as error:
                result = {'owner_refusal': str(error)}
            else:
                raise ValueError('altered complete linked owner unexpectedly admitted: ' + label)
            if label != 'missing-f20':
                cfg, cfg_graph = WriteConfigMut(link.ConfigValue.RootValue, 19000, link.ConfigValue.HeaderValue)
                resolved, _ = WriteResolMut(link.ResolvedValue.RootsValue, link.ResolvedValue.ExtraFields, 19000,
                                            cfg_graph.MapValue, link.ResolvedValue.ContextValue)
                streams = {row.name: row.data for row in archive.records}
                streams.update({'Contents/Config-0': cfg, 'Contents/Config-0-ResolvedFeatures': resolved})
                try:
                    read(BuildSldprt(streams, FormatVersion=4))
                except SldprtFormat as error:
                    require(str(error) == 'SLDPRT contains no readable Parasolid payload', 'unexpected strict geometry refusal')
                    result['strict_public_refusal'] = str(error)
                else:
                    raise ValueError('altered complete archive reconstructed a public solid: ' + label)
            return result

        for label in ('missing-f20', 'no-primary', 'no-draft', 'nonzero-draft', 'duplicate-draft-id', 'unassigned-draft-id', 'reversed-stock',
                      'active-second-end', 'foreign-stock-wrapper', 'inactive-value', 'all-body-null'):
            payload = {'inactive-value': present, 'all-body-null': front['all']}.get(label, front['selected'])
            negatives[label] = check_bad(label, payload)
    require(not attempts, 'SDK swallowed attempted runtime access')
    return {'cases': corpus, 'geometry': geometry, 'negatives': negatives, 'runtime_external_accesses': len(attempts),
            'front': b64encode(front['selected']).decode()}


def manifest(src):
    return {path.relative_to(src).as_posix(): digest(path.read_bytes()) for path in sorted(src.rglob('*'))
            if path.is_file() and path.suffix != '.pyc' and '__pycache__' not in path.parts}


def verify(output):
    require(not output.exists(), 'choose a fresh verification report output')
    freeze = json.loads(checked(PACKET / 'Freeze.json', FREEZE))
    native = json.loads(checked(REPO / 're/solidworks/measurements/2026/MidPlaneStockSecondaryNative01.json', NATIVE))
    require(native['passed'] and native['freeze_sha256'] == FREEZE and len(native['phase_sha256']) == 6,
            'exact disclosed native evidence is unqualified')
    case = json.loads(checked(PACKET / 'CandidateCase.json', freeze['files']['CandidateCase.json']))
    proof = json.loads(checked(PACKET / 'BuildProof.json', freeze['files']['BuildProof.json']))
    verified = {name: checked(PACKET / f'Arms/{name}/StockSecondaryCalibration.SLDPRT', proof['arms'][name]['sha256']) for name in ('Present', 'Absent')}
    request = {'recipe': case['recipe'], 'prediction': case['prediction']['source']}
    current = manifest(REPO / 'src')
    with TemporaryDirectory(prefix='KitStockSecondaryVerify-') as tmp:
        stage = Path(tmp)
        code = stage / 'Code'
        copytree(REPO / 'src', code / 'src', ignore=ignore_patterns('__pycache__', '*.pyc'))
        require(manifest(code / 'src') == current, 'copied SDK changed before verification')
        runner = stage / HERE.name
        copyfile(HERE, runner)
        tools = ('SdkNativeRoundTrips.py',)
        for name in tools:
            (stage / name).write_bytes(checked(PACKET / 'Tools' / name, freeze['files']['Tools/' + name]))

        def run(mode, inputs):
            command = [sys.executable, '-I', '-B', str(runner), 'worker', str(code), mode]
            process = subprocess.run(command, input=wire(inputs), capture_output=True, timeout=120)
            require(process.returncode == 0, 'verified worker failed: ' + process.stderr.decode(errors='replace'))
            return json.loads(process.stdout)

        current_request = request | {'disclosed_present': b64encode(verified['Present']).decode()}
        first = run('changed', current_request)
        second = run('changed', current_request)
        require(first == second, 'two fresh SDK workers disagree')
        require(manifest(code / 'src') == current, 'SDK source changed during runtime verification')
        originals = checked(PACKET / 'Sdk.tar', freeze['files']['Sdk.tar'])
        with open_tar(fileobj=BytesIO(originals), mode='r:') as archive:
            for relative, pin in FILES.items():
                prior = archive.extractfile(relative).read()
                require(digest(prior) == pin, 'wrong four-file baseline source: ' + relative)
                (code / relative).write_bytes(prior)
        baseline = manifest(code / 'src')
        require({key for key in baseline if baseline[key] != current[key]} == {path[4:] for path in FILES},
                'comparison baseline differs outside the exact four approved product files')
        old = run('baseline', request)
        require(manifest(code / 'src') == baseline, 'baseline SDK source changed during execution')

    require(b64decode(first.pop('front'), validate=True) == verified['Absent']
            and b64decode(old.pop('front'), validate=True) == verified['Present'], 'normal SDK bytes differ from the exact native-tested arms')
    for key in first['cases']:
        updated, original = first['cases'][key], old['cases'][key]
        require(updated['all'] == original['all'], 'ordinary all bodies path changed: ' + key)
        new, previous = updated['selected'], original['selected']
        require(new['active_and_draft_ids'] == previous['active_and_draft_ids'] and new['binding'] == previous['binding']
                and {name for name, expected in new['streams'].items() if previous['streams'][name] != expected}
                == {'Contents/Config-0-ResolvedFeatures'}, 'selected paths changed outside the measured display owner: ' + key)
    require(manifest(REPO / 'src') == current, 'live SDK changed during guarded proof')
    result = {'passed': True, 'source_start': AT, 'native_result_sha256': NATIVE, 'freeze_sha256': FREEZE,
              'code_manifest_sha256': digest(wire(current)), 'baseline_manifest_sha256': digest(wire(baseline)),
              'source_files': len(current), 'changed_files': {path: current[path[4:]] for path in FILES},
              'tool_sha256': digest(HERE.read_bytes()), 'supporting_tools_sha256': {f'Tools/{name}': freeze['files'][f'Tools/{name}'] for name in tools},
              'workers': 3, 'normal_sdk_matched_both_native_tested_arms': True, 'current': first,
              'baseline': old, 'runtime_external_accesses': 0, 'new_native_launches': 0,
              'whole_source_admitted': False, 'public_writer_qualified': False, 'heldout_credit': 0}
    encoded = wire(result)
    with output.open('xb') as handle:
        handle.write(encoded)
    return {'passed': True, 'result_sha256': digest(encoded), 'workers': 3, 'refusals': len(first['negatives']),
            'selected_sha256': first['cases']['front_forward']['selected']['sha256']}


def main():
    parser = ArgumentParser()
    commands = parser.add_subparsers(dest='action', required=True)
    commands.add_parser('verify').add_argument('output', type=Path)
    child = commands.add_parser('worker')
    child.add_argument('code', type=Path)
    child.add_argument('mode', choices=('baseline', 'changed'))
    args = parser.parse_args()
    result = verify(args.output) if args.action == 'verify' else worker(args.code, args.mode)
    sys.stdout.buffer.write(wire(result))


if __name__ == '__main__':
    main()
