from convert.adapters.solidworks.Archive.Construction.Blind.BlindZeroFields import (
    KBlindZeroFields,
)
from convert.adapters.solidworks.Archive.Construction.Blind.EmptyEndArray import (
    EmptyEndArray,
)
from convert.adapters.solidworks.Archive.Construction.Blind.EndMode import KEndMode
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# solid extrusions share the native end record while their callers supply the appropriate live displays
def MakeEndSpec(
    ModeValue: KEndMode,
    IsReversed: bool,
    ForwardValue: ArchiveNode,
    ReverseValue: ArchiveNode | None,
    ForwardDraft: ArchiveNode | None,
    ReverseDraft: ArchiveNode | None,
    FromEndValue: ArchiveNode,
) -> ArchiveNode:
    FieldsValue: dict[str, object] = {FieldName: 0 for FieldName in KBlindZeroFields}
    FieldsValue.update(
        {
            "f138": None,
            "f08": int(ModeValue != "two_directions"),
            "f0c": 6 if ModeValue == "mid_plane" else 0,
            "f8c": int(IsReversed),
            "f90": None,
            "f18": ForwardValue,
            "f20": ReverseValue,
            "fa0": 0.0,
            "fc8": ForwardDraft,
            "fd0": ReverseDraft,
            "fe0": EmptyEndArray(),
            "f100": EmptyEndArray(),
            "f128": 1,
            "f140": FromEndValue,
        }
    )
    return ArchiveNode(RuntimeClass("moEndSpec_c", 1), FieldsValue)
