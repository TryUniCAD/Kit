from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# each endpoint incidence owns a distinct native handle while retaining its actual line identity
def MakeLineHandle(
    SketchValue: ArchiveNode, LineValue: ArchiveNode, IndexValue: int
) -> ArchiveNode:
    return ArchiveNode(
        RuntimeClass("sgLineHandle", 1),
        {
            "_sketch": SketchValue,
            "_line": LineValue,
            "f1c": -1,
            "f08": 0,
            "idx": min(IndexValue, 0x777F),
            "f18": IndexValue,
        },
    )
