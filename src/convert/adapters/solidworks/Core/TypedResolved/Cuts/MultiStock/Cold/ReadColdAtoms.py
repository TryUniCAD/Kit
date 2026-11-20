from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadStockAtom import (
    ReadStockAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadCutAtomId import (
    ReadCutAtomId,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadManagedCutAtoms import (
    ReadCutAtoms,
)
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ColdOutput.CheckColdAtom import (
    CheckColdAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows


# each initial stock must own the same actual object in the history and manager
def ReadColdAtoms(
    LinkValue: NativeLink, StocksValue: tuple[ExtrudeOwner, ExtrudeOwner]
) -> tuple[tuple[ArchiveNode, ArchiveNode], tuple[int, int]]:
    FirstNode, SecondNode = (Value.NodeValue for Value in StocksValue)
    FirstAtom = ReadStockAtom(FirstNode, False)
    SecondAtom = ReadStockAtom(SecondNode, False)
    AtomsValue = (FirstAtom, SecondAtom)
    if FirstAtom is SecondAtom or set(AtomsValue) != ReadCutAtoms(LinkValue):
        raise ValueError("provisional stocks must be the two actual manager atoms")
    ManagerValue = NativeRecord(LinkValue.ConfigValue.RootValue.FieldsValue.get("fd88"))
    Assigned = tuple(
        RowValue.get("o") for RowValue in NativeRows(ManagerValue.get("atoms"))
    )
    FirstId = ReadCutAtomId(FirstAtom, FirstNode)
    SecondId = ReadCutAtomId(SecondAtom, SecondNode)
    if (
        Assigned != AtomsValue
        or ManagerValue.get("fa8") != 0
        or SecondId != FirstId + 1
        or ManagerValue.get("f260") != SecondId
    ):
        raise ValueError(
            "provisional stock atoms disagree with their manager allocation"
        )
    for AtomValue in AtomsValue:
        CheckColdAtom(AtomValue, ImplicitName=True)
    return AtomsValue, (FirstId, SecondId)
