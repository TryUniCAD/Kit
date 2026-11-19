from pathlib import Path
from hashlib import sha256
import argparse
import ast
import json
import shutil


PREVIOUS_TRIAL = '90f6ddf5543712f32a6d93ffe997872d9be1c76e480497715fd1db1ea3334a40'
PREVIOUS_FILES = '4a5d15e116079a948033926015316e2673c4f03dc3d7d2b0d284610b464621e8'
PREVIOUS_RESULT = 'ec4fb7e13afe41bb7906c28973f699be380f67fac17c7d6b59dabbaab6caadb3'
COMPONENT_METADATA = 'bd66c956040c0547d1f0b7f5bd35e80681e9910542ccf0e9a61dcd79d34daa24'


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def freeze(source_root, output):
    base = source_root / 'NativePacket04'
    require(not output.exists(), 'use an unused root-owner retry directory')
    require(digest(base / 'Trial.json') == PREVIOUS_TRIAL and digest(base / 'Files.json') == PREVIOUS_FILES, 'frozen predecessor changed')
    result_path = base / 'Inspection/Result.json'
    require(digest(result_path) == PREVIOUS_RESULT, 'original failed native result changed')
    prior = json.loads(result_path.read_bytes())
    require(prior['passed'] is False and prior['distinct_processes'] == 2 and prior['inputs_unchanged']
            and prior['encoded_slots_unchanged'] and not any(name.startswith('Generated') for name in prior['phases']),
            'retry must preserve the exact observer-only failure and skipped generated states')
    metadata = source_root / 'CaptureDrawingComponentConfigApi02.Root.stdout'
    require(digest(metadata) == COMPONENT_METADATA, 'new exact 2026 component API metadata changed')
    files = json.loads((base / 'Files.json').read_bytes())
    for name, row in files.items():
        path = base / name
        require(path.stat().st_size == row['bytes'] and digest(path) == row['sha256'], 'original frozen input/tool changed: ' + name)
    output.mkdir()
    for name in files:
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(base / name, target)
    for name in ['DrawingEdgeState01.py', 'InspectDrawingEdgeQualification01.py']:
        source = Path(__file__).with_name(name)
        compile(ast.parse(source.read_text()), str(source), 'exec')
        shutil.copyfile(source, output / 'Tools' / name)
    shutil.copyfile(metadata, output / 'ComponentApiMetadata.json')
    trial = json.loads((base / 'Trial.json').read_bytes())
    trial.update(observer_revision='drawing-projection-owner-03', previous_trial_sha256=PREVIOUS_TRIAL,
                 previous_failed_result_sha256=PREVIOUS_RESULT, component_api_metadata_sha256=COMPONENT_METADATA,
                 original_trial_sha256='36143744fc79f19fb60434d24884288f72733e764ed9fd8a8138aff4233d0872',
                 original_failed_result_sha256='1056bde8473497d695c89276812fab2db2a66136c9c7351e8ddac40af47c6eb0')
    trial['tools_sha256'] = {p.name: digest(p) for p in sorted((output / 'Tools').glob('*.py'))}
    (output / 'Trial.json').write_text(json.dumps(trial, sort_keys=True, indent=2) + '\n')
    rows = {p.relative_to(output).as_posix(): {'bytes': p.stat().st_size, 'sha256': digest(p)} for p in sorted(output.rglob('*')) if p.is_file()}
    (output / 'Files.json').write_text(json.dumps(rows, sort_keys=True, indent=2) + '\n')
    return output / 'Trial.json'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path)
    parser.add_argument('--source-root', type=Path, required=True)
    args = parser.parse_args()
    trial = freeze(args.source_root.resolve(strict=True), args.output.resolve())
    print(json.dumps({'trial': str(trial), 'sha256': digest(trial), 'native_processes_started': 0, 'heldout_inputs_read': 0}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
