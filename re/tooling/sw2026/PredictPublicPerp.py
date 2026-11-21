from itertools import product
from math import cos, fsum, isclose, pi, sin, sqrt


def require(value, message):
    if not value:
        raise ValueError(message)


def dot(left, right):
    return fsum(a * b for a, b in zip(left, right, strict=True))


def rotate(axis, degrees):
    length = sqrt(dot(axis, axis))
    require(length > 0, 'the independent live rotation needs an actual fixed plane normal')
    x, y, z = (v / length for v in axis)
    c, s = cos(degrees * pi / 180), sin(degrees * pi / 180)
    v = 1 - c
    return [c+x*x*v, x*y*v+z*s, x*z*v-y*s,
            x*y*v-z*s, c+y*y*v, y*z*v+x*s,
            x*z*v+y*s, y*z*v-x*s, c+z*z*v]


def multiply(left, right):
    return [fsum(left[row*3+k] * right[k*3+column] for k in range(3))
            for row in range(3) for column in range(3)]


def point(matrix, local):
    return [fsum(local[k] * matrix[k*3+index] for k in range(3)) + matrix[9+index]
            for index in range(3)]


def intent(fixture, edit):
    document = fixture['document']
    graph = document['assembly']
    child, = [row['document'] for row in graph['documents']['$tuple']]
    require(document['units']['value'] == child['units']['value'] == 'mm',
            'the disclosed prediction admits explicit millimetre neutral inputs')
    sketch, = child['sketches']['$tuple']
    loop, = sketch['closed_profile_entity_ids']['$tuple']
    entities = {row['id']: row for row in sketch['entities']['$tuple']}
    vertices = [[entities[key]['geometry']['start'][axis] * 0.001 for axis in ('x', 'y')]
                for key in loop['$tuple']]
    require(len(vertices) == 4, 'the independent predictor needs the complete authored rectangle')
    width = max(p[0] for p in vertices) - min(p[0] for p in vertices)
    height = max(p[1] for p in vertices) - min(p[1] for p in vertices)
    require(min(p[0] for p in vertices) == -width / 2 and min(p[1] for p in vertices) == -height / 2,
            'the current independent prediction is restricted to a centered rectangle')
    feature, = child['feature_timeline']['$tuple']
    length = feature['definition']['length']
    require(length['unit'] == 'mm', 'the explicit child depth must retain its actual unit')
    depth = length['value'] * 0.001
    instances = sorted(graph['instances']['$tuple'], key=lambda value: value['order'])
    require(len(instances) == 2 and sum(value['fixed'] for value in instances) == 1,
            'the ordinary perpendicular prediction needs two occurrences and one fixed owner')
    matrices = []
    for value in instances:
        source = value['transform']['values']['$tuple']
        require(source[12:] == [0., 0., 0., 1.], 'the authored transform must be affine')
        matrices.append([source[r*4+c] for c in range(3) for r in range(3)] +
                        [source[index] * 0.001 for index in (3, 7, 11)] + [1., 0., 0., 0.])
    mate, = graph['mates']['$tuple']
    require(mate['kind']['value'] == 'perpendicular' and mate['alignment']['value'] == 'unknown'
            and mate['value'] is None and mate['parameter_ids']['$tuple'] == [],
            'the neutral perpendicular owns no scalar or inferred alignment')
    owners = {value['id']: index for index, value in enumerate(instances)}
    planes = {value['id']: value for value in child['support_planes']['$tuple']}
    entities = {value['id']: value for value in graph['mate_entities']['$tuple']}
    ends = []
    for key in mate['entity_ids']['$tuple']:
        value = entities[key]
        path, = value['instance_path']['$tuple']
        plane = planes[value['source_entity_id']]
        normal = plane['transform']['z_axis']
        vector = [normal[axis] for axis in ('x', 'y', 'z')]
        axis, = [axis for index, axis in enumerate('xyz') if vector == [float(i == index) for i in range(3)]]
        ends.append({'occurrence': owners[path], 'axis': axis, 'datum_name': plane['name']})
    fixed, = [index for index, value in enumerate(instances) if value['fixed']]
    return {'width_m': width, 'height_m': height, 'depth_m': depth, 'matrices': matrices,
            'endpoints': ends, 'fixed_occurrence': fixed,
            'edit_depth_m': edit['edit_depth_m'], 'edit_rotation_deg': edit['edit_rotation_deg']}


def predict(fixture, edit):
    source = intent(fixture, edit)
    result = {}
    for edited, key in ((False, 'source'), (True, 'edited')):
        matrices = [list(value) for value in source['matrices']]
        fixed = source['fixed_occurrence']
        if edited:
            endpoint = next(value for value in source['endpoints'] if value['occurrence'] == fixed)
            start = 3 * 'xyz'.index(endpoint['axis'])
            matrices[1-fixed][:9] = multiply(matrices[1-fixed][:9],
                                             rotate(matrices[fixed][start:start+3], source['edit_rotation_deg']))
        width, height = source['width_m'], source['height_m']
        depth = source['edit_depth_m'] if edited else source['depth_m']
        center = [0., 0., depth / 2]
        centers = [point(matrix, center) for matrix in matrices]
        corners = [point(matrix, vertex) for matrix in matrices
                   for vertex in product((-width/2, width/2), (-height/2, height/2), (0., depth))]
        ends = [{'occurrence': value['occurrence'], 'axis': value['axis'],
                 'normal': matrices[value['occurrence']][3*'xyz'.index(value['axis']):3*'xyz'.index(value['axis'])+3],
                 'point_m': matrices[value['occurrence']][9:12]} for value in source['endpoints']]
        residual = dot(ends[0]['normal'], ends[1]['normal'])
        require(isclose(residual, 0., abs_tol=1e-12), 'the independent real neutral planes are not perpendicular')
        volume = width * height * depth
        area = 2 * (width*height + width*depth + height*depth)
        result[key] = {'child': {'body_count': 1, 'volume_m3': volume, 'area_m2': area, 'com_m': center},
                       'assembly': {'body_count': 2, 'volume_m3': 2*volume, 'area_m2': 2*area,
                                    'com_m': [fsum(value[index] for value in centers)/2 for index in range(3)],
                                    'bounds_min_m': [min(value[index] for value in corners) for index in range(3)],
                                    'bounds_max_m': [max(value[index] for value in corners) for index in range(3)]},
                       'native_transforms': matrices, 'ordered_endpoints': ends, 'normal_dot': residual,
                       'child_driver_values_m': [width, height, depth], 'alignment': 'unknown',
                       'internal_alignment': 0, 'scalar_mate_dimension': None, 'fixed_occurrence': fixed}
    return result
