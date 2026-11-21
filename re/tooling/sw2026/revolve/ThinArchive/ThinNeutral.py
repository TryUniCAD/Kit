from math import pi, radians

from AuditRevEndOwners import require
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CheckPartLinks import CheckPartLinks
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.ReadRevDriver import ReadRevDriver
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.ReadRevSelect import ReadRevSelect
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.RequireRevDoc import RequireRevDoc
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.RevolvePlan import RevolvePlan
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.Enums.EnumUnits import UnitSystem
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Features.FeatureAngleRev import AngularRevolve
from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Selection import SelectPathElem, Selection
from interchange.geometry.Models.Sketch import Sketch, SketchEntity
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordParameter import Parameter, ParameterValue
from interchange.Records.RecordSource import CadSource

MODES = {"one": 0, "opposite": 1, "midplane": 2, "two": 3}
DRIVER = "feature/revolve"
FIRST_WALL, SECOND_WALL = "parameter/first-wall", "parameter/second-wall"
ANGLE = "parameter/angle"


def make_model(case):
    def line(label, x, span, construction=False):
        start, end = [PlaneVector(x * 1000, y * 1000) for y in span]
        return SketchEntity(label, GeometryKind.KLine, LineGeometry(start, end), construction=construction)

    def driver(name, identity, value):
        return Parameter(identity, name, value, ParameterRole.KDriving, owner_id=DRIVER)

    axis_x = case["axis_x_m"]
    axis = line("axis/centre", axis_x, case["axis_axial_m"], True)
    wall = line("profile/open", axis_x + case["profile_radius_m"], case["axial_m"])
    plane = SupportPlane("plane/front", "Front Plane", Transform())
    sketch = Sketch("sketch/profile", "RevolveSketch", plane.id, (wall, axis))
    selection = Selection("selection/axis", "Selected construction axis", (
        SelectPathElem("sketch", sketch.id), SelectPathElem("sketch_entity", axis.id)))
    direction = SpaceVector(0, -1 if case["reverse"] else 1, 0)
    definition = AngularRevolve(selection.id, ANGLE,
        SpaceVector(axis.geometry.start.x, axis.geometry.start.y, 0), direction)
    parameters = (driver("D1", ANGLE, ParameterValue(radians(case["angle_deg"]), ValueKind.KAngle, "rad")),
                  driver("D3", FIRST_WALL, ParameterValue(case["wall_m"][0] * 1000, ValueKind.KLength, "mm")))
    mode = case["wall_mode"]
    if mode == "two":
        parameters += (driver("D4", SECOND_WALL, ParameterValue(case["wall_m"][1] * 1000, ValueKind.KLength, "mm")),)
    feature = FeatureStep(DRIVER, "ThinBossRevolve", FeatureKind.KRevolution, 0,
        sketch_id=sketch.id, parameter_ids=tuple(p.id for p in parameters), operation=BooleanOp.KCreate,
        definition=definition, selection_ids=(selection.id,))
    body = DesignBody("body/revolve", feature.name, feature.id)
    return CadDocument(CadSource("kit-neutral", "<authored-thin-research>", "0" * 64),
                       (Configuration("configuration/default", "Default", True),), parameters,
                       (plane,), (sketch,), (selection,), (feature,), (body,),
                       metadata={"name": case["name"]}, units=UnitSystem.KMillimeter)


def points(entity, axis):
    geometry = entity.geometry
    require(entity.kind == GeometryKind.KLine and type(geometry) is LineGeometry
            and entity.construction is axis and not entity.fixed and not entity.attributes,
            "thin profile requires its plain line and distinct construction axis")
    return tuple((RequireScalar(p.x) * 0.001, RequireScalar(p.y) * 0.001) for p in (geometry.start, geometry.end))


def width(parameter, owner, name):
    require(parameter.name == name and parameter.owner_id == owner and parameter.role == ParameterRole.KDriving
            and parameter.expression is None and not parameter.attributes
            and parameter.value.kind == ValueKind.KLength and parameter.value.unit == "mm",
            "thin wall requires its own editable neutral millimetre driver")
    return RequireScalar(parameter.value.value) * 0.001


def plan_thin(doc, mode):
    RequireRevDoc(doc)
    plane = CheckPartLinks(doc)
    (feature,) = doc.feature_timeline
    definition = feature.definition
    require(mode in MODES and plane.transform == Transform() and type(definition) is AngularRevolve
            and definition.SideMode == "one_sided" and feature.kind == FeatureKind.KRevolution
            and feature.order == 0 and feature.operation == BooleanOp.KCreate and not feature.suppressed
            and not feature.input_feature_ids and not feature.configuration_states and not feature.attributes,
            "thin research construction requires one Forward Front blind boss")
    (sketch,) = doc.sketches
    axis_id = ReadRevSelect(doc, definition)
    require(len(sketch.entities) == 2 and not sketch.constraints and not sketch.closed_profile_entity_ids
            and not sketch.attributes and not sketch.suppressed and not sketch.parameter_ids,
            "thin profile must contain two actual independent open lines")
    wall, axis = sketch.entities
    require(axis.id == axis_id, "thin sketch axis must follow its open body line")
    start, end = points(axis, True)
    edge = points(wall, False)
    x, low = edge[0]
    _, high = edge[1]
    require(start[0] == end[0] < x == edge[1][0] and start[1] < low < high < end[1]
            and definition.AxisDirection == SpaceVector(0, 1, 0)
            and definition.AxisOrigin == SpaceVector(axis.geometry.start.x, axis.geometry.start.y, 0),
            "thin profile and actual upward axis must be separate and ordered")
    ids = (definition.AlongParameterId, FIRST_WALL) + ((SECOND_WALL,) if mode == "two" else ())
    params = {parameter.id: parameter for parameter in doc.parameters}
    require(feature.parameter_ids == ids and set(params) == set(ids), "unqualified thin driver inventory")
    angle = ReadRevDriver(params[ids[0]], feature.id, "D1")
    first = width(params[ids[1]], feature.id, "D3")
    second = width(params[ids[2]], feature.id, "D4") if mode == "two" else 0.0
    require(0 < angle < pi and 0 < first < x - start[0]
            and (mode != "two" or 0 < second < x - start[0] and second != first),
            "thin wall and angle must stay inside the measured open-sector domain")
    plan = RevolvePlan(doc.metadata["name"], doc.configurations[0].name, plane.name, sketch.name, feature.name,
                       edge, start, end, angle, False, sketch.id, feature.id, ids[0], doc.bodies[0].id,
                       definition.AxisSelectionId, axis_id, UnaryRules=(), EqualRule=None)
    return plan, MODES[mode], (first, second)
