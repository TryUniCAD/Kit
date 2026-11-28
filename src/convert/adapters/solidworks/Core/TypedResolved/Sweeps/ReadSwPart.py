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
    KResolvedFeaturesStream,
)
from convert.adapters.solidworks.Core.Reading.ConfigLanes import (
    ResolvedLanes,
    ResolvedStream,
    SelectLaneId,
)
from convert.adapters.solidworks.Core.Native import ParseClasses, ParseKeywords
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.Saved.ReadSavedSw import (
    ReadSavedSw,
)
from interchange.document.Models.DocumentModel import CadDocument


# physical saved sweep dispatch honors the selected native configuration lane
def IsSavedSweep(Archive: SldprtArchive, ConfigurationName: str | None) -> bool:
    if (
        Archive.format_version != 4
        or KConfigStream not in Archive.streams
        or KResolvedFeaturesStream not in Archive.streams
        or KeywordsStream not in Archive.streams
        or KPartitionStream not in Archive.streams
        or ContainerMo(Archive.streams) != 19000
    ):
        return False
    ConfigValues, FeaturesValue = ParseKeywords(Archive.require(KeywordsStream))
    if not any(
        Value.kind == "Sweep" and Value.name == KSweepBossName
        for Value in FeaturesValue
    ):
        return False
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
        Value.name == "moSweep_c"
        for Value in ParseClasses(Archive.require(KResolvedFeaturesStream))
    )


# a qualified saved sweep requires the retained history and physical result to agree
def ReadSwPart(
    Archive: SldprtArchive, DataValue: bytes, Label: str, SettingsValue: ReadOptions
) -> CadDocument:
    try:
        DocValue = ReadSavedSw(Archive, DataValue, Label, SettingsValue)
        DocValue.assert_valid()
        return DocValue
    except (IndexError, KeyError, TypeError, ValueError, SyntaxError) as ErrorValue:
        raise SldprtFormatError(
            f"unsupported SOLIDWORKS saved sweep result partition: {ErrorValue}"
        ) from ErrorValue
