from collections.abc import Mapping, Sequence
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# concrete archive owners prevent lookup through an unresolved or unrelated node
def RequireNode(NodeValue: object, ClassName: str) -> ArchiveNode:
    if (
        not isinstance(NodeValue, ArchiveNode)
        or not isinstance(NodeValue.ClassValue, RuntimeClass)
        or NodeValue.ClassValue.NameValue != ClassName
    ):
        raise ValueError(f"planar mate graph expected concrete {ClassName}")
    return NodeValue


# embedded records carry fields without a separately allocated class slot
def RequireRecord(RecordValue: object) -> Mapping[str, object]:
    if not isinstance(RecordValue, Mapping):
        raise ValueError("planar mate graph expected an embedded record")
    return CastValue(Mapping[str, object], RecordValue)


# identity and flag fields require integers from their typed wire owners
def FieldInt(Values: Mapping[str, object], FieldName: str) -> int:
    ItemValue = Values.get(FieldName)
    if type(ItemValue) is not int:
        raise ValueError(f"planar mate graph expected integer {FieldName}")
    return ItemValue


# native names must have a real serialized owner before they can identify a datum
def FieldText(Values: Mapping[str, object], FieldName: str) -> str:
    ItemValue = Values.get(FieldName)
    if type(ItemValue) is not str or not ItemValue:
        raise ValueError(f"planar mate graph expected text {FieldName}")
    return ItemValue


# object names must come from their typed node owner before projection
def ReadNodeName(NodeValue: ArchiveNode) -> str:
    NameNode = RequireNode(NodeValue.FieldsValue.get("f18"), "moNodeName_c")
    return FieldText(NameNode.FieldsValue, "f08")


# collection framing must retain complete ordered records for ownership checks
def ReadRows(RowsValue: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(RowsValue, (list, tuple)):
        raise ValueError("planar mate graph expected an ordered record collection")
    return tuple(
        RequireRecord(ItemValue) for ItemValue in CastValue(Sequence[object], RowsValue)
    )
