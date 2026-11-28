from convert.adapters.solidworks.Archive.Config.ConfigGraph import ConfigGraph
from convert.adapters.solidworks.Archive.Construction.Part.EmitPartArchive import (
    EmitPartArchive,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordDim import (
    KeywordDim,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakePartKeys import (
    MakePartKeys,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import (
    BlindPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Definition.ModelDefGraph import ModelDefGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Resolved.ResolvedGraph import ResolvedGraph


# complete part serialization must use each real sdk stream owner and extend the exact configuration map without saved stream fallback
def EmitPartStreams(
    SystemValue: PartSystem,
    FeatureValues: tuple[ArchiveNode, ...],
    HeadersValue: tuple[ArchiveNode, ArchiveNode, ArchiveNode],
    DefinitionValue: ModelDefGraph,
    InputValue: PartBuildInput,
    PlanValue: BlindPlan,
    SketchDims: tuple[KeywordDim, ...] = (),
) -> tuple[dict[str, bytes], ConfigGraph, ResolvedGraph]:
    return EmitPartArchive(
        SystemValue,
        FeatureValues,
        HeadersValue,
        DefinitionValue,
        InputValue,
        MakePartKeys(SystemValue, FeatureValues, InputValue, PlanValue, SketchDims),
    )
