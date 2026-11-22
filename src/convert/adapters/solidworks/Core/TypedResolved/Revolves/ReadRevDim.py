from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# angular edits must resolve through the display and its local driving dimension
def ReadRevDim(DisplayNode: object) -> tuple[ArchiveNode, ArchiveNode, ArchiveNode]:
    DisplayValue = RequireNative(DisplayNode, "moDisplayAngularDim_c")
    RowsValue = NativeRows(DisplayValue.FieldsValue.get("f850"))
    if DisplayValue.FieldsValue.get("n850") != 1 or len(RowsValue) != 1:
        raise ValueError("ordinary revolve angular display has multiple targets")
    HandleValue = RequireNative(RowsValue[0].get("o"), "moFeatureDimHandle_c")
    if (
        HandleValue.FieldsValue.get("fe8") is not None
        or HandleValue.FieldsValue.get("f100") is not None
    ):
        raise ValueError("ordinary revolve angle requires its local dimension branch")
    DimensionValue = RequireNative(HandleValue.FieldsValue.get("ff0"), "AngleDim_c")
    DimFields = DimensionValue.FieldsValue
    DimensionId = DimFields.get("f50")
    if (
        any(DimFields.get(NameValue) is not None for NameValue in ("f48", "f60"))
        or any(DimFields.get(NameValue) != 0 for NameValue in ("f54", "f30"))
        or type(DimensionId) is not int
        or DimensionId < 0
    ):
        raise ValueError("ordinary revolve angular driving state is unqualified")
    return DisplayValue, HandleValue, DimensionValue
