from convert.adapters.solidworks.Archive.Construction.Part.EmitPartArchive import (
    EmitPartArchive,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakePartHeaders import (
    MakePartHeaders,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Definition.Construction.MakePartDef import (
    MakePartDef,
)
from convert.adapters.solidworks.Container.Container import BuildSldprt
from convert.adapters.solidworks.Core.Preparation.TwoStock.MakeStockGraph import (
    MakeStockGraph,
)
from convert.adapters.solidworks.Core.Preparation.TwoStock.StockCandidate import (
    StockCandidate,
)
from convert.adapters.solidworks.Core.Preparation.TwoStock.StockKeywords import (
    StockKeywords,
)
from convert.adapters.solidworks.Core.Preparation.TwoStock.TwoStockPlan import (
    TwoStockPlan,
)


# the neutral evaluator and future adapter must share the exact same complete part construction
def EmitStockPart(
    PlanValue: TwoStockPlan, SettingsValue: PartBuildInput
) -> StockCandidate:
    GraphValue = MakeStockGraph(SettingsValue, PlanValue)
    SystemValue = GraphValue.SystemValue
    StreamsValue, _, _ = EmitPartArchive(
        SystemValue,
        GraphValue.RootValues,
        MakePartHeaders(SystemValue, SettingsValue, GraphValue.Allocator),
        MakePartDef(SettingsValue.DefinitionValue, SettingsValue.DensityValue),
        SettingsValue,
        StockKeywords(GraphValue, SettingsValue, PlanValue.NameValue),
    )
    if any(
        "Partition" in NameValue or "LocalBodies" in NameValue
        for NameValue in StreamsValue
    ):
        raise ValueError("fresh two-stock writer cannot generate a stored solid cache")
    return StockCandidate(StreamsValue, BuildSldprt(StreamsValue, FormatVersion=4))
