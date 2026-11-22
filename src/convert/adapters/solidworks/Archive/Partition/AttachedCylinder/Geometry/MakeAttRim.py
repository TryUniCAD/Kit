from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.Geometry.CylKeys import (
    KCylMantle,
)
from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.Geometry.CylRimRef import (
    CylRimRef,
)
from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.Geometry.CylSpan import (
    CylSpan,
)
from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.Geometry.MakeCircFin import (
    MakeCircFin,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismCell import PrismCell
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismRootKeys import (
    KPrismBody,
)


# both cap and ring carriers retain their actual centre and signed sketch basis
def MakeAttRim(
    RimValue: CylRimRef,
    OtherValue: CylRimRef,
    SpanValue: CylSpan,
    IsNear: bool,
) -> tuple[PrismCell, ...]:
    PointValue = SpanValue.NearValue if IsNear else SpanValue.FarValue
    CapSense, SideSense = ("-", "+") if IsNear else ("+", "-")
    return (
        PrismCell(
            RimValue.LoopValue,
            {"face": RimValue.FaceValue, "halfedge": RimValue.CapFin},
        ),
        PrismCell(
            RimValue.EdgeValue,
            {
                "owner": KPrismBody,
                "curve": RimValue.CurveValue,
                "halfedge": RimValue.SideFin if IsNear else RimValue.CapFin,
                "previous": 0 if IsNear else OtherValue.EdgeValue,
                "next": OtherValue.EdgeValue if IsNear else 0,
            },
        ),
        PrismCell(
            RimValue.CurveValue,
            {
                "owner": RimValue.EdgeValue,
                "sense": "+",
                "centre": PointValue,
                "normal": SpanValue.AxisValue,
                "x_axis": SpanValue.RadialValue,
                "radius": SpanValue.RadiusValue,
                "previous": 0 if IsNear else OtherValue.CurveValue,
                "next": OtherValue.CurveValue if IsNear else 0,
            },
        ),
        PrismCell(
            RimValue.PlaneValue,
            {
                "owner": RimValue.FaceValue,
                "sense": "+",
                "pvec": PointValue,
                "normal": SpanValue.AxisValue,
                "x_axis": SpanValue.RadialValue,
                "previous": KCylMantle if IsNear else OtherValue.PlaneValue,
                "next": OtherValue.PlaneValue if IsNear else 0,
            },
        ),
        MakeCircFin(
            RimValue.CapFin,
            RimValue.SideFin,
            RimValue.LoopValue,
            RimValue.EdgeValue,
            CapSense,
        ),
        MakeCircFin(
            RimValue.SideFin,
            RimValue.CapFin,
            RimValue.SideLoop,
            RimValue.EdgeValue,
            SideSense,
        ),
    )
