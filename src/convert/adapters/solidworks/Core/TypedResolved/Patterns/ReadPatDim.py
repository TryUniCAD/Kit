from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Scalars.ReadScalar import ReadScalar
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.Patterns.PatternDim import (
    PatternDim,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# a retained pattern driver follows its actual display handle before reading a live value
def ReadPatDim(PatternValue: ArchiveNode, SlotName: str, IsCount: bool) -> PatternDim:
    Display = RequireNative(
        PatternValue.FieldsValue.get(SlotName),
        "moDisplayDim_c" if IsCount else "moDisplayDistanceDim_c",
    )
    RowsValue = NativeRows(Display.FieldsValue.get("f850"))
    if Display.FieldsValue.get("n850") != 1 or len(RowsValue) != 1:
        raise ValueError("pattern driver requires one retained display handle")
    Handle = RequireNative(RowsValue[0].get("o"), "moFeatureDimHandle_c")
    Dimension = RequireNative(
        Handle.FieldsValue.get("ff0"),
        "moNumberDim_c" if IsCount else "ParallelPlaneDistanceDim_c",
    )
    Parameter = RequireNative(
        Dimension.FieldsValue.get("f28"),
        "moIntegerParameter_c" if IsCount else "moLengthParameter_c",
    )
    LiveValue = Parameter.FieldsValue.get("f58")
    DimId = Dimension.FieldsValue.get("f50")
    if (
        any(
            Handle.FieldsValue.get(NameValue) is not None
            for NameValue in ("f100", "fe8")
        )
        or Parameter.FieldsValue.get("f60" if IsCount else "f68") != 0
        or type(DimId) is not int
        or DimId < 0
        or (IsCount and type(LiveValue) is not int)
    ):
        raise ValueError("pattern driver has alternate dimension ownership")
    Cache = NativeRecord(Display.FieldsValue.get("f5b0"))
    Payload = Cache.get("data")
    if (
        Cache.get("elem") != 8
        or Cache.get("n") != 1
        or type(Payload) is not bytes
        or len(Payload) != 8
    ):
        raise ValueError("pattern display does not have one typed binary64 cell")
    return PatternDim(
        SlotName,
        Display,
        Handle,
        Dimension,
        Parameter,
        ReadNativeName(Parameter),
        LiveValue if type(LiveValue) is int else RequireScalar(LiveValue),
        RequireScalar(ReadScalar(Payload, 0, "f64")[0]),
    )
