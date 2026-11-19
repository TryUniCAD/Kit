from dataclasses import dataclass, replace

from CheckConcentricNeutralBrep import check_complete_brep
from math import isclose, isfinite
from types import MappingProxyType

from convert.Geometry.Extrude.Circular.CircularExtrude import BuildCircular
from convert.adapters.solidworks.Archive.Construction.Assembly.Bounds.Circles.NeedCircChild import NeedCircChild
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
from convert.adapters.solidworks.Archive.Partition.CheckXmtGraph import CheckXmtGraph
from convert.adapters.solidworks.Archive.Partition.ReadXmtVector import ReadXmtVector
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt, ReadNodeName
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.ReadAsmModel import ReadAsmModel
from convert.adapters.solidworks.Core.AssemblyPreparation.Placements.ReadAsmPlace import ReadAsmPlace
from convert.adapters.solidworks.Core.Preparation.Circle.PlanCircle import PlanCircle
from convert.adapters.solidworks.Core.TypedMates.Cylinders.CheckCylSide import CheckCylSide
from convert.adapters.solidworks.Core.TypedMates.Cylinders.CylChild import CylChild
from convert.adapters.solidworks.Core.TypedMates.Cylinders.PickCylFace import PickCylFace
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylAttr import ReadCylAttr
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylOwner import ReadCylOwner
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylWords import ReadCylWords
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyScalar import ReadBodyScalar
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from interchange.brep.Surfaces.BrepSurfaces import CylinderSurface, PlaneSurface
from interchange.brep.Validation.BrepValidate import GetBrepErrors
from interchange.geometry.Models.Transform import Transform


def require(value, message):
    if not value:
        raise ValueError('concentric neutral admission: ' + message)


def close(first, second):
    return len(first) == len(second) and all(isfinite(a) and isfinite(b) and isclose(a, b, rel_tol=1e-12, abs_tol=1e-12) for a, b in zip(first, second, strict=True))


def vector(value):
    return (value.x, value.y, value.z)


@dataclass(frozen=True)
class CylinderBinding:
    document: object
    candidate: object
    nodes: object
    neutral_brep: object
    neutral_face: object
    neutral_surface: object
    child: CylChild
    body: object
    profile: str
    neutral_id_map: object = None


@dataclass(frozen=True)
class CylinderEnd:
    entity: object
    occurrence: object
    occurrence_index: int
    placement: object
    binding: CylinderBinding
    origin_m: tuple[float, float, float]
    axis: tuple[float, float, float]
    radius_m: float


@dataclass(frozen=True)
class ConcentricIntent:
    document: object
    model: object
    mate: object
    ends: tuple[CylinderEnd, CylinderEnd]
    fixed_index: int
    alignment_code: int
    rotation_locked: bool


def derive_brep(document, plan):
    circle = document.sketches[0].entities[0].geometry
    return BuildCircular(plan.BodyId, document.support_planes[0].transform, circle,
                         0.0, plan.DepthValue * 1000.0, circle.radius, circle.radius)[0]


def read_neutral_side(document, plan, profile):
    require(str(document.units) == 'mm', 'child units require explicit millimetres')
    if profile == 'authored_brep':
        require(document.brep is not None, 'authored_brep requires the actual owned neutral face graph')
        brep = document.brep
    elif profile == 'derived_feature':
        require(document.brep is None, 'derived_feature requires an unambiguous feature-only child')
        brep = derive_brep(document, plan)
    else:
        raise ValueError('concentric neutral admission: unknown neutral face owner profile')
    require(not GetBrepErrors(brep, frozenset((plan.BodyId,))), 'neutral face topology is invalid')
    require(brep.schema_version == '1.0' and not brep.wires
            and all(not getattr(value, 'attributes', {}) and getattr(value, 'provenance', None) is None
                    for name in ('curves','pcurves','surfaces','vertices','edges','coedges','loops','faces','face_uses','shells','shell_uses','regions','bodies') for value in getattr(brep, name)),
            'neutral face graph has unrepresented extensions')
    require(len(brep.faces) == 3 and len(brep.bodies) == 1 and len(brep.surfaces) == 3
            and brep.bodies[0].design_body_id == plan.BodyId
            and brep.bodies[0].transform == Transform(),
            'neutral shape requires one complete ordinary cylinder body')
    surfaces = {value.id: value for value in brep.surfaces}
    sides = tuple(face for face in brep.faces if type(surfaces[face.surface_id]) is CylinderSurface)
    require(len(sides) == 1, 'neutral lateral face is absent or ambiguous')
    side = sides[0]
    surface = surfaces[side.surface_id]
    center = (*plan.CircleValue.CenterValue, 0.0)
    radius = plan.CircleValue.RadiusValue
    require(close(tuple(v * 0.001 for v in vector(surface.origin)), center)
            and close(vector(surface.axis), (0.0, 0.0, 1.0))
            and close((surface.radius * 0.001,), (radius,))
            and side.same_sense is True,
            'neutral lateral surface differs from its actual circular feature')
    caps = tuple(surfaces[face.surface_id] for face in brep.faces if face is not side)
    require(all(type(value) is PlaneSurface for value in caps), 'neutral cylinder caps are unqualified')
    caps = tuple(sorted(caps, key=lambda value: value.origin.z))
    actual = tuple(tuple(v * 0.001 for v in vector(value.origin)) for value in caps)
    expected = [center, (*center[:2], plan.DepthValue)]
    require(all(close(a, b) for a, b in zip(actual, expected, strict=True))
            and all(close(vector(value.normal), normal) for value, normal in zip(caps, ((0.0, 0.0, -1.0), (0.0, 0.0, 1.0)), strict=True)),
            'neutral cylinder cap placement differs from the authored blind extent')
    id_map = check_complete_brep(brep, derive_brep(document, plan))
    return brep, side, surface, id_map


