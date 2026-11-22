from math import tau as FullTurn

from convert.Geometry.Revolve.FullPolySweep import BuildFullSweep
from convert.Geometry.Revolve.PolygonSweep import BuildPolySweep
from convert.Geometry.Revolve.SweepMetrics import MeasureInterval
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PartGeometry import (
    PartGeometry,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Geometry.MakeRevMerid import (
    MakeRevMeridian,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.RevolveOwner import (
    RevolveOwner,
)
from interchange.Records.RecordTopology import TopologyCounts


# the actual directed sketch axis and ordered contour define the meridian without a saved kernel body
def BuildRevBody(OwnerValue: RevolveOwner, BodyId: str) -> PartGeometry:
    AxisValue = OwnerValue.FrameValue
    StartValue, EndValue = OwnerValue.EndValue.IntervalValue
    SweepArgs = (
        MakeRevMeridian(OwnerValue),
        AxisValue.StartValue,
        AxisValue.DirectionValue,
        AxisValue.SupportValue.x_axis,
    )
    ModelValue = (
        BuildFullSweep(BodyId, *SweepArgs)
        if EndValue - StartValue == FullTurn
        else BuildPolySweep(BodyId, *SweepArgs, StartValue, EndValue)
    )
    if ModelValue.validate(frozenset((BodyId,))):
        raise ValueError(
            "cache free revolve geometry failed neutral boundary validation"
        )
    VolumeValue, AreaValue, BoundsValue = MeasureInterval(
        *SweepArgs, StartValue, EndValue
    )
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
            "angle_radians": OwnerValue.AngleValue.RadiansValue,
            "reversed": OwnerValue.IsReverse,
        },
        ProducerValue=OwnerValue.NodeValue,
    )
