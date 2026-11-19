from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeDisplayFields import (
    MakeDisplayFields,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakePoint import (
    MakePoint,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Drawing.Construction.Notes.MakeNoteStyleFields import (
    MakeNoteStyleFields,
)
from convert.adapters.solidworks.Drawing.Construction.Notes.MakeNoteTail import (
    MakeNoteTail,
)


# the display combines the shared drawing item with the ordinary note style and actual local reference
def MakeNoteDisplay(
    ReferenceValue: ArchiveNode, StyleValue: Mapping[str, object], VersionValue: int
) -> ArchiveNode:
    Points = tuple({"p": MakePoint()} for _ in range(4))
    Vectors = tuple({"v": MakePoint(YValue=1.0)} for _ in range(2))
    FieldsValue = MakeDisplayFields(VersionValue, 0x82 | (1 << 19))
    FieldsValue.update(MakeNoteStyleFields(StyleValue))
    FieldsValue.update(MakeNoteTail(StyleValue))
    FieldsValue.update(
        f48=ReferenceValue,
        f2b0=(),
        n2b0=0,
        f3c0=(),
        n3d0=0,
        f2e0=(),
        n2e8=0,
        f4a8=(),
        n4a8=0,
        f4f0=Points,
        n4f0=len(Points),
        f550=Vectors,
        n550=len(Vectors),
    )
    return ArchiveNode(RuntimeClass("moDisplayNote_c", 1), FieldsValue)
