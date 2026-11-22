from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# sketch driver references must derive native indices from actual owned point order while retaining their runtime identity
def MakePointRef(
    SketchValue: ArchiveNode,
    PointValues: tuple[ArchiveNode, ...],
    PointValue: ArchiveNode,
) -> ArchiveNode:
    if (
        PointValue.ClassValue != RuntimeClass("sgPoint", 1)
        or PointValue.FieldsValue.get("_sketch") is not SketchValue
        or sum(NodeValue is PointValue for NodeValue in PointValues) != 1
    ):
        raise ValueError(
            "sketch dimension point references require unique actual local point ownership"
        )
    IndexValue = PointValues.index(PointValue)
    return ArchiveNode(
        RuntimeClass("sgPointHandle", 1),
        {
            "_sketch": SketchValue,
            "_point": PointValue,
            "f1c": -1,
            "f08": 0,
            "idx": min(IndexValue, 0x777F),
            "f18": IndexValue,
        },
    )
