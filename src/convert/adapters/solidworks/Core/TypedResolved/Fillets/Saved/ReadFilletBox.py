from itertools import product as Corners

from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyTree import (
    ReadBodyTree,
)
from convert.adapters.solidworks.Core.TypedResolved.Fillets.FilletHistory import (
    FilletHistory,
)
from convert.adapters.solidworks.Core.TypedResolved.Fillets.Saved.FilletEdge import (
    FilletEdge,
)
from convert.adapters.solidworks.Core.TypedResolved.Fillets.Saved.ReadFilletEnds import (
    ReadStockPoint,
)


# the prior body must own the eight corners of an axis aligned box and the full selected edge
def ReadFilletBox(
    History: FilletHistory,
    EdgeValue: FilletEdge,
) -> tuple[tuple[tuple[float, float], ...], int, tuple[int, ...]]:
    Previous = History.StagesValue[1].NodesValue
    TreeValue = ReadBodyTree(Previous)
    Points = {
        ReadStockPoint(Previous, IndexValue) for IndexValue in TreeValue.VertexIds
    }
    Bounds = tuple((min(Value), max(Value)) for Value in zip(*Points, strict=True))
    First, Final = EdgeValue.Endpoints
    AxisRoles = tuple(
        Index
        for Index, Values in enumerate(zip(First, Final, strict=True))
        if Values[0] != Values[1]
    )
    if (
        len(Points) != 8
        or Points != set(Corners(*Bounds))
        or len(AxisRoles) != 1
        or any(Lower >= Upper for Lower, Upper in Bounds)
    ):
        raise ValueError("saved fillet does not own an ordinary rectangular stock edge")
    (AxisIndex,) = AxisRoles
    if set((First[AxisIndex], Final[AxisIndex])) != set(Bounds[AxisIndex]):
        raise ValueError("saved fillet edge does not span its actual stock")
    CrossAxes = tuple(Index for Index in range(3) if Index != AxisIndex)
    Signs = tuple(1 if First[Index] == Bounds[Index][0] else -1 for Index in CrossAxes)
    return Bounds, AxisIndex, Signs
