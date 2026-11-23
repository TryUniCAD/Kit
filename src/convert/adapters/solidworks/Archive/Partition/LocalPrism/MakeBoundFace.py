from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismCell import (
    PrismCell,
    PrismRef,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismRootKeys import (
    KPrismSolidShell,
    KPrismVoidShell,
)


# every local face needs reciprocal links for both sides of its material boundary
def MakeBoundFace(
    FaceRef: PrismRef,
    LoopRef: PrismRef,
    SurfaceRef: PrismRef,
    Previous: PrismRef | int,
    Following: PrismRef | int,
    SameSense: bool,
) -> PrismCell:
    return PrismCell(
        FaceRef,
        {
            "shell": KPrismSolidShell,
            "front_shell": KPrismVoidShell,
            "loop": LoopRef,
            "surface": SurfaceRef,
            "previous": Previous,
            "next": Following,
            "previous_front": Previous,
            "next_front": Following,
            "sense": "+" if SameSense else "-",
        },
    )
