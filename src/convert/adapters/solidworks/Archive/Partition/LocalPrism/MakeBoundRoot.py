from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismCell import (
    PrismCell,
    PrismRef,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismRootKeys import (
    KPrismBody,
    KPrismSolidRegion,
    KPrismSolidShell,
    KPrismVoidRegion,
    KPrismVoidShell,
)

# the local kernel body has the proven session linear resolution in meters
KLocalLinearResolution = 1e-8

# the selected session precision determines the dimensionless size ratio
KLocalSessionPrecision = 1e-11


# finite and periodic local solids need the same paired native regions and shells
def MakeBoundRoot(
    FirstFace: PrismRef,
    FirstEdge: PrismRef,
    FirstCurve: PrismRef,
    FirstSurface: PrismRef,
    FirstVertex: PrismRef | int = 0,
    FirstPoint: PrismRef | int = 0,
) -> tuple[PrismCell, ...]:
    return (
        PrismCell(
            KPrismBody,
            {
                "shell": KPrismSolidShell,
                "region": KPrismVoidRegion,
                "edge": FirstEdge,
                "vertex": FirstVertex,
                "boundary_point": FirstPoint,
                "boundary_curve": FirstCurve,
                "boundary_surface": FirstSurface,
                "res_size": KLocalLinearResolution / KLocalSessionPrecision,
                "res_linear": KLocalLinearResolution,
                "state": 1,
                "body_type": 1,
                "nom_geom_state": 1,
            },
        ),
        PrismCell(
            KPrismVoidRegion,
            {
                "body": KPrismBody,
                "next": KPrismSolidRegion,
                "previous": 0,
                "shell": KPrismVoidShell,
                "type": "V",
            },
        ),
        PrismCell(
            KPrismSolidRegion,
            {
                "body": KPrismBody,
                "next": 0,
                "previous": KPrismVoidRegion,
                "shell": KPrismSolidShell,
                "type": "S",
            },
        ),
        PrismCell(
            KPrismSolidShell,
            {
                "body": KPrismBody,
                "region": KPrismSolidRegion,
                "face": FirstFace,
                "front_face": 0,
            },
        ),
        PrismCell(
            KPrismVoidShell,
            {"body": 0, "region": KPrismVoidRegion, "face": 0, "front_face": FirstFace},
        ),
    )
