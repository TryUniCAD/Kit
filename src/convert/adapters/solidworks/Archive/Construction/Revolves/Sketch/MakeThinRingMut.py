from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.RevolvePlan import (
    RevolvePlan,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.MakeLineHandle import (
    MakeLineHandle,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.MakeRingLine import (
    MakeRingLine,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.MakeRingPoint import (
    MakeRingPoint,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.MakeSketchSeed import (
    MakeSketchSeed,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.PolygonGraph import (
    PolygonGraph,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# the body line and construction axis each own two independent endpoint records
def BindThinRingMut(
    SketchValue: ArchiveNode,
    PointValues: tuple[ArchiveNode, ...],
    LineValues: tuple[ArchiveNode, ...],
) -> None:
    for IndexValue, (LineValue, MaskValue) in enumerate(
        zip(LineValues, (0x40, 8), strict=True)
    ):
        LineValue.FieldsValue.update(
            f08=len(LineValues) - IndexValue,
            f0c=IndexValue + 1,
            f54=FieldInt(LineValue.FieldsValue, "f54") | MaskValue,
            fd0=int(IndexValue == 0),
        )
        for PointValue in PointValues[2 * IndexValue : 2 * IndexValue + 2]:
            PointValue.FieldsValue.update(
                h1=MakeLineHandle(SketchValue, LineValue, IndexValue), fe8=1
            )


# the open profile transports actual incidence through the shared planar sketch owner
def MakeThinRingMut(ProfileValue: ArchiveNode, PlanValue: RevolvePlan) -> PolygonGraph:
    SketchValue = MakeSketchSeed(ProfileValue)
    Coordinates = (*PlanValue.VerticesValue, PlanValue.AxisStart, PlanValue.AxisEnd)
    PointValues = tuple(
        MakeRingPoint(SketchValue, Position, IndexValue)
        for IndexValue, Position in enumerate(Coordinates)
    )
    BodyValue = MakeRingLine(SketchValue, PointValues, 0)
    AxisValue = MakeRingLine(SketchValue, PointValues, 2)
    LineValues = (BodyValue, AxisValue)
    BindThinRingMut(SketchValue, PointValues, LineValues)
    FieldsValue = SketchValue.FieldsValue
    FieldsValue.update(
        points=tuple(
            {"kind": 0, "point": PointValue.FieldsValue} for PointValue in PointValues
        ),
        lines=(
            {"flags": 0, "line": BodyValue.FieldsValue},
            {"flags": 2, "line": AxisValue.FieldsValue},
        ),
        npoints=len(PointValues),
        nlines=len(LineValues),
        f130=len(LineValues) + 1,
        f56c=len(LineValues) + 1,
    )
    CreationValue = CastValue(dict[str, int], FieldsValue["f140"])
    CreationValue.update(f08=len(PointValues) + 1, f0c=len(LineValues) + 1)
    return PolygonGraph(SketchValue, PointValues, LineValues)
