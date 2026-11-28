from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.Native import NativeDimension
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# radial modes and driving values must follow the actual sketch value and display handle
def ReadRadialDrive(
    LinkValue: NativeLink, SketchValue: ArchiveNode
) -> tuple[NativeDimension, str, ArchiveNode] | None:
    DimensionFields = NativeRecord(SketchValue.FieldsValue.get("dims"))
    Values = NativeRows(DimensionFields.get("val_g1"))
    if len(Values) != 1 or any(
        DimensionFields.get(NameValue)
        for NameValue in ("val_g2", "val_g3", "offset_dims")
    ):
        return None
    Dimension = RequireNative(Values[0].get("d"), "sgCircleDim")
    FieldsValue = Dimension.FieldsValue
    ShapeCode = FieldsValue.get("f80")
    if ShapeCode not in (3, 15) or FieldsValue.get("f68") != 0:
        return None
    ArcHandle = RequireNative(FieldsValue.get("h1"), "sgArcHandle")
    if ArcHandle.FieldsValue.get("idx") != 0:
        return None
    DisplayList = RequireNative(DimensionFields.get("f118"), "suObList")
    Displays = NativeRows(DisplayList.FieldsValue.get("items"))
    if len(Displays) != 1:
        return None
    Display = RequireNative(Displays[0].get("o"), "moDisplayRadialDim_c")
    Handles = NativeRows(Display.FieldsValue.get("f850"))
    if len(Handles) != 1:
        return None
    Handle = RequireNative(Handles[0].get("o"), "moSkDimHandleRadial_c")
    if (
        Handle.FieldsValue.get("ff0") is not SketchValue
        or Handle.FieldsValue.get("ff8") != 0
    ):
        return None
    Parameter = RequireNative(FieldsValue.get("f28"), "moLengthParameter_c")
    NativeValue = RequireScalar(Parameter.FieldsValue.get("f58"))
    if NativeValue <= 0.0 or Parameter.FieldsValue.get("f68") != 0:
        return None
    Value = NativeDimension(
        ReadNativeName(Parameter),
        1000.0 * NativeValue,
        "length",
        f"{1000.0 * NativeValue:.17g}mm",
        native_value=NativeValue,
        native_role="driving",
        TypedOwner={
            **NativeNodeSpan(LinkValue, Parameter),
            "value_field": "f58",
            "dimension_index": Dimension.IndexValue,
            "display_index": Display.IndexValue,
            "handle_index": Handle.IndexValue,
            "arc_handle_index": ArcHandle.IndexValue,
        },
    )
    return Value, "radius" if ShapeCode == 3 else "diameter", Dimension
