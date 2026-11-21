from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from json import dumps,loads
from pathlib import Path
import subprocess,sys


def main():
    parser=ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    root=args.root.resolve(strict=True)
    source=args.source.resolve(strict=True)
    pins=[
        ('RevolveFull','28e1f9cd045a7a264b2bdf8658ae593744d65ca708def4a48199ec357f063ab0','35795ccd5a42ad297a187d516e6a36c9d4e089a6eabce1558b6c669c505908bc'),
        ('RevolvePartialForward','0ea9ae68f7da6bd1d5542ce5b6689fd8f793dfcf2b5fefea44373043da17804d','3178d37339a68d7b5257c3996739d17e066208f0f3bd1d9390b23206bb576c85'),
        ('RevolvePartialReverse','b3b345451717fef654043008f95f477a04cd369a1b838c86e7f7ef975080533b','27c5496ffd5f0ed868fe1d043a2e3e7a63bfe82652f64490ad08122dc8da591c')]
    manifest=loads((root/'BaselineSource01.json').read_bytes())
    for name,h in manifest['files'].items():
        if sha256((root/'Baseline01'/name).read_bytes()).hexdigest()!=h:raise ValueError('source closure differs')
    jobs=[]
    negative=('invalid_reverse','legacy_type','second_angle','missing_forward','negative_angle',
        'nonfinite_angle','over_full_turn','parameter_expression','axis_profile_mismatch','axis_mark_mismatch',
        'axis_index_outside','boundary_selected','degenerate_axis','axis_relation','wrong_relation_geometry','region_selects_axis')
    for name,native,record in pins:
        row={'name':name,'path':str(source/name/(name+'.SLDPRT')),'sha256':native,
            'native_record':str(source/name/(name+'.reopen.json')),'native_record_sha256':record}
        modes=('truth','presentation_cache',*negative) if name=='RevolvePartialForward' else ('truth',)
        for mode in modes:jobs.append({'input':row,'mode':mode})
    args.output.mkdir(parents=True,exist_ok=False)
    def run(job):
        result=subprocess.run([sys.executable,'-B',str(root/'AuditRevolveSemantics02.py'),'--root',str(root)],
            input=dumps(job),text=True,capture_output=True,timeout=40)
        name=job['input']['name']+'-'+job['mode']
        record={'name':name,'exit':result.returncode,'stderr':result.stderr}
        if result.stdout:
            try:record['result']=loads(result.stdout)
            except ValueError:record['stdout']=result.stdout
        record['passed']=result.returncode==0 and record.get('result',{}).get('passed',False)
        (args.output/(name+'.json')).write_text(dumps(record,indent=2,sort_keys=True)+'\n')
        return record
    with ThreadPoolExecutor(max_workers=4) as pool:records=list(pool.map(run,jobs))
    result={'schema':'kit.sw2026.revolve-semantic-process-proof.v1','passed':all(row['passed'] for row in records),
        'processes':len(records),'truth_cases':3,'negative_variants':len(negative),'presentation_variant':1,
        'native_geometry_numeric_checks':sum(row.get('result',{}).get('native_geometry_numeric_checks',0) for row in records),
        'source_manifest_sha256':sha256((root/'BaselineSource01.json').read_bytes()).hexdigest(),
        'tools_sha256':{name:sha256((root/name).read_bytes()).hexdigest() for name in ('ReadOrdinaryRevolve01.py','AuditRevolveSemantics02.py','RunRevolveSemantics02.py')},
        'heldout_inputs_read':0,'native_processes_started':0,'sdk_source_changed':False,
        'records':{row['name']:{'passed':row['passed'],'sha256':sha256((args.output/(row['name']+'.json')).read_bytes()).hexdigest(),
            'exit':row['exit']} for row in records}}
    target=args.output/'Proof.json'
    target.write_text(dumps(result,indent=2,sort_keys=True)+'\n')
    print(dumps({'passed':result['passed'],'processes':result['processes'],'output':str(target),
        'sha256':sha256(target.read_bytes()).hexdigest(),'failed':[row['name'] for row in records if not row['passed']]}))
    raise SystemExit(0 if result['passed'] else 3)


if __name__=='__main__':main()
