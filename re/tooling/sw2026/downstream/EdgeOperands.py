from dataclasses import dataclass
from operator import attrgetter

from downstream.BoundaryRoles import permanent_edge_ids
from downstream.CacheInputs import attached_part_chains, face_incidence, topology_node
from para.Partition import Node


@dataclass(frozen=True)
class EdgeOperands:
    edge: Node
    downstream_id: int
    role_face_ids: tuple[int, int, int, int]


def opposite_fin(nodes, fin):
    partner = topology_node(nodes, fin.fields["other"], 17)
    if (partner.index == fin.index or partner.fields["other"] != fin.index
            or partner.fields["edge"] != fin.fields["edge"]):
        raise ValueError("ordinary edge operands require a reciprocal loop-owned fin")
    return partner


def prism_edge_operands(partition, allocation, updated_at, *, special_id_map_present):
    if special_id_map_present is not False or permanent_edge_ids(partition):
        raise ValueError("ordinary edge operands require the unmodified surface-ID path")
    nodes, faces, edges = attached_part_chains(partition, allocation, updated_at)
    if len(faces) != 6 or len(edges) != 12:
        raise ValueError("prism edge operands require the actual six faces and twelve edges")

    face_ids = {face.index: number for face, (_, number) in zip(faces, allocation.faces, strict=True)}
    fin_faces = face_incidence(nodes, faces, identity=attrgetter("index"))
    fins_by_edge = {edge.index: [] for edge in edges}
    for index in fin_faces:
        fins_by_edge[nodes[index].fields["edge"]].append(index)

    result = []
    adjacent_pairs = set()
    for edge, (_, number) in zip(edges, allocation.edges, strict=True):
        carrier = topology_node(nodes, edge.fields["curve"], 30)
        if carrier.fields["owner"] != edge.index:
            raise ValueError("prism edge operands need the actual line carrier owned by the edge")
        first = topology_node(nodes, edge.fields["halfedge"], 17)
        partner = opposite_fin(nodes, first)
        if (set(fins_by_edge[edge.index]) != {first.index, partner.index}
                or {first.fields["sense"], partner.fields["sense"]} != {"+", "-"}):
            raise ValueError("prism edge operands need exactly two opposite-sense live edge fins")
        selected = first if first.fields["sense"] == "+" else partner
        left = fin_faces[selected.index]
        right = fin_faces[opposite_fin(nodes, selected).index]
        previous = topology_node(nodes, selected.fields["backward"], 17)
        following = topology_node(nodes, selected.fields["forward"], 17)
        start = fin_faces[opposite_fin(nodes, previous).index]
        end = fin_faces[opposite_fin(nodes, following).index]

        pair = frozenset((left, right))
        if pair in adjacent_pairs or len({left, right, start, end}) != 4:
            raise ValueError("ordinary prism mode one needs one common edge and four distinct face operands")
        adjacent_pairs.add(pair)
        roles = (face_ids[left], face_ids[right], face_ids[start], face_ids[end])
        result.append(EdgeOperands(edge, number, roles))
    return tuple(result)
