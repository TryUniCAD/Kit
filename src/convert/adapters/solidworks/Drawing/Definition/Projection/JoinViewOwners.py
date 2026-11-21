from dataclasses import replace as ReplaceValue
from math import isclose as IsClose
from types import MappingProxyType

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Drawing.Definition.Projection.JoinGeometry import (
    JoinGeometry,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptMap,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedDrawNumber,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ReadConceptName import (
    ReadConceptName,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ReadViewMatrix import (
    ReadViewMatrix,
)
from interchange.document.Models.Drawing.DrawingView import DrawingView

# native named views retain their selector and matrix relationship
KViewDirections = MappingProxyType(
    {"*Front": 0, "*Right": 1, "*Top": 2, "*Isometric": 7}
)


# absolute view properties come from the same native owner as the ordered view
def JoinViewOwners(ViewNode: ArchiveNode, ViewValue: DrawingView) -> DrawingView:
    Fields = ViewNode.FieldsValue
    Orientation = Fields.get("f1018")
    if (
        ReadConceptName(ViewNode) != ViewValue.EntityName
        or not isinstance(Orientation, str)
        or Orientation not in KViewDirections
    ):
        raise ValueError("unsupported SOLIDWORKS drawing view name or orientation")
    if Orientation != "*Front" and Fields.get("f1010") != KViewDirections[Orientation]:
        raise ValueError("SOLIDWORKS drawing view direction differs from its name")
    Ratio = (
        NeedDrawNumber(Fields.get("f780")),
        NeedDrawNumber(Fields.get("f788")),
    )
    Transform = NeedConceptMap(Fields.get("f5e0"))
    if Transform.get("has_matrix") != int(Orientation != "*Front"):
        raise ValueError("SOLIDWORKS drawing orientation differs from its transform")
    Scale = NeedDrawNumber(Transform.get("f70"))
    if min(Ratio) <= 0 or not IsClose(Ratio[0] / Ratio[1], Scale, rel_tol=1e-9):
        raise ValueError("SOLIDWORKS drawing view scale differs from its transform")
    return ReplaceValue(
        JoinGeometry(ViewNode, ViewValue),
        OrientationName=Orientation,
        ScaleRatio=Ratio,
        ModelToSheet=ReadViewMatrix(Transform, Scale),
    )
