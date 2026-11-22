from itertools import product as Corners
from math import dist as Distance, isclose as IsClose

from convert.adapters.solidworks.Archive.Partition.ReadXmtVector import ReadXmtVector
from convert.adapters.solidworks.Core.TypedResolved.Fillets.FilletHistory import (
    FilletHistory,
)
from convert.adapters.solidworks.Core.TypedResolved.Fillets.Saved.CheckFilletFace import (
    CheckFilletFace,
)
from convert.adapters.solidworks.Core.TypedResolved.Fillets.Saved.CheckFilletRims import (
    CheckFilletRims,
)
from convert.adapters.solidworks.Core.TypedResolved.Fillets.Saved.FilletEdge import (
    FilletEdge,
)
from convert.adapters.solidworks.Core.TypedResolved.Fillets.Saved.ReadFilletEnds import (
    ReadStockPoint,
)


# measured round geometry must keep the expected tangencies on the actual convex stock corner
def CheckFilletGeom(
    History: FilletHistory,
    EdgeValue: FilletEdge,
    Bounds: tuple[tuple[float, float], ...],
    AxisIndex: int,
    Signs: tuple[int, ...],
) -> None:
    Nodes = History.StagesValue[0].NodesValue
    Radius = History.RadiusValue
    CrossAxes = tuple(Index for Index in range(3) if Index != AxisIndex)
    (Cylinder,) = (Value for Value in Nodes.values() if Value.KindValue == 51)
    Origin = ReadXmtVector(Cylinder, "pvec")
    Direction = ReadXmtVector(Cylinder, "axis")
    CheckFilletFace(History.StagesValue[1].NodesValue, Bounds)
    CheckFilletFace(Nodes, Bounds)
    CheckFilletRims(Nodes, Origin, Bounds, AxisIndex, Radius)
    Expected = set(Corners(*Bounds)).difference(EdgeValue.Endpoints)
    for Index, AxisSign in zip(CrossAxes, Signs, strict=True):
        Lower, Upper = Bounds[Index]
        if not 0 < Radius < (Upper - Lower) / 2 or not IsClose(
            Origin[Index],
            EdgeValue.Endpoints[0][Index] + AxisSign * Radius,
            rel_tol=0.0,
            abs_tol=1e-11,
        ):
            raise ValueError(
                "saved fillet carrier differs from its actual rounded corner"
            )
        for Endpoint in EdgeValue.Endpoints:
            PointValue = list(Endpoint)
            PointValue[Index] += AxisSign * Radius
            Expected.add(tuple(PointValue))
    Actual = tuple(
        ReadStockPoint(Nodes, Value.IndexValue)
        for Value in Nodes.values()
        if Value.KindValue == 18
    )
    if (
        abs(Direction[AxisIndex]) != 1.0
        or any(Direction[Index] != 0.0 for Index in CrossAxes)
        or len(Expected) != len(Actual)
        or any(
            sum(Distance(Point, Target) <= 1e-11 for Target in Expected) != 1
            for Point in Actual
        )
        or any(
            sum(Distance(Point, Target) <= 1e-11 for Point in Actual) != 1
            for Target in Expected
        )
    ):
        raise ValueError(
            "saved fillet carrier or tangent vertices differ from the actual edge"
        )
