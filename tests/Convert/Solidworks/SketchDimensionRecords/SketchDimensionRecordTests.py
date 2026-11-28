# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from json import loads as LoadJson
from math import dist as Distance
from pathlib import Path as FilePath
from typing import NotRequired, TypedDict, cast as CastValue

from pytest import approx as Approx, mark as TestMark

from convert.api.ApiOpen import OpenDocument
from interchange.geometry.Models.GeometryCurves import CircleGeometry, LineGeometry
from interchange.geometry.Models.Sketch import SketchEntity, SketchRelation

# the saved edit cases establish the layout without the four withheld configurations
KDiscovery = (
    "edit-cut_depth_mm-5",
    "edit-cut_height_mm-10",
    "edit-cut_width_mm-12",
    "edit-depth_mm-12",
    "edit-height_mm-24",
    "edit-width_mm-44",
    "units-inch",
)

# repeated saves and layout shifts test the same bindings without teaching the reader offsets
KHoldout = ("baseline-a", "baseline-b", "plane-yz", "termination-through-all")


# point and circle observations carry different geometry for the same native identity
class MeasuredEntity(TypedDict):
    id: list[int]
    point_local_mm: NotRequired[list[float]]
    radius_mm: NotRequired[float]


# measurement operands stay in the order returned by the vendor
class MeasuredRule(TypedDict):
    type: int
    entities: list[MeasuredEntity]


# the test consumes only the solver fields of the reopened sketch
class MeasuredSketch(TypedDict):
    name: str
    fully_defined: bool
    entities: list[MeasuredEntity]
    relations: list[MeasuredRule]


# the reopened measurement must be from the exact native file being read
def ReadMeasurement(
    Family: str, CaseName: str, SketchName: str
) -> tuple[FilePath, MeasuredSketch]:
    RootPath = FilePath(__file__).resolve().parents[4]
    Capture = RootPath / "re" / "automation" / "PairedCaptures" / Family
    (Ledger,) = Capture.glob("solidworks-*/measurements.json")
    Source = Ledger.with_name(f"{Family}-solidworks-{CaseName}.SLDPRT")
    Measurements = LoadJson(Ledger.read_text(encoding="utf-8"))
    Reopened = Measurements["observations"]["reopened_files"][Source.name]
    Sketches = CastValue(list[MeasuredSketch], Reopened["sketches"])
    (SketchValue,) = (Record for Record in Sketches if Record["name"] == SketchName)
    assert SketchValue["fully_defined"]
    return Source, SketchValue


# native solver operand order must resolve to the same points on the neutral edges
def AssertEndpoints(
    RuleValue: SketchRelation,
    Entities: dict[str, SketchEntity],
    PointPair: list[MeasuredEntity],
) -> None:
    assert RuleValue.attributes["native_point_ids"] == tuple(
        tuple(Point["id"]) for Point in PointPair
    )
    assert len(RuleValue.references) == 2
    for Reference, Point in zip(RuleValue.references, PointPair, strict=True):
        Entity = Entities[Reference.entity_id]
        Shape = Entity.geometry
        assert isinstance(Shape, LineGeometry)
        assert Reference.point in ("start", "end")
        Endpoint = Shape.start if Reference.point == "start" else Shape.end
        assert "point_local_mm" in Point
        assert (Endpoint.x, Endpoint.y) == Approx(Point["point_local_mm"][:2])


# the record and nested scalar must be independently addressable in the same stream
def AssertDistSpan(RuleValue: SketchRelation) -> None:
    assert RuleValue.provenance is not None
    BodySpan, Scalar = RuleValue.provenance.spans
    assert BodySpan.stream == Scalar.stream == "Contents/Config-0"
    assert BodySpan.record_kind == "sketch-distance"
    assert Scalar.record_kind == "dimension-scalar"
    assert BodySpan.offset <= Scalar.offset
    assert Scalar.length == 8
    assert Scalar.offset + Scalar.length <= BodySpan.offset + BodySpan.length


