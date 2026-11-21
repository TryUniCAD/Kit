from convert.adapters.solidworks.Archive.Partition.Fields.WorldShapes import (
    KWorldShapes,
)
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# local import topology lives outside the active world and both preceding world records
def MakeEmptyWorld(IndexValue: int, AliveValue: int, MarkId: int) -> XmtNode:
    FieldsValue = dict.fromkeys(
        (FieldValue.NameValue for FieldValue in KWorldShapes[101].FieldsValue), 0
    )
    FieldsValue.update(alive=AliveValue, highest_id=MarkId, current_id=MarkId)
    return XmtNode(IndexValue, 101, FieldsValue)
