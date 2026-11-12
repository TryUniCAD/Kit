from dataclasses import dataclass as MakeDataClass

from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode


@MakeDataClass(frozen=True, slots=True)
class RectContext:
    Component: NativeNode
    Fragment: NativeNode
    SketchFeature: NativeNode
    Extrude: NativeNode
    Sketch: NativeNode
    Plane: NativeNode
    Along: NativeNode
    Taper: NativeNode
    BodyNode: NativeNode
    DcBody: NativeNode
