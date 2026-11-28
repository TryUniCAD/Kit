from dataclasses import replace as ReplaceValue
from math import isclose as IsClose

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptMap,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedDrawNumber,
)
from interchange.document.Models.Drawing.DrawingView import DrawingView
from interchange.geometry.Models.VectorPlane import PlaneVector


# view position has an independent definition owner while the header corroborates its outline
def JoinGeometry(NodeValue: ArchiveNode, ViewValue: DrawingView) -> DrawingView:
    Point = NeedConceptMap(NodeValue.FieldsValue.get("f778"))
    Position = PlaneVector(
        NeedDrawNumber(Point.get("x")), NeedDrawNumber(Point.get("y"))
    )
    Fields = NodeValue.FieldsValue
    Outline = (
        NeedDrawNumber(Fields.get("f6d8")),
        NeedDrawNumber(Fields.get("f6e0")),
        NeedDrawNumber(Fields.get("f6e8")),
        NeedDrawNumber(Fields.get("f6f0")),
    )
    if (
        Point.get("z") != 0
        or ViewValue.OutlineValues is None
        or not all(
            IsClose(Actual, Expected, rel_tol=1e-9, abs_tol=1e-12)
            for Actual, Expected in zip(
                Outline,
                ViewValue.OutlineValues,
                strict=True,
            )
        )
    ):
        raise ValueError(
            "drawing Definition has a nonplanar position or mismatched outline"
        )
    return ReplaceValue(ViewValue, PositionValue=Position, OutlineValues=Outline)
