from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows


# classify the radius lane independently of handle and driver value validation
def IsRadiusSketch(SketchValue: ArchiveNode) -> bool:
    try:
        Fields = NativeRecord(SketchValue.FieldsValue.get("dims"))
        Values = NativeRows(Fields.get("val_g1"))
    except (TypeError, ValueError):
        return False
    return any(
        isinstance(Dimension := Row.get("d"), ArchiveNode)
        and Dimension.ClassValue.NameValue == "sgCircleDim"
        and Dimension.FieldsValue.get("f80") == 3
        for Row in Values
    )
