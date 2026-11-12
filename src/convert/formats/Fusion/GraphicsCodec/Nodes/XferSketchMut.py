from __future__ import annotations
from typing import TYPE_CHECKING
from convert.formats.Fusion.GraphicsCodec.Nodes.XferBrepMut import XferBrepMut
from convert.formats.Fusion.GraphicsCodec.Nodes.XferLodMut import XferLodMut

from convert.formats.Fusion.GraphicsCodec.Model.Nodes.SketchWorld import SketchWorld

if TYPE_CHECKING:
    from convert.formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


def XferSketchMut(State: SceneCodec, Value: SketchWorld | None) -> SketchWorld:
    FaceBody = (
        XferBrepMut(State, Value.FaceBody if Value else None)
        if State.IsFlag(Value is not None and Value.FaceBody is not None)
        else None
    )
    LodCount = State.CountValue(len(Value.Nodes) if Value else None, "<i")
    if State.Integer(0, "<i"):
        raise ValueError("Unsupported ordinary sketch graphics nodes")
    Nodes = tuple(
        XferLodMut(State, Value.Nodes[Index] if Value else None)
        for Index in range(LodCount)
    )
    if State.Integer(0, "<i"):
        raise ValueError("Unsupported nonculling sketch graphics nodes")
    return SketchWorld(FaceBody, Nodes)