def bind_cylinder(document, candidate, nodes, *, profile):
    plan = NeedCircChild(candidate)
    require(plan.IsDiameter, 'the generated kernel producer is qualified only for the diameter-driven circle profile')
    require(str(document.units) == 'mm', 'child units require explicit millimetres')
    original_plan = PlanCircle(replace(document, brep=None))
    require(original_plan == plan, 'candidate does not represent the actual complete neutral circle plan')
    brep, neutral_face, neutral_surface, id_map = read_neutral_side(document, plan, profile)
    require(all(key == value.IndexValue for key, value in nodes.items()), 'kernel map keys lost actual node identity')
    CheckXmtGraph(nodes)
    face, surface, body = PickCylFace(nodes)
    attributes = {'ATOM_ID_2001': ReadCylAttr(nodes, body, 'ATOM_ID_2001')}
    atom = ReadBodyScalar(nodes, attributes, 'ATOM_ID_2001', 1)
    link = NativeLink(candidate.ConfigValue, candidate.ResolvedValue, plan.ConfigName, 'Contents/Config-0')
    require(link.ConfigValue.HeaderValue is candidate.HeaderValue, 'candidate header is not the actual configuration header')
    feature, marker = ReadCylOwner(link, atom)
    require(feature is candidate.BossValue.FeatureValue
            and marker == FieldInt(candidate.ProfileValue.GeometryValue.ArcValue.FieldsValue, 'f08')
            and ReadNodeName(candidate.CurrentConfig) == document.configurations[0].name,
            'kernel does not retain the actual generated feature sketch and selected configuration')
    child = CylChild(link, nodes, face, surface, feature, marker, atom, '')
    CheckCylSide(child)
    feature_id = FieldInt(feature.FieldsValue, 'f08')
    epoch = DatumTime(candidate.HeaderValue, feature_id)
    caps = tuple(ReadCylWords(nodes, value) for value in nodes.values() if value.KindValue == 14 and value is not face)
    require(set(caps) == {(40, feature_id, epoch, 0, 0, 0), (40, feature_id, epoch, 0, 1, 0)},
            'generated cap identities do not belong to the actual feature and first epoch')
    require(close(ReadXmtVector(surface, 'pvec'), tuple(value * 0.001 for value in vector(neutral_surface.origin)))
            and close(ReadXmtVector(surface, 'axis'), vector(neutral_surface.axis))
            and close((surface.FieldsValue['radius'],), (neutral_surface.radius * 0.001,)),
            'generated lateral geometry differs from the selected neutral cylinder')
    return CylinderBinding(document, candidate, MappingProxyType(dict(nodes)), brep, neutral_face, neutral_surface, child, body, profile, id_map)


def place_point(point, frame):
    return tuple(frame.OriginValue[index] + sum(point[axis] * basis[index] for axis, basis in enumerate((frame.AxisU, frame.AxisV, frame.NormalValue))) for index in range(3))


def place_axis(axis, frame):
    return tuple(sum(axis[slot] * basis[index] for slot, basis in enumerate((frame.AxisU, frame.AxisV, frame.NormalValue))) for index in range(3))


