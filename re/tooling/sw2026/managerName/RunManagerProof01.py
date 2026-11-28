import argparse
import base64
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def verify(path, directory):
    value = json.loads(path.read_bytes())
    require({row['path'] for row in value['files']} == {str(item.relative_to(directory)) for item in directory.rglob('*') if item.is_file()}, 'frozen source/tool membership differs')
    for row in value['files']:
        item = directory / row['path']
        require(item.stat().st_size == row['bytes'] and digest(item) == row['sha256'], 'frozen file differs: '+row['path'])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    output = args.output.resolve()
    require(not output.exists(), 'process proof output must be unused')
    verify(root/'Source01.json',root/'Code01')
    verify(root/'BaselineSource02.json',root/'Baseline01')
    verify(root/'Tools01.json',root/'Tools01')
    require(digest(root/'Inputs01.json')=='9df7ffdfa513226e453a29d87a0e855a13e8fe6a23ac383c03ce5227afd9dee3', 'disclosed input manifest differs')
    inputs=json.loads((root/'Inputs01.json').read_bytes())
    require(inputs['heldout_inputs_read']==0 and len(inputs['sources'])==len(inputs['generated_requests'])==4, 'declared input scope differs')
    for row in inputs['sources']:
        require(row['disclosed'] is True and digest(Path(row['path']))==row['sha256'], 'disclosed source identity differs')
    output.mkdir(parents=True)
    report={'schema':'kit.sw2026.optional-manager-proof.v1','passed':False,'base_revision':'7971e9c01b4299f6764357c3f07699c2ddd72091','source_manifest_sha256':digest(root/'Source01.json'),'baseline_manifest_sha256':digest(root/'BaselineSource02.json'),'tools_manifest_sha256':digest(root/'Tools01.json'),'input_manifest_sha256':digest(root/'Inputs01.json'),'runner_sha256':digest(Path(__file__)),'workers':[],'sources':[],'graphs':[],'builds':[],'rejections':[],'heldout_inputs_read':0,'native_processes':0,'full_original_source_preparation_admitted':False,'public_unnamed_manager_preparation_enabled':False,'unnamed_output_native_qualification':False}

    def save():
        (output/'Replay.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')

    def worker(name,mode,row):
        encoded=json.dumps(row,ensure_ascii=False).encode()
        (output/(name+'.stdin.json')).write_bytes(encoded)
        trial=subprocess.run([sys.executable,'-I','-B',str(root/'Tools01'/'AuditManager01.py'),'--sdk',str(root/'Code01'),'--mode',mode],input=encoded,capture_output=True,timeout=90)
        (output/(name+'.stdout.json')).write_bytes(trial.stdout)
        (output/(name+'.stderr.txt')).write_bytes(trial.stderr)
        report['workers'].append({'name':name,'exit_code':trial.returncode,'stdin_sha256':sha256(encoded).hexdigest(),'stdout_sha256':sha256(trial.stdout).hexdigest(),'stderr_sha256':sha256(trial.stderr).hexdigest()})
        save()
        require(trial.returncode==0,'process failed '+name+' '+trial.stderr.decode()[-2400:])
        value=json.loads(trial.stdout)
        require(value['passed'] and not value['runtime_external_attempts'] and value['native_processes']==value['heldout_inputs_read']==0,'process boundary failed '+name)
        for path in value.pop('sdk_modules'):
            require(Path(path).is_relative_to(root/'Code01'/'src'),'SDK import escaped frozen source')
        if 'artifact_base64' in value:
            data=base64.b64decode(value.pop('artifact_base64'),validate=True)
            require(sha256(data).hexdigest()==value['sha256'],'generated output transport identity differs')
            (output/(name+'.SLDPRT')).write_bytes(data)
        return value

    try:
        for index,row in enumerate(inputs['sources']):
            report['sources'].append(worker('Source'+str(index),'source',row));save()
        configs=[{'name':'Working','description':'explicit working configuration','updated_at':1795000000},{'name':'Review-β','description':'','updated_at':1795000017},{'name':'Export','description':'independent authored state','updated_at':1795000031}]
        for index,(name,values,selected) in enumerate(((None,configs[:1],0),('Configurations',configs[:1],0),(None,configs,2),('Configuration β',configs,1))):
            row=dict(inputs['generated_requests'][0],manager_name=name,configs=values,current_index=selected)
            report['graphs'].append(worker('Graph'+str(index),'graph',row));save()
        for index,row in enumerate(inputs['generated_requests']):
            report['builds'].append(worker('Build'+str(index),'build',row));save()
        faults=('empty_name','nul_name','boolean_name','empty_configs','list_configs','duplicate_configs','boolean_selector','negative_selector','range_selector','none_current','distinct_selectors','foreign_current','wrong_config_class','wrong_local_id','allocation_count','directory_count','empty_directory','missing_name','empty_name_object','wrong_name_class','wrong_name_schema','allocated_null_manager','unnamed_other_node')
        for index,fault in enumerate(faults):
            report['rejections'].append(worker('Reject'+str(index),'reject',dict(inputs['generated_requests'][index%4],fault=fault)));save()
        verify(root/'Source01.json',root/'Code01')
        verify(root/'BaselineSource02.json',root/'Baseline01')
        verify(root/'Tools01.json',root/'Tools01')
        require(all(digest(Path(row['path']))==row['sha256'] for row in inputs['sources']),'disclosed source changed during proof')
        report['passed']=True
    except Exception as error:
        report['error']=repr(error)
    finally:
        report['fresh_processes']=len(report['workers'])
        report['typed_original_cmgr_replays']=len(report['sources'])
        report['guarded_named_default_hashes_preserved']=len(report['builds'])
        report['generated_strict_mode_comparisons']=2*len(report['builds'])
        save()
    print(json.dumps({'passed':report['passed'],'processes':report['fresh_processes'],'report_sha256':digest(output/'Replay.json'),'error':report.get('error')}))
    return 0 if report['passed'] else 3


if __name__=='__main__':
    raise SystemExit(main())
