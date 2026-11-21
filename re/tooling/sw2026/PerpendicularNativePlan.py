from copy import deepcopy
from math import isclose


PLANES = {'x': 'Right Plane', 'y': 'Top Plane', 'z': 'Front Plane'}


def require(value, message):
    if not value:
        raise ValueError(message)


def near(actual, expected):
    return len(actual) == len(expected) and all(isclose(a, b, rel_tol=1e-10, abs_tol=1e-12)
                                                for a, b in zip(actual, expected, strict=True))


def case_from_spec(spec):
    return {'id': spec['id'], 'name': spec['name'], 'split': 'discovery', 'child_name': spec['child_name'],
            'configuration': 'Default', 'fixed_occurrence': spec['fixed_occurrence'],
            'placements': deepcopy(spec['placements']), 'child_size_m': list(spec['size_m']),
            'edit_depth_m': spec['edit_depth_m'], 'edit_rotation_deg': spec['edit_rotation_deg'],
            'mate': {'kind': 'perpendicular', 'name': 'Perpendicular1', 'api_alignment': 0,
                     'planes': [[row['occurrence'], PLANES[row['axis']]] for row in spec['endpoints']]}}


def native_trees(request):
    from PrepareSdkAssemblyNative import tree_rows

    compatible = dict(request, mate={'name': request['mates'][0]['name']})
    result = tree_rows(compatible)
    require(result['parent'][-1][1] == 'MateDistanceDim', 'the existing native tree-role projection changed')
    result['parent'][-1][1] = 'MatePerpendicular'
    return result


def check_predictions(case, prediction):
    from PerpendicularSourcePlan import expected_transforms, geometry

    for edited, key in ((False, 'source'), (True, 'edited')):
        source = geometry(case, edited)
        target = prediction[key]
        for role in ('child', 'assembly'):
            require(near([source[role]['volume'], source[role]['area'], *source[role]['com']],
                         [target[role]['volume_m3'], target[role]['area_m2'], *target[role]['com_m']]),
                    'the independent predictors disagree about native geometry')
        require(all(near(actual, expected) for actual, expected in zip(expected_transforms(case, edited),
                    target['native_transforms'], strict=True)), 'the independent native transform predictions disagree')


def check_state(author, value, case, prediction, trees, identities, edited, same_code):
    from PerpendicularMateEvidence import signature

    expected = prediction['edited' if edited else 'source']
    require(value['body_count'] == 2, 'the generated assembly does not expose two bodies')
    for role, key in (('parent', 'tree'), ('child', 'child_tree')):
        rows = [[item['name'], item['type'], item['parent']] for item in value[key]]
        require(rows == trees[role] and all(not item['suppressed'] for item in value[key]),
                'the generated native feature tree differs from its authored roles')
    for role in ('child', 'assembly'):
        for source, target in (('volume', 'volume_m3'), ('area', 'area_m2')):
            author.rec.close_number('independent generated ' + role + ' ' + source,
                                    value['mass'][role][source], expected[role][target], absolute=1e-15)
        for index, (actual, wanted) in enumerate(zip(value['mass'][role]['com'], expected[role]['com_m'], strict=True)):
            author.rec.close_number('independent generated ' + role + ' centroid ' + str(index), actual, wanted)
    require(value['mate']['native_feature_id'] == identities['mate_id'] and value['mate']['alignment_observed'] == 2,
            'the generated mate ID or independently observed API alignment changed')
    owners = identities['endpoints']
    require([row['occurrence'] for row in value['mate']['ordered_endpoints']] ==
            [case['child_name'] + '-' + str(row['occurrence'] + 1) for row in owners],
            'the generated mate lost its declared ordered occurrence ownership')
    for actual, identity, target in zip(value['mate']['ordered_endpoints'], owners, expected['ordered_endpoints'], strict=True):
        require(actual['occurrence_native_id'] == identity['occurrence_feature_id'] and
                actual['plane_native_id'] == identity['datum_id'] and actual['plane'] == identity['datum_name'] and
                near(actual['normal'], target['normal']) and near(actual['point'], target['point_m']),
                'the generated actual endpoint identity or independent plane geometry differs')
        require(all(actual['object_comparison'][key] == same_code for key in ('repeated_reference', 'repeated_specific')),
                'the native repeated reference control does not establish a stable object')
    require(near([value['dimensions_m'][key] for key in ('D1@Sketch1', 'D2@Sketch1', 'D1@Boss-Extrude1')],
                 expected['child_driver_values_m']), 'the generated native child lost its three authored drivers')
    return signature(value)
