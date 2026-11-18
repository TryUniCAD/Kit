from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    FieldText,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptMap,
    NeedConceptNode,
)


# the drawing external interface must use its actual owner file handles and the exact live internal reference backlink
def MakeDrawExt(Reference: ArchiveNode, HeaderValue: ArchiveNode) -> ArchiveNode:
    RequireRootNode(Reference, "moReferenceInternal_c")
    OwnerFile = NeedConceptNode(HeaderValue.FieldsValue["f38"], "moExtObject_c")
    SharedValue = NeedConceptMap(OwnerFile.FieldsValue["shared"])
    NameNode = NeedConceptNode(Reference.FieldsValue["f18"], "moNodeName_c")
    if SharedValue["f20"] != 4 or SharedValue["f08"] != 0:
        raise ValueError(
            "drawing external feature requires its ordinary actual file owner"
        )
    return ArchiveNode(
        RuntimeClass("moExtFeature_c", 1),
        {
            "f10": SharedValue,
            "f18": {"f08": "", "f10": -1},
            "f38": ArchiveNode(
                RuntimeClass("moCStringHandle_c", 1),
                {"value": CStringValue(FieldText(NameNode.FieldsValue, "f08"), True)},
            ),
            "f40": 0,
            "f44": FieldInt(Reference.FieldsValue, "f08"),
            "f50": Reference,
            "f58": -1,
        },
    )
