from dataclasses import dataclass as MakeDataClass
from convert.formats.Fusion.GraphicsCodec.Model.Nodes.NodePayload import NodePayload
from convert.formats.Fusion.GraphicsCodec.Model.Values.SimpleMesh import SimpleMesh
from convert.formats.Fusion.GraphicsCodec.Model.Values.FatPoint import FatPoint


@MakeDataClass(frozen=True, slots=True)
class LodValue:
    NodeData: NodePayload
    LodMask: int
    Geometry: SimpleMesh | FatPoint | None
    Bounds: tuple[float, ...]
    UseClosest: bool
