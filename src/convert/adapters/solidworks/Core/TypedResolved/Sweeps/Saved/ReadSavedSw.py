from hashlib import sha256 as CalcSha

from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Archive.Construction.Sweeps.SweepLabels import (
    SweepLabels,
)
from convert.adapters.solidworks.Archive.Header.ReadFileTable import GetFileRef
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KeywordsStream, KPartFormatId
from convert.adapters.solidworks.Core.ConfigLanes import ResolvedLanes
from convert.adapters.solidworks.Core.Native import ParseKeywords
from convert.adapters.solidworks.Core.Properties.ApplyPartText import ApplyPartText
from convert.adapters.solidworks.Core.Properties.ReadPartText import ReadPartText
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.MakeSwDoc import MakeSwDesign
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.ReadSwGraph import (
    ReadSwGraph,
)
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.Saved.CheckSwHist import (
    CheckSwHist,
)
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.Saved.CheckSwRefs import (
    CheckSwRefs,
)
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.Saved.ReadSwResult import (
    ReadSwResult,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Records.RecordSource import CadSource


# the reader projects only an independently checked single active saved standard sweep
def ReadSavedSw(
    Archive: SldprtArchive, DataValue: bytes, Label: str, SettingsValue: ReadOptions
) -> CadDocument:
    ConfigValues, _ = ParseKeywords(Archive.require(KeywordsStream))
    if (
        len(ConfigValues) != 1
        or ConfigValues[0].configuration_id != 0
        or set(ResolvedLanes(Archive.streams)) != {0}
    ):
        raise ValueError("SOLIDWORKS saved sweep requires one actual configuration")
    (KeywordsValue,) = ConfigValues
    GraphValue = ReadSwGraph(Archive, Saved=True)
    LinkedConfig = GraphValue.LinkValue.ConfigValue
    Header = LinkedConfig.HeaderValue.FieldsValue
    FileValue = GetFileRef(Header.get("f38"))
    ConfigValue = GraphValue.ConfigValue
    ActualName = ReadNativeName(ConfigValue)
    if (
        ActualName != KeywordsValue.name
        or ActualName != FileValue.ConfigValue
        or NativeNodeId(ConfigValue) != KeywordsValue.configuration_id
        or not FileValue.NameValue
        or SettingsValue.configuration not in (None, ActualName)
    ):
        raise ValueError(
            "SOLIDWORKS saved sweep has a foreign or unavailable configuration owner"
        )
    CheckSwHist(GraphValue, SweepLabels(FileValue.NameValue))
    CheckSwRefs(GraphValue, FileValue)
    SavedBody = ReadSwResult(
        Archive, GraphValue, IncludeBrep=SettingsValue.include_brep
    )
    SourceValue = CadSource(
        KPartFormatId,
        Label,
        CalcSha(DataValue).hexdigest(),
        container_version="4",
        attributes={
            "native_locator": FileValue.PathValue,
            "written_at": Header.get("f70"),
            "saved_sweep_result": True,
        },
    )
    Document = MakeSwDesign(
        GraphValue,
        SourceValue,
        FileValue.NameValue,
        SettingsValue.include_brep,
        SavedBody,
    )
    TextValue = ReadPartText(Document, Archive, LinkedConfig=LinkedConfig)
    return Document if TextValue is None else ApplyPartText(Document, TextValue)
