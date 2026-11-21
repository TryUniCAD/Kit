import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys

from VerifyPerpendicularFreeze import canonical, digest, load, require, runtime, verify


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n', encoding='utf-8')
    return digest(path)


def worker(root, directory, label):
    request = load(root / 'Inputs/G01RegistryInput.json')
    request.update(output=str(directory / label), allow_unqualified=True)
    result = subprocess.Popen([sys.executable, '-I', '-B', str(root / 'RegistryTools/GuardPublicPerpBuild.py'), str(root / 'CodeRoot')],
                              stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = result.communicate(canonical(request), timeout=180)
    (directory / (label + '.stdout.json')).write_bytes(stdout)
    (directory / (label + '.stderr.txt')).write_bytes(stderr)
    require(result.returncode == 0, 'the disclosed public-registry runtime build failed before hidden access')
    value = json.loads(stdout)
    require(value['passed'] and value['round_trips'] == 22 and value['runtime_input_file_reads'] == value['native_processes_started'] == 0
            and value['sdk_runtime_research_imports'] == value['cad_runtime_modules'] == 0
            and value['vendor_loadable'] is False and value['application_usable'] is False,
            'the disclosed replay crossed the frozen public source-only boundary')
    return value, result.pid, sha256(stdout).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=('discover', 'pin', 'verify-runtime'))
    parser.add_argument('method', type=Path)
    parser.add_argument('--method-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--discovery', type=Path)
    parser.add_argument('--comparison', type=Path)
    parser.add_argument('--identity', type=Path)
    parser.add_argument('--identity-sha256')
    args = parser.parse_args()
    root, method = verify(args.method.resolve(strict=True), args.method_sha256)
    require(method['compiler_entry'] == 'convert.write_document default registry' and method['public_default_recipe'] is True,
            'use the separately frozen actual-public-recipe method')
    output = args.output.resolve()
    if args.command == 'pin':
        require(args.discovery is not None and args.comparison is not None and not output.exists(),
                'pin a reviewed disclosed comparison into a new identity file')
        discovery, comparison = load(args.discovery), load(args.comparison)
        require(discovery['passed'] and discovery['method_sha256'] == args.method_sha256
                and discovery['heldout_inputs_read'] == comparison['heldout_inputs_read'] == 0
                and comparison['all_nonfloating_typed_fields_and_aliases_equal']
                and comparison['all_other_logical_streams_equal'] and comparison['differences_within_predeclared_runtime_scope']
                and comparison['guest_discovery_sha256'] == digest(args.discovery),
                'the disclosed guest identity has not been independently explained')
        value = {'schema': 'kit.sw2026.public-perpendicular-disclosed-runtime-identity.v1',
                 'method_sha256': args.method_sha256, 'discovery_sha256': digest(args.discovery),
                 'comparison_sha256': digest(args.comparison), 'files': discovery['files'],
                 'runtime_sha256': discovery['runtime_sha256'], 'heldout_inputs_read': 0,
                 'writer_math_changed': False, 'byte_patch_added': False}
        fingerprint = write(output, value)
        print(json.dumps({'passed': True, 'identity_sha256': fingerprint, 'heldout_inputs_read': 0, 'native_processes_started': 0}))
        return
    require(not output.exists(), 'preserve all earlier runtime attempts')
    output.mkdir(parents=True)
    profile = runtime()
    profile_sha = sha256(canonical(profile)).hexdigest()
    if args.command == 'discover':
        value, pid, stdout_sha = worker(root, output, 'A')
        receipt = {'schema': 'kit.sw2026.public-perpendicular-disclosed-runtime-discovery.v1', 'passed': True,
                   'method_sha256': args.method_sha256, 'files': {role: {key: data[key] for key in ('bytes', 'sha256')}
                   for role, data in value['artifacts'].items()}, 'runtime_profile': profile, 'runtime_sha256': profile_sha,
                   'worker_pid': pid, 'worker_stdout_sha256': stdout_sha, 'heldout_inputs_read': 0,
                   'native_processes_started': 0, 'permits_hidden_release': False}
        fingerprint = write(output / 'Discovery.json', receipt)
        print(json.dumps({'passed': True, 'discovery_sha256': fingerprint, 'runtime_sha256': profile_sha,
                          'permits_hidden_release': False, 'heldout_inputs_read': 0, 'native_processes_started': 0}))
        return
    require(args.identity is not None and args.identity_sha256 is not None
            and digest(args.identity) == args.identity_sha256, 'the separately reviewed disclosed identity is not pinned')
    identity = load(args.identity)
    require(identity['schema'] == 'kit.sw2026.public-perpendicular-disclosed-runtime-identity.v1'
            and identity['method_sha256'] == args.method_sha256 and identity['runtime_sha256'] == profile_sha
            and identity['heldout_inputs_read'] == 0 and not identity['writer_math_changed'] and not identity['byte_patch_added'],
            'the committed disclosed runtime identity differs')
    runs = []
    for label in ('A', 'B'):
        value, pid, stdout_sha = worker(root, output, label)
        for role, known in identity['files'].items():
            require(value['artifacts'][role]['sha256'] == known['sha256'] and value['artifacts'][role]['bytes'] == known['bytes'],
                    'the actual guest did not reproduce its separately committed complete public files')
        runs.append({'worker_pid': pid, 'round_trips': value['round_trips'], 'stdout_sha256': stdout_sha})
    require(runs[0]['worker_pid'] != runs[1]['worker_pid'], 'the actual runtime replay reused a process')
    guest_probe = None
    if os.name == 'nt':
        from CheckPublicPerpGuest import check

        guest_probe = check(root, args.method_sha256, output.name)
    verify(args.method.resolve(strict=True), args.method_sha256)
    receipt = {'schema': 'kit.sw2026.perpendicular-method-runtime-preflight.v1', 'passed': True,
               'method_sha256': args.method_sha256, 'runtime_profile': profile, 'runtime_sha256': profile_sha,
               'disclosed_identity_sha256': args.identity_sha256, 'disclosed_replay': runs,
               'exact_frozen_complete_files_reproduced': True, 'heldout_inputs_read': 0, 'native_processes_started': 0,
               'actual_normal_registry': True, 'existing_public_defaults_preserved': True,
               'disclosed_guest_primary_build_probe': guest_probe,
               'actual_guest_primary_destination_proven': guest_probe is not None}
    fingerprint = write(output / 'Runtime.json', receipt)
    print(json.dumps({'passed': True, 'runtime_record_sha256': fingerprint, 'runtime_sha256': profile_sha,
                      'heldout_inputs_read': 0, 'native_processes_started': 0}))


if __name__ == '__main__':
    main()
