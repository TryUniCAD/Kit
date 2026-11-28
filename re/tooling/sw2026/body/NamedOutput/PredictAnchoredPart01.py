from copy import deepcopy
from math import isclose

from PredictNamedOutput01 import prediction as base_prediction


def prediction(build, source_case, role):
    if role not in ('width', 'height', 'depth') or build['anchor_kind'] != source_case['anchor_kind']:
        raise ValueError('native anchored prediction needs an explicit supported family and edit role')
    value = base_prediction(build)
    intent = value['intent']
    if len(intent['drivers']) != 3 or build['driver_names'] != source_case['driver_names']:
        raise ValueError('native anchored prediction needs all three actual authored drivers')
    kind = source_case['anchor_kind']
    width, height, depth = (build['spec'][key] * 0.001 for key in ('width_mm', 'height_mm', 'depth_mm'))
    center = [width / 2, height / 2] if kind == 'corner' else [0.0, 0.0]
    if build['spec'] != source_case['part'] or not all(isclose(actual,expected*1000,rel_tol=1e-12,abs_tol=1e-12) for actual,expected in zip(build['spec']['centre_xy_mm'],center,strict=True)):
        raise ValueError('native anchor placement differs from its independently authored intent')
    expected_graph = {'kind':kind,'point_count':5 if kind=='corner' else 6,
        'line_count':4 if kind=='corner' else 6,'boundary_points':4,'boundary_lines':4,
        'construction_diagonals':0 if kind=='corner' else 2,'coincidence_count':1 if kind=='corner' else 3,
        'point_distance_drivers':2,'axis_relations':4,'actual_model_origin_bound':True,
        'distinct_external_local_handles':True,'actual_body_contour_preserved':True,
        'all_three_driver_owners_preserved':True}
    if build['anchor_graph'] != expected_graph:
        raise ValueError('generated archive does not contain the complete requested anchor ownership')
    lengths = {'width':width,'height':height,'depth':depth}
    edited = deepcopy(lengths)
    edited[role] = source_case['independent_edits_mm'][role] * 0.001
    if edited[role] == lengths[role] or not 0.001 < edited[role] < 0.2:
        raise ValueError('the independent anchored edit must change the selected driver')
    w,h,d = (edited[key] for key in ('width','height','depth'))
    centroid = [w / 2,h / 2,d / 2] if kind=='corner' else [0.0,0.0,d / 2]
    selected = next(row for row in intent['drivers'] if row['role']==role)
    value['edit'] = {'dimension':selected['reference'],'role':role,'new_value_m':edited[role],
        'new_depth_m':edited[role],
        'expected':{'body_count':1,'volume_m3':w*h*d,'area_m2':2*(w*h+w*d+h*d),
                    'mass_kg':w*h*d,'centre_of_mass_m':centroid}}
    value['initial_dimensions_m'] = lengths
    value['edited_dimensions_m'] = edited
    intent.update(anchor_kind=kind,origin_name='Origin',relation_count=7 if kind=='corner' else 9,
        construction_diagonals=0 if kind=='corner' else 2,sketch_lines=4 if kind=='corner' else 6)
    return value
