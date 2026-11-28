from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.Shells.Cache.ReadShellAttrs import (
    ReadShellAttrs,
)


# native face keys need their actual owner and creator event before a role can resolve
def ReadShellFace(
    NodesValue: Mapping[int, XmtNode],
    FaceValue: XmtNode,
    CreatorId: int,
    EpochValue: int,
) -> tuple[int, int] | None:
    Attribute = ReadShellAttrs(NodesValue, FaceValue).get("FACE_ID_2001")
    if Attribute is None:
        return None
    Definition = RequireXmt(NodesValue, Attribute.Integer("definition"), 80)
    FieldsValue = Attribute.Indexes("fields")
    if (
        Definition.Indexes("fields") != (9, 9, 1, 1)
        or len(FieldsValue) != 4
        or FieldsValue[:2] != (0, 0)
    ):
        raise ValueError("SOLIDWORKS shell face uses an unqualified identity attribute")
    WordsValue = RequireXmt(NodesValue, FieldsValue[2], 82).Indexes("values")
    if WordsValue[1:3] != (CreatorId, EpochValue):
        return None
    if (
        len(WordsValue) == 6
        and WordsValue[0] == 40
        and WordsValue[3] == WordsValue[5] == 0
        and WordsValue[4] in (0, 1)
    ) or (
        len(WordsValue) == 5
        and WordsValue[0] == 74
        and WordsValue[3] == 0
        and WordsValue[4] > 0
    ):
        return WordsValue[0], WordsValue[4]
    raise ValueError("SOLIDWORKS shell face uses an unknown stock role")
