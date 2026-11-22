from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.Geometry.CylKeys import (
    KCylMantle,
    KCylSide,
)
from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.Geometry.CylRimRef import (
    CylRimRef,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismCell import PrismCell
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismChain import (
    PrismChain,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismRootKeys import (
    KPrismSolidShell,
    KPrismVoidShell,
)


# attached blind bosses retain an opposite near cap face on the same signed carrier axis
def MakeAttCylFaces(NearValue: CylRimRef, FarValue: CylRimRef) -> tuple[PrismCell, ...]:
    FacesValue = KCylSide, NearValue.FaceValue, FarValue.FaceValue
    LinksValue = PrismChain(FacesValue)
    return tuple(
        PrismCell(
            FaceValue,
            {
                "shell": KPrismSolidShell,
                "front_shell": KPrismVoidShell,
                "loop": LoopValue,
                "surface": SurfaceValue,
                "previous": PriorValue,
                "next": NextValue,
                "previous_front": PriorValue,
                "next_front": NextValue,
                "sense": SenseValue,
            },
        )
        for FaceValue, LoopValue, SurfaceValue, SenseValue in zip(
            FacesValue,
            (NearValue.SideLoop, NearValue.LoopValue, FarValue.LoopValue),
            (KCylMantle, NearValue.PlaneValue, FarValue.PlaneValue),
            ("+", "-", "+"),
            strict=True,
        )
        for PriorValue, NextValue in (LinksValue[FaceValue],)
    )
