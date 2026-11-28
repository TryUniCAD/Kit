from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

p=argparse.ArgumentParser()
p.add_argument('--method',type=Path,required=True)
p.add_argument('--method-sha256',required=True)
p.add_argument('--baseline',type=Path,required=True)
p.add_argument('--candidate',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
p.add_argument('--python',default=sys.executable)
a=p.parse_args()

def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def pinned(row):
    assert digest(row['path'])==row['sha256']
    return json.loads(Path(row['path']).read_bytes())


def verify(root,description):
    spec=pinned(description)
    for row in spec['files']:
        assert digest(root/row['path'])==row['sha256'],row['path']

assert digest(a.method)==a.method_sha256
method=json.loads(a.method.read_bytes())
assert method['schema']=='kit.sw2026.blank-strict-read-method.v1'
assert digest(method['probe']['path'])==method['probe']['sha256']
verify(a.baseline,method['baseline_manifest'])
verify(a.candidate,method['candidate_manifest'])
a.output.mkdir(parents=True,exist_ok=False)
tasks=[]
groups=[]
for group,rows,modes in (('positive',method['positives'],method['positive_modes']),('negative',method['negatives'],method['negative_modes'])):
    for row in rows:
        assert digest(row['path'])==row['sha256']
        for route,options in modes:
            key=group+'-'+row['name']+'-'+route+'-'+options
            groups.append({'key':key,'kind':group,'case':row['name']})
            for side,root in (('baseline',a.baseline),('candidate',a.candidate)):
                output=a.output/(key+'-'+side+'.json')
                command=[a.python,'-I','-B',method['probe']['path'],'--code',str(root),'--file',row['path'],'--sha256',row['sha256'],'--output',str(output),'--route',route,'--options',options,'--expect','accept' if side=='candidate' and group=='positive' else 'reject']
                if row.get('request'):
                    command+=['--request',row['request']]
                tasks.append({'key':key,'kind':group,'case':row['name'],'side':side,'output':str(output),'command':command})


def execute(row):
    completed=subprocess.run(row['command'],capture_output=True,text=True,timeout=60,check=False)
    path=Path(row['output'])
    report=json.loads(path.read_bytes()) if path.is_file() else None
    return {key:row[key] for key in ('key','kind','case','side')}|{'passed':completed.returncode==0 and report is not None and report['passed'],'exit_code':completed.returncode,'receipt_sha256':digest(path) if path.is_file() else None,'output':row['output'],'stdout_sha256':sha256(completed.stdout.encode()).hexdigest(),'stderr_sha256':sha256(completed.stderr.encode()).hexdigest(),'report':report,'worker_process_id_not_recorded':True}

with ThreadPoolExecutor(max_workers=2) as pool:
    results=list(pool.map(execute,tasks))
comparisons=[]
for group in groups:
    rows=[r for r in results if r['key']==group['key']]
    assert len(rows)==2
    baseline=next(r for r in rows if r['side']=='baseline')
    candidate=next(r for r in rows if r['side']=='candidate')
    pair=bool(baseline['passed'] and candidate['passed'] and baseline['report']['partial']==candidate['report']['partial'])
    comparisons.append(group|{'passed':pair,'partial_output_identical':pair,'baseline_receipt_sha256':baseline['receipt_sha256'],'candidate_receipt_sha256':candidate['receipt_sha256']})
verify(a.baseline,method['baseline_manifest'])
verify(a.candidate,method['candidate_manifest'])
for row in (*method['positives'],*method['negatives']):
    assert digest(row['path'])==row['sha256']
report={'schema':'kit.sw2026.blank-strict-read-replay.v1','passed':all(r['passed'] for r in results) and all(r['passed'] for r in comparisons),'method_sha256':a.method_sha256,'baseline_manifest_sha256':method['baseline_manifest']['sha256'],'candidate_manifest_sha256':method['candidate_manifest']['sha256'],'probe_sha256':method['probe']['sha256'],'workers':len(results),'paired_groups':len(comparisons),'comparisons':comparisons,'results':results,'source_and_inputs_immutable':True,'private_slot_reads':0,'native_app_launches':0,'native_acceptance_claim':False,'unit_tests':False}
with (a.output/'Replay.json').open('x') as f:
    json.dump(report,f,indent=2,allow_nan=False)
print(json.dumps({'passed':report['passed'],'workers':len(results),'groups':len(comparisons),'failures':[{k:r[k] for k in ('key','side','output')} for r in results if not r['passed']],'replay_sha256':digest(a.output/'Replay.json')}))
raise SystemExit(0 if report['passed'] else 3)
