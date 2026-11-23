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
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismFaceLoop import (
    PrismFaceLoop,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismFinLinks import (
    PrismFinLinks,
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


# each trim owns its fins and any link to a further trim on the same face
def MakePrismLoops(
    Boundaries: list[PrismFaceLoop], FaceRef: PrismRef, FinLinks: PrismFinLinks
) -> tuple[PrismCell, ...]:
    LoopRefs = tuple(PrismRef(15, Value.LoopValue.id) for Value in Boundaries)
    FollowingValues: tuple[PrismRef | int, ...] = (*LoopRefs[1:], 0)
    Values: list[PrismCell] = []
    for LoopRef, Boundary, Following in zip(
        LoopRefs, Boundaries, FollowingValues, strict=True
    ):
        Values.append(
            PrismCell(
                LoopRef,
                {
                    "face": FaceRef,
                    "halfedge": PrismRef(17, Boundary.UsesValue[0].id),
                    "next": Following,
                },
            )
        )
        Values.extend(MakePrismFins(Boundary, FinLinks))
    return tuple(Values)


# the solid and void face links traverse the same complete oriented boundary
def MakePrismFaces(
    FacesValue: tuple[PrismFaceLoop, ...], FinLinks: PrismFinLinks
) -> tuple[PrismCell, ...]:
    GroupsValue: dict[PrismRef, list[PrismFaceLoop]] = {}
    for BoundaryValue in FacesValue:
        GroupsValue.setdefault(PrismRef(14, BoundaryValue.FaceValue.id), []).append(
            BoundaryValue
        )
    FaceChain = PrismChain(GroupsValue)
    Values: list[PrismCell] = []
    for FaceRef, Boundaries in GroupsValue.items():
        First = Boundaries[0]
        Previous, Following = FaceChain[FaceRef]
        Values.append(
            MakeBoundFace(
                FaceRef,
                PrismRef(15, First.LoopValue.id),
                PrismRef(50, First.FaceValue.surface_id),
                Previous,
                Following,
                True,
            )
        )
        Values.extend(MakePrismLoops(Boundaries, FaceRef, FinLinks))
    return tuple(Values)
