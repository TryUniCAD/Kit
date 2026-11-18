from convert.adapters.solidworks.Archive.Construction.Assembly.Occurrences.MakeSharedCopy import (
    MakeSharedCopy,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue


# a repeated generated child has one directory record with independent child file and manager save events and users derived from actual occurrences
def MakeDirectory(ChildValue: PartCandidate, UsersValue: int) -> ArchiveNode:
    FileValue = ArchiveNode.RequireNode(ChildValue.HeaderValue.FieldsValue["f38"])
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
            "f70": ChildValue.ManagerHeader.FieldsValue["f60"],
            "f78": 0,
            "refcfg": {"f08": CStringValue("", True), "f10": -1},
        },
    )
