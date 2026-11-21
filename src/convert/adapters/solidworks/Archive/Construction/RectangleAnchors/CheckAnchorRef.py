from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# constructed anchor prerequisites must bind both in memory ownership and the actual serialized local entity slot
def CheckAnchorRef(
    HandleValue: ArchiveNode,
    EntityValue: ArchiveNode,
    SketchValue: ArchiveNode,
    IndexValue: int,
    IsPoint: bool,
) -> None:
    ClassName = "sgPointHandle" if IsPoint else "sgLineHandle"
    FieldName = "_point" if IsPoint else "_line"
    if (
        HandleValue.ClassValue != RuntimeClass(ClassName, 1)
        or HandleValue.FieldsValue.get(FieldName) is not EntityValue
        or HandleValue.FieldsValue.get("_sketch") is not SketchValue
        or HandleValue.FieldsValue.get("idx") != IndexValue
        or HandleValue.FieldsValue.get("f18") != IndexValue
    ):
        raise ValueError("corner anchor requires matching actual local handle identity")
