from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.CanonLoop import CanonLoop
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.InsetLoop import InsetLoop
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LoopMath import LoopArea
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSlab import PrismSlab
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSolid import (
    PrismSolid,
)


def HollowSolid(Solid: PrismSolid, ThicknessCm: float, Operation: int) -> PrismSolid:
    if len(Solid.Slabs) != 1 or len(Solid.Slabs[0].Loops) != 1:
        raise ValueError("Fusion part shell requires one single-profile prism")
    SlabValue = Solid.Slabs[0]
    Outer = SlabValue.Loops[0]
    if (
        LoopArea(Outer) <= 0
        or ThicknessCm >= SlabValue.UpperCm - SlabValue.LowerCm - 1e-9
    ):
        raise ValueError("Fusion part shell thickness exceeds the prism")
    Inner = CanonLoop(InsetLoop(Outer, ThicknessCm, Operation))
    if LoopArea(Inner) >= 0:
        raise ValueError("Fusion part shell thickness collapses the profile")
    Floor = SlabValue.FloorLabel
    Shelf = FaceLabel(Floor.PrimaryId, Floor.OperationIds + (Operation,))
    Middle = SlabValue.LowerCm + ThicknessCm
    BaseValue = PrismSlab(SlabValue.LowerCm, Middle, (Outer,), Floor, Shelf)
    WallValue = PrismSlab(
        Middle, SlabValue.UpperCm, (Outer, Inner), Shelf, SlabValue.RoofLabel
    )
    return ReplaceValue(Solid, Slabs=(BaseValue, WallValue))
