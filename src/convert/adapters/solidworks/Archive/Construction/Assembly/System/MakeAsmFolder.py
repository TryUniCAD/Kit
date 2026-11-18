from convert.adapters.solidworks.Archive.Construction.Assembly.System.AsmVocabulary import (
    KAsmFolders,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.System.MakeAsmNode import (
    MakeAsmNode,
)
from convert.adapters.solidworks.Archive.Construction.Model.EmptyRootRows import (
    EmptyRootRows,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTime import (
    FeatureTime,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# assembly folders retain independent native subtype collections and creation provenance while sharing only generic feature initialization
def MakeAsmFolder(
    ClassName: str,
    NameValue: str,
    OwnerValue: ArchiveNode,
    TargetValue: FeatureTarget,
    Allocator: PersistentIds,
    CreatedAt: int,
) -> ArchiveNode:
    if ClassName not in KAsmFolders:
        raise ValueError("unclassified ordinary assembly folder")
    NodeValue = MakeAsmNode(ClassName, NameValue, OwnerValue, TargetValue, Allocator)
    FieldsValue = NodeValue.FieldsValue
    FieldsValue.update(
        {
            "f360": int(ClassName != "moCommentsFolder_c"),
            "f370": 0,
            **FeatureTime(CreatedAt),
        }
    )
    if ClassName in ("moHistoryFolder_c", "moFavoriteFolder_c"):
        FieldsValue["f3c8"] = EmptyRootRows()
    if ClassName == "moFavoriteFolder_c":
        FieldsValue.update({"f3e8": EmptyRootRows(), "f408": 1})
    if ClassName == "moSelectionSetFolder_c":
        FieldsValue.update({"f3c0": EmptyRootRows(), "f3e0": 1})
    if ClassName == "moLiveSectionFolder_c":
        FieldsValue["f378"] = 1
    if ClassName == "moEqnFolder_c":
        RelationValue = ArchiveNode.RequireNode(OwnerValue.FieldsValue["f9d0"])
        FieldsValue["_relation_manager"] = RelationValue
        RelationValue.FieldsValue["_equation_folder"] = NodeValue
    return NodeValue
