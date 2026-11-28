from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadCutAtomId import (
    ReadCutAtomId,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadSingleNode import (
    ReadSingleNode,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows


# each output needs the same identity in its actual atom and feature result collection
def ReadStockAtom(Feature: ArchiveNode, CutOutput: bool) -> ArchiveNode:
    Fields = Feature.FieldsValue
    if (
        Fields.get("has_f528") != 1
        or Fields.get("has_f530") != int(CutOutput)
        or Fields.get("f538") is not None
        or Fields.get("n494") != 1
    ):
        raise ValueError("two stock operation has alternate body collections")
    AtomValue = ReadSingleNode(Fields.get("f528"), "moAtom_c")
    ResultIds = NativeRows(Fields.get("f498"))
    if tuple(RowValue.get("v") for RowValue in ResultIds) != (
        ReadCutAtomId(AtomValue, Feature),
    ):
        raise ValueError("two stock result identity differs from its actual atom")
    return AtomValue
