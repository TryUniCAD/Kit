from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.ReadSwRow import ReadSwRow


# the stored length parameter owns the driving value while its dimension has a separate persistent identity
@DataClass(frozen=True, slots=True)
class SwDriver:
    ParameterValue: ArchiveNode
    DimensionValue: ArchiveNode
    NativeId: int
    MetresValue: float


# live dimensions and fixed relations must address the actual indexed local sketch entity
def CheckSwIndex(OwnerValue: object, ClassName: str, IndexValue: int) -> None:
    FieldsValue = RequireNative(OwnerValue, ClassName).FieldsValue
    if (
        FieldsValue.get("idx") != IndexValue
        or FieldsValue.get("f1c") != -1
        or FieldsValue.get("f08") != 0
    ):
        raise ValueError("SOLIDWORKS sweep dimension has a foreign sketch handle")


# display and dimension aliases must identify the same editable local circle or arc value
def ReadSwDriver(SketchValue: ArchiveNode, IsSection: bool) -> SwDriver:
    DimsValue = NativeRecord(SketchValue.FieldsValue.get("dims"))
    DimValue = RequireNative(ReadSwRow(DimsValue, "ng1", "val_g1", "d"), "sgCircleDim")
    ParamValue = RequireNative(DimValue.FieldsValue.get("f28"), "moLengthParameter_c")
    DisplayList = RequireNative(DimsValue.get("f118"), "suObList")
    DisplayValue = RequireNative(
        ReadSwRow(DisplayList.FieldsValue), "moDisplayRadialDim_c"
    )
    HandleValue = RequireNative(
        ReadSwRow(DisplayValue.FieldsValue, "n850", "f850"), "moSkDimHandleRadial_c"
    )
    NativeId = DimValue.FieldsValue.get("f50")
    MetresValue = RequireScalar(ParamValue.FieldsValue.get("f58"))
    if (
        type(NativeId) is not int
        or NativeId <= 0
        or MetresValue <= 0.0
        or DimValue.FieldsValue.get("f80") != (15 if IsSection else 3)
        or DimValue.FieldsValue.get("f90") != 2
        or ReadNativeName(ParamValue) != "D1"
        or ParamValue.FieldsValue.get("f48") is not None
        or ParamValue.FieldsValue.get("f68") != 0
        or HandleValue.FieldsValue.get("ff0") is not SketchValue
        or HandleValue.FieldsValue.get("ff8") != 0
        or DisplayValue.FieldsValue.get("f950") != MetresValue
    ):
        raise ValueError("SOLIDWORKS sweep has no live local D1 owner")
    CheckSwIndex(DimValue.FieldsValue.get("h1"), "sgArcHandle", 0)
    return SwDriver(ParamValue, DimValue, NativeId, MetresValue)
