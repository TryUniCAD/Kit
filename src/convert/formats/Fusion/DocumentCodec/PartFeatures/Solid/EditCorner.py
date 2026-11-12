from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.CornerEdit import (
    CornerEdit,
    CornerIndex,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSlab import PrismSlab
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSolid import (
    PrismSolid,
)


def EditCorner(
    Solid: PrismSolid,
    CornerCm: tuple[float, float],
    AmountCm: float,
    Label: FaceLabel,
    Rounded: bool,
) -> PrismSolid:
    Slabs: list[PrismSlab] = []
    for SlabValue in Solid.Slabs:
        Loops = list(SlabValue.Loops)
        Found = [
            (Ordinal, Index)
            for Ordinal, LoopValue in enumerate(Loops)
            if (Index := CornerIndex(LoopValue, CornerCm)) is not None
        ]
        if len(Found) != 1:
            raise ValueError("Fusion part corner must be one vertical edge of the body")
        Ordinal, Index = Found[0]
        Loops[Ordinal] = CornerEdit(Loops[Ordinal], Index, AmountCm, Label, Rounded)
        Slabs.append(ReplaceValue(SlabValue, Loops=tuple(Loops)))
    return ReplaceValue(Solid, Slabs=tuple(Slabs))
