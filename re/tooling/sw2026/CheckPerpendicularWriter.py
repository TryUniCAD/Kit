import argparse
from base64 import b64decode
from copy import deepcopy
from hashlib import sha256
from itertools import permutations
import json
from pathlib import Path
import subprocess
import sys


def digest(data):return sha256(data).hexdigest()


def require(value,message):
    if not value:raise ValueError(message)


def sources(root):
    return {p.relative_to(root).as_posix():digest(p.read_bytes()) for folder in ('src','tests','re/tooling/sw2026') for p in sorted((root/folder).rglob('*.py'))}


def run(root,script,request,out,tag,tools=False):
    target=Path(__file__).with_name(script) if tools else root/'re/tooling/sw2026'/script
    argv=[sys.executable,'-I','-B',str(target)]+(['--root',str(root)] if tools else [str(root)])
    data=json.dumps(request,separators=(',',':'),allow_nan=False).encode()
    (out/(tag+'.Request.json')).write_bytes(data)
    proc=subprocess.Popen(argv,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=root)
    try:stdout,stderr=proc.communicate(data,timeout=90)
    except subprocess.TimeoutExpired:
        proc.kill();stdout,stderr=proc.communicate();raise ValueError('owned SDK process timed out: '+tag)
    (out/(tag+'.stdout.json')).write_bytes(stdout);(out/(tag+'.stderr.txt')).write_bytes(stderr)
    return {'pid':proc.pid,'exit_code':proc.returncode,'stdout':stdout,'stderr':stderr,'input_sha256':digest(data)}


def build(root,request,out,tag,script='SdkPlanarGroupProcess.py'):
    proc=run(root,script,request,out,tag)
    require(proc['exit_code']==0,'complete SDK construction failed '+tag+': '+proc['stderr'].decode()[-1800:])
    value=json.loads(proc['stdout'])
    require(value['passed'] and value['runtime_input_file_reads']==value['sdk_runtime_research_imports']==0,
            'SDK construction read runtime input or imported research logic')
    return value,proc


def fault_cases(original):
    cases={}
    for name in ('Nonorthogonal','SameOccurrence','ExtraOccurrence','ExtraPerpendicular','MixedGroup','ScalarDistance','ExplicitAlignment','UnknownAxis','UnknownKind','MissingEndpoint','MissingAnchor','ScaleOption','Shear','WrongChildLength'):
        value=deepcopy(original)
        mate=value['mates'][0]
        if name=='Nonorthogonal':mate['endpoints'][1]['axis']=mate['endpoints'][0]['axis']
        elif name=='SameOccurrence':mate['endpoints'][1]['occurrence']=0
        elif name=='ExtraOccurrence':
            extra=deepcopy(value['occurrences'][1]);extra['name']+='Extra';value['occurrences'].append(extra)
        elif name in ('ExtraPerpendicular','MixedGroup'):
            extra=deepcopy(mate);extra['name']='ExtraMate'
            if name=='MixedGroup':extra['kind']='parallel';extra['endpoints'][1]['axis']=extra['endpoints'][0]['axis']
            value['mates'].append(extra)
        elif name=='ScalarDistance':mate['distance_m']=.02731
        elif name=='ExplicitAlignment':mate['alignment']='aligned'
        elif name=='UnknownAxis':mate['endpoints'][0]['axis']='a'
        elif name=='UnknownKind':mate['kind']='tangent'
        elif name=='MissingEndpoint':mate['endpoints'].pop()
        elif name=='MissingAnchor':value['fixed_occurrence']=2
        elif name=='ScaleOption':value['occurrences'][0]['scale']=1.25
        elif name=='Shear':value['occurrences'][0]['v']=list(value['occurrences'][0]['u'])
        elif name=='WrongChildLength':
            for parameter in value['child']['document']['parameters']['$tuple']:
                if parameter['id']=='parameter/width':parameter['value']['value']*=1.2
        cases[name]=value
    return cases


def signature(value):
    if 'documents' in value:
        return {name:{key:row[key] for key in ('kind','path','bytes','sha256','activity','direct_references','target_ids','streams')} for name,row in value['documents'].items()}
    return {role:{key:value[role][key] for key in ('bytes','sha256','stream_order','streams')} for role in ('assembly','child')}


def regression_requests(root):
    sys.path[:0]=[str(root),str(root/'src')]
    from tests.Convert.Solidworks.Research.Construction.Assembly.MakeAsmCase import MakeAsmCase
    from tests.Convert.Solidworks.Research.Construction.AssemblySets.MakeOrderCase import MakeOrderCase
    from tests.Convert.Solidworks.Research.Construction.PlanarGroups.GroupCaseInput import GroupCaseInput
    from tests.Convert.Solidworks.Research.Construction.Nesting.MakeNestedCase import MakeNestedCase

    result=[]
    for kind in ('coincident','parallel','distance'):
        for axis in 'xyz':
            for variant in (False,True):result.append(('Single'+kind+axis+str(int(variant)),'SdkAssemblyProcess.py',MakeAsmCase(kind,axis,variant)))
    for order in permutations(('coincident','parallel','distance')):
        for variant in (False,True):result.append(('Ordered'+''.join(word[0] for word in order)+str(int(variant)),'SdkOrderedAssemblyProcess.py',MakeOrderCase(order,variant)))
    for count in (2,3,5):
        for variant in (False,True):result.append(('Group'+str(count)+str(int(variant)),'SdkPlanarGroupProcess.py',GroupCaseInput(count,variant)))
    for mixed in (False,True):result.append(('Nested'+str(int(mixed)),'SdkNestedAssemblyProcess.py',MakeNestedCase(mixed,r'C:\KitPerpendicularRegression')))
    return result


