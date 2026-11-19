from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Drawing.Construction.Notes.MakeNoteParagraph import (
    MakeNoteParagraph,
)


# a fresh line names the first and last authored text positions and leaves device metrics pending
def MakeNoteLine(LastValue: int, StyleValue: Mapping[str, object]) -> ArchiveNode:
    return ArchiveNode(
        RuntimeClass("moTextDataLineHead_c", 1),
        {
            "f08": 0,
            "f0c": LastValue,
            "f14": {"f00": 0.0, "f04": 0.0, "f08": 0.0},
            "f10": 0,
            "f30": MakeNoteParagraph(StyleValue, True),
            "f38": {"f00": 0.0, "f04": 0.0, "f08": 0.0},
            "f48": None,
            "f50": -1,
            "f58": 1.0,
            "f64": 0,
        },
    )
