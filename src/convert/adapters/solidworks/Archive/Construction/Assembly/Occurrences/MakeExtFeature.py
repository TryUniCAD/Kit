from collections.abc import Mapping
from convert.adapters.solidworks.Archive.Construction.Assembly.Occurrences.MakeFileHandle import (
    MakeFileHandle,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName


# occurrence external features retain the actual containing definition name identifier and explicit backlink mode rather than reconstructed file guesses
def MakeExtFeature(
    Reference: ArchiveNode, SharedValue: Mapping[str, object], Backlink: bool
) -> ArchiveNode:
    return ArchiveNode(
        RuntimeClass("moExtFeature_c", 1),
        {
            "f10": SharedValue,
            "f18": {"f08": "", "f10": -1},
            "f38": MakeFileHandle(ReadNodeName(Reference)),
            "f40": 0,
            "f44": Reference.FieldsValue["f08"],
            "f50": Reference if Backlink else None,
            "f58": -1,
        },
    )
