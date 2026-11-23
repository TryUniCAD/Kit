from convert.adapters.solidworks.Archive.Partition.LocalCylinder.LocalCylShape import (
    LocalCylShape,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.MakeBoundFace import (
    MakeBoundFace,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismCell import (
    PrismCell,
    PrismRef,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismChain import (
    PrismChain,
)


# the imported solid needs the same reciprocal face order on both shell sides
def MakeCylFaces(
    ShapeValue: LocalCylShape, SurfaceRefs: tuple[PrismRef, PrismRef, PrismRef]
) -> tuple[PrismCell, ...]:
    FarRim, NearRim = ShapeValue.FarRim, ShapeValue.NearRim
    FaceRefs = tuple(
        PrismRef(14, FaceValue.id)
        for FaceValue in (FarRim.CapFace, NearRim.CapFace, ShapeValue.SideFace)
    )
    LoopRefs = tuple(
        PrismRef(15, LoopValue.id)
        for LoopValue in (FarRim.CapLoop, NearRim.CapLoop, FarRim.SideLoop)
    )
    MantleRef, FarPlane, NearPlane = SurfaceRefs
    LinksValue = PrismChain(FaceRefs)
    return tuple(
        MakeBoundFace(FaceRef, LoopRef, SurfaceRef, PriorRef, NextRef, True)
        for FaceRef, LoopRef, SurfaceRef in zip(
            FaceRefs, LoopRefs, (FarPlane, NearPlane, MantleRef), strict=True
        )
        for PriorRef, NextRef in (LinksValue[FaceRef],)
    )
