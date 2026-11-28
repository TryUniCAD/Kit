from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Drawing.Construction.Notes.MakeNoteGlyph import (
    MakeNoteGlyph,
)
from convert.adapters.solidworks.Drawing.Construction.Notes.MakeNoteLine import (
    MakeNoteLine,
)


# the native text array grows with the authored code units and retains a separate leading line owner
def MakeNoteTokens(TextValue: str, StyleValue: Mapping[str, object]) -> ArchiveNode:
    Units = TextValue.encode("utf-16-le")
    Glyphs = tuple(
        MakeNoteGlyph(
            int.from_bytes(Units[AtValue : AtValue + 2], "little"), AtValue // 2
        )
        for AtValue in range(0, len(Units), 2)
    )
    LineValue = MakeNoteLine(len(Glyphs) - 1, StyleValue)
    Items = tuple({"o": NodeValue} for NodeValue in (LineValue, *Glyphs))
    return ArchiveNode(
        RuntimeClass("moGenTextDataList_c", 1),
        {
            "f10": ArchiveNode(
                RuntimeClass("suObArray", 1), {"n": len(Items), "items": Items}
            ),
            "f18": {"f00": 0.0, "f08": 0.0, "f10": 0.0, "f18": 0.0},
            "f128": 0,
        },
    )
