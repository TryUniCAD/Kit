from collections import Counter

from convert.adapters.solidworks.Archive.Construction.Ellipse.MakeEllipPoints import (
    KPointRoles,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# the mapped ellipse handle belongs to its two use endpoint while axis points retain their own uses
def BindEllipPtsMut(
    SketchValue: ArchiveNode,
    SegmentValue: ArchiveNode,
    PointValues: dict[str, ArchiveNode],
) -> None:
    HandleValue = ArchiveNode(
        RuntimeClass("sgEllipseHandle", 1),
        {
            "_sketch": SketchValue,
            "_ellipse": SegmentValue,
            "idx": 0,
            "f1c": -1,
            "f08": 0,
        },
    )
    UsesValue: Counter[str] = Counter(("seam", "seam", "center", *KPointRoles[2:]))
    KindsValue = {"center": 0, "seam": 2}
    for RoleName, PointValue in PointValues.items():
        PointValue.FieldsValue.update(
            fe4=KindsValue.get(RoleName, 3),
            fe8=UsesValue[RoleName],
            fec=int(RoleName == "center"),
            h1=HandleValue if RoleName == "seam" else None,
        )
