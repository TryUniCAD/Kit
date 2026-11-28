from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    DatumOffset,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import (
    DimensionGraph,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.CrossVector import (
    CrossVector,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Direction.CheckPatRef import (
    CheckPatRef,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Direction.ReadPatDir import (
    ReadPatDir,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Drivers.PatDriveStyle import (
    PatDriveStyle,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Drivers.PrincDrive import (
    PrincDrive,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Drivers.PutPatDriveMut import (
    PutPatDriveMut,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Drivers.ReadSeedLow import (
    ReadSeedLow,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.SeedStockGraph import (
    SeedStockGraph,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# principal displays need separate annotation membership and pitch geometry from the same selected datum
def PutPrincMut(
    StockValue: SeedStockGraph,
    PatternValue: ArchiveNode,
    PlaneValue: ArchiveNode,
    Styles: tuple[PatDriveStyle, ...],
    CountValue: int,
    PitchValue: float,
    ReversedValue: bool,
) -> tuple[DimensionGraph, ...]:
    LineValue = ReadPatDir(PlaneValue)
    if type(CastValue(object, ReversedValue)) is not bool or (
        LineValue.RoleValue,
        ReversedValue,
    ) not in ((1, False), (2, True)):
        raise ValueError(
            "principal pattern pitch requires the measured signed Right or Top direction"
        )
    SystemValue = StockValue.SystemValue
    Allocator = StockValue.Allocator
    _ = CheckPatRef(SystemValue, Allocator, PlaneValue, LineValue.RoleValue)
    First, SketchNormal = ReadSeedLow(StockValue, PatternValue)
    AxisX, AxisY, AxisZ = LineValue.DirectionValue
    Travel = (-AxisX, -AxisY, -AxisZ) if ReversedValue else (AxisX, AxisY, AxisZ)
    Normal = CrossVector(Travel, SketchNormal)
    FrameValue = PlaneFrame(First, Travel, CrossVector(Normal, Travel), Normal)
    ViewName = "*Left" if ReversedValue else "*Top"
    return PutPatDriveMut(
        PatternValue,
        SystemValue.RootValue,
        Styles,
        CountValue,
        PitchValue,
        (First, DatumOffset(First, Travel, PitchValue)),
        Allocator,
        PrincipalValue=PrincDrive(FrameValue, SketchNormal, ViewName),
    )
