from hashlib import sha256

from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.Enums.EnumValues import ValueKind
from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.GeometryCurves import CircleGeometry, LineGeometry, PointGeometry
from interchange.geometry.Models.Selection import SelectPathElem, Selection
from interchange.geometry.Models.Sketch import ConstraintRef, Sketch, SketchEntity, SketchRelation
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordParameter import Parameter, ParameterValue
from interchange.Records.RecordSource import CadSource


NAME = "GeneratedTwoStockGraph01"
LOCATOR = rf"C:\KitSdkCandidates\{NAME}.SLDPRT"
EPOCH = 1765500071
FRONT = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
RIGHT = ((0, 0, -1), (0, 1, 0), (1, 0, 0))


def stock(index, name, profile, basis, limits, depth):
    feature_id = f"stock:{index}"
    plane_id = f"{feature_id}:plane"
    sketch_id = f"{feature_id}:profile"
    driver_id = f"{feature_id}:D1"
    frame = Transform(SpaceVector(0, 0, 0), *(SpaceVector(*axis) for axis in basis))
    plane = SupportPlane(plane_id, plane_id, frame)
    x0, y0, x1, y1 = limits
    corners = tuple(PlaneVector(x, y) for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)))
    edges = tuple(
        SketchEntity(f"{sketch_id}:edge:{i}", GeometryKind.KLine, LineGeometry(first, second))
        for i, (first, second) in enumerate(zip(corners, (*corners[1:], corners[0]), strict=True))
    )
    constraints = tuple(
        SketchRelation(f"{edge.id}:axis", axis, (ConstraintRef(edge.id),))
        for edge, axis in zip(edges, ("horizontal", "vertical", "horizontal", "vertical"), strict=True)
    )
    sketch = Sketch(sketch_id, profile, plane_id, edges, constraints,
                    closed_profile_entity_ids=(tuple(edge.id for edge in edges),))
    length = ParameterValue(depth, ValueKind.KLength, "mm")
    driver = Parameter(driver_id, "D1", length, owner_id=feature_id)
    operation = FeatureStep(
        feature_id, name, FeatureKind.KExtrusion, index - 1, sketch_id=sketch_id,
        parameter_ids=(driver_id,), operation=BooleanOp.KCreate, definition=ExtrudeFeature(length),
    )
    return plane, sketch, driver, operation


def selected_stock_document(*, alternate=False):
    if alternate:
        stocks = (
            stock(1, "Independent forward prism", "Front rectangle profile", FRONT, (-9, -15, 19, -1), 13.625),
            stock(2, "Separate right stock", "Right rectangle profile", RIGHT, (-20, 8, -6, 19), 31.875),
        )
        model_name, sketch_name, cut_name, radius, center = (
            "IndependentStockBore", "Free closed circle", "Explicit through cut", 2.375, PlaneVector(5, -7)
        )
    else:
        stocks = (
            stock(1, "SteadyStock", "SteadyProfile", FRONT, (12, -12, 30, -4), 12),
            stock(2, "MovingStock", "MovingProfile", RIGHT, (-16, 4, -2, 12), 10),
        )
        model_name, sketch_name, cut_name, radius, center = NAME, "ThroughProfile", "ThroughFeature", 8, PlaneVector(21, 0)
    planes, sketches, drivers, features = (tuple(values) for values in zip(*stocks, strict=True))
    circle = SketchEntity("cut:circle", GeometryKind.KCircle, CircleGeometry(center, radius))
    point = SketchEntity("cut:center", GeometryKind.KPoint, PointGeometry(center))
    profile = Sketch("cut:profile", sketch_name, planes[0].id, (circle, point),
                     closed_profile_entity_ids=((circle.id,),))
    choice = Selection("cut:selection", "Selected stock", (SelectPathElem("feature", features[0].id, "body"),))
    through = FeatureStep(
        "cut", cut_name, FeatureKind.KExtrusion, 2,
        input_feature_ids=(features[0].id,), sketch_id=profile.id, selection_ids=(choice.id,),
        operation=BooleanOp.KCutOperation,
        definition=ExtrudeFeature(None, end_condition=ExtrudeEnd.KThroughAll, direction=SpaceVector(0, 0, 1)),
    )
    bodies = (
        DesignBody("body:untouched", features[1].name, features[1].id),
        DesignBody("body:result", through.name, through.id),
    )
    return CadDocument(
        CadSource("kit.neutral", "independent modeled stock intent", sha256(model_name.encode()).hexdigest()),
        (Configuration("cfg", "Default", active=True),), drivers, planes, (*sketches, profile), (choice,),
        (*features, through), bodies, metadata={"name": model_name},
    )
