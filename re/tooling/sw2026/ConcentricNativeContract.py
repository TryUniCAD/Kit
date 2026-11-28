from hashlib import sha256
import json
import math
from pathlib import Path

SCHEMA='kit.sw2026.generated-concentric-native.v1'
ORACLE='3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe'
ROLES=('ControlBefore','Generated','Reopen','ControlAfter')


def require(value,message):
    if not value:
        raise ValueError(message)


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def write_json(path,value):
    path=Path(path)
    temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n')
    temporary.replace(path)


def checked(path,wanted):
    path=Path(path)
    require(path.is_file() and not path.is_symlink() and digest(path)==wanted,'a frozen concentric observer input changed: '+path.name)
    return path


def close_numbers(actual,expected,relative=2e-7,absolute=1e-12):
    return len(actual)==len(expected) and all(type(value) in (int,float) and math.isfinite(value)
        and math.isclose(value,target,rel_tol=relative,abs_tol=absolute) for value,target in zip(actual,expected,strict=True))


def world(matrix,point):
    return [sum(point[row]*matrix[row*3+column] for row in range(3))+matrix[9+column] for column in range(3)]


def geometric_prediction(radius,center,depth,transforms):
    local=[*center,depth/2]
    volume=math.pi*radius*radius*depth
    area=2*math.pi*radius*(radius+depth)
    points=[world(matrix,local) for matrix in transforms]
    return {'child':{'volume':volume,'area':area,'com':local},
            'assembly':{'volume':2*volume,'area':2*area,'com':[sum(point[index] for point in points)/2 for index in range(3)]}}


def validate_prediction(row):
    require(len(row['occurrences'])==2 and len({value['name'] for value in row['occurrences']})==2,'expected exactly two named occurrences')
    require(type(row['fixed_index']) is int and row['fixed_index'] in (0,1),'expected one exact fixed occurrence')
    require(sorted(row['endpoint_indexes'])==[0,1] and all(type(value) is int for value in row['endpoint_indexes']),'endpoint order is incomplete')
    require(type(row['rotation_locked']) is bool and type(row['api_alignment']) is int and row['api_alignment'] in (0,1),'mate intent is incomplete')
    require(row['radius_m']>0 and row['depth_m']>0 and row['edited_depth_m']>0 and row['depth_m']!=row['edited_depth_m'],'depth edit must be real and positive')
    matrices=[value['transform'] for value in row['occurrences']]
    for matrix in matrices:
        require(len(matrix)==16 and matrix[12:]==[1.0,0.0,0.0,0.0] and all(math.isfinite(value) for value in matrix),'invalid authored native transform')
        axes=[matrix[index:index+3] for index in (0,3,6)]
        require(all(math.isclose(sum(a*b for a,b in zip(axes[first],axes[second],strict=True)),float(first==second),abs_tol=1e-12,rel_tol=1e-10)
            for first in range(3) for second in range(3)),'authored occurrence is not rigid')
        determinant=sum(axes[0][index]*(axes[1][(index+1)%3]*axes[2][(index+2)%3]-axes[1][(index+2)%3]*axes[2][(index+1)%3]) for index in range(3))
        require(math.isclose(determinant,1.0,rel_tol=1e-10,abs_tol=1e-12),'authored occurrence is reflected')
    for edited,key in ((False,'initial'),(True,'edited')):
        depth=row['edited_depth_m'] if edited else row['depth_m']
        expected=geometric_prediction(row['radius_m'],row['center_m'],depth,matrices)
        for role in ('child','assembly'):
            require(close_numbers([*row[key][role]['com'],row[key][role]['volume'],row[key][role]['area']],
                [*expected[role]['com'],expected[role]['volume'],expected[role]['area']],relative=1e-12,absolute=1e-15),'frozen independent geometry differs')
    return row


def signature(state):
    return {'tree':state['tree'],'child_tree':state['child_tree'],'body_count':state['body_count'],
        'occurrences':[{key:row[key] for key in ('name','native_id','configuration','fixed','visible_child_bodies')} for row in state['occurrences']],
        'mate':{key:state['mate'][key] for key in ('name','type','native_feature_id','alignment','rotation_locked')}|
            {'ordered_endpoints':[{key:row[key] for key in ('occurrence','occurrence_native_id','selection_type','surface_kind')} for row in state['mate']['ordered_endpoints']]}}


