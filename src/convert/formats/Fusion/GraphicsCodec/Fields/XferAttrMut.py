from __future__ import annotations
from typing import TYPE_CHECKING
from convert.formats.Fusion.GraphicsCodec.Schema.AttrRules import KAttrRules
from convert.formats.Fusion.GraphicsCodec.Fields.XferFieldsMut import XferFieldsMut

from convert.formats.Fusion.GraphicsCodec.Model.Values.GraphicAttr import GraphicAttr

if TYPE_CHECKING:
    from convert.formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec


def XferAttrMut(State: SceneCodec, Value: GraphicAttr | None) -> GraphicAttr:
    ClassName = State.TextValue(Value.ClassName if Value else None)
    Rules = KAttrRules.get(ClassName)
    if Rules is None:
        raise ValueError(f"Unsupported graphics attribute class: {ClassName}")
    Priority = State.Integer(Value.Priority if Value else None, "<i")
    WinTies = State.IsFlag(Value.WinTies if Value else None)
    Fields = XferFieldsMut(State, Rules, Value.Fields if Value else None)
    return GraphicAttr(ClassName, Priority, WinTies, Fields)
