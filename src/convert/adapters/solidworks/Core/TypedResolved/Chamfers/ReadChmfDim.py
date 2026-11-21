from math import pi as PiValue

from convert.adapters.solidworks.Archive.Scalars.ReadScalar import ReadScalar
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ChmfDriver import (
    ChmfDriver,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismParam import (
    ReadPrismParam,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# the stored chamfer display value must agree with the separately owned positive editable parameter
def ReadChmfDim(
    LinkValue: NativeLink, DisplayNode: object, IsAngle: bool
) -> ChmfDriver:
    Display = RequireNative(DisplayNode)
    Dimension, Parameter, ValueSi = ReadPrismParam(Display, IsAngle)
    (HandleRow,) = NativeRows(Display.FieldsValue["f850"])
    Handle = RequireNative(HandleRow["o"], "moFeatureDimHandle_c")
    DimId = Dimension.FieldsValue.get("f50")
    NameValue = ReadNativeName(Parameter)
    if (
        type(DimId) is not int
        or DimId <= 0
        or NameValue != ("D2" if IsAngle else "D1")
        or Parameter.FieldsValue.get("f20") != ""
        or Dimension.FieldsValue.get("f30") != 0
        or (IsAngle and Dimension.FieldsValue.get("ff8") != 1)
        or ValueSi <= 0
        or (IsAngle and ValueSi >= PiValue / 2)
    ):
        raise ValueError("ordinary chamfer driver has unqualified local ownership")
    CellValue = NativeRecord(Display.FieldsValue.get("f5b0"))
    Payload = CellValue.get("data")
    if (
        Display.FieldsValue.get("n850") != 1
        or CellValue.get("elem") != 8
        or CellValue.get("n") != 1
        or type(Payload) is not bytes
        or len(Payload) != 8
        or ReadScalar(Payload, 0, "f64")[0] != ValueSi
    ):
        raise ValueError("ordinary chamfer display differs from its live driver")
    CheckTreeAlias(LinkValue, (Display, Handle, Dimension, Parameter))
    return ChmfDriver(NameValue, ValueSi, Display, Handle, Dimension, Parameter)
