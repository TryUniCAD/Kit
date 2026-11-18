from __future__ import annotations

import math

from interchange.serialization.Deserialize import FromData


PART_ROLES = (
    ('Comments', 'CommentsFolder'), ('Favorites', 'FavoriteFolder'), ('History', 'HistoryFolder'),
    ('Selection Sets', 'SelectionSetFolder'), ('Sensors', 'SensorFolder'), ('Design Binder', 'DocsFolder'),
    ('Surface Bodies', 'SurfaceBodyFolder'), ('Solid Bodies', 'SolidBodyFolder'), ('Lights and Cameras', 'EnvFolder'),
    ('Markups', 'InkMarkupFolder'), ('Equations', 'EqnFolder'), ('Material <not specified>', 'MaterialFolder'),
)
ASSEMBLY_ROLES = (
    ('Comments', 'CommentsFolder'), ('Favorites', 'FavoriteFolder'), ('History', 'HistoryFolder'),
    ('Selection Sets', 'SelectionSetFolder'), ('Sensors', 'SensorFolder'), ('Live Section Planes', 'LiveSectionFolder'),
    ('Design Binder', 'DocsFolder'), ('Lights and Cameras', 'EnvFolder'), ('Markups', 'InkMarkupFolder'), ('Equations', 'EqnFolder'),
)
MATE_TYPES = {'coincident': 'MateCoincident', 'parallel': 'MateParallel', 'distance': 'MateDistanceDim'}


def require(value, text):
    if not value:
        raise ValueError(text)


def folders(values):
    result = []
    for name, kind in values:
        result.append([name, kind, None])
        if kind == 'DocsFolder':
            result += [['Annotations', 'DetailCabinet', None], ['Notes', 'NotesAreaFtrFolder', 'Annotations'], ['Notes1___EndTag___', 'NotesAreaFtrFolder', 'Annotations']]
        if kind == 'EnvFolder':
            result += [['Ambient', 'AmbientLight', name], *[[f'Directional{index}', 'DirectionLight', name] for index in (1, 2, 3)]]
    return result


def trees(document, child, occurrences, mates, group):
    parent = folders(ASSEMBLY_ROLES)
    nested = folders(PART_ROLES)
    for target, model in ((parent, document), (nested, child)):
        require(len(model.support_planes) == 3, 'prediction requires three explicitly named canonical planes')
        target.extend([model.support_planes[index].name, 'RefPlane', None] for index in (2, 1, 0))
        target.append(['Origin', 'OriginProfileFeature', None])
    parent += [[value.name, 'Reference', None] for value in occurrences]
    parent.append([group.name, 'MateGroup', None])
    parent += [[value.name, MATE_TYPES[str(value.kind)], group.name] for value in mates]
    nested += [[child.sketches[0].name, 'ProfileFeature', None], [child.feature_timeline[0].name, 'Extrusion', None]]
    return {'parent': parent, 'child': nested}


def native_matrix(value):
    matrix = value.transform.values
    return [matrix[0], matrix[4], matrix[8], matrix[1], matrix[5], matrix[9], matrix[2], matrix[6], matrix[10],
            matrix[3] * .001, matrix[7] * .001, matrix[11] * .001, 1., 0., 0., 0.]


def predict(request):
    document = FromData(request['document'])
    graph = document.assembly
    child, = graph.documents
    child = child.document
    occurrences = sorted(graph.instances, key=lambda value: value.order)
    mates = sorted(graph.mates, key=lambda value: value.order)
    group, = graph.mate_groups
    fixed, = [index for index, value in enumerate(occurrences) if value.fixed]
    require(fixed == 0, 'this disclosed packet has an explicitly fixed first occurrence')
    plane_names = {value.id: value.name for value in child.support_planes}
    entities = {value.id: value for value in graph.mate_entities}
    indices = {value.id: index for index, value in enumerate(occurrences)}
    vertices = [value.geometry.start for value in child.sketches[0].entities]
    width = (max(value.x for value in vertices) - min(value.x for value in vertices)) * .001
    height = (max(value.y for value in vertices) - min(value.y for value in vertices)) * .001
    depth = child.feature_timeline[0].definition.length.value * .001
    require(all(math.isclose(abs(value.x), width * 500, abs_tol=1e-12) and math.isclose(abs(value.y), height * 500, abs_tol=1e-12) for value in vertices), 'packet prediction requires its independently authored centered rectangle')
    child_mass = {'volume': width * height * depth, 'area': 2 * (width * height + width * depth + height * depth), 'com': [0., 0., depth / 2], 'body_count': 1}
    matrices = [native_matrix(value) for value in occurrences]
    placements = []
    for value, matrix in zip(occurrences, matrices, strict=True):
        raw = value.transform.values
        angle = math.degrees(math.atan2(raw[4], raw[0]))
        require(all(math.isclose(raw[index], expected, abs_tol=1e-12) for index, expected in ((2, 0.), (6, 0.), (8, 0.), (9, 0.), (10, 1.))), 'this disclosed packet uses its authored rotation around the z axis only')
        placements.append({'axis': 'z', 'angle_deg': angle, 'translation_m': matrix[9:12]})
    constraints = []
    for value in mates:
        ends = [entities[identity] for identity in value.entity_ids]
        row = {'kind': str(value.kind), 'name': value.name, 'planes': [[indices[end.instance_path[0]], plane_names[end.source_entity_id]] for end in ends]}
        if str(value.kind) == 'distance':
            row['distance_m'] = value.value.value * .001
        constraints.append(row)
    distance_index, = [index for index, value in enumerate(mates) if str(value.kind) == 'distance']
    distance = constraints[distance_index]['distance_m']
    edited_distance = distance + .01573
    case = {'name': document.metadata['name'], 'split': 'discovery', 'fixed_occurrence': fixed, 'placements': placements, 'mates': constraints}
    from PlanarMateEdit import predict_edit, check_satisfied
    from SdkPlanarGroupPrediction import transform
    edited_case = predict_edit(case, edited_distance, transform)
    result = {'schema': 'kit.sw2026.portable-assembly-independent-prediction.v1', 'case': case, 'edited_case': edited_case,
              'edit_distance_m': edited_distance, 'child_dimensions_m': {'width': width, 'height': height, 'depth': depth},
              'child_configuration': child.configurations[0].name, 'assembly_configuration': document.configurations[0].name,
              'child_parameters_m': {'D1@' + child.sketches[0].name: width, 'D2@' + child.sketches[0].name: height, 'D1@' + child.feature_timeline[0].name: depth},
              'occurrence_names': [value.name for value in occurrences], 'tree': trees(document, child, occurrences, mates, group),
              'writer_frames_or_readback_used': False, 'source_observations_read': 0, 'heldout_inputs_read': 0, 'native_acceptance': False}
    for label, chosen in (('initial', case), ('edited', edited_case)):
        transforms = [transform(value) for value in chosen['placements']]
        check_satisfied(chosen['mates'], transforms)
        centers = [[matrix[9 + index] + matrix[6 + index] * depth / 2 for index in range(3)] for matrix in transforms]
        count = len(transforms)
        result[label] = {'body_count': count, 'fixed_flags': [index == fixed for index in range(count)], 'occurrence_transforms': transforms,
                         'assembly': {'volume': count * child_mass['volume'], 'area': count * child_mass['area'], 'com': [math.fsum(row[index] for row in centers) / count for index in range(3)]},
                         'child': child_mass, 'mate_values_m': [value.get('distance_m') for value in chosen['mates']]}
    return result
