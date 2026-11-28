from convert.adapters.solidworks.Archive.Construction.Configuration.SetCfgStampMut import (
    SetCfgStampMut,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.EmitPartArchive import (
    EmitPartArchive,
)
from convert.adapters.solidworks.Archive.Construction.Part.Imports.BindImportMut import (
    BindImportMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.Imports.BindImportScene import (
    BindImportScene,
)
from convert.adapters.solidworks.Archive.Construction.Part.Imports.FinishImportMut import (
    FinishImportMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.Imports.ImportCandidate import (
    ImportCandidate,
)
from convert.adapters.solidworks.Archive.Construction.Part.Imports.LogImportMut import (
    LogImportMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.Imports.MakeImportKeys import (
    MakeImportKeys,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import (
    MakePartBaseMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakePartHeaders import (
    MakePartHeaders,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartLabels import PartLabels
from convert.adapters.solidworks.Archive.Construction.System.Members.LightInput import (
    LightInput,
)
from convert.adapters.solidworks.Archive.Definition.Construction.MakePartDef import (
    MakePartDef,
)
from convert.adapters.solidworks.Archive.Partition.ImportHistory.ImportEvent import (
    ImportEvent,
)
from convert.adapters.solidworks.Archive.Partition.ImportHistory.MakeImportHist import (
    MakeImportHist,
)
from convert.adapters.solidworks.Archive.Partition.LocalWrite.EncodeLocalBody import (
    EncodeLocalBody,
)
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Container.Container import BuildSldprt
from convert.adapters.solidworks.Container.Format import (
    KLocalBodyStream,
    KPartitionStream,
)


# the imported solid assembly uses independent body geometry and one shared feature history
def MakeBoxPart(
    InputValue: PartBuildInput,
    LabelsValue: PartLabels,
    NodesValue: tuple[XmtNode, ...],
    AmbientValue: LightInput,
) -> ImportCandidate:
    Allocator = PersistentIds()
    SystemValue = MakePartBaseMut(InputValue, LabelsValue, Allocator)
    TargetValue = InputValue.TargetValue
    HistoryValue = MakeImportHist(
        TargetValue.FileVersion, (ImportEvent.KActivation, ImportEvent.KLocalAttach)
    )
    FeatureValue, AtomId = BindImportMut(
        SystemValue,
        Allocator,
        TargetValue,
        LabelsValue.FeatureName,
        HistoryValue.MarkIds,
    )
    BindImportScene(SystemValue, (AmbientValue,), TargetValue, Allocator)
    SetCfgStampMut(SystemValue.ConfigValues[0], Allocator)
    HeadersValue = MakePartHeaders(SystemValue, InputValue, Allocator)
    _ = LogImportMut(FeatureValue, HeadersValue, InputValue.HeaderValue)
    FinishImportMut(SystemValue, FeatureValue, HeadersValue, InputValue)
    DefinitionValue = MakePartDef(InputValue.DefinitionValue, InputValue.DensityValue)
    KeywordsValue = MakeImportKeys(
        SystemValue, FeatureValue, InputValue.HeaderValue.ModifiedAt
    )
    StreamsValue, ConfigValue, ResolvedValue = EmitPartArchive(
        SystemValue,
        (*SystemValue.FeatureValues, FeatureValue),
        HeadersValue,
        DefinitionValue,
        InputValue,
        KeywordsValue,
        BodyMapFields={"n": 0, "fcd8": []},
    )
    StreamsValue.update(
        {
            KLocalBodyStream: EncodeLocalBody(LabelsValue.FeatureName, NodesValue),
            KPartitionStream: HistoryValue.BytesValue,
        }
    )
    return ImportCandidate(
        SystemValue,
        FeatureValue,
        AtomId,
        HeadersValue,
        DefinitionValue,
        ConfigValue,
        ResolvedValue,
        StreamsValue,
        BuildSldprt(StreamsValue, FormatVersion=4),
    )
