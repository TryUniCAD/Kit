from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# a principal frame cannot substitute for an attached clipped or differently defined datum with coincident cached coordinates
def CheckPrismDatum(DatumValue: ArchiveNode) -> None:
    Fields = RequireNative(
        DatumValue.FieldsValue.get("f6f8"), "moDefaultRefPlnData_c"
    ).FieldsValue
    if any(
        Fields.get(FieldName) is not None for FieldName in ("f48", "f68", "f70", "f78")
    ):
        raise ValueError("cache free prism datum has additional geometric owners")
    if any(
        Fields.get(FieldName) != 0
        for FieldName in ("b0", "b1", "b2", "b3", "f50", "old_e5", "f60", "f64")
    ):
        raise ValueError("cache free prism datum has unsupported border or mode state")
    if Fields.get("f54") != -4 or Fields.get("f58") != -4 or Fields.get("f5c") != 1:
        raise ValueError("cache free prism datum has alternate constructor state")
    if any(
        NativeRecord(Fields.get("display_root")).get(FieldName) != 0.0
        for FieldName in ("x", "y", "z")
    ):
        raise ValueError("cache free prism datum has a displaced display origin")
