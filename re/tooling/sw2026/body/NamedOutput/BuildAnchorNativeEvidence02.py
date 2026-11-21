from argparse import ArgumentParser
from hashlib import sha256
from json import dumps,loads
from math import isclose
from pathlib import Path


RAW='458374829202dbb1b298c0948e9e5308a69aa72618d8c9b6dab808c922eb89ae'
TRIAL='542de0e34ace2fb574d112302fb57c71302781fcbb81fb39f1ef9be2812af9fc'
TRANSPORT='0f5986dbfcb47bd7f4fe7e29745a0aee23929a1c5aaa9a9a6925fe19b99e56ec'
FAILED='e402c2967320c0309e8d02b0eb90a290e3220c17c429e633b43429b35b185895'


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def load(path,expected):
    if digest(path)!=expected:
        raise ValueError('exact native evidence custody differs: '+path.name)
    return loads(path.read_bytes())


def close(actual,wanted):
    if not isclose(actual,wanted,rel_tol=2e-7,abs_tol=1e-12):
        raise ValueError('recorded native value differs from the pre-run independent model')


def main():
    parser=ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    root=args.root.resolve(strict=True)
    raw=load(root/'NativePacket02/Inspection/Result.json',RAW)
    job=load(root/'NativePacket02/Trial.json',TRIAL)
    transport=load(root/'NativeTransport02/Result.json',TRANSPORT)
    prior=load(root/'NativePacket01/Inspection/Result.json',FAILED)
    if not raw['passed'] or not raw['controls_healthy'] or not raw['frozen_inputs_unchanged'] or raw['distinct_processes']!=16 or not transport['passed'] or transport['transport_exit']!=0:
        raise ValueError('the complete controlled native lifecycle is not qualified')
    if prior['passed'] or not prior['controls_healthy'] or prior['distinct_processes']!=4:
        raise ValueError('the original controlled false outcome was not preserved')
    phases={}
    identities=set()
    numeric=states=saves=0
    for name,phase in raw['phases'].items():
        identity=phase['oracle_identity']
        if not phase['passed'] or not identity['version_matches'] or identity['sha256']!=job['oracle_sha256']:
            raise ValueError('native phase or process identity differs')
        key=(identity['process_id'],identity['process_creation_filetime'])
        if key in identities:
            raise ValueError('native phases reused an application process')
        identities.add(key)
        journal=load(root/'NativePacket02/Inspection'/name/'Record.json',phase['record_sha256'])
        summary={'passed':True,'record_sha256':phase['record_sha256'],
            'oracle_identity':{key:identity[key] for key in ('process_id','process_creation_filetime','sha256','file_version','pe_machine','version_matches')}}
        if name.startswith('Control'):
            if not journal['opened'] or not journal['rebuilt'] or journal['open_errors'] or journal['open_warnings'] or journal['whats_wrong'] or journal['bodies']!=1:
                raise ValueError('pristine native control differs')
            summary.update({key:journal[key] for key in ('opened','rebuilt','open_errors','open_warnings','whats_wrong','bodies','mass')})
            phases[name]=summary
            continue
        case=next(case for case in job['cases'] if name.startswith(case['name']))
        role=next((role for role in ('width','height','depth') if role.title() in name),'depth')
        predicted=case['predictions'][role]
        if phase['open_errors'] or phase['open_warnings'] or not phase['immutable_bytes'] or any(phase[key] for key in ('controller_diagnostics','dialogs','progress_windows')) or journal['first_failure'] is not None or journal['cleanup_errors']:
            raise ValueError('native open immutability or cleanup differs')
        value_states={}
        for label,state in phase['states'].items():
            edited=label=='Edited' or name.endswith('Reopen')
            target=predicted['edit']['expected'] if edited else predicted['expected_initial']
            lengths=predicted['edited_dimensions_m'] if edited else predicted['initial_dimensions_m']
            intent=predicted['intent']
            expected_name=intent['feature'] if name.endswith('Plain') else predicted['body_label']
            if state['native_body_name']!=expected_name or state['body_count']!=1 or state['complete_solid_count']!=1 or state['native_body_type']!=0 or state['constraint_status']!=3 or state['whats_wrong']!=0 or state['topology']!={'faces':6,'edges':12,'vertices':8}:
                raise ValueError('actual native body label topology or solver state differs')
            if state['sketch_parents']!=[intent['support'],intent['origin_name']] or state['boss_parents']!=[intent['profile'],intent['support'],intent['origin_name']]:
                raise ValueError('actual native anchor dependency differs')
            if len(state['tree'])!=25 or any(row['error'] or row['warning'] or row['suppressed'] for row in state['tree']):
                raise ValueError('native tree or feature diagnostics differ')
            for actual,expected in zip(state['actual_drivers'],intent['drivers'],strict=True):
                if actual['reference']!=expected['reference'] or actual['name']!=expected['name'] or not actual['driving']:
                    raise ValueError('actual native driving owner differs')
                close(actual['value_m'],lengths[expected['role']])
            for measured,wanted in (('volume','volume_m3'),('area','area_m2'),('mass','mass_kg')):
                close(state['mass'][measured],target[wanted])
            for actual,wanted in zip(state['mass']['com'],target['centre_of_mass_m'],strict=True):
                close(actual,wanted)
            fields=('configuration','sketch_parents','boss_parents','constraint_status','sketch_relation_count','dimension_m','dimension_driving','body_count','complete_solid_count','native_body_type','native_body_name','topology','mass','actual_drivers','actual_anchor_identity','whats_wrong')
            value_states[label]={key:state[key] for key in fields}|{'tree_rows':25,'tree_all_clean':True,
                'ordinary_lines':sum(not row['construction'] for row in state['sketch_geometry']),
                'construction_diagonals':sum(row['construction'] for row in state['sketch_geometry']),
                'relation_rows':len(state['relations'])}
            states+=1
        summary.update(states=value_states,numeric_check_count=phase['numeric_check_count'],open_errors=0,open_warnings=0,immutable_bytes=True,diagnostics_empty=True)
        numeric+=phase['numeric_check_count']
        if 'save_status' in phase:
            if phase['save_status']!=[True,0,0] or phase['edit_status']!=0:
                raise ValueError('native independent edit or save differs')
            derivative=root/'NativePacket02/Inspection'/name/'Edited.SLDPRT'
            if digest(derivative)!=phase['derivative_sha256']:
                raise ValueError('native saved derivative custody differs')
            summary.update({key:phase[key] for key in ('save_status','edit_status','derivative_sha256','derivative_bytes')})
            saves+=1
        phases[name]=summary
    if len(identities)!=16 or numeric!=1088 or states!=34 or saves!=6:
        raise ValueError('native phase state save or numeric totals differ')
    result={'schema':'kit.sw2026.sdk-anchored-named-native-measurement.v1','task_id':'B04-SW2026-ANCHORED-NAMED-PART','delivery_pr':121,
        'native_trial_passed':True,'native_report_sha256':RAW,'trial_sha256':TRIAL,'transport_result_sha256':TRANSPORT,
        'source_manifest_sha256':job['source_manifest_sha256'],'source_only_process_proof_sha256':job['process_proof_sha256'],
        'native_tools_sha256':job['tools_sha256'],'native_processes':16,'controls_healthy':True,'candidate_opens':14,
        'candidate_open_errors':0,'candidate_open_warnings':0,'numeric_checks':numeric,'measured_candidate_states':states,
        'independent_edits':['width','height','depth'],'clean_native_saves':6,'fresh_reopen_processes':6,
        'source_inputs_immutable':True,'sdk_source_changed_for_retry':False,'generated_inputs_changed_for_retry':False,
        'earlier_failure':{'native_report_sha256':FAILED,'passed':False,'processes':4,'controls_healthy':True,'numeric_checks':0,'named_candidate_opens':0,'cause':'observer_omitted_the_actual_origin_parent'},
        'qualified_scope':'two_disclosed_plain_and_named_corner_center_rectangles_only',
        'typed_anchor_policy_is_explicit_authored_constructor_input':True,'public_construction_registration_changed':False,
        'public_writer_enabled':False,'original_named_H_sources_remain_sealed':True,'original_source_qualification':False,
        'heldout_inputs_read':0,'writer_native_partition_generated':False,'document_density_preference_kg_m3':1000.0,
        'effective_unassigned_body_density_kg_m3':1.0,'phases':phases,
        'remaining':['complete_original_neutral_binding_and_pre_unseal_evaluator_freeze','original_source_native_comparison','public_preparation_and_registration']}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x',encoding='utf-8',newline='\n') as output:
        output.write(dumps(result,indent=2,sort_keys=True,ensure_ascii=True)+'\n')
    print(dumps({'path':str(args.output),'sha256':digest(args.output),'native_processes':16,'numeric_checks':numeric,'states':states},sort_keys=True))


if __name__=='__main__':
    main()
