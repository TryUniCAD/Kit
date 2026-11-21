import argparse
from hashlib import sha256
import json
from pathlib import Path, PureWindowsPath
from shutil import copyfile


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n', encoding='utf-8')
    return digest(path)


def copy_group(source, target, entries):
    target.mkdir()
    for name, expected in entries.items():
        path = source / name
        require(path.is_file() and not path.is_symlink() and digest(path) == expected,
                'a before-execution public method dependency changed')
        destination = target / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        copyfile(path, destination)
    return dict(entries)


def main():
    parser = argparse.ArgumentParser()
    for name in ('candidate', 'previous-method', 'native-packet', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--guest-root', required=True)
    args = parser.parse_args()
    base, previous, native = (value.resolve(strict=True) for value in (args.candidate, args.previous_method, args.native_packet))
    output = args.output.resolve()
    guest = PureWindowsPath(args.guest_root)
    require(not output.exists() and guest.is_absolute(), 'use an unused isolated method identity')
    manifest = base / 'Proof01/SourceManifest.json'
    require(digest(manifest) == '68f3acd0d0a65f25783dd31def611c63b8651163497bed9c8abb129f2bbf26c1'
            and digest(base / 'Proof01/RegistryProof.json') == 'dac307b3371f6102aa036684a60f9b6613c0e425bab2aa591a984aa14e360539'
            and digest(base / 'GuardProof01/GuardProof.json') == '82992e321fa9aba46c6b8414863c06500b0a8ba47a30a4077ac4a6416dca3c9b',
            'the complete public source/positive/negative proof differs')
    require(digest(previous / 'Method.json') == 'dc644609ac4e3fa11000b10948ee2171e0c7a859b446ebbeb04f8cfebc4ad44f',
            'the original guest-private source custody and comparator method differs')
    old = load(previous / 'Method.json')
    require(digest(native / 'Inspection/Result.json') == '2c694d52c50d65971dd569c51bd91a8313ee1f606e3536b63160bc939dd26272'
            and load(native / 'Inspection/Result.json')['passed']
            and digest(base / 'SavedReadback01/SavedReadback.json') == '838004669c96519e8c2e7a6480011550c91571f7630177ee985c24cabe0ac763',
            'the exact actual-registry native lifecycle and saved SDK readback are not qualified')
    output.mkdir()
    groups = {'CodeRoot': copy_group(base / 'CodeRoot01', output / 'CodeRoot', load(manifest)['candidate'])}
    for group in ('WriterTools', 'EvaluationTools', 'ReaderTools', 'GuestTools'):
        groups[group] = copy_group(previous / group, output / group, old['source_groups'][group])
    job = load(native / 'Job.json')
    groups['NativeTools'] = copy_group(native / 'Tools', output / 'NativeTools', job['tools_sha256'])
    registry = {path.name: digest(path) for path in sorted((base / 'Tools01').glob('*.py'))}
    registry.update({name: digest(native / 'Tools' / name) for name in
                     ('PredictPublicPerp.py', 'PreparePublicPerpNative.py', 'InspectPublicPerpNative.py')})
    (output / 'RegistryTools').mkdir()
    for name, expected in registry.items():
        path = base / 'Tools01' / name
        if not path.is_file():
            path = native / 'Tools' / name
        require(digest(path) == expected, 'the measured registry helper differs')
        copyfile(path, output / 'RegistryTools' / name)
    groups['RegistryTools'] = registry
    local = Path(__file__).parent
    copyfile(local / 'GuardPublicPerpBuild.py', output / 'RegistryTools/GuardPublicPerpBuild.py')
    groups['RegistryTools']['GuardPublicPerpBuild.py'] = digest(local / 'GuardPublicPerpBuild.py')
    for source_name, group, target_name in (
        ('TranslatePublicPerpCase.py', 'EvaluationTools', 'TranslatePerpendicularCase.py'),
        ('EvaluatePublicPerpSlot.py', 'GuestTools', 'EvaluatePublicPerpSlot.py'),
        ('VerifyPublicPerpFreeze.py', 'GuestTools', 'VerifyPublicPerpFreeze.py'),
        ('ComparePublicPerpRuntime.py', 'GuestTools', 'ComparePublicPerpRuntime.py'),
        ('CheckPublicPerpGuest.py', 'GuestTools', 'CheckPublicPerpGuest.py'),
    ):
        copyfile(local / source_name, output / group / target_name)
        groups[group][target_name] = digest(local / source_name)
    inputs = output / 'Inputs'
    inputs.mkdir()
    pairs = [(base / 'Fixtures01/G01.json', 'G01RegistryInput.json'),
             (base / 'Proof01/RegistryProof.json', 'RegistrySourceProof.json'),
             (base / 'GuardProof01/GuardProof.json', 'RegistryGuardProof.json'),
             (base / 'Proof01/SourceManifest.json', 'RegistrySourceManifest.json'),
             (base / 'SavedReadback01/SavedReadback.json', 'RegistrySavedReadback.json'),
             (native / 'Inspection/Result.json', 'G01NativeResult.json'),
             (native / 'Prediction.json', 'G01Prediction.json'),
             (native / 'ControlCase.json', 'ControlCase.json'), (native / 'ControlState.json', 'ControlState.json')]
    for name in ('PreWriterSourceLock.json', 'SourcePacket.json', 'SourceSeal.json'):
        pairs.append((previous / 'Inputs' / name, name))
    for source, name in pairs:
        copyfile(source, inputs / name)
    (inputs / 'HostGenerated').mkdir()
    for name, known in job['generated_files'].items():
        source = native / 'FrozenGenerated' / name
        require(digest(source) == known['sha256'], 'the measured disclosed host output changed')
        copyfile(source, inputs / 'HostGenerated' / name)
    method = {'schema': 'kit.sw2026.perpendicular-blind-method.v1',
              'task_id': 'B04-SW2026-MATES-PERPENDICULAR/public', 'owner': 'assembly_occurrence', 'delivery_pr': 121,
              'heldout_contents_read_at_freeze': False, 'compiler_entry': 'convert.write_document default registry',
              'public_default_recipe': True, 'source_groups': groups,
              'writer_source_manifest_sha256': digest(manifest),
              'inputs_sha256': {path.relative_to(output).as_posix(): digest(path) for path in sorted(inputs.rglob('*')) if path.is_file()},
              'source_packet_guest_path': old['source_packet_guest_path'],
              'source_packet_sha256': old['source_packet_sha256'], 'source_seal_record_sha256': old['source_seal_record_sha256'],
              'combined_neutral_spec_sha256': old['combined_neutral_spec_sha256'], 'slots': old['slots'],
              'control_files': old['control_files'], 'native_phases': old['native_phases'],
              'native_oracle_sha256': old['native_oracle_sha256'], 'native_generated_discovery_qualified': True,
              'admission': old['admission'], 'independent_expectations': old['independent_expectations'],
              'public_admission': 'one unknown-alignment perpendicular; two rigid direct occurrences; one fixed owner; owned centered dimensioned rectangle; no unprojected metadata or parameters',
              'native_observations_excluded_from_generation': True, 'request_prediction_lock_before_native_source_access': True,
              'runtime_byte_identity_basis': 'separately pinned disclosed guest identity after independent typed comparison, then two fresh exact registry replays',
              'previous_internal_method_sha256': digest(previous / 'Method.json'),
              'previous_internal_source_cases_reused': True, 'additional_unseen_design_credit': 0,
              'public_perpendicular_writer_qualified': False, 'active_invalid_angle_correction_qualified': False,
              'new_method_and_implementing_agent_heldout_payload_reads': 0,
              'native_execution_requires_root_review_and_release': True,
              'input_output_policy': 'neutral/source/observations stay on canonical guest fixed drive; host receives only opaque slot hashes statuses process identities'}
    method_sha = write(output / 'Method.json', method)
    entry = ['py', '-3.12', '-B']
    verifier = str(guest / 'GuestTools/VerifyPublicPerpFreeze.py')
    common = [str(guest / 'Method.json'), '--method-sha256', method_sha]
    private = r'C:\KitPublicPerpRegistry121'
    recipe = {'schema': 'kit.sw2026.public-perpendicular-method-recipe.v1', 'method_sha256': method_sha,
              'guest_root': str(guest), 'guest_private_root': private,
              'disclosed_discovery_before_any_release': entry + [verifier, 'discover', *common, '--output', str(guest / 'Runtime/GuestDiscovery01')],
              'host_typed_comparison_required': {'tool': str(guest / 'GuestTools/ComparePublicPerpRuntime.py'),
                   'method_sha256': method_sha, 'guest_discovery': str(guest / 'Runtime/GuestDiscovery01/Discovery.json')},
              'pin_reviewed_disclosed_identity': entry + [verifier, 'pin', *common, '--discovery', str(guest / 'Runtime/GuestDiscovery01/Discovery.json'),
                   '--comparison', str(guest / 'Runtime/Comparison01/Comparison.json'), '--output', str(guest / 'Runtime/Identity01.json')],
              'verify_before_any_hidden_access': entry + [verifier, 'verify-runtime', *common,
                   '--identity', str(guest / 'Runtime/Identity01.json'), '--identity-sha256', '<reviewed-disclosed-identity-sha256>',
                   '--output', str(guest / 'Runtime/GuestVerified01')],
              'release_templates': {slot: {'schema': 'kit.sw2026.perpendicular-neutral-slot-release.v1', 'method_sha256': method_sha,
                   'runtime_sha256': '<verified-runtime-sha256>', 'slot': slot, 'allow_combined_neutral_container_read': True} for slot in method['slots']},
              'slots': {}, 'always_run_trailing_control_independently': True, 'phase_timeout_seconds': 900,
              'no_automatic_process_termination': True, 'heldout_inputs_read_at_preparation': 0, 'native_processes_started': 0,
              'source_cases_are_reused_original_pre_writer_locks': True, 'additional_unseen_design_credit': 0}
    for slot in method['slots']:
        arguments = [*common, '--slot', slot, '--private-root', private]
        public = guest / 'Progress' / slot
        recipe['slots'][slot] = {
            'prepare_after_explicit_root_release': entry + [str(guest / 'GuestTools/PreparePerpendicularSlot.py'), *arguments,
                '--runtime-sha256', '<verified-runtime-sha256>', '--runtime-record', str(guest / 'Runtime/GuestVerified01/Runtime.json'),
                '--runtime-record-sha256', '<verified-runtime-record-sha256>', '--release', str(guest / 'Release' / (slot + '.json')),
                '--release-sha256', '<reviewed-slot-release-sha256>', '--public-output', str(public / 'Prepare/Record.json')],
            'build_before_source_native_access': entry + [str(guest / 'GuestTools/EvaluatePublicPerpSlot.py'), 'build', *arguments,
                '--public-output', str(public / 'Build/Record.json')],
            'native': {phase: entry + [str(guest / 'GuestTools/EvaluatePublicPerpSlot.py'), 'native', *arguments, '--phase', phase,
                '--public-output', str(public / phase / 'Record.json')] for phase in method['native_phases']},
            'finalize': entry + [str(guest / 'GuestTools/EvaluatePublicPerpSlot.py'), 'finalize', *arguments,
                '--public-output', str(public / 'Final/Record.json')]}
    recipe_sha = write(output / 'Recipe.json', recipe)
    print(json.dumps({'method_sha256': method_sha, 'recipe_sha256': recipe_sha,
                      'code_files': len(groups['CodeRoot']), 'tool_files': sum(len(value) for key, value in groups.items() if key != 'CodeRoot'),
                      'heldout_inputs_read': 0, 'native_processes_started': 0, 'public_writer_qualified': False}))


if __name__ == '__main__':
    main()
