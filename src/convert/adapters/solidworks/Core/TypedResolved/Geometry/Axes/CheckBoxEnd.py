from convert.adapters.solidworks.Archive.Construction.Blind.BlindZeroFields import (
    KBlindZeroFields,
)
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismParam import (
    ReadPrismParam,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# the signed blind boss must own a live distinct driver without other end or draft intent
def CheckBoxEnd(OwnerValue: ExtrudeOwner) -> None:
    Fields = OwnerValue.EndValue.FieldsValue
    if (
        not OwnerValue.IsReversed
        or OwnerValue.ParentsValue != (OwnerValue.ProfileValue,)
        or any(Fields.get(NameValue) != 0 for NameValue in KBlindZeroFields)
        or Fields.get("f08") != 1
        or Fields.get("f128") != 1
        or Fields.get("f138") is not None
        or Fields.get("f90") is not None
        or Fields.get("fa0") != 0.0
        or not IsLineState(Fields.get("fe0"))
        or not IsLineState(Fields.get("f100"))
        or RequireNative(Fields.get("f140"), "moFromEndSpec_c").FieldsValue != {"t": 0}
    ):
        raise ValueError("cache free box has unsupported signed blind end controls")
    Values = tuple(
        ReadPrismParam(Fields.get(NameValue), Angular)
        for NameValue, Angular in (
            ("f18", False),
            ("f20", False),
            ("fc8", True),
            ("fd0", True),
        )
    )
    if (
        len({DimValue.FieldsValue.get("f50") for DimValue, _, _ in Values}) != 4
        or len({Parameter for _, Parameter, _ in Values}) != 4
        or not Values[0][2] > 0
        or Values[0][2] != Values[1][2]
        or any(Value[2] != 0 for Value in Values[2:])
        or Values[0][:2]
        != (OwnerValue.DepthValue.Dimension, OwnerValue.DepthValue.Parameter)
    ):
        raise ValueError(
            "cache free box has duplicated or independent inactive end owners"
        )
