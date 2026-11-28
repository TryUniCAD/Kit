from hashlib import sha256
from json import dumps

from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.Enums.EnumUnits import UnitSystem
from interchange.Enums.EnumValues import ValueKind
from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.GeometryCurves import (
    CircleGeometry,
    LineGeometry,
    PointGeometry,
)
from interchange.geometry.Models.Selection import Selection, SelectPathElem
from interchange.geometry.Models.Sketch import (
    ConstraintRef,
    Sketch,
    SketchEntity,
    SketchRelation,
)
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordParameter import Parameter, ParameterValue
from interchange.Records.RecordSource import CadSource

FRONT = ((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1))
RIGHT = ((0, 0, 0), (0, 0, -1), (0, 1, 0), (1, 0, 0))
NEGATIVE_FRONT = ((5, 20, 30), (1, 0, 0), (0, -1, 0), (0, 0, -1))
NEGATIVE_RIGHT = ((20, 10, 22), (0, 0, 1), (0, 1, 0), (-1, 0, 0))
AUTHORED = {
    "disclosed-initial": {
        "stocks": (
            (FRONT, (12, -12, 30, -4), 12, False),
            (RIGHT, (-16, 4, -2, 12), 10, False),
        ),
        "circle": (21, 0, 8),
        "selected": 0,
    },
    "disclosed-depth-edit": {
        "stocks": (
            (FRONT, (12, -12, 30, -4), 12, False),
            (RIGHT, (-16, 4, -2, 12), 29, False),
        ),
        "circle": (21, 0, 8),
        "selected": 0,
    },
    "signed-metre": {
        "stocks": (
            (NEGATIVE_FRONT, (-9, -11, 7, -1), 10, False),
            (NEGATIVE_RIGHT, (-7, -8, 4, 1), 12, False),
        ),
        "circle": (0, 1, 4.75),
        "selected": 0,
        "metre_coordinates": True,
    },
    "right-selected-reversed": {
        "stocks": (
            (FRONT, (-11, 21, 4, 32), 9, False),
            (((14, 0, 0), *NEGATIVE_RIGHT[1:]), (-6, -7, 8, 11), 7.5, True),
        ),
        "circle": (-7.5, 1, 5),
        "selected": 1,
        "result_first": True,
    },
    "interior-tunnel": {
        "stocks": (
            (FRONT, (-8, -9, 12, 3), 6.5, True),
            (RIGHT, (2, 14, 13, 26), 9, False),
        ),
        "circle": (2, -2, 2.25),
        "selected": 0,
    },
}


def rectangle(identity, support, bounds, factor):
    x0, y0, x1, y1 = (value * factor for value in bounds)
    points = tuple(
        PlaneVector(*coords) for coords in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))
    )
    entities = tuple(
        SketchEntity(
            f"{identity}:edge:{index}", GeometryKind.KLine, LineGeometry(first, last)
        )
        for index, (first, last) in enumerate(
            zip(points, (*points[1:], points[0]), strict=True)
        )
    )
    constraints = tuple(
        SketchRelation(f"{entity.id}:axis", axis, (ConstraintRef(entity.id),))
        for entity, axis in zip(
            entities, ("horizontal", "vertical", "horizontal", "vertical"), strict=True
        )
    )
    return Sketch(
        identity,
        identity,
        support,
        entities,
        constraints,
        closed_profile_entity_ids=(tuple(entity.id for entity in entities),),
    )


def authored_document(values):
    factor = 0.001 if values.get("metre_coordinates") else 1.0
    stocks = []
    planes, sketches, drivers, operations = [], [], [], []
    for index, (pose, rectangle_bounds, depth, reverse) in enumerate(values["stocks"]):
        identity = f"stock:{index + 1}"
        support_id, sketch_id, driver_id = (
            f"{identity}:{suffix}" for suffix in ("plane", "profile", "D1")
        )
        origin, *axes = pose
        frame = Transform(
            SpaceVector(*(v * factor for v in origin)),
            *(SpaceVector(*axis) for axis in axes),
        )
        planes.append(SupportPlane(support_id, support_id, frame))
        sketches.append(rectangle(sketch_id, support_id, rectangle_bounds, factor))
        param = ParameterValue(depth, ValueKind.KLength, "mm")
        drivers.append(Parameter(driver_id, "D1", param, owner_id=identity))
        operations.append(
            FeatureStep(
                identity,
                identity,
                FeatureKind.KExtrusion,
                index,
                sketch_id=sketch_id,
                parameter_ids=(driver_id,),
                operation=BooleanOp.KCreate,
                definition=ExtrudeFeature(param, reversed=reverse),
            )
        )
        stocks.append((identity, support_id, frame.z_axis, reverse))
    selected, untouched = stocks[values["selected"]], stocks[1 - values["selected"]]
    chosen, support, normal, reverse = selected
    direction = SpaceVector(
        *(sign * (-1 if reverse else 1) for sign in (normal.x, normal.y, normal.z))
    )
    x, y, radius = (value * factor for value in values["circle"])
    center = PlaneVector(x, y)
    entity = SketchEntity(
        "cut:circle", GeometryKind.KCircle, CircleGeometry(center, radius)
    )
    point = SketchEntity("cut:center", GeometryKind.KPoint, PointGeometry(center))
    sketches.append(
        Sketch(
            "cut:profile",
            "Cut profile",
            support,
            (entity, point),
            closed_profile_entity_ids=((entity.id,),),
        )
    )
    selection = Selection(
        "cut:selection", "Selected stock", (SelectPathElem("feature", chosen, "body"),)
    )
    operations.append(
        FeatureStep(
            "cut",
            "Through cut",
            FeatureKind.KExtrusion,
            2,
            input_feature_ids=(chosen,),
            sketch_id="cut:profile",
            selection_ids=(selection.id,),
            operation=BooleanOp.KCutOperation,
            definition=ExtrudeFeature(
                end_condition=ExtrudeEnd.KThroughAll, direction=direction
            ),
        )
    )
    bodies = (
        DesignBody("body:untouched", "Untouched stock", untouched[0]),
        DesignBody("body:result", "Cut result", "cut"),
    )
    return CadDocument(
        CadSource(
            "kit.neutral",
            "authored two stock intent",
            sha256(dumps(values, sort_keys=True).encode()).hexdigest(),
        ),
        (Configuration("cfg", "Default", active=True),),
        tuple(drivers),
        tuple(planes),
        tuple(sketches),
        (selection,),
        tuple(operations),
        bodies[::-1] if values.get("result_first") else bodies,
        units=UnitSystem.KMeter if factor != 1.0 else UnitSystem.KMillimeter,
    )
