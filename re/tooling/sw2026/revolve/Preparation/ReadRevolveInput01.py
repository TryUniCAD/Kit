from dataclasses import dataclass
from math import isfinite, tau

from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CheckPartLinks import CheckPartLinks
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadPrincAxis import ReadPrincAxis
from convert.adapters.solidworks.Archive.Construction.Sketch.PolygonInput import PolygonInput
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Features.FeatureAngleRev import AngularRevolve
from interchange.geometry.Models.GeometryCurves import LineGeometry


@dataclass(frozen=True)
class RevolvePlan:
    NameValue: str
    ConfigName: str
    PlaneName: str
    SketchName: str
    FeatureName: str
    VerticesValue: tuple
    AxisStart: tuple
    AxisEnd: tuple
    AngleValue: float
    IsReverse: bool
    AxisValue: str = 'z'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_plan(document):
    require(type(document) is CadDocument, 'revolve requires a real neutral document')
    document.assert_valid()
    require(document.assembly is None and document.DrawingValue is None
        and document.brep is None and not document.meshes and not document.brep_payloads
        and not document.materials and not document.diagnostics,
        'revolve prototype does not admit other geometry or document domains')
    require(tuple(map(len, (document.configurations, document.support_planes, document.sketches,
        document.feature_timeline, document.bodies, document.parameters, document.selections)))
        == (1, 1, 1, 1, 1, 1, 1), 'revolve requires one complete ordinary model inventory')
    require(set(document.metadata) == {'name'} and type(document.metadata['name']) is str
        and document.metadata['name'], 'revolve requires only its explicit modeled document name')
    require(document.units == 'mm', 'revolve prototype admits millimetre neutral coordinates')
    plane = CheckPartLinks(document)
    require(ReadPrincAxis(plane.transform) == 'z', 'revolve prototype requires canonical Front support')
    feature, sketch, parameter, selection = (document.feature_timeline[0], document.sketches[0],
        document.parameters[0], document.selections[0])
    definition = feature.definition
    require(feature.kind == FeatureKind.KRevolution and feature.operation in (BooleanOp.KCreate, BooleanOp.KJoin)
        and type(definition) is AngularRevolve and feature.order == 0 and not feature.input_feature_ids
        and not feature.suppressed and not feature.configuration_states and not feature.attributes,
        'revolve requires one active standalone ordinary angular boss')
    require(definition.SideMode == 'one_sided' and definition.AgainstParameterId is None,
        'revolve prototype requires one forward angular owner')
    require(parameter.name == 'D1' and parameter.role == ParameterRole.KDriving
        and parameter.owner_id == feature.id and parameter.expression is None and not parameter.attributes
        and parameter.value.kind == ValueKind.KAngle and parameter.value.unit == 'rad'
        and definition.AlongParameterId == parameter.id and feature.parameter_ids == (parameter.id,),
        'revolve requires its actual sole unexpressed D1 radian driver')
    angle = parameter.value.value
    require(type(angle) in (int, float) and isfinite(angle) and 1e-8 < angle <= tau,
        'revolve angle must be finite positive radians through one full turn')
    require(feature.selection_ids == (selection.id,) and definition.AxisSelectionId == selection.id
        and not selection.query and selection.point is None and not selection.attributes
        and len(selection.path) == 2 and selection.path[0].entity_kind == 'sketch'
        and selection.path[0].entity_id == sketch.id and selection.path[0].subelement == ''
        and selection.path[1].entity_kind == 'sketch_entity' and selection.path[1].subelement == '',
        'revolve axis must select an actual local sketch entity')
    require(not sketch.suppressed and not sketch.attributes and not sketch.parameter_ids
        and len(sketch.entities) == 5 and len(sketch.constraints) == 4
        and len(sketch.closed_profile_entity_ids) == 1,
        'revolve sketch must contain four contour lines one axis and four unary relations')
    entities = {entity.id: entity for entity in sketch.entities}
    loop = sketch.closed_profile_entity_ids[0]
    require(len(loop) == 4 and len(set(loop)) == 4 and set(loop).issubset(entities),
        'revolve requires one explicit four-edge perimeter')
    axis_id = selection.path[1].entity_id
    require(set(entities) - set(loop) == {axis_id}, 'revolve selected axis must be outside its perimeter')
    vertices, ends = [], []
    for entity_id in (*loop, axis_id):
        entity = entities[entity_id]
        geometry = entity.geometry
        require(entity.kind == GeometryKind.KLine and type(geometry) is LineGeometry
            and not entity.fixed and not entity.attributes and entity.construction == (entity_id == axis_id),
            'revolve requires actual ordinary lines and a distinct unfixed construction axis')
        values = (geometry.start.x, geometry.start.y, geometry.end.x, geometry.end.y)
        require(all(type(value) in (int, float) and isfinite(value) for value in values),
            'revolve line coordinates must be finite')
        vertices.append(tuple(value * 0.001 for value in values[:2]))
        ends.append(tuple(value * 0.001 for value in values[2:]))
    axis_start, axis_end = vertices.pop(), ends.pop()
    require(all(end == vertices[(index + 1) % 4] for index, end in enumerate(ends)),
        'revolve perimeter must preserve exact joined endpoint identity')
    vertices = PolygonInput(tuple(vertices), 19000).VerticesValue
    xs, ys = set(x for x, _ in vertices), set(y for _, y in vertices)
    require(len(xs) == len(ys) == 2 and set(vertices) == {(x,y) for x in xs for y in ys},
        'revolve prototype requires an axis-aligned rectangle')
    require(axis_start[0] == axis_end[0] and axis_start[0] < min(xs)
        and axis_end[1] - axis_start[1] >= 1e-8,
        'revolve axis must point upward strictly left of the rectangle')
    for index, relation in enumerate(sketch.constraints):
        entity = entities[loop[index]]
        geometry = entity.geometry
        kind = 'horizontal' if geometry.start.y == geometry.end.y else 'vertical'
        require(relation.kind == kind and len(relation.references) == 1
            and relation.references[0].entity_id == entity.id and relation.references[0].point == ''
            and relation.parameter_id is None and relation.driving and not relation.suppressed
            and not relation.attributes, 'revolve must preserve exactly its authored contour axis relations')
    origin, direction = definition.AxisOrigin, definition.AxisDirection
    require((origin.x * 0.001, origin.y * 0.001, origin.z) == (*axis_start, 0.0)
        and direction.x == direction.z == 0.0 and direction.y in (-1.0, 1.0),
        'revolve normalized definition must agree with the actual selected axis')
    return RevolvePlan(document.metadata['name'], document.configurations[0].name,
        plane.name, sketch.name, feature.name, vertices, axis_start, axis_end, float(angle), direction.y < 0)
