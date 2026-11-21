from convert.adapters.solidworks.Archive.Construction.Dimensions.DistanceInput import (
    DistanceInput,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeDistance import (
    MakeDistance,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.ReadLinearStyle import (
    ReadLinearStyle,
)
from convert.adapters.solidworks.Archive.Construction.PlanarDistance.CheckDistCtx import (
    CheckDistCtx,
)
from convert.adapters.solidworks.Archive.Construction.PlanarDistance.CheckDistPlanes import (
    CheckDistPlanes,
)
from convert.adapters.solidworks.Archive.Construction.PlanarDistance.MakeDistBase import (
    MakeDistBase,
)
from convert.adapters.solidworks.Archive.Construction.PlanarDistance.RequireIdRoom import (
    RequireIdRoom,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.MakeDetached import (
    MakeDetached,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.MakeEndpoint import (
    MakeEndpoint,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.MakeResolved import (
    MakeResolved,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.MateContext import (
    MateContext,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.PlanarMateIn import (
    PlanarMateIn,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# driving planar distance construction retains its complete actual graph and consumes dimension identity before mate and wrapper publication
def MakeDistMateMut(
    Context: MateContext, InputValue: PlanarMateIn, DimensionInput: DistanceInput
) -> ArchiveNode:
    _ = CheckDistCtx(Context, InputValue)
    First, Second = (
        MakeEndpoint(Context.AssemblyValue, Value) for Value in InputValue.Selections
    )
    _ = CheckDistPlanes((First, Second))
    Resolved = tuple(MakeResolved(Value) for Value in (First, Second))
    Detached = [
        {"k": Index, "o": MakeDetached(Value, Context)}
        for Index, Value in enumerate((First, Second))
    ]
    StyleValue = ReadLinearStyle(Context.AssemblyValue)
    MateValue = MakeDistBase(Context, InputValue)
    GraphValue = MakeDistance(MateValue, DimensionInput, StyleValue)
    MateValue.FieldsValue.update(
        {
            "f3c8": Detached,
            "f410": [{"o": Value} for Value in Resolved],
            "f4b8": GraphValue.DisplayValue,
        }
    )
    RequireIdRoom(Context.Allocator)
    _ = Context.Allocator.AllocateMut(GraphValue.DimensionValue, "f50")
    MateId = Context.Allocator.AllocateMut(MateValue)
    Counter = FieldInt(Context.AssemblyValue.FieldsValue, "fd48")
    for Index, Wrapper in enumerate(Resolved):
        Wrapper.FieldsValue.update(
            {"f74": MateId, "f78": Counter + Index, "f7c": Index}
        )
    Context.AssemblyValue.FieldsValue["fd48"] = Counter + 2
    InputValue.FixedValue.FieldsValue["f408"] = 1
    return MateValue
