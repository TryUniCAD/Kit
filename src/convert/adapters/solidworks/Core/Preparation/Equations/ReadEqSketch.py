from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.Preparation.Readback.ReadColdSketch import (
    ReadColdSketch,
)
from interchange.Core.Common import FreezeMapping
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.geometry.Models.Sketch import Sketch


# detached origin provenance may be regenerated only while retaining the actual active relation and datum
def ReadEqSketch(SketchValue: Sketch) -> Sketch:
    Contour = tuple(
        Entity for Entity in SketchValue.entities if Entity.kind is GeometryKind.KLine
    )
    Datum = tuple(
        Entity for Entity in SketchValue.entities if Entity.kind is GeometryKind.KPoint
    )
    if len(Contour) != 4 or len(Datum) != 1 or len(SketchValue.entities) != 5:
        raise ValueError(
            "SOLIDWORKS cold equation needs its actual contour and origin datum"
        )
    Plain = ReadColdSketch(ReplaceValue(SketchValue, entities=Contour))
    return ReplaceValue(
        Plain,
        entities=(
            *Plain.entities,
            ReplaceValue(Datum[0], attributes=FreezeMapping(), provenance=None),
        ),
        constraints=tuple(
            ReplaceValue(Relation, attributes=FreezeMapping(), provenance=None)
            for Relation in SketchValue.constraints
        ),
    )
