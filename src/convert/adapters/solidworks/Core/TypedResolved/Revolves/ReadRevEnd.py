from collections.abc import Mapping
from math import tau as FullTurn

from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from convert.adapters.solidworks.Core.TypedResolved.Revolves.ReadRevAngle import (
    ReadRevAngle,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.ReadRevMode import (
    ReadRevMode,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.RevolveAngle import (
    RevolveAngle,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.RevolveEnd import (
    RevolveEnd,
)


# independent end controls cannot share a display handle dimension or parameter
def CheckRevPair(AlongValue: RevolveAngle, AgainstValue: RevolveAngle) -> None:
    if (
        AgainstValue.NameValue != "D2"
        or AlongValue.DisplayValue is AgainstValue.DisplayValue
        or AlongValue.HandleValue is AgainstValue.HandleValue
        or AlongValue.ParameterValue is AgainstValue.ParameterValue
        or AlongValue.DimensionValue.FieldsValue["f50"]
        == AgainstValue.DimensionValue.FieldsValue["f50"]
    ):
        raise ValueError("ordinary revolve requires its distinct D1 and D2 owners")


# positive live drivers are needed to rebuild the measured modern angular end modes
def ReadRevEnd(
    LinkValue: NativeLink, FieldsValue: Mapping[str, object], IsReverse: bool
) -> RevolveEnd:
    if FieldsValue.get("f808") is not None or FieldsValue.get("f810") is not None:
        raise ValueError("ordinary revolve requires the modern angular branch")
    EndFields = RequireNative(FieldsValue.get("f8d8"), "moRevEndSpec_c").FieldsValue
    ModeValue = ReadRevMode(EndFields)
    AlongValue = ReadRevAngle(LinkValue, EndFields.get("f18"))
    AgainstValue = (
        ReadRevAngle(LinkValue, EndFields["f20"]) if ModeValue == "two_sided" else None
    )
    ResultValue = RevolveEnd(ModeValue, AlongValue, AgainstValue)
    if ModeValue == "one_sided":
        return ResultValue
    if AlongValue.NameValue != "D1":
        raise ValueError("ordinary revolve requires its actual D1 owner")
    if ModeValue == "symmetric_full" and IsReverse:
        raise ValueError("ordinary revolve reversed mid plane is unqualified")
    if AgainstValue is not None:
        CheckRevPair(AlongValue, AgainstValue)
    LowerValue, UpperValue = ResultValue.IntervalValue
    if UpperValue - LowerValue >= FullTurn:
        raise ValueError("ordinary revolve extended ends require a partial turn")
    return ResultValue
