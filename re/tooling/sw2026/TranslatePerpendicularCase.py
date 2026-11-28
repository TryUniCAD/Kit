import argparse
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path, PureWindowsPath
import sys


def require(value, message):
    if not value:
        raise ValueError(message)


def translate(case, native_root):
    from PerpendicularInputs import prediction_pair, request
    from PerpendicularSourcePlan import AXES, validate

    validate(case)
    require(not case['id'].startswith('H') or os.name == 'nt', 'sealed case translation is guest-only')
    require([index for index, _ in case['mate']['planes']] == [0, 1],
            'reverse source-selection order remains outside the frozen native-order translation profile')
    root = PureWindowsPath(native_root)
    require(root.is_absolute() and not any(part in ('.', '..') for part in root.parts), 'the generated case requires an explicit absolute Windows output owner')
    spec = {'id': case['id'], 'name': case['name'], 'child_name': case['child_name'],
            'size_m': list(case['child_size_m']), 'edit_depth_m': case['edit_depth_m'],
            'edit_rotation_deg': case['edit_rotation_deg'], 'fixed_occurrence': case['fixed_occurrence'],
            'placements': deepcopy(case['placements']),
            'endpoints': [{'occurrence': index, 'axis': 'xyz'[AXES[plane]]} for index, plane in case['mate']['planes']]}
    neutral = request(spec, root)
    folders = neutral['child']['settings']['system']['folders']
    require(sum(kind == 'moEnvFolder_c' for kind, _ in folders) == 1, 'the child default environment role is ambiguous')
    neutral['child']['settings']['system']['folders'] = [[kind, 'Lights and Cameras' if kind == 'moEnvFolder_c' else name]
                                                      for kind, name in folders]
    neutral['assembly']['configuration_name'] = case['configuration']
    return {'schema': 'kit.sw2026.perpendicular-neutral-translation.v1', 'spec': spec, 'case': case,
            'request': neutral, 'prediction': prediction_pair(spec), 'native_observations_used': False,
            'source_files_read': 0, 'native_processes_started': 0, 'public_writer_qualified': False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--model-tools', type=Path, required=True)
    parser.add_argument('--native-root', required=True)
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    tools = args.model_tools.resolve(strict=True)
    sys.path[:0] = [str(tools), str(root), str(root / 'src'), str(root / 're/tooling/sw2026')]
    incoming = sys.stdin.buffer.read()
    case = json.loads(incoming)
    result = translate(case, args.native_root)
    result['neutral_spec_sha256'] = sha256(incoming).hexdigest()
    print(json.dumps(result, separators=(',', ':'), allow_nan=False))


if __name__ == '__main__':
    main()
