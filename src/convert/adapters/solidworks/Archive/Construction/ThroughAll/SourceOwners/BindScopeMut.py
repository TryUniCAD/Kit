from typing import cast as CastValue

from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadRows

from convert.adapters.solidworks.Archive.Construction.BodyScope.BindStockMut import (
    BindStockMut,
)
from convert.adapters.solidworks.Archive.Construction.BodyScope.MakeBodyRef import (
    MakeBodyRef,
)
from convert.adapters.solidworks.Archive.Construction.BodyScope.StockBodyGraph import (
    StockBodyGraph,
)
from convert.adapters.solidworks.Archive.Construction.Extrusion.CutGraph import CutGraph
from convert.adapters.solidworks.Archive.Construction.Extrusion.ExtrusionGraph import (
    ExtrusionGraph,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceInputs.ThruOwnerInput import (
    ThruOwnerInput,
)


# the owner component must reuse fresh atom and body reference rules without fabricating a complete part candidate
def BindScopeMut(
    InputValue: ThruOwnerInput,
    SystemValue: PartSystem,
    StockValue: ExtrusionGraph,
    CutValue: CutGraph,
) -> StockBodyGraph:
    RootValue, FeatureValue = SystemValue.RootValue, StockValue.FeatureValue
    if (
        InputValue.ScopeValue.StockValues != (InputValue.ShapeValue.StockValue,)
        or InputValue.ScopeValue.StockValues[0] is not InputValue.ShapeValue.StockValue
    ):
        raise ValueError("source selection differs from its actual typed stock")
    ManagerValue = RootValue.FieldsValue.get("fd88")
    if not isinstance(ManagerValue, dict):
        raise ValueError("fresh owner graph lacks its actual mutable atom manager")
    Manager = CastValue(dict[str, object], ManagerValue)
    if Manager.get("n6c") != 0 or ReadRows(Manager.get("atoms")):
        raise ValueError("owner component cannot replace existing stock bodies")
    AtomValue = BindStockMut(Manager, FeatureValue)
    WrapperValue = MakeBodyRef(RootValue, FeatureValue, AtomValue)
    FeatureValue.FieldsValue["f544"] = 1
    CutValue.FeatureValue.FieldsValue.update(
        f544=1, has_f548=1, f548={"n": 1, "items": [{"o": WrapperValue}]}
    )
    return StockBodyGraph(
        InputValue.ShapeValue.StockValue,
        RootValue,
        FeatureValue,
        AtomValue,
        WrapperValue,
        CutValue.FeatureValue,
    )
