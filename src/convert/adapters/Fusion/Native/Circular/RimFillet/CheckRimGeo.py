from math import isfinite as IsFinite

from convert.adapters.Fusion.Native.Circular.RimFillet.CheckRimCover import (
    CheckRimCover,
)
from convert.adapters.Fusion.Native.Circular.RimFillet.ReadRimCarriers import (
    ReadRimCarriers,
)
from convert.adapters.Fusion.Native.Circular.RimFillet.ReadRimFaces import ReadRimFaces
from convert.adapters.Fusion.Native.Circular.RimFillet.ReadRimEdges import ReadRimEdges
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)


# native geometry is qualified completely before physical labels can select feature operands
def CheckRimGeo(
    State: GeometryState, RadiusMm: float, HeightMm: float, FilletMm: float
) -> tuple[dict[str, int], dict[str, int]]:
    if (
        not all(IsFinite(Value) for Value in (RadiusMm, HeightMm, FilletMm))
        or min(RadiusMm, HeightMm) <= 0
        or not 0 <= FilletMm < min(RadiusMm, HeightMm)
    ):
        raise ValueError("Native rim dimensions exceed the qualified domain")
    RootIndex = CheckRimCover(State, FilletMm > 0)
    Surfaces, Circles = ReadRimCarriers(
        State, RadiusMm / 10, HeightMm / 10, FilletMm / 10
    )
    FaceRoles = ReadRimFaces(State, RootIndex, Surfaces, Circles, FilletMm > 0)
    if {
        Entity.Surface for Entity in State.Entities if isinstance(Entity, FaceNode)
    } != set(Surfaces):
        raise ValueError("Native rim faces omit saved surfaces")
    EdgeRoles = ReadRimEdges(State, Circles, FilletMm > 0)
    FaceRoles["body"] = RootIndex
    return FaceRoles, EdgeRoles
