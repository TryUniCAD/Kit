from math import isclose as IsClose

from convert.Formats.Fusion.BrepCodec.Journal.Geometry.ConeNode import ConeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EllipseNode import EllipseNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)


# physical geometry must select a role before persistent labels can establish ownership
def ReadDualLabel(
    State: GeometryState,
    OwnerRef: int,
    FirstMm: float,
    SecondMm: float,
) -> str:
    Owner = State.Entities[OwnerRef]
    if isinstance(Owner, FaceNode):
        Carrier = State.Entities[Owner.Surface]
        if isinstance(Carrier, ConeNode):
            if Carrier.AxisVector == (0.0, 0.0, 1.0):
                return "first"
            if Carrier.AxisVector == (0.0, 0.0, -1.0):
                return "second"
            raise ValueError("Native dual side cone has an unsupported axis")
        if not isinstance(Carrier, PlaneNode):
            raise ValueError("Native dual side face has an unsupported carrier")
        Levels: tuple[tuple[str, float], ...] = (
            ("lower", -SecondMm / 10),
            ("upper", FirstMm / 10),
        )
    elif isinstance(Owner, EdgeNode):
        Carrier = State.Entities[Owner.CurveRef]
        if not isinstance(Carrier, EllipseNode):
            raise ValueError("Native dual side edge has an unsupported carrier")
        Levels = (
            ("rim_lower", -SecondMm / 10),
            ("joint", 0.0),
            ("rim_upper", FirstMm / 10),
        )
    else:
        raise ValueError("Native dual side label has an unsupported physical owner")
    Matches = tuple(
        RoleName
        for RoleName, Level in Levels
        if IsClose(Carrier.OriginCm[2], Level, rel_tol=0.0, abs_tol=1e-9)
    )
    if len(Matches) != 1:
        raise ValueError("Native dual side label has an ambiguous physical station")
    return Matches[0]
