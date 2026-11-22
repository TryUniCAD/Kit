from math import tau as FullTurn

from convert.Geometry.Revolve.FullPolySweep import BuildFullSweep
from convert.Geometry.Revolve.PolygonSweep import BuildPolySweep
from convert.Geometry.Revolve.SweepMetrics import MeasureInterval
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PartGeometry import (
    PartGeometry,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.Revolves.RevolveOwner import (
    RevolveOwner,
)
from interchange.Records.RecordTopology import TopologyCounts


# the actual directed sketch axis and ordered contour define the meridian without a saved kernel body
def BuildRevBody(OwnerValue: RevolveOwner, BodyId: str) -> PartGeometry:
    ProfileValue = OwnerValue.ProfileGraph
    LoopValue = ProfileValue.LoopValue
    AxisValue = OwnerValue.FrameValue
    LocalStart = ProfileValue.AxisPoints[
        ProfileValue.AxisValue.StartValue
    ].PositionValue
    LocalEnd = ProfileValue.AxisPoints[ProfileValue.AxisValue.EndValue].PositionValue
    if LocalStart[0] != LocalEnd[0]:
        raise ValueError("cache free revolve requires its vertical sketch axis")
    HeightSign = -1.0 if OwnerValue.IsReverse else 1.0
    CornerValues = tuple(
        LoopValue.PointsValue[KeyValue].PositionValue
        for KeyValue in LoopValue.OrderValue
    )
    Meridian = tuple(
        (PointValue[0] - LocalStart[0], HeightSign * (PointValue[1] - LocalStart[1]))
        for PointValue in CornerValues
    )
    Angle = OwnerValue.AngleValue.RadiansValue
    SweepArgs = (
        Meridian,
        AxisValue.StartValue,
        AxisValue.DirectionValue,
        AxisValue.SupportValue.x_axis,
    )
    ModelValue = (
        BuildFullSweep(BodyId, *SweepArgs)
        if Angle == FullTurn
        else BuildPolySweep(BodyId, *SweepArgs, 0.0, Angle)
    )
    if ModelValue.validate(frozenset((BodyId,))):
        raise ValueError(
            "cache free revolve geometry failed neutral boundary validation"
        )
    VolumeValue, AreaValue, BoundsValue = MeasureInterval(*SweepArgs, 0.0, Angle)
    TopologyValue = TopologyCounts(
        solid_count=len(ModelValue.bodies),
        shell_count=len(ModelValue.shells),
        face_count=len(ModelValue.faces),
        edge_count=len(ModelValue.edges),
        vertex_count=len(ModelValue.vertices),
        volume=VolumeValue,
        surface_area=AreaValue,
        bounding_box=BoundsValue,
        valid=True,
    )
    return PartGeometry(
        ModelValue,
        TopologyValue,
        {
            "method": "typed_parametric_ordinary_revolve",
            "revolve_feature_id": NativeNodeId(OwnerValue.NodeValue),
            "source_profile_id": NativeNodeId(OwnerValue.ProfileValue),
            "angle_radians": Angle,
            "reversed": OwnerValue.IsReverse,
        },
        ProducerValue=OwnerValue.NodeValue,
    )
