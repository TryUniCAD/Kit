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


def copy_group(source, output, entries):
    output.mkdir()
    for name, wanted in entries.items():
        path = source / name
        require(path.is_file() and not path.is_symlink() and digest(path) == wanted, 'a declared method source dependency changed')
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        copyfile(path, target)
    return dict(entries)


def main():
    parser = argparse.ArgumentParser()
    for name in ('writer', 'reader', 'native-packet', 'source-packet', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--guest-root', required=True)
    parser.add_argument('--runtime-worker', type=Path)
    parser.add_argument('--runtime-worker-sha256')
    parser.add_argument('--runtime-classification', type=Path)
    parser.add_argument('--runtime-classification-sha256')
    args = parser.parse_args()
    writer, reader, native, source = (value.resolve(strict=True) for value in (args.writer, args.reader, args.native_packet, args.source_packet))
    output = args.output.resolve()
    guest = PureWindowsPath(args.guest_root)
    require(guest.is_absolute() and not output.exists(), 'use a new method packet with an explicit absolute guest identity')
    manifest = writer / 'Proof01/SourceManifest.json'
    require(digest(manifest) == '0f660dcb6fef84b12b382fa40e542069d49dab0ec6169151b154b4222f5884fa', 'the writer source freeze changed')
    require(digest(writer / 'BlindMethodFreeze01.json') == '1bd6567368e31f010932078cc3ff486f91efe752ccd96ce57d485ac89c861821', 'the independent semantic method changed')
    require(digest(writer / 'TranslationProof01/TranslationProof.json') == '87b8d69ead4a38bae4ec6bb9fbb0f00165e8f9760b8d928bc8f217316ee0551c', 'the disclosed neutral method proof changed')
    require(digest(native / 'Inspection/Result.json') == 'e709d1cadabb2d010d3f4470d4d27c1e834da85841dcd8e0441f43ff8d64e28d'
            and load(native / 'Inspection/Result.json')['passed'], 'the disclosed native lifecycle is not qualified')
    require(digest(source / 'Source.json') == 'de5f421da1caae884565329c2d99bfbd4d9c262ccdda92b74eea71df05394b3c', 'the original native source packet differs')
    require(digest(source / 'Progress/D00/seal/Record.json') == 'cbf204d405ad1a9dcfce367b3c028fbb7b3c2b626a8277bd5acb558632df10f9', 'the public before-code neutral seal differs')
    output.mkdir()
    groups = {}
    groups['CodeRoot'] = copy_group(writer / 'CodeRoot01', output / 'CodeRoot', load(manifest)['current'])
    groups['WriterTools'] = copy_group(writer / 'Tools01', output / 'WriterTools', load(writer / 'BlindMethodFreeze01.json')['constructor_tools'])
    groups['EvaluationTools'] = copy_group(writer / 'EvaluationTools01', output / 'EvaluationTools', load(writer / 'BlindMethodFreeze01.json')['tools'])
    groups['NativeTools'] = copy_group(native / 'Tools', output / 'NativeTools', load(native / 'Job.json')['tools_sha256'])
    groups['ReaderTools'] = copy_group(reader / 'Tools01', output / 'ReaderTools', load(reader / 'ReaderCodeFreeze01.json')['tools'])
    for group, folder in (('GuestTools', writer / 'GuestTools01'), ('FreezeTools', writer / 'FreezeTools01'),
                          ('ProofTools', writer / 'EvaluationProofTools01'), ('SavedAuditTools', writer / 'NativeTools01')):
        entries = {path.name: digest(path) for path in sorted(folder.glob('*.py'))}
        groups[group] = copy_group(folder, output / group, entries)
    inputs = output / 'Inputs'
    inputs.mkdir()
    pairs = [(manifest, 'SourceManifest.json'), (writer / 'Proof01/WriterResults.json', 'WriterResults.json'),
             (writer / 'BlindMethodFreeze01.json', 'BlindMethodFreeze01.json'),
             (writer / 'PreWriterSourceLock01.json', 'PreWriterSourceLock.json'),
             (writer / 'TranslationProof01/TranslationProof.json', 'TranslationProof.json'),
             (writer / 'SavedReadback01/SavedReadback.json', 'SavedReadback.json'),
             (native / 'Inspection/Result.json', 'G01NativeResult.json'),
             (native / 'NeutralRequest.json', 'G01Request.json'),
             (native / 'Prediction.json', 'G01Prediction.json'), (native / 'ControlCase.json', 'ControlCase.json'),
             (native / 'ControlState.json', 'ControlState.json'), (source / 'Source.json', 'SourcePacket.json'),
             (source / 'Progress/D00/seal/Record.json', 'SourceSeal.json'),
             (writer / 'FieldClassifications02.json', 'FieldClassifications.json')]
    for path, name in pairs:
        copyfile(path, inputs / name)
    first = load(writer / 'Proof01/G01BuildA.stdout.json')
    expected_files = {role: {key: first[role][key] for key in ('bytes', 'sha256')} for role in ('assembly', 'child')}
    write(inputs / 'G01HostExpectedFiles.json', expected_files)
    runtime_basis = 'host Python 3.11 source proof'
    if args.runtime_worker is not None:
        require(args.runtime_worker_sha256 is not None and digest(args.runtime_worker) == args.runtime_worker_sha256
                and args.runtime_classification is not None and args.runtime_classification_sha256 is not None
                and digest(args.runtime_classification) == args.runtime_classification_sha256,
                'the independently classified disclosed runtime identity differs')
        classification = load(args.runtime_classification)
        require(classification['guest_worker_sha256'] == args.runtime_worker_sha256 and
                classification['all_nonfloating_typed_fields_and_aliases_equal'] and
                classification['stream_lengths_and_topology_equal'] and classification['heldout_inputs_read'] == 0
                and classification['writer_math_source_changed'] is False and classification['byte_patch_or_rounding_override_added'] is False,
                'the disclosed runtime variation was not independently bounded')
        runtime_result = load(args.runtime_worker)
        require(runtime_result['passed'] and runtime_result['runtime_input_file_reads'] == runtime_result['sdk_runtime_research_imports'] == 0,
                'the disclosed runtime build crossed its generative input boundary')
        expected_files = {role: {key: runtime_result[role][key] for key in ('bytes', 'sha256')} for role in ('assembly', 'child')}
        write(inputs / 'DisclosedRuntimeIdentity.json', {'worker_sha256': args.runtime_worker_sha256, 'files': expected_files,
              'classification_sha256': args.runtime_classification_sha256, 'basis': 'disclosed guest discovery before any H input access'})
        copyfile(args.runtime_classification, inputs / 'RuntimeClassification.json')
        runtime_basis = 'separate exact disclosed guest Python 3.12 identity; unchanged writer math and retained host baseline'
    write(inputs / 'G01ExpectedFiles.json', expected_files)
    native_job = load(native / 'Job.json')
    method = {'schema': 'kit.sw2026.perpendicular-blind-method.v1', 'task_id': 'B04-SW2026-MATES-PERPENDICULAR',
              'owner': 'assembly_occurrence', 'delivery_pr': 121, 'heldout_contents_read_at_freeze': False,
              'writer_source_manifest_sha256': digest(manifest), 'source_groups': groups,
              'inputs_sha256': {path.relative_to(output).as_posix(): digest(path) for path in sorted(inputs.glob('*.json'))},
              'source_packet_guest_path': str(guest.parent / 'PerpendicularMateSourcePacket05'),
              'source_packet_sha256': digest(source / 'Source.json'),
              'source_seal_record_sha256': digest(source / 'Progress/D00/seal/Record.json'),
              'combined_neutral_spec_sha256': 'c86195e3ebd547b562d847218ee55ada42acb86e31b67ef451c02a67cf80b0e4',
              'slots': {'Slot01': {'case_id': 'H01', 'source_lock_sha256': '6538c86b5fa05b7f3f7b7c605cbdad10a565820432959562e591f86d41beed7b'},
                        'Slot02': {'case_id': 'H02', 'source_lock_sha256': 'bcc0ad312a740ddfa56f2dade91ab6d7a209d7a2121bf555db82bcc2f732b416'}},
              'control_files': native_job['control_files'], 'native_phases': ['control-before', 'source', 'source-edited', 'generated', 'reopen', 'control-after'],
              'native_oracle_sha256': native_job['oracle_sha256'], 'native_generated_discovery_qualified': True,
              'disclosed_translation_qualified': True, 'admission': load(writer / 'BlindMethodFreeze01.json')['admission'],
              'runtime_byte_identity_basis': runtime_basis,
              'independent_expectations': load(writer / 'BlindMethodFreeze01.json')['independent_expectations'],
              'native_observations_excluded_from_generation': True, 'request_prediction_lock_before_native_source_access': True,
              'input_output_policy': 'neutral and native held-out payloads stay only on a canonical guest fixed drive; public progress exposes opaque slots hashes statuses and process identities',
              'public_perpendicular_writer_qualified': False, 'active_invalid_angle_correction_qualified': False,
              'native_execution_requires_root_review_and_release': True}
    method_sha = write(output / 'Method.json', method)
    entry = ['py', '-3.12', '-B']
    private = r'C:\KitSdkPerpendicular121'
    recipe = {'method_sha256': method_sha, 'guest_root': str(guest), 'guest_private_root': private,
              'verify_before_any_hidden_access': entry + [str(guest / 'GuestTools/VerifyPerpendicularFreeze.py'), str(guest / 'Method.json'),
                              '--method-sha256', method_sha, '--output', str(guest / 'Runtime/Guest01')],
              'runtime_freeze_requires_exact_disclosed_G01_bytes_in_two_processes': True,
              'release_templates': {slot: {'schema': 'kit.sw2026.perpendicular-neutral-slot-release.v1', 'method_sha256': method_sha,
                                          'runtime_sha256': '<verified-runtime-sha256>', 'slot': slot,
                                          'allow_combined_neutral_container_read': True} for slot in method['slots']},
              'slots': {}, 'always_run_trailing_control_independently': True, 'phase_timeout_seconds': 900,
              'no_automatic_process_termination': True, 'heldout_inputs_read_at_preparation': 0, 'native_processes_started': 0}
    for slot in method['slots']:
        common = [str(guest / 'Method.json'), '--method-sha256', method_sha, '--slot', slot, '--private-root', private]
        prep = entry + [str(guest / 'GuestTools/PreparePerpendicularSlot.py'), *common,
                        '--runtime-sha256', '<verified-runtime-sha256>', '--runtime-record', str(guest / 'Runtime/Guest01/Runtime.json'),
                        '--runtime-record-sha256', '<verified-runtime-record-sha256>', '--release', str(guest / 'Release' / (slot + '.json')),
                        '--release-sha256', '<reviewed-slot-release-sha256>', '--public-output', str(guest / 'Progress' / slot / 'Prepare.json')]
        tool = str(guest / 'GuestTools/EvaluatePerpendicularSlot.py')
        recipe['slots'][slot] = {'prepare_after_explicit_root_release': prep,
            'build_before_source_native_access': entry + [tool, 'build', *common, '--public-output', str(guest / 'Progress' / slot / 'Build.json')],
            'native': {phase: entry + [tool, 'native', *common, '--phase', phase,
                       '--public-output', str(guest / 'Progress' / slot / (phase + '.json'))] for phase in method['native_phases']},
            'finalize': entry + [tool, 'finalize', *common, '--public-output', str(guest / 'Progress' / slot / 'Final.json')]}
    recipe_sha = write(output / 'Recipe.json', recipe)
    print(json.dumps({'method_sha256': method_sha, 'recipe_sha256': recipe_sha, 'code_files': len(groups['CodeRoot']),
                      'executable_tools': sum(len(value) for key, value in groups.items() if key != 'CodeRoot'),
                      'heldout_inputs_read': 0, 'native_processes_started': 0}, sort_keys=True))


if __name__ == '__main__':
    main()
