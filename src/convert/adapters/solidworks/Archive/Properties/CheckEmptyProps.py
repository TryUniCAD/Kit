from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# property list validation must bind the concrete file and cut list owners before testing their contents
def ReadPropChild(NodeValue: object, ClassName: str) -> ArchiveNode:
    if not isinstance(NodeValue, ArchiveNode) or NodeValue.ClassValue != RuntimeClass(
        ClassName, 1
    ):
        raise ValueError("part property manager has an unexpected native owner")
    return NodeValue


# present advanced containers can be admitted only when every property scope is empty
def CheckEmptyProps(RootValue: ArchiveNode) -> None:
    FieldsValue = RootValue.FieldsValue
    StateValue = (FieldsValue["f0c"], FieldsValue["f08"], FieldsValue["f54"])
    RowsValue = CastValue(tuple[dict[str, object], ...], FieldsValue["f20"])
    if StateValue == (-1, 0, 0) and not RowsValue:
        return
    if len(RowsValue) != 1 or RowsValue[0]["key"] != 0:
        raise ValueError(
            "part property manager policy is outside the compatible profile"
        )
    Container = ReadPropChild(RowsValue[0]["o"], "moCusPropContainer_c").FieldsValue
    FileValue = ReadPropChild(Container["f08"], "moFilePropContainer_c").FieldsValue
    CutValue = ReadPropChild(Container["f10"], "moCutListPropContainer_c").FieldsValue
    if (
        FileValue["f08"] is not None
        or FileValue["f10"] is not None
        or CutValue["f08"]
        or CutValue["f38"]
        or Container["f18"] is not None
    ):
        raise ValueError(
            "unsupported SOLIDWORKS native field path populated advanced property manager"
        )
    if StateValue != (-1, 1, 0) or Container["f20"] != 0:
        raise ValueError(
            "part property manager policy is outside the compatible profile"
        )
