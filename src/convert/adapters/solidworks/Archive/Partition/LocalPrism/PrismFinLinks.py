from collections.abc import Mapping
from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismFaceLoop import (
    PrismFaceLoop,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.ReadFaceRing import (
    PrismFinEnd,
)
from convert.Geometry.Parasolid import BrepTopology


# fin ownership needs end vertices and three independent traversals
@DataClass(frozen=True, slots=True)
class PrismFinLinks:
    EndVertices: Mapping[str, str]
    AcrossEdge: Mapping[str, str]
    AroundLoop: Mapping[str, str]
    AroundVertex: Mapping[str, str | None]
    VertexHeads: Mapping[str, str]
    EdgeHeads: Mapping[str, str]


# each closed prism edge needs exactly one positive and one negative coedge
def PrismEdgeFins(
    TopologyValue: BrepTopology,
) -> tuple[dict[str, str], dict[str, str]]:
    AcrossEdge: dict[str, str] = {}
    EdgeHeads: dict[str, str] = {}
    for EdgeId, UseIds in TopologyValue.edge_coedges.items():
        if len(UseIds) != 2:
            raise ValueError("local prism needs two fins per edge")
        First, Second = (TopologyValue.coedges[UseId] for UseId in UseIds)
        if First.reversed == Second.reversed:
            raise ValueError("local prism edge fins do not oppose each other")
        AcrossEdge.update({First.id: Second.id, Second.id: First.id})
        EdgeHeads[EdgeId] = Second.id if First.reversed else First.id
    return AcrossEdge, EdgeHeads


# a vertex chain follows the next loop fin across its edge to rotate around the vertex
def PrismVertexFins(
    Incident: Mapping[str, list[str]],
    AroundLoop: Mapping[str, str],
    AcrossEdge: Mapping[str, str],
) -> tuple[dict[str, str], dict[str, str | None]]:
    HeadsValue: dict[str, str] = {}
    LinksValue: dict[str, str | None] = {}
    for VertexId, FinIds in Incident.items():
        First = FinIds[0]
        Second = AcrossEdge[AroundLoop[First]]
        Third = AcrossEdge[AroundLoop[Second]]
        if (
            len(FinIds) != 3
            or set(FinIds) != {First, Second, Third}
            or AcrossEdge[AroundLoop[Third]] != First
        ):
            raise ValueError(
                "local prism vertex does not have one closed three fin rotation"
            )
        HeadsValue[VertexId] = First
        LinksValue.update({First: Second, Second: Third, Third: None})
    return HeadsValue, LinksValue


# access through the actual face loops establishes deterministic fin and incident order
def MakeFinLinks(
    FacesValue: tuple[PrismFaceLoop, ...], TopologyValue: BrepTopology
) -> PrismFinLinks:
    AcrossEdge, EdgeHeads = PrismEdgeFins(TopologyValue)
    AroundLoop: dict[str, str] = {}
    EndVertices: dict[str, str] = {}
    Incident: dict[str, list[str]] = {}
    for BoundaryValue in FacesValue:
        UsesValue = BoundaryValue.UsesValue
        for First, Second in zip(UsesValue, UsesValue[1:] + UsesValue[:1], strict=True):
            VertexId = PrismFinEnd(TopologyValue, First)
            EndVertices[First.id] = VertexId
            AroundLoop[First.id] = Second.id
            Incident.setdefault(VertexId, []).append(First.id)
    if Incident.keys() != TopologyValue.vertex_by_id.keys():
        raise ValueError("local prism vertices must all belong to the finite boundary")
    VertexHeads, AroundVertex = PrismVertexFins(Incident, AroundLoop, AcrossEdge)
    return PrismFinLinks(
        EndVertices, AcrossEdge, AroundLoop, AroundVertex, VertexHeads, EdgeHeads
    )
