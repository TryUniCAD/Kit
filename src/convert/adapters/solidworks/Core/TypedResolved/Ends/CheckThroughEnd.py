from collections.abc import Mapping

from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import (
    IsLineState,
)


# unbounded cuts require actual null length owners and no alternate geometric controls
def CheckThroughEnd(FieldsValue: Mapping[str, object]) -> None:
    if any(
        FieldsValue.get(NameValue) is not None
        for NameValue in ("f18", "f20", "fc8", "fd0", "f138", "f90")
    ) or any(
        FieldsValue.get(NameValue) != 0
        for NameValue in (
            "fa0",
            "fb8",
            "fbc",
            "fc0",
            "fc4",
            "fb0",
            "fb4",
            "fa8",
            "fac",
            "fd8",
            "fdc",
            "f12c",
            "f130",
            "f148",
            "f14c",
        )
    ):
        raise ValueError("typed through all cut carries active distance or draft state")
    if FieldsValue.get("f128") != 1 or not all(
        IsLineState(FieldsValue.get(NameValue)) for NameValue in ("fe0", "f100")
    ):
        raise ValueError("typed through all cut has unsupported selection state")
