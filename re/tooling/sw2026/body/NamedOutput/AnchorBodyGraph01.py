from collections import Counter
from math import isclose

from AuthorCurves import require


def close(first,last):
    return isclose(first,last,rel_tol=2e-7,abs_tol=1e-10)


def identity(value):
    require(type(value) is list and len(value)==2 and all(type(item) is int for item in value),
            'native anchor identity must retain both actual GetID components')
    return tuple(value)


def roles(geometry, lengths, kind, recorder):
    width,height = lengths['width'],lengths['height']
    left,bottom = (0.0,0.0) if kind=='corner' else (-width/2,-height/2)
    points = [(left,bottom),(left+width,bottom),(left+width,bottom+height),(left,bottom+height)]
    ordinary = [row for row in geometry if not row['construction']]
    construction = [row for row in geometry if row['construction']]
    require(len(ordinary)==4 and len(construction)==(0 if kind=='corner' else 2)
            and all(row['kind']=='line' for row in geometry),'native anchor has an extra missing or unsupported entity')
    line_ids,point_ids = [],[None]*4
    for index,(first,last) in enumerate(zip(points,points[1:]+points[:1],strict=True)):
        matches=[]
        for row in ordinary:
            for forward in (True,False):
                observed = (row['start'],row['end']) if forward else (row['end'],row['start'])
                if all(close(a,b) for actual,wanted in zip(observed,(first,last),strict=True) for a,b in zip(actual,wanted,strict=True)):
                    matches.append((row,forward))
        require(len(matches)==1,'native anchor boundary is missing or ambiguous')
        row,forward=matches[0]
        line_ids.append(identity(row['id']))
        sides=('start','end') if forward else ('end','start')
        for ordinal,side,expected in ((index,sides[0],first),((index+1)%4,sides[1],last)):
            point_id=identity(row['point_bindings'][side]['id'])
            require(point_ids[ordinal] in (None,point_id),'native anchor incident lines lost their actual common point')
            point_ids[ordinal]=point_id
            for actual,target in zip(row[side],expected,strict=True):
                recorder.close_number('independent anchored coordinate',actual,target,absolute=1e-10)
    require(len(set(line_ids))==len(set(point_ids))==4,'native anchor boundary identities are not distinct')
    diagonal_ids=[]
    if kind=='center':
        for index in range(2):
            endpoints={point_ids[index],point_ids[index+2]}
            candidates=[row for row in construction if {identity(row['point_bindings'][side]['id']) for side in ('start','end')}==endpoints]
            require(len(candidates)==1,'native construction diagonal lost its actual opposite contour endpoints')
            row=candidates[0]
            diagonal_ids.append(identity(row['id']))
            for side in ('start','end'):
                ordinal=point_ids.index(identity(row['point_bindings'][side]['id']))
                for actual,target in zip(row[side],points[ordinal],strict=True):
                    recorder.close_number('independent construction diagonal coordinate',actual,target,absolute=1e-10)
        require(len(set(diagonal_ids))==2 and not set(diagonal_ids)&set(line_ids),'native diagonals share an unrelated segment identity')
    return {'boundary_lines':[list(value) for value in line_ids],
            'boundary_points':[list(value) for value in point_ids],
            'diagonals':[list(value) for value in diagonal_ids]}


def check_relations(rows, role_map, drivers, lengths, kind, recorder):
    expected=Counter()
    for index,value in enumerate(role_map['boundary_lines']):
        expected[(4 if index%2==0 else 5,(identity(value),),None)]+=1
    for index,driver in enumerate(drivers[:2]):
        expected[(1,tuple(sorted(identity(value) for value in role_map['boundary_points'][index:index+2])),driver['reference'])]+=1
    actual=Counter()
    point_line=[]
    point_point=[]
    for row in rows:
        require(not row['suppressed'] and len(row['entity_types'])==len(row['entity_ids']),
                'native anchor relation is suppressed or lacks actual entities')
        if row['kind']==9:
            require(row['dimension'] is None,'coincidence acquired an unrelated display dimension')
            if sorted(row['entity_types'])==[2,3]:
                point_line.append(row)
            elif row['entity_types']==[2,2]:
                point_point.append(row)
            else:
                raise ValueError('native origin coincidence has an unsupported entity ownership domain')
            continue
        dimension=row['dimension']
        name=None if dimension is None else dimension['reference']
        actual[(row['kind'],tuple(sorted(identity(value) for value in row['entity_ids'])),name)]+=1
        if row['kind']==1:
            require(row['entity_types']==[2,2] and dimension is not None and dimension['driving'],
                    'native length lost its actual editable point distance owner')
            driver=next(value for value in drivers if value['reference']==name)
            recorder.close_number('native relation driver',dimension['value_m'],lengths[driver['role']])
        else:
            require(row['kind'] in (4,5) and row['entity_types']==[3] and dimension is None,
                    'native unary axis relation has an unsupported concrete owner')
    require(actual==expected and len(point_point)==1 and len(point_line)==(0 if kind=='corner' else 2),
            'native anchor relations differ from the complete declared owner inventory')
    anchor,=point_point
    point_values=anchor['point_owners']
    external=[point for point in point_values if point['type']==10]
    require(len(external)==1,'origin coincidence lacks its actual external point')
    external=external[0]
    local,=[point for point in point_values if point is not external]
    for point in (external,local):
        require(not point['owner_null'] and point['same_self_raw']==point['owner_same_self_raw']==point['owner_same_profile_raw']==1
                and point['same_origin_raw']==point['owner_same_origin_raw']==0
                and all(close(value,0.0) for value in point['position_m']),
                'origin coincidence collapsed actual local and external point ownership')
    local_id,external_id=identity(local['id']),identity(external['id'])
    require(local_id!=external_id and external_id not in {identity(value) for value in role_map['boundary_points']},
            'external origin reused a local boundary point identity')
    if kind=='corner':
        require(local_id==identity(role_map['boundary_points'][0]) and local['type']==0,
                'corner origin relation lost the actual selected boundary corner')
    else:
        require(local_id not in {identity(value) for value in role_map['boundary_points']},
                'center origin relation references a boundary corner')
        observed=[]
        for row in point_line:
            point_index=row['entity_types'].index(2)
            line_index=row['entity_types'].index(3)
            require(identity(row['entity_ids'][point_index])==local_id,
                    'center diagonal coincidence lost the same actual center point')
            observed.append(identity(row['entity_ids'][line_index]))
            point,=row['point_owners']
            require(point['owner_same_profile_raw']==point['owner_same_self_raw']==point['same_self_raw']==1
                    and point['owner_same_origin_raw']==point['same_origin_raw']==0
                    and all(close(value,0.0) for value in point['position_m']),
                    'diagonal center point lost its actual user sketch ownership')
        require(sorted(observed)==sorted(identity(value) for value in role_map['diagonals']),
                'center point is not constrained by both real construction diagonals')
    return {'local_anchor':list(local_id),'external_origin':list(external_id)}
