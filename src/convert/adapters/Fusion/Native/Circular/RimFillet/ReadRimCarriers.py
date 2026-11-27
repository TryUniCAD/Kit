from convert.adapters.Fusion.Native.Circular.RimFillet.CheckRimCone import CheckRimCone
from convert.adapters.Fusion.Native.Circular.RimFillet.CheckRimTorus import (
    CheckRimTorus,
)
from convert.adapters.Fusion.Native.Circular.RimFillet.ReadRimPlane import ReadRimPlane
from convert.adapters.Fusion.Native.Circular.RimFillet.ReadRimCircle import (
    ReadRimCircle,
)
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.ConeNode import ConeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EllipseNode import EllipseNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.PointNode import PointNode
from convert.Formats.Fusion.BrepCodec.Journal.Round.TorusNode import TorusNode
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)


# physical carrier roles are derived from exact dimensions before any native tag is trusted
def ReadRimCarriers(
    State: GeometryState, Radius: float, Height: float, Fillet: float
) -> tuple[dict[int, str], dict[int, str]]:
    Surfaces: dict[int, str] = {}
    Circles: dict[int, str] = {}
    for Index, Entity in enumerate(State.Entities):
        if isinstance(
            Entity, (ConeNode, PlaneNode, EllipseNode, TorusNode, PointNode)
        ) and (Entity.Prefix.Attribute != -1 or Entity.Prefix.EntityTag != -1):
            raise ValueError("Native rim carrier has unqualified metadata")
        if isinstance(Entity, ConeNode):
            CheckRimCone(Entity, Radius)
            Surfaces[Index] = "side"
        elif isinstance(Entity, TorusNode):
            CheckRimTorus(Entity, Radius, Height, Fillet)
            Surfaces[Index] = "blend"
        elif isinstance(Entity, PlaneNode):
            Surfaces[Index] = ReadRimPlane(Entity, Height)
        elif isinstance(Entity, EllipseNode):
            Circles[Index] = ReadRimCircle(Entity, Radius, Height, Fillet)
    return Surfaces, Circles
