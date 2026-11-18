from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from json import dumps,loads
from pathlib import Path
import subprocess,sys


def main():
    parser=ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    root=args.root.resolve(strict=True)
    manifests={}
    for name,folder in (('BaselineSource01.json','Baseline01'),('CodeSource02.json','Code02')):
        manifest=loads((root/name).read_bytes())
        for relative,pin in manifest['files'].items():
            if sha256((root/folder/relative).read_bytes()).hexdigest()!=pin:
                raise ValueError('frozen public reader source differs: '+relative)
        manifests[name]=sha256((root/name).read_bytes()).hexdigest()
    fixtures=loads((root/'Fixtures03.json').read_bytes())
    for row in fixtures['sources']:
        if sha256(Path(row['path']).read_bytes()).hexdigest()!=row['sha256']:
            raise ValueError('frozen public reader input differs')
    tools={name:sha256((root/name).read_bytes()).hexdigest() for name in
        ('AuditPublicRevolve01.py','RunPublicRevolve02.py','PreparePublicRevolve02.py')}
    args.output.mkdir(parents=True,exist_ok=False)
    jobs=[(row,side) for row in fixtures['sources'] for side in ('baseline','candidate')]
    def run(job):
        row,side=job
        command=[sys.executable,'-B',str(root/'AuditPublicRevolve01.py'),'--sdk',str(root/('Code02' if side=='candidate' else 'Baseline01'))]
        if side=='candidate':command.append('--candidate')
        result=subprocess.run(command,input=dumps(row),text=True,capture_output=True,timeout=90)
        record={'name':row['name'],'side':side,'exit':result.returncode,'stderr':result.stderr}
        if result.stdout:
            try:record['result']=loads(result.stdout)
            except ValueError:record['stdout']=result.stdout
        record['passed']=result.returncode==0 and record.get('result',{}).get('passed',False)
        path=args.output/(row['name']+'-'+side+'.json')
        path.write_text(dumps(record,indent=2,sort_keys=True)+'\n')
        return record
    with ThreadPoolExecutor(max_workers=4) as pool:records=list(pool.map(run,jobs))
    lookup={(row['name'],row['side']):row for row in records}
    comparisons={}
    for row in fixtures['sources']:
        first=lookup[(row['name'],'baseline')]
        second=lookup[(row['name'],'candidate')]
        modes={}
        if first['passed'] and second['passed']:
            for name,before in first['result']['modes'].items():
                after=second['result']['modes'][name]
                if row['kind']=='revolve':
                    modes[name]={'unrelated_exact':before['unrelated_semantics_sha256']==after['unrelated_semantics_sha256'],
                        'brep_exact':before['brep_sha256']==after['brep_sha256'],
                        'tessellation_exact':before['tessellation_sha256']==after['tessellation_sha256'],
                        'body_exact':before['bodies_sha256']==after['bodies_sha256'],
                        'candidate_projected':after['projected'],
                        'capability_delta':sorted(set(after['capabilities']).difference(before['capabilities'])),
                        'capabilities_lost':sorted(set(before['capabilities']).difference(after['capabilities']))}
                    modes[name]['passed']=all(modes[name][key] for key in ('unrelated_exact','brep_exact','tessellation_exact','body_exact','candidate_projected')) and not modes[name]['capabilities_lost']
                else:
                    modes[name]={'passed':before==after,'no_new_projection':not after['projected']}
        comparisons[row['name']]={'kind':row['kind'],'passed':len(modes)==5 and all(value['passed'] for value in modes.values()),'modes':modes}
    report={'schema':'kit.sw2026.public-revolve-reader-replay.v1','passed':all(row['passed'] for row in records)
        and all(row['passed'] for row in comparisons.values()),'processes':len(records),'groups':len(comparisons),
        'public_mode_comparisons':sum(len(row['modes']) for row in comparisons.values()),
        'source_manifests':manifests,'tools_sha256':tools,
        'fixture_manifest_sha256':sha256((root/'Fixtures03.json').read_bytes()).hexdigest(),
        'numeric_checks':sum(sum(mode.get('numeric_checks',0) for mode in row.get('result',{}).get('modes',{}).values()) for row in records),
        'heldout_inputs_read':0,'native_processes_started':0,
        'records':{row['name']+'-'+row['side']:{'sha256':sha256((args.output/(row['name']+'-'+row['side']+'.json')).read_bytes()).hexdigest(),
            'passed':row['passed'],'exit':row['exit']} for row in records},'comparisons':comparisons}
    target=args.output/'Replay.json'
    target.write_text(dumps(report,indent=2,sort_keys=True)+'\n')
    print(dumps({'passed':report['passed'],'processes':len(records),'groups':len(comparisons),
        'sha256':sha256(target.read_bytes()).hexdigest(),'path':str(target),
        'worker_failures':[row['name']+'-'+row['side'] for row in records if not row['passed']],
        'comparison_failures':[key for key,value in comparisons.items() if not value['passed']]}))
    raise SystemExit(0 if report['passed'] else 3)


if __name__=='__main__':main()
