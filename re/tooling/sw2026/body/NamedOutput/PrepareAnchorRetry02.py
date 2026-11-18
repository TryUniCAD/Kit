from argparse import ArgumentParser
from hashlib import sha256
from json import dumps,loads
from pathlib import Path
from shutil import copyfile


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    parser=ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--prior-corner-result',type=Path,required=True)
    args=parser.parse_args()
    root=args.root.resolve(strict=True)
    prior=root/'NativePacket01'
    if digest(prior/'Trial.json')!='e7c0cdf57d3bfbc7b8c2bd18a7e78e4e2de1cd0c3127c4d99c6395de254b74cb':
        raise ValueError('exact anchored native predecessor packet differs')
    result=prior/'Inspection/Result.json'
    if digest(result)!='e402c2967320c0309e8d02b0eb90a290e3220c17c429e633b43429b35b185895':
        raise ValueError('exact retained anchored native failure differs')
    failed=loads(result.read_bytes())
    job=loads((prior/'Trial.json').read_bytes())
    if failed['passed'] or not failed['controls_healthy'] or failed['distinct_processes']!=4 or not failed['frozen_inputs_unchanged']:
        raise ValueError('predecessor is not the healthy controlled observer failure')
    if digest(args.prior_corner_result)!='a230f247f6d5db4c423303ef52d4cbe1ee0450cbd40eb92ebcfb9770ce3919c6':
        raise ValueError('independent prior corner qualification differs')
    older=loads(args.prior_corner_result.read_bytes())
    observed=[]
    for edit in older['edits']:
        for phase in ('edit','reopen'):
            for label,state in edit[phase]['states'].items():
                if state['sketch_parents']!=['Front Plane','Origin'] or state['boss_parents']!=['Sketch1','Front Plane','Origin']:
                    raise ValueError('prior native ownership does not independently support the declared dependency rule')
                observed.append({'phase':phase,'state':label,'profile':'Sketch1','sketch_parents':state['sketch_parents'],'boss_parents':state['boss_parents']})
    if not older['passed'] or not older['controls_healthy'] or len(observed)!=15:
        raise ValueError('the prior corner lifecycle is not complete and controlled')
    for name,wanted in job['inputs_sha256'].items():
        if digest(prior/name)!=wanted:
            raise ValueError('original native input changed: '+name)
    for name,wanted in job['tools_sha256'].items():
        if digest(prior/'Tools'/name)!=wanted:
            raise ValueError('original native observer changed: '+name)
    args.output.mkdir(parents=True,exist_ok=False)
    tools=args.output/'Tools'
    tools.mkdir()
    for name in job['inputs_sha256']:
        copyfile(prior/name,args.output/name)
    for name in job['tools_sha256']:
        if name!='InspectAnchorBody01.py':
            copyfile(prior/'Tools'/name,tools/name)
    copyfile(root/'InspectAnchorBody02.py',tools/'InspectAnchorBody02.py')
    copyfile(prior/'Trial.json',args.output/'PriorTrial01.json')
    copyfile(result,args.output/'FailedResult01.json')
    copyfile(prior/'Tools/InspectAnchorBody01.py',args.output/'PriorObserver01.py')
    evidence={'schema':'kit.sw2026.anchored-origin-parent-evidence.v1',
        'independent_prior_native_report_sha256':digest(args.prior_corner_result),
        'prior_qualified_processes':8,'prior_measured_states':15,'prior_states':observed,
        'native_failed_report_sha256':digest(result),'source_graph_rule':'profile_support_then_actual_external_origin_boss_profile_then_those_supports',
        'correction':'require_the_actual_declared_origin_in_both_exact_parent_lists',
        'source_method_or_generated_bytes_changed':False,'heldout_inputs_read':0}
    (args.output/'DependencyEvidence01.json').write_text(dumps(evidence,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
    job['tools_sha256']={path.name:digest(path) for path in tools.iterdir()}
    job['inputs_sha256']={path.name:digest(path) for path in args.output.iterdir() if path.is_file()}
    job.update(observer_revision=2,observer_only_dependency_correction=True,
        predecessor_failed_report_sha256=digest(result),predecessor_native_trial_sha256=digest(prior/'Trial.json'))
    path=args.output/'Trial.json'
    path.write_text(dumps(job,indent=2,ensure_ascii=True,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
    print(dumps({'path':str(path),'sha256':digest(path),'source_method_and_bytes_unchanged':True,'expected_native_processes':16},sort_keys=True))


if __name__=='__main__':
    main()
