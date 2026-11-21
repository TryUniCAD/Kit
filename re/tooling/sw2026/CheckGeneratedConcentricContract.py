import argparse
from copy import deepcopy
import json
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent))

from ConcentricNativeContract import checked,digest,require,state_matches,summarize,write_json


def replay(packet,expected,output):
    from InspectGeneratedConcentric import verify
    job=verify(packet,expected)
    results={};refusals=[]
    for name,case in job['cases'].items():
        prediction=json.loads((packet.parent/case['prediction_path']).read_bytes())['control']
        evidence=case['evidence']['SourceAuthor']
        source=json.loads(checked(packet.parent/evidence['path'],evidence['sha256']).read_bytes())['source']
        observed=deepcopy(source)
        observed['configurations']=[prediction['parent_configuration'],prediction['child_configuration']]
        observed['diagnostic_counts']={'child':0,'assembly':0}
        state_matches(observed,prediction)
        results[name]={'source_capture_sha256':evidence['sha256'],'passed':True,
            'added_context':'configuration and zero diagnostics were mandatory assertions in the frozen native source capture'}
        for change in ('warning','diagnostics','fixed','order','radius','volume','dimension','configuration','transform','tree'):
            bad=deepcopy(observed)
            if change=='warning':bad['tree'][-1]['warning']=True
            elif change=='diagnostics':bad['diagnostic_counts']['child']=1
            elif change=='fixed':bad['occurrences'][0]['fixed']=not bad['occurrences'][0]['fixed']
            elif change=='order':bad['mate']['ordered_endpoints'].reverse()
            elif change=='radius':bad['mate']['ordered_endpoints'][0]['radius_m']*=1.1
            elif change=='volume':bad['mass']['child']['volume']*=1.1
            elif change=='dimension':bad['dimensions_m'][prediction['depth_parameter']]*=1.1
            elif change=='configuration':bad['configurations'][1]='Wrong'
            elif change=='transform':bad['occurrences'][0]['transform'][9]+=.00473
            elif change=='tree':bad['child_tree'].pop()
            try:state_matches(bad,prediction)
            except (ValueError,TypeError,KeyError):refusals.append([name,change])
            else:raise ValueError('altered native observation accepted: '+name+' '+change)
    require(not summarize({'cases':{}},{})['passed'],'an empty native cohort must never pass')
    missing=summarize(job,{})
    require(not missing['passed'] and missing['distinct_native_processes']==0,'missing native phases must remain incomplete')
    for name,case in job['cases'].items():
        states={'ControlBefore':{'passed':False}}
        require(not summarize({'cases':{name:case}},{name:states})['passed'],'failed/partial controls must remain incomplete')
    result={'passed':True,'source_record_replays':len(results),'malformed_observation_refusals':len(refusals),
        'source_cases':results,'refusals':refusals,'missing_and_partial_phase_results_refused':True,
        'native_processes_started':0,'heldout_inputs_read':0,'new_native_acceptance':False,
        'packet_sha256':expected,'scope':'host-only contract replay of already disclosed native observations'}
    require(not output.exists(),'contract replay output exists')
    write_json(output,result)
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('packet',type=Path)
    parser.add_argument('--packet-sha256',required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=replay(args.packet.resolve(strict=True),args.packet_sha256,args.output)
    print(json.dumps({'passed':result['passed'],'native_processes_started':0,'result_sha256':digest(args.output)}))


if __name__=='__main__':main()
