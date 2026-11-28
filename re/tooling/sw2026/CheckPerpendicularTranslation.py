import argparse
from base64 import b64decode
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(data):
    return sha256(data).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')
    return digest(path.read_bytes())


def source_check(base):
    require(digest((base / 'BlindMethodFreeze01.json').read_bytes()) == '1bd6567368e31f010932078cc3ff486f91efe752ccd96ce57d485ac89c861821',
            'the before-execution blind translation method freeze differs')
    freeze = json.loads((base / 'BlindMethodFreeze01.json').read_bytes())
    for label, folder in (('tools', 'EvaluationTools01'), ('constructor_tools', 'Tools01'), ('native_tools', 'OracleTools01')):
        for name, wanted in freeze[label].items():
            require(digest((base / folder / name).read_bytes()) == wanted, 'a frozen prediction translation or comparison tool changed')
    source = json.loads((base / 'Proof01/SourceManifest.json').read_bytes())
    for name, wanted in source['current'].items():
        require(digest((base / 'CodeRoot01' / name).read_bytes()) == wanted, 'the frozen writer/codec source changed')
    return freeze


def run(command, incoming, output, tag):
    result = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = result.communicate(incoming, timeout=120)
    (output / (tag + '.stdin.json')).write_bytes(incoming)
    (output / (tag + '.stdout.json')).write_bytes(stdout)
    (output / (tag + '.stderr.txt')).write_bytes(stderr)
    return {'pid': result.pid, 'exit_code': result.returncode, 'stdout': stdout, 'stderr': stderr}


