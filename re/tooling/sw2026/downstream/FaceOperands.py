from dataclasses import dataclass
from operator import attrgetter

from downstream.BoundaryRoles import permanent_edge_ids
from downstream.CacheInputs import attached_part_chains, face_incidence, topology_node
from para.Partition import Node


@dataclass(frozen=True)
class FaceOperands:
    face: Node
    downstream_id: int
    inline_faces: tuple[Node | None, ...]
    initial_role_values: tuple[tuple[int, int], ...]


def single_loop_face_operands(partition, allocation, updated_at, *, special_id_map_present):
    if special_id_map_present is not False or permanent_edge_ids(partition):
        raise ValueError("ordinary face operands require the unmodified surface-ID path")
    nodes, faces, _ = attached_part_chains(partition, allocation, updated_at)
    fin_faces = face_incidence(nodes, faces, identity=attrgetter("index"))
    fins_by_face = {face.index: [] for face in faces}
    for fin, face in fin_faces.items():
        fins_by_face[face].append(fin)

    result = []
    registered = {}
    for face, (_, identifier) in zip(faces, allocation.faces, strict=True):
        loop = topology_node(nodes, face.fields["loop"], 15)
        if loop.fields["next"]:
            raise ValueError("face operands need the actual single selected loop")
        adjacent_faces = []
        for reference in fins_by_face[face.index]:
            fin = topology_node(nodes, reference, 17)
            partner = topology_node(nodes, fin.fields["other"], 17)
            if (partner.index == reference or partner.fields["other"] != reference
                    or partner.fields["edge"] != fin.fields["edge"] or partner.index not in fin_faces):
                raise ValueError("face operands require a reciprocal loop-owned fin")
            adjacent_faces.append(nodes[fin_faces[partner.index]])
        inline_faces = (face, *adjacent_faces, None)
        initial_roles = tuple(
            (index, registered[owner.index]) for index, owner in enumerate(inline_faces[:-1])
            if owner.index in registered
        )
        result.append(FaceOperands(face, identifier, inline_faces, initial_roles))
        registered[face.index] = identifier
    return tuple(result)
