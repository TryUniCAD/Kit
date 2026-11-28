import argparse
from hashlib import sha256
import json
from pathlib import Path, PureWindowsPath
from shutil import copyfile
import sys


PROOF = '0744dfc514fb2524147918d7b56da4ee548bd50854d48a78b9b768610f10be0b'
SOURCES = '0f660dcb6fef84b12b382fa40e542069d49dab0ec6169151b154b4222f5884fa'
SOURCE_PACKET = 'de5f421da1caae884565329c2d99bfbd4d9c262ccdda92b74eea71df05394b3c'
SOURCE_LOCK = '614c05ee076b728018e2371fa0d992ab59e379afc625eec22aa699dd16729aee'
CONTROL_STATE = '0d0783ba55f61d192e30b317a54def4784a0941ed4e6e63561e6f9e92bf9fbcd'
CONTROL_PARENT = '54303798c1386b050dd80544c0394f85fd2c56e6bd306d70f8d1d188b5aed5ef'
CONTROL_CHILD = '14c79efaae814f6d4802fba9ebeafaf463685ab1754b1469d9313b60384d36f8'


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def checked(path, wanted):
    require(path.is_file() and not path.is_symlink() and digest(path) == wanted, 'a declared perpendicular proof dependency changed')
    return path


def load(path):
    return json.loads(path.read_bytes())


