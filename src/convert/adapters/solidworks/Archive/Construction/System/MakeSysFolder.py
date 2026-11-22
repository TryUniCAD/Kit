from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTime import (
    FeatureTime,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.System.ClearSystemMut import (
    ClearSystemMut,
)
from convert.adapters.solidworks.Archive.Construction.System.MakeSystemNode import (
    MakeSystemNode,
)
from convert.adapters.solidworks.Archive.Construction.System.SystemClasses import (
    KSystemFolders,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# each empty system folder must retain its own subtype constructor state and authored provenance without saved member lists
def MakeSysFolder(
    ClassName: str,
    NameValue: str,
    OwnerValue: ArchiveNode,
    TargetValue: FeatureTarget,
    Allocator: PersistentIds,
    CreatedAt: int,
) -> ArchiveNode:
    if ClassName not in KSystemFolders:
        raise ValueError(
            "system folder class is outside the classified fresh part profile"
        )
    TimeFields = FeatureTime(CreatedAt)
    NodeValue = MakeSystemNode(ClassName, NameValue, OwnerValue, TargetValue, Allocator)
    FieldsValue = NodeValue.FieldsValue
    FieldsValue.update(
        {
            "f360": int(
                ClassName
                not in {
                    "moCommentsFolder_c",
                    "moSolidBodyFolder_c",
                    "moSurfaceBodyFolder_c",
                }
            ),
            "f370": 0,
            **TimeFields,
        }
    )
    if ClassName in {"moHistoryFolder_c", "moFavoriteFolder_c"}:
        FieldsValue["f3c8"] = {"n": 0, "items": []}
    if ClassName == "moFavoriteFolder_c":
        FieldsValue.update({"f3e8": {"n": 0, "items": []}, "f408": 1})
    if ClassName == "moSelectionSetFolder_c":
        FieldsValue.update({"f3c0": {"n": 0, "items": []}, "f3e0": 1})
    if ClassName == "moMaterialFolder_c":
        FieldsValue.update(
            {"f378": "", "flags380": 0x80000000 | int(False) | (int(False) << 1)}
        )
    if ClassName in {"moSolidBodyFolder_c", "moSurfaceBodyFolder_c"}:
        FieldsValue.update({"f37c": 0, "f380": 0, "f388": None, "f3d8": None})
    ClearSystemMut(NodeValue)
    return NodeValue
