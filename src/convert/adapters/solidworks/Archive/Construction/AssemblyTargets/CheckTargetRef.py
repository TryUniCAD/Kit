from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.TargetDocument import (
    TargetDocument,
)
from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.TargetStamps import (
    TargetStamps,
)
from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.FieldRecord import (
    FieldRecord,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileKey
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName


# each recursive edge must preserve its actual target file configuration bounds and independently derived stamps rather than inherit parent or sibling state
def CheckTargetRef(
    ParentValue: TargetDocument, Reference: ArchiveNode, ChildValue: TargetDocument
) -> None:
    RequireRootNode(Reference, "moReference_c")
    Directory = ArchiveNode.RequireNode(Reference.FieldsValue["f3b0"])
    ChildFile = ArchiveNode.RequireNode(ChildValue.HeaderValue.FieldsValue["f38"])
    Selection = FieldRecord(Reference.FieldsValue["f3c0"])
    if (
        Reference.FieldsValue.get("owner") is not ParentValue.RootValue
        or ReadFileKey(Directory) != ReadFileKey(ChildFile)
        or Selection["f08"] != ReadNodeName(ChildValue.CurrentConfig)
        or Selection["f10"] != ChildValue.CurrentConfig.FieldsValue["f08"]
        or FieldRecord(Reference.FieldsValue["f370"]) != ChildValue.BoundsValue
    ):
        raise ValueError(
            "generated recursive occurrence target identity or local bounds differ"
        )
    StampsValue = TargetStamps(ChildValue)
    if any(
        Reference.FieldsValue[NameValue] != NumberValue
        for NameValue, NumberValue in StampsValue.items()
    ):
        raise ValueError("generated recursive occurrence target stamps differ")
