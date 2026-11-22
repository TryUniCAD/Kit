from convert.adapters.solidworks.Archive.Construction.Sketch.MakeRingPoint import (
    MakeRingPoint,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# the referenced origin is a separate external point row rather than an additional contour vertex
def MakeExtPoint(
    SketchValue: ArchiveNode, ExternalEntity: ArchiveNode, IndexValue: int
) -> ArchiveNode:
    PointValue = MakeRingPoint(SketchValue, (0.0, 0.0), IndexValue)
    PointValue.FieldsValue.update(
        {
            "ext": ExternalEntity,
            "fe4": 6,
            "f54": FieldInt(PointValue.FieldsValue, "f54") & 0xFFFC,
        }
    )
    return PointValue
