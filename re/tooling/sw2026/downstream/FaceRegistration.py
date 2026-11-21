from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from downstream.Body import UNIQUE
from downstream.CacheInputs import attached_part_chains
from para.Tracking import unsigned
from para.concentric.CylinderFace import words


def cache_identity_info(ordinal, body_atom, node_id, identifier_time):
    return ArchiveNode(UNIQUE, {
        "f08": ordinal, "f0c": body_atom, "f10": node_id,
        "high": identifier_time >> 32, "low": identifier_time & 0xffffffff,
    })


def fresh_face_registration(partition, allocation, cache_fields, cache_filetime):
    nodes, faces, _ = attached_part_chains(partition, allocation, cache_fields["f28"])
    if len(faces) != 6:
        raise ValueError("face lookup registration requires the admitted six-face body")
    body, = (member for member in nodes.values() if member.kind == 12)
    body_atom, = words(nodes, body, "ATOM_ID_2001", 1)
    identifier_time = unsigned(cache_filetime, 64, "cache construction FILETIME")
    rows = []
    for ordinal, (face, row, (_, downstream_id)) in enumerate(
        zip(faces, cache_fields["f48"], allocation.faces, strict=True)
    ):
        fields = row["object"].FieldsValue
        if (row["word"] != downstream_id or fields["f18"] != body_atom or fields["f1c"] != body_atom
                or row["object"].ClassValue.NameValue != "moCompFace_c"):
            raise ValueError("face lookup registration requires the actual retained body and face row")
        info = cache_identity_info(ordinal, body_atom, face.fields["node_id"], identifier_time)
        rows.append({"key": downstream_id, "object": info})
    return rows
