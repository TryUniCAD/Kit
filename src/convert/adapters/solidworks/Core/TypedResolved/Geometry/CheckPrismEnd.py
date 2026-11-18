from convert.adapters.solidworks.Archive.Construction.Blind.BlindZeroFields import (
    KBlindZeroFields,
)
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismParam import (
    ReadPrismParam,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# blind scalar mode flags do not prove the absence of retained draft reference or start offset controls
def CheckPrismEnd(OwnerValue: ExtrudeOwner) -> None:
    Fields = OwnerValue.EndValue.FieldsValue
    if (
        any(Fields.get(FieldName) != 0 for FieldName in KBlindZeroFields)
        or Fields.get("f08") != 1
        or Fields.get("f8c") != 0
        or Fields.get("f128") != 1
    ):
        raise ValueError("cache free prism has unsupported termination options")
    if (
        Fields.get("f138") is not None
        or Fields.get("f90") is not None
        or Fields.get("fa0") != 0.0
    ):
        raise ValueError("cache free prism has reference or draft termination state")
    if not IsLineState(Fields.get("fe0")) or not IsLineState(Fields.get("f100")):
        raise ValueError("cache free prism has end selection collections")
    FromValue = RequireNative(Fields.get("f140"), "moFromEndSpec_c")
    if FromValue.FieldsValue != {"t": 0}:
        raise ValueError("cache free prism has a nonordinary start owner")
    Values = tuple(
        ReadPrismParam(Fields.get(FieldName), Angular)
        for FieldName, Angular in (
            ("f18", False),
            ("f20", False),
            ("fc8", True),
            ("fd0", True),
        )
    )
    if (
        len({Dimension for Dimension, _, _ in Values}) != 4
        or len({Parameter for _, Parameter, _ in Values}) != 4
    ):
        raise ValueError("cache free prism end roles share live owners")
    if (
        Values[0][2] <= 0
        or Values[1][2] != Values[0][2]
        or Values[2][2] != 0
        or Values[3][2] != 0
    ):
        raise ValueError(
            "cache free prism has draft or independent inactive end controls"
        )
    if len({Dimension.FieldsValue.get("f50") for Dimension, _, _ in Values}) != 4:
        raise ValueError("cache free prism has duplicated end dimension identities")
    if Values[0][1] is not OwnerValue.DepthValue.Parameter:
        raise ValueError(
            "cache free prism active depth does not alias its selected live owner"
        )