def state_matches(state,prediction,edited=False):
    validate_prediction(prediction)
    require(state['body_count']==2 and state['configurations']==[prediction['parent_configuration'],prediction['child_configuration']],'native document configuration or body count differs')
    for field,expected in (('tree',prediction['tree']),('child_tree',prediction['child_tree'])):
        rows=state[field]
        require([[row['name'],row['type'],row['parent']] for row in rows]==expected,'complete native feature tree differs')
        require(all(row['error']==0 and row['warning'] is False and row['suppressed'] is False for row in rows),'native feature has an error warning or suppression')
    require(state['diagnostic_counts']=={'child':0,'assembly':0},'native document has warnings or errors')
    expected_geometry=prediction['edited' if edited else 'initial']
    for role in ('child','assembly'):
        observed=state['mass'][role];expected=expected_geometry[role]
        require(close_numbers([observed['volume'],observed['area']],[expected['volume'],expected['area']],absolute=1e-15) and close_numbers(observed['com'],expected['com']),'native measured geometry differs from the independent model')
    for index,(actual,expected) in enumerate(zip(state['occurrences'],prediction['occurrences'],strict=True)):
        require(actual['name']==expected['name'] and actual['configuration']==prediction['child_configuration']
            and actual['fixed'] is (index==prediction['fixed_index']) and actual['visible_child_bodies']==1,'actual occurrence ownership or fixed state differs')
        require(close_numbers(actual['transform'],expected['transform'],relative=1e-9,absolute=1e-12),'actual rigid placement differs from the authored matrix')
    require(len({row['native_id'] for row in state['occurrences']})==2,'native occurrence identities collide')
    wanted_depth=prediction['edited_depth_m'] if edited else prediction['depth_m']
    wanted_parameters={prediction['radial_parameter']:prediction['radial_value_m'],prediction['depth_parameter']:wanted_depth}
    require(set(state['dimensions_m'])==set(wanted_parameters) and all(close_numbers([state['dimensions_m'][name]],[value]) for name,value in wanted_parameters.items()),'native driving dimensions differ')
    mate=state['mate']
    require((mate['name'],mate['type'],mate['alignment'],mate['rotation_locked'])==
            (prediction['mate_name'],1,prediction['api_alignment'],prediction['rotation_locked']),'actual native mate intent differs')
    require([value['occurrence'] for value in mate['ordered_endpoints']]==[prediction['occurrences'][index]['name'] for index in prediction['endpoint_indexes']],'actual native endpoint order differs')
    for endpoint,index in zip(mate['ordered_endpoints'],prediction['endpoint_indexes'],strict=True):
        require(endpoint['occurrence_native_id']==state['occurrences'][index]['native_id'] and endpoint['selection_type']==2 and endpoint['surface_kind']=='cylinder','native face endpoint lost its actual occurrence identity')
        require(close_numbers([endpoint['radius_m']],[prediction['radius_m']]),'native selected radius differs')
        require(endpoint['object_evidence']['persist_reference_bytes']>0,'native face selection has no persistent owner evidence')
    require(mate['axis_parallel_residual']<1e-10 and mate['axis_distance_m']<1e-10,'native selected cylinders are not coaxial')
    return True


def summarize(job,records):
    result={'schema':SCHEMA,'passed':False,'cases':{},'native_acceptance':'pending','heldout_inputs_read':0}
    births=[]
    for name in job['cases']:
        phases=records.get(name,{})
        complete=set(phases)==set(ROLES) and all(value.get('passed') is True for value in phases.values())
        row={'all_phases_passed':complete,'controls_healthy':False,'identities_preserved':False,'chronology':False,'passed':False}
        if complete:
            before,generated,reopen,after=(phases[role] for role in ROLES)
            row['controls_healthy']=signature(before['rebuilt'])==signature(after['rebuilt'])
            row['identities_preserved']=(signature(generated['initial'])==signature(generated['rebuilt'])==signature(generated['relocated'])==signature(generated['edited'])==signature(reopen['initial'])==signature(reopen['rebuilt']))
            ordered_births=[value['oracle_identity']['process_creation_filetime'] for value in (before,generated,reopen,after)]
            row['chronology']=all(first<second for first,second in zip(ordered_births,ordered_births[1:]))
            row['passed']=bool(row['controls_healthy'] and row['chronology'] and row['identities_preserved'] and all(value.get('immutable_inputs_unchanged') is True for value in phases.values()))
        for value in phases.values():
            identity=value.get('oracle_identity',{})
            if identity.get('process_creation_filetime'):births.append(identity['process_creation_filetime'])
        result['cases'][name]=row
    result['distinct_native_processes']=len(set(births))
    result['passed']=bool(job['cases'] and all(value['passed'] for value in result['cases'].values()) and len(births)==len(set(births))==4*len(job['cases']))
    result['native_acceptance']='disclosed_generated_lifecycle_pass' if result['passed'] else 'incomplete_or_failed'
    return result
