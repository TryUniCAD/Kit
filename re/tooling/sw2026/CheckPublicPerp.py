import argparse
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys


def require(value,message):
    if not value:raise ValueError(message)


def sources(root):
    return {p.relative_to(root).as_posix():sha256(p.read_bytes()).hexdigest()
            for area in ('src','tests','re/tooling/sw2026') for p in sorted((root/area).rglob('*.py'))}


def invoke(code,tool,request,folder,tag):
    incoming=json.dumps(request,separators=(',',':'),allow_nan=False).encode()
    result=subprocess.Popen([sys.executable,'-I','-B',str(tool),str(code)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    stdout,stderr=result.communicate(incoming,timeout=180)
    (folder/(tag+'.stdin.json')).write_bytes(incoming);(folder/(tag+'.stdout.json')).write_bytes(stdout);(folder/(tag+'.stderr.txt')).write_bytes(stderr)
    require(result.returncode==0,'actual registry process failed '+tag+': '+stderr.decode()[-2000:])
    value=json.loads(stdout);require(value['passed'],'registry proof did not pass '+tag)
    return {'tag':tag,'pid':result.pid,'result':value,'stdout_sha256':sha256(stdout).hexdigest()}


def main():
    parser=argparse.ArgumentParser()
    for name in ('candidate','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();base=args.candidate.resolve(strict=True);out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    code,baseline=base/'CodeRoot01',base/'BaselineRoot01'
    before=sources(code);older=sources(baseline)
    tools={p.name:sha256(p.read_bytes()).hexdigest() for p in sorted(Path(__file__).parent.glob('*.py'))}
    manifest={'candidate':before,'baseline':older,'tools':tools,'fixtures':{p.name:sha256(p.read_bytes()).hexdigest() for p in sorted((base/'Fixtures01').glob('*.json'))}}
    data=(json.dumps(manifest,indent=2,sort_keys=True)+'\n').encode();(out/'SourceManifest.json').write_bytes(data)
    cases=json.loads((base/'Fixtures01/Inputs.json').read_bytes())['cases']
    jobs=[]
    for case in cases:
        original=json.loads((base/'Fixtures01'/case['file']).read_bytes())
        formats=(None,'solidworks.sldasm') if case['case'] in ('G01','G04') else (None,)
        for fmt in formats:
            tag=case['case']+('Explicit' if fmt else 'Default')
            request=dict(original,output=str(out/tag),format_id=fmt,allow_unqualified=not original['expected_reject'])
            jobs.append((tag,request))
    strict=json.loads((base/'Fixtures01/G01.json').read_bytes())
    strict.update(output=str(out/'StrictDefault'),expected_policy_reject=True,allow_unqualified=False)
    jobs.append(('StrictDefault',strict))
    def work(job):
        tag,request=job
        value=invoke(code,Path(__file__).with_name('RunPerpRegistry.py'),request,out,tag)
        print(json.dumps({'case':tag,'passed':True}),flush=True)
        return value
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(work,jobs))
    indexed={row['tag']:row['result'] for row in results}
    for case in ('G01','G04'):
        require(indexed[case+'Default']['artifacts']==indexed[case+'Explicit']['artifacts'],'default and explicit format selected different native bytes')
    require(indexed['G01Default']['artifacts']==indexed['ReorderedEntitiesDefault']['artifacts'],
            'storage entity order changed the explicit closed-loop primary geometry')
    regressions=[]
    for count in (2,3):
        prior=[]
        for label,root in (('Baseline',baseline),('Candidate',code)):
            tag='Prior'+str(count)+label
            target=out/tag
            process=subprocess.Popen([sys.executable,'-I','-B',str(root/'re/tooling/sw2026/PublicAssemblyRegistryProcess.py'),str(root),'fresh',str(count),str(target)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            stdout,stderr=process.communicate(timeout=180)
            (out/(tag+'.stdout.json')).write_bytes(stdout);(out/(tag+'.stderr.txt')).write_bytes(stderr)
            require(process.returncode==0,'the existing aligned public bundle regressed: '+stderr.decode()[-1500:])
            value=json.loads(stdout);require(value['passed'] and value['writer_native_flags'],'an earlier public profile lost its qualified metadata')
            prior.append({'pid':process.pid,'bundle':value['after'],'stdout_sha256':sha256(stdout).hexdigest()})
        require(prior[0]['bundle']==prior[1]['bundle'],'an earlier aligned complete public bundle changed bytes')
        regressions.append({'occurrences':count,'complete_native_bundle_equal':True,'qualified_metadata_preserved':True,'processes':prior})
    pids=[row['pid'] for row in results]+[item['pid'] for row in regressions for item in row['processes']]
    require(len(pids)==len(set(pids)) and sources(code)==before and sources(baseline)==older and
            {p.name:sha256(p.read_bytes()).hexdigest() for p in sorted(Path(__file__).parent.glob('*.py'))}==tools,
            'source or process identity changed during the registry proof')
    receipt={'schema':'kit.sw2026.private-public-perpendicular-registry-proof.v1','passed':True,'source_manifest_sha256':sha256(data).hexdigest(),
             'distinct_process_count':len(pids),'registry_cases':results,'prior_public_regressions':regressions,
             'default_explicit_complete_bytes_equal':True,'ordered_primary_geometry_preserved':True,'strict_default_rejects_unqualified_output':True,
             'research_opt_in_emits_no_carrier_capabilities_or_payload':True,'runtime_input_file_reads':0,'native_processes_started':0,
             'hidden_values_used':False,'shared_registry_changed':False,'public_native_qualification':False,'vendor_flags_for_new_profile':False}
    data=(json.dumps(receipt,indent=2,sort_keys=True,allow_nan=False)+'\n').encode();(out/'RegistryProof.json').write_bytes(data)
    print(json.dumps({'passed':True,'distinct_process_count':len(pids),'result_sha256':sha256(data).hexdigest(),
                      'runtime_input_file_reads':0,'native_processes_started':0,'public_native_qualification':False},sort_keys=True),flush=True)


if __name__=='__main__':main()
