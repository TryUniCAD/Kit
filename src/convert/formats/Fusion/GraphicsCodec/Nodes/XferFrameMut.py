from __future__ import annotations
from typing import TYPE_CHECKING
from convert.formats.Fusion.GraphicsCodec.Nodes.XferNodeMut import XferNodeMut

from convert.formats.Fusion.GraphicsCodec.Model.Nodes.RenderFrame import RenderFrame

if TYPE_CHECKING:
    from convert.formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


def XferFrameMut(State: SceneCodec, Value: RenderFrame | None) -> RenderFrame:
    Matrix = State.OptionalMat(Value.Matrix if Value else None)
    State.EmptyLinks(4)
    NodeData = None
    if State.IsFlag(Value is not None and Value.NodeData is not None):
        State.ExpectText("NodeData")
        NodeData = XferNodeMut(State, Value.NodeData if Value else None, False)
    return RenderFrame(Matrix, NodeData)
