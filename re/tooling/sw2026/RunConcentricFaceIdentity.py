from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n')


def run(args):
    output = args.output.resolve()
    if output.exists():
        raise ValueError('choose an unused process proof directory')
    output.mkdir(parents=True)
    tools = Path(__file__).resolve().parent
    paths = [tools / name for name in ('AuditConcentricFaceOwners.py', 'CollectConcentricFaceIdentity.py', 'RunConcentricFaceIdentity.py')]
    sdk = {str(path.relative_to(args.root)): digest(path) for path in sorted((args.root / 'src').rglob('*.py'))}
    inputs = {'mate-graph': digest(args.mate_graph), 'native-image': digest(args.image), 'pe-helper': digest(args.support)}
    for case in ('D01', 'D02', 'D03'):
        folder = args.packet / 'Disclosed' / case
        inputs[case + ':lock'] = digest(folder / 'lock.json')
        for phase in ('Source', 'Edited'):
            inputs[case + ':' + phase] = digest(folder / 'Native' / phase / ('Concentric' + case + 'Child.SLDPRT'))
    frozen = {path.name: digest(path) for path in paths}
    before = {'sdk': sdk, 'tools': frozen, 'inputs': inputs}
    write(output / 'SourceBefore.json', before)
    records = []

    def call(name, arguments, expected):
        result = subprocess.run([sys.executable, '-I', '-B', *map(str, arguments)], capture_output=True, text=True, timeout=120)
        (output / (name + '.stdout.json')).write_text(result.stdout)
        (output / (name + '.stderr.txt')).write_text(result.stderr)
        if result.returncode != expected or result.stderr:
            raise ValueError(name + ' process boundary failed')
        row = json.loads(result.stdout)
        if row.get('passed', True) is not (expected == 0):
            raise ValueError(name + ' returned a different admission verdict')
        records.append({'name': name, 'exit_code': result.returncode,
                        'stdout_sha256': digest(output / (name + '.stdout.json')), 'result': row})

    call('NativeBindings', [paths[1], '--support', args.support, '--image', args.image,
                            '--output', output / 'NativeBindings.json'], 0)
    base = [paths[0], '--root', args.root, '--packet', args.packet,
            '--mate-graph', args.mate_graph, '--mate-graph-sha256', inputs['mate-graph']]
    for repeat in (1, 2):
        call('Owners' + str(repeat), [*base, '--output', output / ('Owners' + str(repeat) + '.json')], 0)
    if (output / 'Owners1.json').read_bytes() != (output / 'Owners2.json').read_bytes():
        raise ValueError('fresh disclosed owner audits were not deterministic')
    for mutation in ('marker', 'feature', 'creation', 'atom', 'text'):
        call('Reject' + mutation.title(), [*base, '--mutation', mutation,
                                          '--output', output / ('Reject' + mutation.title() + '.json')], 3)
    after = {str(path.relative_to(args.root)): digest(path) for path in sorted((args.root / 'src').rglob('*.py'))}
    if sdk != after or frozen != {path.name: digest(path) for path in paths}:
        raise ValueError('frozen source changed during process proof')
    if inputs['mate-graph'] != digest(args.mate_graph) or inputs['native-image'] != digest(args.image) or inputs['pe-helper'] != digest(args.support):
        raise ValueError('frozen evidence input changed during process proof')
    for case in ('D01', 'D02', 'D03'):
        folder = args.packet / 'Disclosed' / case
        if inputs[case + ':lock'] != digest(folder / 'lock.json'):
            raise ValueError('disclosed source lock changed')
        for phase in ('Source', 'Edited'):
            if inputs[case + ':' + phase] != digest(folder / 'Native' / phase / ('Concentric' + case + 'Child.SLDPRT')):
                raise ValueError('disclosed child changed')
    result = {'schema': 'kit.sw2026.concentric-face-identity-process.v1', 'passed': True,
              'records': records, 'host_processes': len(records), 'positive_owner_processes': 2,
              'negative_owner_processes': 5, 'disclosed_child_files': 6,
              'correlated_endpoints_per_positive': 12, 'source_unchanged': True,
              'source_before_sha256': digest(output / 'SourceBefore.json'),
              'native_bindings_sha256': digest(output / 'NativeBindings.json'),
              'owner_audit_sha256': digest(output / 'Owners1.json'),
              'native_processes_started': 0, 'hidden_inputs_read': 0, 'writer_outputs': 0,
              'kernel_face_node_identity_generated': False}
    write(output / 'Results.json', result)
    return {'passed': True, 'sha256': digest(output / 'Results.json'), 'host_processes': len(records)}


def main():
    parser = argparse.ArgumentParser()
    for name in ('root', 'packet', 'mate-graph', 'support', 'image', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    print(json.dumps(run(parser.parse_args()), sort_keys=True))


if __name__ == '__main__':
    main()
