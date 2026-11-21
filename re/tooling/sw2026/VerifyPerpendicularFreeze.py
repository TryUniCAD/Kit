from hashlib import sha256
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import unicodedata
import zlib


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def runtime():
    return {'python_version': sys.version, 'python_implementation': platform.python_implementation(),
            'python_executable_sha256': digest(Path(sys.executable)), 'os_name': os.name, 'machine': platform.machine(),
            'byteorder': sys.byteorder, 'unicode_version': unicodedata.unidata_version,
            'zlib_compile_version': zlib.ZLIB_VERSION, 'zlib_runtime_version': zlib.ZLIB_RUNTIME_VERSION,
            'distributions': sorted((str(item.metadata['Name']).casefold(), item.version) for item in importlib.metadata.distributions())}


def verify(method, expected):
    root = method.parent.resolve(strict=True)
    require(digest(method) == expected, 'the complete perpendicular method identity differs')
    value = load(method)
    require(value['schema'] == 'kit.sw2026.perpendicular-blind-method.v1' and value['heldout_contents_read_at_freeze'] is False,
            'use the closed pre-exposure method')
    for group, entries in value['source_groups'].items():
        folder = root / group
        for name, wanted in entries.items():
            path = folder / name
            require(not path.is_symlink() and path.is_file() and digest(path) == wanted, 'a frozen executable source changed')
        if group == 'CodeRoot':
            actual = {path.relative_to(folder).as_posix() for area in ('src', 'tests', 're/tooling/sw2026')
                      for path in (folder / area).rglob('*.py')}
            require(actual == set(entries), 'the complete code closure has extra or missing source')
        else:
            require({path.name for path in folder.glob('*.py')} == set(entries), 'a frozen tool closure has extra or missing source')
    for name, wanted in value['inputs_sha256'].items():
        path = root / name
        require(not Path(name).is_absolute() and '..' not in Path(name).parts and not path.is_symlink()
                and digest(path) == wanted, 'a frozen public method input changed')
    return root, value


def replay(root, directory):
    require(not directory.exists(), 'use an unused runtime preflight directory')
    directory.mkdir(parents=True)
    incoming = (root / 'Inputs/G01Request.json').read_bytes()
    known = load(root / 'Inputs/G01ExpectedFiles.json')
    outputs = []
    for label in ('A', 'B'):
        code = root / 'CodeRoot'
        result = subprocess.run([sys.executable, '-I', '-B', str(code / 're/tooling/sw2026/SdkPlanarGroupProcess.py'), str(code)],
                                input=incoming, capture_output=True, timeout=180)
        (directory / (label + '.stdout.json')).write_bytes(result.stdout)
        (directory / (label + '.stderr.txt')).write_bytes(result.stderr)
        require(result.returncode == 0, 'the disclosed runtime replay failed before any hidden access')
        value = json.loads(result.stdout)
        require(value['passed'] and value['runtime_input_file_reads'] == value['sdk_runtime_research_imports'] == 0,
                'the runtime replay crossed the source-only boundary')
        for role in ('assembly', 'child'):
            require(value[role]['sha256'] == known[role]['sha256'] and value[role]['bytes'] == known[role]['bytes'],
                    'the actual runtime did not reproduce the frozen complete disclosed files')
        outputs.append({'worker_pid': value['worker_pid'], 'round_trips': value['round_trips'],
                        'stdout_sha256': sha256(result.stdout).hexdigest()})
    require(outputs[0]['worker_pid'] != outputs[1]['worker_pid'], 'runtime replay reused a process identity')
    return outputs


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('method', type=Path)
    parser.add_argument('--method-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root, method = verify(args.method.resolve(strict=True), args.method_sha256)
    outputs = replay(root, args.output.resolve())
    verify(args.method.resolve(strict=True), args.method_sha256)
    profile = runtime()
    result = {'schema': 'kit.sw2026.perpendicular-method-runtime-preflight.v1', 'passed': True,
              'method_sha256': args.method_sha256, 'runtime_profile': profile,
              'runtime_sha256': sha256(canonical(profile)).hexdigest(), 'disclosed_replay': outputs,
              'exact_frozen_complete_files_reproduced': True, 'heldout_inputs_read': 0, 'native_processes_started': 0}
    target = args.output / 'Runtime.json'
    target.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n', encoding='utf-8')
    print(json.dumps({'passed': True, 'method_sha256': args.method_sha256, 'runtime_sha256': result['runtime_sha256'],
                      'runtime_record_sha256': digest(target), 'heldout_inputs_read': 0, 'native_processes_started': 0}, sort_keys=True))


if __name__ == '__main__':
    main()
