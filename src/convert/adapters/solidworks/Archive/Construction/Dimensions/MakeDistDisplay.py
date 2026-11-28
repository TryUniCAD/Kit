from convert.adapters.solidworks.Archive.Construction.Dimensions.DistanceInput import (
    DistanceInput,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.LinearStyle import (
    LinearStyle,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeDisplayCore import (
    MakeDisplayCore,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# the real model handle and projected document style complete an ordinary distance display while geometric caches retain justified constructor state
def MakeDistDisplay(
    OwnerValue: ArchiveNode,
    HandleValue: ArchiveNode,
    InputValue: DistanceInput,
    StyleValue: LinearStyle,
) -> ArchiveNode:
    FieldsValue = MakeDisplayCore(HandleValue, InputValue)
    FieldsValue.update(StyleValue.ProjectionValue)
    FieldsValue["owner"] = OwnerValue
    FieldsValue["f8a4"] = (FieldInt(FieldsValue, "f8a4") & ~0x50) | StyleValue.UnderText
    FieldsValue["fb64"] = (
        FieldInt(FieldsValue, "fb64") & ~0x103000
    ) | StyleValue.FlagValue
    return ArchiveNode(RuntimeClass("moDisplayDistanceDim_c", 1), FieldsValue)
