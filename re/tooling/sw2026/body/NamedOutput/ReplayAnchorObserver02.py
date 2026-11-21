from argparse import ArgumentParser
from copy import deepcopy
from hashlib import sha256
from json import dumps,loads
from pathlib import Path
import sys


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    parser=ArgumentParser()
    parser.add_argument('--packet',type=Path,required=True)
    parser.add_argument('--packet-sha256',required=True)
    parser.add_argument('--failed-result',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    packet=args.packet.resolve(strict=True)
    sys.path.insert(0,str(packet.parent/'Tools'))
    import InspectAnchorBody02 as observer
    job=observer.verify(packet,args.packet_sha256)
    if digest(args.failed_result)!='e402c2967320c0309e8d02b0eb90a290e3220c17c429e633b43429b35b185895':
        raise ValueError('exact immutable native failed aggregate differs')
    raw=loads(args.failed_result.read_bytes())
    args.output.mkdir(parents=True,exist_ok=False)
    phases=[]
    for name in ('CornerAsciiPlain','CenterWidePlain'):
        native=raw['phases'][name]
        record_path=args.failed_result.parent/name/'Record.json'
        if digest(record_path)!=native['record_sha256']:
            raise ValueError('recorded complete native API observations differ')
        record=loads(record_path.read_bytes())
        if native['passed'] or native['open_errors'] or native['open_warnings'] or not native['immutable_bytes']:
            raise ValueError('replay source is not the exact zero-warning observer failure')
        if any('error' in call or 'exception' in call for call in record['api_calls']):
            raise ValueError('replay source contains an actual native API error')
        source=next(case for case in job['cases'] if name==case['name']+'Plain')
        predicted=deepcopy(source['predictions']['depth'])
        predicted['body_label']=predicted['intent']['feature']
        states=deepcopy(native['states'])
        recorder=observer.curves.Recorder(args.output/(name+'.json'),
            {'offline_only':True,'source_native_record_sha256':native['record_sha256'],
             'native_result_remains_failed':True,'packet_sha256':args.packet_sha256})
        recorder.data['result']={'states':states}
        tree=observer.part.tree_prediction(source['tree_request'],predicted)
        for label,state in states.items():
            observer.verify_state(recorder,state,predicted,tree,edited=False)
        recorder.data.update(passed=True,offline_only=True,native_processes_started=0,
            native_source_passed=False,numeric_check_count=len(recorder.data['checks']))
        recorder.flush()
        phases.append({'phase':name,'passed':True,'native_source_record_sha256':native['record_sha256'],
            'states':list(states),'api_calls_observed':len(record['api_calls']),
            'numeric_checks':len(recorder.data['checks']),'replay_record_sha256':digest(recorder.path),
            'native_source_numeric_checks':native['numeric_check_count']})
    result={'schema':'kit.sw2026.anchored-parent-observer-offline-replay.v1','passed':True,
        'native_failed_report_sha256':digest(args.failed_result),'native_source_remains_failed':True,
        'retry_trial_sha256':args.packet_sha256,'observer_sha256':digest(packet.parent/'Tools/InspectAnchorBody02.py'),
        'phases':phases,'recorded_candidate_states':sum(len(row['states']) for row in phases),
        'offline_numeric_checks':sum(row['numeric_checks'] for row in phases),
        'native_processes_started':0,'writer_changes':0,'heldout_inputs_read':0}
    path=args.output/'Replay.json'
    path.write_text(dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
    print(dumps({'passed':True,'sha256':digest(path),'offline_checks':result['offline_numeric_checks'],
        'recorded_states':result['recorded_candidate_states'],'native_processes_started':0},sort_keys=True))


if __name__=='__main__':
    main()
