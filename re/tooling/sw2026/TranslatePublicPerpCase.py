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


def translate(case, root, native_root):
    from interchange.serialization.EncodeData import ToData
    from PerpendicularInputs import request, prediction_pair
    from PerpendicularNativePlan import case_from_spec, check_predictions, native_trees
    from PerpendicularSourcePlan import AXES, validate
    from PreparePublicPerpNative import tree_intent
    from ProbePerpendicularPublic import portable
    from PredictPublicPerp import intent, predict

    validate(case)
    require(not case['id'].startswith('H') or os.name == 'nt', 'sealed public translation is guest-only')
    require([index for index, _ in case['mate']['planes']] == [0, 1],
            'reverse native selection normalization remains outside the frozen public translation')
    target = PureWindowsPath(native_root)
    require(target.is_absolute() and not any(value in ('.', '..') for value in target.parts),
            'the public registry needs its explicit canonical native final owner')
    spec = {'id': case['id'], 'name': case['name'], 'child_name': case['child_name'],
            'size_m': list(case['child_size_m']), 'edit_depth_m': case['edit_depth_m'],
            'edit_rotation_deg': case['edit_rotation_deg'], 'fixed_occurrence': case['fixed_occurrence'],
            'placements': deepcopy(case['placements']),
            'endpoints': [{'occurrence': index, 'axis': 'xyz'[AXES[plane]]} for index, plane in case['mate']['planes']]}
    semantic = request(spec, target)
    document = portable(semantic, prediction_pair(spec))
    fixture = {'document': ToData(document), 'native_parent': str(target / (case['name'] + '.SLDASM')),
               'saved_at': 1794700075, 'expected_reject': False}
    edit = {key: case[key] for key in ('edit_depth_m', 'edit_rotation_deg')}
    model = intent(fixture, edit)
    for index, value in enumerate(spec['placements']):
        value['translation_m'] = model['matrices'][index][9:12]
    spec['size_m'] = [model[key] for key in ('width_m', 'height_m', 'depth_m')]
    predicted = predict(fixture, edit)
    check_predictions(case_from_spec(spec), predicted)
    roles = tree_intent(root, fixture)
    envelope = dict(roles, registry_input=fixture)
    return {'schema': 'kit.sw2026.public-perpendicular-neutral-translation.v1',
            'case': case, 'spec': spec, 'request': envelope, 'prediction': predicted, 'trees': native_trees(envelope),
            'native_observations_used': False, 'source_files_read': 0, 'native_processes_started': 0,
            'existing_public_defaults_preserved': True, 'public_writer_qualified': False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--model-tools', type=Path, required=True)
    parser.add_argument('--native-root', required=True)
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    sys.path[:0] = [str(Path(__file__).parent), str(args.model_tools.resolve(strict=True)),
                    str(root / 'src'), str(root), str(root / 're/tooling/sw2026'),
                    str(Path(__file__).parent.parent / 'RegistryTools'), str(Path(__file__).parent.parent / 'NativeTools')]
    data = sys.stdin.buffer.read()
    result = translate(json.loads(data), root, args.native_root)
    result['neutral_spec_sha256'] = sha256(data).hexdigest()
    print(json.dumps(result, separators=(',', ':'), allow_nan=False))


if __name__ == '__main__':
    main()
