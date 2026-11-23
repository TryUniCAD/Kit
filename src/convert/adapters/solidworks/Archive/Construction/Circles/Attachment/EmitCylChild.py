from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Construction.Circles.Attachment.MakeCylViewMut import (
    MakeCylViewMut,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeMgrHeader import (
    MakeMgrHeader,
)
from convert.adapters.solidworks.Archive.Construction.Part.Displays.Rendering.PartLookInput import (
    PartLookInput,
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
    *,
    LookValue: PartLookInput | None = None,
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
    ViewValue, VisualStreams = (
        (None, {}) if LookValue is None else MakeCylViewMut(ChildValue, LookValue)
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
    StreamsValue.update(VisualStreams)
    return ReplaceValue(
        ChildValue,
        ManagerHeader=ManagerHeader,
        StreamsValue=StreamsValue,
        ConfigValue=ConfigValue,
        ResolvedValue=ResolvedValue,
        BytesValue=BuildSldprt(StreamsValue, FormatVersion=4),
        SelfView=ViewValue,
    )
