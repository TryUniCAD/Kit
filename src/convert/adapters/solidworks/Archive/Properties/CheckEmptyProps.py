from collections.abc import Mapping, Sequence
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# an empty proof must bind each actual concrete scope rather than treating an absent row as an owner
def RequireOwner(NodeValue: object, ClassName: str) -> Mapping[str, object]:
    if not isinstance(NodeValue, ArchiveNode) or NodeValue.ClassValue != RuntimeClass(
        ClassName, 1
    ):
        raise ValueError("part property manager has an unexpected native owner")
    return NodeValue.FieldsValue


# all advanced file and cut list scopes must be empty before a legacy text absence proof
def CheckEmptyProps(RootValue: ArchiveNode) -> None:
    FieldsValue = RootValue.FieldsValue
    StateValue = (FieldsValue["f0c"], FieldsValue["f08"], FieldsValue["f54"])
    RowsValue = CastValue(Sequence[Mapping[str, object]], FieldsValue["f20"])
    if StateValue == (-1, 0, 0) and not RowsValue:
        return
    if StateValue != (-1, 1, 0) or len(RowsValue) != 1 or RowsValue[0]["key"] != 0:
        raise ValueError("part property manager policy is outside the empty profile")
    Container = RequireOwner(RowsValue[0]["o"], "moCusPropContainer_c")
    FileValue = RequireOwner(Container["f08"], "moFilePropContainer_c")
    CutValue = RequireOwner(Container["f10"], "moCutListPropContainer_c")
    if (
        FileValue["f08"] is not None
        or FileValue["f10"] is not None
        or CutValue["f08"]
        or CutValue["f38"]
        or Container["f18"] is not None
        or Container["f20"] != 0
    ):
        raise ValueError("legacy part property manager has nonempty native scopes")
