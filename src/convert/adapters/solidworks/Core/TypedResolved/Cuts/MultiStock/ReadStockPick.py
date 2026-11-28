from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Cuts.CheckSavedCutScope import (
    CheckCutScope,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.CheckPickMirror import (
    CheckPickMirror,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.CheckStockFace import (
    CheckStockFace,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadStockAtoms import (
    ReadStockAtoms,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.StockCutAtoms import (
    StockCutAtoms,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadCutAtomId import (
    ReadCutAtomId,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadSingleNode import (
    ReadSingleNode,
)
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# a saved selector can omit its face only when the consumed atom and both actual choosers prove the same stock
def ReadStockPick(
    LinkValue: NativeLink,
    StockValues: tuple[ExtrudeOwner, ExtrudeOwner],
    CutValue: ExtrudeOwner,
) -> tuple[StockCutAtoms, ArchiveNode]:
    FirstStock, SecondStock = StockValues
    CutNode = CutValue.NodeValue
    Atoms = ReadStockAtoms(
        LinkValue, FirstStock.NodeValue, SecondStock.NodeValue, CutNode
    )
    Stock = StockValues[Atoms.SelectedIndex]
    StockNode = Stock.NodeValue
    RootValue = RequireNative(LinkValue.ConfigValue.RootValue, "moPart_c")
    AtomId = ReadCutAtomId(Atoms.ConsumedAtom, StockNode)
    if CheckCutScope(RootValue, StockNode, CutNode, AtomId, StockScope=0) != 1:
        raise ValueError("two stock cut requires its actual selected scope")
    Wrapper = ReadSingleNode(CutNode.FieldsValue.get("f548"), "moCompSolidBody_c")
    Fields = Wrapper.FieldsValue
    if Fields.get("ff0") is not None:
        CheckStockFace(Wrapper, StockNode)
    else:
        Component = RequireNative(Fields.get("f58"), "moUnitComponent_c")
        if (
            Component.FieldsValue.get("has_ext") != 0
            or Fields.get("f100") != 0
            or Fields.get("f104") != 0
        ):
            raise ValueError(
                "face-less saved stock selector has alternate component or cache state"
            )
        CheckTreeAlias(LinkValue, (Wrapper, Component, StockNode, CutNode))
        CheckPickMirror(LinkValue, Stock, CutValue)
    return Atoms, Wrapper
