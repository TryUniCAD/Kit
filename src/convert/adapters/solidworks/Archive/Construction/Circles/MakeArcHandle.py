from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# the endpoint adjacency handle points at the actual array index of the local arc
def MakeArcHandle(
    SketchValue: ArchiveNode, ArcValue: ArchiveNode, IndexValue: int
) -> ArchiveNode:
    return ArchiveNode(
        RuntimeClass("sgArcHandle", 1),
        {
            "_sketch": SketchValue,
            "_arc": ArcValue,
            "f1c": -1,
            "f08": 0,
            "idx": min(IndexValue, 0x777F),
            "f18": IndexValue,
        },
    )
