from convert.adapters.solidworks.Archive.Config.ConfigGraph import ConfigGraph
from convert.adapters.solidworks.Archive.Construction.Extrusion.CutGraph import CutGraph
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordDim import (
    KeywordDim,
)
from convert.adapters.solidworks.Archive.Construction.Part.EmitPartArchive import (
    EmitPartArchive,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakePartKeys import (
    MakePartKeys,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.PartPlan import (
    KPartPlan,
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
    PlanValue: KPartPlan,
    SketchDims: tuple[KeywordDim, ...] = (),
    *,
    CutValue: CutGraph | None = None,
    CutSketchDims: tuple[KeywordDim, ...] = (),
    PartRelations: bool = False,
) -> tuple[dict[str, bytes], ConfigGraph, ResolvedGraph]:
    KeywordsValue = MakePartKeys(
        SystemValue,
        FeatureValues,
        InputValue,
        PlanValue,
        SketchDims,
        CutValue=CutValue,
        CutSketchDims=CutSketchDims,
    )
    return EmitPartArchive(
        SystemValue,
        FeatureValues,
        HeadersValue,
        DefinitionValue,
        InputValue,
        KeywordsValue,
        PartRelations=PartRelations,
    )
