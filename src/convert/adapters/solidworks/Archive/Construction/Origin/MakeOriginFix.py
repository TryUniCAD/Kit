from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# the native origin initializer retains one local type seventeen logical point constraint without allocating a persistent feature identifier
def MakeOriginFix(SketchValue: ArchiveNode, PointValue: ArchiveNode) -> ArchiveNode:
    HandleValue = ArchiveNode(
        RuntimeClass("sgPointHandle", 1),
        {
            "_sketch": SketchValue,
            "_point": PointValue,
            "f1c": -1,
            "f08": 0,
            "idx": 0,
            "f18": 0,
        },
    )
    return ArchiveNode(
        RuntimeClass("sgLogG1Dim", 1),
        {
            "refcount": 0,
            "f28": None,
            "f48": None,
            "f50": -1,
            "f30": 0,
            "f54": 0,
            "f5c": 0,
            "f60": None,
            "f68": 0,
            "has_f78": 0,
            "_sketch": SketchValue,
            "f80": 0x11,
            "f90": 2,
            "f94": 0,
            "f98": 0,
            "fa0": 0xFFFE,
            "fa4": 0,
            "h1": HandleValue,
        },
    )
