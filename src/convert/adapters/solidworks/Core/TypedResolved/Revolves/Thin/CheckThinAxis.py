from math import hypot as Hypot
from math import isclose as IsClose

from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.Revolves.AxisReference import (
    AxisReference,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.RevolveAxis import (
    RevolveAxis,
)


# the detached position and direction must agree with the actual selected local endpoints
def CheckThinAxis(Reference: AxisReference, FrameValue: RevolveAxis) -> None:
    FieldsValue = Reference.WrapperValue.FieldsValue
    StartPoint = FrameValue.StartValue
    EndPoint = FrameValue.EndValue
    Direction = FrameValue.RawDirection
    StartValue = (StartPoint.x * 0.001, StartPoint.y * 0.001, StartPoint.z * 0.001)
    DirectionValue = (Direction.x, Direction.y, Direction.z)
    for NameValue, Expected in (("fc8", StartValue), ("fe0", DirectionValue)):
        Stored = NativeRecord(FieldsValue.get(NameValue))
        if not all(
            IsClose(RequireScalar(Stored.get(KeyValue)), Value, abs_tol=1e-14, rel_tol=1e-13)
            for KeyValue, Value in zip("xyz", Expected, strict=True)
        ):
            raise ValueError("SOLIDWORKS thin native axis disagrees with its selected line")
    LengthValue = Hypot(EndPoint.x - StartPoint.x, EndPoint.y - StartPoint.y, EndPoint.z - StartPoint.z)
    if not IsClose(RequireScalar(FieldsValue.get("fb8")), LengthValue * 0.001, abs_tol=1e-14, rel_tol=1e-13):
        raise ValueError("SOLIDWORKS thin native axis span disagrees with its selected line")
