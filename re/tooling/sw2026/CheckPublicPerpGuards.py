import argparse
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from hashlib import sha256
import json
from math import sqrt
from pathlib import Path
import subprocess
import sys


def require(value, message):
    if not value:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    base = args.candidate.resolve(strict=True)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    source = json.loads((base / 'Fixtures01/G01.json').read_bytes())
    cases = {}
    def case(name):
        value = deepcopy(source)
        value.update(expected_reject=True, output=str(output / name))
        cases[name] = value
        return value['document']['assembly']
    value = case('NonOrthogonal')['instances']['$tuple'][1]['transform']['values']['$tuple']
    value[:3], value[4:7], value[8:11] = [1., 0., 0.], [0., 1., 0.], [0., 0., 1.]
    value = case('UniformScale')['instances']['$tuple'][1]['transform']['values']['$tuple']
    for index in (0, 1, 2, 4, 5, 6, 8, 9, 10):
        value[index] *= 2
    value = case('MovedPrincipal')['documents']['$tuple'][0]['document']['support_planes']['$tuple'][0]['transform']
    value['origin']['x'] = 0.5
    value = case('SlantedDatum')['documents']['$tuple'][0]['document']['support_planes']['$tuple'][0]['transform']
    value['x_axis'].update(x=sqrt(0.5), y=0., z=-sqrt(0.5))
    value['z_axis'].update(x=sqrt(0.5), y=0., z=sqrt(0.5))
    case('SameOccurrence')['mate_entities']['$tuple'][1]['instance_path']['$tuple'] = ['instance/0']
    case('SuppressedMate')['mates']['$tuple'][0]['suppressed'] = True
    case('FlexibleOccurrence')['instances']['$tuple'][1]['flexible'] = True
    case('SuppressedOccurrence')['instances']['$tuple'][1]['suppressed'] = True
    closure = json.loads((base / 'Proof01/SourceManifest.json').read_bytes())
    for name, expected in closure['candidate'].items():
        require(sha256((base / 'CodeRoot01' / name).read_bytes()).hexdigest() == expected, 'the frozen SDK source changed')
    tool = base / 'Tools01/RunPerpRegistry.py'
    tool_sha = sha256(tool.read_bytes()).hexdigest()
    def invoke(row):
        tag, value = row
        incoming = json.dumps(value, separators=(',', ':'), allow_nan=False).encode()
        process = subprocess.Popen([sys.executable, '-I', '-B', str(tool), str(base / 'CodeRoot01')],
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate(incoming, timeout=180)
        (output / (tag + '.stdin.json')).write_bytes(incoming)
        (output / (tag + '.stdout.json')).write_bytes(stdout)
        (output / (tag + '.stderr.txt')).write_bytes(stderr)
        require(process.returncode == 0, 'the actual guard process failed ' + tag + ': ' + stderr.decode()[-1200:])
        result = json.loads(stdout)
        require(result['passed'] and result['rejected'] and not result['admitted']
                and result['runtime_input_file_reads'] == result['native_processes_started'] == result['writer_output_count'] == 0,
                'an unsupported ordinary geometry reached construction or publication')
        return {'case': tag, 'pid': process.pid, 'request_sha256': sha256(incoming).hexdigest(),
                'stdout_sha256': sha256(stdout).hexdigest(), 'result': result}
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(invoke, cases.items()))
    require(len({value['pid'] for value in results}) == len(results), 'a guard process identity was repeated')
    for name, expected in closure['candidate'].items():
        require(sha256((base / 'CodeRoot01' / name).read_bytes()).hexdigest() == expected, 'source changed during the guard proof')
    result = {'schema': 'kit.sw2026.public-perpendicular-geometry-guards.v1', 'passed': True,
              'process_count': len(results), 'cases': results, 'worker_sha256': tool_sha,
              'source_manifest_sha256': sha256((base / 'Proof01/SourceManifest.json').read_bytes()).hexdigest(),
              'runtime_input_file_reads': 0, 'native_processes_started': 0, 'heldout_inputs_read': 0,
              'writer_output_count': 0, 'public_writer_qualified': False}
    data = (json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()
    (output / 'GuardProof.json').write_bytes(data)
    print(json.dumps({'passed': True, 'process_count': len(results), 'receipt_sha256': sha256(data).hexdigest()}))


if __name__ == '__main__':
    main()
