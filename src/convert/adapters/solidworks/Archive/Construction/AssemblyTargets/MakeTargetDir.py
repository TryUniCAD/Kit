from convert.adapters.solidworks.Archive.Construction.Assembly.Occurrences.MakeSharedCopy import (
    MakeSharedCopy,
)
from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.TargetDocument import (
    TargetDocument,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue


# repeated definitions need one direct directory entry with independent file and manager save stamps and an index derived from first use
def MakeTargetDir(
    TargetValue: TargetDocument, UsersValue: int, DirectoryId: int = 0
) -> ArchiveNode:
    if (
        type(UsersValue) is not int
        or UsersValue <= 0
        or type(DirectoryId) is not int
        or DirectoryId < 0
    ):
        raise ValueError("generated directory users and first use index must be valid")
    FileValue = ArchiveNode.RequireNode(TargetValue.HeaderValue.FieldsValue["f38"])
    return ArchiveNode(
        RuntimeClass("moExtObject_c", 1),
        {
            "shared": MakeSharedCopy(FileValue),
            "f48": UsersValue,
            "f4c": 0,
            "f50": 0,
            "f54": 0,
            "f58": 0,
            "f60": FileValue.FieldsValue["f60"],
            "f70": TargetValue.ManagerHeader.FieldsValue["f60"],
            "f78": DirectoryId,
            "refcfg": {"f08": CStringValue("", True), "f10": -1},
        },
    )