def main():
    parser=argparse.ArgumentParser()
    for name in ('root','baseline-root','fixtures','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    require(not args.output.exists(),'use a fresh guarded writer proof directory')
    root,baseline=args.root.resolve(),args.baseline_root.resolve()
    current,before=sources(root),sources(baseline)
    tool_hashes={p.name:digest(p.read_bytes()) for p in sorted(Path(__file__).parent.glob('*.py'))}
    args.output.mkdir(parents=True)
    code_data=(json.dumps({'current':current,'baseline':before,'tools':tool_hashes},indent=2,sort_keys=True)+'\n').encode()
    (args.output/'SourceManifest.json').write_bytes(code_data)
    positives=[];pids=[]
    for case in ('G01','G02','G03','G04'):
        folder=args.fixtures/case
        request=json.loads((folder/'Request.json').read_bytes())
        first,one=build(root,request,args.output,case+'BuildA');second,two=build(root,request,args.output,case+'BuildB')
        a,b=dict(first),dict(second);a.pop('worker_pid');b.pop('worker_pid')
        require(a==b,'generated bytes or typed metadata vary across processes: '+case)
        target=args.output/case/'Generated';target.mkdir(parents=True)
        parent=target/Path(request['assembly']['output']['path_name'].replace('\\','/')).name
        child=target/Path(request['child']['settings']['output']['path_name'].replace('\\','/')).name
        parent.write_bytes(b64decode(first['assembly']['blob']));child.write_bytes(b64decode(first['child']['blob']))
        compare=run(root,'VerifyPerpendicularGraph.py',{'parent':str(parent),'child':str(child),'prediction':json.loads((folder/'Prediction.json').read_bytes())},args.output,case+'Readback',tools=True)
        require(compare['exit_code']==0,'independent typed graph prediction differs: '+compare['stderr'].decode()[-1700:])
        check=json.loads(compare['stdout']);require(check['passed'],'generated graph comparison failed')
        pids.extend((one['pid'],two['pid'],compare['pid']))
        positives.append({'case':case,'request_sha256':digest((folder/'Request.json').read_bytes()),'prediction_sha256':digest((folder/'Prediction.json').read_bytes()),
                          'assembly':{key:first['assembly'][key] for key in ('bytes','sha256','stream_order')},'child':{key:first['child'][key] for key in ('bytes','sha256','stream_order')},
                          'round_trips':first['round_trips']+second['round_trips'],'endpoints':first['endpoints'],'independent_readback':check,
                          'deterministic':True,'runtime_input_file_reads':0,'sdk_runtime_research_imports':0})
        print(json.dumps({'case':case,'generated':True,'typed_prediction_equal':True}),flush=True)
    negative=[]
    first_request=json.loads((args.fixtures/'G01/Request.json').read_bytes())
    for name,request in fault_cases(first_request).items():
        proc=run(root,'SdkPlanarGroupProcess.py',request,args.output,'Reject'+name)
        require(proc['exit_code']!=0 and not proc['stdout'] and b'ValueError' in proc['stderr'] and b'PermissionError' not in proc['stderr'],
                'unsupported perpendicular intent did not fail before output: '+name)
        pids.append(proc['pid']);negative.append({'case':name,'rejected':True,'writer_output_count':0,'diagnostic':proc['stderr'].decode().strip().splitlines()[-1]})
    regressions=[]
    for name,script,request in regression_requests(root):
        old,first=build(baseline,request,args.output,name+'Base',script);new,second=build(root,request,args.output,name+'Current',script)
        require(signature(old)==signature(new),'prior complete native bytes changed: '+name)
        pids.extend((first['pid'],second['pid']))
        regressions.append({'case':name,'script':script,'exact_complete_bundle_equal':True,'signature':{key:row['sha256'] for key,row in signature(new).items()}})
    require(len(pids)==len(set(pids)) and sources(root)==current and sources(baseline)==before
            and {p.name:digest(p.read_bytes()) for p in sorted(Path(__file__).parent.glob('*.py'))}==tool_hashes,'proof reused worker identities or changed frozen source')
    result={'schema':'kit.sw2026.perpendicular-sdk-writer-process-proof.v1','passed':True,'source_manifest_sha256':digest(code_data),
            'positive_cases':positives,'negative_cases':negative,'prior_bundles':regressions,'distinct_worker_count':len(pids),'worker_pids':pids,
            'runtime_input_file_reads':0,'sdk_runtime_research_imports':0,'heldout_inputs_read':False,'native_processes_started':0,
            'native_acceptance':False,'public_writer_qualified':False,'cold_source_reader_remains_solved_only':True}
    data=(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n').encode();(args.output/'WriterResults.json').write_bytes(data)
    print(json.dumps({'passed':True,'positives':len(positives),'negatives':len(negative),'prior_bundles':len(regressions),'workers':len(pids),'result_sha256':digest(data)}),flush=True)


if __name__=='__main__':main()
