from convert.adapters.solidworks.Archive.Construction.BodyNames.MakeColdAtom import (
    MakeColdAtom,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName


# stock selection needs the shared cold atom while keeping its body label in native derived name state
def MakeStockAtom(FeatureValue: ArchiveNode, AtomId: int) -> ArchiveNode:
    OutputValue = MakeColdAtom(ReadNodeName(FeatureValue), AtomId, FeatureValue)
    OutputValue.FieldsValue.update(f18=None, f18c=1)
    return OutputValue
