from typing import cast as CastValue
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.CmgrHeader.WriteMgrHeader import WriteMgrHeader
from convert.adapters.solidworks.Archive.Config.ConfigGraph import ConfigGraph
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeBiography import (
    MakeBiography,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeFreshHist import (
    MakeFreshHist,
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
from convert.adapters.solidworks.Archive.History.WriteHistGraph import WriteHistGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Resolved.ResolvedGraph import ResolvedGraph
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Format import (
    KeywordsStream,
    KResolvedFeaturesStream,
)


# complete part serialization must use each real sdk stream owner and extend the exact configuration map without saved stream fallback
def EmitPartArchive(
    SystemValue: PartSystem,
    FeatureValues: tuple[ArchiveNode, ...],
    HeadersValue: tuple[ArchiveNode, ArchiveNode, ArchiveNode],
    DefinitionValue: ModelDefGraph,
    InputValue: PartBuildInput,
    KeywordsValue: bytes,
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
        "Contents/CMgrHdr2": WriteMgrHeader(ManagerHeader, 19000)[0],
        KResolvedFeaturesStream: ResolvedBytes,
        "Contents/Definition": WriteModelDef(DefinitionValue).OutputValue,
        "_MO_VERSION_19000/Biography": WriteHistGraph(MakeBiography(), 19000)[0],
        "_MO_VERSION_19000/History": WriteHistGraph(
            MakeFreshHist(InputValue.HistoryValue), 19000
        )[0],
        KeywordsStream: KeywordsValue,
    }
    return StreamsValue, ConfigValue, ResolvedValue
