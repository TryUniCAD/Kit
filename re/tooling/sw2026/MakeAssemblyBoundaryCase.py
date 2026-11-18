from dataclasses import replace
from math import cos, sin, radians

from tests.Convert.Solidworks.Research.Construction.Part.MakePlainDoc import MakePlainDoc
from interchange.geometry.Models.Sketch import ConstraintRef, SketchRelation
from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import PrincipalFrame
from interchange.assembly.AssemblyEnums import ComponentKind, MateAlignment, MateEntityKind, MateKind
from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.assembly.ComponentInstance import ComponentInst
from interchange.assembly.MateConstraint import MateConstraint
from interchange.assembly.MateEntity import MateEntity
from interchange.assembly.MateGroup import MateGroup
from interchange.assembly.TransformMatrix import TransformMatrix
from interchange.document.Models.DocumentModel import AssemblyData, CadDocument, ComponentDoc
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordParameter import Parameter, ParameterValue
from interchange.Records.RecordSource import CadSource


def dimensioned_child(name, dimensions, configuration_name):
    document = MakePlainDoc(name, *(value * 1000 for value in dimensions))
    sketch, = document.sketches
    parameters = tuple(Parameter('parameter/' + role, 'D' + str(index + 1), ParameterValue(length * 1000, ValueKind.LENGTH, 'mm'), owner_id=sketch.id)
                       for index, (role, length) in enumerate(zip(('width', 'height'), dimensions[:2], strict=True)))
    axes = tuple(SketchRelation('relation/axis/' + str(index), 'horizontal' if index % 2 == 0 else 'vertical', (ConstraintRef(row.id),))
                 for index, row in enumerate(sketch.entities))
    lengths = tuple(SketchRelation('relation/length/' + str(index), 'distance', (ConstraintRef(sketch.entities[index].id, 'start'), ConstraintRef(sketch.entities[index].id, 'end')), parameter.id)
                    for index, parameter in enumerate(parameters))
    sketch = replace(sketch, constraints=(*axes, *lengths), parameter_ids=tuple(row.id for row in parameters))
    return replace(document, sketches=(sketch,), parameters=(*parameters, document.parameters[0]),
                   configurations=(replace(document.configurations[0], name=configuration_name),))


def principal(scope):
    result = []
    for axis, name in zip('xyz', ('Right Plane', 'Top Plane', 'Front Plane'), strict=True):
        frame = PrincipalFrame(axis)
        result.append(SupportPlane(scope + '/plane/' + axis, name,
            Transform(*(SpaceVector(*value) for value in (frame.OriginValue, frame.AxisU, frame.AxisV, frame.NormalValue)))))
    return tuple(result)


def make_case(count):
    name, child_name = 'PublicPlanarPair' + str(count), 'PublicDatumPrism'
    child = dimensioned_child(child_name, (.0371, .0186, .0093), 'Child configuration')
    child_planes = principal('child')
    child = replace(child, support_planes=child_planes,
                    sketches=(replace(child.sketches[0], support_plane_id=child_planes[2].id),))
    root_config = Configuration('root/config', 'Assembly configuration', True)
    root_id, child_id, document_id = 'assembly/root', 'assembly/child', 'document/child'
    child_config, = child.configurations
    definitions = (
        ComponentDef(root_id, name, ComponentKind.ASSEMBLY, configuration_name=root_config.name, configuration_id=root_config.id),
        ComponentDef(child_id, child_name, ComponentKind.PART, document_id=document_id, configuration_name=child_config.name,
                     configuration_id=child_config.id, body_ids=tuple(value.id for value in child.bodies)),
    )
    angle = radians(31.)
    cosine, sine = cos(angle), sin(angle)
    instances = []
    for index, local in enumerate(((0., 0., 0.), (83., 0., 42.), (161., 0., 42.))[:count]):
        x, y, z = local
        matrix = (cosine, -sine, 0., cosine * x - sine * y,
                  sine, cosine, 0., sine * x + cosine * y,
                  0., 0., 1., z, 0., 0., 0., 1.)
        instances.append(ComponentInst('instance/' + str(index), child_name + '-' + str(index + 1), child_id,
            root_id, TransformMatrix(matrix), index, configuration_name=child_config.name,
            configuration_id=child_config.id, fixed=index == 0))
    specs = [('CoincidentY', 'coincident', 'y', 0, 1)]
    if count == 3:
        specs += [('ParallelX', 'parallel', 'x', 1, 2)]
    specs += [('DistanceZ', 'distance', 'z', 0, count - 1)]
    entities, mates, parameters = [], [], []
    for order, (mate_name, kind, axis, first, second) in enumerate(specs):
        mate_id = 'mate/' + mate_name
        ends = []
        for ordinal, occurrence in enumerate((first, second)):
            identity = mate_id + '/entity/' + str(ordinal)
            entities.append(MateEntity(identity, root_id, (instances[occurrence].id,), MateEntityKind.PLANE,
                                       source_entity_id='child/plane/' + axis))
            ends.append(identity)
        value, parameter_ids = None, ()
        if kind == 'distance':
            value = ParameterValue(42., ValueKind.LENGTH, 'mm')
            parameter = Parameter(mate_id + '/parameter', 'D1', value, ParameterRole.DRIVING, owner_id=mate_id)
            parameters.append(parameter)
            parameter_ids = (parameter.id,)
        mates.append(MateConstraint(mate_id, mate_name, MateKind(kind), root_id, tuple(ends), order, value,
                                    parameter_ids, MateAlignment.ALIGNED))
    graph = AssemblyData(root_id, definitions, tuple(instances), (ComponentDoc(document_id, child),),
                         tuple(entities), tuple(mates), (MateGroup('group/mates', 'Mates', root_id, tuple(row.id for row in mates)),))
    document = CadDocument(CadSource('kit-neutral', '<independently authored assembly>', '0' * 64), (root_config,),
                            tuple(parameters), principal('root'), (), (), (), (), assembly=graph, metadata={'name': name})
    document.assert_valid()
    return document
