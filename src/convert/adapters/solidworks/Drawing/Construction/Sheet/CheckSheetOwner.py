from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# the sheet must use its actual drawing and a valid self component before creating owned copies
def CheckSheetOwner(OwnerValue: ArchiveNode, ComponentValue: ArchiveNode) -> None:
    if OwnerValue.ClassValue != RuntimeClass("moDrawing_c", 1):
        raise ValueError(
            "drawing sheet construction requires its concrete owning drawing"
        )
    if (
        ComponentValue.ClassValue != RuntimeClass("moUnitComponent_c", 1)
        or ComponentValue.FieldsValue.get("owner") is not OwnerValue
        or ComponentValue.FieldsValue.get("has_ext") != 0
        or set(ComponentValue.FieldsValue) != {"owner", "has_ext"}
    ):
        raise ValueError(
            "drawing sheet construction requires its actual ordinary self component"
        )
