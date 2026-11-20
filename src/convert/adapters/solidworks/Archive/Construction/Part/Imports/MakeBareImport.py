from convert.adapters.solidworks.Archive.Construction.Configuration.SetCfgStampMut import (
    SetCfgStampMut,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.EmitPartArchive import (
    EmitPartArchive,
)
from convert.adapters.solidworks.Archive.Construction.Part.Imports.BindImportScene import (
    BindImportScene,
)
from convert.adapters.solidworks.Archive.Construction.Part.Imports.BindImportMut import (
    BindImportMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.Imports.CheckBareImport import (
    CheckBareImport,
)
from convert.adapters.solidworks.Archive.Construction.Part.Imports.FinishImportMut import (
    FinishImportMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.Imports.ImportKeyInput import (
    ImportKeyInput,
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
from convert.adapters.solidworks.Archive.Construction.Part.Imports.ReadImportScene import (
    ReadImportScene,
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
from convert.adapters.solidworks.Archive.Construction.System.MakePartExplode import (
    MakePartExplode,
)
from convert.adapters.solidworks.Archive.Construction.System.Members.AttachMembers import (
    AttachMembers,
)
from convert.adapters.solidworks.Archive.Construction.System.Members.LightInput import (
    LightInput,
)
from convert.adapters.solidworks.Archive.Construction.System.Members.MemberInput import (
    MemberInput,
)
from convert.adapters.solidworks.Archive.Construction.System.Members.NotesInput import (
    NotesInput,
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
from convert.adapters.solidworks.Archive.Partition.LocalCylinder.MakeLocalCyl import (
    MakeLocalCyl,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.MakeLocalPrism import (
    MakeLocalPrism,
)
from convert.adapters.solidworks.Archive.Partition.LocalWrite.EncodeLocalBody import (
    EncodeLocalBody,
)
from convert.adapters.solidworks.Container.Container import BuildSldprt
from convert.adapters.solidworks.Container.Format import (
    KLocalBodyStream,
    KPartitionStream,
)
from interchange.brep.Surfaces.BrepSurfaces import CylinderSurface
from interchange.document.Models.DocumentModel import CadDocument


# a local solid needs one fresh part graph whose feature and kernel owners share the same modeled events
def MakeBareImport(
    DocumentValue: CadDocument,
    InputValue: PartBuildInput,
    LabelsValue: PartLabels,
    *,
    AmbientValue: LightInput | None = None,
    LightValues: tuple[LightInput, ...] = (),
    NotesValue: NotesInput | None = None,
    HasEmptyExplodedView: bool = False,
    KeywordInput: ImportKeyInput | None = None,
) -> ImportCandidate:
    if type(HasEmptyExplodedView) is not bool:
        raise TypeError("part exploded view presence requires an explicit boolean")
    Selected = ReadImportScene(AmbientValue, LightValues)
    ModelValue = CheckBareImport(DocumentValue, InputValue, LabelsValue, Selected)
    NodesValue = (
        MakeLocalCyl(ModelValue)
        if any(isinstance(Surface, CylinderSurface) for Surface in ModelValue.surfaces)
        else MakeLocalPrism(ModelValue)
    )
    LocalValue = EncodeLocalBody(LabelsValue.FeatureName, NodesValue)
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
    NotesGraphValue = None
    if NotesValue is not None:
        NotesGraphValue = AttachMembers(
            SystemValue, MemberInput(NotesValue, Selected), TargetValue, Allocator
        ).NotesValue
    elif Selected:
        BindImportScene(SystemValue, Selected, TargetValue, Allocator)
    if HasEmptyExplodedView:
        SystemValue.RootValue.FieldsValue["f13f8"] = MakePartExplode(
            SystemValue.RootValue, TargetValue, Allocator
        )
    SetCfgStampMut(SystemValue.ConfigValues[0], Allocator)
    HeadersValue = MakePartHeaders(SystemValue, InputValue, Allocator)
    _ = LogImportMut(FeatureValue, HeadersValue, InputValue.HeaderValue)
    FinishImportMut(SystemValue, FeatureValue, HeadersValue, InputValue)
    DefinitionValue = MakePartDef(InputValue.DefinitionValue, InputValue.DensityValue)
    KeywordsValue = MakeImportKeys(
        SystemValue,
        FeatureValue,
        InputValue.HeaderValue.ModifiedAt,
        NotesGraphValue,
        KeywordInput=KeywordInput,
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
        {KLocalBodyStream: LocalValue, KPartitionStream: HistoryValue.BytesValue}
    )
    BytesValue = BuildSldprt(StreamsValue, FormatVersion=4)
    return ImportCandidate(
        SystemValue,
        FeatureValue,
        AtomId,
        HeadersValue,
        DefinitionValue,
        ConfigValue,
        ResolvedValue,
        StreamsValue,
        BytesValue,
    )
