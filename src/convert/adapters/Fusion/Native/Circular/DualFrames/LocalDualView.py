from dataclasses import replace as ReplaceData
from math import dist as Distance

from convert.adapters.Fusion.Native.Circular.DualFrames.DualBodyView import DualBodyView
from convert.adapters.Fusion.Native.Circular.DualFrames.LocalDualEntity import (
    LocalDualEntity,
)
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.CheckGeometry import (
    CheckGeometry,
)
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Geometry.Revolve.SweepInput import CheckSweepFrame
from convert.Geometry.Revolve.SweepVector import CrossVector
from interchange.geometry.Models.Transform import KTransformIdentity, Transform


# local geometric comparison must preserve the entire original record and ownership inventory
def LocalDualView(State: GeometryState, Frame: Transform) -> GeometryState:
    CheckGeometry(State)
    CheckSweepFrame(Frame.origin, Frame.z_axis, Frame.x_axis)
    Cross = CrossVector(Frame.z_axis, Frame.x_axis)
    if (
        not Distance(
            (Cross.x, Cross.y, Cross.z),
            (Frame.y_axis.x, Frame.y_axis.y, Frame.y_axis.z),
        )
        <= 1e-9
    ):
        raise ValueError("Native dual comparison frame must be right handed")
    for Entity in State.Entities:
        if isinstance(Entity, BodyNode):
            _ = DualBodyView(State, Entity)
    if Frame == KTransformIdentity:
        return State
    Local = ReplaceData(
        State,
        Entities=tuple(LocalDualEntity(Entity, Frame) for Entity in State.Entities),
    )
    CheckGeometry(Local)
    return Local
