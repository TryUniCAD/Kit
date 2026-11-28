from convert.adapters.solidworks.Archive.Construction.Dimensions.DistanceInput import (
    DistanceInput,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeCommonView import (
    MakeCommonView,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeDistTail import (
    MakeDistTail,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the retained planar mate entry keeps its exact native text kind and distance tail while sharing the common display constructor
def MakeDisplayCore(
    HandleValue: ArchiveNode, InputValue: DistanceInput
) -> dict[str, object]:
    FieldsValue = MakeCommonView(
        HandleValue, InputValue.DesignIntent, InputValue.SelectedLeader, 18
    )
    FieldsValue.update(MakeDistTail())
    return FieldsValue
