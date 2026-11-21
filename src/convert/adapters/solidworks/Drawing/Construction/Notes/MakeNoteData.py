from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeObList import (
    MakeObList,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# the actual local note data retains fresh node state independently of its display and owns its text
def MakeNoteData(TextValue: ArchiveNode) -> ArchiveNode:
    return ArchiveNode(
        RuntimeClass("moNoteData_c", 1),
        {
            "f08": -1,
            "f0c": 0,
            "f18": None,
            "f20": "",
            "f28": 1 << 30,
            "f2c": 0,
            "f50": 0,
            "f48": None,
            "f58": MakeObList(),
            "f68": (),
            "n70": 0,
            "f80": 0,
            "f88": None,
            "f98": TextValue,
        },
    )
