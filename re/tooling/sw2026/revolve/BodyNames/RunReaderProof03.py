import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys


def require(value,message):
    if not value:raise ValueError(message)


def digest(path):return sha256(path.read_bytes()).hexdigest()


def verify(path,directory):
    values=json.loads(path.read_bytes());require({row['path'] for row in values['files']}=={str(p.relative_to(directory)) for p in directory.rglob('*') if p.is_file()},'frozen file membership differs')
    for row in values['files']:
        require(digest(directory/row['path'])==row['sha256'],'frozen content differs: '+row['path'])


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();root=args.root.resolve(strict=True);output=args.output.resolve();require(not output.exists(),'reader proof output must be unused')
    for manifest,directory in (('Source03.json','Code02'),('Baseline01Source.json','Baseline01'),('Tools01.json','Tools01'),('FixtureGrammar01.json','FixtureGrammar01')):verify(root/manifest,root/directory)
    inputs=json.loads((root/'Inputs02.json').read_bytes());require(inputs['heldout_inputs_read']==0 and len(inputs['cases'])==26,'declared disclosed scope differs')
    for row in inputs['cases']:require(digest(Path(row['path']))==row['sha256'],'disclosed source custody differs')
    output.mkdir(parents=True)
    report={'schema':'kit.sw2026.revolve-body-name-reader-proof.v1','passed':False,'base_revision':'62044821b7736939bd36ac99fe9c3f63e23d5a79','source_manifest_sha256':digest(root/'Source03.json'),'baseline_manifest_sha256':digest(root/'Baseline01Source.json'),'tools_manifest_sha256':digest(root/'Tools01.json'),'grammar_manifest_sha256':digest(root/'FixtureGrammar01.json'),'input_manifest_sha256':digest(root/'Inputs02.json'),'runner_sha256':digest(Path(__file__)),'workers':[],'groups':[],'heldout_inputs_read':0,'native_processes':0,'writer_qualification':False}

    def save():(output/'Replay.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')

    def execute(name,command,row=None,allowed_exit_codes=(0,)):
        result=subprocess.run(command,input=json.dumps(row).encode() if row is not None else None,capture_output=True,timeout=90)
        (output/(name+'.stdout.txt')).write_bytes(result.stdout);(output/(name+'.stderr.txt')).write_bytes(result.stderr)
        report['workers'].append({'name':name,'exit_code':result.returncode,'stdout_sha256':sha256(result.stdout).hexdigest(),'stderr_sha256':sha256(result.stderr).hexdigest()});save();require(result.returncode in allowed_exit_codes,'worker failed '+name+' '+result.stderr.decode()[-2000:]);return result

    def probe(name,row,candidate):
        sdk=root/('Code02' if candidate else 'Baseline01');path=output/(name+'.json')
        command=[sys.executable,'-I','-B',str(root/'Tools01/ProbeBodyReader01.py'),'--sdk',str(sdk),'--source',row['path'],'--source-sha256',row['sha256'],'--expected-label',row.get('expected_label','unused'),'--output',str(path)]
        if candidate and row.get('positive'):command.append('--candidate')
        execute(name,command,allowed_exit_codes=(0,3) if row.get('negative') else (0,));value=json.loads(path.read_bytes());require((value['passed'] or row.get('negative') and all(isinstance(observation.get('error'),dict) or isinstance(observation.get('full_document_sha256'),str) and len(observation['full_document_sha256'])==64 for observation in value['observations'])) and value['source_immutable'] and not value['file_access_attempts'] and not value['unexpected_sdk_module_origins'] and not value['research_imports'],'public boundary failed');return value

    def compare(name,row):
        before=probe(name+'Baseline',row,False);after=probe(name+'Candidate',row,True);comparisons=[]
        for old,new in zip(before['observations'],after['observations'],strict=True):
            require(old['mode']==new['mode'],'mode order differs')
            changed=row.get('positive') and old['mode']!='History'
            if changed:require(old['unrelated_semantics_sha256']==new['unrelated_semantics_sha256'] and old['payloads']==new['payloads'] and old['body_ids']==new['body_ids'],'name projection changed unrelated source semantics or payload')
            else:require(old.get('full_document_sha256')==new.get('full_document_sha256') and old.get('error')==new.get('error'),'unchanged or refused profile changed')
            comparisons.append({'mode':old['mode'],'passed':True,'name_projection_expected':bool(changed),'baseline_label':old.get('labels'),'candidate_label':new.get('labels'),'error':new.get('error')})
        report['groups'].append({'name':name,'positive':bool(row.get('positive')),'source_sha256':row['sha256'],'comparisons':comparisons});save()

    try:
        for index,row in enumerate(inputs['cases']):compare('Case'+str(index),row)
        for index,variant in enumerate(inputs['negative_variants']):
            source=inputs['sources'][index%3];other=inputs['sources'][(index+1)%3];path=output/(variant+'.SLDPRT')
            fixture_row=dict(source,variant=variant,other_path=other['path'],other_sha256=other['sha256'])
            result=execute('Fixture'+str(index),[sys.executable,'-I','-B',str(root/'Tools01/MutateBodyReader01.py'),'--sdk',str(root/'Code02'),'--grammar',str(root/'FixtureGrammar01'),'--output',str(path)],fixture_row)
            value=json.loads(result.stdout);require(value['passed'] and value['source_immutable'] and not value['writer_output'],'research fixture custody failed');compare('Negative'+str(index),{'path':str(path),'sha256':value['sha256'],'negative':True})
        for manifest,directory in (('Source03.json','Code02'),('Baseline01Source.json','Baseline01'),('Tools01.json','Tools01'),('FixtureGrammar01.json','FixtureGrammar01')):verify(root/manifest,root/directory)
        require(all(digest(Path(row['path']))==row['sha256'] for row in inputs['cases']),'disclosed source changed during proof');report['passed']=True
    except Exception as error:report['error']=repr(error)
    finally:report['fresh_processes']=len(report['workers']);report['paired_mode_comparisons']=sum(len(group['comparisons']) for group in report['groups']);save()
    print(json.dumps({'passed':report['passed'],'processes':report['fresh_processes'],'groups':len(report['groups']),'report_sha256':digest(output/'Replay.json'),'error':report.get('error')}));return 0 if report['passed'] else 3


if __name__=='__main__':raise SystemExit(main())
