from collections.abc import Mapping
from typing import Literal

from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.SourceFields import (
    RequireBox,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.SourceSchema import (
    KPlaneFrames,
)
from interchange.geometry.Models.SupportPlane import SupportPlane


# actual datum identity and basis distinguish the admitted xz plane from geometry alone
def ReadTopPlane(
    Planes: tuple[SupportPlane, ...], Objects: Mapping[str, Mapping[str, object]]
) -> SupportPlane:
    return ReadBoxPlane(Planes, Objects, "XZ-plane")


# both lowerings must use an actual owned datum with its native frame
def ReadBoxPlane(
    Planes: tuple[SupportPlane, ...],
    Objects: Mapping[str, Mapping[str, object]],
    PlaneName: Literal["XY-plane", "XZ-plane"],
) -> SupportPlane:
    RequireBox(
        {PlaneValue.name for PlaneValue in Planes} == set(KPlaneFrames)
        and len(Planes) == 3,
        "FreeCAD primitive does not carry the actual three origin datums",
    )
    for PlaneValue in Planes:
        OwnerName, OwnerIndex, Expected = KPlaneFrames[PlaneValue.name]
        Frame = PlaneValue.transform
        Actual = tuple(
            (Vector.x, Vector.y, Vector.z)
            for Vector in (Frame.x_axis, Frame.y_axis, Frame.z_axis)
        )
        RequireBox(
            Frame.origin.x == Frame.origin.y == Frame.origin.z == 0.0
            and Actual == Expected
            and PlaneValue.support_selection_id is None
            and PlaneValue.offset_parameter_id is None
            and PlaneValue.id == f"freecad:plane:{OwnerName}"
            and PlaneValue.attributes.get("freecad") == Objects[OwnerName]
            and PlaneValue.attributes.get("principal_role") == OwnerName
            and PlaneValue.attributes.get("principal_index") == OwnerIndex,
            "FreeCAD datum is no longer an ordinary owned origin plane",
        )
    return next(PlaneValue for PlaneValue in Planes if PlaneValue.name == PlaneName)
