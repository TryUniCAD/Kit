from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.Patterns.PatternDim import (
    PatternDim,
)
from convert.adapters.solidworks.Core.TypedResolved.Patterns.ReadPatDim import (
    ReadPatDim,
)
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)


# each active and dormant slot must retain its own mapped dimension and parameter
def ReadPatDrivers(
    LinkValue: NativeLink, PatternValue: ArchiveNode
) -> tuple[PatternDim, ...]:
    Drivers = tuple(
        ReadPatDim(PatternValue, SlotName, IsCount)
        for SlotName, IsCount in (
            ("f1258", True),
            ("f1260", False),
            ("f1268", True),
            ("f1270", False),
            ("f1318", False),
            ("f1320", False),
        )
    )
    Count, Pitch, *IdleValues = Drivers
    NodesValue = tuple(
        Member
        for Driver in Drivers
        for Member in (
            Driver.DisplayValue,
            Driver.HandleValue,
            Driver.DimensionValue,
            Driver.ParameterValue,
        )
    )
    CheckTreeAlias(LinkValue, NodesValue)
    if (
        len(set(NodesValue)) != len(NodesValue)
        or len({Driver.DimensionValue.FieldsValue["f50"] for Driver in Drivers})
        != len(Drivers)
        or tuple(Driver.NativeName for Driver in Drivers)
        != ("D1", "D3", "D2", "D4", "D5", "D6")
        or tuple(Driver.DisplayValue.FieldsValue.get("f58") for Driver in Drivers)
        != (11, 10, 0, 0, 0, 0)
        or not 2 <= Count.LiveValue <= 8
        or not 0 < Pitch.LiveValue
        or any(Driver.LiveValue != Driver.CacheValue for Driver in (Count, Pitch))
        or tuple((Driver.LiveValue, Driver.CacheValue) for Driver in IdleValues)
        != ((1, 0.0), (0.0, 0.0), (0.0, 0.0), (0.0, 0.0))
    ):
        raise ValueError(
            "pattern requires separate actual count and pitch and an inactive second direction"
        )
    return Drivers
