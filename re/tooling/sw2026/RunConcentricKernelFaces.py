from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')


def source_inputs(args):
    result = {'mate-graph': digest(args.mate_graph), 'source-manifest': digest(args.source_manifest),
              'analytic-manifest': digest(args.analytic_manifest)}
    for case in ('D01', 'D02', 'D03'):
        folder = args.packet / 'Disclosed' / case
        result[case + ':lock'] = digest(folder / 'lock.json')
        for phase in ('Source', 'Edited'):
            result[case + ':' + phase] = digest(folder / 'Native' / phase / ('Concentric' + case + 'Child.SLDPRT'))
    return result


def run(args):
    require(not args.output.exists(), 'choose an unused kernel process directory')
    inputs = source_inputs(args)
    require(inputs['mate-graph'] == '5a28338afa61c3b71daa0059970321e8134b3ace275ebc6f3f36dac0fef8ce4b', 'disclosed parent graph identity changed')
    require(inputs['source-manifest'] == 'c225fc9a4575b3b8d65a68f3db4182877009018b6796f3d8ed6546e519bc54bf', 'frozen SDK closure changed')
    require(inputs['analytic-manifest'] == '64e185c02e680a277e1ced16cae0fc8691b0f0d76e512db9bccd50199ec1d8ba', 'shared analytic grammar provenance changed')
    source = json.loads(args.source_manifest.read_bytes())
    sdk = {str(path.relative_to(args.root)): digest(path) for path in sorted((args.root / 'src').rglob('*.py'))}
    require(sdk == source['source_files'], 'actual SDK differs from the exact frozen kernel closure')
    tools = Path(__file__).resolve().parent
    auditor = tools / 'AuditConcentricKernelFaces.py'
    frozen = {path.name: digest(path) for path in (Path(__file__).resolve(), auditor)}
    args.output.mkdir(parents=True)
    write(args.output / 'SourceBefore.json', {'sdk': sdk, 'tools': frozen, 'inputs': inputs})
    base = [sys.executable, '-I', '-B', str(auditor), '--root', str(args.root), '--packet', str(args.packet),
            '--mate-graph', str(args.mate_graph), '--mate-graph-sha256', inputs['mate-graph']]
    records = []

    def call(name, options, expected, message=None):
        path = args.output / (name + '.json')
        result = subprocess.run([*base, *options, '--output', str(path)], capture_output=True, text=True, timeout=120)
        stdout = args.output / (name + '.stdout.json')
        stderr = args.output / (name + '.stderr.txt')
        stdout.write_text(result.stdout)
        stderr.write_text(result.stderr)
        require(result.returncode == expected and not result.stderr, name + ' process boundary failed')
        value = json.loads(result.stdout)
        require(value['passed'] is (expected == 0), name + ' admission verdict differs')
        if message:
            require(value.get('error') == message and not path.exists(), name + ' failed for a different reason')
        records.append({'name': name, 'exit_code': result.returncode, 'stdout_sha256': digest(stdout), 'result': value})

    for repeat in (1, 2):
        call('Owners' + str(repeat), [], 0)
    require((args.output / 'Owners1.json').read_bytes() == (args.output / 'Owners2.json').read_bytes(), 'fresh kernel owner audits differ')
    negatives = {'transmit-index': 'snapshot face id differs from actual kernel face node id',
                 'cap-face': 'snapshot face id differs from actual kernel face node id',
                 'marker': 'active surface reference differs from actual cylinder id',
                 'atom': 'snapshot body id differs from actual body atom',
                 'local-axis': 'optional vector differs from actual child-local cylinder axis'}
    for mutation, message in negatives.items():
        call('Reject' + mutation.title().replace('-', ''), ['--mutation', mutation], 3, message)
    after = {str(path.relative_to(args.root)): digest(path) for path in sorted((args.root / 'src').rglob('*.py'))}
    require(sdk == after and inputs == source_inputs(args), 'frozen SDK or disclosed inputs changed')
    require(frozen == {path.name: digest(path) for path in (Path(__file__).resolve(), auditor)}, 'kernel proof tools changed')
    result = {'schema': 'kit.sw2026.concentric-kernel-process.v1', 'passed': True, 'records': records,
              'host_processes': len(records), 'positive_owner_processes': 2, 'negative_owner_processes': 5,
              'disclosed_child_files': 6, 'correlated_endpoints_per_positive': 12, 'active_nodes_per_positive': 564,
              'source_unchanged': True, 'source_before_sha256': digest(args.output / 'SourceBefore.json'),
              'owner_audit_sha256': digest(args.output / 'Owners1.json'),
              'source_manifest_sha256': inputs['source-manifest'], 'analytic_manifest_sha256': inputs['analytic-manifest'],
              'native_processes_started': 0, 'hidden_inputs_read': 0, 'writer_outputs': 0,
              'kernel_face_node_identity_generated': False, 'optional_axis_constructor_qualified': False}
    write(args.output / 'Results.json', result)
    return {'passed': True, 'sha256': digest(args.output / 'Results.json'), 'host_processes': len(records)}


def main():
    parser = argparse.ArgumentParser()
    for name in ('root', 'packet', 'mate-graph', 'source-manifest', 'analytic-manifest', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    print(json.dumps(run(parser.parse_args()), sort_keys=True))


if __name__ == '__main__':
    main()
