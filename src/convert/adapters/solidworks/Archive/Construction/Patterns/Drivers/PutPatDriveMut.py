from math import isfinite as IsFinite

from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    KDatumVector,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import (
    DimensionGraph,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.ReadModelLinear import (
    ReadModelLinear,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Drivers.MakePatDrive import (
    MakePatDrive,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Drivers.PatDriveStyle import (
    CheckPatStyles,
    KPatDriveSlots,
    PatDriveStyle,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    RequireNode,
)


# the two live displays consume model identities and all six dimensions consume persistent identities in native slot order
def PutPatDriveMut(
    OwnerValue: ArchiveNode,
    ModelValue: ArchiveNode,
    Styles: tuple[PatDriveStyle, ...],
    CountValue: int,
    PitchValue: float,
    Witnesses: tuple[KDatumVector, KDatumVector],
    Allocator: PersistentIds,
) -> tuple[DimensionGraph, ...]:
    CheckPatStyles(Styles)
    Fields = RequireNode(OwnerValue, "moLPattern_c").FieldsValue
    if (
        Fields.get("owner") is not ModelValue
        or any(SlotName in Fields for SlotName, _, _ in KPatDriveSlots)
        or type(CountValue) is not int
        or not 2 <= CountValue < (1 << 31)
        or not IsFinite(PitchValue)
        or PitchValue <= 0.0
    ):
        raise ValueError(
            "pattern requires fresh local driver slots and a positive modeled count and pitch"
        )
    DisplayId = FieldInt(ModelValue.FieldsValue, "fd44")
    if not 0 < DisplayId < 0x7FFFFFFE:
        raise ValueError("pattern requires two actual model display IDs")
    LinearValue = ReadModelLinear(ModelValue)
    DisplayIds = {"D3": DisplayId, "D1": DisplayId + 1}
    Values = (CountValue, PitchValue, 1, 0.0, 0.0, 0.0)
    Drivers = tuple(
        MakePatDrive(
            OwnerValue,
            ModelValue,
            StyleValue,
            DriveValue,
            DisplayIds.get(NameValue, 0),
            IsCount,
            Witnesses,
            LinearValue,
        )
        for StyleValue, DriveValue, (_, NameValue, IsCount) in zip(
            Styles, Values, KPatDriveSlots, strict=True
        )
    )
    for (SlotName, _, _), DriveGraph in zip(KPatDriveSlots, Drivers, strict=True):
        _ = Allocator.AllocateMut(DriveGraph.DimensionValue, "f50")
        Fields[SlotName] = DriveGraph.DisplayValue
    ModelValue.FieldsValue["fd44"] = DisplayId + len(DisplayIds)
    return Drivers
