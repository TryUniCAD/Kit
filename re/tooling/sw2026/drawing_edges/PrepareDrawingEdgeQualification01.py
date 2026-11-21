from __future__ import annotations

import argparse
import ast
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import sys


W = Path('/Users/odin/.codex/worktrees/solidworks-121-takeover/Kit')
B = Path('/Users/odin/Documents/UniCAD/Oracle121Takeover')
SOURCE = B / 'SdkLinkedNative01'
LOCAL = Path(__file__).resolve().parent
ORACLE = '3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe'
PINS = {'Fixture.json': '39670020e79d93747b8018dd5e7ac4becf60bd91a6331016834cd1d22fa314b3',
        'Control.json': 'bef2c3389dfcf9c3790590d5afa5800a7b720479b66c1a4432cfd64af6412292',
        'NeutralRequest.json': 'b25d66ef0b1176687481eef7db746df7c08ff3f24760ddf420124660fad7cca6'}
TOOLS = ('AuthorCurves.py', 'AuthorDrawingSources.py', 'DrawingCacheCases.py', 'InspectDrawingCache.py', 'OracleIdentity.py', 'Swapp.py')


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n')


def require(value, message):
    if not value:
        raise ValueError(message)


def frozen_json(name):
    path = SOURCE / name
    require(digest(path) == PINS[name], 'disclosed source metadata differs: ' + name)
    return json.loads(path.read_bytes())


def annotation(bounds, expected):
    lower, upper = bounds
    x = expected['view']['model_to_view'][9] + lower[0]
    y = expected['view']['model_to_view'][10] + (lower[1] + upper[1]) / 2
    return {'before_text': 'edge a', 'after_text': 'edge b', 'before_position_m': [x + 0.002, y, 0],
            'after_position_m': [x + 0.004, y + 0.001, 0]}


def prepare(output):
    require(not output.exists(), 'use an unused packet directory')
    fixture, control, neutral = (frozen_json(name) for name in PINS)
    output.mkdir()
    tools = output / 'Tools'
    tools.mkdir()
    for name in TOOLS:
        shutil.copyfile(W / 're/tooling/sw2026' / name, tools / name)
    for name in ('DrawingEdgeState01.py', 'InspectDrawingEdgeQualification01.py'):
        shutil.copyfile(LOCAL / name, tools / name)
    metadata = LOCAL / 'CaptureDrawingEdgeApi01.Root.stdout'
    require(digest(metadata) == '92235db40b63b95246f2479a9166ecaa12c242d3f96d149e13827d1e92b756f5', 'registered wrapper metadata differs')
    shutil.copyfile(metadata, output / 'ApiMetadata.json')
    control_bounds = [[0, 0, 0], [0.02, 0.01, 0.007]]
    document = neutral['part']['document']
    entities = document['sketches']['$tuple'][0]['entities']['$tuple']
    require(len(entities) == 4 and all(entity['geometry']['$type'] == 'LineGeometry' and not entity['construction'] for entity in entities), 'disclosed child is not the ordinary four-line contour')
    points = [entity['geometry'][side] for entity in entities for side in ('start', 'end')]
    dimensions = [[float(point[axis]) / 1000 for point in points] for axis in ('x', 'y')]
    depth = float(document['feature_timeline']['$tuple'][0]['definition']['length']['value']) / 1000
    generated_bounds = [[min(dimensions[0]), min(dimensions[1]), 0], [max(dimensions[0]), max(dimensions[1]), depth]]
    cases = []
    first = {'role': 'Control', 'expected': control['expected'], 'prism_m': {'minimum': control_bounds[0], 'maximum': control_bounds[1]},
             'provenance_sha256': PINS['Control.json'], 'approved_child_paths': [control['expected']['view']['resolved_reference_path']],
             'child_parameters_m': {}, 'child_tree': None, 'drawing_tree': None, 'drawing_target': None}
    for label in ('drawing', 'part'):
        info = control[label]
        source = SOURCE / 'Control' / info['filename']
        require(digest(source) == info['sha256'], 'native pristine source differs')
        target = output / 'Inputs' / 'Control' / info['filename']
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        first.update({label + '_source': target.relative_to(output).as_posix(), label + '_sha256': digest(target), label + '_bytes': target.stat().st_size})
    cases.append(first)
    child_tree = [list(row) for row in fixture['child_history_sequence']]
    cabinet = child_tree.pop(next(index for index, row in enumerate(child_tree) if row[1] == 'DetailCabinet'))
    binder = next(index for index, row in enumerate(child_tree) if row[1] == 'DocsFolder')
    child_tree.insert(binder + 1, cabinet)
    child_tree[-1][1] = 'Extrusion'
    second = {'role': 'Generated', 'expected': fixture['expected_before'],
              'prism_m': {'minimum': generated_bounds[0], 'maximum': generated_bounds[1]},
              'provenance_sha256': PINS['NeutralRequest.json'], 'approved_child_paths': [fixture['expected_before']['view']['resolved_reference_path']],
              'child_parameters_m': fixture['child_parameters'], 'child_tree': child_tree, 'drawing_tree': fixture['drawing_tree']}
    for name, info in fixture['files'].items():
        label = 'drawing' if name.endswith('.SLDDRW') else 'part'
        source = SOURCE / 'Generated' / name
        require(digest(source) == info['sha256'] and source.stat().st_size == info['bytes'], 'previous SDK generated source differs')
        target = output / 'Inputs' / 'Generated' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        second.update({label + '_source': target.relative_to(output).as_posix(), label + '_sha256': digest(target),
                       label + '_bytes': target.stat().st_size, label + '_target': info['encoded_windows_path']})
    cases.append(second)
    for case, bounds in zip(cases, (control_bounds, generated_bounds), strict=True):
        case['edge_endpoints_m'] = [[bounds[0][0], bounds[0][1], 0], [bounds[0][0], bounds[1][1], 0]]
        case['annotation'] = annotation(bounds, case['expected'])
    job = {'schema': 'kit.sw2026.drawing-edge-qualification.v1', 'oracle_sha256': ORACLE, 'heldout_inputs_read': 0,
           'source_scope': 'disclosed-only', 'native_acceptance': False, 'cases': cases,
           'source_metadata_sha256': PINS, 'tools_sha256': {p.name: digest(p) for p in sorted(tools.iterdir())},
           'api_metadata_sha256': digest(output / 'ApiMetadata.json'), 'cache_consumer_measured': False,
           'scope': 'COM edge-associated note creation, text/position edit, SaveModelData=true, save and fresh reopen; no cache-consumer or original-source qualification'}
    write_json(output / 'Trial.json', job)
    manifest = {p.relative_to(output).as_posix(): {'bytes': p.stat().st_size, 'sha256': digest(p)} for p in sorted(output.rglob('*')) if p.is_file()}
    write_json(output / 'Files.json', manifest)
    return output / 'Trial.json'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    trial = prepare(args.output.resolve())
    print(json.dumps({'trial': str(trial), 'sha256': digest(trial), 'processes_started': 0, 'native_acceptance': False}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
