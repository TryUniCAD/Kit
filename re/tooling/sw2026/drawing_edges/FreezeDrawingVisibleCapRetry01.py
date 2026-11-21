from pathlib import Path
from hashlib import sha256
import argparse
import ast
import json
import shutil


PREVIOUS_TRIAL = '3224ebc2de12538b843206675b3dbad38791300b02dc2e995bc155c0c79d737c'
PREVIOUS_FILES = 'f85ce0e89b1244915f56d5fe4a9d7d502ddc89ce1c21f3ea5a3d5087556df080'
PREVIOUS_RESULT = '839bcbd4a5dfd89cfae2879ba9e2932d3b7dc71b2a02e7f2d8303bf46905a9fb'
COMPONENT_METADATA = 'bd66c956040c0547d1f0b7f5bd35e80681e9910542ccf0e9a61dcd79d34daa24'


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def freeze(source_root, output):
    base = source_root / 'NativePacket05'
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
    for name in ['InspectDrawingEdgeQualification01.py']:
        source = Path(__file__).with_name(name)
        compile(ast.parse(source.read_text()), str(source), 'exec')
        shutil.copyfile(source, output / 'Tools' / name)
    shutil.copyfile(metadata, output / 'ComponentApiMetadata.json')
    trial = json.loads((base / 'Trial.json').read_bytes())
    trial.update(observer_revision='visible-front-cap-04', previous_trial_sha256=PREVIOUS_TRIAL,
                 previous_failed_result_sha256=PREVIOUS_RESULT, component_api_metadata_sha256=COMPONENT_METADATA,
                 original_trial_sha256='36143744fc79f19fb60434d24884288f72733e764ed9fd8a8138aff4233d0872',
                 original_failed_result_sha256='1056bde8473497d695c89276812fab2db2a66136c9c7351e8ddac40af47c6eb0')
    trial['visible_edge_selection_rule'] = 'positive-view-normal-outer-cap-left-rail-v1'
    for case in trial['cases']:
        view = case['expected']['view']
        lower, upper = case['prism_m']['minimum'], case['prism_m']['maximum']
        require(view['orientation'] == '*Front' and view['model_to_view'][:9] == [1,0,0,0,1,0,0,0,1]
                and view['scale'] == 1 and lower[2] == 0 and upper[2] > 0, 'derive only the canonical Front positive-depth visible cap')
        case['edge_endpoints_m'] = [[lower[0], lower[1], upper[2]], [lower[0], upper[1], upper[2]]]
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
