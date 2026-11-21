from downstream.CacheInputs import attached_part_chains
from downstream.FaceRegistration import cache_identity_info
from para.Tracking import signed_dword, unsigned
from para.concentric.CylinderFace import words


def fresh_edge_registration(partition, allocation, cache_fields, cache_filetime):
    nodes, faces, edges = attached_part_chains(partition, allocation, cache_fields["f28"])
    if len(faces) != 6 or len(edges) != 12:
        raise ValueError("edge lookup registration needs the admitted fresh six-face twelve-edge map")
    body, = (member for member in nodes.values() if member.kind == 12)
    body_atom, = words(nodes, body, "ATOM_ID_2001", 1)
    identifier_time = unsigned(cache_filetime, 64, "cache construction FILETIME")
    rows = []
    for ordinal, (edge, row, (_, downstream_id)) in enumerate(
        zip(edges, cache_fields["f60"], allocation.edges, strict=True)
    ):
        fields = row["object"].FieldsValue
        if (row["word"] != downstream_id or fields["f18"] != body_atom or fields["f1c"] != body_atom
                or row["object"].ClassValue.NameValue != "moCompEdge_c"):
            raise ValueError("edge lookup registration requires the actual retained body and edge row")
        info = cache_identity_info(ordinal, body_atom, edge.fields["node_id"], identifier_time)
        rows.append({"key": signed_dword(downstream_id), "object": info})
    return rows
