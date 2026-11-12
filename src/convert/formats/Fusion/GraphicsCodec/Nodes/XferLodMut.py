from __future__ import annotations
from typing import TYPE_CHECKING
from convert.formats.Fusion.GraphicsCodec.Nodes.XferPayloadMut import XferPayloadMut
from convert.formats.Fusion.GraphicsCodec.Geometry.XferGeometryMut import (
    XferGeometryMut,
)

from convert.formats.Fusion.GraphicsCodec.Model.Nodes.LodValue import LodValue

if TYPE_CHECKING:
    from convert.formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


def XferLodMut(State: SceneCodec, Value: LodValue | None) -> LodValue:
    NodeData = XferPayloadMut(State, Value.NodeData if Value else None)
    LodMask = State.Integer(Value.LodMask if Value else None)
    Geometry = None
    if LodMask:
        if LodMask & (LodMask - 1) or State.Integer(0) != 0:
            raise ValueError("Unsupported graphics display item or LOD set")
        Geometry = XferGeometryMut(State, Value.Geometry if Value else None)
    Bounds = State.Vector(Value.Bounds if Value else None, 6, "<d")
    UseClosest = State.IsFlag(Value.UseClosest if Value else None)
    Result = LodValue(NodeData, LodMask, Geometry, Bounds, UseClosest)
    State.CheckResult(Value, Result)
    return Result
