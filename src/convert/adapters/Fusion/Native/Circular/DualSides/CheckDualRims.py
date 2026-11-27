from convert.adapters.Fusion.Native.Circular.CircleShape import CircleShape
from convert.adapters.Fusion.Native.Circular.DualSides.ReadDualLabel import (
    ReadDualLabel,
)
from convert.adapters.Fusion.Native.Circular.Spans.CheckSpanRim import CheckSpanRim
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Geometry.Extrude.Circular.DualSide.DualMeridian import DualMeridian


# each physical orbit must retain its radius seam and two opposite boundary uses
def CheckDualRims(
    State: GeometryState,
    Shape: CircleShape,
    FirstMm: float,
    SecondMm: float,
    FirstTaper: float,
    SecondTaper: float,
) -> None:
    Meridian = DualMeridian(
        Shape.Geometry.radius, FirstMm, SecondMm, FirstTaper, SecondTaper
    )
    Center = (Shape.Geometry.center.x / 10, Shape.Geometry.center.y / 10)
    RimValues = {
        "rim_lower": Meridian[1],
        "joint": (Shape.Geometry.radius, 0.0),
        "rim_upper": Meridian[-2],
    }
    for Index, Entity in enumerate(State.Entities):
        if isinstance(Entity, CoedgeNode):
            Partner = State.Entities[Entity.Partner]
            if (
                not isinstance(Partner, CoedgeNode)
                or Partner.Partner != Index
                or Partner.EdgeRef != Entity.EdgeRef
                or Partner.Reversed == Entity.Reversed
                or Entity.Pcurve != -1
            ):
                raise ValueError("Native dual side boundary uses are not reciprocal")
        elif isinstance(Entity, EdgeNode):
            RoleName = ReadDualLabel(State, Index, FirstMm, SecondMm)
            Radius, Level = RimValues[RoleName]
            CheckSpanRim(State, Entity, (*Center, Level / 10), Radius / 10)
