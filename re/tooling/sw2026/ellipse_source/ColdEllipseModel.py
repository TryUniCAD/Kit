from dataclasses import dataclass
from math import atan2, degrees, hypot, isclose, isfinite
import re

from EllipseModel import require
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CheckPlainLinks import CheckPlainLinks
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadLength import ReadLength
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.RequireBossDef import RequireBossDef
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.RequirePlainDoc import RequirePlainDoc
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.Enums.EnumUnits import UnitSystem
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.GeometryConics import EllipseGeometry
from interchange.geometry.Models.Sketch import Sketch, SketchEntity
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordParameter import Parameter, ParameterValue
from interchange.Records.RecordSource import CadSource

FRONT, SKETCH, BOSS = "Front Plane", "EllipseProfile", "EllipseBoss"


@dataclass(frozen=True, slots=True)
class EllipsePlan:
    NameValue: str
    ConfigName: str
    PlaneName: str
    SketchName: str
    FeatureName: str
    DepthValue: float
    CenterValue: tuple[float, float]
    MajorValue: tuple[float, float]
    MinorValue: tuple[float, float]
    AxisValue: str = "z"
    DepthName: str = "D1"
    SecondDepth: None = None


def make_document(intent):
    require(type(intent) is dict and set(intent) == {"name", "center_mm", "major_xy", "radii_mm", "depth_mm"},
            "ellipse construction requires only typed sketch and live depth intent")
    center, direction, radii = (intent[name] for name in ("center_mm", "major_xy", "radii_mm"))
    require(all(type(value) is list and len(value) == 2 for value in (center, direction, radii))
            and all(type(value) in (int, float) and isfinite(value)
                    for value in (*center, *direction, *radii, intent["depth_mm"])),
            "ellipse intent requires finite pairs and a finite depth")
    entity = SketchEntity("entity/full-ellipse", GeometryKind.KEllipse,
                          EllipseGeometry(PlaneVector(*center), PlaneVector(*direction), *radii))
    sketch = Sketch("sketch/profile", SKETCH, "plane/front", (entity,),
                    closed_profile_entity_ids=((entity.id,),))
    length = ParameterValue(intent["depth_mm"], ValueKind.KLength, "mm")
    boss = FeatureStep("feature/boss", BOSS, FeatureKind.KExtrusion, 0, sketch_id=sketch.id,
                       parameter_ids=("parameter/depth",), operation=BooleanOp.KCreate,
                       definition=ExtrudeFeature(length, ExtrudeEnd.KBlind, False, False))
    return CadDocument(
        CadSource("kit-neutral", "<authored-in-memory>", "0" * 64),
        (Configuration("configuration/default", "Default", True),),
        (Parameter("parameter/depth", "D1", length, ParameterRole.KDriving, owner_id=boss.id),),
        (SupportPlane("plane/front", FRONT, Transform()),),
        (sketch,), (), (boss,), (DesignBody("body/boss", boss.name, boss.id),),
        metadata={"name": intent["name"]}, units=UnitSystem.KMillimeter,
    )


def plan_ellipse(document):
    RequirePlainDoc(document)
    feature, support, sketch = document.feature_timeline[0], document.support_planes[0], document.sketches[0]
    definition = RequireBossDef(feature)
    CheckPlainLinks(document, definition)
    require(document.units == UnitSystem.KMillimeter and support.name == FRONT
            and document.configurations[0].name == "Default" and len(sketch.entities) == 1
            and not (sketch.constraints or sketch.parameter_ids or sketch.suppressed or sketch.attributes or sketch.provenance),
            "cold ellipse needs a single free ordinary Front profile and default configuration")
    entity, = sketch.entities
    geometry = entity.geometry
    require(type(geometry) is EllipseGeometry and entity.kind == GeometryKind.KEllipse and
            sketch.closed_profile_entity_ids == ((entity.id,),)
            and not (entity.construction or entity.fixed or entity.attributes or entity.provenance),
            "cold ellipse needs its one actual free full closed entity")
    name = document.metadata.get("name")
    require(type(name) is str and re.fullmatch("Ellipse[A-Za-z0-9]{1,35}", name), "invalid authored part name")
    direction = geometry.major_axis.x, geometry.major_axis.y
    require(isclose(hypot(*direction), 1.0, rel_tol=0.0, abs_tol=1e-13),
            "ellipse needs an actual unit major direction")
    x, y = geometry.center.x, geometry.center.y
    a, b = geometry.major_radius, geometry.minor_radius
    angle = degrees(atan2(direction[1], direction[0]))
    depth = ReadLength(definition.length)
    require(1 <= abs(x) <= 80 and 1 <= abs(y) <= 80 and 5 <= b < a <= 55 and 1.2 <= a / b <= 3
            and 10 <= abs(angle) <= 70 and 0.003 <= depth <= 0.055,
            "ordinary cold ellipse is outside the noncircular signed positive-depth calibration scope")
    c = x / 1000, y / 1000
    cos, sin = direction
    return EllipsePlan(name, document.configurations[0].name, support.name, sketch.name, feature.name, depth, c,
                       (c[0] + a / 1000 * cos, c[1] + a / 1000 * sin),
                       (c[0] - b / 1000 * sin, c[1] + b / 1000 * cos))
