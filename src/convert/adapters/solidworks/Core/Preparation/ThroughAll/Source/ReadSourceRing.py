from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceInputs.SourceLine import (
    SourceLine,
)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.ReadSourceLine import (
    ReadSourceLine,
)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.MapSourceLines import (
    MapSourceLines,
)
from interchange.geometry.Models.Sketch import Sketch


# native source entity order must not be mistaken for a directed rectangle contour or a disposable history detail
def ReadSourceRing(
    SketchValue: Sketch, UnitScale: float
) -> tuple[tuple[tuple[float, float], ...], tuple[SourceLine, ...]]:
    if (
        SketchValue.suppressed
        or SketchValue.parameter_ids
        or len(SketchValue.entities) != 4
        or len(SketchValue.closed_profile_entity_ids) != 1
    ):
        raise ValueError("source stock has extra geometry dimensions or profiles")
    RingValue = SketchValue.closed_profile_entity_ids[0]
    if len(RingValue) != 4 or set(RingValue) != {
        Value.id for Value in SketchValue.entities
    }:
        raise ValueError("source profile does not own every actual line once")
    Points = {
        Point
        for Value in SketchValue.entities
        for Point in ReadSourceLine(Value, UnitScale)
    }
    XValues, YValues = sorted({Value[0] for Value in Points}), sorted(
        {Value[1] for Value in Points}
    )
    if (
        len(XValues) != 2
        or len(YValues) != 2
        or Points != {(XValue, YValue) for XValue in XValues for YValue in YValues}
    ):
        raise ValueError("source stock is not an axis aligned four corner rectangle")
    LowerX, UpperX = XValues
    LowerY, UpperY = YValues
    Vertices = ((LowerX, LowerY), (UpperX, LowerY), (UpperX, UpperY), (LowerX, UpperY))
    return Vertices, MapSourceLines(SketchValue, Vertices, UnitScale)
