from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadStockAtom import (
    ReadStockAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.StockCutAtoms import (
    StockCutAtoms,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadManagedCutAtoms import (
    ReadCutAtoms,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadSingleNode import (
    ReadSingleNode,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink


# an independent surviving stock must be retained alongside the input and output of the cut
def ReadStockAtoms(
    LinkValue: NativeLink,
    FirstStock: ArchiveNode,
    SecondStock: ArchiveNode,
    CutValue: ArchiveNode,
) -> StockCutAtoms:
    StocksValue = (ReadStockAtom(FirstStock, False), ReadStockAtom(SecondStock, False))
    ResultAtom = ReadStockAtom(CutValue, True)
    Outputs = (*StocksValue, ResultAtom)
    if len({AtomValue.FieldsValue["f140"] for AtomValue in Outputs}) != 3 or ReadCutAtoms(
        LinkValue
    ) != set(Outputs):
        raise ValueError("two stock output atoms do not exhaust the actual manager")
    Consumed = ReadSingleNode(CutValue.FieldsValue.get("f530"), "moAtom_c")
    if Consumed is not StocksValue[0] and Consumed is not StocksValue[1]:
        raise ValueError("two stock cut does not consume an actual independent stock")
    Selected = int(Consumed is StocksValue[1])
    Untouched = StocksValue[1 - Selected]
    if tuple(
        AtomValue.FieldsValue.get("f144")
        for AtomValue in (Consumed, Untouched, ResultAtom)
    ) != (1, 0, 0):
        raise ValueError("two stock consumed and surviving atom states differ")
    return StockCutAtoms(Selected, Consumed, Untouched, ResultAtom)
