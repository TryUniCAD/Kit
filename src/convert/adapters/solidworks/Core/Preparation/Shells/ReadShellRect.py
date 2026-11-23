from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadRectSketch import (
    ReadRectSketch,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ReadStockRectangle import (
    ReadStockRect,
)
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Sketch import Sketch, SketchRelation
from interchange.geometry.Models.VectorPlane import PlaneVector


# a saved rectangle may reverse individual line directions while keeping the same corner incidence
def ShellLoopOrder(
    SketchValue: Sketch,
) -> tuple[Sketch, set[frozenset[tuple[str, str]]]]:
    if len(SketchValue.closed_profile_entity_ids) != 1:
        raise ValueError("shell stock needs one owned rectangle contour")
    (OrderValue,) = SketchValue.closed_profile_entity_ids
    EntityMap = {Value.id: Value for Value in SketchValue.entities}
    if (
        len(OrderValue) != 4
        or len(SketchValue.entities) != 4
        or len(EntityMap) != 4
        or set(OrderValue) != set(EntityMap)
    ):
        raise ValueError("shell stock contour must own exactly four actual lines")
    Edges: dict[str, tuple[tuple[str, PlaneVector], ...]] = {}
    for EntityId in OrderValue:
        Geometry = EntityMap[EntityId].geometry
        if type(Geometry) is not LineGeometry:
            raise ValueError("shell stock must retain four actual line segments")
        Edges[EntityId] = (("start", Geometry.start), ("end", Geometry.end))
    Corners: list[PlaneVector] = []
    Joins: set[frozenset[tuple[str, str]]] = set()
    for PrevId, NextId in zip(
        (OrderValue[-1], *OrderValue[:-1]), OrderValue, strict=True
    ):
        Matches = tuple(
            (PrevEnd, NextEnd, PointValue)
            for PrevEnd, PrevPoint in Edges[PrevId]
            for NextEnd, PointValue in Edges[NextId]
            if PrevPoint == PointValue
        )
        if len(Matches) != 1:
            raise ValueError("shell stock lines require one actual shared corner")
        PrevEnd, NextEnd, PointValue = Matches[0]
        Corners.append(PointValue)
        Joins.add(frozenset(((PrevId, PrevEnd), (NextId, NextEnd))))
    if len(set(Corners)) != 4:
        raise ValueError("shell stock requires four distinct rectangle corners")
    Entities = tuple(
        ReplaceValue(EntityMap[EntityId], geometry=LineGeometry(First, Second))
        for EntityId, First, Second in zip(
            OrderValue, Corners, (*Corners[1:], Corners[0]), strict=True
        )
    )
    return ReplaceValue(SketchValue, entities=Entities), Joins


# each coincidence must join the two actual incident endpoints of one distinct rectangle corner
def CheckShellJoins(
    Expected: set[frozenset[tuple[str, str]]],
    JoinsValue: tuple[SketchRelation, ...],
) -> None:
    Actual: set[frozenset[tuple[str, str]]] = set()
    for Relation in JoinsValue:
        if (
            len(Relation.references) != 2
            or Relation.parameter_id is not None
            or not Relation.driving
            or Relation.suppressed
            or Relation.provenance is not None
            or Relation.attributes
        ):
            raise ValueError("shell stock requires local driving corner coincidences")
        PairValue = frozenset(
            (Value.entity_id, Value.point) for Value in Relation.references
        )
        Actual.add(PairValue)
    if Actual != Expected or len(JoinsValue) != len(Actual):
        raise ValueError("shell stock coincidences must join all four contour corners")


# the constrained shell variant retains its axis intent and exact shared corner incidences
def ReadShellRect(
    SketchValue: Sketch, UnitScale: float
) -> tuple[tuple[float, float], ...]:
    if not SketchValue.constraints:
        return ReadRectSketch(SketchValue, UnitScale)
    AxisValues = tuple(
        Value
        for Value in SketchValue.constraints
        if Value.kind in ("horizontal", "vertical")
    )
    JoinsValue = tuple(
        Value for Value in SketchValue.constraints if Value.kind == "coincident"
    )
    if (len(AxisValues), len(JoinsValue), len(SketchValue.constraints)) != (4, 4, 8):
        raise ValueError("shell stock requires four axes and four corner coincidences")
    OrderedSketch, Expected = ShellLoopOrder(SketchValue)
    CheckShellJoins(Expected, JoinsValue)
    return ReadStockRect(ReplaceValue(OrderedSketch, constraints=AxisValues), UnitScale)
