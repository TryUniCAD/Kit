from argparse import ArgumentParser
from hashlib import sha256
from json import dumps, loads
from pathlib import Path
from shutil import copyfile
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PredictNamedOutput01 import prediction


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    parser = ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    proof_root = root/'LocalProof01'
    proof_path = proof_root/'ProcessProof.json'
    if digest(proof_path) != 'fc6880017dafd45667a1825cab5b24b98e5d2de6aaf32fb8990cf62a4d5600ba':
        raise ValueError('the exact original source-only process result differs')
    proof = loads(proof_path.read_text())
    if not proof['passed'] or proof['process_count'] != 44 or not proof['source_unchanged']:
        raise ValueError('all source-only process boundaries must pass before native staging')
    for name,checksum in loads((root/'WriterSource01.json').read_text())['files'].items():
        if digest(root/'Code01'/name) != checksum:
            raise ValueError('writer source closure changed')
    for name,checksum in loads((root/'WriterTools01.json').read_text())['files'].items():
        if digest(root/name) != checksum:
            raise ValueError('writer process method changed')
    args.output.mkdir(parents=True,exist_ok=False)
    tools = args.output/'Tools'
    tools.mkdir()
    oracle = Path('/Users/odin/Documents/UniCAD/Oracle121Takeover/SdkNamedBodyColdReuse01/RootNativeCold03')
    if digest(oracle/'Trial.json') != '20f481f114288850a77b9c9cbf3a22e251c563c54692ff9b05e614f8232032f4':
        raise ValueError('the previously qualified cold native method differs')
    old_job = loads((oracle/'Trial.json').read_text())
    for name in ('AuthorCurves.py','AuthorRectangleAnchors.py','InspectFresh.py','InspectSdkBlindPart.py','OracleIdentity.py','Swapp.py'):
        source = oracle/'Tools'/name
        if digest(source) != old_job['tools_sha256'][name]:
            raise ValueError('the previously qualified native observer dependency differs')
        copyfile(source,tools/name)
    for name in ('InspectNamedOutputPort01.py','PredictNamedOutput01.py'):
        copyfile(root/name,tools/name)
    control = oracle/'Control.SLDPRT'
    if digest(control) != 'c0472f9f42bf473a9073adb997180040b7767dfae93310610f77cff9509bec57':
        raise ValueError('disclosed native control differs')
    copyfile(control,args.output/'Control.SLDPRT')
    for name in ('WriterSource01.json','WriterTools01.json','NeutralCases01.json'):
        copyfile(root/name,args.output/name)
    copyfile(proof_path,args.output/'ProcessProof.json')
    sys.path[:0] = [str(root/'Code01/src'),str(root/'Harness01')]
    from MakeNamedRequest import request
    cases = []
    all_cases = loads((root/'NeutralCases01.json').read_text())['cases']
    proof_rows = {(row['case'],row['mode']):row for row in proof['build_processes']}
    for case in all_cases:
        if not case['native_trial']:
            continue
        name = case['name']
        for mode in ('Named','Repeat','Default'):
            source = proof_root/(name+mode+'.json')
            if digest(source) != proof_rows[name,mode]['report_sha256']:
                raise ValueError('the named source process custody differs')
            copyfile(source,args.output/source.name)
            generated = proof_root/(name+mode+'.SLDPRT')
            report = loads(source.read_text())
            if digest(generated) != report['artifact_sha256']:
                raise ValueError('the actual generated native file differs')
            copyfile(generated,args.output/generated.name)
        build = loads((args.output/(name+'Named.json')).read_text())
        _, settings, _ = request(case)
        tree = {'settings':{'system':{'folders':settings.SystemValue.FolderValues,
            'planes':dict(settings.SystemValue.PlaneNames),'cabinet_name':settings.SystemValue.CabinetName,
            'origin_name':settings.SystemValue.OriginName}}}
        cases.append({'name':name,'named_build':name+'Named.json','repeat_build':name+'Repeat.json',
            'plain_build':name+'Default.json','named_file':name+'Named.SLDPRT','plain_file':name+'Default.SLDPRT',
            'prediction':prediction(build),'tree_request':tree})
    inputs = {str(path.relative_to(args.output)):digest(path) for path in args.output.iterdir() if path.is_file()}
    job = {'schema':'kit.sw2026.sdk-named-output-native-discovery.v1','cases':cases,
        'oracle_sha256':'3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe',
        'control_sha256':'c0472f9f42bf473a9073adb997180040b7767dfae93310610f77cff9509bec57',
        'tools_sha256':{path.name:digest(path) for path in tools.iterdir()},'inputs_sha256':inputs,
        'source_manifest_sha256':digest(root/'WriterSource01.json'),'process_proof_sha256':digest(proof_path),
        'expected_native_processes':2+3*len(cases),'heldout_inputs_read':0,'public_writer_enabled':False,
        'original_source_qualification':False,'effective_unassigned_body_density_kg_m3':1.0,
        'document_density_preference_kg_m3':1000.0,'edit_scope':'depth_only_with_all_named_drivers_observed'}
    path = args.output/'Trial.json'
    path.write_text(dumps(job,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
    print(dumps({'packet':str(path),'packet_sha256':digest(path),'cases':len(cases),
        'expected_native_processes':job['expected_native_processes']},sort_keys=True))


if __name__ == '__main__':
    main()
