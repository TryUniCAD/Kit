from convert.adapters.solidworks.Archive.Construction.Sweeps.SweepLabels import (
    KSweepBossName,
)
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import (
    KConfigStream,
    KeywordsStream,
    KPartitionStream,
    KResolvedFeaturesStream,
)
from convert.adapters.solidworks.Core.Native import ParseClasses, ParseKeywords
from convert.adapters.solidworks.Core.Reading.ConfigLanes import (
    ResolvedLanes,
    ResolvedStream,
    SelectLaneId,
)


# a cold standard sweep must be recognized in the selected physical lane even when its ghost is missing
def IsColdSweep(Archive: SldprtArchive, ConfigurationName: str | None) -> bool:
    StreamsValue = Archive.streams
    if (
        Archive.format_version != 4
        or KConfigStream not in StreamsValue
        or KResolvedFeaturesStream not in StreamsValue
        or KeywordsStream not in StreamsValue
        or KPartitionStream in StreamsValue
        or ContainerMo(StreamsValue) != 19000
    ):
        return False
    ConfigValues, FeaturesValue = ParseKeywords(StreamsValue[KeywordsStream])
    LanesValue = ResolvedLanes(StreamsValue)
    return (
        SelectLaneId(ConfigValues, LanesValue, ConfigurationName) == 0
        and ResolvedStream(StreamsValue, LanesValue[0]) == KResolvedFeaturesStream
        and any(
            Value.kind == "Sweep" and Value.name == KSweepBossName
            for Value in FeaturesValue
        )
        and (
            len(ConfigValues) == 1
            or any(
                Value.name == "moSweep_c"
                for Value in ParseClasses(StreamsValue[KResolvedFeaturesStream])
            )
        )
    )
