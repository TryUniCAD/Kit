from convert.adapters.solidworks.Archive.Construction.Header.HeaderInput import (
    HeaderInput,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue


# the initial revision log derives its owner name identifier and stamp from the actual root and explicit provenance
def MakeRootLog(OwnerValue: ArchiveNode, InputValue: HeaderInput) -> ArchiveNode:
    NameValue = ArchiveNode.RequireNode(OwnerValue.FieldsValue["f18"])
    OwnerName = NameValue.FieldsValue.get("f08")
    if type(OwnerName) is not str:
        raise ValueError("header log requires the actual model name")
    StampValue = ArchiveNode(
        RuntimeClass("moStamp_c", 1),
        {
            "f08": 0,
            "f0c": 0,
            "f10": 0,
            "f18": InputValue.CreatedAt,
            "f20": CStringValue(InputValue.CommentText, True),
        },
    )
    return ArchiveNode(
        RuntimeClass("moLogs_c", 1),
        {
            "items": (StampValue,),
            "f48": OwnerValue.FieldsValue["f08"],
            "f50": CStringValue(OwnerName, True),
        },
    )
