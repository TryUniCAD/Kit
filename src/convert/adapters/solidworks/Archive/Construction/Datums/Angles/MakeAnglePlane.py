from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Datums.Angles.AngleHeaders import (
    AngleHeaders,
    AngleSlots,
)
from convert.adapters.solidworks.Archive.Construction.Datums.Angles.AnglePlaneInput import (
    AnglePlaneInput,
)
from convert.adapters.solidworks.Archive.Construction.Datums.Angles.CheckAngleHinge import (
    CheckAngleHinge,
)
from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    DatumPoint,
    KHingeRoot,
)
from convert.adapters.solidworks.Archive.Construction.Datums.Angles.MakeAngleData import (
    MakeAngleData,
)
from convert.adapters.solidworks.Archive.Construction.Datums.Angles.MakeAngleDrive import (
    MakeAngleDrive,
)
from convert.adapters.solidworks.Archive.Construction.Datums.Angles.MakeAngleGeom import (
    MakeAngleGeom,
)
from convert.adapters.solidworks.Archive.Construction.Datums.Angles.MakeAngleLine import (
    MakeAngleLine,
)
from convert.adapters.solidworks.Archive.Construction.Datums.Angles.ReadAngleAnno import (
    ReadAngleAnno,
)
from convert.adapters.solidworks.Archive.Construction.Datums.MakeHingePick import (
    MakeHingePick,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import (
    DimensionGraph,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.AtomSeeds import (
    KAtomLists,
    KAtomWords,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.MakeModelFeat import (
    MakeModelFeat,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName


# a fresh angular feature keeps its own exact name and supported presentation without reading any saved display
def CheckAngleInput(
    SystemValue: PartSystem,
    Settings: PartBuildInput,
    HingeValue: ArchiveNode,
    InputValue: AnglePlaneInput,
) -> None:
    NameValue = InputValue.NameValue
    if (
        type(NameValue) is not str
        or not NameValue
        or "\x00" in NameValue
        or any(
            ReadNodeName(Value) == NameValue
            for Value in (*SystemValue.FeatureValues, HingeValue)
        )
    ):
        raise ValueError(
            "angular datum requires its own authored feature name and intent"
        )
    if (
        type(CastValue(object, InputValue.DesignIntent)) is not bool
        or type(InputValue.SelectedLeader) is not int
        or not -(1 << 31) <= InputValue.SelectedLeader < (1 << 31)
        or InputValue.ShiftValue != KHingeRoot
        or any(type(Value) is not float for Value in InputValue.ShiftValue)
    ):
        raise ValueError(
            "ordinary angular datum needs an explicit signed leader and zero shifted point"
        )
    if Settings.TargetValue.FileVersion != 19000:
        raise ValueError("angular datum requires an ordinary 2026 archive")


# the local angle plane builds its actual constraints display and persistent ids through the shared part graph
def MakeAnglePlane(
    SystemValue: PartSystem,
    Settings: PartBuildInput,
    Allocator: PersistentIds,
    HingeValue: ArchiveNode,
    Headers: tuple[ArchiveNode, ...],
    InputValue: AnglePlaneInput,
) -> tuple[ArchiveNode, DimensionGraph, tuple[ArchiveNode, ArchiveNode, ArchiveNode]]:
    CheckAngleInput(SystemValue, Settings, HingeValue, InputValue)
    EndValues, RightValue = CheckAngleHinge(
        SystemValue, Settings, Allocator, HingeValue, Headers
    )
    if InputValue.Reversed is not False:
        raise ValueError(
            "the analytic pattern datum covers an acute unreversed Right plane constraint"
        )
    Geometry = MakeAngleGeom(*EndValues, InputValue.AngleValue)
    ViewId = ReadAngleAnno(
        SystemValue.RootValue, InputValue.AnnotationName, Geometry.DimensionValue
    )
    DimId, PlaneId, Frontier = AngleSlots(Allocator)
    AxisPick = MakeAngleLine(
        SystemValue, HingeValue, Headers[0], EndValues, Settings.HeaderValue.CreatedAt
    )
    RightPick = MakeHingePick(SystemValue, RightValue, "x", Headers)
    PlaneValue = MakeModelFeat(
        "moRefPlane_c",
        InputValue.NameValue,
        SystemValue.RootValue,
        Settings.TargetValue,
    )
    Fields = PlaneValue.FieldsValue
    Fields.update(dict.fromkeys(KAtomWords, 0))
    Fields.update({NameValue: [] for NameValue in KAtomLists})
    Fields.update(
        f368={"n": 0, "items": []},
        f388={"n": 0, "items": []},
        f538=None,
        f4a0=1,
        f6c0=DatumPoint(Geometry.NameCorner),
        f6dc=4,
        f6e0=0,
        f6e8=None,
        f6f0=0,
    )
    DataValue = MakeAngleData(
        PlaneValue, RightPick, AxisPick, Geometry, InputValue.AngleValue
    )
    Fields["f6f8"] = DataValue
    GraphValue = MakeAngleDrive(PlaneValue, InputValue, Geometry, ViewId)
    DataValue.FieldsValue["f150"] = GraphValue.DisplayValue
    if (
        Allocator.AllocateMut(GraphValue.DimensionValue, "f50") != DimId
        or Allocator.AllocateMut(PlaneValue) != PlaneId
        or Allocator.NextValue != Frontier
    ):
        raise ValueError(
            "actual angular dimension and plane allocations departed from their order"
        )
    return (
        PlaneValue,
        GraphValue,
        AngleHeaders(SystemValue, Settings, Allocator, HingeValue, PlaneValue),
    )
