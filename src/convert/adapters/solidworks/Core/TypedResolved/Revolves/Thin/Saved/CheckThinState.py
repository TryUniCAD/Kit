from convert.adapters.solidworks.Archive.Construction.Nodes.AtomSeeds import (
    KAtomLists,
    KAtomWords,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows


# saved output flags distinguish the actual single body chooser from consume and modifier branches
def CheckThinState(
    FeatureValue: ArchiveNode, RootValue: ArchiveNode, AtomValue: ArchiveNode
) -> None:
    FieldsValue = FeatureValue.FieldsValue
    ActiveFlags: dict[str, int] = dict.fromkeys(
        (
            "has_f528",
            "n494",
            "f544",
            "has_f4a8",
            "has_f4b0",
            "f4b8",
            "has_f4c0",
            "has_f3d0",
        ),
        1,
    )
    ActiveFlags["f540"] = 3
    if (
        any(
            FieldsValue.get(NameValue) != ActiveFlags.get(NameValue, 0)
            for NameValue in KAtomWords
        )
        or FieldsValue.get("f4a0") != 1
        or any(
            not IsLineState(FieldsValue.get(NameValue))
            for NameValue in KAtomLists
            if NameValue != "f498"
        )
    ):
        raise ValueError("SOLIDWORKS saved thin has alternate output or modifier state")
    Manager = NativeRecord(RootValue.FieldsValue.get("fd88"))
    GhostValue = NativeRecord(RootValue.FieldsValue.get("fd90"))
    BodyId = AtomValue.FieldsValue.get("f140")
    if (
        Manager.get("fa8") != 19000
        or Manager.get("f260") != BodyId
        or GhostValue.get("n") != 0
        or GhostValue.get("objects")
        or tuple(RowValue.get("v") for RowValue in NativeRows(FieldsValue.get("f498")))
        != (BodyId,)
    ):
        raise ValueError(
            "SOLIDWORKS saved thin has unresolved live or ghost body identities"
        )
