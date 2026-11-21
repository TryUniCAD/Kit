from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.LocalCylinder.CylRim import CylRim
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismCell import (
    PrismCell,
    PrismRef,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismRootKeys import (
    KPrismBody,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismVectors import (
    KMillimetersPerMeter,
    PrismMeters,
    PrismVector,
)
from interchange.brep.Topology.BrepTopology import BrepCoedge


# periodic rim uses must keep their opposite orientations without a stored vertex
def MakeCylFin(
    UseValue: BrepCoedge, Opposite: BrepCoedge, LoopRef: PrismRef, EdgeRef: PrismRef
) -> PrismCell:
    FinRef = PrismRef(17, UseValue.id)
    return PrismCell(
        FinRef,
        {
            "loop": LoopRef,
            "forward": FinRef,
            "backward": FinRef,
            "vertex": 0,
            "other": PrismRef(17, Opposite.id),
            "edge": EdgeRef,
            "next_at_vx": 0,
            "sense": "-" if UseValue.reversed else "+",
        },
    )


# the cap plane and circular edge keep the actual authored spatial frame and carrier links
def MakeCylRim(
    RimValue: CylRim,
    LinksValue: Mapping[PrismRef, tuple[PrismRef | int, PrismRef | int]],
) -> tuple[PrismCell, ...]:
    CapRef = PrismRef(14, RimValue.CapFace.id)
    CapLoop = PrismRef(15, RimValue.CapLoop.id)
    SideLoop = PrismRef(15, RimValue.SideLoop.id)
    EdgeRef = PrismRef(16, RimValue.EdgeValue.id)
    CircleValue, PlaneValue = RimValue.CircleValue, RimValue.PlaneValue
    CircleRef, PlaneRef = PrismRef(31, CircleValue.id), PrismRef(50, PlaneValue.id)
    EdgePrior, EdgeNext = LinksValue[EdgeRef]
    CirclePrior, CircleNext = LinksValue[CircleRef]
    PlanePrior, PlaneNext = LinksValue[PlaneRef]
    return (
        PrismCell(
            CapLoop, {"face": CapRef, "halfedge": PrismRef(17, RimValue.CapUse.id)}
        ),
        PrismCell(
            EdgeRef,
            {
                "halfedge": PrismRef(17, RimValue.SideUse.id),
                "previous": EdgePrior,
                "next": EdgeNext,
                "curve": CircleRef,
                "owner": KPrismBody,
            },
        ),
        PrismCell(
            CircleRef,
            {
                "owner": EdgeRef,
                "previous": CirclePrior,
                "next": CircleNext,
                "sense": "+",
                "centre": PrismMeters(CircleValue.center),
                "normal": PrismVector(CircleValue.axis),
                "x_axis": PrismVector(CircleValue.reference_direction),
                "radius": CircleValue.radius / KMillimetersPerMeter,
            },
        ),
        PrismCell(
            PlaneRef,
            {
                "owner": CapRef,
                "previous": PlanePrior,
                "next": PlaneNext,
                "sense": "+",
                "pvec": PrismMeters(PlaneValue.origin),
                "normal": PrismVector(PlaneValue.normal),
                "x_axis": PrismVector(PlaneValue.reference_direction),
            },
        ),
        MakeCylFin(RimValue.SideUse, RimValue.CapUse, SideLoop, EdgeRef),
        MakeCylFin(RimValue.CapUse, RimValue.SideUse, CapLoop, EdgeRef),
    )
