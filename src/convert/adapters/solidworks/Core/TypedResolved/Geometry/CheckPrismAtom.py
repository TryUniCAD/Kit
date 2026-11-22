from typing import Literal

from convert.adapters.solidworks.Archive.Construction.Nodes.AtomSeeds import (
    KAtomLists,
    KAtomWords,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState


# fresh atom owners cannot carry unrepresented bodies selection lists rollback marks or extra shape modifiers
def CheckPrismAtom(
    NodeValue: ArchiveNode,
    HasColdOutput: bool = False,
    *,
    SelectedScope: Literal["stock", "cut", "first_creator"] | None = None,
) -> None:
    Fields = NodeValue.FieldsValue
    HasOutput = HasColdOutput or SelectedScope == "stock"
    if SelectedScope == "first_creator" and (
        HasOutput
        or any(
            Fields.get(FieldName) is not None for FieldName in ("f528", "f530", "f548")
        )
    ):
        raise ValueError("cache free first creator has stored body owners")
    Expected = {
        "has_f528": int(HasOutput),
        "n494": int(HasOutput),
        "f544": int(SelectedScope is not None),
        "has_f548": int(SelectedScope == "cut"),
    }
    if any(
        Fields.get(FieldName) != Expected.get(FieldName, 0) for FieldName in KAtomWords
    ):
        raise ValueError("cache free prism has atom attachment or modifier flags")
    if any(
        not IsLineState(Fields.get(FieldName))
        for FieldName in KAtomLists
        if not HasOutput or FieldName != "f498"
    ):
        raise ValueError("cache free prism has selected or attached geometry")
    if Fields.get("f538") is not None or Fields.get("f4a0") != 1:
        raise ValueError("cache free prism has an additional atom owner")
