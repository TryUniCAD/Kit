from dataclasses import replace

from MakeColdRequest import make_request
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.RectDimInput import RectDimInput
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Records.RecordParameter import Parameter, ParameterValue
from interchange.geometry.Models.Sketch import ConstraintRef, SketchRelation


def request(case):
    document, settings = make_request(case['part'])
    names = case['driver_names']
    if names is None:
        return document, settings, None
    if type(names) is not list or len(names) != 3:
        raise ValueError('three actual neutral driver names required')
    sketch, = document.sketches
    feature, = document.feature_timeline
    depth, = document.parameters
    width = Parameter('parameter/width', names[0], ParameterValue(case['part']['width_mm'],
        ValueKind.KLength, 'mm'), ParameterRole.KDriving, owner_id=sketch.id)
    height = Parameter('parameter/height', names[1], ParameterValue(case['part']['height_mm'],
        ValueKind.KLength, 'mm'), ParameterRole.KDriving, owner_id=sketch.id)
    edges, = sketch.closed_profile_entity_ids
    relations = tuple(SketchRelation('relation/axis'+str(index),
        'horizontal' if index % 2 == 0 else 'vertical', (ConstraintRef(identity),))
        for index, identity in enumerate(edges)) + tuple(SketchRelation('relation/length'+str(index),
        'distance', (ConstraintRef(edges[index], 'start'), ConstraintRef(edges[index], 'end')),
        parameter_id=parameter.id) for index, parameter in enumerate((width, height)))
    result = replace(document, parameters=(width, height, replace(depth, name=names[2])),
        sketches=(replace(sketch, constraints=relations, parameter_ids=(width.id, height.id)),))
    centre_x, centre_y = (value * 0.001 for value in case['part']['centre_xy_mm'])
    right = centre_x + case['part']['width_mm'] * 0.0005
    bottom = centre_y - case['part']['height_mm'] * 0.0005
    return result, settings, RectDimInput((centre_x, bottom - 0.0073),
        (right + 0.0091, centre_y), False, 0, True)
