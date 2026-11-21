from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# every end value must retain one local live parameter with no alternate expression tolerance or external dimension owner
def ReadPrismParam(
    DisplayValue: object, AngularValue: bool
) -> tuple[ArchiveNode, ArchiveNode, float]:
    Display = RequireNative(
        DisplayValue,
        "moDisplayAngularDim_c" if AngularValue else "moDisplayDistanceDim_c",
    )
    RowsValue = NativeRows(Display.FieldsValue.get("f850"))
    if len(RowsValue) != 1:
        raise ValueError("cache free prism end value has ambiguous display handles")
    Handle = RequireNative(RowsValue[0].get("o"), "moFeatureDimHandle_c")
    if (
        Handle.FieldsValue.get("fe8") is not None
        or Handle.FieldsValue.get("f100") is not None
    ):
        raise ValueError("cache free prism end parameter has an external owner")
    Dimension = RequireNative(
        Handle.FieldsValue.get("ff0"),
        "AngleDim_c" if AngularValue else "ParallelPlaneDistanceDim_c",
    )
    Parameter = RequireNative(
        Dimension.FieldsValue.get("f28"),
        "moAngleParameter_c" if AngularValue else "moLengthParameter_c",
    )
    if (
        Parameter.FieldsValue.get("f68") != 0
        or Parameter.FieldsValue.get("f48") is not None
        or Parameter.FieldsValue.get("f0c") != 0
        or Parameter.FieldsValue.get("f2c") != 0
    ):
        raise ValueError("cache free prism end parameter has alternate values")
    if any(
        Dimension.FieldsValue.get(FieldName) is not None for FieldName in ("f48", "f60")
    ) or any(
        Dimension.FieldsValue.get(FieldName) != 0
        for FieldName in ("f54", "f5c", "f68", "has_f78")
    ):
        raise ValueError("cache free prism end dimension has unqualified driving state")
    return Dimension, Parameter, RequireScalar(Parameter.FieldsValue.get("f58"))
