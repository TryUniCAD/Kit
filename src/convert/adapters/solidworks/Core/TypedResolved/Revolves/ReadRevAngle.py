from math import tau as FullTurn

from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from convert.adapters.solidworks.Core.TypedResolved.Revolves.ReadRevDim import (
    ReadRevDim,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.RevolveAngle import (
    RevolveAngle,
)


# each active end needs its actual parameter independently of display placement
def ReadRevAngle(LinkValue: NativeLink, DisplayNode: object) -> RevolveAngle:
    DisplayValue, HandleValue, DimensionValue = ReadRevDim(DisplayNode)
    ParameterValue = RequireNative(
        DimensionValue.FieldsValue.get("f28"), "moAngleParameter_c"
    )
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
