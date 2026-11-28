from math import pi

from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import PrincipalFrame
from interchange import SweepFeature
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.Enums.EnumValues import ValueKind
from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.GeometryCurves import ArcGeometry, CircleGeometry
from interchange.geometry.Models.Sketch import ConstraintRef, Sketch, SketchEntity, SketchRelation
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.materials.MaterialRecord import MaterialRecord
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordParameter import Parameter, ParameterValue
from interchange.Records.RecordSource import CadSource


SECTION, PATH, SWEEP = "SweepSection", "SweepPath", "OrdinarySweptBoss"


def neutral_support(identifier, name, axis):
    frame = PrincipalFrame(axis)
    return SupportPlane(identifier, name, Transform(
        *(SpaceVector(*vector) for vector in (frame.OriginValue, frame.AxisU, frame.AxisV, frame.NormalValue))
    ))


def neutral_section(radius_mm):
    entity = SketchEntity("section-circle", GeometryKind.KCircle, CircleGeometry(PlaneVector(0.0, 0.0), radius_mm))
    center = ConstraintRef(entity.id, "center")
    diameter = Parameter("circle-diameter", "D1", ParameterValue(radius_mm * 2, ValueKind.KLength, "mm"), owner_id="section-sketch")
    rows = (SketchRelation("section-origin", "fixed", (center,)),
            SketchRelation("section-diameter", "diameter", (ConstraintRef(entity.id),), diameter.id))
    sketch = Sketch("section-sketch", SECTION, "right", (entity,), rows, (diameter.id,), ((entity.id,),))
    return sketch, diameter


def neutral_path(radius_mm):
    entity = SketchEntity("path-arc", GeometryKind.KArcGeometry,
                         ArcGeometry(PlaneVector(0.0, radius_mm), radius_mm, -pi / 2, 0.0))
    center, start, end = (ConstraintRef(entity.id, point) for point in ("center", "start", "end"))
    radius = Parameter("arc-radius", "D1", ParameterValue(radius_mm, ValueKind.KLength, "mm"), owner_id="path-sketch")
    rows = (
        SketchRelation("path-origin", "fixed", (start,)),
        SketchRelation("path-vertical", "vertical", (center, start)),
        SketchRelation("path-horizontal", "horizontal", (end, center)),
        SketchRelation("path-radius", "radius", (ConstraintRef(entity.id),), radius.id),
    )
    return Sketch("path-sketch", PATH, "front", (entity,), rows, (radius.id,)), radius


def neutral_document(name, section_radius, path_radius, density):
    section, diameter = neutral_section(section_radius * 1000.0)
    path, radius = neutral_path(path_radius * 1000.0)
    step = FeatureStep("sweep-boss", SWEEP, FeatureKind.KSweep, 1, sketch_id=section.id,
                       operation=BooleanOp.KCreate, definition=SweepFeature(path.id))
    body = DesignBody("swept-solid", SWEEP, step.id)
    physical = Parameter("body-density", "Density", ParameterValue(density, ValueKind.KQuantity, "kg/m3"), owner_id=body.id)
    return CadDocument(CadSource("neutral", "", ""), (Configuration("default", "Default", True),),
                       (diameter, radius, physical),
                       (neutral_support("front", "Front Plane", "z"), neutral_support("right", "Right Plane", "x"),
                        neutral_support("top", "Top Plane", "y")),
                       (section, path), (), (step,), (body,), metadata={"name": name})
