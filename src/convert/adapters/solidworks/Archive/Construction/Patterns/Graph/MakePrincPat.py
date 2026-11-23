from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Datums.PutHingeViews import (
    PutHingeViews,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Direction.MakePatDir import (
    MakePatDir,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Direction.ReadPatDir import (
    ReadPatDir,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Drivers.PutPrincMut import (
    PutPrincMut,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Graph.FinishPatMut import (
    FinishPatMut,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Graph.MakePatBoxes import (
    MakePatBoxes,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Graph.MakePatFeature import (
    MakePatFeature,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Graph.PatPartGraph import (
    PatPartGraph,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Graph.PutPrincView import (
    PutPrincViewMut,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Input.PrincPatInput import (
    PrincPatInput,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.MakePatternSeed import (
    MakePatternSeed,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.MakeSeedHeaders import (
    MakeSeedHeaders,
)
from convert.adapters.solidworks.Core.Preparation.Patterns.CheckPatNames import (
    CheckPatNames,
)


# an existing system plane can drive the joined pattern without allocating a second datum or angle
def MakePrincPat(
    InputValue: PrincPatInput, *, PlatformMath: bool = False
) -> PatPartGraph:
    Reversed = InputValue.Reversed
    AxisValue = InputValue.AxisValue
    if type(CastValue(object, Reversed)) is not bool or (AxisValue, Reversed) not in (
        ("x", False),
        ("y", True),
    ):
        raise ValueError("principal pattern requires forward Right or reversed Top")
    StockInput = InputValue.StockValue
    CheckPatNames(StockInput, InputValue.NameValue)
    StockValue = MakePatternSeed(StockInput, PlatformMath=PlatformMath)
    SystemValue = StockValue.SystemValue
    Settings = StockValue.SettingsValue
    _ = PutHingeViews(SystemValue, StockValue.BoundsValue)
    PlaneValue = SystemValue.SystemValues.PlaneValues[AxisValue]
    AxisX, AxisY, AxisZ = ReadPatDir(PlaneValue).DirectionValue
    Direction = (-AxisX, -AxisY, -AxisZ) if Reversed else (AxisX, AxisY, AxisZ)
    _ = MakePatBoxes(
        StockInput.PlateValue.BoundsValue,
        StockInput.SeedValue.BoundsValue,
        Direction,
        InputValue.PitchValue,
        InputValue.CountValue,
    )
    PutPrincViewMut(SystemValue, Settings.TargetValue.FileVersion, NeedsLeft=Reversed)
    PatternValue = MakePatFeature(StockValue, InputValue.NameValue)
    Drivers = PutPrincMut(
        StockValue,
        PatternValue,
        PlaneValue,
        InputValue.StyleValues,
        InputValue.CountValue,
        InputValue.PitchValue,
        Reversed,
    )
    Headers = MakeSeedHeaders(StockValue)
    LineValue = MakePatDir(
        SystemValue, Settings, StockValue.Allocator, PlaneValue, Headers[:2]
    )
    FinishPatMut(StockValue, PatternValue, LineValue, Reversed)
    return PatPartGraph(
        StockValue,
        None,
        PlaneValue,
        None,
        PatternValue,
        Drivers,
        MakeSeedHeaders(StockValue, PatternValue),
    )
