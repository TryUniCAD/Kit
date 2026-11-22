from convert.adapters.solidworks.Archive.Construction.Blind.BlindZeroFields import (
    KBlindZeroFields,
)
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName


# saved stock retains two empty end collections and its single active depth
def CheckShellEnd(OwnerValue: ExtrudeOwner) -> None:
    Fields = OwnerValue.EndValue.FieldsValue
    if (
        any(
            Fields.get(NameValue) != int(NameValue in ("has_f28", "has_f48"))
            for NameValue in KBlindZeroFields
            if NameValue not in ("f150", "f154")
        )
        or Fields.get("f128") != 1
        or Fields.get("fa0") != 0.0
        or any(
            Fields.get(NameValue) is not None
            for NameValue in ("f138", "f90", "f20", "fc8", "fd0")
        )
        or not all(
            IsLineState(Fields.get(NameValue))
            for NameValue in ("f28", "f48", "fe0", "f100")
        )
        or ReadNativeName(OwnerValue.DepthValue.Parameter) != "D1"
    ):
        raise ValueError("SOLIDWORKS shell stock has unsupported blind end state")
