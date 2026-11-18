from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.Native import NativeSketch
from convert.adapters.solidworks.Core.TypedResolved.Circles.ReadLocalCirc import (
    ReadLocalCirc,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# the direct circle path recovers the actual parameter and centre when legacy marker bindings are unavailable
def BindLocalCirc(
    SketchValue: NativeSketch, NodeValue: ArchiveNode, LinkValue: NativeLink
) -> NativeSketch | None:
    try:
        ShapeValue = RequireNative(NodeValue.FieldsValue.get("pd_f80"), "sgSketch")
        Result = ReadLocalCirc(ShapeValue, LinkValue)
    except (ValueError, KeyError, TypeError):
        return None
    if Result is None:
        return None
    CircleValue, Dimension = Result
    return ReplaceValue(SketchValue, TypedCircle=CircleValue, dimensions=(Dimension,))
