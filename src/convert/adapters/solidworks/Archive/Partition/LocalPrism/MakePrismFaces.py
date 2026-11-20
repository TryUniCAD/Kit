from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismCell import (
    PrismCell,
    PrismRef,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismChain import (
    PrismChain,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismFaceLoop import (
    PrismFaceLoop,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismFinLinks import (
    PrismFinLinks,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismRootKeys import (
    KPrismSolidShell,
    KPrismVoidShell,
)


# actual coedge order supplies each oriented loop and edge incidence
def MakePrismFins(
    BoundaryValue: PrismFaceLoop, FinLinks: PrismFinLinks
) -> tuple[PrismCell, ...]:
    UsesValue = BoundaryValue.UsesValue
    Values: list[PrismCell] = []
    for IndexValue, UseValue in enumerate(UsesValue):
        UseId = UseValue.id
        Radial = FinLinks.AroundVertex[UseId]
        Values.append(
            PrismCell(
                PrismRef(17, UseId),
                {
                    "edge": PrismRef(16, UseValue.edge_id),
                    "other": PrismRef(17, FinLinks.AcrossEdge[UseId]),
                    "vertex": PrismRef(18, FinLinks.EndVertices[UseId]),
                    "loop": PrismRef(15, BoundaryValue.LoopValue.id),
                    "forward": PrismRef(17, FinLinks.AroundLoop[UseId]),
                    "backward": PrismRef(17, UsesValue[IndexValue - 1].id),
                    "next_at_vx": 0 if Radial is None else PrismRef(17, Radial),
                    "sense": "-" if UseValue.reversed else "+",
                },
            )
        )
    return tuple(Values)


# the solid and void face links traverse the same complete oriented boundary
def MakePrismFaces(
    FacesValue: tuple[PrismFaceLoop, ...], FinLinks: PrismFinLinks
) -> tuple[PrismCell, ...]:
    FaceChain = PrismChain(
        PrismRef(14, BoundaryValue.FaceValue.id) for BoundaryValue in FacesValue
    )
    Values: list[PrismCell] = []
    for BoundaryValue in FacesValue:
        FaceValue = BoundaryValue.FaceValue
        FaceRef = PrismRef(14, FaceValue.id)
        LoopRef = PrismRef(15, BoundaryValue.LoopValue.id)
        Previous, Following = FaceChain[FaceRef]
        Values.extend(
            (
                PrismCell(
                    FaceRef,
                    {
                        "shell": KPrismSolidShell,
                        "front_shell": KPrismVoidShell,
                        "loop": LoopRef,
                        "surface": PrismRef(50, FaceValue.surface_id),
                        "previous": Previous,
                        "next": Following,
                        "previous_front": Previous,
                        "next_front": Following,
                        "sense": "+",
                    },
                ),
                PrismCell(
                    LoopRef,
                    {
                        "face": FaceRef,
                        "halfedge": PrismRef(17, BoundaryValue.UsesValue[0].id),
                    },
                ),
                *MakePrismFins(BoundaryValue, FinLinks),
            )
        )
    return tuple(Values)
