from struct import pack as PackValues

from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.ThinWallOwner import (
    ThinWallOwner,
)


# an owned wall thickness comes from the live length parameter behind its exact local display
def ReadThinDim(DisplayNode: object, NameValue: str, IsActive: bool) -> ThinWallOwner:
    DisplayValue = RequireNative(DisplayNode, "moDisplayDistanceDim_c")
    RowsValue = NativeRows(DisplayValue.FieldsValue.get("f850"))
    if len(RowsValue) != 1 or DisplayValue.FieldsValue.get("n850") != 1:
        raise ValueError("SOLIDWORKS thin wall display requires one local target")
    HandleValue = RequireNative(RowsValue[0].get("o"), "moFeatureDimHandle_c")
    if any(HandleValue.FieldsValue.get(FieldName) is not None for FieldName in ("fe8", "f100")):
        raise ValueError("SOLIDWORKS thin wall display carries an alternate handle")
    Dimension = RequireNative(HandleValue.FieldsValue.get("ff0"), "ParallelPlaneDistanceDim_c")
    FieldsValue = Dimension.FieldsValue
    Parameter = RequireNative(FieldsValue.get("f28"), "moLengthParameter_c")
    ParamFields = Parameter.FieldsValue
    WidthValue = RequireScalar(ParamFields.get("f58"))
    NumberValue = FieldsValue.get("f50")
    if (
        ReadNativeName(Parameter) != NameValue
        or type(NumberValue) is not int or NumberValue <= 0
        or FieldsValue.get("f30") != 0 or FieldsValue.get("f54") != 0
        or FieldsValue.get("f48") is not None or FieldsValue.get("f60") is not None
        or ParamFields.get("f68") != 0 or ParamFields.get("f20") != ""
        or ParamFields.get("f48") is not None or WidthValue < 0.0
        or (WidthValue > 0.0) is not IsActive
        or FieldsValue.get("has_fe0") != int(IsActive)
        or FieldsValue.get("has_ff0") != int(IsActive)
        or NativeRecord(DisplayValue.FieldsValue.get("f5b0")).get("data") != PackValues("<d", WidthValue)
    ):
        raise ValueError("SOLIDWORKS thin wall has unqualified parameter or display state")
    return ThinWallOwner(DisplayValue, HandleValue, Dimension, Parameter, NameValue, WidthValue)
