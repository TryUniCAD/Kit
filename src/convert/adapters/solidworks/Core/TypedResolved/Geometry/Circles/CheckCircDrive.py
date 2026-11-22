from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# radial geometry cannot qualify a parameter with alternate expressions or stale external ownership
def CheckCircDrive(SketchValue: ArchiveNode) -> None:
    Fields = NativeRecord(SketchValue.FieldsValue.get("dims"))
    RowsValue = NativeRows(Fields.get("val_g1"))
    if len(RowsValue) != 1:
        raise ValueError("cache free circle requires its one actual radial value")
    Dimension = RequireNative(RowsValue[0].get("d"), "sgCircleDim")
    Parameter = RequireNative(Dimension.FieldsValue.get("f28"), "moLengthParameter_c")
    if Parameter.FieldsValue.get("f48") is not None or any(
        Parameter.FieldsValue.get(NameValue) != 0 for NameValue in ("f68", "f0c", "f2c")
    ):
        raise ValueError(
            "cache free circle radial parameter has alternate or external state"
        )
