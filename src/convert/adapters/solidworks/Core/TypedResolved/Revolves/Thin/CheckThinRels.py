from collections.abc import Mapping
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.CheckDimGroups import (
    CheckDimGroups,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadDimRows import (
    ReadDimRows,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.CheckLineScope import (
    CheckLineScope,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord


# the measured open profile has no solver rows or hidden region owners
def CheckThinRels(FieldsValue: Mapping[str, object]) -> None:
    CheckLineScope(FieldsValue, HasDrivers=True)
    GroupsValue = NativeRecord(FieldsValue.get("dims"))
    CheckDimGroups(GroupsValue)
    if (
        ReadDimRows(GroupsValue, "ng2", "val_g2")
        or ReadDimRows(GroupsValue, "nlog1", "log_g1")
        or not IsLineState(GroupsValue.get("f118"))
    ):
        raise ValueError("SOLIDWORKS thin sketch has unqualified solver relations")
