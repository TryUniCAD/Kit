from convert.adapters.solidworks.Archive.Construction.OrderedMates.CheckPriorState import (
    CheckPriorState,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.MateContext import (
    MateContext,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.PlanarMateIn import (
    PlanarMateIn,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# ordinary continuation validates the actual published prior graph while preserving the existing empty context fresh state admission
def CheckMateState(
    Context: MateContext,
    InputValue: PlanarMateIn,
    Occurrences: tuple[ArchiveNode, ArchiveNode],
) -> None:
    if type(Context.PreviousValues) is not tuple:
        raise ValueError(
            "ordered context requires an explicit immutable prior mate sequence"
        )
    if Context.PreviousValues:
        CheckPriorState(Context, InputValue, Occurrences)
    if any(
        FieldInt(Value.FieldsValue, "f400") != 3
        or FieldInt(Value.FieldsValue, "f408")
        != int(bool(Context.PreviousValues) and Value is InputValue.FixedValue)
        for Value in Occurrences
    ):
        raise ValueError(
            "mate construction requires the qualified fresh solve state and actual fixed anchor"
        )
