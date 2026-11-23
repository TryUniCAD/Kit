from convert.Geometry.Parasolid import BrepTopology
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismCell import (
    KPrismCellValue,
    PrismCell,
    PrismRef,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismChain import (
    PrismChain,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismRootKeys import (
    KPrismBody,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismVectors import (
    KMillimetersPerMeter,
    PrismMeters,
    PrismVector,
)
from interchange.brep.Curves.BrepCurves import CircleCurve
from interchange.brep.Surfaces.BrepSurfaces import CylinderSurface, PlaneSurface
from interchange.brep.Topology.BrepModel import BrepModel


# physical periodic edges select their positive fin and preserve the actual circle parameterization
def MakeAnnCurves(
    ModelValue: BrepModel,
    TopologyValue: BrepTopology,
    EdgeRefs: tuple[PrismRef, ...],
    CurveRefs: tuple[PrismRef, ...],
) -> tuple[PrismCell, ...]:
    LinksValue = PrismChain(EdgeRefs) | PrismChain(CurveRefs)
    Values: list[PrismCell] = []
    for EdgeValue, EdgeRef, CurveRef in zip(
        ModelValue.edges, EdgeRefs, CurveRefs, strict=True
    ):
        CircleValue = TopologyValue.curve_by_id[CurveRef.IdValue]
        if not isinstance(CircleValue, CircleCurve):
            raise ValueError("local annulus rim requires a circular carrier")
        UseId = next(
            Value
            for Value in TopologyValue.edge_coedges[EdgeValue.id]
            if not TopologyValue.coedges[Value].reversed
        )
        PriorEdge, NextEdge = LinksValue[EdgeRef]
        PriorCurve, NextCurve = LinksValue[CurveRef]
        Values.extend(
            (
                PrismCell(
                    EdgeRef,
                    {
                        "halfedge": PrismRef(17, UseId),
                        "previous": PriorEdge,
                        "next": NextEdge,
                        "curve": CurveRef,
                        "owner": KPrismBody,
                    },
                ),
                PrismCell(
                    CurveRef,
                    {
                        "owner": EdgeRef,
                        "previous": PriorCurve,
                        "next": NextCurve,
                        "sense": "+",
                        "centre": PrismMeters(CircleValue.center),
                        "normal": PrismVector(CircleValue.axis),
                        "x_axis": PrismVector(CircleValue.reference_direction),
                        "radius": CircleValue.radius / KMillimetersPerMeter,
                    },
                ),
            )
        )
    return tuple(Values)


# one face must retain its own analytic carrier and position on the boundary chain
def MakeAnnSurfs(
    ModelValue: BrepModel,
    TopologyValue: BrepTopology,
    SurfaceRefs: tuple[PrismRef, ...],
) -> tuple[PrismCell, ...]:
    LinksValue = PrismChain(SurfaceRefs)
    Values: list[PrismCell] = []
    for FaceValue, SurfaceRef in zip(ModelValue.faces, SurfaceRefs, strict=True):
        Carrier = TopologyValue.surface_by_id[SurfaceRef.IdValue]
        PriorRef, NextRef = LinksValue[SurfaceRef]
        Geometry: dict[str, KPrismCellValue]
        if isinstance(Carrier, PlaneSurface):
            Geometry = {"normal": PrismVector(Carrier.normal)}
        elif isinstance(Carrier, CylinderSurface):
            Geometry = {
                "axis": PrismVector(Carrier.axis),
                "radius": Carrier.radius / KMillimetersPerMeter,
            }
        else:
            raise ValueError("local annulus requires planes and cylindrical walls")
        Values.append(
            PrismCell(
                SurfaceRef,
                {
                    "owner": PrismRef(14, FaceValue.id),
                    "previous": PriorRef,
                    "next": NextRef,
                    "sense": "+",
                    "pvec": PrismMeters(Carrier.origin),
                    "x_axis": PrismVector(Carrier.reference_direction),
                    **Geometry,
                },
            )
        )
    return tuple(Values)
