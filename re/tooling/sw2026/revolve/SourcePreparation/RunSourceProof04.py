import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys


def require(value,message):
    if not value:raise ValueError(message)


def digest(path):return sha256(path.read_bytes()).hexdigest()


def verify(manifest,root):
    values=json.loads(manifest.read_bytes())
    for row in values['files']:
        p=root/row['path'];require(p.is_file() and p.stat().st_size==row['bytes'] and digest(p)==row['sha256'],'frozen dependency differs: '+row['path'])


def ordinary(document):
    value=deepcopy(document)
    value['feature_timeline']={'$tuple':[row for row in value['feature_timeline']['$tuple'] if row['name']=='OrdinaryBossRevolve']}
    for row in value['feature_timeline']['$tuple']:row['order']=0
    value['metadata'].pop('native_feature_count',None)
    value['metadata'].pop('solidworks_source_semantic_sha256',None)
    value['metadata']['solidworks.typed_resolved_semantics'].pop('native_tree',None)
    return value


def fallback(document):
    value=deepcopy(document)
    value['metadata']['solidworks.typed_resolved_semantics'].pop('native_tree',None)
    value['metadata'].pop('solidworks_source_semantic_sha256',None)
    return value


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();root=args.root.resolve(strict=True);output=args.output.resolve();require(not output.exists(),'proof output must be unused')
    verify(root/'Source02.json',root/'Code02');verify(root/'BaselineSource02.json',root/'Baseline02');verify(root/'Tools04.json',root/'Tools04')
    inputs=json.loads((root/'Inputs02.json').read_bytes());output.mkdir(parents=True)
    report={'schema':'kit.sw2026.ordinary-revolve-source-proof.v1','passed':False,'source_manifest_sha256':digest(root/'Source02.json'),'base_manifest_sha256':digest(root/'BaselineSource02.json'),'tools_manifest_sha256':digest(root/'Tools04.json'),'inputs_sha256':digest(root/'Inputs02.json'),'runner_sha256':digest(Path(__file__)),'positives':[],'rejections':[],'generated_replays':[],'polygon_regressions':[],'workers':[],'heldout_inputs_read':0,'native_processes':0}
    def checkpoint():(output/'Replay.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    def run(name,tool,row,sdk='Code02',role=None):
        command=[sys.executable,'-I','-B',str(root/'Tools04'/tool),'--sdk',str(root/sdk)]
        if role:command+=['--role',role]
        process=subprocess.run(command,input=json.dumps(row),capture_output=True,text=True,timeout=90)
        (output/(name+'.stdout')).write_text(process.stdout);(output/(name+'.stderr')).write_text(process.stderr)
        report['workers'].append({'name':name,'exit_code':process.returncode,'stdout_sha256':sha256(process.stdout.encode()).hexdigest(),'stderr_sha256':sha256(process.stderr.encode()).hexdigest()});checkpoint()
        require(process.returncode==0,'worker failed '+name+' '+process.stderr)
        value=json.loads(process.stdout);require(value['passed'] and not value['runtime_external_attempts'],'worker did not pass its actual boundary '+name)
        for module in value.get('sdk_modules',()):require(Path(module).is_relative_to(root/sdk/'src'),'worker SDK import escaped the frozen source')
        value.pop('sdk_modules',None);value.pop('blob',None);return value
    try:
        for index,row in enumerate(inputs['controls']):
            base=run('SourceBase'+str(index),'AuditRevSource01.py',row,'Baseline02','base')
            layer=run('SourceLayer'+str(index),'AuditRevSource01.py',row,role='layer')
            require(base['streams']==layer['streams'] and base['metadata']==layer['metadata'],'source graph codec changed with presentation projection')
            for mode in base['modes']:
                require(ordinary(base['modes'][mode]['source_document'])==ordinary(layer['modes'][mode]['source_document']),'unrelated public source semantics changed in '+mode)
            for value in layer['modes'].values():value.pop('source_document',None)
            report['positives'].append({'name':row['name'],'source_sha256':row['sha256'],'native_observation_sha256':row['native_observation']['sha256'],**layer});checkpoint()
        for index,variant in enumerate(('custom_note','root_order','extra_axis_relation')):
            row={**inputs['controls'][0],'variant':variant}
            base=run('RejectBase'+str(index),'AuditRevSource01.py',row,'Baseline02','base')
            layer=run('RejectLayer'+str(index),'AuditRevSource01.py',row,role='layer')
            require(base['research_repack_sha256']==layer['research_repack_sha256'],'negative source mutation differs between source closures')
            for mode in base['modes']:
                before,after=base['modes'][mode],layer['modes'][mode]
                if 'source_document' in before:
                    require('source_document' in after and fallback(before['source_document'])==fallback(after['source_document']),'unsupported source semantics were discarded by new presentation')
                else:require(before==after,'unsupported source failure changed')
            report['rejections'].append({'variant':variant,'repacked_sha256':layer['research_repack_sha256'],'source_preserved':True,'modes':{key:{name:value for name,value in row.items() if name!='source_document'} for key,row in layer['modes'].items()}});checkpoint()
        for index,row in enumerate(inputs['generated_requests']):
            value=run('FreshRevolve'+str(index),'AuditSdkRevBuild01.py',{'spec':row['spec']})
            require(value['sha256']==row['sha256'],'the existing proven native output hash changed')
            report['generated_replays'].append(value);checkpoint()
        for index,row in enumerate((inputs['generated_requests'][0],inputs['generated_requests'][3])):
            request={'spec':row['spec'],'depth_mm':9.125+index*14.25}
            before=run('PolygonBase'+str(index),'AuditPolygonControl01.py',request,'Baseline02')
            after=run('PolygonLayer'+str(index),'AuditPolygonControl01.py',request)
            require(before==after,'existing bare boss source semantics or bytes changed')
            report['polygon_regressions'].append(after);checkpoint()
        report['passed']=True
    except Exception as error:report['error']=repr(error)
    finally:
        report['fresh_processes']=len(report['workers'])
        report['paired_original_modes']=sum(len(value['modes']) for value in report['positives'])
        report['native_numeric_checks']=sum(row['numeric_checks'] for value in report['positives'] for row in value['native_numeric_comparison'])
        report['inputs_immutable']=all(digest(Path(row['path']))==row['sha256'] and digest(Path(row['native_observation']['path']))==row['native_observation']['sha256'] for row in inputs['controls'])
        report['passed']=report['passed'] and report['inputs_immutable'];checkpoint()
    print(json.dumps({'passed':report['passed'],'processes':report['fresh_processes'],'report_sha256':digest(output/'Replay.json')}));return 0 if report['passed'] else 3


if __name__=='__main__':raise SystemExit(main())
