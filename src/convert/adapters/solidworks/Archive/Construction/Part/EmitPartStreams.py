from typing import cast as CastValue
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.CmgrHeader.WriteMgrHdrMut import WriteMgrHdrMut
from convert.adapters.solidworks.Archive.Config.ConfigGraph import ConfigGraph
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeBiography import (
    MakeBiography,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordDim import (
    KeywordDim,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeFreshHist import (
    MakeFreshHist,
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
from convert.adapters.solidworks.Archive.Definition.WriteModelDef import WriteModelDef
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.History.WriteHistMut import WriteHistMut
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Resolved.ResolvedGraph import ResolvedGraph
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut


# complete part serialization must use each real sdk stream owner and extend the exact configuration map without saved stream fallback
def EmitPartStreams(
    SystemValue: PartSystem,
    FeatureValues: tuple[ArchiveNode, ...],
    HeadersValue: tuple[ArchiveNode, ArchiveNode, ArchiveNode],
    DefinitionValue: ModelDefGraph,
    InputValue: PartBuildInput,
    PlanValue: KPartPlan,
    SketchDims: tuple[KeywordDim, ...] = (),
) -> tuple[dict[str, bytes], ConfigGraph, ResolvedGraph]:
    HeaderValue, TopHeader, ManagerHeader = HeadersValue
    ConfigBytes, ConfigValue = WriteConfigMut(SystemValue.RootValue, 19000, HeaderValue)
    ContextValue = {
        "model_compressed_stream": 1,
        "model_is_part": 1,
        "cmgr_f658": CastValue(int, SystemValue.ManagerValue.FieldsValue["f658"]),
    }
    ResolvedBytes, ResolvedValue = WriteResolMut(
        FeatureValues, None, 19000, ConfigValue.MapValue, ContextValue
    )
    StreamsValue = {
        "Header2": WriteHeadGraph(TopHeader, 19000),
        "Contents/Config-0-ModelHeader": WriteHeadGraph(HeaderValue, 19000),
        "Contents/Config-0": ConfigBytes,
        "Contents/CMgr": WriteCmgrMut(SystemValue.ManagerValue, 19000),
        "Contents/CMgrHdr2": WriteMgrHdrMut(ManagerHeader, 19000)[0],
        "Contents/Config-0-ResolvedFeatures": ResolvedBytes,
        "Contents/Definition": WriteModelDef(DefinitionValue).OutputValue,
        "_MO_VERSION_19000/Biography": WriteHistMut(MakeBiography(), 19000)[0],
        "_MO_VERSION_19000/History": WriteHistMut(
            MakeFreshHist(InputValue.HistoryValue), 19000
        )[0],
        "swXmlContents/KeyWords": MakePartKeys(
            SystemValue, FeatureValues, InputValue, PlanValue, SketchDims
        ),
    }
    return StreamsValue, ConfigValue, ResolvedValue
