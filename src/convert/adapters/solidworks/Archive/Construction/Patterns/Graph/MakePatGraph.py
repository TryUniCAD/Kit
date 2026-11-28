from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    DatumOffset,
)
from convert.adapters.solidworks.Archive.Construction.Datums.Angles.MakeAnglePlane import (
    MakeAnglePlane,
)
from convert.adapters.solidworks.Archive.Construction.Datums.MakeHingeMut import (
    MakeHingeMut,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Direction.MakePatDir import (
    MakePatDir,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Direction.ReadPatDir import (
    ReadPatDir,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Drivers.PutPatDriveMut import (
    PutPatDriveMut,
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
from convert.adapters.solidworks.Archive.Construction.Patterns.Input.LinPatternInput import (
    LinPatternInput,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.MakePatternSeed import (
    MakePatternSeed,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.MakeSeedHeaders import (
    MakeSeedHeaders,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.ReadStockBox import (
    ReadStockBox,
)
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.PutAnnoCatalog import (
    PutAnnoCatalog,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName


# the complete local part constructs the merged stock datums signed pattern and all live owners in native order
def MakePatGraph(InputValue: LinPatternInput) -> PatPartGraph:
    StockInput = InputValue.StockValue
    StockValue = MakePatternSeed(StockInput)
    Labels = (
        *map(ReadNodeName, StockValue.RootsValue),
        InputValue.HingeName,
        InputValue.AngleValue.NameValue,
        InputValue.NameValue,
    )
    if not all(
        type(NameValue) is str and NameValue and NameValue.isprintable()
        for NameValue in Labels
    ) or len(set(Labels)) != len(Labels):
        raise ValueError(
            "pattern feature, hinge and plane labels must be distinct actual native names"
        )
    if type(CastValue(object, InputValue.Reversed)) is not bool:
        raise ValueError(
            "pattern requires explicit raised seed, angle constraint and signed repetition intent"
        )
    SystemValue = StockValue.SystemValue
    Settings = StockValue.SettingsValue
    Allocator = StockValue.Allocator
    AxisValue, Initial = MakeHingeMut(
        SystemValue,
        Settings,
        Allocator,
        InputValue.HingeName,
        StockValue.BoundsValue,
    )
    _ = PutAnnoCatalog(
        SystemValue.RootValue,
        Settings.TargetValue.FileVersion,
        InputValue.AnnoValues,
        InputValue.ActiveAnno,
        InputValue.ShownAnnos,
    )
    PlaneValue, AngleValue, PlaneHeaders = MakeAnglePlane(
        SystemValue,
        Settings,
        Allocator,
        AxisValue,
        Initial,
        InputValue.AngleValue,
    )
    Direction = ReadPatDir(PlaneValue).DirectionValue
    if InputValue.Reversed:
        Direction = (-Direction[0], -Direction[1], -Direction[2])
    _ = MakePatBoxes(
        StockInput.PlateValue.BoundsValue,
        StockInput.SeedValue.BoundsValue,
        Direction,
        InputValue.PitchValue,
        InputValue.CountValue,
    )
    Start = ReadStockBox(StockInput.SeedValue.BoundsValue)[0]
    Witnesses = Start, DatumOffset(Start, Direction, InputValue.PitchValue)
    PatternValue = MakePatFeature(StockValue, InputValue.NameValue)
    DriverValues = PutPatDriveMut(
        PatternValue,
        SystemValue.RootValue,
        InputValue.StyleValues,
        InputValue.CountValue,
        InputValue.PitchValue,
        Witnesses,
        Allocator,
    )
    LineValue = MakePatDir(
        SystemValue,
        Settings,
        Allocator,
        PlaneValue,
        (PlaneHeaders[0], PlaneHeaders[1]),
    )
    FinishPatMut(StockValue, PatternValue, LineValue, InputValue.Reversed)
    return PatPartGraph(
        StockValue,
        AxisValue,
        PlaneValue,
        AngleValue,
        PatternValue,
        DriverValues,
        MakeSeedHeaders(StockValue, AxisValue, PlaneValue, PatternValue),
    )
