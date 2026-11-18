from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptMap,
    NeedConceptNode,
)


# a drawing directory entry must share its actual generated child identity and use the distinct real configuration manager save epoch
def MakeDrawEntry(ChildValue: PartCandidate) -> ArchiveNode:
    if type(ChildValue) is not PartCandidate:
        raise TypeError("drawing directory construction requires the actual SDK child")
    ChildFile = NeedConceptNode(
        ChildValue.HeaderValue.FieldsValue["f38"], "moExtObject_c"
    )
    RequireRootNode(ChildValue.ManagerHeader, "dmConfigMgrHeader_c")
    SharedValue = dict(NeedConceptMap(ChildFile.FieldsValue["shared"]))
    if SharedValue["f20"] != 2 or SharedValue["f08"] != 0:
        raise ValueError(
            "drawing directory requires the ordinary nonvirtual generated part"
        )
    return ArchiveNode(
        RuntimeClass("moExtObject_c", 1),
        {
            "shared": SharedValue,
            "f48": 1,
            "f4c": 0,
            "f50": 0,
            "f54": 0,
            "f58": 0,
            "f60": FieldInt(ChildFile.FieldsValue, "f60"),
            "f70": FieldInt(ChildValue.ManagerHeader.FieldsValue, "f60"),
            "f78": 0,
            "refcfg": {"f08": CStringValue("", True), "f10": -1},
        },
    )
