from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Construction.Metadata.MakeMgrHeader import (
    MakeMgrHeader,
)
from convert.adapters.solidworks.Archive.Construction.Part.EmitPartArchive import (
    EmitPartArchive,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Container.Container import BuildSldprt
from convert.adapters.solidworks.Container.Format import (
    KPartitionStream,
    KeywordsStream,
)


# final emission binds the original feature objects through the updated configuration map and active partition
def EmitCylChild(
    ChildValue: PartCandidate,
    RecipeValue: PartBuildInput,
    PartitionValue: bytes,
) -> PartCandidate:
    SystemValue = ChildValue.SystemValue
    ManagerHeader = MakeMgrHeader(
        SystemValue.ManagerValue, RecipeValue.OutputValue.SavedAt
    )
    FeatureValues = (
        *SystemValue.FeatureValues,
        ChildValue.ProfileValue.ProfileValue,
        ChildValue.BossValue.FeatureValue,
    )
    if FeatureValues != ChildValue.ResolvedValue.RootsValue:
        raise ValueError(
            "concentric output requires the original ordered feature owners"
        )
    StreamsValue, ConfigValue, ResolvedValue = EmitPartArchive(
        SystemValue,
        FeatureValues,
        (ChildValue.HeaderValue, ChildValue.TopHeader, ManagerHeader),
        ChildValue.DefinitionValue,
        RecipeValue,
        ChildValue.StreamsValue[KeywordsStream],
    )
    StreamsValue[KPartitionStream] = PartitionValue
    return ReplaceValue(
        ChildValue,
        ManagerHeader=ManagerHeader,
        StreamsValue=StreamsValue,
        ConfigValue=ConfigValue,
        ResolvedValue=ResolvedValue,
        BytesValue=BuildSldprt(StreamsValue, FormatVersion=4),
    )
