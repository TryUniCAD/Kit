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


def write(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    return digest(path)


def main():
    parser = argparse.ArgumentParser()
    for name in ('candidate', 'native-packet', 'reader-method', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--native-result-sha256', required=True)
    args = parser.parse_args()
    base, packet, reader = (value.resolve(strict=True) for value in (args.candidate, args.native_packet, args.reader_method))
    manifest = base / 'Proof01/SourceManifest.json'
    require(digest(manifest) == '68f3acd0d0a65f25783dd31def611c63b8651163497bed9c8abb129f2bbf26c1',
            'the exact public-registry candidate source closure differs')
    for name, wanted in load(manifest)['candidate'].items():
        require(digest(base / 'CodeRoot01' / name) == wanted, 'a candidate dependency changed')
    require(digest(packet / 'Job.json') == 'a719214c4e12170239a22a07598039d62c15ab176583871ce639f745eaddc42b'
            and digest(packet / 'Inspection/Result.json') == args.native_result_sha256,
            'the exact controlled public-registry native trial differs')
    result = load(packet / 'Inspection/Result.json')
    require(result['passed'] and result['controls_healthy'] and result['distinct_native_process_count'] == 4
            and result['numeric_checks'] == 190 and result['actual_registry_output_measured'],
            'the independent public-registry lifecycle is not complete')
    records = {}
    for name, wanted in result['phase_receipts'].items():
        path = packet / 'Inspection' / name / 'Record.json'
        require(digest(path) == wanted and load(path)['passed'], 'a qualified native phase changed')
        records[name] = load(path)
    method = load(reader / 'Method.json')
    require(digest(reader / 'Method.json') == 'dc644609ac4e3fa11000b10948ee2171e0c7a859b446ebbeb04f8cfebc4ad44f',
            'the unchanged solved-source audit method differs')
    for name, wanted in method['source_groups']['ReaderTools'].items():
        require(digest(reader / 'ReaderTools' / name) == wanted, 'a frozen public-reader auditor changed')
    job = load(packet / 'Job.json')
    parent, child = (packet / 'Saved' / job['generated_names'][role] for role in ('parent', 'child'))
    saved = records['generated']['result']['saved_files']
    require(digest(parent) == saved['parent']['sha256'] and digest(child) == saved['child']['sha256'],
            'a native-saved artifact changed')
    sys.path[:0] = [str(base / 'CodeRoot01/src'), str(base / 'CodeRoot01')]
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    stream = SldprtArchive.from_bytes(parent.read_bytes()).require('Contents/Config-0-MatesList')
    request = {'path': str(parent), 'sha256': digest(parent), 'bytes': parent.stat().st_size,
               'stream_sha256': sha256(stream).hexdigest(), 'child_path': str(child), 'child_sha256': digest(child),
               'expected': records['reopen']['result']['rebuilt']}
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    write(output / 'Request.json', request)
    process = subprocess.run([sys.executable, '-I', '-B', str(reader / 'ReaderTools/AuditPerpendicularReader.py'),
                              '--root', str(base / 'CodeRoot01')], input=json.dumps(request, allow_nan=False).encode(),
                             capture_output=True, timeout=180)
    (output / 'Audit.stdout.json').write_bytes(process.stdout)
    (output / 'Audit.stderr.txt').write_bytes(process.stderr)
    require(process.returncode == 0, 'the actual saved pair failed strict normal SDK readback: ' + process.stderr.decode()[-1500:])
    actual = json.loads(process.stdout)
    require(actual['passed'] and actual['public']['status'] == 'admitted' and actual['public']['child_driver_count'] == 3,
            'the public saved read did not preserve the complete ordinary mate and child graph')
    require(digest(parent) == saved['parent']['sha256'] and digest(child) == saved['child']['sha256']
            and digest(packet / 'Inspection/Result.json') == args.native_result_sha256,
            'the immutable native artifacts changed during SDK audit')
    receipt = {'schema': 'kit.sw2026.actual-registry-perpendicular-saved-sdk-read.v1', 'passed': True,
               'native_result_sha256': args.native_result_sha256, 'source_manifest_sha256': digest(manifest),
               'reader_method_sha256': digest(reader / 'Method.json'), 'audit_stdout_sha256': sha256(process.stdout).hexdigest(),
               'parent_sha256': digest(parent), 'child_sha256': digest(child), 'stream_sha256': sha256(stream).hexdigest(),
               'public': actual['public'], 'typed_owners': actual['typed_owners'], 'codec': actual['codec'],
               'inputs_unchanged': True, 'writer_output_count': 0, 'heldout_inputs_read': 0,
               'native_processes_started': 0, 'public_writer_qualified': False}
    fingerprint = write(output / 'SavedReadback.json', receipt)
    print(json.dumps({'passed': True, 'receipt_sha256': fingerprint, 'public_status': 'admitted',
                      'child_driver_count': 3, 'native_processes_started': 0, 'heldout_inputs_read': 0}))


if __name__ == '__main__':
    main()
