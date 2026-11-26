from convert.adapters.solidworks.Archive.Construction.Presentation.MakeMaterial import (
    MakeMaterial,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# initial model visuals must own their independent constructor material record and explicitly select the model presentation state
def MakeModelVisual() -> ArchiveNode:
    return ArchiveNode(
        RuntimeClass("moVisualProperties_c", 1),
        {
            "f0c": 0xC0C0C0,
            "f14": 0,
            "f18": 0xC0C0C0,
            "f20": MakeMaterial(),
            "f40": "",
            "f48": 0,
            "f4c": 1,
            "f50": "",
            "f58": 0,
            "f5c": 1,
            "f78": -1,
            "f7c": 0,
            "f80": 0,
            "has88": 0,
        },
    )
