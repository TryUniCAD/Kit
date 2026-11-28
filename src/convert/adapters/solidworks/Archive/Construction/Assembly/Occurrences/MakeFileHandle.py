from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue


# one authored native handle supplies matching standalone header and embedded body field views without allocating duplicate string identities
def MakeFileHandle(TextValue: str) -> ArchiveNode:
    return ArchiveNode(
        RuntimeClass("moCStringHandle_c", 1),
        {"value": CStringValue(TextValue, True), "text": TextValue, "f08": TextValue},
    )
