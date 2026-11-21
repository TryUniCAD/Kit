from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# the active curved carrier must agree with the actual driving radial parameter
def ReadFilletRad(FilletValue: ArchiveNode) -> float:
    Fields = FilletValue.FieldsValue
    RadiusList = RequireNative(Fields["f868"], "suObList")
    (RadiusRow,) = NativeRows(RadiusList.FieldsValue["items"])
    RadiusItem = RequireNative(RadiusRow["o"], "edgeRadiusObject_c")
    Display = RequireNative(RadiusItem.FieldsValue["f08"], "moDisplayRadialDim_c")
    (HandleRow,) = NativeRows(Display.FieldsValue["f850"])
    Handle = RequireNative(HandleRow["o"], "moFeatureDimHandle_c")
    Dimension = RequireNative(Handle.FieldsValue["ff0"], "ThreeDRadiusDim_c")
    ParamValue = RequireNative(Dimension.FieldsValue["f28"], "moLengthParameter_c")
    RadiusValue = RequireScalar(ParamValue.FieldsValue["f58"])
    (ResultRow,) = NativeRows(Fields["fbf0"])
    if (
        ReadNativeName(ParamValue) != "D1"
        or ParamValue.FieldsValue.get("f20") != ""
        or ParamValue.FieldsValue.get("f48") is not None
        or ParamValue.FieldsValue.get("f68") != 0
        or Handle.FieldsValue.get("fe8") is not None
        or Handle.FieldsValue.get("f100") is not None
        or RadiusValue <= 0
        or ResultRow["f08"] != RadiusValue
    ):
        raise ValueError("SOLIDWORKS fillet radial definition differs from its driver")
    return RadiusValue
