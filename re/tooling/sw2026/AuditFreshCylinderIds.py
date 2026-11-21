from pathlib import Path
import argparse
import codecs
from hashlib import sha256
from io import BytesIO
import json
import os
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    spec = json.load(sys.stdin)
    sys.path[:0] = [str(args.root / 'src'), str(Path(__file__).parent)]
    from FreshCylinderInput import make_document
    import convert
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.base.WritePolicy import GetDocumentCaps
    from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadOutputAtom import ReadOutputAtom
    from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylNodes import ReadCylNodes
    from convert.adapters.solidworks.Archive.Construction.BodyNames.NameOutputMut import NameOutputMut
    from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
    from convert.adapters.solidworks.Archive.Construction.PlanarMates.ReadLogItems import ReadLogItems
    from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    for encoding in ('utf-16-le', 'utf-16-be', 'cp1252'):
        codecs.lookup(encoding)
    document = make_document(spec)
    document.AssertValid()
    GetDocumentCaps(document)
    active = [False]
    forbidden = []

    def guard(event, values):
        if not active[0]:
            return
        if event == 'open':
            forbidden.append({'event': event, 'path': str(values[0])})
            raise RuntimeError('file I/O is forbidden inside fresh in-memory generation')
        if event in ('subprocess.Popen', 'os.system', 'os.posix_spawn', 'socket.connect'):
            forbidden.append({'event': event})
            raise RuntimeError('runtime or network access is forbidden inside generation')

    sys.addaudithook(guard)
    options = WriteOptions(values={'final_destination': spec['native_destination']})
    active[0] = True
    try:
        candidate = PrepareNative(document, BytesIO(), spec['written_at'], options)
        repeated = PrepareNative(document, BytesIO(), spec['written_at'], options)
        assert repeated.BytesValue == candidate.BytesValue
        output = BytesIO()
        public = convert.write_document(document, output, destination_format='solidworks.sldprt',
            values={'final_destination': spec['native_destination']})
        public_bytes = output.getvalue()
        assert public.bytes_written == len(public_bytes)
        archive = SldprtArchive.from_bytes(candidate.BytesValue)
        link = ReadNativeLink(archive, 0)
    finally:
        active[0] = False
    assert not forbidden
    assert not any(value.startswith(('win32com', 'pythoncom', 'FreeCAD', 'OCC')) for value in sys.modules)
    boss = candidate.BossValue.FeatureValue
    profile = candidate.ProfileValue.ProfileValue
    sketch = candidate.ProfileValue.GeometryValue.SketchValue
    arc = candidate.ProfileValue.GeometryValue.ArcValue
    feature_id = FieldInt(boss.FieldsValue, 'f08')
    epoch = DatumTime(candidate.HeaderValue, feature_id)
    manager = candidate.SystemValue.RootValue.FieldsValue['fd88']
    logs = ReadLogItems(candidate.HeaderValue.FieldsValue['f20'], 'moLogs_c')
    checks = {}
    for label, operation in (
        ('saved_kernel_identity', lambda: ReadCylNodes(archive)),
        ('archive_output_atom', lambda: ReadOutputAtom(boss)),
        ('rectangular_cold_atom_helper_on_circle', lambda: NameOutputMut(candidate, 'independent output name')),
    ):
        try:
            operation()
        except (KeyError, TypeError, ValueError) as error:
            checks[label] = {'refused': True, 'error_type': type(error).__name__, 'error': str(error)}
        else:
            raise AssertionError(label + ' unexpectedly supplied native identity')
    parents = boss.FieldsValue['f60']['list']['items']
    assert len(parents) == 1 and parents[0]['o'] is profile
    assert profile.FieldsValue['pd_f80'] is sketch
    assert sketch.FieldsValue['arcs'][0]['arc'] is arc.FieldsValue
    assert manager['n6c'] == 0 and not manager['atoms']
    assert all(boss.FieldsValue[name] == 0 for name in ('has_f528', 'has_f530', 'n494'))
    assert not any('Partition' in name for name in candidate.StreamsValue)
    assert not any('Partition' in name for name in SldprtArchive.from_bytes(public_bytes).streams)
    args.output.mkdir(parents=True, exist_ok=False)
    paths = {}
    for role, payload in (('Candidate', candidate.BytesValue), ('Public', public_bytes)):
        folder = args.output / role
        folder.mkdir()
        path = folder / (spec['name'] + '.SLDPRT')
        path.write_bytes(payload)
        paths[role] = {'path': str(path), 'sha256': sha256(payload).hexdigest(), 'bytes': len(payload)}
    receipt = {
        'schema': 'kit.sw2026.fresh-cylinder-owner.v1', 'passed': True, 'case': spec['case'], 'pid': os.getpid(),
        'spec_sha256': sha256(json.dumps(spec, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest(),
        'neutral_document_sha256': sha256(document.to_json(indent=None).encode()).hexdigest(),
        'candidate_identities': {
            'model_id': candidate.SystemValue.RootValue.FieldsValue.get('f08'),
            'profile_id': FieldInt(profile.FieldsValue, 'f08'), 'extrusion_id': feature_id,
            'arc_permanent_marker': FieldInt(arc.FieldsValue, 'f08'),
            'arc_creation_id': FieldInt(arc.FieldsValue, 'f0c'), 'feature_epoch': epoch,
            'model_update_stamp': FieldInt(candidate.SystemValue.RootValue.FieldsValue, 'f1300'),
            'feature_log_ids': [FieldInt(log.FieldsValue, 'f48') for log in logs],
            'actual_profile_parent': True, 'actual_sketch_owner': True,
            'surface_identity_formula_inputs': [74, feature_id, epoch, 0, FieldInt(arc.FieldsValue, 'f08')],
            'formula_is_an_emitted_face_attribute': False,
            'manager_atom_count': manager['n6c'], 'manager_id_counter': manager['f260'],
            'boss_output_presence': {name: boss.FieldsValue[name] for name in ('has_f528', 'has_f530', 'n494')},
            'partition_stream_present': False,
        }, 'files': paths, 'stream_sha256': {name: sha256(value).hexdigest() for name, value in candidate.StreamsValue.items()},
        'refusals': checks, 'same_process_repeat_exact': True, 'runtime_file_io_attempts': len(forbidden),
        'cad_runtime_loaded': False, 'native_acceptance_measured': False, 'concentric_writer_output_count': 0,
        'part_candidate_output_count': 1, 'normal_public_part_output_count': 1,
    }
    path = args.output / 'Record.json'
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({'passed': True, 'record': str(path), 'sha256': sha256(path.read_bytes()).hexdigest()}))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(json.dumps({'passed': False, 'error_type': type(error).__name__, 'error': str(error)}))
        raise
