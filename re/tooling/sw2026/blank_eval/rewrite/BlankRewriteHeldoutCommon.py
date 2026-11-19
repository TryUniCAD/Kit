from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from hashlib import sha256
import importlib
import io
import json
import os
from pathlib import Path
import re
import sys

SLOTS = ('Slot01', 'Slot02')
BASES = ('ControlBefore', 'Slot01/Source', 'Slot01/Rewrite', 'Slot02/Source', 'Slot02/Rewrite', 'ControlAfter')
STAGES = ('OpenEditSave', 'FreshReopen')


def require(value, label):
    if not value:
        raise ValueError(label)


def fingerprint(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def descriptor(path):
    return {'path': str(path), 'sha256': fingerprint(path)}


def load(row):
    path = Path(row['path'])
    require(path.is_absolute() and fingerprint(path) == row['sha256'], 'file identity differs')
    return json.loads(path.read_bytes())


def write_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, indent=2, allow_nan=False) + '\n')
    return descriptor(path)


def guest_path(value):
    require(os.name == 'nt', 'guest locality required')
    path = Path(value)
    require(path.is_absolute() and path.drive.upper() == 'C:' and '..' not in path.parts, 'guest local path required')
    resolved = path.resolve()
    require(resolved.drive.upper() == 'C:', 'guest local resolved path required')
    return resolved


def packet():
    root = Path(__file__).resolve().parents[1]
    method = json.loads((root / 'Method.json').read_bytes())
    require(method['schema'] == 'kit.sw2026.blank-preserved-rewrite-heldout-method.v1', 'method schema differs')
    require(fingerprint(root / 'Tools.json') == method['tools_sha256'], 'method tools differ')
    tools = json.loads((root / 'Tools.json').read_bytes())
    for name, digest in tools['tools_sha256'].items():
        require(Path(name).name == name and fingerprint(root / 'Tools' / name) == digest, 'tool identity differs')
    require(fingerprint(root / 'WriterManifest.json') == method['writer_manifest_sha256'], 'writer manifest differs')
    require(fingerprint(root / 'PriorPublicReceipt.json') == method['prior_public_receipt_sha256'], 'prior receipt differs')
    receipt = json.loads((root / 'PriorPublicReceipt.json').read_bytes())
    require(receipt['gates']['comparison_sha256'] == method['prior_comparison_sha256'], 'prior comparison differs')
    return root, method


def verify_source(root, method):
    manifest = json.loads((root / 'WriterManifest.json').read_bytes())
    for row in manifest['files']:
        require(fingerprint(root / 'Sdk' / row['path']) == row['sha256'], 'sdk source identity differs')
    sys.path.insert(0, str(root / 'Sdk' / 'src'))
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        for name in ('convert.api', 'convert.adapters.solidworks.Core.DrawingWriting.Rewrite.ReadBlankInput', 'convert.adapters.solidworks.Drawing.Reading.ReadGeneratedBlank'):
            importlib.import_module(name)
    return len(manifest['files'])


def custody(old_job_row, root, method):
    require(os.name == 'nt', 'custody evaluation is guest only')
    guest_path(old_job_row['path'])
    import RunBlankDrawingComparison01 as legacy
    job = load(old_job_row)
    require(job['binding']['sha256'] == method['prior_binding_sha256'], 'prior binding identity differs')
    require(job['generation']['sha256'] == method['prior_generation_sha256'], 'prior generation identity differs')
    require(job['tools']['sha256'] == method['prior_tools_sha256'], 'prior tools identity differs')
    guest_path(job['binding']['path'])
    generation = load({'path': str(guest_path(job['generation']['path'])), 'sha256': method['prior_generation_sha256']})
    require(list(generation['slots']) == list(SLOTS), 'prior slot order differs')
    for slot in SLOTS:
        row = generation['slots'][slot]
        guest_path(row['prediction']['path'])
        for build in row['builds']:
            guest_path(build['output']['path'])
            require(build['output']['sha256'] == method['prior_output_sha256'][slot], 'preexisting canonical output differs')
    code, job, bound, locked = legacy.verify_job(Path(old_job_row['path']), old_job_row['sha256'])
    predictions, outputs = legacy.generation_gate(code, job, bound, locked, False)
    comparison = load({'path': str(guest_path(job['output_root']) / 'Comparison.json'), 'sha256': method['prior_comparison_sha256']})
    require(comparison['sheet_lifecycle_passed'] is True and comparison['distinct_native_processes'] == 12 and comparison['compared_sheet_states'] == 30 and comparison['ordered_tree_rows'] == 120, 'prior native comparison failed')
    require(comparison['generation_sha256'] == method['prior_generation_sha256'] and comparison['method_binding_sha256'] == method['prior_binding_sha256'], 'prior native custody differs')
    return legacy, code, job, bound, locked, predictions, outputs


def binding(value, expected):
    require(os.name == 'nt', 'binding access is guest only')
    path = guest_path(value)
    data = load({'path': str(path), 'sha256': expected})
    root, method = packet()
    require(data['schema'] == 'kit.sw2026.blank-preserved-rewrite-heldout-binding.v1' and data['method_sha256'] == fingerprint(root / 'Method.json'), 'current binding differs')
    require(data['writer_manifest_sha256'] == method['writer_manifest_sha256'] and data['tools_sha256'] == method['tools_sha256'], 'current writer or observer changed')
    require(Path(sys.executable).resolve() == Path(data['python']).resolve(), 'guest interpreter changed')
    if 'predecessor' in method:
        require(data.get('predecessor') == method['predecessor'] and data.get('new_sdk_builds') == 0 and data.get('reuses_exact_first_run_candidates') is True, 'retry must retain the original generated inputs')
    output = guest_path(data['output_root'])
    require(path == output / 'Binding.json', 'binding owner differs')
    require(not output.is_relative_to(Path('C:/KitBlankDrawingSource121')), 'source storage must remain immutable')
    return root, method, data, output


def export_report(report, raw_sha256):
    result = {
        'schema': 'kit.sw2026.blank-preserved-rewrite-heldout-export.v2',
        'passed': report['passed'],
        'raw_result_sha256': raw_sha256,
        'method_sha256': report['method_sha256'],
        'writer_manifest_sha256': report['writer_manifest_sha256'],
        'binding_sha256': report['binding_sha256'],
        'original_native_source_credit': False,
        'canonical_sdk_rewrite_heldout_only': True,
        'private_payloads_or_paths_exported': False,
        'native_flags_changed': False,
        'sdk_builds_reused': report.get('sdk_builds_reused', False),
        'new_sdk_builds': report.get('new_sdk_builds', 4),
        'predecessor_private_result_sha256': report.get('predecessor_private_result_sha256', '0' * 64),
        'native_processes': report.get('native_processes', 0),
        'controls_passed': report.get('controls_passed', [False, False]),
        'sheet_states': report.get('sheet_states', 0),
        'ordered_tree_rows': report.get('ordered_tree_rows', 0),
        'paired_builds_identical': report.get('paired_builds_identical', False),
        'inputs_immutable': report.get('inputs_immutable', False),
        'sdk_runtime_input_reads': report.get('sdk_runtime_input_reads', -1),
    }
    for key, value in result.items():
        require(type(key) is str, 'export key invalid')
        if type(value) is str:
            require(value == result['schema'] or re.fullmatch('[0-9a-f]{64}', value), 'export text is not allowlisted')
        elif type(value) is list:
            require(len(value) == 2 and all(type(item) is bool for item in value), 'export list invalid')
        else:
            require(type(value) in (int, bool), 'export value invalid')
    return result
