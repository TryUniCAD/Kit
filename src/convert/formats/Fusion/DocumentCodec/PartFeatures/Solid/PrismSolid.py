from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSlab import PrismSlab


@MakeDataClass(frozen=True, slots=True)
class PrismSolid:
    Slabs: tuple[PrismSlab, ...]
    BodyLabel: FaceLabel
    SketchCurves: tuple[tuple[str, int], ...] = ()
