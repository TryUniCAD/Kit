from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# shared fresh ownership helpers must exclude unresolved placeholders and unproved drawing constructor paths
def RequireModel(OwnerValue: ArchiveNode) -> None:
    OwnerValue = ArchiveNode.RequireNode(OwnerValue)
    ClassValue = OwnerValue.ClassValue
    if (
        type(ClassValue) is not RuntimeClass
        or ClassValue.SchemaValue != 1
        or ClassValue.NameValue not in ("moPart_c", "moAssembly_c")
    ):
        raise ValueError(
            "fresh model ownership requires a concrete schema one part or assembly"
        )
