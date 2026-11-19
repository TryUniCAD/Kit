from convert.adapters.solidworks.Archive.Construction.Blind.BlindZeroFields import (
    KBlindZeroFields,
)
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from interchange.Features.FeatureExtrude import ExtrudeEnd


# supported scalar end flags preserve both active directions and reject draft starts and selected termination geometry
def CheckCircEnd(OwnerValue: ExtrudeOwner) -> None:
    Fields = OwnerValue.EndValue.FieldsValue
    EndCode = 6 if OwnerValue.ModeValue == ExtrudeEnd.KMidPlane else 0
    if (
        any(
            Fields.get(NameValue) != (EndCode if NameValue == "f0c" else 0)
            for NameValue in KBlindZeroFields
        )
        or Fields.get("f08") != int(OwnerValue.ModeValue != ExtrudeEnd.KTwoLengths)
        or Fields.get("f8c") != int(OwnerValue.IsReversed)
        or Fields.get("f128") != 1
    ):
        raise ValueError("cache free circle has unsupported termination options")
    if (
        Fields.get("f138") is not None
        or Fields.get("f90") is not None
        or Fields.get("fa0") != 0.0
    ):
        raise ValueError("cache free circle has reference or draft termination state")
    if not IsLineState(Fields.get("fe0")) or not IsLineState(Fields.get("f100")):
        raise ValueError("cache free circle has end selection collections")
    FromValue = RequireNative(Fields.get("f140"), "moFromEndSpec_c")
    if FromValue.FieldsValue != {"t": 0}:
        raise ValueError("cache free circle has a nonordinary start owner")
