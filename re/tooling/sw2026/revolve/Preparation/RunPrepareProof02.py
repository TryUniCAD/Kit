import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys


def require(condition,message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def verify_sources(manifest_path,root):
    manifest=json.loads(manifest_path.read_bytes())
    for row in manifest['files']:
        path=root/row['path']
        require(path.is_file() and path.stat().st_size==row['bytes'] and digest(path)==row['sha256'],
            'source closure differs: '+row['path'])
    actual={str(path.relative_to(root)) for path in root.rglob('*') if path.is_file() and '__pycache__' not in path.parts}
    require(actual=={row['path'] for row in manifest['files']},'source membership differs')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    root=args.root.resolve(strict=True);output=args.output.resolve()
    require(not output.exists(),'proof output must be unused')
    verify_sources(root/'Source03.json',root/'Code03')
    verify_sources(root/'BaseSource01.json',root/'Baseline02')
    verify_sources(root/'ToolsFinal02.json',root/'Tools02')
    inputs=json.loads((root/'Inputs01.json').read_bytes())
    for row in inputs['reader_fixtures']:
        require(digest(Path(row['path']))==row['sha256'],'disclosed input custody differs')
    output.mkdir(parents=True)
    report={'schema':'kit.sw2026.sdk-revolve-internal-prepare-proof.v1','passed':False,
        'source_manifest_sha256':digest(root/'Source03.json'),'base_manifest_sha256':digest(root/'BaseSource01.json'),
        'tools_manifest_sha256':digest(root/'ToolsFinal02.json'),'inputs_sha256':digest(root/'Inputs01.json'),
        'runner_sha256':digest(Path(__file__)),'native_report_sha256':inputs['native_report_sha256'],
        'lifecycle_adjudication_sha256':inputs['lifecycle_adjudication_sha256'],
        'construction':[],'preparation':[],'neutral_rejects':[],'option_rejects':[],
        'polygon_regressions':[],'native_states':[],'processes':[],'heldout_inputs_read':0,'native_processes':0}
    def checkpoint():
        (output/'Replay.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    def worker(label,tool,row,sdk='Code03'):
        completed=subprocess.run([sys.executable,'-I','-B',str(root/'Tools02'/tool),'--sdk',str(root/sdk)],
            input=json.dumps(row),capture_output=True,text=True,timeout=90)
        (output/(label+'.stdout')).write_text(completed.stdout)
        (output/(label+'.stderr')).write_text(completed.stderr)
        report['processes'].append({'name':label,'exit_code':completed.returncode,
            'stdout_sha256':sha256(completed.stdout.encode()).hexdigest(),'stderr_sha256':sha256(completed.stderr.encode()).hexdigest()})
        checkpoint()
        require(completed.returncode==0,'worker failed: '+label+'\n'+completed.stderr)
        value=json.loads(completed.stdout)
        require(value['passed'] and not value['runtime_external_attempts'],'worker failed assertions: '+label)
        for module in value.get('sdk_modules',()):
            require(Path(module).is_relative_to(root/sdk/'src'),'SDK import escaped frozen source: '+module)
        value.pop('sdk_modules',None)
        value.pop('blob',None)
        return value
    try:
        for index,row in enumerate(inputs['generated_requests']):
            built=worker(f'Build{index}','AuditSdkRevBuild01.py',{'spec':row['spec']})
            require(built['sha256']==row['sha256'],'promoted constructor changed the exact native qualified bytes')
            report['construction'].append(built)
            prepared=worker(f'Prepare{index}','AuditRevPrep01.py',row)
            require(prepared['sha256']==row['sha256'],'high level preparation changed native bytes')
            report['preparation'].append(prepared)
            checkpoint()
        mutations=('expression','negative_angle','excess_angle','tiny_angle','nonfinite_angle','two_sided',
            'axis_in_contour','missing_axis_relation','fixed_axis','extra_metadata','body_name','support_origin',
            'alternate_unit','wrong_relation','axis_relation','downward_axis','axis_origin','additional_configuration')
        base=inputs['generated_requests'][1]
        for index,mutation in enumerate(mutations):
            value=worker(f'NeutralReject{index}','AuditSdkRevBuild01.py',{'spec':base['spec'],'mutation':mutation})
            require(value['rejected'],'unsupported neutral source produced output')
            report['neutral_rejects'].append({'mutation':mutation,**value})
        variants=('configuration','unknown_option','unnamed_stream','wrong_suffix','wrong_basename','wrong_format','bad_epoch','wrong_stream_final')
        for index,variant in enumerate(variants):
            value=worker(f'OptionReject{index}','AuditRevPrep01.py',{**base,'variant':variant})
            require(value['rejected'],'unsupported preparation returned output')
            report['option_rejects'].append({'variant':variant,**value})
        for index,row in enumerate((inputs['generated_requests'][0],inputs['generated_requests'][3])):
            request={'spec':row['spec'],'depth_mm':11.375+index*9.25}
            before=worker(f'PolygonBase{index}','AuditPolygonControl01.py',request,'Baseline02')
            after=worker(f'PolygonLayer{index}','AuditPolygonControl01.py',request)
            require(before==after,'shared generic consumers changed an existing polygon output or read')
            report['polygon_regressions'].append(before)
        for index,row in enumerate(inputs['reader_fixtures']):
            before=worker(f'StateBase{index}','AuditRevolveStates02.py',row,'Baseline02')
            after=worker(f'StateLayer{index}','AuditRevolveStates02.py',row)
            require(before==after,'internal writer layer changed normal strict reader behavior')
            require(len(after['streams'])==8 and len(after['modes'])==5,'state method did not reach its complete frozen boundary')
            report['native_states'].append({'name':row['name'],'role':row['role'],'sha256':row['sha256'],**after})
            checkpoint()
        report['passed']=True
    except Exception as error:
        report['error']=repr(error)
    finally:
        report['fresh_processes']=len(report['processes'])
        report['paired_reader_modes']=sum(len(row['modes']) for row in report['native_states'])
        report['critical_model_streams']=sum(len(row['streams']) for row in report['native_states'])
        report['metadata_qualification_complete']=all(row['all_metadata_qualified'] for row in report['native_states'])
        report['inputs_immutable']=all(digest(Path(row['path']))==row['sha256'] for row in inputs['reader_fixtures'])
        report['passed']=report['passed'] and report['inputs_immutable']
        checkpoint()
    print(json.dumps({'passed':report['passed'],'fresh_processes':report['fresh_processes'],
        'paired_reader_modes':report['paired_reader_modes'],'metadata_qualification_complete':report['metadata_qualification_complete'],
        'report_sha256':digest(output/'Replay.json')}))
    return 0 if report['passed'] else 3


if __name__=='__main__':
    raise SystemExit(main())
