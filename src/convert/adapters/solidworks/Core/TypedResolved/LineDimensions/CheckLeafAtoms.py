from convert.adapters.solidworks.Archive.Construction.Nodes.AtomSeeds import (
    KAtomLists,
    KAtomWords,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord


# forward cold leaves cannot derive a body from ambiguous modifiers or retained body selectors
def CheckLeafAtoms(NodeValue: ArchiveNode, RootValue: ArchiveNode) -> None:
    FieldsValue = NodeValue.FieldsValue
    RootFields = RootValue.FieldsValue
    AtomsValue = NativeRecord(RootFields.get("fd88"))
    Excluded = NativeRecord(RootFields.get("fd90"))
    if (
        any(FieldsValue.get(FieldName) != 0 for FieldName in KAtomWords)
        or any(not IsLineState(FieldsValue.get(FieldName)) for FieldName in KAtomLists)
        or any(
            FieldsValue.get(FieldName) is not None
            for FieldName in ("f528", "f530", "f548")
        )
        or FieldsValue.get("f4a0") != 1
        or AtomsValue.get("n6c") != 0
        or AtomsValue.get("fa8") != 0
        or AtomsValue.get("atoms")
        or Excluded.get("n") != 0
        or Excluded.get("objects")
        or RootFields.get("f1420") is not None
    ):
        raise ValueError("dimensioned cold leaf has extra body or scope ownership")
