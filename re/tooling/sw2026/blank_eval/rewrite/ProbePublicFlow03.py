from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
from hashlib import sha256
import importlib
import io
import json
from pathlib import Path
import sys
from uuid import UUID

parser = argparse.ArgumentParser()
parser.add_argument('--code', type=Path, required=True)
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--source-sha256', required=True)
parser.add_argument('--route', choices=('api', 'api-json', 'cli', 'cli-explicit'), required=True)
parser.add_argument('--target', type=Path, required=True)
parser.add_argument('--report', type=Path, required=True)
parser.add_argument('--native-qualified', choices=('yes', 'no'), default='no')
args = parser.parse_args()
sys.dont_write_bytecode = True
sys.path[:0] = [str(args.code / 'src'), str(args.code / 'Cli')]
from convert.api import open_document, write_document
from interchange.document.Models.DocumentModel import CadDocument
from convert.adapters.solidworks.Core.DrawingWriting.Rewrite.ReadBlankInput import ReadBlankInput
from convert.adapters.solidworks.Container.Container import SldprtArchive
sys.path.insert(0, str(Path(__file__).resolve().parent))
from BlankRewriteGuard import OutputGuard
source = args.source.read_bytes()
assert sha256(source).hexdigest() == args.source_sha256
original = open_document(source, source_format='solidworks.slddrw', strict=True)
intent = ReadBlankInput(original.source.attributes['solidworks.blank.intent'])
for name in ('DocumentFeatureValidate', 'DocumentReferenceValidate', 'DocumentAssemblyValidate'):
    importlib.import_module('interchange.document.Validation.' + name)
importlib.import_module('interchange.document.Models.DocumentProvenance')
emitter = importlib.import_module('convert.adapters.solidworks.Core.DrawingWriting.EmitBlankDrawingMut')
emitter.ReadTime = lambda: 1795105101
emitter.AllocateBlockId = lambda: UUID('8e37440a-0096-4ee5-b14a-f05d97e62107')
args.target.parent.mkdir(parents=True, exist_ok=False)
guard = OutputGuard(args.target.parent)
sys.addaudithook(guard.event)
prepare = emitter.PrepareBlankDrawing
calls = []
prepared_payloads = []


def guarded_prepare(*values, **options):
    calls.append(True)
    try:
        guard.active = True
        value = prepare(*values, **options)
        prepared_payloads.append(value.BytesValue)
        return value
    finally:
        guard.active = False


emitter.PrepareBlankDrawing = guarded_prepare
result = {'schema': 'kit.sw2026.public-preserved-blank-flow.v1', 'passed': False, 'route': args.route, 'source_sha256': args.source_sha256}
try:
    if args.route.startswith('api'):
        document = original if args.route == 'api' else CadDocument.from_json(original.to_json(indent=None))
        output = write_document(document, args.target, destination_format='solidworks.slddrw')
        flags = [output.vendor_loadable, output.application_usable]
    else:
        sys.argv = ['kit', 'convert', str(args.source), str(args.target), '--json']
        if args.route == 'cli-explicit':
            sys.argv += ['--from', 'solidworks.slddrw', '--to', 'solidworks.slddrw']
        from KitCli.MainEntry import MainEntry
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = MainEntry()
        result.update(cli_exit_code=code, cli_stdout_sha256=sha256(stdout.getvalue().encode()).hexdigest(), cli_stderr=stderr.getvalue())
        if args.native_qualified == 'yes':
            assert code == 0, stderr.getvalue()
            data = json.loads(stdout.getvalue())
            flags = [data['vendor_loadable'], data['application_usable']]
        else:
            assert code == 1 and not args.target.exists(), 'unqualified CLI must refuse and roll back'
            data = json.loads(stderr.getvalue())
            assert data['error'] == 'ApplicationUsabilityError' and data['details']['vendor_loadable'] is False and data['details']['application_usable'] is False
            assert prepared_payloads
            flags = [False, False]
            result['expected_unqualified_cli_refusal'] = True
    assert flags == ([True, True] if args.native_qualified == 'yes' else [False, False])
    payload = args.target.read_bytes() if args.target.exists() else prepared_payloads[-1]
    new = open_document(payload, source_format='solidworks.slddrw', strict=True)
    typed = ReadBlankInput(new.source.attributes['solidworks.blank.intent'])
    assert typed.HeaderValue == intent.HeaderValue and typed.HistoryValue == intent.HistoryValue and typed.OptionsValue == intent.OptionsValue and typed.UiSettings == intent.UiSettings
    assert new.drawing == original.drawing and typed.FileValue.SavedAt == 1795105101
    before = SldprtArchive.from_bytes(source).streams
    after = SldprtArchive.from_bytes(payload).streams
    changed = [name for name in before if before[name] != after[name]]
    assert set(changed) == {'Header2', 'Contents/Definition'}
    assert calls and not guard.denied and all(value == payload for value in prepared_payloads)
    assert sha256(args.source.read_bytes()).hexdigest() == args.source_sha256
    result.update(passed=True, output_sha256=sha256(payload).hexdigest(), output_size=len(payload), changed_streams=changed, flags=flags, source_owners_preserved=True, output_published=args.target.exists(), source_immutable=True, writer_prepare_calls=len(calls), writer_runtime_input_reads=0)
except Exception as error:
    result['error'] = {'type': type(error).__name__, 'message': str(error)}
result.update(private_inputs_read=0, native_launches=0, attestation_patch_applied=args.native_qualified == 'yes')
args.report.parent.mkdir(parents=True, exist_ok=True)
with args.report.open('x') as stream:
    json.dump(result, stream, indent=2, allow_nan=False)
print(json.dumps({key: result.get(key) for key in ('passed', 'route', 'error', 'output_sha256')}))
raise SystemExit(0 if result['passed'] else 3)
