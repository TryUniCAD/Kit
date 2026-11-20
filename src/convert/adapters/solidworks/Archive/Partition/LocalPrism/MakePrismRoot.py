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
from interchange.brep.Topology.BrepModel import BrepModel

# the local kernel body has the proven session linear resolution in meters
KLocalLinearResolution = 1e-8

# the selected session precision determines the dimensionless size ratio
KLocalSessionPrecision = 1e-11


# the resident body uses a solid and void region with matched face chains
def MakePrismRoot(ModelValue: BrepModel) -> tuple[PrismCell, ...]:
    FirstFace = PrismRef(14, ModelValue.faces[0].id)
    return (
        PrismCell(
            KPrismBody,
            {
                "shell": KPrismSolidShell,
                "region": KPrismVoidRegion,
                "edge": PrismRef(16, ModelValue.edges[0].id),
                "vertex": PrismRef(18, ModelValue.vertices[0].id),
                "boundary_point": PrismRef(29, ModelValue.vertices[0].id),
                "boundary_curve": PrismRef(30, ModelValue.curves[0].id),
                "boundary_surface": PrismRef(50, ModelValue.surfaces[0].id),
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
