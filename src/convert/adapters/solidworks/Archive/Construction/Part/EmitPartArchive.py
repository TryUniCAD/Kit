from collections.abc import MutableMapping
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.CmgrHeader.WriteMgrHdrMut import WriteMgrHdrMut
from convert.adapters.solidworks.Archive.Config.ConfigGraph import ConfigGraph
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeBiography import (
    MakeBiography,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeFreshHist import (
    MakeFreshHist,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.MakePartProps import (
    MakePartProps,
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
from convert.adapters.solidworks.Container.Format import (
    KResolvedFeaturesStream,
    KeywordsStream,
)


# every fresh part feature family needs the same configuration map and stream owners
def EmitPartArchive(
    SystemValue: PartSystem,
    FeatureValues: tuple[ArchiveNode, ...],
    HeadersValue: tuple[ArchiveNode, ArchiveNode, ArchiveNode],
    DefinitionValue: ModelDefGraph,
    InputValue: PartBuildInput,
    KeywordsValue: bytes,
    *,
    BodyMapFields: MutableMapping[str, object] | None = None,
    PartRelations: bool = False,
) -> tuple[dict[str, bytes], ConfigGraph, ResolvedGraph]:
    HeaderValue, TopHeader, ManagerHeader = HeadersValue
    ConfigBytes, ConfigValue = WriteConfigMut(
        SystemValue.RootValue, 19000, HeaderValue, PartRelations=PartRelations
    )
    ContextValue = {
        "model_compressed_stream": 1,
        "model_is_part": 1,
        "cmgr_f658": CastValue(int, SystemValue.ManagerValue.FieldsValue["f658"]),
    }
    ResolvedBytes, ResolvedValue = WriteResolMut(
        FeatureValues, BodyMapFields, 19000, ConfigValue.MapValue, ContextValue
    )
    StreamsValue = {
        "Header2": WriteHeadGraph(TopHeader, 19000),
        "Contents/Config-0-ModelHeader": WriteHeadGraph(HeaderValue, 19000),
        "Contents/Config-0": ConfigBytes,
        "Contents/CMgr": WriteCmgrMut(SystemValue.ManagerValue, 19000),
        "Contents/CMgrHdr2": WriteMgrHdrMut(ManagerHeader, 19000)[0],
        KResolvedFeaturesStream: ResolvedBytes,
        "Contents/Definition": WriteModelDef(DefinitionValue).OutputValue,
        "_MO_VERSION_19000/Biography": WriteHistMut(MakeBiography(), 19000)[0],
        "_MO_VERSION_19000/History": WriteHistMut(
            MakeFreshHist(InputValue.HistoryValue), 19000
        )[0],
        KeywordsStream: KeywordsValue,
        **MakePartProps(InputValue.PropertiesValue),
    }
    return StreamsValue, ConfigValue, ResolvedValue
