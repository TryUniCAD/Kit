from hashlib import sha256 as CalcSha

from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Archive.Construction.Sweeps.SweepLabels import (
    KSweepBossName,
)
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import (
    SldprtArchive,
    SldprtFormatError,
)
from convert.adapters.solidworks.Container.Format import (
    KConfigStream,
    KeywordsStream,
    KPartitionStream,
    KPartFormatId,
    KResolvedFeaturesStream,
)
from convert.adapters.solidworks.Core.ConfigLanes import (
    ResolvedLanes,
    ResolvedStream,
    SelectLaneId,
)
from convert.adapters.solidworks.Core.Native import ParseClasses, ParseKeywords
from convert.adapters.solidworks.Core.Preparation.Sweeps.BuildSweepPart import (
    BuildSweepPart,
)
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.MakeSwDoc import MakeSwDoc
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.ReadSwState import (
    ReadSwState,
    SwReadState,
)
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.Saved.ReadSavedSw import (
    ReadSavedSw,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Records.RecordSource import CadSource


# saved sweep dispatch follows the selected physical lane while cold projection needs one complete configuration
def IsScopedSweep(Archive: SldprtArchive, ConfigurationName: str | None) -> bool:
    if (
        Archive.format_version != 4
        or KConfigStream not in Archive.streams
        or KResolvedFeaturesStream not in Archive.streams
        or KeywordsStream not in Archive.streams
        or ContainerMo(Archive.streams) != 19000
    ):
        return False
    ConfigValues, FeaturesValue = ParseKeywords(Archive.require(KeywordsStream))
    if not any(
        FeatureValue.kind == "Sweep" and FeatureValue.name == KSweepBossName
        for FeatureValue in FeaturesValue
    ):
        return False
    if KPartitionStream not in Archive.streams:
        return len(ConfigValues) == 1 and ConfigValues[0].configuration_id == 0
    Lanes = ResolvedLanes(Archive.streams)
    Selected = SelectLaneId(ConfigValues, Lanes, ConfigurationName)
    if (
        Selected is None
        or Selected not in Lanes
        or ResolvedStream(Archive.streams, Lanes[Selected]) != KResolvedFeaturesStream
        or not any(Value.configuration_id == Selected for Value in ConfigValues)
    ):
        return False
    return len(ConfigValues) == 1 or any(
        ClassValue.name == "moSweep_c"
        for ClassValue in ParseClasses(Archive.require(KResolvedFeaturesStream))
    )


# source identity binds the entire canonical output while its typed owner retains the logical native self locator
def SwSource(StateValue: SwReadState, DataValue: bytes, Label: str) -> CadSource:
    FileValue = StateValue.IntentValue.OutputValue
    return CadSource(
        KPartFormatId,
        Label,
        CalcSha(DataValue).hexdigest(),
        container_version="4",
        attributes={
            "native_locator": FileValue.PathName,
            "written_at": FileValue.SavedAt,
        },
    )


# a strict read may project only the canonical scope that the shared constructor accounts for completely
def ReadSwPart(
    Archive: SldprtArchive, DataValue: bytes, Label: str, SettingsValue: ReadOptions
) -> CadDocument:
    if KPartitionStream in Archive.streams:
        try:
            DocValue = ReadSavedSw(Archive, DataValue, Label, SettingsValue)
            DocValue.assert_valid()
            return DocValue
        except (IndexError, KeyError, TypeError, ValueError, SyntaxError) as ErrorValue:
            raise SldprtFormatError(
                f"unsupported SOLIDWORKS saved sweep result partition: {ErrorValue}"
            ) from ErrorValue
    try:
        StateValue = ReadSwState(Archive)
        if BuildSweepPart(StateValue.IntentValue).BytesValue != DataValue:
            raise ValueError(
                "canonical sweep reconstruction differs from its complete archive"
            )
        DocValue = MakeSwDoc(
            StateValue,
            SwSource(StateValue, DataValue, Label),
            SettingsValue.include_brep,
        )
        ConfigValue = DocValue.configurations[0]
        if SettingsValue.configuration not in (None, ConfigValue.id, ConfigValue.name):
            raise ValueError("requested sweep read configuration is unavailable")
        DocValue.assert_valid()
        return DocValue
    except (IndexError, KeyError, TypeError, ValueError, SyntaxError) as ErrorValue:
        raise SldprtFormatError(
            f"unsupported SOLIDWORKS cold sweep: {ErrorValue}"
        ) from ErrorValue
