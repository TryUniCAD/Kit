from convert.adapters.solidworks.Archive.Construction.BodyScope.BindStockMut import (
    BindStockMut,
)
from convert.adapters.solidworks.Archive.Construction.Configuration.SetCfgStampMut import (
    SetCfgStampMut,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.BindSeedBodyMut import (
    BindSeedBodyMut,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.SeedStockGraph import (
    SeedStockGraph,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import RequireNode


# the actual sole joined seed keeps its plate lineage and supplies the pattern result allocation
def FinishPatMut(
    StockValue: SeedStockGraph,
    PatternValue: ArchiveNode,
    LineValue: ArchiveNode,
    ReversedValue: bool,
) -> None:
    SystemValue = StockValue.SystemValue
    ModelValue = SystemValue.RootValue
    Fields = RequireNode(PatternValue, "moLPattern_c").FieldsValue
    Manager = ModelValue.FieldsValue.get("fd88")
    _ = RequireNode(LineValue, "moLineRef_w")
    if (
        Fields.get("owner") is not ModelValue
        or "f1288" in Fields
        or not isinstance(Manager, dict)
    ):
        raise ValueError("pattern completion requires its actual fresh local owner")
    _ = StockValue.Allocator.AllocateMut(PatternValue)
    Fields.update(f1288=LineValue, f1298=int(ReversedValue))
    Result = BindStockMut(
        CastValue(dict[str, object], Manager),
        PatternValue,
        AppendMember=True,
    )
    PlateValue = StockValue.PlateValue
    SeedValue = StockValue.SeedValue
    _ = BindSeedBodyMut(
        ModelValue,
        SeedValue.FeatureValue,
        SeedValue.AtomValue,
        PatternValue,
        Result,
        PriorValues=((PlateValue.FeatureValue, PlateValue.AtomValue),),
    )
    Fields["f9f0"] = 1
    SetCfgStampMut(SystemValue.ConfigValues[0], StockValue.Allocator)


from typing import cast as CastValue
