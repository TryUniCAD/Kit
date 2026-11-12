from dataclasses import dataclass as MakeDataClass
from convert.formats.Fusion.GraphicsCodec.Model.Nodes.BrepWorld import BrepWorld
from convert.formats.Fusion.GraphicsCodec.Model.Nodes.LodValue import LodValue


@MakeDataClass(frozen=True, slots=True)
class SketchWorld:
    FaceBody: BrepWorld | None
    Nodes: tuple[LodValue, ...]
