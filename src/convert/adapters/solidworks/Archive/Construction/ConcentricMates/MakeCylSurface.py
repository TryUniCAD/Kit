from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Construction.ConcentricMates.CylFaceBuild import (
    CylFaceBuild,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# selected surfaces follow the actual originating feature and its first event
def MakeCylSurface(
    ClassName: str,
    FaceValue: CylFaceBuild,
    FileValue: ArchiveNode,
    ShapeValues: Mapping[str, int],
) -> ArchiveNode:
    FeatureValue = ArchiveNode(
        RuntimeClass("moFR_c", 1),
        {
            "f08": FileValue,
            "f10": {"f00": FaceValue.FeatureId, "f08": FaceValue.CreatedAt},
        },
    )
    return ArchiveNode(
        RuntimeClass(ClassName, 1),
        {"f10": {"f08": None, "f10": FeatureValue}, **ShapeValues},
    )