def build(base, request, output, tag):
    root = base / 'CodeRoot01'
    command = [sys.executable, '-I', '-B', str(root / 're/tooling/sw2026/SdkPlanarGroupProcess.py'), str(root)]
    process = run(command, request, output, tag)
    require(process['exit_code'] == 0, 'the disclosed translated build failed: ' + process['stderr'].decode()[-1200:])
    value = json.loads(process['stdout'])
    require(value['passed'] and value['runtime_input_file_reads'] == value['sdk_runtime_research_imports'] == 0,
            'the disclosed translated build crossed its source-only boundary')
    return value, process


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--writer', type=Path, required=True)
    parser.add_argument('--native-packet', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    base = args.writer.resolve(strict=True)
    packet = args.native_packet.resolve(strict=True)
    freeze = source_check(base)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    sys.path[:0] = [str(packet / 'Tools'), str(base / 'Tools01')]
    from PerpendicularNativePlan import native_trees
    from PerpendicularSourcePlan import disclosed_cases
    cases = disclosed_cases()
    translator = base / 'EvaluationTools01/TranslatePerpendicularCase.py'
    comparator = base / 'EvaluationTools01/ComparePerpendicularNative.py'
    command = [sys.executable, '-I', '-B', str(translator), '--root', str(base / 'CodeRoot01'),
               '--model-tools', str(base / 'Tools01'), '--native-root', r'C:\KitPerpendicularDisclosed\GeneratedInput']
    positives, processes, predictions = [], [], {}
    for case in (cases[0], cases[2]):
        tag = case['id']
        incoming = json.dumps(case, separators=(',', ':'), allow_nan=False).encode()
        translation = run(command, incoming, output, tag + 'Translate')
        require(translation['exit_code'] == 0, 'the disclosed neutral translator failed')
        translated = json.loads(translation['stdout'])
        request = json.dumps(translated['request'], separators=(',', ':'), allow_nan=False).encode()
        prepared = output / tag
        prepared.mkdir()
        (prepared / 'Request.json').write_bytes(request)
        prediction_sha = write(prepared / 'Prediction.json', translated['prediction'])
        trees = native_trees(translated['request'])
        write(prepared / 'PreparationLock.json', {'request_sha256': digest(request), 'prediction_sha256': prediction_sha,
              'native_source_files_opened': False, 'native_observations_used': False, 'method_freeze_sha256': digest((base / 'BlindMethodFreeze01.json').read_bytes())})
        first, first_process = build(base, request, output, tag + 'BuildA')
        second, second_process = build(base, request, output, tag + 'BuildB')
        left, right = dict(first), dict(second)
        left.pop('worker_pid');right.pop('worker_pid')
        require(left == right, 'the translated request produces nondeterministic complete bundles')
        parent = prepared / (case['name'] + '.SLDASM')
        child = prepared / (case['child_name'] + '.SLDPRT')
        parent.write_bytes(b64decode(first['assembly']['blob'], validate=True))
        child.write_bytes(b64decode(first['child']['blob'], validate=True))
        read_request = json.dumps({'parent': str(parent), 'child': str(child), 'prediction': translated['prediction']}, allow_nan=False).encode()
        read = run([sys.executable, '-I', '-B', str(base / 'Tools01/VerifyPerpendicularGraph.py'), '--root', str(base / 'CodeRoot01')],
                   read_request, output, tag + 'Readback')
        require(read['exit_code'] == 0 and json.loads(read['stdout'])['passed'], 'the translated generated typed graph differs from its neutral prediction')
        predictions[tag] = (translated['prediction'], trees)
        positives.append({'case': tag, 'request_sha256': digest(request), 'prediction_sha256': prediction_sha,
                          'parent_sha256': digest(parent.read_bytes()), 'child_sha256': digest(child.read_bytes()),
                          'deterministic_complete_bundles': True, 'independent_typed_graph_equal': True,
                          'runtime_input_file_reads': 0, 'sdk_runtime_research_imports': 0})
        processes.extend((translation, first_process, second_process, read))
    reverse = run(command, json.dumps(cases[1], allow_nan=False).encode(), output, 'RejectReverseSelection')
    require(reverse['exit_code'] != 0 and not reverse['stdout'] and b'reverse source-selection order' in reverse['stderr'],
            'unbound source-selection normalization was not rejected before output')
    private_negative = deepcopy(cases[0])
    private_negative.update(id='H01', split='heldout')
    private = run(command, json.dumps(private_negative, allow_nan=False).encode(), output, 'RejectHostSealedSlot')
    require(private['exit_code'] != 0 and not private['stdout'] and b'sealed case translation is guest-only' in private['stderr'],
            'the host accepted a synthetic sealed-slot payload')
    processes.extend((reverse, private))
    source_path = Path('/Users/odin/Documents/UniCAD/Oracle121Takeover/PerpendicularMateSourcePacket03/Disclosed/D01/SavedAuthor.json')
    require(digest(source_path.read_bytes()) == '0d0783ba55f61d192e30b317a54def4784a0941ed4e6e63561e6f9e92bf9fbcd', 'the disclosed D01 native control changed')
    source = json.loads(source_path.read_bytes())['source']
    require([[item['name'], item['type'], item['parent']] for item in source['tree']] == predictions['D01'][1]['parent'] and
            [[item['name'], item['type'], item['parent']] for item in source['child_tree']] == predictions['D01'][1]['child'],
            'the independently authored native default roles differ from the disclosed control')
    control_record = packet / 'Inspection/control-before/Record.json'
    control = json.loads(control_record.read_bytes())
    require(control['passed'] and control['result']['inputs_unchanged'], 'the independently repeated disclosed control is not qualified')
    compare_request = {'case': cases[0], 'source': source, 'generated': control['result']['initial'],
                       'prediction': predictions['D01'][0], 'edited': False}
    compare = run([sys.executable, '-I', '-B', str(comparator)], json.dumps(compare_request, allow_nan=False).encode(), output, 'CompareIndependentNativeControls')
    require(compare['exit_code'] == 0 and json.loads(compare['stdout'])['passed'], 'the paired comparator rejected independently measured identical native controls')
    generated_record = packet / 'Inspection/generated/Record.json'
    generated = json.loads(generated_record.read_bytes())
    require(generated['passed'], 'the disclosed generated G01 native measurement is not qualified')
    compare_request['generated'] = generated['result']['initial']
    unlike = run([sys.executable, '-I', '-B', str(comparator)], json.dumps(compare_request, allow_nan=False).encode(), output, 'RejectDifferentNativeDesign')
    require(unlike['exit_code'] != 0 and not unlike['stdout'] and b'native trees differ' in unlike['stderr'],
            'the paired comparator accepted an authentically different native design')
    processes.extend((compare, unlike))
    require(len({row['pid'] for row in processes}) == len(processes) and source_check(base) == freeze,
            'the translation method changed or process identities were reused')
    result = {'schema': 'kit.sw2026.perpendicular-blind-translation-disclosed-proof.v1', 'passed': True,
              'method_freeze_sha256': digest((base / 'BlindMethodFreeze01.json').read_bytes()), 'local_process_count': len(processes),
              'positives': positives, 'reverse_source_selection_rejected_before_output': True,
              'host_sealed_slot_payload_rejected_before_output': True, 'synthetic_sealed_negative_contains_no_real_heldout_values': True,
              'authentic_independent_native_control_comparison_passed': True, 'authentic_different_native_design_comparison_rejected': True,
              'native_control_record_sha256': digest(control_record.read_bytes()), 'native_generated_record_sha256': digest(generated_record.read_bytes()),
              'paired_source_generated_native_equivalence_proven': False, 'heldout_inputs_read': 0, 'native_processes_started': 0,
              'public_writer_qualified': False}
    fingerprint = write(output / 'TranslationProof.json', result)
    print(json.dumps({'passed': True, 'local_process_count': len(processes), 'result_sha256': fingerprint,
                      'heldout_inputs_read': 0, 'native_processes_started': 0}, sort_keys=True))


if __name__ == '__main__':
    main()
