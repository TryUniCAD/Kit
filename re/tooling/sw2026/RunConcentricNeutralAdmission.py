import argparse
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def inventory(root):
    return {path.relative_to(root).as_posix():digest(path) for path in sorted(root.rglob('*')) if path.is_file() and '__pycache__' not in path.parts and path.suffix not in ('.pyc','.pyo')}


def write(path,value):
    assert not path.exists()
    path.write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n')


def main():
    parser=argparse.ArgumentParser()
    for name in ('root','inputs','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    args.root=args.root.resolve()
    args.output.mkdir(parents=True,exist_ok=False)
    tools={name:digest(Path(__file__).with_name(name)) for name in ('CheckConcentricNeutralBrep.py','ConcentricNeutralAdmission.py','ConcentricNeutralProcess.py','RunConcentricNeutralAdmission.py')}
    before={'root':str(args.root),'files':inventory(args.root),'tools':tools,'inputs_sha256':digest(args.inputs),'python':sys.version,'interpreter':sys.executable}
    write(args.output/'SourceBefore.json',before)
    cases=json.loads(args.inputs.read_bytes())
    jobs=[]
    for request in cases['positive']:
        jobs.extend((request['label']+suffix,request) for suffix in ('A','B'))
    for mutation in cases['negative']:
        jobs.append(('Negative'+mutation,{**cases['positive'][0],'mutation':mutation}))

    def run(job):
        label,request=job
        target=args.output/(label+'.json')
        command=[sys.executable,'-I','-B',str(Path(__file__).with_name('ConcentricNeutralProcess.py')),'--root',str(args.root),'--output',str(target)]
        if label==cases['positive'][0]['label']+'A':command.extend(('--document-output',str(args.output/'AuthoredDocument.json')))
        result=subprocess.run(command,input=json.dumps(request,sort_keys=True),capture_output=True,text=True,timeout=180)
        write(args.output/(label+'.Transport.json'),{'exit':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
        assert result.returncode==0,(label,result.stderr[-3000:])
        data=json.loads(target.read_bytes())
        assert data['passed'] and data['refused']==bool(request.get('mutation'))
        return label,data

    with ThreadPoolExecutor(max_workers=4) as pool:results=dict(pool.map(run,jobs))
    for request in cases['positive']:
        first={key:value for key,value in results[request['label']+'A'].items() if key!='pid'}
        second={key:value for key,value in results[request['label']+'B'].items() if key!='pid'}
        assert first==second
    pids=[value['pid'] for value in results.values()]
    assert len(pids)==len(set(pids))==len(jobs)
    assert inventory(args.root)==before['files']
    assert all(digest(Path(__file__).with_name(name))==value for name,value in tools.items())
    assert digest(args.inputs)==before['inputs_sha256']
    summary={'passed':True,'sdk_processes':len(jobs),'unique_processes':len(set(pids)),
        'positive_processes':2*len(cases['positive']),'positive_intents':len(cases['positive']),
        'negative_processes':len(cases['negative']),'deterministic_positive_pairs':len(cases['positive']),
        'profiles':sorted(set(value['profile'] for value in cases['positive'])),
        'normal_json_roundtrip_positives':sum(value.get('normal_json_roundtrip_admitted',False) for value in results.values()),
        'source_and_tools_unchanged':True,'runtime_io_attempts':sum(value['runtime_io_attempts'] for value in results.values()),
        'native_processes':0,'hidden_inputs_read':0,'new_assembly_files':0,
        'records':{label:{'sha256':digest(args.output/(label+'.json')),'pid':value['pid']} for label,value in results.items()},
        'source_before_sha256':digest(args.output/'SourceBefore.json')}
    write(args.output/'Results.json',summary)
    print(json.dumps({'passed':True,'result_sha256':digest(args.output/'Results.json')}))


if __name__=='__main__':main()
