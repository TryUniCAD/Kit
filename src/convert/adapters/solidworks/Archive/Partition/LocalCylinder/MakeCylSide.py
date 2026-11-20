from convert.adapters.solidworks.Archive.Partition.LocalCylinder.LocalCylShape import (
    LocalCylShape,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismCell import (
    PrismCell,
    PrismRef,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismVectors import (
    KMillimetersPerMeter,
    PrismMeters,
    PrismVector,
)


# the analytic mantle needs both authored loops before its surface carrier
def MakeCylSide(
    ShapeValue: LocalCylShape, MantleRef: PrismRef, FirstPlane: PrismRef
) -> tuple[PrismCell, ...]:
    FarRim, NearRim = ShapeValue.FarRim, ShapeValue.NearRim
    FaceRef = PrismRef(14, ShapeValue.SideFace.id)
    NearLoop = PrismRef(15, NearRim.SideLoop.id)
    MantleValue = ShapeValue.MantleValue
    return (
        PrismCell(
            PrismRef(15, FarRim.SideLoop.id),
            {
                "face": FaceRef,
                "halfedge": PrismRef(17, FarRim.SideUse.id),
                "next": NearLoop,
            },
        ),
        PrismCell(
            NearLoop, {"face": FaceRef, "halfedge": PrismRef(17, NearRim.SideUse.id)}
        ),
        PrismCell(
            MantleRef,
            {
                "owner": FaceRef,
                "previous": 0,
                "next": FirstPlane,
                "sense": "+",
                "pvec": PrismMeters(MantleValue.origin),
                "axis": PrismVector(MantleValue.axis),
                "radius": MantleValue.radius / KMillimetersPerMeter,
                "x_axis": PrismVector(MantleValue.reference_direction),
            },
        ),
    )
