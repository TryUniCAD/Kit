from convert.adapters.solidworks.Archive.Construction.Nodes.AtomSeeds import (
    KAtomLists,
    KAtomWords,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState


# fresh atom owners cannot carry unrepresented bodies selection lists rollback marks or extra shape modifiers
def CheckPrismAtom(NodeValue: ArchiveNode, HasColdOutput: bool = False) -> None:
    Fields = NodeValue.FieldsValue
    if any(
        Fields.get(FieldName) != 0
        for FieldName in KAtomWords
        if not HasColdOutput or FieldName not in ("has_f528", "n494")
    ):
        raise ValueError("cache free prism has atom attachment or modifier flags")
    if any(
        not IsLineState(Fields.get(FieldName))
        for FieldName in KAtomLists
        if not HasColdOutput or FieldName != "f498"
    ):
        raise ValueError("cache free prism has selected or attached geometry")
    if Fields.get("f538") is not None or Fields.get("f4a0") != 1:
        raise ValueError("cache free prism has an additional atom owner")
