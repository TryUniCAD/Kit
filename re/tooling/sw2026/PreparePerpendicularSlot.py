import argparse
from contextlib import redirect_stderr, redirect_stdout
import ctypes
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parent))

from VerifyPerpendicularFreeze import canonical, digest, load, require, runtime, verify


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n', encoding='utf-8')
    return digest(path)


def fixed_root(path):
    require(os.name == 'nt' and path.is_absolute() and path == path.resolve(), 'sealed preparation requires the canonical guest fixed drive')
    drive = ctypes.windll.kernel32.GetDriveTypeW
    drive.argtypes = (ctypes.c_wchar_p,)
    drive.restype = ctypes.c_uint
    require(drive(path.anchor) == 3, 'sealed neutral data cannot be written to a shared or network drive')
    return path


def prepare(root, method, args, directory):
    require(os.name == 'nt', 'sealed extraction and translation execute only in the root-owned guest')
    require(digest(args.release) == args.release_sha256, 'the explicit slot release identity differs')
    release = load(args.release)
    require(release == {'schema': 'kit.sw2026.perpendicular-neutral-slot-release.v1', 'method_sha256': args.method_sha256,
                        'runtime_sha256': args.runtime_sha256, 'slot': args.slot, 'allow_combined_neutral_container_read': True},
            'the root has not released this exact neutral slot and method')
    profile = runtime()
    require(sha256(canonical(profile)).hexdigest() == args.runtime_sha256, 'the preflight-frozen actual runtime changed')
    require(digest(args.runtime_record) == args.runtime_record_sha256, 'the runtime preflight record identity differs')
    preflight = load(args.runtime_record)
    require(preflight['passed'] and preflight['method_sha256'] == args.method_sha256 and
            preflight['runtime_sha256'] == args.runtime_sha256 and preflight['heldout_inputs_read'] == 0 and
            preflight['exact_frozen_complete_files_reproduced'], 'the actual runtime was not qualified before hidden access')
    slot = method['slots'][args.slot]
    packet = Path(method['source_packet_guest_path'])
    source_path = packet / 'Source.json'
    require(digest(source_path) == method['source_packet_sha256'], 'the source packet identity differs')
    source = load(source_path)
    for name, wanted in source['tools_sha256'].items():
        require(digest(packet / 'Tools' / name) == wanted, 'a pinned original source custody helper changed')
    source_lock = packet / 'Progress' / slot['case_id'] / 'lock/Record.json'
    require(digest(source_lock) == slot['source_lock_sha256'] and load(source_lock)['heldout_source_locked']
            and load(source_lock)['source_locked'] and load(source_lock)['passed'], 'the requested pre-writer source slot is not locked')
    seal = packet / 'Progress/D00/seal/Record.json'
    require(digest(seal) == method['source_seal_record_sha256'] and load(seal)['sealed_spec_sha256'] == method['combined_neutral_spec_sha256'],
            'the pre-writer neutral source seal differs')
    combined = fixed_root(Path(source['guest_private_base'])) / method['source_packet_sha256'] / 'D00/SealedSpecs.json'
    fixed_root(combined)
    require(not combined.is_symlink() and digest(combined) == method['combined_neutral_spec_sha256'], 'the combined pre-writer neutral specification changed')
    pack = load(combined)
    require(pack['schema'] == 'kit.sw2026.perpendicular-mate-source-cases.v1' and len(pack['cases']) == 2,
            'the sealed neutral source container shape differs')
    selected = [row for row in pack['cases'] if row['id'] == slot['case_id']]
    require(len(selected) == 1, 'the released neutral source slot is ambiguous')
    neutral = selected[0]
    spec_data = canonical(neutral)
    (directory / 'NeutralCase.json').write_bytes(spec_data)
    output_identity = str(directory / 'GeneratedInput')
    command = [sys.executable, '-I', '-B', str(root / 'EvaluationTools/TranslatePerpendicularCase.py'),
               '--root', str(root / 'CodeRoot'), '--model-tools', str(root / 'WriterTools'), '--native-root', output_identity]
    process = subprocess.run(command, input=spec_data, capture_output=True, timeout=120)
    (directory / 'Translation.stdout.json').write_bytes(process.stdout)
    (directory / 'Translation.stderr.txt').write_bytes(process.stderr)
    require(process.returncode == 0, 'the immutable translator rejected the released slot')
    translated = json.loads(process.stdout)
    require(translated['neutral_spec_sha256'] == sha256(spec_data).hexdigest() and translated['native_observations_used'] is False
            and translated['source_files_read'] == 0 and translated['native_processes_started'] == 0,
            'the neutral translator crossed its input boundary')
    request = json.dumps(translated['request'], separators=(',', ':'), allow_nan=False).encode()
    prediction = canonical(translated['prediction'])
    (directory / 'NeutralRequest.json').write_bytes(request)
    (directory / 'Prediction.json').write_bytes(prediction)
    sys.path.insert(0, str(root / 'NativeTools'))
    from PerpendicularNativePlan import native_trees
    trees_sha = write(directory / 'Trees.json', native_trees(translated['request']))
    lock = {'schema': 'kit.sw2026.perpendicular-precomparison-preparation-lock.v1', 'method_sha256': args.method_sha256,
            'slot': args.slot, 'combined_neutral_spec_sha256': method['combined_neutral_spec_sha256'],
            'selected_neutral_sha256': sha256(spec_data).hexdigest(), 'request_sha256': sha256(request).hexdigest(),
            'prediction_sha256': sha256(prediction).hexdigest(), 'trees_sha256': trees_sha, 'runtime_sha256': args.runtime_sha256,
            'release_sha256': args.release_sha256, 'native_source_files_opened': 0, 'native_source_observations_opened': 0,
            'native_processes_started': 0, 'writer_output_count': 0, 'prepared_at': time.time()}
    lock_sha = write(directory / 'PreparationLock.json', lock)
    verify(root / 'Method.json', args.method_sha256)
    return {'passed': True, 'slot': args.slot, 'method_sha256': args.method_sha256, 'runtime_sha256': args.runtime_sha256,
            'selected_neutral_sha256': lock['selected_neutral_sha256'], 'request_sha256': lock['request_sha256'],
            'prediction_sha256': lock['prediction_sha256'], 'preparation_lock_sha256': lock_sha,
            'native_source_files_opened': 0, 'native_source_observations_opened': 0, 'native_processes_started': 0,
            'writer_output_count': 0, 'native_acceptance': False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('method', type=Path)
    for option in ('method-sha256', 'runtime-sha256', 'runtime-record-sha256', 'release-sha256'):
        parser.add_argument('--' + option, required=True)
    for option in ('runtime-record', 'release', 'private-root', 'public-output'):
        parser.add_argument('--' + option, type=Path, required=True)
    parser.add_argument('--slot', choices=('Slot01', 'Slot02'), required=True)
    args = parser.parse_args()
    require(os.name == 'nt', 'sealed extraction executes only on the guest and exposes no neutral values to the host')
    root, method = verify(args.method.resolve(strict=True), args.method_sha256)
    private = fixed_root(args.private_root)
    directory = private / args.method_sha256 / args.slot / 'Prepared'
    fixed_root(directory)
    directory.mkdir(parents=True, exist_ok=False)
    args.public_output.parent.mkdir(parents=True, exist_ok=True)
    require(not args.public_output.exists(), 'the opaque public progress receipt must be new')
    write(args.public_output, {'passed': False, 'slot': args.slot, 'stage': 'checking_frozen_inputs',
                               'method_sha256': args.method_sha256, 'native_processes_started': 0})
    try:
        with (directory / 'Preparation.stdout.txt').open('x', encoding='utf-8') as stdout:
            with (directory / 'Preparation.stderr.txt').open('x', encoding='utf-8') as stderr:
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    result = prepare(root, method, args, directory)
    except Exception:
        failure = directory / 'Failure.txt'
        failure.write_text(traceback.format_exc(), encoding='utf-8')
        write(args.public_output, {'passed': False, 'slot': args.slot, 'stage': 'failed', 'private_failure_sha256': digest(failure),
                                  'method_sha256': args.method_sha256, 'native_processes_started': 0, 'native_acceptance': False})
        print(json.dumps({'passed': False, 'slot': args.slot, 'stage': 'failed', 'private_failure_sha256': digest(failure)}))
        raise SystemExit(3)
    write(args.public_output, result)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
