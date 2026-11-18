from argparse import ArgumentParser
from hashlib import sha256
from json import dumps,loads
from pathlib import Path
from shutil import copyfile
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent))

from PredictAnchoredPart01 import prediction


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    parser=ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--oracle-source',type=Path,required=True)
    parser.add_argument('--owner-helper',type=Path,required=True)
    args=parser.parse_args()
    root=args.root.resolve(strict=True)
    prior=args.oracle_source.resolve(strict=True)
    if digest(prior/'Trial.json')!='ce4b4c7c434732775104758686cb83723dcdeb31965f43b4f1fd09a51e9b9e96':
        raise ValueError('the previous qualified native packet differs')
    old=loads((prior/'Trial.json').read_bytes())
    proof_root=root/'LocalProof02'
    proof_path=proof_root/'ProcessProof.json'
    if digest(proof_path)!='a123db3205eed9263a5b52a8a4d6f6646d342b36001c28068afda56765a29953':
        raise ValueError('the exact complete guarded anchored proof differs')
    proof=loads(proof_path.read_bytes())
    if not proof['passed'] or proof['process_count']!=55 or not proof['source_unchanged']:
        raise ValueError('the complete anchored source process qualification must pass')
    for name,wanted in loads((root/'WriterSource01.json').read_bytes())['files'].items():
        if digest(root/'Code01'/name)!=wanted:
            raise ValueError('anchored source closure changed: '+name)
    for name,wanted in loads((root/'WriterTools02.json').read_bytes())['files'].items():
        if digest(root/name)!=wanted:
            raise ValueError('anchored source proof tool changed: '+name)
    args.output.mkdir(exist_ok=False,parents=True)
    tools=args.output/'Tools'
    tools.mkdir()
    for name in ('AuthorCurves.py','AuthorRectangleAnchors.py','InspectFresh.py','InspectSdkBlindPart.py',
                 'OracleIdentity.py','Swapp.py','PredictNamedOutput01.py'):
        source=prior/'Tools'/name
        if digest(source)!=old['tools_sha256'][name]:
            raise ValueError('previous qualified native helper differs: '+name)
        copyfile(source,tools/name)
    if digest(args.owner_helper)!='0d0b4c4d8ea92cb4cf6e0d8242d192b5f4c4608a653cc2abd41ab5e4ac0e74cd':
        raise ValueError('the previously qualified point owner helper differs')
    copyfile(args.owner_helper,tools/'InspectCornerPointOwners.py')
    for name in ('PredictAnchoredPart01.py','AnchorBodyGraph01.py','InspectAnchorBody01.py'):
        copyfile(root/name,tools/name)
    if digest(prior/'Control.SLDPRT')!='c0472f9f42bf473a9073adb997180040b7767dfae93310610f77cff9509bec57':
        raise ValueError('pristine native control differs')
    copyfile(prior/'Control.SLDPRT',args.output/'Control.SLDPRT')
    for name in ('WriterSource01.json','BaselineSource01.json','WriterTools02.json','NeutralCases01.json'):
        copyfile(root/name,args.output/name)
    copyfile(proof_path,args.output/'ProcessProof.json')
    sys.path[:0]=[str(root/'Code01/src'),str(root/'Harness01')]
    from MakeAnchoredRequest import request
    cases=[]
    inputs=loads((root/'NeutralCases01.json').read_bytes())['cases']
    rows={(row['case'],row['mode']):row for row in proof['processes'] if row['mode']!='Reject'}
    for name in ('CornerAscii','CenterWide'):
        source_case=next(row for row in inputs if row['name']==name)
        for mode in ('Named','Repeat','Default','Reference'):
            source=proof_root/(name+mode+'.json')
            if digest(source)!=rows[name,mode]['report_sha256']:
                raise ValueError('anchored source worker custody differs')
            copyfile(source,args.output/source.name)
            native=proof_root/(name+mode+'.SLDPRT')
            build=loads(source.read_bytes())
            if digest(native)!=build['artifact_sha256']:
                raise ValueError('actual generated anchored bytes differ')
            copyfile(native,args.output/native.name)
        build=loads((args.output/(name+'Named.json')).read_bytes())
        unused,settings,dimensions=request(source_case)
        tree={'settings':{'system':{'folders':settings.SystemValue.FolderValues,
            'planes':dict(settings.SystemValue.PlaneNames),'cabinet_name':settings.SystemValue.CabinetName,
            'origin_name':settings.SystemValue.OriginName}}}
        cases.append({'name':name,'named_build':name+'Named.json','repeat_build':name+'Repeat.json',
            'plain_build':name+'Default.json','reference_build':name+'Reference.json',
            'named_file':name+'Named.SLDPRT','plain_file':name+'Default.SLDPRT',
            'predictions':{role:prediction(build,source_case,role) for role in ('width','height','depth')},
            'tree_request':tree})
    paths={str(path.relative_to(args.output)):digest(path) for path in args.output.iterdir() if path.is_file()}
    job={'schema':'kit.sw2026.sdk-anchored-named-body-native.v1','cases':cases,
        'oracle_sha256':old['oracle_sha256'],'control_sha256':old['control_sha256'],
        'inputs_sha256':paths,'tools_sha256':{path.name:digest(path) for path in tools.iterdir()},
        'source_manifest_sha256':digest(root/'WriterSource01.json'),'process_proof_sha256':digest(proof_path),
        'expected_native_processes':16,'heldout_inputs_read':0,'public_writer_enabled':False,
        'original_source_qualification':False,'effective_unassigned_body_density_kg_m3':1.0,
        'document_density_preference_kg_m3':1000.0,
        'edit_scope':'independent_width_height_depth_from_the_same_immutable_baseline',
        'legacy_phase_scalar_alias':'new_depth_m_carries_the_explicit_active_driver_new_value_m_for_the_shared_phase',
        'predecessor_disclosed_native_packet_sha256':digest(prior/'Trial.json')}
    path=args.output/'Trial.json'
    path.write_text(dumps(job,indent=2,ensure_ascii=True,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
    print(dumps({'path':str(path),'sha256':digest(path),'expected_native_processes':16},sort_keys=True))


if __name__=='__main__':
    main()
