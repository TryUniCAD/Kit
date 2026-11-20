from convert.adapters.solidworks.Archive.Construction.Chronology.FeatureInstant import (
    FeatureInstant,
)
from convert.adapters.solidworks.Archive.Construction.Chronology.MakeFeatTime import (
    MakeFeatTime,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    RequireRecord,
)

# completed imports clear only the pending feature and model status bits
KCompleteFlags = 0xFFFD7FF8

# the active part needs its force rebuild and callback dispatch flags together
KModelUpdateFlags = 0x20 | 0x8000


# the completed origin and imported feature share the same modeled update clock
def StampImportMut(
    OwnerValue: ArchiveNode,
    InputValue: PartBuildInput,
    ClockValue: dict[str, int],
    StampValue: int,
) -> None:
    FieldsValue = OwnerValue.FieldsValue
    FieldsValue.update(
        ClockValue,
        f29c=StampValue,
        f2b8=InputValue.TargetValue.FileVersion,
        f2bc=InputValue.TargetValue.DateCode,
        f0c=FieldInt(FieldsValue, "f0c") & KCompleteFlags,
    )


# the fresh local body must publish its completed model and configuration state before serialization
def FinishImportMut(
    SystemValue: PartSystem,
    FeatureValue: ArchiveNode,
    HeadersValue: tuple[ArchiveNode, ArchiveNode, ArchiveNode],
    InputValue: PartBuildInput,
) -> None:
    ActiveHeader, TopHeader, _ = HeadersValue
    StampValue = FieldInt(ActiveHeader.FieldsValue, "f40")
    (ConfigValue,) = SystemValue.ConfigValues
    ModelFields = SystemValue.RootValue.FieldsValue
    AtomCount = FieldInt(RequireRecord(ModelFields.get("fd88")), "n6c")
    if (
        StampValue != FieldInt(TopHeader.FieldsValue, "f40")
        or not 0 <= StampValue <= (1 << 31) - 3
        or FeatureValue.ClassValue.NameValue != "moBaseBody_c"
        or FeatureValue.FieldsValue.get("owner") is not SystemValue.RootValue
        or ConfigValue.FieldsValue.get("f6f8", 0) != 0
        or AtomCount != 1
    ):
        raise ValueError("completed local import requires a fresh bound part")
    ClockValue = MakeFeatTime(FeatureInstant(InputValue.HeaderValue.UpdatedAt, 0))
    OriginValue = SystemValue.OriginValue.ProfileValue
    StampImportMut(OriginValue, InputValue, ClockValue, StampValue + 1)
    StampImportMut(FeatureValue, InputValue, ClockValue, StampValue + 2)
    ModelFields["f0c"] = FieldInt(ModelFields, "f0c") & KCompleteFlags
    ModelFields["f2c"] = FieldInt(ModelFields, "f2c") | KModelUpdateFlags
    ConfigValue.FieldsValue.update(f860=StampValue + 2, f6f8=AtomCount)
    ActiveHeader.FieldsValue["f40"] = TopHeader.FieldsValue["f40"] = StampValue + 2
