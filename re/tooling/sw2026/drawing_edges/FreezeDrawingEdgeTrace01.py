from __future__ import annotations

import argparse
import ast
from hashlib import sha256
import json
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parent
BASE_TRIAL = '36143744fc79f19fb60434d24884288f72733e764ed9fd8a8138aff4233d0872'
BASE_FILES = 'c7b49f275a7cf4b843ef1522b4b759fa4fbd5342acc3055fd47b543f28da5cf2'
DEBUGGER = Path('/Users/odin/Documents/UniCAD/Sw2026Research01a1dc84/debugger')
DEBUGGER_GUEST = r'\\Mac\Home\Documents\UniCAD\Sw2026Research01a1dc84\debugger\DbgEng\content\amd64'
PACKAGE = '875678516f9ceed4a1c8b9b106d165106fcaa38723ad7c584c47b95b231600de'


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    with path.open('x') as output:
        output.write(json.dumps(value, sort_keys=True, indent=2) + '\n')


def verify_engine_metadata():
    report = json.loads((DEBUGGER / 'DbgEngPackage.json').read_bytes())
    require(report['sha256'] == PACKAGE, 'cached debugger package metadata differs')
    actual_package = DEBUGGER / 'Microsoft.Debugging.Platform.DbgEng.20260319.1511.0.nupkg'
    require(digest(actual_package) == PACKAGE, 'cached NuGet package differs')
    source = ast.parse((ROOT / 'TracePrototype01/ObserveDrawingEdgeCache01.py').read_text())
    assignment = next(node for node in source.body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'ENGINE_SHA256' for target in node.targets))
    expected = ast.literal_eval(assignment.value)
    directory = DEBUGGER / 'DbgEng/content/amd64'
    for name, expected_hash in expected.items():
        require(digest(directory / name) == expected_hash, 'cached AMD64 engine differs: ' + name)
    return expected


def prepare(baseline, baseline_sha, output):
    require(not output.exists(), 'use a new two-stop packet directory')
    require(digest(baseline) == baseline_sha, 'completed annotation baseline hash differs')
    prior = json.loads(baseline.read_bytes())
    require(prior.get('passed') is True and prior.get('packet_sha256') == BASE_TRIAL and prior.get('controls_healthy') is True
            and prior.get('distinct_processes') == 6 and len(prior.get('phases') or {}) == 6
            and all(row['passed'] for row in prior['phases'].values()), 'the exact six-process native API baseline must pass first')
    base = ROOT / 'NativePacket03'
    require(digest(base / 'Trial.json') == BASE_TRIAL and digest(base / 'Files.json') == BASE_FILES, 'frozen predecessor changed')
    files = json.loads((base / 'Files.json').read_bytes())
    for name, row in files.items():
        path = base / name
        require(path.is_file() and path.stat().st_size == row['bytes'] and digest(path) == row['sha256'], 'frozen predecessor file changed: ' + name)
    expected_engine = verify_engine_metadata()
    output.mkdir()
    for name in [*files, 'Files.json']:
        source, target = base / name, output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    shutil.copyfile(baseline, output / 'RequiredBaseline.json')
    tools = output / 'TraceTools'
    tools.mkdir()
    for source in sorted((ROOT / 'TracePrototype01').glob('*.py')):
        compile(ast.parse(source.read_text()), str(source), 'exec')
        shutil.copyfile(source, tools / source.name)
    job = {'schema': 'kit.sw2026.drawing-edge-cache-two-stop.v1', 'base_trial_sha256': BASE_TRIAL, 'base_files_sha256': BASE_FILES,
           'required_baseline_sha256': baseline_sha, 'heldout_inputs_read': 0, 'native_acceptance': False,
           'debugger_directory': DEBUGGER_GUEST, 'debugger_package_sha256': PACKAGE, 'debugger_files_sha256': expected_engine,
           'trace_tools_sha256': {p.name: digest(p) for p in sorted(tools.iterdir())},
           'sites': [{'module': 'slduiu.dll', 'rva': 0x13aaed7, 'sample': 'actual component nonnull, requested downstream ID u32, kernel edge nonnull'},
                     {'module': 'slduiu.dll', 'rva': 0x13aaedc, 'sample': 'same thread/stack; returned reference nonnull'}],
           'selected_annotation_edge_joined_to_sampled_id': False, 'generated_downstream_writer_qualified': False}
    write_json(output / 'TraceTrial.json', job)
    frozen = {p.relative_to(output).as_posix(): {'bytes': p.stat().st_size, 'sha256': digest(p)} for p in sorted(output.rglob('*')) if p.is_file()}
    write_json(output / 'TraceFiles.json', frozen)
    return output / 'TraceTrial.json'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--baseline-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    trial = prepare(args.baseline.resolve(strict=True), args.baseline_sha256, args.output.resolve())
    print(json.dumps({'trial': str(trial), 'sha256': digest(trial), 'cad_processes_started': 0, 'native_acceptance': False}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
