from math import tau as FullTurn

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from convert.adapters.solidworks.Core.TypedResolved.Revolves.RevolveAngle import (
    RevolveAngle,
)


# the active end must resolve its real dimension and parameter before any angular intent is published
def ReadRevAngle(LinkValue: NativeLink, NodeValue: ArchiveNode) -> RevolveAngle:
    FieldsValue = RequireNative(NodeValue, "moRevolution_c").FieldsValue
    if FieldsValue.get("f808") is not None or FieldsValue.get("f810") is not None:
        raise ValueError("ordinary revolve requires the modern angular branch")
    EndValue = RequireNative(FieldsValue.get("f8d8"), "moRevEndSpec_c").FieldsValue
    if (
        EndValue.get("f08") != 1
        or any(
            EndValue.get(NameValue) != 0
            for NameValue in ("f138", "f13c", "f0c", "f10", "f140", "f144")
        )
        or any(
            EndValue.get(NameValue) is not None
            for NameValue in ("f118", "f120", "f128", "f130", "f20", "f28", "f30")
        )
    ):
        raise ValueError("ordinary revolve requires one active blind angular owner")
    DisplayValue = RequireNative(EndValue.get("f18"), "moDisplayAngularDim_c")
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
    ParameterValue = RequireNative(DimFields.get("f28"), "moAngleParameter_c")
    ParamFields = ParameterValue.FieldsValue
    if (
        ParamFields.get("f68") != 0
        or ParamFields.get("f20") != ""
        or ParamFields.get("f48") is not None
    ):
        raise ValueError(
            "ordinary revolve angular expression or alternate state is unqualified"
        )
    RadiansValue = RequireScalar(ParamFields.get("f58"))
    if not 0.0 < RadiansValue <= FullTurn:
        raise ValueError("ordinary revolve requires a positive angle at most one turn")
    return RevolveAngle(
        DisplayValue,
        HandleValue,
        DimensionValue,
        ParameterValue,
        ReadNativeName(ParameterValue),
        RadiansValue,
        NativeNodeSpan(LinkValue, ParameterValue),
    )