def read_end(entity, model, binding):
    require(entity.owner_definition_id == model.RootValue.id and str(entity.kind) == 'cylinder',
            'endpoint requires the actual root owner and cylinder kind')
    require(not entity.selection_id and entity.frame is None and entity.provenance is None and not entity.attributes,
            'endpoint has unrepresented selection, frame or native diagnostic extensions')
    require(len(entity.instance_path) == 1, 'endpoint requires one explicit direct occurrence')
    indexes = {value.id: index for index, value in enumerate(model.Occurrences)}
    require(entity.instance_path[0] in indexes, 'endpoint occurrence is absent')
    index = indexes[entity.instance_path[0]]
    occurrence = model.Occurrences[index]
    require(entity.source_entity_id == binding.neutral_face.id, 'selected neutral lateral face is absent or ambiguous')
    require(type(entity.radius) in (int, float) and type(entity.radius) is not bool
            and close((float(entity.radius),), (binding.neutral_surface.radius,)),
            'endpoint radius must match its actual child in millimetres')
    placement = ReadAsmPlace(occurrence)
    cylinder = binding.child.SurfaceValue
    return CylinderEnd(entity, occurrence, index, placement, binding,
                       place_point(ReadXmtVector(cylinder, 'pvec'), placement.FrameValue),
                       place_axis(ReadXmtVector(cylinder, 'axis'), placement.FrameValue),
                       cylinder.FieldsValue['radius'])


def project_concentric(document, bindings):
    model = ReadAsmModel(document)
    graph = model.GraphValue
    require(len(model.Occurrences) == 2, 'only two actual rigid direct occurrences are qualified')
    require(set(bindings) == {model.ChildValue.id}, 'bindings must exactly cover the one owned repeated child')
    binding = bindings[model.ChildValue.id]
    require(type(binding) is CylinderBinding and binding.document is model.ChildDocument,
            'binding must retain the exact actual owned neutral document')
    checked = bind_cylinder(binding.document, binding.candidate, binding.nodes, profile=binding.profile)
    require(checked.neutral_face.id == binding.neutral_face.id
            and checked.child.FaceValue is binding.child.FaceValue
            and checked.child.FeatureValue is binding.child.FeatureValue,
            'binding was replaced or its actual face owner changed')
    require(not document.parameters and len(graph.mates) == 1 and len(graph.mate_entities) == 2,
            'one complete dimensionless concentric mate and two explicit endpoints are required')
    mate = graph.mates[0]
    require(type(mate.order) is int and mate.order == 0
            and mate.owner_definition_id == model.RootValue.id
            and str(mate.kind) == 'concentric' and str(mate.alignment) in ('aligned', 'anti_aligned')
            and type(mate.suppressed) is bool and not mate.suppressed
            and type(mate.driving) is bool and mate.driving
            and mate.value is None and not mate.parameter_ids and mate.provenance is None,
            'mate requires ordinary active driving concentric intent and explicit alignment')
    require(set(mate.attributes) == {'rotation_locked'} and type(mate.attributes['rotation_locked']) is bool,
            'rotation lock must be an explicit boolean without unprojected native state')
    require(model.GroupValue.mate_ids == (mate.id,), 'group membership differs from its actual mate')
    entities = {value.id: value for value in graph.mate_entities}
    require(len(entities) == 2 and len(mate.entity_ids) == 2
            and len(set(mate.entity_ids)) == 2 and set(entities) == set(mate.entity_ids),
            'mate endpoint membership is incomplete or aliased')
    ends = tuple(read_end(entities[identity], model, checked) for identity in mate.entity_ids)
    require(ends[0].occurrence is not ends[1].occurrence, 'the two endpoints select the same occurrence')
    alignment = 1 if str(mate.alignment) == 'aligned' else 2
    product = sum(a * b for a, b in zip(ends[0].axis, ends[1].axis, strict=True))
    offset = tuple(b - a for a, b in zip(ends[0].origin_m, ends[1].origin_m, strict=True))
    slide = sum(value * axis for value, axis in zip(offset, ends[0].axis, strict=True))
    residual = sum((value - slide * axis) ** 2 for value, axis in zip(offset, ends[0].axis, strict=True))
    require(isclose(product, 1.0 if alignment == 1 else -1.0, rel_tol=0.0, abs_tol=1e-10)
            and residual <= 1e-20, 'the authored initial pose is not coaxial with its explicit alignment')
    return ConcentricIntent(document, model, mate, ends, model.FixedIndex, alignment, mate.attributes['rotation_locked'])
