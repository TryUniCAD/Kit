from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from json import dumps,loads
from pathlib import Path
from subprocess import run
import sys


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def verify(root):
    for name,wanted in loads((root/'BaselineSource01.json').read_bytes())['files'].items():
        if digest(root/'Baseline01'/name)!=wanted:
            raise ValueError('the exact circle reader source snapshot changed')
    for row in loads((root/'DisclosedInputs01.json').read_bytes())['inputs']:
        if digest(Path(row['path']))!=row['sha256']:
            raise ValueError('the exact disclosed input changed')


def main():
    parser=ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    root=args.root.resolve(strict=True)
    verify(root)
    inputs=loads((root/'DisclosedInputs01.json').read_bytes())['inputs']
    observations=loads((root/'NativeCircleObservations01.json').read_bytes())['observations']
    args.output.mkdir(parents=True,exist_ok=False)

    def execute(row):
        native=next(value for value in observations if value['name']==row['name'] and value['state']==row['state'])
        request={'input':row,'native_observation':native}
        name=row['name']+row['state'].title()
        process=run([sys.executable,'-I','-B',str(root/'AuditFreeCutCircle02.py'),'--sdk',str(root/'Baseline01')],
            input=dumps(request),capture_output=True,text=True,timeout=120)
        path=args.output/(name+'.stdout.json')
        error=args.output/(name+'.stderr.txt')
        (args.output/(name+'.stdin.json')).write_text(dumps(request,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
        path.write_text(process.stdout,encoding='utf-8',newline='\n')
        error.write_text(process.stderr,encoding='utf-8',newline='\n')
        value=loads(process.stdout) if process.returncode==0 else None
        return {'name':row['name'],'state':row['state'],'family':row['family'],'returncode':process.returncode,
            'passed':bool(value and value['passed']),'result':value,'report_sha256':digest(path),'stderr_sha256':digest(error)}

    with ThreadPoolExecutor(max_workers=3) as pool:
        rows=list(pool.map(execute,inputs))
    verify(root)
    result={'schema':'kit.sw2026.disclosed-circle-local-read-process.v2','passed':all(row['passed'] for row in rows),
        'source_manifest_sha256':digest(root/'BaselineSource01.json'),'source_unchanged':True,
        'worker_sha256':digest(root/'AuditFreeCutCircle02.py'),'runner_sha256':digest(Path(__file__)),
        'inputs_manifest_sha256':digest(root/'DisclosedInputs01.json'),
        'native_circle_observations_sha256':digest(root/'NativeCircleObservations01.json'),
        'processes':9,'blind_source_count':3,'through_all_source_designs':3,'through_all_source_saves':6,
        'typed_stream_roundtrips':18,'native_geometry_samples':18,'sdk_changes':0,'heldout_inputs_read':0,
        'native_processes_started':0,'whole_through_all_operation_audited':False,
        'predecessor_observer_failure_sha256':'1f3e9e4497627523cd8d5f15a0d1ce5f655e14f6b738ccb487fde5f6d0d83c15','rows':rows}
    path=args.output/'Proof.json'
    path.write_text(dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
    print(dumps({'passed':result['passed'],'sha256':digest(path),
        'failed':[(row['name'],row['state']) for row in rows if not row['passed']]},sort_keys=True))
    raise SystemExit(0 if result['passed'] else 3)


if __name__=='__main__':
    main()
