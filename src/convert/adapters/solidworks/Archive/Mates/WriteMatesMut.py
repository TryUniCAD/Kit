from convert.adapters.solidworks.Archive.Counts.EncodeCount import EncodeCount
from convert.adapters.solidworks.Archive.Mates.MatesGraph import MatesGraph
from convert.adapters.solidworks.Archive.Resolved.ResolvedGraph import ResolvedGraph
from convert.adapters.solidworks.Archive.Scalars.EncodeScalar import EncodeScalar


# rigid nested assemblies emit the measured empty mate list using their actual inherited map
def WriteEmptyMates(ResolvedValue: ResolvedGraph) -> tuple[bytes, MatesGraph]:
    if ResolvedValue.ContextValue.get("model_is_part") != 0:
        raise ValueError("empty mate list requires a SOLIDWORKS assembly graph")
    SeedValue = ResolvedValue.MapValue
    DataValue = EncodeScalar(SeedValue.CounterValue, "i32") + EncodeCount(0)
    return DataValue, MatesGraph(
        (),
        SeedValue,
        SeedValue.CounterValue,
        ResolvedValue.VersionValue,
        dict(ResolvedValue.ContextValue),
        {"completed": True},
    )