# the rectangle archive must preserve the named scalar and both ordered solver endpoints
@TestMark.parametrize("CaseName", (*KDiscovery, *KHoldout))
def CheckRectDims(CaseName: str) -> None:
    Source, Measured = ReadMeasurement("P04", CaseName, "RectangleSketch")
    Document = OpenDocument(Source, IncludeBrep=False, IncludeTess=False)
    (SketchValue,) = (
        Record for Record in Document.sketches if Record.name == Measured["name"]
    )
    Entities = {Entity.id: Entity for Entity in SketchValue.entities}
    Parameters = {Parameter.id: Parameter for Parameter in Document.parameters}
    Rules = {
        Parameters[RuleValue.parameter_id].name: RuleValue
        for RuleValue in SketchValue.constraints
        if RuleValue.parameter_id is not None
    }
    assert set(Rules) == {"width_mm", "height_mm"}
    MeasuredPairs = [
        Record["entities"] for Record in Measured["relations"] if Record["type"] == 1
    ]
    assert len(MeasuredPairs) == 2
    for NameValue, PointPair in zip(
        ("width_mm", "height_mm"), MeasuredPairs, strict=True
    ):
        RuleValue = Rules[NameValue]
        assert (
            RuleValue.kind == "distance"
            and RuleValue.driving
            and not RuleValue.suppressed
        )
        assert RuleValue.attributes["native_code"] == 1
        assert RuleValue.parameter_id is not None
        Parameter = Parameters[RuleValue.parameter_id]
        assert Parameter.value.unit == "mm"
        First, Second = PointPair
        assert "point_local_mm" in First and "point_local_mm" in Second
        assert Parameter.value.value == Approx(
            Distance(First["point_local_mm"], Second["point_local_mm"])
        )
        AssertEndpoints(RuleValue, Entities, PointPair)
        AssertDistSpan(RuleValue)


# the circle archive must bind the diameter to the measured circle rather than the origin point
@TestMark.parametrize(
    "CaseName",
    ("baseline-a", "baseline-b", "edit-diameter_mm-16", "plane-yz", "units-inch"),
)
def CheckDiameter(CaseName: str) -> None:
    Source, Measured = ReadMeasurement("P02", CaseName, "CircleSketch")
    Document = OpenDocument(Source, IncludeBrep=False, IncludeTess=False)
    (SketchValue,) = (
        Record for Record in Document.sketches if Record.name == Measured["name"]
    )
    (RuleValue,) = (
        Record for Record in SketchValue.constraints if Record.kind == "diameter"
    )
    (Parameter,) = (
        Record for Record in Document.parameters if Record.id == RuleValue.parameter_id
    )
    (Reference,) = RuleValue.references
    (Circle,) = (
        Entity for Entity in SketchValue.entities if Entity.id == Reference.entity_id
    )
    (MeasuredCircle,) = Measured["entities"]
    (MeasuredDiameter,) = (
        Record for Record in Measured["relations"] if Record["type"] == 15
    )
    assert Reference.point == "" and isinstance(Circle.geometry, CircleGeometry)
    assert MeasuredDiameter["entities"][0]["id"] == MeasuredCircle["id"]
    assert Circle.attributes["native_segment_id"] == MeasuredCircle["id"][1]
    assert RuleValue.driving and not RuleValue.suppressed
    assert Parameter.name == "diameter_mm" and Parameter.value.unit == "mm"
    assert "radius_mm" in MeasuredCircle
    assert Parameter.value.value == Approx(2 * MeasuredCircle["radius_mm"])
    assert RuleValue.provenance is not None
    (BodySpan,) = RuleValue.provenance.spans
    assert (
        BodySpan.stream,
        BodySpan.offset,
        BodySpan.length,
        BodySpan.record_kind,
    ) == (
        "Contents/Config-0-ResolvedFeatures",
        6707,
        215,
        "sketch-diameter",
    )
