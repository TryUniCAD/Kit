from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.CapFace import CapFace
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.CapRings import CapRings
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.GroupRings import (
    GroupRings,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSlab import PrismSlab


def CapFaces(Slabs: tuple[PrismSlab, ...]) -> tuple[CapFace, ...]:
    Levels = sorted(
        {
            Value
            for SlabValue in Slabs
            for Value in (SlabValue.LowerCm, SlabValue.UpperCm)
        }
    )
    Faces: list[CapFace] = []
    for Level in Levels:
        Below = next(
            (SlabValue for SlabValue in Slabs if SlabValue.UpperCm == Level), None
        )
        Above = next(
            (SlabValue for SlabValue in Slabs if SlabValue.LowerCm == Level), None
        )
        for Upward, Source in ((False, Above), (True, Below)):
            if Source is None:
                continue
            Rings = CapRings(Level, Upward, Below, Above)
            Label = Source.RoofLabel if Upward else Source.FloorLabel
            for Loops in GroupRings(Rings, Upward, Level):
                Faces.append(CapFace(Level, Upward, Label, Loops))
    return tuple(Faces)
