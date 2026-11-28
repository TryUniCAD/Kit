from convert.adapters.solidworks.Archive.Construction.Blind.BlindZeroFields import (
    KBlindZeroFields,
)
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# inactive draft and secondary controls cannot authorize a different analytic prism
def CheckDimLeafEnd(OwnerValue: ExtrudeOwner) -> None:
    FieldsValue = OwnerValue.EndValue.FieldsValue
    if (
        any(FieldsValue.get(FieldName) != 0 for FieldName in KBlindZeroFields)
        or FieldsValue.get("f128") != 1
        or FieldsValue.get("f138") is not None
        or FieldsValue.get("f90") is not None
        or FieldsValue.get("fa0") != 0.0
        or not IsLineState(FieldsValue.get("fe0"))
        or not IsLineState(FieldsValue.get("f100"))
        or RequireNative(FieldsValue.get("f140"), "moFromEndSpec_c").FieldsValue
        != {"t": 0}
    ):
        raise ValueError("dimensioned cold leaf has unsupported start or end state")
