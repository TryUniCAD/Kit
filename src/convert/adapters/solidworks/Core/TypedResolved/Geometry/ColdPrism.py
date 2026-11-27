from convert.Geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
from convert.adapters.solidworks.Core.Native import NativeModel
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.VectorPlane import PlaneVector


# the cold part can derive its solid from the qualified native loop datum and depth
def ColdPrism(ModelValue: NativeModel, BodyId: str) -> BrepModel | None:
    if len(ModelValue.sketches) != 1 or len(ModelValue.operations) != 1:
        return None
    (SketchValue,) = ModelValue.sketches
    (Operation,) = ModelValue.operations
    LoopValue, FrameValue = SketchValue.TypedLines, SketchValue.TypedFrame
    DepthValue = Operation.length_mm
    if (
        LoopValue is None
        or FrameValue is None
        or Operation.kind != "join"
        or Operation.profile_id != SketchValue.object_id
        or DepthValue is None
        or type(Operation.direction_code) is not int
        or Operation.direction_code not in (0, 1)
        or Operation.termination_code != 0
    ):
        return None
    Segments = tuple(LoopValue.LinesValue[Index] for Index in LoopValue.OrderValue)
    Profile = tuple(
        LineGeometry(
            PlaneVector(*LoopValue.PointsValue[Segment.StartValue].PositionValue),
            PlaneVector(*LoopValue.PointsValue[Segment.EndValue].PositionValue),
        )
        for Segment in Segments
    )
    try:
        Model, _, _, _ = BuildPrism(
            BodyId,
            FrameValue,
            Profile,
            -DepthValue if Operation.direction_code == 1 else 0.0,
            0.0 if Operation.direction_code == 1 else DepthValue,
        )
    except (ValueError, OverflowError):
        return None
    return Model
