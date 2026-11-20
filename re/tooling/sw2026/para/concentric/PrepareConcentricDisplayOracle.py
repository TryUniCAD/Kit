from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path, PureWindowsPath
import re
import subprocess


REPO = Path(__file__).resolve().parents[5]
HOME = Path('/Users/odin')
ORACLE_ROOT = HOME / 'Documents/UniCAD/Oracle121Takeover'
BASE = ORACLE_ROOT / 'RadialConcentric01'
SOURCE = ORACLE_ROOT / 'ConcentricMateSourcePacket02/Disclosed/D01/Native/Source'
REVISION = 'a93bb38bb3e51529c57872028f606588a5c54c61'
OLD_TRIAL = '5d7680db342c5c7e037313d0a2bc3e02820b1d21dfcbdad5cd77293430d32d01'
OLD_RESULT = '3263e7d2019953bede2c36948b84274d915b9cd8f4de1afc0bcb1988e0397f03'
ORACLE = '3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe'
SCHEMA = 'kit.sw2026.concentric-display-oracle.v1'
OBSERVER = 'ObserveConcentricDisplayOracle.py'
CONTROLS = {
    'parent': ('ConcentricD01AlignedFree.SLDASM', '2267cb6bc7e02d05be19ce5105ba3e43240eb4d1ad897647237dc875445d0dc2'),
    'child': ('ConcentricD01Child.SLDPRT', '92b83376b42ca55aa3b32a350635585c788ea0f968cc6e54f1730fdeb3c99caa'),
}
TOOLS = (
    'AssemblyMateEvidence.py', 'AuthorAssemblySources.py', 'AuthorCurves.py', 'ConcentricApiMetadata.py',
    'ConcentricMateEvidence.py', 'ConcentricNativeContract.py', 'ConcentricSourcePlan.py',
    'InspectCircleSketch.py', 'InspectFresh.py', 'InspectGeneratedConcentric.py', 'ObserveAssemblyLoad.py',
    'ObserveConcentricPersistence.py', 'OracleIdentity.py', 'Swapp.py',
)
STEPS = {
    'preflight': ['preflight'],
    'ControlBefore': ['control', 'before'],
    'Author': ['author'],
    'Observe': ['observe'],
    'ControlAfter': ['control', 'after'],
    'summary': ['summary'],
}


def checked(path, expected):
    if path.resolve() != path or not path.is_file():
        raise ValueError(f'missing or redirected disclosure: {path}')
    data = path.read_bytes()
    if sha256(data).hexdigest() != expected:
        raise ValueError(f'disclosure digest changed: {path}')
    return data


def guest(path):
    return str(PureWindowsPath(r'\\Mac\Home', *path.relative_to(HOME).parts))


def json_bytes(data):
    return (json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + '\n').encode('utf-8')


def publish(directory, relative, data):
    with (directory / relative).open('xb') as stream:
        stream.write(data)
    return sha256(data).hexdigest()


def prepare(name):
    if not re.fullmatch(r'ConcentricDisplayVisibility[0-9]{2}', name):
        raise ValueError('use an unused ConcentricDisplayVisibilityNN directory')
    output = ORACLE_ROOT / name
    if output.exists() or output.resolve() != output:
        raise ValueError('the oracle packet directory must be unused and unredirected')
    head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()
    subprocess.run(['git', 'merge-base', '--is-ancestor', REVISION, head], cwd=REPO, check=True)
    prior = json.loads(checked(BASE / 'Trial.json', OLD_TRIAL))
    receipt = json.loads(checked(BASE / 'Result.json', OLD_RESULT))
    if not (receipt['packet_sha256'] == OLD_TRIAL and receipt['passed'] and receipt['controls_healthy']
            and receipt['distinct_native_processes'] == 4 and prior['heldout_inputs_read'] == 0):
        raise ValueError('the earlier disclosed radial control receipt is required')
    controls = {}
    for side, (basename, expected) in CONTROLS.items():
        path = SOURCE / basename
        data = checked(path, expected)
        controls[side] = {'host_path': str(path), 'guest_path': guest(path), 'sha256': expected, 'bytes': len(data)}
    if prior['controls'] != controls:
        raise ValueError('the exact original D01 linked control is required')
    runtime_path = 'Evidence/GuestPython.json'
    runtime = checked(BASE / runtime_path, prior['files_sha256'][runtime_path])
    prediction_path = 'Evidence/Prediction.json'
    prediction = json.loads(checked(BASE / prediction_path, prior['files_sha256'][prediction_path]))['control']
    sources = {f'Tools/{filename}': checked(BASE / 'Tools' / filename, prior['files_sha256'][f'Tools/{filename}'])
               for filename in TOOLS}
    sources[f'Tools/{OBSERVER}'] = Path(__file__).with_name(OBSERVER).read_bytes()
    sources[runtime_path] = runtime
    sources[prediction_path] = json_bytes(prediction)
    output.mkdir(mode=0o700)
    for folder in ('Tools', 'Evidence', 'Working', 'Inspection'):
        (output / folder).mkdir()
    hashes = {relative: publish(output, relative, data) for relative, data in sorted(sources.items())}
    job = {
        'schema': SCHEMA, 'research_scope': 'disclosed D01, B04-SW2026-MATES-CONCENTRIC/parent-display-state',
        'aggregate_base': REVISION, 'preparation_head': head, 'preparer_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
        'baseline_trial_sha256': OLD_TRIAL, 'baseline_result_sha256': OLD_RESULT,
        'oracle_sha256': ORACLE, 'guest_root': guest(output), 'heldout_inputs_read': 0, 'native_processes_started': 0,
        'controls': controls, 'expected_original_ids': [24, 25], 'require_preference_18_true': True,
        'working_names': {side: basename for side, (basename, _) in CONTROLS.items()},
        'states': [
            {'name': 'Display State-1', 'visibility': [1, 1]},
            {'name': 'VisibilityFirstOnly', 'visibility': [1, 0]},
            {'name': 'VisibilitySecondOnly', 'visibility': [0, 1]},
        ],
        'files_sha256': hashes,
    }
    trial = publish(output, 'Trial.json', json_bytes(job))
    prefix = ['prlctl', 'exec', 'Windows 11', '--current-user', json.loads(runtime)['executable'],
              '-I', '-B', guest(output / 'Tools' / OBSERVER)]
    argv = {phase: [*prefix, *flags, guest(output / 'Trial.json'), trial] for phase, flags in STEPS.items()}
    recipe = publish(output, 'Recipe.json', json_bytes({
        'trial_sha256': trial, 'ordered_steps': list(STEPS), 'argv': argv,
        'stop_author_and_observe_after_failure': True,
        'trailing_control_after_any_native_failure_if_idle': True,
        'max_native_launches': 4, 'repeat_in_fresh_packet_only': True,
        'host_wait_limit_seconds': {'preflight': 30, 'ControlBefore': 150, 'Author': 240,
                                    'Observe': 180, 'ControlAfter': 150, 'summary': 30},
    }))
    return {'packet': str(output), 'trial_sha256': trial, 'recipe_sha256': recipe,
            'native_launches': 0, 'heldout_inputs_read': 0}


def main():
    parser = argparse.ArgumentParser(description='Freeze one private D01 display-state discovery packet without launching CAD')
    parser.add_argument('--name', default='ConcentricDisplayVisibility01')
    print(json.dumps(prepare(parser.parse_args().name), indent=2))


if __name__ == '__main__':
    main()
