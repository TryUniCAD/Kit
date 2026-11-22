from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.Native import NativeDimension
from convert.adapters.solidworks.Core.TypedResolved.DepthOwner import DepthOwner
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# a display cache cannot replace the live parameter selected by the forward end specification
def ReadDepthOwner(
    LinkValue: NativeLink, DisplayValue: ArchiveNode, *, RadiusSlot: bool = False
) -> DepthOwner:
    DisplayValue = RequireNative(DisplayValue, "moDisplayDistanceDim_c")
    HandlesValue = NativeRows(DisplayValue.FieldsValue.get("f850"))
    if len(HandlesValue) != 1:
        raise ValueError("forward depth requires one actual display handle")
    HandleValue = RequireNative(HandlesValue[0].get("o"), "moFeatureDimHandle_c")
    if (
        HandleValue.FieldsValue.get("fe8") is not None
        or HandleValue.FieldsValue.get("f100") is not None
    ):
        raise ValueError("forward depth requires the local dimension branch")
    Dimension = RequireNative(
        HandleValue.FieldsValue.get("ff0"),
        "ThreeDRadiusDim_c" if RadiusSlot else "ParallelPlaneDistanceDim_c",
    )
    Parameter = RequireNative(Dimension.FieldsValue.get("f28"), "moLengthParameter_c")
    if (
        type(Parameter.FieldsValue.get("f68")) is not int
        or Parameter.FieldsValue["f68"] != 0
    ):
        raise ValueError(
            "alternate length parameter values are outside typed depth semantics"
        )
    NativeValue = RequireScalar(Parameter.FieldsValue.get("f58"))
    if NativeValue <= 0:
        raise ValueError("ordinary blind depth must be positive")
    NativeId = Dimension.FieldsValue.get("f50")
    if type(NativeId) is not int or NativeId < 0:
        raise ValueError("forward depth lacks its persistent dimension identity")
    DepthMm = NativeValue / 0.001
    DepthValue = NativeDimension(
        ReadNativeName(Parameter),
        DepthMm,
        "length",
        f"{DepthMm:.17g}mm",
        native_value=NativeValue,
        native_role="driving",
        TypedOwner={
            **NativeNodeSpan(LinkValue, Parameter),
            "value_field": "f58",
            "dimension_id": NativeId,
            "dimension_index": Dimension.IndexValue,
            "handle_index": HandleValue.IndexValue,
            "display_index": DisplayValue.IndexValue,
            "slot": "f818" if RadiusSlot else "f818.f18",
        },
    )
    return DepthOwner(Parameter, Dimension, HandleValue, DisplayValue, DepthValue)
