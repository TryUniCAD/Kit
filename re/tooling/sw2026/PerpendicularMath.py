from itertools import product
from math import cos, fsum, isclose, pi, sin, sqrt


def dot(first, second):
    return fsum(a * b for a, b in zip(first, second, strict=True))


def multiply(first, second):
    return [fsum(first[r * 3 + k] * second[k * 3 + c] for k in range(3)) for r in range(3) for c in range(3)]


def rotate(axis, angle):
    length = sqrt(dot(axis, axis))
    x, y, z = [v / length for v in axis]
    c, s = cos(angle * pi / 180), sin(angle * pi / 180)
    v = 1 - c
    return [c+x*x*v, x*y*v+z*s, x*z*v-y*s, x*y*v-z*s, c+y*y*v, y*z*v+x*s, x*z*v+y*s, y*z*v-x*s, c+z*z*v]


def rotation(steps):
    value = [1., 0., 0., 0., 1., 0., 0., 0., 1.]
    for axis, angle in steps:
        vector = [float(i == 'xyz'.index(axis)) for i in range(3)]
        value = multiply(value, rotate(vector, angle))
    return value


def point(matrix, offset, local):
    return [fsum(local[k] * matrix[k * 3 + i] for k in range(3)) + offset[i] for i in range(3)]


def prediction(spec, edited=False):
    matrices = [rotation(item['orientation']) for item in spec['placements']]
    if edited:
        fixed = spec['fixed_occurrence']
        axis = next(item['axis'] for item in spec['endpoints'] if item['occurrence'] == fixed)
        start = 3 * 'xyz'.index(axis)
        matrices[1-fixed] = multiply(matrices[1-fixed], rotate(matrices[fixed][start:start+3], spec['edit_rotation_deg']))
    normals = [matrices[item['occurrence']][3*'xyz'.index(item['axis']):3*'xyz'.index(item['axis'])+3] for item in spec['endpoints']]
    if not isclose(dot(*normals), 0., rel_tol=0., abs_tol=1e-12):
        raise ValueError('neutral prediction does not satisfy perpendicularity')
    width, height, initial_depth = spec['size_m']
    depth = spec['edit_depth_m'] if edited else initial_depth
    local_center = [0., 0., depth/2]
    centers = [point(m, item['translation_m'], local_center) for m, item in zip(matrices, spec['placements'], strict=True)]
    volume = width * height * depth
    area = 2 * (width*height + width*depth + height*depth)
    vertices = list(product((-width/2, width/2), (-height/2, height/2), (0., depth)))
    corners = [point(m, item['translation_m'], v) for m, item in zip(matrices, spec['placements'], strict=True) for v in vertices]
    return {'child':{'body_count':1,'volume_m3':volume,'area_m2':area,'com_m':local_center},
            'assembly':{'body_count':2,'volume_m3':2*volume,'area_m2':2*area,'com_m':[fsum(v[i] for v in centers)/2 for i in range(3)],
                        'bounds_min_m':[min(v[i] for v in corners) for i in range(3)],'bounds_max_m':[max(v[i] for v in corners) for i in range(3)]},
            'native_transforms':[[*m,*item['translation_m'],1.,0.,0.,0.] for m,item in zip(matrices,spec['placements'],strict=True)],
            'ordered_endpoints':[{'occurrence':end['occurrence'],'axis':end['axis'],'normal':normal,
                                 'point_m':spec['placements'][end['occurrence']]['translation_m']} for end,normal in zip(spec['endpoints'],normals,strict=True)],
            'normal_dot':dot(*normals),'child_driver_values_m':[width,height,depth],
            'alignment':'unknown','internal_alignment':0,'scalar_mate_dimension':None,'fixed_occurrence':spec['fixed_occurrence']}
