from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadStockAtoms import (
    ReadStockAtoms,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.CheckRevPick import (
    CheckRevPick,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.ReadRevCutOps import (
    ReadRevCutOps,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.ReadRevCutTree import (
    ReadRevCutTree,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.ReadRevWrapper import (
    ReadRevWrapper,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.RevCutLineage import (
    RevCutLineage,
)


# public angular and body ownership should bind only after all three live operations agree
def ReadSelRevCut(LinkValue: NativeLink, TopHeader: ArchiveNode) -> RevCutLineage:
    Features = ReadRevCutTree(LinkValue)
    First, Second, CutValue = ReadRevCutOps(LinkValue, Features)
    Stocks = (First, Second)
    if any(
        Value.NodeValue.FieldsValue.get("f544") != 1
        or Value.NodeValue.FieldsValue.get("has_f548") != 0
        or Value.NodeValue.FieldsValue.get("f548") is not None
        for Value in Stocks
    ):
        raise ValueError("independent revolve stocks have an alternate body selector")
    Atoms = ReadStockAtoms(
        LinkValue, First.NodeValue, Second.NodeValue, CutValue.NodeValue
    )
    Wrapper = ReadRevWrapper(
        LinkValue, Stocks[Atoms.SelectedIndex].NodeValue, CutValue.NodeValue, Atoms
    )
    Result = RevCutLineage(Stocks, CutValue, Atoms, Wrapper)
    CheckRevPick(LinkValue, TopHeader, Result)
    return Result