def write(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    return digest(path)


def verify_source(root, source_packet):
    proof = load(checked(root / 'Proof01/WriterResults.json', PROOF))
    closure = load(checked(root / 'Proof01/SourceManifest.json', SOURCES))
    require(proof['passed'] is True and proof['distinct_worker_count'] == 102 and proof['source_manifest_sha256'] == SOURCES
            and proof['runtime_input_file_reads'] == proof['sdk_runtime_research_imports'] == 0,
            'the generated perpendicular process method is not qualified')
    for label, directory in (('current', root / 'CodeRoot01'), ('baseline', root / 'BaselineRoot01'), ('tools', root / 'Tools01')):
        for name, wanted in closure[label].items():
            checked(directory / name, wanted)
    packet = load(checked(source_packet / 'Source.json', SOURCE_PACKET))
    for name, wanted in packet['tools_sha256'].items():
        checked(source_packet / 'Tools' / name, wanted)
    checked(root / 'PreWriterSourceLock01.json', SOURCE_LOCK)
    return proof, packet


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--writer', type=Path, required=True)
    parser.add_argument('--source-packet', type=Path, required=True)
    parser.add_argument('--control', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--guest-root', required=True)
    parser.add_argument('--guest-control', required=True)
    args = parser.parse_args()
    root, source_packet, control = (value.resolve(strict=True) for value in (args.writer, args.source_packet, args.control))
    proof, source = verify_source(root, source_packet)
    observed = load(checked(control / 'SavedAuthor.json', CONTROL_STATE))
    checked(control / 'Native/Source/PerpendicularFrontTop.SLDASM', CONTROL_PARENT)
    checked(control / 'Native/Source/PerpendicularDatum.SLDPRT', CONTROL_CHILD)
    output = args.output.resolve()
    guest, guest_control = PureWindowsPath(args.guest_root), PureWindowsPath(args.guest_control)
    require(guest.is_absolute() and guest_control.is_absolute() and '\\' not in guest.as_posix(), 'use canonical absolute Windows native identities')
    output.mkdir(parents=True, exist_ok=False)
    tools = output / 'Tools'
    tools.mkdir()
    for name in source['tools_sha256']:
        copyfile(source_packet / 'Tools' / name, tools / name)
    for path in Path(__file__).resolve().parent.glob('*.py'):
        copyfile(path, tools / path.name)
    copyfile(root / 'Tools01/PerpendicularMath.py', tools / 'PerpendicularMath.py')
    copyfile(root / 'CodeRoot01/re/tooling/sw2026/PrepareSdkAssemblyNative.py', tools / 'PrepareSdkAssemblyNative.py')
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(tools))
    from PerpendicularNativePlan import case_from_spec, check_predictions, native_trees
    from PerpendicularSourcePlan import disclosed_cases
    spec = load(root / 'Fixtures01/G01/Spec.json')
    request = load(root / 'Fixtures01/G01/Request.json')
    prediction = load(root / 'Fixtures01/G01/Prediction.json')
    case = case_from_spec(spec)
    check_predictions(case, prediction)
    rows = load(root / 'Proof01/G01Readback.stdout.json')['actual_owned_endpoints']
    build = load(root / 'Proof01/G01BuildA.stdout.json')
    identities = {'mate_id': build['endpoints'][0]['mate_id'], 'endpoints': rows,
                  'basis': 'fresh generated allocator and independent complete typed SDK graph readback'}
    names = {'parent': spec['name'] + '.SLDASM', 'child': spec['child_name'] + '.SLDPRT'}
    for directory in ('FrozenGenerated', 'GeneratedInput'):
        (output / directory).mkdir()
        for name in names.values():
            copyfile(root / 'Proof01/G01/Generated' / name, output / directory / name)
    for source_name, target in (('Spec.json', 'Spec.json'), ('Request.json', 'NeutralRequest.json'), ('Prediction.json', 'Prediction.json')):
        copyfile(root / 'Fixtures01/G01' / source_name, output / target)
    for source_path, target in ((root / 'Proof01/WriterResults.json', 'WriterResults.json'),
                                (root / 'Proof01/SourceManifest.json', 'SourceManifest.json'),
                                (root / 'PreWriterSourceLock01.json', 'PreWriterSourceLock.json')):
        copyfile(source_path, output / target)
    write(output / 'Case.json', case)
    write(output / 'Trees.json', native_trees(request))
    write(output / 'GeneratedIdentity.json', identities)
    write(output / 'ControlCase.json', disclosed_cases()[0])
    write(output / 'ControlState.json', observed['source'])
    generated = {name: {'sha256': digest(output / 'FrozenGenerated' / name), 'bytes': (output / 'FrozenGenerated' / name).stat().st_size,
                        'encoded_path': str(guest / 'GeneratedInput' / name)} for name in names.values()}
    require(request['assembly']['output']['path_name'] == generated[names['parent']]['encoded_path'] and
            request['child']['settings']['output']['path_name'] == generated[names['child']]['encoded_path'],
            'the frozen generated identities do not match this exact guest packet')
    job = {'schema': 'kit.sw2026.generated-perpendicular-native-packet.v1', 'guest_root': str(guest),
           'oracle_sha256': source['oracle_sha256'], 'source_manifest_sha256': SOURCES, 'writer_result_sha256': PROOF,
           'prewriter_source_lock_sha256': SOURCE_LOCK, 'qualified_source_packet_sha256': SOURCE_PACKET,
           'tools_sha256': {path.name: digest(path) for path in sorted(tools.glob('*.py'))},
           'inputs_sha256': {path.name: digest(path) for path in sorted(output.glob('*.json'))},
           'generated_names': names, 'generated_files': generated,
           'control_files': {'parent': {'guest_path': str(guest_control / 'Native/Source/PerpendicularFrontTop.SLDASM'), 'sha256': CONTROL_PARENT},
                             'child': {'guest_path': str(guest_control / 'Native/Source/PerpendicularDatum.SLDPRT'), 'sha256': CONTROL_CHILD}},
           'phase_order': ['control-before', 'generated', 'reopen', 'control-after'], 'trailing_control_independent': True,
           'source_controls_read_only': True, 'save_order': ['child', 'parent'], 'immutable_input_pair': True,
           'cold_generated_source_reader': 'rejected by unchanged solved-only reader', 'native_acceptance': False,
           'public_writer_qualified': False, 'heldout_inputs_read': 0, 'native_processes_started': 0,
           'active_angular_correction_proven': False, 'scope': 'one generated principal-plane perpendicular mate with valid live reorientation and dimensioned rectangular child depth edit'}
    job_sha = write(output / 'Job.json', job)
    entry = ['py', '-3.12', '-B', str(guest / 'Tools/InspectGeneratedPerpendicular.py')]
    arguments = [str(guest / 'Job.json'), '--packet-sha256', job_sha]
    recipe = {'packet_sha256': job_sha, 'verify': entry + ['verify', *arguments],
              'phases': {phase: entry + ['run', *arguments, '--phase', phase] for phase in job['phase_order']},
              'summary': entry + ['summary', *arguments], 'phase_timeout_seconds': 900,
              'always_run_trailing_control_independently': True, 'no_automatic_process_termination': True,
              'progress': str(guest / 'Inspection'), 'heldout_inputs_read': 0, 'native_processes_started': 0}
    recipe_sha = write(output / 'Recipe.json', recipe)
    print(json.dumps({'output': str(output), 'packet_sha256': job_sha, 'recipe_sha256': recipe_sha,
                      'observer_sha256': job['tools_sha256']['InspectGeneratedPerpendicular.py'],
                      'files': generated, 'native_processes_started': 0, 'heldout_inputs_read': 0}, indent=2))


if __name__ == '__main__':
    main()
