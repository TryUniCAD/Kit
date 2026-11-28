from argparse import ArgumentParser
from base64 import b64decode
from hashlib import sha256
from json import dumps, loads
from pathlib import Path
from shutil import copyfile
from subprocess import run
import sys


CONTROL = 'c0472f9f42bf473a9073adb997180040b7767dfae93310610f77cff9509bec57'
ORACLE = '3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe'
TOOL_NAMES = ('InspectColdNamedPart.py', 'AuthorCurves.py', 'AuthorRectangleAnchors.py',
              'InspectFresh.py', 'InspectSdkBlindPart.py', 'OracleIdentity.py', 'Swapp.py')


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def verify_sources(sdk, manifest):
    value = loads(manifest.read_text())
    missing = [name for name, expected in value['files'].items()
               if not (sdk / name).is_file() or digest(sdk / name) != expected]
    if missing:
        raise ValueError('cold SDK closure differs: ' + repr(missing[:5]))
    return {'manifest_sha256': digest(manifest), 'verified_files': len(value['files'])}


def main():
    parser = ArgumentParser()
    parser.add_argument('--sdk', type=Path, required=True)
    parser.add_argument('--sdk-manifest', type=Path, required=True)
    parser.add_argument('--oracle-tools', type=Path, required=True)
    parser.add_argument('--control', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    owner = Path(__file__).resolve().parent
    inputs = loads((owner / 'PrepareTools01.json').read_text())
    for name, expected in inputs['files'].items():
        if digest(owner / name) != expected:
            raise ValueError('cold preparation source differs: ' + name)
    if digest(args.sdk_manifest) != inputs['sdk_manifest_sha256']:
        raise ValueError('cold preparation requires the independently qualified SDK closure')
    source = verify_sources(args.sdk, args.sdk_manifest)
    if digest(args.control) != CONTROL:
        raise ValueError('cold preparation has no pinned pristine L1 control')
    native_sources = {}
    for name in TOOL_NAMES:
        path = owner / name if name == 'InspectColdNamedPart.py' else args.oracle_tools / name
        if not path.is_file():
            raise ValueError('cold preparation oracle dependency is missing: ' + name)
        native_sources[name] = path
    specs = loads((owner / 'NeutralSpecs01.json').read_text())
    if len(specs) != 2 or len({row['self_path'] for row in specs}) != 2:
        raise ValueError('cold preparation needs two independent explicit design slots')
    if args.verify_only:
        print(dumps({'verified': True, 'source': source,
                     'host_tool_manifest_sha256': digest(owner / 'PrepareTools01.json'),
                     'oracle_dependencies': {name: digest(path) for name, path in native_sources.items()},
                     'designs': len(specs), 'processes_started': 0}))
        return
    args.output.mkdir(parents=True, exist_ok=False)
    tool_output = args.output / 'Tools'
    tool_output.mkdir()
    for name, path in native_sources.items():
        copyfile(path, tool_output / name)
    copyfile(args.control, args.output / 'Control.SLDPRT')
    copyfile(args.sdk_manifest, args.output / 'SdkSourceManifest.json')
    copyfile(owner / 'PrepareTools01.json', args.output / 'HostToolManifest.json')
    rows = []
    cases = []
    for index, spec in enumerate(specs, 1):
        name = 'Design' + str(index)
        spec_path = args.output / (name + 'Spec.json')
        spec_path.write_text(dumps(spec, indent=2, sort_keys=True) + '\n', newline='\n')
        reports = []
        for role in ('Named', 'Repeat', 'Plain'):
            path = args.output / (name + role + '.json')
            command = [sys.executable, '-I', '-B', str(owner / 'BuildColdNames.py'), '--sdk', str(args.sdk)]
            if role == 'Plain':
                command.append('--unnamed-control')
            process = run(command, input=dumps(spec), capture_output=True, text=True, timeout=120)
            path.write_text(process.stdout, encoding='utf-8', newline='\n')
            (args.output / (name + role + '.stderr.txt')).write_text(process.stderr, encoding='utf-8', newline='\n')
            if process.returncode != 0:
                raise ValueError('cold guarded generation failed: ' + name + role + ': ' + process.stderr)
            value = loads(process.stdout)
            if not value['passed'] or value['runtime_input_file_reads'] != 0:
                raise ValueError('cold guarded generation is unqualified: ' + name + role)
            reports.append(value)
        named, repeated, plain = reports
        if named != repeated or named['plain_artifact_sha256'] != plain['artifact_sha256']:
            raise ValueError('cold design is not deterministic or does not match its generated plain control')
        named_file, plain_file = name + 'Named.SLDPRT', name + 'Plain.SLDPRT'
        for value, filename in ((named, named_file), (plain, plain_file)):
            payload = b64decode(value['blob'], validate=True)
            if sha256(payload).hexdigest() != value['artifact_sha256'] or len(payload) != value['artifact_bytes']:
                raise ValueError('cold generated artifact transport differs')
            (args.output / filename).write_bytes(payload)
        rows.append({'name': name, 'spec_sha256': digest(spec_path),
            'named_sha256': named['artifact_sha256'], 'plain_sha256': plain['artifact_sha256'],
            'repeat_exact': True, 'plain_exact': True,
            'logical_stream_difference': named['logical_stream_difference'],
            'runtime_input_file_reads': 0, 'heldout_inputs_read': 0})
        cases.append({'name': name, 'named_file': named_file, 'plain_file': plain_file,
            'named_build': name + 'Named.json', 'repeat_build': name + 'Repeat.json',
            'plain_build': name + 'Plain.json', 'prediction': named['prediction'],
            'tree_request': named['tree_request']})
    after = verify_sources(args.sdk, args.sdk_manifest)
    proof = {'schema': 'kit.sw2026.cold-named-body-source-proof.v1', 'passed': True,
        'process_count': 6, 'source_before': source, 'source_after': after,
        'host_tools_sha256': digest(owner / 'PrepareTools01.json'), 'rows': rows,
        'heldout_inputs_read': 0, 'native_acceptance': False, 'named_body_writer_qualified': False}
    (args.output / 'BuildProof.json').write_text(dumps(proof, indent=2, sort_keys=True) + '\n', newline='\n')
    job = {'schema': 'kit.sw2026.cold-named-body-native-discovery.v1',
        'oracle_sha256': ORACLE, 'control_sha256': CONTROL,
        'tools_sha256': {name: digest(tool_output / name) for name in TOOL_NAMES},
        'inputs_sha256': {str(path.relative_to(args.output)): digest(path)
            for path in sorted(args.output.iterdir()) if path.is_file() and not path.name.endswith('.stderr.txt')},
        'cases': cases, 'heldout_inputs_read': 0, 'named_body_writer_qualified': False}
    job_path = args.output / 'Trial.json'
    job_path.write_text(dumps(job, indent=2, sort_keys=True) + '\n', newline='\n')
    print(dumps({'passed': True, 'processes': 6, 'packet': str(job_path),
                 'packet_sha256': digest(job_path), 'build_proof_sha256': digest(args.output / 'BuildProof.json')}, sort_keys=True))


if __name__ == '__main__':
    main()
