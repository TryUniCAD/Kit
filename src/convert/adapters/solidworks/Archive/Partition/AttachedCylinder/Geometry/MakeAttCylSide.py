from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.Geometry.CylKeys import (
    KCylMantle,
    KCylSide,
)
from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.Geometry.CylRimRef import (
    CylRimRef,
)
from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.Geometry.CylSpan import (
    CylSpan,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismCell import PrismCell


# the two lateral loops precede the finite side carrier in the attached body schedule
def MakeAttCylSide(
    NearValue: CylRimRef,
    FarValue: CylRimRef,
    SpanValue: CylSpan,
) -> tuple[PrismCell, ...]:
    return (
        PrismCell(
            NearValue.SideLoop,
            {
                "face": KCylSide,
                "halfedge": NearValue.SideFin,
                "next": FarValue.SideLoop,
            },
        ),
        PrismCell(FarValue.SideLoop, {"face": KCylSide, "halfedge": FarValue.SideFin}),
        PrismCell(
            KCylMantle,
            {
                "owner": KCylSide,
                "sense": "+",
                "pvec": SpanValue.NearValue,
                "axis": SpanValue.AxisValue,
                "radius": SpanValue.RadiusValue,
                "x_axis": SpanValue.RadialValue,
                "previous": 0,
                "next": NearValue.PlaneValue,
            },
        ),
    )
