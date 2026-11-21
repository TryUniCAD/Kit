from convert.adapters.solidworks.Archive.Construction.Part.EmitPartArchive import (
    EmitPartArchive,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Emission.MakePatKeys import (
    MakePatKeys,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Graph.PatPartGraph import (
    PatPartGraph,
)
from convert.adapters.solidworks.Archive.Definition.Construction.MakePartDef import (
    MakePartDef,
)
from convert.adapters.solidworks.Container.Container import BuildSldprt


# the complete ordinary part emits the merged editable feature graph without storing a physical body cache
def EmitPatArchive(GraphValue: PatPartGraph) -> tuple[dict[str, bytes], bytes]:
    StockValue = GraphValue.StockValue
    Settings = StockValue.SettingsValue
    Definition = MakePartDef(Settings.DefinitionValue, Settings.DensityValue)
    Roots = GraphValue.RootsValue
    Streams, Config, Resolved = EmitPartArchive(
        StockValue.SystemValue,
        Roots,
        GraphValue.HeaderValues,
        Definition,
        Settings,
        MakePatKeys(GraphValue),
    )
    if (
        Config.MapValue.CounterValue >= Resolved.MapValue.CounterValue
        or Resolved.RootsValue != Roots
        or any(
            "Partition" in NameValue or "LocalBodies" in NameValue
            for NameValue in Streams
        )
    ):
        raise ValueError(
            "local pattern constructor must extend the same ordinary part and omit stored physical body rows"
        )
    return Streams, BuildSldprt(Streams, FormatVersion=4)
