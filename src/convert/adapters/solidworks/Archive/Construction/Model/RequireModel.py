from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# shared fresh ownership helpers must exclude unresolved placeholders while retaining each independently proved concrete model owner
def RequireModel(OwnerValue: ArchiveNode) -> None:
    OwnerValue = ArchiveNode.RequireNode(OwnerValue)
    ClassValue = OwnerValue.ClassValue
    if (
        type(ClassValue) is not RuntimeClass
        or ClassValue.SchemaValue != 1
        or ClassValue.NameValue not in ("moPart_c", "moAssembly_c", "moDrawing_c")
    ):
        raise ValueError(
            "fresh model ownership requires a concrete schema one part assembly or drawing"
        )
