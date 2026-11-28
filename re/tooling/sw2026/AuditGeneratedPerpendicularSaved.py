import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def verify_source(base, reader):
    source = base / 'Proof01/SourceManifest.json'
    require(digest(source) == '0f660dcb6fef84b12b382fa40e542069d49dab0ec6169151b154b4222f5884fa', 'the generated source closure differs')
    for name, wanted in load(source)['current'].items():
        require(digest(base / 'CodeRoot01' / name) == wanted, 'a source dependency changed after generation')
    freeze = reader / 'ReaderCodeFreeze01.json'
    require(digest(freeze) == '47aa5d22d3a158653f8b3e8bff35c28a9e2dcd8b44286713028504e8217bfa1d', 'the original solved-state reader rule freeze differs')
    for name, wanted in load(freeze)['tools'].items():
        require(digest(reader / 'Tools01' / name) == wanted, 'a frozen solved-source audit tool changed')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--writer', type=Path, required=True)
    parser.add_argument('--reader', type=Path, required=True)
    parser.add_argument('--native-packet', type=Path, required=True)
    parser.add_argument('--native-result-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    base, reader, packet = (path.resolve(strict=True) for path in (args.writer, args.reader, args.native_packet))
    verify_source(base, reader)
    raw = packet / 'Inspection/Result.json'
    require(digest(raw) == args.native_result_sha256, 'the independent native result changed')
    result = load(raw)
    require(result['passed'] and result['controls_healthy'] and result['distinct_native_process_count'] == 4
            and result['heldout_inputs_read'] == 0, 'the generated native lifecycle is not qualified')
    records = {}
    for phase, wanted in result['phase_receipts'].items():
        path = packet / 'Inspection' / phase / 'Record.json'
        require(digest(path) == wanted and load(path)['passed'], 'a qualified native phase changed')
        records[phase] = load(path)
    saved = records['generated']['result']['saved_files']
    job = load(packet / 'Job.json')
    parent, child = (packet / 'Saved' / job['generated_names'][role] for role in ('parent', 'child'))
    require(digest(parent) == saved['parent']['sha256'] and digest(child) == saved['child']['sha256'], 'a saved native derivative changed')
    sys.path.insert(0, str(base / 'CodeRoot01/src'))
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    stream = SldprtArchive.from_bytes(parent.read_bytes()).require('Contents/Config-0-MatesList')
    request = {'path': str(parent), 'sha256': digest(parent), 'bytes': parent.stat().st_size,
               'stream_sha256': sha256(stream).hexdigest(), 'child_path': str(child), 'child_sha256': digest(child),
               'expected': records['reopen']['result']['rebuilt']}
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    request_data = json.dumps(request, allow_nan=False).encode()
    (output / 'AuditRequest.json').write_bytes(request_data)
    process = subprocess.run([sys.executable, '-I', '-B', str(reader / 'Tools01/AuditPerpendicularReader.py'),
                              '--root', str(base / 'CodeRoot01')], input=request_data, capture_output=True, timeout=120)
    (output / 'Audit.stdout.json').write_bytes(process.stdout)
    (output / 'Audit.stderr.txt').write_bytes(process.stderr)
    require(process.returncode == 0, 'the unchanged normal saved-source reader rejected: ' + process.stderr.decode()[-1600:])
    actual = json.loads(process.stdout)
    require(actual['passed'] and actual['public']['status'] == 'admitted' and actual['public']['child_driver_count'] == 3,
            'the native-saved generated pair lost its complete ordinary public read')
    verify_source(base, reader)
    require(digest(parent) == saved['parent']['sha256'] and digest(child) == saved['child']['sha256']
            and digest(raw) == args.native_result_sha256, 'native evidence changed during the independent SDK audit')
    receipt = {'schema': 'kit.sw2026.generated-perpendicular-native-saved-sdk-audit.v1', 'passed': True,
               'native_result_sha256': args.native_result_sha256, 'writer_source_manifest_sha256': digest(base / 'Proof01/SourceManifest.json'),
               'solved_reader_freeze_sha256': digest(reader / 'ReaderCodeFreeze01.json'),
               'parent_sha256': digest(parent), 'child_sha256': digest(child), 'stream_sha256': sha256(stream).hexdigest(),
               'audit_stdout_sha256': sha256(process.stdout).hexdigest(), 'public': actual['public'], 'typed_owners': actual['typed_owners'],
               'codec': actual['codec'], 'native_inputs_unchanged': True, 'heldout_inputs_read': 0, 'native_processes_started': 0,
               'writer_output_count': 0, 'public_perpendicular_writer_qualified': False}
    data = (json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()
    (output / 'SavedReadback.json').write_bytes(data)
    print(json.dumps({'passed': True, 'result_sha256': sha256(data).hexdigest(), 'public_status': actual['public']['status'],
                      'child_drivers': actual['public']['child_driver_count'], 'native_processes_started': 0, 'heldout_inputs_read': 0}, sort_keys=True))


if __name__ == '__main__':
    main()
