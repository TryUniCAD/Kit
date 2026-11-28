from convert.adapters.solidworks.Archive.Construction.Ellipse.EllipsePlan import (
    EllipsePlan,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.MakeRingPoint import (
    MakeRingPoint,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode

# physical point ordinals differ from creation order at the centre and separate seam
KPointRoles = ("center", "seam", "major", "minor", "opposite_major", "opposite_minor")


# the seam and axes preserve separate point identities despite sharing the major position
def MakeEllipPoints(
    SketchValue: ArchiveNode, PlanValue: EllipsePlan
) -> dict[str, ArchiveNode]:
    CenterX, CenterY = PlanValue.CenterValue
    MajorX, MajorY = PlanValue.MajorValue
    MinorX, MinorY = PlanValue.MinorValue
    CreatedValues = (
        ("seam", PlanValue.MajorValue),
        ("center", PlanValue.CenterValue),
        ("major", PlanValue.MajorValue),
        ("minor", PlanValue.MinorValue),
        (
            "opposite_major",
            (CenterX - (MajorX - CenterX), CenterY - (MajorY - CenterY)),
        ),
        (
            "opposite_minor",
            (CenterX - (MinorX - CenterX), CenterY - (MinorY - CenterY)),
        ),
    )
    return {
        RoleName: MakeRingPoint(SketchValue, PositionValue, IndexValue)
        for IndexValue, (RoleName, PositionValue) in enumerate(CreatedValues)
    }
