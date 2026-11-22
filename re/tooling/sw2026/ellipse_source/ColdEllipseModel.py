from math import isfinite

from EllipseModel import require
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
